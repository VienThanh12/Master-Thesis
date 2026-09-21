# Chapter 1 — Orientation

**Open:** `cpp/README.md`, then the tree under `cpp/include/uecm/` and `cpp/src/`.

## The claim this layer makes

`cpp/` is one of two language-equivalent encodings of a frozen specification.
It is a **UE Context Management (UECM)** service: a small, stateful, concurrent
store of per-device records, as a gNB-CU-CP holds.
The thesis compares this tree with `rust/`. Fairness is not "they look similar".
It is "they implement the same spec, and every forced idiom difference is
logged".

You are not reading a product. Persistence, ASN.1, radio I/O, and the rest of
a real gNB are out of scope. Message payloads are structs with a realistic
width, not wire-format PDUs.

## What a UE is, here

A **UE** (User Equipment) is one connected device. Its identifier is a
`uint64_t` called `ue_id`. Zero is reserved and rejected. The service owns a
**UE context** for each live id: lifecycle state, serving cell, dummy security
material, a short list of data radio bearers, and two counters.

Four states exist. Only three are observable:

```
create_context -----> Idle --setup_connection--> Connected
                                              |  ^
                         begin_reconfigure    |  |  complete_reconfigure
                                              v  |  abort_reconfigure
                                        Reconfiguring

release_context, from any of the three, deletes the record.
Released is transient: it is never stored.
```

Signaling and bearer setup are allowed only in `Connected`. An illegal
transition returns `InvalidState` and **must not mutate** the record.

## The concurrency picture, before any header

The UE-id space is partitioned into **shards**. Each shard is a hash map plus
one worker thread. Only that worker reads or writes that map. Callers never
touch a context. They enqueue a request on the shard's bounded queue and wait
on a one-shot completion.

```
producers (bench threads, tests, the parity runner)
        |
        |  shard_index(ue_id, n_shards)     // SplitMix64, then modulo
        v
   per-shard BoundedQueue  ---- FIFO ---->  one worker thread
                                                |
                                                v
                                            ShardCore
                                            (unordered_map + state machine)
                                                |
                                                v
                                         std::promise  -->  caller
```

That is the whole architecture. `ShardCore` is the sequential processor.
`Service` is N copies of it, each behind a queue. If you understand those two
classes you understand the library.

## The tree, by job

| Path | Job |
| --- | --- |
| `include/uecm/*.hpp` | Public headers. Most of the types live only here. |
| `src/shard_core.cpp` | State machine and map operations. |
| `src/service.cpp` | Workers, routing, lifecycle. |
| `tests/` | Six standalone `main()` binaries. Each file is one question. |
| `tools/conformance_runner.cpp` | Replay a language-neutral `.vec` file. |
| `tools/layout_probe.cpp` | `sizeof` / `offsetof` for generated thesis macros. Not the library. |
| `bench/` | Latency driver and two microbenchmarks. Clients of `Service`. |
| `CMakeLists.txt` | C++23, `-O2` in Release, sanitiser and coverage knobs, probe flags. |
| `sanitise.sh`, `coverage.sh` | Evidence scripts. Run after you know the tests. |

Headers that look like the library and are not:

| Header | What it actually is |
| --- | --- |
| `include/uecm/flat_map.hpp` | Attribution probe. Open-addressed map. Off unless `-DUECM_FLAT_MAP=ON`. |
| `include/uecm/ring_queue.hpp` | Attribution probe. Preallocated ring inside the queue. Off unless `-DUECM_RING_QUEUE=ON`. |

The compared C++ arm uses `std::unordered_map` and a deque-backed `std::queue`.
Those two headers exist to ask "was the container the cause?", not to ship.

## C++ shape, in one screen

- Namespace `uecm`.
- C++23 because `OpResult<T>` is `std::expected<T, OpError>`.
- The library is a static target named `uecm` with two `.cpp` files.
- Threads come from `Threads::Threads`. There is no Boost, no gtest, no asio.
- Tests use a 30-line `CHECK` macro in `tests/test_util.hpp`.

## A check

From `cpp/include/uecm/`, list the headers. You should be able to sort them
into three piles without opening them:

1. **Vocabulary:** `types.hpp`, `config.hpp`, `error.hpp`, `hash.hpp`
2. **Sequential core:** `shard_core.hpp`
3. **Threaded wrapper:** `message.hpp`, `bounded_queue.hpp`, `service.hpp`

The two probe headers are a fourth pile. Leave them until chapter 10.

## Do not

Do not start in `cpp/bench/bench.cpp`. It is 400 lines of harness around a
service you have not read. Do not start in `faults/cpp/`. Those files are
deliberate defects. Do not start in `ffi/`. That is the C ABI seam for a
different research question.
