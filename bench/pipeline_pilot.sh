#!/usr/bin/env bash
# Engineering pilot for the multi-outstanding overload clock.
# --workload signal is the default. --workload mixed walks the lifecycle generator.
# Results use pipeline-* or pipeline-mixed-* and are never the canonical campaign.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

repeats=2
rates="112000"
duration=1
warmup_s=1
shards=7
producers=7
preload=5000
queue_capacity=1024
drain_timeout_s=30
seed=42
pin=""
diagnose=0
reply=0
workload=signal
active_ues=5000
out_dir=""

while [ $# -gt 0 ]; do
  case "$1" in
    --repeats) repeats="$2"; shift 2;;
    --rates) rates="$2"; shift 2;;
    --duration) duration="$2"; shift 2;;
    --warmup-s) warmup_s="$2"; shift 2;;
    --shards) shards="$2"; shift 2;;
    --producers) producers="$2"; shift 2;;
    --preload) preload="$2"; shift 2;;
    --queue-capacity) queue_capacity="$2"; shift 2;;
    --drain-timeout-s) drain_timeout_s="$2"; shift 2;;
    --seed) seed="$2"; shift 2;;
    --pin) pin="$2"; shift 2;;
    --diagnose) diagnose=1; shift;;
    # PROBE ONLY: adds Rust with a one-slot reply channel (--features sync-oneshot)
    # on both allocators. Writes pipeline-reply-* so it can never be read as the
    # four-variant confirmatory log.
    --reply) reply=1; shift;;
    --workload) workload="$2"; shift 2;;
    --active-ues) active_ues="$2"; shift 2;;
    --out-dir) out_dir="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

if [ "$workload" != signal ] && [ "$workload" != mixed ]; then
  echo "unknown --workload '$workload' (use signal|mixed)" >&2
  exit 2
fi
if [ "$diagnose" -eq 1 ] && [ "$reply" -eq 1 ]; then
  echo "--diagnose and --reply are separate probes; run them one at a time" >&2
  exit 2
fi

for value in "$repeats" "$duration" "$warmup_s" "$shards" "$producers" \
             "$preload" "$queue_capacity" "$seed" "$active_ues"; do
  [[ "$value" =~ ^[0-9]+$ ]] || { echo "integer argument expected: $value" >&2; exit 2; }
done
[ "$repeats" -gt 0 ] && [ "$duration" -gt 0 ] && [ "$shards" -gt 0 ] &&
  [ "$producers" -gt 0 ] || { echo "repeats, duration, shards, and producers must be > 0" >&2; exit 2; }

mkdir -p "$here/.bin" "$here/results"
results_root="$here/results"
[ -n "$out_dir" ] && results_root="$out_dir" && mkdir -p "$results_root"
stamp="$(date +%Y%m%d-%H%M%S)"
prefix="pipeline"
[ "$diagnose" -eq 1 ] && prefix="pipeline-diagnose"
[ "$reply" -eq 1 ] && prefix="pipeline-reply"
[ "$workload" = mixed ] && prefix="${prefix}-mixed"
out="$results_root/$prefix-$stamp.jsonl"
hist="$results_root/$prefix-$stamp.hist.jsonl"
: >"$out"
: >"$hist"

echo "== building pipeline pilot =="
cmake -S "$cpp" -B "$cpp/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$cpp/build" --target pipeline >/dev/null
cmake -S "$cpp" -B "$cpp/build-jemalloc" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DUECM_USE_JEMALLOC=ON -DUECM_BUILD_TESTS=OFF >/dev/null
cmake --build "$cpp/build-jemalloc" --target pipeline >/dev/null
cargo build --release --manifest-path "$rust/Cargo.toml" --example pipeline >/dev/null
cp "$rust/target/release/examples/pipeline" "$here/.bin/pipeline-rust-system"
cargo build --release --manifest-path "$rust/Cargo.toml" --example pipeline \
  --features jemalloc >/dev/null
cp "$rust/target/release/examples/pipeline" "$here/.bin/pipeline-rust-jemalloc"
if [ "$diagnose" -eq 1 ]; then
  cargo build --release --manifest-path "$rust/Cargo.toml" --example pipeline \
    --features mutex-queue >/dev/null
  cp "$rust/target/release/examples/pipeline" "$here/.bin/pipeline-rust-system-mutex"
  cargo build --release --manifest-path "$rust/Cargo.toml" --example pipeline \
    --features jemalloc,mutex-queue >/dev/null
  cp "$rust/target/release/examples/pipeline" "$here/.bin/pipeline-rust-jemalloc-mutex"
fi
if [ "$reply" -eq 1 ]; then
  cargo build --release --manifest-path "$rust/Cargo.toml" --example pipeline \
    --features sync-oneshot >/dev/null
  cp "$rust/target/release/examples/pipeline" "$here/.bin/pipeline-rust-system-oneshot"
  cargo build --release --manifest-path "$rust/Cargo.toml" --example pipeline \
    --features jemalloc,sync-oneshot >/dev/null
  cp "$rust/target/release/examples/pipeline" "$here/.bin/pipeline-rust-jemalloc-oneshot"
