# Why Rust collapses past saturation

**Date:** 18 September 2026  
**Status:** working note. Not a thesis claim. Do not copy numbers, ratios, or causal
sentences from the WSL2 session into `Ha_Vien_Mastersthesis_2026.tex`, `Thesis_v3.tex`,
the deck, or `figures/gen_macros.tex`.  
**Question:** the overload floor is the largest language effect in the tested family
(`\OverloadThrRatio` at `\OverloadLoad` kops/s). The thesis measures it and does not
localise it. This note separates what the reported campaign already shows from what
the 18 September session added, ranks the remaining causes, and says which probe
should run first.

This is not D1. `docs/TODO.md` D1 is still the Request-size substitution. This note
argues that D1 is the wrong next experiment, and that three cheaper probes should
precede it.

---

## 1. What “Rust failed past saturation” actually is

Rust does not saturate earlier. It holds the offered rate further, then falls into a
deeper hole. The published result is the hole.

From the reported campaign (`campaign-20260827-151927`, unprefixed macros, system
allocator row of `tab:overload` unless noted). Medians over `\NRepeats` repeats:

| Offered (kops/s) | C++ achieved | Rust achieved | C++ CPU % | Rust CPU % | Reading |
| --- | --- | --- | --- | --- | --- |
| 392 (`\TrackingLoadCpp`) | 392 (tracks) | 392 (tracks) | 557 | 545 | Both coping |
| 448 (`\TrackingLoadRust`, `\KneeGapLoad`) | 162 | 448 (tracks) | 669 | 602 | C++ has fallen. Rust has not. Shown, not tested. |
| 560 | 144 | 84 | 669 | 685 | Both on the floor |
| 784 (`\OverloadLoad`) | 147 (`\OverloadThrCpp`) | 84 (`\OverloadThrRust`) | 663 | 682 | Tested comparison. Ratio `\OverloadThrRatio`. 20/20. |

The jemalloc rows are the same ordering and almost the same values (146 / 84 at
784 kops/s). The allocator is not the cause.

Three facts follow, and they constrain every later hypothesis.

1. **The knee is not shared.** `\KneeShared` is `no`. A sentence that says “past
   `\SatKnee`” as if both languages left the tracking band together is already wrong.
   `\SatKnee` is a `min` across variants.
2. **The floor is below each language’s own tracking rate.** C++ can serve 392 kops/s
   at 392 offered and only 147 at 784 offered. Rust can serve 448 and only 84. This is
   not a capacity plateau. It is a collapse. Mogul and Ramakrishnan’s receive livelock
   is the named shape (`docs/LITERATURE_NOTES.md` C.4): the process stays busy and
   completes less. Their mechanism was kernel interrupt livelock, not this queue, so
   cite them for the shape and not for the cause.
3. **The slower variant is not idle.** At 784 kops/s Rust draws *more* total CPU
   (`tab:overloadtest`, +19.5 percentage points under the system allocator) while
   completing less work. CPU per completed operation is `\OverloadCpuPerOpRatio`.
   Section `sec:overload` already reads this as effort spent without finishing, the
   mark of a path that spins or parks and wakes repeatedly.

The inner operation, timed with no queue in the path, still favours Rust
(`\BudgetCoreRust` ns against `\BudgetCoreCpp`, ratio `\BudgetCoreRatio`). The
overload result is therefore not “Rust’s safety checks got expensive.” It is
something that only appears once the producer is late.

Arvidsson and Kaller report a similar cliff for 5G control-plane procedures and
attribute it to stackless `async`/`await`. This study excluded that confound on
purpose: one worker per shard, bounded blocking queue, no asynchronous runtime on
either side. The cliff still appeared. That is why the mechanism is worth pinning
down.

---

## 2. What the harness is actually doing

The producer loop (`cpp/bench/bench.cpp`, `rust/examples/bench.rs`) is
open-loop, one outstanding request per producer:

1. Sleep until the next send time on the intended schedule.
2. Call a typed API that allocates a completion, enqueues on the owning shard, and
   blocks until the worker writes the result.
3. Record latency from the *intended* send time, with Gil Tene’s coordinated-omission
   correction.

