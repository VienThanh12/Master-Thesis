//! Loom and Shuttle models of the two RQ2 boundary defect classes.
//!
//! RQ2 asks which defects safe Rust eliminates at compile time **and at what
//! stage and cost the remaining ones are detected**. For the five in-guarantee
//! classes `run_faults.sh` answers both halves: the compiler rejects them, at
//! build time, for nothing. For the two boundary classes it records only that
//! neither language prevents them, which leaves the detection-stage half blank
//! for precisely the two cases that carry the falsifiability of the design.
//!
//! The models live in `src/bin/`, one per case, and are classified by
//! `faults/run_model_checking.sh`. See that script and the README for the
//! outcome table.
//!
//! The cost, which is the part RQ2 actually asks about
//! ---------------------------------------------------
//! Neither `faults/rust/deadlock.rs` nor `faults/rust/lost_update.rs` can be
//! handed to a checker as written. Each had to be:
//!
//!   * re-imported against `loom::sync` / `shuttle::sync` and the matching
//!     `thread` module. A model checker that does not intercept the primitive
//!     cannot schedule it, so `std::sync::Mutex` is invisible to both tools;
//!   * shrunk. `lost_update.rs` runs 20 000 iterations per thread to make the
//!     lost update probable on real hardware. One iteration per thread is
//!     enough here, because a checker does not need the defect to be probable,
//!     only reachable;
//!   * stripped of the `thread::sleep` that widens the race window in
//!     `deadlock.rs`. Sleeping is how you persuade a real scheduler to
//!     cooperate and it means nothing to a tool that owns the schedule.
//!
//! So the answer for the Rust half of the boundary classes is: detected, at
//! test time, but only after the defect is rewritten into the checker's
//! primitives and scaled down to model size. That is a real cost, and a
//! different one from the C++ side, where the sanitiser takes the program as
//! written and the rewrite is unnecessary.
//!
//! Why each defect model is paired with a control
//! ----------------------------------------------
//! Every defect binary has a sibling in which the defect is fixed -- consistent
//! lock order, or the whole read-modify-write inside one critical section --
//! and which must come out clean. Without it, "the checker found the defect"
//! and "the checker reports everything" are indistinguishable, which is the
//! same reason `faults/cpp/deadlock_control.cpp` exists.

/// Printed by a model that completed without the checker objecting. The runner
/// matches on it, so a binary that exits zero without having actually run its
/// model cannot be recorded as clean.
pub const CLEAN_MARKER: &str = "MODEL-CLEAN";
