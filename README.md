# Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia RAN Control-Plane Systems

Master's thesis (University of Helsinki, Software study track) by **Ha Vien**.

This repository holds both the written thesis (LaTeX) and the complete artefact
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
| **RQ1** | Latency predictability (median, p99, p99.9, p99.99, and the maximum) under increasing load and overload | [`bench/`](bench/)   |
| **RQ2** | Which C++ defect classes safe Rust eliminates at compile time, and at what stage and cost the rest are detected | [`faults/`](faults/) |
| **RQ3** | What overhead Rust's safety model imposes on throughput, CPU utilisation, and memory                | [`bench/`](bench/)   |
| **RQ4** | What incremental adoption of Rust inside an existing C++ codebase costs                             | [`ffi/`](ffi/), [`bench/adoption_cost.py`](bench/adoption_cost.py) |

The RQ2 catalogue deliberately spans both sides of the guarantee. Safe Rust rejects seven of
the fourteen defect classes at compile time (use-after-free, double free, iterator
invalidation, data race, unguarded shared mutation, use-after-move, thread-unsafe sharing)
and compiles the other seven without complaint (lock-order deadlock, lost update,
reference-cycle leak, release-build integer overflow, worker-failure blast radius, double-free
across an `unsafe` FFI seam, forgotten lock guard), so the study measures where the guarantee
*stops* rather than only confirming that it holds.

Two of those in-guarantee classes carry information the rest do not. `use_after_move` is the
only one no C++ sanitiser reports (a moved-from object is valid but unspecified, so nothing
is undefined). `thread_unsafe_sharing` is rejected by a `Send`/`Sync` bound (`E0277`), not by
the borrow checker. Two of the boundary classes came back with the C++ tooling ahead: the
reference-cycle leak, caught by ASan and silent in Rust, and the release-build overflow,
caught by UBSan and wrapped in Rust. Both stay in the catalogue. `seam_double_free` is
`double_free` rewritten through `unsafe`, not a new class: the C++ half is unchanged so only
the Rust column moves.

For the two concurrency classes on the boundary, lock-order deadlock and lost update,
[`faults/run_model_checking.sh`](faults/run_model_checking.sh) asks what Loom and Shuttle
catch at test time, and at what cost. For the `unsafe` class,
[`faults/run_miri.sh`](faults/run_miri.sh) asks the same of Miri. Rust eliminates data races
and aliasing errors at compile time. It does not eliminate race conditions or lock-order
deadlocks.

The methodological control against implementation bias is a **frozen, language-neutral
specification**: both implementations must conform to it exactly, and any forced idiomatic
divergence is logged. See [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md).

## The documents

The PDFs in this repository do not share a status and are not interchangeable.

