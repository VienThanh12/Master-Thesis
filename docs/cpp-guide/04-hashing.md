# Chapter 4 — Hashing

**Open:** `cpp/include/uecm/hash.hpp`, then `cpp/tests/test_hash.cpp`.

## The claim this layer makes

Two functions decide where a UE lives and how it is found inside a shard.
They are pinned bit-for-bit against the spec's pseudocode and against Rust.
If they drifted, the performance comparison would be comparing different
partitionings and different probe sequences, not two languages.

## Two different hashes, two jobs

| Function | Spec | Job |
| --- | --- | --- |
| `shard_index(ue_id, n_shards)` | §8.1 | Which worker owns this id. SplitMix64 finalizer, then `% n_shards`. |
| `fnv1a_64(key)` | §8.2 | `unordered_map` bucket. FNV-1a over 8 little-endian bytes of the key. |
| `FnvHash` | §8.2 | The C++ hash functor. Calls `fnv1a_64` and casts to `size_t`. |

They are not interchangeable. `shard_index` mixes sequential ids so they
spread across workers. `fnv1a_64` is a simple byte hash so both languages
do the same work per lookup. Replacing either with `std::hash` would be a
fairness defect even if tests still passed against each other.

## Reading `shard_index`

```cpp
inline std::uint64_t shard_index(std::uint64_t ue_id, std::uint64_t n_shards) noexcept {
  std::uint64_t x = ue_id;
  x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
  x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
  x =  x ^ (x >> 31);
  return x % n_shards;
}
```

Unsigned overflow wraps modulo 2^64, which is what the spec means by
"wrapping multiply". There is no 128-bit widening.

**`n_shards == 0` is undefined behaviour** (`x % 0`). `Service` clamps its
config to 1 before anyone routes. The free function does not. Conformance
vectors never pass 0. Do not "fix" this as your first edit. It is a logged
edge (`docs/CODE_REVIEW.md` finding 2). The `shard` op in the parity runner
uses the raw config value, so a vector with `n_shards=0` would disagree with
routing even if modulo were defined.

## Reading `fnv1a_64`

The loop walks `i = 0 .. 7` and takes `((key >> (i * 8)) & 0xFF)`. That is
little-endian on purpose, independent of host endianness. A host-endian
cast of `&key` would be a silent cross-language split on a big-endian
machine and a maintenance hazard on this one.

## Why `test_hash.cpp` is the first test to read

Most of the suite can pass if both languages are **wrong in the same way**.
The known-answer tables in `test_hash.cpp` were computed from the spec
pseudocode by a third implementation, not read back out of C++ or Rust.
That is what pins the algorithm rather than mere mutual agreement.

The file also checks:

- `shard_index` is in range and deterministic.
- Sequential ids actually use every bucket of 8 shards (the SplitMix64
  reason for existing).
- `FnvHash{}(key)` equals `fnv1a_64(key)` (the functor must not drift).
- `n_shards = 13` is covered. Power-of-two shard counts hide the difference
  between `x % n` and `x & (n - 1)`. Thirteen does not.

## A check

```bash
cmake --build cpp/build --target test_hash
./cpp/build/test_hash
```

Then pick id `1001` and compute `shard_index(1001, 8)` by running a
three-line program, or by adding a temporary print. Confirm it stays the
same if you call it twice. Confirm `shard_index(1001, 13)` is a different
formula result, not "8 plus something".

## Do not

Do not replace `% n_shards` with a bitmask. Do not switch FNV-1a for
`std::hash<uint64_t>`. Do not start here if you have not read chapter 2's
point 6. The code is ten lines. The reason it must not change is the spec.
