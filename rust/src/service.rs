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
//! - One-shot completion: a fresh `std::sync::mpsc::channel()` per request
//!   (the compared arm). `--features sync-oneshot` uses `sync_channel(1)`
//!   instead, an attribution probe, not a reported configuration.
//! - Shared-nothing: each worker owns its `ShardCore`; only the atomic
//!   `activity_seq` counter is shared (via `Arc<AtomicU64>`).

use std::sync::atomic::AtomicU64;
use std::sync::Arc;
use std::thread::JoinHandle;

// Completions are always std::sync::mpsc, even when the shard queue is the
// mutex-queue probe. Fully qualified so `--features mutex-queue` cannot steal
// the name `sync_channel` out from under the oneshot probe.
#[cfg(not(feature = "sync-oneshot"))]
fn completion_channel<T>() -> (std::sync::mpsc::Sender<T>, std::sync::mpsc::Receiver<T>) {
    std::sync::mpsc::channel()
}
#[cfg(feature = "sync-oneshot")]
fn completion_channel<T>() -> (std::sync::mpsc::SyncSender<T>, std::sync::mpsc::Receiver<T>) {
    std::sync::mpsc::sync_channel(1)
}

// The shard queue. The standard bounded channel is the measured configuration;
// the mutex-and-two-condvars alternative mirrors the C++ design and exists only
// to localise the overload divergence. See mutex_queue.rs for why. The one-shot
// completion above is unaffected either way.
#[cfg(feature = "mutex-queue")]
use crate::mutex_queue::{bounded as sync_channel, Receiver, SyncSender};
#[cfg(not(feature = "mutex-queue"))]
use std::sync::mpsc::{sync_channel, Receiver, SyncSender};

