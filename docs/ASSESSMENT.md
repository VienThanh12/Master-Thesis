# Thesis assessment and refinement record

Assessment of **Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia
RAN Control-Plane Systems** against the six-criterion assessment matrix (simplified from the
data science master's thesis matrix), on the Finnish 1–5 scale.

Two states are recorded per criterion: the grade on first reading, and the grade after a
refinement pass. Source material was the thesis PDF and the supporting artefacts in `spec/`,
`bench/`, `faults/`, `ffi/`, and `diagrams/`.

The thesis source was renamed from `Ha_Vien_Mastersthesis_2026.tex` to `Ha_Vien_Mastersthesis_2026.tex` on
19 August 2026. Passes recorded before that date read the same document under the older name.

An interactive version of this document exists as a Cursor canvas at
`~/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grading.canvas.tsx`. This file is
the durable copy; keep the two in step if you revise either.

> **The current grade is the remediation pass, 22 August 2026 afternoon, at the end of this file.** The
> summary table immediately below is the first pass and is kept as history, not as the standing
> view. Eight passes are on record and they do not all agree: the second held criteria 3 and 4 at 4
> rather than 4.5, on the grounds that three criticisms said to need new measurement were
> answerable from the dataset already in hand, the fourth took criterion 6 from 5 to 4.5 on the
> truthfulness of the AI declaration, and the sixth took criterion 4 from 4.5 to 4 after checking
> the hand-typed prose values against the published artefacts rather than only counting them. The
> seventh and eighth confirmed every area where the sixth left it. Read the passes in order if the
> reasoning behind a half-grade matters. Where any two disagree, the later one is current.

---

## Summary

| Criterion | Before | After |
| --- | --- | --- |
| 1. Thesis objective and research questions | 5 | 5 |
| 2. Scholarly framework and use of sources | 5 | 5 |
| 3. Research data and method | 4 | 4.5 |
| 4. Presentation of thesis results | 4 | 4.5 |
| 5. Discussion and conclusions | 5 | 5 |
| 6. Academic text | 4 | 5 |
| **Overall (unweighted mean)** | **4.5** | **4.8** |

Criteria 3 and 4 are held at 4.5 by one thing, and it is not a writing problem. RQ1's
tail-latency result still rests on WSL2 measurements that the thesis itself argues are not
adequate for the claim. Executing the bare-metal protocol in `bench/TESTBED.md` lifts both at
once. Everything that analysis, presentation, or prose could contribute has been done.

The half-grades are deliberate. The distinction they encode — between work that is unfinished
and work that *cannot* be finished by editing — is the point of this record, so do not round
them without also revising the reasoning below.

---

## Criterion 1 — Thesis objective and research questions

**Grade 5, unchanged.**

The topic is justified on three independent axes at once: industrial (a Nokia gNB-CU-CP
component), regulatory (the CISA and ONCD memory-safe roadmap mandates), and scientific (Rust's
fit for latency-critical telecom is genuinely unproven).

The research gap is identified with unusual precision. It is not the generic "compare Rust and
C++" but the specific observation that in the closest prior works the language co-varies with the
runtime and concurrency model, so no measured difference can be attributed to the language. The
entire study design follows from that critique.

**Revised 17 August 2026 after the third literature sweep** (`LITERATURE_NOTES.md`, third sweep).
The gap holds, but its statement had to be corrected: the neighbouring work is a cluster of
**five** Ericsson-hosted master's theses, not two, and one of them (Emberg and Wadsten) already
builds a matched C++/Rust pair across an FFI seam and compares it statistically. The
differentiator is therefore no longer "nobody builds a matched pair" — which was refutable in one
repository search — but the combination that none of them holds: a stateful, concurrent subsystem,
one frozen specification with the concurrency model fixed, a sweep past saturation with tail
percentiles, a two-sided defect boundary, and a measured seam cost. Two further findings from that
sweep support the criterion-1 case rather than weakening it: none of the five is indexed by any
citation database, so the evidence a vendor would rely on has not been reviewed; and no Finnish or
Nokia-side counterpart exists at all.

RQ2 is constructed so that it can refute itself: five defect classes from inside Rust's
guarantee and five chosen from outside it. Building in cases that can disturb the expected answer
is a graduate-level instinct, and here it paid: two of the five boundary classes came back with
the **C++ tooling ahead** (LeakSanitizer reports the reference cycle safe Rust leaks silently;
UBSan reports the overflow Rust defines to wrap), and a third result changed direction on
re-measurement — the lock-order deadlock is detected by ThreadSanitizer *intermittently*, about
30% of runs, not reliably and not never.

Traceability is complete: RQ1–RQ4 map to objectives O1–O5, to hypotheses H1–H3, to stated
success criteria, to explicit scope boundaries, and finally to Table 5.1, which pairs each
question with its method, artefact, and primary metric.

*Nothing outstanding.* Four research questions is ambitious, and the breadth shows in RQ3
receiving the least depth, but this does not cost the grade.

---

## Criterion 2 — Scholarly framework and use of sources

**Grade 5, unchanged.**

Sixty-four references concentrated in top venues: POPL for RustBelt and Stacked Borrows, plus
PLDI, OSDI, SOSP, NSDI, OOPSLA, ICSE, CCS, EuroSys, USENIX ATC, IEEE S&P, CACM, TOSEM, and TSE.
Domain grounding comes from five 3GPP technical specifications rather than secondary summaries.

The literature search is stated explicitly in Section 4.1 — databases, search terms, inclusion
criteria, backward and forward citation chaining — which makes the gap claim auditable rather
than rhetorical.

Critical maturity is the standout. Section 8.5 opens with "Not all of this evidence points the
same way" and means it. Arvidsson and Kaller's tail result contradicts H1; the thesis reports
it, says omitting it "would be dishonest", and converts the disagreement into a falsifiable
prediction about what the bare-metal campaign should find. Emmerich's Rust driver is
acknowledged as genuinely slower, and the "zero-cost" framing is re-read as workload-dependent
rather than universal.

Concepts are defined and then held to. The data race versus race condition distinction, and the
distinction between what the compiler verifies and what is protected at run time, are stated
once in Chapter 2 and honoured consistently through 7.5.3, 8.2, 8.4, and 8.6. Most theses lose
that consistency by the discussion chapter.

**Changed in the refinement pass.** Section 4.1 no longer re-enumerates the four gaps that
Section 2.8 has just stated. It keeps what was genuinely its own contribution — the search
protocol — and reframes the two contrary results as the baseline the thesis works against.

**Outstanding (optional).** One load-bearing citation is still an arXiv preprint rather than
peer-reviewed work: Bugden and Alahmar carries the claim that Rust matches C and C++ on
performance. The deadlock-detection claim no longer is — Zhang et al. appeared in *Automated
Software Engineering* 33(2):65, 2026, and the bibliography now cites that version
(`zhang2026deadlock`). Replacing the remaining preprint would remove the last soft spot in an
otherwise very strong bibliography.

---

## Criterion 3 — Research data and method

**Grade 4 → 4.5.** The method is now unambiguously at 5. The data is not.

### What was already strong

The frozen-specification matched-pair design is the correct control, and it is enforced
concretely rather than declared. Shard selection is pinned to SplitMix64 and intra-shard hashing
to FNV-1a, with a test asserting the Rust `BuildHasher` is bit-identical to the reference, so
neither standard library's hasher becomes an accidental advantage. Both sides link jemalloc with
a system-allocator control retained, and optimisation levels are matched.

Functional equivalence is tested, not assumed: a language-neutral conformance suite emits
canonical transcripts from both implementations and diffs them op-for-op, with the workload's
per-operation-kind counts as a second independent parity signal.

More than that, the suite no longer rests on the two implementations agreeing with each other.
A cross-diff cannot separate *both correct* from *both wrong in the same way*, which is exactly
the risk when one author works from one specification, so a **third implementation of the
specification** (`spec/conformance/model.py`, Python, sharing no code with either) supplies the
expected results. It must reproduce all 223 hand-derived expectations before it is allowed to
generate any of its own; roughly 793 000 generated operations across five profiles have found no
divergence. The §5.2 transition matrix is enumerated exhaustively rather than sampled, on both
sides. The reach of all this is measured rather than asserted — 94.6% C++ and 98.2% Rust library
line coverage — which is what bounds the accompanying negative results: the C++ suite runs clean
under ASan, TSan and UBSan, and the Rust suite clean under Miri, but a dynamic tool only reports
on code that runs.

Methods are grounded in method literature rather than improvised — Georges et al. for
statistics, Natella et al. for fault injection, Tene for coordinated omission, design science
for the constructive element. Ethics are correctly handled and then extended past compliance in
Section 8.7.

### Changed in the refinement pass

- **Added an exact two-sided paired permutation test**, Holm-corrected across the family of
  twelve comparisons. This answers the criticism that conclusions rested on interval overlap.
  It exploits something the design already had but was not using: because the four variants are
  interleaved inside each repeat, the runs form a matched design, so interference common to a
  block cancels in the pairwise difference. With seven repeats all 2⁷ sign assignments are
  enumerated rather than sampled, so the *p*-values are exact and no distributional assumption
  is imposed on a sample known to be skewed. Implemented in `bench/plot_figures.py`; falls back
  to seeded Monte Carlo above eighteen repeats.
- **Replaced symmetric confidence half-widths with explicit asymmetric intervals.** The old form
  produced entries like `582.7 ± 11852.8` µs, implying a lower bound of −11270 µs — an
  impossible latency, and an artefact of the notation rather than of the data.
- **Measured and reported cyclomatic complexity**, which Section 7.3 promised and never
  delivered. `bench/complexity.py` uses `lizard` applied identically to both languages, so the
  comparison is not confounded by each language's native tooling counting different things.
- **Section 5.5 now states the test's resolving power**: an exact test on *n* pairs cannot
  return a two-sided *p* below 2/2ⁿ, so a seven-repeat campaign cannot reach significance after
  correction whatever the effect size. Stating that floor is what keeps the null results honest
  rather than merely convenient.

### What still blocks a 5

- **The blocker.** RQ1 and RQ3 still rest on WSL2 data. No amount of analysis fixes this; the
  measurement has to be retaken on bare metal.
- **Raise the repeat count above seven.** This matters more now than before, because the exact
  test's floor is set by the repeat count: at seven, nothing survives Holm correction; at
  fifteen, it comfortably can.
- **No hardware counters or allocation profiles.** Now the clearest instrumentation gap, because
  the campaign has found a real memory difference that it cannot explain. **The tooling for both
  exists as of Aug 2026** (`bench/counters.sh`, `bench/alloc_profile.sh`, with their parsers
  self-tested so neither is first exercised on the testbed); what is missing is a host that can
  run them. Neither works under WSL2: there is no hardware PMU, and the allocation profile needs
  a prof-enabled jemalloc, which is present here but has no `jeprof` to symbolise with.
- **p99.99 and jitter were promised but not measured.** Chapter 5 said tail percentiles
  "(p99, p99.9, p99.99)" were read from the HDR histograms and §8.6 said RQ1 was answered partly
  with jitter, while the harness emitted neither and discarded the histograms, so neither could
  be recovered from a finished campaign. Fixed at the source in Aug 2026: both are emitted, the
  histograms are persisted per run so the far tail can be pooled across repeats (a single run's
  p99.99 rests on ~17 observations), and §8.6 now states plainly that the two metrics are
  instrumented but not yet reported because the reported campaign predates them. This was a
  claim-versus-evidence gap in criteria 4 and 6, not only a missing measurement.

---

## Criterion 4 — Presentation of thesis results

**Grade 4 → 4.5.** Every presentation defect is fixed and RQ3 now has a positive finding
instead of a null. RQ1 still does not.

### What was already strong

Chapter 7 is organised research question by research question, each with hypothesis, procedure,
and result. Illustration is a genuine strength: around twenty figures, most of them
purpose-drawn conceptual diagrams that carry argument rather than decorate, with self-contained
captions. Table 7.1 instructs the reader to read it "at two different levels of confidence" and
then separates them, which is a model of honest presentation.

Reproducibility is excellent and rare at this level: every figure, table, and quoted summary
number regenerates from the raw logs through one script into `figures/gen_macros.tex`, so prose
and data cannot drift apart.

### Changed in the refinement pass

- **Three stale figures that contradicted the results tables are corrected and re-rendered.**
  Figure 3.2 now shows both boundary classes with their own marker, rather than labelling
  lock-order deadlock as not injected while Table 7.3 injects it. Figure 5.2 says seven defect
  classes and `rustc 1.97`, not five and `1.96`.
- **A genuine new result.** The paired test found a language effect on peak resident set size
  that the eyeball reading had missed — see the section below.
- **Cyclomatic complexity gives Section 6.4.7 quantitative backing.** Rust is 19% longer in code
  lines but 15% lower in total complexity, and the C++ `worker_loop` scores 13 against Rust's
  worst of 6. That is the tagged-struct dispatch of Section 6.4.5 showing up as a number, in the
  one function where branching is hardest to review.
- **Figure 3.3 no longer asserts a finding the study did not obtain.** It previously claimed
  both languages track the overload cliff closely with differences only in the far tail. It is
  now labelled a schematic and framed as the open question of RQ1.
- **Figure 7.7's "129,318× cheaper" is now "roughly five orders of magnitude"**, matching the
  prose and dropping precision that two noisy microbenchmarks cannot support.

### What still blocks a 5

RQ1 still has no positive result, and Figures 7.1 and 7.3 still report that the curves cannot be
separated. Same blocker as criterion 3, and it lifts with the same campaign.

---

## Criterion 5 — Discussion and conclusions

**Grade 5, unchanged.** The strongest chapter in the thesis.

Section 8.6 is a full four-way validity analysis — internal, construct, conclusion, external —
each with named threats, stated mitigations, and an explicit account of residual risk. On
single-author skill asymmetry it concludes "the honest statement is that it is mitigated, not
eliminated", which is the right register.

The refusal to over-read the data is the single best thing in the thesis: *"The correct
conclusion is therefore not 'the languages are equivalent in the tail' but 'this measurement
cannot tell'."* Most theses in this position would have claimed equivalence and been wrong.

H2 is partially refuted by the author's own evidence — accepted for memory safety and data-race
freedom, rejected for concurrency correctness at large, with the observation that the loose
reading "is the reading practitioners tend to assume".

The central conclusion is a genuine reframing rather than a restatement: *"Rust eliminates data
races, not race conditions, and aliasing errors, not lock-ordering errors."* Section 8.7 goes
past data-protection compliance into professional responsibility, noting that migration cost
"was relocated from run time to human effort rather than removed".

**Changed in the refinement pass.** Section 8.6 no longer says no formal significance test is
applied. It now explains something more sophisticated: the peak-RSS effect has an uncorrected
*p* pinned at the 0.016 floor and a Holm-adjusted *p* of 0.188, yet its interval sits far from
zero, so the two instruments disagree. The chapter says which to trust and why. It also names
how the two limitations interact: pairing removes interference common to a repeat, which is why
a run-level statistic like peak RSS survives a shared host, but it cannot remove interference
landing on one run and not its partner — which is exactly where the tail percentiles live.

---

## Criterion 6 — Academic text

**Grade 4 → 5.**

The prose is precise, unhedged, and free of padding, with argumentation that is explicit and
consistently signposted. Referencing is consistent and correctly formatted throughout, including
proper institutional attribution of the five Ericsson master's theses.

### Changed in the refinement pass

- **The figure-versus-text contradictions are resolved.** These were the concrete thing costing
  this criterion, because a figure that contradicts a results table invites doubt about
  everything around it.
- **Section 3.3 no longer restates Section 2.2.** It points back for the general argument and
  contributes only what is specific to the RAN, cutting about half the section and removing a
  duplicated paragraph heading.
- **The contents page is down from 100 entries to 75.** It was listing 25 paragraph headings,
  several of them full sentences such as "Do not generalise these performance results past their
  evidence", turning the contents into a second outline competing with the real one. Note that
  `titlesec` ignores `\setcounter{tocdepth}` in this document, so the entries are suppressed
  where they are typeset, via `\l@paragraph`.
- **Broke up the worst sentences.** The future-work paragraph was one 204-word sentence chaining
  seven directions with semicolons, and is now an itemised list. Two related-work citation chains
  of 110 and 87 words are now two or three sentences each.

### Housekeeping left

- Fill `\censors{}{}{}` on the title page once the faculty assigns examiners. A `TODO` marker is
  in the source.
- Swap the reconstructed `UH_DS_MSc.cls` for the official one before submission.

---

## The result the new analysis turned up

Adding the paired test was meant to close a methodological gap, but it also found something.
Peak resident set size is the one metric in the campaign whose intervals separate the four
variants cleanly, and two effects are present in it rather than one. They are close to additive,
and the language effect is the larger.

| Variant | Peak RSS (MiB) | 95% CI | Decomposition |
| --- | ---: | --- | --- |
| C++ (system alloc) | 8.4 | [8.2, 8.6] | baseline |
| C++ (jemalloc) | 11.2 | [11.1, 11.4] | +2.9 allocator |
| Rust (system alloc) | 11.8 | [11.6, 11.9] | +3.4 language |
| Rust (jemalloc) | 14.6 | [14.5, 14.9] | +2.9 allocator, +3.4 language |

The sign is identical in all seven repeats, which is why the uncorrected *p* sits exactly at the
0.016 floor the design allows. The thesis previously reported that resource use "follows the
allocator rather than the language"; that has been corrected throughout Chapters 7, 8, and 9 and
in the abstract. It follows both, and the language slightly more.

The finding is bounded three ways in the text so it is not oversold: it is fixed cost rather
than per-context (the measured `UeContext` layout difference accounts for roughly 40 kB at 5000
active UEs, three orders of magnitude short of the gap); it is unexplained without counters; and
it must not be read as isolating Rust's safety model.

Whether it survives more repeats is a named item to re-check after the bare-metal run.

---

## Files changed in the refinement pass

| File | What changed |
| --- | --- |
| `bench/plot_figures.py` | Exact paired permutation test, Holm correction, asymmetric bootstrap intervals, order-of-magnitude FFI ratio, new significance table and macros. |
| `bench/complexity.py` | New. Measures lines of code and cyclomatic complexity over both cores with one tool; emits `tab_complexity.tex` and `gen_complexity.tex`. |
| `bench/refresh_thesis.sh` | Runs the complexity pass too, so one command still regenerates everything. |
| `diagrams/13_defect_families_tree.svg` | Both boundary classes added with their own marker; legend corrected from five classes to five plus two. |
| `diagrams/14_fault_injection_method.svg` | Seven classes not five, `rustc 1.97` not `1.96`, and the outcome box no longer claims every case is a compile error. |
| `diagrams/15_overload_cliff.svg` | Dropped the unsupported claim that both languages track the cliff; stale load annotations replaced with qualitative labels. |
| `Ha_Vien_Mastersthesis_2026.tex` | New significance and complexity tables with their discussion; corrected RQ3 finding in Chapters 7, 8, 9 and the abstract; Section 5.5 rewritten; 3.3 and 4.1 de-duplicated; contents trimmed; long sentences broken up. |
| `bibliography.bib` | Added the `lizard` tool entry. |

Verified by full rebuild: 105 pages, zero LaTeX errors, zero undefined references or citations,
and `bench/refresh_thesis.sh` completing end to end. The one remaining overfull box is on the
abstract page and is present in the pre-refinement build as well.

---

## Remaining checklist

1. **Run the bare-metal campaign** (`bench/TESTBED.md`, provisioned by `bench/setup_testbed.sh`).
   The only real blocker. Use more than seven repeats: the exact paired test cannot return a *p*
   below 2/2ⁿ, so at seven nothing survives Holm correction however large the effect, while at
   fifteen it comfortably can. Then run `bench/refresh_thesis.sh`.
2. **Add hardware counters and allocation profiles** on the same testbed visit. Now the clearest
   instrumentation gap, because the study has found a memory difference it cannot explain.
3. **Re-check the four claims shaped by this dataset** (also listed at the end of `TODO.md`): the
   "not yet measurable" tail verdict, the peak-RSS effect, the evidence-status column in
   Table 8.1, and H1's half-answered disposition in Section 8.3.
4. **Two submission items**: fill the examiner field, and swap in the official `UH_DS_MSc.cls`.

> The abstract box is full to the line. Any addition pushes the ACM CCS block into the Keywords
> row, so check page 3 visually if you edit it.

---

## Second pass

An independent re-read graded criteria 3 and 4 at 4 rather than 4.5, arguing that three
criticisms were answerable on the dataset already in hand rather than only on bare metal. All
three were then addressed, and two further measurements were added. Both criteria now stand at
4.5, held there solely by the bare-metal tail campaign.

The unexpected part is that closing methodological gaps changed conclusions rather than merely
firming them up.

### What was done

1. **The campaign was re-run at 15 repeats** (480 runs, same host). The exact paired test floors
   at 2/2ⁿ, so at 7 repeats the Holm-corrected floor sat at 0.1875 and *no* result could reach
   significance whatever its size. At 15 the corrected floor is 0.00061. Three results now clear
   it. Nothing about WSL2 had forced the low count.
2. **The end-to-end latency was decomposed** into the operation and the cross-thread handoff, in
   both languages, by a new harness (`bench/latency_budget.sh` plus a program per language)
   calling `ShardCore` directly and then `Service`. This is the single most consequential
   addition; see below.
3. **RQ4's claim was replaced by the experiment it needed.** "No measurable per-call tax" had
   rested on an empty crossing set against a full round-trip, which is two different
   experiments. `ffi/build.sh` now interleaves 15 repeats of the same signaling operation called
   natively and through the seam. Paired difference −179 ns, interval [−2583, +594], bounding any
   tax at 1.37% of an operation. A single unpaired pass of each, run first, had made the seam
   look *faster* than calling natively, which is why the interleaving is not optional.
4. **The interval-versus-p-value rule is pre-committed** in §5.5 instead of applied after the
   fact, and `tab:significance` is blocked by it. On the 7-repeat data two tail intervals
   excluded zero and went undiscussed while the same reading promoted peak RSS; at 15 repeats
   neither survives, which is evidence for the rule rather than an excuse for the old text.
5. **The allocator control is now also a replication check.** A language effect should keep its
   sign whichever allocator is linked. Only peak RSS does.
6. **Two vacuous tests were dropped** from the Holm family (throughput at a below-saturation
   operating point is pinned to offered load by construction), 12 tests down to 10.

### Three conclusions changed

| Claim | Before (7 repeats) | Now (15 repeats + decomposition) |
| --- | --- | --- |
| Peak RSS | 3.4–3.5 MiB, Holm p = 0.188, "language effect is the larger of the two" | 2.1–2.5 MiB, Holm p = 0.00061, **allocator effect is the larger**; reproduces under both allocators |
| CPU | "no penalty, intervals span zero" | +27.4 pp and clears Holm under the system allocator, reverses under jemalloc: reported as **unresolved** |
| Median latency | a null result about the languages | a null about the **design**: the operation is 0.04% of the measured cost |

### The decomposition, and why it matters

| Component | C++ | Rust | paired *p* |
| --- | ---: | ---: | ---: |
| Operation alone, no queue in the path | 19.0 ns | 10.0 ns | 0.00024 |
| Cross-thread submit-and-complete handoff | 43.30 µs | 43.13 µs | 0.729 |
| End-to-end round-trip, uncontended | 43.32 µs | 43.14 µs | 0.723 |

The work the languages actually perform is **0.04%** of what the sweep measures. The paired
bound on the median difference is therefore 2654× the operation's own cost, which means the
sweep never bounded a language effect at all — a fact no repeat count and no bare-metal host
would have fixed, because it is a property of what was being measured.

It also produced the campaign's only resolved difference in *time*: on the operation alone Rust
is ~1.9× faster (p = 0.00024, non-overlapping intervals). The most likely cause is already in
the forced-idiom log — `std::unordered_map` is node-based by standard requirement while Rust's
`HashMap` is open-addressed — and the thesis says so while noting that confirming it needs
cache-miss counters. Nothing here implicates the borrow checker, and the text says that too.

### Where this leaves the thesis

Chapter 7's results subsection was split into four (§7.5.1 performance, §7.5.2 the budget,
§7.5.3 the sweep figures, §7.5.4 resources), and every claim the new data touched was rewritten:
abstract, §1.6, Table 8.1, the per-RQ discussion, H1 and H3, conclusion validity, the guidelines,
and Chapter 9. H1 is now recorded as *ambiguous in its framing* rather than half-answered,
because "performance-equivalent" turned out to name two quantities that answer differently.