| Document | Status | Role |
| -------- | ------ | ---- |
| `Thesis_Plan_v2.pdf` | Reviewed, supervisor-facing | Approved plan: gap, RQs, methodology, timeline, contributions |
| `Thesis_v3.pdf` | Reviewed, supervisor-facing | Supervisor read-through: Chapter 1 is the full draft introduction, chapters 2--8 keep five argument paragraphs each in plain prose. All eight chapters match the full draft's chapter list since 26 August 2026, the results paragraphs quote the generated macros rather than carrying their own numbers, and the abstract is written (11 September 2026). Called `Thesis_v2` until 8 September 2026 |
| `Ha_Vien_Mastersthesis_2026.pdf` | Full draft, not final | The canonical long-form thesis. Rich figures, generated numbers, a full argument, and everything in it still needs review. The name is the UH submission format (`Lastname_Firstname_Mastersthesis_Year`, ASCII) and says nothing about review status. It was `Thesis_POC` until 19 August 2026 |
| `Ha_Vien_Mastersthesis_2026_short.pdf` | Compression pass, in progress | A shorter cut of the full draft, built from the same class, macros, figures and bibliography. It declares 55 pages against the draft's 97, with the same 12 appendix pages. Both documents are `oneside`, matching electronic submission. The material it sheds is relocated to appendices or merged rather than deleted, and [`.compress/shortcheck.py`](.compress/shortcheck.py) is what checks that nothing was lost. Not supervisor-facing and not a submission candidate |
| `source_audit.pdf` | Generated citation audit | Every bibliography entry, ordered as in the full draft's reference list, with the citing sentence beside the source's own words. Built by [`.bibaudit/build_audit.py`](.bibaudit/build_audit.py). Do not hand-edit `source_audit.tex`, with one exception: the last column of Part 1 is the author's review tick, and turning a `$\square$` into a `$\blacksquare$` is how the source-checking pass records progress. The generator reads those ticks back out of the old document before overwriting it, mirrors them to `.bibaudit/reviewed.txt`, and prints how many it carried. Read that line after every rebuild, because a regeneration silently wiped 22 of them on 1 September 2026 |
| `source_audit_v3.pdf` | Generated citation audit of `Thesis_v3` | The same document scoped to the supervisor skeleton: 61 cited works, numbered as in `Thesis_v3.pdf`, plus the 50 shared-`.bib` entries that this PDF does not cite. Rebuild with `.bibaudit/build_audit.py --document v3 && latexmk -pdf source_audit_v3.tex`. Tick column mirrors to `.bibaudit/reviewed_v3.txt`. Do not copy ticks from the draft audit: compression can leave a key attached to a different clause |
| `ai_statement.tex` | Declaration in the author's name | Statement on generative-AI use, shared by the full draft, the supervisor skeleton, and the short cut. Edit this file, never a copy |
| [`archive/`](archive/) | Superseded, not maintained | Earlier variants kept for reference only. See [`archive/README.md`](archive/README.md). Includes `plain_thesis.tex`, `thesis-vi.tex` (Vietnamese full-draft translation, citations as `[?]`), `Thesis_v3-vi.tex` (Vietnamese skeleton snapshot of 11 September 2026), `thesis_wbm_full_backup.tex`, the pre-cuts `Thesis_POC.tex.bak-before-cuts`, the v1 plan PDF, the retired `UH_DS_MSc.cls`, and the dated `rollback-20260827-220354/` snapshot. They read relative paths from the repository root, so they no longer build where they sit |

[`AGENT.md`](AGENT.md) is the working contract for the repository: document roles, the grade
criteria every edit has to protect, the scientific commitments that must not be weakened, and the
verification workflow. Read it before touching thesis text, figures, or artefacts.
[`docs/guide/README.md`](docs/guide/README.md) is a file-by-file encyclopedia of the same tree
(documents, evidence, campaigns, generated macros, prose screens, tooling).
[`docs/ASSESSMENT.md`](docs/ASSESSMENT.md) holds the criterion-by-criterion self-assessment and
[`docs/TODO.md`](docs/TODO.md) the phase checklist and open items. The durable citation-audit
record is [`docs/Sources_evidence.md`](docs/Sources_evidence.md). `source_audit.pdf` is the
reader-facing view of that record.

## Repository layout

