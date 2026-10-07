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

// Known-answer values for the two functions the specification pins in §8. They
// were computed from the §8 pseudocode by a separate reference implementation,
// not read back out of either language, so these are the checks that hold both
// implementations to the *specified* algorithm rather than merely to each other:
// a self-consistent but wrong hash passes every other test in the suite, and
// would silently change the intra-shard probe sequence and the shard balance
// that the performance comparison depends on.

/// SplitMix64 finalizer output, before the modulo (§8.1).
const MIX_KAT: [(u64, u64); 5] = [
    (0, 0x0000000000000000),
    (1, 0x5692161D100B05E5),
    (2, 0xDBD238973A2B148A),
    (1001, 0x7139BB2427627383),
    (u64::MAX, 0xB4D055FCF2CBBD7B),
];

/// FNV-1a over the 8 little-endian bytes of the key (§8.2).
const FNV_KAT: [(u64, u64); 7] = [
    (0, 0xA8C7F832281A39C5),
    (1, 0x89CD31291D2AEFA4),
    (2, 0xE6BD86443DF8CE07),
    (255, 0x9016B196E349A31A),
    (256, 0xE3757CA7D64666EA),
    (1001, 0x2E5741B73FAF0DDD),
    (u64::MAX, 0x8CF51A8BFCA3883D),
];

// --- Pinned hashing (§8) ----------------------------------------------------
#[test]
fn hash_fnv1a_known_answers() {
    use std::hash::BuildHasher;
    let bh = FnvBuildHasher;
    for (key, digest) in FNV_KAT {
        assert_eq!(fnv1a_64(key), digest, "fnv1a_64({key}) != spec §8.2 digest");
        // The map's hasher must be the same function.
        assert_eq!(bh.hash_one(key), digest, "map hasher != spec §8.2 digest");
    }
}

#[test]
fn hash_shard_index_known_answers() {
    // Checking against the pre-modulo constant for several divisors pins the
    // finalizer at full 64-bit width, including the wrapping multiplies, which
    // a range-and-determinism check cannot do.
    for (id, mixed) in MIX_KAT {
        for n in [1u64, 2, 3, 8, 13, 64, 1000] {
            assert_eq!(
                shard_index(id, n),
                mixed % n,
                "shard_index({id}, {n}) != spec §8.1 value"
            );
        }
    }

    // A non-power-of-two shard count must use the specified modulo, not the
    // bitmask that agrees with it only when n is a power of two. Asserting that
    // the two candidate reductions disagree is what proves the case above is
    // actually discriminating.
    let n = 13u64;
    assert!(
        MIX_KAT
            .iter()
            .any(|&(_, mixed)| mixed % n != mixed & (n - 1)),
        "n=13 must distinguish modulo from bitmask"
    );

    // Every bucket of a non-power-of-two shard count is reachable.
    let mut used = [false; 13];
    for id in 1u64..=2000 {
        used[shard_index(id, 13) as usize] = true;
    }
    assert!(used.iter().all(|&b| b), "some shard never selected");
}

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

#[test]
fn service_async_fifo() {
    let cfg = Config {
        n_shards: 1,
        queue_capacity: 2,
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();

    let create = svc.create_context_async(1001, cp(7));
    let setup = svc.setup_connection_async(1001);
    let signal = svc.handle_signaling_async(1001, sig(3, 10));

    let created = create.recv().expect("create completion");
    let connected = setup.recv().expect("setup completion");
    let signaled = signal.recv().expect("signal completion");
    assert!(created.value.is_ok());
    assert!(connected.value.is_ok());
    assert_eq!(signaled.value.unwrap().new_messages_handled, 1);
    assert!(created.done <= connected.done && connected.done <= signaled.done);
    assert_eq!(created.started, signaled.started);

    svc.shutdown();
}

#[test]
fn service_async_start_stamp() {
    let cfg = Config {
        n_shards: 1,
        queue_capacity: 2,
        stamp_start: true,
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();
    svc.create_context(1001, cp(7)).unwrap();
    svc.setup_connection(1001).unwrap();

    let first = svc.handle_signaling_async(1001, sig(3, 10));
    let second = svc.handle_signaling_async(1001, sig(3, 10));
    let a = first.recv().expect("first");
    let b = second.recv().expect("second");
    assert!(a.value.is_ok());
    assert!(b.value.is_ok());
    assert!(a.started <= a.done);
    assert!(a.done <= b.started);
    assert!(b.started <= b.done);

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
