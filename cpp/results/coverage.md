# C++ line coverage of the parity suite

Regenerate with `cpp/coverage.sh`.

- `gcov (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- Driven by: every CTest binary, plus `conformance_runner` over 22 vectors
  (7 hand-written and the rest generated at 400 ops each)
- Scope: `cpp/src/` and `cpp/include/uecm/`. Test sources are excluded, and so is
  `flat_map.hpp`, which is an attribution probe rather than part of the compared build.

| File | Executable lines | Covered | Coverage |
|---|---:|---:|---:|
| `cpp/include/uecm/bounded_queue.hpp` | 57 | 38 | 66.7% |
| `cpp/include/uecm/error.hpp` | 8 | 7 | 87.5% |
| `cpp/include/uecm/hash.hpp` | 56 | 56 | 100.0% |
| `cpp/include/uecm/service.hpp` | 3 | 3 | 100.0% |
| `cpp/include/uecm/shard_core.hpp` | 7 | 7 | 100.0% |
| `cpp/src/service.cpp` | 124 | 124 | 100.0% |
| `cpp/src/shard_core.cpp` | 103 | 103 | 100.0% |
| **Total** | **358** | **338** | **94.4%** |

Coverage bounds every negative result taken from this suite. A sanitiser
reports only on code that runs, so `results/sanitisers.md` being clean is a
statement about these lines and not about the ones the suite never reaches.

Not comparable with the Rust figure in `rust/results/coverage.md`: gcov counts
C++ lines and llvm-cov counts Rust regions, and the two implementations have no
line-for-line correspondence. Each figure is about its own implementation.
