#!/usr/bin/env bash
# One cycle-sampled profile per language, to test the task-clock profiles for sampling bias.
set -euo pipefail
p="$(cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.." && pwd)/docker/.scratch/prof"
for arm in cpp-deque rust-channel; do
  bash "$p/profile_in.sh" "$arm" 7 4 32768 cycles
  cd "$p/out"
  perf script -i "in-perf-$arm-7.data" --inline -F tid,time,period,ip,sym,symoff,dso 2>/dev/null \
    | python3 "$p/resolve_inline.py" "$p/bin/pf-$arm" > "resolved-$arm-7.txt"
  PERIOD_SCALE=0.350877 python3 "$p/classify.py" "in-bench-$arm-7.json" "$arm-cycles" "cprof-$arm-7.json" \
    kallsyms.txt "own code|UE operation,own code|harness" < "resolved-$arm-7.txt" > "cprof-$arm-7.txt"
  gzip -f "resolved-$arm-7.txt"
  cat "cprof-$arm-7.txt"
  cd - >/dev/null
done
echo CYCLES-DONE
