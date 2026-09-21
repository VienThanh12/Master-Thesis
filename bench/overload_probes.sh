#!/usr/bin/env bash
# Attribution probes for the overload floor (RQ1 mechanism).
#
# The compared campaign is open-loop with a 10 000-sample coordinated-omission
# backfill. Three substitutions test where the C++/Rust floor gap lives, without
# moving the reported pair:
#
#   P0  Closed loop. Same 7/7 mixed service, no --rate, so no backfill.
#   P1  Open loop with --correction-cap 0. The send schedule stays, the
#       synthetic histogram cost does not.
#   P2  Rust completions via sync_channel(1) instead of unbounded channel().
#   P3  Two other clocks, still open-loop, compared pair untouched:
#         --latency-origin start: record t_done - t_actual_send, no fill.
#         --correction-when after: real samples only during the run, then
#         the capped fill once the producer finishes.
#
# System allocator only. Interleaved inside each repeat. Recorded in
# spec/SPECIFICATION.md §12 and docs/OVERLOAD_MECHANISM.md. WSL2 numbers from
# this script are indicative. Quote nothing from them in the thesis.
#
# WHERE THIS RUNS. P1 and P2 are only meaningful past saturation, so --rate has
# to be one the host cannot serve. On the reported EPYC design that is 112000
# per producer (784 kops/s offered). On a 14-thread laptop it is far lower.
# Check a single run first: if achieved throughput tracks the offered rate, the
# host is not in overload and P1/P2 measure nothing.
#
# Usage:
#   bench/overload_probes.sh --phase p0
#   bench/overload_probes.sh --phase p1 --rate 20000
#   bench/overload_probes.sh --phase p3 --rate 112000 --repeats 10 --pin 2-17
#   bench/overload_probes.sh --phase all --rate 112000 --repeats 10 --pin 2-17
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

phase="all"
workload="mixed"
shards=7
producers=7
active_ues=5000
preload=5000
duration=3
warmup_s=1
seed=42
repeats=10
rate=""
pin=""

while [ $# -gt 0 ]; do
  case "$1" in
    --phase)      phase="$2"; shift 2;;
    --rate)       rate="$2"; shift 2;;
    --repeats)    repeats="$2"; shift 2;;
    --pin)        pin="$2"; shift 2;;
    --producers)  producers="$2"; shift 2;;
    --shards)     shards="$2"; shift 2;;
    --duration)   duration="$2"; shift 2;;
    --warmup-s)   warmup_s="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

case "$phase" in
  p0|p1|p2|p3|all) ;;
  *) echo "unknown --phase $phase (p0|p1|p2|p3|all)"; exit 2;;
esac

if [ "$phase" != "p0" ] && [ -z "$rate" ]; then
  echo "P1, P2 and P3 need --rate (ops/s per producer, past this host's knee)."
  echo "  reported campaign: --rate 112000"
  echo "  this laptop:       try --rate 20000 and check the overload warning"
  exit 2
fi

max_run_s="$duration"
# Closed loop must not auto-derive warmup from a huge --ops.
warmup_closed=$(( 2 * active_ues ))

mkdir -p "$here/.bin" "$here/results"

pre=()
if [ -n "$pin" ] && command -v taskset >/dev/null 2>&1; then
  pre+=(taskset -c "$pin")
  echo "== pinning probes to cores: $pin =="
fi

echo "== building probe arms (compared pair untouched: default C++ and Rust) =="
cmake -S "$cpp" -B "$cpp/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null 2>&1
cmake --build "$cpp/build" --target bench >/dev/null 2>&1 || { echo "FAIL: C++ bench build"; exit 1; }

cargo build --release --manifest-path "$rust/Cargo.toml" --example bench >/dev/null 2>&1 \
  || { echo "FAIL: Rust baseline build"; exit 1; }
cp "$rust/target/release/examples/bench" "$here/.bin/probe-rust-std"

if [ "$phase" = "p2" ] || [ "$phase" = "all" ]; then
  cargo build --release --manifest-path "$rust/Cargo.toml" --example bench \
    --features sync-oneshot >/dev/null 2>&1 || { echo "FAIL: Rust sync-oneshot build"; exit 1; }
  cp "$rust/target/release/examples/bench" "$here/.bin/probe-rust-oneshot"
fi

stamp="$(date +%Y%m%d-%H%M%S)"
out="$here/results/overload_probes-$stamp.jsonl"
: > "$out"

run_arm() {
  local arm="$1" bin="$2" rep="$3"; shift 3
  local line
  line="$("${pre[@]}" "$bin" --workload "$workload" --shards "$shards" \
    --producers "$producers" --active-ues "$active_ues" --preload "$preload" \
    --seed "$seed" --run-id "$rep" --json "$@" 2>/dev/null)"
  if [ -z "$line" ]; then echo; echo "FAIL: no output from $arm"; exit 1; fi
  python3 -c "
import json,sys
r=json.loads(sys.argv[1]); r['arm']=sys.argv[2]; r['repeat']=int(sys.argv[3]); r['phase']=sys.argv[4]
print(json.dumps(r))" "$line" "$arm" "$rep" "$phase_tag"
}

