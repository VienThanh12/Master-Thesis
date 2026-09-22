#!/usr/bin/env bash
# One new host, two clocks, same kernel. That is the visit that isolates
# coordinated-omission fill timing.
#
# The 27 August campaign (AMD EPYC 7443, nohz_full=2-17, fill during the timed
# window) cannot be re-run: that machine is gone. The September probes (7443P,
# no nohz_full, fill after) therefore mixed host and kernel with fill timing.
# A later sweep on a *third* host with only the corrected clock would mix
# again. The only design that changes one thing is both clocks, one box,
# one pin, one kernel command line, one Rocky image, one visit.
#
# Clock 1 is the reported instrument: intended origin, fill at record, cap
# 10 000. Prefix campaign-*.jsonl.
# Clock 2 is Clock B: same origin and cap, fill after the timed window. Prefix
# fair-after-*.jsonl, so refresh_thesis.sh cannot promote it.
# Clock A (start origin, cap 0) is omitted. Its percentiles are coordinated-
# omission biased by construction and it is not what deleted the 1.7x / 2.8x
# throughput gaps.
#
# This visit does not replace campaign-20260827-151927. Copy the logs off the
# box, then decide. Do not run bench/refresh_thesis.sh while the new
# campaign-*.jsonl is the newest file in bench/results/.
#
# Usage, on the rented bare-metal host, in this order:
#   bench/same_host_clocks.sh plan
#   sudo bench/canonical_repeat.sh isolate    # writes nohz_full, strips isolcpus
#   reboot
#   bench/same_host_clocks.sh run             # ~5 h after the image is built
#
# Host to rent: dedicated bare metal, no hypervisor, at least 24 cores so that
# pin 2-17 still has 16 CPUs after SMT is turned off. Prefer AMD EPYC 7443P,
# the SKU of the September probes and the 26 August confirmation. Ubuntu is
# fine. Root is required for grub. Never set isolcpus.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
PIN="2-17"

GREEN=$'\033[32m'; YEL=$'\033[33m'; RED=$'\033[31m'; RST=$'\033[0m'
say()  { printf '%s\n' "$*"; }
ok()   { printf '  %s[ ok ]%s %s\n' "$GREEN" "$RST" "$*"; }
warn() { printf '  %s[warn]%s %s\n' "$YEL"   "$RST" "$*"; }
die()  { printf '  %s[FAIL]%s %s\n' "$RED"   "$RST" "$*"; exit 1; }

cmd_plan() {
  say "Same-host two-clock visit. Design is derived, not typed:"
  "$here/canonical_repeat.sh" plan
  say
  say "This visit then runs a second 1120-run sweep on the same box:"
  say "  clock 1  campaign instrument   fill during the timed window"
  say "  clock 2  Clock B               fill after the timed window"
  say "  pin      $PIN"
  say "  kernel   nohz_full=$PIN rcu_nocbs=$PIN   (never isolcpus)"
  say "  image    Rocky gcc-toolset-15 / rustc 1.97.1"
  say
  say "Rent a dedicated bare-metal box, no hypervisor:"
  say "  cores    24 or more (after SMT off, $PIN still needs 16)"
  say "  sku      AMD EPYC 7443P if the vendor still has it"
  say "  access   root (grub) and Docker"
  say "  time     reboot, then about five hours of compute"
  say
  say "Do not mix this visit with the 27 August 7443 or the September 7443P"
  say "probes. The comparison that isolates fill timing is clock 1 versus"
  say "clock 2 on *this* host."
}

refuse_wrong_kernel() {
  if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
    die "this kernel is WSL2. Headline numbers need a bare-metal Linux host."
  fi
  if command -v systemd-detect-virt >/dev/null 2>&1; then
    local virt
    virt="$(systemd-detect-virt --vm 2>/dev/null | head -1)"
    [ -z "$virt" ] && virt="none"
    if [ "$virt" != "none" ]; then
      die "this host is a $virt guest. Rent dedicated metal, not a VM."
    fi
  fi
  if grep -q "isolcpus=" /proc/cmdline; then
    die "isolcpus is active. It disables load balancing on the pinned set.
       Run: sudo bench/canonical_repeat.sh isolate
       then reboot. A campaign on this kernel measures one core."
  fi
  if grep -q "nohz_full=" /proc/cmdline; then
    ok "tickless: $(sed -n 's/.*\(nohz_full=[^ ]*\).*/\1/p' /proc/cmdline)"
  else
    die "no nohz_full on the kernel command line. That is the kernel half of
       the mix we are here to remove. Run: sudo bench/canonical_repeat.sh isolate
       then reboot, then run this again."
  fi
}

