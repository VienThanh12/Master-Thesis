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
  std::uint32_t serving_cell_id = 0; // serving cell ID, unique within the network
  std::array<std::uint8_t, 32> security_key{}; // security key, used to encrypt and decrypt the data
};

// Reconfiguration parameters (§6.5); minimal for the model.
struct ReconfigParams {
  std::uint32_t target_cell_id = 0; // target cell ID, unique within the network
};

// Abstract signaling message (§6). Not a wire-format PDU.
struct SignalingMsg {
  std::uint8_t  kind = 0; // kind of signaling message
  std::uint16_t payload_len = 0; // length of the payload 
  std::array<std::uint8_t, 64> payload{}; // payload of the signaling message
};

struct SignalingAck {
  bool          accepted = false; // true if the signaling message was accepted, false otherwise
  std::uint64_t new_messages_handled = 0; // number of new messages handled
};

// The per-UE context record (§4.2).
struct UeContext {
  UeId          ue_id = 0;
  UeState       state = UeState::Idle;
  std::uint32_t serving_cell_id = 0; // serving cell ID, unique within the network  
  std::uint16_t rrc_transaction_id = 0; // RRC transaction ID, unique within the UE
  std::array<std::uint8_t, 32> security_key{};
  std::vector<DrbEntry> drbs;  // dynamic on purpose (allocator study, RQ3)
  std::uint64_t messages_handled = 0; // number of messages handled
  std::uint64_t last_activity_seq = 0; // last activity sequence number
};

// Read-only snapshot handed out by lookup (§4.4): a by-value copy, never an alias.
struct UeContextView {
  UeId          ue_id = 0; // UE ID, unique within the network  
  UeState       state = UeState::Idle;
  std::uint32_t serving_cell_id = 0; // serving cell ID, unique within the network
  std::uint16_t rrc_transaction_id = 0; // RRC transaction ID, unique within the UE
  std::array<std::uint8_t, 32> security_key{}; // security key, used to encrypt and decrypt the data
  std::vector<DrbEntry> drbs; // dynamic on purpose (allocator study, RQ3)
  std::uint64_t messages_handled = 0; // number of messages handled
  std::uint64_t last_activity_seq = 0; // last activity sequence number
};

}  // namespace uecm
