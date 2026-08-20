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

  # A containerised run's toolchain belongs to the image, not to the host, and
  # the image records its own manifest at build time (docker/Dockerfile). Copying
  # it in here is what lets a result produced in a container be traced back to
  # the exact compiler that produced it. Absent outside the container.
  if [ -r /etc/uecm-image.txt ]; then
    echo "## Container image"
    cat /etc/uecm-image.txt
    echo
  fi

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
  #
  # The hypervisor is asked for specifically (--vm) rather than by the bare
  # `systemd-detect-virt`, which reports the innermost layer: inside a container
  # on a KVM guest it answers "docker" and the kvm provenance disappears from the
  # record. Containerisation is a separate fact and gets its own line below.
  # systemd-detect-virt prints "none" *and* exits 1 when it finds nothing, so its
  # output is read directly instead of through `|| echo none`, which appended a
  # second "none" to the value.
  sdv() {  # sdv --vm|--container
    local out
    out="$(systemd-detect-virt "$1" 2>/dev/null | head -1)"
    printf '%s' "${out:-none}"
  }
  if command -v systemd-detect-virt >/dev/null 2>&1; then
    virt="$(sdv --vm)"
  else
    virt=""
  fi
  if [ -z "$virt" ] || [ "$virt" = "none" ]; then
    if command -v lscpu >/dev/null 2>&1 && lscpu | grep -qi 'hypervisor vendor'; then
      virt="$(lscpu | sed -n 's/^Hypervisor vendor: *//p' | tr 'A-Z' 'a-z')"
    fi
  fi
  [ -z "$virt" ] && virt="unknown"
  echo "virtualisation: ${virt:-none}"

  # Containerisation. A container shares the host kernel, so nothing above this
  # line changes when the campaign moves into one: the scheduler, the
  # clocksource, the governor and the hypervisor are the host's either way. What
  # does change is the toolchain (recorded above) and what the cgroup permits,
  # which is the next four lines. A CPU bandwidth quota is the dangerous one: a
  # throttled period is a stall of milliseconds, and it lands in p99.9.
  # The runtime's own marker file is checked before systemd-detect-virt, which
  # misses Docker on this distribution: with a cgroup namespace /proc/1/cgroup
  # reads "0::/" and Docker sets no container= in PID 1's environment, so the
  # detector has nothing to go on and answers "none" from inside a container.
  if   [ -f /.dockerenv ];        then container="docker"
  elif [ -f /run/.containerenv ]; then container="podman"
  elif grep -qE '(docker|containerd|libpod|kubepods)' /proc/1/cgroup 2>/dev/null; then
    container="container"
  elif command -v systemd-detect-virt >/dev/null 2>&1; then
    container="$(sdv --container)"
  else
    container="none"
  fi
  echo "container: $container"
  cg() {  # cg <cgroup-v2-path> <cgroup-v1-path>
    if   [ -r "/sys/fs/cgroup/$1" ]; then cat "/sys/fs/cgroup/$1"
    elif [ -r "/sys/fs/cgroup/$2" ]; then cat "/sys/fs/cgroup/$2"
    fi
  }
  cpu_quota="$(cg cpu.max cpu/cpu.cfs_quota_us)"
  mem_limit="$(cg memory.max memory/memory.limit_in_bytes)"
  cg_cpuset="$(cg cpuset.cpus.effective cpuset/cpuset.cpus)"
  seccomp="$(sed -n 's/^Seccomp:[[:space:]]*//p' /proc/self/status 2>/dev/null)"
  echo "cgroup cpu quota: ${cpu_quota:-(not exposed)}"
  echo "cgroup memory limit: ${mem_limit:-(not exposed)}"
  echo "cgroup cpuset: ${cg_cpuset:-(not exposed)}"
  echo "seccomp mode: ${seccomp:-(unknown)} (0 = off, 2 = filter on every syscall)"
  # What this process was allowed to run on. Recorded because it is the effect of
  # --cpuset-cpus and of any outer taskset, and because campaign.sh applies its
  # own --pin to the benchmark binary only, not to this capture.
  echo "cpus allowed here: $(sed -n 's/^Cpus_allowed_list:[[:space:]]*//p' /proc/self/status 2>/dev/null)"
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

  echo "## Allocator"
  # The jemalloc arm only isolates the language from the allocator if the
  # allocator itself is held fixed, and its footprint answers to the arena count
  # and to the host's hugepage policy as much as to the program. Both are
  # recorded so a footprint can be compared against another run's.
  echo "system jemalloc: $( (ldconfig -p 2>/dev/null | sed -n 's/.*libjemalloc\.so\.2 .*=> //p' | head -1) || echo '(not installed)')"
  echo "MALLOC_CONF (C++ jemalloc): ${MALLOC_CONF:-(unset -- allocator defaults)}"
  echo "_RJEM_MALLOC_CONF (Rust jemalloc): ${_RJEM_MALLOC_CONF:-(unset -- allocator defaults)}"
  thp="$(sed -n 's/.*\[\(.*\)\].*/\1/p' /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null)"
  echo "transparent hugepages: ${thp:-(not exposed)}"
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
  if [ "$container" != "none" ]; then
    echo "  [CONTAINER] Running inside a container ($container). The toolchain is the"
    echo "              image's and is recorded above, but the kernel is the host's:"
    echo "              scheduler, clocksource, governor and hypervisor are unchanged,"
    echo "              so a container does not make a virtualised host bare metal."
    warned=1
  fi
  case "$cpu_quota" in
    ""|"max "*|"-1") ;;
    *)
      echo "  [QUOTA] A CPU bandwidth quota is in force ($cpu_quota). The cgroup throttles"
      echo "          at every period boundary it exhausts, and a throttled period is a"
      echo "          stall of milliseconds landing straight in p99.9. Pin cores"
      echo "          (--cpuset-cpus) instead of capping bandwidth (--cpus)."
      warned=1;;
  esac
  case "$mem_limit" in
    ""|"max"|"9223372036854771712") ;;
    *)
      echo "  [MEMLIMIT] A memory limit is in force ($mem_limit). Peak RSS is a reported"
      echo "             result, and under a limit it measures reclaim as well as the"
      echo "             program."
      warned=1;;
  esac
  if [ "$seccomp" = "2" ]; then
    echo "  [SECCOMP] A seccomp filter is active: a BPF program runs on every syscall,"
    echo "            including the handoff futexes on the measured path. It costs both"
    echo "            languages the same, so the paired comparison holds, but absolute"
    echo "            latencies are not comparable with an unfiltered run."
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
