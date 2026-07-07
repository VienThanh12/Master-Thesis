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

| Defect class | C++ source | Rust counterpart |
|---|---|---|
| Use-after-free | `cpp/uaf.cpp` | `rust/uaf.rs` |
| Double-free | `cpp/double_free.cpp` | `rust/double_free.rs` |
| Iterator invalidation | `cpp/iterator_invalidation.cpp` | `rust/iterator_invalidation.rs` |
| Data race | `cpp/data_race.cpp` | `rust/data_race.rs` |
| Unguarded shared mutation | `cpp/unguarded_mutation.cpp` | `rust/unguarded_mutation.rs` |

Each Rust file is expected to **fail to compile** — that failure *is* the result.

## Running

```bash
./run_faults.sh
```

The script builds each C++ defect under both `-fsanitize=address` and
`-fsanitize=thread` (at `-O0`, so the optimizer cannot elide an injected defect —
notably new/delete elision hides the double-free at `-O1`), runs it, and compiles
each Rust counterpart with `rustc --edition 2021`. It writes:

- `results/taxonomy.md` — human-readable table (thesis-ready);
- `results/taxonomy.csv` — machine-readable;
- `results/<defect>.<tool>.log` — raw tool output per case.

### WSL2 note

The sanitizer runtimes reject WSL2's default ASLR layout, so runs are wrapped in
`setarch <arch> -R` (disable randomization) when available. The script detects
this automatically.

## Result (this testbed)

`g++ 13.3.0` (`-std=c++23`), `rustc 1.96.0` (`--edition 2021`):

| Defect class | C++ ASan | C++ TSan | C++ detection | Rust outcome |
|---|---|---|---|---|
| Use-after-free | detected | detected | runtime (ASan+TSan) | compile-time prevented (E0499) |
| Double-free | detected | clean | runtime (ASan) | compile-time prevented (E0382) |
| Iterator invalidation | detected | detected | runtime (ASan+TSan) | compile-time prevented (E0502) |
| Data race | clean | detected | runtime (TSan) | compile-time prevented (E0373) |
| Unguarded shared mutation | clean | detected | runtime (TSan) | compile-time prevented (E0502) |

Key observations:

- Every injected defect is a **compile error** in Rust — none can be written in
  safe Rust — whereas in C++ each is valid code whose defect only manifests (if at
  all) at runtime.
- The memory-safety defects (use-after-free, double-free, iterator invalidation)
  are caught by ASan; the concurrency defects (data race, unguarded shared
  mutation) are caught only by TSan and are **invisible to ASan**.
- Runtime detection requires (a) building a dedicated instrumented binary,
  (b) paying the sanitizer's time/memory overhead, and (c) a test input that
  actually exercises the buggy path — none of which is needed for the Rust errors,
  which are reported for every build regardless of test coverage.
