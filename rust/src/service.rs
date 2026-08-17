//! Threaded UE Context Management service (spec §7): shared-nothing,
//! thread-per-shard.
//!
//! Each call on the typed API is routed by `shard_index(ue_id)` to the owning
//! shard's bounded queue and executed by that shard's single worker thread; the
//! caller blocks on a one-shot completion. The bounded queue provides blocking
//! backpressure (a full queue blocks the producer), mirroring the C++ design.
//!
//! Every operation requires the service to be running (§7.1): a call before
//! `start()` or after `shutdown()` is a caller error and panics.
//!
//! Rust specifics vs. C++:
//! - Bounded MPSC queue: `std::sync::mpsc::sync_channel(capacity)` (blocking send).
//! - One-shot completion: a fresh `std::sync::mpsc::channel()` per request.
//! - Shared-nothing: each worker owns its `ShardCore`; only the atomic
//!   `activity_seq` counter is shared (via `Arc<AtomicU64>`).

use std::sync::atomic::AtomicU64;
use std::sync::mpsc::channel;
use std::sync::Arc;
use std::thread::JoinHandle;

// The shard queue. The standard bounded channel is the measured configuration;
// the mutex-and-two-condvars alternative mirrors the C++ design and exists only
// to localise the overload divergence. See mutex_queue.rs for why. The one-shot
// completion above is unaffected either way.
#[cfg(not(feature = "mutex-queue"))]
use std::sync::mpsc::{sync_channel, Receiver, SyncSender};
#[cfg(feature = "mutex-queue")]
use crate::mutex_queue::{bounded as sync_channel, Receiver, SyncSender};

use crate::config::Config;
use crate::error::OpResult;
use crate::hash::shard_index;
use crate::message::Request;
use crate::shard_core::ShardCore;
use crate::types::{
    CreateParams, DrbEntry, ReconfigParams, SignalingAck, SignalingMsg, UeContextView, UeId,
};

// Spec §7.1: operating outside the running window is a caller error, not one of the
// five OpError codes, so it is reported out of band. Written as an explicit `if`
// rather than `assert!` because bench/complexity.py counts branches with lizard,
// which does not expand macros.
const NOT_RUNNING: &str =
    "uecm::Service: operation submitted while the service is not running (spec §7.1)";

struct Shard {
    tx: SyncSender<Request>,
    handle: Option<JoinHandle<()>>,
}

pub struct Service {
    cfg: Config,
    activity_seq: Arc<AtomicU64>,
    shards: Vec<Shard>,
    running: bool,
}

impl Service {
    pub fn new(cfg: Config) -> Self {
        let mut cfg = cfg;
        if cfg.n_shards == 0 {
            cfg.n_shards = 1;
        }
        Self {
            cfg,
            activity_seq: Arc::new(AtomicU64::new(0)),
            shards: Vec::new(),
            running: false,
        }
    }

    /// Spawn one worker thread per shard. Idempotent while running.
    pub fn start(&mut self) {
        if self.running {
            return;
        }
        self.shards.clear();
        for _ in 0..self.cfg.n_shards {
            let (tx, rx): (SyncSender<Request>, Receiver<Request>) =
                sync_channel(self.cfg.queue_capacity);
            let cfg = self.cfg;
            let seq = Arc::clone(&self.activity_seq);
            let handle = std::thread::spawn(move || worker_loop(cfg, seq, rx));
            self.shards.push(Shard {
                tx,
                handle: Some(handle),
            });
        }
        self.running = true;
    }

    /// Stop workers and join. Idempotent.
    pub fn shutdown(&mut self) {
        if !self.running {
            return;
        }
        for s in &self.shards {
            let _ = s.tx.send(Request::Stop);
        }
        for s in &mut self.shards {
            if let Some(h) = s.handle.take() {
                let _ = h.join();
            }
        }
        self.shards.clear();
        self.running = false;
    }

    #[inline]
    pub fn n_shards(&self) -> u64 {
        self.cfg.n_shards
    }

    #[inline]
    fn shard_tx(&self, ue_id: UeId) -> &SyncSender<Request> {
        if !self.running {
            panic!("{NOT_RUNNING}");
        }
        let idx = shard_index(ue_id, self.cfg.n_shards) as usize;
        &self.shards[idx].tx
    }

    pub fn create_context(&self, ue_id: UeId, params: CreateParams) -> OpResult<()> {
        let (rtx, rrx) = channel();
        self.shard_tx(ue_id)
            .send(Request::Create {
                ue_id,
                params,
                resp: rtx,
            })
            .expect("worker alive");
        rrx.recv().expect("completion")
    }

