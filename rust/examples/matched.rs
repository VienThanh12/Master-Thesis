//! Matched-design probe, Rust side. PROBE ONLY, never a reported arm.
//! Twin of `cpp/bench/matched.cpp`. See `docs/OVERLOAD_MECHANISM.md` §4.16.
//!
//! Past saturation the two services differ in how their standard libraries hand a
//! request to a worker and the reply back. This probe runs the same mini-service in both
//! languages around the real `ShardCore`: one worker thread per shard, a fixed ring queue
//! behind a three-state futex mutex, one reply slot per sender, and every wait and wake
//! through the futex system call with the same arguments, issued only when a thread
//! sleeps. Algorithm, memory layout and system calls match, so what differs is each
//! language's own code: `ShardCore`, the dispatch, and the loops.
//!
//! `--design stock` runs the same harness loop through the reported `Service` instead,
//! so within one binary the two modes differ only in the handoff. Senders send back to
//! back, which is the overload state of the campaign. `--self-test` runs one sender
//! through both designs and checks that every operation gets the same result.
//!
//! `--stages` splits each call into four parts on one clock: the queue (from just before
//! the sender hands the request over until the worker starts it), the worker (the
//! operation), the reply (from the worker finishing until the sender holds the result),
//! and the sender (its own time until it hands over the next request). The worker's two
//! stamps are the reported services' own `started` and `done`, so both designs pay the
//! same two extra clock reads. The parts add up to the time per call.
//!
//! The `unsafe` is confined to this probe: the futex system call and the ring that the
//! futex mutex guards. The UECM library itself contains no `unsafe`.

use std::cell::UnsafeCell;
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::sync::mpsc::Receiver;
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

use uecm::hash::shard_index;
use uecm::{
    Completion, Config, CreateParams, DrbEntry, OpResult, ReconfigParams, Service, ShardCore,
    SignalingMsg, UeId,
};

#[cfg(feature = "jemalloc")]
#[global_allocator]
static GLOBAL: tikv_jemallocator::Jemalloc = tikv_jemallocator::Jemalloc;

#[cfg(feature = "jemalloc")]
const ALLOC_NAME: &str = "jemalloc";
#[cfg(not(feature = "jemalloc"))]
const ALLOC_NAME: &str = "system";

#[path = "common/workload.rs"]
mod workload;
use workload::{WKind, WOp, Workload};

const QUEUE_CAPACITY: usize = 1024;

// --- Futex ---------------------------------------------------------------------------

fn futex_wait(word: &AtomicU32, expected: u32) {
    // SAFETY: FUTEX_WAIT reads the aligned 32-bit word, which outlives the call, and
    // writes no user memory. The trailing arguments are unused by this operation.
    unsafe {
        libc::syscall(
            libc::SYS_futex,
            word.as_ptr(),
            libc::FUTEX_WAIT | libc::FUTEX_PRIVATE_FLAG,
            expected,
            std::ptr::null::<libc::timespec>(),
            std::ptr::null::<u32>(),
            0u32,
        );
    }
}

fn futex_wake_one(word: &AtomicU32) {
    // SAFETY: FUTEX_WAKE only uses the word's address as a key and writes no user memory.
    unsafe {
        libc::syscall(
            libc::SYS_futex,
            word.as_ptr(),
            libc::FUTEX_WAKE | libc::FUTEX_PRIVATE_FLAG,
            1u32,
            std::ptr::null::<libc::timespec>(),
            std::ptr::null::<u32>(),
            0u32,
        );
    }
}

/// Three-state futex mutex: 0 unlocked, 1 locked, 2 locked with possible waiters.
struct FutexMutex {
    state: AtomicU32,
}

impl FutexMutex {
    fn new() -> Self {
        Self {
            state: AtomicU32::new(0),
        }
    }

    fn lock(&self) {
        let mut c = match self
            .state
            .compare_exchange(0, 1, Ordering::Acquire, Ordering::Relaxed)
        {
            Ok(_) => return,
            Err(c) => c,
        };
        if c != 2 {
            c = self.state.swap(2, Ordering::Acquire);
        }
        while c != 0 {
            futex_wait(&self.state, 2);
            c = self.state.swap(2, Ordering::Acquire);
        }
    }

    fn unlock(&self) {
        if self.state.swap(0, Ordering::Release) == 2 {
            futex_wake_one(&self.state);
        }
    }
}

