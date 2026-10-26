# Why Rust collapses past saturation

**Date:** 18–20 September 2026  
**Status:** working note. Three Cherry Chicago AMD EPYC 7443P runs are
certified: P0/P1/P2 on 19 September, P3 on 20 September, and the 14-load
fair-clock sweep the same evening. Do not copy their kops/s into
`figures/gen_macros.tex` or as `\OverloadThr*` values. Those macros still
belong to `campaign-20260827-151927`. The cause sentence of the overload
floor may now move. Do not copy WSL2 numbers into the thesis at all.  
**Question:** the overload floor is the largest language effect in the tested family
(`\OverloadThrRatio` at `\OverloadLoad` kops/s). The thesis measures it and does not
localise it. This note separates what the reported campaign already shows from what
the 18–19 September probes added.

This is not D1. `docs/TODO.md` D1 is still the Request-size substitution. P0, P1,
and P2 on the 7443P retire it as the mechanism of the floor: the gap vanishes
when the HDR cap is 0.

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

**Scope of that table (added 30 September 2026).** Every row was measured with the
fill inside the timed window, on the recorder-dominated gap where C++ wins. It says
nothing about the smaller Rust lead that remains once the fill is deferred. On that
clock the mutex-queue swap removes the Rust lead on a further 7443P (§4.12), so
"queue synchronisation is not the cause" holds for the recorder gap only.

The spec then named the last untested *service-side* entry in the forced-idiom
log: tagged-struct dispatch and the 160-byte C++ `Request` (`\CppRequestBytes`)
against Rust’s 96 (`\RustRequestBytes`). That is D1.

**That candidate has the wrong sign.** If moving a larger tagged struct through the
queue were the overload cost, C++ would be slower. C++ is the side that still
completes more work. A probe that shrinks the C++ `Request` can still be run, and a
negative result would be useful, but it cannot be the mechanism of a gap in which
C++ *wins*. P0–P2 (§4.5) now sit in front of it.

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

### 4.5 P0, P1, P2 on this host (`bench/overload_probes.sh`)

Eight interleaved repeats, mixed, 7/7, 5 000 active UEs, system allocator,
2 s measured. P1 and P2 offered 140 kops/s (`--rate 20000` per producer).
Log: `bench/results/overload_probes-20260918-134345.jsonl`. The script
refused to certify every phase. Quote ranges, not medians.

| Phase | Arm | Throughput range (kops/s) | CPU cluster | Reading |
| --- | --- | --- | --- | --- |
| P0 closed | cpp-closed | 67–100 | ~436% | Overlap with Rust |
| P0 closed | rust-closed | 67–103 | ~461% | Overlap with C++ |
| P1 open, cap 10 000 | cpp-open | 47–62 | ~486% | C++ ahead. Ranges do not overlap. |
| P1 open, cap 10 000 | rust-open | 37–45 | ~538% | Rust slower, busier |
| P1 open, cap 0 | cpp-cap0 | 42–94 | ~437% | Recovers toward P0. One outlier at 42. |
| P1 open, cap 0 | rust-cap0 | 42–96 | ~457% | Recovers toward P0. One outlier at 42. C++ advantage gone. |
| P2 open, cap 10 000 | cpp-open | 51–65 | ~498% | Same instrument as P1 open |
| P2 open, cap 10 000 | rust-open | 37–46 | ~542% | Same as P1 rust-open |
| P2 open, cap 10 000 | rust-oneshot | 40–46 | ~544% | Inside the rust-open range. No move. |

Three directional claims survive the refusal to certify.

1. **Closed loop is tied.** The P0 ranges sit on top of each other. That
   confirms the two-repeat smoke in §4.1 with a proper interleave.
2. **The open-loop gap is the 10 000-sample backfill on this host.** With the
   campaign cap, C++’s range sits entirely above Rust’s, and Rust draws more
   CPU while completing less. With the cap at 0, both arms recover toward the
   closed-loop band, CPU recedes to the closed-loop cluster, and the language
   split is no longer visible. Collapsed p50 stays around a second in every
   open-loop arm, including cap 0: the intended schedule is still the latency
   origin. Throughput is what moved.
3. **`sync_channel(1)` is not the floor.** P2 is a clean negative. The 1 KiB
   list oneshot remains a real allocation tax (§4.3) and does not, in this
   service, produce the overload ordering.

What this does **not** license: a thesis sentence, a `\OverloadThr*` edit, or
a claim that the EPYC floor is “just HDR.” This laptop is fully subscribed
(14 threads on 14 logical CPUs). The reported host pins 16 cores for the
same 14 threads. The isolated backfill in §4.2 already left a residual
round-trip gap after subtracting 19 µs and 30 µs. Cap 0 removes the
histogram cost and whatever else that cost’s cache and scheduling effects
were doing on a fully subscribed machine. On the EPYC those extras may be
smaller. That is why the same script has to run there at 784 kops/s offered,
with enough repeats that the 5% spread check passes.

### 4.6 Certified 7443P (Cherry Chicago, 19 September 2026)

Same script, mixed, 7/7, system allocator, 3 s measured, 10 interleaved
repeats, 784 kops/s offered on P1/P2, `--pin 2-17` after SMT off. Rocky
container `g++` 15.2.1 / `rustc` 1.97.1. Host Ubuntu 24.04.4, `virtualisation:
none`, no `isolcpus`, no `nohz_full`, 512 GB RAM, THP never. This is not
the Nokia/UH 7443 of the reported campaign. It is the same CPU SKU as the
26 August confirmation host. Log:
`bench/results/overload_probes-20260919-153013.jsonl`. Certified: spread
under 5% on every arm.

| Phase | Arm | Median kops/s | 95% CI | CPU | Reading |
| --- | --- | --- | --- | --- | --- |
| P0 closed | cpp-closed | 455 | [454, 458] | ~573% | Rust slightly ahead |
| P0 closed | rust-closed | 487 | [485, 488] | ~592% | C++/Rust 0.94× |
| P1 open, cap 10 000 | cpp-open | 138 | [136, 138] | ~632% | Campaign instrument. 1.67× |
| P1 open, cap 10 000 | rust-open | 83 | [81, 84] | ~650% | Matches `\OverloadThrRust` order |
| P1 open, cap 0 | cpp-cap0 | 446 | [440, 451] | ~569% | Recovers to P0 |
| P1 open, cap 0 | rust-cap0 | 467 | [463, 470] | ~585% | C++/Rust 0.95×. Gap gone. |
| P2 open, cap 10 000 | cpp-open | 138 | [137, 139] | ~632% | Same as P1 open |
| P2 open, cap 10 000 | rust-open | 83 | [81, 84] | ~650% | Same as P1 rust-open |
| P2 open, cap 10 000 | rust-oneshot | 83 | [82, 84] | ~651% | No move. |

The WSL2 direction survives on a 24-core 7443P with two spare cores in the
pin set. The default-cap floor ratio is 1.67× against `\OverloadThrRatio`
on the reported campaign. Cap 0 returns both languages to the closed-loop
band. `sync_channel(1)` does not move the floor. Pairwise *p* = 1.95×10⁻³
on every contrast the script reports (10 paired repeats, the permutation
floor).

This licenses a cause sentence in the thesis. It does not license a
`\OverloadThr*` edit. The published floor is still the campaign's 20-repeat
row. What changes is the attribution: the hole is the 10 000-sample
backfill on the open-loop producer, not the service's maximum rate.

### 4.7 Certified P3 on a second 7443P (Cherry Chicago, 20 September 2026)

Same script, `--phase p3`, mixed, 7/7, system allocator, 3 s measured, 10
interleaved repeats, 784 kops/s offered, `--pin 2-17` after SMT off. Rocky
container `g++` 15.2.1 / `rustc` 1.97.1. Host `calm-husky`, Ubuntu 24.04.4,
kernel 6.17.0-23-generic, `virtualisation: none`, no `isolcpus`, no
`nohz_full`, ~512 GB RAM. Not `exciting-moose` (19 September) and not the
Nokia/UH 7443. Same CPU SKU. Log:
`bench/results/overload_probes-20260920-183540.jsonl`. Certified: spread
1.1–2.9% on every arm.