Build verified: 113 pages, zero LaTeX errors, zero undefined references or citations,
`bench/refresh_thesis.sh` clean end to end, abstract page checked visually after the CCS block
overflowed on first attempt.

### Left over

- **The bare-metal campaign.** The only substantive item, and narrower than before: the repeat
  count is no longer binding and the end-to-end sweep is now known not to be the instrument for
  the language question, so what the testbed buys is specifically the tail and the overload cliff.
- **Hardware counters and allocation profiles**, which two results now need rather than one: the
  peak-RSS effect is significant but unexplained, and the operation-level gap rests on a
  plausibility argument.
- **Two submission items**: `\censors{}{}{}` and the official `UH_DS_MSc.cls`.

---

## Third pass — 14 August 2026

Re-read of the thesis source and PDF against the same six-criterion matrix. Source:
full document (Chapters 1–9, abstract, tables, generated macros in `figures/gen_macros.tex`),
plus spot-check of `spec/`, `bench/`, `faults/`, `ffi/`. Build: `latexmk -pdf Ha_Vien_Mastersthesis_2026.tex`
up to date (last PDF 13 Aug 2026).

### Summary (current)

| Criterion | Second pass | Third pass | Notes |
| --- | --- | --- | --- |
| 1. Thesis objective and research questions | 5 | **5** | Unchanged |
| 2. Scholarly framework and use of sources | 5 | **5** | Unchanged |
| 3. Research data and method | 4.5 | **4.5** | Method still at 5; data improved but tail blocker remains |
| 4. Presentation of thesis results | 4.5 | **4.5** | More resolved results; one RQ1 half still open |
| 5. Discussion and conclusions | 5 | **5** | Unchanged |
| 6. Academic text | 5 | **5** | Unchanged |
| **Overall (unweighted mean)** | **4.8** | **4.8** | |

### What changed since the second pass

1. **Measurement host upgraded.** §7.1 no longer reports a WSL2 development laptop. Results are
   from a dedicated dual-socket Xeon E5-2680~v4 KVM guest on Rocky Linux~8.10, with
   `taskset` pinning, seven shards/producers, and environment capture per run. Run-to-run p99
   dispersion fell by more than an order of magnitude versus the earlier pass. This is a material
   improvement in instrument quality, but the host is still virtualised: CPU steal is non-zero,
   frequency/turbo are host-controlled and unobservable from the guest, and `isolcpus` was not
   used. Table~\ref{tab:testbed} states this plainly.
2. **Repeat count raised to 20** (`\NRepeats{}` in `figures/gen_macros.tex`; 1,120 runs total).
   The Holm-corrected floor is now 0.000027; nine comparisons clear it.
3. **Evidence status is more differentiated.** Chapter 7 opens by listing six resolved findings
   (taxonomy, FFI, RSS, operation budget, median below saturation, overload past saturation) and
   one unresolved (far tail below saturation). Table~\ref{tab:findings} carries the same split.
   The overload divergence (C++ sustains $\OverloadThrRatio\times$ Rust throughput at
   $\OverloadLoad$~kops/s) is now a resolved, Holm-significant result on this host—not merely
   preliminary.
4. **Blocker narrowed.** Bare metal is no longer needed to establish the saturation knee, overload
   ordering, or allocator/language RSS decomposition. It is still needed for **far-tail ordering
   below saturation** and for **hardware counters / allocation profiles** (unavailable in the
   guest). A **contended-queue microbenchmark** is named as the missing instrument for the
   overload *mechanism* (construct-validity gap, not a missing measurement).

### Criterion notes (third pass)

**1 — Grade 5.** Gap, RQs, hypotheses, traceability tables (5.1–5.2), and contributions remain
exceptionally tight. The introduction's §1.6 already states the dual division (instrument vs
regime) that the evidence later forces—graduate-level framing.

**2 — Grade 5.** §4.1 search protocol is auditable. §2.8 gap map and §8.5 related work engage
contrary evidence (Arvidsson, Emmerich) honestly. Optional soft spot now one load-bearing arXiv
cite (`Bugden`); the deadlock cite was upgraded to its peer-reviewed journal version.

**3 — Grade 4.5.** Methodology (§5.5–5.6) is among the strongest parts of the thesis: pre-committed
interval-vs-$p$ rule, Holm family design, exact permutation test, allocator replication check,
vacuous-test exclusion, latency decomposition as a second instrument. **Data** still cannot reach 5:
virtualised host blocks far-tail claims; counters and allocation profiles absent; overload
attribution argued via forced-idiom log, not microbenchmarked.

**4 — Grade 4.5.** Presentation is excellent: RQ-by-RQ structure, generated tables/macros,
two-level reading of Table~\ref{tab:latency}, schematic vs measured figures corrected. RQ1's
high-percentile half remains honestly "unresolved on this host." That single gap keeps this
criterion at 4.5 alongside criterion 3.

**5 — Grade 5.** §8.6 four-way validity, Table~\ref{tab:threats}, Figure~\ref{fig:threats},
hypothesis revision (H1 ambiguous in framing), and the refusal to equate "cannot tell" with
"equivalent" remain the thesis's strongest register.

**6 — Grade 5.** Prose is precise and signposted; abstract reflects current evidence (virtualised
host, overload qualification). Housekeeping unchanged: `\censors{}{}{}`, official class file.

### Priority actions to reach 5 on criteria 3 and 4

