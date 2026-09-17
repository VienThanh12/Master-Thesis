#pragma once
#include <array>
#include <cstdint>
#include <vector>

// UE context data model. See spec/SPECIFICATION.md §4 and §5.
namespace uecm {

using UeId = std::uint64_t;  // primary key; 0 is reserved/invalid (§4.1)

// UE lifecycle states (§5.1).
enum class UeState : std::uint8_t {
  Idle = 0, // UE is not connected to the network
  Connected = 1, // UE is connected to the network
  Reconfiguring = 2, // transitioning to this state indicates a reconfiguration is in progress
  Released = 3,  // transient-terminal: reaching it removes the context
};

// Data radio bearer entry (§4.2).
struct DrbEntry {
  std::uint8_t  drb_id = 0; // DRB ID, unique within the UE
  std::uint8_t  qos_flow_id = 0; // QoS flow ID, unique within the DRB
  std::uint32_t teid = 0; // TEID, unique within the UE
};

// Creation parameters (§4.3).
struct CreateParams {
  std::uint32_t serving_cell_id = 0;
  std::array<std::uint8_t, 32> security_key{};
};

// Reconfiguration parameters (§6.5); minimal for the model.
struct ReconfigParams {
  std::uint32_t target_cell_id = 0;
};

// Abstract signaling message (§6). Not a wire-format PDU.
struct SignalingMsg {
  std::uint8_t  kind = 0;
  std::uint16_t payload_len = 0;
  std::array<std::uint8_t, 64> payload{};
};

struct SignalingAck {
  bool          accepted = false;
  std::uint64_t new_messages_handled = 0;
};

// The per-UE context record (§4.2).
struct UeContext {
  UeId          ue_id = 0;
  UeState       state = UeState::Idle;
  std::uint32_t serving_cell_id = 0;
  std::uint16_t rrc_transaction_id = 0;
  std::array<std::uint8_t, 32> security_key{};
  std::vector<DrbEntry> drbs;  // dynamic on purpose (allocator study, RQ3)
  std::uint64_t messages_handled = 0;
  std::uint64_t last_activity_seq = 0;
};

// Read-only snapshot handed out by lookup (§4.4): a by-value copy, never an alias.
struct UeContextView {
  UeId          ue_id = 0;
  UeState       state = UeState::Idle;
  std::uint32_t serving_cell_id = 0;
  std::uint16_t rrc_transaction_id = 0;
  std::array<std::uint8_t, 32> security_key{};
  std::vector<DrbEntry> drbs;
  std::uint64_t messages_handled = 0;
  std::uint64_t last_activity_seq = 0;
};

}  // namespace uecm
