#!/usr/bin/env bash
# RQ2, second half, for the two boundary defect classes.
#
# run_faults.sh answers "which defects does each language prevent, and where are
# the rest caught" for the five in-guarantee classes: rustc rejects them at
# build time, the C++ versions need an instrumented binary and a test input that
# reaches the bug. For the two boundary classes -- lock-order deadlock and lost
# update -- it records only that neither language prevents them. The
# detection-stage half is blank for exactly the two cases the two-sided
# catalogue exists to produce.
#
# This fills it in on the Rust side. Loom explores interleavings exhaustively
# under the C11 model; Shuttle samples them with PCT. Both intercept the
# standard synchronisation primitives, and both are aimed at precisely these two
# defects. Running them converts "the defects safe Rust does not prevent are
# caught later rather than never" from an argued position into a measured one.
#
# Every defect model is paired with a control in which the defect is fixed and
# which must come out clean, for the same reason faults/cpp/deadlock_control.cpp
# exists: without it, "the checker found the defect" and "the checker reports
# everything" are the same observation.
#
# Outputs (categorical, so they do not move with host load):
#   results/model_checking.md
#   results/model_checking.csv
#   results/mc-<binary>.log
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
crate="$here/rust-model-checking"
out_dir="$here/results"
mkdir -p "$out_dir"

RUN_TIMEOUT="${RUN_TIMEOUT:-180}"

# binary | defect class | checker | expectation (reported|clean) | role
CASES=(
  "loom_deadlock|lock_order_deadlock|Loom|reported|defect"
  "loom_control_lock_order|lock_order_deadlock|Loom|clean|control"
  "shuttle_deadlock|lock_order_deadlock|Shuttle|reported|defect"
  "shuttle_control_lock_order|lock_order_deadlock|Shuttle|clean|control"
  "loom_lost_update|lost_update|Loom|reported|defect"
  "loom_control_atomic|lost_update|Loom|clean|control"
  "shuttle_lost_update|lost_update|Shuttle|reported|defect"
  "shuttle_control_atomic|lost_update|Shuttle|clean|control"
)

echo "== RQ2 boundary classes under model checking =="
rustc_ver="$(rustc --version)"
echo "Rust compiler: $rustc_ver"

echo "building $crate ..."
if ! cargo build --manifest-path "$crate/Cargo.toml" >"$out_dir/mc-build.log" 2>&1; then
  echo "BUILD FAILED -- see $out_dir/mc-build.log"
  exit 1
fi

loom_ver="$(awk '/^name = "loom"$/{getline; gsub(/version = |"/,""); print; exit}' "$crate/Cargo.lock")"
shuttle_ver="$(awk '/^name = "shuttle"$/{getline; gsub(/version = |"/,""); print; exit}' "$crate/Cargo.lock")"
echo "loom $loom_ver, shuttle $shuttle_ver"
echo

fail=0
declare -A outcome diagnostic

