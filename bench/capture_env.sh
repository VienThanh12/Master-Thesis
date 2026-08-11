#!/usr/bin/env bash
# Capture the testbed environment for reproducibility (see TESTBED.md). Writes a
# text report to bench/results/env-<timestamp>.txt and echoes it. Flags WSL, an
# active turbo/on-demand governor, and other tail-latency risks so a run is not
# mistaken for testbed-grade data.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$here/results"
ts="$(date +%Y%m%d-%H%M%S)"
out="$here/results/env-$ts.txt"

{
  echo "# Testbed environment capture ($ts)"
  echo

  echo "## Host / OS"
  uname -a
  [ -r /etc/os-release ] && . /etc/os-release && echo "distro: ${PRETTY_NAME:-unknown}"
  echo

  echo "## Toolchains"
  # Report a missing tool rather than omitting its line. A silent omission is
  # indistinguishable from a tool that was never relevant, and a record that
  # simply lacks a rustc version does not describe the build that produced the
  # data beside it.
  ver() {
    if command -v "$1" >/dev/null 2>&1; then "$@" 2>/dev/null | head -1
    else echo "$1: (not found on PATH)"; fi
  }
  ver g++ --version
  command -v clang++ >/dev/null 2>&1 && clang++ --version | head -1
  ver rustc --version
  ver cargo --version
  ver cmake --version
  echo

  echo "## CPU"
  if command -v lscpu >/dev/null; then
    lscpu | grep -E 'Model name|^CPU\(s\)|Thread|Core|Socket|MHz|NUMA' || true
  fi
  echo

  echo "## Frequency governor / turbo / SMT"
  gov_files=(/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor)
  if [ -r "${gov_files[0]}" ]; then
    echo "governors: $(cat "${gov_files[@]}" 2>/dev/null | sort -u | paste -sd, -)"
  else
    echo "governors: (not exposed)"
  fi
  if [ -r /sys/devices/system/cpu/intel_pstate/no_turbo ]; then
    echo "intel_pstate/no_turbo: $(cat /sys/devices/system/cpu/intel_pstate/no_turbo)"
  else
    echo "intel_pstate/no_turbo: (not present)"
  fi
  [ -r /sys/devices/system/cpu/smt/control ] && \
    echo "smt/control: $(cat /sys/devices/system/cpu/smt/control)" || \
    echo "smt/control: (not exposed)"
  echo

  echo "## Virtualisation and core isolation"
  # A guest reports the governor and turbo controls as "not exposed" for the same
  # reason bare metal reports them as absent, so the two are indistinguishable
  # from the section above alone. They are not equivalent: under a hypervisor the
  # frequency state is host-controlled and a vCPU can be descheduled entirely.
  if command -v systemd-detect-virt >/dev/null 2>&1; then
    virt="$(systemd-detect-virt 2>/dev/null || echo none)"
  elif command -v lscpu >/dev/null 2>&1 && lscpu | grep -qi 'hypervisor vendor'; then
    virt="$(lscpu | sed -n 's/^Hypervisor vendor: *//p')"
  else
    virt="unknown"
  fi
  echo "virtualisation: ${virt:-none}"
  cmdline="$(cat /proc/cmdline 2>/dev/null || echo '')"
  echo "kernel cmdline: ${cmdline:-(unreadable)}"
  isolated="$(printf '%s' "$cmdline" | sed -n 's/.*isolcpus=\([^ ]*\).*/\1/p')"
  nohz="$(printf '%s' "$cmdline" | sed -n 's/.*nohz_full=\([^ ]*\).*/\1/p')"
  echo "isolcpus: ${isolated:-(none)}"
  echo "nohz_full: ${nohz:-(none)}"
  # Steal time is the one source of tail latency that cannot be addressed from
  # inside the guest, so it is sampled over a window rather than read cumulatively:
  # a long-lived host accumulates ticks that say nothing about this session.
  steal_a="$(awk '/^cpu /{print $9; exit}' /proc/stat 2>/dev/null || echo '')"
  sleep 1
  steal_b="$(awk '/^cpu /{print $9; exit}' /proc/stat 2>/dev/null || echo '')"
  steal_delta=""
  if [ -n "$steal_a" ] && [ -n "$steal_b" ]; then
    steal_delta=$(( steal_b - steal_a ))
    echo "steal ticks (1 s sample): $steal_delta"
  else
    echo "steal ticks (1 s sample): (unavailable)"
  fi
  echo

  echo "## Warnings"
  warned=0
  if [ "$virt" != "none" ] && [ "$virt" != "unknown" ]; then
    echo "  [VIRT] Running under virtualisation ($virt): the frequency governor and"
    echo "         turbo state are host-controlled and not observable from here, and"
    echo "         the hypervisor may deschedule a vCPU. This is not the bare-metal"
    echo "         host TESTBED.md specifies."
    warned=1
  fi
  if [ -z "$isolated" ]; then
    echo "  [NOISOL] No isolcpus= on the kernel command line: benchmark threads share"
    echo "           their cores with the rest of the system, and a lost timeslice"
    echo "           lands directly in p99."
    warned=1
  fi
  if [ -n "$steal_delta" ] && [ "$steal_delta" -gt 0 ] 2>/dev/null; then
    echo "  [STEAL] $steal_delta tick(s) of CPU steal in a 1 s sample (~$((steal_delta * 10)) ms of"
    echo "          vCPU time): the host descheduled this guest. Small in aggregate, but"
    echo "          the same order as the tail being measured. Quantify with 'vmstat 1 30'."
    warned=1
  fi
  if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
    echo "  [WSL] Running under WSL2: frequency/turbo/SMT hygiene unavailable and"
    echo "        tails are perturbed by the host. NOT testbed-grade for RQ1/RQ3."
    warned=1
  fi
  if [ -r "${gov_files[0]}" ] && cat "${gov_files[@]}" 2>/dev/null | grep -qv performance; then
    echo "  [GOV] A CPU governor is not 'performance' (frequency scaling active)."
    warned=1
  fi
  if [ -r /sys/devices/system/cpu/intel_pstate/no_turbo ] && \
     [ "$(cat /sys/devices/system/cpu/intel_pstate/no_turbo)" = "0" ]; then
    echo "  [TURBO] Turbo/boost is enabled (frequency jitter between runs)."
    warned=1
  fi
  [ "$warned" -eq 0 ] && echo "  none"
} | tee "$out"

echo
echo "wrote $out"
