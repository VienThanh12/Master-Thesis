#!/usr/bin/env bash
# Readiness check for a containerised campaign, run inside the container.
#
# bench/setup_testbed.sh answers "is this host quiet enough to measure on". This
# answers the question a container adds: "does the container hand the host's
# behaviour through, or does it stand in the way". Three of the checks below are
# specific to that and are the reason this script exists:
#
#   * a CPU quota (cgroup cpu.max) throttles the container at period boundaries,
#     and a throttled period is a multi-millisecond stall that lands directly in
#     p99.9. Docker's --cpus sets exactly that, which is why docker/run.sh pins
#     cores with --cpuset-cpus and never with --cpus.
#   * seccomp filtering puts a BPF program in front of every syscall. The handoff
#     under measurement is futex-heavy, so the filter is on the measured path. It
#     costs both languages the same and does not bias the comparison, but it does
#     move the absolute numbers, so it is recorded rather than assumed away.
#   * a memory limit makes the kernel reclaim inside the container, and peak RSS
#     is a reported result (RQ3).
#
# Exit status is 0 when nothing blocking was found, 1 otherwise, so it can gate a
# scripted run.
set -uo pipefail

RED=$'\033[31m'; GREEN=$'\033[32m'; YEL=$'\033[33m'; RST=$'\033[0m'
fails=0; warns=0
say()  { printf '%s\n' "$*"; }
ok()   { printf '  %s[ ok ]%s %s\n' "$GREEN" "$RST" "$*"; }
warn() { printf '  %s[warn]%s %s\n' "$YEL"   "$RST" "$*"; warns=$((warns+1)); }
bad()  { printf '  %s[FAIL]%s %s\n' "$RED"   "$RST" "$*"; fails=$((fails+1)); }
info() { printf '  %s[info]%s %s\n' ""       ""     "$*"; }

# cgroup v2 puts the container's own limits at /sys/fs/cgroup when the container
# has its own cgroup namespace, which is Docker's default. v1 spreads them over
# per-controller directories, so both layouts are tried before a check is
# reported as unavailable.
cg_read() {  # cg_read <v2-name> <v1-controller/v1-name>
  local v2="/sys/fs/cgroup/$1" v1="/sys/fs/cgroup/$2"
  if [ -r "$v2" ]; then cat "$v2"; elif [ -r "$v1" ]; then cat "$v1"; else echo ""; fi
}

cap_has() {  # cap_has <bit>
  local eff bit="$1"
  eff="$(sed -n 's/^CapEff:\s*//p' /proc/self/status 2>/dev/null)"
  [ -n "$eff" ] || return 1
  [ $(( (0x$eff >> bit) & 1 )) -eq 1 ]
}

say "== image =="
if [ -r /etc/uecm-image.txt ]; then
  sed 's/^/  /' /etc/uecm-image.txt
else
  bad "/etc/uecm-image.txt missing: this is not the measurement image"
fi

say
say "== container =="
in_container=0
if [ -f /.dockerenv ] || [ -f /run/.containerenv ] || [ "${UECM_IN_CONTAINER:-0}" = "1" ]; then
  in_container=1
fi
if [ "$in_container" = "1" ]; then
  ok "running in a container (expected)"
else
  warn "no container detected: this script is meant to run inside the image"
fi

cpumax="$(cg_read cpu.max cpu/cpu.cfs_quota_us)"
case "$cpumax" in
  "")        warn "cgroup cpu limit not readable; cannot confirm the absence of a quota";;
  "max "*)   ok "no CPU quota (cpu.max = $cpumax)";;
  "-1")      ok "no CPU quota (cfs_quota_us = -1)";;
  *)         bad "CPU QUOTA SET (cpu.max = $cpumax). Throttled periods land in p99.9."
             bad "  Re-run with --cpuset-cpus and without --cpus / --cpu-quota.";;
esac

cpuset="$(cg_read cpuset.cpus.effective cpuset/cpuset.cpus)"
if [ -n "$cpuset" ]; then
  info "cpuset: $cpuset"
  ncpu="$(python3 - "$cpuset" <<'PY'
