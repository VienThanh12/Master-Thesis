//! UECM latency/throughput benchmark (Rust side), spec §3/§10.
//!
//! Mirrors `cpp/bench/bench.cpp` exactly for fairness. Two workloads:
//!   --workload signal (default): preload contexts, then hammer handle_signaling.
//!   --workload mixed: pinned RAN lifecycle generator (see bench/README.md and the
//!     `workload` module below), attach/signaling/bearer/handover/release.
//!
//! The mixed generator is a pure deterministic function of (active_ues, seed) using
//! the same SplitMix64 draws and the same per-slot state machine as the C++ side, so
//! the per-op-kind counts are identical across languages (a parity signal).
//!
//! Build with the matched allocator: `cargo build --release --example bench --features jemalloc`.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::thread;
use std::time::{Duration, Instant};

use hdrhistogram::Histogram;
use uecm::{Config, CreateParams, DrbEntry, ReconfigParams, Service, SignalingMsg, UeId, MAX_DRBS};

#[cfg(feature = "jemalloc")]
#[global_allocator]
static GLOBAL: tikv_jemallocator::Jemalloc = tikv_jemallocator::Jemalloc;

#[cfg(feature = "jemalloc")]
const ALLOC_NAME: &str = "jemalloc";
#[cfg(not(feature = "jemalloc"))]
const ALLOC_NAME: &str = "system";

const HDR_LOW: u64 = 1;
const HDR_HIGH: u64 = 3_600 * 1_000 * 1_000 * 1_000; // 3.6 s in ns
const HDR_SIG: u8 = 3;

// Upper bound on synthetic samples emitted by one coordinated-omission
// correction. Mirrors kMaxCorrectionSamples in cpp/bench/hdr.hpp.
const MAX_CORRECTION_SAMPLES: u64 = 10_000;

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

/// Pinned workload generator; see the module doc and bench/README.md. Kept in lock-step
/// with `cpp/bench/workload.hpp` (same state machine, weights, and PRNG draw order).
mod workload {
    use super::SplitMix64;
    use uecm::MAX_DRBS;

    pub const KIND_COUNT: usize = 8;
    pub const KIND_NAMES: [&str; KIND_COUNT] = [
        "create",
        "setup",
        "signal",
        "adddrb",
        "begin_reconf",
        "complete_reconf",
        "abort_reconf",
        "release",
    ];

    #[derive(Clone, Copy, PartialEq, Eq)]
    pub enum WKind {
        Create = 0,
        Setup = 1,
        Signal = 2,
        AddDrb = 3,
        BeginReconf = 4,
        CompleteReconf = 5,
        AbortReconf = 6,
        Release = 7,
    }

    pub struct WOp {
        pub kind: WKind,
        pub slot: u64,
        pub drb_id: u8,
    }

    const EMPTY: u8 = 0;
    const IDLE: u8 = 1;
    const CONNECTED: u8 = 2;
    const RECONFIGURING: u8 = 3;

    pub struct Workload {
        n: u64,
        rng: SplitMix64,
        state: Vec<u8>,
        ndrbs: Vec<u8>,
    }

    impl Workload {
        pub fn new(active_ues: u64, seed: u64) -> Self {
            let n = if active_ues == 0 { 1 } else { active_ues };
            Self {
                n,
                rng: SplitMix64 { s: seed },
                state: vec![EMPTY; n as usize],
                ndrbs: vec![0u8; n as usize],
            }
        }

        pub fn next(&mut self) -> WOp {
            let slot = self.rng.next() % self.n;
            let si = slot as usize;
            let mut op = WOp {
                kind: WKind::Signal,
                slot,
                drb_id: 0,
            };
            match self.state[si] {
                EMPTY => {
                    op.kind = WKind::Create;
                    self.state[si] = IDLE;
                }
                IDLE => {
                    op.kind = WKind::Setup;
                    self.state[si] = CONNECTED;
                }
                CONNECTED => {
                    let r = self.rng.next() % 100;
                    if r < 70 {
                        op.kind = WKind::Signal;
                    } else if r < 80 {
                        if (self.ndrbs[si] as usize) < MAX_DRBS {
                            op.kind = WKind::AddDrb;
                            op.drb_id = self.ndrbs[si];
                            self.ndrbs[si] += 1;
                        } else {
                            op.kind = WKind::Signal;
                        }
                    } else if r < 95 {
                        op.kind = WKind::BeginReconf;
                        self.state[si] = RECONFIGURING;
                    } else {
                        op.kind = WKind::Release;
                        self.state[si] = EMPTY;
                        self.ndrbs[si] = 0;
                    }
                }
                _ => {
                    let r = self.rng.next() % 100;
                    op.kind = if r < 80 {
                        WKind::CompleteReconf
                    } else {
                        WKind::AbortReconf
                    };
                    self.state[si] = CONNECTED;
                }
            }
            op
        }
    }
}

