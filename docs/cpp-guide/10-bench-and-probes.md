# Chapter 10 — Benchmarks and attribution probes

**Open:** `cpp/bench/bench.cpp` (the comment at the top, then `Args` and
`main`), `cpp/bench/workload.hpp` (the comment and `Workload::next`), and
the two probe headers' **comments only**: `flat_map.hpp`, `ring_queue.hpp`.

This chapter is optional on a first day. The library does not depend on it.
The thesis numbers do.

## The claim this layer makes

`bench/` inside `cpp/` is a **client** of `uecm::Service`. It does not
reimplement the state machine. The shared campaign harness lives in the
repository's `bench/` directory (`run_bench.sh`, `campaign.sh`). This
chapter is only the C++ driver and the two compile-time probes.

Never quote a timing you took from an instrumented or probe build as a
thesis result. Release `-O2`, standard map, standard queue, that is the
compared C++ arm. Sanitiser and coverage builds are detection-only
(`CMakeLists.txt` says so twice).

## The driver (`bench.cpp`)

Two workloads, identical to the Rust bench:

| `--workload` | What it does |
| --- | --- |
| `signal` (default) | Preload contexts, then `handle_signaling` on random ids. Hot path only. |
| `mixed` | Pinned lifecycle generator in `workload.hpp`: attach, signaling, bearers, handover, release. |

Each measured op's service latency goes into a per-thread HDR histogram
(`bench/hdr.hpp`, vendored). `--rate` turns on coordinated omission.
`--json` is what the campaign harness parses. `--hist-out` dumps buckets
for the pooled far-tail column the thesis reads. You do not need those
flags to learn the code.

A short smoke run, after a Release build:

```bash
cmake --build cpp/build --target bench
./cpp/build/bench --shards 8 --producers 8 --preload 1000 --ops 20000
```

Keep `--ops` modest on a laptop. The campaign is a different machine and a
different protocol (`bench/TESTBED.md`).

## `workload.hpp`

A pure function of `(active_ues, seed)`. It keeps a lightweight expected
state per slot so every emitted op is valid by construction, and it
advances that model **optimistically** so the sequence of op kinds is
identical in C++ and Rust for the same parameters. The PRNG is SplitMix64
with a documented draw order. If you change the draw order, the twins'
mixed workloads silently diverge.

This generator is not `ShardCore`. It is the load that hits `Service`.

## Two other binaries

| Target | Question |
| --- | --- |
| `latency_budget` | Split end-to-end time into the operation's own work vs the cross-thread handoff. The sweep is almost all handoff. Do not bound a language effect from the sweep alone. |
| `queue_contention` | Bounded queue plus completion primitives under multi-producer load, without the UE state machine. |

`layout_probe.cpp` prints `sizeof` and `offsetof`. Thesis macros consume
those. It is not a benchmark.

## Attribution probes (not the compared arm)

CMake flags, off by default:

| Flag | Header | What changes |
| --- | --- | --- |
| `-DUECM_FLAT_MAP=ON` | `flat_map.hpp` | Intra-shard map becomes open-addressed, same FNV-1a. |
| `-DUECM_RING_QUEUE=ON` | `ring_queue.hpp` | Queue storage becomes a preallocated ring. Locking unchanged. |

Why they exist: the compared study uses each language's **standard**
container, because that is what a developer actually reaches for. A
measured gap then has an attribution problem (language vs container). A
probe holds the language fixed and swaps one container.

Read the comment in each header. They are some of the most careful prose
in the tree. Then look at spec §12 for what the informal laptop runs did
and did not show. Do not copy those numbers into a slide or a thesis
paragraph. They are host-bound and unpaired.

`-DUECM_USE_JEMALLOC=ON` is a **campaign** variant (matched allocator),
not a probe. The bench binary then reports `alloc=jemalloc`. That one is
compared, on purpose, for RQ3.

## Sanitisers and coverage, now that you know the suite

```bash
cd cpp
./sanitise.sh    # ASan+UBSan, TSan, UBSan. Writes results/sanitisers.md
./coverage.sh    # gcov of the library under the parity suite
```

These are evidence, not hygiene. Safe Rust rules out data races and memory
errors at compile time. Unless the same detectors run on C++ and find
nothing, "the twins behave identically" rests on C++ merely not having
failed yet. `faults/` shows the tools catch injected defects. These scripts
show they find nothing in the real implementation.

Do not report timings from a sanitiser build.

## A check

In `bench.cpp`, find where `Service` is constructed, `start()`ed, and
where producers are joined relative to `shutdown()`. Confirm producers
stop before shutdown (the concurrent-shutdown race in chapter 7 is not
on this path).

In `CMakeLists.txt`, find `UECM_FLAT_MAP` and read the `message(STATUS …)`
line. A probe build must be loud at configure time.

## Do not

Do not enable both probes and a sanitiser and then wonder why a number
moved. Do not treat `queue_contention` as the service. Do not hand-edit
`figures/gen_macros.tex` because you ran `./build/bench` once. Campaign
numbers are regenerated by `bench/refresh_thesis.sh` from a named log.
