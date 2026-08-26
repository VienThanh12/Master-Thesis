# Benchmark harness (spec §3 / §10)

Latency + throughput benchmark for the UECM service, run identically for both
implementations and both allocators so language effects can be isolated from
allocator effects (RQ1, RQ3).

## Workloads

Selected with `--workload {signal,mixed}` (default `signal`). Each producer owns a
disjoint `ue_id` range, so there is no cross-thread key contention; latency is the
service round-trip time of each measured op, recorded into a per-thread HDR histogram.

### `signal` (hot-path microbenchmark)
1. **Preload** (not measured): each producer creates + sets up `preload` contexts.
2. **Measured**: each producer issues `ops` `handle_signaling` calls to random ids
   (deterministic SplitMix64 PRNG, same sequence in both languages).

### `mixed` (pinned RAN lifecycle model)
A deterministic generator (`cpp/bench/workload.hpp` and the `workload` module in
`rust/examples/bench.rs`) models the full UE lifecycle a gNB-CU-CP performs. It keeps a
lightweight per-slot **expected-state** model so every emitted op is valid by
construction, and advances that model optimistically, so the *sequence of op kinds is
identical in C++ and Rust* for the same `(active_ues, seed)`. The per-kind op counts are
therefore a cross-language parity signal (verified equal).

Per step: draw `slot = rng.next() % active_ues`; then by the slot's expected state:

| state | action (PRNG roll, `next()%100`) | next state |
|---|---|---|
| Empty | `create` (forced, no roll) | Idle |
| Idle | `setup` (forced, no roll) | Connected |
| Connected | `signal` (0–69), `add_drb` (70–79, else signal if DRBs full), `begin_reconfigure` (80–94), `release` (95–99) | unchanged / unchanged / Reconfiguring / Empty |
| Reconfiguring | `complete_reconfigure` (0–79) else `abort_reconfigure` | Connected |

**PRNG draw order (pinned):** 1 draw for the slot, plus 1 draw for the action roll only
when the slot is Connected or Reconfiguring (Empty/Idle transitions are forced). Both
languages must consume draws in exactly this order. `--active-ues N` sets the population
per producer; warmup defaults to `max(ops/10, 2*active_ues)` so slots are populated
before measurement begins.

Latency precision/range is matched: HDR histogram over `[1 ns, 3.6 s]` with 3
significant figures on both sides (C++ uses a vendored HDR port in
`cpp/bench/hdr.hpp`; Rust uses the canonical `hdrhistogram` crate).

**Coordinated omission:** pass `--rate R` (ops/sec per producer) to pace sends to a
fixed schedule and record latency from the *intended* send time with HDR
correction. Without `--rate` the loop is closed (back-to-back).

## Latency statistics, and how the two languages are kept comparable

Both harnesses report, from the merged histogram: `p25 p50 p75 p90 p99 p999 p9999`,
`max`, `mean`, and `stdev`. Three conventions are pinned so the numbers are the
same statistic on both sides rather than two close ones.

- **Quantiles are the primitive, not percentiles.** Both sides call their quantile
  function with the same literal (`0.999`, not `99.9 / 100`). Those differ by a ULP
  of double arithmetic, which is invisible until the product lands on an integer —
  and `0.999 * 168000` is exactly `167832`, with campaign sample counts being round
  numbers by construction. At that point the two languages would select a different
  sample and occasionally a different bucket.
- **`max` is bucket-aligned on both sides.** The Rust crate's `max()` returns
  `highest_equivalent(max_value)`. The C++ port used to return the exact recorded
  sample, so the two languages reported the maximum by different conventions, up to
  one bucket width apart (~0.1% at three significant figures). `HdrHistogram::max()`
  now matches the crate; `max_exact()` keeps the raw sample.
- **`stdev` uses the crate's convention.** It is computed from each occupied
  bucket's median equivalent value, weighted by count, about a mean computed the
  same way, which is what `hdrhistogram::stdev()` does. Note that the reported
  `mean` is *not* this quantity: C++ reports the exact sample mean while the crate
  reports the bucket-representative one. The difference is bounded by the 0.1%
  bucket width and is left as it is, but `stdev` is method-identical by
  construction rather than by coincidence.

