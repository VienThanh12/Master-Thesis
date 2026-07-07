// Defect: unguarded shared mutation (lost updates).
// Several threads mutate shared state (a global counter and a shared context)
// without a lock. Unlike the memory defects, AddressSanitizer does not flag this
// logic-level race: the program "succeeds" but produces a wrong result (lost
// updates). Only ThreadSanitizer reports the underlying race.
#include <cstdio>
#include <thread>
#include <vector>

struct UeContext {
  unsigned long active_drbs = 0;
};

int main() {
  UeContext shared;
  constexpr int kThreads = 4;
  constexpr unsigned long kPer = 250000;

  std::vector<std::thread> ts;
  for (int t = 0; t < kThreads; ++t) {
    ts.emplace_back([&shared]() {
      for (unsigned long i = 0; i < kPer; ++i) shared.active_drbs += 1;  // unguarded
    });
  }
  for (auto& t : ts) t.join();

  const unsigned long expected = kThreads * kPer;
  std::printf("active_drbs=%lu expected=%lu (lost updates: %s)\n", shared.active_drbs,
              expected, shared.active_drbs == expected ? "no" : "yes");
  return 0;
}
