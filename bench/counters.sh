#!/usr/bin/env bash
# Hardware performance counters for the two claims the campaign cannot explain
# from timings alone (RQ1/RQ3 supporting measurement).
#
# Two live results currently rest on argument rather than on measurement:
#
#   * peak RSS differs between the languages by 2.1-2.5 MiB, Holm-significant and
#     reproducing under both allocators, and section 7.5.4 already shows the
#     difference is fixed rather than per-context -- the UeContext layout accounts
#     for ~40 kB at 5000 active UEs, three orders of magnitude short of the gap.
#     What it is remains unexplained.
#   * the operation-level gap is attributed to std::unordered_map being node-based
#     by standard requirement while Rust's HashMap is open-addressed. That is a
#     plausibility argument from the forced-idiom log, not a measurement, and the
#     thesis says so; confirming it needs cache-miss counters.
#
# So this wraps the benchmark binaries in `perf stat` and writes the counters as
# JSON the analysis can read.
#
# It measures BOTH the sweep bench and the latency_budget binaries, and the second
# is the important one. The end-to-end operation is ~0.04% of what the sweep
# measures; the rest is the cross-thread handoff. Counters gathered over the sweep
# therefore describe the queue and the scheduler, which is not where the map claim
# lives. latency_budget drives ShardCore directly with no queue in the path, so
# counters over that loop are counters over the operation itself.
#
# Interleaved by repeat, like every other measurement here: the outer loop is the
# repeat and the languages run back to back inside it, so session drift perturbs
# both equally instead of biasing whichever ran first.
#
# WHERE THIS RUNS. Hardware counters need a real PMU. Under WSL2 there is none
# (/sys/bus/event_source/devices/ exposes no `cpu`), and `perf` is usually not
# installed either, so the hardware events are unavailable on the development
# host by construction rather than by misconfiguration. The script says so and
# exits instead of reporting zeros. `--software` runs the same plumbing on events
# that need no PMU (task-clock, page-faults, context-switches), which is enough to
# prove the wiring works before the testbed visit.
#
# Usage:
#   bench/counters.sh                       # hardware counters (testbed)
#   bench/counters.sh --software            # plumbing check, no PMU needed
#   bench/counters.sh --repeats 10 --pin 2-17
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

# Defaults match campaign.sh and latency_budget.sh so the counters describe the
# same operating point the reported numbers come from.
shards=8
producers=8
active_ues=5000
ops=200000
warmup=20000
seed=42
core_iters=2000000
svc_iters=50000
repeats=5
pin=""
software=0

while [ $# -gt 0 ]; do
  case "$1" in
    --shards)     shards="$2"; shift 2;;
    --producers)  producers="$2"; shift 2;;
    --active-ues) active_ues="$2"; shift 2;;
    --ops)        ops="$2"; shift 2;;
    --warmup)     warmup="$2"; shift 2;;
    --seed)       seed="$2"; shift 2;;
    --core-iters) core_iters="$2"; shift 2;;
    --svc-iters)  svc_iters="$2"; shift 2;;
    --repeats)    repeats="$2"; shift 2;;
    --pin)        pin="$2"; shift 2;;
    --software)   software=1; shift;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

# Same allocator settings the campaign pins, so the jemalloc arms are measured in
# the configuration the campaign reports rather than in whatever the host defaults
# to. See campaign.sh for why this matters to peak RSS.
export MALLOC_CONF="thp:never,narenas:16"
export _RJEM_MALLOC_CONF="thp:never,narenas:16"

# --- Preflight: is there anything to count? ---------------------------------- #
if ! command -v perf >/dev/null 2>&1; then
  echo "ERROR: perf not found."
  echo "  Debian/Ubuntu: sudo apt install linux-tools-common linux-tools-\$(uname -r)"
  echo "  RHEL/Rocky:    sudo dnf install perf"
  exit 1
fi

paranoid="$(cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || echo unknown)"
have_pmu=0
[ -d /sys/bus/event_source/devices/cpu ] && have_pmu=1
[ -d /sys/bus/event_source/devices/cpu_core ] && have_pmu=1   # hybrid Intel

if [ "$software" = "1" ]; then
  events="task-clock,page-faults,context-switches,cpu-migrations"
  kind="software"
