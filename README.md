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

| RQ      | Question                                                                                          | Evidence in          |
| ------- | ------------------------------------------------------------------------------------------------- | -------------------- |
| **RQ1** | Latency predictability (median, p99, p99.9, maximum) under increasing load and overload            | [`bench/`](bench/)   |
| **RQ2** | Which C++ defect classes safe Rust eliminates at compile time, and at what stage and cost the rest are detected | [`faults/`](faults/) |
| **RQ3** | What overhead Rust's safety model imposes on throughput, CPU utilisation, and memory                | [`bench/`](bench/)   |
| **RQ4** | What incremental adoption of Rust inside an existing C++ codebase costs                             | [`ffi/`](ffi/)       |

The RQ2 catalogue deliberately spans both sides of the guarantee. Safe Rust rejects five of the ten
defect classes at compile time (use-after-free, double free, iterator invalidation, data race,
unguarded shared mutation) and compiles the other five without complaint (lock-order deadlock,
lost update, reference-cycle leak, release-build integer overflow, worker-failure blast radius),
so the study measures where the guarantee *stops* rather than only confirming that it holds. Two
of those boundary classes came back with the C++ tooling ahead: the reference-cycle leak, caught
by ASan and silent in Rust, and the release-build overflow, caught by UBSan and wrapped in Rust.
Both stay in the catalogue. For the two concurrency classes on the boundary, lock-order deadlock
and lost update, [`faults/run_model_checking.sh`](faults/run_model_checking.sh) asks the follow-up
question of what Loom and Shuttle catch at test time, and at what cost.

The methodological control against implementation bias is a **frozen, language-neutral
specification**: both implementations must conform to it exactly, and any forced idiomatic
divergence is logged. See [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md).

## The documents

The PDFs in this repository do not share a status and are not interchangeable.

| Document | Status | Role |
| -------- | ------ | ---- |
| `Thesis_Plan_v2.pdf` | Reviewed, supervisor-facing | Approved plan: gap, RQs, methodology, timeline, contributions |
| `Thesis_v2.pdf` | Reviewed, supervisor-facing | Chapter skeleton, one bullet per argument move, five bullets a chapter and seven in the introduction. All eight chapters populated, matching the full draft's chapter list since 26 August 2026, and the results bullets quote the generated macros rather than carrying their own numbers |
| `Ha_Vien_Mastersthesis_2026.pdf` | Full draft, not final | The canonical long-form thesis. Rich figures, generated numbers, full argument, and everything in it still needs review. The name is the UH submission format (`Lastname_Firstname_Mastersthesis_Year`, ASCII) and says nothing about review status. It was `Thesis_POC` until 19 August 2026 |
| `ai_statement.tex` | Declaration in the author's name | Statement on generative-AI use, shared by both thesis documents |
| [`archive/`](archive/) | Superseded, not maintained | Earlier variants kept for reference only: `plain_thesis.tex`, `thesis-vi.tex` (renders its citations as `[?]`), `thesis_wbm_full_backup.tex`, the pre-cuts `Thesis_POC.tex.bak-before-cuts`, and the v1 plan PDF. They read relative paths from the repository root, so they no longer build where they sit |

[`AGENT.md`](AGENT.md) is the working contract for the repository: document roles, the grade
criteria every edit has to protect, the scientific commitments that must not be weakened, and the
verification workflow. Read it before touching thesis text, figures, or artefacts.
[`docs/ASSESSMENT.md`](docs/ASSESSMENT.md) holds the criterion-by-criterion self-assessment and
[`docs/TODO.md`](docs/TODO.md) the phase checklist and open items.

## Repository layout