use workload::{WKind, WOp, Workload, KIND_COUNT, KIND_NAMES};

struct Args {
    workload: String,
    shards: u64,
    queue_capacity: usize,
    producers: u64,
    preload: u64,
    active_ues: u64,
    ops: u64,
    warmup: u64,
    seed: u64,
    rate: f64,
    max_run_s: f64,
    json: bool,
    /// Record inter-operation jitter (IPDV) alongside latency.
    jitter: bool,
    /// Append the full HDR bucket contents here (empty => not written).
    hist_out: String,
    /// Opaque tag echoed into the sidecar, used by campaign.sh for the repeat index.
    run_id: String,
}

fn parse() -> Args {
    let mut a = Args {
        workload: "signal".to_string(),
        shards: 8,
        queue_capacity: 1024,
        producers: 0,
        preload: 10_000,
        active_ues: 10_000,
        ops: 200_000,
        warmup: 0,
        seed: 42,
        rate: 0.0,
        max_run_s: 0.0,
        json: false,
        jitter: false,
        hist_out: String::new(),
        run_id: String::new(),
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
            "--workload" => a.workload = val(),
            "--shards" => a.shards = val().parse().unwrap_or(8),
            "--queue-capacity" => a.queue_capacity = val().parse().unwrap_or(1024),
            "--producers" => a.producers = val().parse().unwrap_or(0),
            "--preload" => a.preload = val().parse().unwrap_or(10_000),
            "--active-ues" => a.active_ues = val().parse().unwrap_or(10_000),
            "--ops" => a.ops = val().parse().unwrap_or(200_000),
            "--warmup" => a.warmup = val().parse().unwrap_or(0),
            "--seed" => a.seed = val().parse().unwrap_or(42),
            "--rate" => a.rate = val().parse().unwrap_or(0.0),
            "--max-run-s" => a.max_run_s = val().parse().unwrap_or(0.0),
            "--jitter" => a.jitter = true,
            "--hist-out" => a.hist_out = val(),
            "--run-id" => a.run_id = val(),
            "--json" => a.json = true,
            other => {
                eprintln!("unknown arg: {other}");
                std::process::exit(2);
            }
        }
        i += 1;
    }
    if a.producers == 0 {
        a.producers = a.shards;
    }
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

// Coordinated-omission correction, mirroring HdrHistogram::record_corrected in
// cpp/bench/hdr.hpp step for step, including the backfill cap. The crate's own
// record_correct() is uncapped, and above saturation `value` grows without
// bound, so the correction would cost O(value/expected_interval) per operation.
// Recording saturates rather than erroring so out-of-range values are clamped
// into the top bucket, which is what the C++ histogram does.
fn record_corrected(hist: &mut Histogram<u64>, value: u64, expected_interval: u64) {
    hist.saturating_record(value);
    if expected_interval == 0 || value <= expected_interval {
        return;
    }
    let mut missing = value - expected_interval;
    let mut emitted = 0u64;
    while missing >= expected_interval && emitted < MAX_CORRECTION_SAMPLES {
        hist.saturating_record(missing);
        missing -= expected_interval;
        emitted += 1;
    }
}

