// Method 3 engineering pilot. `--workload signal` repeats signalling after a
// preload. `--workload mixed` walks the same lifecycle generator as bench.cpp:
// create, setup, signalling, bearer, reconfiguration, and release. Several
// requests stay in flight. Each producer pre-plans `ops` arrivals at a fixed
// interval, keeps each intended timestamp, and blocks only when the shard queue
// is full. One UE hashes to one shard, and that shard is FIFO, so one phone's
// steps stay in order. Different phones overlap. Warmup uses the synchronous
// API and is fully drained before the first planned arrival. The measured phase
// records worker completion (TimedResponse.done) against that intended timestamp,
// plus admission, in-service, and observation components. `--stamp-start` is
// diagnostic only. No coordinated-omission backfill.
//
// This does not replace bench/bench.cpp. The C++ twin of rust/examples/pipeline.rs:
// same schedule, same 60 s histogram bounds, same JSON and sidecar schema.

#include <array>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <future>
#include <latch>
#include <limits>
#include <string>
#include <thread>
#include <utility>
#include <variant>
#include <vector>

#include "hdr.hpp"
#include "uecm/hash.hpp"
#include "uecm/service.hpp"
#include "workload.hpp"

#ifndef UECM_ALLOC_NAME
#define UECM_ALLOC_NAME "system"
#endif

using namespace uecm;
using bench::HdrHistogram;
using clock_type = std::chrono::steady_clock;