phase_tag=""

run_phase_p0() {
  phase_tag="p0"
  local order=("cpp-closed" "rust-closed")
  local -A BIN=(
    ["cpp-closed"]="$cpp/build/bench"
    ["rust-closed"]="$here/.bin/probe-rust-std"
  )
  echo "== P0 closed loop: $repeats repeats x ${#order[@]} arms, ${duration}s measured, no --rate =="
  local rep arm
  for rep in $(seq 1 "$repeats"); do
    for arm in "${order[@]}"; do
      n=$(( n + 1 ))
      printf '\r  run %d/%d (rep %d, %s)      ' "$n" "$expected_total" "$rep" "$arm"
      # Huge --ops so the wall cap is what ends the measured window.
      run_arm "$arm" "${BIN[$arm]}" "$rep" \
        --warmup "$warmup_closed" --ops 10000000 --max-run-s "$max_run_s" \
        >>"$out"
    done
  done
  printf '\n'
}

run_phase_open() {
  local tag="$1"; shift
  phase_tag="$tag"
  local -a order=("$@")
  local ops=$(( rate * duration ))
  local warmup=$(( rate * warmup_s ))
  echo "== $tag open loop: $repeats repeats x ${#order[@]} arms, $rate/prod ($(( rate * producers )) offered) =="
  local rep arm bin extra
  for rep in $(seq 1 "$repeats"); do
    for arm in "${order[@]}"; do
      n=$(( n + 1 ))
      printf '\r  run %d/%d (rep %d, %s)      ' "$n" "$expected_total" "$rep" "$arm"
      case "$arm" in
        cpp-cap0)     bin="$cpp/build/bench"; extra=(--correction-cap 0) ;;
        rust-cap0)    bin="$here/.bin/probe-rust-std"; extra=(--correction-cap 0) ;;
        cpp-open)     bin="$cpp/build/bench"; extra=() ;;
        rust-open)    bin="$here/.bin/probe-rust-std"; extra=() ;;
        rust-oneshot) bin="$here/.bin/probe-rust-oneshot"; extra=() ;;
        cpp-start)    bin="$cpp/build/bench"; extra=(--latency-origin start --correction-cap 0) ;;
        rust-start)   bin="$here/.bin/probe-rust-std"; extra=(--latency-origin start --correction-cap 0) ;;
        cpp-after)    bin="$cpp/build/bench"; extra=(--correction-when after) ;;
        rust-after)   bin="$here/.bin/probe-rust-std"; extra=(--correction-when after) ;;
        *) echo; echo "FAIL: unknown arm $arm"; exit 1;;
      esac
      run_arm "$arm" "$bin" "$rep" \
        --ops "$ops" --warmup "$warmup" --rate "$rate" --max-run-s "$max_run_s" \
        "${extra[@]}" >>"$out"
    done
  done
  printf '\n'
}

n=0
expected_total=0
case "$phase" in
  p0)  expected_total=$(( repeats * 2 )); run_phase_p0 ;;
  p1)  expected_total=$(( repeats * 4 )); run_phase_open p1 cpp-open rust-open cpp-cap0 rust-cap0 ;;
  p2)  expected_total=$(( repeats * 3 )); run_phase_open p2 cpp-open rust-open rust-oneshot ;;
  p3)  expected_total=$(( repeats * 4 )); run_phase_open p3 cpp-start rust-start cpp-after rust-after ;;
  all)
    expected_total=$(( repeats * 13 ))
    run_phase_p0
    run_phase_open p1 cpp-open rust-open cpp-cap0 rust-cap0
    run_phase_open p2 cpp-open rust-open rust-oneshot
    run_phase_open p3 cpp-start rust-start cpp-after rust-after
    ;;
esac

python3 - "$out" "$here" "$phase" <<'PY'
import json, statistics, sys
sys.path.insert(0, sys.argv[2])
from plot_figures import bootstrap_ci, paired_permutation_test

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
want_phase = sys.argv[3]
print(f"wrote {sys.argv[1]}")
print()

def by_arm(phase, field="throughput_ops_s"):
    arms = {}
    for r in rows:
        if r.get("phase") != phase:
            continue
        if field == "p50_ns":
            val = r.get("lat_ns", {}).get("p50")
        else:
            val = r[field]
        if val is None:
            continue
        arms.setdefault(r["arm"], []).append(val)
    return arms

