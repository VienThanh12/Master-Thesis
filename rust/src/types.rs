//! UE context data model. See `../spec/SPECIFICATION.md` §4 and §5.

/// Primary key; `0` is reserved/invalid (§4.1).
pub type UeId = u64;

/// UE lifecycle states (§5.1).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum UeState {
    Idle = 0,
    Connected = 1,
    Reconfiguring = 2,
    Released = 3, // transient-terminal: reaching it removes the context
}

/// Data radio bearer entry (§4.2).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DrbEntry {
    pub drb_id: u8,
    pub qos_flow_id: u8,
    pub teid: u32,
}

/// Creation parameters (§4.3).
#[derive(Debug, Clone, Copy, Default)]
pub struct CreateParams {
    pub serving_cell_id: u32,
    pub security_key: [u8; 32],
}

/// Reconfiguration parameters (§6.5).
#[derive(Debug, Clone, Copy, Default)]
pub struct ReconfigParams {
    pub target_cell_id: u32,
}

/// Abstract signaling message (§6); not a wire-format PDU.
#[derive(Debug, Clone, Copy)]
pub struct SignalingMsg {
    pub kind: u8,
    pub payload_len: u16,
    pub payload: [u8; 64],
}

impl Default for SignalingMsg {
    fn default() -> Self {
        Self {
            kind: 0,
            payload_len: 0,
            payload: [0u8; 64],
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SignalingAck {
    pub accepted: bool,
    pub new_messages_handled: u64,
}

/// The per-UE context record (§4.2).
#[derive(Debug, Clone)]
pub struct UeContext {
    pub ue_id: UeId,
    pub state: UeState,
    pub serving_cell_id: u32,
    pub rrc_transaction_id: u16,
    pub security_key: [u8; 32],
    pub drbs: Vec<DrbEntry>, // dynamic on purpose (allocator study, RQ3)
    pub messages_handled: u64,
    pub last_activity_seq: u64,
}

/// Read-only snapshot handed out by `lookup` (§4.4): a by-value copy.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UeContextView {
    pub ue_id: UeId,
    pub state: UeState,
    pub serving_cell_id: u32,
    pub rrc_transaction_id: u16,
    pub security_key: [u8; 32],
    pub drbs: Vec<DrbEntry>,
    pub messages_handled: u64,
    pub last_activity_seq: u64,
}