namespace {

constexpr std::int64_t kHdrLow = 1;
constexpr std::int64_t kHdrHigh = 60LL * 1000 * 1000 * 1000;  // 60 s in ns
constexpr int kHdrSig = 3;

struct SplitMix64 {
  std::uint64_t s;
  std::uint64_t next() {
    std::uint64_t z = (s += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
  }
};

struct Args {
  std::uint64_t shards = 8;
  std::uint32_t queue_capacity = 1024;
  std::uint64_t producers = 0;
  std::uint64_t preload = 10000;
  std::uint64_t ops = 200000;
  std::uint64_t warmup = 0;
  std::uint64_t seed = 42;
  double rate = 0.0;
  double drain_timeout_s = 5.0;
  std::string hist_out;
  std::string run_id;
  std::string workload = "signal";
  std::uint64_t active_ues = 5000;
  bool json = false;
  bool stamp_start = false;
};

std::uint64_t parse_u64(const char* s, std::uint64_t fallback) {
  if (s == nullptr || *s < '0' || *s > '9') return fallback;
  char* end = nullptr;
  errno = 0;
  const unsigned long long v = std::strtoull(s, &end, 10);
  if (end == s || *end != '\0' || errno == ERANGE) return fallback;
  return static_cast<std::uint64_t>(v);
}

double parse_f64(const char* s, const char* flag) {
  if (s == nullptr || *s == '\0') {
    std::fprintf(stderr, "invalid %s\n", flag);
    std::exit(2);
  }
  char* end = nullptr;
  errno = 0;
  const double v = std::strtod(s, &end);
  if (end == s || *end != '\0' || errno == ERANGE) {
    std::fprintf(stderr, "invalid %s\n", flag);
    std::exit(2);
  }
  return v;
}

Args parse(int argc, char** argv) {
  Args a;
  for (int i = 1; i < argc; ++i) {
    const std::string k = argv[i];
    auto val = [&]() -> const char* {
      ++i;
      return (i < argc) ? argv[i] : "0";
    };
    if (k == "--shards") a.shards = parse_u64(val(), 8);
    else if (k == "--queue-capacity")
      a.queue_capacity = static_cast<std::uint32_t>(parse_u64(val(), 1024));
    else if (k == "--producers") a.producers = parse_u64(val(), 0);
    else if (k == "--preload") a.preload = parse_u64(val(), 10000);
    else if (k == "--ops") a.ops = parse_u64(val(), 200000);
    else if (k == "--warmup") a.warmup = parse_u64(val(), 0);
    else if (k == "--seed") a.seed = parse_u64(val(), 42);
    else if (k == "--rate") a.rate = parse_f64(val(), "--rate");
    else if (k == "--drain-timeout-s") a.drain_timeout_s = parse_f64(val(), "--drain-timeout-s");
    else if (k == "--hist-out") a.hist_out = val();
    else if (k == "--run-id") a.run_id = val();
    else if (k == "--workload") a.workload = val();
    else if (k == "--active-ues") a.active_ues = parse_u64(val(), 5000);
    else if (k == "--json") a.json = true;
    else if (k == "--stamp-start") a.stamp_start = true;
    else {
      std::fprintf(stderr, "unknown arg: %s\n", k.c_str());
      std::exit(2);
    }
  }
  if (!(a.rate > 0.0)) {
    std::fprintf(stderr, "--rate must be > 0\n");
    std::exit(2);
  }
  if (!(a.drain_timeout_s >= 0.0)) {
    std::fprintf(stderr, "--drain-timeout-s must be >= 0\n");
    std::exit(2);
  }
  if (a.workload != "signal" && a.workload != "mixed") {
    std::fprintf(stderr, "unknown --workload '%s' (use signal|mixed)\n", a.workload.c_str());
    std::exit(2);
  }
  if (a.producers == 0) a.producers = a.shards;
  // Same default as the reported bench: an explicit 0 means "auto".
  if (a.warmup == 0) {
    a.warmup = a.ops / 10;
    if (a.workload == "mixed") {
      const std::uint64_t bootstrap = 2 * a.active_ues;
      if (bootstrap > a.warmup) a.warmup = bootstrap;
    }
  }
  return a;
}

bool response_ok(const Response& response) {
  return std::visit([](const auto& result) { return result.has_value(); }, response);
}

bool exec_sync(Service& svc, const bench::WOp& op, UeId id) {
  switch (op.kind) {
    case bench::WKind::Create:
      return svc.create_context(id, CreateParams{static_cast<std::uint32_t>(op.slot), {}}).has_value();
    case bench::WKind::Setup:
      return svc.setup_connection(id).has_value();
    case bench::WKind::Signal:
      return svc.handle_signaling(id, SignalingMsg{1, 4, {}}).has_value();
    case bench::WKind::AddDrb:
      return svc.add_drb(id, DrbEntry{op.drb_id, 0, static_cast<std::uint32_t>(op.slot)}).has_value();
    case bench::WKind::BeginReconf:
      return svc.begin_reconfigure(id, ReconfigParams{static_cast<std::uint32_t>(op.slot + 1)})
          .has_value();
    case bench::WKind::CompleteReconf:
      return svc.complete_reconfigure(id).has_value();
    case bench::WKind::AbortReconf:
      return svc.abort_reconfigure(id).has_value();
    case bench::WKind::Release:
      return svc.release_context(id).has_value();
  }
  return false;
}

Service::Completion submit_async(Service& svc, const bench::WOp& op, UeId id) {
  switch (op.kind) {
    case bench::WKind::Create:
      return svc.create_context_async(id, CreateParams{static_cast<std::uint32_t>(op.slot), {}});
    case bench::WKind::Setup:
      return svc.setup_connection_async(id);
    case bench::WKind::Signal:
      return svc.handle_signaling_async(id, SignalingMsg{1, 4, {}});
    case bench::WKind::AddDrb:
      return svc.add_drb_async(id, DrbEntry{op.drb_id, 0, static_cast<std::uint32_t>(op.slot)});
    case bench::WKind::BeginReconf:
      return svc.begin_reconfigure_async(id, ReconfigParams{static_cast<std::uint32_t>(op.slot + 1)});
    case bench::WKind::CompleteReconf:
      return svc.complete_reconfigure_async(id);
    case bench::WKind::AbortReconf:
      return svc.abort_reconfigure_async(id);
    case bench::WKind::Release:
      return svc.release_context_async(id);
  }
  return svc.release_context_async(id);
}

std::uint64_t sat_mul(std::uint64_t x, std::uint64_t y) {
  if (x != 0 && y > std::numeric_limits<std::uint64_t>::max() / x)
    return std::numeric_limits<std::uint64_t>::max();
  return x * y;
}

struct Ticket {
  clock_type::time_point intended;
  clock_type::time_point submit_begin;
  clock_type::time_point enqueued;
  Service::Completion fut;
};

struct Counts {
  std::uint64_t enqueue_started = 0;
  std::uint64_t enqueued = 0;
  std::uint64_t completed_within_window = 0;
  std::uint64_t completed_during_drain = 0;
  std::uint64_t errors = 0;
  std::uint64_t timed_out = 0;
  std::uint64_t histogram_overflows = 0;
};

struct Hists {
  HdrHistogram primary;
  HdrHistogram admission;
  HdrHistogram in_service;
  HdrHistogram observation;
  HdrHistogram queue_wait;
  HdrHistogram execute;
  bool stamp_start = false;
  Hists()
      : primary(kHdrLow, kHdrHigh, kHdrSig),
        admission(kHdrLow, kHdrHigh, kHdrSig),
        in_service(kHdrLow, kHdrHigh, kHdrSig),
        observation(kHdrLow, kHdrHigh, kHdrSig),
        queue_wait(kHdrLow, kHdrHigh, kHdrSig),
        execute(kHdrLow, kHdrHigh, kHdrSig) {}
  void add(const Hists& o) {
    primary.add(o.primary);
    admission.add(o.admission);
    in_service.add(o.in_service);
    observation.add(o.observation);
    queue_wait.add(o.queue_wait);
    execute.add(o.execute);
  }
};

struct ProducerOut {
  Counts counts;
  Hists hists;
  std::array<std::uint64_t, bench::kWKindCount> kinds{};
  double drain_s = 0.0;
};

std::uint64_t elapsed_ns(clock_type::time_point later, clock_type::time_point earlier) {
  if (later <= earlier) return 0;
  const auto d = std::chrono::duration_cast<std::chrono::nanoseconds>(later - earlier);
  if (d.count() <= 0) return 0;
  return static_cast<std::uint64_t>(d.count());
}

// Floor sub-nanosecond and inverted stamps to 1 ns. Values above the shared
// 60 s bound are counted and left out of the histogram. record() would clamp
// those into the top bucket, which is not a rejection.
void record_ns(HdrHistogram& hist, std::uint64_t ns, std::uint64_t& overflows) {
  const std::uint64_t v = ns < 1 ? 1 : ns;
  if (v > static_cast<std::uint64_t>(kHdrHigh)) {
    ++overflows;
    return;
  }
  hist.record(static_cast<std::int64_t>(v));
}

void on_complete(const Ticket& ticket, const TimedResponse& completion,
                 clock_type::time_point observed, clock_type::time_point window_end,
                 Counts& counts, Hists& hists) {
  if (!response_ok(completion.response)) ++counts.errors;
  const auto done = completion.done;
  if (done <= window_end) ++counts.completed_within_window;
  else ++counts.completed_during_drain;
  record_ns(hists.primary, elapsed_ns(done, ticket.intended), counts.histogram_overflows);
  record_ns(hists.admission, elapsed_ns(ticket.enqueued, ticket.intended),
            counts.histogram_overflows);
  record_ns(hists.in_service, elapsed_ns(done, ticket.enqueued), counts.histogram_overflows);
  record_ns(hists.observation, elapsed_ns(observed, done), counts.histogram_overflows);
  if (hists.stamp_start) {
    record_ns(hists.queue_wait, elapsed_ns(completion.started, ticket.enqueued),
              counts.histogram_overflows);
    record_ns(hists.execute, elapsed_ns(done, completion.started), counts.histogram_overflows);
  }
}

// Non-blocking: only the front of each lane, and every front that is already ready.
void harvest_ready(std::vector<std::deque<Ticket>>& lanes, clock_type::time_point window_end,
                   Counts& counts, Hists& hists) {
  for (auto& lane : lanes) {
    while (!lane.empty()) {
      const auto status = lane.front().fut.wait_for(std::chrono::nanoseconds(0));
      if (status != std::future_status::ready) break;
      TimedResponse timed;
      try {
        timed = lane.front().fut.get();
      } catch (const std::future_error&) {
        lane.pop_front();
        ++counts.errors;
        continue;
      }
      const auto observed = clock_type::now();
      on_complete(lane.front(), timed, observed, window_end, counts, hists);
      lane.pop_front();
    }
  }
}

std::size_t earliest_front(const std::vector<std::deque<Ticket>>& lanes) {
  std::size_t best = lanes.size();
  for (std::size_t i = 0; i < lanes.size(); ++i) {
    if (lanes[i].empty()) continue;
    if (best == lanes.size() || lanes[i].front().intended < lanes[best].front().intended)
      best = i;
  }
  return best;
}

// Block on lane fronts until `deadline`. Anything still queued after that is timed out.
double drain(std::vector<std::deque<Ticket>>& lanes, clock_type::time_point deadline,
             clock_type::time_point window_end, Counts& counts, Hists& hists) {
  const auto drain_start = clock_type::now();
  for (;;) {
    harvest_ready(lanes, window_end, counts, hists);
    bool pending = false;
    for (const auto& lane : lanes)
      if (!lane.empty()) pending = true;
    if (!pending) break;
    if (clock_type::now() >= deadline) break;
    const std::size_t idx = earliest_front(lanes);
    if (idx >= lanes.size()) break;
    const auto remaining = deadline - clock_type::now();
    if (remaining <= clock_type::duration::zero()) break;
    const auto status = lanes[idx].front().fut.wait_for(remaining);
    if (status == std::future_status::timeout) break;
    if (status != std::future_status::ready) break;
    TimedResponse timed;
    try {
      timed = lanes[idx].front().fut.get();
    } catch (const std::future_error&) {
      lanes[idx].pop_front();
      ++counts.errors;
      continue;
    }
    const auto observed = clock_type::now();
    on_complete(lanes[idx].front(), timed, observed, window_end, counts, hists);
    lanes[idx].pop_front();
  }
  harvest_ready(lanes, window_end, counts, hists);
  for (auto& lane : lanes) {
    counts.timed_out += static_cast<std::uint64_t>(lane.size());
    lane.clear();
  }
  return std::chrono::duration<double>(clock_type::now() - drain_start).count();
}

ProducerOut run_producer(Service& svc, std::uint64_t producer, const Args& args,
                         std::uint64_t n_shards, std::uint64_t interval_ns,
                         const clock_type::time_point& origin,
                         const clock_type::time_point& window_end,
                         const clock_type::time_point& deadline, std::latch& ready,
                         std::latch& start) {
  const bool mixed = args.workload == "mixed";
  const std::uint64_t range = args.preload == 0 ? 1 : args.preload;
  const std::uint64_t base = producer * 100000000ULL + 1;
  SplitMix64 rng{args.seed + producer};
  bench::Workload wl(args.active_ues, args.seed + producer);
  const SignalingMsg msg{1, 4, {}};
  std::vector<std::deque<Ticket>> lanes(static_cast<std::size_t>(n_shards));
  ProducerOut out;
  out.hists.stamp_start = args.stamp_start;
  if (mixed) {
    // The generator advances here, then the measured loop continues it.
    for (std::uint64_t i = 0; i < args.warmup; ++i) {
      const auto op = wl.next();
      if (!exec_sync(svc, op, base + op.slot)) ++out.counts.errors;
    }
  } else {
    // Signal warmup consumed these draws in a previous pass. Skip them so measured ids match.
    for (std::uint64_t i = 0; i < args.warmup; ++i) (void)rng.next();
  }
  ready.count_down();
  start.wait();
  for (std::uint64_t n = 0; n < args.ops; ++n) {
    const auto step = sat_mul(interval_ns, n);
    const auto intended = origin + std::chrono::nanoseconds(static_cast<std::int64_t>(step));
    const auto now = clock_type::now();
    if (intended > now) std::this_thread::sleep_until(intended);
    UeId id;
    Service::Completion fut;
    int kind = static_cast<int>(bench::WKind::Signal);
    if (mixed) {
      const auto op = wl.next();
      id = base + op.slot;
      kind = static_cast<int>(op.kind);
      const auto submit_begin = clock_type::now();
      ++out.counts.enqueue_started;
      fut = submit_async(svc, op, id);
      const auto enqueued_at = clock_type::now();
      ++out.counts.enqueued;
      ++out.kinds[static_cast<std::size_t>(kind)];
      const auto shard = static_cast<std::size_t>(shard_index(id, n_shards));
      lanes[shard].push_back(Ticket{intended, submit_begin, enqueued_at, std::move(fut)});
    } else {
      id = base + (rng.next() % range);
      const auto submit_begin = clock_type::now();
      ++out.counts.enqueue_started;
      fut = svc.handle_signaling_async(id, msg);
      const auto enqueued_at = clock_type::now();
      ++out.counts.enqueued;
      ++out.kinds[static_cast<std::size_t>(kind)];
      const auto shard = static_cast<std::size_t>(shard_index(id, n_shards));
      lanes[shard].push_back(Ticket{intended, submit_begin, enqueued_at, std::move(fut)});
    }
    harvest_ready(lanes, window_end, out.counts, out.hists);
  }
  out.drain_s = drain(lanes, deadline, window_end, out.counts, out.hists);
  return out;
}

std::int64_t quantile(const HdrHistogram& h, double q) {
  return h.total() == 0 ? 0 : h.value_at_quantile(q);
}

std::int64_t hist_max(const HdrHistogram& h) { return h.total() == 0 ? 0 : h.max(); }

void dump_hist(std::string& out, const char* key, const HdrHistogram& h) {
  char hdr[128];
  std::snprintf(hdr, sizeof(hdr), ",\"%s\":{\"total\":%lld,\"max\":%lld,\"pairs\":[", key,
                (long long)h.total(), (long long)hist_max(h));
  out += hdr;
  bool first = true;
  h.for_each_recorded([&](std::int64_t v, std::int64_t c) {
    char pair[64];
    std::snprintf(pair, sizeof(pair), "%s[%lld,%lld]", first ? "" : ",", (long long)v, (long long)c);
    out += pair;
    first = false;
  });
  out += "]}";
}

void write_hist_sidecar(const Args& args, std::uint64_t ops_total, const Hists& hists) {
  std::FILE* f = std::fopen(args.hist_out.c_str(), "a");
  if (f == nullptr) {
    std::fprintf(stderr, "warning: cannot open --hist-out '%s'\n", args.hist_out.c_str());
    return;
  }
  std::string line;
  char head[512];
  std::snprintf(head, sizeof(head),
                "{\"schema\":\"pipeline\",\"run_id\":\"%s\",\"lang\":\"cpp\",\"alloc\":\"%s\","
                "\"workload\":\"%s\",\"shards\":%llu,\"producers\":%llu,\"rate\":%.1f,"
                "\"seed\":%llu,\"ops_total\":%llu,\"hdr\":{\"low\":%lld,\"high\":%lld,\"sig\":%d}",
                args.run_id.c_str(), UECM_ALLOC_NAME, args.workload.c_str(),
                (unsigned long long)args.shards,
                (unsigned long long)args.producers, args.rate, (unsigned long long)args.seed,
                (unsigned long long)ops_total, (long long)kHdrLow, (long long)kHdrHigh, kHdrSig);
  line = head;
  dump_hist(line, "primary", hists.primary);
  dump_hist(line, "admission", hists.admission);
  dump_hist(line, "in_service", hists.in_service);
  dump_hist(line, "observation", hists.observation);
  if (args.stamp_start) {
    dump_hist(line, "queue_wait", hists.queue_wait);
    dump_hist(line, "execute", hists.execute);
  }
  line += "}\n";
  if (std::fwrite(line.data(), 1, line.size(), f) != line.size())
    std::fprintf(stderr, "warning: cannot write --hist-out '%s'\n", args.hist_out.c_str());
  std::fclose(f);
}

std::string part_json(const HdrHistogram& h) {
  char buf[160];
  std::snprintf(buf, sizeof(buf), "{\"p50\":%lld,\"p99\":%lld,\"p999\":%lld,\"max\":%lld}",
                (long long)quantile(h, 0.50), (long long)quantile(h, 0.99),
                (long long)quantile(h, 0.999), (long long)hist_max(h));
  return buf;
}

}  // namespace

int main(int argc, char** argv) {
  const Args args = parse(argc, argv);
  const auto interval_ns = static_cast<std::uint64_t>(1e9 / args.rate);
  if (interval_ns == 0) {
    std::fprintf(stderr, "--rate is too high to schedule a 1 ns interval\n");
    return 2;
  }
  const std::uint64_t span = sat_mul(interval_ns, args.ops);
  if (span > static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())) {
    std::fprintf(stderr, "--rate and --ops exceed the schedule range\n");
    return 2;
  }
  const double drain_ns = args.drain_timeout_s * 1e9;
  if (drain_ns > static_cast<double>(std::numeric_limits<std::int64_t>::max())) {
    std::fprintf(stderr, "--drain-timeout-s is too large\n");
    return 2;
  }
  const auto window = std::chrono::nanoseconds(static_cast<std::int64_t>(span));
  const auto drain_timeout = std::chrono::nanoseconds(static_cast<std::int64_t>(drain_ns));

