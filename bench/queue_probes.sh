#!/usr/bin/env bash
# Substitution probes for the overload divergence (RQ1 mechanism).
#
# The load sweep shows C++ sustaining more throughput than Rust past saturation.
# Two candidate mechanisms live inside the shard queue, and each is tested by
# building one arm with that mechanism replaced and nothing else changed:
#
#   1. Synchronisation design. Rust's std sync_channel against a mutex, a
#      VecDeque and two condition variables, which is the C++ arm's design
#      (--features mutex-queue, rust/src/mutex_queue.rs).
#   2. Hot-path allocation. The C++ deque-backed std::queue against a
#      preallocated ring with byte-identical locking (-DUECM_RING_QUEUE=ON).
#      The deque allocates a node every third push inside the queue mutex; the
#      ring allocates nothing.
#
# Both probes are recorded in spec/SPECIFICATION.md section 12. Until this
# script existed they were run by hand on WSL2 at 5 and 7 repeats and the spec
# marks both results "indicative only". This runs all four arms interleaved
# inside one repeat, at one offered rate, so the two probes share their
# baselines instead of coming from two separate sessions.
#
# WHERE THIS RUNS. The probes are only meaningful past saturation, so the rate
# has to be one the host cannot serve. On a bare-metal EPYC 7443P with 16 pinned
# cores that is around 64000 per producer; on a smaller or virtualised host it
# is far lower. Check with a single run before trusting a number from here: if
# achieved throughput tracks the offered rate, the host is not in overload and
# the probe is measuring nothing.
#
# Usage:
#   bench/queue_probes.sh                      # defaults, 15 repeats
#   bench/queue_probes.sh --rate 64000 --repeats 15 --pin 2-17
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

workload="mixed"
shards=8
producers=8
active_ues=5000
preload=5000
duration=3
warmup_s=1
seed=42
repeats=15
rate=64000
pin=""

while [ $# -gt 0 ]; do
  case "$1" in
    --rate)       rate="$2"; shift 2;;
    --repeats)    repeats="$2"; shift 2;;
    --pin)        pin="$2"; shift 2;;
    --producers)  producers="$2"; shift 2;;
    --shards)     shards="$2"; shift 2;;
    --duration)   duration="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

max_run_s=$(( duration * 2 ))

# Every arm runs on the system allocator. The question is the queue, so the
# allocator is held fixed rather than varied: a jemalloc arm here would let an
# allocator effect masquerade as a queue effect.
mkdir -p "$here/.bin" "$here/results"

pre=()
if [ -n "$pin" ] && command -v taskset >/dev/null 2>&1; then
  pre+=(taskset -c "$pin")
  echo "== pinning probes to cores: $pin =="
fi

echo "== building the four arms =="
cmake -S "$cpp" -B "$cpp/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null 2>&1
cmake --build "$cpp/build" --target bench >/dev/null 2>&1 || { echo "FAIL: C++ baseline build"; exit 1; }

cmake -S "$cpp" -B "$cpp/build-ring" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DUECM_RING_QUEUE=ON -DUECM_BUILD_TESTS=OFF >/dev/null 2>&1
cmake --build "$cpp/build-ring" --target bench >/dev/null 2>&1 || { echo "FAIL: C++ ring build"; exit 1; }

cargo build --release --manifest-path "$rust/Cargo.toml" --example bench >/dev/null 2>&1 \
  || { echo "FAIL: Rust baseline build"; exit 1; }
cp "$rust/target/release/examples/bench" "$here/.bin/probe-rust-channel"

cargo build --release --manifest-path "$rust/Cargo.toml" --example bench \
  --features mutex-queue >/dev/null 2>&1 || { echo "FAIL: Rust mutex-queue build"; exit 1; }
cp "$rust/target/release/examples/bench" "$here/.bin/probe-rust-mutexq"

declare -A BIN=(
  ["cpp-deque"]="$cpp/build/bench"
  ["cpp-ring"]="$cpp/build-ring/bench"
  ["rust-channel"]="$here/.bin/probe-rust-channel"
  ["rust-mutexq"]="$here/.bin/probe-rust-mutexq"
)
order=("cpp-deque" "cpp-ring" "rust-channel" "rust-mutexq")

