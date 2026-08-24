#!/usr/bin/env bash
# RQ2, second half, for the boundary class that lives inside `unsafe`.
#
# run_faults.sh records that rust/seam_double_free.rs compiles and then aborts,
# which is the same outcome its C++ counterpart has. That answers "does the
# language prevent it" and leaves "where is it caught instead" blank, exactly as
# it did for the two concurrency boundary classes before run_model_checking.sh
# filled that in with Loom and Shuttle.
#
# Miri is the tool for this one. It interprets the program against the Stacked
# Borrows aliasing model, so it sees the second Box::from_raw reconstruct
# ownership of storage that is already free.
#
# Two things about the result have to be said with it, and the thesis says both.
# The defect case is paired with a control in which the handle is released once,
# because "Miri reported the double release" and "Miri reports anything that goes
# through Box::from_raw" would otherwise be the same observation. And Miri
# interprets Rust: it cannot execute a C++ host, so what is checked here is a
# Rust stand-in for the host. The tool that catches this defect cannot be pointed
# at the configuration the defect is deployed in, which is the seam of ffi/.
#
# Outputs (categorical, so they do not move with host load):
#   results/miri.md
#   results/miri.csv
#   results/miri-<case>.log
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rust_dir="$here/rust"
out_dir="$here/results"
work="$out_dir/.miri"
mkdir -p "$out_dir" "$work"

RUN_TIMEOUT="${RUN_TIMEOUT:-300}"

# case | defect class | expectation (reported|clean) | role
CASES=(
  "seam_double_free|seam_double_free|reported|defect"
  "seam_double_free_control|seam_double_free|clean|control"
)

echo "== RQ2 unsafe boundary class under Miri =="

if ! cargo +nightly miri --version >/dev/null 2>&1; then
  echo "SKIP: Miri is not installed."
  echo "      rustup toolchain install nightly --component miri"
  exit 0
fi
miri_ver="$(cargo +nightly miri --version 2>/dev/null)"
rustc_ver="$(rustc --version)"
echo "Rust compiler: $rustc_ver"
echo "$miri_ver"

# Miri needs a package rather than a loose file, so one is generated here with
# its binaries pointing straight at the catalogue sources. Copying them would
# create a second copy of a defect program that could drift from the one the
# fault runner builds.
{
  echo '[package]'
  echo 'name = "miri-cases"'
  echo 'version = "0.0.0"'
  echo 'edition = "2021"'
  echo
  for row in "${CASES[@]}"; do
    IFS='|' read -r case_id _ _ _ <<<"$row"
    echo '[[bin]]'
    echo "name = \"$case_id\""
    echo "path = \"$rust_dir/$case_id.rs\""
    echo
  done
} >"$work/Cargo.toml"

printf "%-32s %-10s %-10s %s\n" "case" "role" "outcome" "diagnostic"
printf "%-32s %-10s %-10s %s\n" "----" "----" "-------" "----------"

csv="$out_dir/miri.csv"
md="$out_dir/miri.md"
echo "case,defect,role,expected,outcome,diagnostic" >"$csv"
{
  echo "# RQ2: the unsafe boundary class under Miri"
  echo
  echo "Regenerate with \`faults/run_miri.sh\`. Outcomes are categorical."
  echo
  echo "- Rust compiler: \`$rustc_ver\`"
  echo "- \`$miri_ver\`"
  echo "- Run timeout: ${RUN_TIMEOUT}s"
  echo
  echo "| Case | Role | Outcome | Diagnostic |"
  echo "|---|---|---|---|"
} >"$md"

violations=0
for row in "${CASES[@]}"; do
  IFS='|' read -r case_id defect expected role <<<"$row"
  log="$out_dir/miri-$case_id.log"
  timeout -k 5 "$RUN_TIMEOUT" \
    cargo +nightly miri run --manifest-path "$work/Cargo.toml" --bin "$case_id" \
    >"$log" 2>&1
  rc=$?

  if [ $rc -eq 124 ] || [ $rc -eq 137 ]; then
    outcome="timeout"
    diagnostic="exceeded ${RUN_TIMEOUT}s"
  elif grep -q "Undefined Behavior" "$log"; then
    outcome="reported"
    diagnostic="$(grep -m1 "error: Undefined Behavior" "$log" \
                  | sed 's/^error: Undefined Behavior: //' | cut -c1-72)"
  else
    outcome="clean"
    diagnostic="-"
  fi

  if [ "$outcome" != "$expected" ]; then
    outcome="$outcome [UNEXPECTED]"
    violations=$((violations + 1))
  fi

  printf "%-32s %-10s %-10s %s\n" "$case_id" "$role" "$outcome" "$diagnostic"
  echo "$case_id,$defect,$role,$expected,\"$outcome\",\"$diagnostic\"" >>"$csv"
  echo "| \`$case_id\` | $role | $outcome | \`$diagnostic\` |" >>"$md"
done

{
  echo
  echo "## What this answers, and what it does not"
  echo
  echo "The compiler accepts the double release, because \`unsafe\` is where the"
  echo "obligation moves from the compiler to the reviewer. Miri catches it, and"
  echo "names it. So the stage for this class is test time rather than build time,"
  echo "and the cost is an interpreter run rather than a rejected compile."
  echo
  echo "The limit is the one that matters for a migration. Miri interprets Rust."
  echo "It cannot execute the C++ host that a real seam has on the other side, so"
  echo "the case checked here uses a Rust stand-in for that host. The tool that"
  echo "finds this defect cannot be pointed at the configuration the defect ships"
  echo "in, which is the seam of \`ffi/\`."
} >>"$md"

echo
if [ "$violations" -gt 0 ]; then
  echo "WARNING: $violations case(s) did not match the recorded expectation."
fi
echo "Wrote: $md"
echo "Wrote: $csv"
