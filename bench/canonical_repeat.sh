#!/usr/bin/env bash
# The canonical-configuration bare-metal repeat.
#
# The 26 August 2026 visit changed five things at once: the host, the shard
# count, the load grid, the repeat count and the toolchain. Four of those were
# accidents of following the TESTBED.md example rather than the campaign, and
# together they confine that dataset to corroborating the main sweep instead of
# replacing it. This script exists so the same accident cannot happen twice.
#
# It reads the design out of the canonical campaign record and replays it. Shard
# count, producer count, load grid, repeat count, duration and warm-up are
# derived, never typed, so the only way this run can differ from the main sweep
# is in the machine it runs on and the isolation applied to it. The toolchain is
# held by the container image, which is the Rocky/g++ 15/rustc 1.97 combination
# the guest campaign used.
#
# Usage, in this order:
#   bench/canonical_repeat.sh plan       # print the derived design, change nothing
#   bench/canonical_repeat.sh isolate    # kernel core isolation, then REBOOT
#   bench/canonical_repeat.sh run        # hygiene, build, campaign, counters, profile
#
# `isolate` needs a reboot to take effect, so it is a separate subcommand rather
# than a step inside `run`. Everything else is one command on purpose: the
# expensive failure mode of a rented box is discovering at the end that a tool
# was missing at the start.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"

#: The main sweep. Every table in the thesis reports this campaign, so it is the
#: design a replacement has to match.
CANONICAL="$here/results/campaign-20260812-154528.jsonl"

#: Cores handed to the benchmark. Matches the pinned set of the confirmation
#: visit, and leaves 0-1 and 18-23 to the system. With 7 shards and 7 producers
#: the run needs 14, so 16 is comfortable without spilling onto a second die.
PIN="2-17"

GREEN=$'\033[32m'; YEL=$'\033[33m'; RED=$'\033[31m'; RST=$'\033[0m'
say()  { printf '%s\n' "$*"; }
ok()   { printf '  %s[ ok ]%s %s\n' "$GREEN" "$RST" "$*"; }
warn() { printf '  %s[warn]%s %s\n' "$YEL"   "$RST" "$*"; }
die()  { printf '  %s[FAIL]%s %s\n' "$RED"   "$RST" "$*"; exit 1; }

# --------------------------------------------------------------------------- #
# The design, read out of the record rather than restated here.
# --------------------------------------------------------------------------- #
derive() {
  [ -f "$CANONICAL" ] || die "no canonical record at $CANONICAL"
  python3 - "$CANONICAL" <<'PY'
import json, statistics, sys

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
rates = sorted({int(r["rate"]) for r in rows})
variants = {(r["lang"], r["alloc"]) for r in rows}
shards = {r["shards"] for r in rows}
producers = {r["producers"] for r in rows}
if len(shards) != 1 or len(producers) != 1:
    sys.exit("canonical record mixes shard or producer counts; not a single design")

# Duration and warm-up are not fields. Each run sends rate*duration operations
# per producer and reports both its total wall time and its measured phase, so
# both fall out of the record exactly.
duration = statistics.median(r["ops_total"] / (r["rate"] * r["producers"]) for r in rows)
warmup = statistics.median(r["wall_s"] - r["measured_wall_s"] for r in rows)

print(f"SHARDS={shards.pop()}")
print(f"PRODUCERS={producers.pop()}")
print(f"REPEATS={len(rows) // (len(rates) * len(variants))}")
print(f"DURATION={round(duration)}")
print(f"WARMUP={round(warmup)}")
print(f"RATES='{' '.join(str(r) for r in rates)}'")
print(f"LEVELS={len(rates)}")
print(f"TOTAL={len(rows)}")
PY
}

load_design() {
  local spec
  spec="$(derive)" || exit 1
  eval "$spec"
  # The representative load is where the thesis reports peak RSS, so it is where
  # the allocation profile has to be taken. Derived from the same grid.
  PROFILE_RATE=8000
  case " $RATES " in *" $PROFILE_RATE "*) ;;
    *) die "profile rate $PROFILE_RATE is not one of the swept levels: $RATES";;
  esac
}

cmd_plan() {
  load_design
  say "Canonical design, derived from $(basename "$CANONICAL"):"
  say "  shards / producers : $SHARDS / $PRODUCERS"
  say "  load levels        : $LEVELS"
  say "  repeats            : $REPEATS"
  say "  duration / warm-up : ${DURATION}s / ${WARMUP}s"
  say "  rates (per prod.)  : $RATES"
  say "  total runs         : $TOTAL"
  say "  pinned cores       : $PIN"
  say "  profile rate       : $PROFILE_RATE per producer"
  say
  say "Held by the container image, not by this host: g++ and rustc."
  say "Changed on purpose against the main sweep: the machine, and core isolation."
}