1. Execute `bench/TESTBED.md` on bare metal (or Nokia lab host)—target: far tail below
   saturation; counters and allocation profiles on the same visit.
2. ~~Run contended-queue microbenchmark~~ **Done** (§\ref{sec:contention}): primitives alone
   do not reproduce overload ordering; further attribution is in the full handoff path.
3. Re-run `bench/refresh_thesis.sh`; re-read §7.5.1, Table~\ref{tab:findings}, §8.3 H1, and
   abstract.
4. Submission housekeeping: examiners on title page, official `UH_DS_MSc.cls`.

---

## Fourth pass — 17 August 2026

Graded against the **official seven-area CSM matrix** (9 April 2024) rather than the
six-criterion simplification used above, and **from `Ha_Vien_Mastersthesis_2026.tex` alone** — no artefact
directories, nothing the code would prove that the text does not say. Canvas:
`~/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-aug17.canvas.tsx`.

| Area | Third pass | Fourth pass | Note |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | RQ1 names metrics the results do not deliver |
| 2. Scholarly framework and sources | 5 | **5** | Unchanged |
| 3. Research data and method | 4.5 | **4.5** | Method at 5; data still host-bound |
| 4. Presentation of results | 4.5 | **4.5** | Unchanged |
| 5. Discussion and conclusions | 5 | **5** | Three over-reaching phrases, now softened |
| 6. Academic text | 5 | **4.5** | See below — disagreement with the third pass |
| 7. Work during the thesis process | — | **not assessable** | Supervisor and instructors decide it |
| **Mean of the six assessable** | 4.8 | **4.75** | |

### Why area 6 moved down

The level-5 descriptor asks for a presentation that is *technically camera-ready* with
*excellent finishing polish*. The writing meets it; the finishing did not. `ai_statement.tex`
asserted that the abstract was written unaided while an invisible comment recorded that it was
model-drafted, so the printed declaration was false about the one artefact where the rule is
absolute (the summary doubles as the maturity test). Alongside that: a float overflowing its
page, two overfull boxes, sentences of 93 and 86 words, and one passage explained twice from
scratch. Area 6 returns to 5 once the abstract is rewritten unaided.

**Discounted as a false positive:** a mechanical pass flagged ~40 "inconsistencies" of the form
*memory-safety* vs *memory safety* and *compile-time* vs *compile time*. English hyphenates those
compounds attributively and leaves them open otherwise; the thesis does this correctly.

### Fixed in this pass

- **`ai_statement.tex` can no longer assert an untrue claim.** The sentence about the abstract is
  gated on `\ifabstractunaided`, default false. Until it is set the statement says plainly that
  the abstract has not been rewritten unaided, and **every build prints a warning**
  (`ai_statement: ... Not submittable`). Both documents that share the file are covered:
  `Thesis_v2.tex`'s abstract is still a placeholder.
- **The jitter and p99.99 gap is now stated in §"Performance (RQ1, RQ3)"** where the results are,
  not only in the threats section a chapter later. The threats entry was trimmed to point back
  instead of repeating the mechanism, and its internal contradiction removed: it previously
  listed jitter among the metrics answering RQ1 and then said jitter was unreported.
- **Three over-reaching phrases softened.** "Equivalent for any purpose a deployment would care
  about" now scopes to central behaviour and says the equivalence does not extend to the far tail;
  "the guarantee is absolute" now pins what it is absolute over (execution coverage, not catalogue
  breadth); "decision-grade" is gone from the conclusion.
- **Layout:** zero overfull boxes and zero floats too large, down from two and one.
  `tab:overloadtest` wraps its first column; the H1 description label was shortened; one
  threats-table cell trimmed.
- **Copy-edit:** the 93-word and 86-word sentences split; the coordinated-omission explanation in
  the methodology now relies on its Chapter 2 definition instead of restating it;
  *signaling* → *signalling* (29, matching both the British house style and 3GPP usage);
  *sanitizer* → *sanitiser* (4, proper nouns such as AddressSanitizer left alone); one "a
  orders-of-magnitude" → "an".

Build verified on both documents: zero errors, zero undefined references or citations, zero
overfull boxes, zero floats too large. 147 pages.

### Outstanding

1. **Rewrite the abstract unaided**, then set `\abstractunaidedtrue`. Blocking, and it cannot be
   delegated — the summary is the maturity test.
2. **Bare-metal tail campaign** with counters and allocation profiles. Lifts areas 3 and 4.
3. ~~**Align RQ1's metric list** with what is reported, or report jitter.~~ **Done.** RQ1 now
   names the median, p99, p99.9 and the maximum in all three documents — `Thesis_Plan_v2.tex`,
   `Thesis_v2.tex` and `Ha_Vien_Mastersthesis_2026.tex` — which is exactly what the reported campaign delivers,
   and §8.6 states that jitter and p99.99 are instrumented but not yet reported. The question and
   the answer therefore match. Two consequences to keep in view: the change narrowed a
   supervisor-approved RQ, so it should be **flagged explicitly in the next submission** rather
   than left for the supervisor to notice; and jitter and p99.99 are now an evidence upgrade
   (`TODO.md`, "Highest-value work still available", item 2) rather than an unkept promise, so the
   argument for that re-run must not be made on promise-keeping grounds.
4. **Optional:** the use-after-free example is worked three times (introduction, background,
   appendix). Defensible layering for a reader without telecom background — left as the author's
   call rather than cut.
5. **Housekeeping:** examiners on the title page, official class file.

---

## Fifth pass — 19 August 2026

Graded against the **official seven-area CSM matrix** (9 April 2024) using
`.cursor/skills/thesis-grade-csm/`. Source: the thesis PDF (md5 `0b1afc6f…`, then still issued
as a copy of `Thesis_POC.pdf` under the submission name), plus the thesis source and the generated
artefacts under `figures/`. Build dated 18 Aug 2026 15:44 against a source of 15:34, so the
grade describes a current build. 163 pages. Standard applied: a full draft the repository does
not treat as supervisor-approved, judged as an examiner would see the manuscript. Canvas:
`~/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-aug19.canvas.tsx`.

| Area | Fourth pass | Fifth pass | Note |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | RQ1's metric list now verified against Table 7.1 |
| 2. Scholarly framework and sources | 5 | **5** | Unchanged |
| 3. Research data and method | 4.5 | **4.5** | Method at 5, data at 4; host-bound as before |
| 4. Presentation of results | 4.5 | **4.5** | Same grade, different cap — see below |
| 5. Discussion and conclusions | 5 | **5** | One conclusion verb out of step with §7.3 |
| 6. Academic text | 4.5 | **4.5** | Same grade, different cap — see below |
| 7. Work during the thesis process | not assessable | **not assessable** | No manuscript settles it |
| **Mean of the six assessable** | 4.75 | **4.75** | |

### Agreement with the fourth pass, and what changed underneath it

Every area lands on the same number. That is not the same as nothing having happened, because
the reasoning behind two of them has been replaced.

**Area 6 is at 4.5 for a different reason.** The fourth pass held it there because the printed
AI declaration was false about the abstract. That is repaired, and repaired the right way: the
sentence is gated on `\ifabstractunaided`, the switch is still false, and the PDF says plainly
"In this draft it has not yet been rewritten unaided". What holds the area at 4.5 now is that
the abstract is still unwritten, so the document declares itself not submittable, plus the §5.5
inconsistency below.

**Area 4 is at 4.5 for one old reason and three new ones.** The far tail is unchanged. The
fourth pass's caps are largely cleared: hand-typed measured values are far fewer, and the one
unreferenced float is the abbreviations table in Appendix D, which is a glossary and
conventionally not cross-referenced (discount it). In their place are three arithmetic
disagreements that were not in the 147-page build. Worth saying plainly: the work since 17
August was good, and the growth from 147 to 163 pages introduced new defects of exactly the
class the previous pass had cleared.

### What was checked mechanically

`texaudit.py` passes every hard gate: zero LaTeX errors, zero undefined references, zero
undefined citations, zero multiply-defined labels, zero overfull boxes, zero floats too large,
zero placeholders. 100 bibliography entries, all 100 cited, none uncited, 65 in peer-reviewed
venues. `.aitells.py`: zero semicolons, four dash hits all legitimate typography (one compound
proper name, three numeric ranges), sentence-length stdev 13.1 with a mean of 24.5.
`.readability.py`: longest sentence 73 words, down from the 93 the fourth pass split.

The abstract page was rendered and inspected: the form is complete, the CCS block does not
overflow into Keywords, and the declared "140 pages, 11 appendix pages" checks out against the
PDF (printed page 1 is PDF page 13, printed 140 is PDF page 152, appendices run PDF 153–163).

**Figure against table, five pairs, all agree exactly:**

| Pair | Checked | Verdict |
| --- | --- | --- |
| Fig. 7.2 / Table 7.2 | Nine filled markers, one open on peak RSS under jemalloc, four tail rows shaded | Agrees |
| Fig. 7.9 / Table 7.7 | 9.7 / 11.6 / 42.6 / 45.9 MiB; decomposition 32.9, 34.4, 1.9, 3.4 | Agrees |
| Fig. 7.7 / Table 7.5 | 117 / 62 / 115 / 63 kops/s; CPU per kops 5.25 against 10.14 | Agrees |
| Fig. 7.10 / Table 7.8 | All ten classes; TSan "sometimes" on lock-order deadlock; C++ ahead on two boundary rows | Agrees |
| Fig. 7.4 / Table 7.3 | 13.6 µs round-trip, operation at 0.250 %, blind zone at 58× | Agrees |

This is the highest-yield check in the procedure and it came back clean on every pair sampled,
down to the open marker on the one significance row that fails Holm. That is the strongest
single piece of evidence in area 4, and it is why three arithmetic slips cap the area rather
than sink it.

### Findings

1. **Table 6.4 (`tab:loc`) does not add up.** The nine per-concern rows sum to 668 on the C++
   side while the total row prints 674 (`\CppRawLines`). The deltas sum to +94 while the total
   prints +88 (`\LocGap`). The Rust column and every per-row delta are internally consistent, so
   six C++ lines are unaccounted for: either one cell reads six low, or a concern worth six C++
   lines and no Rust lines is missing from the breakdown. The caption promises to show where the
   88-line difference
   comes from by concern, and the concerns account for 94. `bench/complexity.py` carries a
   comment saying the totals were emitted "so the prose and the table cannot quote different
   totals, which they have twice" — the guard covers the total row only, and the hand-decomposed
   rows drifted underneath it. *Areas 4, 6.*
2. **The conformance campaign is reported at two sizes.** §6.7 says "a campaign of roughly
   `\ConfGenOps` generated operations" (793,000). §7.5.6 says the lifecycle defect survived
   "$223$ hand-written and $9\,006$ generated conformance operations". Both name the same suite.
   9,006 matches `run.sh` defaults (4 vectors per profile × 300 ops); 793,000 is the deep
   campaign the thesis reports. `223` is also typed by hand where `\ConfHandOps` exists.
   *Areas 4, 6.*
3. **§5.5 describes instrumentation the reported campaign did not have.** It states in the
   present tense that the harness persists each run's HDR buckets so repeats can be pooled into a
   distribution that "resolves the far tail", that "jitter is measured directly" per RFC 3393,
   and that jitter and p99.99 "are reported descriptively". Neither is reported anywhere, and
   §7.5.1 says the campaign "predates that instrumentation". The gap is disclosed in §7.5.1 and
   in construct validity, but §5.5 was never rewritten, so the description of the setup
   contradicts the results. *Areas 4, 6.*
4. **0.250 % and 99.9 % do not complement each other** (`Ha_Vien_Mastersthesis_2026.tex:2538`). The complement of
   `\BudgetCoreShareMax` is 99.75. The 99.9 figure holds only against Table 7.1's ~80 µs
   latencies rather than the 13.6 µs round-trip that 0.250 % is a share of, and the change of
   denominator is not stated. Figure 7.4 labels the operation "0.250% of the bar", which is the
   reading a checking examiner brings to the sentence. *Area 4.*
