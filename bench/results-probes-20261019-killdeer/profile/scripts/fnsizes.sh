#!/usr/bin/env bash
# Compares per-function code sizes of a profiling build against the measured build. Disposable.
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
p=docker/.scratch/prof
for arm in rust-channel rust-oneshot; do
  for which in "pf:$p/bin/pf-$arm" "fc:bench/.bin/fc-$arm"; do
    nm -S -C --defined-only "${which#*:}" | awk '$3 ~ /[tT]/' \
      | sed -E 's/::h[0-9a-f]{16}$//' \
      | awk '{size=$2; $1=$2=$3=""; sub(/^ +/, ""); print $0 "\t" size}' | sort > "/tmp/sizes-${which%%:*}-$arm.txt"
  done
  total=$(wc -l < "/tmp/sizes-pf-$arm.txt")
  diff_lines=$(diff "/tmp/sizes-pf-$arm.txt" "/tmp/sizes-fc-$arm.txt" | grep -c '^[<>]' || true)
  echo "$arm: $total functions, $diff_lines lines differ"
  diff "/tmp/sizes-pf-$arm.txt" "/tmp/sizes-fc-$arm.txt" | grep '^[<>]' | head -12 || true
  echo "  hot functions:"
  grep -E "worker_loop|ShardCore|Service::handle_signaling|mpmc" \
    "/tmp/sizes-pf-$arm.txt" | head -8 | sed 's/^/    pf  /' || true
done