Seven producers, seven shards, queue capacity 1024. At most seven messages exist at
once. The bounded queue never fills. Overload is “the send interval is shorter than
the round-trip”, not “`push` blocks on a full queue.” Spec §7’s backpressure story
is true of the design and false of this operating point.

Once a producer is late, `intended` is in the past and the sleep becomes a no-op
(Rust skips `thread::sleep` when `intended <= now`. C++ still calls
`sleep_until` on a past time, which returns immediately but still enters the
kernel). The loop then hammers. Throughput is `7 / mean_round_trip` if the seven
in-flight requests stay spread across shards.

The correction is capped at 10 000 synthetic samples per operation
(`kMaxCorrectionSamples` in `cpp/bench/hdr.hpp`, `MAX_CORRECTION_SAMPLES` in
`rust/examples/bench.rs`). The comments in both files say why: without a cap the
backfill is `O(lateness / interval)` and steals CPU from the producer that is
already behind. Past saturation the reported tail is therefore a lower bound. The
cap does not make the backfill free. It bounds it at 10 000 histogram records on
**every** completed operation once lateness exceeds about 10 000 intervals
(at 784 kops/s that is tens of milliseconds of lateness, and collapsed p50 is
seconds).

Collapsed p50 values of ~3 seconds are not service time. They are “how far behind
the original schedule this producer has drifted.” Achieved throughput is the
quantity that remains interpretable, which is why §4.5 keeps latency out of the
Holm family at `\OverloadLoad`.

---

## 3. What has already been ruled out

Recorded in `spec/SPECIFICATION.md` §12. WSL2, unpaired or lightly repeated,
indicative only. Direction is what they support. Do not quote the absolute kops/s.

| Probe | What moved | Overload ratio | Reading |
| --- | --- | --- | --- |
| C++ `-DUECM_FLAT_MAP=ON` | intra-shard map | n/a (core-op probe) | Closes ~15% of the *operation* gap. Not an overload probe. |
| Rust `--features mutex-queue` | shard queue → mutex + `VecDeque` + two condvars | 1.41× → 1.43× | Queue *synchronisation* is not the cause. |
| C++ `-DUECM_RING_QUEUE=ON` | `std::queue` → preallocated ring | 1.44× → 1.43× | Queue *allocation* is not the cause. 1008 `new`/`delete` pairs per 3000 pushes went to zero. Throughput did not move. |
| `queue_contention` | queue + completion, no `ShardCore` | 55 vs 59 kops/s, `p = \ContentionP` | The two primitives alone do not reproduce the ordering. Thesis §`sec:contention`. |

The spec then names the last untested entry in the forced-idiom log: tagged-struct
dispatch and the 160-byte C++ `Request` (`\CppRequestBytes`) against Rust’s 96
(`\RustRequestBytes`). That is D1.

**That candidate has the wrong sign.** If moving a larger tagged struct through the
queue were the overload cost, C++ would be slower. C++ is the side that still
completes more work. A probe that shrinks the C++ `Request` can still be run, and a
negative result would be useful, but it cannot be the mechanism of a gap in which
C++ *wins*.

The same inversion sits in the full-draft discussion
(`Ha_Vien_Mastersthesis_2026.tex`, RQ1 paragraph after the Arvidsson discussion):
the cause is narrowed to “extra work on the C++ handoff path.” Extra work on the
winning side does not explain a loss on the other. Do not copy that sentence
forward. Fix it only if a probe localises the gap, otherwise say the path as a
whole and stop.

Also ruled out by the campaign itself, without a probe:

- **jemalloc vs libc.** Both allocators, same sign, same magnitude.
- **Safety model / bounds checks.** The effect appears only once the handoff is
  contended. The operation timed apart is faster in Rust.
- **Async runtime.** None on either side.
- **Host.** Guest `\GuestOverloadThrRatio`, 26 Aug bare metal `\BmOverloadThrRatio`,
  reported campaign `\OverloadThrRatio`. Same ordering.

A 26 Aug attempt to re-run the queue probes on the EPYC at 512 kops/s is discarded
on purpose. That rung is metastable for Rust (bimodal across repeats). A median of
two modes is not a measurement. Spec §12 already says this. Any new probe runs at
`\OverloadLoad` (784 kops/s on the reported design), past the metastable band.

