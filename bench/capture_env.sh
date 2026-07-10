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
  command -v g++    >/dev/null && g++ --version   | head -1
  command -v clang++>/dev/null && clang++ --version| head -1
  command -v rustc  >/dev/null && rustc --version
  command -v cargo  >/dev/null && cargo --version
  command -v cmake  >/dev/null && cmake --version  | head -1
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

  echo "## Warnings"
  warned=0
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
