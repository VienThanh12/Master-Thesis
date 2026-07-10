#!/usr/bin/env bash
# One-command testbed provisioning for the RQ1/RQ3 measurement campaign.
#
# Brings a fresh bare-metal Linux box to a measurement-ready state:
#   1. installs the build/analysis toolchain (g++, rustc/cargo, cmake+ninja, matplotlib);
#   2. applies CPU hygiene from TESTBED.md (performance governor, turbo off, SMT off);
#   3. verifies the result with capture_env.sh and prints a GREEN/RED readiness check.
#
# Usage:
#   bench/setup_testbed.sh              # install toolchain + apply hygiene + check
#   bench/setup_testbed.sh --check      # only verify readiness (no changes)
#   bench/setup_testbed.sh --no-install # apply hygiene + check, skip package install
#   bench/setup_testbed.sh --no-tune    # install + check, skip CPU hygiene
#
# CPU-hygiene steps need root; the script re-invokes the relevant bits with sudo.
# It is a no-op-with-warning under WSL2 (the controls are not exposed there).
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"

do_install=1
do_tune=1
check_only=0
for a in "$@"; do
  case "$a" in
    --check)      check_only=1;;
    --no-install) do_install=0;;
    --no-tune)    do_tune=0;;
    -h|--help)    sed -n '2,18p' "$0"; exit 0;;
    *) echo "unknown arg: $a"; exit 2;;
  esac
done

RED=$'\033[31m'; GREEN=$'\033[32m'; YEL=$'\033[33m'; RST=$'\033[0m'
say()  { printf '%s\n' "$*"; }
ok()   { printf '  %s[ ok ]%s %s\n'   "$GREEN" "$RST" "$*"; }
warn() { printf '  %s[warn]%s %s\n'   "$YEL"   "$RST" "$*"; }
bad()  { printf '  %s[FAIL]%s %s\n'   "$RED"   "$RST" "$*"; }

is_wsl() { grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; }

# ---------------------------------------------------------------------------
# 1. Toolchain
# ---------------------------------------------------------------------------
install_toolchain() {
  say "== [1/3] Installing toolchain =="
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y build-essential g++ cmake ninja-build python3 python3-pip \
      linux-tools-common "linux-tools-$(uname -r)" 2>/dev/null || \
      sudo apt-get install -y build-essential g++ cmake ninja-build python3 python3-pip
  else
    warn "no apt-get; install g++, cmake, ninja, python3 with your package manager"
  fi

  if ! command -v cargo >/dev/null 2>&1; then
    say "  installing Rust via rustup ..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    # shellcheck disable=SC1091
    . "$HOME/.cargo/env" 2>/dev/null || true
  fi

  python3 -m pip install --user --break-system-packages -r "$here/requirements.txt" 2>/dev/null || \
    python3 -m pip install --user -r "$here/requirements.txt" || \
    warn "matplotlib install failed; plots will be skipped (aggregation still works)"
}

# ---------------------------------------------------------------------------
# 2. CPU hygiene (root). See TESTBED.md §2.
# ---------------------------------------------------------------------------
apply_hygiene() {
  say "== [2/3] Applying CPU hygiene (needs root) =="
  if is_wsl; then
    warn "WSL2 detected: governor/turbo/SMT are not exposed here. Skipping."
    warn "Run this on bare-metal Linux for testbed-grade numbers."
    return
  fi

  # performance governor
  if ls /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1; then
    for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
      echo performance | sudo tee "$f" >/dev/null
    done
    ok "governor -> performance"
  else
    warn "cpufreq governor not exposed (VM?); skipping"
  fi

  # disable turbo/boost (intel_pstate or generic cpufreq)
  if [ -w /sys/devices/system/cpu/intel_pstate/no_turbo ] || \
     [ -e /sys/devices/system/cpu/intel_pstate/no_turbo ]; then
    echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo >/dev/null && ok "intel turbo -> off"
  elif [ -e /sys/devices/system/cpu/cpufreq/boost ]; then
    echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost >/dev/null && ok "cpufreq boost -> off"
  else
    warn "no turbo/boost control exposed; disable it in BIOS if possible"
  fi

  # disable SMT / hyper-threading
  if [ -e /sys/devices/system/cpu/smt/control ]; then
    echo off | sudo tee /sys/devices/system/cpu/smt/control >/dev/null && ok "SMT -> off"
  else
    warn "SMT control not exposed; disable hyper-threading in BIOS if measuring per-core"
  fi
}

