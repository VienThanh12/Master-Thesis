#!/usr/bin/env bash
# In-flight timing and queue-swap probes on the reported campaign host.
#
# Run ON THE HOST (not inside the container) of the bare-metal AMD EPYC 7443P
# machine that produced
# bench/results-20260924-jaybird/campaign-20260924-083351.jsonl. Every
# measurement goes through docker/run.sh with the campaign's pin, so the
# toolchain is the campaign's container image. The environment is captured
# both outside and inside the container, as the campaigns do.
#
# Neither run joins the campaign's Holm family. The in-flight load is frozen by
# the capacity rule in bench/pipeline_mixed_facts.py before any confirmatory
# run, not chosen by which language looks better.
#
# On a further host, pass --tag <yyyymmdd>-<hostname>. The results then go to
# bench/results-pipeline-<tag> and bench/results-probes-<tag>, which the macro
# generators never read unless told to. The default tag, campaign-jaybird, is
# the one they do read, so it is refused on any machine whose root disk is not
# the campaign host's.
#
# Besides the two follow-ups, the session runs three mechanism probes, none of
# them a reported arm: the one-slot reply channel in the in-flight test
# (pipeline_pilot.sh --reply), the same swap past saturation on the deferred
# clock (reply_probes.sh), and kernel calls per request (futex_counts.sh).
#
# Usage (on the host, from the repo root):
#   bench/run_campaign_followups.sh                      # the campaign host only
#   bench/run_campaign_followups.sh --pin 2-17 --tag 20261019-killdeer
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
pin="2-17"
tag="campaign-jaybird"
while [ $# -gt 0 ]; do
  case "$1" in
    --pin) pin="$2"; shift 2;;
    --tag) tag="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

die() { echo "run_campaign_followups: $*" >&2; exit 1; }

# Root filesystem of the machine that wrote campaign-20260924-083351.jsonl, from
# its environment capture. A reinstall changes it, which is the point.
campaign_root_uuid="ccd82249-6338-4a04-b462-b211d137efbe"
if [ "$tag" = "campaign-jaybird" ]; then
  grep -q "root=UUID=$campaign_root_uuid" /proc/cmdline ||
    die "this is not the campaign host, so its results must not be filed as campaign-jaybird. Pass --tag <yyyymmdd>-<hostname>."
else
  case "$tag" in
    *campaign*) die "--tag must not contain 'campaign' on a further host";;
  esac
  [[ "$tag" =~ ^[A-Za-z0-9._-]+$ ]] || die "--tag may hold letters, digits, dot, dash and underscore only"
fi

grep -q 'EPYC 7443' /proc/cpuinfo 2>/dev/null ||
  die "need the campaign host (AMD EPYC 7443P), this is$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-)"
[ -f /.dockerenv ] && die "run this on the host. It starts the container itself."
grep -qw isolcpus /proc/cmdline &&
  die "isolcpus is set. It disables load balancing on the pinned set. Remove it."
grep -q "nohz_full=$pin" /proc/cmdline ||
  echo "WARNING: /proc/cmdline has no nohz_full=$pin. The campaign ran with it." >&2
boost=/sys/devices/system/cpu/cpufreq/boost
if [ -r "$boost" ] && [ "$(cat "$boost")" != 0 ]; then
  die "frequency boost is on. The campaign ran with boost off."
fi
if grep -q 'Thread(s) per core:[[:space:]]*2' <(lscpu); then
  die "SMT is on. The campaign ran with SMT off."
fi

pipeline_rel="bench/results-pipeline-$tag"
probe_rel="bench/results-probes-$tag"
env_name="campaign"
[ "$tag" = "campaign-jaybird" ] || env_name="$(hostname -s)"
pipeline_dir="$root/$pipeline_rel"
probe_dir="$root/$probe_rel"
for d in "$pipeline_dir" "$probe_dir"; do
  if [ -d "$d" ] && [ -n "$(ls -A "$d")" ]; then
    die "$d is not empty. Move it aside so an old log cannot be picked as newest."
  fi
  mkdir -p "$d"
done

in_container() { "$root/docker/run.sh" --cpuset "$pin" exec -- "$@"; }

newest_env() { ls -t "$here/results"/env-*.txt | head -1; }

echo "== environment, outside the container =="
"$here/capture_env.sh" >/dev/null
host_env="$(newest_env)"
cp "$host_env" "$pipeline_dir/env-host-$env_name.txt"
cp "$host_env" "$probe_dir/$(basename "$host_env")"

echo "== environment, inside the container =="
"$root/docker/run.sh" --cpuset "$pin" env >/dev/null
container_env="$(newest_env)"
[ "$container_env" != "$host_env" ] || die "container env capture did not write a new file"
cp "$container_env" "$pipeline_dir/env-container-$env_name.txt"
cp "$container_env" "$probe_dir/container-$(basename "$container_env" | sed 's/^env-//')"
rm -f "$container_env"

