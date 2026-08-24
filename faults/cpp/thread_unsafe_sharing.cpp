// Defect: a handle documented as single-threaded is shared between workers.
//
// UeHandle is the intrusive-refcount idiom a control-plane codebase reaches for
// when std::shared_ptr's atomic control block is more than the hot path wants to
// pay. Its comment says single-threaded, which is the only place that constraint
// is written down: C++ has no way to say it in the type. Two shard workers take
// and drop a handle to the same context, and the count is corrupted.
//
// ThreadSanitizer reports the race on the counter. Nothing reports the design
// error behind it, which is that a type carrying a thread-affinity rule was
// passed across a thread boundary with nothing to stop it. See
// rust/thread_unsafe_sharing.rs, where that is exactly what does not compile.
#include <cstdio>
#include <string>
#include <thread>
#include <vector>

namespace {

constexpr int kWorkers = 4;
constexpr int kOpsPerWorker = 20000;

// Single-threaded refcounted handle. Do not share between threads.
struct UeHandle {
  std::string imsi;
  int refcount = 1;

  void retain() { ++refcount; }
  void release() { --refcount; }
};

void worker(UeHandle* handle) {
  for (int i = 0; i < kOpsPerWorker; ++i) {
    handle->retain();
    handle->release();
  }
}

}  // namespace

int main() {
  UeHandle handle{"244091234567890", 1};

  std::vector<std::thread> workers;
  workers.reserve(kWorkers);
  for (int i = 0; i < kWorkers; ++i) workers.emplace_back(worker, &handle);
  for (auto& w : workers) w.join();

  std::printf("refcount=%d expected=1\n", handle.refcount);
  return handle.refcount == 1 ? 0 : 1;
}