```
.
├── spec/              Frozen specification + language-neutral conformance suite (the fairness baseline)
│   ├── SPECIFICATION.md   The fairness baseline (v0.1 draft, pending supervisor freeze)
│   └── conformance/       Independent Python reference model, vector generator, 3-phase parity harness
├── cpp/               C++23 implementation of the UECM service (also sanitise.sh, coverage.sh)
├── rust/              Rust implementation, byte-for-byte parity with cpp/ (also miri.sh, coverage.sh)
├── bench/             Latency/throughput/resource benchmark harness + plotting (RQ1, RQ3, RQ4 axes)
│   ├── campaign.sh        Full measurement campaign (repeats, interleaving, bootstrap CI)
│   ├── canonical_repeat.sh Pre-campaign hygiene: refuses a broken CPU-spread config
│   ├── latency_budget.sh  Split the end-to-end op into work vs. cross-thread handoff
│   ├── queue_contention.sh Isolate the handoff primitives from the service
│   ├── pool_hist.py       Pool per-run HDR buckets across repeats for the far tail
│   ├── counters.sh        Hardware counters (testbed only, needs a PMU)
│   ├── alloc_profile.sh   Attribute the peak-RSS gap to allocation sites (testbed only)
│   ├── adoption_cost.py   RQ4 axes beyond the seam (build time replayed unless --measure)
│   ├── baremetal_facts.py  Confirmation-host macros (`figures/gen_baremetal.tex`)
│   ├── guest_facts.py     Guest-campaign macros (`figures/gen_guest.tex`)
│   ├── TESTBED.md         Bare-metal protocol: the only route to testbed-grade tail figures
│   └── refresh_thesis.sh  Regenerate figures/tables/macros, rebuild Ha_Vien_Mastersthesis_2026.pdf
├── faults/            Fault-injection taxonomy (RQ2) + Loom/Shuttle/Miri on the boundary classes
├── ffi/               Incremental-adoption prototype: C++ host over a Rust component via a C ABI (RQ4)
├── docker/            Rocky 8.10 image with the campaign toolchain pinned (not itself a testbed)
├── figures/           Generated figures, LaTeX tables, and generated macros consumed by the thesis
├── diagrams/          Source diagrams (SVG, drawio) and their rendered PDF/PNG. Diagrams 20--29 are generated. `check_labels.py` is the prose-style gate
├── docs/              Reference notes that are not part of any document
│   ├── README.md          Index of this folder
│   ├── guide/             Encyclopedia: every artefact, campaign, screen, and rule
│   ├── ASSESSMENT.md      Criterion-by-criterion self-assessment
│   ├── TODO.md            Phase checklist and open items
│   ├── LITERATURE_NOTES.md, Sources_evidence.md   Citation audit trail. `source_audit.pdf` is the reader-facing view
│   ├── citation.md        Citation conventions
│   ├── CHAPTER_READABILITY.md   Per-chapter Flesch table (generated)
│   └── review/            Commented PDFs a reviewer returns, read by pdfannots.py. Gitignored, create it locally
├── .bibaudit/         Generates `source_audit.tex` (full draft) and `source_audit_v3.tex` (`--document v3`) from `bibliography.bib`, the `.bbl`, and the evidence notes
│   ├── reviewed.txt       Mirror of Part 1's review ticks for the draft audit
│   └── reviewed_v3.txt    Same sidecar for the `Thesis_v3` audit
├── .compress/         One-shot tools for the short cut of the full draft. Run them from the repository root, as with bench/
│   ├── lengthprice.py     Price prose words, floats and page span per chapter, section and subsection
│   ├── shortcheck.py      Report citation keys, labels, references and macros the short cut dropped
│   ├── reloc.py, movapp.py   Move a body block into the appendices, or reorder appendices
│   ├── strip.py, deref.py, retarget.py   Delete relocated material and repoint what referenced it
│   └── drafts/            Rewritten chapter candidates and the pre-relocation backup
├── archive/           Superseded document variants and retired assets (including `Thesis_v3-vi.tex`), kept for reference; not maintained, do not build
├── template/          Assets HYthesisML.cls loads by path (cover-page dictionaries, HY logo)
│   └── upstream/          Pristine CSM thesis template the class was taken from
├── build/             latexmk intermediates (.aux, .log, .bbl); gitignored, safe to delete
├── HYthesisML.cls     Department class file the thesis documents build on
├── Ha_Vien_Mastersthesis_2026.tex   Canonical full draft, under the UH submission filename
├── Ha_Vien_Mastersthesis_2026_short.tex   Shorter cut of the same draft, in progress. Tooling in `.compress/`
├── Thesis_v3.tex      Supervisor-facing chapter skeleton
├── Thesis_Plan_v2.tex Revised thesis plan
├── source_audit.tex   Generated citation audit of the full draft. Only the Part 1 review tick is hand-edited. Rebuild with `.bibaudit/build_audit.py && latexmk -pdf source_audit.tex`
├── source_audit_v3.tex   Same audit scoped to `Thesis_v3`. Rebuild with `.bibaudit/build_audit.py --document v3 && latexmk -pdf source_audit_v3.tex`
├── ai_statement.tex  Declaration on generative-AI use, shared by the full draft, the skeleton, and the short cut
├── AGENT.md           Working rules: document roles, grade criteria, verification workflow
├── bibliography.bib
├── build_deck.py      Nokia-branded slide-deck generator (reads figures/ + faults/ results)
├── pdfpreview.py      Rasterise PDF pages into .pdf-preview/, since the WSL webview shows none
├── pdfannots.py       Pull a reviewer's highlights and notes out of a commented PDF in docs/review/
└── .aitells.py, .vocab.py, .b2.py, .readability.py, .acronyms.py, .chapter_readability.py    Prose checks. `.acronyms.py` is a gate, not a count. `.b2.py` is a frequency companion to `.vocab.py`. `.chapter_readability.py` writes `docs/CHAPTER_READABILITY.md`
```

