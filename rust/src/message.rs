//! Inter-thread request messages (spec §7.3).
//!
//! Instead of the C++ `std::variant` `Response` + `std::promise`, Rust uses a
//! per-variant typed one-shot channel: each request carries a sender of the
//! precise result type, so the worker sends the typed value back and the caller
//! receives it directly (no runtime variant dispatch needed).
//!
//! The compared arm uses `std::sync::mpsc::channel()` (unbounded list flavour).
//! `--features sync-oneshot` swaps that for `sync_channel(1)` so the overload
//! probe can ask whether the 31-slot list block is the floor. See spec §12.

#[cfg(not(feature = "sync-oneshot"))]
pub type CompletionTx<T> = std::sync::mpsc::Sender<T>;
#[cfg(feature = "sync-oneshot")]
pub type CompletionTx<T> = std::sync::mpsc::SyncSender<T>;

use crate::error::OpResult;
use crate::types::{
    CreateParams, DrbEntry, ReconfigParams, SignalingAck, SignalingMsg, UeContextView, UeId,
};

pub enum Request {
    Create {
        ue_id: UeId,
        params: CreateParams,
        resp: CompletionTx<OpResult<()>>,
    },
    Setup {
        ue_id: UeId,
        resp: CompletionTx<OpResult<()>>,
    },
    Signal {
        ue_id: UeId,
        msg: SignalingMsg,
        resp: CompletionTx<OpResult<SignalingAck>>,
    },
    AddDrb {
        ue_id: UeId,
        drb: DrbEntry,
        resp: CompletionTx<OpResult<()>>,
    },
    BeginReconf {
        ue_id: UeId,
        params: ReconfigParams,
        resp: CompletionTx<OpResult<()>>,
    },
    CompleteReconf {
        ue_id: UeId,
        resp: CompletionTx<OpResult<()>>,
    },
    AbortReconf {
        ue_id: UeId,
        resp: CompletionTx<OpResult<()>>,
    },
    Release {
        ue_id: UeId,
        resp: CompletionTx<OpResult<()>>,
    },
    Lookup {
        ue_id: UeId,
        resp: CompletionTx<OpResult<UeContextView>>,
    },
    Count {
        resp: CompletionTx<u64>,
    },
    Stop,
}