stamp="$(date +%Y%m%d-%H%M%S)"
out="$here/results/queue_probes-$stamp.jsonl"
: > "$out"

ops=$(( rate * duration ))
warmup=$(( rate * warmup_s ))
total=$(( repeats * ${#order[@]} ))
echo "== probing at $rate per producer ($(( rate * producers )) offered): $repeats repeats x ${#order[@]} arms = $total runs =="

n=0
for rep in $(seq 1 "$repeats"); do
  for arm in "${order[@]}"; do
    n=$(( n + 1 ))
    printf '\r  run %d/%d (rep %d, %s)      ' "$n" "$total" "$rep" "$arm"
    line="$("${pre[@]}" "${BIN[$arm]}" --workload "$workload" --shards "$shards" \
      --producers "$producers" --active-ues "$active_ues" --preload "$preload" \
      --ops "$ops" --warmup "$warmup" --seed "$seed" --rate "$rate" \
      --max-run-s "$max_run_s" --run-id "$rep" --json 2>/dev/null)"
    if [ -z "$line" ]; then echo; echo "FAIL: no output from $arm"; exit 1; fi
    python3 -c "
import json,sys
r=json.loads(sys.argv[1]); r['arm']=sys.argv[2]; r['repeat']=int(sys.argv[3])
print(json.dumps(r))" "$line" "$arm" "$rep" >> "$out"
  done
done
printf '\n\n'

python3 - "$out" "$here" <<'PY'
import json, statistics, sys
sys.path.insert(0, sys.argv[2])
from plot_figures import bootstrap_ci, paired_permutation_test

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
arms = ["cpp-deque", "cpp-ring", "rust-channel", "rust-mutexq"]
thr = {a: [r["throughput_ops_s"] for r in rows if r["arm"] == a] for a in arms}
offered = rows[0]["rate"] * rows[0]["producers"]
n = len(thr[arms[0]])

served = statistics.median(thr["cpp-deque"]) / offered
print(f"offered {offered:,.0f} ops/s, {n} repeats per arm")
if served > 0.95:
    print("WARNING: the baseline arm served %.0f%% of the offered rate, so the host"
          % (served * 100))
    print("         is not in overload and these numbers answer nothing. Raise --rate.")
print()

print(f"{'arm':<14}{'sustained kops/s':>18}{'95% CI':>22}")
for a in arms:
    m, lo, hi = bootstrap_ci(thr[a])
    print(f"{a:<14}{m/1000:>18.2f}{f'[{lo/1000:.2f}, {hi/1000:.2f}]':>22}")
print()

def contrast(label, base, probe, question):
    md, p, k = paired_permutation_test(thr[base], thr[probe])
    b, q = statistics.median(thr[base]), statistics.median(thr[probe])
    print(f"{label}")
    print(f"    {base} {b/1000:.2f} against {probe} {q/1000:.2f} kops/s, "
          f"{(q - b) / b * 100:+.1f}%, paired p={p:.2e}")
    print(f"    {question}")
    print()

print("Divergence and what each substitution does to it")
print()
base_ratio = statistics.median(thr["cpp-deque"]) / statistics.median(thr["rust-channel"])
print(f"    Baseline divergence, C++ over Rust: {base_ratio:.2f}x")
print()
contrast("Probe 1, Rust queue design matched to the C++ arm:",
         "rust-channel", "rust-mutexq",
         "Closes the divergence only if Rust moves up towards C++.")
contrast("Probe 2, C++ hot-path allocation removed:",
         "cpp-deque", "cpp-ring",
         "Explains the divergence only if C++ moves down towards Rust.")

r_mutexq = statistics.median(thr["cpp-deque"]) / statistics.median(thr["rust-mutexq"])
r_ring = statistics.median(thr["cpp-ring"]) / statistics.median(thr["rust-channel"])
print(f"    Ratio with the Rust queue substituted: {r_mutexq:.2f}x")
print(f"    Ratio with the C++ allocation removed: {r_ring:.2f}x")
print()
print(f"wrote {sys.argv[1]}")
PY
