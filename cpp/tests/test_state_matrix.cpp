// The §5.2 transition matrix and the §6.6 error model, enumerated rather than
// sampled.
//
// The existing suites walk representative paths through the state machine:
// test_shard_core follows the §11.3 vector, test_invariants checks that the
// rejections it happens to try do not mutate. Both choose which cells to visit.
// This file visits all of them: every operation of §6 applied to a context in
// every condition it can be in, with the expected result written out as a table
// that can be read against the specification line by line. A transition that
// silently became permissive would have to survive a cell that asserts it does
// not.
//
// Three things are checked per cell:
//   1. the exact OpError (or success), from the table;
//   2. on success, the resulting state, so an op that returns Ok but moves the
//      context somewhere unspecified is caught;
//   3. on failure, that no field changed at all (§6.1), which the sampled
//      version could only claim for the rejections it listed.
//
// The last section pins the error precedences §6 leaves unordered. These are
// the cases where two errors are simultaneously true and the specification does
// not say which is reported; conformance vectors pin them at the transcript
// level, and these pin them at the typed-API level.
//
// Mirrors rust/tests/state_matrix.rs case for case.

#include <atomic>
#include <cstdint>
#include <optional>
#include <string>

#include "test_util.hpp"
#include "uecm/service.hpp"
#include "uecm/shard_core.hpp"

using namespace uecm;