for entry in "${CASES[@]}"; do
  IFS='|' read -r bin defect checker expect role <<<"$entry"
  log="$out_dir/mc-$bin.log"

  # Loom aborts on a detected deadlock. A shell announces a signal-killed child
  # on its own stderr, so the run goes through an inner bash whose stderr is
  # discarded: here the abort is the expected result, not a problem to report.
  bash -c "timeout $RUN_TIMEOUT '$crate/target/debug/$bin' >'$log' 2>&1" 2>/dev/null
  rc=$?

  # Classify. A checker reports a defect by panicking; loom's deadlock panic
  # unwinds through a scheduler-owned thread and aborts (SIGABRT, rc 134),
  # Shuttle and the assertion failures exit 101. A clean model prints its
  # marker, which is checked rather than trusting rc alone: a model that
  # silently did nothing would also exit 0.
  if [ "$rc" -eq 124 ]; then
    got="timeout"
  elif [ "$rc" -eq 0 ]; then
    if grep -q "MODEL-CLEAN" "$log"; then got="clean"; else got="exited 0 without running"; fi
  else
    got="reported"
  fi

  # Pull out the line that says what the tool found, for the table.
  if [ "$got" = "reported" ]; then
    # Backticks are stripped: the diagnostic is rendered inside a backtick-
    # quoted markdown cell, and assertion messages contain their own.
    diag="$(grep -m1 -oE 'deadlock[^"]*|Test deadlocked|assertion .left == right. failed: [^,]*' "$log" \
            | head -1 | tr -d '`' | cut -c1-58)"
    [ -z "$diag" ] && diag="non-zero exit $rc"
  else
    diag="-"
  fi

  outcome["$bin"]="$got"
  diagnostic["$bin"]="$diag"

  flag=""
  if [ "$got" != "$expect" ]; then flag="  [UNEXPECTED: expected $expect]"; fail=1; fi
  printf '%-28s %-8s %-16s %-10s %s%s\n' "$bin" "$checker" "$defect" "$got" "$diag" "$flag"
done

echo

# --- reports ---------------------------------------------------------------
csv="$out_dir/model_checking.csv"
{
  echo "binary,defect_class,checker,role,expected,outcome,diagnostic"
  for entry in "${CASES[@]}"; do
    IFS='|' read -r bin defect checker expect role <<<"$entry"
    echo "$bin,$defect,$checker,$role,$expect,${outcome[$bin]},\"${diagnostic[$bin]}\""
  done
} >"$csv"

md="$out_dir/model_checking.md"
{
  echo "# RQ2 boundary classes under model checking"
  echo
  echo "Regenerate with \`faults/run_model_checking.sh\`. Outcomes are categorical."
  echo
  echo "- Rust compiler: \`$rustc_ver\`"
  echo "- \`loom\` $loom_ver (exhaustive, C11 model), \`shuttle\` $shuttle_ver (PCT, sampled)"
  echo "- Run timeout: ${RUN_TIMEOUT}s"
  echo
  echo "## Detection"
  echo
  echo "| Defect class | Loom | Shuttle | Diagnostic |"
  echo "|---|---|---|---|"
  for defect in lock_order_deadlock lost_update; do
    lo="" sh="" diag=""
    for entry in "${CASES[@]}"; do
      IFS='|' read -r bin d checker expect role <<<"$entry"
      [ "$d" = "$defect" ] || continue
      [ "$role" = "defect" ] || continue
      if [ "$checker" = "Loom" ]; then lo="${outcome[$bin]}"; diag="${diagnostic[$bin]}"; fi
      if [ "$checker" = "Shuttle" ]; then sh="${outcome[$bin]}"; fi
    done
    echo "| \`$defect\` | $lo | $sh | \`$diag\` |"
  done
  echo
  echo "## Controls"
  echo
  echo "The defect models are only informative if the same checker stays quiet on"
  echo "the fixed version. Consistent lock order for the deadlock; one critical"
  echo "section spanning the read-modify-write for the lost update."
  echo
  echo "| Control | Checker | Outcome |"
  echo "|---|---|---|"
  for entry in "${CASES[@]}"; do
    IFS='|' read -r bin d checker expect role <<<"$entry"
    [ "$role" = "control" ] || continue
    echo "| \`$bin\` | $checker | ${outcome[$bin]} |"
  done
  echo
  echo "## Cost, which is the half of RQ2 this answers"
  echo
  echo "Neither \`faults/rust/deadlock.rs\` nor \`faults/rust/lost_update.rs\` runs"
  echo "under either checker as written. Each had to be re-imported against the"
  echo "checker's own \`sync\` and \`thread\` modules, because a tool that does not"
  echo "intercept the primitive cannot schedule it; and each had to be shrunk to"
  echo "model size -- the lost-update model drops from 20 000 iterations per thread"
  echo "to one, and the deadlock model loses the \`thread::sleep\` that widens its"
  echo "window on real hardware."
  echo
  echo "So the Rust answer for the boundary classes is **detected at test time,"
  echo "after a rewrite**. Compare the C++ side, where ASan and TSan take the"
  echo "program as written and need no rewrite at all -- and where, for these same"
  echo "two classes, TSan finds neither (\`results/taxonomy.md\`). The two halves"
  echo "point in opposite directions: C++ tooling accepts the program unchanged and"
  echo "misses the defect; Rust tooling finds it, but only once the program has been"
  echo "rewritten into the tool's primitives. Neither language's story here is the"
  echo "simple one."
} >"$md"

echo "wrote $md"
echo "wrote $csv"
if [ "$fail" -eq 0 ]; then
  echo "ALL CASES AS EXPECTED"
else
  echo "UNEXPECTED OUTCOMES -- see the table above"
fi
exit "$fail"
