//! Inter-thread request messages (spec §7.3).
//!
//! Instead of the C++ `std::variant` `Response` + `std::promise`, Rust uses a
//! per-variant typed one-shot channel: each request carries a `Sender` of the
//! precise result type, so the worker sends the typed value back and the caller
//! receives it directly (no runtime variant dispatch needed).

use std::sync::mpsc::Sender;

use crate::error::OpResult;
use crate::types::{
    CreateParams, DrbEntry, ReconfigParams, SignalingAck, SignalingMsg, UeContextView, UeId,
};

pub enum Request {
    Create {
        ue_id: UeId,
        params: CreateParams,
        resp: Sender<OpResult<()>>,
    },
    Setup {
        ue_id: UeId,
        resp: Sender<OpResult<()>>,
    },
    Signal {
        ue_id: UeId,
        msg: SignalingMsg,
        resp: Sender<OpResult<SignalingAck>>,
    },
    AddDrb {
        ue_id: UeId,
        drb: DrbEntry,
        resp: Sender<OpResult<()>>,
    },
    BeginReconf {
        ue_id: UeId,
        params: ReconfigParams,
        resp: Sender<OpResult<()>>,
    },
    CompleteReconf {
        ue_id: UeId,
        resp: Sender<OpResult<()>>,
    },
    AbortReconf {
        ue_id: UeId,
        resp: Sender<OpResult<()>>,
    },
    Release {
        ue_id: UeId,
        resp: Sender<OpResult<()>>,
    },
    Lookup {
        ue_id: UeId,
        resp: Sender<OpResult<UeContextView>>,
    },
    Count {
        resp: Sender<u64>,
    },
    Stop,
}