# ---------------------------------------------------------------------------
# 3. Readiness check
# ---------------------------------------------------------------------------
readiness() {
  say "== [3/3] Readiness check =="
  local fails=0 warns=0

  for t in g++ cargo cmake ninja python3; do
    if command -v "$t" >/dev/null 2>&1; then ok "found $t ($($t --version 2>/dev/null | head -1))"
    else bad "missing $t"; fails=$((fails+1)); fi
  done
  if python3 -c 'import matplotlib' 2>/dev/null; then ok "python matplotlib present"
  else warn "matplotlib missing (plots skipped; run: pip install --user -r bench/requirements.txt)"; warns=$((warns+1)); fi

  if is_wsl; then
    bad "running under WSL2 -> NOT testbed-grade (frequency/turbo/SMT unavailable)"
    fails=$((fails+1))
  else
    local gov="" turbo="" smt=""
    gov=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "?")
    if [ "$gov" = performance ]; then ok "governor = performance"
    else warn "governor = ${gov:-unknown} (want performance)"; warns=$((warns+1)); fi

    if [ -e /sys/devices/system/cpu/intel_pstate/no_turbo ]; then
      turbo=$(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null)
      if [ "$turbo" = 1 ]; then ok "turbo = off"; else warn "turbo = ON (want off)"; warns=$((warns+1)); fi
    elif [ -e /sys/devices/system/cpu/cpufreq/boost ]; then
      turbo=$(cat /sys/devices/system/cpu/cpufreq/boost 2>/dev/null)
      if [ "$turbo" = 0 ]; then ok "boost = off"; else warn "boost = ON (want off)"; warns=$((warns+1)); fi
    else warn "turbo/boost state unknown (check BIOS)"; warns=$((warns+1)); fi

    smt=$(cat /sys/devices/system/cpu/smt/control 2>/dev/null || echo "?")
    if [ "$smt" = off ] || [ "$smt" = notsupported ]; then ok "SMT = $smt"
    else warn "SMT = ${smt:-unknown} (want off for per-core measurement)"; warns=$((warns+1)); fi

    if command -v taskset >/dev/null 2>&1; then ok "taskset available (core pinning)"
    else warn "taskset missing (install util-linux) -- --pin will be ignored"; warns=$((warns+1)); fi
  fi

  say
  say "== capturing environment snapshot =="
  "$here/capture_env.sh" >/dev/null 2>&1 && ok "wrote bench/results/env-*.txt" || warn "env capture failed"

  say
  if [ "$fails" -gt 0 ]; then
    printf '%sNOT READY%s: %d blocking issue(s), %d warning(s).\n' "$RED" "$RST" "$fails" "$warns"
    say "Fix the [FAIL] items, then re-run: bench/setup_testbed.sh --check"
    return 1
  elif [ "$warns" -gt 0 ]; then
    printf '%sREADY (with caveats)%s: %d warning(s) -- results usable but not maximally clean.\n' "$YEL" "$RST" "$warns"
  else
    printf '%sREADY%s: toolchain present and CPU hygiene applied.\n' "$GREEN" "$RST"
  fi
  say "Next: taskset -c <cores> bench/campaign.sh --repeats 20 --pin <cores> --duration 3"
  return 0
}

# ---------------------------------------------------------------------------
if [ "$check_only" -eq 1 ]; then
  readiness; exit $?
fi
[ "$do_install" -eq 1 ] && install_toolchain
[ "$do_tune"    -eq 1 ] && apply_hygiene
readiness