**Interquartile range** is derived by the analysis as `p75 - p25` rather than
emitted, so there is a single place it is defined.

### Inter-operation jitter (`--jitter`)

RQ1 asks about jitter, which the thesis glossary defines as how much latency varies
*from one operation to the next*. That is a successive-difference quantity and a
latency histogram cannot recover it, so it is measured directly: `--jitter` records
a second HDR histogram over the absolute difference between consecutive latencies,
which is IPDV in the sense of RFC 3393. The definition is pinned identically in
both languages:

- **within one producer only**, never across producers — a difference between two
  threads' latencies is not a difference between consecutive operations;
- **measured phase only**, and the **first measured operation is skipped** because
  it has no predecessor (so `n` is `ops_total` minus the producer count);
- computed from **the same latency value that enters the main histogram**, which is
  the intended-send-time value under `--rate`;
- from **real observations only**. The synthetic samples the coordinated-omission
  correction backfills are not operations, so differencing them would invent
  variation that no operation experienced;
- floored at 1 ns, the same floor the latency path applies.

Reported as `jitter_ns: {p50, p99, p999, max, mean, stdev, n}`.

**What `--jitter` costs.** One extra histogram per producer, about 264 KiB each, so
peak RSS rises by roughly `producers × 264 KiB` — the same order as the language
RSS difference RQ3 reports. Both languages allocate exactly the same amount and
only when the flag is given, so the *comparison* is unaffected and the flag is
uniform across a campaign's four arms. Absolute peak RSS is therefore not
comparable between campaigns run with and without it; `campaign.sh --no-jitter`
reproduces the older footprint when a campaign's purpose is absolute RSS.

### Persisting the histograms (`--hist-out`)

`--hist-out <path>` appends one JSON record per run holding the full occupied
buckets of the latency histogram, and of the jitter histogram when enabled, as
sparse `[value, count]` pairs. `value` is the bucket's highest equivalent value,
which is what the Rust crate's `iter_recorded()` yields and what the C++ port's
`for_each_recorded()` was added to expose, so both languages persist onto one
language-neutral lattice instead of onto two internal bucket indices that merely
happen to agree. `--run-id` tags the record (campaign.sh passes the repeat index).

This exists because **p99.99 and jitter cannot be recovered from a finished
campaign**. Without the buckets, a testbed visit returns the same summary
percentiles it always did, on the one question the visit is for. It also makes the
far tail readable: at the campaign's representative load a single run records about
170k samples, so its p99.99 rests on ~17 observations, while 20 pooled repeats give
~3.4M samples and ~340 observations past p99.99.

Note that a histogram's `total` can exceed `ops_total` under `--rate`: the
coordinated-omission correction backfills synthetic samples. That is by design, not
a miscount of retired operations.

Sidecar files are appended per run and are large compared with the summary JSONL
(tens of KiB per run below saturation, a few hundred above it, where the correction
inflates the sample count). They compress well; gzip them after a campaign.

## Run everything

```bash
bench/run_bench.sh                       # default workload, all 4 variants
bench/run_bench.sh --shards 8 --ops 500000 --preload 20000
bench/run_bench.sh --rate 50000          # open-loop with CO correction
```

This builds C++ (system + jemalloc) and Rust (system + jemalloc), runs the same
workload through each, appends JSON lines to `bench/results/latest.jsonl`, and
prints a comparison table.

## Load sweep (latency vs offered load, RQ1/RQ3)

`load_sweep.sh` runs every variant across a range of target rates open-loop
(coordinated-omission-corrected) for a fixed duration, and writes a tidy CSV of the
latency-vs-load curve to `bench/results/sweep-<timestamp>.csv`.

```bash
bench/load_sweep.sh                               # defaults (mixed workload)
bench/load_sweep.sh --workload mixed --producers 8 --active-ues 5000 \
    --duration 3 --warmup-s 1 --rates "1000 2000 4000 6000 8000 10000 12000 16000"
```

- Rate is **per producer**; offered total = `rate * producers`. Each cell runs
  `ops = rate * duration`, so wall time ≈ `duration` until the service saturates,
  past saturation the loop can't keep up and both wall time and tail latency grow
  (the overload signal). Very high post-saturation rates therefore take longer to run.
