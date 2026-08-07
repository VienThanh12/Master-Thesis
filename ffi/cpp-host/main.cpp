// RQ4 FFI prototype: C++ host driving the Rust UECM component.
//
// This models the incremental-adoption scenario: an existing C++ application
// keeps a Rust component behind a C ABI. The host only ever sees an opaque
// `UecmService*` handle and the plain-C entry points declared in uecm_ffi.h; it
// has no knowledge of Rust types, ownership, or threading.
//
// The program (1) exercises the full UE lifecycle across the seam and checks the
// results, and (2) micro-benchmarks the per-call cost of crossing the FFI
// boundary on the signaling hot path, and (3) drives the shared handle from
// several C++ threads to show the boundary is thread-safe.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <thread>
#include <vector>

#include "uecm_ffi.h"

namespace {

int g_failures = 0;

// Mean nanoseconds per signaling call through the seam, on a freshly created
// service with one connected UE.
//
// Split out so the measurement can be repeated and interleaved with the native
// baseline. A single pass is not enough to compare them: the call is dominated
// by a cross-thread wakeup whose run-to-run spread on a shared host is wider
// than any difference the seam could plausibly introduce, so one pass of each
// can order them either way.
double bench_op(std::uint64_t n_shards, int iters) {
  UecmService* svc = uecm_service_create(n_shards, /*queue_capacity=*/1024);
  if (!svc) return -1.0;
  const uint64_t hot = 2002;
  uecm_create_context(svc, hot, 7);
  uecm_setup_connection(svc, hot);

  for (int i = 0; i < iters / 20 + 100; ++i) uecm_handle_signaling(svc, hot, 1, 0, nullptr);

  const auto t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < iters; ++i) uecm_handle_signaling(svc, hot, 1, 0, nullptr);
  const auto t1 = std::chrono::steady_clock::now();

  uecm_service_destroy(svc);
  return std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count() /
         static_cast<double>(iters);
}

void check(bool cond, const char* what, int status = UECM_OK) {
  if (!cond) {
    std::printf("  [FAIL] %s (status=%d %s)\n", what, status, uecm_status_str(status));
    ++g_failures;
  }
}

// UeState values mirror spec §5.1.
constexpr uint8_t kIdle = 0, kConnected = 1;

}  // namespace

