//! Single-threaded per-shard operation processor: owns the shard's contexts and
//! implements the state machine + map operations (spec §5, §6).
//!
//! Not thread-safe on its own: in the full service exactly one worker thread ever
//! calls these methods for a given shard (shared-nothing, §7), so no locking is
//! needed. The threaded queue/worker wrapper is added in `service.rs`.
//!
//! `last_activity_seq` is stamped ONLY on a successful mutation (parity with the
//! C++ implementation); error paths never consume a sequence number. The stamp is
//! written via a direct `self.activity_seq` field access rather than the
//! `next_seq()` helper so it coexists with an outstanding `&mut self.map` borrow
//! (disjoint fields).

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

use crate::config::{Config, MAX_DRBS, MAX_SIGNALING_PAYLOAD};
use crate::error::{OpError, OpResult};
use crate::hash::FnvBuildHasher;
use crate::types::{
    CreateParams, DrbEntry, ReconfigParams, SignalingAck, SignalingMsg, UeContext, UeContextView,
    UeId, UeState,
};

pub struct ShardCore {
    cfg: Config,
    activity_seq: Arc<AtomicU64>,
    map: HashMap<UeId, UeContext, FnvBuildHasher>,
}

impl ShardCore {
    pub fn new(cfg: Config, activity_seq: Arc<AtomicU64>) -> Self {
        let map = HashMap::with_capacity_and_hasher(cfg.initial_shard_capacity, FnvBuildHasher);
        Self {
            cfg,
            activity_seq,
            map,
        }
    }

    #[inline]
    fn next_seq(&self) -> u64 {
        self.activity_seq.fetch_add(1, Ordering::Relaxed)
    }

    #[inline]
    pub fn count(&self) -> u64 {
        self.map.len() as u64
    }

    pub fn create_context(&mut self, ue_id: UeId, params: &CreateParams) -> OpResult<()> {
        if ue_id == 0 {
            return Err(OpError::InvalidArgument);
        }
        if self.map.len() as u64 >= self.cfg.max_contexts_per_shard {
            return Err(OpError::CapacityExceeded);
        }
        if self.map.contains_key(&ue_id) {
            return Err(OpError::AlreadyExists);
        }
        let seq = self.next_seq();
        self.map.insert(
            ue_id,
            UeContext {
                ue_id,
                state: UeState::Idle,
                serving_cell_id: params.serving_cell_id,
                rrc_transaction_id: 0,
                security_key: params.security_key,
                drbs: Vec::new(),
                messages_handled: 0,
                last_activity_seq: seq,
            },
        );
        Ok(())
    }

    pub fn setup_connection(&mut self, ue_id: UeId) -> OpResult<()> {
        if ue_id == 0 {
            return Err(OpError::InvalidArgument);
        }
        let ctx = self.map.get_mut(&ue_id).ok_or(OpError::NotFound)?;
        if ctx.state != UeState::Idle {
            return Err(OpError::InvalidState);
        }
        ctx.state = UeState::Connected;
        ctx.last_activity_seq = self.activity_seq.fetch_add(1, Ordering::Relaxed);
        Ok(())
    }

    pub fn handle_signaling(&mut self, ue_id: UeId, msg: &SignalingMsg) -> OpResult<SignalingAck> {
        if ue_id == 0 || msg.payload_len as usize > MAX_SIGNALING_PAYLOAD {
            return Err(OpError::InvalidArgument);
        }
        let ctx = self.map.get_mut(&ue_id).ok_or(OpError::NotFound)?;
        if ctx.state != UeState::Connected {
            return Err(OpError::InvalidState);
        }
        ctx.messages_handled += 1;
        ctx.last_activity_seq = self.activity_seq.fetch_add(1, Ordering::Relaxed);
        Ok(SignalingAck {
            accepted: true,
            new_messages_handled: ctx.messages_handled,
        })
    }

    pub fn add_drb(&mut self, ue_id: UeId, drb: DrbEntry) -> OpResult<()> {
        if ue_id == 0 {
            return Err(OpError::InvalidArgument);
        }
        let ctx = self.map.get_mut(&ue_id).ok_or(OpError::NotFound)?;
        if ctx.state != UeState::Connected {
            return Err(OpError::InvalidState);
        }
        if ctx.drbs.len() >= MAX_DRBS {
            return Err(OpError::CapacityExceeded);
        }
        if ctx.drbs.iter().any(|d| d.drb_id == drb.drb_id) {
            return Err(OpError::AlreadyExists);
        }
        ctx.drbs.push(drb);
        ctx.last_activity_seq = self.activity_seq.fetch_add(1, Ordering::Relaxed);
        Ok(())
    }

    pub fn begin_reconfigure(&mut self, ue_id: UeId, params: &ReconfigParams) -> OpResult<()> {
        if ue_id == 0 {
            return Err(OpError::InvalidArgument);
        }
        let ctx = self.map.get_mut(&ue_id).ok_or(OpError::NotFound)?;
        if ctx.state != UeState::Connected {
            return Err(OpError::InvalidState);
        }
        ctx.state = UeState::Reconfiguring;
        ctx.serving_cell_id = params.target_cell_id;
        ctx.last_activity_seq = self.activity_seq.fetch_add(1, Ordering::Relaxed);
        Ok(())
    }

    pub fn complete_reconfigure(&mut self, ue_id: UeId) -> OpResult<()> {
        self.finish_reconfigure(ue_id)
    }

    pub fn abort_reconfigure(&mut self, ue_id: UeId) -> OpResult<()> {
        self.finish_reconfigure(ue_id)
    }

    fn finish_reconfigure(&mut self, ue_id: UeId) -> OpResult<()> {
        if ue_id == 0 {
            return Err(OpError::InvalidArgument);
        }
        let ctx = self.map.get_mut(&ue_id).ok_or(OpError::NotFound)?;
        if ctx.state != UeState::Reconfiguring {
            return Err(OpError::InvalidState);
        }
        ctx.state = UeState::Connected;
        ctx.last_activity_seq = self.activity_seq.fetch_add(1, Ordering::Relaxed);
        Ok(())
    }

    pub fn release_context(&mut self, ue_id: UeId) -> OpResult<()> {
        if ue_id == 0 {
            return Err(OpError::InvalidArgument);
        }
        match self.map.remove(&ue_id) {
            Some(_) => Ok(()), // Idle/Connected/Reconfiguring -> Released -> removed
            None => Err(OpError::NotFound),
        }
    }

    pub fn lookup(&self, ue_id: UeId) -> OpResult<UeContextView> {
        if ue_id == 0 {
            return Err(OpError::InvalidArgument);
        }
        let c = self.map.get(&ue_id).ok_or(OpError::NotFound)?;
        Ok(UeContextView {
            ue_id: c.ue_id,
            state: c.state,
            serving_cell_id: c.serving_cell_id,
            rrc_transaction_id: c.rrc_transaction_id,
            security_key: c.security_key,
            drbs: c.drbs.clone(), // copy by value (§4.4)
            messages_handled: c.messages_handled,
            last_activity_seq: c.last_activity_seq,
        })
    }
}