/// Append one record holding the full bucket contents of the run's histograms.
///
/// Mirrors `write_hist_sidecar` in `cpp/bench/bench.cpp`. Buckets are emitted as
/// `[value, count]` pairs where value is `value_iterated_to()`, the bucket's
/// highest equivalent value, and the C++ port exposes the same lattice through
/// `for_each_recorded`, so the two languages persist onto one grid instead of
/// onto two internal bucket indices that happen to agree. Without this the far
/// tail is unrecoverable after the fact: p99.99 rests on roughly 17 observations
/// in a single run at the campaign's representative load, so it only becomes
/// decision-grade once repeats are pooled, and pooling needs the buckets.
fn write_hist_sidecar(
    a: &Args,
    total_ops: u64,
    lat: &Histogram<u64>,
    jit: Option<&Histogram<u64>>,
) {
    use std::fmt::Write as _;
    use std::io::Write as _;

    let dump = |out: &mut String, key: &str, h: &Histogram<u64>| {
        // `total` can exceed ops_total: under --rate the coordinated-omission
        // correction backfills synthetic samples into the histogram, which is by
        // design and is not a miscount of retired operations.
        let _ = write!(
            out,
            ",\"{}\":{{\"total\":{},\"max\":{},\"pairs\":[",
            key,
            h.len(),
            h.max()
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
    };

    let mut line = format!(
        "{{\"run_id\":\"{}\",\"lang\":\"rust\",\"alloc\":\"{}\",\"workload\":\"{}\",\
\"shards\":{},\"producers\":{},\"rate\":{:.1},\"seed\":{},\"ops_total\":{},\
\"hdr\":{{\"low\":{},\"high\":{},\"sig\":{}}}",
        a.run_id,
        ALLOC_NAME,
        a.workload,
        a.shards,
        a.producers,
        a.rate,
        a.seed,
        total_ops,
        HDR_LOW,
        HDR_HIGH,
        HDR_SIG
    );
    dump(&mut line, "lat", lat);
    if let Some(j) = jit {
        dump(&mut line, "jitter", j);
    }
    line.push_str("}\n");

    match std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&a.hist_out)
    {
        Ok(mut f) => {
            if let Err(e) = f.write_all(line.as_bytes()) {
                eprintln!("warning: cannot write --hist-out '{}': {e}", a.hist_out);
            }
        }
        Err(e) => eprintln!("warning: cannot open --hist-out '{}': {e}", a.hist_out),
    }
}

/// jemalloc's own accounting (RQ3), in bytes, or `None` under the system allocator.
///
/// `getrusage` gives one number for the whole process, which establishes that one
/// build holds more memory than the other without saying what the extra is. These
/// six counters are the split jemalloc already tracks: live allocation, pages
/// handed out, arena and tcache bookkeeping, physically backed bytes, mapped
/// address space, and space unmapped but not returned.
///
/// The C++ arm reads the same six through `mallctl`, so the two can be
/// differenced. This is not the sampled heap profile `bench/alloc_profile.sh`
/// collects: that attributes bytes to allocation sites and needs a prof-enabled
/// build plus `jeprof`, while this attributes bytes to allocator structures and
/// runs anywhere.
#[cfg(feature = "jemalloc")]
fn je_stats() -> Option<[u64; 6]> {
    use tikv_jemalloc_ctl::{epoch, stats};
    // Statistics are cached until `epoch` is advanced; without this the read
    // returns whatever the last refresh saw.
    epoch::advance().ok()?;
    Some([
        stats::allocated::read().ok()? as u64,
        stats::active::read().ok()? as u64,
        stats::metadata::read().ok()? as u64,
        stats::resident::read().ok()? as u64,
        stats::mapped::read().ok()? as u64,
        stats::retained::read().ok()? as u64,
    ])
}

#[cfg(not(feature = "jemalloc"))]
fn je_stats() -> Option<[u64; 6]> {
    None
}

/// A JSON object, or nulls when there is no jemalloc to interrogate. The key is
/// always present so a consumer can tell "measured as absent" from "field missing
/// because the harness predates this".
fn je_json() -> String {
    match je_stats() {
        Some([allocated, active, metadata, resident, mapped, retained]) => format!(
            "\"je\":{{\"available\":true,\"allocated\":{allocated},\"active\":{active},\
\"metadata\":{metadata},\"resident\":{resident},\"mapped\":{mapped},\"retained\":{retained}}}"
        ),
        None => "\"je\":{\"available\":false,\"allocated\":null,\"active\":null,\
\"metadata\":null,\"resident\":null,\"mapped\":null,\"retained\":null}"
            .to_string(),
    }
}

/// Process resource usage (RQ3): (peak RSS kB, user CPU s, sys CPU s), via getrusage.
/// The one `unsafe` FFI call is confined to this benchmark tool; the UECM library
/// itself contains zero `unsafe`.
fn resource_usage() -> (i64, f64, f64) {
    use std::mem::MaybeUninit;
    // SAFETY: getrusage writes a fully-initialised rusage into the provided pointer.
    unsafe {
        let mut ru = MaybeUninit::<libc::rusage>::zeroed();
        libc::getrusage(libc::RUSAGE_SELF, ru.as_mut_ptr());
        let ru = ru.assume_init();
        let user = ru.ru_utime.tv_sec as f64 + ru.ru_utime.tv_usec as f64 / 1e6;
        let sys = ru.ru_stime.tv_sec as f64 + ru.ru_stime.tv_usec as f64 / 1e6;
        (ru.ru_maxrss, user, sys)
    }
}

