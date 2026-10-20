#pragma once
#include <chrono>
#include <cstdint>
#include <future>
#include <variant>
#ifdef UECM_BATCH_PROBE
#include <vector>
#endif

#include "uecm/error.hpp"
#include "uecm/types.hpp"

// Request/Response message types routed to shard workers (spec §7, §8.3).
// C++ uses a tagged struct (OpKind + arg fields) and a std::variant response;
// the Rust side uses an enum + typed oneshot. This forced-idiom difference is
// recorded in spec §12.
namespace uecm {

enum class OpKind : std::uint8_t {
  CreateContext,
  SetupConnection,
  HandleSignaling,
  AddDrb,
  BeginReconfigure,
  CompleteReconfigure,
  AbortReconfigure,
  ReleaseContext,
  Lookup,
  Count,
#ifdef UECM_BATCH_PROBE
  SignalBatch,  // PROBE ONLY: several handle_signaling operations for one shard
#endif
  Stop,  // sentinel to terminate a worker (spec §7.1)
};

// The union of all possible operation results.
using Response = std::variant<
    OpResult<void>,           // create/setup/add_drb/*reconfigure/release
    OpResult<SignalingAck>,   // handle_signaling
    OpResult<UeContextView>,  // lookup
    OpResult<std::uint64_t>>; // count

// A worker-produced completion. The timestamp is captured immediately after the
// shard operation and before the producer observes the future, so client polling
// cannot inflate operation latency.
struct TimedResponse {
  Response response;
  std::chrono::steady_clock::time_point done;
  // Epoch unless Config::stamp_start. A confirmatory run must not read it.
  std::chrono::steady_clock::time_point started{};
};

// A request carries its op kind, arguments, and a one-shot completion (§7.6).
// Move-only because std::promise is move-only.
struct Request {
  OpKind kind{};
  UeId ue_id = 0;
  CreateParams create_params{};
  SignalingMsg signaling{};
  DrbEntry drb{};
  ReconfigParams reconfig{};
  bool stamp_completion = false;
#ifdef UECM_BATCH_PROBE
  // PROBE ONLY: the UEs of one SignalBatch, all owned by the receiving shard.
  std::vector<UeId> batch_ids;
#endif
  std::promise<TimedResponse> completion;
};

}  // namespace uecm