// --- Request, queue, reply ---------------------------------------------------------------

#[derive(Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
enum Kind {
    Create,
    Setup,
    Signal,
    AddDrb,
    BeginReconf,
    CompleteReconf,
    AbortReconf,
    Release,
    Stop,
}

/// One tagged struct carries every operation, in the C++ field order.
#[derive(Clone, Copy)]
#[repr(C)]
struct Request {
    kind: Kind,
    reply: u32,
    ue_id: UeId,
    create: CreateParams,
    signaling: SignalingMsg,
    drb: DrbEntry,
    reconfig: ReconfigParams,
}

impl Request {
    fn of(kind: Kind, reply: u32, ue_id: UeId) -> Self {
        Self {
            kind,
            reply,
            ue_id,
            create: CreateParams::default(),
            signaling: SignalingMsg::default(),
            drb: DrbEntry {
                drb_id: 0,
                qos_flow_id: 0,
                teid: 0,
            },
            reconfig: ReconfigParams::default(),
        }
    }
}

struct Ring {
    buf: Vec<Request>,
    head: usize,
    tail: usize,
    len: usize,
    consumer_sleeping: bool,
    producers_sleeping: u32,
}

/// Bounded queue: a fixed ring under the futex mutex. A pusher wakes the worker only if
/// it is asleep, and a popper wakes a pusher only if one is asleep on a full ring.
struct Queue {
    mutex: FutexMutex,
    ring: UnsafeCell<Ring>,
    items: AtomicU32,
    space: AtomicU32,
}

// SAFETY: every access to `ring` happens with `mutex` held; the other fields are atomics.
unsafe impl Sync for Queue {}

impl Queue {
    fn new() -> Self {
        Self {
            mutex: FutexMutex::new(),
            ring: UnsafeCell::new(Ring {
                buf: vec![Request::of(Kind::Stop, 0, 0); QUEUE_CAPACITY],
                head: 0,
                tail: 0,
                len: 0,
                consumer_sleeping: false,
                producers_sleeping: 0,
            }),
            items: AtomicU32::new(0),
            space: AtomicU32::new(0),
        }
    }

    fn push(&self, r: Request) {
        self.mutex.lock();
        loop {
            // SAFETY: `mutex` is held, so no other reference to the ring is live.
            let ring = unsafe { &mut *self.ring.get() };
            if ring.len < QUEUE_CAPACITY {
                ring.buf[ring.tail] = r;
                ring.tail += 1;
                if ring.tail == QUEUE_CAPACITY {
                    ring.tail = 0;
                }
                ring.len += 1;
                let wake = ring.consumer_sleeping;
                if wake {
                    ring.consumer_sleeping = false;
                    self.items.fetch_add(1, Ordering::Relaxed);
                }
                self.mutex.unlock();
                if wake {
                    futex_wake_one(&self.items);
                }
                return;
            }
            ring.producers_sleeping += 1;
            let seq = self.space.load(Ordering::Relaxed);
            self.mutex.unlock();
            futex_wait(&self.space, seq);
            self.mutex.lock();
            // SAFETY: `mutex` is held again.
            unsafe { (*self.ring.get()).producers_sleeping -= 1 };
        }
    }

    fn pop(&self) -> Request {
        self.mutex.lock();
        loop {
            // SAFETY: `mutex` is held, so no other reference to the ring is live.
            let ring = unsafe { &mut *self.ring.get() };
            if ring.len > 0 {
                let r = ring.buf[ring.head];
                ring.head += 1;
                if ring.head == QUEUE_CAPACITY {
                    ring.head = 0;
                }
                ring.len -= 1;
                let wake = ring.producers_sleeping > 0;
                if wake {
                    self.space.fetch_add(1, Ordering::Relaxed);
                }
                self.mutex.unlock();
                if wake {
                    futex_wake_one(&self.space);
                }
                return r;
            }
            ring.consumer_sleeping = true;
            let seq = self.items.load(Ordering::Relaxed);
            self.mutex.unlock();
            futex_wait(&self.items, seq);
            self.mutex.lock();
        }
    }
}

const EMPTY: u32 = 0;
const WAITING: u32 = 1;
const READY: u32 = 2;

/// One per sender, reused for every request it sends. The worker wakes the sender only if
/// the sender is asleep. The two stamps are written only under `--stages`.
#[repr(C, align(64))]
struct ReplySlot {
    state: AtomicU32,
    ok: AtomicU32,
    started_ns: AtomicU64,
    done_ns: AtomicU64,
}

