#pragma once
#include <condition_variable>
#include <cstddef>
#include <mutex>
#include <queue>
#include <utility>

namespace uecm {

// Bounded, blocking multi-producer / single-consumer queue (spec §7).
// push() blocks when full (backpressure); pop() blocks when empty.
// Stores move-only element types (Request carries a std::promise).
template <class T>
class BoundedQueue {
 public:
  explicit BoundedQueue(std::size_t capacity)
      : capacity_(capacity == 0 ? 1 : capacity) {}

  void push(T value) {
    std::unique_lock<std::mutex> lk(m_);
    not_full_.wait(lk, [&] { return q_.size() < capacity_; });
    q_.push(std::move(value));
    lk.unlock();
    not_empty_.notify_one();
  }

  T pop() {
    std::unique_lock<std::mutex> lk(m_);
    not_empty_.wait(lk, [&] { return !q_.empty(); });
    T value = std::move(q_.front());
    q_.pop();
    lk.unlock();
    not_full_.notify_one();
    return value;
  }

 private:
  const std::size_t capacity_;
  std::mutex m_;
  std::condition_variable not_full_;
  std::condition_variable not_empty_;
  std::queue<T> q_;
};

}  // namespace uecm
