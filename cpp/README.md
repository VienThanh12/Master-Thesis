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
  src/
    shard_core.cpp    ShardCore implementation
  tests/
    test_hash.cpp        hash/shard determinism + distribution
    test_shard_core.cpp  state machine + error model (spec §11.3 vector)
```

Not yet implemented (next steps, spec §7): the threaded service wrapper — bounded MPSC
queue per shard, one worker thread per shard, one-shot completions, `start()`/`shutdown()`.

## Build & test
Requires a C++23 compiler (g++ 13+ / clang 17+) and CMake 3.20+.

```bash
cd cpp
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure
```

Options:
- `-DUECM_USE_JEMALLOC=ON` — link jemalloc (spec §3, matched allocator).
- `-DUECM_BUILD_TESTS=OFF` — skip tests.
