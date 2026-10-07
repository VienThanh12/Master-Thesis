//! Method 3 engineering pilot. `--workload signal` repeats signalling after a
//! preload. `--workload mixed` walks the same lifecycle generator as `bench.rs`.
//! Several requests stay in flight. Each producer pre-plans `ops` arrivals at a
//! fixed interval, keeps each intended timestamp, and blocks only when the shard
//! queue is full. One UE hashes to one shard, and that shard is FIFO, so one
//! phone's steps stay in order. Different phones overlap. Warmup uses the
//! synchronous API and is fully drained before the first planned arrival. The
//! measured phase records worker completion (`Completion.done`) against that
//! intended timestamp, plus admission, in-service, and observation components.
//! `--stamp-start` is diagnostic only. No coordinated-omission backfill.
//!
//! This does not replace `examples/bench.rs`.

use std::collections::VecDeque;
use std::sync::mpsc::{Receiver, RecvTimeoutError, TryRecvError};
use std::sync::{Barrier, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use hdrhistogram::Histogram;
use uecm::{
    hash::shard_index, Config, CreateParams, DrbEntry, OpResult, ReconfigParams, Service,
    SignalingAck, SignalingMsg, UeId,
};

#[path = "common/workload.rs"]
mod workload;
use workload::{WKind, WOp, Workload};

#[cfg(feature = "jemalloc")]
#[global_allocator]
static GLOBAL: tikv_jemallocator::Jemalloc = tikv_jemallocator::Jemalloc;

#[cfg(feature = "jemalloc")]
const ALLOC_NAME: &str = "jemalloc";
#[cfg(not(feature = "jemalloc"))]
const ALLOC_NAME: &str = "system";

#[cfg(feature = "mutex-queue")]
const QUEUE_NAME: &str = "mutex";
#[cfg(not(feature = "mutex-queue"))]
const QUEUE_NAME: &str = "channel";

const HDR_LOW: u64 = 1;
const HDR_HIGH: u64 = 60 * 1_000_000_000; // 60 s in ns
const HDR_SIG: u8 = 3;

#[derive(Clone, Copy)]
struct SplitMix64 {
    s: u64,
}

impl SplitMix64 {
    fn next(&mut self) -> u64 {
        self.s = self.s.wrapping_add(0x9E3779B97F4A7C15);
        let mut z = self.s;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
        z ^ (z >> 31)
    }
}

struct Args {
    shards: u64,
    queue_capacity: usize,
    producers: u64,
    preload: u64,
    ops: u64,
    warmup: u64,
    seed: u64,
    rate: f64,
    drain_timeout_s: f64,
    hist_out: String,
    run_id: String,
    workload: String,
    active_ues: u64,
    json: bool,
    stamp_start: bool,
}

fn parse() -> Args {
    let mut a = Args {
        shards: 8,
        queue_capacity: 1024,
        producers: 0,
        preload: 10_000,
        ops: 200_000,
        warmup: 0,
        seed: 42,
        rate: 0.0,
        drain_timeout_s: 5.0,
        hist_out: String::new(),
        run_id: String::new(),
        workload: "signal".to_string(),
        active_ues: 5000,
        json: false,
        stamp_start: false,
    };
    let argv: Vec<String> = std::env::args().collect();
    let mut i = 1;
    while i < argv.len() {
        let k = argv[i].as_str();
        let mut val = || -> String {
            i += 1;
            argv.get(i).cloned().unwrap_or_else(|| "0".to_string())
        };
        match k {
            "--shards" => a.shards = val().parse().unwrap_or(8),
            "--queue-capacity" => a.queue_capacity = val().parse().unwrap_or(1024),
            "--producers" => a.producers = val().parse().unwrap_or(0),
            "--preload" => a.preload = val().parse().unwrap_or(10_000),
            "--ops" => a.ops = val().parse().unwrap_or(200_000),
            "--warmup" => a.warmup = val().parse().unwrap_or(0),
            "--seed" => a.seed = val().parse().unwrap_or(42),
            "--rate" => match val().parse::<f64>() {
                Ok(v) => a.rate = v,
                Err(_) => {
                    eprintln!("invalid --rate");
                    std::process::exit(2);
                }
            },
            "--drain-timeout-s" => match val().parse::<f64>() {
                Ok(v) => a.drain_timeout_s = v,
                Err(_) => {
                    eprintln!("invalid --drain-timeout-s");
                    std::process::exit(2);
                }
            },
            "--hist-out" => a.hist_out = val(),
            "--run-id" => a.run_id = val(),
            "--workload" => a.workload = val(),
            "--active-ues" => a.active_ues = val().parse().unwrap_or(5000),
            "--json" => a.json = true,
            "--stamp-start" => a.stamp_start = true,
            other => {
                eprintln!("unknown arg: {other}");
                std::process::exit(2);
            }
        }
        i += 1;
    }
    if !a.rate.is_finite() || a.rate <= 0.0 {
        eprintln!("--rate must be > 0");
        std::process::exit(2);
    }
    if a.drain_timeout_s < 0.0 {
        eprintln!("--drain-timeout-s must be >= 0");
        std::process::exit(2);
    }
    if a.workload != "signal" && a.workload != "mixed" {
        eprintln!("unknown --workload '{}' (use signal|mixed)", a.workload);
        std::process::exit(2);
    }
    if a.producers == 0 {
        a.producers = a.shards;
    }
    // Same default as the reported bench: an explicit 0 means "auto".
    if a.warmup == 0 {
        a.warmup = a.ops / 10;
        if a.workload == "mixed" {
            let bootstrap = 2 * a.active_ues;
            if bootstrap > a.warmup {
                a.warmup = bootstrap;
            }
        }
    }
    a
}

fn new_hist() -> Histogram<u64> {
    Histogram::new_with_bounds(HDR_LOW, HDR_HIGH, HDR_SIG).expect("valid hdr bounds")
}

fn record_ns(hist: &mut Histogram<u64>, ns: u128, overflows: &mut u64) {
    // `record` rejects out-of-range samples. A zero duration is below the 1 ns
    // bound, so it is stored as 1 ns. Anything above the 60 s bound is an overflow.
    if ns > HDR_HIGH as u128 {
        *overflows += 1;
        return;
    }
    let v = u64::try_from(ns.max(1)).unwrap_or(u64::MAX);
    if hist.record(v).is_err() {
        *overflows += 1;
    }
}

struct Observed {
    done: Instant,
    started: Instant,
    ok: bool,
}

enum Pending {
    Unit(Receiver<uecm::Completion<OpResult<()>>>),
    Signal(Receiver<uecm::Completion<OpResult<SignalingAck>>>),
}

enum Recv {
    Ready(Observed),
    Pending,
    Closed,
}

fn try_pending(pending: &Pending) -> Recv {
    match pending {
        Pending::Unit(rx) => match rx.try_recv() {
            Ok(c) => Recv::Ready(Observed {
                done: c.done,
                started: c.started,
                ok: c.value.is_ok(),
            }),
            Err(TryRecvError::Empty) => Recv::Pending,
            Err(TryRecvError::Disconnected) => Recv::Closed,
        },
        Pending::Signal(rx) => match rx.try_recv() {
            Ok(c) => Recv::Ready(Observed {
                done: c.done,
                started: c.started,
                ok: c.value.is_ok(),
            }),
            Err(TryRecvError::Empty) => Recv::Pending,
            Err(TryRecvError::Disconnected) => Recv::Closed,
        },
    }
}

fn wait_pending(pending: &Pending, remaining: Duration) -> Recv {
    match pending {
        Pending::Unit(rx) => match rx.recv_timeout(remaining) {
            Ok(c) => Recv::Ready(Observed {
                done: c.done,
                started: c.started,
                ok: c.value.is_ok(),
            }),
            Err(RecvTimeoutError::Timeout) => Recv::Pending,
            Err(RecvTimeoutError::Disconnected) => Recv::Closed,
        },
        Pending::Signal(rx) => match rx.recv_timeout(remaining) {
            Ok(c) => Recv::Ready(Observed {
                done: c.done,
                started: c.started,
                ok: c.value.is_ok(),
            }),
            Err(RecvTimeoutError::Timeout) => Recv::Pending,
            Err(RecvTimeoutError::Disconnected) => Recv::Closed,
        },
    }
}

fn exec_sync(svc: &Service, op: &WOp, id: UeId) -> bool {
    match op.kind {
        WKind::Create => svc
            .create_context(
                id,
                CreateParams {
                    serving_cell_id: op.slot as u32,
                    security_key: [0u8; 32],
                },
            )
            .is_ok(),
        WKind::Setup => svc.setup_connection(id).is_ok(),
        WKind::Signal => svc
            .handle_signaling(
                id,
                SignalingMsg {
                    kind: 1,
                    payload_len: 4,
                    payload: [0u8; 64],
                },
            )
            .is_ok(),
        WKind::AddDrb => svc
            .add_drb(
                id,
                DrbEntry {
                    drb_id: op.drb_id,
                    qos_flow_id: 0,
                    teid: op.slot as u32,
                },
            )
            .is_ok(),
        WKind::BeginReconf => svc
            .begin_reconfigure(
                id,
                ReconfigParams {
                    target_cell_id: op.slot as u32 + 1,
                },
            )
            .is_ok(),
        WKind::CompleteReconf => svc.complete_reconfigure(id).is_ok(),
        WKind::AbortReconf => svc.abort_reconfigure(id).is_ok(),
        WKind::Release => svc.release_context(id).is_ok(),
    }
}

fn submit_async(svc: &Service, op: &WOp, id: UeId, msg: SignalingMsg) -> Pending {
    match op.kind {
        WKind::Create => Pending::Unit(svc.create_context_async(
            id,
            CreateParams {
                serving_cell_id: op.slot as u32,
                security_key: [0u8; 32],
            },
        )),
        WKind::Setup => Pending::Unit(svc.setup_connection_async(id)),
        WKind::Signal => Pending::Signal(svc.handle_signaling_async(id, msg)),
        WKind::AddDrb => Pending::Unit(svc.add_drb_async(
            id,
            DrbEntry {
                drb_id: op.drb_id,
                qos_flow_id: 0,
                teid: op.slot as u32,
            },
        )),
        WKind::BeginReconf => Pending::Unit(svc.begin_reconfigure_async(
            id,
            ReconfigParams {
                target_cell_id: op.slot as u32 + 1,
            },
        )),
        WKind::CompleteReconf => Pending::Unit(svc.complete_reconfigure_async(id)),
        WKind::AbortReconf => Pending::Unit(svc.abort_reconfigure_async(id)),
        WKind::Release => Pending::Unit(svc.release_context_async(id)),
    }
}

struct Ticket {
    intended: Instant,
    submit_begin: Instant,
    enqueued: Instant,
    pending: Pending,
}

struct Counts {
    enqueue_started: u64,
    enqueued: u64,
    completed_within_window: u64,
    completed_during_drain: u64,
    errors: u64,
    timed_out: u64,
    histogram_overflows: u64,
}

struct Hists {
    primary: Histogram<u64>,
    admission: Histogram<u64>,
    in_service: Histogram<u64>,
    observation: Histogram<u64>,
    queue_wait: Histogram<u64>,
    execute: Histogram<u64>,
    stamp_start: bool,
}

struct ProducerOut {
    counts: Counts,
    hists: Hists,
    kinds: [u64; 8],
    drain_s: f64,
}

#[derive(Clone, Copy)]
struct Schedule {
    n_shards: u64,
    interval: Duration,
    window: Duration,
    drain_timeout: Duration,
}

fn on_complete(
    ticket: Ticket,
    completion: Observed,
    observed: Instant,
    window_end: Instant,
    counts: &mut Counts,
    hists: &mut Hists,
) {
    debug_assert!(ticket.submit_begin <= ticket.enqueued);
    if !completion.ok {
        counts.errors += 1;
    }
    let done = completion.done;
    if done <= window_end {
        counts.completed_within_window += 1;
    } else {
        counts.completed_during_drain += 1;
    }
    record_ns(
        &mut hists.primary,
        done.saturating_duration_since(ticket.intended).as_nanos(),
        &mut counts.histogram_overflows,
    );
    record_ns(
        &mut hists.admission,
        ticket
            .enqueued
            .saturating_duration_since(ticket.intended)
            .as_nanos(),
        &mut counts.histogram_overflows,
    );
    record_ns(
        &mut hists.in_service,
        done.saturating_duration_since(ticket.enqueued).as_nanos(),
        &mut counts.histogram_overflows,
    );
    record_ns(
        &mut hists.observation,
        observed.saturating_duration_since(done).as_nanos(),
        &mut counts.histogram_overflows,
    );
    if hists.stamp_start {
        record_ns(
            &mut hists.queue_wait,
            completion
                .started
                .saturating_duration_since(ticket.enqueued)
                .as_nanos(),
            &mut counts.histogram_overflows,
        );
        record_ns(
            &mut hists.execute,
            done.saturating_duration_since(completion.started).as_nanos(),
            &mut counts.histogram_overflows,
        );
    }
}

/// Non-blocking: only the front of each lane, and every front that is already ready.
fn harvest_ready(
    lanes: &mut [VecDeque<Ticket>],
    window_end: Instant,
    counts: &mut Counts,
    hists: &mut Hists,
) {
    for lane in lanes.iter_mut() {
        while let Some(front) = lane.front() {
            match try_pending(&front.pending) {
                Recv::Ready(completion) => {
                    let observed = Instant::now();
                    let ticket = lane.pop_front().expect("front");
                    on_complete(ticket, completion, observed, window_end, counts, hists);
                }
                Recv::Pending => break,
                Recv::Closed => {
                    lane.pop_front();
                    counts.errors += 1;
                }
            }
        }
    }
}

/// Block on lane fronts until `deadline`. Anything still queued after that is timed out.
fn drain(
    lanes: &mut [VecDeque<Ticket>],
    deadline: Instant,
    window_end: Instant,
    counts: &mut Counts,
    hists: &mut Hists,
) -> f64 {
    let drain_start = Instant::now();
    loop {
        harvest_ready(lanes, window_end, counts, hists);
        if lanes.iter().all(|lane| lane.is_empty()) {
            break;
        }
        let now = Instant::now();
        if now >= deadline {
            break;
        }
        let idx = lanes
            .iter()
            .enumerate()
            .filter(|(_, lane)| !lane.is_empty())
            .min_by_key(|(_, lane)| lane.front().expect("non-empty").intended)
            .map(|(i, _)| i)
            .expect("a front");
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            break;
        }
        match wait_pending(&lanes[idx].front().expect("front").pending, remaining) {
            Recv::Ready(completion) => {
                let observed = Instant::now();
                let ticket = lanes[idx].pop_front().expect("front");
                on_complete(ticket, completion, observed, window_end, counts, hists);
            }
            Recv::Pending => break,
            Recv::Closed => {
                lanes[idx].pop_front();
                counts.errors += 1;
            }
        }
    }
    harvest_ready(lanes, window_end, counts, hists);
    for lane in lanes.iter_mut() {
        counts.timed_out += lane.len() as u64;
        lane.clear();
    }
    drain_start.elapsed().as_secs_f64()
}

