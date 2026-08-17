//! The §5.2 transition matrix and the §6.6 error model, enumerated rather than
//! sampled.
//!
//! The existing suites walk representative paths through the state machine:
//! `conformance.rs` follows the §11.3 vector, `invariants.rs` checks that the
//! rejections it happens to try do not mutate. Both choose which cells to
//! visit. This file visits all of them: every operation of §6 applied to a
//! context in every condition it can be in, with the expected result written
//! out as a table that can be read against the specification line by line. A
//! transition that silently became permissive would have to survive a cell that
//! asserts it does not.
//!
//! Three things are checked per cell:
//!   1. the exact `OpError` (or success), from the table;
//!   2. on success, the resulting state, so an op that returns `Ok` but moves
//!      the context somewhere unspecified is caught;
//!   3. on failure, that no field changed at all (§6.1), which the sampled
//!      version could only claim for the rejections it listed.
//!
//! The last section pins the error precedences §6 leaves unordered. These are
//! the cases where two errors are simultaneously true and the specification
//! does not say which is reported; conformance vectors pin them at the
//! transcript level, and these pin them at the typed-API level.
//!
//! Mirrors `cpp/tests/test_state_matrix.cpp` case for case.

use std::sync::atomic::AtomicU64;
use std::sync::Arc;

use uecm::{
    Config, CreateParams, DrbEntry, OpError, ReconfigParams, Service, ShardCore, SignalingMsg,
    UeId, UeState, MAX_DRBS,
};

// --- the four conditions a context can be in --------------------------------
//
// `Released` is deliberately absent: §10.1 I2 says there is no resting
// `Released` context, so "released" is the same condition as `Absent`. That
// equivalence is asserted in `released_is_not_a_resting_state` rather than
// assumed.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Cond {
    Absent,
    Idle,
    Connected,
    Reconfiguring,
}

const CONDS: [Cond; 4] = [Cond::Absent, Cond::Idle, Cond::Connected, Cond::Reconfiguring];

// The operations of §6 that take a `ue_id`. `count()` is the tenth but takes no
// id and cannot fail, so it is checked separately in `count_tracks_live_contexts`.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Op {
    Create,
    Setup,
    Signal,
    AddDrb,
    Begin,
    Complete,
    Abort,
    Release,
    Lookup,
}

const OPS: [Op; 9] = [
    Op::Create,
    Op::Setup,
    Op::Signal,
    Op::AddDrb,
    Op::Begin,
    Op::Complete,
    Op::Abort,
    Op::Release,
    Op::Lookup,
];

/// Where a context ends up when the operation succeeds.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Post {
    /// The cell fails, so there is no post-state to check.
    NotApplicable,
    /// The context no longer exists.
    Gone,
    In(Cond),
}

const BASE_CELL: u32 = 700;
const TARGET_CELL: u32 = 900;