| Phase | Arm | Median kops/s | 95% CI | CPU | Reading |
| --- | --- | --- | --- | --- | --- |
| P3 start-origin | cpp-start | 448 | [440, 453] | ~568% | Recovered band. Call p50 15.7 µs |
| P3 start-origin | rust-start | 471 | [463, 475] | ~590% | C++/Rust 0.95×. Call p50 15.2 µs |
| P3 fill-after | cpp-after | 453 | [449, 455] | ~571% | Recovers to P1 cap 0 |
| P3 fill-after | rust-after | 454 | [446, 467] | ~592% | C++/Rust 1.00×, *p* = 0.54. Cannot tell |

Start-origin p50 is the language comparison of the call. Rust is not
slower there. Fill-after keeps the intended origin, so p50 stays about a
second of schedule drift (C++ 1260 ms, Rust 1119 ms) and is not a
language result. Throughput in both arms sits with P1 cap 0, not with
the campaign 10 000-sample at-record fill.

The 19 September P1 result already said the floor gap is the at-record
backfill. P3 says the same with the campaign cap still at 10 000, provided
the fill is not charged to the timed loop, and with a clock that never
fills. The compared pair stays `--correction-when record --latency-origin
intended --correction-cap 10000`.

### 4.8 The fair-clock sweep across all fourteen loads (20 September 2026)

`bench/fair_latency_sweep.sh --clocks start` is the full reported grid on
Clock A: latency from the actual send, cap 0, so one real sample per
completed call and no synthetic fill. Same 14 per-producer rates, 7/7,
mixed, four variants, 20 interleaved repeats, 3 s measured, `--pin 2-17`
after SMT off. Host `calm-husky`, the same 7443P as P3. Log:
`bench/results/fair-start-20260920-195304.jsonl`. Worst throughput spread
across the 56 cells is 2.5%, so the whole sweep certifies.

| Offered kops/s | C++ p99 µs | Rust p99 µs | C++ p99.9 | Rust p99.9 | C++ kops/s | Rust kops/s |
| --- | --- | --- | --- | --- | --- | --- |
| 7 | 21.1 | 18.9 | 25.3 | 21.2 | 7 | 7 |
| 56 | 20.7 | 20.1 | 23.5 | 22.2 | 56 | 56 |
| 112 | 20.7 | 19.2 | 24.1 | 22.0 | 112 | 112 |
| 280 | 21.1 | 19.4 | 25.3 | 22.6 | 280 | 280 |
| 392 | 21.5 | 19.6 | 26.3 | 22.9 | 392 | 392 |
| 448 | 21.8 | 19.7 | 26.7 | 23.0 | 445 | 448 |
| 560 | 21.8 | 19.7 | 26.7 | 23.0 | 442 | 471 |
| 784 | 21.8 | 19.7 | 26.7 | 23.0 | 441 | 470 |

Two readings, and the second is the larger one.

1. **Rust's p99 is lower at every one of the fourteen loads**, by 1 to 2 µs,
   and the ordering never crosses. At 784 kops/s offered the paired
   difference is $+1.49\,\mu$s (system) and $+2.66\,\mu$s (jemalloc) against
   C++, exact paired permutation *p* = 3.91×10⁻³ on 16 pairs in both
   allocators. On this clock the service's tail favours Rust throughout.
2. **There is no cliff on this clock.** Both languages track to 448 kops/s
   offered and then *plateau*: 441 (C++) and 470 (Rust) at 784. The reported
   campaign reads 147 and 84 at that same point. So the fall below each
   language's own tracking rate, which is the shape `fig:overload` draws, is
   the at-record fill and not the service. P1 cap 0 said this at one load.
   The sweep says it across the grid.

What this does **not** license. It is not the compared pair, it is not the
Nokia/UH host, and no number here may enter `figures/gen_macros.tex` or
replace `\OverloadThr*`. The published campaign measured what it measured on
its own clock. What changes is the attribution, which §4.5 to §4.7 already
established and this extends from one operating point to the whole sweep.

### 4.9 Clock B across the same fourteen loads (20 September 2026)

`bench/fair_latency_sweep.sh --clocks after` is the campaign's own origin
and cap, with the 10 000-sample fill applied after the timed window. Same
grid, same host, same pin. Log:
`bench/results/fair-after-20260920-213440.jsonl`. Worst throughput spread
2.5%.

Throughput matches Clock A, not the published floor. Both languages track
to 448 kops/s offered. At 784 kops/s offered C++ holds 447 kops/s and Rust
461 (0.97×). System-allocator paired *p* = 7.01×10⁻² (cannot tell).
Jemalloc paired *p* = 3.91×10⁻³ (Rust ahead). Intended-origin p50 is
schedule drift of about a second, so latency on this clock is not service
time. P3 fill-after already said 1.00× at one load. The sweep says the
plateau holds across the grid once the fill is not charged during the
timed loop.

### 4.10 Both overload asymmetries are the same artifact (21 September 2026)

The campaign's overload story has two gaps, pointing opposite ways. At the
knee rung, 448 kops/s offered, Rust still serves 448 kops/s and C++ has
fallen to 162, a factor of 2.8 in Rust's favour (`\KneeGap*`). At 784 kops/s
offered the order reverses and C++ holds 147 against Rust's 84, a factor of
1.7 (`\OverloadThr*`).

Clock B removes both. At 448 kops/s offered C++ holds 447 and Rust 448. At
784 it is 446 and 461. So the deferred fill does not merely delete the gap
that flattered C++, it deletes the one that flattered Rust at a lower load in
the same pass. That matters for how the correction reads: an instrument fix
that deletes a finding in each direction is not a fix chosen for its answer.
`probe_facts.py` reads the knee rung from `\KneeGapLoad` in `gen_macros.tex`
rather than repeating 448, so the two datasets cannot drift onto different
rungs.

### 4.11 Why Clock B cannot become the compared pair (21 September 2026)

Asked whether the fair-clock sweep should simply replace
`campaign-20260827-151927`. It cannot, and the reason is measured rather than
procedural.

Below saturation the two datasets agree. Across all fourteen loads to 392
kops/s, p50, p99 and p99.9 match the campaign within 1--2 µs with the same
ordering. That part would survive a swap untouched.

The far tail does not, and RQ1 names p99.99. Pooling Clock B's sidecar with
`bench/pool_hist.py` (written to
`bench/results/fair-after-20260920-213440.hist.pooled.csv`) and counting the
below-saturation cells where pooled Rust p99.99 is lower:

| Dataset | all 22 cells | the 6 cells at 280--392 kops/s |
| --- | --- | --- |
| `campaign-20260827-151927`, `nohz_full=2-17` | 18/22 | 5/6 |
| `fair-after-20260920-213440`, no `nohz_full` | 13/22 | **0/6** |

Every new sign flip sits at 224 kops/s or above and the top two rungs invert
completely. That is where a missing timer tick would show, and it is why the
far tail is called resolved on the measurement host and nowhere else. A swap
would trade a resolved headline finding for an unresolved one and force the
thesis to retract the claim that the far tail favours Rust.

The rented box is therefore sound for a within-host A/B on the instrument,
which is all the probes were for, and unsound as the compared pair. The only
version worth running is Clock B on the measurement host with `nohz_full`
intact, which changes one thing.

Both the pooling loop in `refresh_thesis.sh` and the campaign discovery in
`plot_figures.py` glob `campaign-*`, so the new pooled CSV cannot be mistaken
for the compared pair.

### 4.12 The deferred-fill lead: where it sits and what carries it (30 September 2026)

The Chicago same-host control (`fair-after-20260924-100100.jsonl`) removed the
recorder gaps and left a smaller Rust lead where throughput stops rising. Full
record in spec §12, 2026-09-30 entry.

**Where it sits, from the Chicago log itself.** Every sender waits for its reply,
so past saturation throughput is the round-trip rate. The core call is at most
`\BudgetCoreShareMax`% of a round-trip, so it cannot carry a lead of several per
cent. Kernel time is 57 to 63% of a call's CPU at the top load, and C++ spends
more of it per call than Rust at all 14 loads on both heaps (1.12 times at 784
kops/s). User time per call is equal or higher in Rust.

