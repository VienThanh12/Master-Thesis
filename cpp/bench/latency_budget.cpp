// Latency-budget decomposition for the C++ implementation.
//
// The load sweep measures an end-to-end operation: a caller builds a request,
// routes it to a shard's bounded queue, blocks on a completion handle, and a
// worker thread executes the operation and writes the result back. That path
// bundles two costs of very different character, and the sweep cannot separate
// them:
//
//   1. the operation's own work -- a pinned hash lookup, a state-machine guard,
//      and a field update, all inside one thread;
//   2. the cross-thread submit-and-complete handoff -- an enqueue, a wakeup, a
//      context switch, and a completion, none of which is language-specific and
//      all of which is charged to the scheduler.
//
// Both are measured here on the same host, in one process, with one caller
// thread. ShardCore is the single-threaded operation processor, so calling it
// directly gives (1) with no queue in the path; Service wraps the same core in
// the full threaded machinery, so calling it gives (1) + (2). Their difference
// is the handoff.
//
// Both figures are batch means over a long loop rather than per-call medians.
// That is deliberate: a clock read costs tens of nanoseconds, the same order as
// the core operation itself, so per-call timestamps would measure the
// instrument. The decomposition only needs the relative magnitude of the two
// terms, which a batch mean resolves cleanly.
//
// The map is preloaded to the same occupancy the sweep runs at, so the hash
// lookup does the same amount of work here as it does there.
//
// Mirrors rust/examples/latency_budget.rs operation for operation.
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

#include "uecm/config.hpp"
#include "uecm/service.hpp"
#include "uecm/shard_core.hpp"
#include "uecm/types.hpp"

namespace {

using namespace uecm;
using Clock = std::chrono::steady_clock;

// The UE every timed operation targets. Hot in cache by construction, as the
// sweep's own hot path is.
constexpr UeId kHotUe = 1;

// Keeps the optimizer from discarding a result whose value is never used.
// The compiler must assume the inline asm reads the operand.
template <class T>
inline void keep(T& value) {
  asm volatile("" : "+r,m"(value) : : "memory");
}

double ns_per_call(Clock::time_point t0, Clock::time_point t1, std::uint64_t iters) {
  const auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
  return static_cast<double>(ns) / static_cast<double>(iters);
}

// Mean nanoseconds per call for the operation with no queue in the path.
double measure_core(const Config& cfg, std::uint64_t per_shard, std::uint64_t iters) {
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(cfg, seq);
  const CreateParams params{};
  for (UeId ue = 1; ue <= (per_shard ? per_shard : 1); ++ue) {
    core.create_context(ue, params);
    core.setup_connection(ue);
  }
  const SignalingMsg msg{};

  const std::uint64_t warm = iters / 20 > 1000 ? iters / 20 : 1000;
  for (std::uint64_t i = 0; i < warm; ++i) {
    auto r = core.handle_signaling(kHotUe, msg);
    keep(r);
  }

  const auto t0 = Clock::now();
  for (std::uint64_t i = 0; i < iters; ++i) {
    auto r = core.handle_signaling(kHotUe, msg);
    keep(r);
  }
  const auto t1 = Clock::now();
  return ns_per_call(t0, t1, iters);
}

// Mean nanoseconds per call for the same operation through the full service.
// A single caller thread, so the queue is never contended: this is the floor of
// the handoff cost, not its value under the sweep's offered load.
double measure_service(const Config& cfg, std::uint64_t active_ues, std::uint64_t iters) {
  Service svc(cfg);
  svc.start();
  const CreateParams params{};
  for (UeId ue = 1; ue <= (active_ues ? active_ues : 1); ++ue) {
    svc.create_context(ue, params);
    svc.setup_connection(ue);
  }
  const SignalingMsg msg{};

  const std::uint64_t warm = iters / 20 > 100 ? iters / 20 : 100;
  for (std::uint64_t i = 0; i < warm; ++i) {
    auto r = svc.handle_signaling(kHotUe, msg);
    keep(r);
  }

  const auto t0 = Clock::now();
  for (std::uint64_t i = 0; i < iters; ++i) {
    auto r = svc.handle_signaling(kHotUe, msg);
    keep(r);
  }
  const auto t1 = Clock::now();
  const double ns = ns_per_call(t0, t1, iters);
  svc.shutdown();
  return ns;
}

std::uint64_t arg_u64(int argc, char** argv, const char* name, std::uint64_t fallback) {
  for (int i = 1; i + 1 < argc; ++i) {
    if (std::strcmp(argv[i], name) == 0) return std::strtoull(argv[i + 1], nullptr, 10);
  }
  return fallback;
}

bool has_flag(int argc, char** argv, const char* name) {
  for (int i = 1; i < argc; ++i) {
    if (std::strcmp(argv[i], name) == 0) return true;
  }
  return false;
}

}  // namespace

int main(int argc, char** argv) {
  const std::uint64_t shards = arg_u64(argc, argv, "--shards", 8);
  const std::uint64_t active_ues = arg_u64(argc, argv, "--active-ues", 5000);
  const std::uint64_t core_iters = arg_u64(argc, argv, "--core-iters", 2000000);
  const std::uint64_t svc_iters = arg_u64(argc, argv, "--svc-iters", 50000);
  const bool json = has_flag(argc, argv, "--json");

  Config cfg{};
  cfg.n_shards = shards;
  const std::uint64_t per_shard = active_ues / (shards ? shards : 1);

  const double core_ns = measure_core(cfg, per_shard, core_iters);
  const double svc_ns = measure_service(cfg, active_ues, svc_iters);
  const double handoff_ns = svc_ns - core_ns;

  if (json) {
    std::printf(
        "{\"lang\":\"cpp\",\"shards\":%llu,\"active_ues\":%llu,"
        "\"core_iters\":%llu,\"svc_iters\":%llu,"
        "\"core_ns\":%.1f,\"service_ns\":%.1f,\"handoff_ns\":%.1f,"
        "\"core_share_pct\":%.2f}\n",
        (unsigned long long)shards, (unsigned long long)active_ues,
        (unsigned long long)core_iters, (unsigned long long)svc_iters, core_ns, svc_ns,
        handoff_ns, 100.0 * core_ns / svc_ns);
  } else {
    std::printf("C++ latency budget (%llu shards, %llu active UEs)\n",
                (unsigned long long)shards, (unsigned long long)active_ues);
    std::printf("  core operation (no queue)   : %12.1f ns/call\n", core_ns);
    std::printf("  full service round-trip     : %12.1f ns/call\n", svc_ns);
    std::printf("  cross-thread handoff        : %12.1f ns/call\n", handoff_ns);
    std::printf("  operation's share of the end-to-end cost: %.2f%%\n",
                100.0 * core_ns / svc_ns);
  }
  return 0;
}