  Config cfg;
  cfg.n_shards = args.shards;
  cfg.queue_capacity = args.queue_capacity;
  cfg.stamp_start = args.stamp_start;
  Service svc(cfg);
  svc.start();
  const std::uint64_t n_shards = svc.n_shards();
  const std::uint64_t range = args.preload == 0 ? 1 : args.preload;

  if (args.workload != "mixed") {
  {
    std::vector<std::thread> ts;
    for (std::uint64_t p = 0; p < args.producers; ++p) {
      ts.emplace_back([&, p] {
        const std::uint64_t base = p * 100000000ULL + 1;
        for (std::uint64_t i = 0; i < range; ++i) {
          const UeId id = base + i;
          (void)svc.create_context(id, CreateParams{static_cast<std::uint32_t>(p), {}});
          (void)svc.setup_connection(id);
        }
      });
    }
    for (auto& t : ts) t.join();
  }

  {
    std::vector<std::thread> ts;
    for (std::uint64_t p = 0; p < args.producers; ++p) {
      ts.emplace_back([&, p] {
        const std::uint64_t base = p * 100000000ULL + 1;
        SplitMix64 rng{args.seed + p};
        const SignalingMsg msg{1, 4, {}};
        for (std::uint64_t n = 0; n < args.warmup; ++n) {
          const UeId id = base + (rng.next() % range);
          (void)svc.handle_signaling(id, msg);
        }
      });
    }
    for (auto& t : ts) t.join();
  }
  }