- CSV columns: `lang,alloc,workload,shards,producers,rate_per_prod,offered_ops_s,`
  `achieved_ops_s,errors,p50_ns,p90_ns,p99_ns,p999_ns,max_ns,mean_ns,rss_peak_kb,cpu_pct,wall_s`.

**Throughput accounting.** `throughput_ops_s` is measured operations divided by the
duration of the *measured phase*, not by total wall time. Each producer stamps the
instant its warm-up ends and the instant it finishes; the measured window is the union
of those intervals, reported as `measured_wall_s`. This matters: dividing measured ops
by total wall time understates achieved throughput by exactly the warm-up fraction
(25% at the campaign defaults of `--duration 3 --warmup-s 1`), which makes every point
sit below the offered-equals-achieved line even at trivial load and misplaces the
saturation knee. Both language harnesses use the identical convention, so the bias was
symmetric, but it was still a bias. `cpu_pct` is deliberately left on the full wall
clock, since `getrusage` accounting includes the warm-up.

Every run also reports **peak RSS** and **CPU** (via `getrusage`: `ru_maxrss` peak
resident set, `ru_utime`+`ru_stime` total CPU across all threads; `cpu%` =
CPU/wall·100, so >100% means multiple busy cores). These land in the JSON
(`rss_peak_kb`, `cpu_user_s`, `cpu_sys_s`, `cpu_pct`), the sweep CSV, and the
`run_bench.sh` table, the RQ3 memory/overhead signal. The Rust bench's one `unsafe`
FFI call for `getrusage` is confined to the benchmark tool; the UECM library stays
`unsafe`-free.

Plot it (optional; needs matplotlib):
```bash
python3 bench/plot_sweep.py            # newest sweep CSV -> PNG (p99 by default)
python3 bench/plot_sweep.py results/sweep-XXXX.csv --metric p999_ns
```

## Measurement campaign (repeats + stats + figures, RQ1/RQ3)

**Provision a fresh testbed first** with `setup_testbed.sh` (installs the toolchain,
applies the CPU hygiene from `TESTBED.md`, and prints a GREEN/RED readiness check):

```bash
bench/setup_testbed.sh          # install toolchain + apply hygiene + verify
bench/setup_testbed.sh --check  # verify readiness only (no changes)
```

`load_sweep.sh` runs each point **once**; for thesis-grade numbers use
`campaign.sh`, which is the turnkey pipeline: capture the environment, build all
variants, sweep offered rate × variant with `--repeats` repetitions using the
**interleaving** discipline from `TESTBED.md` (outer loop = repeat, then rate, then
variant, so drift hits all variants equally), then aggregate and plot.

```bash
# Bare metal (recommended): pin to isolated cores, 20 repeats.
taskset -c 2-17 bench/campaign.sh --repeats 20 --pin 2-17 \
    --workload mixed --producers 8 --active-ues 5000 --duration 3 --warmup-s 1 \
    --rates "1000 2000 4000 6000 8000 10000 12000 16000"
```

Inter-operation jitter and histogram persistence are **on by default** (see above);
`--no-jitter` and `--no-hist` turn them off.

Outputs under `bench/results/`:
- `campaign-<stamp>.jsonl`: every individual run (raw).
- `campaign-<stamp>.hist.jsonl`: the full HDR buckets per run, for the pooled far
  tail (`--no-hist` to skip).
- `campaign-<stamp>.agg.csv`: one row per `(variant, offered load)` with, for each
  metric, `<metric>_median`, `<metric>_lo`, `<metric>_hi` where the CI is a **95%
  nonparametric bootstrap CI of the median** across repeats (seeded, dependency-free).
  Metrics: `p50/p90/p99/p999/max/mean` (ns), `achieved_ops_s`, `rss_peak_kb`, `cpu_pct`.
- `campaign-<stamp>.latency.tex`: a ready-to-paste `tab:latency` LaTeX table at an
  auto-selected representative load (the highest offered load still tracking the
  offer, i.e. just before saturation; override with `aggregate.py --rep-load`).

```bash
# Aggregate / plot a campaign manually (also runs automatically at the end):
python3 bench/aggregate.py results/campaign-XXXX.jsonl --out agg.csv --tex tab.tex --producers 8
python3 bench/plot_campaign.py results/campaign-XXXX.agg.csv --metric p99_ns   # median + CI band
python3 bench/plot_campaign.py results/campaign-XXXX.agg.csv --metric p999_ns
```

