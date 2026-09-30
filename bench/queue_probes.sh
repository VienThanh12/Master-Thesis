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
# FILL AFTER THE WINDOW. The gap this script was written for moved with the
# histogram fill: on the reported host it vanished once the fill was deferred,
# and a smaller Rust lead was left. --correction-when after runs every arm on
# that deferred-fill clock, so the probes speak to the lead that remains and
# not to the recorder. --perf-cs wraps each run in `perf stat` and stores the
# process's context switches, which is how often its threads were set aside,
# mostly to sleep until the other side of the handoff answered.
#
# Usage:
#   bench/queue_probes.sh                      # defaults, 15 repeats
#   bench/queue_probes.sh --rate 64000 --repeats 15 --pin 2-17
#   bench/queue_probes.sh --rate 112000 --repeats 10 --pin 2-17 \
#       --shards 7 --producers 7 --correction-when after --perf-cs
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
correction_when=""
perf_cs=0

while [ $# -gt 0 ]; do
  case "$1" in
    --rate)       rate="$2"; shift 2;;
    --repeats)    repeats="$2"; shift 2;;
    --pin)        pin="$2"; shift 2;;
    --producers)  producers="$2"; shift 2;;
    --shards)     shards="$2"; shift 2;;
    --duration)   duration="$2"; shift 2;;
    --correction-when) correction_when="$2"; shift 2;;
    --perf-cs)    perf_cs=1; shift;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

extra=()
[ -n "$correction_when" ] && extra+=(--correction-when "$correction_when")

if [ "$perf_cs" = "1" ] && ! command -v perf >/dev/null 2>&1; then
  echo "FAIL: --perf-cs needs perf, and it is not on PATH"
  exit 1
fi

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
[ -n "$correction_when" ] && echo "   fill timing: --correction-when $correction_when"
[ "$perf_cs" = "1" ] && echo "   counting context switches with perf stat"

n=0
for rep in $(seq 1 "$repeats"); do
  for arm in "${order[@]}"; do
    n=$(( n + 1 ))
    printf '\r  run %d/%d (rep %d, %s)      ' "$n" "$total" "$rep" "$arm"
    cmd=("${BIN[$arm]}" --workload "$workload" --shards "$shards" \
      --producers "$producers" --active-ues "$active_ues" --preload "$preload" \
      --ops "$ops" --warmup "$warmup" --seed "$seed" --rate "$rate" \
      --max-run-s "$max_run_s" --run-id "$rep" "${extra[@]}" --json)
    csv=""
    if [ "$perf_cs" = "1" ]; then
      csv="$(mktemp)"
      line="$("${pre[@]}" perf stat -x, -e context-switches,cpu-migrations \
        -o "$csv" -- "${cmd[@]}" 2>/dev/null)"
    else
      line="$("${pre[@]}" "${cmd[@]}" 2>/dev/null)"
    fi
    if [ -z "$line" ]; then echo; echo "FAIL: no output from $arm"; exit 1; fi
    python3 - "$line" "$arm" "$rep" "$csv" >> "$out" <<'PY'
import json, sys
r = json.loads(sys.argv[1])
r["arm"] = sys.argv[2]
r["repeat"] = int(sys.argv[3])
if sys.argv[4]:
    counts = {}
    for raw in open(sys.argv[4]):
        f = raw.strip().split(",")
        if raw.startswith("#") or len(f) < 3:
            continue
        # "<not counted>" is recorded as null, never as zero.
        try:
            counts[f[2]] = float(f[0])
        except ValueError:
            counts[f[2]] = None
    r["ctx_switches"] = counts.get("context-switches")
    r["cpu_migrations"] = counts.get("cpu-migrations")
print(json.dumps(r))
PY
    [ -n "$csv" ] && rm -f "$csv"
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

usable = True
if served > 0.95:
    print("WARNING: the baseline arm served %.0f%% of the offered rate, so the host"
          % (served * 100))
    print("         is not in overload and these numbers answer nothing. Raise --rate.")
    usable = False

# The first swept load past the knee is metastable: an arm serves the full rate
# in some repeats and collapses in others, and a median across a distribution
# with a mode at each end is not a measurement. This cost one real probe run, so
# it is checked rather than left to the reader of the numbers.
for a in arms:
    vals = thr[a]
    cv = statistics.pstdev(vals) / statistics.mean(vals)
    if cv > 0.05:
        lo, hi = min(vals) / 1000, max(vals) / 1000
        print(f"WARNING: {a} varies by {cv * 100:.0f}% across repeats "
              f"({lo:.0f} to {hi:.0f} kops/s).")
        print("         This operating point is metastable. Its median is not a"
              " measurement,")
        print("         and no ratio below may be quoted. Move further past the knee.")
        usable = False
if not usable:
    print()
    print("REFUSING TO CERTIFY: see the warnings above before using any number here.")
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

# Where each arm's CPU goes, per finished call. Same chain as probe_facts.py's
# CpuPerOp: the run's CPU rate over its window throughput, medians over repeats.
def per_call_us(a, field):
    runs = [r for r in rows if r["arm"] == a]
    rate = statistics.median(r[field] / r["wall_s"] for r in runs)
    return rate / statistics.median(thr[a]) * 1e6

def switches_per_call(a):
    runs = [r for r in rows if r["arm"] == a and r.get("ctx_switches") is not None]
    if not runs:
        return None
    rate = statistics.median(r["ctx_switches"] / r["wall_s"] for r in runs)
    return rate / statistics.median(thr[a])

print(f"{'arm':<14}{'user us/call':>14}{'kernel us/call':>16}{'switches/call':>15}")
for a in arms:
    cs = switches_per_call(a)
    cs_txt = f"{cs:.2f}" if cs is not None else "n/a"
    print(f"{a:<14}{per_call_us(a, 'cpu_user_s'):>14.2f}"
          f"{per_call_us(a, 'cpu_sys_s'):>16.2f}{cs_txt:>15}")
print()

# With the fill after the window Rust leads, so the question turns round: how
# much of Rust's lead over stock C++ does the C++ queue design take away?
by_rep = {a: {r["repeat"]: r["throughput_ops_s"] for r in rows if r["arm"] == a}
          for a in arms}
reps = sorted(set.intersection(*(set(v) for v in by_rep.values())))
lead = statistics.median(thr["rust-channel"]) - statistics.median(thr["cpp-deque"])
if lead > 0:
    closed = (statistics.median(thr["rust-channel"])
              - statistics.median(thr["rust-mutexq"])) / lead
    slower = sum(1 for k in reps if by_rep["rust-mutexq"][k] < by_rep["rust-channel"][k])
    ahead = sum(1 for k in reps if by_rep["rust-channel"][k] > by_rep["cpp-deque"][k])
    print(f"    Rust ahead of C++ in {ahead} of {len(reps)} paired repeats")
    print(f"    Share of that lead the C++ queue design removes: {closed * 100:.0f}%")
    print(f"    Rust with the C++ queue slower than stock Rust in {slower} of {len(reps)}")
else:
    print("    Rust is not ahead at this rate, so no share of a lead is computed.")
print()
print(f"wrote {sys.argv[1]}")
PY
