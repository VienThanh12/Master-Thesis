// Specification invariants that the shared conformance vectors cannot express.
//
// The .vec transcript only carries the canonical result string of each op, so it
// can see a context's state, cell, DRB *count* and message counter, and nothing
// else. The properties below need the typed API: the fields the transcript never
// prints (security_key, rrc_transaction_id, per-DRB contents), the requirement
// that a rejected op mutates nothing at all (§6.1), the activity-sequence
// discipline (§10.3, §11.2), and the structural invariants of §10.1.

#include <atomic>
#include <cstdint>
#include <memory>
#include <vector>

#include "test_util.hpp"
#include "uecm/hash.hpp"
#include "uecm/shard_core.hpp"

using namespace uecm;

namespace {

// Reading .error() on a successful expected is undefined, so every negative
// assertion goes through this instead of dereferencing directly.
template <class T>
bool is_err(const OpResult<T>& r, OpError e) {
  return !r.has_value() && r.error() == e;
}

CreateParams keyed_params(std::uint32_t cell, std::uint8_t seed) {
  CreateParams p;
  p.serving_cell_id = cell;
  for (std::size_t i = 0; i < p.security_key.size(); ++i)
    p.security_key[i] = static_cast<std::uint8_t>(seed + i);
  return p;
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

// §6.1: "On any error, the context MUST remain unchanged (no partial mutation)."
// Every field is compared, including last_activity_seq: a rejected op must not
// consume a sequence number either.
void rejected_ops_do_not_mutate() {
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(Config{}, seq);

  CHECK(core.create_context(10, keyed_params(7, 0x40)).has_value());
  CHECK(core.setup_connection(10).has_value());
  CHECK(core.handle_signaling(10, SignalingMsg{1, 8, {}}).has_value());
  CHECK(core.add_drb(10, DrbEntry{1, 5, 111}).has_value());

  const UeContextView before = core.lookup(10).value();

  // Every operation that must be rejected from Connected.
  CHECK(is_err(core.setup_connection(10), OpError::InvalidState));
  CHECK(is_err(core.complete_reconfigure(10), OpError::InvalidState));
  CHECK(is_err(core.abort_reconfigure(10), OpError::InvalidState));
  CHECK(is_err(core.create_context(10, keyed_params(99, 0x99)), OpError::AlreadyExists));
  CHECK(is_err(core.handle_signaling(10, SignalingMsg{1, 65, {}}), OpError::InvalidArgument));
  CHECK(is_err(core.add_drb(10, DrbEntry{1, 0, 222}), OpError::AlreadyExists));

  CHECK(same_context(before, core.lookup(10).value()));

  // The same from Reconfiguring, where a rejected begin_reconfigure must not
  // commit its target cell.
  CHECK(core.begin_reconfigure(10, ReconfigParams{33}).has_value());
  const UeContextView mid = core.lookup(10).value();
  CHECK(mid.serving_cell_id == 33);
  CHECK(is_err(core.begin_reconfigure(10, ReconfigParams{44}), OpError::InvalidState));
  CHECK(is_err(core.setup_connection(10), OpError::InvalidState));
  CHECK(is_err(core.handle_signaling(10, SignalingMsg{1, 0, {}}), OpError::InvalidState));
  CHECK(is_err(core.add_drb(10, DrbEntry{2, 0, 0}), OpError::InvalidState));
  CHECK(same_context(mid, core.lookup(10).value()));
}

// §10.3 + §11.2: the sequence counter is stamped on successful mutations only,
// and per context the stamps are strictly increasing.
void activity_seq_discipline() {
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(Config{}, seq);

  CHECK(core.create_context(20, keyed_params(1, 0)).has_value());
  const std::uint64_t after_create = core.lookup(20).value().last_activity_seq;

  // Read-only ops must not stamp anything (§6.1).
  (void)core.lookup(20);
  (void)core.count();
  CHECK(core.lookup(20).value().last_activity_seq == after_create);

  // A rejected op must not stamp anything either.
  CHECK(is_err(core.handle_signaling(20, SignalingMsg{1, 0, {}}), OpError::InvalidState));
  CHECK(core.lookup(20).value().last_activity_seq == after_create);

  // Successful mutations advance the stamp, strictly, in order.
  std::uint64_t prev = after_create;
  CHECK(core.setup_connection(20).has_value());
  for (int i = 0; i < 5; ++i) {
    CHECK(core.handle_signaling(20, SignalingMsg{1, 4, {}}).has_value());
    const std::uint64_t now = core.lookup(20).value().last_activity_seq;
    CHECK(now > prev);
    prev = now;
  }
}

// §4.2/§4.4: the fields the conformance transcript never prints must survive a
// round trip through the store, and the DRB list must keep insertion order and
// its full contents (the transcript only shows drbs=<count>).
void context_fields_round_trip() {
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(Config{}, seq);

  const CreateParams p = keyed_params(4242, 0x80);
  CHECK(core.create_context(30, p).has_value());
  CHECK(core.setup_connection(30).has_value());

  for (std::uint8_t i = 0; i < static_cast<std::uint8_t>(MAX_DRBS); ++i) {
    CHECK(core.add_drb(30, DrbEntry{static_cast<std::uint8_t>(i + 1),
                                    static_cast<std::uint8_t>(i + 20),
                                    100u + i})
              .has_value());
  }

  const UeContextView v = core.lookup(30).value();
  CHECK(v.ue_id == 30);
  CHECK(v.serving_cell_id == 4242);
  CHECK(v.security_key == p.security_key);
  CHECK(v.rrc_transaction_id == 0);  // §4.3: zero on creation
  CHECK(v.drbs.size() == MAX_DRBS);
  for (std::size_t i = 0; i < v.drbs.size(); ++i) {
    CHECK(v.drbs[i].drb_id == static_cast<std::uint8_t>(i + 1));
    CHECK(v.drbs[i].qos_flow_id == static_cast<std::uint8_t>(i + 20));
    CHECK(v.drbs[i].teid == 100u + i);
  }

  // §10.1 I4: drb_ids are unique and the list never exceeds MAX_DRBS.
  for (std::size_t i = 0; i < v.drbs.size(); ++i)
    for (std::size_t j = i + 1; j < v.drbs.size(); ++j)
      CHECK(v.drbs[i].drb_id != v.drbs[j].drb_id);
  CHECK(is_err(core.add_drb(30, DrbEntry{99, 0, 0}), OpError::CapacityExceeded));
  CHECK(core.lookup(30).value().drbs.size() == MAX_DRBS);
}

// §4.4: lookup hands out a snapshot, never an alias into live shard state.
// Later mutations must not be visible through a view taken earlier. In C++ this
// is a property of the copy that has to be tested; in Rust the borrow checker
// makes the aliasing version not compile at all (see rust/tests/invariants.rs).
void lookup_returns_a_snapshot() {
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(Config{}, seq);

  CHECK(core.create_context(40, keyed_params(1, 0)).has_value());
  CHECK(core.setup_connection(40).has_value());
  CHECK(core.add_drb(40, DrbEntry{1, 1, 1}).has_value());
  const UeContextView snap = core.lookup(40).value();

  CHECK(core.handle_signaling(40, SignalingMsg{1, 0, {}}).has_value());
  CHECK(core.add_drb(40, DrbEntry{2, 2, 2}).has_value());
  CHECK(core.begin_reconfigure(40, ReconfigParams{777}).has_value());

  CHECK(snap.messages_handled == 0);
  CHECK(snap.drbs.size() == 1);
  CHECK(snap.state == UeState::Connected);
  CHECK(snap.serving_cell_id == 1);

  // The snapshot also survives the context being destroyed entirely.
  CHECK(core.release_context(40).has_value());
  CHECK(snap.ue_id == 40);
  CHECK(snap.drbs.size() == 1 && snap.drbs[0].teid == 1);
}

// §10.1 I1: every live ue_id is stored in exactly one shard, namely
// shard_index(ue_id). Routing is the service's job, so this drives a bank of
// ShardCores the way the service does and checks that no id is reachable
// anywhere else.
void ids_live_only_in_their_own_shard() {
  constexpr std::uint64_t kShards = 5;  // non-power-of-two on purpose
  std::atomic<std::uint64_t> seq{0};
  std::vector<std::unique_ptr<ShardCore>> cores;
  for (std::uint64_t i = 0; i < kShards; ++i)
    cores.push_back(std::make_unique<ShardCore>(Config{}, seq));

  constexpr std::uint64_t kIds = 500;
  for (std::uint64_t id = 1; id <= kIds; ++id) {
    const std::uint64_t owner = shard_index(id, kShards);
    CHECK(cores[owner]->create_context(id, keyed_params(0, 0)).has_value());
  }

  std::uint64_t total = 0;
  for (auto& c : cores) total += c->count();
  CHECK(total == kIds);

  for (std::uint64_t id = 1; id <= kIds; ++id) {
    const std::uint64_t owner = shard_index(id, kShards);
    std::uint64_t found = 0;
    for (std::uint64_t s = 0; s < kShards; ++s)
      if (cores[s]->lookup(id).has_value()) ++found;
    CHECK(found == 1);
    CHECK(cores[owner]->lookup(id).has_value());
  }
}

}  // namespace

int main() {
  rejected_ops_do_not_mutate();
  activity_seq_discipline();
  context_fields_round_trip();
  lookup_returns_a_snapshot();
  ids_live_only_in_their_own_shard();
  return uecm::test::summary("test_invariants");
}