  std::vector<ProducerOut> outs(static_cast<std::size_t>(args.producers));
  {
    clock_type::time_point origin;
    clock_type::time_point window_end;
    clock_type::time_point deadline;
    std::latch ready(static_cast<std::ptrdiff_t>(args.producers));
    std::latch start(1);
    std::vector<std::thread> ts;
    for (std::uint64_t p = 0; p < args.producers; ++p) {
      ts.emplace_back([&, p] {
        outs[p] = run_producer(svc, p, args, n_shards, interval_ns, origin, window_end,
                               deadline, ready, start);
      });
    }
    // Start the common schedule only after every producer has allocated its
    // thread-local state and reached the gate.
    ready.wait();
    origin = clock_type::now();
    window_end = origin + window;
    deadline = window_end + drain_timeout;
    start.count_down();
    for (auto& t : ts) t.join();
  }
  svc.shutdown();

  Hists merged;
  Counts totals;
  std::array<std::uint64_t, bench::kWKindCount> kinds{};
  double drain_s = 0.0;
  for (const auto& o : outs) {
    merged.add(o.hists);
    for (int i = 0; i < bench::kWKindCount; ++i) kinds[static_cast<std::size_t>(i)] += o.kinds[static_cast<std::size_t>(i)];
    totals.enqueue_started += o.counts.enqueue_started;
    totals.enqueued += o.counts.enqueued;
    totals.completed_within_window += o.counts.completed_within_window;
    totals.completed_during_drain += o.counts.completed_during_drain;
    totals.errors += o.counts.errors;
    totals.timed_out += o.counts.timed_out;
    totals.histogram_overflows += o.counts.histogram_overflows;
    if (o.drain_s > drain_s) drain_s = o.drain_s;
  }

