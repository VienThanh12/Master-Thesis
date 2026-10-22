#!/usr/bin/env bash
# Profiling builds: the measured optimisation plus debug info, so inlined code can be
# attributed. Runs inside the campaign container. Disposable.
set -euo pipefail
p="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$p/../../.." && pwd)"
cd "$root"
mkdir -p "$p/bin"

cmake -S cpp -B "$p/cpp-g" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-g \
  -DUECM_BUILD_TESTS=OFF >/dev/null
cmake --build "$p/cpp-g" --target bench >/dev/null
cp "$p/cpp-g/bench" "$p/bin/pf-cpp-deque"

export CARGO_TARGET_DIR="$p/rust-target-g" CARGO_PROFILE_RELEASE_DEBUG=true CARGO_NET_OFFLINE=true
cargo build -q --release --manifest-path rust/Cargo.toml --example bench
cp "$CARGO_TARGET_DIR/release/examples/bench" "$p/bin/pf-rust-channel"
cargo build -q --release --manifest-path rust/Cargo.toml --example bench --features sync-oneshot
cp "$CARGO_TARGET_DIR/release/examples/bench" "$p/bin/pf-rust-oneshot"

# The measured binaries from today's session, for the machine-code comparison.
for arm in cpp-deque rust-channel rust-oneshot; do
  a="$p/bin/pf-$arm"
  b="bench/.bin/fc-$arm"
  ta="$(objcopy -O binary --only-section=.text "$a" /dev/stdout | sha256sum | cut -c1-16)"
  tb="$(objcopy -O binary --only-section=.text "$b" /dev/stdout | sha256sum | cut -c1-16)"
  sa="$(size -A "$a" | awk '$1==".text"{print $2}')"
  sb="$(size -A "$b" | awk '$1==".text"{print $2}')"
  same=no; [ "$ta" = "$tb" ] && same=yes
  echo "$arm: .text $sa bytes ($ta) against measured $sb bytes ($tb), identical: $same"
done
