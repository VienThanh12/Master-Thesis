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
// the caller blocks on the one-shot completion. The async methods expose that
// completion for benchmark clients that keep several requests in flight.
class Service {
 public:
  using Completion = std::future<TimedResponse>;

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

  Completion create_context_async(UeId ue_id, const CreateParams& params,
                                  bool stamp_completion = true);
  Completion setup_connection_async(UeId ue_id, bool stamp_completion = true);
  Completion handle_signaling_async(UeId ue_id, const SignalingMsg& msg,
                                    bool stamp_completion = true);
  Completion add_drb_async(UeId ue_id, const DrbEntry& drb,
                           bool stamp_completion = true);
  Completion begin_reconfigure_async(UeId ue_id, const ReconfigParams& params,
                                     bool stamp_completion = true);
  Completion complete_reconfigure_async(UeId ue_id, bool stamp_completion = true);
  Completion abort_reconfigure_async(UeId ue_id, bool stamp_completion = true);
  Completion release_context_async(UeId ue_id, bool stamp_completion = true);
  Completion lookup_async(UeId ue_id, bool stamp_completion = true);

  std::uint64_t n_shards() const noexcept { return cfg_.n_shards; }

 private:
  struct Shard {
    explicit Shard(const Config& cfg, std::atomic<std::uint64_t>& seq)
        : queue(cfg.queue_capacity), core(std::make_unique<ShardCore>(cfg, seq)) {}
    BoundedQueue<Request> queue;
    std::unique_ptr<ShardCore> core;
    std::thread worker;
  };

  Completion submit_async(OpKind kind, UeId ue_id, Request&& req);
  void worker_loop(Shard& shard);

  Config cfg_;
  std::atomic<std::uint64_t> activity_seq_{0};
  std::vector<std::unique_ptr<Shard>> shards_;
  bool running_ = false;
};

}  // namespace uecm
