#!/usr/bin/env bash
# Profiles one arm at the top load, recording and reading inside the campaign container
# so every library is at its native path. Disposable.
#   profile_in.sh <arm> <repeat> [seconds]
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
p=docker/.scratch/prof
arm="$1"
rep="$2"
secs="${3:-4}"
stack="${4:-8192}"
event="${5:-task-clock}"
if [ "$event" = cycles ]; then
  # Fixed period: one sample per 2.85 million cycles, 1 ms at the fixed 2.85 GHz clock.
  sampling=(-e cycles -c 2850000)
else
  sampling=(-e task-clock -F 999)
fi
mkdir -p "$p/out"
data="$p/out/in-perf-$arm-$rep.data"
json="$p/out/in-bench-$arm-$rep.json"
taskset -c 2-17 "$p/bin/pf-$arm" --workload mixed --shards 7 --producers 7 --active-ues 5000 \
  --preload 5000 --ops $(( 112000 * 30 )) --warmup 112000 --seed $(( 42 + rep )) --rate 112000 \
  --max-run-s 10 --correction-when after --json > "$json" 2>/dev/null &
bpid=$!
# Preload and warm-up take about 2 s at this rate. Sample inside the 10 s timed phase.
sleep 4
perf record -q "${sampling[@]}" --call-graph "dwarf,$stack" -p "$bpid" -o "$data" -- sleep "$secs" \
  2> "$p/out/in-perf-$arm-$rep.err" || true
wait "$bpid"
echo "recorded $arm rep $rep: $(stat -c %s "$data") bytes"
