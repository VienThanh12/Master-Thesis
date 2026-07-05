#!/usr/bin/env bash
# Build both implementations' conformance runners, run every vector through each,
# check them against the expected results, and diff the C++ vs Rust actual
# transcripts (spec §11). Exit non-zero if any check or cross-language diff fails.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
cpp_dir="$root/cpp"
rust_dir="$root/rust"
vec_dir="$here/vectors"

cpp_bin="$cpp_dir/build/conformance_runner"
rust_bin="$rust_dir/target/release/conformance_runner"

echo "== building C++ runner =="
cmake -S "$cpp_dir" -B "$cpp_dir/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$cpp_dir/build" --target conformance_runner >/dev/null

echo "== building Rust runner =="
cargo build --release --manifest-path "$rust_dir/Cargo.toml" --bin conformance_runner >/dev/null

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

fail=0
shopt -s nullglob
for vec in "$vec_dir"/*.vec; do
  name="$(basename "$vec")"

  "$cpp_bin"  "$vec" >"$tmp/cpp.out"  2>"$tmp/cpp.err";  cpp_rc=$?
  "$rust_bin" "$vec" >"$tmp/rust.out" 2>"$tmp/rust.err"; rust_rc=$?

  status="ok"
  if [ "$cpp_rc" -ne 0 ]; then status="FAIL"; fail=1; fi
  if [ "$rust_rc" -ne 0 ]; then status="FAIL"; fail=1; fi
  if ! diff -q "$tmp/cpp.out" "$tmp/rust.out" >/dev/null; then status="FAIL(divergence)"; fail=1; fi

  printf '%-16s cpp_rc=%d rust_rc=%d  %s\n' "$name" "$cpp_rc" "$rust_rc" "$status"

  if [ "$status" != "ok" ]; then
    echo "  --- C++ stderr ---";  sed 's/^/  /' "$tmp/cpp.err"
    echo "  --- Rust stderr ---"; sed 's/^/  /' "$tmp/rust.err"
    if ! diff -q "$tmp/cpp.out" "$tmp/rust.out" >/dev/null; then
      echo "  --- cpp vs rust transcript diff ---"
      diff "$tmp/cpp.out" "$tmp/rust.out" | sed 's/^/  /'
    fi
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "ALL VECTORS PASS (both implementations agree with expected and with each other)"
else
  echo "CONFORMANCE FAILURES DETECTED"
fi
exit "$fail"
