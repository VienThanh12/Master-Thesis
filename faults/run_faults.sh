#!/usr/bin/env bash
# RQ2 fault-injection study.
#
# For each defect in the catalogue this script:
#   * builds and runs the C++ version under AddressSanitizer (ASan) and under
#     ThreadSanitizer (TSan), recording whether the tool detected the defect;
#   * compiles the Rust counterpart with rustc, recording whether it is rejected
#     at compile time (and which error codes fire).
#
# It then prints a taxonomy table and writes:
#   results/taxonomy.md   (human-readable + thesis-ready)
#   results/taxonomy.csv  (machine-readable)
#   results/*.log         (raw tool output per case)
#
# WSL2 note: sanitizer runtimes dislike WSL2's ASLR layout, so runs are wrapped in
# `setarch -R` (disable randomization) when available.
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cpp_dir="$here/cpp"
rust_dir="$here/rust"
out_dir="$here/results"
bin_dir="$out_dir/.bin"
mkdir -p "$out_dir" "$bin_dir"

CXX="${CXX:-g++}"
CXXSTD="${CXXSTD:-c++23}"
RUSTC="${RUSTC:-rustc}"

# Disable ASLR for sanitizer runs on WSL2 if setarch is present.
run_prefix=()
if command -v setarch >/dev/null 2>&1; then
  if setarch "$(uname -m)" -R true >/dev/null 2>&1; then
    run_prefix=(setarch "$(uname -m)" -R)
  fi
fi

# Pin the lock-order-inversion detector on rather than inheriting a default that
# differs between runtimes: the upstream sanitizers wiki documents
# detect_deadlocks as off, while the libtsan shipped with g++ 13.3 has it on. An
# outcome that depends on which of those the host happens to provide is not
# evidence. `second_deadlock_stack` reports both edges of a cycle.
export TSAN_OPTIONS="${TSAN_OPTIONS:-detect_deadlocks=1:second_deadlock_stack=1}"

# Defect list: id | source stem | expected sanitizer (asan|tsan) | expected Rust outcome
#
# The script always runs BOTH sanitizers; the third field only picks the "C++
# detection" column. The fourth field records what safe Rust is *expected* to do:
#
#   prevented      -- the Rust counterpart must fail to compile (that failure is the result)
#   not-prevented  -- the Rust counterpart is expected to compile and to exhibit the
#                     defect, because the class lies outside what ownership and the
#                     Send/Sync discipline can rule out. These cases map the boundary
#                     of the guarantee and are as much a part of the answer to RQ2 as
#                     the prevented ones; the script fails loudly if either
#                     expectation is violated in either direction.
defects=(
  "use_after_free|uaf|asan|prevented"
  "double_free|double_free|asan|prevented"
  "iterator_invalidation|iterator_invalidation|asan|prevented"
  "data_race|data_race|tsan|prevented"
  "unguarded_shared_mutation|unguarded_mutation|tsan|prevented"
  "lock_order_deadlock|deadlock|tsan|not-prevented"
  "lost_update|lost_update|tsan|not-prevented"
)

# The deadlock case hangs by construction, so every run is bounded.
RUN_TIMEOUT="${RUN_TIMEOUT:-25}"
timeout_prefix=()
if command -v timeout >/dev/null 2>&1; then
  timeout_prefix=(timeout -k 5 "$RUN_TIMEOUT")
fi

# --- run one C++ variant under a sanitizer; echo detected|clean|buildfail ------
run_cpp_san() {
  local stem="$1" san="$2" tag="$3"
  local src="$cpp_dir/$stem.cpp"
  local bin="$bin_dir/${stem}.${tag}"
  local log="$out_dir/${stem}.${tag}.log"
  # -O0: keep injected defects faithful; the optimizer can otherwise elide them
  # (e.g. new/delete elision removes a double-free at -O1).
  if ! "$CXX" -std="$CXXSTD" -g -O0 -fno-omit-frame-pointer \
        -fsanitize="$san" -pthread -o "$bin" "$src" >"$log" 2>&1; then
    echo "buildfail"
    return
  fi
  # Sanitizers abort() on detection -> nonzero exit; capture output either way.
  # The deadlock case never returns, so the run is bounded by `timeout`.
  "${timeout_prefix[@]}" "${run_prefix[@]}" "$bin" >>"$log" 2>&1
  local rc=$?
  [ $rc -ge 124 ] && echo "  [run timed out after ${RUN_TIMEOUT}s -- hung]" >>"$log"
  if grep -Eq "(AddressSanitizer|ThreadSanitizer|runtime error|SUMMARY: .*Sanitizer)" "$log"; then
    echo "detected"
  elif [ $rc -ge 124 ]; then
    echo "hung"
  else
    echo "clean"
  fi
}

# --- compile one Rust counterpart; echo "rejected:E0499,E0502" or "compiles:<behaviour>" ---
# For a case Rust is expected to reject, compilation failure is the result. For a
# boundary case it is expected to compile, so the binary is then run (bounded) and its
# observable behaviour recorded, since "it compiles" alone would not say whether the
# defect actually survives into the running program.
run_rust() {
  local stem="$1"
  local src="$rust_dir/$stem.rs"
  local log="$out_dir/${stem}.rust.log"
  local bin="$bin_dir/${stem}_rs"
  if ! "$RUSTC" --edition 2021 --crate-type bin -o "$bin" "$src" >"$log" 2>&1; then
    local codes
    codes=$(grep -oE 'E[0-9]{4}' "$log" | sort -u | paste -sd, -)
    [ -z "$codes" ] && codes="compile-error"
    echo "rejected:$codes"
    return
  fi
  echo "--- compiled cleanly; running (bounded at ${RUN_TIMEOUT}s) ---" >>"$log"
  "${timeout_prefix[@]}" "$bin" >>"$log" 2>&1
  local rc=$?
  if [ $rc -ge 124 ]; then
    echo "  [run timed out after ${RUN_TIMEOUT}s -- hung]" >>"$log"
    echo "compiles:hangs"
  elif [ $rc -ne 0 ]; then
    echo "compiles:wrong-result"
  else
    echo "compiles:ran-clean"
  fi
}

