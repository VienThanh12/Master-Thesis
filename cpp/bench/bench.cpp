// UECM latency/throughput benchmark (C++ side), spec §3/§10.
//
// Two workloads (both identical to the Rust bench for fairness):
//   --workload signal (default): preload `preload` contexts per producer, then issue
//     `ops` handle_signaling calls to random ids. Isolates the hot signaling path.
//   --workload mixed: pinned RAN lifecycle generator (see bench/workload.hpp) —
//     attach/signaling/bearer/handover/release over `--active-ues` UEs per producer.
//
// Each measured op's service latency is recorded into a per-thread HDR histogram.
// Coordinated omission: --rate R (ops/sec/producer) paces sends to a fixed schedule
// and records latency from the intended send time with HDR correction; otherwise the
// loop is closed.

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include <sys/resource.h>

#include "hdr.hpp"
#include "uecm/service.hpp"
#include "workload.hpp"

#ifndef UECM_ALLOC_NAME
#define UECM_ALLOC_NAME "system"
#endif

using namespace uecm;
using bench::HdrHistogram;
using bench::SplitMix64;
using bench::WKind;
using bench::WOp;
using bench::Workload;
using clock_type = std::chrono::steady_clock;

namespace {

struct Args {
  std::string workload = "signal";
  std::uint64_t shards = 8;
  std::uint32_t queue_capacity = 1024;
  std::uint64_t producers = 0;  // 0 => = shards
  std::uint64_t preload = 10000;
  std::uint64_t active_ues = 10000;
  std::uint64_t ops = 200000;
  std::uint64_t warmup = 0;  // 0 => auto
  std::uint64_t seed = 42;
  double rate = 0.0;  // ops/sec/producer; 0 => closed loop
  bool json = false;
};

std::uint64_t to_u64(const char* s) { return std::strtoull(s, nullptr, 10); }

Args parse(int argc, char** argv) {
  Args a;
  for (int i = 1; i < argc; ++i) {
    std::string k = argv[i];
    auto val = [&]() -> const char* { return (i + 1 < argc) ? argv[++i] : "0"; };
    if (k == "--workload") a.workload = val();
    else if (k == "--shards") a.shards = to_u64(val());
    else if (k == "--queue-capacity") a.queue_capacity = static_cast<std::uint32_t>(to_u64(val()));
    else if (k == "--producers") a.producers = to_u64(val());
    else if (k == "--preload") a.preload = to_u64(val());
    else if (k == "--active-ues") a.active_ues = to_u64(val());
    else if (k == "--ops") a.ops = to_u64(val());
    else if (k == "--warmup") a.warmup = to_u64(val());
    else if (k == "--seed") a.seed = to_u64(val());
    else if (k == "--rate") a.rate = std::strtod(val(), nullptr);
    else if (k == "--json") a.json = true;
    else { std::fprintf(stderr, "unknown arg: %s\n", k.c_str()); std::exit(2); }
  }
  if (a.producers == 0) a.producers = a.shards;
  if (a.warmup == 0) {
    a.warmup = a.ops / 10;
    if (a.workload == "mixed") {
      const std::uint64_t bootstrap = 2 * a.active_ues;  // populate slots first
      if (bootstrap > a.warmup) a.warmup = bootstrap;
    }
  }
  return a;
}

constexpr std::int64_t kHdrLow = 1;
constexpr std::int64_t kHdrHigh = 3600LL * 1000 * 1000 * 1000;  // 3.6 s in ns
constexpr int kHdrSig = 3;

using KindCounts = std::array<std::uint64_t, bench::kWKindCount>;

// Execute one generated op; returns true on Ok.
bool exec_op(Service& svc, const WOp& op, UeId id) {
  switch (op.kind) {
    case WKind::Create:
      return svc.create_context(id, CreateParams{static_cast<std::uint32_t>(op.slot), {}}).has_value();
    case WKind::Setup:
      return svc.setup_connection(id).has_value();
    case WKind::Signal:
      return svc.handle_signaling(id, SignalingMsg{1, 4, {}}).has_value();
    case WKind::AddDrb:
      return svc.add_drb(id, DrbEntry{op.drb_id, 0, static_cast<std::uint32_t>(op.slot)}).has_value();
    case WKind::BeginReconf:
      return svc.begin_reconfigure(id, ReconfigParams{static_cast<std::uint32_t>(op.slot + 1)}).has_value();
    case WKind::CompleteReconf:
      return svc.complete_reconfigure(id).has_value();
    case WKind::AbortReconf:
      return svc.abort_reconfigure(id).has_value();
    case WKind::Release:
      return svc.release_context(id).has_value();
  }
  return false;
}

const char* kind_name(int k) {
  switch (static_cast<WKind>(k)) {
    case WKind::Create: return "create";
    case WKind::Setup: return "setup";
    case WKind::Signal: return "signal";
    case WKind::AddDrb: return "adddrb";
    case WKind::BeginReconf: return "begin_reconf";
    case WKind::CompleteReconf: return "complete_reconf";
    case WKind::AbortReconf: return "abort_reconf";
    case WKind::Release: return "release";
  }
  return "?";
}

}  // namespace

