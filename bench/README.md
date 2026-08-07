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

Outputs under `bench/results/`:
- `campaign-<stamp>.jsonl`: every individual run (raw).
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

Produces (vector PDF, embedded by `thesis.tex`):
- `fig_latency_vs_load.pdf`: p99 latency vs offered load, median + bootstrap 95% CI band.
- `fig_throughput_vs_load.pdf`: achieved vs offered throughput (saturation knee).
- `fig_tail_percentiles.pdf`: latency-by-percentile at the representative load.
- `fig_resources.pdf`: peak RSS + CPU utilisation per variant (RQ3).
- `fig_taxonomy.pdf`: fault-injection outcome matrix from `taxonomy.csv` (RQ2).
- `fig_ffi_cost.pdf`: FFI crossing vs end-to-end op cost from `../ffi/results/metrics.json` (RQ4).
- `tab_latency.tex`, `tab_resource.tex`, `tab_significance.tex`, `tab_budget.tex`,
  `tab_ffi.tex`: table bodies `\input` by the thesis.
- `gen_macros.tex`: every campaign number the prose quotes, defined as a LaTeX macro so
  the narrative updates with the data instead of going stale.

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
| `--json` | off | emit one JSON summary line |

## Caveats
- These are microbenchmark numbers for a shared-nothing, blocking request/response
  design; every op is a full cross-thread round trip (queue + worker + one-shot
  completion), so absolute throughput is dominated by handoff cost, not the map.
- For thesis-grade results: follow `TESTBED.md` (pin CPU frequency/governor, isolate
  cores) and use `campaign.sh` (repeats + bootstrap median/CI + figures). `run_bench.sh`
  and a single `load_sweep.sh` pass are for quick comparative smoke runs, not final
  measurement.