# --- positive control for the deadlock detector ---------------------------------
# lock_order_deadlock is recorded as undetected. That outcome only carries
# information if the detector was live, so a case it is known to catch is run
# first. `deadlock_control.cpp` inverts the same two locks without ever blocking,
# which is the shape TSan does report. If this comes back anything but
# "detected", the undetected verdict in the table below is uninformative and the
# script says so instead of letting it pass as a result.
control_outcome=$(run_cpp_san deadlock_control thread tsan)
if [ "$control_outcome" = "detected" ]; then
  control_note="detected (detector live; the undetected verdict below is a real outcome)"
else
  control_note="$control_outcome [CONTROL FAILED -- cannot interpret 'undetected' for lock_order_deadlock]"
fi

# --- environment banner --------------------------------------------------------
cxx_ver=$("$CXX" --version 2>/dev/null | head -1)
rustc_ver=$("$RUSTC" --version 2>/dev/null)
echo "== RQ2 fault-injection study =="
echo "C++ compiler : $cxx_ver (-std=$CXXSTD)"
echo "Rust compiler: $rustc_ver (--edition 2021)"
echo "ASLR wrapper : ${run_prefix[*]:-none}"
echo "TSAN_OPTIONS : $TSAN_OPTIONS"
echo "TSan deadlock-detector control: $control_note"
echo

csv="$out_dir/taxonomy.csv"
md="$out_dir/taxonomy.md"
echo "defect,cpp_asan,cpp_tsan,cpp_detection,rust_compile,rust_expected" >"$csv"

{
  echo "# RQ2 defect-class taxonomy"
  echo
  echo "- C++ compiler: \`$cxx_ver\` (\`-std=$CXXSTD\`)"
  echo "- Rust compiler: \`$rustc_ver\` (\`--edition 2021\`)"
  echo "- ASLR wrapper: \`${run_prefix[*]:-none}\`"
  echo "- \`TSAN_OPTIONS\`: \`$TSAN_OPTIONS\`"
  echo "- TSan deadlock-detector control (\`deadlock_control.cpp\`, inversion without blocking):"
  echo "  **$control_note**"
  echo
  echo "| Defect class | C++ ASan | C++ TSan | C++ detection stage | Rust outcome |"
  echo "|---|---|---|---|---|"
} >"$md"

printf "%-26s %-10s %-10s %-22s %s\n" "defect" "cpp/asan" "cpp/tsan" "cpp detection" "rust"
printf "%-26s %-10s %-10s %-22s %s\n" "------" "--------" "--------" "-------------" "----"

violations=0
for row in "${defects[@]}"; do
  IFS='|' read -r id stem expect expect_rust <<<"$row"
  asan=$(run_cpp_san "$stem" address asan)
  tsan=$(run_cpp_san "$stem" thread  tsan)
  rust=$(run_rust "$stem")

  # C++ detection stage: which tool caught it (runtime), else undetected.
  if [ "$asan" = "detected" ] || [ "$tsan" = "detected" ]; then
    tool=""
    [ "$asan" = "detected" ] && tool="ASan"
    [ "$tsan" = "detected" ] && tool="${tool:+$tool+}TSan"
    detection="runtime ($tool)"
  elif [ "$asan" = "hung" ] || [ "$tsan" = "hung" ]; then
    detection="undetected (hung)"
  else
    detection="undetected"
  fi

  # Rust taxonomy label, checked against the recorded expectation in both directions.
  if [[ "$rust" == rejected:* ]]; then
    rust_label="compile-time prevented (${rust#rejected:})"
    [ "$expect_rust" = "prevented" ] || { rust_label="$rust_label [UNEXPECTED]"; violations=$((violations+1)); }
  else
    case "${rust#compiles:}" in
      hangs)        rust_label="not prevented (compiles; deadlocks)" ;;
      wrong-result) rust_label="not prevented (compiles; wrong result)" ;;
      *)            rust_label="not prevented (compiles; ran clean)" ;;
    esac
    [ "$expect_rust" = "not-prevented" ] || { rust_label="$rust_label [UNEXPECTED]"; violations=$((violations+1)); }
  fi

  printf "%-26s %-10s %-10s %-22s %s\n" "$id" "$asan" "$tsan" "$detection" "$rust_label"
  echo "$id,$asan,$tsan,\"$detection\",\"$rust_label\",$expect_rust" >>"$csv"
  echo "| $id | $asan | $tsan | $detection | $rust_label |" >>"$md"
done

echo
if [ "$violations" -gt 0 ]; then
  echo "WARNING: $violations case(s) did not match the recorded expectation (marked [UNEXPECTED])."
fi
if [ "$control_outcome" != "detected" ]; then
  echo "WARNING: the TSan deadlock-detector control did not fire ($control_outcome)."
  echo "         'undetected' for lock_order_deadlock cannot be read as a finding on this host."
fi
echo "Wrote: $md"
echo "Wrote: $csv"
