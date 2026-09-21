#!/usr/bin/env bash
# Fourteen-load fair-clock sweep. Same grid as campaign-20260827-151927.
# Compared pair untouched. Do not copy kops/s into gen_macros.tex.
#
# Clock A (--clocks start, default): one real sample per call, latency from the
# actual send, no 10 000-sample fill. That is the language comparison of tail
# delay. Prefix fair-start-*.jsonl, so refresh_thesis.sh cannot pick it up.
#
# Clock B (--clocks after): intended origin, fill after the timed loop. That is
# the send-plan question without charging the fill during the run. Prefix
# fair-after-*.jsonl.
#
# Usage, on the EPYC inside the Rocky image, pin 2-17, no isolcpus:
#   docker/run.sh --cpuset 2-17 exec -- bench/fair_latency_sweep.sh --pin 2-17
#   docker/run.sh --cpuset 2-17 exec -- bench/fair_latency_sweep.sh --pin 2-17 --clocks both
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

clocks="start"
repeats=20
pin=""
duration=3
warmup_s=1
# Per-producer rates of the reported 7/7 campaign. Offered load is 7 times these.
rates="1000 2000 4000 8000 12000 16000 24000 32000 40000 48000 56000 64000 80000 112000"

while [ $# -gt 0 ]; do
  case "$1" in
    --clocks)   clocks="$2"; shift 2;;
    --repeats)  repeats="$2"; shift 2;;
    --pin)      pin="$2"; shift 2;;
    --duration) duration="$2"; shift 2;;
    --warmup-s) warmup_s="$2"; shift 2;;
    --rates)    rates="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

case "$clocks" in
  start|after|both) ;;
  *) echo "unknown --clocks $clocks (start|after|both)"; exit 2;;
esac

n_rates=$(echo "$rates" | wc -w)
n_clocks=1
[ "$clocks" = "both" ] && n_clocks=2
total=$(( repeats * n_rates * 4 * n_clocks ))
# 1 s warmup + duration + a little process overhead, times two for the cap.
approx_min=$(( total * (warmup_s + duration + 2) / 60 ))
echo "== fair 14-load sweep: clocks=$clocks repeats=$repeats rates=$n_rates variants=4 =="
echo "   $total runs, on the order of ${approx_min} minutes once built"
echo "   compared pair unchanged. do not copy kops/s into gen_macros.tex"

run_clock() {
  local prefix="$1"; shift
  local pin_args=()
  [ -n "$pin" ] && pin_args=(--pin "$pin")
  "$here/campaign.sh" \
    --prefix "$prefix" \
    --workload mixed --shards 7 --producers 7 \
    --active-ues 5000 --preload 5000 \
    --repeats "$repeats" --duration "$duration" --warmup-s "$warmup_s" \
    --rates "$rates" \
    "${pin_args[@]}" \
    "$@"
}

case "$clocks" in
  start)
    run_clock fair-start --latency-origin start --correction-cap 0 ;;
  after)
    run_clock fair-after --correction-when after ;;
  both)
    run_clock fair-start --latency-origin start --correction-cap 0
    run_clock fair-after --correction-when after ;;
esac