The PDFs stay beside their sources, so `Ha_Vien_Mastersthesis_2026.pdf` and the SyncTeX index land
at the root where the editor expects them. Only the intermediates go to `build/`, which
`.latexmkrc` sets. An editor that overrides the aux directory will still drop `.aux` and `.log`
files at the root. `bench/refresh_thesis.sh` already falls back to those copies.

**The document sources have to stay at the root**, which is worth knowing before anyone tidies them
into a subdirectory. Every one of them resolves `figures/`, `diagrams/pdf/`, `template/figures/` and
`ai_statement.tex` as paths from the root, and [`archive/README.md`](archive/README.md) records that
the archived variants stopped building the moment they moved. The four prose checks are pinned for a
different reason: `bench/refresh_thesis.sh`, `diagrams/check_labels.py`, the grading skill and
`.cursor/rules/thesis-quality.mdc` all name them by path.

Each component directory (`spec/conformance/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/`,
`docker/`) has its own `README.md` with build and run instructions.

## Prerequisites

| Tool | Used for |
| ---- | -------- |
| C++23 compiler (g++ 13+ / clang 17+, `std::expected` is required), CMake 3.20+, Ninja | [`cpp/`](cpp/) |
| Rust stable, edition 2021 (developed on 1.97), `cargo` | [`rust/`](rust/) |
| jemalloc (`libjemalloc`) | the jemalloc variants of the benchmark (`-DUECM_USE_JEMALLOC=ON`, `cargo --features jemalloc`) |
| `latexmk`, TeX Live, bundled `HYthesisML.cls` | `Ha_Vien_Mastersthesis_2026.tex`, `Thesis_v3.tex`, `Thesis_Plan_v2.tex`, `source_audit.tex`, `source_audit_v3.tex` |
| Python 3 + `matplotlib` | [`bench/`](bench/) plotting (`pip install -r bench/requirements.txt`) |
| AddressSanitizer / ThreadSanitizer / UBSan (`g++`) | [`faults/`](faults/), `cpp/sanitise.sh` |

The reported campaign was built with GCC 15 and rustc 1.97.1 inside the Rocky Linux 8.10
image of [`docker/`](docker/README.md). A host compiler that meets the table above is enough
for development, parity, and fault injection. It is not enough to reproduce the quoted
numbers, because those also depend on the machine.

Optional, each needed by one script only:

