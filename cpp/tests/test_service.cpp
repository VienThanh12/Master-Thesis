#include <atomic>
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

// 2) Concurrent load across shards: disjoint ue_id ranges per producer thread,
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

int main() {
  functional();
  concurrent();
  return uecm::test::summary("test_service");
}
