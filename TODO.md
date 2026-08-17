# Thesis To-Do Plan

**Title:** Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia RAN Control-Plane Systems
**Author:** Ha Vien

This plan is organized into phases. Each phase lists concrete tasks and notes which
research question(s) it serves. The hard ordering constraint: **freeze the shared
specification (Phase 2) before writing any implementation code**, since it is the
primary control against implementation bias.

---

## Next up (as of 9 Aug 2026)

Implementation, analysis, and writing are finished: `Thesis_POC.pdf` builds at 143 pages with zero
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
   - p99.99 and a jitter statistic. **The instrumentation is done** (Aug 2026: `--jitter`,
     `--hist-out`, `bench/pool_hist.py`; see Phase 5). What is not done is *using* it — no
     reported campaign carries the sidecars, so the numbers still cannot be quoted. Run a
     campaign with both flags before the visit rather than discovering on the day that the
     bare-metal data came back with the same hole as the WSL2 data, on the one question the
     visit exists to answer. Costed as item 2 of "Highest-value work still available".
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
- [x] Create `bibliography.bib` with all cited references (97 active entries as of 17 Aug 2026,
      all cited, no orphans; one superseded entry is commented out)
- [x] Verify `Thesis_POC.tex` compiles to PDF end-to-end (161 pages as of 17 Aug 2026, all
      refs/citations resolve; bibliography style is now `IEEEtran`, numbered in citation order)
- [x] Initialize git repository; add `.gitignore` (build artifacts, LaTeX aux files)
- [x] (Optional) Replace reconstructed `UH_DS_MSc.cls` with the official one from Overleaf/Moodle
- [x] Confirm the cover-page programme label ("Master's Programme in Computer Science") is correct
- [x] Decide repo layout: `spec/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/`, `figures/` at
      repo root; `Thesis_POC.tex` + `bibliography.bib` at root. No separate `experiments/` or
      `analysis/` dirs (folded into `bench/`).