**What carries it, on a further 7443P** (Cherry Singapore `immune-bullfrog`,
`nohz_full=2-17`, SMT off, Rocky image, fill after the window):

| Swap, interleaved against stock | Result at 784 kops/s offered | Reading |
| --- | --- | --- |
| C++ `-DUECM_FLAT_MAP=ON` | Rust still ahead in 10 of 10; flat map beats stock C++ in 2 of 10 | The map does not carry the lead. |
| Rust `--features mutex-queue` | Closes 105% of the lead; slower than stock Rust in 9 of 10, *p* = 3.91×10⁻³ | The queue's synchronisation carries it. |
| C++ `-DUECM_RING_QUEUE=ON` (control) | C++ moves 0.4%, *p* = 0.86 | Storage does not matter; the lock does. |

Thread switches per call are the same in every build (2.83 at 56 kops/s, 1.60 to
1.63 at 784 kops/s), so the C++ design costs more kernel time per handoff, not
more sleeps. Counting switches with `perf` slowed every arm by about a tenth and
hid the lead, so the swap reading comes from the uncounted session only.

Not re-measured on the campaign host. The thesis says "on a further host" wherever
it uses this, and the threats paragraph names the host transfer.

### 4.13 A third 7443P, the reply handle, and kernel calls per request (19 October 2026)

**Host.** Cherry Servers Lithuania `composed-killdeer`, AMD EPYC 7443P, 64 GB, Ubuntu
26.04.1, kernel 7.0.0-34-generic, `virtualisation: none`, root UUID `35737914-…`. SMT off
and boost off at runtime, performance governor, `nohz_full=2-17 rcu_nocbs=2-17` (set in
`/etc/default/grub.d/99z-thesis-nohz.cfg`, then reboot), no `isolcpus`, THP `madvise` as on
the campaign host. Docker 29.1.3 running the campaign image `uecm-bench:el8-gcc15-rust1.97.1`
(`g++` 15.2.1 20260123, `rustc` 1.97.1, jemalloc 5.2.1-3.el8, the campaign's versions),
copied from the development laptop rather than rebuilt so no point release could move.
Pin 2-17. **This is a further host, not the campaign host.** Driver:
`bench/run_campaign_followups.sh --pin 2-17 --tag 20261019-killdeer`, which now refuses the
campaign tag on any machine whose root UUID is not the campaign host's. Results:
`bench/results-pipeline-20261019-killdeer/` and `bench/results-probes-20261019-killdeer/`,
both checksummed. The macro generators read neither.

**What replicated.**

- *Several requests in flight* (`pipeline_pilot.sh`, capacity rule froze 560000 per producer,
  3920 kops/s offered, the same rate `major-louse` froze). Medians of 20 interleaved repeats:

  | Workload | C++ system | Rust system | C++ jemalloc | Rust jemalloc |
  | --- | --- | --- | --- | --- |
  | signal: finished kops/s, wait before queue (ms) | 2505, 281.7 | 2449, 295.0 | 2926, 166.1 | 3309, 89.3 |
  | mixed: finished kops/s, wait before queue (ms) | 2527, 274.7 | 2401, 312.1 | 2889, 183.2 | 3234, 97.4 |

  Rust waits less than C++ in 20 of 20 (signal) and 18 of 20 (mixed) repeats on jemalloc,
  and in 3 of 20 and 0 of 20 on the system allocator. The allocator split of
  `tab:pipeline` holds on a third machine.
- *Queue swap past saturation* (`queue_probes.sh --correction-when after`, 784 kops/s offered,
  10 repeats, system heap): `cpp-deque` 431.8, `cpp-ring` 436.0, `rust-channel` 442.5,
  `rust-mutexq` 421.7 kops/s. Rust ahead of C++ in 8 of 10. Rust with the C++ queue is 4.7%
  slower than stock Rust in 9 of 10 (*p* = 3.91×10⁻³), which puts it behind C++ on this clock.
  The clock charges Rust about 2.4% for its own fill (§4.17), so without that it is about
  level with C++. The ring
  moves C++ by 1.0%. Kernel µs per call 8.59, 8.55, 7.72, 8.10. User µs per call 5.26, 5.06,
  6.13, 6.47. Two further hosts now show the queue design carrying the lead.

**The reply handle.**

- *What it allocates* (LD_PRELOAD tracker, campaign image on the WSL2 laptop, per request by
  the difference of two run lengths, senders back to back; allocation counts do not depend
  on the host). Files: `bench/results-alloc-20261019-wsl2/`.

  | Build | Bytes allocated per request | Freed by another thread |
  | --- | --- | --- |
  | C++ as measured | about 390 | a 480-byte deque chunk every third request |
  | C++ ring buffer | about 220 | nothing |
  | Rust as measured | about 2,360 | the 1,744-byte reply block, every request |
  | Rust one-slot reply (`sync-oneshot`) | about 810 | nothing |
  | Rust with the C++ queue (`mutex-queue`) | about 2,380 | the same 1,744-byte block |

  `std::promise` is two blocks (48–63 and 160–175 bytes) made and freed on the sending thread.
  Rust's `channel()` makes a 512-byte shared part (128-byte aligned, so `posix_memalign`) on
  the sender, and its 31-slot block on the worker's first send (`list.rs`, `start_send`).
  The second releaser frees both, which is the sender. The 2026-09 figure of about 1 KiB
  used `T = Result<(), u8>`. The real reply type makes the block 1,744 bytes. The queue swap
  changes no allocation, so the 30 September result is about locking, not memory.
- *In flight* (`pipeline_pilot.sh --reply`, 10 interleaved repeats per workload, same frozen
  rate). On the system allocator the one-slot reply lifts Rust from 2443 to 3171 kops/s
  (signal) and from 2420 to 3065 (mixed), and cuts the median wait from 295 to 112 ms and from
  305 to 141 ms, lower in 10 of 10 both times (exact sign-flip *p* = 0.002, the floor for 10
  pairs). That puts Rust ahead of C++ on both allocators (C++ system 2507 and 2460, jemalloc
  2912 and 2899). On jemalloc the change is small (3333 to 3410, 3225 to 3322). **The
  allocator split comes from Rust's standard reply channel**, whose cross-thread 1,744-byte
  block glibc handles badly and jemalloc well.
- *Past saturation, one request per sender* (`bench/reply_probes.sh`, fill after, 784 kops/s
  offered, 10 interleaved repeats). `cpp-system` 437.1, `rust-system` 443.5,
  `rust-system-oneshot` 449.3, `cpp-jemalloc` 428.4, `rust-jemalloc` 464.0,
  `rust-jemalloc-oneshot` 465.5 kops/s. The one-slot reply changes nothing detectable
  (+1.3%, *p* = 0.88. +0.3%, *p* = 0.79). Rust's allocator effect stays (+4.6% standard,
  +3.6% one-slot). The Rust lead is +1.5% on the system allocator (9 of 10) and +8.3% on
  jemalloc (10 of 10).
- *Superseded laptop pilot.* On WSL2 the one-slot reply did not move Rust in flight. That
  host is not representative: Rust's senders submitted 5 to 10 times fewer requests than
  C++'s there, against near parity on bare metal. Do not cite it.

**Kernel calls per request** (`bench/futex_counts.sh`, bpftrace on the host, separate session,
784 kops/s offered, system heap, difference of 6 s and 3 s runs, 3 repeats, medians).
Tracing slows every arm, so its throughput is not the comparison.

| Per request | cpp-deque | rust-channel | rust-mutexq | cpp-ring | rust-oneshot |
| --- | --- | --- | --- | --- | --- |
| futex waits that slept | 1.48 | 1.43 | 1.45 | 1.47 | 1.43 |
| waits that returned at once | 0.09 | 0.15 | 0.10 | 0.08 | 0.14 |
| wakes that woke a thread | 1.48 | 1.43 | 1.45 | 1.47 | 1.43 |
| wakes that found nobody | 1.63 | 0.22 | 1.59 | 1.63 | 0.20 |
| all system calls | 4.67 | 3.24 | 4.59 | 4.66 | 3.20 |

