# Rust line coverage of the parity suite

Regenerate with `rust/coverage.sh`.

- `cargo-llvm-cov 0.9.0`
- Driven by: every integration test, plus `conformance_runner` over 22 vectors
  (7 hand-written and the rest generated at 400 ops each)
- Scope: `rust/src/`, excluding `src/bin/`, `tests/` and `examples/`, which are harness
  rather than the library under study.

| File | Lines | Covered | Line coverage | Region coverage |
|---|---:|---:|---:|---:|
| `rust/src/config.rs` | 8 | 8 | 100.0% | 100.0% |
| `rust/src/error.rs` | 8 | 8 | 100.0% | 100.0% |
| `rust/src/hash.rs` | 33 | 33 | 100.0% | 100.0% |
| `rust/src/service.rs` | 185 | 185 | 100.0% | 99.7% |
| `rust/src/shard_core.rs` | 140 | 140 | 100.0% | 100.0% |
| `rust/src/types.rs` | 7 | 0 | 0.0% | 0.0% |
| **Total** | **381** | **374** | **98.2%** | **99.3%** |

Coverage bounds every negative result taken from this suite, the Miri run in
`results/miri.md` included: an interpreter reports only on code that runs.

Not comparable with the C++ figure in `cpp/results/coverage.md`: llvm-cov counts
Rust regions and gcov counts C++ lines, and the two implementations have no
line-for-line correspondence. Each figure is about its own implementation.
