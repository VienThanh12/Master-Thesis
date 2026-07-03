# Thesis To-Do Plan

**Title:** Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia RAN Control-Plane Systems
**Author:** Ha Vien

This plan is organized into phases. Each phase lists concrete tasks and notes which
research question(s) it serves. The hard ordering constraint: **freeze the shared
specification (Phase 2) before writing any implementation code**, since it is the
primary control against implementation bias.

---

## Phase 0 - Environment & repository setup
- [ ] Install LaTeX toolchain (TeX Live: `pdflatex`, `bibtex`, `latexmk`)
- [ ] Obtain the `UH_DS_MSc.cls` University of Helsinki thesis class file
- [ ] Create `bibliography.bib` with all cited references (see Phase 7)
- [ ] Verify `thesis.tex` compiles to PDF end-to-end
- [ ] Initialize git repository; add `.gitignore` (build artifacts, LaTeX aux files)
- [ ] Decide repo layout: `spec/`, `cpp/`, `rust/`, `bench/`, `experiments/`, `analysis/`, `thesis/`

## Phase 1 - Literature & background solidification
- [ ] Collect and read the core references (3GPP 38.401/38.300, RustBelt, MSRC, Google Android, Pereira energy study, HdrHistogram/coordinated omission)
- [ ] Confirm gNB-CU-CP / UE Context Management framing with Nokia supervisors
- [ ] Note any Nokia-internal constraints (what can/cannot be published)

## Phase 2 - Shared specification (FAIRNESS BASELINE - freeze first)
- [ ] Define the public API of the UE Context Management service
- [ ] Define the UE state machine (states + transitions, e.g. idle -> connected)
- [ ] Define data structures & algorithmic strategy (sharded hash map keyed by UE id)
- [ ] Define locking/sharding granularity and the concurrency model (thread-per-shard)
- [ ] Define the message/signaling set to handle
- [ ] Define parity-test contract (behaviour both implementations must match)
- [ ] Review spec with supervisors and FREEZE it (tag/version it)

## Phase 3 - C++ implementation
- [ ] Scaffold CMake project (C++17/20, STL, standard threading)
- [ ] Wire jemalloc allocator + HdrHistogram latency capture
- [ ] Implement sharded context store + UE state machine per spec
- [ ] Implement signaling/message handling + concurrent lookup
- [ ] Unit tests + run against parity-test contract

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
- Deadline / target submission date: TBD
- Current code status: none written yet (workspace has only thesis.tex)
- Source of `UH_DS_MSc.cls` and existing `.bib`: TBD (Overleaf? university?)
