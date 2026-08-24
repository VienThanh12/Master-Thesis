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

# The deadlock case hangs by construction, so every run is bounded.
RUN_TIMEOUT="${RUN_TIMEOUT:-25}"
# Bound for a repeated case. Shorter because repeated cases are the ones that
# hang, and paying 25 s a repeat would dominate the run for no extra
# information: the detection rate is the same at 3 s as at 25 s.
REPEAT_TIMEOUT="${REPEAT_TIMEOUT:-3}"
# How many times to repeat the sanitizer named in a case's third field. Only
# lock_order_deadlock needs it; see run_cpp_san.
DEADLOCK_REPEATS="${DEADLOCK_REPEATS:-12}"

# Defect list:
#   id | source stem | expected sanitizer (asan|tsan|ubsan) | expected Rust outcome |
#   rustc flags | repeats | display label | observable
#
# The script always runs ALL THREE sanitizers; the third field only picks the
# "C++ detection" column. The fourth field records what safe Rust is *expected*
# to do:
#
#   prevented      -- the Rust counterpart must fail to compile (that failure is the result)
#   not-prevented  -- the Rust counterpart is expected to compile and to exhibit the
#                     defect, because the class lies outside what ownership and the
#                     Send/Sync discipline can rule out. These cases map the boundary
#                     of the guarantee and are as much a part of the answer to RQ2 as
#                     the prevented ones; the script fails loudly if either
#                     expectation is violated in either direction.
#
# The fifth field is extra `rustc` flags for that case, empty for almost all of
# them. It exists for `integer_overflow`, where the outcome depends on the build
# profile: `debug-assertions` on turns the wrap into a panic, and a panic is a
# detection. The thesis compares an `opt-level = 2` Rust build against `-O2`
# (spec §3), and that profile leaves `overflow-checks` off, so the case must be
# built the way the measured configuration is built or the table would record a
# detection the compared arm does not have.
#
# The seventh and eighth fields exist so the thesis table can be generated from
# this run instead of typed beside it. Seven is the display name of the class and
# eight names, for a boundary case, *which* misbehaviour the program exhibits.
# The runner measures whether the program misbehaves and refuses a boundary case
# that comes out clean, so field eight labels a checked outcome rather than
# standing in for one: "leaks" is printed only for a run that ended non-zero
# because nothing was dropped.
defects=(
  "use_after_free|uaf|asan|prevented|||Use-after-free|"
  "double_free|double_free|asan|prevented|||Double-free|"
  "iterator_invalidation|iterator_invalidation|asan|prevented|||Iterator invalidation|"
  "data_race|data_race|tsan|prevented|||Data race|"
  "unguarded_shared_mutation|unguarded_mutation|tsan|prevented|||Unguarded shared mutation|"
  "use_after_move|use_after_move|none|prevented|||Use-after-move|"
  "thread_unsafe_sharing|thread_unsafe_sharing|tsan|prevented|||Thread-unsafe handle shared|"
  "lock_order_deadlock|deadlock|tsan|not-prevented||$DEADLOCK_REPEATS|Lock-order deadlock|deadlocks"
  "lost_update|lost_update|tsan|not-prevented|||Lost update|wrong result"
  "leak_cycle|leak_cycle|asan|not-prevented|||Reference-cycle leak|leaks"
  "integer_overflow|integer_overflow|ubsan|not-prevented|-O -C debug-assertions=off -C overflow-checks=off||Integer overflow (release)|wrong result"
  "worker_failure_blast_radius|worker_failure|none|not-prevented|||Worker-failure blast radius|shard outage"
  "seam_double_free|seam_double_free|asan|not-prevented|||Double-free across the seam|aborts"
  "forgotten_guard|forgotten_guard|none|not-prevented|||Forgotten lock guard|deadlocks"
)

timeout_prefix=()
if command -v timeout >/dev/null 2>&1; then
  timeout_prefix=(timeout -k 5 "$RUN_TIMEOUT")
fi