int main(int argc, char** argv) {
  const Args a = parse(argc, argv);
  if (a.workload != "signal" && a.workload != "mixed") {
    std::fprintf(stderr, "unknown --workload '%s' (use signal|mixed)\n", a.workload.c_str());
    return 2;
  }

  Config cfg;
  cfg.n_shards = a.shards;
  cfg.queue_capacity = a.queue_capacity;
  Service svc(cfg);
  svc.start();

  const std::uint64_t range = a.preload == 0 ? 1 : a.preload;

  // --- Preload (signal workload only; not measured) -------------------------
  if (a.workload == "signal") {
    std::vector<std::thread> ts;
    for (std::uint64_t p = 0; p < a.producers; ++p) {
      ts.emplace_back([&, p]() {
        const std::uint64_t base = p * 100000000ULL + 1;
        for (std::uint64_t i = 0; i < range; ++i) {
          const UeId id = base + i;
          svc.create_context(id, CreateParams{static_cast<std::uint32_t>(p), {}});
          svc.setup_connection(id);
        }
      });
    }
    for (auto& t : ts) t.join();
  }

  // --- Measured phase --------------------------------------------------------
  HdrHistogram merged(kHdrLow, kHdrHigh, kHdrSig);
  KindCounts merged_counts{};
  std::mutex merge_mtx;
  std::atomic<std::uint64_t> errors{0};
  const std::int64_t interval_ns =
      a.rate > 0.0 ? static_cast<std::int64_t>(1e9 / a.rate) : 0;

  const auto wall_start = clock_type::now();
  // Throughput must be counted over the measured phase only. `total_ops` excludes
  // the warm-up iterations, so dividing it by the whole run's wall time would
  // understate achieved throughput by exactly the warm-up fraction. Each producer
  // stamps the instant its measured phase starts and ends; the measured window is
  // the union of those intervals. Distinct indices, so no synchronisation needed.
  std::vector<clock_type::time_point> meas_start(a.producers, clock_type::time_point::max());
  std::vector<clock_type::time_point> meas_end(a.producers, clock_type::time_point::min());
  {
    std::vector<std::thread> ts;
    for (std::uint64_t p = 0; p < a.producers; ++p) {
      ts.emplace_back([&, p]() {
        HdrHistogram hist(kHdrLow, kHdrHigh, kHdrSig);
        KindCounts counts{};
        SplitMix64 rng{a.seed + p};
        Workload wl(a.active_ues, a.seed + p);
        const std::uint64_t base = p * 100000000ULL + 1;
        const SignalingMsg msg{1, 4, {}};
        std::uint64_t local_errors = 0;

        auto schedule = clock_type::now();
        const std::uint64_t total_iters = a.warmup + a.ops;
        for (std::uint64_t n = 0; n < total_iters; ++n) {
          const bool measured = n >= a.warmup;
          if (n == a.warmup) meas_start[p] = clock_type::now();

          // Select the op for this step.
          WOp op{WKind::Signal, 0, 0};
          UeId id;
          if (a.workload == "mixed") {
            op = wl.next();
            id = base + op.slot;
          } else {
            op.kind = WKind::Signal;
            id = base + (rng.next() % range);
          }

          clock_type::time_point intended;
          if (interval_ns > 0) {
            intended = schedule;
            std::this_thread::sleep_until(intended);
            schedule += std::chrono::nanoseconds(interval_ns);
          }
          const auto t0 = clock_type::now();
          bool ok;
          if (a.workload == "mixed") {
            ok = exec_op(svc, op, id);
          } else {
            ok = svc.handle_signaling(id, msg).has_value();
          }
          const auto t1 = clock_type::now();
          if (!ok) ++local_errors;

          if (measured) {
            ++counts[static_cast<std::size_t>(op.kind)];
            std::int64_t lat;
            if (interval_ns > 0)
              lat = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - intended).count();
            else
              lat = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
            if (lat < 1) lat = 1;
            if (interval_ns > 0) hist.record_corrected(lat, interval_ns);
            else hist.record(lat);
          }
        }
        meas_end[p] = clock_type::now();
        errors.fetch_add(local_errors, std::memory_order_relaxed);
        std::lock_guard<std::mutex> lk(merge_mtx);
        merged.add(hist);
        for (int k = 0; k < bench::kWKindCount; ++k) merged_counts[static_cast<std::size_t>(k)] += counts[static_cast<std::size_t>(k)];
      });
    }
    for (auto& t : ts) t.join();
  }
  const auto wall_end = clock_type::now();
  svc.shutdown();

  const double wall_ns =
      std::chrono::duration_cast<std::chrono::nanoseconds>(wall_end - wall_start).count();
  const double wall_s = wall_ns / 1e9;
  const auto meas_lo = *std::min_element(meas_start.begin(), meas_start.end());
  const auto meas_hi = *std::max_element(meas_end.begin(), meas_end.end());
  const double measured_wall_s =
      meas_hi > meas_lo
          ? std::chrono::duration_cast<std::chrono::nanoseconds>(meas_hi - meas_lo).count() / 1e9
          : wall_s;
  const std::int64_t total_ops = static_cast<std::int64_t>(a.ops * a.producers);
  const double thr = measured_wall_s > 0 ? total_ops / measured_wall_s : 0.0;
  const char* alloc = UECM_ALLOC_NAME;

  // Process resource usage (RQ3): peak RSS + total CPU across all threads.
  struct rusage ru{};
  getrusage(RUSAGE_SELF, &ru);
  const long rss_peak_kb = ru.ru_maxrss;  // Linux: kilobytes
  const double cpu_user_s = ru.ru_utime.tv_sec + ru.ru_utime.tv_usec / 1e6;
  const double cpu_sys_s = ru.ru_stime.tv_sec + ru.ru_stime.tv_usec / 1e6;
  const double cpu_pct = wall_s > 0 ? (cpu_user_s + cpu_sys_s) / wall_s * 100.0 : 0.0;

  if (a.json) {
    std::printf(
        "{\"lang\":\"cpp\",\"alloc\":\"%s\",\"workload\":\"%s\",\"shards\":%llu,\"producers\":%llu,"
        "\"rate\":%.1f,\"ops_total\":%lld,\"errors\":%llu,\"wall_s\":%.6f,"
        "\"measured_wall_s\":%.6f,\"throughput_ops_s\":%.1f,"
        "\"lat_ns\":{\"p50\":%lld,\"p90\":%lld,\"p99\":%lld,\"p999\":%lld,\"max\":%lld,"
        "\"mean\":%.1f},\"rss_peak_kb\":%ld,\"cpu_user_s\":%.3f,\"cpu_sys_s\":%.3f,"
        "\"cpu_pct\":%.1f,\"kinds\":{",
        alloc, a.workload.c_str(), (unsigned long long)a.shards, (unsigned long long)a.producers,
        a.rate, (long long)total_ops, (unsigned long long)errors.load(), wall_s, measured_wall_s,
        thr,
        (long long)merged.value_at_percentile(50), (long long)merged.value_at_percentile(90),
        (long long)merged.value_at_percentile(99), (long long)merged.value_at_percentile(99.9),
        (long long)merged.max(), merged.mean(), rss_peak_kb, cpu_user_s, cpu_sys_s, cpu_pct);
    for (int k = 0; k < bench::kWKindCount; ++k)
      std::printf("%s\"%s\":%llu", k ? "," : "", kind_name(k),
                  (unsigned long long)merged_counts[static_cast<std::size_t>(k)]);
    std::printf("}}\n");
  } else {
    std::printf("UECM bench [cpp, alloc=%s, workload=%s]\n", alloc, a.workload.c_str());
    std::printf("  shards=%llu producers=%llu active_ues=%llu ops/prod=%llu rate=%.0f\n",
                (unsigned long long)a.shards, (unsigned long long)a.producers,
                (unsigned long long)(a.workload == "mixed" ? a.active_ues : a.preload),
                (unsigned long long)a.ops, a.rate);
    std::printf("  ops_total=%lld errors=%llu wall=%.3fs (measured %.3fs) throughput=%.0f ops/s\n",
                (long long)total_ops, (unsigned long long)errors.load(), wall_s, measured_wall_s,
                thr);
    std::printf("  latency ns: p50=%lld p90=%lld p99=%lld p99.9=%lld max=%lld mean=%.1f\n",
                (long long)merged.value_at_percentile(50),
                (long long)merged.value_at_percentile(90),
                (long long)merged.value_at_percentile(99),
                (long long)merged.value_at_percentile(99.9), (long long)merged.max(),
                merged.mean());
    std::printf("  resource: peak_rss=%.1f MB  cpu=%.2fs (user %.2f + sys %.2f)  cpu%%=%.0f\n",
                rss_peak_kb / 1024.0, cpu_user_s + cpu_sys_s, cpu_user_s, cpu_sys_s, cpu_pct);
    if (a.workload == "mixed") {
      std::printf("  op kinds:");
      for (int k = 0; k < bench::kWKindCount; ++k)
        std::printf(" %s=%llu", kind_name(k), (unsigned long long)merged_counts[static_cast<std::size_t>(k)]);
      std::printf("\n");
    }
  }
  return errors.load() == 0 ? 0 : 1;
}
