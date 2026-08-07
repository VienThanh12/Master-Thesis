//! Concurrency-model properties (spec §7 and §10.2).
//!
//! The conformance vectors run one operation at a time against the service, so
//! they exercise the routing but say nothing about the queue and completion
//! machinery underneath, which is exactly the part §7 specifies and the part the
//! thesis compares between the two languages. These tests drive the service from
//! several threads at once and assert the guarantees the spec makes about it:
//! blocking backpressure loses nothing (§7.4-7.5), a shard executes its queue in
//! FIFO order (§10.2 O1), and each request's completion goes to its own caller
//! exactly once (§10.2 O3).
//!
//! Mirrors `cpp/tests/test_concurrency.cpp` case for case. The C++ binary needs
//! ThreadSanitizer to make the data-race claim; here `Send`/`Sync` make it at
//! compile time.

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::thread;

use uecm::hash::shard_index;
use uecm::{Config, CreateParams, Service, SignalingMsg, UeId, UeState};

fn cp(cell: u32) -> CreateParams {
    CreateParams {
        serving_cell_id: cell,
        security_key: [0u8; 32],
    }
}

fn sig(kind: u8, len: u16) -> SignalingMsg {
    SignalingMsg {
        kind,
        payload_len: len,
        payload: [0u8; 64],
    }
}

