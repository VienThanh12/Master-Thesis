My Master Thesis

# Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia RAN Control-Plane Systems

Master's thesis (University of Helsinki, Software study track) by **Ha Vien**.

This repository holds both the written thesis (LaTeX) and the complete artefact it is
built on: a language-agnostic specification, two functionally equivalent implementations
of a Radio Access Network (RAN) control-plane subsystem in **modern C++** and **Rust**, and
the measurement harnesses that produce every figure and table in the thesis.

## What the thesis studies

RAN control-plane software (the L3 of a gNB) is written mostly in C++ for performance, but
C++ carries well-known memory-safety and concurrency risks. Rust promises comparable
performance with safety guaranteed at compile time. Using a **UE Context Management (UECM)**
service modeled on a Nokia gNB-CU-CP component, the thesis compares the two languages along
four research questions:

| RQ      | Question                                                           | Evidence in          |
| ------- | ------------------------------------------------------------------ | -------------------- |
| **RQ1** | Tail latency and jitter under overload                             | [`bench/`](bench/)   |
| **RQ2** | Which C++ defect classes does safe Rust prevent at compile time, and which does it not? | [`faults/`](faults/) |
| **RQ3** | What is the overhead (memory / CPU) of Rust's safety model?        | [`bench/`](bench/)   |
| **RQ4** | What is the cost of incrementally adopting Rust in a C++ codebase? | [`ffi/`](ffi/)       |

The RQ2 catalogue deliberately spans both sides of the guarantee: five defect classes safe Rust
prevents at compile time, and two (lock-order deadlock, lost update) it does not, so the study
measures where the guarantee *stops* rather than only confirming that it holds.

The methodological control against implementation bias is a **frozen, language-neutral
specification**: both implementations must conform to it exactly, and any forced idiomatic
divergence is logged. See [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md).

## Repository layout

```
.
├── spec/          Frozen specification + language-neutral conformance suite (the fairness baseline)
├── cpp/           C++23 implementation of the UECM service
├── rust/          Rust implementation (bit-for-bit parity with cpp/)
├── bench/         Latency/throughput/resource benchmark harness + plotting (RQ1, RQ3)
├── faults/        Fault-injection taxonomy: injected C++ defects vs. Rust compile errors (RQ2)
├── ffi/           Incremental-adoption prototype: C++ host over a Rust component via a C ABI (RQ4)
├── figures/       Generated figures + LaTeX tables consumed by the thesis
├── diagrams/      Source diagrams
├── thesis.tex     Thesis source (LaTeX)
├── bibliography.bib
└── build_deck.py  Slide-deck generator
```

Each component directory has its own `README.md` with build/run instructions.

## Quick start

Reproduce the artefact from the sub-projects (each is self-contained):

```bash
# C++ implementation: build + run tests
cd cpp && cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build && ctest --test-dir build --output-on-failure

# Rust implementation: build + run tests
cd rust && cargo test --release

# Cross-language parity: run every conformance vector through both and diff transcripts
spec/conformance/run.sh

# Fault-injection taxonomy (RQ2)
faults/run_faults.sh

# FFI migration prototype (RQ4)
ffi/build.sh

# Benchmark comparison across both languages × both allocators (RQ1, RQ3)
bench/run_bench.sh
```

For thesis-grade performance numbers, provision a clean testbed and run the full
measurement campaign, see [`bench/README.md`](bench/README.md) and
[`bench/TESTBED.md`](bench/TESTBED.md).

## The subsystem under study

A self-contained, stateful, concurrent **UE Context Management** service that owns the UE
context lifecycle and executes RRC/mobility procedures. Both implementations share:

- the same **shared-nothing, thread-per-shard** concurrency model (one worker per shard, a
  bounded blocking MPSC queue, one-shot completions);
- **pinned** shard selection (SplitMix64) and intra-shard key hashing (FNV-1a), so container
  performance is never an accidental language advantage;
- the same data model, UE state machine, public API, and error model.

Full details, invariants, and the parity contract are in
[`spec/SPECIFICATION.md`](spec/SPECIFICATION.md).

## Building the thesis document

Requires a LaTeX toolchain (`latexmk`, TeX Live) with the bundled `UH_DS_MSc.cls` class:

```bash
latexmk -pdf thesis.tex
```

Figures and tables are regenerated from raw measurement logs with
`python3 bench/plot_figures.py` (see [`bench/README.md`](bench/README.md)).

## Status

Safety (RQ2) and migration (RQ4) results are final; performance work (RQ1, RQ3) is complete
in tooling with testbed-grade latency figures as the remaining step. The specification is
implemented and both languages pass and agree on the shared conformance suite.

Every campaign summary number quoted in the thesis prose (representative load, saturation
knee, repeat count, p99 spread) is generated into `figures/gen_macros.tex` by
`bench/plot_figures.py` alongside the figures and tables, so re-running the campaign on a
bare-metal testbed and then

```bash
python3 bench/plot_figures.py
latexmk -pdf thesis.tex
```

refreshes the narrative and the data together. There are no hand-copied numbers to go stale.
