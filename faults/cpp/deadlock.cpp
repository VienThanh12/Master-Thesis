// Defect: lock-order inversion (deadlock).
//
// Boundary case: unlike the other five, this defect is NOT prevented by safe Rust.
// A handover locks the source UE context and then the target; a concurrent handover
// in the opposite direction locks target then source. Nothing here is a memory-safety
// error and no ownership rule is broken -- the two threads simply wait for each other
// forever. Both languages compile it; in C++ ThreadSanitizer's deadlock detector can
// flag the inverted acquisition order at runtime.
#include <chrono>
#include <cstdio>
#include <mutex>
#include <thread>

struct UeContext {
  std::mutex m;
  unsigned long messages_handled = 0;
};

// Move accounting from `a` to `b`, holding both context locks.
static void handover(UeContext& a, UeContext& b) {
  for (int i = 0; i < 1000; ++i) {
    std::lock_guard<std::mutex> la(a.m);
    // Widen the window so the inversion is hit rather than being raced past.
    std::this_thread::sleep_for(std::chrono::microseconds(200));
    std::lock_guard<std::mutex> lb(b.m);
    a.messages_handled += 1;
    b.messages_handled += 1;
  }
}

int main() {
  UeContext src, dst;
  std::thread t1([&]() { handover(src, dst); });
  std::thread t2([&]() { handover(dst, src); });  // inverted lock order
  t1.join();
  t2.join();
  std::printf("handovers done: src=%lu dst=%lu\n", src.messages_handled,
              dst.messages_handled);
  return 0;
}
