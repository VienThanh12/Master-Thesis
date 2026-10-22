#!/usr/bin/env bash
# More cycle-sampled repeats, interleaved, then re-classifies every cycle-sampled profile.
set -euo pipefail
p="$(cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.." && pwd)/docker/.scratch/prof"
record() {
  bash "$p/profile_in.sh" "$1" "$2" 4 32768 cycles
  (cd "$p/out" && perf script -i "in-perf-$1-$2.data" --inline -F tid,time,period,ip,sym,symoff,dso 2>/dev/null \
    | python3 "$p/resolve_inline.py" "$p/bin/pf-$1" | gzip > "resolved-$1-$2.txt.gz")
}
for rep in 8 9; do
  for arm in rust-oneshot cpp-deque rust-channel; do record "$arm" "$rep"; done
done
record rust-oneshot 7
cd "$p/out"
for f in resolved-*-[789].txt.gz; do
  base="${f#resolved-}"; base="${base%.txt.gz}"
  arm="${base%-*}"; rep="${base##*-}"
  zcat "$f" | PERIOD_SCALE=0.350877 python3 "$p/classify.py" "in-bench-$arm-$rep.json" "$arm-$rep" \
    "cprof-$arm-$rep.json" kallsyms.txt "own code|UE operation" > "cprof-$arm-$rep.txt"
  head -12 "cprof-$arm-$rep.txt"
done
echo CYCLES2-DONE