| Tool | Used for |
| ---- | -------- |
| Rust nightly + `miri` component | `rust/miri.sh`, `faults/run_miri.sh` |
| `cargo-llvm-cov`, `gcov` | `rust/coverage.sh`, `cpp/coverage.sh` |
| `lizard` | complexity proxies in `bench/refresh_thesis.sh` |
| `cairosvg` | re-rendering `diagrams/` |
| `python-pptx` | `build_deck.py` |
| `pymupdf` | `build_deck.py` (rasterising the result plots), `pdfpreview.py`, `pdfannots.py` |
| Docker | [`docker/run.sh`](docker/README.md), the pinned-toolchain campaign path |
| `perf` with a hardware PMU, `jeprof` | `bench/counters.sh`, `bench/alloc_profile.sh` (testbed only) |

## Where the numbers come from

Every measured figure in the thesis comes from the harnesses here, run on a dedicated bare-metal
AMD EPYC 7443 (24 cores, one socket, one NUMA node) with SMT off, the `performance` governor and
boost disabled, `nohz_full` on the pinned cores, and no hypervisor. The toolchain is pinned in the
Rocky Linux 8.10 container image of [`docker/`](docker/README.md) rather than taken from the host.
The container pins the `gcc-toolset` major version, not the point release, so the reported campaign
ran `g++` 15.2.1 against the guest campaign's 15.1.1. `rustc` matches at 1.97.1. Do not write that
the two share a toolchain. The honest comparison is the same design on a different machine, with
that one patch recorded. [`docker/README.md`](docker/README.md) already names it.

Three campaigns exist and they are not interchangeable. The LaTeX macro prefix is what keeps
them apart, and a sentence that quotes the wrong prefix is wrong in a way no build gate catches.

| Campaign | Macros | Role |
| --- | --- | --- |
| `campaign-20260827-151927` (bare metal, 7 shards, 7 producers, 20 repeats, 14 loads) | unprefixed, `figures/gen_macros.tex` | **Every result the thesis reports.** |
| `campaign-20260812-154528` (KVM guest, identical design) | `\Guest*`, `figures/gen_guest.tex` | The measurement-validity comparison: the same code and design on a host that could not resolve the far tail. `g++` is one patch apart from the reported campaign (`\GuestGpp` 15.1.1, `\MainGpp` 15.2.1). |
| `campaign-20260826-*` (bare metal, 8 shards, 8 producers, 15 repeats, 8 loads) | `\Bm*`, `figures/gen_baremetal.tex` | Whether the findings survive a change of shard count, load grid, repeat count and compiler. |

`bench/results-canonical/` holds an invalid 1120-run campaign from 27 August 2026. It was
collected with `isolcpus` set, which pinned every thread to a single core. Do not quote it.

The far tail below saturation was the study's standing open question for as long as it measured
on a virtualised host. It is resolved on bare metal, as a **pooled** statistic over operations
rather than a median of per-run p99.99 values, and favours Rust at every load the two
languages separate. Past saturation the languages diverge, and they stop meeting the offered
rate at different loads: quote the per-language tracking limits, not a single shared knee.
What the host comparison also showed is that the peak-RSS **allocator** effect of an
order of magnitude belonged to the guest, while the **language** effect is the same size on
all three hosts. On both bare-metal machines the two effects are comparable. The
transparent-hugepage policy differed between the hosts and is the named candidate for the
allocator collapse. The study never varied it with everything else fixed, and does not claim
causation.

**Do not add `isolcpus` when reproducing this.** It gives the cleanest tails and it also removes
the cores from every scheduling domain, and because the benchmark pins to a range and relies on
the kernel to spread its threads, an isolated set puts all of them on one core. A full 1120-run
campaign was lost to it on 27 August 2026. `bench/canonical_repeat.sh check-spread` now refuses to
start when that happens, and [`bench/TESTBED.md`](bench/TESTBED.md) §2 documents it.

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

# The unsafe boundary class under Miri, with a control that must stay quiet (RQ2)
faults/run_miri.sh

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

`bench/adoption_cost.py --measure` has the same shape of hazard for build time. The refresh
script calls it *without* `--measure` on purpose, so the recorded timing is replayed and only
the deterministic axes (footprint, third-party surface) are recomputed.

