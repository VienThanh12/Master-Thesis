#include "uecm/service.hpp"

#include <stdexcept>
#include <utility>
#include <variant>

#include "uecm/hash.hpp"

namespace uecm {
namespace {
// Spec §7.1: operating outside the running window is a caller error, not one of
// the five OpError codes, so it is reported out of band rather than widening the
// closed error set.
constexpr const char* kNotRunning =
    "uecm::Service: operation submitted while the service is not running (spec §7.1)";
}  // namespace

Service::Service(const Config& cfg) : cfg_(cfg) {
  if (cfg_.n_shards == 0) cfg_.n_shards = 1;
}

Service::~Service() { shutdown(); }

void Service::start() {
  if (running_) return;
  shards_.clear();
  shards_.reserve(cfg_.n_shards);
  for (std::uint64_t i = 0; i < cfg_.n_shards; ++i)
    shards_.push_back(std::make_unique<Shard>(cfg_, activity_seq_));
  running_ = true;
  for (auto& s : shards_) {
    Shard& shard = *s;
    shard.worker = std::thread([this, &shard] { worker_loop(shard); });
  }
}

void Service::shutdown() {
  if (!running_) return;
  for (auto& s : shards_) {
    Request stop;
    stop.kind = OpKind::Stop;
    s->queue.push(std::move(stop));  // FIFO: drains prior requests first
  }
  for (auto& s : shards_)
    if (s->worker.joinable()) s->worker.join();
  running_ = false;
  shards_.clear();
}

void Service::worker_loop(Shard& shard) {
  ShardCore& core = *shard.core;
  for (;;) {
    Request req = shard.queue.pop();
    // One clock read, and only for a diagnostic run. It sits after the request
    // has left the queue and before the shard operation.
    const auto started = cfg_.stamp_start ? std::chrono::steady_clock::now()
                                          : std::chrono::steady_clock::time_point{};
    auto complete = [&req, started](Response response) {
      req.completion.set_value(TimedResponse{
          std::move(response),
          req.stamp_completion ? std::chrono::steady_clock::now()
                               : std::chrono::steady_clock::time_point{},
          started});
    };
    switch (req.kind) {
      case OpKind::CreateContext:
        complete(core.create_context(req.ue_id, req.create_params));
        break;
      case OpKind::SetupConnection:
        complete(core.setup_connection(req.ue_id));
        break;
      case OpKind::HandleSignaling:
        complete(core.handle_signaling(req.ue_id, req.signaling));
        break;
      case OpKind::AddDrb:
        complete(core.add_drb(req.ue_id, req.drb));
        break;
      case OpKind::BeginReconfigure:
        complete(core.begin_reconfigure(req.ue_id, req.reconfig));
        break;
      case OpKind::CompleteReconfigure:
        complete(core.complete_reconfigure(req.ue_id));
        break;
      case OpKind::AbortReconfigure:
        complete(core.abort_reconfigure(req.ue_id));
        break;
      case OpKind::ReleaseContext:
        complete(core.release_context(req.ue_id));
        break;
      case OpKind::Lookup:
        complete(core.lookup(req.ue_id));
        break;
      case OpKind::Count:
        complete(OpResult<std::uint64_t>(core.count()));
        break;
      case OpKind::Stop:
        return;
    }
  }
}

Service::Completion Service::submit_async(OpKind kind, UeId ue_id, Request&& req) {
  if (!running_) throw std::logic_error(kNotRunning);
  req.kind = kind;
  req.ue_id = ue_id;
  auto fut = req.completion.get_future();
  std::uint64_t s = shard_index(ue_id, cfg_.n_shards);
  shards_[s]->queue.push(std::move(req));
  return fut;
}

// --- Typed API ----------------------------------------------------------------

Service::Completion Service::create_context_async(UeId ue_id, const CreateParams& params,
                                                   bool stamp_completion) {
  Request req;
  req.create_params = params;
  req.stamp_completion = stamp_completion;
  return submit_async(OpKind::CreateContext, ue_id, std::move(req));
}

Service::Completion Service::setup_connection_async(UeId ue_id, bool stamp_completion) {
  Request req;
  req.stamp_completion = stamp_completion;
  return submit_async(OpKind::SetupConnection, ue_id, std::move(req));
}

Service::Completion Service::handle_signaling_async(UeId ue_id, const SignalingMsg& msg,
                                                     bool stamp_completion) {
  Request req;
  req.signaling = msg;
  req.stamp_completion = stamp_completion;
  return submit_async(OpKind::HandleSignaling, ue_id, std::move(req));
}

Service::Completion Service::add_drb_async(UeId ue_id, const DrbEntry& drb,
                                            bool stamp_completion) {
  Request req;
  req.drb = drb;
  req.stamp_completion = stamp_completion;
  return submit_async(OpKind::AddDrb, ue_id, std::move(req));
}

Service::Completion Service::begin_reconfigure_async(UeId ue_id, const ReconfigParams& params,
                                                      bool stamp_completion) {
  Request req;
  req.reconfig = params;
  req.stamp_completion = stamp_completion;
  return submit_async(OpKind::BeginReconfigure, ue_id, std::move(req));
}

Service::Completion Service::complete_reconfigure_async(UeId ue_id, bool stamp_completion) {
  Request req;
  req.stamp_completion = stamp_completion;
  return submit_async(OpKind::CompleteReconfigure, ue_id, std::move(req));
}

Service::Completion Service::abort_reconfigure_async(UeId ue_id, bool stamp_completion) {
  Request req;
  req.stamp_completion = stamp_completion;
  return submit_async(OpKind::AbortReconfigure, ue_id, std::move(req));
}

Service::Completion Service::release_context_async(UeId ue_id, bool stamp_completion) {
  Request req;
  req.stamp_completion = stamp_completion;
  return submit_async(OpKind::ReleaseContext, ue_id, std::move(req));
}

Service::Completion Service::lookup_async(UeId ue_id, bool stamp_completion) {
  Request req;
  req.stamp_completion = stamp_completion;
  return submit_async(OpKind::Lookup, ue_id, std::move(req));
}

OpResult<void> Service::create_context(UeId ue_id, const CreateParams& params) {
  return std::get<OpResult<void>>(create_context_async(ue_id, params, false).get().response);
}

OpResult<void> Service::setup_connection(UeId ue_id) {
  return std::get<OpResult<void>>(setup_connection_async(ue_id, false).get().response);
}

OpResult<SignalingAck> Service::handle_signaling(UeId ue_id, const SignalingMsg& msg) {
  return std::get<OpResult<SignalingAck>>(
      handle_signaling_async(ue_id, msg, false).get().response);
}

OpResult<void> Service::add_drb(UeId ue_id, const DrbEntry& drb) {
  return std::get<OpResult<void>>(add_drb_async(ue_id, drb, false).get().response);
}

OpResult<void> Service::begin_reconfigure(UeId ue_id, const ReconfigParams& params) {
  return std::get<OpResult<void>>(
      begin_reconfigure_async(ue_id, params, false).get().response);
}

OpResult<void> Service::complete_reconfigure(UeId ue_id) {
  return std::get<OpResult<void>>(complete_reconfigure_async(ue_id, false).get().response);
}

OpResult<void> Service::abort_reconfigure(UeId ue_id) {
  return std::get<OpResult<void>>(abort_reconfigure_async(ue_id, false).get().response);
}

OpResult<void> Service::release_context(UeId ue_id) {
  return std::get<OpResult<void>>(release_context_async(ue_id, false).get().response);
}

OpResult<UeContextView> Service::lookup(UeId ue_id) {
  return std::get<OpResult<UeContextView>>(lookup_async(ue_id, false).get().response);
}

std::uint64_t Service::count() {
  if (!running_) throw std::logic_error(kNotRunning);
  std::uint64_t total = 0;
  for (std::uint64_t i = 0; i < cfg_.n_shards; ++i) {
    Request req;
    req.kind = OpKind::Count;
    auto fut = req.completion.get_future();
    shards_[i]->queue.push(std::move(req));
    total += std::get<OpResult<std::uint64_t>>(fut.get().response).value();
  }
  return total;
}

}  // namespace uecm