`aggregate.py` picks up `p25/p75/p9999/stdev`, the derived `iqr_ns`, and the jitter
metrics **only when every run in the campaign carries them**, so campaigns recorded
before these existed still aggregate exactly as they did before, and a campaign that
mixes instruments is reported rather than silently averaged.

## Pooling the far tail (`pool_hist.py`)

```bash
python3 bench/pool_hist.py results/campaign-XXXX.hist.jsonl
python3 bench/pool_hist.py results/campaign-XXXX.hist.jsonl --verify results/campaign-XXXX.jsonl
```

Two jobs. **Pooling** concatenates the per-run distributions across repeats and
takes one percentile of the result, which is what makes p99.99 readable at all.
**Verification** recomputes every run's percentiles from its persisted buckets and
checks them against the values the binary printed, so the sidecar is demonstrably a
faithful record of the histogram rather than a lossy summary of it. Both modes also
assert that every persisted value is a point on the HDR lattice implied by
`(low, high, sig)` and that both languages used the same lattice — the C++ port and
the Rust crate are independent implementations of the same bucketing, so their
agreement is checked rather than assumed.

The pooled percentile and the one `aggregate.py` reports are **different
statistics** and must not be mixed in a claim:

- `aggregate.py` takes the per-run percentile and reports the median across repeats
  with a bootstrap CI. Repeats are the unit, so run-to-run spread is visible and a
  paired test is possible.
- `pool_hist.py` takes one percentile of all samples together. Operations are the
  unit, the far tail is far better resolved, and there is **no across-repeat
  interval** — a single pooled number has no dispersion to quote.

So the pooled figure is the far-tail estimate and the per-repeat figures remain the
basis for any paired comparison.

**p99.99 and jitter are reported descriptively and are not in the Holm-tested
family.** The rule §5.5 pre-commits is that pairing cancels the interference an
interleaved block shares, not interference landing on one run of a pair, so it
rescues run-level and central statistics and not high percentiles, which are
computed from exactly the disturbed operations. p99.99 is the extreme case, and a
jitter percentile is a dispersion of those same samples. Testing them would spend
family-wise budget on comparisons that cannot resolve and make Holm harsher on the
ones that can — the same reasoning that removed achieved throughput from the family.

## Hardware counters (`counters.sh`) — testbed only

```bash
bench/counters.sh                 # hardware counters
bench/counters.sh --software      # plumbing check; needs no PMU
python3 bench/parse_perf.py --self-test
```

Wraps `perf stat` around the benchmark binaries for the two results that currently
rest on argument rather than measurement: the peak-RSS difference (significant but
unexplained) and the operation-level gap (attributed to node-based
`std::unordered_map` against Rust's open-addressed `HashMap` via the forced-idiom
log, not measured).

It measures two scopes, and the second is the important one. `e2e` is the sweep
path, which §7.5.2 shows is ~99.96% cross-thread handoff — counters there describe
the queue and the scheduler. `op` drives `ShardCore` through `latency_budget` with
no queue in the path, which is where the map claim actually lives.

**This cannot run on WSL2**: there is no hardware PMU (`/sys/bus/event_source/devices/`
exposes no `cpu`), and `perf` is usually absent too. The script detects both and
refuses rather than reporting zeros. Events the host cannot count are recorded as
`null`, never `0`, because a counter that did not run is not one that read zero.
The CSV parsing lives in `parse_perf.py` with a self-test so it is known-good before
the visit rather than debugged during it.

## Allocation profile (`alloc_profile.sh`) — testbed only

```bash
bench/alloc_profile.sh --check    # tool availability
bench/alloc_profile.sh            # matched profile of both jemalloc arms
bench/alloc_profile.sh --raw-ok   # collect dumps even without jeprof
python3 bench/parse_jeprof.py --self-test
```

Attributes the 2.1–2.5 MiB peak-RSS difference to allocation sites. §7.5.4 already
shows the difference is fixed rather than per-context — the `UeContext` layout
accounts for ~40 kB at 5000 active UEs, three orders of magnitude short of the gap —
so what is missing is *where the memory goes*.

