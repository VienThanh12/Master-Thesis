// Batch probe, C++ side. PROBE ONLY (-DUECM_BATCH_PROBE=ON), never a reported arm.
// Twin of rust/examples/batch.rs, Method 2 of docs/OVERLOAD_MECHANISM.md.
//
// Each sender owns one shard and sends batches of --batch signalling operations for
// UEs of that shard, one batch at a time and back to back, so the service is past
// saturation by construction. The time per batch is a fixed handoff cost plus the batch
// size times the cost of one operation inside a loaded worker. bench/batch_probes.sh
// sweeps the batch size and fits the two.
//
// Counting window: batches that start and finish inside [warm-up end, warm-up end +
// duration]. Process CPU is read at the two ends of the same window.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <thread>
#include <vector>

#include <sys/resource.h>

#include "uecm/hash.hpp"
#include "uecm/service.hpp"
#include "workload.hpp"

#ifndef UECM_ALLOC_NAME
#define UECM_ALLOC_NAME "system"
#endif

using namespace uecm;
using clock_type = std::chrono::steady_clock;

namespace {

struct Args {
  std::uint64_t shards = 7;
  std::uint64_t preload = 5000;
  std::uint64_t batch = 1;
  double duration_s = 3.0;
  double warmup_s = 1.0;
  std::uint64_t seed = 42;
  bool json = false;
};

Args parse(int argc, char** argv) {
  Args a;
  for (int i = 1; i < argc; ++i) {
    const std::string k = argv[i];
    auto val = [&]() -> const char* { return (i + 1 < argc) ? argv[++i] : "0"; };
    if (k == "--shards") a.shards = std::strtoull(val(), nullptr, 10);
    else if (k == "--preload") a.preload = std::strtoull(val(), nullptr, 10);
    else if (k == "--batch") a.batch = std::strtoull(val(), nullptr, 10);
    else if (k == "--duration-s") a.duration_s = std::strtod(val(), nullptr);
    else if (k == "--warmup-s") a.warmup_s = std::strtod(val(), nullptr);
    else if (k == "--seed") a.seed = std::strtoull(val(), nullptr, 10);
    else if (k == "--json") a.json = true;
    else { std::fprintf(stderr, "unknown arg: %s\n", k.c_str()); std::exit(2); }
  }
  if (a.shards == 0 || a.preload == 0 || a.batch == 0) {
    std::fprintf(stderr, "--shards, --preload and --batch must be positive\n");
    std::exit(2);
  }
  return a;
}

// (user CPU s, sys CPU s) for the whole process.
std::pair<double, double> cpu_times() {
  rusage ru{};
  getrusage(RUSAGE_SELF, &ru);
  return {ru.ru_utime.tv_sec + ru.ru_utime.tv_usec / 1e6,
          ru.ru_stime.tv_sec + ru.ru_stime.tv_usec / 1e6};
}

// The first `count` ids at or above shard * 100'000'000 + 1 that the pinned shard
// function (spec §8.1) assigns to `shard`. Identical in both languages.
std::vector<UeId> shard_ids(std::uint64_t shard, std::uint64_t n_shards, std::uint64_t count) {
  std::vector<UeId> ids;
  ids.reserve(count);
  for (UeId id = shard * 100000000ULL + 1; ids.size() < count; ++id)
    if (shard_index(id, n_shards) == shard) ids.push_back(id);
  return ids;
}

struct SenderOut {
  std::uint64_t ops = 0;
  std::uint64_t messages = 0;
  std::uint64_t errors = 0;
};

}  // namespace

