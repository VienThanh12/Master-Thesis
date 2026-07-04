# Thesis To-Do Plan

**Title:** Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia RAN Control-Plane Systems
**Author:** Ha Vien

This plan is organized into phases. Each phase lists concrete tasks and notes which
research question(s) it serves. The hard ordering constraint: **freeze the shared
specification (Phase 2) before writing any implementation code**, since it is the
primary control against implementation bias.

---

## Phase 0 - Environment & repository setup
- [x] Install LaTeX toolchain (TinyTeX in ~/.TinyTeX; `pdflatex`, `bibtex`, `latexmk` on PATH)
- [x] Obtain the `UH_DS_MSc.cls` class file (local reconstruction from UH_*_MSc family; see note)
- [x] Create `bibliography.bib` with all cited references (9 entries; see Phase 7)
- [x] Verify `thesis.tex` compiles to PDF end-to-end (31 pages, all refs/citations resolve)
- [x] Initialize git repository; add `.gitignore` (build artifacts, LaTeX aux files)
- [ ] (Optional) Replace reconstructed `UH_DS_MSc.cls` with the official one from Overleaf/Moodle
- [ ] Confirm the cover-page programme label ("Master's Programme in Computer Science") is correct
- [ ] Decide repo layout: `spec/`, `cpp/`, `rust/`, `bench/`, `experiments/`, `analysis/`, `thesis/`

### Build instructions
```bash
# Toolchain is TinyTeX; PATH set in ~/.bashrc (open a new terminal or `source ~/.bashrc`)
latexmk -pdf thesis.tex      # build -> thesis.pdf
latexmk -C                   # clean build artifacts
```

## Phase 1 - Literature & background solidification
- [ ] Collect and read the core references (3GPP 38.401/38.300, RustBelt, MSRC, Google Android, Pereira energy study, HdrHistogram/coordinated omission)
- [ ] Confirm gNB-CU-CP / UE Context Management framing with Nokia supervisors
- [ ] Note any Nokia-internal constraints (what can/cannot be published)

## Phase 2 - Shared specification (FAIRNESS BASELINE - freeze first)
- [x] Define the public API of the UE Context Management service  (spec/SPECIFICATION.md §6)
- [x] Define the UE state machine (states + transitions)            (§5)
- [x] Define data structures & algorithmic strategy (sharded map, pinned hash) (§8)
- [x] Define locking/sharding granularity and the concurrency model (thread-per-shard) (§7)
- [x] Define the message/signaling set to handle                    (§6)
- [x] Define parity-test contract (behaviour both implementations must match) (§11)
- [ ] Seed an initial conformance suite in spec/conformance/
- [ ] Review spec DRAFT v0.1 with supervisors; resolve Appendix A open decisions
- [ ] On approval: bump to v1.0 and tag `spec-v1.0` (FREEZE)

## Phase 3 - C++ implementation
- [x] Scaffold CMake project (C++23, STL, standard threading) + smoke tests (2/2 pass)
- [x] Implement pinned types, hash/shard functions, error model (spec §4,§6,§8)
- [x] Implement ShardCore: sharded context store + UE state machine per spec (single-threaded)
- [x] Implement threaded service: bounded MPSC queue per shard + worker threads + completions (spec §7)
- [x] Implement signaling/message handling + concurrent lookup at service level
- [x] Verify data-race freedom under ThreadSanitizer (0 races; use `setarch -m -R` on WSL2)
- [ ] Wire jemalloc allocator (CMake option ready) + HdrHistogram latency capture
- [ ] Run against shared parity-test contract (spec §11)

## Phase 4 - Rust implementation
- [ ] Scaffold Cargo project (stable toolchain, matched release/codegen settings)
- [ ] Wire jemalloc allocator + HdrHistogram (Rust bindings)
- [ ] Implement sharded context store + UE state machine per spec
- [ ] Implement signaling/message handling + concurrent lookup
- [ ] Record location + justification of any `unsafe` blocks
- [ ] Unit tests + run against parity-test contract

