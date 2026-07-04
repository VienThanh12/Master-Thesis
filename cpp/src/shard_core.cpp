#include "uecm/shard_core.hpp"

#include <utility>

namespace uecm {

ShardCore::ShardCore(const Config& cfg, std::atomic<std::uint64_t>& activity_seq)
    : cfg_(cfg), activity_seq_(activity_seq) {
  map_.reserve(cfg_.initial_shard_capacity);
}

OpResult<void> ShardCore::create_context(UeId ue_id, const CreateParams& params) {
  if (ue_id == 0) return std::unexpected(OpError::InvalidArgument);
  if (map_.size() >= cfg_.max_contexts_per_shard)
    return std::unexpected(OpError::CapacityExceeded);
  if (map_.find(ue_id) != map_.end())
    return std::unexpected(OpError::AlreadyExists);

  UeContext ctx;
  ctx.ue_id = ue_id;
  ctx.state = UeState::Idle;
  ctx.serving_cell_id = params.serving_cell_id;
  ctx.security_key = params.security_key;
  ctx.last_activity_seq = next_seq();
  map_.emplace(ue_id, std::move(ctx));
  return {};
}

OpResult<void> ShardCore::setup_connection(UeId ue_id) {
  if (ue_id == 0) return std::unexpected(OpError::InvalidArgument);
  auto it = map_.find(ue_id);
  if (it == map_.end()) return std::unexpected(OpError::NotFound);
  if (it->second.state != UeState::Idle)
    return std::unexpected(OpError::InvalidState);
  it->second.state = UeState::Connected;
  it->second.last_activity_seq = next_seq();
  return {};
}

OpResult<SignalingAck> ShardCore::handle_signaling(UeId ue_id, const SignalingMsg& msg) {
  if (ue_id == 0) return std::unexpected(OpError::InvalidArgument);
  if (msg.payload_len > MAX_SIGNALING_PAYLOAD)
    return std::unexpected(OpError::InvalidArgument);
  auto it = map_.find(ue_id);
  if (it == map_.end()) return std::unexpected(OpError::NotFound);
  if (it->second.state != UeState::Connected)
    return std::unexpected(OpError::InvalidState);
  it->second.messages_handled += 1;
  it->second.last_activity_seq = next_seq();
  return SignalingAck{true, it->second.messages_handled};
}

OpResult<void> ShardCore::add_drb(UeId ue_id, const DrbEntry& drb) {
  if (ue_id == 0) return std::unexpected(OpError::InvalidArgument);
  auto it = map_.find(ue_id);
  if (it == map_.end()) return std::unexpected(OpError::NotFound);
  UeContext& ctx = it->second;
  if (ctx.state != UeState::Connected)
    return std::unexpected(OpError::InvalidState);
  if (ctx.drbs.size() >= MAX_DRBS)
    return std::unexpected(OpError::CapacityExceeded);
  for (const auto& d : ctx.drbs) {
    if (d.drb_id == drb.drb_id) return std::unexpected(OpError::AlreadyExists);
  }
  ctx.drbs.push_back(drb);
  ctx.last_activity_seq = next_seq();
  return {};
}

OpResult<void> ShardCore::begin_reconfigure(UeId ue_id, const ReconfigParams& params) {
  if (ue_id == 0) return std::unexpected(OpError::InvalidArgument);
  auto it = map_.find(ue_id);
  if (it == map_.end()) return std::unexpected(OpError::NotFound);
  if (it->second.state != UeState::Connected)
    return std::unexpected(OpError::InvalidState);
  it->second.state = UeState::Reconfiguring;
  it->second.serving_cell_id = params.target_cell_id;
  it->second.last_activity_seq = next_seq();
  return {};
}

OpResult<void> ShardCore::complete_reconfigure(UeId ue_id) {
  if (ue_id == 0) return std::unexpected(OpError::InvalidArgument);
  auto it = map_.find(ue_id);
  if (it == map_.end()) return std::unexpected(OpError::NotFound);
  if (it->second.state != UeState::Reconfiguring)
    return std::unexpected(OpError::InvalidState);
  it->second.state = UeState::Connected;
  it->second.last_activity_seq = next_seq();
  return {};
}

OpResult<void> ShardCore::abort_reconfigure(UeId ue_id) {
  if (ue_id == 0) return std::unexpected(OpError::InvalidArgument);
  auto it = map_.find(ue_id);
  if (it == map_.end()) return std::unexpected(OpError::NotFound);
  if (it->second.state != UeState::Reconfiguring)
    return std::unexpected(OpError::InvalidState);
  it->second.state = UeState::Connected;
  it->second.last_activity_seq = next_seq();
  return {};
}

OpResult<void> ShardCore::release_context(UeId ue_id) {
  if (ue_id == 0) return std::unexpected(OpError::InvalidArgument);
  auto it = map_.find(ue_id);
  if (it == map_.end()) return std::unexpected(OpError::NotFound);
  map_.erase(it);  // Idle/Connected/Reconfiguring -> Released -> removed
  return {};
}

OpResult<UeContextView> ShardCore::lookup(UeId ue_id) const {
  if (ue_id == 0) return std::unexpected(OpError::InvalidArgument);
  auto it = map_.find(ue_id);
  if (it == map_.end()) return std::unexpected(OpError::NotFound);
  const UeContext& c = it->second;
  UeContextView v;
  v.ue_id = c.ue_id;
  v.state = c.state;
  v.serving_cell_id = c.serving_cell_id;
  v.rrc_transaction_id = c.rrc_transaction_id;
  v.security_key = c.security_key;
  v.drbs = c.drbs;  // copy by value (§4.4)
  v.messages_handled = c.messages_handled;
  v.last_activity_seq = c.last_activity_seq;
  return v;
}

}  // namespace uecm