fn run_producer(
    svc: &Service,
    producer: u64,
    args: &Args,
    schedule: Schedule,
    ready: &Barrier,
    origin_slot: &Mutex<Option<Instant>>,
) -> ProducerOut {
    let mixed = args.workload == "mixed";
    let range = if args.preload == 0 { 1 } else { args.preload };
    let base = producer * 100_000_000 + 1;
    let mut rng = SplitMix64 {
        s: args.seed.wrapping_add(producer),
    };
    let mut wl = Workload::new(args.active_ues, args.seed.wrapping_add(producer));
    let msg = SignalingMsg {
        kind: 1,
        payload_len: 4,
        payload: [0u8; 64],
    };
    let mut lanes: Vec<VecDeque<Ticket>> =
        (0..schedule.n_shards).map(|_| VecDeque::new()).collect();
    let mut kinds = [0u64; 8];
    let mut counts = Counts {
        enqueue_started: 0,
        enqueued: 0,
        completed_within_window: 0,
        completed_during_drain: 0,
        errors: 0,
        timed_out: 0,
        histogram_overflows: 0,
    };
    if mixed {
        // The generator advances here, then the measured loop continues it.
        for _ in 0..args.warmup {
            let op = wl.next();
            if !exec_sync(svc, &op, base + op.slot) {
                counts.errors += 1;
            }
        }
    } else {
        // Signal warmup consumed these draws in a previous pass. Skip them so measured ids match.
        for _ in 0..args.warmup {
            let _ = rng.next();
        }
    }
    let mut hists = Hists {
        primary: new_hist(),
        admission: new_hist(),
        in_service: new_hist(),
        observation: new_hist(),
        queue_wait: new_hist(),
        execute: new_hist(),
        stamp_start: args.stamp_start,
    };

    // Histograms are allocated before the barrier, so the shared origin is the
    // moment every producer is ready to submit, not the moment the threads were spawned.
    ready.wait();
    let origin = {
        let mut slot = origin_slot.lock().expect("origin");
        *slot.get_or_insert_with(Instant::now)
    };
    let window_end = origin + schedule.window;
    let deadline = window_end + schedule.drain_timeout;

    for n in 0..args.ops {
        let step_ns = u64::try_from(schedule.interval.as_nanos()).unwrap_or(u64::MAX);
        let intended = origin + Duration::from_nanos(step_ns.saturating_mul(n));
        let now = Instant::now();
        if intended > now {
            thread::sleep(intended - now);
        }
        let (id, kind, op) = if mixed {
            let op = wl.next();
            (base + op.slot, op.kind as usize, Some(op))
        } else {
            (base + (rng.next() % range), WKind::Signal as usize, None)
        };
        let shard = shard_index(id, schedule.n_shards) as usize;
        let submit_begin = Instant::now();
        counts.enqueue_started += 1;
        let pending = match op {
            Some(op) => submit_async(svc, &op, id, msg),
            None => Pending::Signal(svc.handle_signaling_async(id, msg)),
        };
        let enqueued = Instant::now();
        counts.enqueued += 1;
        kinds[kind] += 1;
        lanes[shard].push_back(Ticket {
            intended,
            submit_begin,
            enqueued,
            pending,
        });
        harvest_ready(&mut lanes, window_end, &mut counts, &mut hists);
    }

    let drain_s = drain(&mut lanes, deadline, window_end, &mut counts, &mut hists);
    ProducerOut {
        counts,
        hists,
        kinds,
        drain_s,
    }
}