  const std::uint64_t planned = sat_mul(args.producers, args.ops);
  const double arrival_window_s = static_cast<double>(span) / 1e9;
  const double throughput_ops_s =
      arrival_window_s > 0.0
          ? static_cast<double>(totals.completed_within_window) / arrival_window_s
          : 0.0;
  const bool valid =
      totals.timed_out == 0 && totals.histogram_overflows == 0 && totals.errors == 0;
  const std::uint64_t ops_total =
      totals.completed_within_window + totals.completed_during_drain;

  const std::string admission = part_json(merged.admission);
  const std::string in_service = part_json(merged.in_service);
  const std::string observation = part_json(merged.observation);
  const std::string queue_wait =
      args.stamp_start ? part_json(merged.queue_wait) : std::string("null");
  const std::string execute = args.stamp_start ? part_json(merged.execute) : std::string("null");
  char kinds_buf[160];
  std::snprintf(kinds_buf, sizeof(kinds_buf),
                "[%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu]",
                (unsigned long long)kinds[0], (unsigned long long)kinds[1],
                (unsigned long long)kinds[2], (unsigned long long)kinds[3],
                (unsigned long long)kinds[4], (unsigned long long)kinds[5],
                (unsigned long long)kinds[6], (unsigned long long)kinds[7]);

