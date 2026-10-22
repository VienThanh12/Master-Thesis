#!/usr/bin/env bash
# Per-request allocation profile, by the difference of two run lengths. Disposable.
set -euo pipefail
p="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out="$p/allocs.jsonl"
: > "$out"
common=(--workload signal --shards 7 --producers 7 --preload 5000 --seed 42 --json)
for v in cpp-stock cpp-ring rust-stock rust-oneshot rust-mutexq; do
  for n in 20000 120000; do
    # One request per sender, sent back to back: the overload condition of the sweep.
    ALLOCPROBE_OUT="$out" ALLOCPROBE_LABEL="$v|bench|$n" LD_PRELOAD="$p/allocprobe.so" \
      "$p/bin/$v-bench" "${common[@]}" --warmup 20000 --ops "$n" > /dev/null
    # Several requests in flight per sender.
    ALLOCPROBE_OUT="$out" ALLOCPROBE_LABEL="$v|pipeline|$n" LD_PRELOAD="$p/allocprobe.so" \
      "$p/bin/$v-pipeline" "${common[@]}" --warmup 20000 --ops "$n" --rate 20000 \
      --drain-timeout-s 60 > /dev/null
    echo "done $v $n"
  done
done
