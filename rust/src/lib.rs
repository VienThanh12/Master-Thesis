//! UE Context Management (UECM) service — Rust implementation.
//!
//! Conforms to `../spec/SPECIFICATION.md`. Structurally mirrors the C++
//! implementation in `../cpp/`: identical pinned hashing (§8), the same UE state
//! machine and API (§5, §6), and the same shared-nothing thread-per-shard
//! concurrency model (§7).

pub mod config;
pub mod error;
pub mod hash;
pub mod message;
pub mod service;
pub mod shard_core;
pub mod types;

pub use config::{Config, MAX_DRBS, MAX_SIGNALING_PAYLOAD};
pub use error::{OpError, OpResult};
pub use service::Service;
pub use shard_core::ShardCore;
pub use types::{
    CreateParams, DrbEntry, ReconfigParams, SignalingAck, SignalingMsg, UeContext, UeContextView,
    UeId, UeState,
};