# --------------------------------------------------------------------------- #
# Kernel tickless configuration.
#
# `isolcpus` is deliberately NOT set here, and the reason cost a campaign.
# bench/TESTBED.md used to recommend it for the cleanest tails, which it does
# deliver, but it also removes those CPUs from every scheduling domain. The
# benchmark pins its threads to a *set* with `taskset -c 2-17` and relies on the
# kernel to spread them, so with no load balancing all fourteen threads inherit
# the first allowed CPU and stay there. The 27 August 2026 campaign ran all 1120
# runs on cpu2 alone, at a flat 100.1% of one core, and nothing in it was usable.
# `nohz_full` and `rcu_nocbs` give the tick and callback benefits without
# touching load balancing, so those are what this sets. Isolating properly would
# need per-thread affinity inside the benchmark, which is a code change.
# --------------------------------------------------------------------------- #
cmd_isolate() {
  [ "$(id -u)" -eq 0 ] || die "run this as root"
  local params="nohz_full=$PIN rcu_nocbs=$PIN"
  local grub=/etc/default/grub
  [ -f "$grub" ] || die "no $grub; set $params on the kernel command line by hand"
  cp "$grub" "$grub.bak-canonical-repeat"
  # Strip any isolcpus this host already carries, including one an earlier run of
  # this script added before the defect was understood.
  if grep -q 'isolcpus=' "$grub"; then
    sed -i 's/ *isolcpus=[^ "]*//g' "$grub"
    warn "removed isolcpus from $grub: it disables load balancing on the pinned set"
  fi
  if grep -q "nohz_full=$PIN" "$grub"; then
    ok "$grub already carries $params"
  else
    sed -i "s/^GRUB_CMDLINE_LINUX_DEFAULT=\"\(.*\)\"/GRUB_CMDLINE_LINUX_DEFAULT=\"\1 $params\"/" "$grub"
    ok "added to $grub: $params"
  fi
  update-grub >/dev/null 2>&1 || grub-mkconfig -o /boot/grub/grub.cfg >/dev/null 2>&1 \
    || die "could not regenerate the grub config"
  ok "grub config regenerated"
  say
  if grep -q 'isolcpus=' /proc/cmdline; then
    say "${YEL}REBOOT REQUIRED${RST}: this kernel still has isolcpus active."
  fi
  say "${YEL}REBOOT NOW${RST}, then run: bench/canonical_repeat.sh run"
}

# --------------------------------------------------------------------------- #
# The guard that should have existed before the first attempt. Runs one short
# high-rate run and checks that the work actually landed on more than one core.
# Costs about half a minute and is the difference between losing that and losing
# two and a half hours.
# --------------------------------------------------------------------------- #
cmd_check_spread() {
  load_design
  local top; top="$(printf '%s' "$RATES" | tr ' ' '\n' | sort -n | tail -1)"
  say "== pre-flight: does the work spread across the pinned cores? =="
  if grep -q 'isolcpus=' /proc/cmdline; then
    die "isolcpus is active on this kernel ($(sed -n 's/.*\(isolcpus=[^ ]*\).*/\1/p' /proc/cmdline)).
       Load balancing is off on those cores and every benchmark thread will pile
       onto one of them. Run 'isolate' to strip it, reboot, and try again."
  fi
  # --smoke sends the probe's records to docker/.scratch/smoke-results, so this
  # cannot leave a two-run campaign as the newest file in bench/results, which
  # is one refresh_thesis.sh away from regenerating every quoted number from it.
  local scratch="$root/docker/.scratch/smoke-results"
  rm -f "$scratch"/campaign-*.jsonl 2>/dev/null
  "$root/docker/run.sh" --cpuset "$PIN" --smoke --no-log campaign \
      --shards "$SHARDS" --producers "$PRODUCERS" --repeats 1 \
      --rates "$top" --duration 6 --warmup-s 1 --active-ues 5000 >/dev/null 2>&1
  # campaign-*.jsonl also matches the campaign-*.hist.jsonl sidecar, which
  # carries buckets and no cpu_pct, so it has to be filtered out by name.
  local probe
  probe="$(ls -1t "$scratch"/campaign-*.jsonl 2>/dev/null \
           | grep -v '\.hist\.jsonl$' | head -1)"
  if [ -z "$probe" ]; then
    die "the probe run produced no records; fix that before spending two hours"
  fi
  # cpu_pct is summed over cores, so it reports how many the run really used.
  local worst
  worst="$(grep -oE '"cpu_pct":[0-9.]+' "$probe" | cut -d: -f2 | sort -n | tail -1)"
  if [ -z "$worst" ]; then
    warn "could not read cpu_pct from $probe; check it by hand"
    return 0
  fi
  say "  highest cpu_pct in the probe: ${worst}% (100% = one core)"
  if [ "${worst%%.*}" -lt 150 ]; then
    die "the run used about one core. Threads are not spreading across $PIN, so a
       full campaign here would measure the scheduler and not the service."
  fi
  ok "work spread over roughly $(( ${worst%%.*} / 100 )) cores or more"
}