fi

declare -A binary=(
  [cpp-system]="$cpp/build/pipeline"
  [cpp-jemalloc]="$cpp/build-jemalloc/pipeline"
  [rust-system]="$here/.bin/pipeline-rust-system"
  [rust-jemalloc]="$here/.bin/pipeline-rust-jemalloc"
  [rust-system-mutex]="$here/.bin/pipeline-rust-system-mutex"
  [rust-jemalloc-mutex]="$here/.bin/pipeline-rust-jemalloc-mutex"
  [rust-system-oneshot]="$here/.bin/pipeline-rust-system-oneshot"
  [rust-jemalloc-oneshot]="$here/.bin/pipeline-rust-jemalloc-oneshot"
)
if [ "$diagnose" -eq 1 ]; then
  variants=(cpp-system rust-system cpp-jemalloc rust-jemalloc rust-system-mutex rust-jemalloc-mutex)
elif [ "$reply" -eq 1 ]; then
  variants=(cpp-system rust-system cpp-jemalloc rust-jemalloc rust-system-oneshot rust-jemalloc-oneshot)
else
  variants=(cpp-system rust-system cpp-jemalloc rust-jemalloc)
fi
pin_cmd=()
[ -n "$pin" ] && pin_cmd=(taskset -c "$pin")

validate_line() {
  python3 -c '
import json, sys
r = json.loads(sys.stdin.read())
required = ("planned", "enqueue_started", "enqueued", "completed_within_window",
            "completed_during_drain", "errors", "timed_out", "histogram_overflows")
missing = [k for k in required if k not in r]
if missing:
    raise SystemExit("missing pipeline fields: " + ", ".join(missing))
accounted = r["completed_within_window"] + r["completed_during_drain"] + r["timed_out"]
if r["planned"] != r["enqueue_started"] or r["planned"] != r["enqueued"]:
    raise SystemExit("not every planned request reached the shard queue")
if accounted != r["enqueued"]:
    raise SystemExit("completion accounting does not equal enqueued")
if not r["valid"] or r["errors"] or r["timed_out"] or r["histogram_overflows"]:
    raise SystemExit("invalid pipeline run")
if "stamp_start" not in r or "queue" not in r:
    raise SystemExit("missing start-split schema fields")
if r["stamp_start"]:
    for key in ("queue_wait_ns", "execute_ns"):
        if not isinstance(r.get(key), dict):
            raise SystemExit(key + " missing while stamp_start is set")
elif r.get("queue_wait_ns") is not None or r.get("execute_ns") is not None:
    raise SystemExit("start split recorded without stamp_start")
kinds = r.get("kinds")
if not isinstance(kinds, list) or len(kinds) != 8 or sum(kinds) != r["planned"]:
    raise SystemExit("kind counts do not match the planned operations")
if r.get("workload") not in ("signal", "mixed"):
    raise SystemExit("workload must be signal or mixed")
'
}

echo "== $workload pipeline pilot =="
if [ "$diagnose" -eq 1 ]; then
  echo "   diagnostic split and Rust mutex-queue arms; not a language ranking"
fi
echo "   output: $out"
n_variants="${#variants[@]}"
for rate in $rates; do
  [[ "$rate" =~ ^[0-9]+$ ]] && [ "$rate" -gt 0 ] ||
    { echo "positive integer rate expected: $rate" >&2; exit 2; }
  ops=$((rate * duration))
  warmup=$((rate * warmup_s))
  if [ "$workload" = mixed ]; then
    bootstrap=$((2 * active_ues))
    if [ "$warmup" -lt "$bootstrap" ]; then warmup=$bootstrap; fi
  fi
  for ((repeat=0; repeat<repeats; ++repeat)); do
    start_at=$((repeat % n_variants))
    for ((k=0; k<n_variants; ++k)); do
      variant="${variants[$(((start_at + k) % n_variants))]}"
      run_id="rate-${rate}-repeat-${repeat}-${variant}"
      echo "   $run_id"
      cmd=("${pin_cmd[@]}" "${binary[$variant]}"
        --shards "$shards" --producers "$producers"
        --queue-capacity "$queue_capacity" --preload "$preload"
        --ops "$ops" --warmup "$warmup" --seed "$((seed + repeat))"
        --workload "$workload" --active-ues "$active_ues"
        --rate "$rate" --drain-timeout-s "$drain_timeout_s"
        --hist-out "$hist" --run-id "$run_id" --json)
      [ "$diagnose" -eq 1 ] && cmd+=(--stamp-start)
      line="$("${cmd[@]}")"
      printf '%s\n' "$line" | validate_line
      printf '%s\n' "$line" >>"$out"
    done
  done
done

echo "pipeline pilot passed all validity gates"
echo "$out"
echo "$hist"
