#!/usr/bin/env bash
# Batch probe: how much work per handoff before each language's own cost decides
# throughput past saturation (RQ1 mechanism, Method 2 of docs/OVERLOAD_MECHANISM.md).
#
# PROBE ONLY. Not a reported arm and not in the Holm-tested family.
#
# Each sender owns one shard and sends batches of B signalling operations, one batch
# at a time and back to back, so the service is past saturation at every B. The time
# a sender spends per batch is modelled as
#
#     T(B) = h + B * t
#
# where h is the cost of one handoff (queue, reply handle, waking threads) and t is
# the cost of one operation inside a loaded worker. The overload throughput the
# campaign reports sits at B = 1, where h dominates. As B grows, throughput approaches
# 1 / t per shard, which is the language's own speed on the operation. The fit gives h
# and t for each build, and B* = h / t is where the operation becomes the larger part.
#
# Four builds, interleaved inside each repeat with the starting build rotated: both
# languages on both allocators, all with the batched request (-DUECM_BATCH_PROBE=ON,
# --features batch-probe). One sender per shard removes contention between senders
# on a queue, so h here is not the campaign's handoff cost.
#
# Usage (inside the container, or anywhere with the toolchain):
#   bench/batch_probes.sh --repeats 5 --pin 2-17
#   bench/batch_probes.sh --batches "1 16 256" --repeats 2 --duration 1   # smoke test
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

batches="1 2 4 8 16 32 64 128 256 512 1024"
repeats=5
duration=3
warmup=1
shards=7
preload=5000
seed=42
pin=""

while [ $# -gt 0 ]; do
  case "$1" in
    --batches) batches="$2"; shift 2;;
    --repeats) repeats="$2"; shift 2;;
    --duration) duration="$2"; shift 2;;
    --warmup) warmup="$2"; shift 2;;
    --shards) shards="$2"; shift 2;;
    --preload) preload="$2"; shift 2;;
    --pin) pin="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

mkdir -p "$here/.bin" "$here/results"
pre=()
if [ -n "$pin" ] && command -v taskset >/dev/null 2>&1; then
  pre+=(taskset -c "$pin")
  echo "== pinning to cores: $pin =="
fi
# The campaign's jemalloc settings (bench/campaign.sh). The C++ arm reads MALLOC_CONF and
# tikv-jemalloc reads _RJEM_MALLOC_CONF. The 19 October run predates this line and used
# the allocator's defaults.
export MALLOC_CONF="thp:never,narenas:16"
export _RJEM_MALLOC_CONF="thp:never,narenas:16"

echo "== building the four builds with the batched request =="
for heap in system jemalloc; do
  dir="$cpp/build-batch-$heap"
  flags=(-DCMAKE_BUILD_TYPE=Release -DUECM_BATCH_PROBE=ON -DUECM_BUILD_TESTS=ON)
  [ "$heap" = jemalloc ] && flags+=(-DUECM_USE_JEMALLOC=ON)
  cmake -S "$cpp" -B "$dir" -G Ninja "${flags[@]}" >/dev/null 2>&1 \
    || { echo "FAIL: C++ $heap configure"; exit 1; }
  cmake --build "$dir" --target batch test_batch >/dev/null 2>&1 || { echo "FAIL: C++ $heap build"; exit 1; }
  "$dir/test_batch" 2>/dev/null || { echo "FAIL: C++ test_batch ($heap)"; exit 1; }
  cp "$dir/batch" "$here/.bin/batch-cpp-$heap"
done
cargo test -q --release --manifest-path "$rust/Cargo.toml" --features batch-probe --test batch_probe \
  >/dev/null 2>&1 || { echo "FAIL: Rust batch_probe test"; exit 1; }
for heap in system jemalloc; do
  feat="batch-probe"
  [ "$heap" = jemalloc ] && feat="batch-probe,jemalloc"
  cargo build --release --manifest-path "$rust/Cargo.toml" --example batch --features "$feat" \
    >/dev/null 2>&1 || { echo "FAIL: Rust $heap build"; exit 1; }
  cp "$rust/target/release/examples/batch" "$here/.bin/batch-rust-$heap"
done