## Phase 5 - Parity verification
- [ ] Confirm both implementations pass identical functional parity tests
- [ ] Diff behaviour on edge cases; document forced-idiom deviations

## Phase 6 - Benchmarking framework & workload generator
- [ ] Build synthetic workload generator (UE creation bursts, mobility/handover,
      context updates, concurrent signaling), rates anchored to 3GPP/RAN characteristics
- [ ] Parameterize by target event rate and number of active UEs (sweep to overload)
- [ ] Ensure histogram-based capture avoids coordinated-omission bias
- [ ] Define testbed config (CPU pinning, disable turbo/freq scaling, warm-up discard)
- [ ] Make runs scriptable + reproducible (publish scripts)

## Phase 7 - Experiment campaigns
### 7a. Load sweep (RQ1 latency predictability, RQ3 overhead)
- [ ] Run load sweep nominal -> saturation -> overload, many repeats
- [ ] Collect latency (mean/p99/p99.9/p99.99/max/jitter), throughput, CPU, memory
### 7b. Fault-injection study (RQ2 safety)
- [ ] Inject C++ defect catalogue (use-after-free, data race, double-free,
      iterator invalidation, unguarded shared mutation)
- [ ] Record per defect: Rust compile-time rejection? C++ runtime (ASan/TSan) cost? undetected?
- [ ] Produce defect-class taxonomy table
### 7c. FFI migration prototype (RQ4 adoption cost)
- [ ] Build a small Rust module interoperating with C++ via FFI
- [ ] Measure interop boilerplate, FFI safety boundary, engineering effort

## Phase 8 - Analysis & figures
- [ ] Compute variance + confidence intervals across runs
- [ ] Generate latency-vs-load plots per language
- [ ] Fill Table (latency percentiles) and Table (defect taxonomy)
- [ ] Draft evidence-based migration/language-selection guidelines

## Phase 9 - Writing (fill placeholders in thesis.tex)
- [ ] Build `bibliography.bib` (3gpp38401, 3gpp38300, msrc2019memory, google2022android,
      klabnik2023rust, jung2018rustbelt, astrauskas2020unsafe, tene_hdrhistogram, pereira2017energy)
- [ ] Complete "Implementation details" section with concrete data structures/locking
- [ ] Populate "Evaluation data" and "Evaluation results" with measured data
- [ ] Complete Discussion: summary of findings, per-RQ discussion
- [ ] Finalize conclusion + future work
- [ ] Polish abstract to reflect actual (not expected) results

## Phase 10 - Finalization
- [ ] Full proofread + supervisor review round(s)
- [ ] Verify all cross-references, citations, tables, figures resolve
- [ ] Reproducibility check: clean clone -> build -> run -> compile PDF
- [ ] Final PDF + submission

---

### Notes / open questions
- Timeline: 3-6 months.
- Current code status: none written yet (thesis.tex + build environment now in place).
- `UH_DS_MSc.cls` is a LOCAL RECONSTRUCTION adapted from `UH_TCM_MSc.cls` (which states it
  is "based heavily on the UH_DS_MSc.cls"). It defines every command thesis.tex uses
  (`\prof`, `\censors`, `\mytableofcontents`, `\mynomenclature`, `\myappendixtitle`,
  `\depositeplace`, `\additionalinformation`, `\quoting`, `\keywords`, `\classification`).
  The genuine class lives behind the UH Overleaf/Moodle login; swap it in for final submission.
- `\mynomenclature` is a no-op here (the `nomencl` package clashes with hyperref/report in
  this class family and is disabled upstream too); it just switches page numbering to arabic.
- Cover/abstract programme is set to "Master's Programme in Computer Science" (English),
  inferred from `\additionalinformation{Software study track}`. Verify this is right.
- Logo `UH-logo.png` is the official UH logo taken from the UH CS thesis-template repo.