/// §7.4-7.5: the queue is bounded and a full queue blocks the producer rather
/// than dropping or rejecting the request. With a capacity of one and more
/// producers than shards, submission blocks constantly; every operation must
/// still complete and the final population must be exact.
#[test]
fn backpressure_loses_nothing() {
    const PRODUCERS: u64 = 6;
    const PER_PRODUCER: u64 = 400;

    let cfg = Config {
        n_shards: 2,
        queue_capacity: 1, // maximum backpressure
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();

    let errors = AtomicU64::new(0);
    thread::scope(|s| {
        for p in 0..PRODUCERS {
            let svc = &svc;
            let errors = &errors;
            s.spawn(move || {
                let base = p * 100_000 + 1;
                for i in 0..PER_PRODUCER {
                    let id = base + i;
                    if svc.create_context(id, cp(1)).is_err() {
                        errors.fetch_add(1, Ordering::Relaxed);
                    }
                    if svc.setup_connection(id).is_err() {
                        errors.fetch_add(1, Ordering::Relaxed);
                    }
                    if svc.handle_signaling(id, sig(1, 4)).is_err() {
                        errors.fetch_add(1, Ordering::Relaxed);
                    }
                }
            });
        }
    });

    assert_eq!(errors.load(Ordering::Relaxed), 0);
    assert_eq!(svc.count(), PRODUCERS * PER_PRODUCER);
    svc.shutdown();
}

/// §10.2 O1: a shard executes its queue strictly FIFO. Each acknowledgement
/// carries the post-increment message count, so a caller issuing its k-th signal
/// on its own UE must see exactly k. Out-of-order execution or a completion
/// handed to the wrong caller both show up as a wrong number here.
///
/// All the ids are forced onto a single shard so the ordering claim is about one
/// worker's queue rather than about independent workers.
#[test]
fn fifo_within_a_shard() {
    const SIGNALS: u64 = 300;

    let cfg = Config {
        n_shards: 4,
        queue_capacity: 8,
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();

    // Collect ids that all route to shard 0.
    let mut ids: Vec<UeId> = Vec::new();
    let mut id: UeId = 1;
    while ids.len() < 4 {
        if shard_index(id, cfg.n_shards) == 0 {
            ids.push(id);
        }
        id += 1;
    }

    let errors = AtomicU64::new(0);
    thread::scope(|s| {
        for &id in &ids {
            let svc = &svc;
            let errors = &errors;
            s.spawn(move || {
                if svc.create_context(id, cp(1)).is_err() {
                    errors.fetch_add(1, Ordering::Relaxed);
                }
                if svc.setup_connection(id).is_err() {
                    errors.fetch_add(1, Ordering::Relaxed);
                }
                for k in 1..=SIGNALS {
                    // The k-th signal on this context must be acknowledged as the k-th.
                    match svc.handle_signaling(id, sig(1, 0)) {
                        Ok(a) if a.accepted && a.new_messages_handled == k => {}
                        _ => {
                            errors.fetch_add(1, Ordering::Relaxed);
                        }
                    }
                }
            });
        }
    });

    assert_eq!(errors.load(Ordering::Relaxed), 0);
    for &id in &ids {
        assert_eq!(svc.lookup(id).unwrap().messages_handled, SIGNALS);
    }
    svc.shutdown();
}

/// Concurrent readers on the lookup path while a writer mutates the same
/// context. Every snapshot must be internally consistent, and because the shard
/// executes FIFO (O1) a single reader can never observe the counter going
/// backwards.
#[test]
fn concurrent_lookups_are_consistent() {
    const ID: UeId = 4321;
    const SIGNALS: u64 = 2000;

    let cfg = Config {
        n_shards: 4,
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();

    assert!(svc.create_context(ID, cp(9)).is_ok());
    assert!(svc.setup_connection(ID).is_ok());

    let done = AtomicBool::new(false);
    let errors = AtomicU64::new(0);

    thread::scope(|s| {
        for _ in 0..3 {
            let svc = &svc;
            let done = &done;
            let errors = &errors;
            s.spawn(move || {
                let mut seen = 0u64;
                while !done.load(Ordering::Relaxed) {
                    match svc.lookup(ID) {
                        Ok(v) => {
                            // Field-level consistency of the snapshot.
                            if v.ue_id != ID
                                || v.serving_cell_id != 9
                                || v.state != UeState::Connected
                                || v.messages_handled > SIGNALS
                            {
                                errors.fetch_add(1, Ordering::Relaxed);
                            }
                            // Per-reader monotonicity: lookups are submitted one
                            // after another to the same shard, so FIFO execution
                            // forbids a decreasing counter.
                            if v.messages_handled < seen {
                                errors.fetch_add(1, Ordering::Relaxed);
                            }
                            seen = v.messages_handled;
                        }
                        Err(_) => {
                            errors.fetch_add(1, Ordering::Relaxed);
                        }
                    }
                }
            });
        }

        for _ in 0..SIGNALS {
            if svc.handle_signaling(ID, sig(1, 0)).is_err() {
                errors.fetch_add(1, Ordering::Relaxed);
            }
        }
        done.store(true, Ordering::Relaxed);
    });

    assert_eq!(errors.load(Ordering::Relaxed), 0);
    assert_eq!(svc.lookup(ID).unwrap().messages_handled, SIGNALS);
    svc.shutdown();
}

/// §7.1 lifecycle, and the shard-count edge cases the default config hides:
/// a single shard (every id on one worker) and a non-power-of-two shard count.
/// `n_shards = 0` is clamped to 1 by both implementations.
#[test]
fn lifecycle_and_shard_counts() {
    const IDS: u64 = 200;

    for n in [0u64, 1, 3, 7] {
        let cfg = Config {
            n_shards: n,
            ..Config::default()
        };
        let mut svc = Service::new(cfg);
        assert_eq!(svc.n_shards(), if n == 0 { 1 } else { n });
        svc.start();
        svc.start(); // idempotent while running (§7.1)

        for id in 1..=IDS {
            assert!(svc.create_context(id, cp(2)).is_ok());
            assert!(svc.setup_connection(id).is_ok());
        }
        assert_eq!(svc.count(), IDS);
        for id in (1..=IDS).step_by(2) {
            assert!(svc.release_context(id).is_ok());
        }
        assert_eq!(svc.count(), IDS / 2);

        svc.shutdown();
        svc.shutdown(); // idempotent
    }
}
