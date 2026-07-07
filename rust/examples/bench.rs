//! UECM latency/throughput benchmark (Rust side), spec §3/§10.
//!
//! Mirrors `cpp/bench/bench.cpp` exactly for fairness. Two workloads:
//!   --workload signal (default): preload contexts, then hammer handle_signaling.
//!   --workload mixed: pinned RAN lifecycle generator (see bench/README.md and the
//!     `workload` module below) — attach/signaling/bearer/handover/release.
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
    json: bool,
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
        json: false,
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
    let merged_counts = Mutex::new([0u64; KIND_COUNT]);
    let errors = AtomicU64::new(0);
    let interval_ns: u64 = if a.rate > 0.0 {
        (1e9 / a.rate) as u64
    } else {
        0
    };

    let wall_start = Instant::now();
    thread::scope(|s| {
        for p in 0..a.producers {
            let svc = &svc;
            let merged = &merged;
            let merged_counts = &merged_counts;
            let errors = &errors;
            let args = &a;
            s.spawn(move || {
                let mut hist = new_hist();
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

                let mut schedule = Instant::now();
                let total_iters = args.warmup + args.ops;
                for n in 0..total_iters {
                    let measured = n >= args.warmup;

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
                            let _ = hist.record_correct(lat, interval_ns);
                        } else {
                            let _ = hist.record(lat);
                        }
                    }
                }
                errors.fetch_add(local_errors, Ordering::Relaxed);
                merged.lock().unwrap().add(&hist).expect("compatible hists");
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
    let counts = merged_counts.into_inner().unwrap();
    let wall_s = wall.as_secs_f64();
    let total_ops = a.ops * a.producers;
    let thr = if wall_s > 0.0 {
        total_ops as f64 / wall_s
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
\"rate\":{:.1},\"ops_total\":{},\"errors\":{},\"wall_s\":{:.6},\"throughput_ops_s\":{:.1},\
\"lat_ns\":{{\"p50\":{},\"p90\":{},\"p99\":{},\"p999\":{},\"max\":{},\"mean\":{:.1}}},\
\"rss_peak_kb\":{},\"cpu_user_s\":{:.3},\"cpu_sys_s\":{:.3},\"cpu_pct\":{:.1},\"kinds\":{{{}}}}}",
            ALLOC_NAME, a.workload, a.shards, a.producers, a.rate, total_ops, errs, wall_s, thr,
            h.value_at_quantile(0.50), h.value_at_quantile(0.90), h.value_at_quantile(0.99),
            h.value_at_quantile(0.999), h.max(), h.mean(),
            rss_peak_kb, cpu_user_s, cpu_sys_s, cpu_pct, kinds,
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
            "  ops_total={} errors={} wall={:.3}s throughput={:.0} ops/s",
            total_ops, errs, wall_s, thr
        );
        println!(
            "  latency ns: p50={} p90={} p99={} p99.9={} max={} mean={:.1}",
            h.value_at_quantile(0.50),
            h.value_at_quantile(0.90),
            h.value_at_quantile(0.99),
            h.value_at_quantile(0.999),
            h.max(),
            h.mean(),
        );
        println!(
            "  resource: peak_rss={:.1} MB  cpu={:.2}s (user {:.2} + sys {:.2})  cpu%={:.0}",
            rss_peak_kb as f64 / 1024.0,
            cpu_user_s + cpu_sys_s,
            cpu_user_s,
            cpu_sys_s,
            cpu_pct
        );
        if a.workload == "mixed" {
            print!("  op kinds:");
            for k in 0..KIND_COUNT {
                print!(" {}={}", KIND_NAMES[k], counts[k]);
            }
            println!();
        }
    }

    if errs != 0 {
        std::process::exit(1);
    }
}