---

## 4. What the 18 September session added

Laptop: Intel Core Ultra 5 135U, 14 logical CPUs, WSL2. 7 shards + 7 producers =
14 threads, fully subscribed. The reported host pins 16 cores for the same 14
threads and has two spare. `rustc` 1.97.1, same as `\MainRustc`. Two repeats
unless noted. **Indicative. Not for the thesis.**

### 4.1 Closed loop versus open loop, full service

Same binaries, mixed workload, 7/7, 5 000 active UEs, 10 000 warmup.

| Mode | C++ kops/s | Rust kops/s | Ratio (C++/Rust) |
| --- | --- | --- | --- |
| Closed loop (`--ops 20000`, no `--rate`, so no 10 000-sample backfill) | 69.3, 68.6 | 66.1, 73.1 | ~1.0 |
| Open loop, 140 kops/s offered (`--rate 20000 --max-run-s 2`) | 48.9, 42.3 | 34.0, 32.4 | ~1.4 |

Open-loop CPU was higher while completing less (C++ ~500–514%, Rust ~549–564%),
which is the same signature as `tab:overload`.

On this host the reversal is a property of **falling behind the send schedule**,
not of the service’s maximum hammering rate. Request size, variant dispatch,
`ShardCore`, and the per-request completion channel are present in both rows.
They cannot be the whole explanation of a gap that appears in only one of them.

The reported campaign never ran closed loop. Every published overload number is
open-loop with the capped backfill.

### 4.2 Isolated histogram backfill

Same bounds as the benches (1 ns to 3.6 s, three significant figures). Cap 10 000.
One call of `record_corrected` / the Rust twin, timed over 2 000 iterations.

| Input | C++ `hdr.hpp` | Rust `hdrhistogram` 7.5.4 |
| --- | --- | --- |
| Collapsed p50 (~3.2 s late, interval 8.93 µs) | 19.0 µs per completed op | 30.2 µs |
| Below-knee sample (40 µs) | 9.4 ns | 10.0 ns |

The Rust crate’s `saturating_record` does index lookup, `saturating_add`,
`update_min_max`, and a `Result` unwrap on every sample. The C++ backfill loop
only does `counts_index_for` and `++counts[i]`. Once lateness is seconds, this
cost is paid in full on every retired operation, on the producer thread, before
the next send. It is invisible below the knee.

A back-of-envelope on the *reported* floor, not to be quoted as a result: at 784
kops/s with seven producers, C++’s 147 kops/s is a 47.6 µs mean round-trip and
Rust’s 84 kops/s is 83.3 µs. Subtracting the isolated backfill leaves ~29 µs
(C++) versus ~53 µs (Rust). HDR explains part of the floor gap, not all of it,
and only in the open-loop collapsed regime. On the EPYC the split may differ.

### 4.3 What `mpsc::channel()` really allocates

`rustc` 1.97’s `std::sync::mpsc::channel()` is `mpmc::channel()` (`library/std/src/sync/mpsc.rs`).
The unbounded flavour is a linked list of blocks (`mpmc/list.rs`). `BLOCK_CAP` is
31. Head and tail are `CachePadded` to 128 bytes.

Per-request allocation, wrapping allocator, 50 000 iterations after warmup, `T = Result<(), u8>`:

| Handle | Allocations | Bytes |
| --- | --- | --- |
| C++ `std::promise` / `std::future` | 2.00 | 88 |
| Rust `mpsc::channel()` | 2.00 | 1016 |

This tax is paid on every call, including below saturation and in closed loop.
`queue_contention` uses the same completion and does not reproduce the overload
ordering (1 producer: Rust 22.0 vs C++ 20.2 kops/s. 7 producers: C++ 57.8 vs
Rust 55.0). So the 1 KiB oneshot is a real cost and not, by itself, the
reversal. Unstable `std::sync::oneshot` wraps `mpmc::sync_channel(1)` (array
flavour, one slot), which is the substitution that would test this tax without
changing the spec’s 1:1 completion rule.

### 4.4 Unfair ping-pong, recorded so it is not reused