### Build instructions
```bash
# Toolchain is TinyTeX; PATH set in ~/.bashrc (open a new terminal or `source ~/.bashrc`)
latexmk -pdf Thesis_POC.tex      # build -> Thesis_POC.pdf
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
- [x] Miri UB/data-race pass (`rust/miri.sh`, nightly + `miri` component). Clean: 14 tests,
      zero undefined-behaviour reports, Stacked Borrows with strict provenance. Confirms rather
      than discovers, since the core has no `unsafe`; its value is symmetry with `cpp/sanitise.sh`
      so neither arm is the one without dynamic-analysis evidence attached.
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
- [x] **Independent oracle + generated vectors** (Aug 2026). The cross-diff proved the two
      implementations agree; it could not distinguish "both correct" from "both wrong the same
      way", and the 223 expectations were hand-derived by the same author who wrote both sides.
      `spec/conformance/model.py` is a third implementation of the spec in Python, validated by
      the §8 KATs and by reproducing all 223 hand-derived expectations before it is allowed to
      generate any. `genvec.py` generates seeded random sequences under five profiles with
      model-derived expectations; `run.sh` gained three phases and a check that the generated
      family reaches every §6.6 code. **~793 000 generated operations, no divergence.**
      Deterministic PRNG, so a failing seed is a permanent regression test.
- [x] **Exhaustive state × operation matrix**, mirrored: `cpp/tests/test_state_matrix.cpp` (439
      checks) and `rust/tests/state_matrix.rs` (9 tests). Every op against every state, asserting
      the exact error, the post-state on success, and no field change on failure; plus the four
      error precedences the spec leaves unordered, `ue_id == 0` on every op, and that `Released`
      is not a resting state. C++ is now 6 test binaries, Rust 25 tests.
- [x] **Dynamic analysis of the parity suite.** `cpp/sanitise.sh` runs every test binary and every
      vector under ASan+UBSan, TSan and UBSan: all clean. This matters for fairness — safe Rust
      carries the property by construction, so without it the C++ arm's equivalent rests on not
      having failed yet. `rust/miri.sh` is the Rust counterpart.
- [x] **Coverage measured, because a sanitiser only reports on code that runs.** 94.6% of C++
      library lines (`cpp/coverage.sh`, gcov) and 98.2% of Rust library lines (`rust/coverage.sh`,
      llvm-cov), with `ShardCore` and `Service` at 100% on both sides. The two are **not**
      comparable with each other; each bounds the claims about its own implementation. Uncovered:
      the C++ `BoundedQueue` template's uninstantiated members and Rust's derive-generated `types.rs`.

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
- [x] Measure interop cost: 11 C-ABI entry points (231 LOC Rust seam + 66 LOC header), 0 `unsafe`
      in core lib (9 `unsafe` fns, all in the seam), raw crossing ~1 ns/call, op cost = service
      round-trip (not FFI-induced); clippy clean. Findings filled into thesis §6.2 (RQ4 Migration).
      The counts were 12/12 until `ffi/build.sh` was taught to count code rather than comments;
      `bench/artefact_facts.py` now regenerates them into the prose.
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
      only `Thesis_POC.tex`. `plain_Thesis_POC.tex` inputs the same `figures/gen_*.tex`, so its prose
      updates while its PDF does not, which is exactly how a companion document goes stale
      without anyone noticing.

## Phase 9 - Writing (fill placeholders in Thesis_POC.tex)
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
The repo now carries four documents besides `Thesis_POC.tex`. Only `Thesis_POC.tex` is the submission
artefact; the rest are unlabelled, which is how two of them drifted without it being visible.
- [x] `plain_Thesis_POC.tex` - plain-language variant (121 pages) for a reader with no 5G
      background. Same argument, same data, same generated macros; builds clean. `Thesis_POC.tex`
      stays the reference version, and its header already says so.
- [ ] `thesis-vi.tex` - Vietnamese translation (75 pages), currently **broken and stale**. All
      113 citations (33 distinct keys) render as `[?]` because bibtex has never been run for this
      variant: there is no `thesis-vi.blg`, and its `.bbl` is a 25 Jul copy predating the
      `IEEEtran` switch. It also does not `\input figures/gen_macros.tex` at all, so its numbers
      are hand-copied and now predate the 15-repeat campaign, the latency decomposition, and the
      corrected RQ3 reading. Decide whether it is a deliverable: if yes, run bibtex and port the
      results across; if no, record that in the notes so it stops reading as unfinished work.
- [ ] `Thesis_v1.tex` - 27-page bullet digest of all ten chapters, useful for a supervisor
      read-through. Its abstract is still the template placeholder, "Abstract to be written last."
- [ ] `Thesis_Plan_v2.tex` - the 5-page plan, reset to a pre-work baseline ("Work has not started
      yet") and dated 9 Aug 2026. If it is handed in later than that date, the date and the status
      table have to move together.
- [ ] Make the title-page fields agree across variants: `Thesis_v1.tex` has
      `\censors{Keijo Heljanko}{}{}` while `Thesis_POC.tex` still has `\censors{}{}{}`. One of the two
      is wrong, and the same programme/study-track labels are duplicated in four files.
- [ ] Housekeeping: `thesis_wbm_full_backup.tex` is a tracked 208 kB leftover still on
      `\bibliographystyle{abbrv}`. Delete it or move it out of the repo root, so the one-word
      difference from `Thesis_v1.tex` cannot be edited by mistake.

## Phase 10 - Finalization
- [ ] **BLOCKER — rewrite the abstract unaided.** The abstract of `Thesis_POC.tex` was drafted
      with model assistance. The UH thesis guide states that a language model may not be used
      when preparing the thesis summary, and in this programme the summary doubles as the
      maturity test, where AI use is never permitted. `ai_statement.tex` already declares the
      abstract as written unaided, so that sentence is false until this is done. Rewrite it in
      your own words from the results, then re-read `ai_statement.tex` end to end and correct
      anything that does not describe what actually happened — it is a statement in your name.
- [x] Declaration of AI use (`ai_statement.tex`), `\input` by both `Thesis_POC.tex` and
      `Thesis_v1.tex` before the bibliography, listed in the ToC. Follows the UH basic
      reporting instruction: scope, purpose, tool and version, how the output was verified,
      what the author took from it, and where responsibility lies. Keep it in step with reality
      if the workflow changes; consider whether `Thesis_Plan_v2.tex` needs the same page.
- [x] Prose de-tic pass (Aug 2026). `.aitells.py` sweeps the draft for language-model
      stylistic fingerprints, the way `.vocab.py` sweeps for hard Latinate words. It found one:
      "rather than" 241 times against 8 for "instead of", repeated inside 58 paragraphs. The
      58 were cut to at most one each (241 -> 162, ~46 per 10k words) using a mix of "instead
      of", ", not", and "and not" so no single replacement becomes the next tic. Direct
      quotations were left alone. Everything else came back clean: no promotional vocabulary,
      no "it is worth noting", sentence-length stdev 14.7 on a mean of 27.6. Re-run
      `.aitells.py Thesis_POC.tex` after any large writing pass.
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

## Phase 11 - Value-adding additions (candidate backlog, 14 Aug 2026)

Everything above treats the bare-metal visit as the gate on the remaining open questions. Three
of those questions are not actually gated on it. They are gated on **changing a variable rather
than measuring the same variable better**, and that can be done on the existing KVM guest.

The distinction matters for scheduling: the testbed is one visit in September, while these are
afternoons. Items 1-4 are the ones that change what the thesis can claim; 5-9 are enrichment;
10-12 are credibility and housekeeping. Nothing here is committed - this is a menu with costs
attached, not a plan.

> **Status, 14 Aug 2026.** Items 1, 3, 4 and 8 were started in this pass and the
> harness work for all four is done and verified. Three of them returned results
> already, and two of those change what the thesis can say. The per-item notes below
> record what landed and what is still open. Items 2, 5-7 and 9-12 are untouched.

### 1. Decompose "language" into language and standard library

**Why.** Two of the campaign's three resolved performance differences are attributed to
standard-library data structures, and neither attribution is measured:

- §7.5.2, the core operation: Rust is $\BudgetCoreRatio\times$ faster, attributed to
  `std::unordered_map` being node-based by standard requirement against Rust's open-addressed
  `HashMap`. The thesis says confirming it "would need the cache-miss counters".
- §7.5.4/§7.5.5, the overload divergence at $\OverloadLoad$~kops/s: the thesis's strongest single
  finding, and `tab:threats` concedes it "is attributed but not localised". The two candidates
  are already in the forced-idiom log (spec §12): a hand-written mutex + two condition variables
  on the C++ side against `std::sync::mpsc::sync_channel` on the Rust side, plus tagged-struct
  dispatch against a typed enum.

Counters would be *observational* evidence for both. Swapping the structure is a *controlled*
experiment, it is strictly stronger, and it does not need a PMU.

**What to build.** Two probe arms, each behind a build flag, each required to stay
conformance-clean:

- C++ `-DUECM_FLAT_MAP=ON`: an open-addressed intra-shard map using the same pinned FNV-1a hash.
  Re-run `bench/latency_budget.sh`. If the $\BudgetCoreRatio\times$ gap collapses, the
  attribution is confirmed by construction.
- Rust `--features mutex-queue`: a `BoundedQueue` mirroring the C++ mutex + two-condvar design,
  replacing `sync_channel` in `Service`. Re-run the overload point only (not the whole sweep).
  If the $\OverloadThrRatio\times$ divergence collapses, the mechanism is localised.

**What must not happen.** These are *additional* arms, not a replacement for the measured pair.
The fairness argument is explicitly "each language as a developer actually finds it", and the
reported comparison has to keep the standard containers on both sides. The probe answers a
different question: how much of the measured difference is the language and how much is the
library that ships with it. Log both in spec §12 as probes.

**Payoff.** Potentially the thesis's most interesting result: that two of its three resolved
differences are library artefacts rather than language artefacts. That *strengthens* RQ3 (the
safety model costs even less than measured) and converts the overload finding from "attributed"
to "localised", closing the residual `tab:threats` names as its most exposed.

- [x] **Both probes built, verified, and run.** `-DUECM_FLAT_MAP=ON`
      (`cpp/include/uecm/flat_map.hpp`) and `--features mutex-queue`
      (`rust/src/mutex_queue.rs`). Both keep byte-for-byte transcript parity with the
      other language on all seven vectors, pass every test binary, and are clippy-clean.
      The Rust probe adds no `unsafe`. The default builds are untouched and still pass
      everything, so the reported pair has not moved.
- [x] **Both came back negative, and that is the result.** On the development host the
      container closes ~15% of the core-operation gap (1.84x to 1.72x) and the queue
      closes none of the overload divergence (1.41x to 1.43x). Numbers, caveats, and the
      reasoning are recorded in `spec/SPECIFICATION.md` §12 under "Attribution probes".
- [x] **Third probe added: C++ preallocated ring queue** (`-DUECM_RING_QUEUE=ON`,
      `cpp/include/uecm/ring_queue.hpp`), because the Rust queue probe could not
      support the conclusion drawn from it. It matched the C++ arm's synchronisation but
      not its buffer: `std::queue` is deque-backed and allocates a node every third push
      (verified at 1008 allocations per 3000 pushes, zero for the ring), while a
      `VecDeque` allocates nothing after warm-up. The contended-primitive microbenchmark
      has the same blind spot from the other side, since its 32-byte job fits sixteen per
      node. The ring probe holds the C++ locking fixed and removes the allocation
      outright: 43.2 to 43.1 kops/s, -0.2%, ratio 1.44x to 1.43x. **The queue is now
      exonerated on both design and allocation**, which is a stronger claim than §12
      previously made on weaker evidence, and dispatch plus the 160-byte request is the
      last untested candidate.
- [ ] **Re-run all three on the measurement host, paired.** These were unpaired runs on
      the WSL2 laptop (10 repeats for the map, 5 for the Rust queue, 7 interleaved for the
      ring) — enough to show direction, not enough to quote. Route the map probe through
      `bench/latency_budget.sh` and both queue probes through `bench/campaign.sh` at the
      overload point, so all get the interleaving and the paired test.
- [ ] **Test the last candidate.** With the container mostly ruled out and the queue
      ruled out entirely, dispatch and request size are what remain. The probe is a C++
      `Request` that carries only the arguments of the operation in flight — a
      `std::variant` of per-operation argument structs, or a discriminated union — which
      would bring the 160 bytes down toward Rust's 96 while keeping the tagged-struct
      dispatch. If the overload divergence closes there, the forced-idiom log has
      explained the study's strongest result end to end.
- [ ] **Then revise the two attributions in the prose.** §7.5.2 explains the
      core-operation gap by `std::unordered_map` being node-based and says confirming it
      "would need the cache-miss counters"; on this evidence that mechanism is a minority
      of the effect, and counters were never the only route to testing it. The overload
      section and the `tab:threats` row for its attribution can now name the queue as
      ruled out rather than as a candidate, which narrows the residual to dispatch and
      request size.
- [ ] **Consider a third arm for the map**, a production flat map
      (`boost::unordered_flat_map` or `absl::flat_hash_map`), since the probe uses plain
      linear probing where `hashbrown` probes sixteen slots at a time with SIMD. That
      bounds how much of the remaining gap is container quality rather than language.

### 2. Re-run the campaign with jitter and HDR sidecars on the host already in hand

**Why.** The instrumentation landed in Aug 2026 (`--jitter`, `--hist-out`,
`bench/pool_hist.py`) but the reported campaign predates it, and `bench/results/` confirms only
the Aug 14 WSL smoke carries `.hist.jsonl`. So jitter and p99.99 are measurable and unmeasured.

Note what this item is **not**, because an earlier version of this note had it wrong. RQ1 no
longer names jitter: as worded in the plan, `Thesis_v1.tex` and `Thesis_POC.tex` it asks about the
median, p99, p99.9 and the maximum, which is exactly what the reported campaign delivers, and
§8.6 says so deliberately rather than confessing a hole. The question and the answer therefore
already match; this re-run is an *upgrade to predictability evidence*, not the discharge of an
unkept promise. Do not re-argue it as one, and do not widen RQ1 to name jitter again unless the
statistic is in hand — narrowing the question to what the campaign delivers was the right call and
should not be undone by a TODO item.

This is filed under "after the bare-metal campaign" at the end of Phase 10, and it does not
belong there. Jitter is an IPDV dispersion statistic, not a far-tail percentile: the reading rule
in §5.5 withholds the tail on a shared host, but it does not withhold a dispersion measure of the
same runs. Pooled p99.99 would at least become *descriptively* reportable with the host's limits
attached, against ~17 observations per run today.

**Cost.** One campaign is ~2.5 h wall clock on the KVM guest (the 1120-run Aug 12 pair started
13:10 and 15:45). Say an afternoon including the `pool_hist.py --verify` pass.

**Watch.** `--jitter` costs ~264 KiB per producer of peak RSS. Absolute RSS from this campaign is
therefore not comparable against the Aug 12 numbers, so either re-run RQ3 from the same campaign
or keep the arms consistent. `NTests` must still read 14; jitter stays descriptive, out of the
Holm family, for the reason §5.5 already gives.

### 3. Read jemalloc's own statistics instead of only `ru_maxrss`

**Why.** RQ3's peak-RSS effect is the campaign's one solid quantitative result and §7.5.4 says
plainly that "the split between arena pre-reservation, per-thread caches, and static footprint is
not resolved here". `tab:threats` gives it the only row in the table whose control column reads
"None available on this host".

That is true of `jeprof`, which needs the testbed. It is not true of jemalloc's `mallctl`
interface, which is compiled in by default and needs no profiling build, no symboliser, and no
PMU. Writing `epoch` and then reading `stats.allocated`, `stats.active`, `stats.metadata`,
`stats.resident`, `stats.mapped` and `stats.retained` decomposes the resident set into live
allocation against arena metadata against retained-but-unmapped - which is exactly the split the
thesis says is unresolved.

It is also the one instrument that measures both languages the same way (`mallctl` in C++,
`tikv-jemalloc-ctl` in Rust, same underlying allocator), which is the choice already made for
`lizard` in the complexity pass and for `jeprof` over heaptrack/dhat in `alloc_profile.sh`.

**Second payoff.** §7.5.4 describes a measurement defect: a handful of runs report a resident set
"some 30 MiB below their variant's median" while being otherwise indistinguishable, and that
bimodality is what keeps peak RSS under jemalloc from clearing Holm. Note that ~30 MiB is close to
the whole measured allocator effect ($\RssAllocDiffLo$-$\RssAllocDiffHi$ MiB). If the low runs
turn out to be runs where fewer arenas were ever touched, `stats.metadata` will show it directly,
and a named cause is worth more than the current "instrumentation work" placeholder.

**Note.** Only the two jemalloc arms can report this. The system-allocator arms emit nulls, never
zeros - the same convention `counters.sh` already uses.

- [x] **Instrumented in both languages and verified.** `cpp/bench/jestats.hpp` (weak
      `mallctl`, no dev header needed) and `je_stats()` in `rust/examples/bench.rs`
      (`tikv-jemalloc-ctl` with its `stats` feature). Both emit a `je` object in the run
      JSON and a line in the human-readable output; both system-allocator arms emit
      nulls. Recorded in spec §12.
- [x] **First reading, and it answers the question.** Under the campaign's own allocator
      configuration (`thp:never,narenas:16`) at 7 shards and 5000 active UEs: C++ holds
      0.5 MB live with 4.1 MB of arena metadata, Rust holds **0.3 MB live** with
      **6.2 MB of metadata**. So the Rust build's larger resident set is not more
      application data — it holds less — it is **2.1 MB more allocator bookkeeping**,
      which sits inside the measured `\RssLangDiffLo`-`\RssLangDiffHi` MiB language
      effect. §7.5.4's "the split ... is not resolved here" is resolvable without the
      testbed.
- [ ] **Re-measure on the KVM host across the campaign**, since the above is one run per
      arm on the laptop. Then check the 30 MiB bimodality against `stats.metadata`: if
      the low-RSS runs are runs where fewer arenas were touched, the measurement defect
      behind peak RSS failing Holm under jemalloc has a named cause.
- [ ] **Name the confound when writing it up.** The C++ arm links the distribution's
      jemalloc while the Rust arm builds 5.3.1 from source, so part of a metadata
      difference is two builds of the allocator, not two programs. Pinning `narenas`
      removes the larger part but not the version difference.
- [ ] **Aggregate it.** `bench/aggregate.py` and `plot_figures.py` do not read the `je`
      fields yet, so nothing reaches a table. Decide whether this becomes a column in
      `tab:resource` or a short subsection of its own.

### 4. Finish RQ2's second half for the two boundary classes

**Why.** RQ2 asks which defects are eliminated at compile time "and **at what stage and cost are
the remaining ones detected**". For the five in-guarantee classes both halves are answered. For
the two boundary classes the catalogue records only that neither language prevents them:
`lock_order_deadlock` is C++ "hung (undetected)" against Rust "compiles and deadlocks", and
`lost_update` is clean under both sanitisers against Rust "compiles, wrong result". The
detection-stage half is simply blank for the two classes that carry the falsifiability of the
whole design.

**Risk, and it is a real one.** The C++ deadlock case is recorded as undetected, but
ThreadSanitizer ships a lock-order-inversion detector that is off by default under the flag the
runner uses: `TSAN_OPTIONS=detect_deadlocks=1` (`second_deadlock_stack=1` for both stacks). If
that flag turns the row from undetected to detected, the current taxonomy understates C++'s
tooling, and an examiner who knows sanitizers is exactly the person who would find it. This needs
checking before anything else in this list. Valgrind's Helgrind is the cross-check.

**The interesting half.** On the Rust side the equivalent question is whether the ecosystem
catches at test time what the compiler does not catch at build time. Loom (exhaustive under the
C11 model) and Shuttle (randomised, PCT) both intercept the standard synchronisation primitives,
and both are aimed precisely at deadlock and lost-update. Running them against the two boundary
cases converts "the defects safe Rust does not prevent are caught later rather than never" from
an argued position into a measured one.

**Why the outcome is worth having either way.** The plausible result is that C++ detects
lock-order inversion with a sanitiser flag while Rust needs a rewrite of the test into a model
checker's primitives - a boundary class where C++ tooling is *ahead*. That is the kind of finding
the two-sided catalogue was designed to be able to produce, and reporting it is what makes the
five in-guarantee results credible.

- [x] **Checked, and the taxonomy is safe: no correction needed.** `taxonomy.csv` is
      byte-identical after the change. But the reason is not the one assumed. The
      detector is *already on by default* in the libtsan g++ 13.3 ships (upstream
      documents it as off, so this varies by runtime), and it still does not fire on the
      injected case.
- [x] **The mechanism is the interesting part, and it is now evidenced.** TSan builds its
      lock-order graph from acquisitions that *succeed*. `deadlock.cpp` blocks on its
      first inversion, so the second edge never completes, the cycle never closes, and
      the detector stays silent — precisely when the bug manifests. A new positive
      control, `faults/cpp/deadlock_control.cpp`, inverts the same two locks without
      blocking and *is* reported, which proves the detector was live. So the honest
      statement for this class is that the tool catches the inversion the program
      survives and misses the one that deadlocks.
- [x] **CORRECTION (Aug 2026): "it still does not fire" was wrong, and the reason it
      looked right is instructive.** The detection is *nondeterministic*, and the
      previous verdict was a single run. Measured over repeats, TSan reports the
      lock-order inversion in **4/12, 6/20 and 7/20 runs** across three trials — roughly
      30% — while the program deadlocks on every one. The mechanism recorded above is
      half right: `deadlock.cpp` **loops**, so on some runs a thread completes an
      inversion without blocking, the cycle closes and the report fires; on others the
      first inversion blocks and only one edge is ever recorded. What was wrong was
      treating one observation of the silent case as the outcome of the class.
      The rate is stable at a 3 s bound and at 25 s, so the report, when it comes, comes
      early. `run_faults.sh` now repeats this case twelve times, records `flaky` as an
      outcome distinct from `detected`, and reports the rate; the thesis table carries a
      footnote and §7.5.6 states it. **Lesson worth keeping: a categorical outcome that
      depends on a schedule needs repeats before it goes in a tracked artefact.**
- [x] **`run_faults.sh` now pins `TSAN_OPTIONS=detect_deadlocks=1:second_deadlock_stack=1`**
      rather than inheriting a default that differs between runtimes, runs the control
      before the catalogue, prints its outcome in the banner and `taxonomy.md`, and warns
      loudly if the control fails — because then "undetected" would carry no information.
- [x] **Written into §7.5.6.** The intermittency, the mechanism, and the positive control
      are all in the results section now, with the rate in the table footnote.
- [x] **Done: the Rust half.** `faults/rust-model-checking/` runs Loom (exhaustive, C11
      model) and Shuttle (PCT, sampled) against both boundary cases; `run_model_checking.sh`
      classifies them and writes `results/model_checking.{md,csv}`.
      **Both checkers report both defects**, and all four controls (consistent lock order;
      read-modify-write in one critical section) come out clean.
      **The cost is the finding, and it is what §4 predicted.** Neither defect program runs
      under either checker as written: each had to be re-imported against the checker's own
      `sync`/`thread` types, and shrunk to model size (lost update from 20 000 iterations
      per thread to one; the deadlock loses its `thread::sleep`). So the Rust answer is
      *detected at test time, after a rewrite*, against a C++ side that needs no rewrite and
      finds one of the two unreliably and the other not at all. The two halves point in
      opposite directions, which is the two-sided result the catalogue was designed to be
      able to produce.
      The crate is separate from `rust/` on purpose: spec §12's dependency-free core is
      load-bearing for RQ4 and should not be weakened for models that never touch the library.

### 5. Three more boundary defect classes — DONE (Aug 2026)

- [x] **All three added; the catalogue is now 5 in-guarantee + 5 boundary.** `leak_cycle`,
      `integer_overflow` and `worker_failure_blast_radius`, with C++ and Rust counterparts,
      taxonomy rows, `tab:defectmap` and `tab:taxonomy` entries, and prose in §4 and §7.5.6.
- [x] **A UBSan column was needed and is now there.** Signed overflow is invisible to both
      ASan and TSan, so without a third sanitiser the overflow class would have been recorded
      as undetected in C++ when it is caught. `run_faults.sh` now runs all three.
- [x] **Two of the three came back with the C++ tooling ahead**, which is the outcome a
      two-sided catalogue exists to be able to produce: LSan reports the C++ reference cycle
      while safe Rust leaks silently, and UBSan reports the C++ overflow while Rust's defined
      wrap says nothing. Do not drop these rows to tidy the narrative.
- [x] **A latent bug in the runner surfaced and is fixed.** `run_cpp_san` classified any
      `rc >= 124` as "hung", which also catches `128 + signal`, so a program aborting by
      design (glibc's double-free check, `std::terminate`) was recorded as a timeout. Now only
      124 and 137 count as hung.
- [x] `integer_overflow` is built with `-O -C overflow-checks=off`, matching the `opt-level = 2`
      profile the thesis compares. Built with the `rustc` defaults it panics, and the table
      would then record a detection the measured configuration does not have.

Original note, kept for the reasoning:

The catalogue holds five in-guarantee classes and two outside. `tab:threats` concedes "seven
programs remain seven programs", and future work already names leaks. Three candidates, each
cheap (two small programs and a taxonomy row) and each a case where **safe Rust does not help**:

- **Leak through a reference cycle** - `Rc`/`RefCell` cycle against `shared_ptr` cycle. Leaks are
  safe in Rust by explicit design; this is the cleanest possible statement of a guarantee
  boundary, and both languages fail identically.
- **Integer overflow in a release build** - `opt-level = 2` leaves `overflow-checks` off, so Rust
  wraps silently where C++ signed overflow is undefined. Defined-but-wrong against
  undefined-and-wrong is a sharper distinction than "Rust is safer", and it maps onto a real
  case: CVE-2026-64467 in `rust_binder` is a `usize`-versus-`u64` stride error
  (`LITERATURE_NOTES.md` §5.1).
- **Panic / exception safety across the shard boundary** - a panicking worker poisons a `Mutex`
  and kills a shard; the C++ analogue throws out of `worker_loop`. Directly relevant to a
  carrier-grade availability argument, and neither language's type system addresses it.

The two `rust_binder` CVEs are already verified in `LITERATURE_NOTES.md` and would let §7.5.6
cite production instances of its own boundary argument rather than only demonstrating it.

### 6. One robustness arm against the compiler, not just the language

`tab:threats` has no row separating the language from its toolchain. Every performance number is
g++ 13.3 / libstdc++ against rustc 1.97, so "C++ is slower on the core operation" is, strictly, a
statement about one implementation of each. A single clang++ / libc++ arm at the representative
load and the overload point would bound that confound. Same for `-O3` / `opt-level = 3` and LTO,
which test whether the matched `-O2` choice is load-bearing. Cheap, and it either adds a
robustness sentence or finds something.

### 7. The RQ4 cost axes that were never measured

RQ4 asks about "effort, FFI interoperability, and risk" and the thesis answers the middle one
well. Three axes are absent and all are near-free to collect:

- **Compile time**, clean and incremental, both languages. The single most cited practical
  objection to Rust adoption, entirely missing, and it matters more to a Nokia RAN build than the
  seam's 192 ns does.
- **Binary size and static footprint**, which belongs next to peak RSS under RQ3.
- **Dependency and `unsafe` supply chain**: `cargo audit`, and `cargo geiger` over the tree. The
  core being dependency-free is currently an assertion in spec §12; it is quantifiable, and it is
  a genuine finding when the usual objection to Rust is transitive-dependency risk.

Vander Stoep's 2025 Android data (`LITERATURE_NOTES.md` §3.1: ~4x lower rollback rate, ~25% less
review time) is the published counterpart to the effort axis and is already verified.

### 8. Report equivalence bounds, not only null results

**Why.** The thesis's most-repeated sentence is that this measurement "cannot tell", and the
register is right. But a non-significant paired test is the *weakest* possible way to say it: it
supports no claim at all, which is why §5.5 has to spend a paragraph on the *p*-floor.

Equivalence testing gives the positive version. The TOST procedure (Schuirmann) tests
$H_0: |\Delta| \ge \delta$ against a pre-specified margin and, when it rejects, licenses
"equivalent within $\pm\delta$" - which is a real claim, and is not the over-claim the register
forbids, because the margin is stated.

**The good version of this.** Rather than argue about the right $\delta$, invert it: report the
**smallest margin at which equivalence holds at 95%**. That is a single number per metric, read
straight off the bootstrap interval already computed, and it turns every null in
`tab:significance` into a bound. "The paired median difference is within $\pm1.6$ µs" says
something; "*p* = 0.7" does not.

**Implementation.** The permutation machinery in `bench/plot_figures.py` already does this: shift
the paired differences by $\pm\delta$ and run the existing one-sided test each way, take the
larger *p*. No new dependency, no distributional assumption, and it composes with the existing
Holm family rather than replacing it.

**Also worth adding while in that file.** A power/repeat-count calculation for the testbed visit.
§5.5 states the *p*-floor at $2/2^n$ but nothing about the *n* needed to detect an effect of a
given size, so the September repeat count is currently guesswork.

- [x] **Implemented and run.** `paired_tost()` (two one-sided permutation tests against a
      margin, reusing the existing enumeration) and `equivalence_bound()` (the tightest
      margin supported, from a 90% bootstrap interval on the paired differences) are in
      `bench/plot_figures.py`. Every row of the family now carries a bound, emitted to
      `figures/tab_equivalence.tex` plus `\NEqvUnresolved`, `\EqvBoundPFifty` and
      `\EqvBoundTailMax`. Every pre-existing macro is unchanged and the build is still
      143 pages with zero errors and zero undefined references.
- [x] **The output makes the case for the testbed better than the current text does.**
      Median latency is equivalent within **±2.0 µs**, a tight positive claim where there
      was only a *p*-value. The tail is bounded at **252-1298 µs** depending on the row —
      against a median of roughly 43 µs. So "cannot tell" now has a number on it: the
      difference could be thirty times the median. That is a far stronger argument for
      the bare-metal campaign than "the intervals overlap".
- [ ] **Adopt it in the document, or stop generating it.** `tab_equivalence.tex` is
      written but nothing `\input`s it — exactly the trap flagged in item 12 below. It
      needs a float and a caption in §7.5 and a sentence in §5.5 explaining why an
      equivalence bound is not the over-claim the register forbids, or it should be
      dropped. This is a claim-level change, so it is the author's call, not the script's.
- [ ] **Still open: the power calculation** for choosing the September repeat count.

### 9. Sensitivity of the ordering to the configuration

`tab:params` fixes shard count, queue capacity, and active-UE population. The external-validity
row concedes "one subsystem, one workload, one machine" and the performance results "do not
travel". A cheap partial answer: does the *ordering* survive a sweep of the knobs? Queue capacity
is the interesting one, because it interacts directly with item 1's overload hypothesis. The
`signal` workload also exists in both benches and has never been run as a campaign, so a second
workload is available for the price of one flag.

### 10. Finish the literature backlog, and add what this list turns up

`LITERATURE_NOTES.md` §10 items 1-7 are applied; **item 8 is not** - the RQ2 and RQ4 enrichment
(§5, §6) and the sharding justification from Pallas and Aquifer (§7.5). It is marked a judgement
call, and items 1 and 4 above change that calculation: if Loom and Shuttle are run, the
verification-landscape sources in §5.2 stop being enrichment and become the related work for a
result. Two additions of the same kind not yet in that file: Schuirmann for TOST (item 8), and
the Loom/Shuttle tooling itself (item 4).

### 11. A citable, archived reproduction package

The repository is public and `bench/refresh_thesis.sh` regenerates every quoted number, which is
already better than most. What is missing is a fixed point: a tagged release archived with a DOI,
plus a `REPRODUCE.md` giving the exact command sequence and expected runtimes per artefact.
Criteria 3 and 4 both reward it, it takes an afternoon, and it also fixes what the thesis means
by "the artefacts" once the repository keeps moving after submission.

### 12. Housekeeping found while surveying

- `bench/plot_figures.py` generates `fig_tail_percentiles.pdf`, `fig_resources.pdf`,
  `fig_taxonomy.pdf` and `fig_ffi_cost.pdf`, and `thesis.tex` includes none of them. Either place
  them or stop generating them; a generated figure nobody reads is a maintenance trap.
- Several `diagrams/pdf/*` are likewise unused where TikZ or a table took over the role.
- `AGENT.md` and `ASSESSMENT.md` both still list `\censors{}{}{}` as the title-page item, but
  `thesis.tex` now uses `\supervisors` with an unset `\examiners`. Same task, wrong command name
  in two places.

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
  is "based heavily on the UH_DS_MSc.cls"). It defines every command Thesis_POC.tex uses
  (`\prof`, `\censors`, `\mytableofcontents`, `\mynomenclature`, `\myappendixtitle`,
  `\depositeplace`, `\additionalinformation`, `\quoting`, `\keywords`, `\classification`).
  The genuine class lives behind the UH Overleaf/Moodle login; swap it in for final submission.
- `\mynomenclature` is a no-op here (the `nomencl` package clashes with hyperref/report in
  this class family and is disabled upstream too); it just switches page numbering to arabic.
- Cover/abstract programme is set to "Master's Programme in Computer Science" (English),
  inferred from `\additionalinformation{Software study track}`. Verify this is right.
- Logo `UH-logo.png` is the official UH logo taken from the UH CS thesis-template repo.
