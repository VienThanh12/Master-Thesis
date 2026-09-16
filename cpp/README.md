# UECM: C++ implementation

Modern C++ (C++23) implementation of the UE Context Management service defined in
[`../spec/SPECIFICATION.md`](../spec/SPECIFICATION.md).

New to this tree: a chaptered reading path is [`../docs/cpp-guide/`](../docs/cpp-guide/README.md).
It starts at the spec, then `ShardCore`, then `Service`. Do not start in `bench/`.

## Layout
```
cpp/
  include/uecm/       public headers
    config.hpp        configuration parameters (spec §9)
    error.hpp         OpError + OpResult<T> = std::expected (spec §6.6)
    hash.hpp          pinned shard_index + FNV-1a (spec §8)
    types.hpp         UE context data model + state enum (spec §4, §5)
    shard_core.hpp    single-threaded per-shard op processor (spec §5, §6)
    bounded_queue.hpp bounded blocking MPSC queue (spec §7)
    message.hpp       Request/Response message types (spec §7.3)
    service.hpp       threaded service: thread-per-shard + queues (spec §7)
  src/
    shard_core.cpp    ShardCore implementation
    service.cpp       Service implementation (workers, dispatch, lifecycle)
  bench/
    hdr.hpp                 vendored HDR histogram (latency percentiles)
    bench.cpp               latency/throughput benchmark driver (spec §3/§10)
  tools/
    conformance_runner.cpp  shared parity-vector runner (spec §11)
  tests/
    test_hash.cpp        hash/shard determinism, distribution, and known-answer
                         values for the pinned §8 functions
    test_shard_core.cpp  state machine + error model (spec §11.3 vector)
    test_service.cpp     threaded service: functional + concurrent load
    test_invariants.cpp  spec invariants the .vec transcript cannot express:
                         no mutation on error (§6.1), activity-sequence
                         discipline (§10.3/§11.2), field round-trips, §10.1 I1/I4
    test_concurrency.cpp §7 queue/completion model: blocking backpressure,
                         FIFO per shard (§10.2 O1), concurrent lookup, lifecycle
    test_state_matrix.cpp the §5.2 transition matrix enumerated rather than
                         sampled: every op against every state, asserting the
                         exact error, the post-state on success, and no field
                         change on failure; plus the error precedences §6
                         leaves unordered
```

Each `tests/*.cpp` file is a standalone `main()` using the `CHECK` macro from
`tests/test_util.hpp`; new files are registered by adding their name to the
`foreach` list in `CMakeLists.txt`. `rust/tests/` mirrors these case for case.

## Build & test
Requires a C++23 compiler (g++ 13+ / clang 17+) and CMake 3.20+.

```bash
cd cpp
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure
```

Options:
- `-DUECM_USE_JEMALLOC=ON`: link jemalloc (spec §3, matched allocator); the `bench`
  target then reports `alloc=jemalloc`.
- `-DUECM_BUILD_TESTS=OFF`: skip tests.
- `-DUECM_SANITIZER=address|thread|undefined|address+undefined`: instrument the whole
  tree, library and tests alike. Detection builds (`-O1 -g`), never measurement builds.
- `-DUECM_COVERAGE=ON`: instrument for gcov (implies `-O0`).

## Dynamic analysis and coverage

```bash
./sanitise.sh    # every test binary + every conformance vector, under
                 # ASan+UBSan, TSan and UBSan in turn -> results/sanitisers.md
./coverage.sh    # gcov line coverage of the library under the parity suite
                 # -> results/coverage.md
```

`sanitise.sh` is evidence rather than hygiene. Safe Rust carries data-race and
memory-safety freedom by construction, so unless the C++ variant is checked for them
too, "the two implementations behave identically" rests on the C++ side merely not
having failed yet. `faults/` shows the tools catch these defects when injected
deliberately; this shows they find nothing in the real implementation. Current
result: **all clean**.

`coverage.sh` bounds that. A sanitiser reports only on code that runs, so a clean
run is a statement about the lines the suite reaches. Current result: **94.6%** of
library lines, with `ShardCore` and `Service` at 100%. Not comparable with the
Rust figure — different tools counting different things.

An agent pass on 16 September 2026 is in [`docs/CODE_REVIEW.md`](../docs/CODE_REVIEW.md).
It does not close TODO item D2 (independent expert review). Edges the suite does not
exercise: `shard_index(_, 0)` is `% 0` (undefined behaviour; `Service` clamps
`n_shards` to 1), and concurrent `shutdown()` while another thread is still submitting
races on the plain `running_` flag. Sequential lifecycle misuse is guarded. Benches
join producers before shutdown.

## Benchmark (spec §3/§10)
```bash
cmake --build build --target bench
./build/bench --shards 8 --producers 8 --preload 10000 --ops 200000   # add --json
```
See [`../bench/README.md`](../bench/README.md) for the full workload description and the
`run_bench.sh` harness that compares all four language × allocator variants.

## Conformance / parity (spec §11)
The `conformance_runner` executable runs a language-neutral vector file against the threaded
service and emits a canonical transcript. To check both implementations agree, run the shared
harness (builds C++ and Rust runners, runs every vector through each, diffs the transcripts):

```bash
../spec/conformance/run.sh
```