Sleeps and real wakes are equal in every build. The C++ queue design adds about 1.4 wake
calls per request that wake nobody, and Rust running the same design adds the same calls.
That is the extra kernel time per handoff with no extra thread switches. For the Rust copy
the source explains it: `Condvar::notify_one` makes the system call whether or not a thread
waits (`library/std/src/sys/sync/condvar/futex.rs`, 1.97.1), and `mutex_queue.rs` notifies on
every push and every pop. Rust's channel checks an `is_empty` flag first
(`SyncWaker::notify`). Where glibc makes the C++ empty calls was not traced by function. The
profile in §4.14 shows `__lll_unlock_wake` under `worker_loop`, which fits glibc marking the
mutex contended when a condition-variable wait re-takes it.

### 4.14 What each part of a call costs in overload (Method 1, 19 October 2026)

**Question.** Past saturation, how much of a call is the language's own work on the UE record,
and where do the two builds differ? The overload throughput cannot say, because each sender
has one request out and throughput is seven over the round trip.

**Method.** Same host as §4.13. Profiling builds add debug info and nothing else: the C++
`.text` is byte-identical to the measured build, and of 1,614 Rust functions only
`bench::main` (302 bytes) and the entry shim (7 bytes) differ in size. Each build ran at
784 kops/s offered (112000 per producer, mixed, 7/7, fill after, system heap) for a 10 s timed
phase. Inside the container, `perf` 4.18 sampled the process every 2.85 million cycles (1 ms at
the fixed 2.85 GHz clock) for 4 s, with DWARF unwinding and 32 KB stack copies. `addr2line -i`
from the toolset re-named every frame in our binaries, which resolves the inlined frames that
`perf` prints as `??`. `classify.py` gives each sample a kind (own code, allocator, kernel)
and an owner (UE operation, shard queue, reply handle, service dispatch, harness) from the
first named frame above the leaf. In the C++ build, pthread mutex and condition-variable
frames mark the queue, and `pthread_once` and a direct `syscall()` mark `std::promise`. Rust
frames beyond a parked thread are often mis-unwound (`Thread::park` "called from"
`backtrace_rs::symbolize`). For Rust wait and wake samples outside lock contention the thread
and direction decide: a worker only waits on its queue and wakes its sender, and a sender does
the reverse. On C++, where names are reliable, that rule agrees with the named frame for 99% of
queue and reply time. Three interleaved repeats per build.

**Discarded first pass.** The same profiles sampled with `task-clock` (a software timer) were
biased. They put C++'s UE operation at 0.26 to 0.42 µs and C++'s harness near zero. Cycle
sampling gives equal harnesses and a close UE operation. Those timer-based files were not
copied back. Do not quote numbers from them.

**Result.** µs of CPU per finished call, mean of three repeats (range in brackets):

| Owner | C++ as measured | Rust as measured | Rust one-slot reply |
| --- | --- | --- | --- |
| UE operation | 0.13 (0.11–0.17) | 0.11 (0.09–0.13) | unreliable |
| shard queue, own code / allocator / kernel | 0.63 / 0.14 / 3.43 | 0.90 / 0.00 / 2.98 | 0.83 / 0.05 / 3.38 |
| reply handle, own code / allocator / kernel | 0.56 / 0.05 / 5.74 | 1.15 / 0.57 / 4.78 | 1.31 / 0.24 / 4.31 |
| service dispatch | 0.20 | 0.04 | 0.06 |
| harness | 0.16 | 0.16 | 0.16 |
| total | 11.10 (11.08–11.12) | 10.82 (10.79–10.86) | 10.57 |
| kops/s while profiled | 410 | 430 | 440 |

- **The language's own work is about 1% of a call.** C++: `ShardCore::handle_signaling` 38 ns,
  the `std::unordered_map` lookup 37 ns, `fnv1a_64` 10 ns, `add_drb` 8, `begin_reconfigure` 8.
  Rust: `handle_signaling` 28 ns, hash-map probing about 35 ns (`likely`, `_mm_movemask_epi8`),
  `finish_reconfigure` 6, `begin_reconfigure` 6. The isolated timing (34.5 against 21.3 ns,
  signal only) rises under load and the ratio narrows to about 1.2. The ranges overlap.
