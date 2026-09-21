// UECM latency/throughput benchmark (C++ side), spec §3/§10.
//
// Two workloads (both identical to the Rust bench for fairness):
//   --workload signal (default): preload `preload` contexts per producer, then issue
//     `ops` handle_signaling calls to random ids. Isolates the hot signaling path.
//   --workload mixed: pinned RAN lifecycle generator (see bench/workload.hpp),
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
#include <numeric>
#include <optional>
#include <string>
#include <thread>
#include <vector>

#include <sys/resource.h>

#include "hdr.hpp"
#include "jestats.hpp"
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
  double max_run_s = 0.0;  // wall-clock cap on the measured phase; 0 => uncapped
  bool json = false;
  bool jitter = false;       // record inter-operation jitter (IPDV) as well
  std::string hist_out;      // append the full HDR bucket contents here
  std::string run_id;        // opaque tag echoed into the sidecar (campaign repeat)
  // Coordinated-omission backfill cap. Default matches kMaxCorrectionSamples.
  // --correction-cap 0 keeps the real sample and drops the synthetics (P1 probe).
  std::int64_t correction_cap = bench::kMaxCorrectionSamples;
  // record: fill during the timed loop (campaign). after: real samples only,
  // then correct_after once the producer finishes (P3). Probe-only.
  std::string correction_when = "record";
  // intended: t_done - t_intended (campaign). start: t_done - t_actual_send (P3).
  std::string latency_origin = "intended";
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
    else if (k == "--max-run-s") a.max_run_s = std::strtod(val(), nullptr);
    else if (k == "--jitter") a.jitter = true;
    else if (k == "--hist-out") a.hist_out = val();
    else if (k == "--run-id") a.run_id = val();
    else if (k == "--correction-cap") a.correction_cap = static_cast<std::int64_t>(to_u64(val()));
    else if (k == "--correction-when") a.correction_when = val();
    else if (k == "--latency-origin") a.latency_origin = val();
    else if (k == "--json") a.json = true;
    else { std::fprintf(stderr, "unknown arg: %s\n", k.c_str()); std::exit(2); }
  }
  if (a.correction_when != "record" && a.correction_when != "after") {
    std::fprintf(stderr, "--correction-when must be record or after\n");
    std::exit(2);
  }
  if (a.latency_origin != "intended" && a.latency_origin != "start") {
    std::fprintf(stderr, "--latency-origin must be intended or start\n");
    std::exit(2);
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

// Append one record holding the full bucket contents of the run's histograms.
//
// The JSON line carries the sparse occupied buckets as [value, count] pairs,
// where value is the bucket's highest equivalent value: the same lattice the
// Rust crate's iter_recorded() yields, so the two languages persist onto one
// grid rather than onto two internal bucket indices that happen to agree. This
// is what makes the far tail recoverable after the fact. p99.99 rests on ~17
// observations in a single run at the campaign's representative load, so it is
// only decision-grade once repeats are pooled, and pooling needs the buckets
// rather than the summary percentiles.
void write_hist_sidecar(const Args& a, const char* alloc, std::int64_t total_ops,
                        const HdrHistogram& lat, const HdrHistogram* jit) {
  std::FILE* f = std::fopen(a.hist_out.c_str(), "a");
  if (f == nullptr) {
    std::fprintf(stderr, "warning: cannot open --hist-out '%s'\n", a.hist_out.c_str());
    return;
  }
  std::fprintf(f,
               "{\"run_id\":\"%s\",\"lang\":\"cpp\",\"alloc\":\"%s\",\"workload\":\"%s\","
               "\"shards\":%llu,\"producers\":%llu,\"rate\":%.1f,\"seed\":%llu,"
               "\"ops_total\":%lld,\"hdr\":{\"low\":%lld,\"high\":%lld,\"sig\":%d}",
               a.run_id.c_str(), alloc, a.workload.c_str(), (unsigned long long)a.shards,
               (unsigned long long)a.producers, a.rate, (unsigned long long)a.seed,
               (long long)total_ops, (long long)kHdrLow, (long long)kHdrHigh, kHdrSig);
  auto dump = [&](const char* key, const HdrHistogram& h) {
    // `total` can exceed ops_total: under --rate the coordinated-omission
    // correction backfills synthetic samples into the histogram, which is by
    // design and is not a miscount of retired operations.
    std::fprintf(f, ",\"%s\":{\"total\":%lld,\"max\":%lld,\"pairs\":[", key,
                 (long long)h.total(), (long long)h.max());
    bool first = true;
    h.for_each_recorded([&](std::int64_t v, std::int64_t c) {
      std::fprintf(f, "%s[%lld,%lld]", first ? "" : ",", (long long)v, (long long)c);
      first = false;
    });
    std::fprintf(f, "]}");
  };
  dump("lat", lat);
  if (jit != nullptr) dump("jitter", *jit);
  std::fprintf(f, "}\n");
  std::fclose(f);
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
  // Allocated only under --jitter. One histogram is ~264 KiB, so allocating it
  // unconditionally would add producers x 264 KiB to peak RSS: the same order as
  // the language RSS difference RQ3 reports, measured by the instrument rather
  // than by the subject. The Rust side gates it identically.
  std::optional<HdrHistogram> merged_jitter;
  if (a.jitter) merged_jitter.emplace(kHdrLow, kHdrHigh, kHdrSig);
  KindCounts merged_counts{};
  std::mutex merge_mtx;
  std::atomic<std::uint64_t> errors{0};
  const std::int64_t interval_ns =
      a.rate > 0.0 ? static_cast<std::int64_t>(1e9 / a.rate) : 0;
  // Above saturation a producer can never retire its full op budget, so the
  // measured phase is also bounded in wall-clock time; throughput is then
  // computed from the ops actually retired, which is what exposes the knee.
  const std::int64_t max_run_ns =
      a.max_run_s > 0.0 ? static_cast<std::int64_t>(a.max_run_s * 1e9) : 0;

  const auto wall_start = clock_type::now();
  // Throughput must be counted over the measured phase only. `total_ops` excludes
  // the warm-up iterations, so dividing it by the whole run's wall time would
  // understate achieved throughput by exactly the warm-up fraction. Each producer
  // stamps the instant its measured phase starts and ends; the measured window is
  // the union of those intervals. Distinct indices, so no synchronisation needed.
  std::vector<clock_type::time_point> meas_start(a.producers, clock_type::time_point::max());
  std::vector<clock_type::time_point> meas_end(a.producers, clock_type::time_point::min());
  std::vector<std::uint64_t> meas_ops(a.producers, 0);
  {
    std::vector<std::thread> ts;
    for (std::uint64_t p = 0; p < a.producers; ++p) {
      ts.emplace_back([&, p]() {
        HdrHistogram hist(kHdrLow, kHdrHigh, kHdrSig);
        std::optional<HdrHistogram> jhist;
        if (a.jitter) jhist.emplace(kHdrLow, kHdrHigh, kHdrSig);
        std::int64_t prev_lat = -1;  // no predecessor yet; first measured op is skipped
        KindCounts counts{};
        SplitMix64 rng{a.seed + p};
        Workload wl(a.active_ues, a.seed + p);
        const std::uint64_t base = p * 100000000ULL + 1;
        const SignalingMsg msg{1, 4, {}};
        std::uint64_t local_errors = 0;
        std::uint64_t local_measured = 0;

        auto schedule = clock_type::now();
        const std::uint64_t total_iters = a.warmup + a.ops;
        clock_type::time_point meas_deadline = clock_type::time_point::max();
        for (std::uint64_t n = 0; n < total_iters; ++n) {
          const bool measured = n >= a.warmup;
          if (n == a.warmup) {
            meas_start[p] = clock_type::now();
            if (max_run_ns > 0)
              meas_deadline = meas_start[p] + std::chrono::nanoseconds(max_run_ns);
          }

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
            ++local_measured;
            std::int64_t lat;
            if (interval_ns > 0 && a.latency_origin != "start")
              lat = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - intended).count();
            else
              lat = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
            if (lat < 1) lat = 1;
            const bool fill_now = interval_ns > 0 && a.latency_origin != "start"
                                  && a.correction_when == "record";
            if (fill_now) hist.record_corrected(lat, interval_ns, a.correction_cap);
            else hist.record(lat);
            // Inter-operation jitter (IPDV, RFC 3393): the absolute difference
            // between consecutive measured latencies within this producer. Never
            // across producers, and only over real observations -- the synthetic
            // samples the coordinated-omission correction backfills are not
            // operations, so differencing them would invent variation.
            if (a.jitter) {
              if (prev_lat >= 0) {
                std::int64_t d = lat > prev_lat ? lat - prev_lat : prev_lat - lat;
                if (d < 1) d = 1;  // same floor the latency path uses
                jhist->record(d);
              }
              prev_lat = lat;
            }
            if (max_run_ns > 0 && t1 >= meas_deadline) break;
          }
        }
        meas_end[p] = clock_type::now();
        meas_ops[p] = local_measured;
        if (interval_ns > 0 && a.latency_origin != "start" && a.correction_when == "after")
          hist.correct_after(interval_ns, a.correction_cap);
        errors.fetch_add(local_errors, std::memory_order_relaxed);
        std::lock_guard<std::mutex> lk(merge_mtx);
        merged.add(hist);
        if (jhist) merged_jitter->add(*jhist);
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
  const std::int64_t total_ops = static_cast<std::int64_t>(
      std::accumulate(meas_ops.begin(), meas_ops.end(), std::uint64_t{0}));
  const double thr = measured_wall_s > 0 ? total_ops / measured_wall_s : 0.0;
  const char* alloc = UECM_ALLOC_NAME;

  // Process resource usage (RQ3): peak RSS + total CPU across all threads.
  struct rusage ru{};
  getrusage(RUSAGE_SELF, &ru);
  const long rss_peak_kb = ru.ru_maxrss;  // Linux: kilobytes
  const double cpu_user_s = ru.ru_utime.tv_sec + ru.ru_utime.tv_usec / 1e6;
  const double cpu_sys_s = ru.ru_stime.tv_sec + ru.ru_stime.tv_usec / 1e6;
  const double cpu_pct = wall_s > 0 ? (cpu_user_s + cpu_sys_s) / wall_s * 100.0 : 0.0;
  // Read after shutdown so the worker tcaches have been flushed, and so this
  // matches the point getrusage is sampled at.
  const std::string je_json = bench::je_json(bench::je_snapshot());

  // Quantiles, not percentiles: the Rust side passes these same literals to
  // hdrhistogram's value_at_quantile, so both languages select the same sample.
  const std::int64_t p25 = merged.value_at_quantile(0.25);
  const std::int64_t p50 = merged.value_at_quantile(0.50);
  const std::int64_t p75 = merged.value_at_quantile(0.75);
  const std::int64_t p90 = merged.value_at_quantile(0.90);
  const std::int64_t p99 = merged.value_at_quantile(0.99);
  const std::int64_t p999 = merged.value_at_quantile(0.999);
  const std::int64_t p9999 = merged.value_at_quantile(0.9999);

  std::string jitter_json;
  if (a.jitter) {
    char jbuf[320];
    std::snprintf(jbuf, sizeof(jbuf),
                  ",\"jitter_ns\":{\"p50\":%lld,\"p99\":%lld,\"p999\":%lld,\"max\":%lld,"
                  "\"mean\":%.1f,\"stdev\":%.1f,\"n\":%lld}",
                  (long long)merged_jitter->value_at_quantile(0.50),
                  (long long)merged_jitter->value_at_quantile(0.99),
                  (long long)merged_jitter->value_at_quantile(0.999),
                  (long long)merged_jitter->max(), merged_jitter->mean(),
                  merged_jitter->stdev(), (long long)merged_jitter->total());
    jitter_json = jbuf;
  }

  if (a.json) {
    std::printf(
        "{\"lang\":\"cpp\",\"alloc\":\"%s\",\"workload\":\"%s\",\"shards\":%llu,\"producers\":%llu,"
        "\"rate\":%.1f,\"correction_cap\":%lld,\"correction_when\":\"%s\",\"latency_origin\":\"%s\","
        "\"ops_total\":%lld,\"errors\":%llu,\"wall_s\":%.6f,"
        "\"measured_wall_s\":%.6f,\"throughput_ops_s\":%.1f,"
        "\"lat_ns\":{\"p25\":%lld,\"p50\":%lld,\"p75\":%lld,\"p90\":%lld,\"p99\":%lld,"
        "\"p999\":%lld,\"p9999\":%lld,\"max\":%lld,\"mean\":%.1f,\"stdev\":%.1f}%s,"
        "\"rss_peak_kb\":%ld,\"cpu_user_s\":%.3f,\"cpu_sys_s\":%.3f,"
        "\"cpu_pct\":%.1f,%s,\"kinds\":{",
        alloc, a.workload.c_str(), (unsigned long long)a.shards, (unsigned long long)a.producers,
        a.rate, (long long)a.correction_cap, a.correction_when.c_str(), a.latency_origin.c_str(),
        (long long)total_ops, (unsigned long long)errors.load(), wall_s, measured_wall_s,
        thr, (long long)p25, (long long)p50, (long long)p75, (long long)p90, (long long)p99,
        (long long)p999, (long long)p9999, (long long)merged.max(), merged.mean(), merged.stdev(),
        jitter_json.c_str(), rss_peak_kb, cpu_user_s, cpu_sys_s, cpu_pct, je_json.c_str());
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
    std::printf(
        "  latency ns: p50=%lld p90=%lld p99=%lld p99.9=%lld p99.99=%lld max=%lld mean=%.1f\n",
        (long long)p50, (long long)p90, (long long)p99, (long long)p999, (long long)p9999,
        (long long)merged.max(), merged.mean());
    std::printf("  dispersion ns: iqr=%lld (p25=%lld p75=%lld) stdev=%.1f\n",
                (long long)(p75 - p25), (long long)p25, (long long)p75, merged.stdev());
    if (a.jitter)
      std::printf("  jitter ns (IPDV): p50=%lld p99=%lld p99.9=%lld max=%lld mean=%.1f n=%lld\n",
                  (long long)merged_jitter->value_at_quantile(0.50),
                  (long long)merged_jitter->value_at_quantile(0.99),
                  (long long)merged_jitter->value_at_quantile(0.999),
                  (long long)merged_jitter->max(), merged_jitter->mean(),
                  (long long)merged_jitter->total());
    std::printf("  resource: peak_rss=%.1f MB  cpu=%.2fs (user %.2f + sys %.2f)  cpu%%=%.0f\n",
                rss_peak_kb / 1024.0, cpu_user_s + cpu_sys_s, cpu_user_s, cpu_sys_s, cpu_pct);
    if (const auto js = bench::je_snapshot(); js.available) {
      std::printf("  jemalloc: allocated=%.1f MB  active=%.1f MB  metadata=%.1f MB  "
                  "resident=%.1f MB  mapped=%.1f MB  retained=%.1f MB\n",
                  js.allocated / 1048576.0, js.active / 1048576.0, js.metadata / 1048576.0,
                  js.resident / 1048576.0, js.mapped / 1048576.0, js.retained / 1048576.0);
    }
    if (a.workload == "mixed") {
      std::printf("  op kinds:");
      for (int k = 0; k < bench::kWKindCount; ++k)
        std::printf(" %s=%llu", kind_name(k), (unsigned long long)merged_counts[static_cast<std::size_t>(k)]);
      std::printf("\n");
    }
  }

  if (!a.hist_out.empty())
    write_hist_sidecar(a, alloc, total_ops, merged,
                       merged_jitter ? &*merged_jitter : nullptr);

  return errors.load() == 0 ? 0 : 1;
}
