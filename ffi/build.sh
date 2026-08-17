#!/usr/bin/env bash
# RQ4 FFI prototype: build the Rust component as a C ABI library, compile and link
# the C++ host against it, run the host, and report the interop cost metrics
# (seam size + per-call latency) used in the migration study.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rust_dir="$here/rust-uecm-ffi"
host_dir="$here/cpp-host"
target="$rust_dir/target/release"

CXX="${CXX:-g++}"
CXXSTD="${CXXSTD:-c++17}"

# The seam's size and width are counted from source and do not depend on the host,
# unlike everything else this script produces. --counts-only refreshes just those
# fields of results/metrics.json, so a miscount can be corrected without
# re-measuring, and without a run on a busy machine overwriting the RQ4 latencies.
counts_only=0
[ "${1:-}" = "--counts-only" ] && counts_only=1

# Counted over code, not over comments: the safety contract in the module header
# names `unsafe extern "C"`, and a counter that matched it reported one entry
# point and three `unsafe` sites that do not exist.
strip_comments() { sed -e 's://.*::' -e '/^\s*\*/d' "$@"; }
count_source() { strip_comments "$2" | grep -cE "$1" || true; }

source_counts() {
  seam_rs=$(count_source 'pub[[:space:]]+(unsafe[[:space:]]+)?extern[[:space:]]+"C"[[:space:]]+fn' \
    "$rust_dir/src/lib.rs")
  loc_rs=$(wc -l < "$rust_dir/src/lib.rs" | tr -d ' ')
  loc_h=$(wc -l < "$rust_dir/include/uecm_ffi.h" | tr -d ' ')
  unsafe_lib=$(cat "$here/../rust/src"/*.rs | strip_comments |
    grep -cE '\bunsafe\b' || true)
  unsafe_seam=$(count_source '\bunsafe[[:space:]]+(extern[[:space:]]+"C"[[:space:]]+)?fn\b' \
    "$rust_dir/src/lib.rs")
}

if [ "$counts_only" -eq 1 ]; then
  source_counts
  python3 - "$here/results/metrics.json" \
    "$seam_rs" "$loc_rs" "$loc_h" "$unsafe_lib" "$unsafe_seam" <<'PY'
import json, sys
path, *vals = sys.argv[1:]
keys = ["entry_points", "seam_loc_rust", "header_loc", "unsafe_core", "unsafe_seam"]
with open(path) as fh:
    m = json.load(fh)
m.update(dict(zip(keys, (int(v) for v in vals))))
with open(path, "w") as fh:
    json.dump(m, fh, indent=2)
    fh.write("\n")
print("  updated source counts in", path)
for k in keys:
    print(f"    {k} = {m[k]}")
PY
  exit 0
fi

echo "== [1/3] Building Rust C-ABI library (cargo build --release) =="
( cd "$rust_dir" && cargo build --release )
ls -1 "$target"/libuecm_ffi.* 2>/dev/null || { echo "ERROR: library not produced"; exit 1; }

echo
echo "== [2/3] Compiling + linking the C++ host against the Rust cdylib =="
"$CXX" -std="$CXXSTD" -O2 -Wall -Wextra \
  -I "$rust_dir/include" \
  "$host_dir/main.cpp" \
  -L "$target" -luecm_ffi -lpthread -ldl \
  -Wl,-rpath,"$target" \
  -o "$here/host"
echo "  built: $here/host"

echo
echo "== [3/3] Running the C++ host =="
"$here/host" | tee "$here/host_run.log"
host_rc=${PIPESTATUS[0]}

echo
echo "== [4/4] Seam cost on a real operation: through the seam vs natively =="
# An empty crossing measured against a full service round-trip says the crossing
# is small; it does not say the seam adds nothing to a real operation, because
# the two quantities are not the same experiment. The direct comparison is the
# same signaling operation, on the same service configuration and the same loop
# shape, invoked natively from Rust and then from C++ through the C ABI.
#
# It has to be repeated and interleaved. The operation is dominated by a
# cross-thread wakeup whose run-to-run spread on a shared host is far wider than
# any per-call cost a C ABI could add, so one pass of each orders them at random:
# a single pair can and does show the seam "faster" than calling natively.
# Running them back to back inside each repeat makes the pair matched, and the
# median of the paired differences is then a usable estimate of the seam's cost.
FFI_REPEATS="${FFI_REPEATS:-15}"
FFI_ITERS="${FFI_ITERS:-50000}"
samples="$here/results/op_cost.jsonl"
mkdir -p "$here/results"
: > "$samples"

cargo build --quiet --release --manifest-path "$here/../rust/Cargo.toml" \
  --example latency_budget
native_bin="$here/../rust/target/release/examples/latency_budget"

echo "  $FFI_REPEATS interleaved repeats of $FFI_ITERS calls, 4 shards"
for rep in $(seq 1 "$FFI_REPEATS"); do
  printf '\r  repeat %d/%d      ' "$rep" "$FFI_REPEATS"
  "$here/host" --op-bench --iters "$FFI_ITERS" >> "$samples"
  "$native_bin" --shards 4 --active-ues 1 --core-iters 2000 \
    --svc-iters "$FFI_ITERS" --json >> "$samples"
done
printf '\n'

read -r native_ns op_ns delta_ns delta_pct paired_p delta_lo delta_hi <<<"$(python3 - "$samples" <<'PY'
import json, random, statistics, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
seam = [r["op_ns"] for r in rows if r["lang"] == "cpp-via-seam"]
native = [r["service_ns"] for r in rows if r["lang"] == "rust"]
n = min(len(seam), len(native))
diffs = [seam[i] - native[i] for i in range(n)]
# Exact two-sided paired sign-flip test over all 2**n assignments, matching the
# treatment the campaign gives its own paired comparisons.
obs = abs(sum(diffs))
extreme = sum(
    1 for mask in range(1 << n)
    if abs(sum(-d if (mask >> i) & 1 else d for i, d in enumerate(diffs))) >= obs - 1e-12
)
# A p-value only says the difference was not detected. The interval says how
# large a difference the measurement would still have missed, which is the claim
# RQ4 actually needs.
rng = random.Random(12345)
boot = sorted(statistics.median([diffs[rng.randrange(n)] for _ in range(n)])
              for _ in range(2000))
mn, ms = statistics.median(native), statistics.median(seam)
print(f"{mn:.1f} {ms:.1f} {statistics.median(diffs):.1f} "
      f"{100.0 * statistics.median(diffs) / mn:.2f} {extreme / (1 << n):.4f} "
      f"{boot[50]:.1f} {boot[1950]:.1f}")
PY
)"
echo "  native caller      : $native_ns ns/call (median of $FFI_REPEATS)"
echo "  through the seam   : $op_ns ns/call"
echo "  seam cost per op   : $delta_ns ns ($delta_pct%), 95% CI [$delta_lo, $delta_hi] ns,"
echo "                       exact paired p = $paired_p"

echo
echo "== Interop-cost metrics (RQ4) =="
source_counts
echo "  C-ABI entry points (extern \"C\" fns) : $seam_rs"
echo "  seam size: lib.rs = $loc_rs LOC, header = $loc_h LOC"
echo "  'unsafe' functions: core Rust library = $unsafe_lib, FFI seam = $unsafe_seam"
echo "  (core library was NOT modified to add FFI; all interop is in the seam crate)"

# Persist machine-readable metrics so the thesis figure/table is reproducible.
noop_ns=$(grep -oE 'raw FFI crossing: [0-9.]+' "$here/host_run.log" | grep -oE '[0-9.]+' || echo 0)
mkdir -p "$here/results"
cat > "$here/results/metrics.json" <<JSON
{
  "ffi_crossing_ns": ${noop_ns:-0},
  "op_roundtrip_ns": ${op_ns:-0},
  "op_roundtrip_native_ns": ${native_ns:-0},
  "op_seam_delta_ns": ${delta_ns:-0},
  "op_seam_delta_pct": ${delta_pct:-0},
  "op_seam_delta_lo_ns": ${delta_lo:-0},
  "op_seam_delta_hi_ns": ${delta_hi:-0},
  "op_paired_p": ${paired_p:-1},
  "op_repeats": ${FFI_REPEATS:-0},
  "entry_points": ${seam_rs:-0},
  "seam_loc_rust": ${loc_rs:-0},
  "header_loc": ${loc_h:-0},
  "unsafe_core": ${unsafe_lib:-0},
  "unsafe_seam": ${unsafe_seam:-0}
}
JSON
echo "  wrote $here/results/metrics.json"
rm -f "$here/host_run.log"

exit "$host_rc"
