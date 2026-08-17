// Positive control for ThreadSanitizer's lock-order-inversion detector.
//
// This is NOT a catalogue defect. It exists so that the "undetected" outcome
// recorded for lock_order_deadlock is interpretable: without a case that the
// detector is known to catch, an absent report cannot be told apart from a
// detector that was never enabled.
//
// The inversion here is the same one deadlock.cpp injects -- a handover takes
// the source context lock then the target, and a second handover takes them in
// the opposite order -- but both sequences run to completion on one thread, so
// no thread ever blocks. TSan therefore observes both acquisition orders, closes
// the cycle in its lock-order graph, and reports.
//
// The contrast is the finding. TSan builds its graph from acquisitions that
// succeed, so it flags an inversion the program survived while staying silent on
// the one that actually deadlocked.
#include <cstdio>
#include <mutex>

struct UeContext {
  std::mutex m;
  unsigned long messages_handled = 0;
};

static void handover(UeContext& a, UeContext& b) {
  std::lock_guard<std::mutex> la(a.m);
  std::lock_guard<std::mutex> lb(b.m);
  a.messages_handled += 1;
  b.messages_handled += 1;
}

int main() {
  UeContext src, dst;
  handover(src, dst);
  handover(dst, src);  // inverted order, but the first handover already released
  std::printf("control completed: src=%lu dst=%lu\n", src.messages_handled,
              dst.messages_handled);
  return 0;
}
