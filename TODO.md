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
- [x] Seed an initial conformance suite in spec/conformance/ (format README + `basic.vec`, `shards.vec` + shared runners + `run.sh`; both impls agree)
- [ ] Review spec DRAFT v0.1 with supervisors; resolve Appendix A open decisions
- [ ] On approval: bump to v1.0 and tag `spec-v1.0` (FREEZE)

## Phase 3 - C++ implementation
- [x] Scaffold CMake project (C++23, STL, standard threading) + smoke tests (2/2 pass)
- [x] Implement pinned types, hash/shard functions, error model (spec §4,§6,§8)
- [x] Implement ShardCore: sharded context store + UE state machine per spec (single-threaded)
- [x] Implement threaded service: bounded MPSC queue per shard + worker threads + completions (spec §7)
- [x] Implement signaling/message handling + concurrent lookup at service level
- [x] Verify data-race freedom under ThreadSanitizer (0 races; use `setarch -m -R` on WSL2)
- [x] Wire jemalloc allocator (`-DUECM_USE_JEMALLOC=ON`, links `libjemalloc.so.2`) + HDR latency capture (`cpp/bench/hdr.hpp`, validated) in `cpp/bench/bench.cpp`
- [x] Run against shared parity-test contract (spec §11) — `conformance_runner` passes `basic.vec`, `shards.vec`

## Phase 4 - Rust implementation
- [x] Scaffold Cargo project (stable toolchain 1.96; release opt-level=2 to match C++ -O2)
- [x] Implement pinned types, hash/shard functions (LE-byte FNV BuildHasher == fnv1a_64), error model (spec §4,§6,§8)
- [x] Implement ShardCore: sharded context store + UE state machine per spec (single-threaded)
- [x] Implement threaded service: thread-per-shard + bounded `sync_channel` backpressure + typed one-shot completions (spec §7)
- [x] Implement signaling/message handling + concurrent lookup at service level
- [x] Record location + justification of any `unsafe` blocks (result: **zero `unsafe`** — safe Rust is data-race-free by construction)
- [x] Unit/conformance tests green (5/5); `cargo clippy -D warnings` clean; `cargo fmt` applied
- [x] Wire jemalloc allocator (`--features jemalloc`, `tikv-jemallocator` global allocator) + HdrHistogram (`hdrhistogram` crate) in `rust/examples/bench.rs`
- [ ] (Optional) Miri UB/data-race pass once a nightly toolchain is available
- [x] Run against shared parity-test contract (spec §11) — `conformance_runner` passes `basic.vec`, `shards.vec`; transcript matches C++ byte-for-byte

## Phase 5 - Parity verification
- [x] Confirm both implementations pass identical functional parity tests (shared `conformance_runner`; op-for-op transcript match on `basic.vec`/`shards.vec` — expand vector coverage later)
- [~] Diff behaviour on edge cases; document forced-idiom deviations (deviations logged in spec §12; add more adversarial vectors)

## Phase 6 - Benchmarking framework & workload generator
- [x] Build synthetic workload generator (UE lifecycle: attach, signaling, bearer setup, handover begin/complete/abort, release) — pinned deterministic model, identical op-stream in C++/Rust (`--workload mixed`)
- [x] Parameterize by number of active UEs (`--active-ues`) and target event rate (`--rate`, open-loop w/ CO correction) — 3GPP-anchored rate calibration still TODO
- [x] Ensure histogram-based capture avoids coordinated-omission bias (HDR histograms both sides; `--rate` fixed schedule + HDR correction from intended send time)
- [x] Define testbed config (CPU pinning, disable turbo/freq scaling, warm-up discard) — protocol
      in `bench/TESTBED.md` (taskset pinning, performance governor, no-turbo, SMT off, repeats,
      interleaving) + `bench/capture_env.sh` (env capture, flags WSL2); execution on bare-metal TBD
- [~] Make runs scriptable + reproducible (`bench/run_bench.sh` runs all 4 variants; full workload generator still TODO)

