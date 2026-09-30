#!/usr/bin/env bash
# Hash map probe on the full service, with the fill after the timed window.
#
# Three arms interleaved inside each repeat: stock C++, C++ built with
# -DUECM_FLAT_MAP=ON (an open-addressed map, as Rust's is), and stock Rust. If
# the node-based C++ map carried the Rust lead that remains once the fill is
# deferred, the flat-map arm would close it.
#
# Run on the 30 September 2026 host (AMD EPYC 7443P, pin 2-17, nohz_full 2-17)
# inside the Rocky image:
#   docker/run.sh --cpuset 2-17 exec -- bench/probe_sg_flatmap.sh 2-17 112000 10
#
# The arguments follow overload_probes.sh (--preload, --max-run-s 3), not
# campaign.sh, so its kops/s are not comparable with a campaign row. Only the
# order of the arms inside one session is. Output goes to
# results-probes-20260930-sg/, where refresh_thesis.sh never looks.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
PROBE="$here/results-probes-20260930-sg"
PIN="${1:-2-17}"
rate="${2:-112000}"
repeats="${3:-10}"
stamp=$(date +%Y%m%d-%H%M%S)
out="$PROBE/probe-sg-flatmap-${rate}-${stamp}.jsonl"
: > "$out"
pre=()
command -v taskset >/dev/null && pre=(taskset -c "$PIN")
cmake -S "$root/cpp" -B "$root/docker/.scratch/cpp-build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$root/docker/.scratch/cpp-build" --target bench >/dev/null
cmake -S "$root/cpp" -B "$root/docker/.scratch/cpp-build-flat" -G Ninja -DCMAKE_BUILD_TYPE=Release -DUECM_FLAT_MAP=ON >/dev/null
cmake --build "$root/docker/.scratch/cpp-build-flat" --target bench >/dev/null
cargo build --release --manifest-path "$root/rust/Cargo.toml" --example bench >/dev/null
rustbin="$root/rust/target/release/examples/bench"
ops=$(( rate * 3 ))
warmup=$(( rate * 1 ))
for rep in $(seq 1 "$repeats"); do
  for arm in cpp-stock cpp-flat rust-stock; do
    case "$arm" in
      cpp-stock) bin="$root/docker/.scratch/cpp-build/bench" ;;
      cpp-flat)  bin="$root/docker/.scratch/cpp-build-flat/bench" ;;
      rust-stock) bin="$rustbin" ;;
    esac
    line=$("${pre[@]}" "$bin" --workload mixed --shards 7 --producers 7 \
      --active-ues 5000 --preload 5000 --seed 42 --run-id "$rep" --json \
      --ops "$ops" --warmup "$warmup" --rate "$rate" --max-run-s 3 \
      --correction-when after 2>/dev/null)
    python3 -c 'import json,sys; r=json.loads(sys.argv[1]); r["arm"]=sys.argv[2]; r["repeat"]=int(sys.argv[3]); print(json.dumps(r))' "$line" "$arm" "$rep" >> "$out"
  done
  echo "rep $rep/$repeats"
done
python3 - "$out" <<'PY'
import json, statistics, sys
from collections import defaultdict
rows=[json.loads(l) for l in open(sys.argv[1])]
by=defaultdict(list)
for r in rows:
    by[r["arm"]].append(r["throughput_ops_s"])
print("== flat-map interleaved summary ==")
for arm in sorted(by):
    print(f"  {arm}: median {statistics.median(by[arm]) / 1000:.1f} kops/s")
cpp=statistics.median(by["cpp-stock"])
flat=statistics.median(by["cpp-flat"])
rust=statistics.median(by["rust-stock"])
print(f"  Rust/C++ stock: {rust/cpp:.3f}")
print(f"  Rust/C++ flat:  {rust/flat:.3f}")
print(f"  C++ flat/stock: {flat/cpp:.3f}")
PY
echo "wrote $out"
