# Thesis To-Do Plan

**Title:** Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia RAN Control-Plane Systems
**Author:** Ha Vien

This plan is organized into phases. Each phase lists concrete tasks and notes which
research question(s) it serves. The hard ordering constraint: **freeze the shared
specification (Phase 2) before writing any implementation code**, since it is the
primary control against implementation bias.

---

## Next up (as of 9 Aug 2026)

Implementation, analysis, and writing are finished: `thesis.pdf` builds at 143 pages with zero
LaTeX errors and zero undefined references or citations, and every quoted number regenerates
from the raw logs. What is left is one measurement, one review round, and housekeeping. The plan
document (`Thesis_Plan_v2.pdf`, dated 9 Aug 2026) puts measurement in September, RQ1/RQ3
resolution in October, and submission in November, so the ordering below is what that timeline
needs.

1. **Send the spec and the plan to the supervisors** (Phase 1, Phase 2). This needs no repo work
   and everything gated on `spec-v1.0` is queued behind it. Of the three Phase 1 items, "what can
   be published" is the one that can force rework rather than just a signature: the repository is
   already public (`github.com/VienThanh12/Master-Thesis`, compiled PDF included), so hearing a
   Nokia objection now costs far less than hearing it in November.
2. **Line up the bare-metal host** (Phase 8). Still the only substantive blocker, and now a
   narrow one: §7.5.2 showed the operation itself to be 0.04% of the end-to-end cost, so the
   testbed buys the tail and the overload cliff specifically, not a better median comparison.
   `bench/setup_testbed.sh` provisions a fresh box and prints a GREEN/RED readiness check. The
   fallbacks named in the plan are a cloud bare-metal instance or a Nokia lab host.
