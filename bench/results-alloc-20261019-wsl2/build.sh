#!/usr/bin/env bash
# Builds the tracker and the five service variants with the campaign image. Disposable.
set -euo pipefail
p="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$p/../../.." && pwd)"
cd "$root"
mkdir -p "$p/bin"

gcc -O2 -shared -fPIC -o "$p/allocprobe.so" "$p/allocprobe.c" -ldl

for v in stock ring; do
  flags=(-DCMAKE_BUILD_TYPE=Release -DUECM_BUILD_TESTS=OFF)
  [ "$v" = ring ] && flags+=(-DUECM_RING_QUEUE=ON)
  cmake -S cpp -B "$p/cpp-$v" -G Ninja "${flags[@]}" >/dev/null
  cmake --build "$p/cpp-$v" --target bench pipeline >/dev/null
  cp "$p/cpp-$v/bench" "$p/bin/cpp-$v-bench"
  cp "$p/cpp-$v/pipeline" "$p/bin/cpp-$v-pipeline"
done

export CARGO_TARGET_DIR="$p/rust-target"
export CARGO_NET_OFFLINE=true
for v in stock oneshot mutexq; do
  feat=()
  [ "$v" = oneshot ] && feat=(--features sync-oneshot)
  [ "$v" = mutexq ] && feat=(--features mutex-queue)
  cargo build -q --release --manifest-path rust/Cargo.toml --example bench --example pipeline "${feat[@]}"
  cp "$CARGO_TARGET_DIR/release/examples/bench" "$p/bin/rust-$v-bench"
  cp "$CARGO_TARGET_DIR/release/examples/pipeline" "$p/bin/rust-$v-pipeline"
done
ls -la "$p/bin"