namespace {

// --- the four conditions a context can be in --------------------------------
//
// Released is deliberately absent: §10.1 I2 says there is no resting Released
// context, so "released" is the same condition as Absent. That equivalence is
// asserted in released_is_not_a_resting_state() below rather than assumed.
enum Cond { kAbsent = 0, kIdle, kConnected, kReconfiguring, kNumConds };

const char* cond_name(int c) {
  switch (c) {
    case kAbsent:        return "Absent";
    case kIdle:          return "Idle";
    case kConnected:     return "Connected";
    case kReconfiguring: return "Reconfiguring";
  }
  return "?";
}

// --- the operations of §6 that take a ue_id ---------------------------------
//
// count() is the tenth operation but takes no id and cannot fail, so it is
// checked separately in count_tracks_live_contexts().
enum Op { kCreate = 0, kSetup, kSignal, kAddDrb, kBegin,
          kComplete, kAbort, kRelease, kLookup, kNumOps };

const char* op_name(int o) {
  switch (o) {
    case kCreate:   return "create_context";
    case kSetup:    return "setup_connection";
    case kSignal:   return "handle_signaling";
    case kAddDrb:   return "add_drb";
    case kBegin:    return "begin_reconfigure";
    case kComplete: return "complete_reconfigure";
    case kAbort:    return "abort_reconfigure";
    case kRelease:  return "release_context";
    case kLookup:   return "lookup";
  }
  return "?";
}

constexpr std::uint32_t kBaseCell = 700;
constexpr std::uint32_t kTargetCell = 900;

CreateParams params(std::uint32_t cell, std::uint8_t seed) {
  CreateParams p;
  p.serving_cell_id = cell;
  for (std::size_t i = 0; i < p.security_key.size(); ++i)
    p.security_key[i] = static_cast<std::uint8_t>(seed + i);
  return p;
}

// Apply one operation, discarding the payload: the matrix is about which error
// comes back, not what a successful call returns.
std::optional<OpError> apply(ShardCore& core, int op, UeId id) {
  auto err = [](auto&& r) -> std::optional<OpError> {
    if (r.has_value()) return std::nullopt;
    return r.error();
  };
  switch (op) {
    case kCreate:   return err(core.create_context(id, params(kBaseCell, 0x10)));
    case kSetup:    return err(core.setup_connection(id));
    case kSignal:   return err(core.handle_signaling(id, SignalingMsg{2, 8, {}}));
    case kAddDrb:   return err(core.add_drb(id, DrbEntry{3, 4, 5}));
    case kBegin:    return err(core.begin_reconfigure(id, ReconfigParams{kTargetCell}));
    case kComplete: return err(core.complete_reconfigure(id));
    case kAbort:    return err(core.abort_reconfigure(id));
    case kRelease:  return err(core.release_context(id));
    case kLookup:   return err(core.lookup(id));
  }
  return std::nullopt;
}

std::optional<OpError> apply(Service& svc, int op, UeId id) {
  auto err = [](auto&& r) -> std::optional<OpError> {
    if (r.has_value()) return std::nullopt;
    return r.error();
  };
  switch (op) {
    case kCreate:   return err(svc.create_context(id, params(kBaseCell, 0x10)));
    case kSetup:    return err(svc.setup_connection(id));
    case kSignal:   return err(svc.handle_signaling(id, SignalingMsg{2, 8, {}}));
    case kAddDrb:   return err(svc.add_drb(id, DrbEntry{3, 4, 5}));
    case kBegin:    return err(svc.begin_reconfigure(id, ReconfigParams{kTargetCell}));
    case kComplete: return err(svc.complete_reconfigure(id));
    case kAbort:    return err(svc.abort_reconfigure(id));
    case kRelease:  return err(svc.release_context(id));
    case kLookup:   return err(svc.lookup(id));
  }
  return std::nullopt;
}

// Drive a context into the requested condition. Uses only specified
// transitions, so a bug in the state machine shows up as a failed setup
// assertion rather than as a silently wrong starting point.
void arrange(ShardCore& core, UeId id, int cond) {
  if (cond == kAbsent) return;
  CHECK(core.create_context(id, params(kBaseCell, 0x10)).has_value());
  if (cond == kIdle) return;
  CHECK(core.setup_connection(id).has_value());
  if (cond == kConnected) return;
  CHECK(core.begin_reconfigure(id, ReconfigParams{kTargetCell}).has_value());
  CHECK(cond == kReconfiguring);
}

void arrange(Service& svc, UeId id, int cond) {
  if (cond == kAbsent) return;
  CHECK(svc.create_context(id, params(kBaseCell, 0x10)).has_value());
  if (cond == kIdle) return;
  CHECK(svc.setup_connection(id).has_value());
  if (cond == kConnected) return;
  CHECK(svc.begin_reconfigure(id, ReconfigParams{kTargetCell}).has_value());
}

bool same_context(const UeContextView& a, const UeContextView& b) {
  if (a.ue_id != b.ue_id || a.state != b.state ||
      a.serving_cell_id != b.serving_cell_id ||
      a.rrc_transaction_id != b.rrc_transaction_id ||
      a.security_key != b.security_key ||
      a.messages_handled != b.messages_handled ||
      a.last_activity_seq != b.last_activity_seq ||
      a.drbs.size() != b.drbs.size())
    return false;
  for (std::size_t i = 0; i < a.drbs.size(); ++i) {
    if (a.drbs[i].drb_id != b.drbs[i].drb_id ||
        a.drbs[i].qos_flow_id != b.drbs[i].qos_flow_id ||
        a.drbs[i].teid != b.drbs[i].teid)
      return false;
  }
  return true;
}

// --- the table --------------------------------------------------------------
//
// Read this against §5.2 (transitions) and §6.6 (error codes). std::nullopt is
// "succeeds". Rows are conditions, columns are operations.
constexpr std::optional<OpError> kExpected[kNumConds][kNumOps] = {
    // create                      setup                      signal
    // adddrb                      begin                      complete
    // abort                       release                    lookup
    /* Absent */
    {std::nullopt,                 OpError::NotFound,         OpError::NotFound,
     OpError::NotFound,            OpError::NotFound,         OpError::NotFound,
     OpError::NotFound,            OpError::NotFound,         OpError::NotFound},
    /* Idle */
    {OpError::AlreadyExists,       std::nullopt,              OpError::InvalidState,
     OpError::InvalidState,        OpError::InvalidState,     OpError::InvalidState,
     OpError::InvalidState,        std::nullopt,              std::nullopt},
    /* Connected */
    {OpError::AlreadyExists,       OpError::InvalidState,     std::nullopt,
     std::nullopt,                 std::nullopt,              OpError::InvalidState,
     OpError::InvalidState,        std::nullopt,              std::nullopt},
    /* Reconfiguring */
    {OpError::AlreadyExists,       OpError::InvalidState,     OpError::InvalidState,
     OpError::InvalidState,        OpError::InvalidState,     std::nullopt,
     std::nullopt,                 std::nullopt,              std::nullopt},
};

// The state a context is in after the operation succeeds. -1 means the context
// is gone; entries for cells that fail are never consulted.
constexpr int kPostState[kNumConds][kNumOps] = {
    /* Absent        */ {kIdle, -2, -2, -2, -2, -2, -2, -2, -2},
    /* Idle          */ {-2, kConnected, -2, -2, -2, -2, -2, -1, kIdle},
    /* Connected     */ {-2, -2, kConnected, kConnected, kReconfiguring, -2, -2, -1, kConnected},
    /* Reconfiguring */ {-2, -2, -2, -2, -2, kConnected, kConnected, -1, kReconfiguring},
};

int observed_cond(ShardCore& core, UeId id) {
  auto v = core.lookup(id);
  if (!v.has_value()) return -1;
  switch (v->state) {
    case UeState::Idle:          return kIdle;
    case UeState::Connected:     return kConnected;
    case UeState::Reconfiguring: return kReconfiguring;
    case UeState::Released:      return -3;  // §10.1 I2 forbids this
  }
  return -3;
}

// --- cases ------------------------------------------------------------------

// Every (condition, operation) pair, on a fresh core so no cell can be
// influenced by the one before it.
void every_cell_of_the_transition_matrix() {
  constexpr UeId kId = 4242;

  for (int cond = 0; cond < kNumConds; ++cond) {
    for (int op = 0; op < kNumOps; ++op) {
      std::atomic<std::uint64_t> seq{0};
      ShardCore core(Config{}, seq);
      arrange(core, kId, cond);

      const bool had_context = (cond != kAbsent);
      const UeContextView before =
          had_context ? core.lookup(kId).value() : UeContextView{};
      const std::uint64_t count_before = core.count();

      const std::optional<OpError> got = apply(core, op, kId);
      const std::optional<OpError> want = kExpected[cond][op];

      const bool matched = (got.has_value() == want.has_value()) &&
                           (!got.has_value() || *got == *want);
      if (!matched) {
        std::fprintf(stderr, "  matrix[%s][%s]: expected %s, got %s\n",
                     cond_name(cond), op_name(op),
                     want ? std::string(to_string(*want)).c_str() : "Ok",
                     got ? std::string(to_string(*got)).c_str() : "Ok");
      }
      CHECK(matched);

      if (!got.has_value()) {
        // Succeeded: the context must be exactly where §5.2 says.
        CHECK(observed_cond(core, kId) == kPostState[cond][op]);
        if (op == kRelease) CHECK(core.count() == count_before - 1);
        if (op == kCreate)  CHECK(core.count() == count_before + 1);
      } else {
        // Failed: §6.1 requires the context to be untouched, and a rejected op
        // must not create or destroy one either.
        CHECK(core.count() == count_before);
        if (had_context) {
          auto after = core.lookup(kId);
          CHECK(after.has_value());
          if (after.has_value()) CHECK(same_context(before, after.value()));
        } else {
          CHECK(!core.lookup(kId).has_value());
        }
      }
    }
  }
}

// §6.1: ue_id == 0 is rejected with InvalidArgument for every operation, and
// the rejection happens before anything else is considered.
void ue_id_zero_is_rejected_everywhere() {
  for (int op = 0; op < kNumOps; ++op) {
    std::atomic<std::uint64_t> seq{0};
    ShardCore core(Config{}, seq);
    // A populated shard, so the rejection is not an artefact of an empty map.
    CHECK(core.create_context(1, params(1, 0)).has_value());
    CHECK(core.setup_connection(1).has_value());

    const std::optional<OpError> got = apply(core, op, 0);
    CHECK(got.has_value() && *got == OpError::InvalidArgument);
    CHECK(core.count() == 1);
  }
}

// The same matrix through the threaded facade. Routing, queueing and the
// completion handoff must not change any result; the transcript vectors show
// this for the paths they walk, this shows it for all 36 cells.
void the_service_facade_preserves_the_matrix() {
  constexpr UeId kId = 4242;

  for (int cond = 0; cond < kNumConds; ++cond) {
    for (int op = 0; op < kNumOps; ++op) {
      Service svc(Config{});
      svc.start();
      arrange(svc, kId, cond);

      const std::optional<OpError> got = apply(svc, op, kId);
      const std::optional<OpError> want = kExpected[cond][op];
      const bool matched = (got.has_value() == want.has_value()) &&
                           (!got.has_value() || *got == *want);
      if (!matched) {
        std::fprintf(stderr, "  service matrix[%s][%s] disagrees with core\n",
                     cond_name(cond), op_name(op));
      }
      CHECK(matched);
      svc.shutdown();
    }
  }
}

// §10.1 I2: Released is transient-terminal. After release the context is gone,
// not sitting in a fourth observable state, so every operation behaves exactly
// as it does for a context that never existed.
void released_is_not_a_resting_state() {
  constexpr UeId kId = 77;
  for (int op = 0; op < kNumOps; ++op) {
    std::atomic<std::uint64_t> seq{0};
    ShardCore core(Config{}, seq);
    CHECK(core.create_context(kId, params(kBaseCell, 0x10)).has_value());
    CHECK(core.setup_connection(kId).has_value());
    CHECK(core.release_context(kId).has_value());
    CHECK(core.count() == 0);

    const std::optional<OpError> got = apply(core, op, kId);
    const std::optional<OpError> want = kExpected[kAbsent][op];
    CHECK((got.has_value() == want.has_value()) &&
          (!got.has_value() || *got == *want));
  }
}

// §6.6 read as a closed set: count() is the one operation with no id and no
// failure mode, so it is checked here rather than in the matrix.
void count_tracks_live_contexts() {
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(Config{}, seq);
  CHECK(core.count() == 0);

  for (UeId id = 1; id <= 10; ++id) {
    CHECK(core.create_context(id, params(1, 0)).has_value());
    CHECK(core.count() == id);
  }
  // Failed creates must not move it.
  CHECK(!core.create_context(5, params(1, 0)).has_value());
  CHECK(!core.create_context(0, params(1, 0)).has_value());
  CHECK(core.count() == 10);

  for (UeId id = 1; id <= 10; ++id) {
    CHECK(core.release_context(id).has_value());
    CHECK(core.count() == 10 - id);
  }
  CHECK(!core.release_context(1).has_value());
  CHECK(core.count() == 0);
}

// --- error precedence -------------------------------------------------------
//
// §6 lists each operation's errors as a set, so where two are true at once it
// does not say which is reported. Both implementations already agree on all
// four orderings; these exist so the agreement cannot drift unnoticed.

// Argument validation runs before the key lookup: an oversized payload on an
// id that does not exist is InvalidArgument, not NotFound.
void argument_checks_precede_key_lookup() {
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(Config{}, seq);

  auto r = core.handle_signaling(999, SignalingMsg{1, 65, {}});
  CHECK(!r.has_value() && r.error() == OpError::InvalidArgument);

  // ... and before the state check, on a context that exists but is Idle.
  CHECK(core.create_context(1, params(1, 0)).has_value());
  auto r2 = core.handle_signaling(1, SignalingMsg{1, 65, {}});
  CHECK(!r2.has_value() && r2.error() == OpError::InvalidArgument);

  // The boundary itself: 64 is accepted, 65 is not (§6.4).
  CHECK(core.setup_connection(1).has_value());
  CHECK(core.handle_signaling(1, SignalingMsg{1, 64, {}}).has_value());
  auto r3 = core.handle_signaling(1, SignalingMsg{1, 65, {}});
  CHECK(!r3.has_value() && r3.error() == OpError::InvalidArgument);
  // The rejected oversized message must not have been counted.
  CHECK(core.lookup(1).value().messages_handled == 1);
}

// create_context checks shard capacity before duplicate detection, so creating
// an id that already exists on a full shard reports CapacityExceeded.
void capacity_precedes_duplicate_on_create() {
  Config cfg;
  cfg.max_contexts_per_shard = 2;
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(cfg, seq);

  CHECK(core.create_context(1, params(1, 0)).has_value());
  CHECK(core.create_context(2, params(1, 0)).has_value());

  // Shard is full. A fresh id and an existing id both report the capacity
  // error; the duplicate never gets as far as being noticed.
  auto fresh = core.create_context(3, params(1, 0));
  CHECK(!fresh.has_value() && fresh.error() == OpError::CapacityExceeded);
  auto dup = core.create_context(1, params(9, 9));
  CHECK(!dup.has_value() && dup.error() == OpError::CapacityExceeded);

  // And the existing context was not overwritten by the rejected create.
  CHECK(core.lookup(1).value().serving_cell_id == 1);
}

// add_drb checks the state first, then the DRB cap, then duplicate drb_id.
void add_drb_precedence_is_state_then_capacity_then_duplicate() {
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(Config{}, seq);
  CHECK(core.create_context(1, params(1, 0)).has_value());
  CHECK(core.setup_connection(1).has_value());

  for (std::uint8_t i = 0; i < static_cast<std::uint8_t>(MAX_DRBS); ++i)
    CHECK(core.add_drb(1, DrbEntry{static_cast<std::uint8_t>(i + 1), 0, i}).has_value());

  // Full list. A new drb_id is CapacityExceeded, which the existing suite
  // covers; an *existing* drb_id is also CapacityExceeded, which it does not.
  auto fresh = core.add_drb(1, DrbEntry{99, 0, 0});
  CHECK(!fresh.has_value() && fresh.error() == OpError::CapacityExceeded);
  auto dup = core.add_drb(1, DrbEntry{1, 0, 0});
  CHECK(!dup.has_value() && dup.error() == OpError::CapacityExceeded);
  CHECK(core.lookup(1).value().drbs.size() == MAX_DRBS);

  // With the list still full, leaving Connected makes the state error win over
  // the capacity error.
  CHECK(core.begin_reconfigure(1, ReconfigParams{2}).has_value());
  auto wrong_state = core.add_drb(1, DrbEntry{1, 0, 0});
  CHECK(!wrong_state.has_value() && wrong_state.error() == OpError::InvalidState);

  // Duplicate detection does still fire when the list has room.
  CHECK(core.complete_reconfigure(1).has_value());
  CHECK(core.release_context(1).has_value());
  CHECK(core.create_context(2, params(1, 0)).has_value());
  CHECK(core.setup_connection(2).has_value());
  CHECK(core.add_drb(2, DrbEntry{7, 0, 0}).has_value());
  auto real_dup = core.add_drb(2, DrbEntry{7, 1, 1});
  CHECK(!real_dup.has_value() && real_dup.error() == OpError::AlreadyExists);
  CHECK(core.lookup(2).value().drbs.size() == 1);
}

// §5.2 calls abort the path where state is "restored", but begin_reconfigure
// has already overwritten serving_cell_id and neither implementation rolls it
// back. states.vec pins this at the transcript level; pinned here too, because
// it is the one place the specification's wording and the behaviour differ.
void abort_restores_state_but_not_the_cell() {
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(Config{}, seq);
  CHECK(core.create_context(1, params(kBaseCell, 0)).has_value());
  CHECK(core.setup_connection(1).has_value());
  CHECK(core.lookup(1).value().serving_cell_id == kBaseCell);

  CHECK(core.begin_reconfigure(1, ReconfigParams{kTargetCell}).has_value());
  CHECK(core.lookup(1).value().serving_cell_id == kTargetCell);

  CHECK(core.abort_reconfigure(1).has_value());
  CHECK(core.lookup(1).value().state == UeState::Connected);
  CHECK(core.lookup(1).value().serving_cell_id == kTargetCell);  // not kBaseCell

  // complete_reconfigure leaves it in the same place, so the two paths differ
  // only in name.
  CHECK(core.begin_reconfigure(1, ReconfigParams{kBaseCell}).has_value());
  CHECK(core.complete_reconfigure(1).has_value());
  CHECK(core.lookup(1).value().serving_cell_id == kBaseCell);
}

}  // namespace

int main() {
  every_cell_of_the_transition_matrix();
  ue_id_zero_is_rejected_everywhere();
  the_service_facade_preserves_the_matrix();
  released_is_not_a_resting_state();
  count_tracks_live_contexts();
  argument_checks_precede_key_lookup();
  capacity_precedes_duplicate_on_create();
  add_drb_precedence_is_state_then_capacity_then_duplicate();
  abort_restores_state_but_not_the_cell();
  return uecm::test::summary("test_state_matrix");
}