- **Rust spends 1.25 µs more per call in user-space queue and reply code.** Reply: the
  cross-core atomic in `Waker::try_select` 140 ns, `Parker::park` 120, `Parker::unpark` 90,
  building the channel (`memmove` into the new box) 85, `Arc<Context>::clone` 78. Reply
  allocation: `_int_free` 170 ns, `memset` 112 (zeroing the new block), `calloc` 86,
  `_int_malloc` 67, `free` 62. Queue: `start_send` 152 ns, `Sender::send` 108, `Mutex::spin`
  96 (the waker's lock), `try_select` 79. C++ by comparison: reply `_M_load` of the promise
  status 117 ns, `exception_ptr` comparison 54, `~promise` 42. Queue `pthread_mutex_lock` 147,
  `pthread_cond_signal` 145, `pthread_cond_wait` 107, moving the 160-byte `Request` 107.
- **C++ spends 1.40 µs more per call in the kernel.** Kernel time by activity, C++ then Rust:
  reply sleeping 2.95 and 2.74, queue sleeping 1.64 and 1.68, reply other 1.52 and 1.03,
  reply waking 1.20 and 0.90, queue other 1.05 and 0.64, queue waking 0.67 and 0.59.
- **Net.** Rust uses 2.5% less CPU per call and finished 5% more calls while profiled. The
  overload difference between the builds is how each standard library hands work between
  threads, not the code each language generates for the operation.

**Limits.** A further host, not the campaign host. Profiling slowed each build by 3 to 6% against
§4.13's untraced runs. About 5.5 µs of each Rust call takes its queue or reply owner from the
thread-and-direction rule. The one-slot build's UE figure ranged 0.000 to 0.067 µs across
repeats, so only its reply numbers are used. Per-call figures divide by the timed-phase
throughput. Files: `bench/results-probes-20261019-killdeer/profile/` (summaries, resolved
samples, scripts, checksums). The 600 MB raw recordings stayed on the rented host.

**jemalloc settings on that day.** `reply_probes.sh`, `pipeline_pilot.sh --reply` and the
batch probe below ran their jemalloc builds with the allocator's defaults, not the campaign's
`thp:never,narenas:16`. So, as far as the scripts show, did the 6 October pipeline runs.
`reply_probes.sh` and `batch_probes.sh` pin the campaign's settings from now on. The
system-allocator results are unaffected.

### 4.15 How much work per handoff before the language decides (Method 2, 19 October 2026)

**Question.** Past saturation the operation is about 1% of a call, so the overload throughput
says almost nothing about the language (§4.14). At what amount of work per handoff does each
language's own speed decide throughput, and what is that speed inside a loaded worker?

**Method.** `bench/batch_probes.sh`, same host as §4.13. A probe-only batched request in both
services (`--features batch-probe`, `-DUECM_BATCH_PROBE=ON`, `Service::handle_signaling_batch`):
one message carries B signalling operations for UEs of one shard, and the worker runs them in
order and answers once with the reply type a single signal call uses. Parity tests:
`cpp/tests/test_batch.cpp`, `rust/tests/batch_probe.rs`. Each of seven senders owns one shard
(5000 preloaded UEs, ids picked by the pinned shard function) and sends batches back to back,
so every B is past saturation. B = 1, 2, 4, …, 1024. Four builds interleaved with the starting
build rotated, 5 repeats, 1 s warm-up, 3 s window, pin 2-17. The time per batch per sender is
fitted as T(B) = h + B·t, least squares weighted by 1/T², with bootstrap intervals over repeats.

**Result.** Medians over repeats, µs per batch per sender:

| B | C++ system | Rust system | C++ jemalloc | Rust jemalloc |
| --- | --- | --- | --- | --- |
| 1 | 14.88 | 12.55 | 14.66 | 12.81 |
| 16 | 16.23 | 13.61 | 15.66 | 12.85 |
| 64 | 20.62 | 16.49 | 21.55 | 15.55 |
| 128 | 32.08 | 22.08 | 33.02 | 22.71 |
| 256 | 56.68 | 37.85 | 55.77 | 42.26 |
| 1024 | 208.97 | 140.53 | 202.74 | 163.55 |

| Fit | handoff h (µs) | per operation t (ns) | crossover B* = h/t |
| --- | --- | --- | --- |
| C++ system | 13.39 [13.19, 13.59] | 167.4 [161.4, 173.6] | 80 [77, 84] |
| Rust system | 11.81 [11.59, 12.09] | 106.6 [104.6, 107.7] | 111 [107, 115] |
| C++ jemalloc | 13.41 [13.27, 14.03] | 168.3 [162.8, 173.3] | 80 [78, 83] |
| Rust jemalloc | 11.26 [11.12, 11.53] | 118.8 [115.9, 121.6] | 95 [92, 99] |

- **The language's own speed in overload.** Inside a loaded worker one signalling operation
  costs C++ 1.57 times what it costs Rust on the system allocator [1.53, 1.62], and 1.42 times
  on jemalloc [1.37, 1.49]. That matches the isolated ratio (34.5 against 21.3 ns, 1.6 times).
  Each operation costs about five times its isolated figure, as expected with 5000 UEs per
  shard drawn at random.
- **The handoff.** 13.4 µs per message in C++ against 11.8 in Rust, 1.13 times [1.10, 1.16].
  This probe has no contention between senders, so h is not the campaign's handoff cost.
- **The crossover.** The operation's work equals the handoff at about 80 operations per message
  in C++ and 95 to 111 in Rust, about 11 to 13 µs of work per message. Below that the handoff
  decides throughput, above it the language does. Rust finishes 1.13 to 1.17 times as many
  operations as C++ at B = 1, and 1.47 to 1.50 times at B ≥ 128 on the system allocator. On
  jemalloc the ratio peaks at 1.45 (B = 128) and falls to 1.25 at B = 1024.
- **Against Method 1.** The profile put the UE operation at 0.13 µs (C++) and 0.11 µs (Rust)
  per call in the mixed workload, with overlapping ranges. The batch probe times the operation
  directly and repeatably, so prefer it for the operation's cost.

**Limits.**

- Not certified by the script's own rule: 8 of 44 cells varied by 5 to 10% across repeats. The
  fitted intervals are narrow.
- Senders were uneven. The busiest sender in a run finished a median 29% more batches than the
  slowest (worst 71%), most likely because the scheduler placed each sender and worker pair
  within or across the processor's core groups, which cores 2-17 span three of. Both languages
  meet it at random.
- jemalloc ran with the allocator's defaults (see above). Rust is 11% slower per operation on
  jemalloc than on the system allocator here, which a pinned rerun should check.
- t includes building the batch on the sender (one SplitMix64 draw and one 64-bit modulo per
  id), the same code in both languages.
- A further host, signalling operations only, one sender per shard.

Files: `bench/results-probes-20261019-killdeer/batch_probes-20261019-133636.jsonl`, `.summary.json`
and `.console.txt`.

### 4.16 The same handoff in both languages (matched design, 19 October 2026)

**Question.** Past saturation the builds differ in how their standard libraries hand work
between threads (§4.13, §4.14). If both languages hand work over the same way, is a lead left,
and how large is it?

**Method.** `bench/matched_probes.sh`, same host as §4.13. One probe program per language,
`cpp/bench/matched.cpp` and `rust/examples/matched.rs`, built only with
`-DUECM_MATCHED_PROBE=ON` and `--features matched-probe`. Neither option changes the library.
Each program runs a small service around the real `ShardCore`: one worker thread per shard, a
fixed 1024-slot ring per shard behind a three-state futex mutex, and one reply slot per sender.
Every wait and wake is the futex system call with the same arguments in both languages, and a
thread is woken only after it has marked itself asleep. The request is one 136-byte tagged
struct in both. With `--design stock` the same program sends the same requests through the
reported `Service` instead, so within one binary the two designs differ only in the handoff.
Seven senders and seven shards, the mixed workload over 5000 UEs per sender, sending back to
back (the overload state), 1 s warm-up and a 3 s window. Every binary first passed a self-test:
one sender, 20,000 operations through each design, with identical results by operation kind in
both designs and both languages. Eight arms (two languages, two designs, two allocators) ran
interleaved with the starting arm rotated, 20 repeats, the campaign's jemalloc settings, pin
2-17. The Rust `unsafe` for the futex call and the ring stays in the example. `rust/src`, which
`bench/adoption_cost.py` counts, has none.

**Result.** Medians of 20 repeats. The script's checks passed: no failed operation, and no arm
varied by more than 5% across repeats. µs per call is seven senders over the throughput. CPU is
per finished operation, read at the window's two ends.

| Arm | kops/s [95% CI] | µs per call | user µs | kernel µs |
| --- | --- | --- | --- | --- |
| C++ through its `Service`, system heap | 452.3 [450.8, 453.0] | 15.48 | 5.01 | 8.51 |
| Rust through its `Service`, system heap | 493.2 [490.3, 494.9] | 14.19 | 5.50 | 7.43 |
| C++ matched design, system heap | 550.4 [549.0, 551.2] | 12.72 | 3.37 | 7.60 |
| Rust matched design, system heap | 556.7 [554.8, 557.6] | 12.57 | 3.25 | 7.55 |
| C++ through its `Service`, jemalloc | 449.4 [442.1, 452.2] | 15.58 | 5.05 | 8.52 |
| Rust through its `Service`, jemalloc | 504.1 [500.2, 505.9] | 13.89 | 5.18 | 7.43 |
| C++ matched design, jemalloc | 546.4 [539.4, 552.2] | 12.81 | 3.37 | 7.66 |
| Rust matched design, jemalloc | 554.6 [550.1, 557.4] | 12.62 | 3.27 | 7.60 |

- **Through the standard libraries Rust leads by 9.0%** [8.5, 9.7] on the system allocator and
  by 11.8% [10.9, 14.3] on jemalloc, in 20 of 20 repeats both times (exact paired *p* =
  1.9×10⁻⁶, the floor for 20 pairs).
- **With the same handoff Rust leads by 1.3%** [0.8, 1.6] on the system allocator, in 17 of 20
  (*p* = 5.2×10⁻⁵), and by 1.4% [0.1, 2.3] on jemalloc, in 16 of 20, where the test cannot
  tell (*p* = 0.17). The lead is smaller with the matched design in 20 of 20 repeats on the
  system allocator and 19 of 20 on jemalloc (*p* = 1.9×10⁻⁶ and 3.8×10⁻⁶), so the handoff
  carries 85 to 88% of it in this harness.
- **What remains fits the language's own code.** Kernel time per operation is equal, 7.55
  against 7.60 µs, and so are the kernel calls below. Rust uses 0.12 µs less user CPU per
  operation (3.25 against 3.37), about 1% of a 12.6 µs call. Inside a loaded worker one
  signalling operation costs 107 ns in Rust and 167 ns in C++ (§4.15).
- **Both standard handoffs cost throughput, in different places.** The matched design lifts
  C++ by 21.7% and 22.4% and Rust by 12.7% and 9.8%. The C++ design costs more kernel time
  (8.51 against 7.43 µs per operation), the wakes that find nobody. The Rust design costs more
  user time (5.50 against 5.01 µs), the channel code §4.14 located.
- **The allocator hardly matters once the handoff is matched.** jemalloc is 0.8% slower for
  C++ (7 of 20 faster, *p* = 0.012) and 0.7% for Rust (*p* = 0.048).

**Kernel calls per request** (`bench/futex_counts.sh --matched`, bpftrace on the host,
separate session, system heap, 3 repeats, difference of 6 s and 3 s windows, medians).

| Per request | C++ `Service` | Rust `Service` | C++ matched | Rust matched |
| --- | --- | --- | --- | --- |
| futex waits that slept | 1.48 | 1.44 | 1.43 | 1.42 |
| waits that returned at once | 0.09 | 0.13 | 0.14 | 0.15 |
| wakes that woke a thread | 1.48 | 1.44 | 1.43 | 1.42 |
| wakes that found nobody | 1.63 | 0.19 | 0.19 | 0.19 |
| all system calls | 4.67 | 3.21 | 3.19 | 3.19 |

The probe running each `Service` reproduces §4.13 (1.63 and 0.22 empty wakes there). The
matched design makes the same calls in both languages. Its 0.19 empty wakes are the race any
sleep flag has: the waker sees the flag after the sleeper set it but before the sleeper
entered the kernel. The waits that return at once are the other half of the same race.

**Limits.**

- A further host, not the campaign host.
- The probe's harness has no histogram, no send schedule and no preload, so its figures are not
  the campaign benchmark's. On the same host and day the benchmark's deferred-fill mode put the
  stock lead at +1.5% (system) and +8.3% (jemalloc) (§4.13). Part of that gap is the mode
  charging Rust for its own fill (§4.17). The rest was not traced.
- The matched design is written for this probe. It is not a proposal for the service, and in
  Rust it needs `unsafe`.
- The ring copies a 136-byte request in and out in both languages (checked with each
  compiler). The stock services move their own types instead: a 160-byte C++ struct and a
  96-byte Rust enum.
- Senders reach shards through the pinned hash, so a request can queue behind another
  sender's, as in the service. Each seed gives every arm the same sequence of operations.

Files: `bench/results-probes-20261019-killdeer/matched_probes-20261019-145238.jsonl`,
`.summary.json`, `.console.txt`, `env-matched-20261019-145238.txt`, and
`futex_counts-20261019-150347.jsonl`, `.summary.txt`, `.console.txt`.

### 4.17 The deferred fill sits inside Rust's measured window (19 October 2026)

**What the code does.** With `--correction-when after`, `cpp/bench/bench.cpp` stamps the end of
a producer's window (`meas_end[p]`) and then runs `correct_after`. `rust/examples/bench.rs` runs
`correct_after` first and then stamps the end (`meas_hi_ns`). Throughput divides by that window,
so in this mode the window includes the fill in Rust and excludes it in C++. The default mode
runs no deferred fill. Every reported campaign used it, including all 1120 runs of
`campaign-20260924-083351`, so the reported campaign is not affected.

**Test.** In deferred mode the cap bounds only the deferred fill, so cap 0 against cap 10000
changes nothing else, and both languages return at once at cap 0. Same host as §4.13, 784
kops/s offered, mixed, 7/7, system heap, 10 interleaved repeats, the reported builds.

| | Cap 10000, as the probes ran | Cap 0, no fill | Change |
| --- | --- | --- | --- |
| C++ kops/s | 429.8 | 426.2 | −1.0%, faster in 3 of 10, *p* = 0.68 |
| Rust kops/s | 441.1 | 451.8 | +2.4%, faster in 9 of 10, *p* = 0.014 |
| Rust over C++ | +2.4%, 10 of 10 | +5.9%, 10 of 10 | |

With the fill, Rust's window is 127 ms longer and C++'s is not (−54 ms, noise).

**What it touches.** On the deferred clock every comparison across languages understates Rust,
by about 2.4 points of throughput at the top load on this host. Comparisons within one
language are unaffected, because both arms carry the same fill. Loads where no sample exceeds
the send interval run no fill and are unaffected, so the effect grows from the knee upwards.

- §4.6 and §4.7, P3 fill-after 1.00× (*p* = 0.54).
- §4.9, the deferred-clock grid: plateau 447 against 461 kops/s, and the system allocator's
  "cannot tell" (*p* = 0.070).
- §4.12 and §4.13, Rust with the C++ queue against C++. On killdeer that arm was 2.3% behind
  C++ (421.7 against 431.8), and adding back the 2.4% puts it about level. The swap within
  Rust (−4.7%, 9 of 10) stands.
- §4.13, the reply probe's lead past saturation (+1.5% and +8.3%).
- `figures/gen_probes.tex`, read from `fair-after-20260924-100100.jsonl`:
  `\ProbeAfterThrRatioSystem` 0.95, `\ProbeAfterThrRatioJemalloc` 0.92, `\ProbeAfterThrRatio`
  0.93, and the `\ProbeAfterThr*` throughputs behind them. `\ProbeAfterCpuPerOpRatio` (1.03,
  C++ higher) divides whole-process CPU, which includes each language's fill, by the window's
  throughput, so Rust's figure is raised twice. The `\SgQueue*` set reads a deferred-mode log
  too.

Every direction the thesis states from these still holds, because the error runs against Rust.
The sizes are conservative.

**Fix, applied 19 October 2026 at the author's request.** `bench.rs` now stamps the end of the
window before the `correct_after` block, as `bench.cpp` orders it. The ordering had been in place
since the deferred mode was committed (`f6bf8d0`, 21 September), so every deferred-mode log
before this date carries the bias, including `fair-after-20260924-100100.jsonl`. Default-mode
behaviour is unchanged. The same test, rerun with the fixed build in a second session on the
same host and boot:

| kops/s, medians of 10 | Before the fix | After the fix |
| --- | --- | --- |
| C++, cap 10000 | 429.8 | 428.7 |
| C++, cap 0 | 426.2 | 433.6 |
| Rust, cap 10000 | 441.1 | 458.3 |
| Rust, cap 0 | 451.8 | 453.2 |
| Rust over C++, cap 10000 | +2.4% | +7.0%, 10 of 10 |
| Rust over C++, cap 0 | +5.9% | +4.0%, 9 of 10 |

After the fix the fill no longer lowers Rust (cap 0 against cap 10000 −2.4%, faster in 3 of
10, *p* = 0.096, the opposite sign to the bug, and two low cap-0 repeats carry it). Across the
sessions Rust at cap 10000 rose 3.9%, while the three arms the fix cannot touch moved by −0.3%
to +1.7%. The two sessions put Rust's lead at 784 kops/s offered at 4 to 7%. The `\ProbeAfter*`
sizes need the deferred-fill sweep rerun on the campaign host before they can be corrected.

Files: `bench/results-probes-20261019-killdeer/fillwindow-20261019-151109.jsonl` (before) and
`fillwindow-20261019-152452.jsonl` (after), each with its `.console.txt`, and the script
`fillwindow.sh`.

### 4.18 How long each part of a call takes, and a second host (20 October 2026)

**Host.** Cherry Servers Chicago `select-bream`, AMD EPYC 7443P, 64 GB, Ubuntu 26.04.1, kernel
7.0.0-34-generic, `virtualisation: none`, root UUID `28ee80da-…`. SMT and boost off at runtime,
performance governor, `nohz_full=2-17 rcu_nocbs=2-17` (`/etc/default/grub.d/99z-thesis-nohz.cfg`,
then reboot), no `isolcpus`, THP `madvise`. Docker 29.1.3 with the campaign image copied from the
laptop (layer list identical, `g++` 15.2.1, `rustc` 1.97.1, jemalloc 5.2.1). Pin 2-17. **A second
further host, not the campaign host.** Session script: `run_bream.sh`, kept with the results.

**Method.** `bench/matched_probes.sh --stages` runs the same-handoff probe with four stamps per
call on one monotonic clock: just before the sender hands the request over, when the worker starts
it, when the worker finishes it, and when the sender holds the result. The two worker stamps are
the reported services' own `started` (`Config::stamp_start`) and `done` (`stamp_completion`), and
the probe's worker takes the same two stamps, so every arm pays the same two extra clock reads.
The parts are the queue (hand-over to start), the worker (start to finish), the reply (finish to
result), and the sender (result to the next hand-over). They add up to the time per call, which
the script checks run by run. Four arms on the system allocator, 20 interleaved repeats. The
untimed comparison of §4.16 then ran again on the same host, 20 repeats.

**Result.** µs per call, medians over repeats of each run's mean. Both runs passed their checks.

| Part | C++ own library | Rust own library | C++ same handoff | Rust same handoff |
| --- | --- | --- | --- | --- |
| queue | 7.67 | 6.55 | 6.31 | 6.41 |
| worker | 0.21 | 0.16 | 0.20 | 0.16 |
| reply | 7.69 | 7.55 | 6.25 | 6.26 |
| sender | 0.08 | 0.07 | 0.18 | 0.15 |
| whole call | 15.65 | 14.32 | 12.94 | 12.98 |

- **A call is two handoffs.** Queue and reply are 97 to 98% of every call, roughly half each.
  The operation is at most 1.5%.
- **Through the standard libraries the gap is in the queue.** Rust's call is 1.39 µs shorter
  (paired, 20 of 20). The queue accounts for 1.14 µs of it, the reply for 0.15 µs, the
  operation for 0.05 µs.
- **With the same handoff the handoff parts match.** Queue and reply differ by at most 0.10 µs.
  Rust's operation is 0.04 µs shorter in 20 of 20 pairs, and its queue code 0.10 µs longer
  (*p* = 2.8×10⁻³). The whole timed call is level (−0.002 µs, *p* = 0.56).
- **The untimed repeat.** Through the standard libraries Rust leads by 7.8% (20 of 20) and with
  the same handoff by 0.6% (16 of 20, *p* = 7.0×10⁻³) on the system allocator, 12.3% and 0.7% on
  jemalloc. So killdeer's 9.0% and 1.3% replicate in direction and roughly in size. The stamps
  move the same-handoff comparison by about the size of what remains, which is why the timed run
  is used for the parts and the untimed runs for whole calls.

**Limits.** A further host. Means hide the spread within a run. The queue part includes the
request's own copy and the lock, and the reply part includes waking the sender, so neither is the
kernel alone. `sender` is larger in the same-handoff arms (0.15 to 0.18 µs against 0.07 to 0.08)
for reasons not traced, in both languages alike.

Files: `bench/results-probes-20261020-bream/` (`matched_stages-*`, `matched_probes-*`, the env
capture, `run_bream.sh`, checksums). `bench/handoff_facts.py` writes `\Stage*` and
`\HandoffRep*` from them, and `diagrams/32_same_handoff` prints the parts in its boxes and bars.

---

## 5. Ranked account

From what can currently be defended.

| Rank | Claim | Status | Why |
| --- | --- | --- | --- |
| 1 | The cliff is real, allocator-independent, and reproduced on three hosts. Rust tracks further. The floor favours C++. CPU per completed op favours C++. | **Measured.** Canonical. | Campaign, `tab:overload`, `tab:overloadtest`. |
| 2 | Shard-queue design, shard-queue allocation, and the two primitives in isolation are not the whole explanation. | **Ruled out** as the whole story. WSL2 for the substitutions, reported `tab:contention` for the isolation. | Spec §12, §`sec:contention`. |
| 3 | The reversal is specific to open-loop collapse (producers late, capped CO backfill on). Closed-loop max favours Rust slightly (0.94×). | **Certified on 7443P.** WSL2 had the same sign, uncertified. | §4.5, §4.6. |
| 4 | With the campaign cap, the open-loop floor favours C++ at 1.67×. With the cap at 0, both arms recover to closed loop and the language split reverses to 0.95×. Start-origin (no fill) is 0.95× with call p50 15 µs either side. Fill after the timed loop is 1.00× (*p* = 0.54, cannot tell). Isolated, the Rust crate is ~1.6× slower than `hdr.hpp` for a full 10 000-sample backfill. | **Certified in-service on 7443P.** Isolated timing remains WSL2. The fill-after ratio understates Rust (§4.17). | §4.2, §4.6 P1, §4.7 P3. RQ1's overload half is this instrument. |
| 4b | On a clock that never fills, the cliff itself does not occur. Across all 14 reported loads both languages track to 448 kops/s offered and then plateau at 441 (C++) and 470 (Rust) rather than falling to 147 and 84. Rust's p99 is lower at every load. | **Certified on 7443P**, 1120 runs, worst cell spread 2.5%. | §4.8. Extends rank 4 from one operating point to the grid. |
| 4c | Same grid with the campaign origin and cap, fill applied after the timed loop: plateau 447 (C++) and 461 (Rust) at 784 kops/s offered, 0.97×. System allocator cannot tell (*p* = 0.070). Jemalloc Rust ahead. | **Certified on 7443P**, 1120 runs, worst cell spread 2.5%. Understates Rust past the knee, because Rust's window includes its fill (§4.17). | §4.9. The correction can stay. Charging it in the timed loop is the cliff. |
| 5 | Per-request unbounded `channel()` allocates about 2.3 KiB for the real reply type, including a 1,744-byte block the worker allocates and the sender frees, against about 220 bytes for `std::promise`. Swapping to `sync_channel(1)` (about 810 bytes, nothing across threads) does not move the open-loop floor or the deferred-clock lead past saturation. | **Allocations measured** (deterministic tracker). **Swaps certified on 7443P.** | §4.3 (superseded figure), §4.6 P2, §4.13. |
| 6 | C++ 160-byte tagged `Request` versus Rust 96-byte enum. | **Weak.** Wrong sign. | Present in closed loop, where Rust is slightly faster. Not the floor. |
| 7 | Bounds checks, `unsafe`, jemalloc, async runtime. | **Not the cause.** | Campaign plus design. |
| 8 | With the fill deferred, the smaller Rust lead sits in kernel time at the handoff and is carried by the shard queue's synchronisation (Rust's `sync_channel` against one mutex and two condition variables). Not the map, not the queue's storage. | **Located on the campaign host, carried on two further 7443Ps.** Swap not repeated on the campaign host. | §4.12, §4.13, spec §12 2026-09-30 and 2026-10-19. |
| 9 | The C++ queue design makes about 1.4 extra futex wake calls per request that wake nobody. Sleeps and real wakes are equal in every build. Rust running the same design makes the same calls, because its `Condvar::notify_one` always enters the kernel. | **Counted on a further 7443P** (bpftrace, separate session). | §4.13. |
| 10 | With several requests in flight, the allocator split comes from Rust's standard reply channel. The one-slot reply lifts Rust on the system allocator from 2443 to 3171 kops/s (10 of 10) and puts it ahead of C++ on both allocators. | **Measured on a further 7443P**, 10 repeats per workload. | §4.13. |
| 11 | In overload the language's own work on the UE record is about 1% of a call: 0.13 µs in C++, 0.11 µs in Rust, overlapping ranges. The builds differ in the standard-library handoff: Rust spends 1.25 µs more in user-space queue and reply code and 1.40 µs less in the kernel. | **Profiled on a further 7443P** (cycle sampling, 3 repeats). | §4.14 (Method 1). |
| 12 | Timed directly in a loaded worker, one signalling operation costs 167 ns in C++ and 107 ns in Rust (system allocator, 1.57 times [1.53, 1.62]; jemalloc 1.42 times). The operation outweighs the handoff only from about 80 (C++) and 111 (Rust) operations per message. | **Measured on a further 7443P**, 5 repeats, not certified by the script's 5% rule (8 of 44 cells at 5 to 10%). | §4.15 (Method 2). |
| 13 | With the handoff written the same way in both languages (one ring, one futex mutex, one reply slot, the same futex calls), Rust leads past saturation by 1.3% on the system allocator (17 of 20) and 1.4% on jemalloc (cannot tell, *p* = 0.17), against 9.0% and 11.8% through the standard libraries in the same harness. Kernel calls (3.19 per request) and kernel time are equal. What remains fits Rust's 0.12 µs less user CPU per operation. | **Certified on a further 7443P**, 20 repeats, the script's 5% rule passed. Kernel calls by bpftrace, 3 repeats. | §4.16. |
| 14 | On the deferred-fill clock, Rust's measured window includes its own fill and C++'s does not (`bench.rs` stamps the end after `correct_after`, `bench.cpp` before). Without the fill Rust gains 2.4% (9 of 10) and C++ nothing, so Rust's lead at 784 kops/s offered is +5.9%, not +2.4%. Directions stand. Sizes on that clock understate Rust. The reported campaign (default mode) is unaffected. | **Measured on a further 7443P**, 10 repeats. Code read on both sides. **Fixed in `bench.rs` on 19 October 2026** and verified on the same host. Deferred-mode logs before that date keep the bias. | §4.17. |
| 15 | Past saturation a call is two handoffs: the queue and the reply take 97 to 98% of it, roughly half each, and the operation at most 1.5%. Through the standard libraries 1.14 µs of Rust's 1.39 µs shorter call is in the queue. With the same handoff the two handoff parts match within 0.10 µs. The same-handoff lead replicated at 0.6% (16 of 20) on a second host. | **Measured on a second further 7443P**, 20 repeats each, both runs passed their checks. | §4.18. |