3. **Do the harness work before that visit, not during it** (Phase 7a). Three things are in this
   category, and all three are cheap now and expensive later:
   - p99.99 and a jitter statistic. Both benches emit only fixed percentiles and never persist
     the HDR histogram, so neither can be recovered from a finished campaign. Left alone, the
     bare-metal data comes back with the same hole as the WSL2 data, on the one question the
     visit exists to answer.
   - `perf` counters. Two results are currently significant but unexplained (peak RSS) or resting
     on a plausibility argument (the 1.9x operation gap, attributed to `std::unordered_map` being
     node-based against Rust's open-addressed `HashMap`).
   - An allocation profile per variant, to attribute the peak-RSS difference to allocation sites.
   The last two do not work under WSL2 at all, so the visit is the only chance to collect them.
4. **Decide what the companion documents are for, and fix the broken one** (new Phase 9b).
   `thesis-vi.pdf` currently renders 113 citations as `[?]` and predates the 15-repeat campaign.
5. **Rebuild the slide deck against the current results** (Phase 10). Three of its slides now
   contradict the thesis.
6. **Then, once the data lands:** `bench/refresh_thesis.sh`, reread the six claims listed under
   "After the bare-metal campaign" at the end of this file, and start the proofread round. The two
   title-page items are not on this path and are not yours to schedule: the examiners come from
   the faculty, and the official `UH_DS_MSc.cls` from the UH Overleaf/Moodle.

---

## Phase 0 - Environment & repository setup
- [x] Install LaTeX toolchain (TinyTeX in ~/.TinyTeX; `pdflatex`, `bibtex`, `latexmk` on PATH)
- [x] Obtain the `UH_DS_MSc.cls` class file (local reconstruction from UH_*_MSc family; see note)
- [x] Create `bibliography.bib` with all cited references (65 entries as of Aug 2026)
- [x] Verify `thesis.tex` compiles to PDF end-to-end (143 pages as of Aug 2026, all
      refs/citations resolve; bibliography style is now `IEEEtran`, numbered in citation order)
- [x] Initialize git repository; add `.gitignore` (build artifacts, LaTeX aux files)
- [ ] (Optional) Replace reconstructed `UH_DS_MSc.cls` with the official one from Overleaf/Moodle
- [ ] Confirm the cover-page programme label ("Master's Programme in Computer Science") is correct
- [x] Decide repo layout: `spec/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/`, `figures/` at
      repo root; `thesis.tex` + `bibliography.bib` at root. No separate `experiments/` or
      `analysis/` dirs (folded into `bench/`).

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
- [x] Expand the conformance suite to 7 vectors / 223 checked ops: `states.vec` (full §5.2
      transition matrix + §6.1 no-mutation-on-error), `errors.vec` (every §6.6 code on every
      op, `ue_id==0` on all ten ops, payload boundary, error precedence), `capacity.vec`
      (per-shard `CapacityExceeded`), `routing.vec` (§10.1 I1), `shards13.vec`
      (non-power-of-two shard count). Both impls pass all seven and agree byte-for-byte.
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
- [x] Run against shared parity-test contract (spec §11): `conformance_runner` passes all 7 vectors

## Phase 4 - Rust implementation
- [x] Scaffold Cargo project (stable toolchain 1.97; release opt-level=2 to match C++ -O2)
- [x] Implement pinned types, hash/shard functions (LE-byte FNV BuildHasher == fnv1a_64), error model (spec §4,§6,§8)
- [x] Implement ShardCore: sharded context store + UE state machine per spec (single-threaded)
- [x] Implement threaded service: thread-per-shard + bounded `sync_channel` backpressure + typed one-shot completions (spec §7)
- [x] Implement signaling/message handling + concurrent lookup at service level
- [x] Record location + justification of any `unsafe` blocks (result: **zero `unsafe`**, safe Rust is data-race-free by construction)
- [x] Unit/conformance tests green (16/16 across `conformance.rs`, `invariants.rs`,
      `concurrency.rs`); `cargo clippy --all-targets -D warnings` clean; `cargo fmt` applied
- [x] Wire jemalloc allocator (`--features jemalloc`, `tikv-jemallocator` global allocator) + HdrHistogram (`hdrhistogram` crate) in `rust/examples/bench.rs`
- [ ] (Optional) Miri UB/data-race pass once a nightly toolchain is available
- [x] Run against shared parity-test contract (spec §11): `conformance_runner` passes all 7 vectors; transcript matches C++ byte-for-byte

## Phase 5 - Parity verification
- [x] Confirm both implementations pass identical functional parity tests (shared
      `conformance_runner`; op-for-op transcript match on all 7 vectors, 223 ops)
- [x] Diff behaviour on edge cases; document forced-idiom deviations (deviations logged in
      spec §12). Adversarial vectors added for the full state matrix, the whole error model,
      per-shard capacity, cross-shard isolation, and a non-power-of-two shard count. **No
      divergence found**: every expectation was derived from the spec by hand and both
      implementations matched it on the first run, including the error-precedence cases
      §6 leaves unordered (now pinned so they cannot drift).
- [x] Mirrored per-language suites for the properties a sequential `.vec` transcript cannot
      express: `test_invariants`/`invariants.rs` (§6.1 no mutation on error, §10.3/§11.2
      activity-sequence discipline, `security_key`/`rrc_transaction_id`/per-DRB round-trip,
      §10.1 I1 and I4) and `test_concurrency`/`concurrency.rs` (§7 blocking backpressure at
      `queue_capacity=1`, §10.2 O1 FIFO per shard, concurrent lookup consistency, §7.1
      lifecycle + shard-count edge cases). C++ 5 binaries / ~13.7k checks, Rust 16 tests.
- [x] Known-answer tests for the pinned §8 functions on both sides. The previous tests only
      checked self-consistency, so an implementation that was internally consistent but not
      actually SplitMix64/FNV-1a would have passed. Verified by mutation: replacing the
      specified `x mod n_shards` with `x & (n_shards-1)` passes `basic.vec`, `shards.vec`,
      `test_shard_core` and `test_service` unchanged, and is caught only by the new
      `shards13.vec` and the new KAT.

## Phase 6 - Benchmarking framework & workload generator
- [x] Build synthetic workload generator (UE lifecycle: attach, signaling, bearer setup, handover begin/complete/abort, release), pinned deterministic model, identical op-stream in C++/Rust (`--workload mixed`)
- [x] Parameterize by number of active UEs (`--active-ues`) and target event rate (`--rate`, open-loop w/ CO correction), 3GPP-anchored rate calibration still TODO
- [x] Ensure histogram-based capture avoids coordinated-omission bias (HDR histograms both sides; `--rate` fixed schedule + HDR correction from intended send time)
- [x] Define testbed config (CPU pinning, disable turbo/freq scaling, warm-up discard), protocol
      in `bench/TESTBED.md` (taskset pinning, performance governor, no-turbo, SMT off, repeats,
      interleaving) + `bench/capture_env.sh` (env capture, flags WSL2); execution on bare-metal TBD
- [~] Make runs scriptable + reproducible (`bench/run_bench.sh` + `bench/campaign.sh` +
      `bench/refresh_thesis.sh` work end-to-end; 3GPP-anchored rate calibration still TODO)

## Phase 7 - Experiment campaigns
### 7a. Load sweep (RQ1 latency predictability, RQ3 overhead)
- [~] Run load sweep nominal -> saturation -> overload: driver ready (`bench/campaign.sh`:
      rates x 4 variants, CO-corrected, repeats + interleaving + bootstrap median/CI + plots).
      15-repeat WSL2 campaign **done** (480 runs, `campaign-20260807-122430.jsonl`,
      `campaign-15rep.log`), and it is what every thesis table currently reports. WSL2 is not
      testbed-grade, so definitive RQ1/RQ3 numbers still need bare-metal execution.
- [x] Collect latency (mean/p50/p90/p99/p99.9/max), throughput, peak RSS + CPU% per offered load
      (getrusage; aggregated with 95% CI by `bench/aggregate.py`). **Jitter + p99.99 done**
      (Aug 2026), before the testbed run rather than after. Both benches now emit
      `lat_ns: p25/p50/p75/p90/p99/p999/p9999/max/mean/stdev`, an IPDV jitter histogram under
      `--jitter` (per-producer consecutive-latency differences, RFC 3393 sense), and the full HDR
      buckets to a `campaign-<stamp>.hist.jsonl` sidecar under `--hist-out`; `campaign.sh` passes
      both by default. `bench/pool_hist.py` pools repeats for a decision-grade far tail (a single
      run's p99.99 rests on ~17 observations; 20 pooled repeats give ~340) and its `--verify`
      mode proves the persistence is lossless by recomputing every printed percentile from the
      buckets. Three cross-language conventions were pinned in the same pass, all of which were
      latent divergences: quantiles rather than percentiles as the primitive (`99.9/100` and the
      literal `0.999` are different doubles, and `0.999 * 168000` is exactly an integer), a
      bucket-aligned `max` on both sides (the crate returns `highest_equivalent`, the C++ port
      returned the exact sample), and `stdev` computed by the crate's own convention.
      Note `--jitter` costs ~264 KiB per producer of peak RSS, equally in both languages and
      uniform across a campaign's arms, so within-campaign RQ3 comparisons are unaffected but
      absolute RSS is not comparable against a campaign run without it (`--no-jitter`).
- [x] Decompose the end-to-end latency into the operation's own work and the cross-thread
      handoff, in both languages, at the sweep's shard count and population
      (`bench/latency_budget.sh` -> `tab_budget.tex`, `\Budget*` macros). Without this a bound
      on the paired median difference cannot be read: "a fifth of the median" is a weak bound
      if the median is mostly handoff, and the sweep alone cannot say whether it is.
      `ShardCore` gives the work with no queue in the path; `Service` gives work + handoff.
- [~] Hardware counters: **`bench/counters.sh` written** (Aug 2026), to be *run* on the testbed
      visit. Wraps `perf stat` (cycles, instructions, cache-references, cache-misses,
      LLC-load-misses) around both the sweep bench and the `latency_budget` binaries, and writes
      `counters-<stamp>.jsonl`. The `op` scope is the one that matters for the map claim: the
      end-to-end path is ~99.96% handoff, so counters over the sweep describe the queue rather
      than the operation. Refuses to run rather than reporting zeros where there is no PMU (WSL2
      exposes none) and records uncountable events as `null`, never `0`. The `perf` CSV parsing
      lives in `bench/parse_perf.py` with `--self-test`, so it is known-good before the visit
      instead of being debugged during it; `--software` exercises the whole path on events that
      need no PMU.
- [ ] Run `bench/counters.sh` on the testbed. Two live claims need it: the peak-RSS effect is
      significant but unexplained, and the operation-level gap rests on the
      node-based-`unordered_map` argument rather than on a measurement.
- [~] Allocation profile per variant: **`bench/alloc_profile.sh` written** (Aug 2026), to be *run*
      on the testbed visit. Uses jemalloc's own `prof` on **both** jemalloc arms rather than
      heaptrack for C++ and dhat for Rust, so the two sides are measured by one instrument with
      one notion of a call site (the same choice already made for the complexity proxies, where
      `lizard` measures both languages); a mismatched pair could not be differenced, which is the
      whole question. Needs the new opt-in `jemalloc-prof` Cargo feature. Prof support is detected
      functionally, by checking a dump actually lands, since a build without `--enable-prof` says
      `Invalid conf pair` while a syntax error says `Malformed conf string` and matching on
      wording is how a false positive survives to the testbed. Verified on this host: both arms
      dump, only `jeprof` is missing, and `--raw-ok` collects dumps plus their binaries for later
      symbolisation so a one-off visit is never wasted. Parsing is in `bench/parse_jeprof.py` with
      `--self-test`.
- [ ] Run `bench/alloc_profile.sh` on the testbed to attribute the 2.1-2.5 MiB peak-RSS
      difference to allocation sites. §7.5.4 already establishes the difference is fixed rather
      than per-context (the `UeContext` layout accounts for ~40 kB at 5000 active UEs, three
      orders of magnitude short of the gap), so the profile is what turns "unexplained" into a
      cause. Install `jeprof` first (`--check` reports readiness).
### 7b. Fault-injection study (RQ2 safety)
- [x] Inject C++ defect catalogue (use-after-free, double-free, iterator invalidation,
      data race, unguarded shared mutation), `faults/cpp/*.cpp`, domain-flavoured
- [x] Rust counterparts, each rejected at compile time (`faults/rust/*.rs`); runner
      `faults/run_faults.sh` builds C++ under ASan+TSan (`-O0`, `setarch -R`) and compiles Rust
- [x] Record per defect: Rust compile-time rejection (E-code) vs C++ ASan/TSan detection,
      `faults/results/taxonomy.{md,csv}` + per-case logs; every defect is compile-error in Rust
- [x] Produce defect-class taxonomy table (filled into thesis §6.2, Table `tab:taxonomy`)
### 7c. FFI migration prototype (RQ4 adoption cost)
- [x] Build a small Rust component behind a C ABI, driven by a C++ host (`ffi/`): seam crate
      `rust-uecm-ffi` (staticlib+cdylib, path-dep on unmodified `rust/`) + hand-written
      `uecm_ffi.h` + `cpp-host/main.cpp`; `ffi/build.sh` builds/links/runs (host PASSes)
- [x] Measure interop cost: 12 C-ABI entry points (~231 LOC Rust seam + 66 LOC header), 0 `unsafe`
      in core lib (confined to seam), raw crossing ~1 ns/call, op cost = service round-trip
      (not FFI-induced); clippy clean. Findings filled into thesis §6.2 (RQ4 Migration)
- [x] Replace the indirect argument for "no measurable per-call tax" with the direct A/B.
      An empty crossing measured against a full round-trip bounds the crossing but is not the
      same experiment; `ffi/build.sh` now also runs the *same* signaling op natively (same
      shard count, same loop shape, `rust/examples/latency_budget.rs --shards 4`) so the
      difference is the seam's actual per-operation cost. Lands in `metrics.json` as
      `op_roundtrip_native_ns` and in `tab_ffi.tex`.

## Phase 8 - Analysis & figures
- [x] Tooling: `bench/campaign.sh` (repeats + interleaving + env capture + pinning) ->
      `bench/aggregate.py` (bootstrap median + 95% CI per metric, tidy CSV + auto `tab:latency`
      LaTeX) -> `bench/plot_campaign.py` (median + CI-band latency-vs-load). Pipeline smoke-tested.
- [ ] **Execute the campaign on a bare-metal testbed** (WSL2 numbers are not testbed-grade),
      provision with `bench/setup_testbed.sh` (toolchain + CPU hygiene + GREEN/RED readiness check).
      Keep **15+ repeats**: the exact paired test cannot return p < 2/2^n, and at 7 repeats the
      corrected floor sat above 0.05 so no result could survive Holm however large the effect.
      At 15 the floor is 0.00061 and three results now clear it. Thesis tables currently use the
      480-run 15-repeat WSL2 campaign (`campaign-20260807-122430.jsonl`).
- [x] Compute variance + confidence intervals across runs (`plot_figures.py`; reported as explicit
      asymmetric [lo, hi] bootstrap intervals, not symmetric half-widths, which at these
      dispersions implied negative latencies)
- [x] Formal significance testing: exact two-sided **paired permutation test** on the interleaved
      repeats (language compared with allocator held fixed), Holm-corrected across the family.
      Emits `figures/tab_significance.tex` + macros. Enumerates all 2^n sign assignments up to
      18 repeats, Monte Carlo above that.
- [x] Drop achieved throughput from the tested family (12 tests -> 10). At a below-saturation
      operating point it is pinned to the offered load by construction, so the comparison
      re-measures the operating point rather than the code, while still consuming two slots of
      the Holm budget and making the correction harsher on the tests that can resolve. It stays
      in `tab_resource.tex`, where confirming the load is sustained is its actual job.
- [x] Pre-commit the rule for reading an interval against a p-value, in §5.5 rather than after
      the results. Pairing cancels what an interleaved block shared, not interference landing on
      one run of a pair; so it rescues run-level and central statistics (peak RSS, CPU, p50) and
      not high percentiles, which are computed from exactly the disturbed operations.
      `tab_significance.tex` is now blocked by that criterion, and `plot_figures.py` emits
      `\NExclZero` / `\NTailExclZero` / `\TailExclZeroRows` so the text names every interval that
      excludes zero instead of only the ones that suit the argument.
- [x] Generate latency-vs-load plots per language (`plot_figures.py`)
- [x] Fill Table (defect taxonomy): thesis §6.2 `tab:taxonomy` from real fault-injection runs
- [x] Fill Table (latency percentiles): generated into `figures/tab_latency.tex`
- [x] Software-quality proxies: `bench/complexity.py` measures LOC + cyclomatic complexity with
      `lizard` over both cores (one tool, both languages) -> `tab_complexity.tex`. Result: Rust is
      19% longer but 15% lower in total complexity; C++ `worker_loop` is CCN 13 vs Rust's max of 6.
- [x] Draft evidence-based migration/language-selection guidelines (RQ4 inputs ready; §8.4)
- [ ] Extend `bench/refresh_thesis.sh` to rebuild every document that quotes the numbers, not
      only `thesis.tex`. `plain_thesis.tex` inputs the same `figures/gen_*.tex`, so its prose
      updates while its PDF does not, which is exactly how a companion document goes stale
      without anyone noticing.

## Phase 9 - Writing (fill placeholders in thesis.tex)
- [x] Build `bibliography.bib` (3gpp38401, 3gpp38300, msrc2019memory, google2022android,
      klabnik2023rust, jung2018rustbelt, astrauskas2020unsafe, tene_hdrhistogram, pereira2017energy)
- [x] Complete "Implementation details" section with concrete data structures/locking
      (§5.4: pinned SplitMix64/FNV hashing, thread-per-shard, std::expected vs Result,
      forced-idiom log, zero-`unsafe` safety story) + new §5.5 Parity verification
- [x] Fill fault-injection results + defect taxonomy from real runs (§6.2, Table `tab:taxonomy`);
      appendix code example now the real UAF C++/Rust pair
- [x] Describe implemented signal/mixed workloads + CO correction in §6.1
- [x] Populate "Evaluation data" and performance results (Table `tab:latency`) with measured
      load-sweep data (labelled preliminary until the bare-metal campaign, Phase 7a/8)
- [x] Complete Discussion: summary of findings, per-RQ discussion
- [x] Finalize conclusion + future work
- [x] Polish abstract to reflect actual (not expected) results.
      NOTE: the abstract box is full to the line. Any addition pushes the CCS block into the
      Keywords row; check page 3 visually after editing it.

## Phase 9b - Companion documents (assign a status, then keep them in step)
The repo now carries four documents besides `thesis.tex`. Only `thesis.tex` is the submission
artefact; the rest are unlabelled, which is how two of them drifted without it being visible.
- [x] `plain_thesis.tex` - plain-language variant (121 pages) for a reader with no 5G
      background. Same argument, same data, same generated macros; builds clean. `thesis.tex`
      stays the reference version, and its header already says so.
- [ ] `thesis-vi.tex` - Vietnamese translation (75 pages), currently **broken and stale**. All
      113 citations (33 distinct keys) render as `[?]` because bibtex has never been run for this
      variant: there is no `thesis-vi.blg`, and its `.bbl` is a 25 Jul copy predating the
      `IEEEtran` switch. It also does not `\input figures/gen_macros.tex` at all, so its numbers
      are hand-copied and now predate the 15-repeat campaign, the latency decomposition, and the
      corrected RQ3 reading. Decide whether it is a deliverable: if yes, run bibtex and port the
      results across; if no, record that in the notes so it stops reading as unfinished work.
- [ ] `thesis_wbm.tex` - 27-page bullet digest of all ten chapters, useful for a supervisor
      read-through. Its abstract is still the template placeholder, "Abstract to be written last."
- [ ] `Thesis_Plan_v2.tex` - the 5-page plan, reset to a pre-work baseline ("Work has not started
      yet") and dated 9 Aug 2026. If it is handed in later than that date, the date and the status
      table have to move together.
- [ ] Make the title-page fields agree across variants: `thesis_wbm.tex` has
      `\censors{Keijo Heljanko}{}{}` while `thesis.tex` still has `\censors{}{}{}`. One of the two
      is wrong, and the same programme/study-track labels are duplicated in four files.
- [ ] Housekeeping: `thesis_wbm_full_backup.tex` is a tracked 208 kB leftover still on
      `\bibliographystyle{abbrv}`. Delete it or move it out of the repo root, so the one-word
      difference from `thesis_wbm.tex` cannot be edited by mistake.

## Phase 10 - Finalization
- [ ] Full proofread + supervisor review round(s)
- [x] Verify all cross-references, citations, tables, figures resolve (0 errors, 0 undefined)
- [x] Reproducibility check: `bench/refresh_thesis.sh` regenerates every figure, table, and
      quoted number from the raw logs and rebuilds the PDF in one command
- [ ] Fill `\censors{}{}{}` on the title page once the faculty assigns examiners
- [ ] Swap the reconstructed `UH_DS_MSc.cls` for the official one (see Notes)
- [x] Rebuild the colloquium deck (`build_deck.py` -> `Rust_vs_Cpp_Nokia_RAN_thesis.pptx`).
      Done Aug 2026, 28 slides. Every measured number is now read at build time from
      `figures/gen_macros.tex`, `figures/gen_complexity.tex`, the `figures/tab_*.tex` bodies the
      thesis itself `\input`s, `faults/results/taxonomy.csv`, and the newest
      `bench/results/env-*.txt`; a macro the deck asks for and the data does not provide is a hard
      error rather than a stale literal. `bench/refresh_thesis.sh` now rebuilds the deck, so the
      drift cannot recur. The three contradicting slides are corrected (RQ3 now reports the peak-RSS
      language effect against the larger allocator effect; RQ1 is split into median, decomposition,
      and overload rather than "diverge only in the far tail"), and five slides were added: the
      measurement host and what it cannot carry, the pre-committed statistical treatment, the
      latency decomposition, the overload divergence, and the contended-primitive mechanism test.
      `build_deck.py` also gates its own layout against the template's content band.
- [ ] Final PDF + submission

### After the bare-metal campaign, re-check these
The prose is generated from the data, so most of it updates itself. These are the claims that
are currently shaped by the **15-repeat WSL2** dataset and should be reread once bare-metal
numbers land:
- §7.5.1 "the tail is not yet measurable" -- becomes a real finding or a bounded null result.
  This is the only remaining blocker. Note §7.5.2 now shows the end-to-end number to be
  0.04% operation and the rest handoff, so bare metal will sharpen the *tail* question without
  making the end-to-end sweep any more informative about the language.
- §7.5.4/§8.2 the peak-RSS language effect: 2.1-2.5 MiB, Holm p = 0.00061, same sign under
  both allocators. Confirm it reproduces; it is now the campaign's one solid quantitative
  result and the prose leans on it.
- §7.5.4 the CPU non-result. Currently clears Holm under the system allocator (+27.4 pp) and
  reverses under jemalloc, so it is reported as unresolved. On a quiet host it should either
  resolve consistently or vanish; either outcome needs a sentence.
- §7.5.2 the core-operation gap (Rust 10.0 ns vs C++ 19.0 ns, p = 0.00024). Re-run
  `bench/latency_budget.sh` on the testbed. If the ratio holds, consider isolating the
  attribution with cache-miss counters rather than leaving it as the most likely explanation.
- Table 8.1 evidence-status column, and the RQ1/RQ3 "preliminary" labels throughout.
- H1 in §8.3, currently recorded as supported end to end, untested in the tail, and ambiguous
  in framing.
- **p99.99 and jitter become reportable for the first time.** The instrumentation landed in
  Aug 2026 but the campaign the thesis reports predates it, so §8.6 currently states plainly
  that RQ1 is answered with p99/p99.9/max and that these two metrics are instrumented but not
  yet reported. Once the new campaign lands:
  - `tab:latency` gains a p99.99 column with **no thesis edit required** -- its column
    specification and header are generated (`\LatencyCols`, `\LatencyHead`) precisely so the
    preamble cannot fall out of step with the `\input` body. Check the table still fits the
    text width at six columns.
  - `figures/tab_jitter.tex` starts being written; it needs a float and a caption in §7.5,
    plus prose using `\JitterRange`, `\JitterSpread`, `\JitterPNineNineRange`,
    `\JitterVsMedian`, `\FarTailSpread`, `\FarTailRange`, `\IqrSpread`.
  - Update the §8.6 paragraph that currently says these are not yet reported, and the
    §5.5 note explaining why they stay descriptive rather than joining the tested family.
  - Run `python3 bench/pool_hist.py <hist.jsonl> --verify <jsonl>` before relying on any of
    it, and quote the **pooled** p99.99 for the far tail while keeping the per-repeat figures
    for anything paired. `NTests` must still read 14.

---

### Notes / open questions
- Timeline: writing and implementation complete; remaining work is spec freeze, bare-metal
  campaign, supervisor review, and submission. `Thesis_Plan_v2.pdf` schedules these as
  September (measure), October (resolve RQ1/RQ3), November (colloquium + submit).
- Current artefact status (verified Aug 2026): spec + C++/Rust implementations + conformance
  suite + bench/fault/ffi harnesses + generated figures/tables + 143-page thesis PDF. All green
  on `spec/conformance/run.sh`, `ctest`, `cargo test`, `faults/run_faults.sh`, `ffi/build.sh`.
- **Remaining critical path:** (1) supervisor review → spec v1.0 freeze, (2) bare-metal campaign
  including counters + allocation profile, (3) `bench/refresh_thesis.sh` with definitive data,
  (4) final proofread + submission.
- Three overfull boxes remain in `thesis.log`; all three are the known abstract-page overflow,
  and they are present in pre-refinement builds too. Nothing else in the build is dirty.
- Two load-bearing citations are still arXiv preprints rather than peer-reviewed work (Bugden and
  Alahmar for "Rust matches C/C++ on performance", Zhang et al. for deadlock detection). Optional,
  but replacing either removes the last soft spot in the bibliography. See `ASSESSMENT.md`
  criterion 2.
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
