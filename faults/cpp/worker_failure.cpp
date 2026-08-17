// Boundary case: a failure inside one shard worker takes down more than that
// shard.
//
// The specified concurrency model (spec §7) is shared-nothing, thread-per-shard:
// each worker owns its contexts and no other thread touches them. The implied
// availability property is that a shard is a failure domain -- if one worker
// hits a bad context, the other seven keep serving. Neither language's type
// system says anything about whether that holds.
//
// In C++ it does not hold at all. An exception that escapes the callable of a
// std::thread does not propagate to the joiner: the runtime calls
// std::terminate and the whole process dies, taking every other shard's
// contexts with it. The blast radius of one malformed message is the node.
//
// The Rust counterpart (rust/worker_failure.rs) fails differently, and the
// difference is the finding rather than a win for either side: there the panic
// is confined to its own thread, but the Mutex it was holding is poisoned, so
// the damage propagates to whoever locks it next.
//
// Detection: none of the three sanitisers reports this, because nothing here is
// a memory error, a data race, or undefined behaviour. It is a design defect,
// and the tooling has no opinion about it. That is the point.
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <stdexcept>
#include <thread>
#include <vector>

namespace {

std::atomic<std::uint64_t> g_handled{0};

// One shard worker. Shard 3 receives a message it cannot process.
void worker(int shard) {
  for (int i = 0; i < 100; ++i) {
    if (shard == 3 && i == 10) {
      // A malformed signalling message on one shard.
      throw std::runtime_error("unparseable signalling PDU on shard 3");
    }
    g_handled.fetch_add(1, std::memory_order_relaxed);
  }
  std::printf("shard %d finished\n", shard);
}

}  // namespace

int main() {
  std::vector<std::thread> workers;
  for (int s = 0; s < 8; ++s) workers.emplace_back(worker, s);

  // Never reached: the escaping exception on shard 3 terminates the process
  // before any of these joins return.
  for (auto& t : workers) t.join();

  std::printf("all shards drained, handled=%lu\n",
              static_cast<unsigned long>(g_handled.load()));
  return 0;
}
