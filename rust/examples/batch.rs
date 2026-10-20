//! Batch probe, Rust side. PROBE ONLY (`--features batch-probe`), never a reported arm.
//! Twin of `cpp/bench/batch.cpp`, Method 2 of `docs/OVERLOAD_MECHANISM.md`.
//!
//! Each sender owns one shard and sends batches of `--batch` signalling operations for
//! UEs of that shard, one batch at a time and back to back, so the service is past
//! saturation by construction. The time per batch is a fixed handoff cost plus the batch
//! size times the cost of one operation inside a loaded worker. `bench/batch_probes.sh`
//! sweeps the batch size and fits the two.
//!
//! Counting window: batches that start and finish inside [warm-up end, warm-up end +
//! duration]. Process CPU is read at the two ends of the same window.

use std::thread;
use std::time::{Duration, Instant};

use uecm::hash::shard_index;
use uecm::{Config, CreateParams, Service, SignalingMsg, UeId};

#[cfg(feature = "jemalloc")]
#[global_allocator]
static GLOBAL: tikv_jemallocator::Jemalloc = tikv_jemallocator::Jemalloc;

#[cfg(feature = "jemalloc")]
const ALLOC_NAME: &str = "jemalloc";
#[cfg(not(feature = "jemalloc"))]
const ALLOC_NAME: &str = "system";

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
    preload: u64,
    batch: u64,
    duration_s: f64,
    warmup_s: f64,
    seed: u64,
    json: bool,
}

fn parse() -> Args {
    let mut a = Args {
        shards: 7,
        preload: 5000,
        batch: 1,
        duration_s: 3.0,
        warmup_s: 1.0,
        seed: 42,
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
            "--shards" => a.shards = val().parse().expect("--shards"),
            "--preload" => a.preload = val().parse().expect("--preload"),
            "--batch" => a.batch = val().parse().expect("--batch"),
            "--duration-s" => a.duration_s = val().parse().expect("--duration-s"),
            "--warmup-s" => a.warmup_s = val().parse().expect("--warmup-s"),
            "--seed" => a.seed = val().parse().expect("--seed"),
            "--json" => a.json = true,
            other => {
                eprintln!("unknown arg: {other}");
                std::process::exit(2);
            }
        }
        i += 1;
    }
    if a.shards == 0 || a.preload == 0 || a.batch == 0 {
        eprintln!("--shards, --preload and --batch must be positive");
        std::process::exit(2);
    }
    a
}

/// (user CPU s, sys CPU s) for the whole process. The one `unsafe` FFI call is confined
/// to this probe tool, as in `bench.rs`; the UECM library itself contains no `unsafe`.
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

/// The first `count` ids at or above `shard * 100_000_000 + 1` that the pinned shard
/// function (spec §8.1) assigns to `shard`. Identical in both languages.
fn shard_ids(shard: u64, n_shards: u64, count: u64) -> Vec<UeId> {
    let mut ids = Vec::with_capacity(count as usize);
    let mut id = shard * 100_000_000 + 1;
    while (ids.len() as u64) < count {
        if shard_index(id, n_shards) == shard {
            ids.push(id);
        }
        id += 1;
    }
    ids
}

fn sleep_until(t: Instant) {
    let now = Instant::now();
    if t > now {
        thread::sleep(t - now);
    }
}

struct SenderOut {
    ops: u64,
    messages: u64,
    errors: u64,
}