## Phase 7 - Experiment campaigns
### 7a. Load sweep (RQ1 latency predictability, RQ3 overhead)
- [~] Run load sweep nominal -> saturation -> overload — driver ready (`bench/campaign.sh`:
      rates x 4 variants, CO-corrected, repeats + interleaving + bootstrap median/CI + plots);
      needs execution on a bare-metal testbed (WSL2 not testbed-grade)
- [~] Collect latency (mean/p50/p90/p99/p99.9/max), throughput, peak RSS + CPU% per offered load
      (getrusage; aggregated with 95% CI by `bench/aggregate.py`) — still add jitter + p99.99
### 7b. Fault-injection study (RQ2 safety)
- [x] Inject C++ defect catalogue (use-after-free, double-free, iterator invalidation,
      data race, unguarded shared mutation) — `faults/cpp/*.cpp`, domain-flavoured
- [x] Rust counterparts, each rejected at compile time (`faults/rust/*.rs`); runner
      `faults/run_faults.sh` builds C++ under ASan+TSan (`-O0`, `setarch -R`) and compiles Rust
- [x] Record per defect: Rust compile-time rejection (E-code) vs C++ ASan/TSan detection —
      `faults/results/taxonomy.{md,csv}` + per-case logs; every defect is compile-error in Rust
- [x] Produce defect-class taxonomy table (filled into thesis §6.2, Table `tab:taxonomy`)
### 7c. FFI migration prototype (RQ4 adoption cost)
- [x] Build a small Rust component behind a C ABI, driven by a C++ host (`ffi/`): seam crate
      `rust-uecm-ffi` (staticlib+cdylib, path-dep on unmodified `rust/`) + hand-written
      `uecm_ffi.h` + `cpp-host/main.cpp`; `ffi/build.sh` builds/links/runs (host PASSes)
- [x] Measure interop cost: 11 C-ABI entry points (~223 LOC Rust + 66 LOC header), 0 `unsafe`
      in core lib (confined to seam), raw crossing ~1 ns/call, op cost = service round-trip
      (not FFI-induced); clippy clean. Findings filled into thesis §6.2 (RQ4 Migration)

## Phase 8 - Analysis & figures
- [x] Tooling: `bench/campaign.sh` (repeats + interleaving + env capture + pinning) ->
      `bench/aggregate.py` (bootstrap median + 95% CI per metric, tidy CSV + auto `tab:latency`
      LaTeX) -> `bench/plot_campaign.py` (median + CI-band latency-vs-load). Pipeline smoke-tested.
- [ ] Execute the campaign on a bare-metal testbed (WSL2 numbers are not testbed-grade)
- [ ] Compute variance + confidence intervals across runs (produced by `aggregate.py` once run)
- [ ] Generate latency-vs-load plots per language (`plot_campaign.py`; needs matplotlib)
- [x] Fill Table (defect taxonomy) — thesis §6.2 `tab:taxonomy` from real fault-injection runs
- [ ] Fill Table (latency percentiles) — paste generated `campaign-*.latency.tex` into `tab:latency`
- [ ] Draft evidence-based migration/language-selection guidelines (RQ4 inputs ready; §7 discussion)

## Phase 9 - Writing (fill placeholders in thesis.tex)
- [x] Build `bibliography.bib` (3gpp38401, 3gpp38300, msrc2019memory, google2022android,
      klabnik2023rust, jung2018rustbelt, astrauskas2020unsafe, tene_hdrhistogram, pereira2017energy)
- [x] Complete "Implementation details" section with concrete data structures/locking
      (§5.4: pinned SplitMix64/FNV hashing, thread-per-shard, std::expected vs Result,
      forced-idiom log, zero-`unsafe` safety story) + new §5.5 Parity verification
- [x] Fill fault-injection results + defect taxonomy from real runs (§6.2, Table `tab:taxonomy`);
      appendix code example now the real UAF C++/Rust pair
- [x] Describe implemented signal/mixed workloads + CO correction in §6.1
- [ ] Populate "Evaluation data" and performance results (Table `tab:latency`) with measured
      load-sweep data (needs testbed hygiene + repeats — Phase 7a/8)
- [ ] Complete Discussion: summary of findings, per-RQ discussion (after performance data)
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
