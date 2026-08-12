#!/usr/bin/env bash
# Turnkey RQ1/RQ3 measurement campaign: builds all four variants, captures the
# testbed environment, sweeps offered rate x variant with REPEATS, using the
# interleaving discipline from TESTBED.md, then aggregates (bootstrap median + 95%
# CI) and plots latency-vs-load with CI bands and emits a LaTeX latency table.
#
# Interleaving: outer loop = repeat, then rate, then variant, so all four variants
# for a given rate run back-to-back and repeats are spread over time -- thermal or
# background drift affects every variant equally rather than biasing one.
#
# Usage:
#   bench/campaign.sh                                  # defaults (10 repeats)
#   bench/campaign.sh --repeats 20 --pin 2-17 \
#       --workload mixed --producers 8 --active-ues 5000 --duration 3 --warmup-s 1 \
#       --rates "1000 2000 4000 6000 8000 10000 12000 16000"
#
# On WSL2 this still runs, but see TESTBED.md: headline numbers need bare metal.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

# Defaults
workload="mixed"
shards=8
producers=8
active_ues=5000
preload=5000
duration=3
warmup_s=1
seed=42
repeats=10
pin=""                       # taskset core list, e.g. "2-17"; empty = no pinning
rt=""                        # SCHED_FIFO priority for the benchmark, e.g. "80"; empty = default scheduling
rates="1000 2000 4000 6000 8000 10000 12000 16000"
# Wall-clock cap on each run's measured phase. A run that keeps up with its
# offered rate finishes on op count in `duration` seconds and never reaches the
# cap; one above saturation never finishes on op count at all, so without a cap
# the sweep cannot be taken past the knee. Empty = 2x duration.
max_run_s=""

while [ $# -gt 0 ]; do
  case "$1" in
    --workload)   workload="$2"; shift 2;;
    --shards)     shards="$2"; shift 2;;
    --producers)  producers="$2"; shift 2;;
    --active-ues) active_ues="$2"; shift 2;;
    --preload)    preload="$2"; shift 2;;
    --duration)   duration="$2"; shift 2;;
    --warmup-s)   warmup_s="$2"; shift 2;;
    --seed)       seed="$2"; shift 2;;
    --repeats)    repeats="$2"; shift 2;;
    --pin)        pin="$2"; shift 2;;
    --rt)         rt="$2"; shift 2;;
    --rates)      rates="$2"; shift 2;;
    --max-run-s)  max_run_s="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

if [ -z "$max_run_s" ]; then max_run_s=$(( duration * 2 )); fi

# The jemalloc arm is the allocator control, so both languages have to run the
# allocator on the same settings -- which does not happen by default. The C++
# variant links the system libjemalloc and reads MALLOC_CONF; the Rust variant
# links tikv-jemalloc, which ignores MALLOC_CONF and reads _RJEM_MALLOC_CONF.
# Left unset, the arena count follows however many CPUs the allocator sees and
# the footprint follows the host's transparent-hugepage policy: on this testbed
# that put peak RSS at 66 MiB against 11 MiB on a host with THP off, swamping
# the few MiB that separate the languages. Pinning both makes the footprint a
# property of the configuration rather than of the machine. Neither variable is
# read by glibc malloc, so the system-allocator arm is untouched.
jemalloc_conf="thp:never,narenas:16"
export MALLOC_CONF="$jemalloc_conf"
export _RJEM_MALLOC_CONF="$jemalloc_conf"

mkdir -p "$here/.bin" "$here/results"

# Optional scheduling prefixes (see TESTBED.md). Applied to the benchmark binary
# only, not to the builds or the analysis, so a real-time priority does not leak
# into a cargo invocation.
pre=()
# SCHED_FIFO removes the benchmark from ordinary timeslice preemption, which is
# what a flat multi-millisecond p99 on an otherwise idle system looks like.
# Needs CAP_SYS_NICE: either run as root or grant the account an rtprio limit.
if [ -n "$rt" ]; then
  if command -v chrt >/dev/null 2>&1; then
    pre+=(chrt -f "$rt")
    echo "== running benchmark at SCHED_FIFO priority $rt =="
  else
    echo "WARN: chrt not found; ignoring --rt $rt"
  fi
fi
if [ -n "$pin" ]; then
  if command -v taskset >/dev/null 2>&1; then
    pre+=(taskset -c "$pin")
    echo "== pinning benchmark to cores: $pin =="
  else
    echo "WARN: taskset not found; ignoring --pin $pin"
  fi
fi

echo "== capturing testbed environment =="
if [ -x "$here/capture_env.sh" ]; then "$here/capture_env.sh" >/dev/null || true; fi

echo "== building variants =="
cmake -S "$cpp" -B "$cpp/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$cpp/build" --target bench >/dev/null
cmake -S "$cpp" -B "$cpp/build-jemalloc" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DUECM_USE_JEMALLOC=ON -DUECM_BUILD_TESTS=OFF >/dev/null
cmake --build "$cpp/build-jemalloc" --target bench >/dev/null
cargo build --release --manifest-path "$rust/Cargo.toml" --example bench >/dev/null 2>&1
cp "$rust/target/release/examples/bench" "$here/.bin/rust-system"
cargo build --release --manifest-path "$rust/Cargo.toml" --example bench --features jemalloc >/dev/null 2>&1
cp "$rust/target/release/examples/bench" "$here/.bin/rust-jemalloc"

declare -A BIN=(
  ["cpp:system"]="$cpp/build/bench"
  ["cpp:jemalloc"]="$cpp/build-jemalloc/bench"
  ["rust:system"]="$here/.bin/rust-system"
  ["rust:jemalloc"]="$here/.bin/rust-jemalloc"
)
order=("cpp:system" "cpp:jemalloc" "rust:system" "rust:jemalloc")

stamp="$(date +%Y%m%d-%H%M%S)"
jsonl="$here/results/campaign-$stamp.jsonl"
: > "$jsonl"

total=$(( repeats * $(echo "$rates" | wc -w) * ${#order[@]} ))
echo "== campaign: $repeats repeats x rates[$rates] x ${#order[@]} variants = $total runs =="
n=0
for rep in $(seq 1 "$repeats"); do
  for r in $rates; do
    ops=$(( r * duration ))
    warmup=$(( r * warmup_s ))
    for variant in "${order[@]}"; do
      bin="${BIN[$variant]}"
      n=$(( n + 1 ))
      printf '\r  run %d/%d (rep %d, rate %d/prod, %s)      ' "$n" "$total" "$rep" "$r" "$variant"
      "${pre[@]}" "$bin" --workload "$workload" --shards "$shards" --producers "$producers" \
        --active-ues "$active_ues" --preload "$preload" --ops "$ops" \
        --warmup "$warmup" --seed "$seed" --rate "$r" --max-run-s "$max_run_s" --json >>"$jsonl"
    done
  done
done
printf '\n'

echo "== aggregating (bootstrap median + 95%% CI over $repeats repeats) =="
agg="$here/results/campaign-$stamp.agg.csv"
tex="$here/results/campaign-$stamp.latency.tex"
python3 "$here/aggregate.py" "$jsonl" --out "$agg" --tex "$tex" --producers "$producers"

echo "== plotting latency-vs-load (CI bands) =="
python3 "$here/plot_campaign.py" "$agg" --metric p99_ns  || true
python3 "$here/plot_campaign.py" "$agg" --metric p999_ns || true

echo
echo "raw:   $jsonl"
echo "agg:   $agg"
echo "table: $tex"
