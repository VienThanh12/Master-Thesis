#include <atomic>

#include "test_util.hpp"
#include "uecm/shard_core.hpp"

using namespace uecm;

int main() {
  Config cfg;
  std::atomic<std::uint64_t> seq{0};
  ShardCore core(cfg, seq);

  // --- Spec §11.3 example vector -------------------------------------------
  CHECK(core.create_context(1001, CreateParams{7, {}}).has_value());
  CHECK(core.setup_connection(1001).has_value());

  auto ack = core.handle_signaling(1001, SignalingMsg{3, 10, {}});
  CHECK(ack.has_value());
  CHECK(ack->accepted);
  CHECK(ack->new_messages_handled == 1);

  auto bad_setup = core.setup_connection(1001);  // not Idle
  CHECK(!bad_setup.has_value() && bad_setup.error() == OpError::InvalidState);

  auto v = core.lookup(1001);
  CHECK(v.has_value());
  CHECK(v->state == UeState::Connected);
  CHECK(v->drbs.empty());
  CHECK(v->messages_handled == 1);

  CHECK(core.release_context(1001).has_value());
  auto rel2 = core.release_context(1001);  // double release
  CHECK(!rel2.has_value() && rel2.error() == OpError::NotFound);
  CHECK(core.count() == 0);

  // --- Error model ----------------------------------------------------------
  auto e0 = core.create_context(0, {});  // reserved id
  CHECK(!e0.has_value() && e0.error() == OpError::InvalidArgument);

  auto nf = core.setup_connection(42);  // absent
  CHECK(!nf.has_value() && nf.error() == OpError::NotFound);

  CHECK(core.create_context(2002, {}).has_value());
  auto dup = core.create_context(2002, {});
  CHECK(!dup.has_value() && dup.error() == OpError::AlreadyExists);

  // signaling requires Connected
  auto sig_idle = core.handle_signaling(2002, SignalingMsg{1, 0, {}});
  CHECK(!sig_idle.has_value() && sig_idle.error() == OpError::InvalidState);

  // oversized payload
  CHECK(core.setup_connection(2002).has_value());
  auto big = core.handle_signaling(2002, SignalingMsg{1, 65, {}});
  CHECK(!big.has_value() && big.error() == OpError::InvalidArgument);

  // --- DRBs -----------------------------------------------------------------
  CHECK(core.add_drb(2002, DrbEntry{1, 9, 100}).has_value());  // drbs = 1
  auto dup_drb = core.add_drb(2002, DrbEntry{1, 9, 101});       // same drb_id
  CHECK(!dup_drb.has_value() && dup_drb.error() == OpError::AlreadyExists);
  // Fill up to MAX_DRBS total (ids 2..MAX_DRBS add MAX_DRBS-1 more).
  for (std::uint8_t i = 2; i <= static_cast<std::uint8_t>(MAX_DRBS); ++i) {
    CHECK(core.add_drb(2002, DrbEntry{i, 0, i}).has_value());
  }
  auto overflow = core.add_drb(2002, DrbEntry{99, 0, 0});  // beyond MAX_DRBS
  CHECK(!overflow.has_value() && overflow.error() == OpError::CapacityExceeded);

  // --- Reconfiguration flow -------------------------------------------------
  CHECK(core.begin_reconfigure(2002, ReconfigParams{55}).has_value());
  auto sig_recfg = core.handle_signaling(2002, SignalingMsg{1, 0, {}});  // not Connected
  CHECK(!sig_recfg.has_value() && sig_recfg.error() == OpError::InvalidState);
  CHECK(core.complete_reconfigure(2002).has_value());
  auto v2 = core.lookup(2002);
  CHECK(v2.has_value() && v2->state == UeState::Connected && v2->serving_cell_id == 55);

  return uecm::test::summary("test_shard_core");
}
