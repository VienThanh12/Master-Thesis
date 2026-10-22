#!/usr/bin/env bash
# Does the deferred fill sit inside the measured window? Inside the container. Diagnostic.
#
# With --correction-when after, bench.cpp reads the end of its window before
# correct_after and bench.rs reads it after. In that mode the cap only bounds the
# deferred fill, so cap 0 against cap 10000 changes nothing but the fill. If the
# fill is inside a language's window, that language gains throughput at cap 0.
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$root"
repeats="${1:-10}"
pin="2-17"
rate=112000
cmake -S cpp -B cpp/build -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null 2>&1
cmake --build cpp/build --target bench >/dev/null 2>&1 || { echo "FAIL: C++ build"; exit 1; }
cargo build --release --manifest-path rust/Cargo.toml --example bench >/dev/null 2>&1 \
  || { echo "FAIL: Rust build"; exit 1; }
mkdir -p bench/.bin bench/results
cp rust/target/release/examples/bench bench/.bin/fw-rust-system
declare -A BIN=(["cpp"]="cpp/build/bench" ["rust"]="bench/.bin/fw-rust-system")
arms=(cpp-10000 rust-10000 cpp-0 rust-0)
out="bench/results/fillwindow-$(date +%Y%m%d-%H%M%S).jsonl"
: > "$out"
for rep in $(seq 1 "$repeats"); do
  start_at=$(( (rep - 1) % 4 ))
  for k in 0 1 2 3; do
    arm="${arms[$(( (start_at + k) % 4 ))]}"
    lang="${arm%-*}"
    cap="${arm#*-}"
    line="$(taskset -c "$pin" "${BIN[$lang]}" --workload mixed --shards 7 --producers 7 \
      --active-ues 5000 --preload 5000 --ops $(( rate * 3 )) --warmup "$rate" --seed 42 \
      --rate "$rate" --max-run-s 6 --run-id "$rep" --correction-when after \
      --correction-cap "$cap" --json 2>/dev/null)"
    [ -n "$line" ] || { echo "FAIL: no output from $arm"; exit 1; }
    python3 -c '
import json, sys
r = json.loads(sys.argv[1]); r["arm"] = sys.argv[2]; r["repeat"] = int(sys.argv[3])
print(json.dumps(r))' "$line" "$arm" "$rep" >> "$out"
    printf '  rep %d %-11s %.1f kops/s, window %.3f s\n' "$rep" "$arm" \
      "$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["throughput_ops_s"]/1000)' "$line")" \
      "$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["measured_wall_s"])' "$line")"
  done
done
python3 - "$out" bench <<'PY'
import json, statistics, sys
sys.path.insert(0, sys.argv[2])
from plot_figures import paired_permutation_test
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
arms = ["cpp-10000", "cpp-0", "rust-10000", "rust-0"]
by = {a: {r["repeat"]: r for r in rows if r["arm"] == a} for a in arms}
reps = sorted(set.intersection(*(set(v) for v in by.values())))
print()
for a in arms:
    t = statistics.median(by[a][k]["throughput_ops_s"] for k in reps)
    w = statistics.median(by[a][k]["measured_wall_s"] for k in reps)
    print(f"{a:<11} {t / 1000:7.1f} kops/s   window {w:.3f} s")
for lang in ("cpp", "rust"):
    base = [by[f"{lang}-10000"][k]["throughput_ops_s"] for k in reps]
    nofill = [by[f"{lang}-0"][k]["throughput_ops_s"] for k in reps]
    dw = [by[f"{lang}-10000"][k]["measured_wall_s"] - by[f"{lang}-0"][k]["measured_wall_s"] for k in reps]
    _, p, _ = paired_permutation_test(base, nofill)
    pct = statistics.median((y - x) / x * 100 for x, y in zip(base, nofill))
    print(f"{lang}: cap 0 against cap 10000 {pct:+.1f}%, higher in "
          f"{sum(1 for x, y in zip(base, nofill) if y > x)} of {len(reps)}, paired p={p:.2e}; "
          f"window longer with the fill by {statistics.median(dw) * 1000:.0f} ms")
for cap in ("10000", "0"):
    c = [by[f"cpp-{cap}"][k]["throughput_ops_s"] for k in reps]
    r = [by[f"rust-{cap}"][k]["throughput_ops_s"] for k in reps]
    _, p, _ = paired_permutation_test(c, r)
    pct = statistics.median((y - x) / x * 100 for x, y in zip(c, r))
    print(f"Rust against C++ at cap {cap}: {pct:+.1f}%, higher in "
          f"{sum(1 for x, y in zip(c, r) if y > x)} of {len(reps)}, paired p={p:.2e}")
print(f"wrote {sys.argv[1]}")
PY
