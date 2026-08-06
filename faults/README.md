# Fault-injection study (RQ2)

This directory implements the RQ2 study: *which classes of memory-safety and
concurrency defects that occur in C++ are eliminated at compile time in Rust, and
at what stage/cost are the remaining ones detected?*

Rather than claiming "Rust has no bugs", we inject a catalogue of classic C++
defects and, for each, record:

1. whether the C++ version is detected at **runtime** by a sanitizer
   (AddressSanitizer / ThreadSanitizer), and by which one; and
2. whether the analogous Rust construct is **rejected at compile time** by the
   borrow checker / type system (and which `rustc` error fires).

The defects are deliberately kept small and self-contained but are flavoured with
the thesis domain (UE contexts, DRB lists, per-context counters) so they map onto
plausible bugs in the UE Context Management service.

## Catalogue

The catalogue is deliberately split into two groups. A catalogue containing only
defects Rust is known to prevent could confirm the expected result but never
disturb it — the outcome would be decided by the choice of test cases. The second
group exists so the study measures the **boundary** of the guarantee rather than
just its interior.

### Within the guarantee — expected to fail to compile

| Defect class | C++ source | Rust counterpart |
|---|---|---|
| Use-after-free | `cpp/uaf.cpp` | `rust/uaf.rs` |
| Double-free | `cpp/double_free.cpp` | `rust/double_free.rs` |
| Iterator invalidation | `cpp/iterator_invalidation.cpp` | `rust/iterator_invalidation.rs` |
| Data race | `cpp/data_race.cpp` | `rust/data_race.rs` |
| Unguarded shared mutation | `cpp/unguarded_mutation.cpp` | `rust/unguarded_mutation.rs` |

Each Rust file here is expected to **fail to compile** — that failure *is* the result.

### Boundary of the guarantee — expected to compile and misbehave

| Defect class | C++ source | Rust counterpart | Why Rust does not prevent it |
|---|---|---|---|
| Lock-order deadlock | `cpp/deadlock.cpp` | `rust/deadlock.rs` | Ownership tracks *aliasing*, not lock *acquisition order* |
| Lost update | `cpp/lost_update.cpp` | `rust/lost_update.rs` | Rust removes *data races*, not *race conditions*: every access is synchronised, the composition is not atomic |

Each Rust file here is expected to **compile and then misbehave** (hang, or produce
a wrong result). The runner records the expected outcome per case and flags any
mismatch in either direction as `[UNEXPECTED]`, so a case that unexpectedly
compiled — or unexpectedly did not — is visible rather than silently absorbed into
the conclusion.

The lost-update case is the sharpest result in the catalogue: **neither** ASan,
TSan, nor the borrow checker reports it, because with every access properly locked
there is no race for a race detector to find.

## Running

```bash
./run_faults.sh
```

The script builds each C++ defect under both `-fsanitize=address` and
`-fsanitize=thread` (at `-O0`, so the optimizer cannot elide an injected defect —
notably new/delete elision hides the double-free at `-O1`), runs it, and compiles
each Rust counterpart with `rustc --edition 2021`. Where the Rust counterpart
compiles, it is also run so that its behaviour is recorded rather than inferred.
Every run is bounded by `timeout` (`RUN_TIMEOUT`, default 25 s) because the
deadlock case hangs by construction. It writes:

- `results/taxonomy.md` — human-readable table (thesis-ready);
- `results/taxonomy.csv` — machine-readable;
- `results/<defect>.<tool>.log` — raw tool output per case.

### WSL2 note

The sanitizer runtimes reject WSL2's default ASLR layout, so runs are wrapped in
`setarch <arch> -R` (disable randomization) when available. The script detects
this automatically.

## Result (this testbed)

See `results/taxonomy.md`, regenerated on every run, for the measured table under
the toolchain versions actually used.

Key observations:

- Within its scope the guarantee is absolute: every one of the five memory-safety
  and data-race defects is a **compile error** in Rust — none can be written in
  safe Rust — whereas in C++ each is valid code whose defect only manifests (if at
  all) at runtime.
- The memory-safety defects (use-after-free, double-free, iterator invalidation)
  are caught by ASan; the data-race defects are caught only by TSan and are
  **invisible to ASan**. No single sanitizer covers the catalogue.
- Runtime detection requires (a) building a dedicated instrumented binary,
  (b) paying the sanitizer's time/memory overhead, and (c) a test input that
  actually exercises the buggy path — none of which is needed for the Rust errors,
  which are reported for every build regardless of test coverage.
- **The guarantee stops at the boundary group.** Both boundary defects compile in
  safe Rust and misbehave exactly as their C++ counterparts do. Rust eliminates
  data races and aliasing errors; it does not eliminate lock-ordering errors or
  atomicity violations. A migration plan that reads "memory-safe" as
  "concurrency-safe" will mis-budget its review effort.
