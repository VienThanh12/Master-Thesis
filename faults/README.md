# Fault-injection study (RQ2)

This directory implements the RQ2 study: *which classes of memory-safety and
concurrency defects that occur in C++ are eliminated at compile time in Rust, and
at what stage/cost are the remaining ones detected?*

Rather than claiming "Rust has no bugs", we inject a catalogue of classic C++
defects and, for each, record:

1. whether the C++ version is detected at **runtime** by a sanitizer
   (AddressSanitizer / ThreadSanitizer / UndefinedBehaviorSanitizer), and by
   which one; and
2. whether the analogous Rust construct is **rejected at compile time** by the
   borrow checker / type system (and which `rustc` error fires).

For the boundary classes, where by construction the compiler has nothing to say,
a third question is asked separately (`run_model_checking.sh`):

3. whether the Rust ecosystem catches at **test time** what the compiler does not
   catch at build time, and at what cost.

The defects are deliberately kept small and self-contained but are flavoured with
the thesis domain (UE contexts, DRB lists, per-context counters) so they map onto
plausible bugs in the UE Context Management service.

## Catalogue

The catalogue is deliberately split into two groups. A catalogue containing only
defects Rust is known to prevent could confirm the expected result but never
disturb it, the outcome would be decided by the choice of test cases. The second
group exists so the study measures the **boundary** of the guarantee rather than
just its interior.

### Within the guarantee: expected to fail to compile

| Defect class | C++ source | Rust counterpart |
|---|---|---|
| Use-after-free | `cpp/uaf.cpp` | `rust/uaf.rs` |
| Double-free | `cpp/double_free.cpp` | `rust/double_free.rs` |
| Iterator invalidation | `cpp/iterator_invalidation.cpp` | `rust/iterator_invalidation.rs` |
| Data race | `cpp/data_race.cpp` | `rust/data_race.rs` |
| Unguarded shared mutation | `cpp/unguarded_mutation.cpp` | `rust/unguarded_mutation.rs` |
| Use-after-move | `cpp/use_after_move.cpp` | `rust/use_after_move.rs` |
| Thread-unsafe handle shared | `cpp/thread_unsafe_sharing.cpp` | `rust/thread_unsafe_sharing.rs` |

Each Rust file here is expected to **fail to compile**, that failure *is* the result.

Two of these seven carry information the other five do not.

**`use_after_move` is the only in-guarantee class no C++ sanitizer reports.** Admission
answers the request from the context it has just moved into the store. A moved-from
object is in a valid but unspecified state, so nothing is corrupted, nothing is
undefined, and ASan, TSan and UBSan all run clean while the acknowledgement goes out
under an empty identity. The rest of the group is caught by at least one of the three,
which is what makes this row the sharper form of the cost argument: the instrumented
build is not merely expensive here, it is empty. Note the honest caveat, which the
thesis states too: `clang-tidy` ships `bugprone-use-after-move` and would plausibly
flag this. No static analyser is run in this study (see the thesis §5.4), so the row
records what the sanitizers report and not a ceiling on C++ tooling.

**`thread_unsafe_sharing` is rejected by a trait bound rather than by the borrow
checker.** Its diagnostic is `E0277`, not an aliasing error: `Rc` is `!Send`, and
`thread::spawn` asks for `Send` in its signature, so the compiler refuses without
analysing the body. The C++ handle carries the same constraint in a comment, because a
comment is the only place C++ has to put it. Every other row in this group is a
borrow-checker rejection, so without this one the table would evidence one mechanism
and the prose would claim two.

### Boundary of the guarantee: expected to compile and misbehave

| Defect class | C++ source | Rust counterpart | Why Rust does not prevent it |
|---|---|---|---|
| Lock-order deadlock | `cpp/deadlock.cpp` | `rust/deadlock.rs` | Ownership tracks *aliasing*, not lock *acquisition order* |
| Lost update | `cpp/lost_update.cpp` | `rust/lost_update.rs` | Rust removes *data races*, not *race conditions*: every access is synchronised, the composition is not atomic |
| Leak through a reference cycle | `cpp/leak_cycle.cpp` | `rust/leak_cycle.rs` | Reference counting cannot collect a cycle in either language, and leaking is safe in Rust by explicit design |
| Integer overflow in a release build | `cpp/integer_overflow.cpp` | `rust/integer_overflow.rs` | `opt-level = 2` leaves `overflow-checks` off, so Rust *defines* the wrap where C++ leaves it undefined |
| Worker failure blast radius | `cpp/worker_failure.cpp` | `rust/worker_failure.rs` | Neither type system says anything about whether a shard is a failure domain |
| Double-free across the seam | `cpp/seam_double_free.cpp` | `rust/seam_double_free.rs` | `Box::into_raw` is where ownership tracking ends, and a C ABI cannot avoid it |
| Forgotten lock guard | `cpp/forgotten_guard.cpp` | `rust/forgotten_guard.rs` | A guard is a value, and leaking a value is safe |