/// Nanoseconds since `base` on the monotonic clock every thread reads.
fn ns_since(base: Instant) -> u64 {
    base.elapsed().as_nanos() as u64
}

// --- The two designs ---------------------------------------------------------------------

trait Backend: Sync {
    fn exec(&self, sender: usize, r: Request) -> bool;
    /// The same call, also returning when the worker started and finished it.
    fn exec_staged(&self, sender: usize, r: Request) -> (bool, u64, u64);
}

struct Stock {
    svc: Service,
    base: Instant,
}

fn take<T>(rx: Receiver<Completion<OpResult<T>>>, base: Instant) -> (bool, u64, u64) {
    let c = rx.recv().expect("completion");
    (
        c.value.is_ok(),
        c.started.duration_since(base).as_nanos() as u64,
        c.done.duration_since(base).as_nanos() as u64,
    )
}

impl Backend for Stock {
    fn exec(&self, _sender: usize, r: Request) -> bool {
        let s = &self.svc;
        match r.kind {
            Kind::Create => s.create_context(r.ue_id, r.create).is_ok(),
            Kind::Setup => s.setup_connection(r.ue_id).is_ok(),
            Kind::Signal => s.handle_signaling(r.ue_id, r.signaling).is_ok(),
            Kind::AddDrb => s.add_drb(r.ue_id, r.drb).is_ok(),
            Kind::BeginReconf => s.begin_reconfigure(r.ue_id, r.reconfig).is_ok(),
            Kind::CompleteReconf => s.complete_reconfigure(r.ue_id).is_ok(),
            Kind::AbortReconf => s.abort_reconfigure(r.ue_id).is_ok(),
            Kind::Release => s.release_context(r.ue_id).is_ok(),
            Kind::Stop => false,
        }
    }

    fn exec_staged(&self, _sender: usize, r: Request) -> (bool, u64, u64) {
        let (s, b) = (&self.svc, self.base);
        match r.kind {
            Kind::Create => take(s.create_context_async(r.ue_id, r.create), b),
            Kind::Setup => take(s.setup_connection_async(r.ue_id), b),
            Kind::Signal => take(s.handle_signaling_async(r.ue_id, r.signaling), b),
            Kind::AddDrb => take(s.add_drb_async(r.ue_id, r.drb), b),
            Kind::BeginReconf => take(s.begin_reconfigure_async(r.ue_id, r.reconfig), b),
            Kind::CompleteReconf => take(s.complete_reconfigure_async(r.ue_id), b),
            Kind::AbortReconf => take(s.abort_reconfigure_async(r.ue_id), b),
            Kind::Release => take(s.release_context_async(r.ue_id), b),
            Kind::Stop => (false, 0, 0),
        }
    }
}

struct Matched {
    n_shards: u64,
    queues: Vec<Queue>,
    slots: Vec<ReplySlot>,
}

impl Backend for Matched {
    fn exec(&self, sender: usize, r: Request) -> bool {
        self.queues[shard_index(r.ue_id, self.n_shards) as usize].push(r);
        let slot = &self.slots[sender];
        if slot
            .state
            .compare_exchange(EMPTY, WAITING, Ordering::Acquire, Ordering::Acquire)
            .is_ok()
        {
            loop {
                futex_wait(&slot.state, WAITING);
                if slot.state.load(Ordering::Acquire) == READY {
                    break;
                }
            }
        }
        let ok = slot.ok.load(Ordering::Relaxed) != 0;
        slot.state.store(EMPTY, Ordering::Relaxed);
        ok
    }

    fn exec_staged(&self, sender: usize, r: Request) -> (bool, u64, u64) {
        // The worker wrote both stamps before its Release swap, which exec observed.
        let ok = self.exec(sender, r);
        let slot = &self.slots[sender];
        (
            ok,
            slot.started_ns.load(Ordering::Relaxed),
            slot.done_ns.load(Ordering::Relaxed),
        )
    }
}

