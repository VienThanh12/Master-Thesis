# UECM — Rust implementation

Rust implementation of the UE Context Management service defined in
[`../spec/SPECIFICATION.md`](../spec/SPECIFICATION.md). Structurally mirrors the C++
implementation in [`../cpp/`](../cpp/): identical pinned hashing (§8), the same UE state
machine and API (§5, §6), and the same shared-nothing, thread-per-shard concurrency model (§7).

## Layout
```
rust/
  Cargo.toml          crate manifest; release opt-level pinned to 2 (match C++ -O2)
  src/
    lib.rs            module tree + public re-exports
    config.rs         Config + MAX_DRBS / MAX_SIGNALING_PAYLOAD (spec §9)
    error.rs          OpError + OpResult<T> = Result<T, OpError> (spec §6.6)
    hash.rs           pinned shard_index (SplitMix64) + FNV-1a BuildHasher (spec §8)
    types.rs          UE context data model + state enum (spec §4, §5)
    shard_core.rs     single-threaded per-shard op processor (spec §5, §6)
    message.rs        Request enum with typed one-shot senders (spec §7.3)
    service.rs        threaded service: thread-per-shard + bounded sync_channel (spec §7)
  tests/
    conformance.rs    hash checks, state machine (§11.3 vector), threaded + concurrent tests
```

## Build & test
Requires a stable Rust toolchain (1.75+; developed on 1.96).

```bash
cd rust
cargo test                       # debug build + all tests
cargo test --release             # optimised (opt-level 2, matches C++ -O2)
cargo clippy --all-targets -- -D warnings
cargo fmt --check
```

## Notes on parity with C++
- **Hashing** is bit-for-bit identical: `hash.rs` forces little-endian byte order so the
  `HashMap` hasher agrees with `fnv1a_64` (checked in `conformance.rs`).
- **Concurrency**: bounded blocking backpressure via `std::sync::mpsc::sync_channel`; one-shot
  completions via a per-request `channel()`; each worker owns its `ShardCore` (shared-nothing),
  with only the atomic `activity_seq` shared through an `Arc<AtomicU64>`.
- **Safety**: the crate contains **zero `unsafe`**. Safe Rust guarantees data-race freedom at
  compile time (`Send`/`Sync`), so no ThreadSanitizer run is needed. Optionally, run Miri
  (`cargo +nightly miri test`) as an extra UB/data-race check once a nightly toolchain is added.

## Benchmark (spec §3/§10)
The benchmark lives as an example (so the library stays dependency-free) and uses the
`hdrhistogram` crate; the matched allocator is enabled with the `jemalloc` feature.

```bash
cargo build --release --example bench                    # system allocator
cargo build --release --example bench --features jemalloc # tikv-jemallocator
./target/release/examples/bench --shards 8 --ops 200000  # add --json
```

See [`../bench/README.md`](../bench/README.md) for the full workload and the `run_bench.sh`
harness comparing all four language × allocator variants.

## Conformance / parity (spec §11)
```bash
cargo build --release --bin conformance_runner
../spec/conformance/run.sh    # runs C++ and Rust runners, diffs transcripts
```
