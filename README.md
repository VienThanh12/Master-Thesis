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
service modelled on a Nokia gNB-CU-CP component, the thesis compares the two languages along
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
├── spec/              Frozen specification + language-neutral conformance suite (the fairness baseline)
├── cpp/               C++23 implementation of the UECM service
├── rust/              Rust implementation (bit-for-bit parity with cpp/)
├── bench/             Latency/throughput/resource benchmark harness + plotting (RQ1, RQ3)
│   ├── campaign.sh    Full measurement campaign (repeats, interleaving, bootstrap CI)
│   ├── latency_budget.sh  Split the end-to-end op into work vs. cross-thread handoff
│   └── refresh_thesis.sh  Regenerate all figures/tables and rebuild thesis.pdf
├── faults/            Fault-injection taxonomy: injected C++ defects vs. Rust compile errors (RQ2)
├── ffi/               Incremental-adoption prototype: C++ host over a Rust component via a C ABI (RQ4)
├── figures/           Generated figures + LaTeX tables consumed by the thesis
├── diagrams/          Source diagrams (SVG/PDF)
├── thesis.tex         Thesis source (LaTeX, canonical)
├── thesis-vi.tex      Vietnamese translation draft (XeLaTeX)
├── Thesis_Plan_v2.tex Revised thesis plan
├── bibliography.bib
├── build_deck.py      Nokia-branded slide-deck generator (reads figures/ + faults/ results)
└── TODO.md            Development checklist and open items
```

Each component directory has its own `README.md` with build/run instructions.

## Prerequisites

| Tool | Used for |
| ---- | -------- |
| C++23 compiler (g++ 13+ / clang 17+), CMake 3.20+, Ninja | [`cpp/`](cpp/) |
| Rust stable (1.75+; developed on 1.96), `cargo` | [`rust/`](rust/) |
| `latexmk`, TeX Live (bundled `UH_DS_MSc.cls`) | `thesis.tex` |
| Python 3 + `matplotlib` (optional: `lizard`) | [`bench/`](bench/) plotting and complexity proxies |
| AddressSanitizer / ThreadSanitizer (`g++`) | [`faults/`](faults/) |

On WSL2, run C++ sanitizer builds under `setarch -m -R` (see [`faults/run_faults.sh`](faults/run_faults.sh)).
WSL2 is fine for development and smoke runs; thesis-grade latency numbers require a bare-metal
testbed (see [`bench/TESTBED.md`](bench/TESTBED.md)).

## Quick start

### 1. Verify both implementations

```bash
# C++: build + run tests
cd cpp && cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build && ctest --test-dir build --output-on-failure

# Rust: build + run tests
cd rust && cargo test --release

# Cross-language parity: run every conformance vector through both and diff transcripts
spec/conformance/run.sh
```

### 2. Run the four studies

```bash
# Fault-injection taxonomy (RQ2)
faults/run_faults.sh

# FFI migration prototype (RQ4). Also runs the same signaling op natively, so the
# reported seam cost is a direct A/B rather than an empty crossing against a full op.
ffi/build.sh

# Benchmark comparison across both languages × both allocators (RQ1, RQ3)
bench/run_bench.sh

# What the end-to-end latency is actually made of: the operation's own work versus
# the cross-thread submit-and-complete handoff, in both languages. Needs a quiet host.
bench/latency_budget.sh
```

### 3. Rebuild the thesis from measured data

After a measurement campaign or fault-injection run, regenerate every figure, table, and
quoted number, then rebuild the PDF:

```bash
bench/refresh_thesis.sh
```

This runs `bench/plot_figures.py` (and `bench/complexity.py` when `lizard` is available),
writes into [`figures/`](figures/), rebuilds the colloquium deck via `build_deck.py`, and calls
`latexmk -pdf thesis.tex`. Campaign summary numbers land in `figures/gen_macros.tex`; the prose
and the slides both refer to them by macro name, so text, slides, and data stay in sync.

To build the thesis document alone:

```bash
latexmk -pdf thesis.tex
```

For thesis-grade performance numbers, provision a clean testbed and run the full
measurement campaign. See [`bench/README.md`](bench/README.md) and
[`bench/TESTBED.md`](bench/TESTBED.md).

```bash
bench/setup_testbed.sh          # install toolchain + apply CPU hygiene + verify
bench/campaign.sh --repeats 20  # full load sweep with bootstrap CI (see bench/README.md)
bench/refresh_thesis.sh         # refresh figures/tables/PDF from the newest campaign
```

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

## Slide deck

A Nokia-branded presentation can be generated from measured results:

```bash
python3 build_deck.py    # -> Rust_vs_Cpp_Nokia_RAN_thesis.pptx
```

Requires the slide toolkit under `create-pptx-master-thesis/` (see `.gitignore`).

## Status

| Area | State |
| ---- | ----- |
| Specification + parity | Implemented; both languages pass and agree byte-for-byte on the shared conformance suite (7 vectors, 223 checked operations), plus mirrored per-language invariant and concurrency suites (spec v0.1 draft, pending supervisor freeze) |
| RQ2 (safety) | Final: fault-injection taxonomy complete |
| RQ4 (migration) | Final: FFI prototype + interop metrics complete |
| RQ1/RQ3 (performance) | Tooling complete; latency figures in the thesis are **preliminary** until a bare-metal campaign with 15+ repeats |

Open items and the post-campaign re-check list are tracked in [`TODO.md`](TODO.md).

Every campaign summary number quoted in the thesis prose (representative load, saturation
knee, repeat count, p99 spread) is generated into `figures/gen_macros.tex` by
`bench/plot_figures.py` alongside the figures and tables. Re-running the campaign on a
bare-metal testbed and then `bench/refresh_thesis.sh` refreshes the narrative and the data
together. There are no hand-copied numbers to go stale.