A consistent picture:

- Below the knee the producer sleeps. Workers own the cores. HDR backfill is ~10 ns.
  The languages agree at the median. Rust’s core is faster, so Rust tracks further.
- At the first missed interval the producer stops sleeping, the 10 000-sample
  backfill switches on, and seven extra threads stay in the runnable set between
  park and the next send. Throughput falls *below* the tracking rate. That is
  the cliff.
- On this 7443P, turning the backfill off (P1 cap 0) recovers throughput to
  the closed-loop band and removes the C++ floor advantage. Swapping the
  oneshot (P2) does not. The 14-load sweep on that clock (§4.8) shows the
  same thing as a curve: the fall below the tracking rate never appears, and
  the p99 favours Rust at every load. The published `\OverloadThrRatio` is
  the campaign instrument, not the languages' maximum rate.

---

## 6. What ran, and what remains

P0, P1, P2, and P3 exist as `bench/overload_probes.sh`. Compared pair
untouched. WSL2 numbers stay uncertified. Two Cherry Chicago 7443P
rentals are certified: P0--P2 on 19 September (`exciting-moose`), P3 on
20 September (`calm-husky`). Same SKU, not the Nokia/UH host.

| Probe | WSL2 (uncertified) | 7443P Chicago (certified) |
| --- | --- | --- |
| P0 closed-loop ratio | ~1 (range overlap) | 0.94× (Rust ahead) |
| P1 default-cap ratio | C++ ahead (ranges disjoint) | 1.67×, *p* = 1.95×10⁻³ |
| P1 cap-0 ratio | ~1 (overlap, both recover) | 0.95×, both at closed-loop band |
| P2 oneshot ratio | No move | No move (83 vs 83 kops/s) |
| P3 start-origin | 0.97×, Rust p50 59 µs vs 63 µs (4 repeats) | 0.95×, p50 15.2 vs 15.7 µs |
| P3 fill-after | 0.99× (4 repeats) | 1.00×, *p* = 0.54. Cannot tell |
| 14-load start-origin | not run | certified, §4.8. Rust p99 lower at all 14 |
| 14-load fill-after | not run | certified, §4.9. Plateau 447 vs 461 kops/s |