fn worker(
    queue: &Queue,
    slots: &[ReplySlot],
    cfg: Config,
    seq: Arc<AtomicU64>,
    base: Instant,
    stamp: bool,
) {
    let mut core = ShardCore::new(cfg, seq);
    loop {
        let r = queue.pop();
        let started = if stamp { ns_since(base) } else { 0 };
        let ok = match r.kind {
            Kind::Create => core.create_context(r.ue_id, &r.create).is_ok(),
            Kind::Setup => core.setup_connection(r.ue_id).is_ok(),
            Kind::Signal => core.handle_signaling(r.ue_id, &r.signaling).is_ok(),
            Kind::AddDrb => core.add_drb(r.ue_id, r.drb).is_ok(),
            Kind::BeginReconf => core.begin_reconfigure(r.ue_id, &r.reconfig).is_ok(),
            Kind::CompleteReconf => core.complete_reconfigure(r.ue_id).is_ok(),
            Kind::AbortReconf => core.abort_reconfigure(r.ue_id).is_ok(),
            Kind::Release => core.release_context(r.ue_id).is_ok(),
            Kind::Stop => return,
        };
        let slot = &slots[r.reply as usize];
        if stamp {
            slot.done_ns.store(ns_since(base), Ordering::Relaxed);
            slot.started_ns.store(started, Ordering::Relaxed);
        }
        slot.ok.store(ok as u32, Ordering::Relaxed);
        if slot.state.swap(READY, Ordering::Release) == WAITING {
            futex_wake_one(&slot.state);
        }
    }
}

// --- Harness -----------------------------------------------------------------------------

struct Args {
    design: String,
    shards: u64,
    producers: u64,
    active_ues: u64,
    duration_s: f64,
    warmup_s: f64,
    seed: u64,
    self_test: bool,
    stages: bool,
    json: bool,
}

fn parse() -> Args {
    let mut a = Args {
        design: "matched".to_string(),
        shards: 7,
        producers: 7,
        active_ues: 5000,
        duration_s: 3.0,
        warmup_s: 1.0,
        seed: 42,
        self_test: false,
        stages: false,
        json: false,
    };
    let argv: Vec<String> = std::env::args().collect();
    let mut i = 1;
    while i < argv.len() {
        let k = argv[i].as_str();
        let mut val = || -> String {
            i += 1;
            argv.get(i).cloned().unwrap_or_default()
        };
        match k {
            "--design" => a.design = val(),
            "--shards" => a.shards = val().parse().expect("--shards"),
            "--producers" => a.producers = val().parse().expect("--producers"),
            "--active-ues" => a.active_ues = val().parse().expect("--active-ues"),
            "--duration-s" => a.duration_s = val().parse().expect("--duration-s"),
            "--warmup-s" => a.warmup_s = val().parse().expect("--warmup-s"),
            "--seed" => a.seed = val().parse().expect("--seed"),
            "--self-test" => a.self_test = true,
            "--stages" => a.stages = true,
            "--json" => a.json = true,
            other => {
                eprintln!("unknown arg: {other}");
                std::process::exit(2);
            }
        }
        i += 1;
    }
    if a.design != "matched" && a.design != "stock" {
        eprintln!("--design must be matched or stock");
        std::process::exit(2);
    }
    if a.shards == 0 || a.producers == 0 {
        eprintln!("--shards and --producers must be positive");
        std::process::exit(2);
    }
    a
}

/// (user CPU s, sys CPU s) for the whole process. As in `bench.rs`.
fn cpu_times() -> (f64, f64) {
    use std::mem::MaybeUninit;
    // SAFETY: getrusage writes a fully-initialised rusage into the provided pointer.
    unsafe {
        let mut ru = MaybeUninit::<libc::rusage>::zeroed();
        libc::getrusage(libc::RUSAGE_SELF, ru.as_mut_ptr());
        let ru = ru.assume_init();
        (
            ru.ru_utime.tv_sec as f64 + ru.ru_utime.tv_usec as f64 / 1e6,
            ru.ru_stime.tv_sec as f64 + ru.ru_stime.tv_usec as f64 / 1e6,
        )
    }
}

fn sleep_until(t: Instant) {
    let now = Instant::now();
    if t > now {
        thread::sleep(t - now);
    }
}