5. **The conclusion asserts the hash-map mechanism** ("for reasons that trace to the standard
   library's choice of hash-map layout") where §7.3 calls it "the single most likely source"
   needing cache-miss counters, and the future-work list says counters "would confirm or refute"
   it. One verb out of step with the other two. *Area 5.*
6. **`\abstractunaidedfalse` is still set.** Honest and correctly gated, but the document
   declares itself not submittable. *Area 6.*

### Resolved since the fourth pass

- **Official class file — done.** `HYthesisML.cls`, the Department of Computer Science's own CSM
  template, with the pristine copy kept in `CSM-thesis-template_2021_09_07/`. The reconstructed
  `UH_DS_MSc.cls` is a leftover file in the root and is no longer loaded. Strike this from the
  housekeeping list.
- **AI declaration — done.** Gated, truthful, and the build warns on every run.
- **RQ1 metric alignment — verified,** not merely marked done. RQ1 names the median, p99, p99.9
  and the maximum; `\LatencyHead` emits exactly those four columns.
- **`zhang2026deadlock` is not a preprint.** The audit flags it only because of the `note` field
  recording that it extends arXiv:2401.01114. Discount it. The one real preprint left is
  `bugden2022rust`, and it appears twice, both times beside peer-reviewed corroboration, so it
  carries no claim alone.

### Outstanding

1. **Rewrite the abstract unaided**, then set `\abstractunaidedtrue`. Blocking, cannot be
   delegated.
2. **Fix the three arithmetic disagreements** (findings 1, 2, 4). Minutes each, and they are the
   cheapest defects an examiner can find.
3. **Put §5.5's pooling, jitter and p99.99 sentences in the conditional** so the setup
   description matches §7.5.1. About an hour.
4. **Soften "trace to" in the conclusion** to match §7.3. One word.
5. **Bare-metal tail campaign** with hardware counters and allocation profiles on the same visit.
   Unchanged in scope. The only item that needs an instrument the author does not have, and the
   only thing holding areas 3 and 4 at 4.5.
6. **Housekeeping:** `\censors{}{}{}` once the faculty assigns examiners.
7. **Unrealised asset:** `figures/tab_equivalence.tex` is generated on every refresh and never
   `\input` by any document. Its data reaches the page through the `\EqvBound*` macros, so
   nothing is missing from the argument, but the table itself earns nothing where it sits.
   Either place it in the results or drop it from the build.

## Sixth pass — 19 August 2026, afternoon

Graded against the **official seven-area CSM matrix** (9 April 2024) using
`.cursor/skills/thesis-grade-csm/`. Source: `Ha_Vien_Mastersthesis_2026.tex`, its 16:31 build, the
generated artefacts under `figures/`, and the published evidence under `faults/results/`,
`spec/conformance/results/` and `ffi/results/`. Source, PDF and log all carry the 16:31 timestamp,
so the grade describes a current build. Standard applied: a full draft the repository does not
treat as supervisor-approved, judged as an examiner would see the manuscript. Canvas:
`~/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-aug19-rev2.canvas.tsx`.

**This is a different document from the one the fifth pass graded seven hours earlier**: 113 PDF
pages against 163, 99 declared body pages against 140, 105 bibliography entries against 100. The
length work landed between the two passes.

| Area | Fifth pass | Sixth pass | Note |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Unchanged |
| 2. Scholarly framework and sources | 5 | **5** | 105 entries, all cited, 69 peer-reviewed (66%) |
| 3. Research data and method | 4.5 | **4.5** | Method at 5, data at 4; host-bound as before |
| 4. Presentation of results | 4.5 | **4.0** | Hand-typed values verified against the artefacts and three disagree |
| 5. Discussion and conclusions | 5 | **5** | Unchanged |
| 6. Academic text | 4.5 | **4.5** | Same cap: abstract unwritten, §5.5 in the indicative |
| 7. Work during the thesis process | not assessable | **not assessable** | No manuscript settles it |
| **Mean of the six assessable** | 4.75 | **4.67** | |

### Where this pass disagrees with the fifth, and why

Five areas land on the same number for the same reasons, and the fifth pass's reasoning stands.
Area 4 moves down half a grade, and the disagreement is about evidence rather than about judgement.

The fifth pass held area 4 at 4.5 partly because the hand-typed residue in the prose had shrunk to
a handful of values, and it verified five figure-against-table pairs, which all agreed. Both
findings still hold. What that check could not see is whether the hand-typed values are *correct*,
because none of them appears in a table. This pass checked them against the artefacts the thesis
names as their source. Three disagree. The previous 4.5 was awarded on the assumption that the
residue was accurate, so the split behind it no longer holds.

Level 4's clause, that the use of pictures, tables and drawings supports the analysis of results,
holds comfortably. Level 5's "well considered and apt" does not, while a table footnote contradicts
the CSV the same paragraph names as its generator.

### New findings, not in the fifth pass

1. **The TSan deadlock rate in the manuscript is not the rate in the artefact.** Table 7.6's
   footnote and §7.9 both say ThreadSanitizer reports the lock-order inversion in "four of twelve
   repeats here". `faults/results/taxonomy.csv` records `TSan reported in 7/12 runs`,
   `taxonomy.md` says the same, and the twelve run logs confirm it: runs 0, 1, 2, 3, 7, 8 and 9
   carry `lock-order-inversion`, the other five are empty. The control is a separate binary
   (`deadlock_control.tsan.log`), so it does not inflate the count. The same paragraph states that
   the outcomes "are generated from the runner's machine-readable log
   (`faults/results/taxonomy.csv`)", and Table 7.6 is in fact typed by hand in the `.tex` while
   only `fig_taxonomy.pdf` is generated. The finding is unaffected, intermittent detection is
   intermittent at 7/12 as at 4/12, but the number an examiner reproduces is not the number
   printed. Note that `AGENT.md` §3 also carries the stale figure ("about 30% of runs").
   *Areas 4, 6.*
2. **The lost-update counts do not match the logs.** §7.9 reports the safe-Rust program recording
   $35\,030$ of $40\,000$ increments and losing $4\,970$, against C++ under TSan recording
   $25\,448$ and losing $14\,552$. The logs, regenerated 17 August 15:00, hold 28,914 lost 11,086
   for Rust and 27,788 lost 12,212 for C++. The expected total of 40,000 matches. The thesis's
   conclusion, that both terminate with a silently wrong answer, survives either set, but the
   three-to-one asymmetry the printed figures imply becomes near-parity in the data, and the
   printed figures cannot be reproduced from the published artefacts. *Areas 4, 6.*
3. **§7.5.1 makes a claim its own table refutes.** "At the median the four variants sit within
   $\PFiftyRange\,\mu$s of one another, or $\PFiftySpread\%$, and each variant's confidence
   interval contains the others' point estimates, so the table on its own separates nothing." From
   `figures/tab_latency.tex`: C++ system 79.9 [79.6, 80.7], C++ jemalloc 80.3 [79.4, 80.7], Rust
   system 79.0 [78.7, 79.7], Rust jemalloc 78.6 [78.1, 79.7]. No interval contains a
   cross-language median. They do all overlap, which is the weaker claim the argument actually
   needs. Figure 7.6(b) reports the opposite of the sentence and is right: at the median the spread
   between variants (1.7 µs) exceeds the widest single interval (1.6 µs), which is the regime in
   which an ordering means something. One word, "contains" to "overlaps", fixes it. *Areas 4, 6.*
4. **§7.2's self-description is falsified by the five hand-typed values.** "No value is
   hand-copied: `bench/refresh_thesis.sh` regenerates every figure, table, and quoted number
   directly from the raw logs, so the text and the data cannot drift apart." Five quoted numbers
   are outside that pipeline and three of them have drifted. The claim should be narrowed to what
   is true and impressive on its own, that every campaign statistic reaches the page through a
   generated macro. *Areas 4, 6.*
5. **Jitter is named in the abstract and never reported.** The abstract lists "tail latency and
   jitter under overload" among the four dimensions average-throughput comparisons leave open.
   RQ1 does not name jitter, no jitter figure appears anywhere, and §7.5.1 records that the
   campaign predates the instrumentation. This is the abstract-level face of fifth-pass finding 3.
   *Area 6.*

### Confirmed against the artefacts, and clean

- **FFI evidence intact.** `ffi/results/metrics.json` matches every `\Ffi*` macro: crossing 2.535
  → 2.54 ns, native 12,284.4 → 12.3 µs, seam 12,673.4 → 12.7 µs, delta +192.5 → +192 ns, interval
  [−953.9, +1340.8] → [−954, +1341], p 0.2395 → 0.239, bound 1340.8/12284.4 = 10.91 %. The 63 µs
  noise run `AGENT.md` §5 warns about has not overwritten it.
- **Conformance size.** `spec/conformance/results/summary.json` holds 792,964 operations, so
  `\ConfGenOps` (793,000) is right and the hand-typed 9,006 in §7.9 is the wrong figure of the two.
- **Taxonomy table against CSV, all ten rows.** Every sanitiser cell and every Rust outcome agrees
  with `taxonomy.csv`. Only the intermittency rate disagrees.
- **Model checking.** Loom and Shuttle report both boundary defects and both controls come out
  clean, exactly as §7.9 states.
- **Statistics, recomputed.** 9 of 14 tests survive Holm (five below saturation: both p50 rows,
  peak RSS under the system allocator, both CPU rows; plus the four overload rows), matching
  `\NSignificant`. Ten paired intervals exclude zero and none of them is in the tail block,
  matching `\NExclZero` and `\TailExclZeroRows`. CPU per sustained operation is 1.93 and 1.89
  across the allocators, matching `\OverloadCpuPerOpRatio` of 1.9. Peak-RSS decomposition 32.9 to
  34.4 MiB for the allocator against 1.9 to 3.4 MiB for the language, both as printed.
- **Abstract page rendered and inspected.** The form is complete at 113 pages, the CCS block does
  not overflow into Keywords, and it declares 99 pages with 6 appendix pages, matching the `.aux`.
- **Build gates.** Zero LaTeX errors, undefined references, undefined citations, multiply-defined
  labels, overfull boxes, floats too large, placeholders. Zero semicolons. Four dash hits, all
  legitimate typography. Sentence length 24.3 ± 13.0 words.

One rounding nit worth a look in the generator rather than the prose: §7.7 says the overload
paired difference is "at least $\OverloadThrBound$~kops/s under either allocator", where the
weaker interval bound is 49.6 and `\OverloadThrBound` rounds it up to 50. For a claim of the form
"at least", `bench/plot_figures.py` should floor rather than round.

### Nothing was changed in the thesis during this pass

The pass graded and did not edit. Every item below is still open in the source.

### Outstanding, cheapest first

1. **Quote the deadlock rate and the lost-update counts from the fault artefacts**, or regenerate
   those sentences from `taxonomy.csv` and the logs. Under an hour, and it closes the only place
   where the manuscript disagrees with published evidence rather than with itself. Update
   `AGENT.md` §3's "about 30% of runs" in the same edit.
2. **Replace the hand-typed `9\,006` with `\ConfGenOps`** and the hand-typed `223` with
   `\ConfHandOps` (`Ha_Vien_Mastersthesis_2026.tex:3073`). Minutes.
3. **Repair the p50 sentence** in §7.5.1: the intervals overlap, they do not contain one another's
   medians. One word.
4. **Find the six missing C++ lines in Table 6.4**, or say in the caption what the breakdown
   omits. Under an hour.
5. **Put §5.5's pooling, jitter and p99.99 sentences in the conditional**, and either drop jitter
   from the abstract's list of open dimensions or mark it as future work. About an hour.
6. **State the denominator behind the 99.9 %**, since 0.250 % is a share of the 13.6 µs round-trip
   while 99.9 % is a share of the sweep's ~80 µs latencies. Both are true and the pairing reads as
   an arithmetic slip. One clause.
7. **Narrow §7.2's "no value is hand-copied"** to the claim that is both true and strong: every
   campaign statistic reaches the page through a generated macro.
8. **Soften "trace to" in the conclusion** (line 4151) to match §7.3's "most likely source". One
   word.
9. **Rewrite the abstract unaided**, then set `\abstractunaidedtrue`. Blocking, cannot be
   delegated. In the same pass, drop "median latency matches": the paired test resolves a 1.6 µs
   median difference under both allocators that clears the Holm correction, and Chapter 8 states it
   correctly as a difference no deployment would notice.
10. **Unrealised asset:** `figures/tab_equivalence.tex`, still generated on every refresh (15:50
    today) and still `\input` by no document.
11. **Bare-metal tail campaign** with hardware counters and allocation profiles on the same visit.
    Unchanged in scope, and the only item editing cannot reach.
12. **Housekeeping:** `\censors{}{}{}` once the faculty assigns examiners.

---

## Seventh pass — 20 August 2026

Graded against the **official seven-area CSM matrix** (9 April 2024) using
`.cursor/skills/thesis-grade-csm/`. Source: `Ha_Vien_Mastersthesis_2026.tex`, its 09:52 build, the
generated artefacts under `figures/`, and the published evidence under `faults/results/` and
`ffi/results/`. Source, PDF and log all carry the 09:52 timestamp, so the grade describes a current
build. Standard applied: a full draft the repository does not treat as supervisor-approved, judged
as an examiner would see the manuscript. Canvas:
`~/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-aug20.canvas.tsx`.

**Every finding was re-derived from the artefacts in this pass rather than inherited from the
sixth**, because the sixth pass moved a grade on the strength of them and a grade that rests on
another pass's arithmetic is not a grade.

| Area | Sixth pass | Seventh pass | Note |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Unchanged. RQ1's four named metrics match Table 7.1's four columns exactly |
| 2. Scholarly framework and sources | 5 | **5** | Unchanged. 105 entries, all cited, 69 peer-reviewed (66%) |
| 3. Research data and method | 4.5 | **4.5** | Method at 5, data at 4. Host-bound as before |
| 4. Presentation of results | 4.0 | **4.0** | Held, and now firm rather than provisional: the defects behind it are a pass old, untouched, and there are eight of them rather than five |
| 5. Discussion and conclusions | 5 | **5** | Unchanged |
| 6. Academic text | 4.5 | **4.5** | Same two failing clauses (abstract not yet unaided, §5.5 in the indicative), plus a newly named surface: about twenty dash asides and prose semicolons in diagram labels |
| 7. Work during the thesis process | not assessable | **not assessable** | No manuscript settles it |
| **Mean of the six assessable** | 4.67 | **4.67** | |

### The finding of this pass is that there is no new finding

Every area lands where the sixth pass put it, for the same reasons, and this pass agrees with all
seven. The document has not been edited on any graded point since. `git status` is clean, and the
only commit touching the thesis source after `19b276c` recorded the sixth pass is `d5fc423`
*Strip template scaffolding comments from thesis source and regenerate PDF*, which changed no
prose that any item names. The `.tex` mtime moved to 09:52 today without a content change.

Of the sixth pass's twelve outstanding items, **all twelve are untouched**:

| # | Item | Status |
| --- | --- | --- |
| 1 | Deadlock rate and lost-update counts quoted from the artefacts | Still open, both places |
| 2 | Hand-typed conformance sizes replaced by macros | Still open. `$9\,006$` and a hand-typed `$223$` both survive at L3051–3052, beside the correct `\ConfGenOps` and `\ConfHandOps` use at L2110–2115 |
| 3 | p50 sentence repaired from "contains" to "overlaps" | Still open |
| 4 | Six missing C++ lines in Table 6.4 | Still open |
| 5 | §5.5's pooling, jitter and p99.99 sentences in the conditional | Still open |
| 6 | Jitter dropped from the abstract's open dimensions | Still open |
| 7 | Denominator behind the 99.9 % stated | Still open |
| 8 | §7.2's "no value is hand-copied" narrowed | Still open |
| 9 | "Trace to" softened in the conclusion | Still open |
| 10 | Abstract rewritten unaided, switch set | Still open, blocking for a third pass |
| 11 | `figures/tab_equivalence.tex` placed or dropped | Still open |
| 12 | Bare-metal tail campaign | Still open |

That does not change area 4's number, and it does change what the number means. A defect found in a
pass is a discovery. A defect that survives a pass is a finishing failure, which is the clause
area 6 is held on as well. So 4.0 is no longer provisional on "the residue might be accurate": it
has been checked twice from two directions, and the second check found three more wrong values
rather than fewer. Level 4's clauses still hold, which is why the area does not fall further: the
defects are localised values and labels, not a failure of the reporting logic, and the generated
pipeline that carries every campaign statistic is untouched by any of them.

### Re-derived independently, and the sixth pass was right on all five

1. **TSan deadlock rate.** Line 2990 prints "four of twelve repeats here" and the Table 7.6
   footnote prints "$4$ of $12$". `faults/results/taxonomy.csv` records
   `TSan reported in 7/12 runs` and `taxonomy.md` says the same. Confirmed. `AGENT.md` §3 has
   since been corrected to 7 of 12 and now flags the prose as stale, so the repository and the
   manuscript disagree in the manuscript's disfavour.
2. **Lost-update counts.** Lines 2969 to 2971 print 35,030 recorded and 4,970 lost for safe Rust
   against 25,448 and 14,552 for C++ under TSan. The logs read
   `messages_handled=28914 expected=40000 lost=11086` and
   `messages_handled=27788 expected=40000 lost=12212`. Confirmed. Both printed pairs sum to
   40,000, which is why they look reproducible and are not. The printed figures imply Rust loses
   roughly a third of what C++ loses; the logs put them within ten percent of each other.
3. **Table 6.4.** The nine concern rows sum to 668 in the C++ column against a printed
   `\CppRawLines` of 674, and the delta column sums to +94 against a printed +`\LocGap` of 88.
   The Rust column sums correctly to 762, so the six lines are missing from the C++ breakdown
   alone. Confirmed.
4. **The p50 sentence.** `figures/tab_latency.tex` gives C++ system 79.9 [79.6, 80.7], C++
   jemalloc 80.3 [79.4, 80.7], Rust system 79.0 [78.7, 79.7], Rust jemalloc 78.6 [78.1, 79.7].
   No interval contains a cross-language median. All four overlap. Confirmed, and one word fixes
   it.
5. **The 99.9 % complement.** Line 2533 pairs "better than $99.9\%$" with `\BudgetCoreShareMax`
   of 0.250 two sentences above it, whose complement is 99.750 %. Confirmed. Both halves are
   true of different denominators and the pairing reads as an arithmetic slip.

### Checked in this pass and clean

- **FFI evidence after the seam-count correction.** `8244901` *Correct FFI seam counts and refresh
  generated artefacts* landed after the sixth pass, which is exactly when prose drifts from a
  rewritten artefact. All ten quantities in `ffi/results/metrics.json` agree with their macros:
  crossing 2.535 → 2.54 ns, native 12,284.4 → 12.3 µs, seam 12,673.4 → 12.7 µs, delta +192.5 →
  +192 ns, interval [−953.9, +1340.8] → [−954, +1341], p 0.2395 → 0.239, 11 entry points, 231 and
  66 lines, 9 seam `unsafe` functions against 0 in the core, and the bound recomputes to
  1340.8/12284.4 = 10.91 %. The RQ4 prose quotes nothing by hand.
- **Build gates.** Zero LaTeX errors, undefined references, undefined citations, multiply-defined
  labels, overfull boxes, floats too large, placeholder markers. 113 PDF pages, `\pagesCount` 99
  with `\appendixCount` 6, matching the abstract form.
- **Abstract page rendered and inspected at 110 dpi.** The form is complete, the CCS block does
  not overflow into Keywords, and the keyword row is intact.
- **Prose gates.** Zero semicolons in 33,425 words. Four dash hits, all legitimate (one compound
  proper name, three numeric ranges). Sentence length 24.1 ± 13.0 words, max 73, so the 93- and
  86-word sentences of the fourth pass stay gone. Two transition openers, four promotional
  adjectives.
- **RQ1's metric alignment.** RQ1 names the median, p99, p99.9 and the maximum; Table 7.1 reports
  exactly those four. The question and the answer match, and §7.5.1 states the p99.99 and jitter
  gap in the results chapter rather than only in the threats section.
- **Statistics.** `figures/tab_significance.tex` recomputed against `gen_macros.tex`: the two p50
  rows clear Holm at 0.012 and 0.00069 with effects of −1.1 and −1.6 µs, the four tail rows all
  sit at Holm 1.000, and `\NSignificant` of 9 and `\NTailExclZero` of 0 both hold.
- **Bibliography.** 105 entries, 105 cited, no uncited entry and no missing key. `bugden2022rust`
  is the one remaining arXiv item and is cited twice, both times beside a peer-reviewed source, so
  it carries no claim alone. `zhang2026deadlock` is the *Automated Software Engineering* version
  and the audit's preprint flag on it stays a false positive.

### New in this pass, not in the sixth

1. **Three more hand-typed values are wrong, so the count is eight rather than five.** All three
   are in the same paragraph region of §7.9 and none has a macro:
   - **L3051, "twenty-five Rust tests".** `cargo test --release -- --list` reports 6, 7, 5 and 9
     across the four binaries that hold tests, so the suite is **27**. The six C++ test binaries
     are right.
   - **L2957, "the three between them still leave four of the ten classes untouched".**
     `taxonomy.csv` marks `cpp_detection` as `undetected` for **two** classes, `lost_update` and
     `worker_failure_blast_radius`. The deadlock is `runtime, intermittent (TSan)`, so counting it
     as untouched gives three. No reading of the CSV yields four.
   - **L3051–3052, `$223$` and `$9\,006$` typed out** where `\ConfHandOps` and `\ConfGenOps`
     exist. The 223 is right, the 9,006 contradicts `summary.json`'s 792,964 by two orders of
     magnitude, and it is the same sentence the sixth pass flagged. **My first sweep of this pass
     reported the item closed, which was wrong**: the grep missed `9\,006` because the LaTeX thin
     space breaks a naive digit pattern. Search for `9\\,006`, not `9,006` or `9006`.
2. **The diagram labels are a reader-visible surface with no automated gate, and they breach the
   house style in about twenty places.** `.aitells.py` reads `.tex` only, and `build_deck.py`'s
   `check_prose_style` covers the slide deck only, so nothing checks the figures. Of the eleven
   diagrams the thesis includes, five carry a dash aside in a label, panel title or in-figure
   footer, fourteen occurrences in total: `17_guarantee_boundary` (5), `04_request_lifecycle_sequence`
   (4), `08_borrow_checker_uaf` (2, both panel titles), `27_workload_timeline` (2, literal `—`),
   `16_coordinated_omission` (1). Six more carry a prose semicolon in a label:
   `17_guarantee_boundary` (2), `29_research_gap` (1 subtitle plus two name lists),
   `07_ffi_seam` (1 subtitle plus one label), `12_concurrency_models` (1),
   `15_overload_cliff` (1). Editing the `diagrams/` sources and re-rendering fixes all of it, and
   the durable fix is a dash and semicolon gate over the diagram sources beside the two that
   already exist.
3. **The antithesis tic is the top prose signature in the `.tex`.** "rather than" carries 154
   sentences at 4.7 per thousand words, which `.aitells.py` scores at 44.0 per ten thousand. The
   next pattern it counts is at 1.2. Secondary: 48 of 243 multi-sentence paragraphs carry no short
   sentence, and long-then-short alternation sits at 23 % against the tool's 30 to 40 % target.
4. **Figure 8.1 (`fig:boundary`) draws two of the five boundary classes while the prose claims it
   states the whole result.** The diagram shows the lock-order deadlock and the lost update
   outside the guarantee, and its own caption says the leak, the overflow and the worker-failure
   case "sit alongside them", which is disclosure. §8.2's sentence that the figure "states the
   whole result in one picture" is the part that overreaches. The outcomes drawn agree with
   `taxonomy.csv`. One clause in the prose, or two more boxes in the diagram.
2. **The "analysis on data already in hand" lift category is now empty.** It was the whole
   substance of the second pass. Every question answerable from the existing dataset has been
   answered, so the lift list has collapsed to editing plus one testbed visit. Worth recording,
   because it means no further grade movement is available without either an hour of editing or
   the bare-metal campaign.
3. **`\censors` housekeeping is closed as written.** The `censored` class option is set in
   `\documentclass`, `\examiners` carries only the settled name, and a source comment records
   that the class prints examiners nowhere, so an unassigned second examiner cannot leak into a
   submitted PDF. Nothing to do until the faculty assigns them.

### False positives this pass burned time on, recorded so the next one does not

- **`pdftotext` on `diagrams/pdf/*.pdf` extracts nothing.** The eleven included diagrams render
  their text as paths, so a dash or semicolon check routed through `pdftotext` returns zero on
  every file and means nothing. Check the `.svg` and `.drawio` sources instead, and search for
  both the literal `—` and the `&#8212;` entity, because the sources use both.
- **Semicolons inside verbatim code in a diagram are legitimate**, which the house style says
  explicitly. `08_borrow_checker_uaf` carries five in C++ and Rust statements and
  `05_data_model` one in `[u8; 32]`. Six of the semicolon hits are therefore not defects.

### Nothing was changed in the thesis during this pass

The pass graded and did not edit. `CALIBRATION.md`'s standing blockers were refreshed to the
seventh-pass state, its stale "about 30% of runs" for the deadlock rate was corrected to 7 of 12,
and the two false positives above were added, so a future pass does not inherit a wrong figure or
repeat a vacuous check from the grading skill itself.

### Outstanding, cheapest first

Nothing from the sixth pass is closed. Three defects and one whole surface are added. The first
seven items are under three hours between them and close every place where the manuscript
disagrees with its own published evidence.

1. **Regenerate the deadlock-rate and lost-update sentences** from `taxonomy.csv` and the run
   logs. Under an hour, and the largest of the evidence disagreements.
2. **Replace the hand-typed `$9\,006$` and `$223$` at L3051–3052** with `\ConfGenOps` and
   `\ConfHandOps`. Minutes, and it removes a two-order-of-magnitude error.
3. **Fix "twenty-five Rust tests" to 27** at L3051, and **"four of the ten classes untouched" to
   two** at L2957, or to three if the intermittent deadlock is counted, in which case say so.
   Minutes each.
4. **"contains" to "overlaps"** in §7.5.1. One word.
5. **State the denominator behind the 99.9 %**, or quote the complement of
   `\BudgetCoreShareMax`. One clause.
6. **Soften "trace to"** in the conclusion to §7.3's "most likely source". One word. And soften
   §8.2's claim that Figure 8.1 "states the whole result", since it draws two of five boundary
   classes and its own caption says so.
7. **Find the six missing C++ lines in Table 6.4**, or say in the caption what the breakdown
   omits. Under an hour, and the cheapest defect an examiner with a calculator finds.
8. **Narrow §7.2's "no value is hand-copied"** to the claim that every campaign statistic reaches
   the page through a generated macro. True, strong on its own, and no longer falsifiable by
   eight values.
9. **Clear the dash asides and prose semicolons out of the diagram labels** and re-render. Five
   diagrams for the dashes, five for the semicolons, about an hour. Then **extend the style gate
   to `diagrams/`**, because this surface is the only reader-visible prose in the project that
   nothing checks.
10. **Put §5.5's pooling, jitter and p99.99 sentences in the conditional**, and either drop jitter
    from the abstract's list of open dimensions or mark it as future work. About an hour.
11. **Thin the "rather than" construction.** A careful hour, area 6 only.
12. **Unrealised asset:** `figures/tab_equivalence.tex`, still generated on every refresh and still
    `\input` by no document. It holds the equivalence-bound reading of RQ1, which is the strongest
    available answer to the half of RQ1 the host cannot resolve.
13. **Rewrite the abstract unaided**, then set `\abstractunaidedtrue`. Blocking, cannot be
    delegated, open for a third pass. Drop "median latency matches" in the same edit.
14. **Bare-metal tail campaign** with hardware counters and allocation profiles on the same visit.
    The only item editing cannot reach, and its target stays narrow: the far tail below
    saturation, plus a mechanism for the peak-RSS effect and the operation-level gap.

## Eighth pass — 22 August 2026

Graded against the **official seven-area CSM matrix** (9 April 2024) using
`.cursor/skills/thesis-grade-csm/`. Source: `Ha_Vien_Mastersthesis_2026.tex`, a **forced full
rebuild taken in this pass** (`latexmk -g`), the generated artefacts under `figures/`, and the
published evidence under `bench/results/`, `faults/results/` and `ffi/results/`. Standard applied:
a full draft the repository does not treat as supervisor-approved, judged as an examiner would see
the manuscript. Canvas:
`~/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-aug22.canvas.tsx`.

The `.tex` mtime (14:00) had moved ahead of the log (13:10), so `texaudit.py` opened by declaring
the build stale. The working tree was clean and `latexmk` reported nothing to do, meaning the save
carried no content change, but the pass forced a rebuild anyway rather than grade on that
inference. Every finding below was re-derived from the artefacts.

| Area | Seventh pass | Eighth pass | Note |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Unchanged. Gap located in named flaws of five specific studies, four RQs traced, RQ2 falsifiable |
| 2. Scholarly framework and sources | 5 | **5** | Unchanged. 105 entries, all cited, 69 peer-reviewed (66%), search protocol in an appendix |
| 3. Research data and method | 4.5 | **4.5** | Method at 5, data at 4. Host-bound as before, and the method half now has a stronger warrant (see below) |
| 4. Presentation of results | 4.0 | **4.0** | Held for a third pass. Eleven hand-typed values, ten wrong, none fixed since the sixth |
| 5. Discussion and conclusions | 5 | **5** | Unchanged |
| 6. Academic text | 4.5 | **4.5** | Held after considering 4.0. Writing measurably improved, and one new false sentence landed in the declaration |
| 7. Work during the thesis process | not assessable | **not assessable** | No manuscript settles it |
| **Mean of the six assessable** | 4.67 | **4.67** | |

### The finding of this pass: the prose moved, the numbers did not

The seventh pass reported that nothing had changed on any graded point. That is no longer true, and
the split matters, because the surfaces that improved are not the surfaces capping the grades.

| Quantity | Seventh pass | This pass | Reading |
| --- | --- | --- | --- |
| `rather than` antithesis | 154 instances, 44.0 per 10k words | **51 instances, 14.5 per 10k** | Raw occurrences 167 to 69, a 59% cut. `.aitells.py` was last modified before the seventh pass, so the change is in the prose and not in the tool |
| Longest sentence | 73 words | **63 words** | Stdev 13.0 to 10.4, mean 24.1 to 20.3 |
| Declared length | 99 body + 6 appendix | **103 body + 6 appendix** | §7.6 landed with the three RQ4 adoption-cost axes. 113 PDF pages to 117 |
| Prose word count | 33,425 | **35,279** | The new section plus the four passages that stopped calling RQ4 environment-insensitive |
| Wrong hand-typed values | 8 open | **11 open, none fixed** | Third consecutive pass with the graded defects untouched |

Item 11 of the seventh pass's outstanding list, thinning the antithesis construction, is therefore
largely done and is the **only** item on that list of fourteen to have moved.

### Re-derived independently: all eight of the seventh pass's values confirmed, and three more found

Every value was checked against the artefact rather than against the previous pass's note.

1. **TSan deadlock rate.** L3044 prints "four of twelve" and the Table 7.6 footnote prints
   `$4$ of $12$`. `taxonomy.csv` records `TSan reported in 7/12 runs`. This pass went further and
   counted the twelve run logs one by one: `WARNING: ThreadSanitizer` appears in runs 0, 1, 2, 3,
   7, 8 and 9, so **7 of 12** is reproducible from the shipped logs. Confirmed.
2. **The footnote's second number is stale too, and this is new.** The same footnote prints
   "$6$ of $20$ in a longer trial". `faults/results/` holds exactly twelve deadlock run logs
   (`run0`–`run11`), so **no 20-run trial is published at all**, and `faults/README.md` says
   "7 of 20 in longer trials". The footnote carries two stale numbers and one of them cites a
   campaign the repository does not ship. Either publish the longer trial or drop the clause.
3. **Lost-update counts.** L3023–3025 print 35,030 recorded and 4,970 lost for safe Rust against
   25,448 and 14,552 for C++ under TSan. The logs read `messages_handled=28914 expected=40000
   lost=11086` and `messages_handled=27788 expected=40000 lost=12212`. Confirmed. Worth restating
   why this one is the costly error: as printed, Rust loses roughly a third of what C++ loses, so
   the number **flatters Rust on a boundary class inside the one chapter written to show that
   neither language is protected**. The logs put the two within ten percent.
4. **Conformance campaign size.** L3105–3106 print `$223$` and `$9\,006$` where `\ConfHandOps`
   and `\ConfGenOps` exist and are used correctly forty lines earlier. `summary.json` gives
   `generated_ops: 792964` and the macro prints `793\,000`. Confirmed. Search for `9\\,006`.
5. **Rust test count.** L3105 says "twenty-five Rust tests". `cargo test --release -- --list` was
   run in this pass and reports **27**. The six C++ test binaries are right. Confirmed.
6. **Classes untouched.** L3010 says "the three between them still leave four of the ten classes
   untouched". `taxonomy.csv` marks `cpp_detection` as `undetected` for **two** classes,
   `lost_update` and `worker_failure_blast_radius`. Three if the intermittent deadlock counts. No
   reading gives four. Confirmed.
7. **Table 6.4.** The nine concern rows sum to **668** in the C++ column against a printed
   `\CppRawLines` of 674, and the delta column sums to **+94** against a printed `+\LocGap` of 88.
   The Rust column sums correctly to 762. Confirmed.
8. **The p50 sentence.** `tab_latency.tex` gives C++ system 79.9 [79.6, 80.7], C++ jemalloc 80.3
   [79.4, 80.7], Rust system 79.0 [78.7, 79.7], Rust jemalloc 78.6 [78.1, 79.7]. No interval
   contains a cross-language median, and all four overlap. Confirmed, and one word fixes it.
9. **The 99.9% complement.** L2584 pairs "better than $99.9\%$" with `\BudgetCoreShareMax` of
   0.250 two sentences above, whose complement is 99.750%. Confirmed.

### New in this pass, and it is the cheapest grade-protecting edit in the document

**`ai_statement.tex` carries a false sentence about the method.** Under *What the model did not
settle* it reads: "Every measurement was run by the author on the hosts documented here. Each
number reaches the text through a macro regenerated from the raw logs, so no figure is transcribed
by hand." Eleven values falsify the second sentence, five of them against evidence the thesis
ships.

The seventh pass's item 8 flagged §7.2's version of this claim. The declaration's version is a
distinct and more serious instance, for three reasons. It is signed in the author's name. It is the
document's own account of what the author did rather than of what the pipeline does. And
`CALIBRATION.md` ranks declaration truthfulness above any prose defect, on the grounds that a
reader who catches the declaration overstating has reason to re-audit everything else.

The claim underneath is true and strong. This pass **proved** it: `bench/plot_figures.py` was rerun
with `--outdir /tmp/figcheck` and `tab_significance.tex`, `tab_latency.tex`, `tab_resource.tex`,
`tab_overload.tex`, `tab_equivalence.tex` and `gen_macros.tex` all came back **byte-identical** to
the committed files. Narrow the sentence to the campaign statistics and it stops being falsifiable
while saying something no other thesis in this literature can say.

### Checked in this pass and clean

- **The generated layer regenerates exactly.** Six artefacts reproduced byte-identically from
  `campaign-20260812-154528.jsonl`. This is a new check and it strengthens criterion 3's method
  half: the analysis is reproducible from the raw logs, not merely documented as reproducible.
- **Build gates.** Zero LaTeX errors, undefined references, undefined citations, multiply-defined
  labels, overfull boxes, floats too large, placeholder markers. 117 PDF pages, `\pagesCount` 103
  with `\appendixCount` 6, matching the abstract form. Note `AGENT.md` §1 still says 104; the
  `.aux` says 103.
- **Abstract page rendered at 110 dpi and inspected.** The form is complete, the CCS block does not
  overflow into Keywords, the keyword row is intact, and the date reads 22 August 2026.
- **Prose gates.** Zero semicolons in 35,279 words. Four dash hits, all legitimate (one compound
  proper name, three numeric ranges). Sentence length 20.3 ± 10.4 words, max 63.
- **FFI evidence.** All ten quantities in `ffi/results/metrics.json` still agree with their macros,
  and the diagram `07_ffi_seam` quotes 11 entry points, 231 lines, 9 `unsafe` functions, 12.7 µs
  and 2.54 ns, every one matching. No noise run has overwritten the evidence.
- **RSS and CPU results at the representative load.** "18 of the 20 paired repeats agree" and "some
  30 MiB below their variant's median" both check out exactly (jemalloc RSS: 18 positive of 20,
  with two runs 33.1 and 28.7 MiB low). `\CpuDiffAbsMax` of 3.4 matches a median paired difference
  of −3.35 percentage points. See the false positive below before re-checking these.