Both 14-load clocks are in. Clock B corroborates Clock A: the campaign
origin and cap 10 000 can stay if the fill runs after the timed loop.
Do not copy any figure from either into `gen_macros.tex`. The rented
box is idle. Terminate it when you are done.

D1 does not explain a gap that is gone at cap 0. It can still run as a
negative for the forced-idiom log. It is no longer the live candidate for
the floor.

The three 2026-08 queue and map substitutions were never re-run on an
EPYC with the fill inside the window. They stay WSL2 for the recorder
floor, and that does not reopen them as its mechanism. On 30 September
2026 all three ran on a further 7443P with the fill after the window,
which is a different question: what carries the smaller Rust lead. The
mutex-queue swap removed it (§4.12).

Do **not** start from `std::sync::oneshot` itself. It is unstable and would
pull a nightly story into a freeze that currently has none.

**19 October 2026 (`composed-killdeer`).** The campaign-host follow-ups ran on a third
further host instead (§4.13), with three probes added to the driver: the one-slot reply in
flight, the same swap past saturation, and kernel calls per request. Method 1, the cost of
each part of a call, ran on the same host (§4.14), and so did Method 2, the batch probe
(§4.15). Method 2 is probe only, behind `--features batch-probe` and `-DUECM_BATCH_PROBE=ON`,
never a reported arm. What remains for it: a rerun with the campaign's jemalloc settings and
enough stability to pass the script's own check, and if it is to be quoted beside the campaign,
a run on the campaign host.