`faults/run_faults.sh` carries no such hazard. Its outcomes are categorical (compile-time
prevented, sanitiser-detected, undetected) and do not move with host load.

### 3. Rebuild the thesis from measured data

After a measurement campaign or a fault-injection run, regenerate every figure, table, and quoted
number, then rebuild the PDF:

```bash
bench/refresh_thesis.sh
```

This pools the histogram sidecars (so the p99.99 column is the pooled statistic, not a median
of per-run values), runs `bench/plot_figures.py`, regenerates the confirmation-host and guest
macros (`bench/baremetal_facts.py`, `bench/guest_facts.py`), re-renders the diagrams that quote
campaign numbers, checks their labels, regenerates the complexity proxies (`bench/complexity.py`,
when `lizard` is available) and the artefact-level measurements (`bench/artefact_facts.py`),
replays the RQ4 adoption-cost axes, writes all of it into [`figures/`](figures/), rebuilds the
colloquium deck via `build_deck.py`, and calls `latexmk -pdf Ha_Vien_Mastersthesis_2026.tex`.
Campaign summary numbers land in `figures/gen_macros.tex`, and both the prose and the slides
refer to them by macro name, so text, slides, and data stay in step. The generated
`figures/gen_*.tex` files are never hand-edited. The citation audit is a separate document and
is not rebuilt here. Neither are `Thesis_v3.pdf` and `Thesis_Plan_v2.pdf`: rebuild those with
`latexmk` after the macros move.

Without `--campaign`, the refresh takes the newest log in `bench/results/`. Pass the reported
campaign explicitly if that directory holds anything else:

```bash
bench/refresh_thesis.sh --campaign bench/results/campaign-20260827-151927.jsonl
```

To build a document alone:

```bash
latexmk -pdf Ha_Vien_Mastersthesis_2026.tex   # the thesis
latexmk -pdf Thesis_v3.tex                    # supervisor skeleton
latexmk -pdf Thesis_Plan_v2.tex               # thesis plan
.bibaudit/build_audit.py && latexmk -pdf source_audit.tex   # citation audit (full draft)
.bibaudit/build_audit.py --document v3 && latexmk -pdf source_audit_v3.tex   # citation audit (Thesis_v3)
```

The audit generator takes printed numbers from the thesis `.bbl` and refuses to run when that
file disagrees with the source's cite keys, so a stale numbering cannot reach the page.
Everything in `source_audit.tex` and `source_audit_v3.tex` is derived and a hand edit to either is lost on the next run, apart
from the review tick described above.

For thesis-grade performance numbers, provision a clean testbed and run the full measurement
campaign. See [`bench/README.md`](bench/README.md) and [`bench/TESTBED.md`](bench/TESTBED.md).
The pinned-toolchain path is [`docker/run.sh`](docker/README.md). A container is not a
testbed: it shares the host kernel, so the scheduler, the governor, and any hypervisor stay
whatever the host's are.

```bash
bench/canonical_repeat.sh check-spread   # refuses to start on a one-core pin
bench/setup_testbed.sh                   # install toolchain + apply CPU hygiene + verify
bench/campaign.sh --repeats 20           # full load sweep with bootstrap CI (see bench/README.md)
bench/refresh_thesis.sh                  # refresh figures/tables/PDF from the newest campaign
```

### 4. Check the prose after writing

Prose reaches a reader through three surfaces, the LaTeX sources, the diagram labels and the
slide deck, and each carries its own gate because none of them can see the other two:

```bash
./.aitells.py Ha_Vien_Mastersthesis_2026.tex   # LaTeX sources, and the default if none is given
python3 .vocab.py                              # hard Latinate vocabulary (hand-written list)
python3 .b2.py                                 # CEFR-frequency vocabulary (companion to .vocab.py)
python3 .readability.py                        # sentence and paragraph load
./.acronyms.py                                 # every front-matter acronym written out at first use
diagrams/check_labels.py                       # diagram labels, also run by refresh_thesis.sh
python3 build_deck.py                          # the deck checks its own slides on save
```

