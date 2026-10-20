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
use std::time::Instant;

/// A worker-produced result and its completion time. The worker captures `done`
/// before the producer observes the channel, so polling delay is not measured as
/// operation latency.
pub struct Completion<T> {
    pub value: T,
    pub done: Instant,
    /// Meaningful only when `Config::stamp_start` is set. Otherwise every
    /// completion from a worker carries the same sentinel.
    pub started: Instant,
}

pub enum Request {
    Create {
        ue_id: UeId,
        params: CreateParams,
        stamp_completion: bool,
        resp: CompletionTx<Completion<OpResult<()>>>,
    },
    Setup {
        ue_id: UeId,
        stamp_completion: bool,
        resp: CompletionTx<Completion<OpResult<()>>>,
    },
    Signal {
        ue_id: UeId,
        msg: SignalingMsg,
        stamp_completion: bool,
        resp: CompletionTx<Completion<OpResult<SignalingAck>>>,
    },
    AddDrb {
        ue_id: UeId,
        drb: DrbEntry,
        stamp_completion: bool,
        resp: CompletionTx<Completion<OpResult<()>>>,
    },
    BeginReconf {
        ue_id: UeId,
        params: ReconfigParams,
        stamp_completion: bool,
        resp: CompletionTx<Completion<OpResult<()>>>,
    },
    CompleteReconf {
        ue_id: UeId,
        stamp_completion: bool,
        resp: CompletionTx<Completion<OpResult<()>>>,
    },
    AbortReconf {
        ue_id: UeId,
        stamp_completion: bool,
        resp: CompletionTx<Completion<OpResult<()>>>,
    },
    Release {
        ue_id: UeId,
        stamp_completion: bool,
        resp: CompletionTx<Completion<OpResult<()>>>,
    },
    Lookup {
        ue_id: UeId,
        stamp_completion: bool,
        resp: CompletionTx<Completion<OpResult<UeContextView>>>,
    },
    Count {
        resp: CompletionTx<u64>,
    },
    #[cfg(feature = "batch-probe")]
    /// PROBE ONLY (`--features batch-probe`): several signalling operations for UEs
    /// of one shard, answered once with the reply type a single `Signal` uses.
    SignalBatch {
        ue_ids: Vec<UeId>,
        msg: SignalingMsg,
        resp: CompletionTx<Completion<OpResult<SignalingAck>>>,
    },
    Stop,
}