/// The same mapping from a generated operation to its arguments as `bench.rs`.
fn request_for(op: &WOp, id: UeId, reply: u32) -> Request {
    let mut r = Request::of(Kind::Stop, reply, id);
    match op.kind {
        WKind::Create => {
            r.kind = Kind::Create;
            r.create.serving_cell_id = op.slot as u32;
        }
        WKind::Setup => r.kind = Kind::Setup,
        WKind::Signal => {
            r.kind = Kind::Signal;
            r.signaling.kind = 1;
            r.signaling.payload_len = 4;
        }
        WKind::AddDrb => {
            r.kind = Kind::AddDrb;
            r.drb = DrbEntry {
                drb_id: op.drb_id,
                qos_flow_id: 0,
                teid: op.slot as u32,
            };
        }
        WKind::BeginReconf => {
            r.kind = Kind::BeginReconf;
            r.reconfig.target_cell_id = op.slot as u32 + 1;
        }
        WKind::CompleteReconf => r.kind = Kind::CompleteReconf,
        WKind::AbortReconf => r.kind = Kind::AbortReconf,
        WKind::Release => r.kind = Kind::Release,
    }
    r
}

#[derive(Default)]
struct SenderOut {
    ops: u64,
    errors: u64,
    queue_ns: u64,
    worker_ns: u64,
    reply_ns: u64,
    sender_ns: u64,
    gaps: u64,
}

/// Senders send back to back. Operations that finish inside [t0, t1] are counted, and
/// process CPU is read at t0 and t1.
fn drive<B: Backend>(b: &B, a: &Args, clock: Instant) -> (Vec<SenderOut>, (f64, f64), (f64, f64)) {
    let start = Instant::now();
    let t0 = start + Duration::from_secs_f64(a.warmup_s);
    let t1 = t0 + Duration::from_secs_f64(a.duration_s);
    let (t0_ns, t1_ns) = (
        t0.duration_since(clock).as_nanos() as u64,
        t1.duration_since(clock).as_nanos() as u64,
    );
    thread::scope(|sc| {
        let handles: Vec<_> = (0..a.producers)
            .map(|p| {
                sc.spawn(move || {
                    let mut wl = Workload::new(a.active_ues, a.seed + p);
                    let id_base = p * 100_000_000 + 1;
                    let mut out = SenderOut::default();
                    let mut prev_back: Option<u64> = None;
                    loop {
                        let op = wl.next();
                        let req = request_for(&op, id_base + op.slot, p as u32);
                        if a.stages {
                            let sent = ns_since(clock);
                            let (ok, started, finished) = b.exec_staged(p as usize, req);
                            let back = ns_since(clock);
                            if back >= t1_ns {
                                break;
                            }
                            if back >= t0_ns {
                                out.ops += 1;
                                if !ok {
                                    out.errors += 1;
                                }
                                out.queue_ns += started.saturating_sub(sent);
                                out.worker_ns += finished.saturating_sub(started);
                                out.reply_ns += back.saturating_sub(finished);
                                if let Some(prev) = prev_back {
                                    out.sender_ns += sent.saturating_sub(prev);
                                    out.gaps += 1;
                                }
                            }
                            prev_back = Some(back);
                            continue;
                        }
                        let ok = b.exec(p as usize, req);
                        let done = Instant::now();
                        if done >= t1 {
                            break;
                        }
                        if done >= t0 {
                            out.ops += 1;
                            if !ok {
                                out.errors += 1;
                            }
                        }
                    }
                    out
                })
            })
            .collect();
        sleep_until(t0);
        let cpu0 = cpu_times();
        sleep_until(t1);
        let cpu1 = cpu_times();
        let outs = handles.into_iter().map(|h| h.join().expect("sender")).collect();
        (outs, cpu0, cpu1)
    })
}

/// Runs `f` with the matched mini-service up, then stops its workers.
fn with_matched<R>(a: &Args, clock: Instant, f: impl FnOnce(&Matched) -> R) -> R {
    let m = Matched {
        n_shards: a.shards,
        queues: (0..a.shards).map(|_| Queue::new()).collect(),
        slots: (0..a.producers)
            .map(|_| ReplySlot {
                state: AtomicU32::new(EMPTY),
                ok: AtomicU32::new(0),
                started_ns: AtomicU64::new(0),
                done_ns: AtomicU64::new(0),
            })
            .collect(),
    };
    let cfg = Config {
        n_shards: a.shards,
        ..Config::default()
    };
    let seq = Arc::new(AtomicU64::new(0));
    let stamp = a.stages;
    thread::scope(|sc| {
        for s in 0..a.shards as usize {
            let (queue, slots, seq) = (&m.queues[s], &m.slots[..], Arc::clone(&seq));
            sc.spawn(move || worker(queue, slots, cfg, seq, clock, stamp));
        }
        let result = f(&m);
        for q in &m.queues {
            q.push(Request::of(Kind::Stop, 0, 0));
        }
        result
    })
}