The count scripts report frequency rather than errors, so read the language-model fingerprints
(transition openers, promotional adjectives, uniform sentence length) as frequency and aim low
rather than at zero. `.acronyms.py` is a gate: it exits non-zero if a listed acronym is not written
out at first use. Four of `.aitells.py`'s checks are house rules where zero is the target: em
dashes, semicolons, and the two colon checks added on 4 September 2026 at the supervisor's
request. A capital follows a colon in two shapes only, a run-in label such as `\textbf{H1:}` and
a colon introducing a question. Every other colon keeps a lowercase word after it, so do not
sweep them.

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
| RQ2 (safety) | Final. Fault-injection taxonomy complete across fourteen defect classes, seven inside the guarantee and seven outside it, plus Loom and Shuttle on the two concurrency boundary classes and Miri on the unsafe one |
| RQ4 (migration) | Final. FFI prototype, interleaved native-vs-seam measurement of one real operation, seam size, and the three adoption-cost axes beyond the seam (build time, static footprint, third-party surface) |
| RQ1/RQ3 (performance) | Complete. The matched bare-metal campaign ran on 27 August 2026 and is the reported dataset, so the per-language saturation limits, the overload divergence, the resource comparisons and the far tail below saturation are all resolved on one host at the canonical design. Rust's pooled p99.99 sits below C++'s at every load the two separate. Jitter and the p99.99 column are reported. One question the data raised remains open: whether the peak-RSS allocator effect tracks the transparent-hugepage policy |
| Sources | 111 bibliography entries, every one of them cited. `docs/Sources_evidence.md` records per entry what claim the citation carries and where the supporting passage was read, and `source_audit.pdf` is the reader-facing view of it. 29 entries were ticked as read against the source itself at 2 September 2026 |
| Writing | `Ha_Vien_Mastersthesis_2026.pdf` builds clean with zero LaTeX errors and no undefined references. It is a full draft awaiting review. The printed abstract matches the tables, and the AI declaration records that it was written unaided. The draft and the skeleton carry a front-matter list of acronyms as of 4 September 2026, so an acronym added to either needs a row there as well as the expansion at its first use. `Thesis_v3.pdf` is the eight-chapter supervisor read-through (full Chapter 1, five prose paragraphs in each of chapters 2--8). Its abstract is written, dated 11 September 2026, and the twenty-fourth grading pass of that day put all six assessable areas at 5. That grade is the skeleton's, not the draft's |

The self-assessment in [`docs/ASSESSMENT.md`](docs/ASSESSMENT.md) records two current grades, and
they are not interchangeable. The submission draft stands at the twenty-second pass, 7 September
2026 afternoon: areas 1, 2, 3 and 5 at 5, areas 4 and 6 at **4.5**, mean **4.83**. The supervisor
skeleton stands at the twenty-fourth pass, 11 September 2026: all six assessable areas at **5**.
Do not copy that 5 onto the draft. The draft's remaining caps are disclosure, listed as items
**O** to **S** in [`docs/TODO.md`](docs/TODO.md): three prose sites plus `tab:testbed` claiming
toolchain parity with the guest (`\GuestGpp` 15.1.1 against `\MainGpp` 15.2.1), §6.4.7 hand-typing
the guest's compiler as the measurement host's, and the RQ3 cell of `tab:findings` saying "on bare
metal". Those items are closed in the skeleton. What earned the rest was reviewers who were told
nothing about what had changed: they found 49 of the 69 recorded defects, all of them prose
disagreeing with an artefact that was itself correct.

Every campaign summary number quoted in the thesis prose (representative load, saturation
knee, repeat count, p99 spread) is generated into `figures/gen_macros.tex` by
`bench/plot_figures.py` alongside the figures and tables. Re-running the campaign on a
bare-metal testbed and then `bench/refresh_thesis.sh` refreshes the narrative and the data
together. There are no hand-copied numbers to go stale.
