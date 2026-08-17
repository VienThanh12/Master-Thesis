# RQ2 boundary classes under model checking

Regenerate with `faults/run_model_checking.sh`. Outcomes are categorical.

- Rust compiler: `rustc 1.97.1 (8bab26f4f 2026-07-14)`
- `loom` 0.7.2 (exhaustive, C11 model), `shuttle` 0.9.2 (PCT, sampled)
- Run timeout: 180s

## Detection

| Defect class | Loom | Shuttle | Diagnostic |
|---|---|---|---|
| `lock_order_deadlock` | reported | reported | `deadlock; threads = [(Id(0), Blocked(Location(None))), (Id` |
| `lost_update` | reported | reported | `assertion left == right failed: lost update: messages_hand` |

## Controls

The defect models are only informative if the same checker stays quiet on
the fixed version. Consistent lock order for the deadlock; one critical
section spanning the read-modify-write for the lost update.

| Control | Checker | Outcome |
|---|---|---|
| `loom_control_lock_order` | Loom | clean |
| `shuttle_control_lock_order` | Shuttle | clean |
| `loom_control_atomic` | Loom | clean |
| `shuttle_control_atomic` | Shuttle | clean |

## Cost, which is the half of RQ2 this answers

Neither `faults/rust/deadlock.rs` nor `faults/rust/lost_update.rs` runs
under either checker as written. Each had to be re-imported against the
checker's own `sync` and `thread` modules, because a tool that does not
intercept the primitive cannot schedule it; and each had to be shrunk to
model size -- the lost-update model drops from 20 000 iterations per thread
to one, and the deadlock model loses the `thread::sleep` that widens its
window on real hardware.

So the Rust answer for the boundary classes is **detected at test time,
after a rewrite**. Compare the C++ side, where ASan and TSan take the
program as written and need no rewrite at all -- and where, for these same
two classes, TSan finds neither (`results/taxonomy.md`). The two halves
point in opposite directions: C++ tooling accepts the program unchanged and
misses the defect; Rust tooling finds it, but only once the program has been
rewritten into the tool's primitives. Neither language's story here is the
simple one.
