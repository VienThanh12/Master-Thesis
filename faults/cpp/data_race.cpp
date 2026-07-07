// Defect: data race.
// Two threads concurrently read and write a shared UE context field with no
// synchronization. The behaviour is undefined; ThreadSanitizer detects the race.
#include <cstdio>
#include <thread>

struct UeContext {
  unsigned long messages_handled = 0;
};

int main() {
  UeContext ctx;
  auto work = [&ctx]() {
    for (int i = 0; i < 200000; ++i) ctx.messages_handled += 1;  // unsynchronized
  };
  std::thread a(work);
  std::thread b(work);
  a.join();
  b.join();
  std::printf("messages_handled=%lu\n", ctx.messages_handled);
  return 0;
}
