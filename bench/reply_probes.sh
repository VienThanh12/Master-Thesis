#!/usr/bin/env bash
# Reply-handle probe for the Rust lead that remains past saturation (RQ1 mechanism).
#
# PROBE ONLY. Not a reported arm and not in the Holm-tested family.
#
# The two reply handles differ by an order of magnitude in what they allocate.
# Counted per request with an allocation tracker on 19 October 2026, campaign
# image, senders sending back to back:
#   C++ std::promise           about 220 bytes, made and freed on the sending thread
#   Rust std channel()         about 2,360 bytes, and a 1,744-byte message block
#                              that the worker allocates and the sender frees
#   Rust sync_channel(1)       about 810 bytes, nothing freed across threads
# Both Rust forms also make one 128-byte-aligned allocation per request, because
# the channel pads its head and tail to separate cache lines.
#
# The 19 September swap (spec section 12, P2) ran with the fill inside the timed
# loop, where the recorder set the limit, so it cannot speak to the lead that is
# left once the fill is deferred. This script asks that question on the deferred
# clock: six arms interleaved inside each repeat, at one offered rate past
# saturation, both languages on both allocators and Rust with the one-slot reply
# on both.
#
#   1. Does the lighter reply move Rust's throughput on either allocator?
#   2. Does it remove Rust's allocator difference, system against jemalloc?
#   3. What does it do to the Rust lead over C++ on each allocator?
#
# Usage:
#   bench/reply_probes.sh --rate 112000 --repeats 10 --pin 2-17 \
#       --shards 7 --producers 7 --correction-when after
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

workload="mixed"
shards=7
producers=7
active_ues=5000
preload=5000
duration=3
warmup_s=1
seed=42
repeats=10
rate=112000
pin=""
correction_when="after"

while [ $# -gt 0 ]; do
  case "$1" in
    --rate)       rate="$2"; shift 2;;
    --repeats)    repeats="$2"; shift 2;;
    --pin)        pin="$2"; shift 2;;
    --producers)  producers="$2"; shift 2;;
    --shards)     shards="$2"; shift 2;;
    --duration)   duration="$2"; shift 2;;
    --correction-when) correction_when="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

max_run_s=$(( duration * 2 ))
mkdir -p "$here/.bin" "$here/results"

pre=()
if [ -n "$pin" ] && command -v taskset >/dev/null 2>&1; then
  pre+=(taskset -c "$pin")
  echo "== pinning probes to cores: $pin =="
fi
# The campaign's jemalloc settings (bench/campaign.sh). The C++ arm reads MALLOC_CONF and
# tikv-jemalloc reads _RJEM_MALLOC_CONF. The 19 October run predates this line and used
# the allocator's defaults.
export MALLOC_CONF="thp:never,narenas:16"
export _RJEM_MALLOC_CONF="thp:never,narenas:16"

echo "== building the six arms =="
cmake -S "$cpp" -B "$cpp/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null 2>&1
cmake --build "$cpp/build" --target bench >/dev/null 2>&1 || { echo "FAIL: C++ system build"; exit 1; }
cmake -S "$cpp" -B "$cpp/build-jemalloc" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DUECM_USE_JEMALLOC=ON -DUECM_BUILD_TESTS=OFF >/dev/null 2>&1
cmake --build "$cpp/build-jemalloc" --target bench >/dev/null 2>&1 || { echo "FAIL: C++ jemalloc build"; exit 1; }

build_rust() {
  local name="$1"; shift
  cargo build --release --manifest-path "$rust/Cargo.toml" --example bench "$@" >/dev/null 2>&1 \
    || { echo "FAIL: Rust build $name"; exit 1; }
  cp "$rust/target/release/examples/bench" "$here/.bin/reply-$name"
}
build_rust rust-system
build_rust rust-jemalloc --features jemalloc
build_rust rust-system-oneshot --features sync-oneshot
build_rust rust-jemalloc-oneshot --features jemalloc,sync-oneshot

declare -A BIN=(
  ["cpp-system"]="$cpp/build/bench"
  ["cpp-jemalloc"]="$cpp/build-jemalloc/bench"
  ["rust-system"]="$here/.bin/reply-rust-system"
  ["rust-jemalloc"]="$here/.bin/reply-rust-jemalloc"
  ["rust-system-oneshot"]="$here/.bin/reply-rust-system-oneshot"
  ["rust-jemalloc-oneshot"]="$here/.bin/reply-rust-jemalloc-oneshot"
)
order=("cpp-system" "rust-system" "rust-system-oneshot" "cpp-jemalloc" "rust-jemalloc" "rust-jemalloc-oneshot")

stamp="$(date +%Y%m%d-%H%M%S)"
out="$here/results/reply_probes-$stamp.jsonl"
: > "$out"