A two-thread test that put Rust’s oneshot behind a second unbounded channel, and
C++’s promise behind a spinning atomic, produced 39 µs versus 5 µs. That
comparison does not match the service and is not evidence. `queue_contention` is
the fair isolation of the same two primitives.

---

## 5. Ranked account

From what can currently be defended.

| Rank | Claim | Status | Why |
| --- | --- | --- | --- |
| 1 | The cliff is real, allocator-independent, and reproduced on three hosts. Rust tracks further. The floor favours C++. CPU per completed op favours C++. | **Measured.** Canonical. | Campaign, `tab:overload`, `tab:overloadtest`. |
| 2 | Shard-queue design, shard-queue allocation, and the two primitives in isolation are not the whole explanation. | **Ruled out** as the whole story. WSL2 for the substitutions, reported `tab:contention` for the isolation. | Spec §12, §`sec:contention`. |
| 3 | The reversal is specific to open-loop collapse (producers late, capped CO backfill on). Closed-loop max on this laptop is tied. | **Strong hypothesis.** WSL2 only. | §4.1. Needs the EPYC. |
| 4 | Rust’s histogram crate is ~1.6× slower than the C++ header for a full 10 000-sample backfill (30 µs vs 19 µs). That cost is zero below the knee. | **Measured in isolation.** WSL2. | §4.2. Construct-validity risk for RQ1’s overload half if it survives on the EPYC. |
| 5 | Per-request unbounded `channel()` is a 31-slot MPMC list, ~1 KiB versus an 88-byte promise. | **Measured in isolation.** Always on. | §4.3. Does not create the gap in `queue_contention` or in closed loop here. |
| 6 | C++ 160-byte tagged `Request` versus Rust 96-byte enum. | **Weak.** Wrong sign. | Present in closed loop, where this laptop showed no gap. D1 can still falsify it. |
| 7 | Bounds checks, `unsafe`, jemalloc, async runtime. | **Not the cause.** | Campaign plus design. |

A consistent picture, not yet a localisation:

- Below the knee the producer sleeps. Workers own the cores. HDR backfill is ~10 ns.
  The languages agree at the median. Rust’s core is faster, so Rust tracks further.
- At the first missed interval the producer stops sleeping, the 10 000-sample
  backfill switches on, and seven extra threads stay in the runnable set between
  park and the next send. Throughput falls *below* the tracking rate. That is
  the cliff.
- Rust pays more for the backfill and more for each oneshot allocation. On a
  fully subscribed 14-thread laptop that is enough to open a 1.4× floor gap that
  closed loop does not show. On the EPYC, with two spare cores, the same pair of
  taxes may or may not produce `\OverloadThrRatio`. That is the measurement that
  is missing.

---

## 6. What to run, in order

All three before D1. Each behind a flag or a one-line cap. Compared pair
untouched. Interleaved, paired, at `\OverloadLoad` on the measurement host.
WSL2 numbers stay in this file.

**P0. Closed loop, same 7/7 mixed design, no `--rate`.**

If the 1.7× shrinks, most of the published floor is the open-loop / backfill
regime and not the languages’ maximum rate. That is the cheapest construct check
in the study. The campaign has never reported it.

Throughput is then `ops_total / measured_wall_s` from a long enough `--ops` that
the measured window is seconds, not the warmup. Cap wall time with `--max-run-s`
if a producer would otherwise run forever. Do not enable `--rate`.

**P1. Open loop with the backfill cap at 0 or 1.**

Same `--rate` as the reported overload point. If the floor ratio shrinks, the
`hdrhistogram` crate versus `hdr.hpp` is inside RQ1’s strongest number. The
defensible thesis sentence becomes: the languages diverge past saturation under
this open-loop instrument, and the isolated primitives do not. That is weaker
than “the handoff path” and more honest than D1’s current candidate.

A cap of 0 still records the real sample. It drops only the synthetic backfill.
The collapsed p50 will change. Throughput is the row that must be compared.

**P2. Completion swap: `sync_channel(1)` instead of `channel()`.**

Array flavour, one slot, still a 1:1 blocking completion, no `unsafe`. Unstable
`std::sync::oneshot` is that wrapper. Keep the shard queue on `sync_channel(1024)`.
If the remaining gap after P0/P1 moves, the 31-slot list oneshot was the
service-side piece.

