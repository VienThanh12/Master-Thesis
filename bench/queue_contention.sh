#!/usr/bin/env bash
# Contended-queue microbenchmark (overload mechanism, RQ1/RQ3 supporting).
#
# The load sweep shows C++ sustaining more throughput than Rust past saturation,
# and attributes the gap to the two forced-idiom primitives: the bounded blocking
# queue and the one-shot completion handle. This harness isolates those primitives
# without ShardCore work: N producer threads hammer one queue while a single
# consumer drains it.
#
# Defaults match the service: seven producers, queue capacity 1024. Repeats are
# interleaved C++/Rust inside each block, as in the campaign and latency_budget.
#
# Usage:
#   bench/queue_contention.sh
#   bench/queue_contention.sh --producers 7 --repeats 20 --seconds 2
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

producers=7
capacity=1024
seconds=2
repeats=20

while [ $# -gt 0 ]; do
  case "$1" in
    --producers) producers="$2"; shift 2;;
    --capacity)  capacity="$2"; shift 2;;
    --seconds)   seconds="$2"; shift 2;;
    --repeats)   repeats="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

mkdir -p "$here/results"
out="$here/results/queue_contention.json"

echo "== building =="
cmake -S "$cpp" -B "$cpp/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$cpp/build" --target queue_contention >/dev/null
cargo build --release --manifest-path "$rust/Cargo.toml" --example queue_contention >/dev/null 2>&1

args=(--producers "$producers" --capacity "$capacity" --seconds "$seconds" --json)

echo "== measuring: ${repeats} interleaved repeats (${producers} producers, cap ${capacity}) =="
: > "$out"
for rep in $(seq 1 "$repeats"); do
  printf '\r  repeat %d/%d      ' "$rep" "$repeats"
  "$cpp/build/queue_contention" "${args[@]}" >> "$out"
  "$rust/target/release/examples/queue_contention" "${args[@]}" >> "$out"
done
printf '\n\n'

python3 - "$out" <<'PY'
import json, statistics, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
by = {}
for r in rows:
    by.setdefault(r["lang"], []).append(r)
print(f"{'':6} {'kops/s':>10} {'ns/op':>12}   n")
for lang, rs in by.items():
    print(f"{lang:6} {statistics.median(x['throughput_kops'] for x in rs):10.1f} "
          f"{statistics.median(x['ns_per_op'] for x in rs):12.1f}  {len(rs)}")
PY

echo
echo "wrote $out"