# --- run one C++ variant under a sanitizer -------------------------------------
# Sets `last_outcome` to detected|flaky|clean|hung|buildfail and `last_rate` to
# "k/N" when the case was repeated. Two globals rather than an echoed result,
# because a command substitution would run this in a subshell and the rate
# would not survive it.
#
# Repeats exist because one outcome here is schedule-dependent. TSan builds its
# lock-order graph from acquisitions that *succeed*, and `deadlock.cpp` loops:
# on some runs an inversion completes without blocking, closes the cycle and is
# reported; on others the first inversion blocks and the cycle never closes. A
# single run therefore records whichever happened that day, and the tracked
# taxonomy would flip between commits for no reason anyone could see. Measuring
# the rate turns that into the finding it actually is.
last_rate=""
last_outcome=""
run_cpp_san() {
  local stem="$1" san="$2" tag="$3" repeats="${4:-1}"
  local src="$cpp_dir/$stem.cpp"
  local bin="$bin_dir/${stem}.${tag}"
  local log="$out_dir/${stem}.${tag}.log"
  last_rate=""
  last_outcome=""
  # -O0: keep injected defects faithful; the optimizer can otherwise elide them
  # (e.g. new/delete elision removes a double-free at -O1).
  if ! "$CXX" -std="$CXXSTD" -g -O0 -fno-omit-frame-pointer \
        -fsanitize="$san" -pthread -o "$bin" "$src" >"$log" 2>&1; then
    last_outcome="buildfail"
    return
  fi

  # A repeated case is one that hangs, so it gets the short bound: the report,
  # when it comes, comes within the first few iterations (verified: the rate is
  # the same at 3 s and at 25 s).
  local bound=("${timeout_prefix[@]}")
  [ "$repeats" -gt 1 ] && bound=(timeout -k 2 "$REPEAT_TIMEOUT")

  local hits=0 hung_runs=0 i
  for (( i = 0; i < repeats; i++ )); do
    local run_log="$log"
    [ "$repeats" -gt 1 ] && run_log="$log.run$i"
    : >"$run_log"
    # Several of these defects abort by design -- glibc's double-free check,
    # std::terminate, a sanitizer halting. A shell announces a signal-killed
    # child on its own stderr, so the run goes through an inner bash whose
    # stderr is discarded; here the abort is the expected outcome.
    bash -c '"$@"' _ "${bound[@]}" "${run_prefix[@]}" "$bin" >>"$run_log" 2>&1
    local rc=$?
    # 124 is `timeout` firing; 137 is the follow-up SIGKILL from -k. Anything
    # else above 128 is the program dying on a signal, which is a different
    # outcome: an abort() from glibc's double-free check or from
    # std::terminate is the defect manifesting, not the run hanging.
    if [ $rc -eq 124 ] || [ $rc -eq 137 ]; then
      hung_runs=$((hung_runs + 1))
      echo "  [run timed out -- hung]" >>"$run_log"
    fi
    if grep -Eq "(AddressSanitizer|ThreadSanitizer|runtime error|SUMMARY: .*Sanitizer)" "$run_log"; then
      hits=$((hits + 1))
    fi
    # Keep the first repeat as the representative log under the plain name.
    [ "$repeats" -gt 1 ] && [ "$i" -eq 0 ] && cp "$run_log" "$log"
  done

  if [ "$repeats" -gt 1 ]; then
    last_rate="$hits/$repeats"
    if   [ "$hits" -eq 0 ];          then last_outcome="clean"
    elif [ "$hits" -eq "$repeats" ]; then last_outcome="detected"
    else                                  last_outcome="flaky"; fi
    return
  fi

  if   [ "$hits" -gt 0 ];      then last_outcome="detected"
  elif [ "$hung_runs" -gt 0 ]; then last_outcome="hung"
  else                              last_outcome="clean"; fi
}