fn with_stock<R>(a: &Args, clock: Instant, f: impl FnOnce(&Stock) -> R) -> R {
    let cfg = Config {
        n_shards: a.shards,
        stamp_start: a.stages,
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();
    let mut stock = Stock { svc, base: clock };
    let result = f(&stock);
    stock.svc.shutdown();
    result
}

/// One sender, `n` generated operations: (ok count, error count, per-kind ok counts).
fn sequence<B: Backend>(b: &B, a: &Args, n: u64) -> (u64, u64, [u64; 8]) {
    let mut wl = Workload::new(a.active_ues, a.seed);
    let (mut ok, mut err, mut kinds) = (0u64, 0u64, [0u64; 8]);
    for _ in 0..n {
        let op = wl.next();
        if b.exec(0, request_for(&op, 1 + op.slot, 0)) {
            ok += 1;
            kinds[op.kind as usize] += 1;
        } else {
            err += 1;
        }
    }
    (ok, err, kinds)
}

fn main() {
    let a = parse();
    let clock = Instant::now();
    if a.self_test {
        let n = 20_000;
        let s = with_stock(&a, clock, |b| sequence(b, &a, n));
        let m = with_matched(&a, clock, |b| sequence(b, &a, n));
        println!(
            "self-test rust: stock ok {} err {} kinds {:?} | matched ok {} err {} kinds {:?}",
            s.0, s.1, s.2, m.0, m.1, m.2
        );
        std::process::exit(if s == m { 0 } else { 1 });
    }
    let (outs, cpu0, cpu1) = if a.design == "matched" {
        with_matched(&a, clock, |b| drive(b, &a, clock))
    } else {
        with_stock(&a, clock, |b| drive(b, &a, clock))
    };
    let ops: u64 = outs.iter().map(|o| o.ops).sum();
    let errors: u64 = outs.iter().map(|o| o.errors).sum();
    let per_op_us = |field: fn(&SenderOut) -> u64| {
        let n: u64 = if ops > 0 { ops } else { 1 };
        outs.iter().map(field).sum::<u64>() as f64 / n as f64 / 1e3
    };
    let gaps: u64 = outs.iter().map(|o| o.gaps).sum::<u64>().max(1);
    let stages = if a.stages {
        format!(
            ",\"stages\":true,\"queue_us\":{:.4},\"worker_us\":{:.4},\"reply_us\":{:.4},\"sender_us\":{:.4}",
            per_op_us(|o| o.queue_ns),
            per_op_us(|o| o.worker_ns),
            per_op_us(|o| o.reply_ns),
            outs.iter().map(|o| o.sender_ns).sum::<u64>() as f64 / gaps as f64 / 1e3
        )
    } else {
        String::new()
    };
    let user = cpu1.0 - cpu0.0;
    let sys = cpu1.1 - cpu0.1;
    let ops_per_s = ops as f64 / a.duration_s;
    let cpu_us_per_op = if ops > 0 { (user + sys) / ops as f64 * 1e6 } else { 0.0 };
    let us_per_op_per_sender = if ops > 0 {
        a.producers as f64 * a.duration_s / ops as f64 * 1e6
    } else {
        0.0
    };
    if a.json {
        println!(
            "{{\"schema\":\"matched\",\"lang\":\"rust\",\"alloc\":\"{ALLOC_NAME}\",\"design\":\"{}\",\
\"shards\":{},\"producers\":{},\"active_ues\":{},\"seed\":{},\"duration_s\":{:.3},\"warmup_s\":{:.3},\
\"ops\":{ops},\"errors\":{errors},\"ops_per_s\":{ops_per_s:.1},\"us_per_op_per_sender\":{us_per_op_per_sender:.4},\
\"cpu_user_s\":{user:.4},\"cpu_sys_s\":{sys:.4},\"cpu_us_per_op\":{cpu_us_per_op:.4}{stages}}}",
            a.design, a.shards, a.producers, a.active_ues, a.seed, a.duration_s, a.warmup_s
        );
    } else {
        println!(
            "UECM matched probe [rust, alloc={ALLOC_NAME}, design={}] ops/s={ops_per_s:.0} \
us/op/sender={us_per_op_per_sender:.3} cpu us/op={cpu_us_per_op:.3} errors={errors}",
            a.design
        );
    }
}