import sys
spec = sys.argv[1].strip()
n = 0
for part in spec.split(","):
    if not part:
        continue
    if "-" in part:
        a, b = part.split("-")
        n += int(b) - int(a) + 1
    else:
        n += 1
print(n)
PY
)"
  # The campaign runs N_SHARDS + producers threads, 16 at the documented
  # settings, and TESTBED.md asks for at least that many cores reserved.
  if [ "${ncpu:-0}" -ge 16 ]; then
    ok "$ncpu cores in the cpuset (16 or more: shards + producers fit)"
  elif [ "${ncpu:-0}" -ge 8 ]; then
    warn "$ncpu cores in the cpuset: fewer than the 16 threads the documented settings run"
  else
    bad "$ncpu core(s) in the cpuset: the campaign will contend with itself"
  fi
else
  warn "cpuset not readable; cannot confirm which cores this container may use"
fi

memmax="$(cg_read memory.max memory/memory.limit_in_bytes)"
case "$memmax" in
  ""|"max"|"9223372036854771712") ok "no memory limit (peak RSS is not reclaim-shaped)";;
  *) warn "memory limit set ($memmax): reclaim inside the container perturbs peak RSS (RQ3)";;
esac

seccomp="$(sed -n 's/^Seccomp:\s*//p' /proc/self/status 2>/dev/null)"
case "$seccomp" in
  0) ok "seccomp disabled (no syscall filter on the measured path)";;
  2) warn "seccomp filter active: a BPF program runs on every syscall, including the"
     warn "  handoff futexes. Equal across arms, but absolute latencies shift."
     warn "  docker/run.sh --seccomp off removes it.";;
  *) info "seccomp mode: ${seccomp:-unknown}";;
esac

# Capabilities are reported, not judged. docker/run.sh runs the container as the
# invoking user so that everything written into the bind-mounted repository is
# owned by that user, and a non-root uid has an empty *effective* capability set
# however many --cap-add flags were passed: they land in the bounding set and go
# no further without file or ambient capabilities. Neither thing the campaign
# wants from that set actually needs them, and both are tested directly instead:
# SCHED_FIFO is reachable through RLIMIT_RTPRIO, and perf can self-monitor at
# perf_event_paranoid 2 or lower.
caps=""
cap_has 23 && caps="$caps SYS_NICE"
cap_has 38 && caps="$caps PERFMON"
cap_has 21 && caps="$caps SYS_ADMIN"
info "effective capabilities:${caps:- none (expected when running as a non-root uid)}"
info "rtprio limit: $(ulimit -Hr 2>/dev/null || echo unknown) (SCHED_FIFO without CAP_SYS_NICE)"

# The cgroup can refuse a real-time class even when the limit and the capability
# both allow it, so this is tested rather than inferred.
if command -v chrt >/dev/null 2>&1; then
  if chrt -f 1 true 2>/dev/null; then ok "SCHED_FIFO works (campaign.sh --rt is available)"
  else warn "SCHED_FIFO refused. cgroup v2 keeps real-time tasks out of non-root cgroups,"
       warn "  so --rt may need the campaign run outside a container."; fi
else
  warn "chrt not found: --rt unavailable"
fi

say
say "== toolchain =="
for t in g++ cargo rustc cmake ninja python3 taskset; do
  if command -v "$t" >/dev/null 2>&1; then ok "$t: $("$t" --version 2>&1 | head -1)"
  else bad "missing $t"; fi
done
if python3 -c 'import matplotlib' 2>/dev/null; then ok "matplotlib importable"
else warn "matplotlib missing: plots skipped, aggregation still works"; fi
if command -v jeprof >/dev/null 2>&1; then ok "jeprof present (alloc_profile.sh can symbolise)"
else bad "jeprof missing: bench/alloc_profile.sh would need --raw-ok"; fi
je="$(ldconfig -p 2>/dev/null | sed -n 's/.*libjemalloc\.so\.2 .*=> //p' | head -1)"
if [ -n "$je" ]; then ok "system jemalloc: $je"
else bad "system jemalloc missing: the C++ jemalloc arm cannot link"; fi

