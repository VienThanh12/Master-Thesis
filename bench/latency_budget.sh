#!/usr/bin/env bash
# Latency-budget decomposition (RQ1/RQ3 supporting measurement).
#
# The load sweep reports one end-to-end number per operation, which bundles the
# operation's own work with the cross-thread submit-and-complete handoff that
# carries it. Those two costs answer to different things: the first is what the
# language compiles, the second is what the scheduler does, and only the first
# can differ between C++ and Rust. Without separating them a bound on the paired
# median difference cannot be read, because it is a bound relative to a total
# that may be mostly handoff.
#
# This runs the same decomposition in both languages, at the sweep's own shard
# count and context population, and writes one JSON record per language per
# repeat.
#
# Repeats are interleaved the same way the campaign interleaves its variants: the
# outer loop is the repeat and the two languages run back to back inside it, so
# drift over the session perturbs both equally instead of biasing whichever ran
# first. The analysis takes medians with bootstrap intervals across repeats, as
# it does everywhere else, rather than trusting a single run.
#
# Run it on a quiet host. It is a microbenchmark, and interleaving only cancels
# the interference a whole block shares.
#
# Usage:
#   bench/latency_budget.sh                       # sweep-matched defaults
#   bench/latency_budget.sh --shards 8 --active-ues 5000 --repeats 15
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

# Defaults match the campaign's configuration so the decomposition applies to
# the numbers the sweep actually reports.
shards=8
active_ues=5000
core_iters=2000000
svc_iters=50000
repeats=15

while [ $# -gt 0 ]; do
  case "$1" in
    --shards)      shards="$2"; shift 2;;
    --active-ues)  active_ues="$2"; shift 2;;
    --core-iters)  core_iters="$2"; shift 2;;
    --svc-iters)   svc_iters="$2"; shift 2;;
    --repeats)     repeats="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

mkdir -p "$here/results"
out="$here/results/latency_budget.json"

echo "== building =="
cmake -S "$cpp" -B "$cpp/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$cpp/build" --target latency_budget >/dev/null
cargo build --release --manifest-path "$rust/Cargo.toml" --example latency_budget >/dev/null 2>&1

args=(--shards "$shards" --active-ues "$active_ues"
      --core-iters "$core_iters" --svc-iters "$svc_iters" --json)

echo "== measuring: ${repeats} interleaved repeats (${shards} shards, ${active_ues} active UEs) =="
: > "$out"
for rep in $(seq 1 "$repeats"); do
  printf '\r  repeat %d/%d      ' "$rep" "$repeats"
  "$cpp/build/latency_budget" "${args[@]}" >> "$out"
  "$rust/target/release/examples/latency_budget" "${args[@]}" >> "$out"
done
printf '\n\n'

python3 - "$out" <<'PY'
import json, statistics, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
by = {}
for r in rows:
    by.setdefault(r["lang"], []).append(r)
print(f"{'':6} {'core (ns)':>12} {'handoff (ns)':>14} {'round-trip (ns)':>16}   n")
for lang, rs in by.items():
    med = lambda k: statistics.median(x[k] for x in rs)
    print(f"{lang:6} {med('core_ns'):12.1f} {med('handoff_ns'):14.1f} "
          f"{med('service_ns'):16.1f}  {len(rs)}")
PY

echo
echo "wrote $out"
