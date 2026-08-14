// Contended-queue microbenchmark for the C++ implementation.
//
// Isolates the bounded blocking queue and one-shot completion primitives that
// the full service uses under overload, without ShardCore work in the path.
// N producer threads each push a job carrying a std::promise and block on the
// matching std::future; one consumer thread pops and signals completion.
//
// Mirrors rust/examples/queue_contention.rs operation for operation.
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <future>
#include <thread>
#include <vector>

#include "uecm/bounded_queue.hpp"

namespace {

using Clock = std::chrono::steady_clock;

struct Job {
  bool stop = false;
  std::promise<void> done;
};

struct Args {
  std::uint64_t producers = 7;
  std::uint64_t capacity = 1024;
  std::uint64_t seconds = 2;
};

std::uint64_t arg_u64(int argc, char** argv, const char* name, std::uint64_t fallback) {
  for (int i = 1; i + 1 < argc; ++i) {
    if (std::strcmp(argv[i], name) == 0) return std::strtoull(argv[i + 1], nullptr, 10);
  }
  return fallback;
}

bool has_flag(int argc, char** argv, const char* name) {
  for (int i = 1; i < argc; ++i) {
    if (std::strcmp(argv[i], name) == 0) return true;
  }
  return false;
}

Args parse_args(int argc, char** argv) {
  Args a;
  a.producers = arg_u64(argc, argv, "--producers", a.producers);
  a.capacity = arg_u64(argc, argv, "--capacity", a.capacity);
  a.seconds = arg_u64(argc, argv, "--seconds", a.seconds);
  return a;
}

struct Result {
  std::uint64_t completed = 0;
  double wall_s = 0.0;
};

Result run_once(const Args& a) {
  uecm::BoundedQueue<Job> queue(a.capacity);

  std::thread consumer([&] {
    for (;;) {
      Job job = queue.pop();
      job.done.set_value();
      if (job.stop) break;
    }
  });

  const auto deadline = Clock::now() + std::chrono::seconds(a.seconds);
  std::atomic<std::uint64_t> completed{0};

  const auto t0 = Clock::now();
  std::vector<std::thread> producers;
  producers.reserve(a.producers);
  for (std::uint64_t p = 0; p < a.producers; ++p) {
    producers.emplace_back([&] {
      while (Clock::now() < deadline) {
        Job job;
        auto fut = job.done.get_future();
        queue.push(std::move(job));
        fut.get();
        completed.fetch_add(1, std::memory_order_relaxed);
      }
    });
  }

  for (auto& t : producers) t.join();
  const auto t1 = Clock::now();

  Job stop_job;
  stop_job.stop = true;
  auto stop_fut = stop_job.done.get_future();
  queue.push(std::move(stop_job));
  stop_fut.get();
  consumer.join();

  Result r;
  r.completed = completed.load(std::memory_order_relaxed);
  r.wall_s = std::chrono::duration<double>(t1 - t0).count();
  if (r.wall_s <= 0.0) r.wall_s = static_cast<double>(a.seconds);
  return r;
}

}  // namespace

int main(int argc, char** argv) {
  const Args a = parse_args(argc, argv);
  const bool json = has_flag(argc, argv, "--json");

  // Warm the queue and the scheduler before the timed window.
  (void)run_once(a);

  const Result r = run_once(a);
  const double kops = static_cast<double>(r.completed) / r.wall_s / 1000.0;
  const double ns_per_op = r.completed > 0
                               ? (r.wall_s * 1e9) / static_cast<double>(r.completed)
                               : 0.0;

  if (json) {
    std::printf(
        "{\"lang\":\"cpp\",\"producers\":%llu,\"capacity\":%llu,\"seconds\":%llu,"
        "\"completed\":%llu,\"wall_s\":%.4f,\"throughput_kops\":%.2f,"
        "\"ns_per_op\":%.1f}\n",
        (unsigned long long)a.producers, (unsigned long long)a.capacity,
        (unsigned long long)a.seconds, (unsigned long long)r.completed, r.wall_s, kops,
        ns_per_op);
  } else {
    std::printf("C++ queue contention (%llu producers, capacity %llu, %llu s)\n",
                (unsigned long long)a.producers, (unsigned long long)a.capacity,
                (unsigned long long)a.seconds);
    std::printf("  completed ops : %llu\n", (unsigned long long)r.completed);
    std::printf("  throughput    : %.2f kops/s\n", kops);
    std::printf("  mean ns/op    : %.1f\n", ns_per_op);
  }
  return 0;
}