```
.
├── spec/              Frozen specification + language-neutral conformance suite (the fairness baseline)
│   ├── SPECIFICATION.md   The fairness baseline (v0.1 draft, pending supervisor freeze)
│   └── conformance/       Independent Python reference model, vector generator, 3-phase parity harness
├── cpp/               C++23 implementation of the UECM service (also sanitise.sh, coverage.sh)
├── rust/              Rust implementation, byte-for-byte parity with cpp/ (also miri.sh, coverage.sh)
├── bench/             Latency/throughput/resource benchmark harness + plotting (RQ1, RQ3)
│   ├── campaign.sh        Full measurement campaign (repeats, interleaving, bootstrap CI)
│   ├── latency_budget.sh  Split the end-to-end op into work vs. cross-thread handoff
│   ├── pool_hist.py       Pool per-run HDR buckets across repeats for the far tail
│   ├── counters.sh        Hardware counters (testbed only, needs a PMU)
│   ├── alloc_profile.sh   Attribute the peak-RSS gap to allocation sites (testbed only)
│   ├── TESTBED.md         Bare-metal protocol: the only route to testbed-grade tail figures
│   └── refresh_thesis.sh  Regenerate figures/tables/macros, rebuild Ha_Vien_Mastersthesis_2026.pdf
├── faults/            Fault-injection taxonomy (RQ2) + Loom/Shuttle model checking of the boundary classes
├── ffi/               Incremental-adoption prototype: C++ host over a Rust component via a C ABI (RQ4)
├── figures/           Generated figures, LaTeX tables, and generated macros consumed by the thesis
├── diagrams/          Source diagrams (SVG, drawio) and their rendered PDF/PNG
├── docs/              Reference notes that are not part of any document
│   ├── ASSESSMENT.md      Criterion-by-criterion self-assessment
│   ├── TODO.md            Phase checklist and open items
│   ├── LITERATURE_NOTES.md, Sources_evidence.md   Citation audit trail and literature gaps
│   └── citation.md        Citation conventions
├── archive/           Superseded document variants, kept for reference; not maintained, do not build
├── template/          Assets HYthesisML.cls loads by path (cover-page dictionaries, HY logo)
│   └── upstream/          Pristine CSM thesis template the class was taken from
├── build/             latexmk intermediates (.aux, .log, .bbl); gitignored, safe to delete
├── Ha_Vien_Mastersthesis_2026.tex   Canonical full draft, under the UH submission filename
├── Thesis_v2.tex      Supervisor-facing chapter skeleton
├── Thesis_Plan_v2.tex Revised thesis plan
├── AGENT.md           Working rules: document roles, grade criteria, verification workflow
├── bibliography.bib
├── build_deck.py      Nokia-branded slide-deck generator (reads figures/ + faults/ results)
└── .aitells.py, .vocab.py, .readability.py    Prose checks run over the LaTeX sources
```

The PDFs stay beside their sources, so `Ha_Vien_Mastersthesis_2026.pdf` and the SyncTeX index land
at the root where the editor expects them. Only the intermediates go to `build/`, which
`.latexmkrc` sets.

Each component directory (`spec/conformance/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/`) has
its own `README.md` with build and run instructions.

## Prerequisites

| Tool | Used for |
| ---- | -------- |
| C++23 compiler (g++ 13+ / clang 17+, `std::expected` is required), CMake 3.20+, Ninja | [`cpp/`](cpp/) |
| Rust stable, edition 2021 (developed on 1.97), `cargo` | [`rust/`](rust/) |
| jemalloc (`libjemalloc`) | the jemalloc arms of the benchmark (`-DUECM_USE_JEMALLOC=ON`, `cargo --features jemalloc`) |
| `latexmk`, TeX Live, bundled `HYthesisML.cls` | `Ha_Vien_Mastersthesis_2026.tex`, `Thesis_v2.tex`, `Thesis_Plan_v2.tex` |
| Python 3 + `matplotlib` | [`bench/`](bench/) plotting (`pip install -r bench/requirements.txt`) |
| AddressSanitizer / ThreadSanitizer / UBSan (`g++`) | [`faults/`](faults/), `cpp/sanitise.sh` |

Optional, each needed by one script only:

| Tool | Used for |
| ---- | -------- |
| Rust nightly + `miri` component | `rust/miri.sh` |
| `cargo-llvm-cov`, `gcov` | `rust/coverage.sh`, `cpp/coverage.sh` |
| `lizard` | complexity proxies in `bench/refresh_thesis.sh` |
| `cairosvg` | re-rendering `diagrams/` |
| `python-pptx`, `pymupdf` | `build_deck.py` |
| `perf` with a hardware PMU, `jeprof` | `bench/counters.sh`, `bench/alloc_profile.sh` (testbed only) |

## Where the numbers come from

