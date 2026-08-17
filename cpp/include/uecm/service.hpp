#pragma once
#include <atomic>
#include <cstdint>
#include <memory>
#include <thread>
#include <vector>

#include "uecm/bounded_queue.hpp"
#include "uecm/config.hpp"
#include "uecm/error.hpp"
#include "uecm/message.hpp"
#include "uecm/shard_core.hpp"
#include "uecm/types.hpp"

namespace uecm {

// The threaded UE Context Management service (spec §7): shared-nothing,
// thread-per-shard. Callers use the typed API below; each call is routed to the
// owning shard's queue and executed by that shard's single worker thread, and
// the caller blocks on the one-shot completion.
class Service {
 public:
  explicit Service(const Config& cfg = {});
  ~Service();

  Service(const Service&) = delete;
  Service& operator=(const Service&) = delete;

  void start();     // spawn one worker per shard
  void shutdown();   // drain, stop workers, join (idempotent)

  // Typed API (spec §6). Each call blocks until its completion is signaled.
  // Precondition (§7.1): the service is running. Calling before start() or after
  // shutdown() throws std::logic_error; it is not an OpError, which stays the
  // closed five-value set of §6.6.
  OpResult<void>          create_context(UeId ue_id, const CreateParams& params);
  OpResult<void>          setup_connection(UeId ue_id);
  OpResult<SignalingAck>  handle_signaling(UeId ue_id, const SignalingMsg& msg);
  OpResult<void>          add_drb(UeId ue_id, const DrbEntry& drb);
  OpResult<void>          begin_reconfigure(UeId ue_id, const ReconfigParams& params);
  OpResult<void>          complete_reconfigure(UeId ue_id);
  OpResult<void>          abort_reconfigure(UeId ue_id);
  OpResult<void>          release_context(UeId ue_id);
  OpResult<UeContextView> lookup(UeId ue_id);
  std::uint64_t           count();  // sum across shards (routed per shard)

  std::uint64_t n_shards() const noexcept { return cfg_.n_shards; }

 private:
  struct Shard {
    explicit Shard(const Config& cfg, std::atomic<std::uint64_t>& seq)
        : queue(cfg.queue_capacity), core(std::make_unique<ShardCore>(cfg, seq)) {}
    BoundedQueue<Request> queue;
    std::unique_ptr<ShardCore> core;
    std::thread worker;
  };

  Response submit(OpKind kind, UeId ue_id, Request&& req);
  void worker_loop(Shard& shard);

  Config cfg_;
  std::atomic<std::uint64_t> activity_seq_{0};
  std::vector<std::unique_ptr<Shard>> shards_;
  bool running_ = false;
};

}  // namespace uecm