int main(int argc, char** argv) {
  const Args a = parse(argc, argv);
  Config cfg;
  cfg.n_shards = a.shards;
  Service svc(cfg);
  svc.start();

  std::vector<std::vector<UeId>> ids;
  for (std::uint64_t s = 0; s < a.shards; ++s) ids.push_back(shard_ids(s, a.shards, a.preload));
  {
    std::vector<std::thread> ts;
    for (std::uint64_t s = 0; s < a.shards; ++s) {
      ts.emplace_back([&, s]() {
        for (const UeId id : ids[s]) {
          svc.create_context(id, CreateParams{static_cast<std::uint32_t>(s), {}});
          svc.setup_connection(id);
        }
      });
    }
    for (auto& t : ts) t.join();
  }

  const SignalingMsg msg{1, 4, {}};
  const auto start = clock_type::now();
  const auto t0 = start + std::chrono::duration_cast<clock_type::duration>(
                              std::chrono::duration<double>(a.warmup_s));
  const auto t1 = t0 + std::chrono::duration_cast<clock_type::duration>(
                           std::chrono::duration<double>(a.duration_s));
  const std::size_t batch = static_cast<std::size_t>(a.batch);

  std::vector<SenderOut> outs(a.shards);
  std::pair<double, double> cpu0, cpu1;
  {
    std::vector<std::thread> ts;
    for (std::uint64_t s = 0; s < a.shards; ++s) {
      ts.emplace_back([&, s]() {
        bench::SplitMix64 rng{a.seed + s};
        const std::vector<UeId>& mine = ids[s];
        const std::uint64_t n = mine.size();
        SenderOut out;
        for (;;) {
          std::vector<UeId> ue_ids;
          ue_ids.reserve(batch);
          for (std::size_t i = 0; i < batch; ++i) ue_ids.push_back(mine[rng.next() % n]);
          const auto began = clock_type::now();
          if (began >= t1) break;
          const auto ack = svc.handle_signaling_batch(std::move(ue_ids), msg);
          const auto done = clock_type::now();
          if (began >= t0 && done <= t1) {
            ++out.messages;
            out.ops += batch;
            if (!ack.has_value() || ack->new_messages_handled != batch) ++out.errors;
          }
        }
        outs[s] = out;
      });
    }
    std::this_thread::sleep_until(t0);
    cpu0 = cpu_times();
    std::this_thread::sleep_until(t1);
    cpu1 = cpu_times();
    for (auto& t : ts) t.join();
  }
  svc.shutdown();

  std::uint64_t ops = 0, messages = 0, errors = 0;
  std::uint64_t min_msgs = UINT64_MAX, max_msgs = 0;
  for (const auto& o : outs) {
    ops += o.ops;
    messages += o.messages;
    errors += o.errors;
    min_msgs = std::min(min_msgs, o.messages);
    max_msgs = std::max(max_msgs, o.messages);
  }
  const double user = cpu1.first - cpu0.first;
  const double sys = cpu1.second - cpu0.second;
  const double window = a.duration_s;
  const double us_per_msg = messages > 0 ? a.shards * window / messages * 1e6 : 0.0;
  const double cpu_us_per_op = ops > 0 ? (user + sys) / ops * 1e6 : 0.0;
  if (a.json) {
    std::printf(
        "{\"schema\":\"batch\",\"lang\":\"cpp\",\"alloc\":\"%s\",\"batch\":%llu,"
        "\"shards\":%llu,\"producers\":%llu,\"preload\":%llu,\"seed\":%llu,\"duration_s\":%.3f,"
        "\"warmup_s\":%.3f,\"ops\":%llu,\"messages\":%llu,\"errors\":%llu,"
        "\"messages_min_sender\":%llu,\"messages_max_sender\":%llu,\"ops_per_s\":%.1f,"
        "\"messages_per_s\":%.1f,\"us_per_message_per_sender\":%.3f,\"cpu_user_s\":%.4f,"
        "\"cpu_sys_s\":%.4f,\"cpu_us_per_op\":%.4f}\n",
        UECM_ALLOC_NAME, (unsigned long long)a.batch, (unsigned long long)a.shards,
        (unsigned long long)a.shards, (unsigned long long)a.preload, (unsigned long long)a.seed,
        a.duration_s, a.warmup_s, (unsigned long long)ops, (unsigned long long)messages,
        (unsigned long long)errors, (unsigned long long)min_msgs, (unsigned long long)max_msgs,
        ops / window, messages / window, us_per_msg, user, sys, cpu_us_per_op);
  } else {
    std::printf(
        "UECM batch probe [cpp, alloc=%s] batch=%llu shards=%llu ops/s=%.0f "
        "us/message/sender=%.2f cpu us/op=%.3f errors=%llu\n",
        UECM_ALLOC_NAME, (unsigned long long)a.batch, (unsigned long long)a.shards, ops / window,
        us_per_msg, cpu_us_per_op, (unsigned long long)errors);
  }
  return errors == 0 ? 0 : 1;
}
