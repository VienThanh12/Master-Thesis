#!/usr/bin/env bash
# Matched-design probe: the overload comparison with the handoff written the same way
# in both languages (RQ1 mechanism, §4.16 of docs/OVERLOAD_MECHANISM.md).
#
# PROBE ONLY. Not a reported arm and not in the Holm-tested family.
#
# Past saturation the Rust lead goes away when Rust is given the C++ queue design
# (spec §12), and the C++ queue design asks the kernel for about 1.4 wakes per request
# that wake nobody. This asks the converse question: with one queue and one reply
# written the same way in both languages around the real ShardCore, is any lead left?
# Each probe binary runs either design, so within one binary the two differ only in
# how a request reaches a worker and how the reply comes back:
#   stock     the reported Service: std channels in Rust; a mutex, two condition
#             variables and std::promise in C++
#   matched   a fixed ring behind a three-state futex mutex and one reply slot per
#             sender, waking a thread only when it sleeps, with the same futex calls
#             in both languages
#
# Eight arms, interleaved inside each repeat with the starting arm rotated: both
# languages, both designs, both allocators. Senders send back to back, which is the
# overload state, so throughput is the comparison. Every binary first passes a
# self-test: one sender, 20,000 operations through each design, same results.
#
# With --stages the same probe splits every call into four parts on one clock (the queue,
# the worker, the reply, and the sender's own time), on the system allocator only. The
# worker's stamps cost two clock reads per call in every arm, so stage runs are kept apart
# from the throughput runs above.
#
# Usage (inside the container):
#   bench/matched_probes.sh --repeats 20 --pin 2-17
#   bench/matched_probes.sh --stages --repeats 20 --pin 2-17
#   bench/matched_probes.sh --repeats 2 --duration 1      # smoke test
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

shards=7
producers=7
active_ues=5000
duration=3
warmup=1
seed=42
repeats=20
pin=""
stages=0

while [ $# -gt 0 ]; do
  case "$1" in
    --stages) stages=1; shift;;
    --repeats) repeats="$2"; shift 2;;
    --duration) duration="$2"; shift 2;;
    --warmup) warmup="$2"; shift 2;;
    --shards) shards="$2"; shift 2;;
    --producers) producers="$2"; shift 2;;
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
# tikv-jemalloc reads _RJEM_MALLOC_CONF.
export MALLOC_CONF="thp:never,narenas:16"
export _RJEM_MALLOC_CONF="thp:never,narenas:16"

echo "== building the probe in both languages on both allocators =="
for heap in system jemalloc; do
  dir="$cpp/build-matched-$heap"
  flags=(-DCMAKE_BUILD_TYPE=Release -DUECM_MATCHED_PROBE=ON -DUECM_BUILD_TESTS=OFF)
  [ "$heap" = jemalloc ] && flags+=(-DUECM_USE_JEMALLOC=ON)
  cmake -S "$cpp" -B "$dir" -G Ninja "${flags[@]}" >/dev/null 2>&1 \
    || { echo "FAIL: C++ $heap configure"; exit 1; }
  cmake --build "$dir" --target matched >/dev/null 2>&1 || { echo "FAIL: C++ $heap build"; exit 1; }
  cp "$dir/matched" "$here/.bin/matched-cpp-$heap"
done
for heap in system jemalloc; do
  feat="matched-probe"
  [ "$heap" = jemalloc ] && feat="matched-probe,jemalloc"
  cargo build --release --manifest-path "$rust/Cargo.toml" --example matched --features "$feat" \
    >/dev/null 2>&1 || { echo "FAIL: Rust $heap build"; exit 1; }
  cp "$rust/target/release/examples/matched" "$here/.bin/matched-rust-$heap"
done

echo "== self-test: both designs give every operation the same result =="
for b in cpp-system rust-system cpp-jemalloc rust-jemalloc; do
  "${pre[@]}" "$here/.bin/matched-$b" --self-test --shards "$shards" --active-ues "$active_ues" \
    --seed "$seed" || { echo "FAIL: self-test of $b"; exit 1; }
done

arms=(cpp-stock-system rust-stock-system cpp-matched-system rust-matched-system
      cpp-stock-jemalloc rust-stock-jemalloc cpp-matched-jemalloc rust-matched-jemalloc)
extra=()
prefix="matched_probes"
if [ "$stages" = 1 ]; then
  arms=(cpp-stock-system rust-stock-system cpp-matched-system rust-matched-system)
  extra=(--stages)
  prefix="matched_stages"
