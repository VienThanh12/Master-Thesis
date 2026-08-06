// Defect: lost update (a race condition that is not a data race).
//
// Boundary case: NOT prevented by safe Rust, and not reported by any sanitizer.
// Two workers bump a UE's message counter with a read-modify-write split across two
// separate critical sections. Every individual access is properly synchronized, so
// there is no data race for ThreadSanitizer to find and no lifetime error for a
// borrow checker to reject; the atomicity violation is in the algorithm. The counter
// simply ends up lower than it should, which in a control plane is a silently wrong
// activity statistic rather than a crash.
#include <cstdio>
#include <mutex>
#include <thread>

constexpr int kIters = 20000;

struct UeContext {
  std::mutex m;
  unsigned long messages_handled = 0;
};

static void bump(UeContext& ctx) {
  for (int i = 0; i < kIters; ++i) {
    unsigned long seen;
    {
      std::lock_guard<std::mutex> lk(ctx.m);
      seen = ctx.messages_handled;  // read ... lock released here
    }
    {
      std::lock_guard<std::mutex> lk(ctx.m);
      ctx.messages_handled = seen + 1;  // ... modify-write: update may be lost
    }
  }
}

int main() {
  UeContext ctx;
  std::thread a([&]() { bump(ctx); });
  std::thread b([&]() { bump(ctx); });
  a.join();
  b.join();
  const unsigned long expected = 2UL * kIters;
  std::printf("messages_handled=%lu expected=%lu lost=%lu\n", ctx.messages_handled,
              expected, expected - ctx.messages_handled);
  return ctx.messages_handled == expected ? 0 : 1;
}