fn quantile(h: &Histogram<u64>, q: f64) -> u64 {
    if h.is_empty() {
        0
    } else {
        h.value_at_quantile(q)
    }
}

fn hist_max(h: &Histogram<u64>) -> u64 {
    if h.is_empty() {
        0
    } else {
        h.max()
    }
}

fn dump_hist(out: &mut String, key: &str, h: &Histogram<u64>) {
    use std::fmt::Write as _;
    let _ = write!(
        out,
        ",\"{key}\":{{\"total\":{},\"max\":{},\"pairs\":[",
        h.len(),
        hist_max(h)
    );
    let mut first = true;
    for v in h.iter_recorded() {
        if !first {
            out.push(',');
        }
        first = false;
        let _ = write!(out, "[{},{}]", v.value_iterated_to(), v.count_at_value());
    }
    out.push_str("]}");
}

fn write_hist_sidecar(
    args: &Args,
    ops_total: u64,
    primary: &Histogram<u64>,
    admission: &Histogram<u64>,
    in_service: &Histogram<u64>,
    observation: &Histogram<u64>,
    queue_wait: &Histogram<u64>,
    execute: &Histogram<u64>,
) {
    use std::io::Write as _;
    let mut line = format!(
        "{{\"schema\":\"pipeline\",\"run_id\":\"{}\",\"lang\":\"rust\",\"alloc\":\"{}\",\
\"workload\":\"{}\",\"shards\":{},\"producers\":{},\"rate\":{:.1},\"seed\":{},\
\"ops_total\":{},\"hdr\":{{\"low\":{},\"high\":{},\"sig\":{}}}",
        args.run_id,
        ALLOC_NAME,
        args.workload,
        args.shards,
        args.producers,
        args.rate,
        args.seed,
        ops_total,
        HDR_LOW,
        HDR_HIGH,
        HDR_SIG
    );
    dump_hist(&mut line, "primary", primary);
    dump_hist(&mut line, "admission", admission);
    dump_hist(&mut line, "in_service", in_service);
    dump_hist(&mut line, "observation", observation);
    if args.stamp_start {
        dump_hist(&mut line, "queue_wait", queue_wait);
        dump_hist(&mut line, "execute", execute);
    }
    line.push_str("}\n");

    match std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&args.hist_out)
    {
        Ok(mut f) => {
            if let Err(e) = f.write_all(line.as_bytes()) {
                eprintln!("warning: cannot write --hist-out '{}': {e}", args.hist_out);
            }
        }
        Err(e) => eprintln!("warning: cannot open --hist-out '{}': {e}", args.hist_out),
    }
}