fi
n_arms=${#arms[@]}
stamp="$(date +%Y%m%d-%H%M%S)"
out="$here/results/$prefix-$stamp.jsonl"
: > "$out"
total=$(( repeats * n_arms ))
echo "== $repeats repeats x $n_arms arms = $total runs, ${warmup} s warm-up and ${duration} s measured =="
n=0
for rep in $(seq 1 "$repeats"); do
  start_at=$(( (rep - 1) % n_arms ))
  for k in $(seq 0 $(( n_arms - 1 ))); do
    arm="${arms[$(( (start_at + k) % n_arms ))]}"
    IFS=- read -r lang design heap <<< "$arm"
    n=$(( n + 1 ))
    printf '\r  run %d/%d (rep %d, %s)          ' "$n" "$total" "$rep" "$arm"
    line="$("${pre[@]}" "$here/.bin/matched-$lang-$heap" --design "$design" --shards "$shards" \
      --producers "$producers" --active-ues "$active_ues" --duration-s "$duration" \
      --warmup-s "$warmup" --seed $(( seed + rep )) "${extra[@]}" --json 2>/dev/null)"
    if [ -z "$line" ]; then echo; echo "FAIL: no output from $arm"; exit 1; fi
    python3 -c '
import json, sys
r = json.loads(sys.argv[1])
r["arm"] = sys.argv[2]
r["repeat"] = int(sys.argv[3])
print(json.dumps(r))' "$line" "$arm" "$rep" >> "$out"
  done
done
printf '\n\n'

if [ "$stages" = 1 ]; then
python3 - "$out" "$here" <<'PY'
import json, statistics, sys
sys.path.insert(0, sys.argv[2])
from plot_figures import paired_permutation_test

path = sys.argv[1]
rows = [json.loads(l) for l in open(path) if l.strip()]
arms = ["cpp-stock-system", "rust-stock-system", "cpp-matched-system", "rust-matched-system"]
parts = ["queue_us", "worker_us", "reply_us", "sender_us"]
by_rep = {a: {r["repeat"]: r for r in rows if r["arm"] == a} for a in arms}
reps = sorted(set.intersection(*(set(v) for v in by_rep.values())))
print(f"{len(reps)} paired repeats per arm, system allocator, time per call in microseconds")

usable = True
if any(r["errors"] for r in rows):
    print("WARNING: an operation failed in at least one run.")
    usable = False
for a in arms:
    for field in ["us_per_op_per_sender"] + parts:
        vals = [by_rep[a][k][field] for k in reps]
        cv = statistics.pstdev(vals) / statistics.mean(vals)
        if field in ("us_per_op_per_sender", "queue_us", "reply_us") and cv > 0.05:
            print(f"WARNING: {a} {field} varies by {cv * 100:.0f}% across repeats.")
            usable = False
    gap = max(abs(sum(by_rep[a][k][p] for p in parts) - by_rep[a][k]["us_per_op_per_sender"])
              / by_rep[a][k]["us_per_op_per_sender"] for k in reps)
    if gap > 0.02:
        print(f"WARNING: {a} parts miss the time per call by up to {gap * 100:.1f}%.")
        usable = False
if not usable:
    print()
    print("REFUSING TO CERTIFY: see the warnings above before using any number here.")
print()

med = {a: {f: statistics.median(by_rep[a][k][f] for k in reps)
           for f in ["us_per_op_per_sender"] + parts} for a in arms}
print(f"{'arm':<22}{'queue':>9}{'worker':>9}{'reply':>9}{'sender':>9}{'sum':>9}{'per call':>10}")
for a in arms:
    m = med[a]
    print(f"{a:<22}" + "".join(f"{m[p]:>9.3f}" for p in parts)
          + f"{sum(m[p] for p in parts):>9.2f}{m['us_per_op_per_sender']:>10.2f}")
print()
print("Rust against C++ per part, median of paired differences (negative: Rust faster)")
for design in ("stock", "matched"):
    c, r = f"cpp-{design}-system", f"rust-{design}-system"
    cells = []
    for f in parts + ["us_per_op_per_sender"]:
        x = [by_rep[c][k][f] for k in reps]
        y = [by_rep[r][k][f] for k in reps]
        _md, p, _n = paired_permutation_test(x, y)
        d = statistics.median(b - a for a, b in zip(x, y))
        cells.append(f"{f.replace('_us', '').replace('us_per_op_per_sender', 'per call')} "
                     f"{d:+.3f} (p={p:.1e})")
    print(f"  {design:<8} " + "   ".join(cells))
json.dump({"path": path, "repeats": len(reps), "certified": usable, "medians": med},
          open(path.replace(".jsonl", ".summary.json"), "w"), indent=1)
print()
print(f"wrote {path}")
PY
exit 0
fi

python3 - "$out" "$here" <<'PY'
import json, math, statistics, sys
sys.path.insert(0, sys.argv[2])
from plot_figures import bootstrap_ci, paired_permutation_test

path = sys.argv[1]
rows = [json.loads(l) for l in open(path) if l.strip()]
arms = ["cpp-stock-system", "rust-stock-system", "cpp-matched-system", "rust-matched-system",
        "cpp-stock-jemalloc", "rust-stock-jemalloc", "cpp-matched-jemalloc", "rust-matched-jemalloc"]
by_rep = {a: {r["repeat"]: r for r in rows if r["arm"] == a} for a in arms}
reps = sorted(set.intersection(*(set(v) for v in by_rep.values())))
thr = {a: [by_rep[a][k]["ops_per_s"] for k in reps] for a in arms}
print(f"{len(reps)} paired repeats per arm, {rows[0]['producers']} senders, "
      f"{rows[0]['shards']} shards, {rows[0]['duration_s']:.0f} s measured")

usable = True
if any(r["errors"] for r in rows):
    print("WARNING: an operation failed in at least one run.")
    usable = False
for a in arms:
    cv = statistics.pstdev(thr[a]) / statistics.mean(thr[a])
    if cv > 0.05:
        print(f"WARNING: {a} varies by {cv * 100:.0f}% across repeats "
              f"({min(thr[a]) / 1000:.0f} to {max(thr[a]) / 1000:.0f} kops/s).")
        usable = False
if not usable:
    print()
    print("REFUSING TO CERTIFY: see the warnings above before using any number here.")
print()


def per_op_us(a, field):
    return statistics.median(by_rep[a][k][field] / by_rep[a][k]["ops"] * 1e6 for k in reps)


print(f"{'arm':<24}{'kops/s':>9}{'95% CI':>20}{'us per call':>13}{'user us/op':>12}{'kernel us/op':>14}")
summary = {"path": path, "repeats": len(reps), "certified": usable, "arms": {}, "contrasts": {}}
for a in arms:
    m, lo, hi = bootstrap_ci(thr[a])
    rt = statistics.median(by_rep[a][k]["us_per_op_per_sender"] for k in reps)
    u, s = per_op_us(a, "cpu_user_s"), per_op_us(a, "cpu_sys_s")
    summary["arms"][a] = {"kops": m / 1000, "lo": lo / 1000, "hi": hi / 1000,
                          "us_per_call": rt, "user_us_per_op": u, "sys_us_per_op": s}
    print(f"{a:<24}{m / 1000:>9.1f}{f'[{lo / 1000:.1f}, {hi / 1000:.1f}]':>20}"
          f"{rt:>13.2f}{u:>12.2f}{s:>14.2f}")
print()


def contrast(label, base, probe):
    md, p, _ = paired_permutation_test(thr[base], thr[probe])
    pct = [(y - x) / x * 100 for x, y in zip(thr[base], thr[probe])]
    m, lo, hi = bootstrap_ci(pct)
    ahead = sum(1 for x, y in zip(thr[base], thr[probe]) if y > x)
    summary["contrasts"][f"{probe} vs {base}"] = {"pct": m, "lo": lo, "hi": hi,
                                                  "ahead": ahead, "n": len(reps), "p": p}
    print(f"{label}")
    print(f"    {probe} against {base}: {m:+.1f}% [{lo:+.1f}, {hi:+.1f}], "
          f"higher in {ahead} of {len(reps)}, paired p={p:.2e}")


print("1. Rust against C++, with each design")
for heap in ("system", "jemalloc"):
    contrast(f"   stock design, {heap}:", f"cpp-stock-{heap}", f"rust-stock-{heap}")
    contrast(f"   matched design, {heap}:", f"cpp-matched-{heap}", f"rust-matched-{heap}")
print()
print("2. What the matched design does for each language")
for heap in ("system", "jemalloc"):
    for lang in ("cpp", "rust"):
        contrast(f"   {lang}, {heap}:", f"{lang}-stock-{heap}", f"{lang}-matched-{heap}")
print()
print("3. The allocator, with the matched design")
for lang in ("cpp", "rust"):
    contrast(f"   {lang}:", f"{lang}-matched-system", f"{lang}-matched-jemalloc")
print()
print("4. How much of the stock gap the matched design leaves, per repeat")
for heap in ("system", "jemalloc"):
    stock = [math.log(r / c) for c, r in zip(thr[f"cpp-stock-{heap}"], thr[f"rust-stock-{heap}"])]
    matched = [math.log(r / c) for c, r in zip(thr[f"cpp-matched-{heap}"], thr[f"rust-matched-{heap}"])]
    md, p, _ = paired_permutation_test(stock, matched)
    s, m = statistics.median(stock), statistics.median(matched)
    summary["contrasts"][f"gap change {heap}"] = {"stock_pct": (math.exp(s) - 1) * 100,
                                                  "matched_pct": (math.exp(m) - 1) * 100, "p": p}
    print(f"   {heap}: Rust over C++ is {(math.exp(s) - 1) * 100:+.1f}% with the stock design and "
          f"{(math.exp(m) - 1) * 100:+.1f}% with the matched one, paired p={p:.2e}")
json.dump(summary, open(path.replace(".jsonl", ".summary.json"), "w"), indent=1)
print()
print(f"wrote {path}")
PY
