//! Latency-budget decomposition for the Rust implementation.
//!
//! The load sweep measures an end-to-end operation: a caller builds a request,
//! routes it to a shard's bounded queue, blocks on a completion handle, and a
//! worker thread executes the operation and writes the result back. That path
//! bundles two costs of very different character, and the sweep cannot separate
//! them:
//!
//!   1. the operation's own work -- a pinned hash lookup, a state-machine guard,
//!      and a field update, all inside one thread;
//!   2. the cross-thread submit-and-complete handoff -- an enqueue, a wakeup,
//!      a context switch, and a completion, none of which is language-specific
//!      and all of which is charged to the scheduler.
//!
//! Both are measured here on the same host, in one process, with one caller
//! thread. `ShardCore` is the single-threaded operation processor, so calling it
//! directly gives (1) with no queue in the path; `Service` wraps the same core
//! in the full threaded machinery, so calling it gives (1) + (2). Their
//! difference is the handoff.
//!
//! Both figures are batch means over a long loop rather than per-call medians.
//! That is deliberate: a `clock_gettime` pair costs tens of nanoseconds, which
//! is the same order as the core operation itself, so per-call timestamps would
//! measure the instrument. The decomposition only needs the relative magnitude
//! of the two terms, which a batch mean resolves cleanly.
//!
//! The map is preloaded to the same occupancy the sweep runs at, so the hash
//! lookup does the same amount of work here as it does there.
//!
//! Usage:
//!     cargo run --release --example latency_budget -- [--shards N]
//!         [--active-ues N] [--core-iters N] [--svc-iters N] [--json]

use std::hint::black_box;
use std::sync::atomic::AtomicU64;
use std::sync::Arc;
use std::time::Instant;

use uecm::{Config, CreateParams, Service, ShardCore, SignalingMsg, UeId};

/// The UE every timed operation targets. Hot in cache by construction, as the
/// sweep's own hot path is.
const HOT_UE: UeId = 1;

struct Args {
    shards: u64,
    active_ues: u64,
    core_iters: u64,
    svc_iters: u64,
    json: bool,
}

fn parse_args() -> Args {
    let mut a = Args {
        shards: 8,
        active_ues: 5000,
        core_iters: 2_000_000,
        svc_iters: 50_000,
        json: false,
    };
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let mut i = 0;
    while i < argv.len() {
        let next = |i: usize| -> u64 {
            argv.get(i + 1)
                .and_then(|v| v.parse().ok())
                .unwrap_or_else(|| panic!("missing or bad value for {}", argv[i]))
        };
        match argv[i].as_str() {
            "--shards" => {
                a.shards = next(i);
                i += 2;
            }
            "--active-ues" => {
                a.active_ues = next(i);
                i += 2;
            }
            "--core-iters" => {
                a.core_iters = next(i);
                i += 2;
            }
            "--svc-iters" => {
                a.svc_iters = next(i);
                i += 2;
            }
            "--json" => {
                a.json = true;
                i += 1;
            }
            other => panic!("unknown argument: {other}"),
        }
    }
    a
}

/// Mean nanoseconds per call for the operation with no queue in the path.
///
/// One shard's worth of the sweep population is loaded so the hash map is at
/// the same occupancy, then a single connected UE is signalled in a tight loop.
fn measure_core(cfg: Config, per_shard: u64, iters: u64) -> f64 {
    let seq = Arc::new(AtomicU64::new(0));
    let mut core = ShardCore::new(cfg, seq);
    let params = CreateParams::default();
    for ue in 1..=per_shard.max(1) {
        core.create_context(ue, &params).expect("create");
        core.setup_connection(ue).expect("setup");
    }
    let msg = SignalingMsg::default();

    // Warm the branch predictors and the map's cache lines before timing.
    for _ in 0..(iters / 20).max(1000) {
        black_box(core.handle_signaling(HOT_UE, &msg).expect("warmup signal"));
    }

    let t0 = Instant::now();
    for _ in 0..iters {
        black_box(
            core.handle_signaling(black_box(HOT_UE), black_box(&msg))
                .expect("signal"),
        );
    }
    t0.elapsed().as_nanos() as f64 / iters as f64
}

/// Mean nanoseconds per call for the same operation through the full service.
///
/// A single caller thread, so the queue is never contended: this is the floor
/// of the handoff cost, not its value under the sweep's offered load.
fn measure_service(cfg: Config, active_ues: u64, iters: u64) -> f64 {
    let mut svc = Service::new(cfg);
    svc.start();
    let params = CreateParams::default();
    for ue in 1..=active_ues.max(1) {
        svc.create_context(ue, params).expect("create");
        svc.setup_connection(ue).expect("setup");
    }
    let msg = SignalingMsg::default();

    for _ in 0..(iters / 20).max(100) {
        black_box(svc.handle_signaling(HOT_UE, msg).expect("warmup signal"));
    }

    let t0 = Instant::now();
    for _ in 0..iters {
        black_box(
            svc.handle_signaling(black_box(HOT_UE), black_box(msg))
                .expect("signal"),
        );
    }
    let ns = t0.elapsed().as_nanos() as f64 / iters as f64;
    svc.shutdown();
    ns
}

fn main() {
    let a = parse_args();
    let cfg = Config {
        n_shards: a.shards,
        ..Config::default()
    };
    let per_shard = a.active_ues / a.shards.max(1);

    let core_ns = measure_core(cfg, per_shard, a.core_iters);
    let svc_ns = measure_service(cfg, a.active_ues, a.svc_iters);
    let handoff_ns = svc_ns - core_ns;

    if a.json {
        println!(
            concat!(
                r#"{{"lang":"rust","shards":{},"active_ues":{},"#,
                r#""core_iters":{},"svc_iters":{},"#,
                r#""core_ns":{:.1},"service_ns":{:.1},"handoff_ns":{:.1},"#,
                r#""core_share_pct":{:.2}}}"#
            ),
            a.shards,
            a.active_ues,
            a.core_iters,
            a.svc_iters,
            core_ns,
            svc_ns,
            handoff_ns,
            100.0 * core_ns / svc_ns,
        );
    } else {
        println!(
            "Rust latency budget ({} shards, {} active UEs)",
            a.shards, a.active_ues
        );
        println!("  core operation (no queue)   : {core_ns:>12.1} ns/call");
        println!("  full service round-trip     : {svc_ns:>12.1} ns/call");
        println!("  cross-thread handoff        : {handoff_ns:>12.1} ns/call");
        println!(
            "  operation's share of the end-to-end cost: {:.2}%",
            100.0 * core_ns / svc_ns
        );
    }
}