Each Rust file here is expected to **compile and then misbehave** (hang, leak, abort,
or produce a wrong result). The runner records the expected outcome per case and
flags any mismatch in either direction as `[UNEXPECTED]`, so a case that
unexpectedly compiled (or unexpectedly did not) is visible rather than silently
absorbed into the conclusion. It also records *which* misbehaviour each boundary case
should exhibit and checks that against the run, so a boundary case that quietly stopped
reproducing is a violation rather than a row that still reads as evidence.

Two of these seven are newer and are worth reading together.

**`seam_double_free` is not a new defect class, and that is the point.** It is
`double_free` moved to the other side of the rule by being written the way a
foreign-function boundary has to write it. `rust/double_free.rs` is a compile error
because ownership tracks the value; handing a C caller a raw pointer is precisely the
operation that ends that tracking, and `Box::from_raw` then asserts ownership of
whatever address it is given. The C++ half of the pair is deliberately unremarkable and
unchanged, so the Rust column is the only thing that moves. The guarantee is a property
of the language *plus the boundary the component is deployed behind*, which is the
boundary `ffi/` is built on.

**`forgotten_guard` separates "Rust removes this bug" from "Rust removes this class".**
The C++ version fails because a validation path returns before a hand-written unlock,
and there is no hand-written unlock in the Rust version to skip: RAII does remove that
form of it. What it does not remove is the class, because a guard parked anywhere that
outlives the procedure leaves the context locked forever. Where `leak_cycle` shows a
leak costing memory, this shows one costing liveness. No sanitizer reports the C++ side
either: a lock that is never released is not a race and not a cycle, so there is nothing
for a lock-order detector to close.

**Two of the five go the other way, and that is the point of having them.**
LeakSanitizer reports the C++ reference cycle while safe Rust leaks in silence,
and UBSan reports the C++ overflow while Rust's defined wrap says nothing. A
two-sided catalogue that could only ever flatter Rust would not be two-sided;
these are the rows where the C++ tooling is ahead.

The lost-update case remains the quietest in the catalogue: **no** sanitizer
reports it, because with every access properly locked there is no race for a race
detector to find.

Two cases need care in how they are built or read:

- `integer_overflow` is compiled with `-O -C overflow-checks=off` rather than the
  `rustc` defaults, because the outcome depends on the profile. With
  `debug-assertions` on it panics, and a panic is a detection; the thesis compares
  an `opt-level = 2` build (spec §3), so building it any other way would record a
  detection the measured configuration does not have.
- `lock_order_deadlock` is run **twelve times** under TSan rather than once. Its
  detection is schedule-dependent, so a single run records whichever outcome the
  machine happened to give (see below).

## Running

```bash
./run_faults.sh
```

The script builds each C++ defect under `-fsanitize=address`, `-fsanitize=thread`
and `-fsanitize=undefined` (at `-O0`, so the optimizer cannot elide an injected
defect, notably new/delete elision hides the double-free at `-O1`), runs it, and
compiles each Rust counterpart with `rustc --edition 2021` plus any per-case flags
the catalogue records. Where the Rust counterpart compiles, it is also run so that
its behaviour is recorded rather than inferred. Every run is bounded by `timeout`
(`RUN_TIMEOUT`, default 25 s) because the deadlock case hangs by construction. It
writes:

- `results/taxonomy.md`: human-readable table (thesis-ready);
- `results/taxonomy.csv`: machine-readable;
- `results/<defect>.<tool>.log`: raw tool output per case.

UBSan is a third axis rather than a refinement of the other two: signed overflow
is invisible to ASan and TSan alike, so without its own column the
`integer_overflow` class would read as undetected in C++ when in fact it is caught.

```bash
./run_model_checking.sh
```

Runs Loom and Shuttle against the two original boundary classes and writes
`results/model_checking.{md,csv}`. See below.

### WSL2 note

The sanitizer runtimes reject WSL2's default ASLR layout, so runs are wrapped in
`setarch <arch> -R` (disable randomization) when available. The script detects
this automatically.

