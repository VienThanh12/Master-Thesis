// Concurrency-model properties (spec §7 and §10.2).
//
// The conformance vectors run one operation at a time against the service, so
// they exercise the routing but say nothing about the queue and completion
// machinery underneath, which is exactly the part §7 specifies and the part the
// thesis compares between the two languages. These tests drive the service from
// several threads at once and assert the guarantees the spec makes about it:
// blocking backpressure loses nothing (§7.4-7.5), a shard executes its queue in
// FIFO order (§10.2 O1), and each request's completion goes to its own caller
// exactly once (§10.2 O3).
//
// Build this binary under ThreadSanitizer to also check data-race freedom; the
// Rust counterpart (rust/tests/concurrency.rs) needs no sanitizer for that.

#include <atomic>
#include <cstdint>
#include <thread>
#include <vector>

#include "test_util.hpp"
#include "uecm/hash.hpp"
#include "uecm/service.hpp"

using namespace uecm;

namespace {

// §7.4-7.5: the queue is bounded and a full queue blocks the producer rather
// than dropping or rejecting the request. With a capacity of one and more
// producers than shards, submission blocks constantly; every operation must
// still complete and the final population must be exact.
void backpressure_loses_nothing() {
  Config cfg;
  cfg.n_shards = 2;
  cfg.queue_capacity = 1;  // maximum backpressure
  Service svc(cfg);
  svc.start();

  constexpr int kProducers = 6;
  constexpr std::uint64_t kPerProducer = 400;
  std::atomic<std::uint64_t> errors{0};

  auto work = [&](int p) {
    const std::uint64_t base = static_cast<std::uint64_t>(p) * 100'000ULL + 1;
    for (std::uint64_t i = 0; i < kPerProducer; ++i) {
      const UeId id = base + i;
      if (!svc.create_context(id, CreateParams{1, {}})) ++errors;
      if (!svc.setup_connection(id)) ++errors;
      if (!svc.handle_signaling(id, SignalingMsg{1, 4, {}})) ++errors;
    }
  };

  std::vector<std::thread> ts;
  for (int p = 0; p < kProducers; ++p) ts.emplace_back(work, p);
  for (auto& t : ts) t.join();

  CHECK(errors.load() == 0);
  CHECK(svc.count() == kProducers * kPerProducer);
  svc.shutdown();
}

// §10.2 O1: a shard executes its queue strictly FIFO. Each acknowledgement
// carries the post-increment message count, so a caller issuing k-th signal on
// its own UE must see exactly k. Out-of-order execution or a completion handed
// to the wrong caller both show up as a wrong number here.
//
// All the ids are forced onto a single shard so the ordering claim is about one
// worker's queue rather than about independent workers.
void fifo_within_a_shard() {
  Config cfg;
  cfg.n_shards = 4;
  cfg.queue_capacity = 8;
  Service svc(cfg);
  svc.start();

  // Collect ids that all route to shard 0.
  std::vector<UeId> ids;
  for (UeId id = 1; ids.size() < 4; ++id)
    if (shard_index(id, cfg.n_shards) == 0) ids.push_back(id);
  for (UeId id : ids) CHECK(shard_index(id, cfg.n_shards) == 0);

  constexpr std::uint64_t kSignals = 300;
  std::atomic<std::uint64_t> errors{0};

  auto work = [&](UeId id) {
    if (!svc.create_context(id, CreateParams{1, {}})) ++errors;
    if (!svc.setup_connection(id)) ++errors;
    for (std::uint64_t k = 1; k <= kSignals; ++k) {
      auto ack = svc.handle_signaling(id, SignalingMsg{1, 0, {}});
      // The k-th signal on this context must be acknowledged as the k-th.
      if (!ack || !ack->accepted || ack->new_messages_handled != k) ++errors;
    }
  };

  std::vector<std::thread> ts;
  for (UeId id : ids) ts.emplace_back(work, id);
  for (auto& t : ts) t.join();

  CHECK(errors.load() == 0);
  for (UeId id : ids) {
    auto v = svc.lookup(id);
    CHECK(v.has_value() && v->messages_handled == kSignals);
  }
  svc.shutdown();
}

// Concurrent readers on the lookup path while a writer mutates the same
// context. Every snapshot must be internally consistent, and because the shard
// executes FIFO (O1) a single reader can never observe the counter going
// backwards.
void concurrent_lookups_are_consistent() {
  Config cfg;
  cfg.n_shards = 4;
  Service svc(cfg);
  svc.start();

  constexpr UeId kId = 4321;
  constexpr std::uint64_t kSignals = 2000;
  CHECK(svc.create_context(kId, CreateParams{9, {}}).has_value());
  CHECK(svc.setup_connection(kId).has_value());

  std::atomic<bool> done{false};
  std::atomic<std::uint64_t> errors{0};

  auto reader = [&]() {
    std::uint64_t seen = 0;
    while (!done.load(std::memory_order_relaxed)) {
      auto v = svc.lookup(kId);
      if (!v) { ++errors; continue; }
      // Field-level consistency of the snapshot.
      if (v->ue_id != kId || v->serving_cell_id != 9 ||
          v->state != UeState::Connected || v->messages_handled > kSignals)
        ++errors;
      // Per-reader monotonicity: lookups are submitted one after another to the
      // same shard, so FIFO execution forbids a decreasing counter.
      if (v->messages_handled < seen) ++errors;
      seen = v->messages_handled;
    }
  };

  std::vector<std::thread> readers;
  for (int i = 0; i < 3; ++i) readers.emplace_back(reader);

  for (std::uint64_t k = 0; k < kSignals; ++k)
    if (!svc.handle_signaling(kId, SignalingMsg{1, 0, {}})) ++errors;

  done.store(true);
  for (auto& t : readers) t.join();

  CHECK(errors.load() == 0);
  auto v = svc.lookup(kId);
  CHECK(v.has_value() && v->messages_handled == kSignals);
  svc.shutdown();
}

// §7.1 lifecycle, and the shard-count edge cases the default config hides:
// a single shard (every id on one worker) and a non-power-of-two shard count.
// n_shards = 0 is clamped to 1 by both implementations.
void lifecycle_and_shard_counts() {
  for (std::uint64_t n : {std::uint64_t{0}, std::uint64_t{1}, std::uint64_t{3},
                          std::uint64_t{7}}) {
    Config cfg;
    cfg.n_shards = n;
    Service svc(cfg);
    CHECK(svc.n_shards() == (n == 0 ? 1 : n));
    svc.start();
    svc.start();  // idempotent while running (§7.1)

    constexpr std::uint64_t kIds = 200;
    for (UeId id = 1; id <= kIds; ++id) {
      CHECK(svc.create_context(id, CreateParams{2, {}}).has_value());
      CHECK(svc.setup_connection(id).has_value());
    }
    CHECK(svc.count() == kIds);
    for (UeId id = 1; id <= kIds; id += 2) CHECK(svc.release_context(id).has_value());
    CHECK(svc.count() == kIds / 2);

    svc.shutdown();
    svc.shutdown();  // idempotent
  }
}

}  // namespace

int main() {
  backpressure_loses_nothing();
  fifo_within_a_shard();
  concurrent_lookups_are_consistent();
  lifecycle_and_shard_counts();
  return uecm::test::summary("test_concurrency");
}
