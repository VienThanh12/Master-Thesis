# UECM: Rust implementation

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
    conformance.rs    hash checks incl. known-answer values for the pinned §8
                      functions, state machine (§11.3 vector), threaded tests
    invariants.rs     spec invariants the .vec transcript cannot express: no
                      mutation on error (§6.1), activity-sequence discipline
                      (§10.3/§11.2), field round-trips, §10.1 I1/I4
    concurrency.rs    §7 queue/completion model: blocking backpressure, FIFO per
                      shard (§10.2 O1), concurrent lookup, lifecycle
    state_matrix.rs   the §5.2 transition matrix enumerated rather than sampled:
                      every op against every state, asserting the exact error,
                      the post-state on success, and no field change on failure;
                      plus the error precedences §6 leaves unordered
```

`tests/invariants.rs`, `tests/concurrency.rs` and `tests/state_matrix.rs` mirror
`cpp/tests/test_invariants.cpp`, `cpp/tests/test_concurrency.cpp` and
`cpp/tests/test_state_matrix.cpp` case for case, so the two suites check the same
stated properties and any divergence is a real one rather than a coverage difference.

## Build & test
Requires a stable Rust toolchain (1.75+; developed on 1.97).

```bash
cd rust
cargo test                       # debug build + all tests
cargo test --release             # optimised (opt-level 2, matches C++ -O2)
cargo clippy --all-targets -- -D warnings
cargo fmt --check
```

## Dynamic analysis and coverage

```bash
./miri.sh        # state-machine + invariant suites under Miri -> results/miri.md
                 # needs: rustup toolchain install nightly --component miri
./coverage.sh    # llvm-cov line coverage under the parity suite -> results/coverage.md
                 # needs: cargo install cargo-llvm-cov --locked
```

Miri confirms rather than discovers, since the core has no `unsafe`; it exists so
that both language arms are checked by the strongest dynamic tool each offers and
the remaining asymmetry is one of what the tools can guarantee, not of whether
anyone looked. Current result: **clean**, no undefined behaviour under Stacked
Borrows with strict provenance.

Coverage bounds that, because an interpreter only reports on code that runs.
Current result: **98.2%** of library lines, with `ShardCore` and `Service` at 100%.
Not comparable with the C++ figure — different tools counting different things.

## Notes on parity with C++
- **Hashing** is bit-for-bit identical: `hash.rs` forces little-endian byte order so the
  `HashMap` hasher agrees with `fnv1a_64` (checked in `conformance.rs`).
- **Concurrency**: bounded blocking backpressure via `std::sync::mpsc::sync_channel`; one-shot
  completions via a per-request `channel()`; each worker owns its `ShardCore` (shared-nothing),
  with only the atomic `activity_seq` shared through an `Arc<AtomicU64>`.
- **Safety**: the crate contains **zero `unsafe`**. Safe Rust guarantees data-race freedom at
  compile time (`Send`/`Sync`), so no ThreadSanitizer run is needed. Miri has been run anyway
  (`./miri.sh`) and is clean, so the C++ arm is not the only one with dynamic-analysis evidence.
- **Dependency-freedom is deliberate and is kept.** The Loom and Shuttle models of the RQ2
  boundary defect classes live in a separate crate, `faults/rust-model-checking/`, rather than as
  dev-dependencies here: the dependency-free core is load-bearing for the RQ4 supply-chain
  argument and should not be weakened for models that never touch the library.

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
