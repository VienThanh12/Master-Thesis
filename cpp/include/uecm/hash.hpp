#pragma once
#include <cstddef>
#include <cstdint>

// Pinned hashing functions. See spec/SPECIFICATION.md §8.
// These MUST be bit-for-bit identical to the Rust implementation.
namespace uecm {

// Shard selection via the SplitMix64 finalizer, then modulo n_shards (§8.1).
// All arithmetic wraps modulo 2^64 (native for uint64_t).
// https://rosettacode.org/wiki/Pseudo-random_numbers/Splitmix64
inline std::uint64_t shard_index(std::uint64_t ue_id, std::uint64_t n_shards) noexcept {
  std::uint64_t x = ue_id;
  x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
  x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
  x =  x ^ (x >> 31);
  return x % n_shards;
}

// FNV-1a 64-bit over the 8 little-endian bytes of the key (§8.2).
inline std::uint64_t fnv1a_64(std::uint64_t key) noexcept {
  std::uint64_t h = 0xcbf29ce484222325ULL;
  for (int i = 0; i < 8; ++i) {
    std::uint8_t b = static_cast<std::uint8_t>((key >> (i * 8)) & 0xFF);  // little-endian
    h = (h ^ b) * 0x100000001b3ULL;
  }
  return h;
}

// Hash functor for std::unordered_map<UeId, UeContext, FnvHash> (§8.2).
struct FnvHash {
  std::size_t operator()(std::uint64_t key) const noexcept {
    return static_cast<std::size_t>(fnv1a_64(key));
  }
};

}  // namespace uecm
