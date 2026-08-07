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
# count and context population, and writes one JSON record per language.
#
# Run it on a quiet host: it is a microbenchmark, and unlike the sweep it has no
# interleaving discipline to fall back on.
#
# Usage:
#   bench/latency_budget.sh                       # sweep-matched defaults
#   bench/latency_budget.sh --shards 8 --active-ues 5000
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

while [ $# -gt 0 ]; do
  case "$1" in
    --shards)      shards="$2"; shift 2;;
    --active-ues)  active_ues="$2"; shift 2;;
    --core-iters)  core_iters="$2"; shift 2;;
    --svc-iters)   svc_iters="$2"; shift 2;;
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

echo "== measuring (${shards} shards, ${active_ues} active UEs) =="
: > "$out"
"$cpp/build/latency_budget" "${args[@]}" | tee -a "$out"
"$rust/target/release/examples/latency_budget" "${args[@]}" | tee -a "$out"

echo
echo "wrote $out"
