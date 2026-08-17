#!/usr/bin/env bash
# Conformance and parity harness (spec §11). Three phases:
#
#   1. Oracle validation -- the Python reference model (model.py) is checked
#      against the pinned §8 known-answer tables and replayed over every
#      hand-written vector. The model only earns the right to generate
#      expectations in phase 3 by first reproducing the ones a human derived.
#   2. Hand-written vectors -- both runners execute each vector, are checked
#      against its expected results, and their transcripts are diffed.
#   3. Generated vectors -- randomised operation sequences from pinned seeds,
#      with every expectation computed by the model. This is what distinguishes
#      "both implementations are correct" from "both are wrong in the same way",
#      which a cross-diff between two implementations of one specification
#      cannot do on its own.
#
# Exit non-zero if any check, any cross-language diff, or the oracle fails.
#
# Scale the random campaign with --random N (vectors per profile, default 4) and
# --ops N (operations per vector, default 300). A failing seed is printed and is
# exactly reproducible: genvec.py is deterministic.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
cpp_dir="$root/cpp"
rust_dir="$root/rust"
vec_dir="$here/vectors"

cpp_bin="$cpp_dir/build/conformance_runner"
rust_bin="$rust_dir/target/release/conformance_runner"

per_profile=4
ops=300
profiles=(lifecycle adversarial capacity routing mixed)

while [ $# -gt 0 ]; do
  case "$1" in
    --random) per_profile="$2"; shift 2 ;;
    --ops)    ops="$2";         shift 2 ;;
    --no-random) per_profile=0; shift ;;
    -h|--help)
      sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

echo "== building C++ runner =="
cmake -S "$cpp_dir" -B "$cpp_dir/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$cpp_dir/build" --target conformance_runner >/dev/null

echo "== building Rust runner =="
cargo build --release --manifest-path "$rust_dir/Cargo.toml" --bin conformance_runner >/dev/null

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

fail=0

# --- phase 1: validate the oracle ------------------------------------------
echo
echo "== phase 1: reference model =="
if ! python3 "$here/model.py" --self-test --check "$vec_dir"/*.vec; then
  echo "  the model disagrees with the hand-written expectations; not using it to generate"
  fail=1
  per_profile=0
fi

# --- shared: run one vector through both runners and compare ---------------
#
# Sets last_ops rather than echoing it: the function also prints status and
# mutates `fail`, and a command substitution would both swallow the output and
# run the assignment in a subshell where it could not stick.
hand_ops=0
gen_ops=0
last_ops=0

run_vector() {
  local vec="$1" label="$2"
  local cpp_rc rust_rc status

  "$cpp_bin"  "$vec" >"$tmp/cpp.out"  2>"$tmp/cpp.err";  cpp_rc=$?
  "$rust_bin" "$vec" >"$tmp/rust.out" 2>"$tmp/rust.err"; rust_rc=$?

  status="ok"
  if [ "$cpp_rc"  -ne 0 ]; then status="FAIL"; fail=1; fi
  if [ "$rust_rc" -ne 0 ]; then status="FAIL"; fail=1; fi
  if ! diff -q "$tmp/cpp.out" "$tmp/rust.out" >/dev/null; then
    status="FAIL(divergence)"; fail=1
  fi

  printf '%-26s cpp_rc=%d rust_rc=%d  %s\n' "$label" "$cpp_rc" "$rust_rc" "$status"

  if [ "$status" != "ok" ]; then
    echo "  --- C++ stderr ---";  sed 's/^/  /' "$tmp/cpp.err"
    echo "  --- Rust stderr ---"; sed 's/^/  /' "$tmp/rust.err"
    if ! diff -q "$tmp/cpp.out" "$tmp/rust.out" >/dev/null; then
      echo "  --- cpp vs rust transcript diff ---"
      diff "$tmp/cpp.out" "$tmp/rust.out" | sed 's/^/  /'
    fi
    echo "  --- vector kept at: $tmp/$(basename "$vec") ---"
    cp "$vec" "$tmp/" 2>/dev/null || true
    trap - EXIT   # keep the temp dir so the failing vector survives
  fi

  # Op count as reported by the runner itself.
  last_ops="$(sed -n 's/.*: \([0-9]*\) ops,.*/\1/p' "$tmp/cpp.err" | tail -1)"
  last_ops="${last_ops:-0}"
}

# --- phase 2: hand-written vectors -----------------------------------------
echo
echo "== phase 2: hand-written vectors =="
shopt -s nullglob
for vec in "$vec_dir"/*.vec; do
  run_vector "$vec" "$(basename "$vec")"
  hand_ops=$(( hand_ops + last_ops ))
done

# --- phase 3: generated vectors --------------------------------------------
if [ "$per_profile" -gt 0 ]; then
  echo
  echo "== phase 3: generated vectors (model-derived expectations) =="
  gen_dir="$tmp/generated"
  mkdir -p "$gen_dir"
  for profile in "${profiles[@]}"; do
    for (( seed = 1; seed <= per_profile; seed++ )); do
      out="$gen_dir/$profile-$seed.vec"
      if ! python3 "$here/genvec.py" --seed "$seed" --ops "$ops" \
             --profile "$profile" --out "$out" 2>/dev/null; then
        echo "  generation failed for profile=$profile seed=$seed"; fail=1; continue
      fi
      run_vector "$out" "$profile seed=$seed"
      gen_ops=$(( gen_ops + last_ops ))
    done
  done

  # The random campaign is only worth its runtime if it actually reaches every
  # branch of the §6.6 error model; a generator that silently stopped producing
  # CapacityExceeded would still pass and would still look like broad coverage.
  echo
  echo "-- error-model coverage across the generated family --"
  missing=0
  for code in NotFound AlreadyExists InvalidState CapacityExceeded InvalidArgument; do
    hits=$(grep -ho "Err($code)" "$gen_dir"/*.vec 2>/dev/null | wc -l)
    printf '   %-18s %6d\n' "$code" "$hits"
    [ "$hits" -eq 0 ] && missing=1
  done
  if [ "$missing" -ne 0 ]; then
    echo "   a §6.6 error code was never generated: the campaign is weaker than it looks"
    fail=1
  fi
fi

echo
echo "checked operations: $hand_ops hand-written, $gen_ops generated"
if [ "$fail" -eq 0 ]; then
  echo "ALL VECTORS PASS (both implementations agree with the model and with each other)"
else
  echo "CONFORMANCE FAILURES DETECTED"
fi
exit "$fail"
