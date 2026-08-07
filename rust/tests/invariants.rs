//! Specification invariants that the shared conformance vectors cannot express.
//!
//! The `.vec` transcript only carries the canonical result string of each op, so
//! it can see a context's state, cell, DRB *count* and message counter, and
//! nothing else. The properties below need the typed API: the fields the
//! transcript never prints (`security_key`, `rrc_transaction_id`, per-DRB
//! contents), the requirement that a rejected op mutates nothing at all (§6.1),
//! the activity-sequence discipline (§10.3, §11.2), and the structural
//! invariants of §10.1.
//!
//! Mirrors `cpp/tests/test_invariants.cpp` case for case.

use std::sync::atomic::AtomicU64;
use std::sync::Arc;

use uecm::hash::shard_index;
use uecm::{
    Config, CreateParams, DrbEntry, OpError, ReconfigParams, ShardCore, SignalingMsg, UeState,
    MAX_DRBS,
};

fn keyed_params(cell: u32, seed: u8) -> CreateParams {
    let mut security_key = [0u8; 32];
    for (i, b) in security_key.iter_mut().enumerate() {
        *b = seed.wrapping_add(i as u8);
    }
    CreateParams {
        serving_cell_id: cell,
        security_key,
    }
}

fn sig(kind: u8, len: u16) -> SignalingMsg {
    SignalingMsg {
        kind,
        payload_len: len,
        payload: [0u8; 64],
    }
}

fn core() -> ShardCore {
    ShardCore::new(Config::default(), Arc::new(AtomicU64::new(0)))
}

/// §6.1: "On any error, the context MUST remain unchanged (no partial
/// mutation)." The whole view is compared, including `last_activity_seq`: a
/// rejected op must not consume a sequence number either.
#[test]
fn rejected_ops_do_not_mutate() {
    let mut core = core();

    assert!(core.create_context(10, &keyed_params(7, 0x40)).is_ok());
    assert!(core.setup_connection(10).is_ok());
    assert!(core.handle_signaling(10, &sig(1, 8)).is_ok());
    assert!(core
        .add_drb(
            10,
            DrbEntry {
                drb_id: 1,
                qos_flow_id: 5,
                teid: 111
            }
        )
        .is_ok());

    let before = core.lookup(10).unwrap();

    // Every operation that must be rejected from Connected.
    assert_eq!(core.setup_connection(10), Err(OpError::InvalidState));
    assert_eq!(core.complete_reconfigure(10), Err(OpError::InvalidState));
    assert_eq!(core.abort_reconfigure(10), Err(OpError::InvalidState));
    assert_eq!(
        core.create_context(10, &keyed_params(99, 0x99)),
        Err(OpError::AlreadyExists)
    );
    assert_eq!(
        core.handle_signaling(10, &sig(1, 65)),
        Err(OpError::InvalidArgument)
    );
    assert_eq!(
        core.add_drb(
            10,
            DrbEntry {
                drb_id: 1,
                qos_flow_id: 0,
                teid: 222
            }
        ),
        Err(OpError::AlreadyExists)
    );

    assert_eq!(before, core.lookup(10).unwrap());

    // The same from Reconfiguring, where a rejected begin_reconfigure must not
    // commit its target cell.
    assert!(core
        .begin_reconfigure(10, &ReconfigParams { target_cell_id: 33 })
        .is_ok());
    let mid = core.lookup(10).unwrap();
    assert_eq!(mid.serving_cell_id, 33);
    assert_eq!(
        core.begin_reconfigure(10, &ReconfigParams { target_cell_id: 44 }),
        Err(OpError::InvalidState)
    );
    assert_eq!(core.setup_connection(10), Err(OpError::InvalidState));
    assert_eq!(
        core.handle_signaling(10, &sig(1, 0)),
        Err(OpError::InvalidState)
    );
    assert_eq!(
        core.add_drb(
            10,
            DrbEntry {
                drb_id: 2,
                qos_flow_id: 0,
                teid: 0
            }
        ),
        Err(OpError::InvalidState)
    );
    assert_eq!(mid, core.lookup(10).unwrap());
}

/// §10.3 + §11.2: the sequence counter is stamped on successful mutations only,
/// and per context the stamps are strictly increasing.
#[test]
fn activity_seq_discipline() {
    let mut core = core();

    assert!(core.create_context(20, &keyed_params(1, 0)).is_ok());
    let after_create = core.lookup(20).unwrap().last_activity_seq;

    // Read-only ops must not stamp anything (§6.1).
    let _ = core.lookup(20);
    let _ = core.count();
    assert_eq!(core.lookup(20).unwrap().last_activity_seq, after_create);

    // A rejected op must not stamp anything either.
    assert_eq!(
        core.handle_signaling(20, &sig(1, 0)),
        Err(OpError::InvalidState)
    );
    assert_eq!(core.lookup(20).unwrap().last_activity_seq, after_create);

    // Successful mutations advance the stamp, strictly, in order.
    let mut prev = after_create;
    assert!(core.setup_connection(20).is_ok());
    for _ in 0..5 {
        assert!(core.handle_signaling(20, &sig(1, 4)).is_ok());
        let now = core.lookup(20).unwrap().last_activity_seq;
        assert!(now > prev, "last_activity_seq must increase per context");
        prev = now;
    }
}