Every measured figure in the thesis comes from the harnesses here, run on a dedicated
dual-socket Xeon E5-2680 v4 (16 cores, one NUMA node) under Rocky Linux 8.10. That host is a
**KVM guest**, and the consequence is narrow but real: frequency and turbo are host-controlled and
unobservable, CPU steal is non-zero, and no hardware counters are exposed.

- **Resolved on this host.** Parity, the fault-injection taxonomy, the FFI seam structure and its
  cost, the saturation knee, the overload divergence past saturation, and the peak-RSS and CPU
  comparisons.
- **Not resolved on this host.** The far tail below saturation. Closing it needs a bare-metal
  campaign following [`bench/TESTBED.md`](bench/TESTBED.md), which is also the only chance to
  collect the counters and the allocation profile that would explain the peak-RSS and
  operation-level results.

WSL2 is fine for development, builds, parity runs, and fault injection. Run C++ sanitizer builds
there under `setarch -m -R` (see [`faults/run_faults.sh`](faults/run_faults.sh)). It cannot produce
thesis-grade latency numbers, and it exposes no hardware PMU, so `bench/counters.sh` detects that
and refuses rather than reporting zeros for counters that never ran.

## Quick start

### 1. Verify both implementations

```bash
# C++: build + run tests
cd cpp && cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build && ctest --test-dir build --output-on-failure

# Rust: build + run tests
cd rust && cargo test --release

# Cross-language parity: reference model, hand-written vectors, then generated vectors,
# run through both implementations and diffed transcript line by line
spec/conformance/run.sh
spec/conformance/run.sh --random 60 --ops 2000   # the full generated campaign, ~9 min
```

The size of the last campaign that ran is recorded in
[`spec/conformance/results/summary.json`](spec/conformance/results/summary.json).

Deeper checks, all categorical and therefore safe on any host:

```bash
cpp/sanitise.sh     # whole suite under ASan+UBSan / TSan / UBSan
rust/miri.sh        # needs: rustup toolchain install nightly --component miri
cpp/coverage.sh     # gcov line coverage of the parity suite
rust/coverage.sh    # needs: cargo install cargo-llvm-cov --locked
```

### 2. Run the four studies

```bash
# Fault-injection taxonomy (RQ2)
faults/run_faults.sh

# The boundary classes under model checking: what Loom and Shuttle catch at test
# time, with controls that must stay quiet on the fixed versions (RQ2)
faults/run_model_checking.sh

# FFI migration prototype (RQ4). Also runs the same signaling op natively, so the
# reported seam cost is a direct A/B rather than an empty crossing against a full op.
ffi/build.sh

# Benchmark comparison across both languages × both allocators (RQ1, RQ3)
bench/run_bench.sh

# What the end-to-end latency is actually made of: the operation's own work versus
# the cross-thread submit-and-complete handoff, in both languages. Needs a quiet host.
bench/latency_budget.sh
```

**`ffi/build.sh` is a measurement, not a smoke test.** It overwrites the tracked
`ffi/results/metrics.json` and `op_cost.jsonl` with numbers from whatever host it runs on, and
those feed the RQ4 table and every `\Ffi*` macro. On a busy development machine it will quietly
replace the RQ4 evidence with noise. If you ran it only to confirm that it still builds and
passes, restore the evidence afterwards:

```bash
git checkout -- ffi/results/metrics.json ffi/results/op_cost.jsonl
```

`faults/run_faults.sh` carries no such hazard. Its outcomes are categorical (compile-time
prevented, sanitiser-detected, undetected) and do not move with host load.

### 3. Rebuild the thesis from measured data

After a measurement campaign or a fault-injection run, regenerate every figure, table, and quoted
number, then rebuild the PDF:

```bash
bench/refresh_thesis.sh
```

This runs `bench/plot_figures.py`, re-renders the diagrams that quote campaign numbers,
regenerates the complexity proxies (`bench/complexity.py`, when `lizard` is available) and the
artefact-level measurements (`bench/artefact_facts.py`), writes all of it into
[`figures/`](figures/), rebuilds the colloquium deck via `build_deck.py`, and calls
`latexmk -pdf Ha_Vien_Mastersthesis_2026.tex`. Campaign summary numbers land in
`figures/gen_macros.tex`, and both the prose and the slides refer to them by macro name, so text,
slides, and data stay in step. The generated `figures/gen_*.tex` files are never hand-edited.

