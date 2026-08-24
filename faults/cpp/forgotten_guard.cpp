// Boundary case: a lock that is taken and never released.
//
// Bearer setup holds the context lock for the whole procedure. The validation
// failure path was added later and returns before the unlock, so the context
// stays locked and the next worker to touch it waits forever. A scoped guard is
// the fix and is what the rest of the service uses. This is the shape that
// survives a refactor which adds an early return to a function that unlocks by
// hand.
//
// Nothing here is a race and nothing is a lock-order inversion, so
// ThreadSanitizer's deadlock detector has no cycle to close. The program simply
// stops. See rust/forgotten_guard.rs, where the guard makes the ordinary form of
// this bug unwritable and leaking the guard puts it back.
#include <cstdio>
#include <mutex>
#include <thread>

namespace {

struct UeContext {
  unsigned long ue_id;
  unsigned long bearers;
};

std::mutex ctx_mutex;
UeContext ctx{1001, 0};

bool setup_bearer(unsigned long teid) {
  ctx_mutex.lock();
  if (teid == 0) {
    std::printf("rejecting bearer with zero TEID\n");
    return false;  // returns still holding the lock
  }
  ctx.bearers += 1;
  ctx_mutex.unlock();
  return true;
}

}  // namespace

int main() {
  setup_bearer(0);
  std::printf("context locked and not released; next worker will block\n");
  std::fflush(stdout);

  // Another shard worker touches the same context.
  std::thread worker([] { setup_bearer(4711); });
  worker.join();  // never returns

  std::printf("bearers=%lu\n", ctx.bearers);
  return 0;
}
