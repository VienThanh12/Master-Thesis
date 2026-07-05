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
construction, and advances that model optimistically — so the *sequence of op kinds is
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
  `ops = rate * duration`, so wall time ≈ `duration` until the service saturates —
  past saturation the loop can't keep up and both wall time and tail latency grow
  (the overload signal). Very high post-saturation rates therefore take longer to run.
- CSV columns: `lang,alloc,workload,shards,producers,rate_per_prod,offered_ops_s,`
  `achieved_ops_s,errors,p50_ns,p90_ns,p99_ns,p999_ns,max_ns,mean_ns,wall_s`.

Plot it (optional; needs matplotlib):
```bash
python3 bench/plot_sweep.py            # newest sweep CSV -> PNG (p99 by default)
python3 bench/plot_sweep.py results/sweep-XXXX.csv --metric p999_ns
```

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
- For thesis-grade results: pin CPU frequency/governor, isolate cores, repeat runs,
  and report medians across repetitions (Phase 6). `run.sh` here is for quick
  comparative smoke runs, not final measurement.
