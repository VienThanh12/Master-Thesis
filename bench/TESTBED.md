# Testbed protocol and reproducibility

This document defines the measurement protocol for the RQ1/RQ3 load sweep so that
the latency and resource numbers reported in the thesis are reproducible and free
of avoidable noise. It is the concrete realisation of the "Testbed configuration"
section of the thesis.

The rule of thumb: **the machine, not the code, is usually the source of tail-latency
noise.** Every item below removes a source of variance that would otherwise show up
in p99/p99.9.

## 1. Hardware and OS

- A dedicated Linux host (bare metal or a VM with pinned vCPUs), *not* a laptop on
  battery and *not* a shared CI runner.
- Record: CPU model, core/thread count, cache sizes, total RAM, kernel version,
  distro, compiler versions. `capture_env.sh` (below) collects these into the
  results directory.

## 2. CPU and frequency hygiene (bare-metal Linux)

**Quick start:** `bench/setup_testbed.sh` does everything in this section
automatically, it installs the toolchain, applies the hygiene below, and prints a
GREEN/RED readiness check:

```bash
bench/setup_testbed.sh          # install toolchain + apply hygiene + verify
bench/setup_testbed.sh --check  # verify readiness only (no changes)
```

The manual steps it runs are documented here for reference. Run these once per
session (they require `sudo` and a real Linux host; they are **not** available
under WSL2, see §5):

```bash
# 1. Pin the frequency governor to 'performance' (no on-demand scaling).
for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
  echo performance | sudo tee "$f" >/dev/null
done

# 2. Disable turbo/boost (removes frequency jitter between runs).
#    Intel p-state:
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo >/dev/null
#    (generic cpufreq boost: `echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost`)

# 3. Disable SMT / hyper-threading if measuring per-core behaviour.
echo off | sudo tee /sys/devices/system/cpu/smt/control >/dev/null
```

Isolate the cores the benchmark uses from the scheduler and IRQs for the cleanest
tails (optional, kernel cmdline): `isolcpus=2-9 nohz_full=2-9 rcu_nocbs=2-9`.

## 3. Running the benchmark pinned

The turnkey campaign driver applies all of the guidelines below automatically,
prefer it over hand-running the sweep:

```bash
# 8 shards + 8 producers on isolated cores 2..17, 20 repeats, full rate sweep.
taskset -c 2-17 bench/campaign.sh --repeats 20 --pin 2-17 \
    --workload mixed --producers 8 --active-ues 5000 --duration 3 --warmup-s 1 \
    --rates "1000 2000 4000 6000 8000 10000 12000 16000"
```

`campaign.sh` captures the environment (`capture_env.sh`), builds all variants,
runs the sweep with repeats and interleaving, then aggregates (bootstrap median +
95 % CI) and plots, see `bench/README.md`. With `N_SHARDS + producers` threads,
reserve at least that many cores in `--pin`.

Guidelines (all handled by `campaign.sh`):

- **Warm-up:** discard the first fraction of operations (`--warmup-s`) so
  cache-cold and allocator-cold effects do not pollute steady state.
- **Repeats:** run each sweep point at least 10 times (`--repeats`); report the
  median and a 95 % CI across repeats, not a single run.
- **Interleave, don't batch:** the driver loops `repeat → rate → variant`, so all
  four variants for a rate run back-to-back and thermal/background drift affects
  every variant equally rather than biasing one.
- **One variant in flight:** never run two benchmark variants concurrently on the
  same host (the driver runs them serially).
- **Fix the seed:** the workload is deterministic for a given `(active_ues, seed)`;
  the seed is held constant across variants so all four see the identical op stream.

## 4. What to record per run

`bench/run_bench.sh` / `load_sweep.sh` already emit per run: language, allocator,
workload, offered rate, throughput, latency percentiles (p50/p90/p99/p99.9/max,
mean), peak RSS, and CPU%. Additionally capture the environment once per session
with `capture_env.sh` and store it alongside the CSVs.

## 5. WSL2 caveat (this development machine)

The development environment is WSL2, where the frequency governor, turbo, and SMT
controls in §2 are **not** exposed, the clocksource and scheduler are virtualised,
and background Windows activity perturbs tails. WSL2 is therefore fine for
*functional* work (parity, fault injection, FFI) and for smoke-testing the sweep
scripts, but the **headline RQ1/RQ3 numbers in the thesis must be produced on a
bare-metal Linux testbed** following §2–§4. `capture_env.sh` flags when it is
running under WSL so results are not mistaken for testbed-grade data.