ops=$(( rate * duration ))
warmup=$(( rate * warmup_s ))
n_arms=${#order[@]}
total=$(( repeats * n_arms ))
echo "== probing at $rate per producer ($(( rate * producers )) offered): $repeats repeats x $n_arms arms = $total runs =="
echo "   fill timing: --correction-when $correction_when"

n=0
for rep in $(seq 1 "$repeats"); do
  # Rotate the starting arm so no arm always runs first in a repeat.
  start_at=$(( (rep - 1) % n_arms ))
  for k in $(seq 0 $(( n_arms - 1 ))); do
    arm="${order[$(( (start_at + k) % n_arms ))]}"
    n=$(( n + 1 ))
    printf '\r  run %d/%d (rep %d, %s)        ' "$n" "$total" "$rep" "$arm"
    line="$("${pre[@]}" "${BIN[$arm]}" --workload "$workload" --shards "$shards" \
      --producers "$producers" --active-ues "$active_ues" --preload "$preload" \
      --ops "$ops" --warmup "$warmup" --seed "$seed" --rate "$rate" \
      --max-run-s "$max_run_s" --run-id "$rep" --correction-when "$correction_when" \
      --json 2>/dev/null)"
    if [ -z "$line" ]; then echo; echo "FAIL: no output from $arm"; exit 1; fi
    python3 -c '
import json, sys
r = json.loads(sys.argv[1])
r["arm"] = sys.argv[2]
r["repeat"] = int(sys.argv[3])
print(json.dumps(r))' "$line" "$arm" "$rep" >> "$out"
  done
done
printf '\n\n'

python3 - "$out" "$here" <<'PY'
import json, statistics, sys
sys.path.insert(0, sys.argv[2])
from plot_figures import bootstrap_ci, paired_permutation_test

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
arms = ["cpp-system", "rust-system", "rust-system-oneshot",
        "cpp-jemalloc", "rust-jemalloc", "rust-jemalloc-oneshot"]
by_rep = {a: {r["repeat"]: r for r in rows if r["arm"] == a} for a in arms}
reps = sorted(set.intersection(*(set(v) for v in by_rep.values())))
thr = {a: [by_rep[a][k]["throughput_ops_s"] for k in reps] for a in arms}
offered = rows[0]["rate"] * rows[0]["producers"]
print(f"offered {offered:,.0f} ops/s, {len(reps)} paired repeats per arm")

usable = True
for a in arms:
    served = statistics.median(thr[a]) / offered
    if served > 0.95:
        print(f"WARNING: {a} served {served * 100:.0f}% of the offered rate, so it is not"
              " in overload. Raise --rate.")
        usable = False
    cv = statistics.pstdev(thr[a]) / statistics.mean(thr[a])
    if cv > 0.05:
        print(f"WARNING: {a} varies by {cv * 100:.0f}% across repeats "
              f"({min(thr[a]) / 1000:.0f} to {max(thr[a]) / 1000:.0f} kops/s). This"
              " operating point is metastable and no ratio below may be quoted.")
        usable = False
if not usable:
    print()
    print("REFUSING TO CERTIFY: see the warnings above before using any number here.")
print()

def per_call_us(a, field):
    rate = statistics.median(by_rep[a][k][field] / by_rep[a][k]["wall_s"] for k in reps)
    return rate / statistics.median(thr[a]) * 1e6

print(f"{'arm':<24}{'kops/s':>9}{'95% CI':>20}{'user us/call':>14}{'kernel us/call':>16}")
for a in arms:
    m, lo, hi = bootstrap_ci(thr[a])
    print(f"{a:<24}{m / 1000:>9.1f}{f'[{lo / 1000:.1f}, {hi / 1000:.1f}]':>20}"
          f"{per_call_us(a, 'cpu_user_s'):>14.2f}{per_call_us(a, 'cpu_sys_s'):>16.2f}")
print()

def contrast(label, base, probe):
    md, p, k = paired_permutation_test(thr[base], thr[probe])
    b, q = statistics.median(thr[base]), statistics.median(thr[probe])
    ahead = sum(1 for x, y in zip(thr[base], thr[probe]) if y > x)
    print(f"{label}")
    print(f"    {base} {b / 1000:.1f} against {probe} {q / 1000:.1f} kops/s, "
          f"{(q - b) / b * 100:+.1f}%, {probe} higher in {ahead} of {len(reps)}, paired p={p:.2e}")

print("1. The lighter reply, per allocator")
contrast("   system allocator:", "rust-system", "rust-system-oneshot")
contrast("   jemalloc:", "rust-jemalloc", "rust-jemalloc-oneshot")
print()
print("2. The allocator difference, with each reply")
contrast("   Rust, standard reply:", "rust-system", "rust-jemalloc")
contrast("   Rust, one-slot reply:", "rust-system-oneshot", "rust-jemalloc-oneshot")
contrast("   C++ for reference:", "cpp-system", "cpp-jemalloc")
print()
print("3. The Rust lead over C++")
contrast("   system, standard reply:", "cpp-system", "rust-system")
contrast("   system, one-slot reply:", "cpp-system", "rust-system-oneshot")
contrast("   jemalloc, standard reply:", "cpp-jemalloc", "rust-jemalloc")
contrast("   jemalloc, one-slot reply:", "cpp-jemalloc", "rust-jemalloc-oneshot")
print()
print(f"wrote {sys.argv[1]}")
PY
