#pragma once
#include <cstdint>
#include <future>
#include <variant>

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
  Stop,  // sentinel to terminate a worker (spec §7.1)
};

// The union of all possible operation results.
using Response = std::variant<
    OpResult<void>,           // create/setup/add_drb/*reconfigure/release
    OpResult<SignalingAck>,   // handle_signaling
    OpResult<UeContextView>,  // lookup
    OpResult<std::uint64_t>>; // count

// A request carries its op kind, arguments, and a one-shot completion (§7.6).
// Move-only because std::promise is move-only.
struct Request {
  OpKind kind{};
  UeId ue_id = 0;
  CreateParams create_params{};
  SignalingMsg signaling{};
  DrbEntry drb{};
  ReconfigParams reconfig{};
  std::promise<Response> completion;
};

}  // namespace uecm
