// Compact High Dynamic Range (HDR) histogram for latency capture (spec §10/§11).
//
// A from-scratch, header-only port of the canonical HdrHistogram bucketing
// algorithm (Gil Tene et al.), sufficient for latency percentiles with a fixed
// number of significant figures and O(1) recording. Used by the C++ benchmark;
// the Rust benchmark uses the `hdrhistogram` crate. Both are configured with the
// same (lowest, highest, sig_figs) so the two languages measure latency with
// equivalent precision and dynamic range (fairness, spec §3).

#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>

namespace bench {

class HdrHistogram {
 public:
  HdrHistogram(std::int64_t lowest, std::int64_t highest, int sig_figs) {
    lowest_ = lowest < 1 ? 1 : lowest;
    highest_ = highest;
    const std::int64_t largest = 2 * static_cast<std::int64_t>(std::pow(10.0, sig_figs));
    const int sub_bucket_count_magnitude =
        static_cast<int>(std::ceil(std::log2(static_cast<double>(largest))));
    sub_bucket_half_count_magnitude_ =
        (sub_bucket_count_magnitude > 1 ? sub_bucket_count_magnitude : 1) - 1;
    unit_magnitude_ = static_cast<int>(std::floor(std::log2(static_cast<double>(lowest_))));
    sub_bucket_count_ = static_cast<int>(std::pow(2.0, sub_bucket_half_count_magnitude_ + 1));
    sub_bucket_half_count_ = sub_bucket_count_ / 2;
    sub_bucket_mask_ = (static_cast<std::int64_t>(sub_bucket_count_) - 1) << unit_magnitude_;

    std::int64_t smallest_untrackable =
        static_cast<std::int64_t>(sub_bucket_count_) << unit_magnitude_;
    int buckets_needed = 1;
    while (smallest_untrackable < highest_) {
      if (smallest_untrackable > (std::numeric_limits<std::int64_t>::max() / 2)) {
        ++buckets_needed;
        break;
      }
      smallest_untrackable <<= 1;
      ++buckets_needed;
    }
    bucket_count_ = buckets_needed;
    counts_len_ = static_cast<std::int64_t>(bucket_count_ + 1) * (sub_bucket_count_ / 2);
    counts_.assign(static_cast<std::size_t>(counts_len_), 0);
  }

  void record(std::int64_t value) {
    if (value < 0) return;
    std::int64_t idx = counts_index_for(value);
    if (idx < 0) idx = 0;
    if (idx >= counts_len_) idx = counts_len_ - 1;  // clamp values above highest
    ++counts_[static_cast<std::size_t>(idx)];
    ++total_;
    sum_ += value;
    if (value > max_) max_ = value;
    if (value < min_) min_ = value;
  }

  // Coordinated-omission correction: if an operation took longer than the
  // expected inter-arrival interval, backfill the samples that "should" have
  // been recorded during the stall (Gil Tene's correction).
  void record_corrected(std::int64_t value, std::int64_t expected_interval) {
    record(value);
    if (expected_interval <= 0 || value <= expected_interval) return;
    for (std::int64_t missing = value - expected_interval; missing >= expected_interval;
         missing -= expected_interval) {
      std::int64_t idx = counts_index_for(missing);
      if (idx < 0) idx = 0;
      if (idx >= counts_len_) idx = counts_len_ - 1;
      ++counts_[static_cast<std::size_t>(idx)];
      ++total_;
      sum_ += missing;
    }
  }

  void add(const HdrHistogram& o) {  // both must share identical parameters
    for (std::int64_t i = 0; i < counts_len_; ++i)
      counts_[static_cast<std::size_t>(i)] += o.counts_[static_cast<std::size_t>(i)];
    total_ += o.total_;
    sum_ += o.sum_;
    if (o.total_ > 0) {
      if (o.max_ > max_) max_ = o.max_;
      if (o.min_ < min_) min_ = o.min_;
    }
  }

