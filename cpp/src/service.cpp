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
    switch (req.kind) {
      case OpKind::CreateContext:
        req.completion.set_value(core.create_context(req.ue_id, req.create_params));
        break;
      case OpKind::SetupConnection:
        req.completion.set_value(core.setup_connection(req.ue_id));
        break;
      case OpKind::HandleSignaling:
        req.completion.set_value(core.handle_signaling(req.ue_id, req.signaling));
        break;
      case OpKind::AddDrb:
        req.completion.set_value(core.add_drb(req.ue_id, req.drb));
        break;
      case OpKind::BeginReconfigure:
        req.completion.set_value(core.begin_reconfigure(req.ue_id, req.reconfig));
        break;
      case OpKind::CompleteReconfigure:
        req.completion.set_value(core.complete_reconfigure(req.ue_id));
        break;
      case OpKind::AbortReconfigure:
        req.completion.set_value(core.abort_reconfigure(req.ue_id));
        break;
      case OpKind::ReleaseContext:
        req.completion.set_value(core.release_context(req.ue_id));
        break;
      case OpKind::Lookup:
        req.completion.set_value(core.lookup(req.ue_id));
        break;
      case OpKind::Count:
        req.completion.set_value(OpResult<std::uint64_t>(core.count()));
        break;
      case OpKind::Stop:
        return;
    }
  }
}

Response Service::submit(OpKind kind, UeId ue_id, Request&& req) {
  if (!running_) throw std::logic_error(kNotRunning);
  req.kind = kind;
  req.ue_id = ue_id;
  auto fut = req.completion.get_future();
  std::uint64_t s = shard_index(ue_id, cfg_.n_shards);
  shards_[s]->queue.push(std::move(req));
  return fut.get();
}

// --- Typed API ----------------------------------------------------------------

OpResult<void> Service::create_context(UeId ue_id, const CreateParams& params) {
  Request req;
  req.create_params = params;
  return std::get<OpResult<void>>(submit(OpKind::CreateContext, ue_id, std::move(req)));
}

OpResult<void> Service::setup_connection(UeId ue_id) {
  Request req;
  return std::get<OpResult<void>>(submit(OpKind::SetupConnection, ue_id, std::move(req)));
}

OpResult<SignalingAck> Service::handle_signaling(UeId ue_id, const SignalingMsg& msg) {
  Request req;
  req.signaling = msg;
  return std::get<OpResult<SignalingAck>>(
      submit(OpKind::HandleSignaling, ue_id, std::move(req)));
}

OpResult<void> Service::add_drb(UeId ue_id, const DrbEntry& drb) {
  Request req;
  req.drb = drb;
  return std::get<OpResult<void>>(submit(OpKind::AddDrb, ue_id, std::move(req)));
}

OpResult<void> Service::begin_reconfigure(UeId ue_id, const ReconfigParams& params) {
  Request req;
  req.reconfig = params;
  return std::get<OpResult<void>>(submit(OpKind::BeginReconfigure, ue_id, std::move(req)));
}

OpResult<void> Service::complete_reconfigure(UeId ue_id) {
  Request req;
  return std::get<OpResult<void>>(
      submit(OpKind::CompleteReconfigure, ue_id, std::move(req)));
}

OpResult<void> Service::abort_reconfigure(UeId ue_id) {
  Request req;
  return std::get<OpResult<void>>(submit(OpKind::AbortReconfigure, ue_id, std::move(req)));
}

OpResult<void> Service::release_context(UeId ue_id) {
  Request req;
  return std::get<OpResult<void>>(submit(OpKind::ReleaseContext, ue_id, std::move(req)));
}

OpResult<UeContextView> Service::lookup(UeId ue_id) {
  Request req;
  return std::get<OpResult<UeContextView>>(submit(OpKind::Lookup, ue_id, std::move(req)));
}

std::uint64_t Service::count() {
  if (!running_) throw std::logic_error(kNotRunning);
  std::uint64_t total = 0;
  for (std::uint64_t i = 0; i < cfg_.n_shards; ++i) {
    Request req;
    req.kind = OpKind::Count;
    auto fut = req.completion.get_future();
    shards_[i]->queue.push(std::move(req));
    total += std::get<OpResult<std::uint64_t>>(fut.get()).value();
  }
  return total;
}

}  // namespace uecm