# --- compile one Rust counterpart; echo "rejected:E0499,E0502" or "compiles:<behaviour>" ---
# For a case Rust is expected to reject, compilation failure is the result. For a
# boundary case it is expected to compile, so the binary is then run (bounded) and its
# observable behaviour recorded, since "it compiles" alone would not say whether the
# defect actually survives into the running program.
run_rust() {
  local stem="$1"
  local extra_flags="${2:-}"
  local src="$rust_dir/$stem.rs"
  local log="$out_dir/${stem}.rust.log"
  local bin="$bin_dir/${stem}_rs"
  # shellcheck disable=SC2086  # extra_flags is a deliberate word-split flag list
  if ! "$RUSTC" --edition 2021 --crate-type bin $extra_flags -o "$bin" "$src" >"$log" 2>&1; then
    local codes
    codes=$(grep -oE 'E[0-9]{4}' "$log" | sort -u | paste -sd, -)
    [ -z "$codes" ] && codes="compile-error"
    echo "rejected:$codes"
    return
  fi
  echo "--- compiled cleanly; running (bounded at ${RUN_TIMEOUT}s) ---" >>"$log"
  # One of these defects aborts by design, and a shell announces a signal-killed
  # child on its own stderr, so the run goes through an inner bash whose stderr
  # is discarded. Same treatment as the C++ side, and for the same reason.
  bash -c '"$@"' _ "${timeout_prefix[@]}" "$bin" >>"$log" 2>&1
  local rc=$?
  # 124 is `timeout` firing and 137 its follow-up SIGKILL. Any other status
  # above 128 is the program dying on a signal, which is a different outcome:
  # an abort from glibc's double-free check is the defect manifesting, not the
  # run hanging. Reading every high status as a timeout would record the seam
  # double free as a deadlock.
  if [ $rc -eq 124 ] || [ $rc -eq 137 ]; then
    echo "  [run timed out after ${RUN_TIMEOUT}s -- hung]" >>"$log"
    echo "compiles:hangs"
  elif [ $rc -gt 128 ]; then
    echo "  [killed by signal $((rc - 128))]" >>"$log"
    echo "compiles:crashes"
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
run_cpp_san deadlock_control thread tsan
control_outcome="$last_outcome"
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
echo "defect,label,cpp_asan,cpp_tsan,cpp_ubsan,cpp_detection,rust_compile,rust_observed,rust_expected,note" >"$csv"

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
  echo "\`integer_overflow\` is built with \`-O -C overflow-checks=off\` so it matches"
  echo "the \`opt-level = 2\` profile the thesis compares (spec §3). With the \`rustc\`"
  echo "defaults it would panic, and the table would record a detection the measured"
  echo "configuration does not have."
  echo
  echo "\`lock_order_deadlock\` is run $DEADLOCK_REPEATS times under TSan rather than once."
  echo "Its detection is schedule-dependent: TSan closes a lock-order cycle only from"
  echo "acquisitions that *succeed*, so a run whose first inversion blocks never"
  echo "produces the second edge. \`flaky\` records that, where a single run would"
  echo "record whichever outcome the scheduler happened to give."
  echo
  echo "| Defect class | C++ ASan | C++ TSan | C++ UBSan | C++ detection stage | Rust outcome | Note |"
  echo "|---|---|---|---|---|---|---|"
} >"$md"

printf "%-28s %-9s %-9s %-9s %-30s %s\n" "defect" "cpp/asan" "cpp/tsan" "cpp/ubsan" "cpp detection" "rust"
printf "%-28s %-9s %-9s %-9s %-30s %s\n" "------" "--------" "--------" "---------" "-------------" "----"

# A sanitizer counts as having caught the defect if it reported on every run or
# on some of them; the two are kept apart in the columns and merged only here.
hit() { [ "$1" = "detected" ] || [ "$1" = "flaky" ]; }