arms=(cpp-system rust-system cpp-jemalloc rust-jemalloc)
n_arms=${#arms[@]}
stamp="$(date +%Y%m%d-%H%M%S)"
out="$here/results/batch_probes-$stamp.jsonl"
: > "$out"
n_b=$(wc -w <<< "$batches")
total=$(( repeats * n_b * n_arms ))
echo "== $repeats repeats x $n_b batch sizes x $n_arms builds = $total runs, ${duration} s each =="
n=0
bi=0
for rep in $(seq 1 "$repeats"); do
  bi=0
  for b in $batches; do
    start_at=$(( (rep - 1 + bi) % n_arms ))
    for k in $(seq 0 $(( n_arms - 1 ))); do
      arm="${arms[$(( (start_at + k) % n_arms ))]}"
      n=$(( n + 1 ))
      printf '\r  run %d/%d (rep %d, batch %d, %s)        ' "$n" "$total" "$rep" "$b" "$arm"
      line="$("${pre[@]}" "$here/.bin/batch-$arm" --shards "$shards" --preload "$preload" \
        --batch "$b" --duration-s "$duration" --warmup-s "$warmup" --seed $(( seed + rep )) \
        --json 2>/dev/null)"
      if [ -z "$line" ]; then echo; echo "FAIL: no output from $arm at batch $b"; exit 1; fi
      python3 -c '
import json, sys
r = json.loads(sys.argv[1])
r["arm"] = sys.argv[2]
r["repeat"] = int(sys.argv[3])
print(json.dumps(r))' "$line" "$arm" "$rep" >> "$out"
    done
    bi=$(( bi + 1 ))
  done
done
printf '\n\n'

python3 - "$out" <<'PY'
import json
import random
import statistics
import sys

path = sys.argv[1]
rows = [json.loads(l) for l in open(path) if l.strip()]
arms = ["cpp-system", "rust-system", "cpp-jemalloc", "rust-jemalloc"]
batches = sorted({r["batch"] for r in rows})
reps = sorted({r["repeat"] for r in rows})
cell = {(r["arm"], r["batch"], r["repeat"]): r for r in rows}

usable = True
if any(r["errors"] for r in rows):
    print("REFUSING TO CERTIFY: a batch reported failed operations.")
    usable = False
for a in arms:
    for b in batches:
        vals = [cell[(a, b, k)]["us_per_message_per_sender"] for k in reps if (a, b, k) in cell]
        if len(vals) > 1 and statistics.pstdev(vals) / statistics.mean(vals) > 0.05:
            print(f"WARNING: {a} at batch {b} varies by "
                  f"{statistics.pstdev(vals) / statistics.mean(vals) * 100:.0f}% across repeats")
            usable = False


def fit(points):
    """Least squares for T = h + B t, each point weighted by 1/T^2 so every batch size
    counts by its relative error rather than its absolute size."""
    w = [1.0 / (t * t) for _, t in points]
    sw = sum(w)
    sx = sum(wi * b for wi, (b, _) in zip(w, points))
    sy = sum(wi * t for wi, (_, t) in zip(w, points))
    sxx = sum(wi * b * b for wi, (b, _) in zip(w, points))
    sxy = sum(wi * b * t for wi, (b, t) in zip(w, points))
    t_op = (sw * sxy - sx * sy) / (sw * sxx - sx * sx)
    h = (sy - t_op * sx) / sw
    return h, t_op


def medians(a, ks):
    return [(b, statistics.median(cell[(a, b, k)]["us_per_message_per_sender"] for k in ks))
            for b in batches]


random.seed(1)
boot = {a: [] for a in arms}
dropped = 0
for _ in range(2000):
    ks = [random.choice(reps) for _ in reps]
    fits = {a: fit(medians(a, ks)) for a in arms}
    # A draw whose slope is not positive cannot give a crossover or a ratio. The same
    # repeats are drawn for every build, so the draws stay paired.
    if any(t <= 0 for _, t in fits.values()):
        dropped += 1
        continue
    for a in arms:
        boot[a].append(fits[a])
if dropped:
    print(f"note: {dropped} of 2000 bootstrap draws had a non-positive slope and were left out")


def ci(xs):
    xs = sorted(xs)
    return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]


print("Time per batch per sender T(B), in us (median over repeats)")
print(f"{'batch':>6}" + "".join(f"{a:>15}" for a in arms))
for b in batches:
    print(f"{b:>6}" + "".join(
        f"{statistics.median(cell[(a, b, k)]['us_per_message_per_sender'] for k in reps):>15.2f}" for a in arms))
print()
print("Fit T(B) = h + B t, bootstrap 95% intervals over repeats")
summary = {}
for a in arms:
    h, t_op = fit(medians(a, reps))
    hs, ts = zip(*boot[a])
    bstar = [x / y for x, y in boot[a]]
    summary[a] = {"h_us": h, "t_ns": t_op * 1000, "crossover_batch": h / t_op}
    print(f"  {a:<14} handoff h = {h:6.2f} us [{ci(hs)[0]:.2f}, {ci(hs)[1]:.2f}]   "
          f"per operation t = {t_op * 1000:6.1f} ns [{ci(ts)[0] * 1000:.1f}, {ci(ts)[1] * 1000:.1f}]   "
          f"crossover B* = {h / t_op:5.0f} [{ci(bstar)[0]:.0f}, {ci(bstar)[1]:.0f}]")
print()
for heap in ("system", "jemalloc"):
    c, r = f"cpp-{heap}", f"rust-{heap}"
    ratio = [bc[1] / br[1] for bc, br in zip(boot[c], boot[r])]
    hr = [bc[0] / br[0] for bc, br in zip(boot[c], boot[r])]
    print(f"  {heap}: C++ per-operation cost is {summary[c]['t_ns'] / summary[r]['t_ns']:.2f} times Rust's "
          f"[{ci(ratio)[0]:.2f}, {ci(ratio)[1]:.2f}], C++ handoff is {summary[c]['h_us'] / summary[r]['h_us']:.2f} "
          f"times Rust's [{ci(hr)[0]:.2f}, {ci(hr)[1]:.2f}]")
print()
print("Finished operations per second, Rust over C++ (median over repeats)")
print(f"{'batch':>6}{'system':>10}{'jemalloc':>10}   CPU us per operation: cpp-sys rust-sys cpp-je rust-je")
for b in batches:
    ratios = []
    for heap in ("system", "jemalloc"):
        rr = [cell[(f"rust-{heap}", b, k)]["ops_per_s"] / cell[(f"cpp-{heap}", b, k)]["ops_per_s"] for k in reps]
        ratios.append(statistics.median(rr))
    cpu = [statistics.median(cell[(a, b, k)]["cpu_us_per_op"] for k in reps) for a in arms]
    print(f"{b:>6}{ratios[0]:>10.3f}{ratios[1]:>10.3f}   " + " ".join(f"{v:8.3f}" for v in cpu))
if not usable:
    print()
    print("REFUSING TO CERTIFY: see the warnings above before using any number here.")
json.dump(summary, open(path.replace(".jsonl", ".summary.json"), "w"), indent=1)
print()
print(f"wrote {path}")
PY
