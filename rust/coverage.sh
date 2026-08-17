#!/usr/bin/env bash
# Line and region coverage of the Rust implementation by the parity suite.
#
# The counterpart to cpp/coverage.sh, and it exists for the same reason: the
# fairness argument rests on the parity suite, and a suite's authority is its
# reach. "All tests pass" is compatible with a suite that never executes half
# the code. This is the figure that says which.
#
# What is measured
#   Lines and regions of `src/` executed while running every integration test
#   and the conformance runner over every vector, hand-written and generated.
#   Examples, benches and the runner binary itself are excluded: their coverage
#   is about the harness rather than about the library under study.
#
# Cross-language comparison is NOT the point. llvm-cov counts Rust regions and
# gcov counts C++ lines, and the two implementations have no line-for-line
# correspondence. Read each figure against its own implementation.
#
# Outputs results/coverage.md and results/coverage.csv.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
vec_dir="$root/spec/conformance/vectors"
out_dir="$here/results"
mkdir -p "$out_dir"

GEN_SEEDS=(1 2 3)
GEN_OPS="${GEN_OPS:-400}"

if ! cargo llvm-cov --version >/dev/null 2>&1; then
  echo "cargo-llvm-cov not found; install with: cargo install cargo-llvm-cov --locked" >&2
  exit 2
fi

echo "== Rust coverage of the parity suite =="
echo "$(cargo llvm-cov --version | head -1)"
echo

log="$out_dir/coverage.log"
: >"$log"

# Everything that is not the library itself. The conformance runner is excluded
# for the same reason the C++ script excludes its tests: it is the harness.
IGNORE='(tests|examples|src/bin)/'

echo "clearing previous profile data ..."
cargo llvm-cov clean --workspace --manifest-path "$here/Cargo.toml" >>"$log" 2>&1

echo "running the test suite ..."
cargo llvm-cov --no-report --manifest-path "$here/Cargo.toml" test >>"$log" 2>&1
test_rc=$?

echo "running the conformance vectors ..."
gen_dir="$(mktemp -d)"
trap 'rm -rf "$gen_dir"' EXIT
for seed in "${GEN_SEEDS[@]}"; do
  for profile in lifecycle adversarial capacity routing mixed; do
    python3 "$root/spec/conformance/genvec.py" --seed "$seed" --ops "$GEN_OPS" \
      --profile "$profile" --out "$gen_dir/$profile-$seed.vec" 2>/dev/null || true
  done
done
vec_count=0
for vec in "$vec_dir"/*.vec "$gen_dir"/*.vec; do
  [ -e "$vec" ] || continue
  cargo llvm-cov --no-report --manifest-path "$here/Cargo.toml" \
    run --quiet --bin conformance_runner -- "$vec" >/dev/null 2>>"$log"
  vec_count=$((vec_count + 1))
done

echo "collecting counters ..."
csv="$out_dir/coverage.csv"
cargo llvm-cov report --manifest-path "$here/Cargo.toml" \
  --ignore-filename-regex "$IGNORE" --summary-only >"$out_dir/coverage.txt" 2>>"$log"

# The text summary is the human-readable form; the CSV is parsed out of the
# same run's JSON so the two cannot disagree.
cargo llvm-cov report --manifest-path "$here/Cargo.toml" \
  --ignore-filename-regex "$IGNORE" --json --output-path "$out_dir/coverage.json" >>"$log" 2>&1

python3 - "$out_dir/coverage.json" "$csv" "$out_dir/coverage.rows" <<'PY'
import json, os, sys

with open(sys.argv[1]) as fh:
    data = json.load(fh)

rows = []
for f in data["data"][0]["files"]:
    s = f["summary"]["lines"]
    r = f["summary"]["regions"]
    name = f["filename"]
    marker = f"{os.sep}rust{os.sep}"
    if marker in name:
        name = "rust/" + name.split(marker, 1)[1]
    rows.append((name, s["count"], s["covered"], s["percent"], r["count"], r["covered"], r["percent"]))
rows.sort()

tot = data["data"][0]["totals"]
with open(sys.argv[2], "w") as out:
    out.write("file,lines_total,lines_covered,line_percent,regions_total,regions_covered,region_percent\n")
    for n, lt, lc, lp, rt, rc, rp in rows:
        out.write(f"{n},{lt},{lc},{lp:.1f},{rt},{rc},{rp:.1f}\n")
    out.write("TOTAL,{},{},{:.1f},{},{},{:.1f}\n".format(
        tot["lines"]["count"], tot["lines"]["covered"], tot["lines"]["percent"],
        tot["regions"]["count"], tot["regions"]["covered"], tot["regions"]["percent"]))

with open(sys.argv[3], "w") as out:
    for n, lt, lc, lp, rt, rc, rp in rows:
        out.write(f"| `{n}` | {lt} | {lc} | {lp:.1f}% | {rp:.1f}% |\n")
    out.write("| **Total** | **{}** | **{}** | **{:.1f}%** | **{:.1f}%** |\n".format(
        tot["lines"]["count"], tot["lines"]["covered"],
        tot["lines"]["percent"], tot["regions"]["percent"]))
PY
overall="$(python3 -c "
import csv
print(list(csv.reader(open('$csv')))[-1][3])
")"

md="$out_dir/coverage.md"
{
  echo "# Rust line coverage of the parity suite"
  echo
  echo "Regenerate with \`rust/coverage.sh\`."
  echo
  echo "- \`$(cargo llvm-cov --version | head -1)\`"
  echo "- Driven by: every integration test, plus \`conformance_runner\` over $vec_count vectors"
  echo "  (7 hand-written and the rest generated at $GEN_OPS ops each)"
  echo "- Scope: \`rust/src/\`, excluding \`src/bin/\`, \`tests/\` and \`examples/\`, which are harness"
  echo "  rather than the library under study."
  echo
  echo "| File | Lines | Covered | Line coverage | Region coverage |"
  echo "|---|---:|---:|---:|---:|"
  cat "$out_dir/coverage.rows"
  echo
  echo "Coverage bounds every negative result taken from this suite, the Miri run in"
  echo "\`results/miri.md\` included: an interpreter reports only on code that runs."
  echo
  echo "Not comparable with the C++ figure in \`cpp/results/coverage.md\`: llvm-cov counts"
  echo "Rust regions and gcov counts C++ lines, and the two implementations have no"
  echo "line-for-line correspondence. Each figure is about its own implementation."
} >"$md"

rm -f "$out_dir/coverage.rows"

echo
echo "total line coverage: $overall%"
[ "$test_rc" -ne 0 ] && echo "WARNING: cargo test reported failures under instrumentation; see $log"
echo "wrote $md"
echo "wrote $csv"