## Result (this testbed)

See `results/taxonomy.md`, regenerated on every run, for the measured table under
the toolchain versions actually used.

Key observations:

- Within its scope the guarantee is absolute: every one of the seven memory-safety
  and data-race defects is a **compile error** in Rust, none can be written in
  safe Rust, whereas in C++ each is valid code whose defect only manifests (if at
  all) at runtime.
- The memory-safety defects (use-after-free, double-free, iterator invalidation)
  are caught by ASan; the data-race defects are caught only by TSan and are
  **invisible to ASan**. No single sanitizer covers the catalogue, and one
  in-guarantee class (`use_after_move`) is reported by none of the three.
- Runtime detection requires (a) building a dedicated instrumented binary,
  (b) paying the sanitizer's time/memory overhead, and (c) a test input that
  actually exercises the buggy path, none of which is needed for the Rust errors,
  which are reported for every build regardless of test coverage.
- **The guarantee stops at the boundary group.** All seven boundary defects compile
  in safe Rust and misbehave exactly as their C++ counterparts do. Rust eliminates
  data races and aliasing errors; it does not eliminate lock-ordering errors,
  atomicity violations, leaks, wrapping arithmetic, or the blast radius of a
  failed worker, and it eliminates nothing at all inside an `unsafe` block. A
  migration plan that reads "memory-safe" as "concurrency-safe", or as
  "leak-free", or as "fault-tolerant", will mis-budget its review effort.
- **On two boundary classes the C++ tooling is ahead**, which a one-sided
  catalogue could never have shown: LSan reports the reference cycle that safe
  Rust leaks silently, and UBSan reports the overflow that Rust defines to wrap.

## One defect that was not injected (2026-08-17)

Everything above was written on purpose, which is the standing objection to a
fault-injection study: whoever chooses the cases already knows what Rust prevents.
This entry exists because one defect in this repository was not chosen. It is kept
apart from the catalogue for that reason — `run_faults.sh` does not build it and it
does not appear in `results/taxonomy.*`, because it was never a program written to
fail.

**What it was.** A design review of `spec/SPECIFICATION.md` §4–§6 found that §7.1
prohibited submitting an operation outside the service's running window — before
`start()`, or after `shutdown()` — while neither implementation checked for it. The
prohibition was addressed to the caller with no mechanism behind it.

**How the two variants failed.** `Service::submit` indexes the shard vector that
`shutdown()` clears:

| Call | C++ (`cpp/`) | Rust (`rust/`) |
|---|---|---|
| operation after `shutdown()` | **heap-use-after-free** in `BoundedQueue::push` (ASan) | panic: index out of bounds |
| operation before `start()` | **SEGV** on the zero page | panic: index out of bounds |