  std::int64_t total() const { return total_; }
  std::int64_t max() const { return total_ ? max_ : 0; }
  std::int64_t min() const { return total_ ? min_ : 0; }
  double mean() const {
    return total_ ? static_cast<double>(sum_) / static_cast<double>(total_) : 0.0;
  }

  std::int64_t value_at_percentile(double percentile) const {
    if (total_ == 0) return 0;
    double p = std::clamp(percentile, 0.0, 100.0);
    std::int64_t count_at =
        static_cast<std::int64_t>(std::ceil((p / 100.0) * static_cast<double>(total_)));
    if (count_at < 1) count_at = 1;
    std::int64_t running = 0;
    for (std::int64_t i = 0; i < counts_len_; ++i) {
      running += counts_[static_cast<std::size_t>(i)];
      if (running >= count_at) return highest_equivalent_value(value_at_index(i));
    }
    return max_;
  }

 private:
  static int clz64(std::int64_t v) {
    return __builtin_clzll(static_cast<unsigned long long>(v));
  }

  int get_bucket_index(std::int64_t value) const {
    const int pow2ceiling = 64 - clz64(value | sub_bucket_mask_);
    return pow2ceiling - unit_magnitude_ - (sub_bucket_half_count_magnitude_ + 1);
  }
  int get_sub_bucket_index(std::int64_t value, int bucket_index) const {
    return static_cast<int>(value >> (bucket_index + unit_magnitude_));
  }
  std::int64_t counts_index(int bucket_index, int sub_bucket_index) const {
    const int bucket_base_index = (bucket_index + 1) << sub_bucket_half_count_magnitude_;
    const int offset_in_bucket = sub_bucket_index - sub_bucket_half_count_;
    return static_cast<std::int64_t>(bucket_base_index + offset_in_bucket);
  }
  std::int64_t counts_index_for(std::int64_t value) const {
    const int bi = get_bucket_index(value);
    const int si = get_sub_bucket_index(value, bi);
    return counts_index(bi, si);
  }
  std::int64_t value_from_sub(int bucket_index, int sub_bucket_index) const {
    return static_cast<std::int64_t>(sub_bucket_index) << (bucket_index + unit_magnitude_);
  }
  std::int64_t value_at_index(std::int64_t index) const {
    int bucket_index = static_cast<int>(index >> sub_bucket_half_count_magnitude_) - 1;
    int sub_bucket_index =
        static_cast<int>(index & (sub_bucket_half_count_ - 1)) + sub_bucket_half_count_;
    if (bucket_index < 0) {
      sub_bucket_index -= sub_bucket_half_count_;
      bucket_index = 0;
    }
    return value_from_sub(bucket_index, sub_bucket_index);
  }
  std::int64_t size_of_equivalent_value_range(std::int64_t value) const {
    const int bi = get_bucket_index(value);
    const int si = get_sub_bucket_index(value, bi);
    const int adjusted_bucket = (si >= sub_bucket_count_) ? bi + 1 : bi;
    return static_cast<std::int64_t>(1) << (unit_magnitude_ + adjusted_bucket);
  }
  std::int64_t lowest_equivalent_value(std::int64_t value) const {
    const int bi = get_bucket_index(value);
    const int si = get_sub_bucket_index(value, bi);
    return value_from_sub(bi, si);
  }
  std::int64_t highest_equivalent_value(std::int64_t value) const {
    return lowest_equivalent_value(value) + size_of_equivalent_value_range(value) - 1;
  }

  std::int64_t lowest_ = 1, highest_ = 1;
  int unit_magnitude_ = 0;
  int sub_bucket_half_count_magnitude_ = 0;
  int sub_bucket_count_ = 0, sub_bucket_half_count_ = 0;
  std::int64_t sub_bucket_mask_ = 0;
  int bucket_count_ = 0;
  std::int64_t counts_len_ = 0;
  std::vector<std::int64_t> counts_;
  std::int64_t total_ = 0, sum_ = 0;
  std::int64_t max_ = 0;
  std::int64_t min_ = std::numeric_limits<std::int64_t>::max();
};

}  // namespace bench