fn main() {
    let a = parse();
    let cfg = Config {
        n_shards: a.shards,
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();

    let ids: Vec<Vec<UeId>> = (0..a.shards).map(|s| shard_ids(s, a.shards, a.preload)).collect();
    thread::scope(|sc| {
        for s in 0..a.shards {
            let svc = &svc;
            let mine = &ids[s as usize];
            sc.spawn(move || {
                for &id in mine {
                    let _ = svc.create_context(
                        id,
                        CreateParams {
                            serving_cell_id: s as u32,
                            security_key: [0u8; 32],
                        },
                    );
                    let _ = svc.setup_connection(id);
                }
            });
        }
    });

    let msg = SignalingMsg {
        kind: 1,
        payload_len: 4,
        payload: [0u8; 64],
    };
    let start = Instant::now();
    let t0 = start + Duration::from_secs_f64(a.warmup_s);
    let t1 = t0 + Duration::from_secs_f64(a.duration_s);
    let batch = a.batch as usize;

    let (outs, cpu0, cpu1) = thread::scope(|sc| {
        let handles: Vec<_> = (0..a.shards)
            .map(|s| {
                let svc = &svc;
                let mine = &ids[s as usize];
                let seed = a.seed + s;
                sc.spawn(move || {
                    let mut rng = SplitMix64 { s: seed };
                    let n = mine.len() as u64;
                    let mut out = SenderOut {
                        ops: 0,
                        messages: 0,
                        errors: 0,
                    };
                    loop {
                        let mut ue_ids = Vec::with_capacity(batch);
                        for _ in 0..batch {
                            ue_ids.push(mine[(rng.next() % n) as usize]);
                        }
                        let began = Instant::now();
                        if began >= t1 {
                            break;
                        }
                        let ack = svc.handle_signaling_batch(ue_ids, msg);
                        let done = Instant::now();
                        if began >= t0 && done <= t1 {
                            out.messages += 1;
                            out.ops += batch as u64;
                            match ack {
                                Ok(ack) if ack.new_messages_handled == batch as u64 => {}
                                _ => out.errors += 1,
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
        let outs: Vec<SenderOut> = handles.into_iter().map(|h| h.join().expect("sender")).collect();
        (outs, cpu0, cpu1)
    });
    svc.shutdown();

    let ops: u64 = outs.iter().map(|o| o.ops).sum();
    let messages: u64 = outs.iter().map(|o| o.messages).sum();
    let errors: u64 = outs.iter().map(|o| o.errors).sum();
    let min_msgs = outs.iter().map(|o| o.messages).min().unwrap_or(0);
    let max_msgs = outs.iter().map(|o| o.messages).max().unwrap_or(0);
    let user = cpu1.0 - cpu0.0;
    let sys = cpu1.1 - cpu0.1;
    let window = a.duration_s;
    let us_per_msg = if messages > 0 {
        a.shards as f64 * window / messages as f64 * 1e6
    } else {
        0.0
    };
    let cpu_us_per_op = if ops > 0 { (user + sys) / ops as f64 * 1e6 } else { 0.0 };
    if a.json {
        println!(
            "{{\"schema\":\"batch\",\"lang\":\"rust\",\"alloc\":\"{ALLOC_NAME}\",\"batch\":{},\
\"shards\":{},\"producers\":{},\"preload\":{},\"seed\":{},\"duration_s\":{:.3},\"warmup_s\":{:.3},\
\"ops\":{ops},\"messages\":{messages},\"errors\":{errors},\"messages_min_sender\":{min_msgs},\
\"messages_max_sender\":{max_msgs},\"ops_per_s\":{:.1},\"messages_per_s\":{:.1},\
\"us_per_message_per_sender\":{:.3},\"cpu_user_s\":{user:.4},\"cpu_sys_s\":{sys:.4},\
\"cpu_us_per_op\":{cpu_us_per_op:.4}}}",
            a.batch,
            a.shards,
            a.shards,
            a.preload,
            a.seed,
            a.duration_s,
            a.warmup_s,
            ops as f64 / window,
            messages as f64 / window,
            us_per_msg
        );
    } else {
        println!(
            "UECM batch probe [rust, alloc={ALLOC_NAME}] batch={} shards={} ops/s={:.0} \
us/message/sender={:.2} cpu us/op={:.3} errors={errors}",
            a.batch,
            a.shards,
            ops as f64 / window,
            us_per_msg,
            cpu_us_per_op
        );
    }
}
