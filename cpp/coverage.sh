#!/usr/bin/env bash
# Line coverage of the C++ implementation by the parity suite.
#
# Why report this at all
# ----------------------
# The thesis rests a fairness claim on the parity suite: both implementations
# were built from one specification and the suite shows they behave alike. That
# argument is only as strong as the suite's reach. "All tests pass" is
# compatible with a suite that never executes half the code, and a reviewer is
# entitled to ask which it is. This is the number that answers them, and it
# bounds every other negative result in the repository -- the sanitiser runs in
# particular, since a sanitiser can only report on code that runs.
#
# What is measured
#   Lines of the library (src/ and include/uecm/) executed while running the
#   CTest binaries and the conformance runner over every vector, hand-written
#   and generated. Test sources themselves are excluded: their coverage is
#   nearly total by construction and would inflate the figure.
#
# Cross-language comparison is NOT the point. gcov counts C++ lines and
# llvm-cov counts Rust regions, and the two implementations do not have
# corresponding lines. Read each figure against its own implementation.
#
# Outputs results/coverage.md and results/coverage.csv.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
vec_dir="$root/spec/conformance/vectors"
out_dir="$here/results"
build="$here/build-coverage"
mkdir -p "$out_dir"

GEN_SEEDS=(1 2 3)
GEN_OPS="${GEN_OPS:-400}"

if ! command -v gcov >/dev/null 2>&1; then
  echo "gcov not found; it ships with gcc" >&2
  exit 2
fi

echo "== C++ coverage of the parity suite =="
echo "gcov: $(gcov --version | head -1)"
echo

log="$out_dir/coverage.log"
: >"$log"

echo "configuring and building an instrumented tree ..."
if ! cmake -S "$here" -B "$build" -G Ninja -DCMAKE_BUILD_TYPE=Debug \
      -DUECM_COVERAGE=ON >>"$log" 2>&1; then
  echo "configure failed; see $log"; exit 1
fi
if ! cmake --build "$build" >>"$log" 2>&1; then
  echo "build failed; see $log"; exit 1
fi

# Clear any counters left by an earlier run, so the figure belongs to this one.
find "$build" -name '*.gcda' -delete

echo "running the test binaries ..."
ctest --test-dir "$build" --output-on-failure >>"$log" 2>&1
ctest_rc=$?

echo "running the conformance vectors ..."
gen_dir="$(mktemp -d)"
trap 'rm -rf "$gen_dir"' EXIT
vec_count=0
for seed in "${GEN_SEEDS[@]}"; do
  for profile in lifecycle adversarial capacity routing mixed; do
    python3 "$root/spec/conformance/genvec.py" --seed "$seed" --ops "$GEN_OPS" \
      --profile "$profile" --out "$gen_dir/$profile-$seed.vec" 2>/dev/null || true
  done
done
for vec in "$vec_dir"/*.vec "$gen_dir"/*.vec; do
  [ -e "$vec" ] || continue
  "$build/conformance_runner" "$vec" >/dev/null 2>>"$log"
  vec_count=$((vec_count + 1))
done

echo "collecting counters ..."
gcov_dir="$build/gcov"
rm -rf "$gcov_dir"; mkdir -p "$gcov_dir"
( cd "$gcov_dir" && find "$build" -name '*.gcno' -exec gcov -p -b {} + ) >>"$log" 2>&1

# gcov writes one .gcov per source it saw, named with the path flattened by '#'.
# Keep the library's own sources and drop everything else: the standard library
# headers dominate by line count and say nothing about this implementation, and
# the test sources would inflate the figure with their own bodies.
summary="$out_dir/coverage.csv"
{
  echo "file,lines_total,lines_covered,percent"
} >"$summary"

total=0
covered=0
declare -a report_rows

while IFS= read -r f; do
  # Recover the original path from the flattened gcov filename.
  src="$(basename "$f" .gcov | tr '#' '/' | sed 's/^\^//')"
  case "$src" in
    */cpp/src/*|*/cpp/include/uecm/*) ;;
    *) continue ;;
  esac
  # Skip the probe-only container: it is not in the compared configuration.
  case "$src" in */flat_map.hpp) continue ;; esac

  # Executable lines are those with a count or '#####'; '-' is not code.
  file_total=$(grep -cE '^ *([0-9]+\*?|#####|\$\$\$\$\$):' "$f" 2>/dev/null || echo 0)
  file_hit=$(grep -cE '^ *[0-9]+\*?:' "$f" 2>/dev/null || echo 0)
  [ "$file_total" -eq 0 ] && continue

  pct=$(awk -v h="$file_hit" -v t="$file_total" 'BEGIN{printf "%.1f", 100*h/t}')
  short="${src#"$root"/}"
  echo "$short,$file_total,$file_hit,$pct" >>"$summary"
  report_rows+=("$(printf '| `%s` | %d | %d | %s%% |' "$short" "$file_total" "$file_hit" "$pct")")
  total=$((total + file_total))
  covered=$((covered + file_hit))
done < <(find "$gcov_dir" -name '*.gcov')

if [ "$total" -eq 0 ]; then
  echo "no library counters found; see $log" >&2
  exit 1
fi

overall=$(awk -v h="$covered" -v t="$total" 'BEGIN{printf "%.1f", 100*h/t}')
echo "TOTAL,$total,$covered,$overall" >>"$summary"

md="$out_dir/coverage.md"
{
  echo "# C++ line coverage of the parity suite"
  echo
  echo "Regenerate with \`cpp/coverage.sh\`."
  echo
  echo "- \`$(gcov --version | head -1)\`"
  echo "- Driven by: every CTest binary, plus \`conformance_runner\` over $vec_count vectors"
  echo "  (7 hand-written and the rest generated at $GEN_OPS ops each)"
  echo "- Scope: \`cpp/src/\` and \`cpp/include/uecm/\`. Test sources are excluded, and so is"
  echo "  \`flat_map.hpp\`, which is an attribution probe rather than part of the compared build."
  echo
  echo "| File | Executable lines | Covered | Coverage |"
  echo "|---|---:|---:|---:|"
  printf '%s\n' "${report_rows[@]}" | sort
  echo "| **Total** | **$total** | **$covered** | **$overall%** |"
  echo
  echo "Coverage bounds every negative result taken from this suite. A sanitiser"
  echo "reports only on code that runs, so \`results/sanitisers.md\` being clean is a"
  echo "statement about these lines and not about the ones the suite never reaches."
  echo
  echo "Not comparable with the Rust figure in \`rust/results/coverage.md\`: gcov counts"
  echo "C++ lines and llvm-cov counts Rust regions, and the two implementations have no"
  echo "line-for-line correspondence. Each figure is about its own implementation."
} >"$md"

echo
echo "total: $covered/$total lines ($overall%)"
[ "$ctest_rc" -ne 0 ] && echo "WARNING: ctest reported failures under instrumentation; see $log"
echo "wrote $md"
echo "wrote $summary"
