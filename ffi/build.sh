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
"$here/host"
host_rc=$?

echo
echo "== Interop-cost metrics (RQ4) =="
count_matches() { { grep -rhoE "$1" "$2" 2>/dev/null || true; } | wc -l | tr -d ' '; }
seam_rs=$(count_matches 'extern "C"' "$rust_dir/src/lib.rs")
loc_rs=$(wc -l < "$rust_dir/src/lib.rs" | tr -d ' ')
loc_h=$(wc -l < "$rust_dir/include/uecm_ffi.h" | tr -d ' ')
unsafe_lib=$(count_matches 'unsafe' "$here/../rust/src")
unsafe_seam=$(count_matches 'unsafe' "$rust_dir/src/lib.rs")
echo "  C-ABI entry points (extern \"C\" fns) : $seam_rs"
echo "  seam size: lib.rs = $loc_rs LOC, header = $loc_h LOC"
echo "  'unsafe' occurrences: core Rust library = $unsafe_lib, FFI seam = $unsafe_seam"
echo "  (core library was NOT modified to add FFI; all interop is in the seam crate)"

exit "$host_rc"