fn params(cell: u32, seed: u8) -> CreateParams {
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

/// Apply one operation, discarding the payload: the matrix is about which error
/// comes back, not what a successful call returns.
fn apply_core(core: &mut ShardCore, op: Op, id: UeId) -> Option<OpError> {
    match op {
        Op::Create => core.create_context(id, &params(BASE_CELL, 0x10)).err(),
        Op::Setup => core.setup_connection(id).err(),
        Op::Signal => core.handle_signaling(id, &sig(2, 8)).err(),
        Op::AddDrb => core
            .add_drb(
                id,
                DrbEntry {
                    drb_id: 3,
                    qos_flow_id: 4,
                    teid: 5,
                },
            )
            .err(),
        Op::Begin => core
            .begin_reconfigure(
                id,
                &ReconfigParams {
                    target_cell_id: TARGET_CELL,
                },
            )
            .err(),
        Op::Complete => core.complete_reconfigure(id).err(),
        Op::Abort => core.abort_reconfigure(id).err(),
        Op::Release => core.release_context(id).err(),
        Op::Lookup => core.lookup(id).err(),
    }
}

fn apply_service(svc: &Service, op: Op, id: UeId) -> Option<OpError> {
    match op {
        Op::Create => svc.create_context(id, params(BASE_CELL, 0x10)).err(),
        Op::Setup => svc.setup_connection(id).err(),
        Op::Signal => svc.handle_signaling(id, sig(2, 8)).err(),
        Op::AddDrb => svc
            .add_drb(
                id,
                DrbEntry {
                    drb_id: 3,
                    qos_flow_id: 4,
                    teid: 5,
                },
            )
            .err(),
        Op::Begin => svc
            .begin_reconfigure(
                id,
                ReconfigParams {
                    target_cell_id: TARGET_CELL,
                },
            )
            .err(),
        Op::Complete => svc.complete_reconfigure(id).err(),
        Op::Abort => svc.abort_reconfigure(id).err(),
        Op::Release => svc.release_context(id).err(),
        Op::Lookup => svc.lookup(id).err(),
    }
}

/// Drive a context into the requested condition. Uses only specified
/// transitions, so a bug in the state machine shows up as a failed setup
/// assertion rather than as a silently wrong starting point.
fn arrange_core(core: &mut ShardCore, id: UeId, cond: Cond) {
    if cond == Cond::Absent {
        return;
    }
    assert!(core.create_context(id, &params(BASE_CELL, 0x10)).is_ok());
    if cond == Cond::Idle {
        return;
    }
    assert!(core.setup_connection(id).is_ok());
    if cond == Cond::Connected {
        return;
    }
    assert!(core
        .begin_reconfigure(
            id,
            &ReconfigParams {
                target_cell_id: TARGET_CELL
            }
        )
        .is_ok());
}

fn arrange_service(svc: &Service, id: UeId, cond: Cond) {
    if cond == Cond::Absent {
        return;
    }
    assert!(svc.create_context(id, params(BASE_CELL, 0x10)).is_ok());
    if cond == Cond::Idle {
        return;
    }
    assert!(svc.setup_connection(id).is_ok());
    if cond == Cond::Connected {
        return;
    }
    assert!(svc
        .begin_reconfigure(
            id,
            ReconfigParams {
                target_cell_id: TARGET_CELL
            }
        )
        .is_ok());
}

fn observed_cond(core: &ShardCore, id: UeId) -> Post {
    match core.lookup(id) {
        Err(_) => Post::Gone,
        Ok(v) => match v.state {
            UeState::Idle => Post::In(Cond::Idle),
            UeState::Connected => Post::In(Cond::Connected),
            UeState::Reconfiguring => Post::In(Cond::Reconfiguring),
            // §10.1 I2 forbids a resting Released context.
            UeState::Released => panic!("observed a resting Released context"),
        },
    }
}

// --- the table --------------------------------------------------------------
//
// Read this against §5.2 (transitions) and §6.6 (error codes). `None` is
// "succeeds". Rows are conditions in `CONDS` order, columns are operations in
// `OPS` order.
#[rustfmt::skip]
const EXPECTED: [[Option<OpError>; 9]; 4] = [
    // create                      setup                        signal
    // adddrb                      begin                        complete
    // abort                       release                      lookup
    /* Absent */
    [None,                         Some(OpError::NotFound),     Some(OpError::NotFound),
     Some(OpError::NotFound),      Some(OpError::NotFound),     Some(OpError::NotFound),
     Some(OpError::NotFound),      Some(OpError::NotFound),     Some(OpError::NotFound)],
    /* Idle */
    [Some(OpError::AlreadyExists), None,                        Some(OpError::InvalidState),
     Some(OpError::InvalidState),  Some(OpError::InvalidState), Some(OpError::InvalidState),
     Some(OpError::InvalidState),  None,                        None],
    /* Connected */
    [Some(OpError::AlreadyExists), Some(OpError::InvalidState), None,
     None,                         None,                        Some(OpError::InvalidState),
     Some(OpError::InvalidState),  None,                        None],
    /* Reconfiguring */
    [Some(OpError::AlreadyExists), Some(OpError::InvalidState), Some(OpError::InvalidState),
     Some(OpError::InvalidState),  Some(OpError::InvalidState), None,
     None,                         None,                        None],
];

#[rustfmt::skip]
const POST_STATE: [[Post; 9]; 4] = [
    /* Absent */
    [Post::In(Cond::Idle),  Post::NotApplicable, Post::NotApplicable,
     Post::NotApplicable,   Post::NotApplicable, Post::NotApplicable,
     Post::NotApplicable,   Post::NotApplicable, Post::NotApplicable],
    /* Idle */
    [Post::NotApplicable,   Post::In(Cond::Connected), Post::NotApplicable,
     Post::NotApplicable,   Post::NotApplicable, Post::NotApplicable,
     Post::NotApplicable,   Post::Gone,          Post::In(Cond::Idle)],
    /* Connected */
    [Post::NotApplicable,   Post::NotApplicable, Post::In(Cond::Connected),
     Post::In(Cond::Connected), Post::In(Cond::Reconfiguring), Post::NotApplicable,
     Post::NotApplicable,   Post::Gone,          Post::In(Cond::Connected)],
    /* Reconfiguring */
    [Post::NotApplicable,   Post::NotApplicable, Post::NotApplicable,
     Post::NotApplicable,   Post::NotApplicable, Post::In(Cond::Connected),
     Post::In(Cond::Connected), Post::Gone,      Post::In(Cond::Reconfiguring)],
];

// --- cases ------------------------------------------------------------------

/// Every (condition, operation) pair, on a fresh core so no cell can be
/// influenced by the one before it.
#[test]
fn every_cell_of_the_transition_matrix() {
    const ID: UeId = 4242;

    for (ci, &cond) in CONDS.iter().enumerate() {
        for (oi, &op) in OPS.iter().enumerate() {
            let mut core = core();
            arrange_core(&mut core, ID, cond);

            let before = core.lookup(ID).ok();
            let count_before = core.count();

            let got = apply_core(&mut core, op, ID);
            assert_eq!(
                got, EXPECTED[ci][oi],
                "matrix[{cond:?}][{op:?}] disagrees with §5.2/§6.6"
            );

            match got {
                None => {
                    // Succeeded: the context must be exactly where §5.2 says.
                    assert_eq!(
                        observed_cond(&core, ID),
                        POST_STATE[ci][oi],
                        "matrix[{cond:?}][{op:?}] landed in the wrong state"
                    );
                    match op {
                        Op::Release => assert_eq!(core.count(), count_before - 1),
                        Op::Create => assert_eq!(core.count(), count_before + 1),
                        _ => {}
                    }
                }
                Some(_) => {
                    // Failed: §6.1 requires the context to be untouched, and a
                    // rejected op must not create or destroy one either.
                    assert_eq!(core.count(), count_before);
                    assert_eq!(
                        core.lookup(ID).ok(),
                        before,
                        "matrix[{cond:?}][{op:?}] mutated on a rejected op"
                    );
                }
            }
        }
    }
}

/// §6.1: `ue_id == 0` is rejected with `InvalidArgument` for every operation,
/// and the rejection happens before anything else is considered.
#[test]
fn ue_id_zero_is_rejected_everywhere() {
    for &op in OPS.iter() {
        let mut core = core();
        // A populated shard, so the rejection is not an artefact of an empty map.
        assert!(core.create_context(1, &params(1, 0)).is_ok());
        assert!(core.setup_connection(1).is_ok());

        assert_eq!(
            apply_core(&mut core, op, 0),
            Some(OpError::InvalidArgument),
            "{op:?} must reject ue_id 0"
        );
        assert_eq!(core.count(), 1);
    }
}

/// The same matrix through the threaded facade. Routing, queueing and the
/// completion handoff must not change any result; the transcript vectors show
/// this for the paths they walk, this shows it for all 36 cells.
#[test]
fn the_service_facade_preserves_the_matrix() {
    const ID: UeId = 4242;

    for (ci, &cond) in CONDS.iter().enumerate() {
        for (oi, &op) in OPS.iter().enumerate() {
            let mut svc = Service::new(Config::default());
            svc.start();
            arrange_service(&svc, ID, cond);

            assert_eq!(
                apply_service(&svc, op, ID),
                EXPECTED[ci][oi],
                "service matrix[{cond:?}][{op:?}] disagrees with the core"
            );
            svc.shutdown();
        }
    }
}

/// §10.1 I2: `Released` is transient-terminal. After release the context is
/// gone, not sitting in a fourth observable state, so every operation behaves
/// exactly as it does for a context that never existed.
#[test]
fn released_is_not_a_resting_state() {
    const ID: UeId = 77;

    for (oi, &op) in OPS.iter().enumerate() {
        let mut core = core();
        assert!(core.create_context(ID, &params(BASE_CELL, 0x10)).is_ok());
        assert!(core.setup_connection(ID).is_ok());
        assert!(core.release_context(ID).is_ok());
        assert_eq!(core.count(), 0);

        assert_eq!(
            apply_core(&mut core, op, ID),
            EXPECTED[0][oi], // the Absent row
            "a released context must behave as absent for {op:?}"
        );
    }
}

/// §6.6 read as a closed set: `count()` is the one operation with no id and no
/// failure mode, so it is checked here rather than in the matrix.
#[test]
fn count_tracks_live_contexts() {
    let mut core = core();
    assert_eq!(core.count(), 0);

    for id in 1..=10u64 {
        assert!(core.create_context(id, &params(1, 0)).is_ok());
        assert_eq!(core.count(), id);
    }
    // Failed creates must not move it.
    assert!(core.create_context(5, &params(1, 0)).is_err());
    assert!(core.create_context(0, &params(1, 0)).is_err());
    assert_eq!(core.count(), 10);

    for id in 1..=10u64 {
        assert!(core.release_context(id).is_ok());
        assert_eq!(core.count(), 10 - id);
    }
    assert!(core.release_context(1).is_err());
    assert_eq!(core.count(), 0);
}

// --- error precedence -------------------------------------------------------
//
// §6 lists each operation's errors as a set, so where two are true at once it
// does not say which is reported. Both implementations already agree on all
// four orderings; these exist so the agreement cannot drift unnoticed.

/// Argument validation runs before the key lookup: an oversized payload on an
/// id that does not exist is `InvalidArgument`, not `NotFound`.
#[test]
fn argument_checks_precede_key_lookup() {
    let mut core = core();

    assert_eq!(
        core.handle_signaling(999, &sig(1, 65)),
        Err(OpError::InvalidArgument)
    );

    // ... and before the state check, on a context that exists but is Idle.
    assert!(core.create_context(1, &params(1, 0)).is_ok());
    assert_eq!(
        core.handle_signaling(1, &sig(1, 65)),
        Err(OpError::InvalidArgument)
    );

    // The boundary itself: 64 is accepted, 65 is not (§6.4).
    assert!(core.setup_connection(1).is_ok());
    assert!(core.handle_signaling(1, &sig(1, 64)).is_ok());
    assert_eq!(
        core.handle_signaling(1, &sig(1, 65)),
        Err(OpError::InvalidArgument)
    );
    // The rejected oversized message must not have been counted.
    assert_eq!(core.lookup(1).unwrap().messages_handled, 1);
}

/// `create_context` checks shard capacity before duplicate detection, so
/// creating an id that already exists on a full shard reports
/// `CapacityExceeded`.
#[test]
fn capacity_precedes_duplicate_on_create() {
    let cfg = Config {
        max_contexts_per_shard: 2,
        ..Config::default()
    };
    let mut core = ShardCore::new(cfg, Arc::new(AtomicU64::new(0)));

    assert!(core.create_context(1, &params(1, 0)).is_ok());
    assert!(core.create_context(2, &params(1, 0)).is_ok());

    // Shard is full. A fresh id and an existing id both report the capacity
    // error; the duplicate never gets as far as being noticed.
    assert_eq!(
        core.create_context(3, &params(1, 0)),
        Err(OpError::CapacityExceeded)
    );
    assert_eq!(
        core.create_context(1, &params(9, 9)),
        Err(OpError::CapacityExceeded)
    );

    // And the existing context was not overwritten by the rejected create.
    assert_eq!(core.lookup(1).unwrap().serving_cell_id, 1);
}

/// `add_drb` checks the state first, then the DRB cap, then duplicate `drb_id`.
#[test]
fn add_drb_precedence_is_state_then_capacity_then_duplicate() {
    let mut core = core();
    assert!(core.create_context(1, &params(1, 0)).is_ok());
    assert!(core.setup_connection(1).is_ok());

    for i in 0..MAX_DRBS as u8 {
        assert!(core
            .add_drb(
                1,
                DrbEntry {
                    drb_id: i + 1,
                    qos_flow_id: 0,
                    teid: i as u32,
                }
            )
            .is_ok());
    }

    // Full list. A new drb_id is CapacityExceeded, which the existing suite
    // covers; an *existing* drb_id is also CapacityExceeded, which it does not.
    assert_eq!(
        core.add_drb(
            1,
            DrbEntry {
                drb_id: 99,
                qos_flow_id: 0,
                teid: 0
            }
        ),
        Err(OpError::CapacityExceeded)
    );
    assert_eq!(
        core.add_drb(
            1,
            DrbEntry {
                drb_id: 1,
                qos_flow_id: 0,
                teid: 0
            }
        ),
        Err(OpError::CapacityExceeded)
    );
    assert_eq!(core.lookup(1).unwrap().drbs.len(), MAX_DRBS);

    // With the list still full, leaving Connected makes the state error win
    // over the capacity error.
    assert!(core
        .begin_reconfigure(1, &ReconfigParams { target_cell_id: 2 })
        .is_ok());
    assert_eq!(
        core.add_drb(
            1,
            DrbEntry {
                drb_id: 1,
                qos_flow_id: 0,
                teid: 0
            }
        ),
        Err(OpError::InvalidState)
    );

    // Duplicate detection does still fire when the list has room.
    assert!(core.complete_reconfigure(1).is_ok());
    assert!(core.release_context(1).is_ok());
    assert!(core.create_context(2, &params(1, 0)).is_ok());
    assert!(core.setup_connection(2).is_ok());
    assert!(core
        .add_drb(
            2,
            DrbEntry {
                drb_id: 7,
                qos_flow_id: 0,
                teid: 0
            }
        )
        .is_ok());
    assert_eq!(
        core.add_drb(
            2,
            DrbEntry {
                drb_id: 7,
                qos_flow_id: 1,
                teid: 1
            }
        ),
        Err(OpError::AlreadyExists)
    );
    assert_eq!(core.lookup(2).unwrap().drbs.len(), 1);
}

/// §5.2 calls abort the path where state is "restored", but `begin_reconfigure`
/// has already overwritten `serving_cell_id` and neither implementation rolls
/// it back. `states.vec` pins this at the transcript level; pinned here too,
/// because it is the one place the specification's wording and the behaviour
/// differ.
#[test]
fn abort_restores_state_but_not_the_cell() {
    let mut core = core();
    assert!(core.create_context(1, &params(BASE_CELL, 0)).is_ok());
    assert!(core.setup_connection(1).is_ok());
    assert_eq!(core.lookup(1).unwrap().serving_cell_id, BASE_CELL);

    assert!(core
        .begin_reconfigure(
            1,
            &ReconfigParams {
                target_cell_id: TARGET_CELL
            }
        )
        .is_ok());
    assert_eq!(core.lookup(1).unwrap().serving_cell_id, TARGET_CELL);

    assert!(core.abort_reconfigure(1).is_ok());
    assert_eq!(core.lookup(1).unwrap().state, UeState::Connected);
    assert_eq!(core.lookup(1).unwrap().serving_cell_id, TARGET_CELL); // not BASE_CELL

    // complete_reconfigure leaves it in the same place, so the two paths differ
    // only in name.
    assert!(core
        .begin_reconfigure(
            1,
            &ReconfigParams {
                target_cell_id: BASE_CELL
            }
        )
        .is_ok());
    assert!(core.complete_reconfigure(1).is_ok());
    assert_eq!(core.lookup(1).unwrap().serving_cell_id, BASE_CELL);
}