/// §4.2/§4.4: the fields the conformance transcript never prints must survive a
/// round trip through the store, and the DRB list must keep insertion order and
/// its full contents (the transcript only shows `drbs=<count>`).
#[test]
fn context_fields_round_trip() {
    let mut core = core();

    let p = keyed_params(4242, 0x80);
    assert!(core.create_context(30, &p).is_ok());
    assert!(core.setup_connection(30).is_ok());

    for i in 0..MAX_DRBS as u8 {
        assert!(core
            .add_drb(
                30,
                DrbEntry {
                    drb_id: i + 1,
                    qos_flow_id: i + 20,
                    teid: 100 + i as u32,
                }
            )
            .is_ok());
    }

    let v = core.lookup(30).unwrap();
    assert_eq!(v.ue_id, 30);
    assert_eq!(v.serving_cell_id, 4242);
    assert_eq!(v.security_key, p.security_key);
    assert_eq!(v.rrc_transaction_id, 0); // §4.3: zero on creation
    assert_eq!(v.drbs.len(), MAX_DRBS);
    for (i, d) in v.drbs.iter().enumerate() {
        assert_eq!(d.drb_id, i as u8 + 1);
        assert_eq!(d.qos_flow_id, i as u8 + 20);
        assert_eq!(d.teid, 100 + i as u32);
    }

    // §10.1 I4: drb_ids are unique and the list never exceeds MAX_DRBS.
    let mut ids: Vec<u8> = v.drbs.iter().map(|d| d.drb_id).collect();
    let total = ids.len();
    ids.sort_unstable();
    ids.dedup();
    assert_eq!(ids.len(), total, "drb_ids must be unique");
    assert_eq!(
        core.add_drb(
            30,
            DrbEntry {
                drb_id: 99,
                qos_flow_id: 0,
                teid: 0
            }
        ),
        Err(OpError::CapacityExceeded)
    );
    assert_eq!(core.lookup(30).unwrap().drbs.len(), MAX_DRBS);
}

/// §4.4: lookup hands out a snapshot, never an alias into live shard state.
///
/// The C++ counterpart has to assert this at run time, because there a view
/// holding a pointer into the map would compile and only misbehave later. Here
/// the same mistake is not expressible: `lookup` returns an owned
/// `UeContextView`, and a variant borrowing from the map would make the
/// subsequent `&mut self` calls below fail to compile. The run-time assertions
/// are kept anyway so both suites check the same stated property.
#[test]
fn lookup_returns_a_snapshot() {
    let mut core = core();

    assert!(core.create_context(40, &keyed_params(1, 0)).is_ok());
    assert!(core.setup_connection(40).is_ok());
    assert!(core
        .add_drb(
            40,
            DrbEntry {
                drb_id: 1,
                qos_flow_id: 1,
                teid: 1
            }
        )
        .is_ok());
    let snap = core.lookup(40).unwrap();

    assert!(core.handle_signaling(40, &sig(1, 0)).is_ok());
    assert!(core
        .add_drb(
            40,
            DrbEntry {
                drb_id: 2,
                qos_flow_id: 2,
                teid: 2
            }
        )
        .is_ok());
    assert!(core
        .begin_reconfigure(
            40,
            &ReconfigParams {
                target_cell_id: 777
            }
        )
        .is_ok());

    assert_eq!(snap.messages_handled, 0);
    assert_eq!(snap.drbs.len(), 1);
    assert_eq!(snap.state, UeState::Connected);
    assert_eq!(snap.serving_cell_id, 1);

    // The snapshot also survives the context being destroyed entirely.
    assert!(core.release_context(40).is_ok());
    assert_eq!(snap.ue_id, 40);
    assert_eq!(snap.drbs[0].teid, 1);
}

/// §10.1 I1: every live `ue_id` is stored in exactly one shard, namely
/// `shard_index(ue_id)`. Routing is the service's job, so this drives a bank of
/// `ShardCore`s the way the service does and checks that no id is reachable
/// anywhere else.
#[test]
fn ids_live_only_in_their_own_shard() {
    const SHARDS: u64 = 5; // non-power-of-two on purpose
    const IDS: u64 = 500;

    let seq = Arc::new(AtomicU64::new(0));
    let mut cores: Vec<ShardCore> = (0..SHARDS)
        .map(|_| ShardCore::new(Config::default(), Arc::clone(&seq)))
        .collect();

    for id in 1..=IDS {
        let owner = shard_index(id, SHARDS) as usize;
        assert!(cores[owner].create_context(id, &keyed_params(0, 0)).is_ok());
    }

    let total: u64 = cores.iter().map(|c| c.count()).sum();
    assert_eq!(total, IDS);

    for id in 1..=IDS {
        let owner = shard_index(id, SHARDS) as usize;
        let found = cores.iter().filter(|c| c.lookup(id).is_ok()).count();
        assert_eq!(found, 1, "ue_id {id} must live in exactly one shard");
        assert!(cores[owner].lookup(id).is_ok(), "ue_id {id} in wrong shard");
    }
}
