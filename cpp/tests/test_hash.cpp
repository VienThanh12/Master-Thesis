#include "uecm/hash.hpp"
#include "test_util.hpp"

using namespace uecm;

namespace {

// Known-answer values for the two functions the specification pins in §8. They
// were computed from the §8 pseudocode by a separate reference implementation,
// not read back out of either language, so these are the checks that hold both
// implementations to the *specified* algorithm rather than merely to each other:
// a self-consistent but wrong hash passes every other test in the suite, and
// would silently change the intra-shard probe sequence and the shard balance
// that the performance comparison depends on.

// SplitMix64 finalizer output, before the modulo (§8.1).
struct MixKat {
  std::uint64_t id;
  std::uint64_t mixed;
};
constexpr MixKat kMixKat[] = {
    {0ULL, 0x0000000000000000ULL},
    {1ULL, 0x5692161D100B05E5ULL},
    {2ULL, 0xDBD238973A2B148AULL},
    {1001ULL, 0x7139BB2427627383ULL},
    {~0ULL, 0xB4D055FCF2CBBD7BULL},
};

// FNV-1a over the 8 little-endian bytes of the key (§8.2).
struct FnvKat {
  std::uint64_t key;
  std::uint64_t digest;
};
constexpr FnvKat kFnvKat[] = {
    {0ULL, 0xA8C7F832281A39C5ULL},
    {1ULL, 0x89CD31291D2AEFA4ULL},
    {2ULL, 0xE6BD86443DF8CE07ULL},
    {255ULL, 0x9016B196E349A31AULL},
    {256ULL, 0xE3757CA7D64666EAULL},
    {1001ULL, 0x2E5741B73FAF0DDDULL},
    {~0ULL, 0x8CF51A8BFCA3883DULL},
};

}  // namespace

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

  // --- Known-answer: the pinned FNV-1a digest (§8.2) -------------------------
  for (const auto& k : kFnvKat) CHECK(fnv1a_64(k.key) == k.digest);

  // The map's hash functor must be the same function (§8.2).
  {
    FnvHash h;
    for (const auto& k : kFnvKat)
      CHECK(h(k.key) == static_cast<std::size_t>(k.digest));
  }

  // --- Known-answer: shard_index == finalizer(id) mod n (§8.1) ---------------
  // Checking against the pre-modulo constant for several divisors pins the
  // finalizer at full 64-bit width, including the wrapping multiplies, which a
  // range-and-determinism check cannot do.
  for (const auto& k : kMixKat) {
    for (std::uint64_t n : {1ULL, 2ULL, 3ULL, 8ULL, 13ULL, 64ULL, 1000ULL})
      CHECK(shard_index(k.id, n) == k.mixed % n);
  }

  // A non-power-of-two shard count must use the specified modulo, not the
  // bitmask that agrees with it only when n is a power of two. The mask is
  // computed here from the reference constant so the two candidate reductions
  // are compared directly, and the assertion that they disagree is what proves
  // the case above is actually discriminating.
  {
    bool discriminates = false;
    for (const auto& k : kMixKat) {
      const std::uint64_t n = 13;
      CHECK(shard_index(k.id, n) == k.mixed % n);
      if ((k.mixed % n) != (k.mixed & (n - 1))) discriminates = true;
    }
    CHECK(discriminates);
  }

  // Every bucket of a non-power-of-two shard count is reachable.
  {
    bool used[13] = {false};
    for (std::uint64_t id = 1; id <= 2000; ++id) used[shard_index(id, 13)] = true;
    for (bool b : used) CHECK(b);
  }

  return uecm::test::summary("test_hash");
}