  if (args.json) {
    std::printf(
        "{\"schema\":\"pipeline\",\"lang\":\"cpp\",\"alloc\":\"%s\","
        "\"workload\":\"%s\",\"shards\":%llu,\"queue_capacity\":%u,"
        "\"producers\":%llu,\"preload\":%llu,\"ops\":%llu,\"warmup\":%llu,"
        "\"active_ues\":%llu,\"kinds\":%s,"
        "\"seed\":%llu,\"rate\":%.1f,\"drain_timeout_s\":%.6f,"
        "\"planned\":%llu,\"enqueue_started\":%llu,\"enqueued\":%llu,"
        "\"completed_within_window\":%llu,"
        "\"completed_during_drain\":%llu,\"errors\":%llu,"
        "\"timed_out\":%llu,\"histogram_overflows\":%llu,"
        "\"valid\":%s,\"arrival_window_s\":%.6f,\"drain_s\":%.6f,"
        "\"throughput_ops_s\":%.1f,"
        "\"primary_ns\":{\"p50\":%lld,\"p99\":%lld,\"p999\":%lld,\"p9999\":%lld,\"max\":%lld},"
        "\"admission_ns\":%s,\"in_service_ns\":%s,\"observation_ns\":%s,"
        "\"stamp_start\":%s,\"queue\":\"mutex\",\"queue_wait_ns\":%s,\"execute_ns\":%s}\n",
        UECM_ALLOC_NAME, args.workload.c_str(), (unsigned long long)args.shards, args.queue_capacity,
        (unsigned long long)args.producers, (unsigned long long)args.preload,
        (unsigned long long)args.ops, (unsigned long long)args.warmup,
        (unsigned long long)args.active_ues, kinds_buf,
        (unsigned long long)args.seed, args.rate, args.drain_timeout_s,
        (unsigned long long)planned, (unsigned long long)totals.enqueue_started,
        (unsigned long long)totals.enqueued, (unsigned long long)totals.completed_within_window,
        (unsigned long long)totals.completed_during_drain, (unsigned long long)totals.errors,
        (unsigned long long)totals.timed_out, (unsigned long long)totals.histogram_overflows,
        valid ? "true" : "false", arrival_window_s, drain_s, throughput_ops_s,
        (long long)quantile(merged.primary, 0.50), (long long)quantile(merged.primary, 0.99),
        (long long)quantile(merged.primary, 0.999), (long long)quantile(merged.primary, 0.9999),
        (long long)hist_max(merged.primary), admission.c_str(), in_service.c_str(),
        observation.c_str(), args.stamp_start ? "true" : "false", queue_wait.c_str(),
        execute.c_str());
  } else {
    std::printf("UECM pipeline [cpp, alloc=%s, schema=pipeline, workload=%s]\n",
                UECM_ALLOC_NAME, args.workload.c_str());
    std::printf("  kinds=%s\n", kinds_buf);
    std::printf(
        "  shards=%llu producers=%llu preload=%llu ops/prod=%llu warmup=%llu rate=%.0f "
        "drain_timeout_s=%.3f\n",
        (unsigned long long)args.shards, (unsigned long long)args.producers,
        (unsigned long long)args.preload, (unsigned long long)args.ops,
        (unsigned long long)args.warmup, args.rate, args.drain_timeout_s);
    std::printf(
        "  planned=%llu enqueue_started=%llu enqueued=%llu "
        "within_window=%llu during_drain=%llu "
        "errors=%llu timed_out=%llu histogram_overflows=%llu valid=%s\n",
        (unsigned long long)planned, (unsigned long long)totals.enqueue_started,
        (unsigned long long)totals.enqueued, (unsigned long long)totals.completed_within_window,
        (unsigned long long)totals.completed_during_drain, (unsigned long long)totals.errors,
        (unsigned long long)totals.timed_out, (unsigned long long)totals.histogram_overflows,
        valid ? "true" : "false");
    std::printf("  arrival_window_s=%.6f drain_s=%.6f throughput_ops_s=%.1f\n",
                arrival_window_s, drain_s, throughput_ops_s);
    std::printf("  primary ns: p50=%lld p99=%lld p999=%lld p99.99=%lld max=%lld\n",
                (long long)quantile(merged.primary, 0.50),
                (long long)quantile(merged.primary, 0.99),
                (long long)quantile(merged.primary, 0.999),
                (long long)quantile(merged.primary, 0.9999),
                (long long)hist_max(merged.primary));
    std::printf("  admission ns: p50=%lld p99=%lld p999=%lld max=%lld\n",
                (long long)quantile(merged.admission, 0.50),
                (long long)quantile(merged.admission, 0.99),
                (long long)quantile(merged.admission, 0.999),
                (long long)hist_max(merged.admission));
    std::printf("  in_service ns: p50=%lld p99=%lld p999=%lld max=%lld\n",
                (long long)quantile(merged.in_service, 0.50),
                (long long)quantile(merged.in_service, 0.99),
                (long long)quantile(merged.in_service, 0.999),
                (long long)hist_max(merged.in_service));
    std::printf("  observation ns: p50=%lld p99=%lld p999=%lld max=%lld\n",
                (long long)quantile(merged.observation, 0.50),
                (long long)quantile(merged.observation, 0.99),
                (long long)quantile(merged.observation, 0.999),
                (long long)hist_max(merged.observation));
    if (args.stamp_start) {
      std::printf("  queue_wait ns: p50=%lld p99=%lld p999=%lld max=%lld\n",
                  (long long)quantile(merged.queue_wait, 0.50),
                  (long long)quantile(merged.queue_wait, 0.99),
                  (long long)quantile(merged.queue_wait, 0.999),
                  (long long)hist_max(merged.queue_wait));
      std::printf("  execute ns: p50=%lld p99=%lld p999=%lld max=%lld\n",
                  (long long)quantile(merged.execute, 0.50),
                  (long long)quantile(merged.execute, 0.99),
                  (long long)quantile(merged.execute, 0.999),
                  (long long)hist_max(merged.execute));
    }
  }

  if (!args.hist_out.empty()) write_hist_sidecar(args, ops_total, merged);
  return valid ? 0 : 1;
}
