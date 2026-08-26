# Thesis To-Do Plan

**Title:** Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia RAN Control-Plane Systems
**Author:** Ha Vien

This plan is organized into phases. Each phase lists concrete tasks and notes which
research question(s) it serves. The hard ordering constraint: **freeze the shared
specification (Phase 2) before writing any implementation code**, since it is the
primary control against implementation bias.

---

## Next up (as of 26 Aug 2026, after the bare-metal campaign)

Implementation, analysis, and writing are finished: the thesis builds at **103 declared pages plus
6 appendix pages, 117 physical** (26 Aug 2026) with zero LaTeX errors, zero undefined references or
citations and zero overfull boxes, and every quoted number regenerates from the raw logs. The plan
document (`Thesis_Plan_v2.pdf`, dated 9 Aug 2026) puts measurement in September, RQ1/RQ3
resolution in October, and submission in November. **Measurement is now ahead of that schedule and
the writing is behind it**: the bare-metal campaign ran on 26 August and the eleventh grading pass
found fourteen places in the document that still describe a study with less evidence than it has.

**The shape of the remaining work has changed.** It used to be one measurement plus review. It is
now three hours of sync editing, two half-days of analysis on data already on disk, one two-hour
repeat measurement, and the abstract.

1. **Send the spec and the plan to the supervisors** (Phase 1, Phase 2). This needs no repo work
   and everything gated on `spec-v1.0` is queued behind it. Of the three Phase 1 items, "what can
   be published" is the one that can force rework rather than just a signature: the repository is
   already public (`github.com/VienThanh12/Master-Thesis`, compiled PDF included), so hearing a
   Nokia objection now costs far less than hearing it in November.