# --------------------------------------------------------------------------- #
# Everything else, in the order that fails cheaply first.
# --------------------------------------------------------------------------- #
cmd_run() {
  load_design
  cmd_plan
  say

  say "== 1. host hygiene =="
  "$here/setup_testbed.sh" --no-install || warn "setup_testbed reported problems, read them"
  # perf_event_paranoid defaults to 4 on Ubuntu 24.04, which blocks counters.sh
  # entirely. Found the hard way on the 26 August visit.
  if [ "$(id -u)" -eq 0 ]; then
    sysctl -w kernel.perf_event_paranoid=1 >/dev/null && ok "perf_event_paranoid = 1"
  else
    sudo sysctl -w kernel.perf_event_paranoid=1 >/dev/null && ok "perf_event_paranoid = 1"
  fi
  if grep -q "isolcpus=" /proc/cmdline; then
    die "isolcpus is active. It disables load balancing on the pinned set, which
       put all 1120 runs of the 27 August campaign on a single core. Run
       'bench/canonical_repeat.sh isolate' to strip it, then reboot."
  fi
  if grep -q "nohz_full=" /proc/cmdline; then
    ok "tickless: $(sed -n 's/.*\(nohz_full=[^ ]*\).*/\1/p' /proc/cmdline)"
  else
    warn "no nohz_full on the kernel command line; tails will be slightly noisier"
  fi

  say
  say "== 2. container image (this is what holds the toolchain) =="
  "$root/docker/run.sh" build || die "image build failed"
  "$root/docker/run.sh" check || warn "readiness check raised issues, read them before quoting"

  # Both of these have failed at the end of a visit before. Failing here costs
  # minutes; failing after the campaign costs the visit.
  say
  say "== 3. tool checks, before the long run =="
  "$root/docker/run.sh" counters --software || warn "perf counters unavailable"
  "$root/docker/run.sh" alloc-profile --check || warn "allocation profiling unavailable"
  # Blocking, and the most important check here. A campaign whose threads sit on
  # one core produces 1120 records that all look plausible in isolation.
  cmd_check_spread

  say
  say "== 4. the campaign: $TOTAL runs, roughly two hours =="
  # docker/run.sh takes its own options *before* the subcommand and passes
  # everything after it through untouched. Putting --cpuset on the right of
  # `campaign` sends it to campaign.sh, which rejects it, and leaves the
  # container on its default cpuset of every core but 0-1. Both halves of that
  # are silent until the run has already started on the wrong cores.
  "$root/docker/run.sh" --cpuset "$PIN" campaign \
      --shards "$SHARDS" --producers "$PRODUCERS" \
      --repeats "$REPEATS" --duration "$DURATION" --warmup-s "$WARMUP" \
      --active-ues 5000 --rates "$RATES" || die "campaign failed"

  say
  say "== 5. counters and allocation profile, same visit =="
  "$root/docker/run.sh" --cpuset "$PIN" counters --repeats 10 \
    || warn "counters failed"
  # At a swept load, not closed loop. The 26 August profile ran unthrottled,
  # landed past the saturation plateau, and reversed the sign of the peak-RSS
  # difference it was collected to explain, so it could attribute nothing.
  "$root/docker/run.sh" --cpuset "$PIN" alloc-profile \
      --shards "$SHARDS" --producers "$PRODUCERS" \
      --rate "$PROFILE_RATE" || warn "allocation profile failed"

  say
  say "== 6. verify the histograms persisted, while a re-run is still possible =="
  local newest
  newest="$(ls -1t "$here"/results/campaign-*.hist.jsonl 2>/dev/null | head -1)"
  if [ -n "$newest" ]; then
    python3 "$here/pool_hist.py" "$newest" --verify "${newest%.hist.jsonl}.jsonl" \
      && ok "histograms verified against the printed percentiles" \
      || warn "histogram verification failed: do not leave the host yet"
  else
    warn "no histogram sidecar found, which means p99.99 is not recoverable"
  fi

  say
  say "Done. Copy bench/results/ off this machine before terminating it."
  say "Then, on the laptop: move the new campaign into bench/results-baremetal/,"
  say "point baremetal_facts.py at it, and run bench/refresh_thesis.sh."
}

case "${1:-}" in
  plan)         cmd_plan;;
  isolate)      cmd_isolate;;
  check-spread) cmd_check_spread;;
  run)          cmd_run;;
  *) sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2;;
esac
