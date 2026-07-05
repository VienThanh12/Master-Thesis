// Pinned synthetic RAN control-plane workload generator (spec §10, bench model).
//
// Models the UE lifecycle a gNB-CU-CP performs: attach (create -> setup), signaling
// activity, bearer setup (add_drb), handover (begin_reconfigure -> complete/abort),
// and release (detach). The generator is a pure, deterministic function of
// (active_ues, seed): it keeps a lightweight per-slot expected-state model so every
// emitted op is valid by construction, and it advances that model optimistically so
// the *sequence of op kinds* is identical in C++ and Rust for the same parameters.
// That makes the per-kind op counts a cross-language parity signal.
//
// PRNG draw order (MUST match the Rust generator exactly):
//   1 draw  -> slot = next() % active_ues
//   + if the slot is Connected or Reconfiguring: 1 more draw for the action roll.
// Empty/Idle slots consume no action draw (their transition is forced).

#pragma once
#include <cstdint>
#include <vector>

#include "uecm/config.hpp"

namespace bench {

struct SplitMix64 {
  std::uint64_t s;
  std::uint64_t next() {
    std::uint64_t z = (s += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
  }
};

enum class WKind : std::uint8_t {
  Create = 0,
  Setup = 1,
  Signal = 2,
  AddDrb = 3,
  BeginReconf = 4,
  CompleteReconf = 5,
  AbortReconf = 6,
  Release = 7,
};
inline constexpr int kWKindCount = 8;

struct WOp {
  WKind kind;
  std::uint64_t slot;
  std::uint8_t drb_id;
};

// Expected per-slot state (mirrors uecm::UeState plus an "Empty" for no context).
enum : std::uint8_t { kEmpty = 0, kIdle = 1, kConnected = 2, kReconfiguring = 3 };

class Workload {
 public:
  Workload(std::uint64_t active_ues, std::uint64_t seed)
      : n_(active_ues == 0 ? 1 : active_ues),
        rng_{seed},
        state_(n_, kEmpty),
        ndrbs_(n_, 0) {}

  WOp next() {
    const std::uint64_t slot = rng_.next() % n_;
    WOp op{WKind::Signal, slot, 0};
    switch (state_[slot]) {
      case kEmpty:
        op.kind = WKind::Create;
        state_[slot] = kIdle;
        break;
      case kIdle:
        op.kind = WKind::Setup;
        state_[slot] = kConnected;
        break;
      case kConnected: {
        const std::uint64_t r = rng_.next() % 100;
        if (r < 70) {
          op.kind = WKind::Signal;  // steady-state signaling dominates
        } else if (r < 80) {
          if (ndrbs_[slot] < uecm::MAX_DRBS) {
            op.kind = WKind::AddDrb;
            op.drb_id = ndrbs_[slot];
            ++ndrbs_[slot];
          } else {
            op.kind = WKind::Signal;
          }
        } else if (r < 95) {
          op.kind = WKind::BeginReconf;
          state_[slot] = kReconfiguring;
        } else {
          op.kind = WKind::Release;
          state_[slot] = kEmpty;
          ndrbs_[slot] = 0;
        }
        break;
      }
      case kReconfiguring:
      default: {
        const std::uint64_t r = rng_.next() % 100;
        op.kind = (r < 80) ? WKind::CompleteReconf : WKind::AbortReconf;
        state_[slot] = kConnected;
        break;
      }
    }
    return op;
  }

 private:
  std::uint64_t n_;
  SplitMix64 rng_;
  std::vector<std::uint8_t> state_;
  std::vector<std::uint8_t> ndrbs_;
};

}  // namespace bench