Later the same day, on the same host and boot, the matched-design probe ran (§4.16), behind
`-DUECM_MATCHED_PROBE=ON` and `--features matched-probe`, and so did its kernel-call count. It
found the deferred-fill window asymmetry, tested in §4.17. The one-line fix in `bench.rs` is
applied and verified. What remains: if the thesis keeps the `\ProbeAfter*` sizes, the
deferred-fill sweep rerun on the campaign host with the fixed build.

---

## 7. What must not happen

- Do not add `isolcpus`. It collapses the pin onto one core.
- Do not treat a WSL2 kops/s as a `\OverloadThr*` value.
- Do not treat the 7443P probe kops/s as a `\OverloadThr*` value either.
  The campaign row stays. The probe licenses the cause, not a replacement
  floor.
- Do not let `fair-start-*.jsonl` become a `campaign-*.jsonl`. `refresh_thesis.sh`
  would then quote it.
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

## 8. Thesis sites that can move

The 7443P run is in the thesis as a cause sentence. Campaign macros were not
replaced. Sites that now carry that sentence:

- `sec:overload` and `sec:contention` in both `Ha_Vien_Mastersthesis_2026.tex`
  and `Thesis_v5.tex`
- `tab:threats` construct row
- `tab:findings` RQ1 evidence cell
- Chapter 8 / conclusion overload sentence
- `spec/SPECIFICATION.md` §12 (updated 19 September 2026)
- The inverted ``extra work on the C++ handoff path'' sentence in the RQ1
  discussion
- `docs/TODO.md` D1: no longer the live floor candidate

`bench/refresh_thesis.sh` is not required unless a compared-pair number moves.
These probes must not move the compared pair.

**30 September 2026.** `Thesis_v5.tex` now carries the §4.12 cause at seven
sites: the cause paragraph closing `sec:overload`, the resource paragraph,
§6.1, §6.2, the threats paragraph, the conclusion, and future work. The full
draft was not changed, by the author's choice. Its source file has been empty
since 25 September 2026, and its last built PDF (24 September) still says the
smaller lead is not explained.

**19 October 2026.** §4.17 touches the sites that quote the deferred-fill clock
across languages. In `Thesis_v5.tex`: the throughput ratios and CPU per call at
the top load (lines 1513 to 1523), "Rust with that lock lost the lead" (1549),
and `\ProbeAfterCpuPerOpRatio` at 1686, 2012, 2204 and 2440. In
`Ha_Vien_Mastersthesis_2026.tex` they are lines 1532 to 1542, 1568, 1706, 2032,
2225 and 2467. Every direction they state holds. The sizes understate Rust.
None was edited.

**20 October 2026.** `Thesis_v5.tex` now carries the §4.17 caveat after the
method paragraph of `sec:overload`, sized by `\FillWindowRustGain`, and the
limitations item states it too. §4.16 is in `sec:overload` as one probe
paragraph, a results paragraph and a kernel-call paragraph, with
figure `fig:samehandoff` (`diagrams/32_same_handoff`). Its numbers come from
`figures/gen_handoff.tex`, which `bench/handoff_facts.py` writes. The
discussion's RQ1 paragraph and the summary of findings quote
`\HandoffSameLeadSystem`. The sentences that put the queue swap and the
in-flight runs on the reported campaign host now say a further host, because
neither `results-probes-campaign-jaybird/` nor `results-pipeline-campaign-jaybird/`
exists. If those campaign-host runs land, `probe_facts.py` and
`pipeline_facts.py` switch to them, and the same sentences must switch back.

Later on 20 October `sec:overload` gained the per-part paragraph and `tab:callparts` (§4.18), the
second-host repeat sentence, and a figure whose boxes and bars give each part's time. The two
discussion sentences now quote `\HandoffSameLeadLo` to `\HandoffSameLeadHi` across the two hosts.

The same afternoon `sec:overload` was rebuilt answer first, at the author's request, from 20
paragraphs to 9. It opens with the three findings, then four headed parts: what the sweep shows
(the timer caveat now follows the numbers it qualifies), where the lead comes from (the probes
in one table, `tab:probes`), where a call's time goes (`fig:samehandoff` and `tab:callparts` in
one float, so they stay together), and delay with several requests in flight. The further hosts
are named A to D. Appendix B (`appendix:probes`) holds the host list (`tab:probehosts`), the
same-handoff design, the jemalloc and repeat counts, thread switches, the timer test and the
stamping method. No result was dropped.

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
- 18 September 2026 WSL2: `bench/results/overload_probes-20260918-134345.jsonl`
  (uncertified).
- 19 September 2026: Cherry Chicago AMD EPYC 7443P,
  `bench/results/overload_probes-20260919-153013.jsonl` (certified, 10
  repeats, 784 kops/s offered, `--pin 2-17`).
