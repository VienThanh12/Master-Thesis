//! Contended-queue microbenchmark for the Rust implementation.
//!
//! Isolates `sync_channel` and a fresh `mpsc::channel` per request — the same
//! primitives the full service uses under overload — without `ShardCore` work in
//! the path. `N` producer threads each send a job carrying a one-shot completion
//! sender and block on the matching receiver; one consumer thread receives and
//! signals completion.
//!
//! Mirrors `cpp/bench/queue_contention.cpp` operation for operation.

use std::sync::mpsc::{channel, sync_channel, Receiver, Sender, SyncSender};
use std::thread;
use std::time::{Duration, Instant};

enum Job {
    Work(Sender<()>),
    Stop(Sender<()>),
}

struct Args {
    producers: u64,
    capacity: usize,
    seconds: u64,
    json: bool,
}

fn parse_args() -> Args {
    let mut a = Args {
        producers: 7,
        capacity: 1024,
        seconds: 2,
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
            "--producers" => {
                a.producers = next(i);
                i += 2;
            }
            "--capacity" => {
                a.capacity = next(i) as usize;
                i += 2;
            }
            "--seconds" => {
                a.seconds = next(i);
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

struct Result {
    completed: u64,
    wall_s: f64,
}

fn run_once(a: &Args) -> Result {
    let (tx, rx): (SyncSender<Job>, Receiver<Job>) = sync_channel(a.capacity);

    let consumer = thread::spawn(move || loop {
        match rx.recv() {
            Ok(Job::Work(done)) => {
                let _ = done.send(());
            }
            Ok(Job::Stop(done)) => {
                let _ = done.send(());
                break;
            }
            Err(_) => break,
        }
    });

    let deadline = Instant::now() + Duration::from_secs(a.seconds);
    let completed = std::sync::Arc::new(std::sync::atomic::AtomicU64::new(0));

    let t0 = Instant::now();
    let mut producers = Vec::new();
    for _ in 0..a.producers {
        let tx = tx.clone();
        let completed = std::sync::Arc::clone(&completed);
        producers.push(thread::spawn(move || {
            while Instant::now() < deadline {
                let (done_tx, done_rx) = channel();
                tx.send(Job::Work(done_tx)).expect("send");
                done_rx.recv().expect("recv");
                completed.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            }
        }));
    }

    for p in producers {
        let _ = p.join();
    }
    let wall_s = t0.elapsed().as_secs_f64();

    let (stop_tx, stop_rx) = channel();
    tx.send(Job::Stop(stop_tx)).expect("stop send");
    stop_rx.recv().expect("stop recv");
    consumer.join().expect("consumer join");

    Result {
        completed: completed.load(std::sync::atomic::Ordering::Relaxed),
        wall_s: wall_s.max(0.001),
    }
}

fn main() {
    let a = parse_args();

    let _ = run_once(&a);
    let r = run_once(&a);

    let kops = (r.completed as f64) / r.wall_s / 1000.0;
    let ns_per_op = if r.completed > 0 {
        r.wall_s * 1e9 / r.completed as f64
    } else {
        0.0
    };

    if a.json {
        println!(
            concat!(
                r#"{{"lang":"rust","producers":{},"capacity":{},"seconds":{},"#,
                r#""completed":{},"wall_s":{:.4},"throughput_kops":{:.2},"#,
                r#""ns_per_op":{:.1}}}"#
            ),
            a.producers,
            a.capacity,
            a.seconds,
            r.completed,
            r.wall_s,
            kops,
            ns_per_op
        );
    } else {
        println!(
            "Rust queue contention ({} producers, capacity {}, {} s)",
            a.producers, a.capacity, a.seconds
        );
        println!("  completed ops : {}", r.completed);
        println!("  throughput    : {:.2} kops/s", kops);
        println!("  mean ns/op    : {:.1}", ns_per_op);
    }
}
