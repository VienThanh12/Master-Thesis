#include <atomic>
#include <stdexcept>
#include <thread>
#include <vector>

#include "test_util.hpp"
#include "uecm/service.hpp"

using namespace uecm;

// 1) Functional path through the threaded service (spec §11.3).
static void functional() {
  Service svc(Config{});
  svc.start();

  CHECK(svc.create_context(1001, CreateParams{7, {}}).has_value());
  CHECK(svc.setup_connection(1001).has_value());
  auto ack = svc.handle_signaling(1001, SignalingMsg{3, 10, {}});
  CHECK(ack.has_value() && ack->accepted && ack->new_messages_handled == 1);
  auto bad = svc.setup_connection(1001);
  CHECK(!bad.has_value() && bad.error() == OpError::InvalidState);
  auto v = svc.lookup(1001);
  CHECK(v.has_value() && v->state == UeState::Connected);
  CHECK(svc.count() == 1);
  CHECK(svc.release_context(1001).has_value());
  CHECK(svc.count() == 0);

  svc.shutdown();
}

// 2) Multiple requests may remain in flight while preserving per-shard FIFO.
static void async_fifo() {
  Config cfg;
  cfg.n_shards = 1;
  cfg.queue_capacity = 2;
  Service svc(cfg);
  svc.start();

  auto create = svc.create_context_async(1001, CreateParams{7, {}});
  auto setup = svc.setup_connection_async(1001);
  auto signal = svc.handle_signaling_async(1001, SignalingMsg{3, 10, {}});

  auto created = create.get();
  auto connected = setup.get();
  auto signaled = signal.get();
  CHECK(std::get<OpResult<void>>(created.response).has_value());
  CHECK(std::get<OpResult<void>>(connected.response).has_value());
  const auto& ack = std::get<OpResult<SignalingAck>>(signaled.response);
  CHECK(ack.has_value() && ack->new_messages_handled == 1);
  CHECK(created.done <= connected.done && connected.done <= signaled.done);
  CHECK(created.started.time_since_epoch().count() == 0);
  CHECK(signaled.started.time_since_epoch().count() == 0);

  svc.shutdown();
}

// The diagnostic clock is taken after dequeue and before the operation.
// One shard keeps the two requests in order, so the first completion cannot
// follow the second start.
static void async_start_stamp() {
  Config cfg;
  cfg.n_shards = 1;
  cfg.stamp_start = true;
  Service svc(cfg);
  svc.start();
  CHECK(svc.create_context(1001, CreateParams{7, {}}).has_value());
  CHECK(svc.setup_connection(1001).has_value());

  auto first = svc.handle_signaling_async(1001, SignalingMsg{3, 10, {}});
  auto second = svc.handle_signaling_async(1001, SignalingMsg{3, 10, {}});
  auto a = first.get();
  auto b = second.get();
  CHECK(std::get<OpResult<SignalingAck>>(a.response).has_value());
  CHECK(std::get<OpResult<SignalingAck>>(b.response).has_value());
  CHECK(a.started.time_since_epoch().count() != 0);
  CHECK(a.started <= a.done);
  CHECK(a.done <= b.started);
  CHECK(b.started <= b.done);

  svc.shutdown();
}

// 3) Concurrent load across shards: disjoint ue_id ranges per producer thread,
//    so there are no cross-thread key conflicts; verifies routing + lifecycle
//    under real threads (run this binary under TSan to check data-race freedom).
static void concurrent() {
  Config cfg;
  cfg.n_shards = 8;
  cfg.queue_capacity = 256;  // smaller -> exercises blocking backpressure
  Service svc(cfg);
  svc.start();

  constexpr int kProducers = 8;
  constexpr std::uint64_t kPerProducer = 5000;
  std::atomic<std::uint64_t> errors{0};

  auto work = [&](int p) {
    const std::uint64_t base = static_cast<std::uint64_t>(p) * 1'000'000ULL + 1;
    for (std::uint64_t i = 0; i < kPerProducer; ++i) {
      UeId id = base + i;
      if (!svc.create_context(id, CreateParams{static_cast<std::uint32_t>(p), {}}))
        ++errors;
      if (!svc.setup_connection(id)) ++errors;
      for (int k = 0; k < 3; ++k)
        if (!svc.handle_signaling(id, SignalingMsg{1, 4, {}})) ++errors;
      auto v = svc.lookup(id);
      if (!v || v->messages_handled != 3) ++errors;
      // release the odd-numbered ids; keep the even ones alive
      if (i % 2 == 1)
        if (!svc.release_context(id)) ++errors;
    }
  };

  std::vector<std::thread> ts;
  for (int p = 0; p < kProducers; ++p) ts.emplace_back(work, p);
  for (auto& t : ts) t.join();

  CHECK(errors.load() == 0);
  // Half of each producer's ids survive (the even i).
  const std::uint64_t expected = kProducers * (kPerProducer / 2);
  CHECK(svc.count() == expected);

  svc.shutdown();
}

// 4) Spec §7.1: an operation outside the running window is a caller error, not an
//    OpError, and must fail immediately rather than reading shard state that does not
//    exist. Both cases were unguarded until 2026-08: before start() this indexed an
//    empty vector (segmentation fault), after shutdown() a cleared one
//    (heap-use-after-free under ASan). Mirrored by the two #[should_panic] cases in
//    rust/tests/concurrency.rs.
static void lifecycle_precondition() {
  auto throws = [](auto&& fn) {
    try {
      fn();
    } catch (const std::logic_error&) {
      return true;
    }
    return false;
  };

  Service before(Config{});
  CHECK(throws([&] { (void)before.create_context(1001, CreateParams{}); }));
  CHECK(throws([&] { (void)before.lookup(1001); }));
  CHECK(throws([&] { (void)before.count(); }));

  Service after(Config{});
  after.start();
  CHECK(after.create_context(1001, CreateParams{}).has_value());
  after.shutdown();
  CHECK(throws([&] { (void)after.release_context(1001); }));
  CHECK(throws([&] { (void)after.count(); }));
}

int main() {
  functional();
  async_fifo();
  async_start_stamp();
  concurrent();
  lifecycle_precondition();
  return uecm::test::summary("test_service");
}