else
  events="cycles,instructions,cache-references,cache-misses,LLC-load-misses"
  kind="hardware"
  if [ "$have_pmu" = "0" ]; then
    echo "ERROR: no hardware PMU is exposed on this host."
    echo "  /sys/bus/event_source/devices/ has no 'cpu' entry, which is what a"
    echo "  virtualised or WSL2 kernel looks like. Hardware counters cannot be"
    echo "  collected here at all, and a run that reported zeros would be worse"
    echo "  than no run. Collect these on the bare-metal testbed (TESTBED.md),"
    echo "  or use --software to check this script's plumbing."
    exit 1
  fi
  # perf_event_paranoid > 2 blocks even self-monitoring; > 0 blocks some events.
  if [ "$paranoid" != "unknown" ] && [ "$paranoid" -gt 2 ] 2>/dev/null; then
    echo "ERROR: perf_event_paranoid=$paranoid blocks user-space counter access."
    echo "  Lower it for the session:  sudo sysctl -w kernel.perf_event_paranoid=1"
    exit 1
  fi
fi

pre=()
if [ -n "$pin" ]; then
  if command -v taskset >/dev/null 2>&1; then
    pre+=(taskset -c "$pin")
    echo "== pinning to cores: $pin =="
  else
    echo "WARN: taskset not found; ignoring --pin $pin"
  fi
fi

mkdir -p "$here/results"
stamp="$(date +%Y%m%d-%H%M%S)"
out="$here/results/counters-$stamp.jsonl"
: > "$out"

echo "== building =="
cmake -S "$cpp" -B "$cpp/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$cpp/build" --target bench latency_budget >/dev/null
cmake -S "$cpp" -B "$cpp/build-jemalloc" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DUECM_USE_JEMALLOC=ON -DUECM_BUILD_TESTS=OFF >/dev/null
cmake --build "$cpp/build-jemalloc" --target bench >/dev/null
cargo build --release --manifest-path "$rust/Cargo.toml" --example bench >/dev/null 2>&1
mkdir -p "$here/.bin"
cp "$rust/target/release/examples/bench" "$here/.bin/rust-system"
cargo build --release --manifest-path "$rust/Cargo.toml" --example bench --features jemalloc >/dev/null 2>&1
cp "$rust/target/release/examples/bench" "$here/.bin/rust-jemalloc"
cargo build --release --manifest-path "$rust/Cargo.toml" --example latency_budget >/dev/null 2>&1

# One perf run. The CSV parsing lives in bench/parse_perf.py rather than inline
# here so it can be exercised without a PMU (`parse_perf.py --self-test`): these
# counters can only be collected on the testbed, so the parsing has to be
# known-good before that visit rather than debugged during it.
run_one() {  # run_one <scope> <lang> <alloc> <repeat> -- <cmd...>
  local scope="$1" lang="$2" alloc="$3" rep="$4"; shift 5
  local csv
  csv="$(mktemp)"
  # perf writes its counters to $csv; the workload's own stdout is discarded so the
  # JSON the benchmark prints cannot mix into the counter stream.
  "${pre[@]}" perf stat -x, -e "$events" -o "$csv" -- "$@" >/dev/null 2>&1
  python3 "$here/parse_perf.py" record "$csv" "$scope" "$lang" "$alloc" "$rep" "$kind" >> "$out"
  rm -f "$csv"
}

bench_args=(--workload mixed --shards "$shards" --producers "$producers"
            --active-ues "$active_ues" --ops "$ops" --warmup "$warmup"
            --seed "$seed" --json)
budget_args=(--shards "$shards" --active-ues "$active_ues"
             --core-iters "$core_iters" --svc-iters "$svc_iters" --json)

echo "== collecting $kind counters: $repeats interleaved repeats =="
echo "   events: $events"
for rep in $(seq 1 "$repeats"); do
  printf '\r  repeat %d/%d      ' "$rep" "$repeats"
  # Scope "op": ShardCore directly, no queue in the path. This is the scope the
  # map/allocator claims are about.
  run_one op cpp  system   "$rep" -- "$cpp/build/latency_budget" "${budget_args[@]}"
  run_one op rust system   "$rep" -- "$rust/target/release/examples/latency_budget" "${budget_args[@]}"
  # Scope "e2e": the full sweep path, dominated by the handoff. Kept because the
  # RSS difference is a property of the whole process, not of the core loop.
  run_one e2e cpp  system   "$rep" -- "$cpp/build/bench" "${bench_args[@]}"
  run_one e2e cpp  jemalloc "$rep" -- "$cpp/build-jemalloc/bench" "${bench_args[@]}"
  run_one e2e rust system   "$rep" -- "$here/.bin/rust-system" "${bench_args[@]}"
  run_one e2e rust jemalloc "$rep" -- "$here/.bin/rust-jemalloc" "${bench_args[@]}"
done
printf '\n\n'

python3 "$here/parse_perf.py" summarise "$out"

echo
echo "wrote $out"
echo "The 'op' scope is the one that speaks to the operation-level gap; 'e2e' is"
echo "mostly cross-thread handoff (section 7.5.2)."