say
say "== counters =="
if ! command -v perf >/dev/null 2>&1; then
  bad "perf missing"
else
  ok "perf: $(perf --version 2>&1 | head -1)"
  paranoid="$(cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || echo unknown)"
  info "kernel.perf_event_paranoid = $paranoid (needs 2 or lower, set on the host)"
  if [ -d /sys/bus/event_source/devices/cpu ] || [ -d /sys/bus/event_source/devices/cpu_core ]; then
    ok "hardware PMU exposed"
    if perf stat -x, -e cycles true >/dev/null 2>&1; then
      ok "perf stat -e cycles works: bench/counters.sh can run for real"
    else
      warn "PMU present but 'perf stat -e cycles' failed. Check paranoid level and"
      warn "  CAP_PERFMON, and note this image's perf is the EL8 build while the host"
      warn "  kernel may be much newer. bench/counters.sh --software still exercises"
      warn "  the plumbing."
    fi
  else
    warn "no hardware PMU: counters.sh will refuse hardware events (correctly)."
    warn "  This is what a virtualised or WSL2 kernel looks like from inside."
  fi
fi

say
say "== host, seen through the container =="
info "kernel: $(uname -r)"
virt="$(lscpu 2>/dev/null | sed -n 's/^Hypervisor vendor: *//p')"
[ -z "$virt" ] && virt="(none reported by lscpu)"
info "hypervisor vendor: $virt"
if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  bad "host kernel is WSL2: not testbed-grade for RQ1/RQ3 whatever the container does"
elif [ "$virt" != "(none reported by lscpu)" ]; then
  warn "host is virtualised ($virt): the far tail below saturation stays unresolved."
  warn "  The container does not change this. See bench/TESTBED.md."
else
  ok "no hypervisor reported: this looks like bare metal"
fi
gov="$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo '(not exposed)')"
info "cpu0 governor: $gov"
isol="$(sed -n 's/.*isolcpus=\([^ ]*\).*/\1/p' /proc/cmdline 2>/dev/null)"
info "isolcpus: ${isol:-(none)}"
thp="$(sed -n 's/.*\[\(.*\)\].*/\1/p' /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null)"
info "transparent hugepages: ${thp:-(not exposed)} (the campaign pins thp:never in jemalloc)"

say
say "== repository mounts =="
if [ -x bench/campaign.sh ]; then ok "repository mounted at $(pwd)"
else bad "bench/campaign.sh not found in $(pwd): the repository is not mounted here"; fi
for d in bench/results cpp rust; do
  if [ -w "$d" ] 2>/dev/null; then ok "writable: $d"
  elif [ -d "$d" ]; then bad "not writable by uid $(id -u): $d"
  else warn "missing: $d"; fi
done
# The build trees are bind-mounted aside on purpose: a CMake cache records the
# absolute path of its compiler, so a tree configured on the host with
# /usr/bin/g++ and reused here against the toolset compiler makes CMake refuse to
# build rather than silently mixing toolchains.
for d in cpp/build cpp/build-jemalloc rust/target bench/.bin; do
  if awk -v t="/$d" '$5 ~ t"$" {found=1} END{exit !found}' /proc/self/mountinfo 2>/dev/null; then
    ok "separate build mount: $d"
  else
    warn "$d is not a separate mount: host and container builds will collide"
  fi
done

say
if [ "$fails" -gt 0 ]; then
  printf '%sNOT READY%s: %d blocking issue(s), %d warning(s).\n' "$RED" "$RST" "$fails" "$warns"
  exit 1
elif [ "$warns" -gt 0 ]; then
  printf '%sREADY (with caveats)%s: %d warning(s). Read them before quoting anything.\n' \
    "$YEL" "$RST" "$warns"
else
  printf '%sREADY%s: container is not standing in the way of the measurement.\n' "$GREEN" "$RST"
fi
say "A container does not make a virtualised host bare metal. What it fixes is the"
say "toolchain and the missing tools, not the scheduler."
exit 0