capacity_rates="112000 224000 336000 448000 560000 672000"
echo "== mixed capacity sweep (one interleaved pass per rate) =="
in_container bench/pipeline_pilot.sh --workload mixed --repeats 1 \
  --rates "$capacity_rates" --shards 7 --producers 7 --pin "$pin" \
  --out-dir "$pipeline_rel" | tee "$pipeline_dir/pipeline-mixed-capacity.log"

capacity_log="$(ls -t "$pipeline_dir"/pipeline-mixed-*.jsonl | grep -v '\.hist\.' | head -1)"
frozen_rate="$(python3 - "$capacity_log" <<'PY'
import json, sys
ORDER = ("cpp-system", "rust-system", "cpp-jemalloc", "rust-jemalloc")
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
grouped = {}
for row in rows:
    grouped.setdefault(int(row["rate"]), {})[f"{row['lang']}-{row['alloc']}"] = row
for rate in sorted(grouped):
    items = grouped[rate]
    if set(items) != set(ORDER):
        raise SystemExit(f"capacity rate {rate} is missing a variant")
    if all(r["completed_within_window"] / r["planned"] < 0.99 for r in items.values()):
        print(rate)
        raise SystemExit(0)
raise SystemExit("no capacity rate makes all four variants fall behind")
PY
)"
echo "   frozen per-producer rate: $frozen_rate" | tee -a "$pipeline_dir/pipeline-mixed-capacity.log"

echo "== signal confirmatory (20 interleaved repeats) =="
in_container bench/pipeline_pilot.sh --workload signal --repeats 20 \
  --rates "$frozen_rate" --shards 7 --producers 7 --pin "$pin" \
  --out-dir "$pipeline_rel" | tee "$pipeline_dir/pipeline-signal-confirm.log"

echo "== mixed confirmatory (20 interleaved repeats) =="
in_container bench/pipeline_pilot.sh --workload mixed --repeats 20 \
  --rates "$frozen_rate" --shards 7 --producers 7 --pin "$pin" \
  --out-dir "$pipeline_rel" | tee "$pipeline_dir/pipeline-mixed-confirm.log"

echo "== queue swap (deferred fill, no perf context-switch counting) =="
stamp="$(date +%Y%m%d-%H%M%S)"
console="$probe_dir/probe-sg-queue-nocount-112000-$stamp.console.txt"
in_container bench/queue_probes.sh --shards 7 --producers 7 --rate 112000 \
  --repeats 10 --pin "$pin" --correction-when after | tee "$console"
latest_queue="$(ls -t "$here/results"/queue_probes-*.jsonl | head -1)"
mv "$latest_queue" "$probe_dir/probe-sg-queue-nocount-112000-$stamp.jsonl"

echo "== reply-handle swap, in flight (10 interleaved repeats per workload) =="
for workload in signal mixed; do
  in_container bench/pipeline_pilot.sh --reply --workload "$workload" --repeats 10 \
    --rates "$frozen_rate" --shards 7 --producers 7 --pin "$pin" \
    --out-dir "$pipeline_rel" | tee "$pipeline_dir/pipeline-reply-$workload.log"
done

echo "== reply-handle swap past saturation (deferred fill, 10 interleaved repeats) =="
stamp="$(date +%Y%m%d-%H%M%S)"
reply_console="$probe_dir/reply_probes-112000-$stamp.console.txt"
in_container bench/reply_probes.sh --shards 7 --producers 7 --rate 112000 \
  --repeats 10 --pin "$pin" --correction-when after | tee "$reply_console"
latest_reply="$(ls -t "$here/results"/reply_probes-*.jsonl | head -1)"
mv "$latest_reply" "$probe_dir/reply_probes-112000-$stamp.jsonl"

echo "== kernel calls per request (bpftrace on the host, separate from the timing runs) =="
if command -v bpftrace >/dev/null 2>&1 && [ "$(id -u)" = 0 ]; then
  "$here/futex_counts.sh" --pin "$pin" --rate 112000 --repeats 3 --out-dir "$probe_dir" ||
    echo "   futex_counts.sh failed. The timing results above are unaffected."
else
  echo "   skipped: needs bpftrace and root on the host"
fi

(cd "$root" && sha256sum "$pipeline_rel"/* > "$pipeline_dir/SHA256SUMS" &&
  sha256sum "$probe_rel"/* > "$probe_dir/SHA256SUMS")

refused=0
for c in "$console" "$reply_console"; do
  if grep -q 'REFUSING TO CERTIFY' "$c"; then
    echo
    echo "$(basename "$c"): not in overload or metastable. Do not quote it."
    echo "Read it, raise --rate, and rerun that probe alone."
    refused=1
  fi
done

echo
if [ "$tag" = "campaign-jaybird" ]; then
  echo "run_campaign_followups: done. Copy both directories back, then run:"
  echo "  bench/refresh_thesis.sh"
else
  echo "run_campaign_followups: done on a further host ($tag)."
  echo "Copy $pipeline_rel and $probe_rel back. The macro generators do not read"
  echo "them, so the thesis numbers are unchanged until THESIS_PIPELINE_DIR or"
  echo "THESIS_SG_DIR points at them, and any sentence using them says a further host."
fi
exit "$refused"
