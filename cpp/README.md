# UECM — C++ implementation

Modern C++ (C++23) implementation of the UE Context Management service defined in
[`../spec/SPECIFICATION.md`](../spec/SPECIFICATION.md).

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
    test_hash.cpp        hash/shard determinism + distribution
    test_shard_core.cpp  state machine + error model (spec §11.3 vector)
    test_service.cpp     threaded service: functional + concurrent load
```

## Build & test
Requires a C++23 compiler (g++ 13+ / clang 17+) and CMake 3.20+.

```bash
cd cpp
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure
```

Options:
- `-DUECM_USE_JEMALLOC=ON` — link jemalloc (spec §3, matched allocator); the `bench`
  target then reports `alloc=jemalloc`.
- `-DUECM_BUILD_TESTS=OFF` — skip tests.

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