**One tool, both languages:** jemalloc's own `prof`, run against the two jemalloc
arms that already exist, which needs the opt-in `jemalloc-prof` Cargo feature on the
Rust side. Profiling C++ with heaptrack and Rust with dhat would measure the two
sides with different instruments, different sampling, and different notions of a
call site, and the entire point is a comparison; this mirrors the choice already
made for the complexity proxies, where one tool measures both languages. If prof is
unavailable the script names the per-language fallbacks together with the caveat
that they do not form a matched pair and must not be differenced.

Prof support is detected **functionally** — run the arm's own binary with profiling
on and check a dump lands — rather than by matching jemalloc's diagnostics, since a
build without `--enable-prof` says `Invalid conf pair` while a syntax error says
`Malformed conf string`, and treating the absence of one wording as success is how a
false positive survives until the testbed. Note jemalloc's conf syntax is
colon-separated (`prof_prefix:/path`); `prof_prefix=/path` is rejected as malformed.

Profiling perturbs the allocation path, so these runs are for attribution only and
must never be quoted as latency or throughput.

## Latency-budget decomposition (what the end-to-end number is made of)

Every measured op is a full cross-thread round trip: submit to a bounded queue, block
on a one-shot completion, wake when the shard's worker has run the operation. The sweep
reports that whole path as one number, which means a bound on the paired *difference*
between the languages is a bound relative to a total the language mostly does not
control. `latency_budget.sh` splits it, in both languages, at the sweep's own shard
count and context population:

```bash
bench/latency_budget.sh                                  # sweep-matched defaults
bench/latency_budget.sh --shards 8 --active-ues 5000 --svc-iters 100000
```

It calls `ShardCore` directly (the single-threaded operation processor: no queue in the
path) and then `Service` (the same core behind the full threaded machinery), so the
difference between the two is the handoff. Both are batch means over a long loop rather
than per-call medians, deliberately: a clock read costs tens of nanoseconds, the same
order as the core operation, so per-call timestamps would measure the instrument.

Output is `bench/results/latency_budget.json`, one JSON line per language, picked up by
`plot_figures.py` into `tab_budget.tex` and the `\Budget*` macros.

**Run it on a quiet host.** Unlike the campaign it has no interleaving discipline to
fall back on, so a concurrent build or a second campaign will corrupt it.

## Thesis figures + tables (one command, RQ1/RQ2/RQ3)

`plot_figures.py` regenerates every figure and LaTeX table the thesis `\input`s /
`\includegraphics`, straight from the raw logs, into `../figures/`:

```bash
python3 bench/plot_figures.py            # newest campaign + taxonomy -> ../figures/
python3 bench/plot_figures.py --campaign results/campaign-XXXX.jsonl \
    --taxonomy ../faults/results/taxonomy.csv --load 16000
```

Produces (vector PDF, all nine embedded by `Ha_Vien_Mastersthesis_2026.tex`):
- `fig_latency_vs_load.pdf`: p99 latency vs offered load, median + bootstrap 95% CI band.
- `fig_throughput_vs_load.pdf`: achieved vs offered throughput (saturation knee).
- `fig_load_sweep.pdf`: the two above as one two-panel figure. The thesis uses this one, because it
  reads the two sweeps as a pair against a single x axis and pays one caption instead of two. The
  single-panel versions stay because `build_deck.py` places them side by side on their own slide.
- `fig_tail_percentiles.pdf`: latency by percentile at the representative load, with
  bootstrap bands, beside the between-variant spread against the within-variant interval.
  The second panel is where the host stops resolving the comparison (RQ1).
- `fig_effects.pdf`: the whole Holm-corrected family as paired effects, normalised by the
  C++ median so metrics in different units share an axis. Filled markers clear the
  correction; the high-percentile rows are shaded because the pre-committed reading rule
  does not treat their intervals as findings (RQ1, RQ3).
- `fig_budget.pdf`: the end-to-end round-trip decomposed, against what the sweep can resolve.
- `fig_overload.pdf`: past-saturation divergence. Sustained throughput, and total CPU divided
  by the work that completed, which is what separates effort from idleness (RQ1).
- `fig_resources.pdf`: peak RSS and CPU per variant, plus the allocator effect drawn against
  the language effect as paired differences (RQ3).