cmd_run() {
  refuse_wrong_kernel
  "$here/canonical_repeat.sh" plan
  say

  say "== 1. host hygiene =="
  "$here/setup_testbed.sh" --no-install || warn "setup_testbed reported problems, read them"
  if [ "$(id -u)" -eq 0 ]; then
    sysctl -w kernel.perf_event_paranoid=1 >/dev/null && ok "perf_event_paranoid = 1"
  else
    sudo sysctl -w kernel.perf_event_paranoid=1 >/dev/null && ok "perf_event_paranoid = 1"
  fi

  say
  say "== 2. environment capture on the host, outside the container =="
  # The 27 August capture written inside the container recorded Rocky as the
  # distro of an Ubuntu machine. Keep a host-side capture in the same session
  # so plot_figures.py can split those.
  if [ -x "$here/capture_env.sh" ]; then
    "$here/capture_env.sh" || warn "host capture_env failed"
  fi

  say
  say "== 3. container image (holds the toolchain) =="
  "$root/docker/run.sh" build || die "image build failed"
  "$root/docker/run.sh" check || warn "readiness check raised issues, read them before quoting"

  say
  say "== 4. spread check, before spending five hours =="
  "$here/canonical_repeat.sh" check-spread

  say
  say "== 5. clock 1 of 2: campaign instrument, fill during the timed window =="
  say "    1120 runs, about two hours. Prefix campaign-*.jsonl."
  "$root/docker/run.sh" --cpuset "$PIN" campaign \
      --shards 7 --producers 7 --repeats 20 --duration 3 --warmup-s 1 \
      --active-ues 5000 \
      --rates "1000 2000 4000 8000 12000 16000 24000 32000 40000 48000 56000 64000 80000 112000" \
      || die "campaign clock failed"

  say
  say "== 6. clock 2 of 2: Clock B, fill after the timed window =="
  say "    1120 runs, about two hours. Prefix fair-after-*.jsonl."
  "$root/docker/run.sh" --cpuset "$PIN" exec -- \
      bench/fair_latency_sweep.sh --pin "$PIN" --clocks after \
      || die "Clock B failed"

  say
  say "== 7. verify both histogram sidecars, while a re-run is still possible =="
  local camp hist
  camp="$(ls -1t "$here"/results/campaign-*.jsonl 2>/dev/null \
          | grep -v '\.hist\.jsonl$' | head -1)"
  hist="$(ls -1t "$here"/results/campaign-*.hist.jsonl 2>/dev/null | head -1)"
  if [ -n "$hist" ] && [ -n "$camp" ]; then
    python3 "$here/pool_hist.py" "$hist" --verify "$camp" \
      && ok "campaign histograms verified" \
      || warn "campaign histogram verification failed: do not leave the host yet"
  else
    warn "no campaign histogram sidecar, so p99.99 is not recoverable"
  fi
  local after after_hist
  after="$(ls -1t "$here"/results/fair-after-*.jsonl 2>/dev/null \
          | grep -v '\.hist\.jsonl$' | head -1)"
  after_hist="$(ls -1t "$here"/results/fair-after-*.hist.jsonl 2>/dev/null | head -1)"
  if [ -n "$after_hist" ] && [ -n "$after" ]; then
    python3 "$here/pool_hist.py" "$after_hist" --verify "$after" \
      && ok "Clock B histograms verified" \
      || warn "Clock B histogram verification failed: do not leave the host yet"
  else
    warn "no Clock B histogram sidecar"
  fi

  say
  say "Done. Copy all of bench/results/ off this machine before terminating it."
  say "Keep the new campaign-*.jsonl out of the live bench/results/ on the laptop"
  say "until you decide whether it replaces campaign-20260827-151927. A"
  say "refresh_thesis.sh run takes the newest campaign-*.jsonl and would rewrite"
  say "every quoted number. Clock B is already safe: fair-after-*.jsonl is not"
  say "that glob."
}

case "${1:-}" in
  plan) cmd_plan;;
  run)  cmd_run;;
  *) sed -n '2,34p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2;;
esac
