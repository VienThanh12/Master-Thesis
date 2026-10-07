#pragma once
#include <cstdint>

// Configuration parameters. See spec/SPECIFICATION.md §9.
// Values are set at construction and fixed for a run; benchmarks override them.
namespace uecm {

struct Config {
  std::uint64_t n_shards = 8;                       // == worker-thread count
  std::uint32_t queue_capacity = 1024;              // bounded, blocking backpressure, full when > capacity, wait for space to become available
  std::uint64_t max_contexts_per_shard = 200000;    // CapacityExceeded beyond this
  std::uint32_t initial_shard_capacity = 4096;      // reserved at start()
  // Diagnostic only. When set, the worker reads the clock after dequeue and
  // before the operation. Compared and confirmatory runs leave this false.
  bool stamp_start = false;
};

inline constexpr std::size_t MAX_DRBS = 8;             // spec §4.2 / §9
inline constexpr std::size_t MAX_SIGNALING_PAYLOAD = 64;  // spec §6 / §9

}  // namespace uecm