Do **not** start from `std::sync::oneshot` itself. It is unstable and would pull
a nightly story into a freeze that currently has none.

**Then D1**, if anything remains. Shrinking the C++ `Request` while keeping tagged
dispatch. A negative is the likely outcome given the sign, and it is still worth
having so spec §12 can retire that entry.

Re-run the three existing substitution probes on the EPYC only after P0–P2, and
only at 784 kops/s, never at 512. Spec §12 already forbids quoting the 512 kops/s
attempt.

### What each outcome licenses

| P0 closed-loop ratio | P1 HDR-off ratio | P2 oneshot ratio | What the thesis can say |
| --- | --- | --- | --- |
| Still ~1.7 |  |  | The floor is the service, not the instrument. Proceed to P2, then D1. |
| ~1 | Still ~1.7 with HDR on |  | The published floor is an open-loop / backfill effect. RQ1’s overload half has to be scoped to that instrument. |
| ~1 | ~1 |  | Same, and the crate-versus-header cost was the open-loop piece. |
| ~1.7 | ~1.7 | ~1 | The 31-slot oneshot was the service-side piece. Forced-idiom log, not “the language.” |
| ~1.7 | ~1.7 | ~1.7 | Path as a whole. D1 is then the last single-idiom try. A fourth negative retires localisation. |

---

## 7. What must not happen

- Do not add `isolcpus`. It collapses the pin onto one core.
- Do not treat a WSL2 kops/s as a `\OverloadThr*` value.
- Do not describe 448 kops/s as a tested comparison. `\KneeGap*` is shown, not
  tested, because the operating point was found after the data.
- Do not put the 512 kops/s metastable probe back into circulation.
- Do not write that the queue “fills” under this harness.
- Do not attribute the floor to bounds checking, `unsafe`, or jemalloc.
- Do not quote TSan deadlock rates from memory. Irrelevant here, but the same
  class of error.
- Do not edit `figures/gen_macros.tex` by hand if a probe later produces a
  number. A probe that is not the compared pair does not belong in those macros
  at all. Record it in spec §12, like the three existing probes.

---

## 8. Thesis sites that would move, if a probe lands

Only after a measurement-host result, and only the sentence that the result
actually supports.

- `sec:overload` and `sec:contention` in both `Ha_Vien_Mastersthesis_2026.tex`
  and `Thesis_v3.tex`
- `tab:threats` construct row (“attributed but not localised”)
- `tab:findings` RQ1 overload cell
- Chapter 8 / conclusion overload sentence
- `spec/SPECIFICATION.md` §12, a new “Attribution probes” entry
- The inverted “extra work on the C++ handoff path” sentence in the RQ1
  discussion
- `docs/TODO.md` D1, if P0–P2 retire or reorder it

`bench/refresh_thesis.sh` is not required unless a compared-pair number moves.
These probes must not move the compared pair.

---

## 9. Sources for this note

- Reported campaign: `bench/results-canonical2/campaign-20260827-151927.agg.csv`
  and `figures/gen_macros.tex` (`\TrackingLoadCpp`, `\TrackingLoadRust`,
  `\OverloadLoad`, `\OverloadThrCpp`, `\OverloadThrRust`, `\OverloadThrRatio`,
  `\OverloadCpuPerOpRatio`, `\ContentionP`).
- Existing probes: `spec/SPECIFICATION.md` §12, `docs/TODO.md` D1, §`sec:contention`.
- Producer loop and cap: `cpp/bench/bench.cpp`, `cpp/bench/hdr.hpp`,
  `rust/examples/bench.rs`.
- Completions: `rust/src/service.rs` (`channel()` per request),
  `cpp/src/service.cpp` (`std::promise`).
- `rustc` 1.97 mpsc: `$(rustc --print sysroot)/lib/rustlib/src/rust/library/std/src/sync/mpsc.rs`
  and `mpmc/list.rs`.
- 18 September session: closed/open-loop runs of the Release `bench` binaries on
  this WSL2 host, plus `/tmp/overload-research/` probes that are disposable and
  not in the tree.
