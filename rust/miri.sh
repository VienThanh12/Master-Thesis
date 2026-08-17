#!/usr/bin/env bash
# Run the Rust test suite under Miri.
#
# What this adds, given the library has no `unsafe`
# -------------------------------------------------
# spec §12 records that the Rust core contains no `unsafe`, and safe Rust is
# data-race-free by construction, so a reasonable reading is that Miri has
# nothing to find. That reading is what this checks rather than assumes, and it
# is worth checking for two reasons.
#
# First, "no `unsafe` in the core" is a claim about the code in `rust/src`, not
# about the standard library it calls into or about the compiler's own
# reasoning. Miri interprets the program against the Stacked Borrows aliasing
# model and reports undefined behaviour wherever it actually occurs.
#
# Second, it is the counterpart to `cpp/sanitise.sh`. That script runs the C++
# parity suite under ASan, UBSan and TSan and reports it clean. Reporting only
# the C++ half would leave the comparison lopsided: the C++ arm would be the one
# with dynamic-analysis evidence attached. Both arms get the same treatment, and
# the asymmetry that remains is then a real one -- the C++ result is bounded by
# the executions the suite drives, while the Rust result restates a property the
# compiler already enforced.
#
# Scope
#   Miri interprets, so it is slow: the threaded `Service` tests spawn eight
#   workers each and the concurrency suite is impractical under it. The default
#   selection is the single-threaded state-machine and invariant work, which is
#   where aliasing questions actually live. Pass --all to attempt everything.
#
# Outputs results/miri.md and results/miri.csv (categorical, host-independent).
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out_dir="$here/results"
mkdir -p "$out_dir"

TOOLCHAIN="${MIRI_TOOLCHAIN:-nightly}"

# Stacked Borrows is the default; the extra flags make the run stricter rather
# than faster. -Zmiri-disable-isolation is required because the suite reads the
# clock and spawns threads.
export MIRIFLAGS="${MIRIFLAGS:--Zmiri-disable-isolation -Zmiri-strict-provenance}"

TARGETS=("--test" "state_matrix" "--test" "invariants")
ALL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --all) ALL=1; shift ;;
    -h|--help) sed -n '2,32p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [ "$ALL" -eq 1 ]; then
  TARGETS=()
fi

echo "== Rust suite under Miri =="

if ! rustup toolchain list 2>/dev/null | grep -q "^${TOOLCHAIN}"; then
  echo "toolchain '$TOOLCHAIN' is not installed."
  echo "install it with:  rustup toolchain install $TOOLCHAIN --component miri"
  exit 2
fi
if ! rustup run "$TOOLCHAIN" cargo miri --version >/dev/null 2>&1; then
  echo "miri is not available on '$TOOLCHAIN'."
  echo "install it with:  rustup component add miri --toolchain $TOOLCHAIN"
  exit 2
fi

miri_ver="$(rustup run "$TOOLCHAIN" cargo miri --version 2>/dev/null | head -1)"
rustc_ver="$(rustup run "$TOOLCHAIN" rustc --version 2>/dev/null | head -1)"
echo "toolchain : $TOOLCHAIN"
echo "rustc     : $rustc_ver"
echo "miri      : $miri_ver"
echo "MIRIFLAGS : $MIRIFLAGS"
if [ "$ALL" -eq 1 ]; then
  echo "scope     : every test target (slow; the threaded suites may take a long time)"
else
  echo "scope     : ${TARGETS[*]}"
fi
echo

log="$out_dir/miri.log"
start=$(date +%s)
if rustup run "$TOOLCHAIN" cargo miri test --manifest-path "$here/Cargo.toml" \
     "${TARGETS[@]+"${TARGETS[@]}"}" >"$log" 2>&1; then
  status="clean"
  rc=0
else
  status="REPORTS"
  rc=1
fi
elapsed=$(( $(date +%s) - start ))

passed="$(grep -oE '[0-9]+ passed' "$log" | awk '{s+=$1} END {print s+0}')"
ub="$(grep -c 'Undefined Behavior' "$log" || true)"

echo "outcome   : $status"
echo "tests run : $passed"
echo "UB reports: $ub"
echo "elapsed   : ${elapsed}s"
[ "$rc" -ne 0 ] && { echo; echo "--- tail of $log ---"; tail -30 "$log"; }

csv="$out_dir/miri.csv"
{
  echo "toolchain,scope,tests_passed,ub_reports,outcome,elapsed_s"
  echo "$TOOLCHAIN,\"${TARGETS[*]:-all}\",$passed,$ub,$status,$elapsed"
} >"$csv"

md="$out_dir/miri.md"
{
  echo "# Rust suite under Miri"
  echo
  echo "Regenerate with \`rust/miri.sh\`. Categorical outcome; the elapsed time is"
  echo "incidental and is not a measurement."
  echo
  echo "- Toolchain: \`$TOOLCHAIN\` ($rustc_ver)"
  echo "- \`$miri_ver\`"
  echo "- \`MIRIFLAGS\`: \`$MIRIFLAGS\`"
  echo "- Scope: \`${TARGETS[*]:-all test targets}\`"
  echo
  echo "| Tests passed | Undefined-behaviour reports | Outcome |"
  echo "|---:|---:|---|"
  echo "| $passed | $ub | $status |"
  echo
  if [ "$rc" -eq 0 ]; then
    echo "Clean. Miri found no undefined behaviour and no aliasing violation under"
    echo "Stacked Borrows with strict provenance."
    echo
    echo "This is a weaker statement than it looks, and deliberately so. The core"
    echo "contains no \`unsafe\` (spec §12), so the aliasing discipline Miri checks is"
    echo "already enforced by the compiler; the run confirms the property rather than"
    echo "discovering it. Its value is symmetry with \`cpp/sanitise.sh\`: both arms are"
    echo "now checked by the strongest dynamic tool their language offers, so the"
    echo "difference between them is a difference in what the tools can guarantee and"
    echo "not in whether anyone looked."
  else
    echo "Miri reported. See \`miri.log\`; a report against an \`unsafe\`-free core would"
    echo "be a significant finding and should be investigated before anything else."
  fi
} >"$md"

echo
echo "wrote $md"
echo "wrote $csv"
exit "$rc"
