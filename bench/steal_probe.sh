#!/usr/bin/env bash
# CPU steal on the measurement guest, sampled across a window rather than a moment.
#
# WHY THIS EXISTS. Section 7.5 names non-zero CPU steal as a mechanism behind the
# unresolved far tail, and Table 7.x quotes it at roughly 10 ms of vCPU time per
# second. Nothing in bench/results/ backs that. `capture_env.sh` samples steal once
# per session over a single second, every environment record on file reports zero
# ticks, and no record carries its [STEAL] warning. The number was written from
# expectation rather than from data.
#
# A one-second sample also cannot settle the question either way. It is usually
# taken before the campaign starts, when the guest is idle and the host has no
# reason to deschedule it, so a zero says almost nothing about what happens under
# load. Steal is a property of contention, and contention is what the benchmark
# creates. So the measurement has to run *while the benchmark runs*, which is what
# this does, and it is why `capture_env.sh` was left alone rather than extended:
# its job is a snapshot of the configuration, not a time series.
#
# WHAT IT MEASURES. Field 9 of each per-CPU line in /proc/stat is the time the
# hypervisor spent running something other than this vCPU. Sampling it per core
# matters, because the claim is about the cores the benchmark is pinned to, and an
# aggregate over all sixteen would divide a stall on one pinned core by the fifteen
# that were idle. Both the mean and the worst interval are reported: a tail argument
# rests on the worst, and a mean over a quiet window will hide it.
#
# WHERE IT RUNS. On the virtualised guest, where the question is open. On bare metal
# steal is structurally zero and the script says so rather than pretending to
# measure. Under WSL2 /proc/stat reports the field but the value is not meaningful.
#
# OUTPUT. A JSON artefact in bench/results/, so whatever the thesis ends up saying
# about steal is generated from a file rather than typed from memory. That is the
# rule the current claim broke.
#
# Usage:
#   bench/steal_probe.sh --duration 60                 # sample for 60 s
#   bench/steal_probe.sh -- bench/campaign.sh --repeats 20 ...   # sample for the run
#   bench/steal_probe.sh --cpus 2-15 --interval 1 --duration 300
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
mkdir -p "$here/results"

# Defaults track campaign.sh: those are the cores whose steal the tail claim is about.
cpus="2-15"
interval=1
duration=60
out=""
cmd=()

while [ $# -gt 0 ]; do
  case "$1" in
    --cpus)      cpus="$2"; shift 2;;
    --all-cpus)  cpus="all"; shift;;
    --interval)  interval="$2"; shift 2;;
    --duration)  duration="$2"; shift 2;;
    --out)       out="$2"; shift 2;;
    --)          shift; cmd=("$@"); break;;
    -h|--help)   sed -n '1,36p' "$0"; exit 0;;
    *) echo "unknown argument: $1" >&2; exit 2;;
  esac
done

ts="$(date +%Y%m%d-%H%M%S)"
[ -n "$out" ] || out="$here/results/steal-$ts.json"

# ---------------------------------------------------------------- preconditions
virt="$(systemd-detect-virt --vm 2>/dev/null | head -1)"
[ -z "$virt" ] && virt="none"
if [ "$virt" = "none" ]; then
  echo "NOTE: systemd-detect-virt reports no hypervisor."
  echo "  On bare metal there is nothing to steal this machine's cores: the counter"
  echo "  exists but no hypervisor increments it. Measuring here answers a question"
  echo "  that only has content on the guest. Proceeding anyway, expect zero."
fi
if ! grep -qE '^cpu0 ' /proc/stat 2>/dev/null; then
  echo "ERROR: /proc/stat has no per-CPU lines. Cannot measure." >&2
  exit 1
fi

# A tick is 1/CLK_TCK of a second. capture_env.sh hardcodes 10 ms, which is right
# on every configuration seen so far and wrong in principle.
clk="$(getconf CLK_TCK 2>/dev/null || echo 100)"
[ "$clk" -gt 0 ] 2>/dev/null || clk=100
ms_per_tick="$(awk -v c="$clk" 'BEGIN{printf "%.6f", 1000.0/c}')"

# Expand "2-15,20" into a comma list of ids, so the sampler can test membership.
expand_cpus() {
  local spec="$1" part lo hi i acc=""
  if [ "$spec" = "all" ]; then
    acc="$(awk '/^cpu[0-9]+ /{print substr($1,4)}' /proc/stat | paste -sd, -)"
    printf '%s' "$acc"; return
  fi
  local IFS=','
  for part in $spec; do
    case "$part" in
      *-*) lo="${part%%-*}"; hi="${part##*-}"
           for ((i=lo; i<=hi; i++)); do acc="$acc,$i"; done;;
      *)   acc="$acc,$part";;
    esac
  done
  printf '%s' "${acc#,}"
}
cpu_sel="$(expand_cpus "$cpus")"
ncpus="$(awk -v s="$cpu_sel" 'BEGIN{print split(s, a, ",")}')"
if [ "$ncpus" -eq 0 ]; then
  echo "ERROR: --cpus '$cpus' selected no CPUs." >&2
  exit 2
fi

# ---------------------------------------------------------------------- sampling
# One line per selected core: "cpuN <steal ticks>".
read_steal() {
  awk -v sel="$cpu_sel" '
    BEGIN { n = split(sel, a, ","); for (i = 1; i <= n; i++) want[a[i]] = 1 }
    /^cpu[0-9]+ / { id = substr($1, 4); if (id in want) print $1, $9 }
  ' /proc/stat
}

