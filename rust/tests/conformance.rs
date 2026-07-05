//! Conformance + concurrency tests, mirroring the C++ suite and the spec's
//! example vector (§11.3). Run with `cargo test`.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;

use uecm::hash::{fnv1a_64, shard_index, FnvBuildHasher};
use uecm::{
    Config, CreateParams, DrbEntry, OpError, ReconfigParams, Service, ShardCore, SignalingMsg,
    UeState, MAX_DRBS,
};

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

// --- Pinned hashing (§8) ----------------------------------------------------
#[test]
fn hash_shard_index_range_and_determinism() {
    for &n in &[1u64, 2, 8, 13, 64] {
        for id in 0u64..1000 {
            let s = shard_index(id, n);
            assert!(s < n, "shard_index out of range");
            assert_eq!(s, shard_index(id, n), "shard_index not deterministic");
        }
    }
}

#[test]
fn hash_fnv1a_matches_std_hashmap_hasher() {
    // The FnvBuildHasher used by ShardCore's map must agree with fnv1a_64.
    use std::hash::BuildHasher;
    let bh = FnvBuildHasher;
    for id in [0u64, 1, 2, 1234, u64::MAX, 1_000_001] {
        assert_eq!(
            bh.hash_one(id),
            fnv1a_64(id),
            "map hasher != fnv1a_64 for {id}"
        );
    }
    assert_ne!(fnv1a_64(1), fnv1a_64(2));
    assert_eq!(fnv1a_64(1234), fnv1a_64(1234));
}

// --- ShardCore state machine (§11.3 vector + error model) -------------------
#[test]
fn shard_core_state_machine() {
    let seq = Arc::new(AtomicU64::new(0));
    let mut core = ShardCore::new(Config::default(), Arc::clone(&seq));

    // Example vector.
    assert!(core.create_context(1001, &cp(7)).is_ok());
    assert!(core.setup_connection(1001).is_ok());

    let ack = core.handle_signaling(1001, &sig(3, 10)).unwrap();
    assert!(ack.accepted);
    assert_eq!(ack.new_messages_handled, 1);

    assert_eq!(core.setup_connection(1001), Err(OpError::InvalidState)); // not Idle

    let v = core.lookup(1001).unwrap();
    assert_eq!(v.state, UeState::Connected);
    assert!(v.drbs.is_empty());
    assert_eq!(v.messages_handled, 1);

    assert!(core.release_context(1001).is_ok());
    assert_eq!(core.release_context(1001), Err(OpError::NotFound)); // double release
    assert_eq!(core.count(), 0);

    // Error model.
    assert_eq!(
        core.create_context(0, &cp(0)),
        Err(OpError::InvalidArgument)
    );
    assert_eq!(core.setup_connection(42), Err(OpError::NotFound));

    assert!(core.create_context(2002, &cp(0)).is_ok());
    assert_eq!(
        core.create_context(2002, &cp(0)),
        Err(OpError::AlreadyExists)
    );

    // signaling requires Connected
    assert_eq!(
        core.handle_signaling(2002, &sig(1, 0)),
        Err(OpError::InvalidState)
    );

    // oversized payload
    assert!(core.setup_connection(2002).is_ok());
    assert_eq!(
        core.handle_signaling(2002, &sig(1, 65)),
        Err(OpError::InvalidArgument)
    );

    // DRBs
    assert!(core
        .add_drb(
            2002,
            DrbEntry {
                drb_id: 1,
                qos_flow_id: 9,
                teid: 100
            }
        )
        .is_ok());
    assert_eq!(
        core.add_drb(
            2002,
            DrbEntry {
                drb_id: 1,
                qos_flow_id: 9,
                teid: 101
            }
        ),
        Err(OpError::AlreadyExists)
    );
    for i in 2..=MAX_DRBS as u8 {
        assert!(core
            .add_drb(
                2002,
                DrbEntry {
                    drb_id: i,
                    qos_flow_id: 0,
                    teid: i as u32
                }
            )
            .is_ok());
    }
    assert_eq!(
        core.add_drb(
            2002,
            DrbEntry {
                drb_id: 99,
                qos_flow_id: 0,
                teid: 0
            }
        ),
        Err(OpError::CapacityExceeded)
    );

    // Reconfiguration
    assert!(core
        .begin_reconfigure(2002, &ReconfigParams { target_cell_id: 55 })
        .is_ok());
    assert_eq!(
        core.handle_signaling(2002, &sig(1, 0)),
        Err(OpError::InvalidState)
    ); // not Connected
    assert!(core.complete_reconfigure(2002).is_ok());
    let v2 = core.lookup(2002).unwrap();
    assert_eq!(v2.state, UeState::Connected);
    assert_eq!(v2.serving_cell_id, 55);
}

// --- Threaded service, functional path (§11.3) ------------------------------
#[test]
fn service_functional() {
    let mut svc = Service::new(Config::default());
    svc.start();

    assert!(svc.create_context(1001, cp(7)).is_ok());
    assert!(svc.setup_connection(1001).is_ok());
    let ack = svc.handle_signaling(1001, sig(3, 10)).unwrap();
    assert!(ack.accepted && ack.new_messages_handled == 1);
    assert_eq!(svc.setup_connection(1001), Err(OpError::InvalidState));
    assert_eq!(svc.lookup(1001).unwrap().state, UeState::Connected);
    assert_eq!(svc.count(), 1);
    assert!(svc.release_context(1001).is_ok());
    assert_eq!(svc.count(), 0);

    svc.shutdown();
}

// --- Concurrent load across shards ------------------------------------------
// Disjoint ue_id ranges per producer, so no cross-thread key conflicts.
#[test]
fn service_concurrent() {
    let cfg = Config {
        n_shards: 8,
        queue_capacity: 256, // small -> exercises blocking backpressure
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();

    const PRODUCERS: u64 = 8;
    const PER_PRODUCER: u64 = 5000;
    let errors = AtomicU64::new(0);

    thread::scope(|s| {
        for p in 0..PRODUCERS {
            let svc = &svc;
            let errors = &errors;
            s.spawn(move || {
                let base = p * 1_000_000 + 1;
                for i in 0..PER_PRODUCER {
                    let id = base + i;
                    if svc.create_context(id, cp(p as u32)).is_err() {
                        errors.fetch_add(1, Ordering::Relaxed);
                    }
                    if svc.setup_connection(id).is_err() {
                        errors.fetch_add(1, Ordering::Relaxed);
                    }
                    for _ in 0..3 {
                        if svc.handle_signaling(id, sig(1, 4)).is_err() {
                            errors.fetch_add(1, Ordering::Relaxed);
                        }
                    }
                    match svc.lookup(id) {
                        Ok(v) if v.messages_handled == 3 => {}
                        _ => {
                            errors.fetch_add(1, Ordering::Relaxed);
                        }
                    }
                    if i % 2 == 1 && svc.release_context(id).is_err() {
                        errors.fetch_add(1, Ordering::Relaxed);
                    }
                }
            });
        }
    });

    assert_eq!(errors.load(Ordering::Relaxed), 0);
    let expected = PRODUCERS * (PER_PRODUCER / 2);
    assert_eq!(svc.count(), expected);

    svc.shutdown();
}