**Why it carries evidence an injected case cannot.** It was in code written to be
correct, in the variant whose safety claim rests on ThreadSanitizer, and reachable
through the public API by calling documented operations in a documented order. It
survived six C++ test binaries, twenty-five Rust tests, 223 hand-written and 9 006
generated conformance operations, and three clean sanitizer configurations — because
none of them ever called an operation outside the window. ASan finds it only once a
test drives it, which is the third condition listed above ("a test input that
actually exercises the buggy path") observed on this study's own artefact rather than
on a planted one.

**What it is not.** Rust did not prevent this at compile time. Nothing in the borrow
checker knows that a service must be started before it is used; what turned undefined
behaviour into a diagnosable failure was an ordinary slice bounds check — a *runtime*
guarantee, and therefore the same kind of assurance the C++ sanitizer gives rather
than the compile-time kind the taxonomy records. Putting it in a "compile error"
column would be exactly the over-claim the boundary group exists to prevent. The
defensible statement is that checking by default converted a specification gap into a
panic.

**Fixed.** Both implementations now reject the call explicitly (C++ throws
`std::logic_error`, Rust panics), §7.1 states the precondition and the required
failure mode, and both suites cover both directions:
`lifecycle_precondition` in `cpp/tests/test_service.cpp`, and the two
`#[should_panic]` cases in `rust/tests/concurrency.rs`.

## The lock-order deadlock is detected *intermittently*

Recorded here because it corrects an earlier reading of this same case, and
because a single-run harness would hide it.

`TSAN_OPTIONS=detect_deadlocks=1` is pinned by the runner rather than inherited,
since the upstream sanitizers documentation says the detector is off by default
while the libtsan shipped with g++ 13.3 has it on, and an outcome that depends on
which the host provides is not evidence. With it pinned, TSan reports the
lock-order inversion on **some runs and not others**, while the program deadlocks
on *every* run. Take the rate from `results/taxonomy.csv` rather than from here:
successive 12-repeat runs on this host have recorded 4, 5, 7 and 9 hits, and
longer trials 6 of 20 and 7 of 20. The rate is unstable enough that prose should
not describe it as a majority or a minority without checking the current run.
Twelve repeats establish that the detection is intermittent. They do not pin the
rate, and raising `DEADLOCK_REPEATS` is the way to estimate it.

The mechanism is specific and generalises beyond this catalogue. TSan builds its
lock-order graph from acquisitions that **succeed**. `deadlock.cpp` loops, so on
some runs a thread completes an inversion without blocking, the cycle closes, and
the report fires; on others the first inversion blocks, only one edge is ever
recorded, and the detector stays silent — precisely when the bug manifests.
`cpp/deadlock_control.cpp` inverts the same two locks *without* blocking and is
reported every time, which is what establishes the detector was live rather than
misconfigured.

The honest statement for this class is therefore that the tool catches the
inversion the program survives and is unreliable on the one that deadlocks. The
runner records this as `flaky` and reports the rate; collapsing it to `detected`
would describe a 30%-of-the-time detector as a clean catch.

## Model checking the boundary classes (RQ2's second half)

RQ2 asks not only which defects are prevented but **at what stage and cost** the
rest are detected. For the seven in-guarantee classes both halves are answered:
rejected at build time, for nothing. For the boundary classes the sanitizer
columns leave the detection half largely blank, which is unsatisfying for exactly
the cases that carry the falsifiability of the design.

`faults/rust-model-checking/` answers it. Loom explores interleavings exhaustively
under the C11 model; Shuttle samples them with PCT. Both intercept the standard
synchronisation primitives, and both are aimed at these two defects.

| Defect class | Loom | Shuttle |
|---|---|---|
| `lock_order_deadlock` | reported | reported |
| `lost_update` | reported | reported |

Every defect model is paired with a control in which the defect is fixed —
consistent lock order, or the read-modify-write inside one critical section — and
all four controls come out clean, for the same reason `deadlock_control.cpp`
exists.

**The cost is the finding.** Neither `rust/deadlock.rs` nor `rust/lost_update.rs`
runs under either checker as written. Each had to be re-imported against the
checker's own `sync` and `thread` modules, because a tool that does not intercept
the primitive cannot schedule it; and each had to be shrunk to model size — the
lost-update model drops from 20 000 iterations per thread to one, and the deadlock
model loses the `thread::sleep` that widens its window on real hardware.

So the Rust answer is **detected at test time, after a rewrite**, against a C++
side where the sanitizer takes the program unchanged and, for these same two
classes, finds one unreliably and the other not at all. The two halves point in
opposite directions, and neither language's story here is the simple one.

The crate is deliberately separate from `rust/` rather than a dev-dependency of
it: spec §12 records the core as dependency-free, and that claim is load-bearing
for the RQ4 supply-chain argument.

## The unsafe boundary class under Miri

```bash
./run_miri.sh
```

`seam_double_free` is the third boundary class whose detection stage had to be
established rather than argued, and Loom and Shuttle are the wrong tools for it:
nothing about it is a schedule. Miri is the right one. It interprets the program
against the Stacked Borrows aliasing model and reports the second release exactly,
as a dangling box reconstructed from a freed allocation. `run_miri.sh` records the
outcome to `results/miri.{md,csv}` and runs `rust/seam_double_free_control.rs`
beside it, in which the same handle is released once, for the same reason
`deadlock_control.cpp` exists: without a control, "Miri reported the double
release" and "Miri reports anything that goes through `Box::from_raw`" are the
same observation. The control comes out clean.

Miri needs a package rather than a loose file, so the runner generates a throwaway
one under `results/.miri/` whose `[[bin]]` entries point straight at the sources in
`rust/`. Copying them would create a second copy of a defect program that could
drift from the one `run_faults.sh` builds.

**The limit is the finding for a migration.** Miri interprets Rust and cannot
execute a C++ host, so the program checked here uses a Rust stand-in for the host.
The tool that finds this defect cannot be pointed at the configuration the defect
ships in, which is the seam in `ffi/`. Nothing in either toolchain checks that
boundary, which is why the practical answer is to keep the seam small enough to
review by hand.