To build a document alone:

```bash
latexmk -pdf Ha_Vien_Mastersthesis_2026.tex   # the thesis
latexmk -pdf Thesis_v2.tex                    # supervisor skeleton
latexmk -pdf Thesis_Plan_v2.tex               # thesis plan
```

For thesis-grade performance numbers, provision a clean testbed and run the full measurement
campaign. See [`bench/README.md`](bench/README.md) and [`bench/TESTBED.md`](bench/TESTBED.md).

```bash
bench/setup_testbed.sh          # install toolchain + apply CPU hygiene + verify
bench/campaign.sh --repeats 20  # full load sweep with bootstrap CI (see bench/README.md)
bench/refresh_thesis.sh         # refresh figures/tables/PDF from the newest campaign
```

## The subsystem under study

A self-contained, stateful, concurrent **UE Context Management** service that owns the UE
context lifecycle and executes RRC/mobility procedures. Both implementations share:

- the same **shared-nothing, thread-per-shard** concurrency model (one worker per shard, a
  bounded blocking MPSC queue, one-shot completions),
- **pinned** shard selection (SplitMix64) and intra-shard key hashing (FNV-1a), so container
  performance is never an accidental language advantage,
- the same data model, UE state machine, public API, and error model.

Full details, invariants, and the parity contract are in
[`spec/SPECIFICATION.md`](spec/SPECIFICATION.md).

## Slide deck

A Nokia-branded presentation can be generated from measured results:

```bash
python3 build_deck.py    # -> Rust_vs_Cpp_Nokia_RAN_thesis.pptx
```

The deck is figure-first: it places the generated result plots from `figures/*.pdf`
and the thesis diagrams from `diagrams/png/`, and keeps prose to a headline and a
sentence beside each picture. Nothing is transcribed. Every number comes from
`figures/gen_macros.tex`, the `figures/tab_*.tex` bodies, `faults/results/taxonomy.csv`,
and the environment capture belonging to the campaign that was plotted, and the build
fails rather than print a stale value, including when a hand-authored diagram's own
labels disagree with the generated data.

Requires the slide toolkit under `.cursor/skills/create-pptx-master-thesis/` (see `.gitignore`),
`python-pptx`, and `pymupdf` for rasterising the result plots. Diagram artwork is read
from `diagrams/png/`, which `diagrams/render.py` writes.

## Status

| Area | State |
| ---- | ----- |
| Specification + parity | Both languages pass and agree byte-for-byte on the shared conformance suite: hand-written vectors plus a generated campaign whose expectations come from an independent Python model, with mirrored per-language invariant and concurrency suites. Spec is v0.1 draft, pending supervisor freeze |
| RQ2 (safety) | Final. Fault-injection taxonomy complete across ten defect classes, five inside the guarantee and five outside it, plus Loom and Shuttle results for the two concurrency classes on the boundary |
| RQ4 (migration) | Final. FFI prototype, interleaved native-vs-seam measurement of one real operation, and seam size complete |
| RQ1/RQ3 (performance) | Campaign complete on the virtualised host, so the saturation knee, the overload divergence, and the resource comparisons are resolved there. That host cannot resolve the far tail below saturation, and a bare-metal confirmation campaign does, with Rust's pooled p99.99 below C++'s at every load the two separate. What remains is a matched repeat at the main sweep's own shard count, load grid, repeat count and toolchain. The collected jitter and the p99.99 column of the latency table are still unreported |
| Writing | `Ha_Vien_Mastersthesis_2026.pdf` builds clean with zero LaTeX errors and no undefined references, as a full draft awaiting review. `Thesis_v2.pdf` covers all eight chapters in bullets, 35 pages, and its abstract is still the template placeholder |

Open items and the post-campaign re-check list are tracked in [`docs/TODO.md`](docs/TODO.md).

Every campaign summary number quoted in the thesis prose (representative load, saturation
knee, repeat count, p99 spread) is generated into `figures/gen_macros.tex` by
`bench/plot_figures.py` alongside the figures and tables. Re-running the campaign on a
bare-metal testbed and then `bench/refresh_thesis.sh` refreshes the narrative and the data
together. There are no hand-copied numbers to go stale.
