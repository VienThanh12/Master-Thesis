// Boundary case: leak through a reference cycle.
//
// Two UE contexts hold owning references to each other -- the shape that occurs
// whenever a context keeps a back-pointer to the peer it is being handed over
// to. Reference counting cannot collect a cycle: when the last external
// shared_ptr goes out of scope each object is still referenced by the other, so
// both counts stay at one and neither destructor ever runs.
//
// This is the cleanest possible statement of a guarantee boundary, because both
// languages fail in exactly the same way. Rust's Rc has the identical problem
// and leaking is safe in Rust by explicit design (mem::forget is a safe
// function). Whatever else ownership buys, it does not buy leak freedom.
//
// C++ detection: LeakSanitizer, which ships inside AddressSanitizer, reports
// the two allocations as unreachable at exit. See rust/leak_cycle.rs for the
// counterpart, where nothing in the default toolchain says anything at all.
#include <cstdio>
#include <memory>

struct UeContext;

// The leak is counted rather than asserted, and symmetrically with the Rust
// counterpart: a destructor that records itself is what lets the program state
// how many contexts were actually collected instead of claiming none were.
static int destroyed = 0;

struct UeContext {
  std::uint64_t ue_id;
  std::uint64_t messages_handled = 0;
  // Owning back-pointer to the handover peer: this is what closes the cycle.
  // A weak_ptr here would be the fix.
  std::shared_ptr<UeContext> peer;

  explicit UeContext(std::uint64_t id) : ue_id(id) {}
  ~UeContext() { ++destroyed; }
};

int main() {
  {
    auto src = std::make_shared<UeContext>(1001);
    auto dst = std::make_shared<UeContext>(1002);

    // Handover pairs the two contexts in both directions.
    src->peer = dst;
    dst->peer = src;

    src->messages_handled = 7;
    dst->messages_handled = 9;

    std::printf("paired %lu <-> %lu (use_count src=%ld dst=%ld)\n",
                static_cast<unsigned long>(src->ue_id),
                static_cast<unsigned long>(dst->ue_id),
                static_cast<long>(src.use_count()),
                static_cast<long>(dst.use_count()));
  }
  // Both roots are gone. Neither destructor ran, so both allocations are
  // unreachable and still live.
  std::printf("scope exited; contexts destroyed: %d of 2\n", destroyed);
  return destroyed == 2 ? 0 : 1;
}
