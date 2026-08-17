#!/usr/bin/env bash
# Run the whole C++ parity suite under dynamic analysis.
#
# Why this is evidence and not just hygiene
# -----------------------------------------
# The thesis compares two implementations of one specification and argues the
# comparison is fair. Safe Rust rules out data races, use-after-free and
# out-of-bounds access at compile time, so the Rust arm carries that guarantee
# by construction. The C++ arm carries no such guarantee, and "the tests pass"
# does not supply one: a program with a latent data race or a read past the end
# of a buffer passes tests routinely, and can still be the reason a tail
# measurement looks the way it does.
#
# faults/ already shows these tools catch the defects when they are injected
# deliberately. That establishes the detectors work. This script is the other
# half: pointing the same detectors at the real implementation, over the whole
# parity suite, and finding nothing.
#
# What runs
#   * every CTest binary, under each sanitiser in turn;
#   * the conformance runner over every hand-written vector, plus a small
#     generated family, so the instrumented paths include the threaded Service
#     under randomised operation sequences rather than only the unit tests.
#
# ASan and TSan cannot be combined, so they are separate build trees. UBSan
# rides along with ASan and also runs on its own, because -fno-sanitize-recover
# turns a diagnostic into a failure and that is the point.
#
# Outputs results/sanitisers.md and results/sanitisers.csv, both categorical:
# like faults/, the outcomes are "clean" or "reports", never a number, so they
# do not move with host load and are safe to collect on the virtualised host.
#
# WSL2 note: sanitiser runtimes dislike WSL2's ASLR layout, so runs are wrapped
# in `setarch -R` when available, matching faults/run_faults.sh.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
vec_dir="$root/spec/conformance/vectors"
out_dir="$here/results"
mkdir -p "$out_dir"

SANITISERS=("address+undefined" "thread" "undefined")
GEN_SEEDS=(1 2 3)
GEN_OPS="${GEN_OPS:-400}"

# Disable ASLR for sanitiser runs on WSL2 if setarch is present.
run_prefix=()
if command -v setarch >/dev/null 2>&1; then
  if setarch "$(uname -m)" -R true >/dev/null 2>&1; then
    run_prefix=(setarch "$(uname -m)" -R)
  fi
fi

# Pin the detector options rather than inheriting defaults that differ between
# runtimes, for the reason faults/run_faults.sh gives: an outcome that depends
# on which libtsan the host happens to ship is not evidence.
export TSAN_OPTIONS="${TSAN_OPTIONS:-detect_deadlocks=1:second_deadlock_stack=1:halt_on_error=1}"
export ASAN_OPTIONS="${ASAN_OPTIONS:-detect_leaks=1:detect_stack_use_after_return=1:strict_string_checks=1}"
export UBSAN_OPTIONS="${UBSAN_OPTIONS:-print_stacktrace=1:halt_on_error=1}"

cxx_ver="$("${CXX:-g++}" --version | head -1)"

echo "== C++ parity suite under dynamic analysis =="
echo "C++ compiler : $cxx_ver"
echo "ASLR wrapper : ${run_prefix[*]:-none}"
echo "ASAN_OPTIONS : $ASAN_OPTIONS"
echo "TSAN_OPTIONS : $TSAN_OPTIONS"
echo "UBSAN_OPTIONS: $UBSAN_OPTIONS"
echo

# Generate a small random family once and reuse it across sanitisers, so each
# tool sees the same operation sequences.
gen_dir="$(mktemp -d)"
trap 'rm -rf "$gen_dir"' EXIT
gen_vecs=()
if python3 "$root/spec/conformance/model.py" --self-test >/dev/null 2>&1; then
  for seed in "${GEN_SEEDS[@]}"; do
    for profile in lifecycle adversarial capacity; do
      out="$gen_dir/$profile-$seed.vec"
      if python3 "$root/spec/conformance/genvec.py" --seed "$seed" --ops "$GEN_OPS" \
           --profile "$profile" --out "$out" 2>/dev/null; then
        gen_vecs+=("$out")
      fi
    done
  done
fi
echo "generated vectors for the instrumented runs: ${#gen_vecs[@]}"
echo

fail=0
declare -A ctest_result
declare -A vector_result

