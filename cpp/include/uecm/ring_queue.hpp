#pragma once
#include <cstddef>
#include <optional>
#include <utility>
#include <vector>

namespace uecm {

// Attribution probe, not a compared configuration. A fixed-capacity ring exposing the
// five members BoundedQueue uses from std::queue (push/front/pop/size/empty), so the
// queue can be built on either storage without a line of its locking changing.
// Enable with -DUECM_RING_QUEUE=ON. Record any result in spec/SPECIFICATION.md §12.
//
// Why it exists. BoundedQueue stores its elements in a std::queue, which is deque-backed.
// libstdc++ sizes a deque node at 512 bytes and a Request is 160, so three requests fit
// per node: push() reaches the allocator on roughly every third call and pop() frees on
// every third call, both while holding the queue mutex. The Rust arm's sync_channel
// preallocates its slots and never allocates in send().
//
// The §12 queue probe was meant to settle whether that handoff explains the overload
// divergence, and it cannot: it replaced Rust's channel with a mutex and a VecDeque,
// matching the C++ synchronisation but not its buffer, because a VecDeque grows by
// doubling and never shrinks, so after warm-up it allocates nothing either. The
// contended-primitive microbenchmark has the same gap in the other direction -- its job
// is 32 bytes, so sixteen fit per deque node and it allocates at a fifth of the service's
// rate. Both controls removed the allocation along with the thing they meant to isolate.
//
// This probe holds the C++ locking fixed and removes only the allocation.
template <class T>
class RingBuffer {
 public:
  RingBuffer() = default;
  explicit RingBuffer(std::size_t capacity) : slots_(capacity) {}

  std::size_t size() const noexcept { return size_; }
  bool empty() const noexcept { return size_ == 0; }

  void push(T value) {
    slots_[tail_].emplace(std::move(value));
    tail_ = next(tail_);
    ++size_;
  }

  T& front() noexcept { return *slots_[head_]; }

  // Destroys a moved-from element, which for a Request means an already-empty promise:
  // nothing is returned to the allocator and the slot is reused by the next push.
  void pop() {
    slots_[head_].reset();
    head_ = next(head_);
    --size_;
  }

 private:
  std::size_t next(std::size_t i) const noexcept {
    return i + 1 == slots_.size() ? 0 : i + 1;
  }

  std::vector<std::optional<T>> slots_;
  std::size_t head_ = 0;
  std::size_t tail_ = 0;
  std::size_t size_ = 0;
};

}  // namespace uecm