fn part_json(h: &Histogram<u64>) -> String {
    format!(
        "{{\"p50\":{},\"p99\":{},\"p999\":{},\"max\":{}}}",
        quantile(h, 0.50),
        quantile(h, 0.99),
        quantile(h, 0.999),
        hist_max(h)
    )
}

fn main() {
    let args = parse();
    let interval_ns = (1e9 / args.rate) as u64;
    if interval_ns == 0 {
        eprintln!("--rate is too high to schedule a 1 ns interval");
        std::process::exit(2);
    }
    let interval = Duration::from_nanos(interval_ns);
    let window = Duration::from_nanos(interval_ns.saturating_mul(args.ops));
    let drain_timeout = Duration::from_secs_f64(args.drain_timeout_s);

    let cfg = Config {
        n_shards: args.shards,
        queue_capacity: args.queue_capacity,
        stamp_start: args.stamp_start,
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();
    let n_shards = svc.n_shards();
    let schedule = Schedule {
        n_shards,
        interval,
        window,
        drain_timeout,
    };
    let range = if args.preload == 0 { 1 } else { args.preload };

    if args.workload != "mixed" {
    thread::scope(|s| {
        for p in 0..args.producers {
            let svc = &svc;
            s.spawn(move || {
                let base = p * 100_000_000 + 1;
                for i in 0..range {
                    let id: UeId = base + i;
                    let _ = svc.create_context(
                        id,
                        CreateParams {
                            serving_cell_id: p as u32,
                            security_key: [0u8; 32],
                        },
                    );
                    let _ = svc.setup_connection(id);
                }
            });
        }
    });

    thread::scope(|s| {
        for p in 0..args.producers {
            let svc = &svc;
            let args = &args;
            s.spawn(move || {
                let range = if args.preload == 0 { 1 } else { args.preload };
                let base = p * 100_000_000 + 1;
                let mut rng = SplitMix64 {
                    s: args.seed.wrapping_add(p),
                };
                let msg = SignalingMsg {
                    kind: 1,
                    payload_len: 4,
                    payload: [0u8; 64],
                };
                for _ in 0..args.warmup {
                    let id = base + (rng.next() % range);
                    let _ = svc.handle_signaling(id, msg);
                }
            });
        }
    });
    }

    // One shared schedule, taken once every producer is ready to submit.
    // The drain deadline is that origin plus the planned window plus the timeout.
    let ready = Barrier::new(args.producers.max(1) as usize);
    let origin_slot = Mutex::new(None);

    let mut outs = Vec::with_capacity(args.producers as usize);
    thread::scope(|s| {
        let mut handles = Vec::with_capacity(args.producers as usize);
        for p in 0..args.producers {
            let svc = &svc;
            let args = &args;
            let ready = &ready;
            let origin_slot = &origin_slot;
            handles.push(s.spawn(move || run_producer(svc, p, args, schedule, ready, origin_slot)));
        }
        for h in handles {
            outs.push(h.join().expect("producer"));
        }
    });
    svc.shutdown();

    let mut primary = new_hist();
    let mut admission = new_hist();
    let mut in_service = new_hist();
    let mut observation = new_hist();
    let mut queue_wait = new_hist();
    let mut execute = new_hist();
    let mut enqueue_started = 0u64;
    let mut enqueued = 0u64;
    let mut completed_within_window = 0u64;
    let mut completed_during_drain = 0u64;
    let mut errors = 0u64;
    let mut timed_out = 0u64;
    let mut histogram_overflows = 0u64;
    let mut drain_s = 0.0f64;
    let mut kinds = [0u64; 8];
    for o in &outs {
        primary.add(&o.hists.primary).expect("primary");
        admission.add(&o.hists.admission).expect("admission");
        in_service.add(&o.hists.in_service).expect("in_service");
        observation.add(&o.hists.observation).expect("observation");
        queue_wait.add(&o.hists.queue_wait).expect("queue_wait");
        execute.add(&o.hists.execute).expect("execute");
        enqueue_started += o.counts.enqueue_started;
        enqueued += o.counts.enqueued;
        completed_within_window += o.counts.completed_within_window;
        completed_during_drain += o.counts.completed_during_drain;
        errors += o.counts.errors;
        timed_out += o.counts.timed_out;
        histogram_overflows += o.counts.histogram_overflows;
        drain_s = drain_s.max(o.drain_s);
        for i in 0..8 {
            kinds[i] += o.kinds[i];
        }
    }

    let planned = args.producers.saturating_mul(args.ops);
    let arrival_window_s = window.as_secs_f64();
    let throughput_ops_s = if arrival_window_s > 0.0 {
        completed_within_window as f64 / arrival_window_s
    } else {
        0.0
    };
    let valid = timed_out == 0 && histogram_overflows == 0 && errors == 0;
    let ops_total = completed_within_window + completed_during_drain;

    let primary_ns = format!(
        "{{\"p50\":{},\"p99\":{},\"p999\":{},\"p9999\":{},\"max\":{}}}",
        quantile(&primary, 0.50),
        quantile(&primary, 0.99),
        quantile(&primary, 0.999),
        quantile(&primary, 0.9999),
        hist_max(&primary)
    );

    if args.json {
        println!(
            "{{\"schema\":\"pipeline\",\"lang\":\"rust\",\"alloc\":\"{alloc}\",\
\"workload\":\"{workload}\",\"shards\":{shards},\"queue_capacity\":{cap},\
\"producers\":{producers},\"preload\":{preload},\"ops\":{ops},\"warmup\":{warmup},\
\"active_ues\":{active_ues},\"kinds\":{kinds_j},\
\"seed\":{seed},\"rate\":{rate:.1},\"drain_timeout_s\":{drain_to:.6},\
\"planned\":{planned},\"enqueue_started\":{enqueue_started},\"enqueued\":{enqueued},\
\"completed_within_window\":{completed_within_window},\
\"completed_during_drain\":{completed_during_drain},\"errors\":{errors},\
\"timed_out\":{timed_out},\"histogram_overflows\":{histogram_overflows},\
\"valid\":{valid},\"arrival_window_s\":{arrival_window_s:.6},\"drain_s\":{drain_s:.6},\
\"throughput_ops_s\":{throughput_ops_s:.1},\
\"primary_ns\":{primary_ns},\"admission_ns\":{admission},\
\"in_service_ns\":{in_service_j},\"observation_ns\":{observation_j},\
\"stamp_start\":{stamp_start},\"queue\":\"{queue}\",\
\"queue_wait_ns\":{queue_wait_ns},\"execute_ns\":{execute_ns}}}",
            alloc = ALLOC_NAME,
            workload = args.workload,
            shards = args.shards,
            cap = args.queue_capacity,
            producers = args.producers,
            preload = args.preload,
            ops = args.ops,
            warmup = args.warmup,
            active_ues = args.active_ues,
            kinds_j = format!(
                "[{},{},{},{},{},{},{},{}]",
                kinds[0], kinds[1], kinds[2], kinds[3], kinds[4], kinds[5], kinds[6], kinds[7]
            ),
            seed = args.seed,
            rate = args.rate,
            drain_to = args.drain_timeout_s,
            valid = if valid { "true" } else { "false" },
            admission = part_json(&admission),
            in_service_j = part_json(&in_service),
            observation_j = part_json(&observation),
            stamp_start = if args.stamp_start { "true" } else { "false" },
            queue = QUEUE_NAME,
            queue_wait_ns = if args.stamp_start {
                part_json(&queue_wait)
            } else {
                "null".to_string()
            },
            execute_ns = if args.stamp_start {
                part_json(&execute)
            } else {
                "null".to_string()
            },
        );
    } else {
        println!(
            "UECM pipeline [rust, alloc={ALLOC_NAME}, schema=pipeline, workload={}]",
            args.workload
        );
        println!(
            "  kinds=[{},{},{},{},{},{},{},{}]",
            kinds[0], kinds[1], kinds[2], kinds[3], kinds[4], kinds[5], kinds[6], kinds[7]
        );
        println!(
            "  shards={} producers={} preload={} ops/prod={} warmup={} rate={:.0} drain_timeout_s={:.3}",
            args.shards,
            args.producers,
            args.preload,
            args.ops,
            args.warmup,
            args.rate,
            args.drain_timeout_s
        );
        println!(
            "  planned={planned} enqueue_started={enqueue_started} enqueued={enqueued} \
within_window={completed_within_window} during_drain={completed_during_drain} \
errors={errors} timed_out={timed_out} histogram_overflows={histogram_overflows} valid={valid}"
        );
        println!(
            "  arrival_window_s={arrival_window_s:.6} drain_s={drain_s:.6} \
throughput_ops_s={throughput_ops_s:.1}"
        );
        println!(
            "  primary ns: p50={} p99={} p999={} p99.99={} max={}",
            quantile(&primary, 0.50),
            quantile(&primary, 0.99),
            quantile(&primary, 0.999),
            quantile(&primary, 0.9999),
            hist_max(&primary)
        );
        println!(
            "  admission ns: p50={} p99={} p999={} max={}",
            quantile(&admission, 0.50),
            quantile(&admission, 0.99),
            quantile(&admission, 0.999),
            hist_max(&admission)
        );
        println!(
            "  in_service ns: p50={} p99={} p999={} max={}",
            quantile(&in_service, 0.50),
            quantile(&in_service, 0.99),
            quantile(&in_service, 0.999),
            hist_max(&in_service)
        );
        println!(
            "  observation ns: p50={} p99={} p999={} max={}",
            quantile(&observation, 0.50),
            quantile(&observation, 0.99),
            quantile(&observation, 0.999),
            hist_max(&observation)
        );
        if args.stamp_start {
            println!(
                "  queue_wait ns: p50={} p99={} p999={} max={}",
                quantile(&queue_wait, 0.50),
                quantile(&queue_wait, 0.99),
                quantile(&queue_wait, 0.999),
                hist_max(&queue_wait)
            );
            println!(
                "  execute ns: p50={} p99={} p999={} max={}",
                quantile(&execute, 0.50),
                quantile(&execute, 0.99),
                quantile(&execute, 0.999),
                hist_max(&execute)
            );
        }
    }

    if !args.hist_out.is_empty() {
        write_hist_sidecar(
            &args,
            ops_total,
            &primary,
            &admission,
            &in_service,
            &observation,
            &queue_wait,
            &execute,
        );
    }

    if !valid {
        std::process::exit(1);
    }
}
