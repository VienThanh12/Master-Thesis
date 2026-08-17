#pragma once
// An open-addressed intra-shard map, built only to attribute a measured result.
//
// This is NOT part of the compared implementation. The reported C++ arm uses
// std::unordered_map, because the study compares each language as a developer
// actually finds it and a developer reaching for the standard hash map gets
// whichever one their language ships.
//
// The problem that leaves is attribution. The core operation measures faster in
// Rust, and the explanation offered for it is structural rather than measured:
// std::unordered_map is required by its iterator- and reference-stability
// guarantees to be node-based, so a lookup chases a pointer out of the bucket
// array, while Rust's HashMap is open-addressed and usually resolves a lookup
// within one cache line. That is an argument, and the thesis says confirming it
// would need cache-miss counters.
//
// Counters would be observational. This is the controlled version of the same
// question: hold the language fixed and change only the container. If the gap
// closes, the container was the cause; if it does not, the explanation was wrong
// and something else is going on. Neither outcome needs a PMU.
//
// Fairness notes, since this only means anything if the substitution is honest:
//   * the pinned FNV-1a hash is unchanged, so hashing cannot be the difference;
//   * capacity is a power of two with a 7/8 load factor and linear probing,
//     which is what Rust's hashbrown does, so the analogue is to Rust's actual
//     container rather than to open addressing in the abstract;
//   * nothing in the ShardCore API iterates the map, so replacing an unordered
//     container with a differently-unordered one cannot change any transcript.
//     Conformance is still run against it rather than assumed.
//
// Enable with -DUECM_FLAT_MAP=ON. Record any result in spec/SPECIFICATION.md §12.
#include <cstddef>
#include <cstdint>
#include <utility>
#include <vector>

namespace uecm {

template <class K, class V, class Hash>
class FlatMap {
 public:
  using value_type = std::pair<K, V>;

  // A pointer wrapper, so call sites keep using `it->second` and `it == end()`
  // and the substitution stays confined to this header.
  struct iterator {
    value_type* p = nullptr;
    value_type* operator->() const noexcept { return p; }
    value_type& operator*() const noexcept { return *p; }
    bool operator==(const iterator& o) const noexcept { return p == o.p; }
    bool operator!=(const iterator& o) const noexcept { return p != o.p; }
  };
  struct const_iterator {
    const value_type* p = nullptr;
    const value_type* operator->() const noexcept { return p; }
    const value_type& operator*() const noexcept { return *p; }
    bool operator==(const const_iterator& o) const noexcept { return p == o.p; }
    bool operator!=(const const_iterator& o) const noexcept { return p != o.p; }
  };

  FlatMap() { rehash(kMinCapacity); }

  std::size_t size() const noexcept { return size_; }

  void reserve(std::size_t n) {
    std::size_t want = kMinCapacity;
    // Grow until n entries fit under the load factor, so a reserve() big enough
    // for the workload means no rehash on the measured path.
    while (max_load(want) < n) want <<= 1;
    if (want > slots_.size()) rehash(want);
  }

  iterator end() noexcept { return iterator{nullptr}; }
  const_iterator end() const noexcept { return const_iterator{nullptr}; }

  iterator find(const K& key) noexcept {
    const std::size_t i = probe_find(key);
    return i == kNpos ? end() : iterator{&slots_[i].kv};
  }

  const_iterator find(const K& key) const noexcept {
    const std::size_t i = probe_find(key);
    return i == kNpos ? end() : const_iterator{&slots_[i].kv};
  }

  // Only ever called after a find() miss in ShardCore, but it re-checks anyway
  // so the container is correct on its own terms rather than only in context.
  void emplace(const K& key, V&& value) {
    if (size_ + tombstones_ + 1 > max_load(slots_.size())) grow();
    const std::size_t mask = slots_.size() - 1;
    std::size_t i = Hash{}(key)&mask;
    std::size_t first_tomb = kNpos;
    while (true) {
      Slot& s = slots_[i];
      if (s.state == kEmpty) {
        // Reuse an earlier tombstone if the probe passed one: it keeps the run
        // short, which is the whole point of the layout.
        const std::size_t at = first_tomb == kNpos ? i : first_tomb;
        if (first_tomb != kNpos) --tombstones_;
        slots_[at].kv.first = key;
        slots_[at].kv.second = std::move(value);
        slots_[at].state = kFull;
        ++size_;
        return;
      }
      if (s.state == kTomb && first_tomb == kNpos) first_tomb = i;
      if (s.state == kFull && s.kv.first == key) {
        s.kv.second = std::move(value);
        return;
      }
      i = (i + 1) & mask;
    }
  }

  void erase(iterator it) noexcept {
    if (it.p == nullptr) return;
    // The iterator points into the slot array, so the slot is recovered by
    // offset rather than by probing for the key a second time.
    Slot* base = slots_.data();
    const std::size_t idx =
        static_cast<std::size_t>(reinterpret_cast<Slot*>(
                                     reinterpret_cast<char*>(it.p) - offsetof(Slot, kv)) -
                                 base);
    slots_[idx].state = kTomb;
    slots_[idx].kv.second = V{};  // release any owned storage (UeContext::drbs)
    --size_;
    ++tombstones_;
  }

 private:
  enum : std::uint8_t { kEmpty = 0, kFull = 1, kTomb = 2 };
  struct Slot {
    value_type kv{};
    std::uint8_t state = kEmpty;
  };

  static constexpr std::size_t kMinCapacity = 16;
  static constexpr std::size_t kNpos = static_cast<std::size_t>(-1);

  // hashbrown's load factor, so the probe mirrors Rust's container rather than
  // an arbitrary choice that would make the comparison mean less.
  static std::size_t max_load(std::size_t cap) noexcept { return cap - cap / 8; }

  std::size_t probe_find(const K& key) const noexcept {
    const std::size_t mask = slots_.size() - 1;
    std::size_t i = Hash{}(key)&mask;
    while (true) {
      const Slot& s = slots_[i];
      if (s.state == kEmpty) return kNpos;
      if (s.state == kFull && s.kv.first == key) return i;
      i = (i + 1) & mask;
    }
  }

  void grow() {
    // Tombstones alone can fill the table without the live set growing, in which
    // case a rehash at the same capacity is enough to clear them.
    rehash(size_ + 1 > max_load(slots_.size()) / 2 ? slots_.size() << 1 : slots_.size());
  }

  void rehash(std::size_t new_cap) {
    std::vector<Slot> old;
    old.swap(slots_);
    slots_.assign(new_cap, Slot{});
    size_ = 0;
    tombstones_ = 0;
    for (Slot& s : old)
      if (s.state == kFull) emplace(s.kv.first, std::move(s.kv.second));
  }

  std::vector<Slot> slots_;
  std::size_t size_ = 0;
  std::size_t tombstones_ = 0;
};

}  // namespace uecm