for san in "${SANITISERS[@]}"; do
  slug="${san//+/-}"
  build="$here/build-san-$slug"
  log="$out_dir/sanitiser-$slug.log"

  echo "---- $san ----"
  : >"$log"

  if ! cmake -S "$here" -B "$build" -G Ninja \
        -DCMAKE_BUILD_TYPE=Release -DUECM_SANITIZER="$san" >>"$log" 2>&1; then
    echo "  configure FAILED (see $log)"
    ctest_result[$san]="configure failed"; vector_result[$san]="skipped"; fail=1; continue
  fi
  if ! cmake --build "$build" >>"$log" 2>&1; then
    echo "  build FAILED (see $log)"
    ctest_result[$san]="build failed"; vector_result[$san]="skipped"; fail=1; continue
  fi

  # -- unit and property suites --
  if "${run_prefix[@]}" ctest --test-dir "$build" --output-on-failure >>"$log" 2>&1; then
    ctest_result[$san]="clean"
    echo "  ctest            clean"
  else
    ctest_result[$san]="REPORTS"
    echo "  ctest            REPORTS -- see $log"
    fail=1
  fi

  # -- conformance vectors through the instrumented threaded Service --
  runner="$build/conformance_runner"
  bad=0 ran=0
  for vec in "$vec_dir"/*.vec "${gen_vecs[@]}"; do
    [ -e "$vec" ] || continue
    ran=$((ran + 1))
    if ! "${run_prefix[@]}" "$runner" "$vec" >/dev/null 2>>"$log"; then
      bad=$((bad + 1))
      echo "  vector FAILED: $(basename "$vec")"
    fi
  done
  if [ "$bad" -eq 0 ]; then
    vector_result[$san]="clean ($ran vectors)"
    echo "  conformance      clean ($ran vectors)"
  else
    vector_result[$san]="REPORTS ($bad/$ran)"
    echo "  conformance      REPORTS ($bad/$ran) -- see $log"
    fail=1
  fi
  echo
done

# --- reports ---------------------------------------------------------------
csv="$out_dir/sanitisers.csv"
{
  echo "sanitiser,ctest,conformance_vectors"
  for san in "${SANITISERS[@]}"; do
    echo "$san,${ctest_result[$san]:-not run},${vector_result[$san]:-not run}"
  done
} >"$csv"

md="$out_dir/sanitisers.md"
{
  echo "# C++ parity suite under dynamic analysis"
  echo
  echo "Regenerate with \`cpp/sanitise.sh\`. Categorical outcomes only, so they do"
  echo "not move with host load."
  echo
  echo "- C++ compiler: \`$cxx_ver\`"
  echo "- ASLR wrapper: \`${run_prefix[*]:-none}\`"
  echo "- \`ASAN_OPTIONS\`: \`$ASAN_OPTIONS\`"
  echo "- \`TSAN_OPTIONS\`: \`$TSAN_OPTIONS\`"
  echo "- \`UBSAN_OPTIONS\`: \`$UBSAN_OPTIONS\`"
  echo "- Generated vectors per run: ${#gen_vecs[@]} (at $GEN_OPS ops each)"
  echo
  echo "| Sanitiser | Test binaries | Conformance vectors |"
  echo "|---|---|---|"
  for san in "${SANITISERS[@]}"; do
    echo "| \`$san\` | ${ctest_result[$san]:-not run} | ${vector_result[$san]:-not run} |"
  done
  echo
  if [ "$fail" -eq 0 ]; then
    echo "All clean: no memory error, no undefined behaviour, and no data race was"
    echo "reported anywhere in the C++ implementation across the parity suite."
    echo
    echo "This is a negative result and is worth exactly what a negative result is"
    echo "worth: sanitisers observe the executions that happen, so this covers the"
    echo "paths the suite drives and says nothing about paths it does not. It is not"
    echo "the compile-time guarantee the Rust arm has, and the distinction is the"
    echo "point -- the coverage-bounded version of the same property."
  else
    echo "At least one run reported. See the per-sanitiser logs in this directory;"
    echo "a report here is a defect in the implementation, not in the harness."
  fi
} >"$md"

echo "wrote $md"
echo "wrote $csv"
if [ "$fail" -eq 0 ]; then
  echo "ALL SANITISER RUNS CLEAN"
else
  echo "SANITISER REPORTS DETECTED"
fi
exit "$fail"
