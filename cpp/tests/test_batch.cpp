// The batch probe's request (-DUECM_BATCH_PROBE=ON). Twin of rust/tests/batch_probe.rs.
#include <vector>

#include "test_util.hpp"
#include "uecm/hash.hpp"
#include "uecm/service.hpp"

using namespace uecm;

static std::vector<UeId> ids_on_shard(std::uint64_t shard, std::uint64_t n_shards, std::size_t count) {
  std::vector<UeId> ids;
  for (UeId id = 1; ids.size() < count; ++id)
    if (shard_index(id, n_shards) == shard) ids.push_back(id);
  return ids;
}

int main() {
  Config cfg;
  cfg.n_shards = 4;
  Service svc(cfg);
  svc.start();
  const std::vector<UeId> ids = ids_on_shard(2, 4, 4);
  for (std::size_t i = 0; i < 3; ++i) {
    CHECK(svc.create_context(ids[i], CreateParams{7, {}}).has_value());
    CHECK(svc.setup_connection(ids[i]).has_value());
  }
  const SignalingMsg msg{3, 10, {}};

  const auto all = svc.handle_signaling_batch({ids[0], ids[1], ids[2]}, msg);
  CHECK(all.has_value() && all->accepted && all->new_messages_handled == 3);

  // The fourth id was never created, so one of four fails.
  const auto some = svc.handle_signaling_batch(ids, msg);
  CHECK(some.has_value() && !some->accepted && some->new_messages_handled == 3);

  // Each successful operation in a batch is a real signalling call.
  const auto one = svc.handle_signaling(ids[0], msg);
  CHECK(one.has_value() && one->new_messages_handled == 3);

  const auto empty = svc.handle_signaling_batch({}, msg);
  CHECK(empty.has_value() && empty->accepted && empty->new_messages_handled == 0);
  svc.shutdown();
  return uecm::test::summary("test_batch");
}