    pub fn setup_connection(&self, ue_id: UeId) -> OpResult<()> {
        let (rtx, rrx) = channel();
        self.shard_tx(ue_id)
            .send(Request::Setup { ue_id, resp: rtx })
            .expect("worker alive");
        rrx.recv().expect("completion")
    }

    pub fn handle_signaling(&self, ue_id: UeId, msg: SignalingMsg) -> OpResult<SignalingAck> {
        let (rtx, rrx) = channel();
        self.shard_tx(ue_id)
            .send(Request::Signal {
                ue_id,
                msg,
                resp: rtx,
            })
            .expect("worker alive");
        rrx.recv().expect("completion")
    }

    pub fn add_drb(&self, ue_id: UeId, drb: DrbEntry) -> OpResult<()> {
        let (rtx, rrx) = channel();
        self.shard_tx(ue_id)
            .send(Request::AddDrb {
                ue_id,
                drb,
                resp: rtx,
            })
            .expect("worker alive");
        rrx.recv().expect("completion")
    }

    pub fn begin_reconfigure(&self, ue_id: UeId, params: ReconfigParams) -> OpResult<()> {
        let (rtx, rrx) = channel();
        self.shard_tx(ue_id)
            .send(Request::BeginReconf {
                ue_id,
                params,
                resp: rtx,
            })
            .expect("worker alive");
        rrx.recv().expect("completion")
    }

    pub fn complete_reconfigure(&self, ue_id: UeId) -> OpResult<()> {
        let (rtx, rrx) = channel();
        self.shard_tx(ue_id)
            .send(Request::CompleteReconf { ue_id, resp: rtx })
            .expect("worker alive");
        rrx.recv().expect("completion")
    }

    pub fn abort_reconfigure(&self, ue_id: UeId) -> OpResult<()> {
        let (rtx, rrx) = channel();
        self.shard_tx(ue_id)
            .send(Request::AbortReconf { ue_id, resp: rtx })
            .expect("worker alive");
        rrx.recv().expect("completion")
    }

    pub fn release_context(&self, ue_id: UeId) -> OpResult<()> {
        let (rtx, rrx) = channel();
        self.shard_tx(ue_id)
            .send(Request::Release { ue_id, resp: rtx })
            .expect("worker alive");
        rrx.recv().expect("completion")
    }

    pub fn lookup(&self, ue_id: UeId) -> OpResult<UeContextView> {
        let (rtx, rrx) = channel();
        self.shard_tx(ue_id)
            .send(Request::Lookup { ue_id, resp: rtx })
            .expect("worker alive");
        rrx.recv().expect("completion")
    }

    /// Total contexts across all shards (routed per shard, summed). Not a snapshot:
    /// see §6.7. Panics if the service is not running (§7.1).
    pub fn count(&self) -> u64 {
        if !self.running {
            panic!("{NOT_RUNNING}");
        }
        let mut total = 0;
        for s in &self.shards {
            let (rtx, rrx) = channel();
            s.tx.send(Request::Count { resp: rtx })
                .expect("worker alive");
            total += rrx.recv().expect("completion");
        }
        total
    }
}

impl Drop for Service {
    fn drop(&mut self) {
        self.shutdown();
    }
}

fn worker_loop(cfg: Config, seq: Arc<AtomicU64>, rx: Receiver<Request>) {
    let mut core = ShardCore::new(cfg, seq);
    while let Ok(req) = rx.recv() {
        match req {
            Request::Create {
                ue_id,
                params,
                resp,
            } => {
                let _ = resp.send(core.create_context(ue_id, &params));
            }
            Request::Setup { ue_id, resp } => {
                let _ = resp.send(core.setup_connection(ue_id));
            }
            Request::Signal { ue_id, msg, resp } => {
                let _ = resp.send(core.handle_signaling(ue_id, &msg));
            }
            Request::AddDrb { ue_id, drb, resp } => {
                let _ = resp.send(core.add_drb(ue_id, drb));
            }
            Request::BeginReconf {
                ue_id,
                params,
                resp,
            } => {
                let _ = resp.send(core.begin_reconfigure(ue_id, &params));
            }
            Request::CompleteReconf { ue_id, resp } => {
                let _ = resp.send(core.complete_reconfigure(ue_id));
            }
            Request::AbortReconf { ue_id, resp } => {
                let _ = resp.send(core.abort_reconfigure(ue_id));
            }
            Request::Release { ue_id, resp } => {
                let _ = resp.send(core.release_context(ue_id));
            }
            Request::Lookup { ue_id, resp } => {
                let _ = resp.send(core.lookup(ue_id));
            }
            Request::Count { resp } => {
                let _ = resp.send(core.count());
            }
            Request::Stop => break,
        }
    }
}