int main(int argc, char** argv) {
  // Bench-only mode: emit one op-cost sample and nothing else, so the runner can
  // interleave repeats of this with the native baseline.
  int iters = 50000;
  bool op_bench = false;
  for (int i = 1; i < argc; ++i) {
    if (std::strcmp(argv[i], "--op-bench") == 0) op_bench = true;
    else if (std::strcmp(argv[i], "--iters") == 0 && i + 1 < argc)
      iters = std::atoi(argv[++i]);
  }
  if (op_bench) {
    const double ns = bench_op(/*n_shards=*/4, iters);
    if (ns < 0) return 1;
    std::printf("{\"lang\":\"cpp-via-seam\",\"iters\":%d,\"op_ns\":%.1f}\n", iters, ns);
    return 0;
  }

  std::printf("== RQ4 FFI prototype: C++ host -> Rust UECM component ==\n");

  UecmService* svc = uecm_service_create(/*n_shards=*/4, /*queue_capacity=*/1024);
  check(svc != nullptr, "service created");
  if (!svc) return 1;

  // --- 1. Functional lifecycle across the seam -------------------------------
  const uint64_t ue = 1001;
  int s;
  s = uecm_create_context(svc, ue, /*serving_cell_id=*/7);
  check(s == UECM_OK, "create_context", s);
  s = uecm_setup_connection(svc, ue);
  check(s == UECM_OK, "setup_connection", s);

  uint64_t new_count = 0;
  s = uecm_handle_signaling(svc, ue, /*kind=*/3, /*payload_len=*/10, &new_count);
  check(s == UECM_OK && new_count == 1, "handle_signaling -> messages_handled==1", s);

  s = uecm_add_drb(svc, ue, /*drb_id=*/5, /*qos_flow_id=*/9, /*teid=*/0xABCD);
  check(s == UECM_OK, "add_drb", s);

  uint8_t state = 0xFF;
  uint64_t msgs = 0;
  s = uecm_lookup(svc, ue, &state, &msgs);
  check(s == UECM_OK && state == kConnected && msgs == 1, "lookup -> Connected, msgs==1", s);

  // Error path is transported faithfully: setup again must be InvalidState.
  s = uecm_setup_connection(svc, ue);
  check(s != UECM_OK, "duplicate setup rejected (InvalidState)", s);
  std::printf("  duplicate setup returned: %s\n", uecm_status_str(s));

  s = uecm_release_context(svc, ue);
  check(s == UECM_OK, "release_context", s);
  s = uecm_lookup(svc, ue, &state, &msgs);
  check(s != UECM_OK, "lookup after release -> NotFound", s);

  // --- 2a. Raw FFI crossing cost (no service work) ---------------------------
  // Isolates the intrinsic cost of crossing the C ABI from the op round-trip.
  const int noop_iters = 5000000;
  uint64_t sink = 0;
  auto n0 = std::chrono::steady_clock::now();
  for (int i = 0; i < noop_iters; ++i) sink = uecm_abi_noop(sink);
  auto n1 = std::chrono::steady_clock::now();
  const double ns_per_crossing =
      std::chrono::duration_cast<std::chrono::nanoseconds>(n1 - n0).count() /
      static_cast<double>(noop_iters);
  std::printf("  raw FFI crossing: %.3f ns/call (sink=%llu)\n", ns_per_crossing,
              (unsigned long long)sink);

  // --- 2b. End-to-end op latency through the seam ----------------------------
  // Dominated by the service's cross-thread submit+complete handoff. Whether a
  // native caller pays the same is measured rather than asserted: build.sh
  // interleaves repeats of `--op-bench` with the same operation called natively.
  // This single pass is indicative only and is not the figure the thesis quotes.
  const uint64_t hot = 2002;
  uecm_create_context(svc, hot, 7);
  uecm_setup_connection(svc, hot);

  auto t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < iters; ++i) {
    uecm_handle_signaling(svc, hot, 1, 0, nullptr);
  }
  auto t1 = std::chrono::steady_clock::now();
  const double ns_per_call =
      std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count() /
      static_cast<double>(iters);
  std::printf("  end-to-end signaling op: %d calls, %.1f ns/call (submit+complete round-trip)\n",
              iters, ns_per_call);
  uecm_release_context(svc, hot);  // don't leave it live for the count check below

  // --- 3. Shared handle from multiple C++ threads ----------------------------
  const int n_threads = 4;
  const int per_thread = 2000;
  std::vector<std::thread> ts;
  for (int t = 0; t < n_threads; ++t) {
    ts.emplace_back([svc, t]() {
      const uint64_t base = 100000ull + static_cast<uint64_t>(t) * per_thread;
      for (int i = 0; i < per_thread; ++i) {
        const uint64_t id = base + i;
        uecm_create_context(svc, id, 7);
        uecm_setup_connection(svc, id);
        uecm_handle_signaling(svc, id, 1, 0, nullptr);
      }
    });
  }
  for (auto& th : ts) th.join();

  const uint64_t live = uecm_count(svc);
  const uint64_t expected = static_cast<uint64_t>(n_threads) * per_thread;
  check(live == expected, "concurrent creates counted correctly", static_cast<int>(live));
  std::printf("  live contexts after %d-thread load: %llu (expected %llu)\n", n_threads,
              (unsigned long long)live, (unsigned long long)expected);

  uecm_service_destroy(svc);
  std::printf("  service destroyed\n");

  std::printf("== %s (%d failure%s) ==\n", g_failures == 0 ? "PASS" : "FAIL", g_failures,
              g_failures == 1 ? "" : "s");
  (void)kIdle;
  return g_failures == 0 ? 0 : 1;
}