def report(phase, arms_order, offered=None):
    thr = by_arm(phase)
    if not thr:
        return
    n = len(next(iter(thr.values())))
    print(f"=== {phase}  ({n} repeats per arm) ===")
    usable = True
    if offered:
        served = statistics.median(thr[arms_order[0]]) / offered
        print(f"offered {offered:,.0f} ops/s")
        if served > 0.95:
            print("WARNING: baseline served %.0f%% of offered. Not in overload."
                  % (served * 100))
            usable = False
    for a in arms_order:
        vals = thr[a]
        cv = statistics.pstdev(vals) / statistics.mean(vals) if statistics.mean(vals) else 0
        if cv > 0.05:
            lo, hi = min(vals) / 1000, max(vals) / 1000
            print(f"WARNING: {a} varies by {cv * 100:.0f}% ({lo:.0f} to {hi:.0f} kops/s).")
            print("         Metastable. Do not quote the median.")
            usable = False
    print(f"{'arm':<14}{'sustained kops/s':>18}{'95% CI':>22}")
    for a in arms_order:
        m, lo, hi = bootstrap_ci(thr[a])
        print(f"{a:<14}{m/1000:>18.2f}{f'[{lo/1000:.2f}, {hi/1000:.2f}]':>22}")
    print()
    def contrast(label, left, right):
        md, p, k = paired_permutation_test(thr[left], thr[right])
        b, q = statistics.median(thr[left]), statistics.median(thr[right])
        ratio = b / q if q else float("inf")
        print(f"  {label}")
        print(f"    {left} {b/1000:.2f} against {right} {q/1000:.2f} kops/s, "
              f"C++/Rust {ratio:.2f}x, paired p={p:.2e}")
    if not usable:
        print("  REFUSING TO CERTIFY: see warnings above.")
        print()
        return
    if phase == "p0":
        contrast("Closed-loop language ratio (no --rate, no backfill):",
                 "cpp-closed", "rust-closed")
    elif phase == "p1":
        contrast("Open loop, default 10 000-sample cap (the campaign instrument):",
                 "cpp-open", "rust-open")
        contrast("Open loop, cap 0 (schedule on, backfill off):",
                 "cpp-cap0", "rust-cap0")
        b = statistics.median(thr["cpp-open"]) / statistics.median(thr["rust-open"])
        q = statistics.median(thr["cpp-cap0"]) / statistics.median(thr["rust-cap0"])
        print(f"  Ratio with backfill on:  {b:.2f}x")
        print(f"  Ratio with backfill off: {q:.2f}x")
        print("  The instrument is in the result only if the second is nearer 1.")
    elif phase == "p2":
        contrast("Open loop, standard unbounded oneshot:",
                 "cpp-open", "rust-open")
        contrast("Open loop, Rust sync_channel(1) completions:",
                 "cpp-open", "rust-oneshot")
        b = statistics.median(thr["cpp-open"]) / statistics.median(thr["rust-open"])
        q = statistics.median(thr["cpp-open"]) / statistics.median(thr["rust-oneshot"])
        print(f"  Ratio with channel():      {b:.2f}x")
        print(f"  Ratio with sync_channel(1): {q:.2f}x")
        print("  The list oneshot is in the result only if the second is nearer 1.")
    elif phase == "p3":
        contrast("Open loop, latency from actual send, no fill:",
                 "cpp-start", "rust-start")
        contrast("Open loop, intended origin, fill after the timed loop:",
                 "cpp-after", "rust-after")
        p50 = by_arm(phase, "p50_ns")
        print("  service-time p50 (start origin, ns):")
        for a in ("cpp-start", "rust-start"):
            if a in p50:
                m, lo, hi = bootstrap_ci(p50[a])
                print(f"    {a:<12}{m/1000:.1f} us  [{lo/1000:.1f}, {hi/1000:.1f}]")
        print("  intended-origin p50 (after fill, ns) stays schedule drift:")
        for a in ("cpp-after", "rust-after"):
            if a in p50:
                m = statistics.median(p50[a])
                print(f"    {a:<12}{m/1e6:.1f} ms")
        print("  Start-origin p50 is the language comparison of the call.")
        print("  After-fill throughput should sit with P1 cap 0, not with P1 default cap.")
    print()

offered = None
if any(r.get("rate", 0) for r in rows):
    r0 = next(r for r in rows if r.get("rate", 0))
    offered = r0["rate"] * r0["producers"]

if want_phase in ("p0", "all"):
    report("p0", ["cpp-closed", "rust-closed"])
if want_phase in ("p1", "all"):
    report("p1", ["cpp-open", "rust-open", "cpp-cap0", "rust-cap0"], offered)
if want_phase in ("p2", "all"):
    report("p2", ["cpp-open", "rust-open", "rust-oneshot"], offered)
if want_phase in ("p3", "all"):
    report("p3", ["cpp-start", "rust-start", "cpp-after", "rust-after"], offered)

print("Indicative on this host. Do not copy kops/s into gen_macros.tex or the thesis.")
print("Re-run on the measurement host at 784 kops/s offered before revising claims.")
PY
