#!/usr/bin/env bash
# Build and run the UECM benchmark for all four language x allocator variants
# (C++/system, C++/jemalloc, Rust/system, Rust/jemalloc) with an identical
# workload, then print a comparison table. Extra CLI args are forwarded to every
# bench invocation, e.g.:
#
#   bench/run_bench.sh --shards 8 --producers 8 --preload 20000 --ops 500000
#   bench/run_bench.sh --rate 50000            # open-loop, coordinated-omission-corrected
#
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

args=("$@")
if [ ${#args[@]} -eq 0 ]; then
  args=(--shards 8 --producers 8 --preload 10000 --ops 200000)
fi

mkdir -p "$here/.bin" "$here/results"

echo "== building C++ (system) =="
cmake -S "$cpp" -B "$cpp/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$cpp/build" --target bench >/dev/null

echo "== building C++ (jemalloc) =="
cmake -S "$cpp" -B "$cpp/build-jemalloc" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DUECM_USE_JEMALLOC=ON -DUECM_BUILD_TESTS=OFF >/dev/null
cmake --build "$cpp/build-jemalloc" --target bench >/dev/null

echo "== building Rust (system) =="
cargo build --release --manifest-path "$rust/Cargo.toml" --example bench >/dev/null 2>&1
cp "$rust/target/release/examples/bench" "$here/.bin/rust-system"

echo "== building Rust (jemalloc) =="
cargo build --release --manifest-path "$rust/Cargo.toml" --example bench --features jemalloc >/dev/null 2>&1
cp "$rust/target/release/examples/bench" "$here/.bin/rust-jemalloc"

out="$here/results/latest.jsonl"
: > "$out"

echo "== running workload: ${args[*]} =="
"$cpp/build/bench"          "${args[@]}" --json >>"$out"
"$cpp/build-jemalloc/bench" "${args[@]}" --json >>"$out"
"$here/.bin/rust-system"    "${args[@]}" --json >>"$out"
"$here/.bin/rust-jemalloc"  "${args[@]}" --json >>"$out"

echo
python3 - "$out" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
hdr = ("lang","alloc","workload","thr(ops/s)","p50","p90","p99","p99.9","max","mean")
w   = (6, 9, 9, 12, 9, 9, 9, 9, 10, 10)
def fmt(vals):
    return "  ".join(str(v).rjust(width) for v,width in zip(vals,w))
print(fmt(hdr))
print(fmt(tuple("-"*wi for wi in w)))
for r in rows:
    L = r["lat_ns"]
    print(fmt((r["lang"], r["alloc"], r.get("workload","-"), f'{r["throughput_ops_s"]:.0f}',
               L["p50"], L["p90"], L["p99"], L["p999"], L["max"], f'{L["mean"]:.0f}')))
print("\nlatency in ns; wrote", sys.argv[1])
PY