raw="$(mktemp)"
trap 'rm -f "$raw"' EXIT

child=""
if [ "${#cmd[@]}" -gt 0 ]; then
  echo "== sampling steal on cores $cpus for the lifetime of: ${cmd[*]}"
  "${cmd[@]}" &
  child=$!
else
  echo "== sampling steal on cores $cpus for ${duration}s"
fi

declare -A prev
while read -r name ticks; do prev[$name]=$ticks; done < <(read_steal)

start_ns="$(date +%s%N)"
last_ns="$start_ns"
while :; do
  sleep "$interval"
  now_ns="$(date +%s%N)"
  # Real elapsed time, not the requested interval: `sleep 1` under load is not 1 s,
  # and dividing by the nominal value would overstate the rate on exactly the busy
  # intervals this exists to catch.
  elapsed_s="$(awk -v a="$last_ns" -v b="$now_ns" 'BEGIN{printf "%.6f", (b-a)/1e9}')"
  sum=0; worst=0
  while read -r name ticks; do
    d=$(( ticks - ${prev[$name]:-0} ))
    [ "$d" -lt 0 ] && d=0
    prev[$name]=$ticks
    sum=$(( sum + d ))
    [ "$d" -gt "$worst" ] && worst=$d
  done < <(read_steal)
  printf '%s %d %d\n' "$elapsed_s" "$sum" "$worst" >> "$raw"
  last_ns="$now_ns"

  if [ -n "$child" ]; then
    kill -0 "$child" 2>/dev/null || break
  else
    total_s="$(awk -v a="$start_ns" -v b="$now_ns" 'BEGIN{printf "%d", (b-a)/1e9}')"
    [ "$total_s" -ge "$duration" ] && break
  fi
done

rc=0
if [ -n "$child" ]; then wait "$child"; rc=$?; fi

# --------------------------------------------------------------------- reporting
host="$(uname -n)"
kernel="$(uname -r)"
awk -v mspt="$ms_per_tick" -v ncpus="$ncpus" -v cpus="$cpus" -v host="$host" \
    -v kernel="$kernel" -v virt="$virt" -v clk="$clk" -v out="$out" -v ts="$ts" '
{
  n++
  wall += $1
  ticks += $2
  if ($2 > 0) busy++
  # Worst single core in this interval, as a rate: a 20 ms stall inside a 1 s
  # sample and inside a 4 s sample are not the same disturbance.
  rate = $3 * mspt / $1
  if (rate > worst_rate) worst_rate = rate
  if ($3 > worst_ticks) worst_ticks = $3
}
END {
  if (n == 0) { print "ERROR: no intervals sampled." > "/dev/stderr"; exit 1 }
  stolen_ms = ticks * mspt
  # Milliseconds of vCPU time lost per core per second of wall clock, which is the
  # unit the thesis claim is stated in.
  mean_rate = stolen_ms / ncpus / wall

  printf "{\n" > out
  printf "  \"timestamp\": \"%s\",\n", ts > out
  printf "  \"host\": \"%s\",\n", host > out
  printf "  \"kernel\": \"%s\",\n", kernel > out
  printf "  \"virtualisation\": \"%s\",\n", virt > out
  printf "  \"cpus\": \"%s\",\n", cpus > out
  printf "  \"n_cpus\": %d,\n", ncpus > out
  printf "  \"clk_tck\": %d,\n", clk > out
  printf "  \"intervals\": %d,\n", n > out
  printf "  \"intervals_with_steal\": %d,\n", busy > out
  printf "  \"wall_seconds\": %.3f,\n", wall > out
  printf "  \"steal_ticks_total\": %d,\n", ticks > out
  printf "  \"steal_ms_total\": %.3f,\n", stolen_ms > out
  printf "  \"mean_ms_per_core_per_s\": %.4f,\n", mean_rate > out
  printf "  \"worst_core_interval_ms_per_s\": %.4f,\n", worst_rate > out
  printf "  \"worst_core_interval_ticks\": %d\n", worst_ticks > out
  printf "}\n" > out

  printf "\n== CPU steal over %d interval(s), %.1f s of wall clock, %d core(s) [%s]\n",
         n, wall, ncpus, cpus
  printf "  intervals showing any steal : %d of %d\n", busy, n
  printf "  total vCPU time stolen      : %.1f ms (%d ticks)\n", stolen_ms, ticks
  printf "  mean per core               : %.4f ms/s\n", mean_rate
  printf "  worst single core, one interval: %.4f ms/s\n", worst_rate
  printf "\n"
  if (ticks == 0) {
    printf "VERDICT: no steal observed on these cores over this window.\n"
    printf "  A claim that steal is non-zero is not supported by this run. Either drop it\n"
    printf "  or repeat this under the load that is supposed to provoke it. Note that a\n"
    printf "  quiet window does not prove a quiet host, so say what was measured.\n"
  } else {
    printf "VERDICT: steal is non-zero on these cores.\n"
    printf "  Quote the measured rate from this file through a generated macro, never by\n"
    printf "  transcribing it. Compare the worst-interval figure against the latency being\n"
    printf "  claimed: the mean is the wrong statistic for a tail argument.\n"
  }
  printf "\nwrote %s\n", out
}
' "$raw"

exit "$rc"