use crate::config::Config;
use crate::error::OpResult;
use crate::hash::shard_index;
use crate::message::{Completion, Request};
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

    fn create_context_completion(
        &self,
        ue_id: UeId,
        params: CreateParams,
        stamp_completion: bool,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        let (rtx, rrx) = completion_channel();
        self.shard_tx(ue_id)
            .send(Request::Create {
                ue_id,
                params,
                stamp_completion,
                resp: rtx,
            })
            .expect("worker alive");
        rrx
    }

    fn setup_connection_completion(
        &self,
        ue_id: UeId,
        stamp_completion: bool,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        let (rtx, rrx) = completion_channel();
        self.shard_tx(ue_id)
            .send(Request::Setup {
                ue_id,
                stamp_completion,
                resp: rtx,
            })
            .expect("worker alive");
        rrx
    }

    fn handle_signaling_completion(
        &self,
        ue_id: UeId,
        msg: SignalingMsg,
        stamp_completion: bool,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<SignalingAck>>> {
        let (rtx, rrx) = completion_channel();
        self.shard_tx(ue_id)
            .send(Request::Signal {
                ue_id,
                msg,
                stamp_completion,
                resp: rtx,
            })
            .expect("worker alive");
        rrx
    }

    fn add_drb_completion(
        &self,
        ue_id: UeId,
        drb: DrbEntry,
        stamp_completion: bool,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        let (rtx, rrx) = completion_channel();
        self.shard_tx(ue_id)
            .send(Request::AddDrb {
                ue_id,
                drb,
                stamp_completion,
                resp: rtx,
            })
            .expect("worker alive");
        rrx
    }

    fn begin_reconfigure_completion(
        &self,
        ue_id: UeId,
        params: ReconfigParams,
        stamp_completion: bool,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        let (rtx, rrx) = completion_channel();
        self.shard_tx(ue_id)
            .send(Request::BeginReconf {
                ue_id,
                params,
                stamp_completion,
                resp: rtx,
            })
            .expect("worker alive");
        rrx
    }

    fn complete_reconfigure_completion(
        &self,
        ue_id: UeId,
        stamp_completion: bool,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        let (rtx, rrx) = completion_channel();
        self.shard_tx(ue_id)
            .send(Request::CompleteReconf {
                ue_id,
                stamp_completion,
                resp: rtx,
            })
            .expect("worker alive");
        rrx
    }

    fn abort_reconfigure_completion(
        &self,
        ue_id: UeId,
        stamp_completion: bool,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        let (rtx, rrx) = completion_channel();
        self.shard_tx(ue_id)
            .send(Request::AbortReconf {
                ue_id,
                stamp_completion,
                resp: rtx,
            })
            .expect("worker alive");
        rrx
    }

    fn release_context_completion(
        &self,
        ue_id: UeId,
        stamp_completion: bool,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        let (rtx, rrx) = completion_channel();
        self.shard_tx(ue_id)
            .send(Request::Release {
                ue_id,
                stamp_completion,
                resp: rtx,
            })
            .expect("worker alive");
        rrx
    }

    fn lookup_completion(
        &self,
        ue_id: UeId,
        stamp_completion: bool,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<UeContextView>>> {
        let (rtx, rrx) = completion_channel();
        self.shard_tx(ue_id)
            .send(Request::Lookup {
                ue_id,
                stamp_completion,
                resp: rtx,
            })
            .expect("worker alive");
        rrx
    }

    pub fn create_context_async(
        &self,
        ue_id: UeId,
        params: CreateParams,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        self.create_context_completion(ue_id, params, true)
    }

    pub fn setup_connection_async(
        &self,
        ue_id: UeId,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        self.setup_connection_completion(ue_id, true)
    }

    pub fn handle_signaling_async(
        &self,
        ue_id: UeId,
        msg: SignalingMsg,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<SignalingAck>>> {
        self.handle_signaling_completion(ue_id, msg, true)
    }

    pub fn add_drb_async(
        &self,
        ue_id: UeId,
        drb: DrbEntry,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        self.add_drb_completion(ue_id, drb, true)
    }

    pub fn begin_reconfigure_async(
        &self,
        ue_id: UeId,
        params: ReconfigParams,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        self.begin_reconfigure_completion(ue_id, params, true)
    }

    pub fn complete_reconfigure_async(
        &self,
        ue_id: UeId,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        self.complete_reconfigure_completion(ue_id, true)
    }

    pub fn abort_reconfigure_async(
        &self,
        ue_id: UeId,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        self.abort_reconfigure_completion(ue_id, true)
    }

    pub fn release_context_async(
        &self,
        ue_id: UeId,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<()>>> {
        self.release_context_completion(ue_id, true)
    }

    pub fn lookup_async(
        &self,
        ue_id: UeId,
    ) -> std::sync::mpsc::Receiver<Completion<OpResult<UeContextView>>> {
        self.lookup_completion(ue_id, true)
    }

    pub fn create_context(&self, ue_id: UeId, params: CreateParams) -> OpResult<()> {
        self.create_context_completion(ue_id, params, false)
            .recv()
            .expect("completion")
            .value
    }

    pub fn setup_connection(&self, ue_id: UeId) -> OpResult<()> {
        self.setup_connection_completion(ue_id, false)
            .recv()
            .expect("completion")
            .value
    }

    pub fn handle_signaling(&self, ue_id: UeId, msg: SignalingMsg) -> OpResult<SignalingAck> {
        self.handle_signaling_completion(ue_id, msg, false)
            .recv()
            .expect("completion")
            .value
    }

    pub fn add_drb(&self, ue_id: UeId, drb: DrbEntry) -> OpResult<()> {
        self.add_drb_completion(ue_id, drb, false)
            .recv()
            .expect("completion")
            .value
    }

    pub fn begin_reconfigure(&self, ue_id: UeId, params: ReconfigParams) -> OpResult<()> {
        self.begin_reconfigure_completion(ue_id, params, false)
            .recv()
            .expect("completion")
            .value
    }

    pub fn complete_reconfigure(&self, ue_id: UeId) -> OpResult<()> {
        self.complete_reconfigure_completion(ue_id, false)
            .recv()
            .expect("completion")
            .value
    }

    pub fn abort_reconfigure(&self, ue_id: UeId) -> OpResult<()> {
        self.abort_reconfigure_completion(ue_id, false)
            .recv()
            .expect("completion")
            .value
    }

    pub fn release_context(&self, ue_id: UeId) -> OpResult<()> {
        self.release_context_completion(ue_id, false)
            .recv()
            .expect("completion")
            .value
    }

    pub fn lookup(&self, ue_id: UeId) -> OpResult<UeContextView> {
        self.lookup_completion(ue_id, false)
            .recv()
            .expect("completion")
            .value
    }

    /// Total contexts across all shards (routed per shard, summed). Not a snapshot:
    /// see §6.7. Panics if the service is not running (§7.1).
    pub fn count(&self) -> u64 {
        if !self.running {
            panic!("{NOT_RUNNING}");
        }
        let mut total = 0;
        for s in &self.shards {
            let (rtx, rrx) = completion_channel();
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

#[inline]
fn completed<T>(
    value: T,
    stamp_completion: bool,
    started: std::time::Instant,
    unstamped: std::time::Instant,
) -> Completion<T> {
    Completion {
        value,
        started,
        done: if stamp_completion {
            std::time::Instant::now()
        } else {
            unstamped
        },
    }
}

fn worker_loop(cfg: Config, seq: Arc<AtomicU64>, rx: Receiver<Request>) {
    let mut core = ShardCore::new(cfg, seq);
    let unstamped = std::time::Instant::now();
    while let Ok(req) = rx.recv() {
        // One clock read, and only for a diagnostic run. It sits after the
        // request has left the queue and before the shard operation.
        let started = if cfg.stamp_start {
            std::time::Instant::now()
        } else {
            unstamped
        };
        match req {
            Request::Create {
                ue_id,
                params,
                stamp_completion,
                resp,
            } => {
                let value = core.create_context(ue_id, &params);
                let _ = resp.send(completed(value, stamp_completion, started, unstamped));
            }
            Request::Setup {
                ue_id,
                stamp_completion,
                resp,
            } => {
                let value = core.setup_connection(ue_id);
                let _ = resp.send(completed(value, stamp_completion, started, unstamped));
            }
            Request::Signal {
                ue_id,
                msg,
                stamp_completion,
                resp,
            } => {
                let value = core.handle_signaling(ue_id, &msg);
                let _ = resp.send(completed(value, stamp_completion, started, unstamped));
            }
            Request::AddDrb {
                ue_id,
                drb,
                stamp_completion,
                resp,
            } => {
                let value = core.add_drb(ue_id, drb);
                let _ = resp.send(completed(value, stamp_completion, started, unstamped));
            }
            Request::BeginReconf {
                ue_id,
                params,
                stamp_completion,
                resp,
            } => {
                let value = core.begin_reconfigure(ue_id, &params);
                let _ = resp.send(completed(value, stamp_completion, started, unstamped));
            }
            Request::CompleteReconf {
                ue_id,
                stamp_completion,
                resp,
            } => {
                let value = core.complete_reconfigure(ue_id);
                let _ = resp.send(completed(value, stamp_completion, started, unstamped));
            }
            Request::AbortReconf {
                ue_id,
                stamp_completion,
                resp,
            } => {
                let value = core.abort_reconfigure(ue_id);
                let _ = resp.send(completed(value, stamp_completion, started, unstamped));
            }
            Request::Release {
                ue_id,
                stamp_completion,
                resp,
            } => {
                let value = core.release_context(ue_id);
                let _ = resp.send(completed(value, stamp_completion, started, unstamped));
            }
            Request::Lookup {
                ue_id,
                stamp_completion,
                resp,
            } => {
                let value = core.lookup(ue_id);
                let _ = resp.send(completed(value, stamp_completion, started, unstamped));
            }
            Request::Count { resp } => {
                let _ = resp.send(core.count());
            }
            Request::Stop => break,
        }
    }
}