violations=0
for row in "${defects[@]}"; do
  IFS='|' read -r id stem expect expect_rust rust_flags repeats label observed <<<"$row"
  repeats="${repeats:-1}"
  label="${label:-$id}"
  note=""

  # Repeats apply only to the sanitizer named in field 3: that is the one whose
  # outcome the case is about, and repeating the other two would triple the
  # runtime to re-confirm two cells that are not in question.
  run_cpp_san "$stem" address   asan  "$([ "$expect" = asan  ] && echo "$repeats" || echo 1)"
  asan="$last_outcome"
  [ -n "$last_rate" ] && note="ASan reported in $last_rate runs"
  run_cpp_san "$stem" thread    tsan  "$([ "$expect" = tsan  ] && echo "$repeats" || echo 1)"
  tsan="$last_outcome"
  [ -n "$last_rate" ] && note="TSan reported in $last_rate runs"
  # UBSan is a third axis rather than a refinement of the other two: signed
  # overflow is invisible to both ASan and TSan, so without this column the
  # integer_overflow class would read as undetected in C++ when it is not.
  run_cpp_san "$stem" undefined ubsan "$([ "$expect" = ubsan ] && echo "$repeats" || echo 1)"
  ubsan="$last_outcome"
  [ -n "$last_rate" ] && note="UBSan reported in $last_rate runs"
  rust=$(run_rust "$stem" "$rust_flags")

  # C++ detection stage: which tool caught it, and whether reliably. "flaky" is
  # kept distinct from "detected" on purpose -- a detector that fires on a
  # minority of runs is a materially different proposition for a CI pipeline,
  # and collapsing the two would report it as a clean catch.
  if hit "$asan" || hit "$tsan" || hit "$ubsan"; then
    tool=""
    hit "$asan"  && tool="ASan"
    hit "$tsan"  && tool="${tool:+$tool+}TSan"
    hit "$ubsan" && tool="${tool:+$tool+}UBSan"
    if [ "$asan" = "flaky" ] || [ "$tsan" = "flaky" ] || [ "$ubsan" = "flaky" ]; then
      detection="runtime, intermittent ($tool)"
    else
      detection="runtime ($tool)"
    fi
  elif [ "$asan" = "hung" ] || [ "$tsan" = "hung" ] || [ "$ubsan" = "hung" ]; then
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
      crashes)      rust_label="not prevented (compiles; crashes)" ;;
      wrong-result) rust_label="not prevented (compiles; wrong result)" ;;
      *)            rust_label="not prevented (compiles; ran clean)" ;;
    esac
    if [ "$expect_rust" != "not-prevented" ]; then
      rust_label="$rust_label [UNEXPECTED]"
      violations=$((violations+1))
    else
      # A boundary case earns its place in the catalogue by misbehaving, so the
      # run has to agree with the misbehaviour field eight names. "deadlocks"
      # means the harness had to kill the program; anything else means the
      # program ended by itself with a failing status. Without this check a
      # boundary case that quietly stopped reproducing would still be recorded
      # as "not prevented" and would still read as evidence.
      case "$observed" in
        deadlocks) want="hangs" ;;
        aborts)    want="crashes" ;;
        "")        want="" ;;
        *)         want="wrong-result" ;;
      esac
      if [ -z "$want" ]; then
        rust_label="$rust_label [UNEXPECTED: no misbehaviour recorded for a boundary case]"
        violations=$((violations+1))
      elif [ "${rust#compiles:}" != "$want" ]; then
        rust_label="$rust_label [UNEXPECTED: recorded as '$observed', ran as '${rust#compiles:}']"
        violations=$((violations+1))
      fi
    fi
  fi

  printf "%-28s %-9s %-9s %-9s %-30s %s\n" "$id" "$asan" "$tsan" "$ubsan" "$detection" "$rust_label"
  [ -n "$note" ] && printf "%-28s   %s\n" "" "($note)"
  echo "$id,\"$label\",$asan,$tsan,$ubsan,\"$detection\",\"$rust_label\",\"$observed\",$expect_rust,\"$note\"" >>"$csv"
  echo "| $id | $asan | $tsan | $ubsan | $detection | $rust_label | ${note:--} |" >>"$md"
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