- `fig_taxonomy.pdf`: fault-injection outcome matrix from `taxonomy.csv` (RQ2).
- `fig_ffi_cost.pdf`: the seam's cost on one real operation. Interleaved native-vs-seam
  repeats from `../ffi/results/op_cost.jsonl`, then their paired difference with the bound on
  what the measurement could have missed (RQ4). Skipped, with a note, when the paired repeats
  are absent: the empty crossing alone does not answer RQ4.
- `tab_latency.tex`, `tab_resource.tex`, `tab_significance.tex`, `tab_budget.tex`,
  `tab_ffi.tex`: table bodies `\input` by the thesis.
- `gen_macros.tex`: every campaign number the prose quotes, defined as a LaTeX macro so
  the narrative updates with the data instead of going stale.

Every figure that shows a comparison shows its uncertainty with it. A bar chart or a line
plot without an interval cannot distinguish "the same" from "not separable here", and that
distinction is load-bearing for RQ1.

`tab_significance.tex` is blocked into statistics that pairing rescues (peak RSS, CPU,
p50) and high percentiles that it does not, because a paired interval excluding zero
means different things in the two cases. Achieved throughput is deliberately not tested:
at a below-saturation operating point it is pinned to the offered load by construction,
so the comparison cannot resolve a language effect, and including it would only make the
Holm correction harsher on the comparisons that can.

The representative load is auto-selected (highest offered rate with every variant still
below 5 ms p99) unless `--load` is given. The RQ2 taxonomy and RQ4 FFI inputs come from
`../faults/results/taxonomy.csv` (produced by `faults/run_faults.sh`) and
`../ffi/results/metrics.json` (produced by `ffi/build.sh`); override with `--taxonomy` /
`--ffi`. Rerun after the bare-metal campaign to refresh the whole thesis with testbed-grade
numbers, no manual copy-paste.

## Run one variant directly

```bash
# C++
cmake -S cpp -B cpp/build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build cpp/build --target bench
cpp/build/bench --shards 8 --producers 8 --preload 10000 --ops 200000 [--json]

# C++ with jemalloc
cmake -S cpp -B cpp/build-jemalloc -G Ninja -DCMAKE_BUILD_TYPE=Release -DUECM_USE_JEMALLOC=ON
cmake --build cpp/build-jemalloc --target bench

# Rust (system / jemalloc)
cargo build --release --manifest-path rust/Cargo.toml --example bench
cargo build --release --manifest-path rust/Cargo.toml --example bench --features jemalloc
rust/target/release/examples/bench --shards 8 --ops 200000 [--json]
```

## CLI (identical in both languages)
| flag | default | meaning |
|---|---|---|
| `--shards N` | 8 | shards / worker threads |
| `--queue-capacity N` | 1024 | per-shard bounded queue depth |
| `--producers N` | = shards | producer (client) threads |
| `--workload W` | signal | `signal` (hot path) or `mixed` (RAN lifecycle) |
| `--preload N` | 10000 | contexts per producer (signal preload) |
| `--active-ues N` | 10000 | UE population per producer (mixed) |
| `--ops N` | 200000 | measured ops per producer |
| `--warmup N` | ops/10 | unmeasured warmup ops per producer |
| `--seed S` | 42 | PRNG seed base |
| `--rate R` | 0 (closed loop) | target ops/sec/producer (enables CO correction) |
| `--jitter` | off | also record inter-operation jitter (IPDV); see above for its RSS cost |
| `--hist-out P` | off | append the full HDR buckets for this run to `P` |
| `--run-id S` | empty | opaque tag echoed into the sidecar (campaign.sh passes the repeat) |
| `--json` | off | emit one JSON summary line |

## Caveats
- These are microbenchmark numbers for a shared-nothing, blocking request/response
  design; every op is a full cross-thread round trip (queue + worker + one-shot
  completion), so absolute throughput is dominated by handoff cost, not the map.
- For thesis-grade results: follow `TESTBED.md` (pin CPU frequency/governor, isolate
  cores) and use `campaign.sh` (repeats + bootstrap median/CI + figures). `run_bench.sh`
  and a single `load_sweep.sh` pass are for quick comparative smoke runs, not final
  measurement.
