#pragma once
#include <atomic>
#include <cstdint>
#include <unordered_map>

#include "uecm/config.hpp"
#include "uecm/error.hpp"
#include "uecm/hash.hpp"
#include "uecm/types.hpp"

#ifdef UECM_FLAT_MAP
#include "uecm/flat_map.hpp"
#endif

namespace uecm {

// The intra-shard store. std::unordered_map is the measured configuration; the
// open-addressed alternative exists only to attribute the core-operation result
// and is never the reported arm. See flat_map.hpp for why.
#ifdef UECM_FLAT_MAP
using ContextMap = FlatMap<UeId, UeContext, FnvHash>;
#else
using ContextMap = std::unordered_map<UeId, UeContext, FnvHash>;
#endif

// ShardCore is the single-threaded operation processor for one shard: it owns the
// shard's contexts and implements the state machine + map operations (spec §5, §6).
//
// It is intentionally NOT thread-safe on its own: in the full service exactly one
// worker thread ever calls these methods for a given shard (shared-nothing, §7), so
// no locking is needed. The threaded queue/worker wrapper is added on top of this.
class ShardCore {
 public:
  explicit ShardCore(const Config& cfg, std::atomic<std::uint64_t>& activity_seq);

  // Mutating operations (spec §6).
  OpResult<void>         create_context(UeId ue_id, const CreateParams& params);
  OpResult<void>         setup_connection(UeId ue_id);
  OpResult<SignalingAck> handle_signaling(UeId ue_id, const SignalingMsg& msg);
  OpResult<void>         add_drb(UeId ue_id, const DrbEntry& drb);
  OpResult<void>         begin_reconfigure(UeId ue_id, const ReconfigParams& params);
  OpResult<void>         complete_reconfigure(UeId ue_id);
  OpResult<void>         abort_reconfigure(UeId ue_id);
  OpResult<void>         release_context(UeId ue_id);

  // Read-only operations.
  OpResult<UeContextView> lookup(UeId ue_id) const;
  std::uint64_t           count() const noexcept { return map_.size(); }

 private:
  std::uint64_t next_seq() noexcept {
    return activity_seq_.fetch_add(1, std::memory_order_relaxed);
  }

  Config cfg_;
  std::atomic<std::uint64_t>& activity_seq_;
  ContextMap map_;
};

}  // namespace uecm