- **Overload macros against the abstract.** `\OverloadThrRatio` 1.8 and `\OverloadThrAgree` 20/20,
  both as printed.
- **Literature search protocol is in the manuscript**, as `appendix:search`, not only in the
  repository. Four databases, term combinations, chaining, the two repository searches that were
  needed because the closest prior work is unindexed, the absence evidence on both sides, and the
  grey-literature caveat.
- **Bibliography.** 105 entries, 105 cited, no uncited entry and no missing key. `bugden2022rust`
  is the one remaining arXiv item, cited twice and both times beside a peer-reviewed source.

### Why area 6 stayed at 4.5 rather than falling to 4.0

This pass considered 4.0 and did not take it, and the reasoning belongs on record because the
balance inside the area shifted in both directions at once.

Level 4 asks that "the whole text is logical and consistent when it comes to research questions,
description of research setup, findings and conclusions". Three things strain that clause: §5.5
describing pooled far-tail histograms, directly measured jitter and p99.99 "reported descriptively"
when none is reported anywhere (`plot_figures.py` prints "campaign has no inter-operation jitter
data" and declines to write `tab_jitter.tex`); the abstract's bare "median latency matches" against
a paired test that resolves −1.1 and −1.6 µs; and the declaration sentence above.

Against that: the *writing* half improved measurably this pass, and the finishing defects that took
this area from 5 to 4.5 in the fourth pass are all closed (zero overfull boxes, no float too large,
no 93- or 86-word sentences). Of the three strains, two are disclosed elsewhere in the document
(§7.5.1 states the instrumentation gap explicitly, and §8.3 states the median result correctly), so
the text as a whole is not inconsistent so much as unrepaired in the place a reader meets first. The
declaration sentence is one sentence and a minute's work.

A half-step drop on one sentence, in the pass where the prose measurably improved, would be
deflation. 4.5 stands, with the declaration sentence recorded as the highest-priority item inside
the area rather than as a grade movement. If a ninth pass finds it still there, that reasoning
should be revisited, because at that point it is a finishing failure and not an oversight.

### False positive this pass burned time on, recorded so the next one does not

**Filtering the campaign JSONL on the `rate` field is wrong.** `offered_load(row)` in
`plot_figures.py` is `row["rate"] * row["producers"]`, and there are seven producers, so the
representative load of 56 kops/s is `rate == 8000`, not `rate == 56000`. Filtering on `rate ==
56000` reads the **overload region**, where the RSS sign agreement and the direction of the CPU
result both genuinely reverse. This pass briefly scored two correct claims as defects on that
basis, "18 of the 20 paired repeats agree" and "Rust draws slightly less CPU", and both are right.
Pair by position after filtering on `offered_load`, which is what the repo's own
`_paired_effect` does and documents.

Also re-confirmed from earlier passes: `pdftotext` on `diagrams/pdf/*.pdf` extracts nothing, so
route diagram style checks through the `.svg` sources and search for both the literal em dash and
the `&#8212;` entity. Semicolons inside verbatim code in a diagram are exempt by the house style:
`08_borrow_checker_uaf` and `05_data_model`'s `[u8; 32]`.

### Nothing was changed in the thesis during this pass

The pass graded and did not edit. Only `docs/ASSESSMENT.md` was written, plus the canvas.

### Outstanding, cheapest first

Fifteen items. Fourteen are editing and the first nine are under three hours between them.

1. **Delete or narrow the declaration's "no figure is transcribed by hand"** in
   `ai_statement.tex`. Minutes. Highest credibility cost per character in the document, and the
   claim underneath is true and now proven.
2. **"contains" to "overlaps"** in §7.5.1. One word.
3. **Replace the hand-typed `$9\,006$` and `$223$`** with `\ConfGenOps` and `\ConfHandOps`.
   Minutes, and it removes a two-order-of-magnitude error.
4. **"twenty-five Rust tests" to 27**, and **"four of the ten classes untouched" to two** (or three
   if the intermittent deadlock is counted, in which case say so). Minutes each.
5. **State the denominator behind the 99.9%**, or quote the complement of `\BudgetCoreShareMax`.
   One clause.
6. **Regenerate the deadlock-rate and lost-update sentences** from `taxonomy.csv` and the run logs.
   Under an hour, and the largest of the evidence disagreements.
7. **Publish the deadlock footnote's longer trial or drop the clause.** No 20-run log is shipped
   and `faults/README.md` disagrees with the printed figure.
8. **Find the six missing C++ lines in Table 6.4**, or say in the caption what the breakdown omits.
9. **Narrow §7.2's "no value is hand-copied"** to the campaign statistics, for the same reason as
   item 1.
10. **Put §5.5's pooling, jitter and p99.99 sentences in the conditional**, and either drop jitter
    from the abstract's open dimensions or mark it as future work. About an hour.
11. **Soften §8.2's claim that Figure 8.1 "states the whole result"**, since it draws two of five
    boundary classes and its own caption says so. And soften "trace to" in the conclusion.
12. **Clear the dash asides and prose semicolons out of the diagram labels** and re-render, then
    **extend the style gate to `diagrams/`**. About two dozen breaches across the eleven included
    diagrams, on the only reader-visible prose surface with no check.
13. **Unrealised asset:** `figures/tab_equivalence.tex`, still generated on every refresh and still
    `\input` by no document. It holds the equivalence-bound reading of RQ1, which is the strongest
    available answer to the half of RQ1 the host cannot resolve.
14. **Rewrite the abstract unaided**, then set `\abstractunaidedtrue`. Blocking, cannot be
    delegated, open for a fourth pass. Drop "median latency matches" in the same edit.
15. **Bare-metal tail campaign** with hardware counters and allocation profiles on the same visit.
    The only item editing cannot reach, and its target stays narrow: the far tail below saturation,
    plus a mechanism for the peak-RSS effect and the operation-level gap.

## Remediation pass — 22 August 2026, afternoon

The eighth pass graded and did not edit. This pass closes thirteen of its fifteen outstanding
items. Two are deliberately untouched: the abstract cannot be delegated, and the bare-metal
campaign needs an instrument the author does not have.

| Area | Eighth pass | After remediation | Why it moved |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Unchanged |
| 2. Scholarly framework and sources | 5 | **5** | Unchanged |
| 3. Research data and method | 4.5 | **4.5** | Unchanged. Only the bare-metal campaign lifts it |
| 4. Presentation of results | 4.0 | **4.5** | Every hand-typed value is gone, the reproducibility claim is true as written, and the equivalence table is placed. What remains of the cap is RQ1's far tail, which is the 4.5 the sixth pass started from |
| 5. Discussion and conclusions | 5 | **5** | Unchanged |
| 6. Academic text | 4.5 | **4.5** | Three of its four failing clauses closed. The fourth, the abstract, is the whole of the remaining cap |
| 7. Work during the thesis process | not assessable | **not assessable** | No manuscript settles it |
| **Mean of the six assessable** | 4.67 | **4.75** | |

### The durable part: three classes of defect are now generated rather than typed

Correcting eleven wrong numbers would have left the mechanism that produced them intact. Each
was instead moved behind a generator, so a rerun moves the prose and a drift becomes a build
failure rather than a paragraph an examiner checks.

**`bench/artefact_facts.py`** gained two sources, the fault catalogue and the parity suite, and
emits eleven new macros: `\DeadlockTsanHits`, `\DeadlockTsanRuns`, `\FaultClasses`,
`\FaultClassesUndetected`, `\LostUpdateExpected`, `\LostUpdate{Rust,Cpp}{Handled,Lost}`,
`\CppTestBinaries`, `\RustTests`. Two checks are built in rather than trusted. The deadlock rate
is read twice, from `taxonomy.csv`'s note field and by counting `WARNING: ThreadSanitizer` across
the per-run logs, and a mismatch is a hard error, so a partial rerun cannot leave the catalogue
and its evidence disagreeing. The two lost-update runs must agree on their expected total, since
the prose quotes one figure for both.

**`bench/complexity.py`** now emits `figures/tab_loc.tex`, so Table 5.4's breakdown is measured
rather than maintained. A `CONCERNS` partition assigns every measured file to exactly one row and
the generator refuses to write the table if the partition does not cover both file sets or if a
column does not sum to its measured total. That is the check the six missing C++ lines needed:
the bounded queue had grown from 45 to 51 lines and the table had not followed. Rows are now
ordered by the size of the difference, so the ordering also stops being hand-maintained.
`\CppBoundedQueueLines` feeds the two prose sites that name the same figure.

**`diagrams/check_labels.py`** is new, and it closes the surface the eighth pass called the only
reader-visible prose in the project with no gate over it. It walks every text run in the diagram
sources, refuses em dashes, spaced en dashes and prose semicolons, and exempts verbatim code
through an explicit list keyed by diagram and string rather than by a heuristic that would also
wave through prose. Scope is computed from the documents, every diagram a `.tex` file includes or
`build_deck.py` names, so it covers 19 diagrams today and picks up a twentieth the moment one is
included. `bench/refresh_thesis.sh` runs it beside the two gates that already existed.

### What changed in the manuscript

| Item | Before | After |
| --- | --- | --- |
| TSan deadlock rate, prose and Table 7.6 footnote | "four of twelve", plus "six of twenty in a longer trial" | `\DeadlockTsanHits` of `\DeadlockTsanRuns`. The unsupported longer trial is dropped, and "minority" is corrected to "a majority of runs and not all of them", since 7 of 12 is a majority |
| Taxonomy figure caption | "flags the inversion on a minority of runs" | The same two macros. This one was found only by sweeping after the prose was fixed |
| Lost-update counts | 35,030/4,970 and 25,448/14,552 | Four macros off the logs, plus a sentence saying neither language is meaningfully better off, which is what the corrected figures show and the point of carrying the class |
| Conformance campaign | `$223$` and `$9\,006$` | `\ConfHandOps` and `\ConfGenOps` |
| Rust test count | "twenty-five Rust tests" | `\RustTests`, which measures 27. `\CppTestBinaries` replaces the hand-typed six |
| Classes no sanitiser touches | "four of the ten" | `\FaultClassesUndetected` of `\FaultClasses`, with the intermittently detected deadlock named separately rather than folded in |
| Table 5.4 | Nine hand-maintained rows, C++ column six short, deltas six over | `\input{figures/tab_loc.tex}`, columns summing to 674 and 762 and deltas to +88, all three asserted by the generator |
| Bounded queue, two prose sites | "45 lines" | `\CppBoundedQueueLines` |
| §7.5.1 p50 reading | "each variant's confidence interval contains the others' point estimates" | "every pair of confidence intervals overlaps", which is true and is all the argument needs |
| Budget complement | "Better than $99.9\%$" | `\BudgetCoreShareRest`, a new macro computed as the complement, so the arithmetic cannot be eyeballed wrong again |
| §7.2 reproducibility claim | "No value is hand-copied ... the text and the data cannot drift apart" | "Every measured quantity this chapter quotes reaches the page as a generated macro", which is now true and was verified byte-for-byte in the eighth pass |
| `ai_statement.tex` | "so no figure is transcribed by hand" | "the measured quantities the thesis quotes reach the page as macros regenerated from the raw logs rather than as figures typed into a paragraph" |
| §5.5 instrumentation | Pooling, direct jitter and "reported descriptively" in the indicative | Conditional throughout, with an explicit sentence that neither is reported in Chapter 7 because the campaign predates the instrumentation, cross-referenced to §7.5.1 |
| §8.2 on Figure 8.1 | "states the whole result in one picture" | "draws the boundary itself", with the two-of-five scope stated in the prose and the full catalogue pointed at Table 7.6 |
| `figures/tab_equivalence.tex` | Generated every refresh, `\input` by nothing | Placed in §7.5.2 as Table 6.3 with a new paragraph, as the fourth of five readings of the test family |
| Diagram labels | About two dozen dash asides and prose semicolons across the reader-visible set | Zero, gated. 13 SVG sources and `build_new_diagrams.py` edited |

### The equivalence table earns its place

It was the one unrealised asset on the list and it turned out to be the strongest single addition.
The new paragraph uses it to separate the five unresolved rows into two kinds, which the thesis
could previously only assert. At the median the bound is $2.0\,\mu$s, so the difference the test
resolves is also small in absolute terms and the two readings agree. In the tail block the bounds
run to $1298\,\mu$s, which is the host's inability to see stated as a quantity instead of as a
null. That is a real strengthening of the answer to the half of RQ1 the host cannot resolve, and
it cost two pages.

### Prose quality after the edits

Six labels came out of the dash and semicolon removal with a comma splice or a panel overrun,
across nine lines of text. The gate passed every one, because it checks punctuation and not sense.
All six were caught instead by rendering the diagrams and reading them, which is the method note
worth keeping: the gate tells you a label is legal, not that it is good.
`17_guarantee_boundary` needed two passes for this reason, one for a splice and one for a line
that grew past its panel.

Thesis prose after the pass: zero semicolons in 35,544 words, four dash hits all legitimate
typography, sentence length 20.4 ± 10.4 with a maximum of 63. "rather than" sits at 53 instances
and 14.9 per ten thousand words, essentially where the eighth pass found it.

### Build state

Zero LaTeX errors, undefined references, undefined citations, multiply-defined labels, overfull
boxes, floats too large, placeholder markers. 119 PDF pages. `\pagesCount` 105 with
`\appendixCount` 6, up from 103, and the abstract form picked the new figure up on its own. All
three prose gates report clean in one `refresh_thesis.sh` run: diagram labels, deck layout, deck
prose. The abstract page was rendered and inspected again and still fits.

**105 is above the author's stated preference of under 100.** Two pages are the equivalence table
and its paragraph, and the rest is the RQ4 section that landed on 21 August. `AGENT.md` §5 says
substance wins when the two conflict, so the figure is reported rather than traded away.

### Outstanding

1. **Rewrite the abstract unaided, then set `\abstractunaidedtrue`.** Now the *only* thing between
   area 6 and level 5, and the only editing item left anywhere. Deliberately untouched by this
   pass: the abstract is the maturity test in this programme, where a model is never permitted, so
   a model rewriting it would defeat the point of the gate. Drop "median latency matches" while
   rewriting, since the paired test resolves $-1.1$ and $-1.6\,\mu$s under the two allocators, and
   decide what to do with jitter in the list of open dimensions now that §5.5 is conditional.
2. **Bare-metal tail campaign** with hardware counters and allocation profiles on the same visit.
   The only lift no editing reaches, and the only thing holding areas 3 and 4 below 5.
3. **Optional:** replace `bugden2022rust` with a peer-reviewed equivalent. Area 2 is at 5 without
   it.
4. **Optional:** the ten diagrams no document includes still carry breaches, which
   `check_labels.py --all` lists. They are not reader-visible, and the gate starts covering any of
   them the moment a document includes it.

---

## Ninth pass — 23 August 2026

Graded from `Ha_Vien_Mastersthesis_2026.tex` at its 22 August 14:46 state with a current build
(PDF and log both 14:52), the generated artefacts under `figures/`, and the published evidence
under `bench/results/`, `faults/results/` and `ffi/results/`. No edits were made: this is a
grading pass.

**The headline: not one measured value is wrong, and seven statements about the values are.**
This is the first pass on record to find no wrong number anywhere. Every mechanism the
remediation pass installed still holds. What replaced the old defect class is a new one in the
same neighbourhood: claims about the evidence that the evidence does not support.

| Area | Remediation pass | This pass | Why it moved |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Unchanged |
| 2. Scholarly framework and sources | 5 | **5** | Unchanged |
| 3. Research data and method | 4.5 | **4.5** | Unchanged. Only the bare-metal campaign lifts it |
| 4. Presentation of results | 4.5 | **4.0** | **Disagreement.** Three figures misstate the result they illustrate, two reproducibility claims outrun their artefacts, and three summary passages assert median equivalence that §7.5.1 resolves against. No data error is involved |
| 5. Discussion and conclusions | 5 | **5** | Unchanged. The discussion chapter states the median result correctly, so the summary slips are not its defect |
| 6. Academic text | 4.5 | **4.5** | Unchanged. The abstract is still the whole of the cap |
| 7. Work during the thesis process | not assessable | **not assessable** | No manuscript settles it |
| **Mean of the six assessable** | 4.75 | **4.67** | |

### What was verified as still holding

Worth recording, because the point of the generated layer is that a later pass can check it
cheaply and did.

- `bench/artefact_facts.py` regenerated into a scratch directory and `gen_artefacts.tex` came
  back **byte-identical**.
- `figures/tab_loc.tex` column sums verified by hand: C++ 674, Rust 762, delta +88, matching
  `\CppRawLines`, `\RustRawLines` and `\LocGap`. The generator's assertion is doing its job.
- Around thirty macros cross-checked against the generated table bodies. Every one agrees.
  Sampled: `\PNineNineMaxCI` 1480 against the widest p99 interval in `tab_latency`, `\NSignificant`
  9 and `\NExclZero` 10 counted off `tab_significance` and the overload rows, `\NEqvUnresolved` 5
  against the five "not resolved" verdicts in `tab_equivalence`, `\EqvBoundTailMax` 1298,
  `\BudgetBoundVsCore` 58 as 2.0 µs over 34.5 ns, `\BudgetCoreShareRest` 99.750, `\DepsJemallocShipping`
  plus `\DepsJemallocBuildOnly` summing to `\DepsJemalloc`, `\BuildDepShareCpu` 54 from 64.8 and
  29.6, `\FootStaticRatioAbs` 2.2 from 1577 and 723.
- All ten rows of Table 7.9 checked against all four columns of `faults/results/taxonomy.csv`.
  They agree.
- Every generated figure reproduces from the current campaign, and every numeric claim in every
  generated caption checks out.
- Build: zero LaTeX errors, undefined references, undefined citations, multiply-defined labels,
  overfull boxes, underfull boxes, floats too large, placeholder markers. 119 PDF pages,
  `\pagesCount` 105 with `\appendixCount` 6.
- Prose: zero semicolons in 35,544 words, four dash hits all legitimate typography, sentence
  length 20.4 ± 10.4 with a range of 3 to 63. `diagrams/check_labels.py` clean over all 19
  reader-visible diagrams.

### Finding 1: the median is resolved in Chapter 7 and equivalent in three summaries

The widest-reaching finding, because two of the three sites are where a reader looks first.
§7.5.1 says "the median is now a resolved difference and not a null". `tab_significance` gives
both p50 rows a Holm-adjusted *p* that clears (0.012 and 0.00069) and `tab_equivalence` gives
both the verdict "significant".

There were **four** sites, not three. The sync rule caught the fourth: `Thesis_v2.tex`, the
supervisor-facing skeleton, carried the same bare claim in its chapter 9 bullet.

| Where | What it said | Status |
| --- | --- | --- |
| Abstract, l. 226 | "Below it median latency matches" | **Open.** Already on record from the remediation pass. Untouchable by a model, so it waits for the unaided rewrite |
| §1.4, l. 548 | "the two implementations cannot be told apart end to end at the median" | **Fixed 23 August.** Was the sharpest of the four: the paired test is precisely the instrument that does tell them apart |
| §9, l. 4391 | "the two languages are equivalent at the median, which is a real result about deployments of this shape" | **Fixed 23 August.** Was defensible, since the trailing clause signalled practical rather than statistical equivalence, but it never mentioned the resolved difference |
| `Thesis_v2.tex`, l. 531 | "Below saturation the two are equivalent at the median." | **Fixed 23 August.** Found by applying the sync rule rather than by reading the thesis. Supervisor-facing, so it mattered more than its length suggests |
| §8.2, l. 3489 | "equivalent in central behaviour, by a margin no deployment would notice. The small paired difference at the median that does clear the correction is a fraction of an $80\,\mu$s operation" | **Was already correct**, and supplied the register the three fixes adopt |

The thesis is strict about the mirror error, never letting "cannot tell" become "equivalent".
Here the register slipped the other way. The honest claim is a difference too small to matter, not
the absence of one.

**What the three fixes say now.** Each states the practical equivalence first, then names the
resolved difference through `\PFiftyDiffAbsMax`, then draws the distinction explicitly. §1.4 adds
"so the equivalence is practical and not statistical" and §9 and the skeleton carry the same
clause. §1.4's following sentence changed too, because "That null is less informative than it
looks" no longer had a null to refer to at the median: it now reads "Neither result is as
informative as it looks", covering the small resolved difference and the unresolved tail together.
No number is typed: both new figures are macros. Build after the edits: zero LaTeX errors,
undefined references, undefined citations, multiply-defined labels, overfull boxes, floats too
large. `\pagesCount` unchanged at 105 with 6 appendix pages, 119 physical. `.aitells.py` on both
files reports no new dash aside and no semicolon, and the thesis's sentence-length distribution is
unmoved at 20.4 ± 10.4.

### Finding 2: three figures misstate the result they illustrate

| Figure | What it says | What the thesis says elsewhere |
| --- | --- | --- |
| `fig:borrowuaf`, caption l. 827 | the C++ use-after-free "is caught only at runtime (and only under AddressSanitizer, on a path a test exercises)" | `taxonomy.csv` row 1 is `use_after_free,detected,detected` and Table 7.9 prints "detected & detected & not detected". TSan catches it too |
| `fig:ffiseam`, `diagrams/07_ffi_seam.svg` bottom band | "Per-call cost: the crossing is negligible next to the operation it invokes", 2.54 ns against 12.7 µs | §7.6 disowns exactly this ("an empty call and a full round-trip are not the same experiment") and §8.3 records the first version of the measurement as right-answer-wrong-reason. The measured $+192$ ns, its $[-954, +1341]$ interval and the 10.91 % bound appear nowhere on the diagram |
| `fig:tailconcept`, `diagrams/11_tail_latency_concept.svg` | "so a p99 per-op delay becomes a p99 per-procedure delay" | The panel heading is "Fan-out turns a rare delay into a common one" and the caption argues amplification. With the four operations drawn it is roughly 4 %, not 1 % |

Plus two smaller items: `fig:budget`'s caption says "the campaign's one resolved timing
difference" where the body sentence it compresses says "one *language* difference in time", which
is defensible and the caption is not. And `fig:effects`'s right-panel axis label is clipped at the
canvas edge, because `plot_figures.py` saves it without `bbox_inches="tight"` where
`fig_taxonomy` passes it.

The diagram-11 and diagram-07 cases are the failure mode the remediation pass's own method note
predicted: `check_labels.py` checks punctuation, not sense.

### Finding 3: two reproducibility claims outrun their artefacts

Same defect class the remediation pass closed in §7.2 and `ai_statement.tex`. Both narrowings
hold. Two more of the same shape survive, and they share one root cause.

| Where | The claim | What holds |
| --- | --- | --- |
| §5.6, l. 1623 | "every figure and table in the evaluation is produced by a single script directly from the raw measurement logs, so that rerunning the campaign on a different host regenerates the artifacts verbatim" | Fails twice. `tab:taxonomy` has no generator, its ten rows are typed at l. 3171–3182. And the artefacts come from four scripts, not one: `plot_figures.py` (11 tables), `complexity.py` (2), `adoption_cost.py` (1), `artefact_facts.py` |
| §7.4, l. 3207 | "Table and figure come from the same log, so neither can drift from the other" | True of `fig_taxonomy.pdf`. Not of the table. The rows agree with the CSV today, so this is an unenforced claim rather than a live error |

**Table 7.9 is the only results table in Chapter 7 with no generator behind it.** That single
fact is the root of both claims failing, which is why generating it is the durable fix rather
than rewording twice.

### Finding 4: one derivable number still typed

l. 2642, "so its own attainable floor is $0.000061$". This is $2/2^{15}$, determined by
`\BudgetRepeats`, so it is a weaker instance than the eleven the eighth pass found. It would go
stale if the repeat count moved, and it happens to equal the *p*-value `tab_budget` reports.

### Why area 4 moves down, stated as a disagreement

The remediation pass set area 4 at 4.5 on the strength of the generated pipeline, with the
remaining cap being RQ1's far tail. The pipeline is intact and this pass re-verified it. But 4.5
encodes "reporting at 5, evidence at 4", and reporting cannot read at 5 when three figures
misstate their own results and two reproducibility claims are unenforced. Level 4's clauses all
hold, strongly: the findings are reported clearly and logically, the figures and tables support
the analysis, and §8.6 weighs generalisability better than most published work. Level 5's "well
considered and apt" is what fails.

Calibrated against the eighth pass, which set area 4 at 4.0 for about nine hand-typed values, a
comparable count of comparable defects lands in the same place. The remediation path is the same
shape too: the first six lift items below are under two hours between them and restore 4.5.

### Housekeeping, not thesis defects

- `bench/complexity.py` cannot run in this environment: `lizard` is not installed, so
  `refresh_thesis.sh` would fail at that step on a fresh checkout. It **is** declared in
  `bench/requirements.txt`, so this is an environment note.
- `AGENT.md` is stale on the declared page count: §1 says 103 pages and §5 says 99, while the
  `.aux` reads 105 with 6 appendix pages. The footer paragraph has 105 correct.
- `tab:abbrev` is a float label never referenced from the body. Appendix glossary, reachable from
  the List of Tables, discounted as in earlier passes.
- The audit's one flagged prose number, `0.19 \%` at l. 3909, is a value quoted from
  `gonzalez2023rustudp` and not a measurement of this study. Not a defect.
- The abstract's Objective paragraph lists "tail latency and jitter under overload" among the open
  dimensions, and jitter is never reported (§5.5 and §7.5.1 both say the campaign predates the
  instrumentation). RQ1 itself does not name jitter, so the question-against-metric match is
  clean. Decide this during the abstract rewrite.

### Outstanding

**Closed the same day (23 August), in a remediation edit after grading.** Finding 1's three
editable sites: §1.4, §9, and `Thesis_v2.tex` l. 531. Both PDFs rebuilt, all gates clean. The
abstract is the one site left, and it is the one a model may not touch. **Area 4 stays at 4.0**,
because findings 2 and 3 are untouched and the abstract still carries the bare claim. Do not lift
the grade on partial remediation.

1. **Rewrite the abstract unaided, then set `\abstractunaidedtrue`.** Unchanged for a fifth pass,
   still the whole of area 6's cap, still not delegable. Drop "median latency matches" and settle
   jitter in the same edit. The wording to reach for is now in three other places in the two
   documents: state the practical equivalence, then say the paired test resolves
   $\PFiftyDiffAbsMax\,\mu$s, then call the equivalence practical and not statistical.
2. **Generate `figures/tab_taxonomy.tex` from `faults/results/taxonomy.csv`.** Half a day, and the
   most useful piece of work available. Closes findings 3 and 4's mechanism, removes the last
   hand-maintained results table, and is the same move that caught six unnoticed lines in Table 5.4.
3. **Four editing fixes remaining from the original six, about an hour between them:** delete "and
   only under AddressSanitizer" from `fig:borrowuaf`; add "language" to `fig:budget`'s caption;
   narrow §5.6 and §7.4; pass `bbox_inches="tight"` to `fig_effects`; add a macro for the 15-repeat
   floor. (§1.4's rewording is done.)
4. **Two artefact edits, one to two hours:** rewrite diagram 11's key label to state amplification,
   and replace diagram 07's "Per-call cost" panel with the measured seam cost. Re-render and
   *read* both, since the style gate will pass either way.
5. **Bare-metal tail campaign** with hardware counters and allocation profiles on the same visit.
   Unchanged, and still the only lift no editing reaches.
6. **Optional:** replace `bugden2022rust` with a peer-reviewed equivalent. Area 2 is at 5 without it.

## Tenth pass — 26 August 2026

Graded from `Ha_Vien_Mastersthesis_2026.tex` at its 26 August 11:42 state against a current build
(PDF and log both 11:43), the generated artefacts under `figures/`, and the evidence under
`bench/results/`, `faults/results/` and `ffi/results/`. Declared length 99 pages with 6 appendix
pages, 113 physical. No edits were made: this is a grading pass.

**Standard applied.** This is the full draft, and it declares itself unfinished: the build prints
`Not submittable` and the printed declaration on page 99 says the summary has not been rewritten
unaided. The abstract is therefore graded as provisional text rather than as submitted text, which
matters for area 6 and is argued below.

**The headline: every area holds, and the reason is narrow.** The one durable fix the ninth pass
asked for is done, and nothing else on its list moved. `figures/tab_taxonomy.tex` is generated now,
which removed the last hand-maintained results table and turned §6.4.4's no-drift claim from an
assertion into a property of the pipeline. The five figure defects are untouched. Two new items of
the same class turned up, one of them a claim in Chapter 6 that prose in the same chapter
falsifies.

| Area | Ninth pass | This pass | Why it held |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | RQ2 is still two-sided at seven and seven, and the two contrary boundary results are still carried |
| 2. Scholarly framework and sources | 5 | **5** | 109 entries, 109 cited, 72 peer-reviewed venues at 66 per cent, contrary results engaged |
| 3. Research data and method | 4.5 | **4.5** | Method at 5, data at 4. Only the bare-metal campaign moves it |
| 4. Presentation of results | 4.0 | **4.0** | One of three ninth-pass findings closed, two untouched, two new items of the same class opened |
| 5. Discussion and conclusions | 5 | **5** | Hypotheses revisited individually, validity by type with residual risk per row, register held |
| 6. Academic text | 4.5 | **4.5** | Writing at 5, finishing not. The abstract is still the whole of the cap, and it now carries three errors rather than one |
| 7. Work during the thesis process | not assessable | **not assessable** | No manuscript settles feedback uptake, independence, or schedule |
| **Mean of the six assessable** | 4.67 | **4.67** | |

### What was verified as still holding

- Build: zero LaTeX errors, undefined references, undefined citations, multiply-defined labels,
  overfull boxes, floats too large, placeholder markers. 113 physical pages, `\pagesCount` 99 with
  `\appendixCount` 6.
- **Second consecutive pass to find no wrong measured value.** About forty macros checked against
  the generated table bodies. Sampled: `\PFiftyRange` 2 and `\PFiftySpread` 2.1 against
  `tab_latency`, `\PNineNineMaxCI` 1480 as the widest p99 interval, `\NSignificant` 9 and
  `\NExclZero` 10 counted off `tab_significance` plus the four overload rows, `\NEqvUnresolved` 5,
  `\EqvBoundTailMax` 1298, `\BudgetCoreRatio` 1.6 from 34.5 over 21.3, `\BudgetBoundVsCore` 58,
  `\OverloadCpuPerOpRatio` 1.9 from 632.7/62.4 against 611.6/116.6, `\RssAllocDiffLo` 32.9 and
  `\RssLangDiffHi` 3.4 off `tab_resource`, `\FfiOpBoundPct` 10.91 from 1340.8 over 12284.4 in
  `ffi/results/metrics.json`, `\FaultClassesUndetected` 4 counted off `taxonomy.csv`.
- `\DeadlockTsanHits` and `\DeadlockTsanRuns` read 5 and 12, matching `taxonomy.csv`'s
  `TSan reported in 5/12 runs`, in all three places the rate appears. The macro layer is doing its
  job: the rate moved since the ninth pass and the prose moved with it.
- Twelve of the thirteen generated result tables are `\input` and the thirteenth
  (`tab_adoption`) goes through `\gentablebody`.
- Prose: zero semicolons in 34,708 words. Three dash hits, all legitimate typography (one compound
  proper name, two numeric ranges). Sentence length 21.3 ± 11.0.

### Finding 1 (new): §6.3's generated-macro claim is falsified 570 lines later

l. 2323 states that **every measured quantity this chapter quotes reaches the page as a generated
macro**, so a rerun moves the prose and cannot leave a headline number behind. l. 2894–2895 then
type two:

| Typed value | What it is | Macro |
| --- | --- | --- |
| "$18$ of the $20$ paired repeats agree" | Per-repeat sign-agreement count for peak RSS under `jemalloc` | None. `\OverloadThrAgree` is the same quantity for the overload table and is generated at 20/20 |
| "a resident set some $30$~MiB low" | The offset of the contaminated runs | None |

Both are load-bearing rather than decorative: together they are the whole justification for reading
that row from its interval rather than its $p$-value, which is the pre-committed reading rule doing
the one thing it exists to do. A rerun moves neither number.

Two more instances of the same claim failing. The AI declaration carries its own version ("the
quantities the thesis quotes reach the page as macros regenerated from the raw logs"), and
`diagrams/07_ffi_seam.svg` has `12.7 µs` and `2.54 ns` typed into the drawing, in a figure included
at l. 3218 inside the chapter making the claim. All match their macros today, so these are
unenforced claims and not live errors, which is exactly what the ninth pass said about the taxonomy
table before it was generated.

The cheapest fix is the generator, not the wording: `_paired_effect` already computes the agreement
count for the overload family, so extending it to the significance family is an hour.

### Finding 2 (new): `\SatKnee` is a throughput value used as a position on the load axis

`bench/plot_figures.py:1652` defines the knee as the highest achieved throughput anywhere in the
sweep, taken as the minimum across variants. That is a quantity on the vertical axis.
`\TrackingLoad` is an offered load, on the horizontal one. l. 2685 puts them in one sentence:
"Every variant tracks the ideal offered-equals-achieved line up to $\TrackingLoad$~kops/s and
saturates at around $\SatKnee$~kops/s", which prints as tracking to 336 and saturating at 335. Read
as written the service tracks past its own saturation point.

`fig:loadsweep`'s caption compounds it: "the dotted line marking the ideal offered-equals-achieved
regime and the knee at $\SatKnee$~kops/s", where panel (b) draws one dotted line and no knee marker
at all. The fix is to say the plateau is 335 kops/s of achieved throughput reached at 336 kops/s
offered, and either draw the knee or drop it from the caption's list.

### Finding 3: the abstract now carries three errors, not one

The ninth pass listed the abstract once. It has two more, and they are the worse pair.

| What the abstract says | What the rest of the thesis says |
| --- | --- |
| l. 228 "all **five** injected memory-safety and data-race defect classes" | Seven. §1.4, §6.4.4, Table 6.9, Figure 6.9, Table 7.1 and the conclusion, and `Thesis_v2.tex` in four places |
| l. 230 "**Five** further classes fail in both languages" | Seven boundary classes, and the count is RQ2's falsifiability evidence, which is criterion 1's own blocker |
| l. 232 "Below it median latency matches" | The paired test resolves 1.1 and 1.6 µs, both clearing Holm, and `tab_equivalence` marks both rows significant. Open since the remediation pass |
| Objective lists "tail latency and jitter under overload" | Jitter is never reported. RQ1 does not name it, so only the abstract creates the mismatch |

`AGENT.md` recorded the catalogue-size error during a length pass on 26 August, but it has not been
on the grading record before, and it is worse than the median slip: it understates the size of the
catalogue that makes RQ2 falsifiable, on the page an examiner reads first, in the document's only
maturity-test text.

**Why area 6 is not deflated to 4.0 for it.** Level 4 asks for a text that is logical and
consistent on research questions, setup, findings and conclusions, and an abstract contradicting
the findings fails that clause. Two things hold it at 4.5 anyway. The document does not present
this paragraph as finished, since the build refuses to call it submittable and the printed
declaration says so. And every item in the table above is closed by the one rewrite already
scheduled and already blocking. Deflating for defects inside a paragraph that has to be replaced
wholesale counts the same blocker twice. **Stated plainly: submitted as it stands, this abstract
puts area 6 at 4.0 and area 4 follows it.**

### The ninth pass's list, checked item by item

| Item | Status |
| --- | --- |
| Rewrite the abstract unaided, set `\abstractunaidedtrue` | **Open.** `ai_statement.tex:27` still `\abstractunaidedfalse`, build log l. 1552 still warns. Sixth consecutive pass |
| Generate `figures/tab_taxonomy.tex` | **Done.** `write_taxonomy_table()` in `plot_figures.py`, table `\input` like the other twelve |
| Delete "and only under AddressSanitizer" from `fig:borrowuaf` | **Open.** l. 834 unchanged, `taxonomy.csv` row 1 is `detected,detected` |
| Add "language" to `fig:budget`'s caption | **Open.** l. 2639 still reads "the campaign's one resolved timing difference", and the p50 rows are also resolved timing differences |
| Narrow §5.6 and §6.4.4 | **Half.** §6.4.4 fixed, and by generation rather than wording. §5.6 now names `refresh_thesis.sh` instead of claiming one script, which answers the count objection, but "every figure and table in the evaluation" still covers two hand-drawn diagrams and "regenerates the artifacts verbatim" cannot hold for a timing measurement on a different host |
| `bbox_inches="tight"` on `fig_effects` | **Open.** `plot_figures.py:1429`. Rendered at 130 dpi the right panel's axis label reads "…(% of the C++ media" |
| Macro for the 15-repeat floor | **Open.** l. 2621 still types 0.000061 |
| Diagram 11's fan-out label, diagram 07's per-call band | **Open.** Both unchanged, both included (l. 691, l. 3218) |
| Bare-metal campaign | **Open.** Still the only lift no editing reaches |
| Optional: replace `bugden2022rust` | Open, still not blocking |

### Lifts, ordered by cost

| Work | Kind | Cost | Areas |
| --- | --- | --- | --- |
| `bbox_inches="tight"` in `fig_effects`, rerun `plot_figures.py` | Editing | 5 min | 4, 6 |
| Delete "and only under AddressSanitizer"; restore "language" to `fig:budget` | Editing | 10 min | 4 |
| Fix the knee sentence and `fig:loadsweep`'s caption | Editing | 15 min | 4, 6 |
| Narrow §5.6 to what the pipeline enforces, and drop "verbatim" | Editing | 20 min | 4 |
| Macros for the peak-RSS agreement count, the low-run offset, and the 15-repeat floor | Analysis on data in hand | 1 h | 4, 6 |
| Diagram 11's label and diagram 07's per-call band. Re-render and **read** both | Editing artefacts | 1–2 h | 4, 6 |
| Rewrite the abstract unaided: seven and seven, the practical-not-statistical median, jitter, then set the switch | Author only | One sitting | 6, and 4 follows |
| Bare-metal tail campaign with counters and allocation profiles | New measurement | Testbed access | 3, 4 |

The first six are under two and a half hours between them and restore area 4 to 4.5.

### Discounted, and one new false positive to record

- `tab:abbrev` unreferenced from the body: appendix glossary, reachable from the List of Tables.
  Discounted as in every earlier pass.
- The audit's one flagged prose number, `0.19 \%`, is quoted from `gonzalez2023rustudp`. Not a
  measurement of this study.
- `.aitells.py`'s L708 hit, "not just at nominal load but , which is why": the tool strips
  `\emph{into overload}`. The source is fine.
- **New.** The longest "sentence" `.aitells.py` reports comes from table rows, not prose. Its
  `is_prose` filter drops lines starting with a backslash but keeps `RQ1 & The answer divides…`, so
  the 63-to-71-word movement since the ninth pass is not a prose regression. The standard deviation
  of 11.0 is the number to read there. Mean sentence length rose 20.4 to 21.3 while the document
  lost 836 words, which is what removing short framing sentences from §6.4 does.
- Peak RSS under `jemalloc`, interval `[+3.3, +3.5]` against $p$ 0.727: **not a defect.** §6.4.3
  explains it in mechanism and the threats table records the reading rule as costing that row.
- The contended-primitive microbenchmark has Rust ahead where the full service under overload has
  C++ ahead. The sign genuinely reverses, the thesis says so, and that is the finding.
- `\OverloadThrBound` prints 50 where the tighter interval bound is 49.6. Rounding, at 0.8 per
  cent. Noted and not scored.

### Housekeeping

- `Thesis_v2.pdf` was built 24 August 23:30 from a source of 24 August 20:01, while
  `figures/gen_macros.tex` carries a 26 August 10:15 timestamp. `AGENT.md` records that the third
  §6.4 pass regenerated it byte-identical, so the skeleton's numbers are in step, but the
  timestamps no longer show it. Rebuild it before it next goes to the supervisor.
- The skeleton's nine chapters against the draft's eight is still unresolved (`AGENT.md` §4). It
  costs no grade today, since no cross-reference is broken, but it is a sync-rule violation and the
  author has to pick a canonical list.

### Outstanding

1. **Rewrite the abstract unaided, then set `\abstractunaidedtrue`.** Now four items in one edit:
   seven and seven, the practical-not-statistical median, jitter, and the switch.
2. **Six editing fixes, under two and a half hours, restoring area 4 to 4.5.** Listed above.
3. **Bare-metal tail campaign.** Unchanged.
