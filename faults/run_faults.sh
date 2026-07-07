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

# Defect list: id | source stem | which sanitizer is expected to catch it (asan|tsan)
# The script still runs BOTH sanitizers regardless; the expectation is only used
# to pick the "C++ detection" column for the taxonomy.
defects=(
  "use_after_free|uaf|asan"
  "double_free|double_free|asan"
  "iterator_invalidation|iterator_invalidation|asan"
  "data_race|data_race|tsan"
  "unguarded_shared_mutation|unguarded_mutation|tsan"
)

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
  "${run_prefix[@]}" "$bin" >>"$log" 2>&1
  if grep -Eq "(AddressSanitizer|ThreadSanitizer|runtime error|SUMMARY: .*Sanitizer)" "$log"; then
    echo "detected"
  else
    echo "clean"
  fi
}

# --- compile one Rust counterpart; echo "rejected:E0499,E0502" or "compiles" ---
run_rust() {
  local stem="$1"
  local src="$rust_dir/$stem.rs"
  local log="$out_dir/${stem}.rust.log"
  if "$RUSTC" --edition 2021 --crate-type bin -o "$bin_dir/${stem}_rs" "$src" >"$log" 2>&1; then
    echo "compiles"
  else
    local codes
    codes=$(grep -oE 'E[0-9]{4}' "$log" | sort -u | paste -sd, -)
    [ -z "$codes" ] && codes="compile-error"
    echo "rejected:$codes"
  fi
}

# --- environment banner --------------------------------------------------------
cxx_ver=$("$CXX" --version 2>/dev/null | head -1)
rustc_ver=$("$RUSTC" --version 2>/dev/null)
echo "== RQ2 fault-injection study =="
echo "C++ compiler : $cxx_ver (-std=$CXXSTD)"
echo "Rust compiler: $rustc_ver (--edition 2021)"
echo "ASLR wrapper : ${run_prefix[*]:-none}"
echo

csv="$out_dir/taxonomy.csv"
md="$out_dir/taxonomy.md"
echo "defect,cpp_asan,cpp_tsan,cpp_detection,rust_compile" >"$csv"

{
  echo "# RQ2 defect-class taxonomy"
  echo
  echo "- C++ compiler: \`$cxx_ver\` (\`-std=$CXXSTD\`)"
  echo "- Rust compiler: \`$rustc_ver\` (\`--edition 2021\`)"
  echo "- ASLR wrapper: \`${run_prefix[*]:-none}\`"
  echo
  echo "| Defect class | C++ ASan | C++ TSan | C++ detection stage | Rust outcome |"
  echo "|---|---|---|---|---|"
} >"$md"

printf "%-26s %-10s %-10s %-22s %s\n" "defect" "cpp/asan" "cpp/tsan" "cpp detection" "rust"
printf "%-26s %-10s %-10s %-22s %s\n" "------" "--------" "--------" "-------------" "----"

for row in "${defects[@]}"; do
  IFS='|' read -r id stem expect <<<"$row"
  asan=$(run_cpp_san "$stem" address asan)
  tsan=$(run_cpp_san "$stem" thread  tsan)
  rust=$(run_rust "$stem")

  # C++ detection stage: which tool caught it (runtime), else undetected.
  if [ "$asan" = "detected" ] || [ "$tsan" = "detected" ]; then
    tool=""
    [ "$asan" = "detected" ] && tool="ASan"
    [ "$tsan" = "detected" ] && tool="${tool:+$tool+}TSan"
    detection="runtime ($tool)"
  else
    detection="undetected"
  fi

  # Rust taxonomy label.
  if [[ "$rust" == rejected:* ]]; then
    rust_label="compile-time prevented (${rust#rejected:})"
  else
    rust_label="COMPILES (unexpected!)"
  fi

  printf "%-26s %-10s %-10s %-22s %s\n" "$id" "$asan" "$tsan" "$detection" "$rust_label"
  echo "$id,$asan,$tsan,\"$detection\",\"$rust_label\"" >>"$csv"
  echo "| $id | $asan | $tsan | $detection | $rust_label |" >>"$md"
done

echo
echo "Wrote: $md"
echo "Wrote: $csv"