fn exec_op(svc: &Service, op: &WOp, id: UeId) -> bool {
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

fn main() {
    let a = parse();
    if a.workload != "signal" && a.workload != "mixed" {
        eprintln!("unknown --workload '{}' (use signal|mixed)", a.workload);
        std::process::exit(2);
    }
    let _ = MAX_DRBS; // referenced via workload module

    let cfg = Config {
        n_shards: a.shards,
        queue_capacity: a.queue_capacity,
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();

    let range = if a.preload == 0 { 1 } else { a.preload };

    // --- Preload (signal workload only) -------------------------------------
    if a.workload == "signal" {
        thread::scope(|s| {
            for p in 0..a.producers {
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
    }

    // --- Measured phase ------------------------------------------------------
    let merged = Mutex::new(new_hist());
    // Allocated only under --jitter. One histogram is ~264 KiB, so allocating it
    // unconditionally would add producers x 264 KiB to peak RSS: the same order as
    // the language RSS difference RQ3 reports, measured by the instrument rather
    // than by the subject. The C++ side gates it identically.
    let merged_jitter: Mutex<Option<Histogram<u64>>> =
        Mutex::new(if a.jitter { Some(new_hist()) } else { None });
    let merged_counts = Mutex::new([0u64; KIND_COUNT]);
    let errors = AtomicU64::new(0);
    let interval_ns: u64 = if a.rate > 0.0 {
        (1e9 / a.rate) as u64
    } else {
        0
    };

    let wall_start = Instant::now();
    // Throughput must be counted over the measured phase only. `total_ops` excludes
    // the warm-up iterations, so dividing it by the whole run's wall time would
    // understate achieved throughput by exactly the warm-up fraction. Each producer
    // reports the nanosecond offsets at which its measured phase starts and ends;
    // the measured window is the union of those intervals.
    let meas_lo_ns = AtomicU64::new(u64::MAX);
    let meas_hi_ns = AtomicU64::new(0);
    let measured_ops = AtomicU64::new(0);
    thread::scope(|s| {
        for p in 0..a.producers {
            let svc = &svc;
            let merged = &merged;
            let merged_jitter = &merged_jitter;
            let merged_counts = &merged_counts;
            let errors = &errors;
            let args = &a;
            let meas_lo_ns = &meas_lo_ns;
            let meas_hi_ns = &meas_hi_ns;
            let measured_ops = &measured_ops;
            s.spawn(move || {
                let mut hist = new_hist();
                let mut jhist = if args.jitter { Some(new_hist()) } else { None };
                let mut prev_lat: Option<u64> = None; // first measured op has no predecessor
                let mut counts = [0u64; KIND_COUNT];
                let mut rng = SplitMix64 {
                    s: args.seed.wrapping_add(p),
                };
                let mut wl = Workload::new(args.active_ues, args.seed.wrapping_add(p));
                let base = p * 100_000_000 + 1;
                let msg = SignalingMsg {
                    kind: 1,
                    payload_len: 4,
                    payload: [0u8; 64],
                };
                let mut local_errors = 0u64;
                let mut local_measured = 0u64;

                let mut schedule = Instant::now();
                let total_iters = args.warmup + args.ops;
                let mut meas_deadline: Option<Instant> = None;
                for n in 0..total_iters {
                    let measured = n >= args.warmup;
                    if n == args.warmup {
                        let now = Instant::now();
                        let off = wall_start.elapsed().as_nanos() as u64;
                        meas_lo_ns.fetch_min(off, Ordering::Relaxed);
                        if args.max_run_s > 0.0 {
                            meas_deadline =
                                Some(now + Duration::from_nanos((args.max_run_s * 1e9) as u64));
                        }
                    }

                    let (op, id) = if args.workload == "mixed" {
                        let op = wl.next();
                        let id = base + op.slot;
                        (Some(op), id)
                    } else {
                        (None, base + (rng.next() % range))
                    };

                    let mut intended = schedule;
                    if interval_ns > 0 {
                        intended = schedule;
                        let now = Instant::now();
                        if intended > now {
                            thread::sleep(intended - now);
                        }
                        schedule += Duration::from_nanos(interval_ns);
                    }
                    let t0 = Instant::now();
                    let ok = match &op {
                        Some(o) => exec_op(svc, o, id),
                        None => svc.handle_signaling(id, msg).is_ok(),
                    };
                    let t1 = Instant::now();
                    if !ok {
                        local_errors += 1;
                    }
                    if measured {
                        let kind_idx = match &op {
                            Some(o) => o.kind as usize,
                            None => WKind::Signal as usize,
                        };
                        counts[kind_idx] += 1;
                        let lat = if interval_ns > 0 {
                            t1.duration_since(intended).as_nanos() as u64
                        } else {
                            t1.duration_since(t0).as_nanos() as u64
                        }
                        .max(1);
                        if interval_ns > 0 {
                            record_corrected(&mut hist, lat, interval_ns);
                        } else {
                            hist.saturating_record(lat);
                        }
                        // Inter-operation jitter (IPDV, RFC 3393): the absolute
                        // difference between consecutive measured latencies within
                        // this producer. Never across producers, and only over real
                        // observations -- the synthetic samples the
                        // coordinated-omission correction backfills are not
                        // operations, so differencing them would invent variation.
                        if let Some(j) = jhist.as_mut() {
                            if let Some(prev) = prev_lat {
                                let d = lat.abs_diff(prev).max(1); // same floor the latency path uses
                                j.saturating_record(d);
                            }
                            prev_lat = Some(lat);
                        }
                        local_measured += 1;
                        if let Some(deadline) = meas_deadline {
                            if t1 >= deadline {
                                break;
                            }
                        }
                    }
                }
                meas_hi_ns.fetch_max(wall_start.elapsed().as_nanos() as u64, Ordering::Relaxed);
                errors.fetch_add(local_errors, Ordering::Relaxed);
                measured_ops.fetch_add(local_measured, Ordering::Relaxed);
                merged.lock().unwrap().add(&hist).expect("compatible hists");
                if let Some(j) = jhist.as_ref() {
                    if let Some(mj) = merged_jitter.lock().unwrap().as_mut() {
                        mj.add(j).expect("compatible hists");
                    }
                }
                let mut mc = merged_counts.lock().unwrap();
                for k in 0..KIND_COUNT {
                    mc[k] += counts[k];
                }
            });
        }
    });
    let wall = wall_start.elapsed();
    svc.shutdown();

    let h = merged.into_inner().unwrap();
    let hj = merged_jitter.into_inner().unwrap();
    let counts = merged_counts.into_inner().unwrap();
    let wall_s = wall.as_secs_f64();
    let lo = meas_lo_ns.load(Ordering::Relaxed);
    let hi = meas_hi_ns.load(Ordering::Relaxed);
    let measured_wall_s = if hi > lo && lo != u64::MAX {
        (hi - lo) as f64 / 1e9
    } else {
        wall_s
    };
    let total_ops = measured_ops.load(Ordering::Relaxed);
    let thr = if measured_wall_s > 0.0 {
        total_ops as f64 / measured_wall_s
    } else {
        0.0
    };
    let errs = errors.load(Ordering::Relaxed);

    let (rss_peak_kb, cpu_user_s, cpu_sys_s) = resource_usage();
    let cpu_pct = if wall_s > 0.0 {
        (cpu_user_s + cpu_sys_s) / wall_s * 100.0
    } else {
        0.0
    };

    // The C++ side passes these same literals to its value_at_quantile, so both
    // languages select the same sample rather than two that differ by a ULP of
    // quantile arithmetic.
    let (p25, p50, p75) = (
        h.value_at_quantile(0.25),
        h.value_at_quantile(0.50),
        h.value_at_quantile(0.75),
    );
    let (p90, p99, p999, p9999) = (
        h.value_at_quantile(0.90),
        h.value_at_quantile(0.99),
        h.value_at_quantile(0.999),
        h.value_at_quantile(0.9999),
    );
    let jitter_json = match hj.as_ref() {
        Some(j) => format!(
            ",\"jitter_ns\":{{\"p50\":{},\"p99\":{},\"p999\":{},\"max\":{},\"mean\":{:.1},\
\"stdev\":{:.1},\"n\":{}}}",
            j.value_at_quantile(0.50),
            j.value_at_quantile(0.99),
            j.value_at_quantile(0.999),
            j.max(),
            j.mean(),
            j.stdev(),
            j.len()
        ),
        None => String::new(),
    };

    if a.json {
        let kinds: String = KIND_NAMES
            .iter()
            .enumerate()
            .map(|(k, name)| {
                format!(
                    "{}\"{}\":{}",
                    if k == 0 { "" } else { "," },
                    name,
                    counts[k]
                )
            })
            .collect();
        println!(
            "{{\"lang\":\"rust\",\"alloc\":\"{}\",\"workload\":\"{}\",\"shards\":{},\"producers\":{},\
\"rate\":{:.1},\"ops_total\":{},\"errors\":{},\"wall_s\":{:.6},\"measured_wall_s\":{:.6},\
\"throughput_ops_s\":{:.1},\
\"lat_ns\":{{\"p25\":{},\"p50\":{},\"p75\":{},\"p90\":{},\"p99\":{},\"p999\":{},\"p9999\":{},\
\"max\":{},\"mean\":{:.1},\"stdev\":{:.1}}}{},\
\"rss_peak_kb\":{},\"cpu_user_s\":{:.3},\"cpu_sys_s\":{:.3},\"cpu_pct\":{:.1},{},\"kinds\":{{{}}}}}",
            ALLOC_NAME, a.workload, a.shards, a.producers, a.rate, total_ops, errs, wall_s,
            measured_wall_s, thr,
            p25, p50, p75, p90, p99, p999, p9999, h.max(), h.mean(), h.stdev(), jitter_json,
            rss_peak_kb, cpu_user_s, cpu_sys_s, cpu_pct, je_json(), kinds,
        );
    } else {
        println!(
            "UECM bench [rust, alloc={ALLOC_NAME}, workload={}]",
            a.workload
        );
        println!(
            "  shards={} producers={} active_ues={} ops/prod={} rate={:.0}",
            a.shards,
            a.producers,
            if a.workload == "mixed" {
                a.active_ues
            } else {
                a.preload
            },
            a.ops,
            a.rate
        );
        println!(
            "  ops_total={} errors={} wall={:.3}s (measured {:.3}s) throughput={:.0} ops/s",
            total_ops, errs, wall_s, measured_wall_s, thr
        );
        println!(
            "  latency ns: p50={} p90={} p99={} p99.9={} p99.99={} max={} mean={:.1}",
            p50,
            p90,
            p99,
            p999,
            p9999,
            h.max(),
            h.mean(),
        );
        println!(
            "  dispersion ns: iqr={} (p25={} p75={}) stdev={:.1}",
            p75 - p25,
            p25,
            p75,
            h.stdev()
        );
        if let Some(j) = hj.as_ref() {
            println!(
                "  jitter ns (IPDV): p50={} p99={} p99.9={} max={} mean={:.1} n={}",
                j.value_at_quantile(0.50),
                j.value_at_quantile(0.99),
                j.value_at_quantile(0.999),
                j.max(),
                j.mean(),
                j.len()
            );
        }
        println!(
            "  resource: peak_rss={:.1} MB  cpu={:.2}s (user {:.2} + sys {:.2})  cpu%={:.0}",
            rss_peak_kb as f64 / 1024.0,
            cpu_user_s + cpu_sys_s,
            cpu_user_s,
            cpu_sys_s,
            cpu_pct
        );
        if let Some([allocated, active, metadata, resident, mapped, retained]) = je_stats() {
            const MIB: f64 = 1048576.0;
            println!(
                "  jemalloc: allocated={:.1} MB  active={:.1} MB  metadata={:.1} MB  \
resident={:.1} MB  mapped={:.1} MB  retained={:.1} MB",
                allocated as f64 / MIB,
                active as f64 / MIB,
                metadata as f64 / MIB,
                resident as f64 / MIB,
                mapped as f64 / MIB,
                retained as f64 / MIB
            );
        }
        if a.workload == "mixed" {
            print!("  op kinds:");
            for k in 0..KIND_COUNT {
                print!(" {}={}", KIND_NAMES[k], counts[k]);
            }
            println!();
        }
    }

    if !a.hist_out.is_empty() {
        write_hist_sidecar(&a, total_ops, &h, hj.as_ref());
    }

    if errs != 0 {
        std::process::exit(1);
    }
}
