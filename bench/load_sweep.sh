#!/usr/bin/env bash
# Load sweep: for each language x allocator variant and each target rate, run the
# benchmark open-loop (coordinated-omission-corrected) for a fixed duration, then
# write a tidy CSV of the latency-vs-load curve for plotting (RQ1 / RQ3).
#
# Rate is per-producer ops/sec; offered total load = rate * producers. Each run does
# ops = rate * duration (so wall time ~= duration until the service saturates, after
# which latency from the intended send time grows -- the overload signal we want).
#
# Usage:
#   bench/load_sweep.sh                                  # defaults
#   bench/load_sweep.sh --workload mixed --producers 8 --active-ues 5000 \
#       --duration 3 --warmup-s 1 --rates "1000 2000 4000 6000 8000 10000 12000"
#
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
rates="1000 2000 4000 6000 8000 10000 12000 16000"

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
    --rates)      rates="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

mkdir -p "$here/.bin" "$here/results"

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
jsonl="$here/results/sweep-$stamp.jsonl"
csv="$here/results/sweep-$stamp.csv"
: > "$jsonl"

echo "== sweeping rates (per producer): $rates =="
for variant in "${order[@]}"; do
  bin="${BIN[$variant]}"
  for r in $rates; do
    ops=$(( r * duration ))
    warmup=$(( r * warmup_s ))
    args=(--workload "$workload" --shards "$shards" --producers "$producers" \
          --active-ues "$active_ues" --preload "$preload" --ops "$ops" \
          --warmup "$warmup" --seed "$seed" --rate "$r" --json)
    echo "  $variant rate=$r/prod ops=$ops ..."
    "$bin" "${args[@]}" >>"$jsonl"
  done
done

python3 - "$jsonl" "$csv" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
cols = ["lang","alloc","workload","shards","producers","rate_per_prod",
        "offered_ops_s","achieved_ops_s","errors",
        "p50_ns","p90_ns","p99_ns","p999_ns","max_ns","mean_ns","wall_s"]
with open(sys.argv[2], "w") as f:
    f.write(",".join(cols) + "\n")
    for r in rows:
        L = r["lat_ns"]
        rate = r.get("rate", 0.0)
        offered = rate * r["producers"]
        vals = [r["lang"], r["alloc"], r["workload"], r["shards"], r["producers"],
                f'{rate:.0f}', f'{offered:.0f}', f'{r["throughput_ops_s"]:.0f}', r["errors"],
                L["p50"], L["p90"], L["p99"], L["p999"], L["max"], f'{L["mean"]:.0f}',
                f'{r["wall_s"]:.3f}']
        f.write(",".join(str(v) for v in vals) + "\n")

# Console preview: p99 vs offered load per variant.
w = (6, 9, 14, 14, 12, 12)
def fmt(v): return "  ".join(str(x).rjust(width) for x, width in zip(v, w))
print()
print(fmt(("lang","alloc","offered(op/s)","achieved(op/s)","p99_ns","p99.9_ns")))
print(fmt(tuple("-"*x for x in w)))
for r in rows:
    L = r["lat_ns"]
    print(fmt((r["lang"], r["alloc"], f'{r.get("rate",0)*r["producers"]:.0f}',
               f'{r["throughput_ops_s"]:.0f}', L["p99"], L["p999"])))
print("\nwrote", sys.argv[2])
PY