2. **DONE 26 Aug 2026. Two campaigns, and what each one settled.** A bare-metal visit ran on a
   rented Cherry Servers AMD EPYC 7443P (24 cores, one socket, SMT off, governor `performance`,
   `virtualisation: none`, **0 of 60 sampling intervals showed any steal** on the 16 pinned cores).
   It wrote two sweeps, kept apart on purpose because they answer different questions:

   | Campaign | Offered load | What it settled |
   | --- | --- | --- |
   | `campaign-20260826-102047` | 8 to 128 kops/s | The far tail, the paired median, peak RSS |
   | `campaign-20260826-124950` | 128 to 640 kops/s | The knee, the overload divergence, the metastable point |

   Both are 480 runs (8 levels x 15 repeats x 4 variants). Macros in `figures/gen_baremetal.tex`
   via `bench/baremetal_facts.py`, which `refresh_thesis.sh` calls. Reported in §`sec:baremetal`.

   **What it returned**, all of it verified against the raw logs by the eleventh grading pass:
   - **The far tail resolves and favours Rust.** Pooled p99.99 over 32 to 96 kops/s is 147 to
     228 µs for the two C++ variants and 88 to 115 µs for the two Rust variants, and the ranges do
     not meet. Below 32 kops/s the four are indistinguishable. Pooling gives 360 000 to 5 761 198
     operations per group against about seventeen for a single run's p99.99.
   - **The instrument inverted, which is the reason the trip was worth taking.** The widest 95 %
     interval on one variant's p99 is 2.8 µs against a between-variant range of 3.6 µs. On the
     guest those numbers are 1480 and 293.
   - **The median difference sharpens.** 14 of 16 load-and-allocator points clear Holm, Rust lower
     by 0.5 to 1.1 µs on a 73.6 µs operation.
   - **Peak RSS reproduces in direction**, 16 of 16 significant, language effect 0.7 to 1.8 MiB,
     allocator effect 1.9 to 3.2 MiB. **But see the new item 7 below: the order-of-magnitude gap
     between the two effects did not survive the change of host.**
   - **The overload divergence reproduces on another vendor's silicon.** Tracking to 448 kops/s,
     knee between 448 and 512, and at 640 kops/s C++ sustains 158 kops/s against Rust's 96, a
     ratio of 1.64 against the guest's 1.8. The 512 kops/s point is **not quotable**: the Rust arms
     are bimodal there with 37 % dispersion.
   - **Counters give the mechanism the thesis had argued.** At the operation scope over 10
     interleaved repeats, Rust retires 11 % fewer instructions (*p* = 0.002) in 15 % fewer cycles
     (*p* = 0.0117) while missing cache 29 % more often per thousand instructions (*p* = 0.002).

   **Two caveats, and both are now follow-up items.** First, the run used the `TESTBED.md` example
   configuration: 8 shards and 8 producers over 8 load levels at 15 repeats, against the canonical
   campaign's (`campaign-20260812-154528`) 7 and 7 over 14 levels at 20 repeats. Shard count is a
   fairness control and the repeat count sets the exact test's floor, so this corroborates the main
   sweep and cannot replace it. Second, and **not yet stated anywhere in the thesis**: the
   toolchain moved too, `g++ 15.1.1`/`rustc 1.97` on Rocky 8.10 against `g++ 13.3.0`/`rustc 1.98.0`
   on Ubuntu 24.04. §`sec:baremetal` says the campaign "changes one thing that matters, the
   machine", and `tab:testbed`'s caption says a machine meeting the protocol was used. Neither is
   true as written: the protocol column also asks for the same toolchain, `isolcpus` and
   `nohz_full` (the capture's own warning block reports neither), and 20 repeats.

   **Repeating it at the canonical configuration and toolchain is the one measurement still
   outstanding**, about two hours and one euro of rented machine. Set
   `kernel.perf_event_paranoid=1`, source `~/.cargo/env`, and add `isolcpus`/`nohz_full` this time.
3. **Harness work: done, and it paid off.** p99.99 and jitter sidecars, `perf` counters and the
   allocation profile were all collected on the bare-metal visit, which is what the earlier
   version of this item was trying to ensure. Two lessons are recorded for a repeat run:
   - `kernel.perf_event_paranoid` defaults to 4 on Ubuntu 24.04 and blocks `counters.sh`. Set it
     to 1 for the session.
   - `alloc_profile.sh --check` reports the Rust arm as unbuildable when `cargo` is not on
     `PATH`, which is what a non-login SSH session gives you. Source `~/.cargo/env` first.
4. **DONE 26 Aug 2026, evening: the sync editing.** The eleventh grading pass moved criterion 5 off
   5 and criterion 6 from 4.5 to 4.0, both on staleness rather than on anything the campaign did,
   and a remediation pass the same evening closed every item except the abstract and restored both.
   All six statements denying an instrument the study used are rewritten, four of the five far-tail
   sites are synced, the toolchain is named in §`sec:baremetal`, `tab:testbed`'s caption stops
   claiming a protocol the host missed, H1's revisit uses the campaign that settles H1's own clause,
   the peak-RSS order-of-magnitude phrasing carries a host at five sites, all five figure defects
   are closed, and six new macros retire the last typed measured values in Chapter 6. Mean back to
   4.67. Detail in `docs/ASSESSMENT.md`, remediation pass.
5. **NOW THE TOP PRIORITY, and it is two hours of reading with no new measurement: the `je`
   statistics the confirmation campaign already recorded.** The twelfth grading pass found that
   **480 bare-metal runs carry jemalloc's own decomposition of the resident set** through the
   instrumentation of Phase 11 item 3, that no generator in `bench/` reads it, that §6.3 does not
   list it, and that §7.2 meanwhile declares that exact split unresolved and pins it on an
   allocation profile. Aggregate the seven fields, write the split, then rewrite the four sites that
   call it open. **Read the numbers before writing them**: Rust holds *less* live data and *less*
   allocator-resident memory while its process peak is higher, so the difference is neither
   application data nor fully inside `jemalloc`, which points at the Rust runtime's own fixed pages.
   That is a better finding than the placeholder. Mind the two caveats: peak RSS is a `getrusage`
   maximum against sampled `je` figures, and the two arms link different builds of jemalloc.
6. **Forty minutes of editing that criterion 5 is waiting on**, plus half an hour of finishing.
   Four sites give the counter result the wrong job, claiming an operation-scope cache-miss rate
   accounts for a fixed footprint. Appendix D's intro says the confirmation campaign "satisfies" the
   protocol column its own caption says it missed on three rows, and that page is 80 per cent white
   because `tab:testbed` floats away, which is what took `\appendixCount` from 6 to 7. Full list in
   `docs/ASSESSMENT.md`, twelfth pass.
7. **Analyse the allocation profile** (Phase 7a below). Half a day, and note it answers a *different*
   question from item 5: call-site attribution, which code allocates, rather than the composition of
   the resident set.
8. **Report the jitter that was collected, and add the p99.99 column to `tab:latency`.** Half a
   day. `\LatencyCols` and `\LatencyHead` are generated so this needs no preamble edit, and the
   `tab_jitter.tex` machinery has been proven since 20 Aug. Also consider giving §`sec:baremetal` a
   figure: it answers the chapter's headline question in prose alone, and its central result is two
   non-overlapping ranges across seven load levels.
9. **Rebuild the slide deck against the bare-metal results** (Phase 10). `build_deck.py` holds no
   `Bm` macro and l. 1052 still reads "The far tail here needs bare metal, not more repeats". The
   deck passes both its gates while contradicting the thesis, which is the quiet failure mode: the
   gates check layout and punctuation, not agreement with the source.
10. **Decide what the companion documents are for, and fix the broken one** (Phase 9b).
   `thesis-vi.pdf` currently renders 113 citations as `[?]` and predates the 15-repeat campaign.
11. **Then:** the proofread round. The two title-page items are not on this path and are not yours
   to schedule: the examiners come from the faculty, and the official class file from the UH
   Overleaf/Moodle.

---

## Phase 0 - Environment & repository setup
- [x] Install LaTeX toolchain (TinyTeX in ~/.TinyTeX; `pdflatex`, `bibtex`, `latexmk` on PATH)
- [x] Obtain the `UH_DS_MSc.cls` class file (local reconstruction from UH_*_MSc family; see note)
- [x] Create `bibliography.bib` with all cited references (97 active entries as of 17 Aug 2026,
      all cited, no orphans; one superseded entry is commented out)
- [x] Verify `Ha_Vien_Mastersthesis_2026.tex` compiles to PDF end-to-end (103 declared pages plus 6
      appendix, 117 physical, as of 26 Aug 2026; all refs/citations resolve; bibliography style is
      now `IEEEtran`, numbered in citation order). Read the declared figure from
      `build/Ha_Vien_Mastersthesis_2026.aux`, not from the PDF's physical total, which includes
      front matter
- [x] Initialize git repository; add `.gitignore` (build artifacts, LaTeX aux files)
- [x] (Optional) Replace reconstructed `UH_DS_MSc.cls` with the official one from Overleaf/Moodle
- [x] Confirm the cover-page programme label ("Master's Programme in Computer Science") is correct
- [x] Decide repo layout: `spec/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/`, `figures/` at
      repo root; `Ha_Vien_Mastersthesis_2026.tex` + `bibliography.bib` at root. No separate `experiments/` or
      `analysis/` dirs (folded into `bench/`).

### Build instructions
```bash
# Toolchain is TinyTeX; PATH set in ~/.bashrc (open a new terminal or `source ~/.bashrc`)
latexmk -pdf Ha_Vien_Mastersthesis_2026.tex      # build -> Ha_Vien_Mastersthesis_2026.pdf
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
- [x] **Run `bench/counters.sh` on the testbed. DONE 26 Aug 2026**, `counters-20260826-105541.jsonl`,
      10 interleaved repeats at both the `op` and `e2e` scopes. The `op` scope is the one that
      speaks to the language and it answers both live claims at once: Rust retires **11 % fewer
      instructions** (*p* = 0.002) in **15 % fewer cycles** (*p* = 0.0117) while missing cache
      **29 % more often per thousand instructions** (*p* = 0.002). Less work and worse locality is
      one account of the operation-level gap and the peak-RSS effect together, and it replaces the
      node-based-`unordered_map` argument with a measurement. Reported in §`sec:baremetal`.
      `kernel.perf_event_paranoid` defaults to 4 on Ubuntu 24.04 and blocks the script; set it to 1.
- [x] **Fixed 26 Aug 2026, evening.** Four places said these counters were never collected (§6.4.3,
      §7.2, §7.6, and `tab:threats`'s RQ3-origin row, whose control column read "None available on
      this host"), and the first was falsified 90 lines later in its own chapter. All four now name
      §`sec:baremetal`. Watch out when editing that table row: `tab:threats` is the densest table in
      the thesis and sits within a few points of its page, so a longer cell overflows it.
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
- [x] **Collected 26 Aug 2026.** `bench/results-baremetal/alloc_profile-20260826-110718/` holds
      40 interval heap dumps per arm, both stderr transcripts, the C++ allocation trajectory as a
      TSV, and the Rust binary kept for later symbolisation. The instrument the thesis has said it
      lacked since the first grading pass now exists as data.
- [ ] **ANALYSE IT. This is the highest-value half day left in the project.** Nothing in the
      document mentions the profile, so under the grading rule that a grade describes the
      manuscript and not the repository it currently earns nothing. What it buys: `tab:findings`'s
      RQ3 status goes from "resolved, unexplained" to a mechanism, and `tab:threats` loses its one
      row whose control column is empty. §6.4.3 already establishes the difference is fixed rather
      than per-context (the `UeContext` layout accounts for ~40 kB at 5000 active UEs, orders of
      magnitude short of the gap), so the profile is what turns "unexplained" into a cause. Note the
      confound recorded in Phase 11 item 3: the C++ arm links the distribution jemalloc while the
      Rust arm builds 5.3.1 from source, so part of any metadata difference is two builds of the
      allocator. Symbolise from the kept binary rather than assuming `jeprof` is on this host.
- [x] **Fixed 26 Aug 2026, evening.** The places that said allocation profiles were never collected
      now say they were captured and are unanalysed, which is the truth and keeps the lift visible.
      Rewrite them again when the analysis lands.
- [x] **The profile would have come back empty, and that is now fixed** (20 Aug 2026, found by
      running it in the container rather than on the testbed). Three defects, all in the
      instrument and none of them visible without running it end to end: the distribution
      jemalloc the Rocky host links is built *without* `--enable-prof`, so the C++ arm had
      nothing to profile with and the script correctly refuses to profile one arm alone;
      backtraces at `-O2` stopped inside the allocator, so not one application site appeared;
      and `prof_final` dumps the live heap *at exit*, after teardown, which measured 92 kB
      (C++) and 640 bytes (Rust) against 2.3 MB live mid-run. Fixed by a dedicated profiling
      build tree with frame pointers, a prof-enabled jemalloc built from the same source the
      Rust arm links (`docker/Dockerfile`), and interval dumps with peak selection. Verified:
      both arms now attribute, C++ 61% cumulative to `ShardCore::create_context` under
      `worker_loop`, Rust 65% under `Service::start` with 8% in the `sync_channel<Request>`
      slot array. Recorded in spec §12. **`jeprof` no longer needs installing on the host:**
      the image carries it.
- [ ] Optional, and a methodology call: jemalloc 5.3 keeps its own frame at the leaf of every
      sampled stack, so the *flat* column collapses onto `prof_backtrace_impl` and the
      cumulative column carries the attribution (totals are unaffected). Building the
      profiling jemalloc with `--enable-prof-libunwind` would put application sites back in
      the flat column for the C++ arm, but `tikv-jemalloc-sys` exposes no hook to do the same
      for Rust, so it would make the two arms use different unwinders. That cuts against the
      one-instrument principle the matched profile rests on, which is why it is not done.
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
- [x] **Execute the campaign on a bare-metal testbed. DONE 26 Aug 2026**, two 480-run sweeps at 15
      repeats (below saturation and through the knee). See "Next up" item 2 for what each returned.
      Kept **15+ repeats** for the reason this item always gave: the exact paired test cannot return
      p < 2/2^n, and at 7 repeats the corrected floor sat above 0.05 so no result could survive Holm
      however large the effect.
- [ ] **Repeat it at the canonical configuration**: 7 shards, 7 producers, 14 load levels, 20
      repeats, on `g++ 15.1.1`/`rustc 1.97`, with `isolcpus` and `nohz_full` on the benchmark cores.
      Until then every thesis table is the KVM-guest campaign (`campaign-20260812-154528`) and the
      bare-metal sweeps corroborate rather than replace it. This is the last thing holding criterion
      3's data half below 5.
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
      only `Ha_Vien_Mastersthesis_2026.tex`. `plain_Ha_Vien_Mastersthesis_2026.tex` inputs the same `figures/gen_*.tex`, so its prose
      updates while its PDF does not, which is exactly how a companion document goes stale
      without anyone noticing.

## Phase 9 - Writing (fill placeholders in Ha_Vien_Mastersthesis_2026.tex)
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
The repo now carries four documents besides `Ha_Vien_Mastersthesis_2026.tex`. Only `Ha_Vien_Mastersthesis_2026.tex` is the submission
artefact; the rest are unlabelled, which is how two of them drifted without it being visible.
- [x] `plain_thesis.tex` - plain-language variant (121 pages) for a reader with no 5G
      background. Same argument, same data, same generated macros, and it built clean.
      `Ha_Vien_Mastersthesis_2026.tex` stays the reference version, and its header already says so. Moved to
      `archive/` on 18 Aug 2026, so it now needs its relative paths fixed before it builds again.
- [x] `thesis-vi.tex` - Vietnamese translation (75 pages), **broken and stale**, and now
      **decided against as a deliverable**. All 113 citations (33 distinct keys) rendered as `[?]`
      because bibtex was never run for this variant, and it did not `\input figures/gen_macros.tex`
      at all, so its numbers were hand-copied and predate the 15-repeat campaign, the latency
      decomposition, and the corrected RQ3 reading. Moved to `archive/` on 18 Aug 2026, where it
      reads as a superseded variant rather than unfinished work. Reviving it means porting the
      generated macros across, not just running bibtex.
- [ ] `Thesis_v2.tex` - 35-page bullet digest of all nine chapters, useful for a supervisor
      read-through. Chapters 6 to 9 were filled on 20 Aug 2026 at the author's request, five
      bullets each, and the results bullets read `figures/gen_macros.tex` and its two companions
      instead of holding their own copies of the numbers, so the file has to be rebuilt after
      `bench/refresh_thesis.sh`. Its abstract is still the template placeholder, "Abstract to be
      written last."
- [ ] `Thesis_Plan_v2.tex` - the 5-page plan, reset to a pre-work baseline ("Work has not started
      yet") and dated 9 Aug 2026. If it is handed in later than that date, the date and the status
      table have to move together.
- [ ] Make the title-page fields agree across variants: `Thesis_v2.tex` has
      `\censors{Keijo Heljanko}{}{}` while `Ha_Vien_Mastersthesis_2026.tex` still has `\censors{}{}{}`. One of the two
      is wrong, and the same programme/study-track labels are duplicated in four files.
- [x] Housekeeping: `thesis_wbm_full_backup.tex` was a tracked 208 kB leftover still on
      `\bibliographystyle{abbrv}`, one word different from `Thesis_v2.tex` and easy to edit by
      mistake. Moved to `archive/` on 18 Aug 2026 together with `plain_thesis.tex`, `thesis-vi.tex`,
      the pre-cuts `Ha_Vien_Mastersthesis_2026.tex` backup, and the v1 plan PDF.

## Phase 10 - Finalization
- [ ] **BLOCKER — rewrite the abstract unaided.** The abstract of `Ha_Vien_Mastersthesis_2026.tex` was drafted
      with model assistance. The UH thesis guide states that a language model may not be used
      when preparing the thesis summary, and in this programme the summary doubles as the
      maturity test, where AI use is never permitted. `ai_statement.tex` already declares the
      abstract as written unaided, so that sentence is false until this is done. Rewrite it in
      your own words from the results, then re-read `ai_statement.tex` end to end and correct
      anything that does not describe what actually happened — it is a statement in your name.
- [x] Declaration of AI use (`ai_statement.tex`), `\input` by both `Ha_Vien_Mastersthesis_2026.tex` and
      `Thesis_v2.tex` before the bibliography, listed in the ToC. Follows the UH basic
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
      `.aitells.py Ha_Vien_Mastersthesis_2026.tex` after any large writing pass.
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
- [ ] **Stale again as of 26 Aug 2026, and the gates did not catch it.** `build_deck.py` reads no
      `Bm` macro and l. 1052 still reads "The far tail here needs bare metal, not more repeats",
      which the thesis now contradicts. The deck rebuilt clean in the same `refresh_thesis.sh` run
      that regenerated the bare-metal macros and reported both "Layout" and "Prose style" passing,
      because those gates check placement and punctuation and not agreement with the source. Add
      the far-tail slide, correct the RQ3 slide's mechanism now that the counters exist, and
      consider whether the "what this host cannot carry" slide becomes a two-host slide.
- [ ] Final PDF + submission (`Ha_Vien_Mastersthesis_2026.pdf`, written directly by `bench/refresh_thesis.sh`)

### After the bare-metal campaign: what each re-check returned (26 Aug 2026)

Section numbers below use the full draft's current eight-chapter numbering, not the skeleton's.

- [x] **The far tail (§6.4.1's "not measurable on this host") became a real finding.** Pooled
      p99.99 separates the languages over 32 to 96 kops/s and does not below it, with Rust lower.
      Reported in §`sec:baremetal`. **But five sites still say it is unresolved**, and one of them
      is `tab:findings`'s RQ1 row, which is where an examiner reads the verdict. See "Next up"
      item 4.
- [x] **Peak RSS reproduces.** 16 of 16 points significant, same sign, language effect 0.7 to
      1.8 MiB. The prose leaning on it is safe.
- [x] **FIXED 26 Aug 2026, evening: the peak-RSS *ratio* did not reproduce, and now the thesis says so.** The allocator effect fell
      from 32.9-34.4 MiB on the guest to **1.9-3.2 MiB** on bare metal, while the language effect
      only halved. So the gap between the two effects went from about thirteenfold to about
      twofold, with the allocator configuration matched at `thp:never,narenas:16` on both hosts.
      §`sec:baremetal` says only that the allocator effect "remains the larger of the two", which
      is true and incomplete. Three sites state the finding as a bare "order of magnitude" with no
      host attached: §1.4, `tab:findings`'s RQ3 row, and the conclusion. **Attach a host to that
      phrase.** The non-negotiable claim is untouched: both effects are real and the allocator's is
      still larger. Note the confound worth naming while writing it: the C++ arm links the
      distribution jemalloc, which is 5.2.x on Rocky and 5.3.x on Ubuntu, and the Rust arm builds
      5.3.1 from source on both.
- [x] **FIXED 26 Aug 2026, evening, and this note was wrong about the guest.** The claim above that
      the CPU comparison "clears Holm under the system allocator and reverses under jemalloc" came
      from an earlier campaign. §6.4.3 has for some time reported the below-saturation CPU result as
      clearing the correction under **both** allocators, so there was no non-result to resolve. What
      bare metal adds is a cleaner confirmation, **16 of 16 points with one sign**: Rust draws
      **less** CPU, by 0.3 to 7.6 percentage points, the gap widening with offered load, under both
      allocators. Six `\BmCpu*` macros now carry it and §`sec:baremetal` reports it. Lesson worth
      keeping: a re-check list that predates two campaigns will describe a state the thesis has
      already left, so re-read the thesis before scoring an item on this list.
- [ ] **The core-operation gap was NOT re-measured.** `bench/results-baremetal/latency_budget.json`
      is byte-identical to `bench/results/latency_budget.json`, so it is a copied guest file and
      `\BudgetCoreRatio` remains a guest number. Its presence in that directory is misleading and
      it should either be re-measured or removed. What *did* land is better than the timing repeat
      this item asked for: the op-scope counters give the attribution directly (11 % fewer
      instructions, 15 % fewer cycles, 29 % more cache misses per thousand instructions), which is
      what "consider isolating the attribution with cache-miss counters" meant.
- [x] **Fixed 26 Aug 2026, evening.** RQ1's status now reads "unresolved here, resolved on bare
      metal at one shard count" and its finding cell names the pooled p99.99 result. RQ3's reads
      "direction accounted for by counters, split within the resident set open". The remaining half
      of RQ3's is closed properly by analysing the allocation profile, not by rewording again.
- [x] **Fixed 26 Aug 2026, evening.** The revisit now records the clause H1 named as **half right**:
      the main host cannot resolve the far tail at all, the confirmation host does and finds a
      difference there in Rust's favour, so H1 was right about where to look and wrong that it was
      the only place. The overload finding is framed as something H1 did not consider rather than as
      a refutation of the tail clause. `Thesis_v2.tex` carries the same reading.
- [x] **p99.99 is reportable and reported.** The pooled far tail is in §`sec:baremetal`, and
      `pool_hist.py` wrote `campaign-20260826-102047.hist.pooled.csv`. `NTests` still reads 14 and
      p99.99 stayed out of the Holm family, as §`sec:stats` committed.
- [x] **Fixed 26 Aug 2026, evening.** §`sec:stats` now says the main campaign reports neither and
      the confirmation campaign carries both, with jitter recorded and left undiscussed because no
      research question asks for it. §`sec:threats` splits the two the same way.
- [ ] **`tab:latency` has not gained its p99.99 column.** `\LatencyCols` and `\LatencyHead` are
      generated precisely so this needs no preamble edit. The bare-metal campaign records the
      column. Check the table still fits the text width at six columns.
- [ ] **Jitter is measured and unreported.** All 32 pooled groups carry `jitter_p50_ns`,
      `jitter_p99_ns`, `jitter_p999_ns` and `jitter_max_ns`. RQ1 does not name jitter, so nothing
      is promised and this is an upgrade rather than a hole, but `tab_jitter.tex`'s machinery was
      proven on 20 Aug and is idle. If it is adopted it needs a float and a caption, plus the
      `\Jitter*` / `\FarTail*` / `\Iqr*` prose. Keep it descriptive and out of the tested family,
      for the reason §`sec:stats` already gives.
- [x] **Fixed 26 Aug 2026, evening.** `refresh_thesis.sh` now pools every
      `results-baremetal/campaign-*.hist.jsonl` before calling `baremetal_facts.py`, so the far-tail
      macros can no longer keep stale values silently. It does not pass `--verify`, which is a
      one-time lossless check and not a per-refresh one, so run
      `python3 bench/pool_hist.py <hist.jsonl> --verify <jsonl>` by hand after a new campaign.
- [x] **Fixed 26 Aug 2026, evening.** "Verbatim" is gone. The scope now reads "every result table,
      every plot of measured data, and every quoted number", with the two exclusions stated: a
      hand-drawn schematic is authored, and a rerun on another host regenerates by the same
      procedure and not to the same values, of which §`sec:baremetal` is the worked example.
      `bench/results-baremetal/` is listed beside `bench/results/`.

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
longer names jitter: as worded in the plan, `Thesis_v2.tex` and `Ha_Vien_Mastersthesis_2026.tex` it asks about the
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

- [x] **The harness for this is proven end to end** (20 Aug 2026, `docker/VALIDATION.md`): a
      200-run campaign through the container on the WSL2 laptop wrote `tab_jitter.tex` and the
      whole `Jitter*` / `FarTail*` / `Iqr*` macro family for the first time, and
      `pool_hist.py --verify` confirmed every percentile of all 200 runs recomputes from the
      persisted buckets on a shared lattice. `NTests` still read 14. So the §7.5 float, its
      caption and the prose can be written against the real macro names *before* the run,
      instead of discovering their shape afterwards.
- [x] **Overtaken by events, 26 Aug 2026.** The bare-metal campaign carries `--jitter` and
      `--hist-out` and its pooled p99.99 is now reported in §`sec:baremetal`, which is what this
      item existed to make possible. `NTests` still reads 14. Running the same campaign on the KVM
      guest would now buy only a jitter comparison between two hosts, which no research question
      asks for, so this is closed rather than done. What is still open is *reporting* the jitter
      that was collected, which is tracked in the post-campaign re-check list above.
- [ ] **One thing this item warned about now applies to the reported RSS numbers.** `--jitter` costs
      about 264 KiB per producer of peak RSS. The bare-metal campaign ran with it and the guest
      campaign did not, so the two hosts' **absolute** peak RSS figures are not comparable, only
      their paired within-host differences are. §`sec:baremetal` compares differences and is
      therefore safe as written, but say so if any absolute figure is ever quoted across the two.

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
- [~] **The bare-metal campaign records the `je` object in every run, and this is now the top item in
      "Next up".** The twelfth grading pass promoted it: `je` is a top-level field in all 960
      bare-metal records, 480 of which carry values (the system arms emit nulls, correctly), and
      **nothing reads it**. Meanwhile §7.2 declares the split it measures unresolved and pins it on
      an allocation profile. Medians over the 90 runs per arm at steady state, jemalloc arms, MiB:

      | Field | C++ | Rust | Rust − C++ |
      | --- | --- | --- | --- |
      | `allocated` | 0.78 | 0.62 | −0.16 |
      | `active` | 1.43 | 0.79 | −0.64 |
      | `metadata` | 4.19 | 6.26 | **+2.07** |
      | `resident` | 11.02 | 9.10 | −1.92 |
      | `mapped` | 42.82 | 44.83 | +2.01 |
      | `retained` | 27.72 | 31.67 | +3.95 |
      | peak RSS | 15.08 | 16.82 | **+1.74** |

      **Read this before writing it up, because the obvious reading is wrong.** It is tempting to
      say metadata explains the +1.74 MiB and stop. But jemalloc's own `resident` goes the *other*
      way by 1.92 MiB, and Rust holds less live data, so the extra process footprint is neither
      application data nor inside the allocator's mappings at all. It points at the Rust runtime's
      own fixed pages, which is a sharper and more interesting claim than the placeholder. Mind that
      peak RSS is a `getrusage` maximum while the `je` figures are sampled at a point, so the two are
      not strictly commensurable and the write-up has to say so.
- [ ] **Two further questions the same field can answer.** Check the 30 MiB bimodality against
      `metadata`: if the low-RSS runs are runs where fewer arenas were touched, the measurement
      defect behind peak RSS failing Holm under jemalloc has a named cause. And check whether
      `metadata` explains why the allocator effect fell from ~33 MiB on the guest to ~2.5 MiB on bare
      metal.
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

### 5b. Four more defect classes, and the taxonomy table generated — DONE (24 Aug 2026)

**Why.** The catalogue was 5 + 5 and every in-guarantee class was caught by at least one
sanitiser, so the "at what stage and cost" half of RQ2 rested on an argument (an instrumented
build is expensive, and detection needs a test that drives the path) rather than on a row.
Nothing in the catalogue tested the `Send`/`Sync` discipline either: all five Rust rejections
were borrow-checker diagnostics while the prose claimed two mechanisms.

- [x] **The taxonomy table is generated, and that was done first.** `write_taxonomy_table()` in
      `bench/plot_figures.py` writes `figures/tab_taxonomy.tex` from `faults/results/taxonomy.csv`,
      and Table 7.6 `\input`s it. This was the last hand-maintained results table in the thesis
      and the ninth grading pass's durable fix for criterion 4. §7.3's claim that table and figure
      come from the same log is now enforced instead of asserted. It was done before any new class
      went in, because hand-typing four rows into the table that was already flagged for being
      hand-typed is the wrong order.
- [x] **The figure now groups the same way the table does.** Both split on `rust_expected`, the
      expectation recorded before the run, rather than on the measured result. Grouping on the
      result would make the structure a restatement of it, and a case that changed sides would land
      in different halves of the table and the figure while the caption claimed they agree.
- [x] **Catalogue is now 7 in-guarantee + 7 boundary.** `use_after_move` and
      `thread_unsafe_sharing` inside the guarantee, `seam_double_free` and `forgotten_guard`
      outside it. Added in pairs on purpose: the two sides being the same size is the defence
      against "the author picked the cases", and it was 5 + 5 for the same reason.
- [x] **`use_after_move` is the row the catalogue did not have.** No C++ sanitiser reports it,
      because a moved-from object is valid but unspecified, so nothing is corrupted and nothing is
      undefined while the acknowledgement goes out under an empty identity. Every other
      in-guarantee class is caught by at least one of the three. Quote it with the caveat: a static
      analyser would plausibly flag it (`clang-tidy` has `bugprone-use-after-move`), and this study
      runs none, by the decision recorded in §5.4.
- [x] **`thread_unsafe_sharing` is the only `E0277` in the table.** `Rc` is `!Send` and
      `thread::spawn` asks for `Send` in its signature, so the rejection is a trait bound rather
      than an aliasing analysis. The C++ handle states the same rule in a comment, because a
      comment is the only place C++ has for it.
- [x] **`seam_double_free` is not a new class, and that is why it earns a row.** It is
      `double_free` rewritten through the `unsafe` a C ABI forces, so it appears on both sides of
      the rule. The C++ half is deliberately unchanged, which makes the Rust column the only thing
      that moves. This reproduces the CVE finding that Rust memory-safety bugs trace back to
      `unsafe` (`xu2021rustcve`) under controlled conditions instead of only citing it.
- [x] **`forgotten_guard` separates "Rust removes this bug" from "removes this class".** RAII
      removes the C++ form, a validation path returning before a hand-written unlock. It does not
      remove the class, because a guard is a value and leaking one is safe. No sanitiser reports
      the C++ side: a lock never released is neither a race nor a cycle. The liveness counterpart
      to `leak_cycle`.
- [x] **Miri answers the detection stage for the unsafe class**, `faults/run_miri.sh` with
      `rust/seam_double_free_control.rs` as its control, writing `results/miri.{md,csv}`. Miri
      names the defect exactly and the control is clean. **The limit is the finding**: Miri
      interprets Rust and cannot execute a C++ host, so the tool that catches this defect cannot be
      pointed at the configuration it ships in.
- [x] **A latent runner bug surfaced, the mirror of the one section 5 found.** `run_rust`
      classified any `rc >= 124` as "hung", so the seam double free's `SIGABRT` would have been
      recorded as a deadlock. Only 124 and 137 are timeouts now, and `crashes` is a distinct
      outcome from `wrong-result`.
- [x] **The boundary group is now policed.** Each boundary case declares which misbehaviour it
      exhibits and the runner checks the run against it, so a case that quietly stopped reproducing
      is a violation rather than a row that still reads as evidence. `leak_cycle` needed a real fix
      to satisfy this: it printed that nothing was dropped without observing it, and now counts
      destructor calls on both sides and exits non-zero.
- [x] Prose synced in `Ha_Vien_Mastersthesis_2026.tex` (§3.2 catalogue and `tab:defectmap`, §5.4,
      §7.3, Table 8.1, §8.2, §8.5 threats, §9), `Thesis_v2.tex`, `Thesis_Plan_v2.tex`,
      `faults/README.md`, `build_deck.py`'s `DEFECTS`, `AGENT.md` and the workspace rule. Declared
      length 105 to 108 pages.
- [ ] **The abstract still says "five" and "Five further classes", twice.** It is the only place
      the counts are now wrong, and it is the one place a model may not edit. The author has to
      make that change when rewriting the abstract unaided.
- [ ] **The deadlock detection rate is not stable and the prose leans on it.** Successive 12-repeat
      runs recorded 4, 5, 7 and 9 hits, so "a majority of runs" was true at 7 and 9 and false at 4
      and 5. Twelve repeats establish intermittency but do not estimate the rate. Raising
      `DEADLOCK_REPEATS` to 60 costs about three minutes and would let the prose say something
      stable, or the sentence should be rewritten to claim only intermittency.

### 6. One robustness arm against the compiler, not just the language

`tab:threats` has no row separating the language from its toolchain. Every performance number is
g++ / libstdc++ against rustc, so "C++ is slower on the core operation" is, strictly, a
statement about one implementation of each. A single clang++ / libc++ arm at the representative
load and the overload point would bound that confound. Same for `-O3` / `opt-level = 3` and LTO,
which test whether the matched `-O2` choice is load-bearing. Cheap, and it either adds a
robustness sentence or finds something.

> **Status, 26 Aug 2026: a partial answer arrived by accident and has to be reported either way.**
> The bare-metal campaign ran `g++ 13.3.0` and `rustc 1.98.0` where the guest campaign ran
> `g++ 15.1.1` and `rustc 1.97`. Every finding survived, across two major versions of the C++
> compiler and a minor version of rustc. That is a free robustness result and it argues *for* the
> thesis. It is also a fifth difference between the two campaigns that §`sec:baremetal` does not
> name while claiming the campaign "changes one thing that matters, the machine", and
> `tab:testbed`'s caption says the confirmation host met a protocol column that asks for the same
> toolchain. **Either name it as a robustness arm or stop claiming one variable moved.** The clang
> arm would still be worth having, and it is now less urgent.

### 7. The RQ4 cost axes that were never measured — DONE (21 Aug 2026)

RQ4 asks about "effort, FFI interoperability, and risk" and the thesis answered the middle one
well. All three missing axes are now measured by `bench/adoption_cost.py`, which writes
`figures/tab_adoption.tex` and `figures/gen_adoption.tex` and is called by
`bench/refresh_thesis.sh`. Written into §7.6 (five `\paragraph` blocks plus `tab:adoption`),
Table 8.1's RQ4 row, §8.4's RQ4 paragraph, §5.4's method description, and the conclusion.

- [x] **Compile time**, clean and incremental, 15 interleaved repeats after 2 discarded, same
      job count on both sides. **Two findings, and the headline one goes against the objection.**
      The full build does cost `\BuildAllCpuRatio` times the CPU, but `\BuildDepShareCpu`% of that
      is third-party code: measured with the dependency tree warm, the project's own source
      compiles in `\BuildAllFirstPartyCpuRatio` times the CPU `g++` needs. So the build-time
      objection is an argument about a dependency budget and not about `rustc`. Second, the
      incremental loop is where C++ genuinely leads and it leads unevenly: an edit inside a
      translation unit rebuilds in `\BuildIncCppTu`s against Rust's `\BuildIncRust`s, an edit to a
      core header takes `\BuildIncCppHeader`s, and Rust's figure does not move with the size of
      the edit because the crate is the compilation unit.
- [x] **Binary size and static footprint.** Measured on `conformance_runner`, the tightest matched
      executable pair (spec-defined, built by both, no dev-dependency either side). **The naive
      comparison is a linkage-policy artefact and the ordering reverses when the policy is held
      fixed:** shipped defaults give Rust `\FootShippedRatio`x the size, matched *dynamic* std
      gives C++ smaller by `\FootDynamicRatio`x, matched *static* std gives **Rust** smaller by
      `\FootStaticRatioAbs`x. Cause measured, not argued: `\FootCppLocaleShare`% of the sized
      symbols in the static C++ binary are locale and stream facets, including the money, date and
      `wchar_t` facets the program never instantiates, because a static libstdc++ link takes the
      facet table as a set. Both dynamic rows also report what they leave on the host
      (`\FootSharedCpp` vs `\FootSharedRust` KiB) so the row cannot be read as the std being free.
- [x] **Dependency and `unsafe` supply chain.** `\DepsCore` transitive crates and `\CoreUnsafe`
      `unsafe` sites in the compared component, which turns spec §12's dependency-free assertion
      into a measurement. The allocator arm resolves `\DepsJemalloc` (`\DepsJemallocShipping`
      shipping, `\DepsJemallocBuildOnly` build-only, a distinction that matters because a
      build-dependency ships nothing and still executes on the build machine) and the benchmark
      harness `\DepsHarness`, holding `\DepsUnsafeJemalloc` and `\DepsUnsafeHarness` `unsafe`
      sites. **The uncomfortable half is worth keeping:** the largest unaudited surface in the
      project belongs to the measurement apparatus, not to the component that would ship.
- [x] **`cargo geiger` was not used and should not be.** It measures one language, where the house
      rule is one instrument applied to both (`lizard` for complexity, jemalloc's own `prof` for
      allocation). The counter is written here instead, one syntactic rule over the resolved
      sources, and the C++ column is left empty on purpose: the language marks no such region, so
      entering a zero would be a category error rather than a favourable result.
- [ ] **`cargo audit` deliberately not adopted as a thesis number.** An advisory scan's result
      moves with the advisory database and not with the code, so it is not reproducible from the
      repository and would go stale in the PDF. It is a deployment-time control. If it is ever
      wanted, report it with the database date beside it, or not at all.
- [x] **Build time is the one host-sensitive axis, and the sync pass fixed four places that said
      otherwise.** §5.3, §8.1, `tab:threats`'s external row and §8.6's external-validity paragraph
      all claimed RQ2 and RQ4 were environment-insensitive without qualification. They now say
      that the build-time absolutes belong to the machine and the paired ratio is what travels.
- [x] **`refresh_thesis.sh` calls it without `--measure` on purpose.** Build time is replayed from
      `bench/results/adoption-*.json`, so a refresh on a loaded machine cannot quietly overwrite
      the recorded figures the way an `ffi/build.sh` run once did (AGENT.md §5). Footprint and
      supply chain are deterministic and are recomputed every run.
- [ ] **Re-measure build time on the KVM guest** if the numbers are ever quoted as absolutes
      rather than as a ratio. Not blocking: the ratio is a within-host paired comparison and the
      other two axes are toolchain properties.
- [ ] **`git add -f bench/results/adoption-20260821-134156.json` when committing this.**
      `bench/results/` is in `.gitignore` and the campaign records are tracked only because they
      were force-added. The adoption record needs the same, or the build-time rows vanish for
      anyone else: `adoption_cost.py` without `--measure` finds no record, exits non-zero, and
      `refresh_thesis.sh` reports it as a WARN while leaving the last generated table in place,
      which is the quiet-staleness failure mode rather than a loud one. The two smoke-test records
      from this pass (1 and 2 repeats) were deleted on purpose, since the 1-repeat one contains the
      `cargo clean -p` no-op that the first version of the script recorded as the first-party cost.

Vander Stoep's 2025 Android data (`LITERATURE_NOTES.md` §3.1: ~4x lower rollback rate, ~25% less
review time) is the published counterpart to the effort axis and is already verified. It is now
the obvious companion cite for the build-time result, since both say the adoption cost sits
somewhere other than where the objection puts it.

**Cost of the addition: `\pagesCount` moved 99 to 104.** Above the author's under-100 working
preference, so it is reported here for a decision rather than trimmed silently (AGENT.md §5,
"substance wins"). The table is one float and the prose is five `\paragraph` blocks, so the
cheapest reduction if one is wanted is to cut the footprint discussion to the reversal alone.

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
- [x] **Adopted, 22 Aug 2026.** `tab:equivalence` is placed in the equivalence subsection as the
      fourth of five readings of the test family, with a paragraph separating tight bounds from
      wide ones.
- [ ] **Still open, and now cheap: the power calculation.** It was for choosing the September
      repeat count and the campaign already ran at 15. Its remaining use is the canonical repeat:
      the bare-metal far tail separated at 15 repeats where the guest could not separate at 20, so
      the binding constraint was never the repeat count, and a power calculation on the bare-metal
      dispersion would say what n the canonical repeat actually needs.

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

- ~~`bench/plot_figures.py` generates `fig_tail_percentiles.pdf`, `fig_resources.pdf`,
  `fig_taxonomy.pdf` and `fig_ffi_cost.pdf`, and `thesis.tex` includes none of them.~~ **Done
  (Aug 2026).** All four are placed, and two were rebuilt first because they were not fit to
  place as they stood: the percentile fan had no intervals, so four overlapping lines read as a
  claim of equivalence, and `fig_ffi_cost` was titled with the crossing-vs-round-trip ratio that
  §6.4.8 explicitly declines to reason from. Two figures were added with them: `fig_effects.pdf`
  (the Holm family as paired effects on one normalised axis) and `fig_overload.pdf` (the
  past-saturation divergence, which was the study's strongest result and had no figure at all).
  Chapter 6 now runs nine plots of measured data against eleven tables, where it ran three.
  Regenerating `tab_ffi.tex` in the same pass also fixed a live figure/table/prose disagreement:
  the committed table said 12 entry points and 12 `unsafe` functions where `gen_artefacts.tex`
  and the prose said 11 and 9. `build_deck.py` needed the matching row labels and full-width
  boxes for the two figures that grew wider.
- Several `diagrams/pdf/*` are likewise unused where TikZ or a table took over the role.
- `AGENT.md` and `ASSESSMENT.md` both still list `\censors{}{}{}` as the title-page item, but
  `thesis.tex` now uses `\supervisors` with an unset `\examiners`. Same task, wrong command name
  in two places.

---

### Notes / open questions
- Timeline: writing and implementation complete, and the bare-metal campaign ran on 26 August,
  ahead of the plan's September slot. Remaining work is spec freeze, the sync editing the campaign
  created, supervisor review, and submission. `Thesis_Plan_v2.pdf` still schedules measurement for
  September in its timeline table while its status paragraph records the campaign as run; those two
  have to move together before the plan goes out again.
- Current artefact status (verified 26 Aug 2026): spec + C++/Rust implementations + conformance
  suite + bench/fault/ffi harnesses + generated figures/tables + a **103-page** thesis PDF (117
  physical). All green on `spec/conformance/run.sh`, `ctest`, `cargo test`,
  `faults/run_faults.sh`, `ffi/build.sh`.
- **Remaining critical path:** (1) supervisor review → spec v1.0 freeze, (2) the fourteen sync
  edits the campaign created, about three hours, (3) analyse the allocation profile and add the CPU
  macros, about a day, (4) repeat the bare-metal campaign at the canonical configuration and
  toolchain, about two hours, (5) rewrite the abstract unaided, (6) final proofread + submission.
  Only (4) needs anything the author does not already have.
- Overfull boxes are **zero** as of 26 Aug 2026, so the abstract-page overflow this note used to
  record is fixed. The abstract box is still full to the line, so check page 3 visually after
  editing it.
- Two load-bearing citations are still arXiv preprints rather than peer-reviewed work (Bugden and
  Alahmar for "Rust matches C/C++ on performance", Zhang et al. for deadlock detection). Optional,
  but replacing either removes the last soft spot in the bibliography. See `ASSESSMENT.md`
  criterion 2.
- `UH_DS_MSc.cls` is a LOCAL RECONSTRUCTION adapted from `UH_TCM_MSc.cls` (which states it
  is "based heavily on the UH_DS_MSc.cls"). It defines every command Ha_Vien_Mastersthesis_2026.tex uses
  (`\prof`, `\censors`, `\mytableofcontents`, `\mynomenclature`, `\myappendixtitle`,
  `\depositeplace`, `\additionalinformation`, `\quoting`, `\keywords`, `\classification`).
  The genuine class lives behind the UH Overleaf/Moodle login; swap it in for final submission.
- `\mynomenclature` is a no-op here (the `nomencl` package clashes with hyperref/report in
  this class family and is disabled upstream too); it just switches page numbering to arabic.
- Cover/abstract programme is set to "Master's Programme in Computer Science" (English),
  inferred from `\additionalinformation{Software study track}`. Verify this is right.
- Logo `UH-logo.png` is the official UH logo taken from the UH CS thesis-template repo.
