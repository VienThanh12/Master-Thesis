#include "uecm/hash.hpp"
#include "test_util.hpp"

using namespace uecm;

int main() {
  // shard_index is deterministic and always in range.
  for (std::uint64_t n : {1ULL, 2ULL, 8ULL, 13ULL, 64ULL}) {
    for (std::uint64_t id = 1; id < 1000; ++id) {
      auto s = shard_index(id, n);
      CHECK(s < n);
      CHECK(s == shard_index(id, n));  // deterministic
    }
  }

  // Sequential ids should spread across shards (SplitMix64 finalizer, §8.1):
  // with 8 shards over 800 ids we expect every bucket used.
  {
    bool used[8] = {false};
    for (std::uint64_t id = 1; id <= 800; ++id) used[shard_index(id, 8)] = true;
    for (bool b : used) CHECK(b);
  }

  // FNV-1a is deterministic and distinguishes adjacent keys.
  CHECK(fnv1a_64(1234) == fnv1a_64(1234));
  CHECK(fnv1a_64(1) != fnv1a_64(2));

  return uecm::test::summary("test_hash");
}
