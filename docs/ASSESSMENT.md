# Thesis assessment and refinement record

Assessment of **Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia
RAN Control-Plane Systems** against the six-criterion assessment matrix (simplified from the
data science master's thesis matrix), on the Finnish 1–5 scale.

Two states are recorded per criterion: the grade on first reading, and the grade after a
refinement pass. Source material was the thesis PDF and the supporting artefacts in `spec/`,
`bench/`, `faults/`, `ffi/`, and `diagrams/`.

The thesis source was renamed from `Ha_Vien_Mastersthesis_2026.tex` to `Ha_Vien_Mastersthesis_2026.tex` on
19 August 2026. Passes recorded before that date read the same document under the older name.

Interactive canvases live beside this file. The standing full-draft grade is
`thesis-grade-csm-sep07-rev2.canvas.tsx`. The latest pass, of the supervisor skeleton, is
`thesis-grade-csm-oct14.canvas.tsx`. This file is the durable copy.

> **Latest pass: thirtieth, 14 October 2026, of `Thesis_v5.tex` only, mean 4.83.**
> Areas 1 to 4 are at 5, and areas 5 and 6 are **4.5**. The abstract scope defect from
> 8 October is closed. The live caps are one contradictory allocator explanation in the
> discussion and finalisation defects: undefined references, overfull defect-table cells,
> ABI bare at first use, and the not-submittable abstract declaration. Canvas:
> `thesis-grade-csm-oct14.canvas.tsx`.
>
> **Twenty-eighth pass, 29 September 2026, mean 4.92.** Areas 1 to 5 at 5, area 6 at **4.5**.
> Superseded on area 4 by the abstract regression noted above. Canvas:
> `thesis-grade-csm-sep29.canvas.tsx`.
>
> **The summary table immediately below is the first pass** and is kept as history, not as the
> standing view. Twenty-one passes are on record and they do not all agree. Read the passes in
> order if the reasoning behind a half-grade matters. Where any two disagree, the later one is
> current.

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

---

## Eleventh pass — 26 August 2026, evening

Graded from `Ha_Vien_Mastersthesis_2026.tex` at its 16:55 state, after the bare-metal confirmation
campaign was integrated (commits `240346a` and `dd6bb01`). The PDF was **stale** on arrival: it was
built at 16:58 while `figures/gen_baremetal.tex` was regenerated at 17:02 and
`figures/gen_artefacts.tex` at 17:19. It was rebuilt before grading and came back byte-identical at
1 346 119 bytes, so both regenerations were no-ops and the grade describes a current build.
Declared length **103 pages with 6 appendix pages, 117 physical**, up from 99 and 113. No thesis
edits were made in this pass.

**Standard applied.** Unchanged from the tenth pass. The build prints `Not submittable` and the
printed declaration says the summary has not been rewritten unaided, so the abstract is graded as
provisional text rather than as submitted text.

**The headline. The campaign lands and the document has not caught up.** The bare-metal visit is
real work and it does what it was scheduled to do: virtualisation none, zero CPU steal across 60
sampling intervals on 16 pinned cores, `perf` counters at the operation and end-to-end scopes, and
pooled HDR sidecars giving 360 000 to 5 761 198 operations per group where a single run's p99.99
rested on about seventeen. Twenty of its macros were recomputed from the raw logs in this pass and
every one matched to the printed digit. That closes the instrument gap that has held area 3's data
half at 4 since the third pass. The cost is that **fourteen sites elsewhere in the document still
describe a study with less evidence than this one now has**, six of them by naming an instrument
that was in fact used. Three of those six sit in the discussion chapter, which is why area 5 moves
off 5 for the first time on record, and the rest push area 6 down from 4.5 on the level-4
consistency clause rather than on the abstract.

| Area | Tenth pass | This pass | Why it moved, or held |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Four RQs still traced end to end, RQ2 still two-sided at seven and seven, and the campaign closes the one half of RQ1 that had only a negative answer |
| 2. Scholarly framework and sources | 5 | **5** | 109 entries, 109 cited, 72 peer-reviewed venues at 66 per cent, Arvidsson's contrary tail result engaged at four sites |
| 3. Research data and method | 4.5 | **4.5** | Method 5, data **4.5 rather than 4**. Real movement, inside the half grade. Held by an off-protocol confirmation and an unanalysed profile, not by a missing instrument |
| 4. Presentation of results | 4.0 | **4.0** | Held, and now at the bottom of the band. The claims-about-the-evidence class went from five sites to about fourteen, and the new subsection carries no float |
| 5. Discussion and conclusions | 5 | **4.5** | **Disagreement.** Three statements in Chapter 7 deny instruments the study used, and H1's revisit does not use the evidence that settles H1's own clause |
| 6. Academic text | 4.5 | **4.0** | **Disagreement.** Level 4's clause on consistency of setup, findings and conclusions now fails in a countable set of sites. Not scored on the abstract, which is separate and still open |
| 7. Work during the thesis process | not assessable | **not assessable** | No manuscript settles feedback uptake, independence, or schedule |
| **Mean of the six assessable** | 4.67 | **4.50** | |

### What was verified as still holding

- Build: zero LaTeX errors, undefined references, undefined citations, multiply-defined labels,
  overfull boxes, floats too large, placeholder markers. `\pagesCount` 103, `\appendixCount` 6.
- Prose: **zero semicolons in 35 536 words.** Five dash hits, all legitimate typography (one
  compound proper name, four numeric ranges, two of them new in the bare-metal section and both
  correct). Sentence length 21.3 ± 11.0, inside the human band.
- **Third consecutive pass with no wrong measured value.** Twenty bare-metal quantities were
  re-derived from `bench/results-baremetal/` using the same `paired_permutation_test` and
  `holm_adjust` that `baremetal_facts.py` imports. All matched: `\BmFarTailCppLo/Hi` 147 and 228
  against a recomputed 147.4 and 228.0, `\BmFarTailRustLo/Hi` 88 and 115 against 87.6 and 115.4
  (and the two ranges genuinely do not meet), `\BmPFiftySig` 14 of 16 with every sign negative,
  `\BmPFiftyDiffLo/Hi` 0.5 and 1.1 against 0.51 and 1.09, all three counter deltas with their
  *p*-values (10.9 % / 0.0020, 15.3 % / 0.0117, 29.4 % / 0.0020, n = 10),
  `\BmOverloadThrRatio` 1.64 from 157.5 over 96.1, `\BmMetastableCv` 37 from 37.1 %,
  `\BmStealWithSteal` 0 of 60, and the pooled sample bounds exactly.
- `refresh_thesis.sh` **does** call `baremetal_facts.py`, so the new macros are inside the
  regeneration pipeline rather than beside it.
- The sync rule was mostly obeyed: `Thesis_v2.tex` carries the campaign in five bullets and reads
  `gen_baremetal.tex`, `Thesis_Plan_v2.tex` records the campaign as run, and the conclusion names
  the canonical-configuration repeat as the immediate priority.

### Finding 1 (new, and the reason two areas moved): six statements deny an instrument the study used

The visit collected `perf` counters at both scopes **and** a matched jemalloc allocation profile for
both languages. §6.4.4 reports the counters under the heading *A mechanism, from counters the guest
did not expose*, and says the result "replaces an argument from structure with a measurement". Six
other places say those instruments were unavailable or their outputs unreported. The worst pair is
inside one chapter, ninety lines apart.

| Site | What it says | What is true |
| --- | --- | --- |
| §6.4.3, l. 2930 | "for want of hardware counters and allocation profiles" | Counters collected and reported 90 lines later. Profiles collected |
| §7.2, l. 3704 | "needs the allocation profiles and hardware counters this study did not collect" | Both were collected on 26 August |
| §7.6, l. 4281 | "because no hardware counters or allocation profiles were collected" | Same, in the construct-validity paragraph |
| `tab:threats`, RQ3 origin row | Control applied: "None available on this host" | True of the guest, false of the study. The virtualised-host row of the same table already names §6.4.4 |
| §4.4, l. 1597 | "Neither is reported in Chapter 6, because the campaign analysed there predates the instrumentation" | p99.99 is reported in §6.4.4, pooled exactly as this paragraph describes in the conditional |
| §7.6, l. 4263 | "jitter and p99.99 are instrumented but postdate the reported campaign" | Half true. p99.99 is reported. Splitting the sentence fixes it |

**The unrealised asset behind it.** `bench/results-baremetal/alloc_profile-20260826-110718/` holds
forty interval heap dumps per arm, both stderr transcripts, the C++ allocation trajectory as a TSV,
and the Rust binary kept for later symbolisation. That is the instrument the thesis has said it
lacked since the first pass, and it is the one thing that turns RQ3's memory result from resolved
and unexplained into resolved and explained. Nothing in the document mentions it, so under the rule
that a grade describes the manuscript it earns nothing today. It is the highest-value half day
available.

Jitter is the smaller half of the same shape: all 32 pooled groups carry `jitter_p50_ns`,
`jitter_p99_ns`, `jitter_p999_ns` and `jitter_max_ns`, RQ1 does not name jitter so no promise is
broken, and `tab_jitter.tex`'s machinery already exists from the 20 August validation run.

### Finding 2 (new): five summary sites still say the far tail is unresolved

The integration was mostly done well, which is what makes the exceptions legible. §1.4, §6.4, §7.2,
the conclusion, `tab:threats`'s virtualised-host row, `tab:testbed`, `Thesis_v2.tex` and
`Thesis_Plan_v2.tex` all point at §6.4.4 correctly. Five sites did not move, and they cluster where
a reader looks for the verdict.

| Site | Text | Why it matters |
| --- | --- | --- |
| Abstract, l. 245 | "The far tail below saturation cannot be settled on a virtualised host." | Literally true, and the Results paragraph's last word on RQ1. **Author-only fix** |
| `tab:findings`, RQ1 row | "no tail ordering is resolvable"; status "Far tail: unresolved on this host" | The findings table is the verdict |
| §7.1, l. 3506 | "The far tail below saturation stays unresolved" | The summary paragraph immediately above that table |
| `tab:threats`, non-determinism row | "so the far tail below saturation stays unresolved" | The residual column |
| §6.3, l. 2389 | "answer RQ1 and RQ3 provisionally … replaces these numbers with testbed-grade ones" | §6.4.4 says the opposite: a confirmation and **not** a replacement |

§5.6's "rerunning the campaign on a different host regenerates the artifacts verbatim" belongs with
these. The ninth pass called it a claim that *cannot* hold for a timing measurement. It is now
*falsified by this document*, because §6.4.4 is a rerun on a different host that produced different
numbers on purpose. §5.6 also still lists `bench/results/` as where campaigns live, and the new one
is under `bench/results-baremetal/`.

### Finding 3 (new): the confirmation changed a fifth variable, and a caption promises it did not

§6.4.4's closing paragraph is one of the best in the chapter. It lists three differences from the
main sweep (8 shards and producers against 7, 8 load levels against 14, 15 repeats against 20),
argues that substituting them would change a control, a design and the host at once, and concludes
"Kept separate it changes one thing that matters, the machine."

The environment captures do not support that last clause. The main sweep ran `g++ 15.1.1` and
`rustc 1.97` on Rocky Linux 8.10; the confirmation ran **`g++ 13.3.0` and `rustc 1.98.0`** on Ubuntu
24.04.4. Two major versions of the C++ compiler, and the distribution jemalloc the C++ arm links
moves with the distribution. Arguably that *strengthens* external validity, since the findings
survived a toolchain change too, but it has to be named, and Phase 11 item 6 of `docs/TODO.md` is
about exactly this confound.

`tab:testbed`'s caption compounds it: "A machine meeting the right-hand column was used for the
confirmation campaign." That column asks for the same toolchain (missed), `isolcpus` and
`nohz_full` on the benchmark cores (missed, and the capture's own warning block says so), benchmark
cores removed from the scheduler (missed), and `\NRepeats` repeats (missed, 15 against 20). Four
rows of eleven.

### Finding 4 (new): the peak-RSS order-of-magnitude claim does not survive the change of host

| Host | Language effect (Rust − C++) | Allocator effect (jemalloc − system) | Ratio |
| --- | --- | --- | --- |
| KVM guest, every table in the thesis | 1.9–3.4 MiB | 32.9–34.4 MiB | ≈ 13× |
| Bare metal, confirmation | 0.7–1.8 MiB | 1.9–3.2 MiB | ≈ 2× |

Allocator configuration is matched across hosts at `thp:never,narenas:16`, so the collapse is not a
configuration artefact. §6.4.4 is careful and says only that the allocator effect "remains the
larger of the two", which is true on both hosts. What it does not say is that the ratio fell by a
factor of six, because the allocator effect fell thirteenfold while the language effect only halved.
Three summary sites state the finding as a bare order of magnitude with no host attached: §1.4,
`tab:findings`'s RQ3 row, and the conclusion. A reader comparing the two sections will notice
before the thesis tells them, because the bare-metal *allocator* effect (1.9–3.2 MiB) is numerically
almost the guest's *language* effect (1.9–3.4 MiB).

**The non-negotiable claim is untouched**: both effects are real, they reproduce under both
allocators, and the allocator effect is still the larger. Only the order-of-magnitude phrasing has
to acquire a host.

### Finding 5 (smaller): the new subsection has no float, and adds a sixth hand-typed value

§6.4.4 is roughly 72 lines answering the chapter's headline open question, quoting about forty
generated values, with **no figure and no table**. Its central result is two non-overlapping ranges
across seven load levels, which is a figure. Level 5 in area 4 asks that the use of pictures and
tables be "well considered and apt", and this is the one place in the chapter where the visual layer
is simply absent. `tab:latency`'s column specification is generated precisely so a p99.99 column can
appear without a preamble edit, and it has not been used.

The chapter-6 hand-typed count is now five against §6.3's promise that every measured quantity the
chapter quotes reaches the page as a generated macro: "roughly $80\,\mu$s" (l. 2572), "roughly
$240\,\mu$s" (l. 2684), "$18$ of the $20$ paired repeats agree" and "some $30$~MiB low" (l.
2911–2912, both from the tenth pass), and the new "an operation of about $74\,\mu$s" (l. 3004). The
recomputed bare-metal median is 73.6 µs, so the value is right, which is what makes this an
unenforced claim rather than an error. The 15-repeat *p*-floor is still typed at l. 2638.

### The tenth pass's list, checked item by item

| Item | Status |
| --- | --- |
| Rewrite the abstract unaided, set `\abstractunaidedtrue` | **Open, seventh consecutive pass**, and now five items rather than four. `ai_statement.tex:27` still `\abstractunaidedfalse` |
| Delete "only under AddressSanitizer" from `fig:borrowuaf` | **Open.** l. 843 unchanged; `taxonomy.csv` row 1 is `detected,detected` with detection recorded as `runtime (ASan+TSan)` |
| `bbox_inches="tight"` on `fig_effects` | **Open.** `plot_figures.py:1429` still bare; the only `bbox_inches` in the file is at l. 825 for `fig_taxonomy` |
| Diagram 11's fan-out label, diagram 07's per-call band | **Open.** Both strings unchanged in the SVG sources |
| Fix the `\SatKnee` axis confusion | **Open.** l. 2702–2703 still print tracking to 336 and saturating at 335. §6.4.4 solves the same problem correctly by bracketing its own knee between 448 and 512, so the pattern to copy is already in the document |
| Macro for the 15-repeat floor | **Open.** l. 2638 still types `0.000061` |
| Macros for the peak-RSS agreement count and low-run offset | **Open**, and the class grew by one |
| Narrow §5.6 | **Worse.** "verbatim" is now falsified by §6.4.4 rather than merely unenforceable |
| `fig:budget`'s missing "language" | **Closed.** The caption now reads "why the sweep cannot bound a language effect" |
| Bare-metal campaign | **Done, with a caveat that is the new item.** Off-protocol on four rows of `tab:testbed`, so it corroborates and cannot replace |
| Rebuild `Thesis_v2.pdf` | **Done.** Source 16:56, PDF 16:57 |
| Optional: replace `bugden2022rust` | Open, still not blocking |

### Lifts, ordered by cost

| Work | Kind | Cost | Areas |
| --- | --- | --- | --- |
| Rewrite the six statements that deny an instrument the study used; split the p99.99-and-jitter sentence | Editing | 45 min | 4, 5, 6 |
| Sync the five far-tail sites, including `tab:findings`'s RQ1 row and §6.3's provisional paragraph | Editing | 30 min | 4, 5, 6 |
| Name the toolchain in §6.4.4; stop `tab:testbed`'s caption claiming the host met the right-hand column | Editing | 20 min | 3, 4, 6 |
| H1's revisit: record that the clause H1 named resolves on bare metal, in Rust's favour, on one machine | Editing | 15 min | 5 |
| Attach a host to the peak-RSS order-of-magnitude phrasing in §1.4, `tab:findings` and the conclusion | Editing | 20 min | 4, 5 |
| Narrow §5.6: drop "verbatim", add `bench/results-baremetal/` | Editing | 20 min | 4, 6 |
| `bbox_inches="tight"` on `fig_effects`; delete "only under AddressSanitizer"; bracket the knee | Editing | 30 min | 4, 6 |
| Diagram 11's label and diagram 07's per-call band. Re-render and **read** both | Editing artefacts | 1–2 h | 4, 6 |
| Macros for the five typed chapter-6 values and the 15-repeat floor | Analysis on data in hand | 1 h | 4 |
| **Analyse `alloc_profile-20260826-110718/`.** Turns "resolved, unexplained" into a mechanism and closes `tab:threats`'s one empty control cell | Analysis on data in hand | Half a day | 3, 4, 5 |
| Give §6.4.4 a figure and the jitter data a home; add p99.99 to `tab:latency` | Analysis on data in hand | Half a day | 3, 4 |
| Rebuild the deck. `build_deck.py` holds no `Bm` macro and l. 1052 still reads "The far tail here needs bare metal, not more repeats" | Editing artefacts | 1 h | Repository consistency |
| Repeat the campaign at 7 shards, 7 producers, 14 loads, 20 repeats, on the main sweep's toolchain, with `isolcpus` set | New measurement | ~2 h, one euro | 3, 4 |
| Rewrite the abstract unaided, then set the switch | Author only | One sitting | 6, and 4 follows |

The first seven are under three hours between them and they restore area 5 to 5 and area 6 to 4.5.

### Why area 5 and area 6 moved, stated as disagreements

The tenth pass held both, and its reasoning for area 6 was explicit: deflating for defects inside a
paragraph that has to be replaced wholesale counts the same blocker twice. **That reasoning still
holds and it is not what moved area 6.** The abstract is graded exactly as the tenth pass graded it.
What moved area 6 is a different set of sites, none of them in the abstract, and none of them closed
by the rewrite: §4.4 denying that Chapter 6 reports p99.99, §6.3 promising a replacement §6.4.4
declines to be, and `tab:testbed`'s caption claiming a protocol the host missed on four rows. Level
4 asks that the whole text be consistent on the description of the research setup and the findings,
and those three are inconsistencies in exactly that.

Area 5 moved on the discussion chapter's own sites, so this is not the area-4 finding counted twice:
§7.2, §7.6 and `tab:threats` are chapter-7 text, and H1's revisit is chapter-7 text. A discussion
that says an instrument was not collected, one section after the results report its output, is a
failure of the reliability sub-factor. The insight, the register, the four-way validity analysis and
the ethics section are all untouched and all still read at 5, which is why this is 4.5 and not 4.

### Discounted

- `tab:abbrev` unreferenced: appendix glossary, reachable from the List of Tables. Every pass.
- `0.19 \%` at l. 3985: quoted from `gonzalez2023rustudp`, not a measurement of this study.
- The 71-word longest "sentence" comes from a table row. Read the stdev, 11.0.
- `.aitells.py`'s l. 717 gap: the tool strips `\emph{...}`. The source is fine.
- §6.4.4's refusal to quote the 512 kops/s point, where the Rust arms are bimodal at 37 per cent
  dispersion, is the same discipline as the pre-committed reading rule. It costs a load rather than
  rescuing one, and it is evidence for areas 3 and 5.
- "every percentile above it stays flat" (l. 2998) is loose: at the excluded top load p90, p99 and
  p99.9 are flat but pooled p99.99 moves both ways. The exclusion itself is right. Noted, not scored.

### Housekeeping

- The far-tail macros read `campaign-20260826-102047.hist.pooled.csv`, which `refresh_thesis.sh`
  never produces because it does not call `pool_hist.py`. One line closes that gap.
- The deck passes both its gates and is stale in content, which is the quiet failure mode. Its gates
  check layout and punctuation, not whether a slide still agrees with the thesis.
- `Thesis_Plan_v2.tex`'s timeline still schedules the campaign for September while its status
  paragraph records it as run.
- The skeleton's nine chapters against the draft's eight is still unresolved (`AGENT.md` §4).

### Outstanding

1. **Rewrite the abstract unaided, then set `\abstractunaidedtrue`.** Now **five** items in one
   edit: seven and seven, the practical-not-statistical median, jitter, the far tail that is no
   longer unsettled, and the switch.
2. **Seven editing fixes, under three hours, restoring area 5 to 5 and area 6 to 4.5.** Listed
   above.
3. **Analyse the allocation profile already on disk.** Half a day, moves three areas, and it is the
   only lift on the list that closes a cell in the threats table.
4. **Repeat the bare-metal campaign at the canonical configuration and toolchain.** The last thing
   holding area 3's data half below 5.

---

## Remediation pass — 26 August 2026, evening

Worked the eleventh pass's editing tier the same evening. **Every item on it is closed except the
abstract**, which is the author's alone. Areas 5 and 6 return to 5 and 4.5, so the mean goes back to
4.67, and area 4's two long-standing figure defects are closed as well. Declared length 103 pages
with 7 appendix pages, 118 physical, up one appendix page from the pass that graded it. The build is
clean on every gate and `refresh_thesis.sh` runs end to end.

| Area | Eleventh pass | After remediation | What moved it |
| --- | --- | --- | --- |
| 1 | 5 | **5** | Held |
| 2 | 5 | **5** | Held |
| 3 | 4.5 | **4.5** | Held deliberately. The toolchain is now named and `tab:testbed`'s caption is honest, which was the *reporting* half of the finding. The canonical-configuration repeat is still the measurement |
| 4 | 4.0 | **4.0** | Held deliberately, and it is now much closer to 4.5 than to 3.5. Every claims-about-the-evidence site is closed and so are all five figure defects. What is left is the abstract and the two analyses on data in hand, so this is the next area to move and the cheapest one |
| 5 | 4.5 | **5** | The three Chapter 7 statements denying collected instruments are rewritten, and H1's revisit now uses the campaign that settles H1's own clause |
| 6 | 4.0 | **4.5** | The level-4 consistency clause holds again: §4.4, §6.3, §5.6 and `tab:testbed`'s caption all describe the study as it is. Level 5 still waits on the abstract, exactly as the tenth pass argued |
| 7 | n/a | **n/a** | No manuscript settles it |
| **Mean** | 4.50 | **4.67** | |

### Finding 1 (the six denials): closed, all six

| Site | Now reads |
| --- | --- |
| §6.4.3 | "What this campaign cannot do is explain the gap, because the guest exposes no hardware counters", pointing at §`sec:baremetal` for the half it supplies |
| §7.2 | Names the counter result in mechanism, then scopes what is still open to the split inside the resident set, and says the allocation profile was captured and not analysed |
| §7.6 construct validity | p99.99 is reported on one host, and the question is now answered with a metric its own wording does not name |
| §7.6 conclusion validity | Same narrowing for the resource origin |
| `tab:threats` RQ3 row | Control column reads "Counters on the confirmation host (§6.4.4)", residual "Direction accounted for, the split inside the resident set not" |
| §4.4 | "The main campaign ... reports neither. The confirmation campaign carries both", and jitter is recorded and left undiscussed because no research question asks for it |

The honest half is preserved everywhere: the profile is described as captured and unanalysed rather
than quietly dropped, so the lift stays visible in the document instead of only in this file.

### Finding 2 (the far tail): four of five closed, the abstract remains

`tab:findings`'s RQ1 row now says this host resolves no tail ordering while a quiet host puts the
pooled p99.99 of the Rust variants below the C++ variants, with an evidence status of "unresolved
here, resolved on bare metal at one shard count". §7.1, `tab:threats`'s non-determinism row and
§6.3 follow. §6.3's "provisionally ... replaces these numbers" paragraph is replaced by a
description of the fourth dataset, which §6.3 previously did not describe at all, and its opening
count went from three campaigns to four.

### Finding 3 (the fifth variable): closed, and two more caveats added unprompted

§`sec:baremetal` now says the campaign "differs from the main sweep in four ways at once" and names
`g++` and `rustc` among them, then makes the toolchain change do some work: it is the only evidence
in the study separating either language from one implementation of it. `tab:testbed`'s caption no
longer claims the host met the right-hand column. It says which four rows it met and which three it
did not. Two caveats were added that no pass had asked for, both found while checking the capture:
no `isolcpus` or `nohz_full`, and the jitter sidecar was enabled on the confirmation campaign and
not on the sweep, so the two hosts' paired differences are comparable and their absolute footprints
are not.

### Finding 4 (the RSS ratio): closed at five sites

§1.4, `tab:findings`'s RQ3 row, §6.4.3, §7.2 and the conclusion all attach a host to the
order-of-magnitude phrasing, and §`sec:baremetal` now flags the collapse itself: both effects are
smaller on the confirmation host and the allocator's is smaller by far the more, so the ratio
narrows to roughly two with the arena count pinned identically. §7.2 states the general form, that
the ordering travels and the ratio does not. The non-negotiable claim is untouched.

### The figure and macro defects: all closed

| Item | How |
| --- | --- |
| `fig:effects` clipped axis label | **Not** by `bbox_inches`, which was tried and did not work: a tight bbox crops to the artists it can measure and the overhang was not one of them. Fixed by one shared `fig.supxlabel` instead of a per-axes copy, which is also better design since both panels plot the same normalised quantity. Verified by extracting the text from the PDF and by reading the render |
| `fig:borrowuaf` "only under AddressSanitizer" | Now "only under a sanitiser on a path a test exercises", which matches `taxonomy.csv`'s `detected,detected` |
| Diagram 11's inverted fan-out label | Now "so a 1-in-100 per-op delay is a 1-in-25 procedure delay". With the four ops the panel draws, $1-0.99^4 = 3.9\%$, so the label finally argues the amplification its own heading claims |
| Diagram 07's disowned per-call framing | The band now shows the direct A/B the harness runs, the same operation native against through the seam, with the two bars almost the same length because that is the finding. The crossing-against-round-trip ratio is gone |
| Diagram 07's typed numbers | A regression was introduced and then fixed. The first rewrite typed eight measured values into a hand-authored SVG, worse than the two it replaced. The statistics moved to the caption as macros and the band now types only the two bar lengths, which a bar chart cannot avoid |
| The five typed chapter-6 values plus the floor | Six new generated macros: `\PFiftyMedian` 80, `\PNineNineLightest` 245, `\PNineNinePreCliff` 6, `\RssAgree` 18/20, `\RssLowRunOffset` 31, `\BudgetFloor` 0.000061, and `\BmPFiftyMedian` 74. All seven were recomputed from the raw logs and match |
| `\SatKnee` used as a load-axis position | Reworded at all four sites. The sweep now "tracks to an offered `\TrackingLoad` where it plateaus at an achieved `\SatKnee`", the knee is described as bracketed by the rate ladder rather than pinned by it, `fig:loadsweep`'s caption no longer lists a knee marker it does not draw, and `tab:params`'s row is relabelled "Measured throughput plateau". §`sec:baremetal` already did it correctly and supplied the pattern |
| §5.6's "regenerates the artifacts verbatim" | Replaced. The scope is now "every result table, every plot of measured data, and every quoted number", with the two exclusions named: hand-drawn schematics are authored, and a rerun on another host regenerates by the same procedure and not to the same values, which §`sec:baremetal` is the worked example of. `bench/results-baremetal/` is now listed beside `bench/results/` |

### Two mechanical fixes to the pipeline

`bench/refresh_thesis.sh` now pools the bare-metal histogram sidecars before calling
`baremetal_facts.py`. Without that step the far-tail macros silently kept whatever
`gen_baremetal.tex` last held, which is the quiet-staleness failure mode the script exists to
prevent. And `rss_low_run_offset()` in `plot_figures.py` measures the contaminated-run offset by
splitting each variant's repeats at their largest gap rather than at a threshold, refuses a variant
whose runs are unimodal or whose low group is not a minority, and returns nothing when no variant
qualifies, so the macro is absent rather than zero on a campaign that does not show the defect.

### One number the pass had wrong, corrected here

The eleventh pass called the bare-metal CPU result a resolution of a guest non-result. It is not:
§6.4.3 already reports the below-saturation CPU comparison as clearing the correction under both
allocators, and the "reverses under jemalloc" reading came from a stale `docs/TODO.md` note about an
earlier campaign. What the bare-metal data adds is a cleaner confirmation, 16 of 16 points with one
sign, and the new `\BmCpu*` macros report it that way in §`sec:baremetal`.

### What is left

1. **The abstract.** Five items, author only, unchanged. It is now the sole blocker on area 6's
   level 5 and it is the last far-tail site in the document.
2. **Analyse the allocation profile.** Half a day. Area 4's cheapest remaining lift, and the
   document now says plainly that the profile exists and is unanalysed, so the gap is visible.
3. **Report the jitter that was collected, and add p99.99 to `tab:latency`.** Half a day.
4. **Rebuild the deck against the bare-metal results.** It still holds no `Bm` macro.
5. **Repeat the campaign at the canonical configuration and toolchain.** The measurement.

---

## Twelfth pass — 26 August 2026, late evening

Graded from `Ha_Vien_Mastersthesis_2026.tex` at its 18:18 state against a current build (PDF and log
both 18:23). Declared length **103 pages with 7 appendix pages, 118 physical**. Run deliberately as
an **audit of the remediation pass** rather than as a fresh look, because the remediation graded its
own work and that is the one thing rule 3 of the grading skill forbids. The question asked throughout
was what that pass broke or over-credited. No edits were made.

**The headline: the remediation over-credited itself by one area, and the reason generalises.** It
closed the five figure defects and the far-tail sync, and those really are closed. It also declared
the ninth-pass defect class closed, and that was wrong. **The class has two live members and both
were created or propagated by the remediation itself.** Area 5 goes back to 4.5 and area 4 stays at
4.0.

| Area | After remediation | This pass | Why |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Catalogue re-verified off `taxonomy.csv` at 7 and 7. H1's revisit is the strongest version on record |
| 2. Scholarly framework and sources | 5 | **5** | 109 of 109 cited, 66 per cent peer-reviewed venues, all keys survived two editing passes |
| 3. Research data and method | 4.5 | **4.5** | Method got *better* (three volunteered caveats in §6.4.4). Data held, and now carries a description defect in §6.3 |
| 4. Presentation of results | 4.0 | **4.0** | The figure defects are genuinely closed. The claims-about-the-evidence class is **not**, and its two live members are new |
| 5. Discussion and conclusions | 5 | **4.5** | **Disagreement with the remediation pass.** §7.2's RQ3 paragraph over-claims and under-claims at once, and both halves reach the findings and threats tables |
| 6. Academic text | 4.5 | **4.5** | Held. Body consistency is repaired. Two new finishing defects in Appendix D, both created by the remediation |
| 7. Work during the thesis process | n/a | **n/a** | No manuscript settles it |
| **Mean of the six assessable** | 4.67 | **4.58** | |

### Finding 1: the thesis declares open a question its own reported dataset answers

**Both bare-metal campaigns record jemalloc's own statistics in every run of their two jemalloc
arms, 480 runs in total.** The instrumentation was purpose-built in both languages
(`cpp/bench/jestats.hpp` with a weak `mallctl`, `je_stats()` in `rust/examples/bench.rs`), the system
arms correctly emit nulls and never zeros, and the seven fields are `allocated`, `active`,
`metadata`, `resident`, `mapped`, `retained` and `available`. Those fields decompose the resident set
into live allocation against arena bookkeeping against retained-but-unmapped, which is word for word
the split §7.2 calls unresolved.

**No generator in `bench/` reads them.** They reach no macro, no table, no figure and no sentence,
and §6.3 does not list them among the fields the confirmation dataset carries. The guest campaign has
none of them, so the capability arrived with the confirmation campaign and nothing was built on it.

Median over the 90 runs per arm at steady-state loads (offered $\ge 32$ kops/s), jemalloc arms of
`campaign-20260826-102047`, in MiB:

| Field | C++ | Rust | Rust − C++ |
| --- | --- | --- | --- |
| `allocated` | 0.78 | 0.62 | −0.16 |
| `active` | 1.43 | 0.79 | −0.64 |
| `metadata` | 4.19 | 6.26 | **+2.07** |
| `resident` | 11.02 | 9.10 | −1.92 |
| `mapped` | 42.82 | 44.83 | +2.01 |
| `retained` | 27.72 | 31.67 | +3.95 |
| peak RSS | 15.08 | 16.82 | **+1.74** |

**The answer in the data is better than the placeholder it would replace, and it is not the simple
one.** Rust holds less live data *and* less allocator-resident memory while its process peak is
higher, so the footprint difference is neither application data nor fully inside `jemalloc`. That
points at the Rust runtime's own fixed pages, which is sharper than what the thesis currently claims
and argues in the same direction as its conclusion. Two caveats belong in any write-up. Peak RSS is a
`getrusage` maximum while the `je` figures are sampled at a point, so the two are not strictly
commensurable. And the C++ arm links the distribution `jemalloc` while the Rust arm builds 5.3.1 from
source, which `docs/TODO.md` Phase 11 item 3 already records as a confound on any metadata
comparison. Note also that this reproduces at campaign scale what that TODO item recorded from a
single laptop run (4.1 against 6.2 MiB of metadata), so the finding is not new to the repository,
only to the thesis.

Estimated cost: **two hours**, not the half day the previous passes assigned to the profile. The
allocation profile answers a different question, call-site attribution, and is still worth having.

### Finding 2: four sites give the counter result the wrong job

The counters are a real result and they explain something real, the operation-level timing difference
§6.4.1 had previously argued from structure. What they cannot explain is peak RSS. §6.4.3 states in
its own words that the gap is runtime and allocator-arena overhead and a fixed cost rather than a
per-context one, and an operation's cache-miss rate does not generate fixed overhead. If anything the
causal arrow runs the other way, since a larger resident set is a reason to miss cache more often.

| Site | What it says | Provenance |
| --- | --- | --- |
| §6.4.4 l. 3056 | "Less work and worse locality is one account of both RQ3 results at once" | The bare-metal integration (`240346a`), **not** the remediation |
| §7.2 l. 3761 | "a plausible account of a larger resident set and a faster operation at once" | Propagated by the remediation |
| `tab:findings` RQ3 | "direction accounted for by counters" | The remediation. Right conclusion, wrong instrument |
| `tab:threats` RQ3 | Control "Counters on the confirmation host", residual "Direction accounted for" | The remediation |

The mirror of it, in the same paragraph and the same two tables: the split is declared unresolved and
pinned on an instrument the campaign already holds. §7.2 l. 3762, `tab:findings`'s "split within the
resident set open", and `tab:threats`'s "the split inside the resident set not".

**Why this costs area 5 and not only area 4.** One paragraph of the discussion over-claims and
under-claims at the same time, on the same result, and both halves reach the findings table and the
threats table. The threats table *is* the reliability apparatus, so a wrong entry there fails the
sub-factor the area scores rather than being a reporting slip. Everything else in area 5 is still
exceptional, which is why this is 4.5 and not 4. The over-claim is hedged ("one account", "a
plausible account"), which is why it is an imprecision rather than a false claim, but the pairing of
the two errors in one paragraph is not defensible.

### Finding 3: two defects the remediation created, both in Appendix D

- **The intro contradicts its own table.** The caption was fixed to say the confirmation host met the
  protocol on four aspects and missed it on three. The paragraph four lines above still says
  "Section~\ref{sec:baremetal} reports a campaign that **satisfies** it". One of the two was edited
  and the other was not, which is the eleventh pass's failure mode reproduced at small scale while
  fixing it.
- **The opening page is 80 per cent white.** Four lines of text and nothing else, because
  `tab:testbed` at `[tp]` floats to the following page. **That stranded page is what took
  `\appendixCount` from 6 to 7.** It is exactly the diagnosis `AGENT.md` §5 gives for this shape, so
  the fix is a per-table float change and not a prose cut.

### Finding 4 (smaller): two descriptions the remediation got wrong

- §6.3's new paragraph says the confirmation dataset has "the same record shape as the sweep and two
  additions". It has at least three kinds of addition, and one of them is Finding 1: `je`,
  `jitter_ns`, and four latency fields (`p25`, `p75`, `p9999`, `stdev`) that §6.3's own enumeration
  of the sweep's record does not include. The section whose job is describing the data understates
  what was captured, which is why Finding 1 was invisible.
- §5.6 says a rerun on another host regenerates by procedure and not by value, and calls
  §`sec:baremetal` "exactly that exercise". It is not a rerun of the campaign, it is a different
  design, which §`sec:baremetal` spends a closing paragraph establishing.
- §7.2's paragraph lost its structure: it announces two bounds, digresses into a mechanism, then says
  "A third bound belongs here."

### What the remediation genuinely closed, verified again

- All five figure defects, checked by rendering and not by reading the source. `fig:effects`' axis
  label is whole, `fig:borrowuaf`'s caption matches `taxonomy.csv`, diagram 11's label argues the
  amplification its heading claims, diagram 07's band shows the direct A/B.
- Four of the five far-tail sites. The abstract is the fifth and is the author's.
- The `\SatKnee` axis confusion, at all four sites.
- Every typed measured value in Chapter 6, through seven new macros, all recomputed and matching.
- The toolchain named in §6.4.4, and three caveats volunteered there that no reviewer asked for.
  Those are area 3 evidence and should not be edited away.

### Lifts, ordered by cost

| Work | Kind | Cost | Areas |
| --- | --- | --- | --- |
| Fix Appendix D's intro sentence to match its caption | Editing | 5 min | 4, 6 |
| Move `tab:testbed` off `[tp]`, one table at a time, to close the white page | Editing | 10 min | 6 |
| Fix §6.3's record-shape sentence and §5.6's "exactly that exercise" | Editing | 15 min | 3, 4 |
| Re-attach the counters to the operation-level result at all four sites | Editing | 30 min | 4, 5 |
| Repair §7.2's "two bounds … a third bound" enumeration | Editing | 10 min | 5, 6 |
| **Read the `je` statistics and write the split**, then rewrite the four "unresolved" sites | Analysis on data in hand | **2 h** | 3, 4, 5 |
| Allocation profile, for call-site attribution | Analysis on data in hand | Half a day | 3, 4 |
| A figure for §`sec:baremetal`, jitter, and p99.99 in `tab:latency` | Analysis on data in hand | Half a day | 3, 4 |
| Rebuild the deck. Zero `Bm` macros, and l. 1052 still contradicts the thesis | Editing artefacts | 1 h | Repository |
| Canonical-configuration repeat, on the sweep's toolchain, with `isolcpus` | New measurement | ~2 h | 3, 4 |
| Rewrite the abstract unaided | Author only | One sitting | 6, and 4 follows |

The first five are about seventy minutes and restore area 5 to 5. The two-hour row is the next one
worth doing, because it is the only item that moves three areas without new measurement.

### The durable lesson from today

Three passes and two remediations in one day produced one clear rule. **A remediation pass must not
grade its own work**, because the two failures it is most likely to make are invisible from inside
it: propagating a claim it did not originate (the counters), and fixing one half of a pair (the
Appendix D caption without its intro). Both happened. The second rule is narrower and just as
useful: **closing a sentence is not closing the claim inside it.** Every site that said "the profiles
were not collected" was rewritten, and not one of them asked whether the question those profiles were
for had already been answered by a different instrument in the same dataset.

### Outstanding

1. **The abstract.** Five items, author only. Still the sole blocker on area 6's level 5.
2. **Seventy minutes of editing**, listed above, restoring area 5 to 5.
3. **Two hours on the `je` statistics.** The highest-value item in the project, and it needs no
   measurement, no rented machine and no new code beyond a reader.
4. **Repeat the campaign at the canonical configuration and toolchain.** Still the only thing holding
   area 3's data half below 5.

---

## Remediation pass — 26 August 2026, night

Worked the twelfth pass's list. **Items 1 to 5 of its lift table are closed, and so is the two-hour
`je` item, which was the point of the exercise.** Declared length **104 pages with 6 appendix
pages, 118 physical**: the new subsection and table cost two pages and the two layout fixes gave one
back, for a net of one page against the 103 the twelfth pass graded.

| Area | Twelfth pass | After this pass | Why |
| --- | --- | --- | --- |
| 1 | 5 | **5** | Held |
| 2 | 5 | **5** | Held |
| 3 | 4.5 | **4.5** | Held deliberately. The description defect in §6.3 is fixed and the campaign's own instrument is now used, but the canonical-configuration repeat is still the measurement |
| 4 | 4.0 | **4.5** | Both live members of the defect class are closed, §`sec:baremetal` has a float, and the RQ3 memory result is located rather than bounded by elimination |
| 5 | 4.5 | **5** | §7.2's paragraph no longer over-claims or under-claims, and its enumeration is repaired |
| 6 | 4.5 | **4.5** | Two finishing defects closed, both stranded pages recovered. The abstract still holds level 5 |
| 7 | n/a | **n/a** | |
| **Mean** | 4.58 | **4.75** | Highest on record since the first remediation pass |

### The `je` result, written up

`bench/baremetal_facts.py` gained `je_facts()` and `write_resident_table()`. Twenty-six macros and
`figures/tab_resident.tex`, all recomputed from the raw logs and matching. The new §`sec:baremetal`
paragraph group reports three readings, in the order they change the claim:

1. **The bookkeeping is fixed.** Arena metadata costs the Rust build $+2.07$ MiB more and that
   figure moves by $0.5\%$ across the whole swept range, so it is a constant of the process. This
   *measures* what §6.4.3 previously argued by elimination from the struct layout. Rust holds
   $0.16$ MiB **less** live allocation, which settles outright that the larger resident set is not
   more application data.
2. **The finding relocates.** `jemalloc`'s own resident bytes are $1.92$ MiB **lower** in the Rust
   build while its peak resident set is $1.74$ MiB higher. Paired inside each run, the footprint
   outside the allocator's mappings is $4.0$ MiB for C++ against $7.9$ for Rust, a difference of
   $+3.8$ MiB. **So the peak-RSS language effect is not an allocator effect at all**: it is the
   standard library and runtime a Rust process carries before it allocates, and the allocator
   comparison runs the other way and partly offsets it.
3. **A negative result about the guest.** The bimodality that costs peak RSS under `jemalloc` its
   place in `tab:significance`, a handful of runs $31$ MiB low, does not appear here: no arm's peak
   RSS spans more than $1.7$ MiB across its repeats. That defect belonged to the host, which is what
   the reading rule of §`sec:stats` assumed without being able to show.

Two caveats are stated in the text rather than left for a reader to find. Peak RSS is a `getrusage`
maximum while the `je` figures are sampled once, so the outside-mappings figure is an upper bound.
And the derived row is a median of per-run differences and not a difference of medians, because the
two figures come from one process at one moment, so **the table's column does not sum exactly**
(15.06 against 15.08 for C++, 16.96 against 16.82 for Rust). The caption says so. Pairing inside the
run is the better method and it is what `_paired_effect` does elsewhere, so the arithmetic slack is
the honest cost of the better statistic.

**This also closes the twelfth pass's other area-4 finding for free**: §`sec:baremetal` now has a
float, and `tab:resident` is exactly the kind of six-row decomposition a table is for.

### The counter over-claim, closed at all four sites

§`sec:baremetal` now says the counters are "a mechanism for the operation-level result" and adds the
sentence that was missing: "It says nothing about the resident set, and the worse locality is not
evidence that it does: a larger footprint is a reason to miss cache more often, so the two are
related in the opposite direction." `tab:findings` reads "resolved, and located outside the allocator
by its own accounting". `tab:threats`'s row reads "RQ3 captures resource cost, and its origin outside
the allocator" against a residual of "Which runtime pages carry it is not attributed to a call
site", which is the honest remaining gap and is what the allocation profile is actually for. §7.2's
paragraph is rebuilt around three bounds with the third being the new location, and it opens "Back to
the memory penalty" because the antecedent had drifted two paragraphs away.

### The four smaller items

| Item | Fix |
| --- | --- |
| Appendix D's intro contradicting its caption | Now "not fully satisfied either", pointing at the caption's itemisation |
| Appendix D's 80-per-cent-white opening page | `tab:testbed` moved from `[H]` to `[ht]`. **The cause was `[H]`, not `[tp]`**: `[H]` forbade the following text from flowing back into the gap. Recovered the seventh appendix page |
| §6.3's "same record shape and two additions" | Now three ways, naming the wider latency block, the sidecars and counters, and the allocator accounting, with the system arms' nulls explained on the same principle as the governor state |
| §5.6's "exactly that exercise" | Now "demonstrates on a campaign of its own design". Shortened in the same edit, because the first version spilled a line onto a near-empty chapter-tail page |

### Two layout lessons

- **The stranded appendix page was caused by `[H]`, and the fix was to float the table.** Every
  earlier length pass in this repository moved tables *to* `[H]` or measured `[tp]` as worse. This is
  the first case of the reverse, and it is the mechanism `AGENT.md` §5 describes rather than an
  exception to it: `[H]` forbids reflow, so a table that does not fit under its own intro strands the
  page. Diagnose before choosing a direction.
- **A two-line prose addition stranded a different page.** The §5.6 edit pushed a chapter's last
  line onto a page of its own. Tightening the same passage recovered it. That is the trap
  `AGENT.md` §5 names: shaving words moves nothing until a whole line comes out.

### What is left

1. **The abstract.** Five items, author only, unchanged, and it is now the only thing holding area 6
   at 4.5 rather than 5.
2. **The allocation profile**, for call-site attribution. Half a day. Its scope is now stated
   correctly in `tab:threats`: which runtime pages carry the footprint is not attributed to a call
   site.
3. **Jitter and the p99.99 column in `tab:latency`.** Half a day.
4. **Rebuild the deck.** Zero `Bm` macros, and one slide still contradicts the thesis.
5. **Repeat the campaign at the canonical configuration and toolchain.** The only thing holding
   area 3's data half below 5.
6. **A pass that did not write any of this.** Two remediations in a row have now been audited by a
   grading pass and both were found to have over-credited themselves. This one should be too.

---

## Dataset promotion — 27 August 2026, evening

**This is a record, not a grading pass.** No criterion is scored here. The work described below was
done by the same session that would be grading it, and the standing rule in this file is that a
remediation pass must not score its own output. A fresh pass is the open item.

### What happened

The canonical-configuration bare-metal repeat, named as the last measurement outstanding by every
pass since the ninth, ran on 27 August and is now the thesis's main dataset:
`bench/results/campaign-20260827-151927.jsonl`, 1120 runs at 7 shards, 7 producers, 20 repeats, 14
load levels, zero errors, all 1120 histograms verified against the printed percentiles. AMD EPYC
7443, SMT off, `performance` governor with boost off, `nohz_full` on the pinned cores, no
hypervisor, toolchain pinned in the Rocky container so it matches the guest campaign's.

45 of 98 generated macros changed. Every chapter was synced in the same pass, which is the lesson the
eleventh pass paid for: when a dataset lands, the summary tables, the threats table, the hypothesis
revisit and the statistical-treatment section are where a grader looks and where the previous
integration failed.

### What the data settled

**The far tail, which had been open since the first pass.** At the representative load the widest
95% interval on one variant's p99 is now 1 µs against a between-variant range of 2 µs. On the guest
those were 1480 and 293 µs, inverted by a factor of five. p99 fell from 4518 to 78 µs while the
median barely moved, 80 to 70 µs. `NSignificant` 9 → 14 of 14, `NTailExclZero` 0 → 4,
`NEqvUnresolved` 5 → 0, `RssAgree` 18/20 → 20/20.

**Both standing analysis items landed in the main tables.** `tab:latency` gained its p99.99 column,
which was blocked on data rather than on effort: the guest campaign records no `p9999` field at all.
`tab:jitter` is generated and placed in §6.4.2 with its own paragraph.

**The peak-RSS bimodality was the machine's.** 31 MiB on the guest, 1 MiB here, so the reading rule
§`sec:stats` fixed in advance for that row was never needed on adequate hardware. It stays stated,
because a design that only declares its reading rules when they rescue a result is not applying them.

### The one claim the data overturned

`AGENT.md` non-negotiable #5 said the allocator effect on peak RSS is the larger of the two. It is
not, on either bare-metal host:

| Host | THP | Language effect | Allocator effect |
| --- | --- | --- | --- |
| KVM guest, 12 Aug | `always` | 1.8–3.5 MiB | **32.5–34.3 MiB** |
| Bare metal, 26 Aug (8/8/15) | `madvise` | 0.7–1.8 MiB | 1.9–3.2 MiB |
| Bare metal, 27 Aug (reported) | `madvise` | 1.4–2.5 MiB | **1.5–2.4 MiB** |

The language effect is stable on all three. The allocator effect is not, and the guest is the outlier
of three rather than one reading of two. Transparent hugepages differed and only the
system-allocator arm inherits that policy, so it is the named candidate, but the study never varied
it with everything else fixed and **the thesis does not claim causation**. Chapter 8 now names that
experiment as the immediate priority, replacing the canonical repeat.

The rule was rewritten rather than defended. That is the right direction: this file's own standing
instruction is to fix the prose to match the artefact and not the artefact to match the prose.

### Two measurement failures, both invisible from inside the dataset

**1. `isolcpus` put an entire 1120-run campaign on one core.** The first attempt on 27 August booted
with `isolcpus=2-17`, which removes those cores from every scheduling domain. The benchmark pins to a
*range* and relies on the kernel to spread 14 threads, so all of them inherited `cpu2`. `cpu2` at
85.9% busy with `cpu3`–`cpu17` at exactly 0.0%. `cpu_pct` flat at 100.1% in all 1120 records. Plateau
84 kops/s against 336 on the guest and 448 on 26 August. **Every record looked individually
plausible**, and the defect was found only by comparing three campaigns against each other before
touching the thesis.

**2. `systemd-detect-virt --vm` prints `none` and exits non-zero on bare metal**, so a
`|| echo none` fallback appended a second line and `host_virt` never compared equal to `"none"`.
`docker/run.sh` therefore warned that the far tail stays unresolved on the one host where it can be
resolved, and wrote the same value into the provenance records.

Both are now guarded in the tooling rather than in a note:
`bench/canonical_repeat.sh check-spread` refuses to start a campaign whose work lands on about one
core (broken config reads 100% `cpu_pct`, fixed reads 688%), `run` hard-fails on `isolcpus`, and
`bench/TESTBED.md` §2 no longer recommends it.

**The durable lesson.** The ninth pass's lesson was that a hand-maintained table drifts, so generate
it. This pass adds the measurement equivalent: a campaign can be internally consistent, pass every
existing gate, and still measure the wrong thing, so the guard belongs in the harness at the point
where the cost of being wrong is minutes rather than hours.

### A methodology change worth grading later

`ReprLoad` is now pinned (`REPR_LOAD_OPS = 56000` in `bench/plot_figures.py`) rather than derived,
with the old rule kept as `deadline_limited_load()`. The old rule took the busiest load holding p99
under 5 ms. On the guest that returned 56 kops/s because p99 there was 4667 µs, a hair under the
threshold, so it was locating the host's noise floor. On a quiet host the same rule climbs until
capacity binds and returns the tracking limit, collapsing the representative point onto the knee at
392 kops/s. One rule, two quantities, decided by how noisy the machine was. A grader should check
whether §`sec:workload`'s new wording earns the change or merely announces it.

### Build state

118 physical pages. Zero LaTeX errors, zero undefined references, zero warnings. One overfull box,
pre-existing, in a running header. `./.aitells.py`: zero semicolons, sentence-length stdev 11.3, all
14 dash hits numeric ranges or a compound proper name. `bench/refresh_thesis.sh` runs end to end.
Rollback point: `archive/rollback-20260827-220354` (at the repository root as `.rollback-20260827-220354` until 8 September 2026).

### What is left

1. **The abstract.** Author only, five defects, and it is the only thing holding area 6 below 5. It
   still ends "The far tail below saturation cannot be settled on a virtualised host", which the same
   document now contradicts, so it is a consistency defect and not only a style one.
2. **A grading pass that did not write any of this.** Three remediations in a row have now gone
   ungraded or been found to over-credit themselves. Areas 3 and 4 are the ones to check: both were
   held at 4.5 solely by the measurement that has now been made.
3. **The transparent-hugepage experiment**, which is the only open question the data raised rather
   than answered.

---

## Thirteenth pass — 27 August 2026, night

Graded from `Ha_Vien_Mastersthesis_2026.tex` against a build verified current: source, PDF and
`build/Ha_Vien_Mastersthesis_2026.log` all written at 22:29 on 27 August. Declared length **104 pages
with 6 appendix pages, 118 physical**. This is the fresh pass the dataset-promotion record asked for,
and it wrote none of the work it grades. Graded as a full draft, the standard `AGENT.md` §1 sets for
this file. No edits made.

**The headline: the campaign the thesis waited five passes for is excellent, and the document lost a
quarter of a grade point because the prose describing it did not follow.** Area 3's data half is
closed and reads at 5 for the first time on record. Against that, the promotion's claim that "every
chapter was synced in the same pass" does not hold: thirteen sites still describe a study measured on
a virtual machine, and thirteen statements in the results and discussion chapters disagree with the
artefact beside them. **This is the eleventh pass repeating, at larger scale and with one new defect
class.**

Graded against the 22:29 state of the source. Two §1.4 sites were repaired at 23:34 while this entry
was being written, which is why the far-tail count reads thirteen and not fifteen. Line numbers below
are taken from the later file. That repair is discussed under Finding 6, because of what it did to
Finding 1.

| Area | 12th pass | 3rd remediation claim | This pass | Why |
| --- | --- | --- | --- | --- |
| 1. Objective and research questions | 5 | 5 | **5** | Gap located in a named flaw of the closest prior work. Catalogue re-verified off `taxonomy.csv` at 7 and 7. The RQ1 metric item is now a live inconsistency rather than a cosmetic one |
| 2. Scholarly framework and sources | 5 | 5 | **5** | 109 of 109 cited, 66 per cent peer-reviewed venues, contrary results reconciled in mechanism, replication status stated per finding |
| 3. Research data and method | 4.5 | 4.5 | **4.5** | Same number, **different reason**. The data half is now 5. The *description* of the method is what holds it, on two counts |
| 4. Presentation of results | 4.0 | 4.5 | **4.0** | **Disagreement with the remediation.** Thirteen prose-against-artefact statements, six of them wrong rather than stale, four inside one subsection |
| 5. Discussion and conclusions | 4.5 | 5 | **4.5** | **Disagreement with the remediation.** Four chapter-7 sites still describe a virtualised host. Same failure as the eleventh pass |
| 6. Academic text | 4.5 | 4.5 | **4.0** | Level 4's consistency clause fails on all four things it names. Same clause and same mechanism as the eleventh pass |
| 7. Work during the thesis process | n/a | n/a | **n/a** | No manuscript settles feedback uptake, independence or schedule |
| **Mean of the six assessable** | 4.58 | 4.75 | **4.50** | Lowest since the eleventh pass, and for the same cause |

Canvas: `thesis-grade-csm-aug27.canvas.tsx`.

### What the campaign bought, stated first because it is the larger fact

`bench/results/campaign-20260827-151927.jsonl` is the main dataset: 1120 runs at the canonical
7 shards, 7 producers, 14 load levels, 20 repeats, zero errors, AMD EPYC 7443, `virtualisation:
none`, SMT off, `performance` governor with boost off, `nohz_full` on the pinned cores, toolchain
pinned in a container so the host comparison isolates hardware alone. `\PNineNineMaxCI` is 1 µs
against a between-variant `\PNineNineRange` of 2, where the guest had 1480 against 293. All 14 tests
clear Holm. `tab:latency` has its p99.99 column and `tab:jitter` is placed.

Mechanically the document is clean: zero LaTeX errors, zero undefined references or citations, no
multiply-defined labels, no float too large, no overfull boxes, no placeholders, abstract form fits
its box, 109 of 109 bibliography entries cited. `./.aitells.py`: zero semicolons, sentence length
21.7 ± 11.3, all 14 dash hits numeric ranges or `Herfindahl--Hirschman`. **No table or figure holds a
wrong measured value, which is now six passes running.**

### Finding 1: the p99.99 is not computed the way two sections say it is

**This is the most serious item and it is the one to fix first.** §4.5 l. 1608 says "Its p99.99 is
pooled across repeats by exactly the procedure described above, and reaches Table~\ref{tab:latency}
as a column of its own". §6.4.1 l. 2443 says predictability is evidenced "from pooled histogram
buckets rather than per-run summaries".

`write_latency_table()` in `bench/plot_figures.py` builds the cell as
`med_ci_cell([r["lat_ns"]["p9999"] ...])`: a **median of the twenty per-run p99.99 values** with a
bootstrap interval. `plot_figures.py` opens no pooled file anywhere, and the `\FarTail*` macros use
the same per-run field. §4.5 argues on the same page that a single run retires about 170 thousand
operations so its p99.99 "rests on roughly seventeen observations" and is "dominated by sampling
noise even on a perfectly quiet host". **By the thesis's own argument the number it prints is the one
that means nothing.**

The pooled data exists. `bench/results/campaign-20260827-151927.hist.pooled.csv` is on disk with
3 360 051 to 3 360 084 operations per group, at the representative load:

| Variant | As printed (median of 20 per-run p99.99) | Pooled |
| --- | --- | --- |
| C++ system | 135.0 µs | 142.0 µs |
| C++ jemalloc | 135.6 µs | **176.4 µs** |
| Rust system | 89.2 µs | 92.1 µs |
| Rust jemalloc | 83.6 µs | 89.5 µs |
| between-variant range | 52 µs (`\FarTailRange`) | **87 µs** |
| spread | 62 % (`\FarTailSpread`) | **97 %** |

**The direction survives and the effect is larger pooled, so fixing this strengthens the finding.**
Two pieces of pipeline work close it: point the generator at the pooled CSV, and add `bench/results/`
to `refresh_thesis.sh`'s pooling loop, which still globs only `bench/results-baremetal/`. The
script's own comment names this exact failure as "the quiet-staleness failure mode rather than a loud
one", so the warning was written and then not applied to the new directory.

### Finding 2: six statements in §6.4 are wrong against their own tables and figures

This is a **new defect class** for this thesis and it is not staleness. These are claims that were
true of the guest and that the new data **reverses**, so a sweep grepping for "virtualised" or
"unresolved" catches none of them.

| Site | Claim | Artefact |
| --- | --- | --- |
| l. 2425 | "every pair of confidence intervals overlaps, so the table on its own separates nothing" | `tab:latency` separates every C++/Rust pair at the median, 73.5--73.7 against 72.3--72.5. Four of the six pairs do not overlap. The passage that follows describes a distance that no longer exists |
| l. 2558 | "Peak resident set size under jemalloc is the one upper-block row that does not clear it" | `tab_significance` gives that row Holm $0.000027$. `\NSignificant` is 14 of 14, and the sentence before prints 14 of 14 then enumerates nine rows. §6.4.3 states the correct version four pages later |
| l. 2575 | "The `\NEqvUnresolved` rows the correction does not clear are not all saying the same thing" | `\NEqvUnresolved` is 0, so it prints "The 0 rows ..." |
| l. 2578 | tail bounds "run out to `\EqvBoundTailMax` µs, wider than any difference a deployment would care about ... the campaign declining to answer" | Every row of `tab_equivalence` reads *significant* and the widest tail margin is 5 µs. Written for the guest, where five rows did not resolve and the bounds ran to 1480 µs |
| l. 2718 | the four variants "climb together and gently, from `\PNineNineLightest` µs at the lightest load to single-digit milliseconds by the top of that region ... from `\PNineNinePreCliff`~ms to several seconds" | p99 runs 78.3 µs at 7 kops/s **down** to 74.1 µs at 392. It never climbs and never reaches a millisecond. `fig:loadsweep`(a) draws a flat line. `\PNineNinePreCliff` rounds to **0**, so the cliff is anchored at "0 ms" |
| l. 2745 | "The knee also sits at the same place for all four variants" | Both Rust arms hold their offered rate to 448 kops/s; both C++ arms collapse there to ~162. `fig:loadsweep`(b) draws it. `\SatKnee` is the *minimum* across variants, so the macro conceals a 14 per cent capacity difference the prose then asserts is absent |

Three more of the same family, all captions or cells: `tab:significance`'s caption still reads
"Measured on the virtualised Xeon host"; `tab:resource`'s caption and §6.4.3 l. 2934 say peak RSS is
"the one metric here whose intervals separate the four variants cleanly", where C++/jemalloc
[12.5, 12.6] and Rust/system [12.4, 12.7] overlap visibly in `fig:resources`(a) and CPU separates the
languages cleanly; and `tab:findings`'s RQ1 headline cell contradicts its own *Evidence status* cell
in the same row.

### Finding 3: an unreported result, and it favours Rust

At **448 kops/s** both Rust arms serve the full offered rate (447.9 achieved) while both C++ arms have
already collapsed to about 162. Rust is ahead by a factor of 2.8 at the load where the C++ arms first
stop coping, in 20 repeats under both allocators. **No page of the thesis mentions it.** The overload
comparison is made at 784 kops/s, where C++ leads 147 to 84, and that operating point is
pre-committed and defensible. But the document asserts a shared knee, reports the rung that favours
C++, and is silent on the rung that favours Rust. §6.4.4 holds out an analogous metastable rung on
the second bare-metal host and explains why, which is the pattern to copy.

### Finding 4: the pre-committed reading rule is broken where it first costs something

§4.5 fixes in advance that intervals in `tab:significance`'s second block "are not read as findings
however far from zero they sit", and names the failure the pre-commitment exists to prevent:
"Applying the rule to the block that suits the argument and quietly dropping it for the other".
§6.4.1 l. 2441 then says the tail rows "carry a finding rather than a shrug" and grounds it in exactly
the barred instrument, "resolve with a paired interval excluding zero". `fig:effects` still shades
those rows *not read as findings*.

**The finding itself is fine** and the fix is cheap: the tail rows clear Holm at $0.000027$ and
$0.00016$, and a $p$-value is not what the rule bars. Justify from Holm, or argue explicitly that the
rule's premise weakened once the hypervisor was gone. Left as written it reads as dropping the rule
the moment it stopped paying, which is the one thing §4.5 promises not to do. **This is what holds
area 3 rather than any property of the data.**

### Finding 5: §6.2 states a load-selection rule the code abandoned

`REPR_LOAD_OPS = 56000` is pinned in `plot_figures.py`, with the old rule kept as
`deadline_limited_load()` and a docstring giving the reason: on the guest the derived rule returned
56 kops/s because p99 there was a hair under 5 ms, so it was locating the host's noise floor, and on
a quiet host the same rule climbs until capacity binds and returns 392, collapsing the representative
point onto the knee. **The reasoning is good and the thesis does not carry it.** §6.2 l. 2322 still
says "Two derived values are used throughout what follows. The representative operating point is not
chosen by eye. It is the busiest swept load at which all four build variants still hold their p99
below $5$~ms". On this host that rule returns 392, not 56. The dataset-promotion record flagged this
for a grader to check; the answer is that the new wording announces nothing, because there is no new
wording.

### Finding 6: four chapter-7 sites and eleven others still describe a virtual machine

Scored against area 5 from the chapter-7 sites only, so it is not Finding 2 counted twice.

- §7.2 l. 3780: the far tail is "a null this host cannot turn into an ordering", and "a quiet machine
  does turn it into an ordering". The reported campaign is the quiet machine.
- §7.7 l. 4546: "the measurements were taken inside a virtual machine that does not expose frequency
  or turbo control and that records non-zero CPU steal", four pages after `tab:testbed` prints
  `virtualisation: none` and a governor verified on the machine.
- §7.8 l. 4665: "Tail-latency numbers from a virtual machine with non-zero CPU steal are not a sound
  basis for a production commitment", which disowns evidence the thesis now has.
- `tab:threats` l. 4472 and l. 4478: the external row still lists "A virtualised measurement host" as
  a live threat with "steal non-zero" as its residual, and the conclusion row still reports peak RSS
  under `jemalloc` as read from its interval against its $p$-value, which §6.4.3 says was not needed
  here.

Nine more outside chapter 7, scored against area 6: §6.4's opening l. 2407, l. 2582,
`tab:significance`'s caption l. 2527, `tab:findings`'s RQ1 cell l. 3737, Chapter 8 l. 4716,
`fig:cliff`'s caption l. 1306 ("the development host cannot resolve it"), `tab:vendortheses`' caption
l. 4340, Appendix D's intro l. 4879 ("itemises both machines ... the guest of
Section~\ref{sec:testbed} that every table in this thesis is drawn from", above a three-column table
whose first column is bare metal), and `ai_statement.tex` l. 67.

**Two §1.4 sites were closed while this pass was being written**, at 23:34, and the line numbers above
are from the file after that edit. §1.4 l. 574 now reads "The far tail in the same regime now resolves
on the reported host" and l. 586 replaces "a virtualised measurement host" among the four limitations
with "an allocator footprint whose size moved with the host", which is the better limitation to name.
**The new sentence carries the pooled claim of Finding 1 forward**, so the sync propagated an unchecked
claim into freshly written prose. That is pattern 2 of this file's own list, observed live, and it is
the argument for doing Finding 1 before the rest of the sync rather than after.

**H1's revisit is correctly synced**, and so is the §7.1 introduction, `tab:findings`'s *Evidence
status* column, `tab:testbed` itself, `tab:vendortheses`' own row and §7.7's construct-validity
paragraph. The pattern is the eleventh pass's third shape exactly: **half a pair fixed**, repeatedly,
with the caption right and the paragraph above it wrong, or the table row right and the headline cell
in the same row wrong.

### Finding 7: four macro misuses, and two hand-typed values are back

- §6.4.4 l. 3161 uses `\RssLowRunOffset` (1 MiB, this host) where `\GuestRssLowRunOffset` (31) is
  meant, so the sentence contrasts a 1 MiB defect against a 1.7 MiB spread and defeats itself. Two
  paragraphs earlier, l. 3072, the same contrast uses both macros correctly.
- l. 3073 uses `\RssAgree` (the per-repeat sign agreement for one row, 20/20 repeats) as a count of
  "resource comparisons".
- l. 3039 compares `\GuestPNineNine` (guest p99 at the representative load) against
  `\PNineNineLightest` (this host's p99 at the *lightest* load). The magnitudes happen to work, the
  quantities do not.
- §7.2 l. 3779 types "$80\,\mu$s operation", the guest's median, where `\PFiftyMedian` is 70.
- §7.7 l. 2563 types "$18$ of $20$ repeats", the guest's agreement count. **This was closed by
  `\RssAgree` at the third remediation and has come back as prose.**

### Area-by-area reasoning, where it is not obvious from the table

**Area 1 holds at 5.** The level-5 clause is about topic significance and it plainly holds. The one
item worth naming: RQ1 names "median, p99 and p99.9 tail latency, and the maximum", the decisive
result of the study is now the p99.99 far tail, and §7.7 l. 4504 asserts that "RQ1 names the statistic
that decides it". While the statistic was unavailable the narrowing was honest. Now the question and
the answer disagree and one sentence claims otherwise, so this is CALIBRATION check 8 firing. Ten
minutes either way.

**Area 3 keeps 4.5 for a new reason, and this is the substantive news of the pass.** It has been 4.5
since the third pass because the *data* half was 4 for want of adequate hardware. That is closed. The
half now holding it is the *description*: Finding 4 (the pre-commitment broken in its own results
section) and Finding 5 (a selection rule the code abandoned). Level 5 asks for methods analysed in
depth, and a document that states a rule it does not follow has not been. Both are prose fixes of
about half an hour, which makes this **the cheapest 5 on the sheet**.

**Area 4 goes to 4.0** on level 5's clause that the reporting of findings and use of pictures and
tables be "well considered and apt". Thirteen statements disagree with the artefact they describe,
six of them wrong rather than stale, two of them checkable by eye against `fig:loadsweep`, and one of
them a false claim about how the headline statistic was computed. Level 4 holds: the structure, the
per-question evidence status and the generalisability discussion are intact, and no value in a table
or figure is wrong.

**Area 6 goes to 4.0** on level 4's consistency clause, and it fails on all four of the things that
clause names: research questions (RQ1), description of the research setup (§6.2, §4.5's pooling claim
and its "isolating the cores" where §6.1 explains at length why `isolcpus` is deliberately absent,
§4.6's results directory, Appendix D's intro), findings (Finding 2), conclusions (Chapter 8, §7.8,
`tab:threats`). Graded separately from the abstract, per the tenth pass's reasoning, but **submitted
as it stands that abstract puts this area at 4.0 on its own**: it still says five injected classes and
five further classes where the body says seven and seven, still says median latency matches, still
names jitter in the *Objective* and never reports it, and still ends "The far tail below saturation
cannot be settled on a virtualised host", which is the thesis's principal new result stated
backwards.

### The lift list, by cost

**Editing, about seven hours total, recovers areas 4, 5 and 6 and takes area 3 to 5.**

1. 10 min — add p99.99 to RQ1's metric list, or delete §7.7's claim that it is already there.
2. 10 min — §4.5's "isolating the cores"; §4.6's results-directory sentence.
3. 30 min — justify the tail rows from Holm, or argue the rule's premise weakened (Finding 4).
4. 30 min — rewrite §6.2's representative-load paragraph from the generator's own reasoning.
5. 30 min — the four macro misuses and the two hand-typed values (Finding 7).
6. 1 h — the four §6.4.1 statements contradicting `tab:latency`, `tab:significance`, `tab:equivalence`.
7. 1 h — the sweep-shape paragraph: p99 is flat, `\PNineNinePreCliff` prints 0 ms, the knee is not shared.
8. 3 h — the fifteen far-tail and host sites (Finding 6).

**Analysis on data already in hand, half a day each.**

9. Point `tab:latency`'s p99.99 column and the `\FarTail*` macros at the pooled CSV, and add
   `bench/results/` to `refresh_thesis.sh`'s pooling loop. The only item that changes a printed
   number, and it changes it in the thesis's favour.
10. Report the 448 kops/s rung (Finding 3).

**New measurement.**

11. The transparent-hugepage experiment, about one machine-hour. Chapter 8 already names it as the
    priority and the thesis correctly claims no causation without it.

**Author only.**

12. The abstract. Five defects, and `\abstractunaidedtrue` still unset, so every build prints
    "Not submittable".

### Two notes outside the grade

**A repository rule now contradicts the evidence and will re-introduce a corrected error.**
`.cursor/rules/thesis-quality.mdc` still reads "Peak RSS: real language + allocator effect; allocator
effect is larger", and `CALIBRATION.md`'s *Findings a grader must not "correct"* section says the
same. That is the claim the 27 August repeat overturned and that `AGENT.md` §3 item 5 now forbids
restoring. The rule file is always applied, so the next agent will be instructed to restore a claim
this record spent a pass removing. `CALIBRATION.md`'s standing blockers are also a day stale: blocker
2, the canonical repeat, is closed.

**What to add to the calibration file.** Its one-line diagnosis, that this thesis's failure mode is
prose describing an older state of the evidence, held again and found ten of the thirteen entries.
The other three are a distinct class: **a claim that was true of the old dataset and is now false in
the opposite direction.** "Every pair of intervals overlaps", "the one row that does not clear the
correction" and "the knee sits at the same place" are not stale hedges, they are assertions the new
data reverses, and no grep for "virtualised" or "unresolved" finds them. The check that does is
reading each numeric claim in §6.4 against the generated table beside it, which is the check already
ranked first in the file and the one a promotion pass is most tempted to skip **because the macros all
regenerated cleanly**. A clean regeneration says the numbers are right. It says nothing about the
sentences around them.

---

## Remediation pass — 27 August 2026, night

**No criterion is scored here.** This pass wrote the fixes for the thirteenth pass's list, and the
standing rule in this file is that a remediation must not grade its own work. The two failures a
remediation is most likely to make are invisible from inside it, propagating a claim it did not check
and fixing one half of a pair, so **areas 3, 4, 5 and 6 need a fresh pass before the numbers move**.
The thirteenth pass's grades stand until then.

Closed: the whole editing tier, both analysis items, and four defects the pass itself turned up while
verifying. Open: the abstract, and the transparent-hugepage experiment.

### The generator change, which is the part that matters

`tab:latency`'s p99.99 column and every `\FarTail*` macro now come from
`campaign-20260827-151927.hist.pooled.csv`, which is what §4.5 and §6.4.1 always said. Four pieces:

- `pooled_far_tail()` in `bench/plot_figures.py` reads the pooled sidecar and **returns `None`
  rather than falling back to the per-run `p9999` field**. The fallback is what let the prose
  describe a statistic the pipeline was not computing, so the column now disappears on a campaign
  whose sidecars were never pooled and says so on stderr.
- `latency_table_fields()` keys the column on pooled data being present, not on the runs carrying a
  per-run field.
- The pooled cell prints **without an interval**, because pooling takes the operation as the unit of
  analysis and there is no across-repeat dispersion to quote. The column carries a dagger and the
  caption explains that it is the one column of that table computed differently and the one column no
  paired test uses. `pool_hist.py`'s own docstring warns against mixing the two statistics inside one
  claim, and a labelled column is how the table avoids doing that.
- `refresh_thesis.sh` pools `bench/results/` as well as `bench/results-baremetal/`, and the loop is
  now a `for dir in ...` so the next directory is one word. It ran only over the confirmation
  directory before, which is the whole reason this defect existed.

**The numbers moved and they moved in the thesis's favour.**

| Quantity | Per-run median (as printed before) | Pooled (as printed now) |
| --- | --- | --- |
| C++ system p99.99 | 135.0 µs | 142.0 µs |
| C++ jemalloc p99.99 | 135.6 µs | **176.4 µs** |
| Rust system p99.99 | 89.2 µs | 92.1 µs |
| Rust jemalloc p99.99 | 83.6 µs | 89.5 µs |
| `\FarTailRange` | 52 µs | **87 µs** |
| `\FarTailSpread` | 62 % | **97 %** |

New macros beside them: `\FarTailMin`, `\FarTailLower` (Rust), `\FarTailByLang` (yes, the two
languages' arms do not interleave), `\FarTailSamplesMin` and `\FarTailSamplesMax` (3 360 051 to
3 360 084 operations per variant), so the prose quotes the pooling depth instead of asserting it.

### The unreported result, now reported

The Rust arms track their offered rate to **448 kops/s** and the C++ arms to **392**. At 448 the Rust
arms still serve 448 while the C++ arms have collapsed to about 162, a factor of 2.8 in **40 of 40**
paired repeats across both allocators. This is the largest throughput ratio anywhere in the sweep and
it runs opposite to the tested overload result.

Three decisions about it are worth recording, because each protects a criterion.

1. **It is not added to the tested family.** The operating point was identified after seeing the
   sweep, and §4.5 fixes the family in advance precisely so a point chosen that way cannot enter it.
   It is reported descriptively with its per-repeat agreement, and a new `tab:threats` row names the
   threat by name: *an operating point chosen after seeing the data*. Adding a fifteenth test would
   have bought a $p$-value and cost the pre-commitment, which is the more valuable asset.
2. **The capacity difference is bounded by the ladder, not measured.** The true C++ limit lies
   between 392 and 448 kops/s, and the prose says so rather than quoting a knee to three figures.
3. **`\SatKnee` was the mechanism that hid it.** It is `min` across variants, so it reported 392 as
   though all four shared it. `\TrackingLoadCpp`, `\TrackingLoadRust`, `\SatKneeCpp`, `\SatKneeRust`
   and `\KneeShared` are now emitted beside it, and the prose quotes the per-language ones wherever
   it says where an arm stops coping. **The lesson generalises: a macro can be correctly generated
   and still be the wrong quantity for the sentence holding it.**

### Four defects this pass found while verifying its own work

All four were invisible to the thirteenth pass and none would have been caught by a gate.

1. **`\JitterVsMedian` was a percentage printed as a multiple.** It is
   `100 * median(jitter p50) / median(p50)` = 2, and the prose read "jitter at p99 is $2\times$ the
   median operation". Wrong statistic (median jitter, not p99) and wrong unit (2 per cent, not
   200 per cent). Split into `\JitterVsMedianPct` (2) and `\JitterPNineNineVsMedianPct` (33) and
   named for the unit they carry, because the old name invited exactly the sentence that was written.
2. **`--` inside math mode typesets as two minus signs.** `\JitterRange` held `1--2` and the sentence
   wrapped it in `$...\mu$s`, so Table 6.2's paragraph read "spans 1 − −2 µs" in the built PDF for as
   long as the macro existed. Replaced by `\JitterLo`/`\JitterHi` and `\JitterPNineNineLo`/`Hi`, which
   is the Lo/Hi pattern every other range in the file already used. `\IqrRange` had the same latent
   defect and is split too. `\MainPinned` and `\BmPinned` keep their `2--17` form because both are
   quoted in text mode. **Found by rendering the page, not by grepping the source.**
3. **`\PNineNinePreCliff` divided by 1000 and printed `:.0f`**, so on a quiet host it rendered as
   "0 ms" and anchored the cliff sentence at zero. Retired in favour of `\PNineNineTrackingTop` (74,
   in µs) and `\PNineNineTrackingDrift` (−4, signed, because the direction is the finding).
4. **"six of the fourteen pinned cores" was typed and wrong.** The pinned range is 2--17, so
   sixteen. `\MainPinnedCount` is derived from the environment capture at two sites.

### What else changed, by area

**Area 3, method as described.** §6.4.1 no longer reads the tail block's intervals as findings. It
grounds those rows in their Holm-adjusted $p$-values, which the pre-commitment never barred, and says
plainly that a rule dropped once the machine improves was never a rule. `fig:effects`' caption now
says the shading marks the instrument set aside and not the rows. §6.2 states that the representative
load is **pinned**, gives the generator's own reasoning for it (the derived rule returned
`\GuestDeadlineLoad` on the guest by locating that host's noise floor, and collapses onto the knee on
a quiet host), and `tab:params` follows. §4.5's protocol list no longer claims the cores are isolated,
which §6.1 spends a paragraph explaining they deliberately are not.

**Area 4, the results prose.** All six wrong claims are gone. Table 6.1 does separate the languages
at the median and the prose now says which pairs overlap and which do not. All 14 tests clear Holm
and the prose says so, then names what *would* have failed (peak RSS under jemalloc on the guest,
and every tail row) so a family with no failures does not read as a threshold doing no work. The
equivalence paragraph reports margins rather than verdicts and carries the guest's contrast through
four new generated macros. `tab:resource`'s caption and §6.4.3 now say peak RSS separates the two
*languages*, and explain why one middle pair coincides: the allocator and language effects are of
comparable size. `tab:significance`'s caption names the bare-metal host.

**Area 5, the discussion.** §7.2's RQ1 paragraph reports the far tail as an ordering, notes that the
two overload effects point in opposite directions, and says which deployment question each answers.
§7.7's first conclusion-validity limitation is rebuilt around the real residual, which is the absent
`isolcpus` and what bounds it, instead of a hypervisor the host does not have. §7.8 no longer disowns
the study's own numbers. `tab:threats` loses the virtualised-host row, gains the
chosen-operating-point row, and its contaminated-run row records that the bimodality belonged to the
previous machine.

**Area 6, consistency.** RQ1 names p99.99, in the draft, in `Thesis_v2.tex` and in
`Thesis_Plan_v2.tex`. §4.6 names the right results directory and mentions the histogram sidecars.
Appendix D's intro describes three machines rather than two and no longer calls §6.1's host the guest.
`fig:cliff` and `tab:vendortheses` captions are corrected. `ai_statement.tex`'s restraint sentence
now lists the restraints that actually bind, including the new one about a point chosen after the
fact.

### Sync and build state

`Thesis_v2.tex` carries the knee finding, the pooled far tail and RQ1's widened metric list, all
inside its existing paragraphs: chapters 2 to 8 are still **five argument paragraphs** each, verified
by counting. `Thesis_Plan_v2.tex` has the metric list, and its two pre-existing prose semicolons and
three table-cell semicolons are gone, so all three documents now read zero.

Every gate passes: zero LaTeX errors, zero undefined references or citations, no multiply defined
labels, **no float too large**, no overfull boxes, no placeholders, 109 of 109 bibliography entries
cited. `./.aitells.py` on the draft reports zero semicolons, sentence length 22.1 ± 11.5, and all 14
dash hits are numeric ranges or `Herfindahl--Hirschman`. `Thesis_v2.tex` and `Thesis_Plan_v2.tex`
report zero semicolons. `diagrams/check_labels.py` clean over 19 diagrams. The deck passes both
`check_layout` and `check_prose_style`.

**`tab:threats` overflowed its page by 79pt** when the fifteenth row landed, which is the trap this
file has warned about twice. Tightening four cells recovered half and `\arraystretch` 1.25 to 1.15
recovered the rest. Measure that table after any row edit.

### Length, which is the one thing that got worse

**109 declared pages with 6 appendix pages, 123 physical**, against 104 and 6 before. Five pages, and
the author should decide whether to spend them. About two are irreducible: the knee finding, the
pooled-statistic explanation and §6.2's pinned-load reasoning are new argument, not new words. The
other three are float reflow.

Word cuts recovered **nothing**, which is this file's own finding restated: about 120 words came out
of §6.4.5 and §7.2 across three attempts and the declared count did not move once. The chapter-6 tail
page (physical 84, six lines and otherwise white) resisted every attempt, and its bottom gap grew
from 627pt to 642pt as words came out, which is the "shaving words moves nothing until a whole line
comes out" trap in its purest form. **Do not retry it from the prose side.** If a page is wanted
there, it has to come from a float in §6.4.5 or from letting chapter 7 open on the same page, and the
second is a class rule.

### What is left

1. **The abstract.** Author only, unchanged, and now the only item on the thirteenth pass's list that
   is still open. Five defects: five injected classes where the body says seven, five further classes
   where the body says seven, "median latency matches" where the paired test resolves 1.3 and 1.2 µs
   under Holm, jitter named in the *Objective* and absent from the *Results*, and a closing sentence
   that the far tail cannot be settled on a virtualised host, which is the study's principal result
   stated backwards. `\abstractunaidedfalse` still stands, so every build prints "Not submittable".
2. **A grading pass that did not write any of this.** Ask it specifically what this pass propagated
   and what it half-fixed. The two places to look first: the pooled-p99.99 claim, which now appears in
   §1.4, §4.5, §6.4.1, `tab:findings`, `tab:latency`'s caption and `Thesis_v2.tex`, and the knee
   finding, which appears in §1.4, §6.4.1, §6.4.2, `tab:params`, `tab:findings`, §7.2, `tab:threats`
   and `Thesis_v2.tex`. Six and eight sites respectively, written in one pass, by one session.
3. **The transparent-hugepage experiment.** Unchanged, about one machine-hour, and Chapter 8 already
   names it as the priority.

---

## Fourteenth pass — 28 August 2026

Graded from `Ha_Vien_Mastersthesis_2026.tex` against a build kept current throughout. **109 declared
pages with 6 appendix pages, 123 physical.** Graded as a full draft.

**This pass has a conflict of interest and reports two columns because of it.** The remediation of
27 August night was written by the same session. The standing rule here is that a remediation must
not grade its own work, so the *on record* column below does not move and the *supported* column is
self-assessed and must not be banked until an independent reader confirms it.

| Area | On record (13th pass) | Evidence now supports | What decides it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Already 5. The RQ1 metric item is closed, so the reasoning changed and the number did not |
| 2. Scholarly framework and sources | 5 | **5** | Untouched by two editing passes and verified intact |
| 3. Research data and method | 4.5 | **5** | Both description defects closed, and the study now refuses to test a favourable post-hoc result |
| 4. Presentation of results | 4.0 | **4.5** | All thirteen defects closed and verified. Capped at 4.5 by the abstract, which is where results are reported first |
| 5. Discussion and conclusions | 4.5 | **5** | All four chapter-7 sites synced, and §7.2 now gives a decision rule instead of a verdict |
| 6. Academic text | 4.0 | **4.5** | Level 4's consistency clause holds on all four things it names. Capped by the abstract |
| 7. Work during the thesis process | n/a | **n/a** | No manuscript settles it |
| **Mean of the six assessable** | 4.50 | **4.83** | The whole gap is this session's own work |

Canvas: `thesis-grade-csm-aug28.canvas.tsx`.

### The part of this pass worth keeping: four defects in its own overnight work

Three were introduced by the remediation and one was pre-existing and missed by the pass that should
have caught it. **None would have been caught by any gate in the repository.** All four are fixed,
regenerated and rebuilt.

| Site | What was written | What the data says |
| --- | --- | --- |
| `tab:resource` caption | "Peak RSS and CPU both separate the two languages here." | True of CPU unconditionally. True of peak RSS only **at a fixed allocator**: the unpaired envelopes overlap, C++ reaching $12.63$ MiB and Rust starting at $12.42$. The §6.4.3 prose beside it was precise and the caption was not, which is the half-a-pair pattern with the halves reversed |
| §6.4.1, equivalence paragraph | "`\GuestNEqvUnresolved` of its `\GuestNTests` rows unresolved", printing 5 of 14 | `tab:equivalence` shows **10** rows: `write_equivalence_table` filters to the representative load and the other four are overload tests. All five unresolved rows were among the ten shown, so the count was right and the denominator named something the reader cannot count. New macro `\GuestNEqvRows` supplies 10 |
| `fig:loadsweep` caption | 448 kops/s is "the one place in the sweep where the two languages part company below the deepest overload" | False. They also part company at **560** kops/s, where C++ sustains $143.6$ against Rust's $84.6$. What is true is that 448 is the only load at which the ordering favours **Rust** |
| §6.4.1 and §6.4.2 | "An interval of `\PFiftyDiffCIMax` µs is `\BudgetBoundVsCore` times the operation's own cost", printing 1 µs and 38 | `\BudgetBoundVsCore` divides the unrounded $1.3$ µs by $34.5$ ns and rounds only the ratio, so the printed figures divide to 29. The same quantity printed as $1.3$ through `\EqvBoundPFifty` two paragraphs earlier. **Pre-existing, missed by the thirteenth pass.** `\PFiftyDiffCIMax` now carries one decimal |

**Three of the four share a shape and it is worth naming as a class.** A sentence true of the paired
comparison and false of the unpaired one. A count right against the family and wrong against the
table it names. A uniqueness claim true in one respect and false as written. **None is a wrong
number. Each is a correct statement attached to the wrong scope.** A reader checking the value finds
nothing and a reader checking the sentence finds it at once. The check that catches this class is to
ask of every comparative claim exactly which set it quantifies over.

### What was checked and did hold

- **The generated layer.** 18 macros recomputed from the raw campaign JSONL, all 18 matching. Four
  looked like mismatches on the first attempt and were the false positive `CALIBRATION.md` warns
  about: `RssLangDiff*`, `RssAllocDiff*` and `CpuDiffAbsMax` are **medians of paired differences**,
  not differences of medians, so a naive recompute disagrees. Re-derived through `_paired_effect`
  they match exactly. **Seven passes now with no wrong measured value.**
- **The interval claims of §6.4.1**, re-derived on both hosts. On the reported host the two Rust
  median intervals overlap each other ($[72.063, 72.319]$ against $[72.287, 72.479]$), the two C++
  intervals overlap each other, and all four cross-language pairs separate. On the guest all six
  pairs overlap. Both halves of that sentence are true.
- **The knee finding**, recomputed: C++ arms track to 392 kops/s, Rust arms to 448, and at 448 Rust
  serves $447.9$ against C++'s $163.3$ in 40 of 40 paired repeats. The gap of $286$ kops/s is indeed
  the largest in the sweep, against $63$ at the tested overload point.
- **Every gate.** Zero LaTeX errors, zero undefined references or citations, no multiply defined
  labels, no float too large, no overfull boxes, no placeholders, 109 of 109 entries cited.
  `./.aitells.py`: zero semicolons in all three documents, sentence length $22.1 \pm 11.4$, all 14
  dash hits numeric ranges or `Herfindahl--Hirschman`. Diagram labels clean over 19 diagrams. Deck
  passes `check_layout` and `check_prose_style`.
- **Style drift corrected.** "rather than" reached 95 instances after the remediation, against 89
  before it. Six of this session's own were rewritten and it now reads 90, which is baseline.

### Why each area sits where it does

**Area 3 has the strongest case of the four to move.** What closed it is not only the two fixes. The
document now declines to test the 448 kops/s rung, an overwhelming result in its own favour, on the
grounds that the operating point was identified after the data was in hand, and it adds a
`tab:threats` row naming that threat. Refusing a favourable post-hoc test is a harder thing to do
than any of the apparatus around it, and it is what the level-5 clause about methods analysed in
depth actually looks like. An independent reader should test whether the pre-commitment reads as
**kept** rather than as quietly relaxed, since §6.4.1 now reports the tail rows as findings on their
$p$-values while still setting their intervals aside.

**Areas 4 and 6 are capped at 4.5 by the abstract and by nothing else.** Level 5 in area 6 asks for
presentation that is technically camera-ready, and the build prints "Not submittable". Area 4 follows
because the abstract is where results are reported first. One rewrite closes both caps.

**Area 5 is where the writing improved most.** §7.2 no longer states a verdict on RQ1's overload
half. It states that the two effects run in opposite directions, and then says which deployment
question each answers: a service sized to run below its knee should prefer the arm with the higher
knee, and one a signalling storm will drive past every knee should prefer the arm that degrades less
steeply. That is a more useful thing to give a vendor than a winner.

### Length

**109 declared, up from 104 before the remediation and 99 at the start of the week.** About two pages
are new argument: the knee finding, the pooled-statistic explanation, and §6.2's pinned-load
reasoning. The other three are float reflow. Three rounds of word cuts recovered **nothing**, and the
chapter-6 tail page at physical 84 grew its bottom gap from 627pt to 642pt as words came out of the
paragraphs feeding it, which is this file's own trap in its purest form. **Do not attack that page
from the prose side.** If pages are wanted there they have to come from a float in §6.4.5. Under 100
remains a preference and substance won here, so the number is reported and the decision is the
author's.

### What is left

1. **The abstract.** Author only. It now caps two areas and nothing else caps anything.
2. **An independent grading pass.** The only thing that can move areas 3, 4, 5 and 6. Ask it what the
   remediation propagated and what it half-fixed: the pooled far-tail claim now appears at six sites
   and the knee finding at nine including `Thesis_v2.tex`, all written in one night by one session.
   This morning's audit found the shared claims sound and three sentences around them wrong, which is
   roughly the ratio the twelfth pass found when it audited its predecessor.
3. **The transparent-hugepage experiment**, about one machine-hour, already named in Chapter 8.

### Addendum to the fourteenth pass: an independent audit, run in parallel

The pass above was written by the session that wrote the remediation, so a second reader audited the
same claims from scratch, without that context, working only from the artefacts. **It found five
defects the fourteenth pass missed, and one of them is worse than anything either pass had found so
far.** All five are verified and fixed. This is the clearest evidence yet for the rule this file
already states: a session cannot audit its own editing, and running a second reader is cheap.

The audit also re-derived every artefact from the raw campaign into a scratch directory and confirmed
that `gen_macros.tex` and all eleven `tab_*.tex` reproduce **byte for byte**. So no macro or table
disagrees with the data, and every finding below is prose against a correct artefact.

| # | Site | The claim | The data |
| --- | --- | --- | --- |
| A1 | §6.4.1, the `fig:tailpct` paragraph, and the figure caption | "from p90 upward the interval wins, so the fan marks where the measurement loses resolution and not where the languages differ", and the caption's "Why they cannot be separated above the median" | **The interval never wins.** The ratio of widest interval to between-variant spread is 0.17, 0.18, 0.49, 0.64 and 0.70 at p50 to p99.99. The figure's own annotations print those numbers, so the prose said the opposite of the panel above it. **The panel's generated title was wrong too**, reading "Where the host stops resolving the comparison" |
| A2 | §6.4.1, budget paragraph l. 2724, and `fig:budget`'s caption | "the only place in the whole performance campaign where a language difference in *time* is resolved at all" | False. Six rows measured in microseconds clear Holm: p50, p99 and p99.9 under both allocators. The caption conceded "the sweep's one resolved language difference in time", so the two also contradicted each other |
| A3 | `tab:latency` caption | the p99.99 is "the one column of this table that no paired test uses" | The **maximum** is untested too, so it is one of two |
| A4 | `Thesis_v2.tex` l. 616 | the representative load "is the busiest swept load at which all four variants still hold p99 below 5 ms" | The rule the draft's §6.2 was rewritten to disown, surviving in the skeleton. On this host it returns 392 kops/s. **A half-fixed pair across documents**, which is the sync rule's own failure mode |
| A5 | Chapter 8 l. 4813 | the far tail "resolves in Rust's favour by `\FarTailRange` µs" | `\FarTailRange` (87) spans the extremes across all four variants. The language separation is the worst-case pair, $50$ µs. Five other sites qualify the macro correctly ("the widest gap between variants", "by up to"); this one dropped the qualifier and overstated by three quarters |

**A1 is the most serious defect found in this thesis since the ninth pass**, and it is worth saying
why. It is not staleness in a summary: it is a results paragraph telling the reader the opposite of
what the figure beside it draws, in a passage whose whole job is to say whether the tail ordering can
be trusted. It also contradicted §6.4.1's own p99 paragraph four pages earlier, which correctly says
the uncertainty is smaller than the gap. Both passes before this one read that subsection and neither
caught it, because both were reading for the claims they knew had changed.

Fixes, all generated rather than typed. `_tail_resolution()` in `plot_figures.py` emits
`\TailResolveRatioMax` (0.7), `\TailResolveRatioMaxAt` (p99.99) and `\TailResolveCrossed` (no), and
panel (b)'s title is now chosen from the data, so a host where the crossover does happen gets the old
heading back. `\FarTailLangSep` (50) is the language separation, distinct from `\FarTailRange`.
`\NTailSignificant` counts tail rows clearing Holm, where the sentence had been quoting
`\NTailExclZero`, a different question that happens to give 4 today.

Three further imprecisions the audit raised were checked and corrected: `\JitterSpread` is computed
from the median jitter and the sentence attached it to the p99 range as well, "two orders of magnitude
below the conventional threshold" understated a factor of 820, and §6.4.4 called the second
bare-metal host's two peak-RSS effects "of comparable size" where `\BmRssLargerEffect` is
`allocator` and the ranges there do not overlap. That last one now says what both bare-metal hosts
actually agree on, which is the order of magnitude, and states that the ordering within it is not
established.

**What the audit checked and found sound**, which matters as much as what it found wrong: the pooled
far-tail implementation and all eight of its macros; every one of the twelve sites describing it; the
knee finding recomputed end to end, including 40 of 40 paired repeats; the p50 interval-overlap claim
on both hosts; the significance family, equivalence bounds, budget decomposition, flat-p99 paragraph,
overload block, contention microbenchmark, resident-set decomposition, fault taxonomy, FFI seam and
every adoption figure recomputed from `adoption-20260821-134156.json`.

**The grade is unchanged.** The recorded 4.50 stands and the self-assessed 4.83 stands, because
areas 4 and 6 were already capped at 4.5 by the abstract and A1 through A5 are all now closed. What
this addendum changes is confidence, not the number: two consecutive editing passes each left defects
that only a third reader found, so **the "supported" column needs an independent grader more than it
needed one this morning**, not less.

### Cross-document check, 28 August, done by hand while the chapter audits ran

Three defects, all in material no grading pass had looked at, and all visible to a supervisor.

1. **`Thesis_Plan_v2.tex` was dated 13 August while describing work done on 27 August.** A
   supervisor-facing plan reporting the canonical bare-metal campaign as complete, over a date two
   weeks before it ran. Now 28 August.
2. **The plan's timeline marked September "Done" on 28 August.** It also duplicated the measurement
   work across the August and September rows. August now carries build and measurement, September
   the abstract and proofread, October review, November submission, and nothing in the future claims
   to be finished.
3. **Chapter 8's future-work opening named the wrong priority and miscounted the hosts.** It read
   "the immediate priority is a third machine at the reported campaign's own design", then described
   the transparent-hugepage experiment, which needs **no new machine** and is a two-setting
   comparison on one host. It also said "two hosts now agree on every direction ... and on one
   quantity they disagree", where the disagreement is with the *third* host, the virtualised one.
   Rewritten in the draft and in `Thesis_v2.tex` to name the hugepage experiment first and to state
   the three-host position correctly: all three agree the Rust build carries the larger footprint,
   and they disagree about how that compares against the allocator's cost.

Item 3 matters beyond its wording, because `AGENT.md`, `docs/TODO.md` and the plan all name the
hugepage experiment as the immediate priority and Chapter 8 named something else. **The thesis was
the only one of the four documents that did not say what the next experiment is.**

Verified correct in the same check: RQ1 through RQ4 are byte-identical between the draft and
`Thesis_v2.tex` and the plan's list now carries p99.99 too; H1 to H3 are identical between draft and
skeleton; the limitations list matches; the plan's host and status descriptions are accurate; and
`Thesis_v2.tex` chapters 2 to 8 still hold exactly five body paragraphs each, with Chapter 1 the full
introduction.

### Second independent audit, 28 August: Chapters 1 to 5 and the appendices

Nobody had audited this material. Every grading pass on record concentrated on Chapters 6 and 7.
An independent reader with no account of what had changed found **twelve defects and five minor
items**, all fixed. Two of the twelve were introduced by the remediation of 27 August night and the
rest had been there longer, some since the guest campaign.

**The three that mattered most.**

**The CPU-steal figure in `tab:testbed` had no artefact behind it and its own capture said zero.**
The guest column read "Non-zero, order $10$~ms per second of vCPU time, comparable to the tails
measured", hand-typed, while `bench/results/env-20260812-154523.txt` records `steal ticks (1 s
sample): 0` and `\GuestSteal` is generated as `0` from exactly that field. No steal probe was ever
run on the guest: the only `steal_probe.sh` output in the repository is from the bare-metal visit.
The caption sixteen lines above claimed every cell was generated from the campaign's own capture.
`Thesis_v2.tex` carried the same unsupported claim as the *reason* the guest could not resolve the
far tail. **The fix matters for the argument and not only for the number**: the guest's failure is
established by the measured interval-versus-spread relation, which §6.1 and §6.4.4 already give, so
removing the steal claim costs nothing and removing it was necessary, because the study cannot
support it. The cell now says the quantity was not characterised and quotes the one recorded sample.

**§4.6's description of where the campaigns live was wrong, and it was wrong because of the
remediation.** Yesterday's edit wrote that the virtualised campaign and the second bare-metal one are
"kept in directories of their own so that no analysis can pool two hosts by accident". The guest
campaign sits in `bench/results/` beside the reported sweep, and `plot_figures.py` selects its default
with `sorted(glob(...))[-1]`, so both hosts match one glob and filename order is what separates them.
The same sentence promised a histogram sidecar beside every campaign, where the guest has none. The
paragraph now says what actually keeps the hosts apart, which is that each campaign has its own
generator and macro prefix.

**Appendix D claimed every table in the thesis comes from the reported host.** Also written yesterday.
`tab:resident` is the second bare-metal host and says so in its own caption, `tab:ffi` and
`tab:adoption` were measured on the development machine, and `tab:taxonomy`, `tab:complexity` and
`tab:loc` come from no campaign at all.

**The rest.** §4.2.2 sent "the boundary classes" to Loom and Shuttle where `model_checking.csv`
covers two of the seven, contradicting §4.6 and §6.3 in the same document. Table 4.1's RQ1 metric row
and §3.3's metric list both stopped at p99.9 after RQ1 was widened, which is the half-fixed-pair
pattern again. §5.2 and `tab:params` justified seven shards as "one thread owns one shard, one of
each per pinned core", arithmetic that is exactly right for the retired 14-core guest and wrong on
sixteen pinned cores; the rationale is now that seven is held across all three hosts as a fairness
control, which is the true reason. `fig:cliff`'s caption, rewritten yesterday, pointed at the wrong
section and promised a per-language comparison of the cliff's steepness that §4.5 pre-commits to
never making. §4.5 still described pooling and jitter in the conditional and referred to "the missing
data" two sentences after saying the campaign carries both. And §4.2.3 pointed at a dependency-free
claim that §5.4.4 did not make, which is now made there and checked.

**One finding outside the auditor's scope proved the stipulation wrong.** Chapter 6 was declared
correct to that reader, and it flagged §6.3 anyway: the performance-sweep paragraph listed the
record's latency block as "mean, p50, p90, p99, p99.9, maximum" and the paragraph after it presented
the quartiles, p99.99, the sidecar, the counters and the allocator accounting as things the *second*
campaign adds. The reported campaign carries all of them. Both paragraphs are rewritten, and the
section's opening no longer asserts a dataset count, which had been wrong before this pass and wrong
again after it.

**Cumulative across the four reviews of 27 and 28 August: 34 prose defects**, against a generated
layer that has re-derived byte for byte every time it was checked. Nine of the thirty-four were
introduced by the two editing passes themselves. **The reviews that found the most were the two run
by readers who were told nothing about what had changed.**

### Third independent audit, 28 August: the abstract, Chapter 8, the declaration, and cross-document

**This audit found a direction error in a headline claim, repeated at five sites in two documents,
that three grading passes and two other audits had all read past.**

**The overload CPU-per-operation ratio was attributed to the wrong language.** The sentence read "the
C++ build sustains $\OverloadThrRatio\times$ the throughput of the Rust build \dots while drawing
$\OverloadCpuPerOpRatio\times$ the CPU per completed operation", and the participle attaches to C++.
Recomputed from `campaign-20260827-151927.jsonl` at 784 kops/s: C++ 4.52 and 4.54 per cent CPU per
kop/s, Rust 8.07 and 8.07, so **Rust** draws 1.8 times as much. Rust also draws more *total* CPU
($+19.5$ and $+16.8$ percentage points, 20/20 repeats), so no reading of the sentence was right.

Why it matters more than its size: §6.4.2 wrote that clause specifically to rule out the reading that
the slower variant is simply doing less work. Inverted, it says the faster variant is burning the CPU,
which is the opposite claim and would make the overload finding incoherent. §6.4.2, `fig:overload`'s
caption and `tab:findings`'s RQ3 row all had it right; §1.4, §7.2 and Chapter 8 had it wrong, and
`Thesis_v2.tex` contradicted itself between its Chapter 6 and its Chapter 8. **A sentence can be wrong
at every summary site while the section that owns the result is correct**, and a reviewer checking
"does this match the table" at the owning section will never see it.

Four more in Chapter 8, all fixed. The binary-size gap "reverses when the policy is matched", where
the ordering reverses *between* the two matched policies (Rust smaller static, C++ smaller dynamic)
and quoting one alone is what `AGENT.md` §3 item 6a forbids. The seven boundary classes "misbehave in
safe Rust exactly as they do in C++", where §6.4.4 spends a paragraph on two that do not, the
forgotten guard having no unlock to skip and the overflow being defined-but-wrong against
undefined-and-wrong. The peak-RSS effect "the same size on all three machines measured", where the
three ranges are 1.4--2.5, 1.8--3.5 and 0.7--1.8 MiB, so what travels is the direction and the order
of magnitude. And Chapter 8 delivered the single overload verdict "one that currently favours C++"
three paragraphs after reporting both halves, which is exactly the verdict §7.2 argues would be false.

**The declaration over-claimed the author's own verification.** `ai_statement.tex` said every
bibliography entry was "traced to the page or clause carrying the claim made of it".
`docs/Sources_evidence.md` grades entries A, B or C, where B is a publisher-deposited record and C is
metadata behind a paywall with the passage never opened, and it lists 22 entries at those levels. The
sentence now describes the graded scheme and says the unopened entries are listed rather than
absorbed. This is the second false method sentence found in that file, after the eighth pass, and it
is a statement in the author's name.

**Four cross-document disagreements**, all resolved in favour of the draft and now synced:
`Thesis_v2.tex` had dropped the attribution bound from Chapter 8's contributions list while its own
Chapter 1 introduces it, had cut the saturation-limit finding from §1.4 so that three of the four
RQ1 summary sites reported only the half favouring C++, and still carried the "comparable on both
bare-metal hosts" wording that §6.4.5 was moved off. The plan's contributions list had five items
where both theses have six.

**One rounding item of the class this record has now seen three times.** `\JitterLo` and `\JitterHi`
printed at one decimal as 1.4 and 1.7, which divide to 21 per cent, beside a `\JitterSpread` of 26
computed from the unrounded 1.3655 and 1.7205. Two decimals now.

**The audit also caught the record lying about itself.** `docs/ASSESSMENT.md` recorded the Chapter 8
future-work fix as "Rewritten in the draft and in `Thesis_v2.tex`" while only the skeleton carried it;
the draft was rewritten minutes later. The interval between an assessment claiming a paired fix and
the second half landing is precisely the failure mode this file names, and it was visible only to a
reader who checked the artefact instead of the record.

**Running total across five reviews on 27 and 28 August: 56 prose defects, all fixed.** The generated
layer has re-derived byte for byte at every check. **The three reviews by readers told nothing about
what had changed found 34 of the 56.**

---

## Fifteenth pass — 28 August 2026, after the fixes

Graded on a build rebuilt after the last edit. **109 declared pages with 6 appendix pages, 123
physical.** Every gate passes.

| Area | 13th pass (on record) | This pass | Independent confirmation |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Chapters 1--5 audited, no findings in this area |
| 2. Scholarly framework and sources | 5 | **5** | Audited. One improvement: the declaration now states the source audit's real coverage |
| 3. Research data and method | 4.5 | **5** | Audited, four findings, all closed |
| 4. Presentation of results | 4.0 | **4.5** | Audited three times, all findings closed. Capped by the abstract |
| 5. Discussion and conclusions | 4.5 | **5** | Audited, all findings closed |
| 6. Academic text | 4.0 | **4.5** | Audited across three documents. Capped by the abstract |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.50 | **4.83** | |

Canvas: `thesis-grade-csm-aug28-rev2.canvas.tsx`.

### The number did not move this morning. Whether it is justified did.

The fourteenth pass self-assessed 4.83 and refused to record it, on the grounds that it had written
the edits. **That refusal was correct, and the reason is now concrete.** At the moment it graded, the
thesis still said the C++ build drew $1.8\times$ the CPU per completed operation, at five sites in
two documents, where the data has **Rust** drawing it. A headline claim was inverted and 4.83 was not
defensible with it live. Three independent readers have since audited the whole document and 41
further defects have been found and closed. The same number now rests on evidence.

### What the seven reviews found

| Reviewer | Scope | Found | Independent |
| --- | --- | --- | --- |
| Thirteenth grading pass | Ch. 6--7 | 13 | no |
| Fourteenth pass, self-audit | its own remediation | 4 | no |
| Independent reader | Ch. 6--7 | 5 | **yes** |
| Cross-document check by hand | all three documents | 3 | no |
| Independent reader | Ch. 1--5, appendices | 17 | **yes** |
| Independent reader | abstract, Ch. 8, declaration, cross-doc | 19 | **yes** |
| Independent reader | the last two hours of edits | 8 | **yes** |
| **Total** | | **69** | 49 found independently |

**Every one of the 69 was prose disagreeing with an artefact that was itself correct.** The generated
layer re-derived byte for byte at every check, four times. Roughly 25 of the 69 were introduced by
the editing passes themselves.

### The last audit is the one worth reading twice

It examined only the thirty passages changed between 10:00 and 11:15 and found **eight new defects**,
a rate near one in four. Three are worth recording.

**A fix created a fresh instance of the class it was fixing.** `_tail_resolution()`, added that
morning to stop §6.4.1 asserting a crossover the figure refutes, computed its ratio from the per-run
`p9999` field. That is precisely the statistic §4.5 calls dominated by sampling noise and says no
analysis script reads, and it is why `tab:latency` reports the far tail pooled. The new prose then
put the peak of its argument at that percentile and called it "the condition that licenses the tail
ordering". Both the macro and `fig:tailpct` now stop at p99.9, because a pooled percentile has no
across-repeat interval to weigh a spread against, and the figure's caption says so.

**A new sentence contradicted itself.** §5.3 gained "Holding it at seven across all three machines is
what makes the shard count a fairness control \dots and the second bare-metal campaign varies it
deliberately to test that." Both halves in one sentence, and `\BmShards` is 8. The fairness control
was never constancy across hosts: `tab:controls` states it as identity between the two languages,
which is true in every campaign.

**Two result tables had no provenance and one claimed the wrong host.** `tab:budget` and
`tab:contention` come from August runs on the virtualised host. The previous day's Appendix D
sentence certified that "three result tables come from elsewhere", missing both, and
`tab:contention`'s own caption asserted the reported host, which its 14 August date makes impossible.
Both captions now name the host and say why the ratio travels while the absolute figures do not.

### Why each area sits where it does

**Area 3 reaches 5**, and what earns it is a pattern of refusals rather than any single control. The
pre-committed reading rule is kept on a host where it costs nothing, and said to be kept for that
reason. The 448 kops/s rung is described and not tested because the operating point was found after
the data, with a threats row naming that threat. The pooled and per-repeat statistics are held apart,
the generator returns `None` rather than falling back to the disowned one, and the figure was
narrowed so it could not quote it either. **Declining a favourable post-hoc test is harder than any
apparatus around it**, and it is what the level-5 clause about methods analysed in depth looks like.

**Areas 4 and 6 sit at 4.5 for the same reason and no other.** The abstract carries ten factual
defects, five recorded for the first time today, and the build prints "Not submittable". One rewrite
closes both.

**Area 5 reaches 5** on the strength of §7.2 refusing a verdict: it reports that the two overload
effects run in opposite directions and names which deployment question each answers, which is more
useful than a winner and is the harder thing to write.

### Residual risk

The last audit found eight defects in thirty changed passages. Closing them took about fifteen
further edits, and **those fifteen have not been independently read**. On the observed rate that is
two to four undiscovered defects, concentrated in: §5.3 and `tab:params` on the shard rationale,
Appendix D's provenance sentence and the `tab:budget` and `tab:contention` captions, the narrowed
`fig:tailpct` and its caption, and `ai_statement.tex`'s coverage sentence. One focused audit of that
set is the cheapest remaining improvement.

### What this exercise established that no gate could

All 69 defects were prose against a correct artefact, so no gate in the repository could catch any of
them, and the macro-recomputation check that has been the mainstay of these passes catches only the
subset that is a wrong number. Three shapes defeated it and all three are now first-rank checks in
the grading skill's calibration file: **a correct statement attached to the wrong scope**, a claim
right where it is derived and wrong at every site that summarises it, and a figure title asserting a
conclusion its own bars refute.

### Fourth independent audit, 28 August noon: the fifteen edits nobody had read

The fifteenth pass named these fifteen edits as its own residual risk and estimated two to four
undiscovered defects in them. **The real number was eight**, three found by re-checking by hand
before the audit reported and five by the audit. The estimate was low by a factor of two, which is
itself worth recording: the rate at which this project's editing introduces defects has been
consistently under-estimated by the sessions doing the editing.

**The audit re-derived the generated layer again and it is clean**, five checks running:
`gen_macros.tex` and every `tab_*.tex` byte-identical, and the narrowed `fig:tailpct` rendering
exactly as its new macros claim.

**Found by hand, before the audit.** Yesterday's caption fix had replaced a wrong host attribution
with a differently wrong one. `tab:budget` and `tab:contention` were given "Measured on the
virtualised host", where neither `latency_budget.json` nor `queue_contention.json` records an
environment and neither runner calls `capture_env.sh`. For the contention file the nearest evidence
points the other way: it was written on 14 August and the only capture from that day is the WSL
development laptop, `virtualisation: wsl`, not the KVM guest. Both captions now state what is
checkable, that the experiment predates the environment-record discipline and supports a ratio
between two alternately measured arms. `tab:ffi` had no provenance at all while Appendix D asserted
that every such table names its own, so it gained one, and §6.3's "Every campaign writes the
environment record" was scoped to the load sweeps, since three paired experiments do not.

**Found by the audit, and the first is the sharpest defect of the day.** The `tab:latency` caption's
new reason for not testing the maximum, "a single observation per run and carries no distribution to
test at all", is refuted by the table it captions: the max column is
`\mci{243.1}{239.2}{275.8}`, a median of twenty per-run maxima above a bootstrap interval, printed
four columns away. **The wording it replaced was correct** and the replacement swapped a right reason
for a wrong one. The maximum is untested because it is the limiting case of a statistic read off
exactly the operations interference lands on, which is what §4.5 already says, and the caption now
says that.

Three more. Appendix D's replacement sentence swept `tab:adoption` and `tab:ffi` into a
paired-and-alternating claim their own sections refuse, since only build time is host-sensitive and
the footprint and dependency figures are deterministic, which is the mirror image of the error
`AGENT.md` §3 item 6a exists to prevent. Its count of five omitted `tab:taxonomy`, which runs on the
development machine under `g++ 13.3` against the reported host's 15.2.1. And §6.3's corrected
enumeration promised a build and footprint dataset that no following paragraph described, so it now
has one, at the cost of a page.

**A defect outside every gate the thesis has.** The audit looked past its own brief and found that
`build_deck.py`'s tail-percentile slide is titled "the host runs out of resolution" and annotated
"Uncertainty about one exceeds the gap between all four", where the macros beside it are
`\PNineNineRange` 2 against `\PNineNineMaxCI` 1 and say the opposite. The slide had just been given a
regenerated figure whose own panel title reads "The comparison stays resolvable at every percentile",
so the deck contradicted the picture on it. Title and note now read off the same macros as the panel.
**A deck defect is invisible to `texaudit.py`, to `.aitells.py` and to every check in this file**, and
the deck's own two gates gate layout and punctuation, not agreement with the data.

**Length.** 110 declared pages with 6 appendix, 124 physical, up one. The page is the new
adoption-cost dataset paragraph, which explains why build time is a ratio and the footprint is not,
a distinction `AGENT.md` §3 item 6a protects. Worth the page.

**Running total: 77 defects across eight reviews.** Five independent readers found 54 of them. The
grade is unchanged at 4.83, because every one of these was closed and none touched a level
descriptor, but the residual-risk estimate in the fifteenth pass should be read as what it was: an
under-estimate by half.

## Sixteenth pass — 30 August 2026

Graded independently against the CSM matrix of 9 April 2024, on
`Ha_Vien_Mastersthesis_2026.tex` as a **full draft**, not as a submitted copy. The PDF was two days
behind the source; it was force-rebuilt with `latexmk -g` before any grade was assigned. Declared
length is now **95 pages plus 12 appendix pages** (115 physical), down from the fifteenth pass's 109
plus 6. Appendices F (implementation of the two cores) and G (engineering guidelines) are in the
document. Standard applied: a draft that prints "Not submittable" is not scored as if an examiner
had received it, but the abstract is still the first reporting of the results and it still caps
areas 4 and 6.

View formed before reading this file. Canvas: `thesis-grade-csm-aug30.canvas.tsx`.

| Area | 15th pass (28 Aug) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Level 5 holds: topic publication-worthy, gap in named prior work, four RQs traced, RQ2 two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Level 5 holds: 109/109 cited, 66% peer-reviewed, search protocol, contrary results engaged |
| 3. Research data and method | 5 | **5** | Level 5 holds: method analysed in depth, data is the canonical bare-metal campaign, description matches |
| 4. Presentation of results | 4.5 | **4.5** | Level 5's aptness clause fails on the abstract. Level 4 holds on the body |
| 5. Discussion and conclusions | 5 | **5** | Level 5 holds: H1--H3 revisited including a refutation, four-way validity, register held |
| 6. Academic text | 4.5 | **4.5** | Level 5's camera-ready clause fails on the abstract *and* on a running-header overflow. Level 4 holds on the body |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.83 | **4.83** | |

### Agreement and disagreement with the fifteenth pass

**Agree on every number.** Areas 1, 2, 3 and 5 stay at 5. Areas 4 and 6 stay at 4.5. The mean is
4.83. The abstract is still the item that holds two areas below 5, and only the author may rewrite
it.

**Disagree on what would lift area 6 to 5.** The fifteenth pass closed with "one rewrite would put
all six assessable areas there" and "nothing else on the sheet is capped". That is no longer true.
Level 5 asks for presentation that is technically camera-ready with excellent finishing polish. The
rebuild log contains one overfull box the audit script does not see:

```
Overfull \hbox (23.0782pt too wide) has occurred while \output is active
2.2.  LATENCY, THROUGHPUT, AND PREDICTABILITY IN REAL-TIME SOFTWARE 9
```

Body page 9, physical page 17. The extracted header is `SOFTWARE9`, page number jammed against the
last word. Chapter 2 already carries `\chaptermark{Background}`. Section 2.2 does not. `texaudit.py`
reports `PASS no overfull boxes` because it does not match overflows that happen during page output.
Every pass that trusted the script recorded this page as clean. After the abstract rewrite, area 6
would still sit at 4.5 until a short `\sectionmark` is added.

**Submitted as-is, both 4.5s would be 4.0.** Level 4 in area 6 requires the whole text to be logical
and consistent on research questions, setup, findings and conclusions. The abstract says five and
five, median matches, and the far tail cannot be settled on a virtualised host. The body says seven
and seven, a resolved $-1.3\,\mu$s, and a pooled p99.99 that favours Rust. The draft standard holds
4.5 because the document declares the abstract unfinished. An examiner who received this PDF would
not.

### Mechanical evidence

Hard gates pass: no LaTeX errors, no undefined references or citations, no multiply defined labels,
no float too large, no placeholders. 109 bibliography entries, all 109 cited, 72 peer-reviewed
(66%). `bugden2022rust` is the remaining arXiv load-bearing cite (beside Pereira). `zhang2026deadlock`
is the journal version; the preprint flag is its `note` field. One unreferenced float: `tab:abbrev`,
the glossary that *is* Appendix A. Not capping. Sentence length 21.4 ± 11.6, zero semicolons.
`\abstractunaidedfalse`. Build prints "Not submittable".

Generated layer: not re-derived this pass. Twelve claims in Chapters 1, 6, 7 and 8 were read against
the tables the PDF includes. No wrong measured value. Sample: pooled p99.99 89.5 / 92.1 vs 142.0 /
176.4 (widest gap 86.9 against `\FarTailRange` 87); paired median $-1.3$ and $-1.2\,\mu$s;
overload 146.7 / 84.5 = 1.74 against `\OverloadThrRatio` 1.7, CPU per op 1.78 against 1.8, attached
to Rust; knees `\TrackingLoadCpp` 392 and `\TrackingLoadRust` 448, and the prose states they are
not shared; RSS paired $+1.4$ and $+2.5$ MiB; deadlock 5/12 matching `taxonomy.csv`;
`\TailResolveRatioMax` 0.6 at p99.9, figure title generated from whether the ratio crossed one.

Residual-risk sites named by the fifteenth pass were re-read, not as a full independent audit of
those fifteen edits, but as a check that the recorded fixes are what the PDF now prints. They are:
§5.3 states identity between languages and not across hosts, `tab:params` says the same,
`tab:budget` and `tab:contention` captions state they predate the environment record, `fig:tailpct`
stops at p99.9 and says why, the AI declaration is gated and truthful.

### Per-area notes

**1, carries 5.** Gap located in Karlback (runtime co-varies), Olsson/Stenstrom (effect of two to
five times), Arvidsson (contrary p99, stackless async, excluded here), Emberg (matched pair on a
stateless object, two sessions reversed). Four RQs, three hypotheses, RQ2 built to fail.

**2, carries 5.** Written protocol including the DiVA/Finna step. Gonzalez 0.19% used to keep
statistical and operational significance apart. Karlback's reversed peak-RSS sign is treated as a
runtime confound, not waved at.

**3, carries 5.** The method half is still the pattern of refusals: reading rule kept, 448 kops/s
descriptive, pooled statistic with no fallback. Ethics section present.

**4, 4.5.** Body reporting is apt. The abstract is where findings are reported first and it is
wrong in ten places, all still in the PDF of 30 August. Item 5 of that list has changed shape
slightly: jitter is now reported in Appendix D, so the defect is "Objective names a metric the
Results paragraph omits" rather than "unreported anywhere".

**5, carries 5.** H1 supported below saturation, refuted above it, then declared ill-posed because
"performance-equivalent" named three quantities that do not move together. §7.2 still refuses a
single overload verdict.

**6, 4.5.** Level 4 holds on the body. Level 5 fails on finishing: the unaided abstract, and the
23 pt running header. The previous pass's "every mechanical gate passes" was true of `texaudit.py`
and false of the log.

### Outstanding

1. **Rewrite the abstract unaided**, then set `\abstractunaidedtrue`. Author only. Ten defects, list
   in `docs/TODO.md` § *Do now*. Caps areas 4 and 6.
2. **Short `\sectionmark` on §2.2.** Minutes. Caps area 6's camera-ready clause after (1).
3. **Transparent-hugepage experiment.** Named in Chapter 8. Converts a candidate into a finding.
   Not required for the current grades.

Housekeeping, not capping: `\ref{tab:abbrev}`; replace `bugden2022rust`. Examiners still
`\censors` when faculty assigns them.

## Seventeenth pass — 30 August 2026 (evening)

Graded independently against the CSM matrix of 9 April 2024, on
`Ha_Vien_Mastersthesis_2026.tex` as a **full draft**, not as a submitted copy. The PDF matches the
source (tex 23:44, PDF 23:45). Declared length is unchanged at **95 pages plus 12 appendix pages**
(115 physical). Standard applied: a draft that prints "Not submittable" is not scored as if an
examiner had received it. The difference from this morning is that the first reporting of the
results is now factually aligned with the tables, so the draft standard no longer has a results
defect to hold area 4 on.

View formed from the manuscript and the artefacts before this file was re-read. Canvas:
`thesis-grade-csm-aug30-rev2.canvas.tsx`.

| Area | 16th pass (30 Aug morning) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Level 5 holds: topic publication-worthy, gap in named prior work, four RQs traced, RQ2 two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Level 5 holds: 109/109 cited, 66% peer-reviewed, search protocol, contrary results engaged |
| 3. Research data and method | 5 | **5** | Level 5 holds: method analysed in depth, data is the canonical bare-metal campaign, description matches |
| 4. Presentation of results | 4.5 | **5** | Level 5's aptness clause now holds. The ten abstract defects are gone from the printed page 3 |
| 5. Discussion and conclusions | 5 | **5** | Level 5 holds: H1--H3 revisited including a refutation, four-way validity, register held |
| 6. Academic text | 4.5 | **4.5** | Level 5's camera-ready clause fails on the unaided switch *and* on a running-header overflow that a following `\sectionmark` did not fix. Level 4 now holds on the whole text, including the abstract |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.83 | **4.92** | |

### Agreement and disagreement with the sixteenth pass

**Agree on areas 1, 2, 3, 5 and 7.** Those were 5 / n/a this morning and they stay there. The body
sample of twelve claims still matches the generated tables. No wrong measured value.

**Disagree on area 4.** The sixteenth pass's failing clause was level 5's aptness of the first
reporting of the results. The printed abstract then said five and five, median matches, and the
far tail cannot be settled on a virtualised host. Page 3 now prints seven and seven, a few
microseconds in Rust's favour, Rust 448 / C++ 392, then C++ 1.7× after both have stopped tracking,
a 10.91% seam bound, 0.250% language share, and 1.6× on the operation alone. Those are the
generated macros. The CCS block and keywords are visible, so the 12 cm box holds. The far-tail
gap is compressed out. That is a writing choice, not a wrong claim, and it does not fail a
descriptor clause.

**Agree that area 6 stays 4.5, disagree on why a `\sectionmark` would finish it.** The source now
has `\sectionmark{Latency and predictability}` immediately after `\section{...}`. The shipped
header on body page 9 is still `2.2. LATENCY, THROUGHPUT, AND PREDICTABILITY IN REAL-TIME SOFTWARE9`.
The log line is unchanged: 23.0782 pt too wide while `\output` is active. titlesec sets the mark
from the section title, so a following `\sectionmark` never reaches the page that contains the
heading. The lift that ships is `\section[Latency and predictability]{...}`. `texaudit.py` still
reports `PASS no overfull boxes`.

**The "submitted as-is both 4.5s would be 4.0" reading is withdrawn for area 4.** Level 4 in area
6 required the whole text to be logical and consistent on questions, setup, findings and
conclusions. That clause now holds, because the abstract no longer contradicts the body. An
examiner who received this PDF would still see "Not submittable" and a jammed running header,
which is why area 6 stays 4.5 rather than 5, not why it would drop to 4.

### Mechanical evidence

Hard gates pass: no LaTeX errors, no undefined references or citations, no multiply defined labels,
no float too large, no placeholders. 109 bibliography entries, all 109 cited, 72 peer-reviewed
(66%). `bugden2022rust` is the remaining arXiv load-bearing cite (beside Pereira).
`zhang2026deadlock` is the journal version; the preprint flag is its `note` field. One unreferenced
float: `tab:abbrev`. Not capping. Sentence length 21.4 ± 11.6, zero semicolons.
`\abstractunaidedfalse`. Build prints "Not submittable".

Generated layer: not re-derived this pass. The printed abstract was extracted with PyMuPDF and
checked against `gen_macros.tex`, `tab_latency.tex`, `tab_significance.tex`, `tab_overload.tex` and
`taxonomy.csv`. Twelve body claims in Chapters 1, 6, 7 and 8 were read against the same artefacts.
No wrong measured value. Sample: pooled p99.99 89.5 / 92.1 vs 142.0 / 176.4 (widest gap 86.9
against `\FarTailRange` 87, language separation 49.9 against `\FarTailLangSep` 50); paired median
$-1.3$ and $-1.2\,\mu$s; overload 146.7 / 84.5 = 1.74 against `\OverloadThrRatio` 1.7, CPU per op
1.78 against 1.8, attached to Rust; knees `\TrackingLoadCpp` 392 and `\TrackingLoadRust` 448; RSS
paired $+1.4$ and $+2.5$ MiB; deadlock 5/12 matching `taxonomy.csv`.

Nothing was edited in the thesis source during this pass.

### Per-area notes

**1, carries 5.** Unchanged. Gap located in Karlback, Arvidsson, Emberg. Four RQs, three
hypotheses, RQ2 built to fail.

**2, carries 5.** Unchanged. Written protocol including the DiVA/Finna step. Gonzalez 0.19% used
to keep statistical and operational significance apart.

**3, carries 5.** Unchanged. The method half is still the pattern of refusals: reading rule kept,
448 kops/s descriptive, pooled statistic with no fallback. Ethics section present.

**4, now 5.** The body was already at this level this morning. What moved is the first page an
examiner reads. Every numeric claim on that page is a generated macro, and the two-sided catalogue,
the tracking split, and the overload 1.7× after collapse are all present and in the right order.
The optional compression of the far tail is recorded in the lift list and is not a cap.

**5, carries 5.** Unchanged. H1 supported below saturation, refuted above it, then declared
ill-posed. §7.2 still refuses a single overload verdict.

**6, 4.5.** Level 4 now holds on the whole text, not only the body. Level 5 fails on finishing: the
unaided switch, and the 23 pt running header after a `\sectionmark` that does not take effect. The
split is named: writing is 5, finishing is 4.

### Outstanding

1. **Look at page 3, then set `\abstractunaidedtrue`.** Author only. Facts are closed. Caps area 6.
2. **Short optional title on §2.2**, not another `\sectionmark`. Minutes. Caps area 6's
   camera-ready clause after (1).
3. **Transparent-hugepage experiment.** Named in Chapter 8. Converts a candidate into a finding.
   Not required for the current grades.

Housekeeping, not capping: `\ref{tab:abbrev}`; replace `bugden2022rust`. Examiners still
`\censors` when faculty assigns them. Optional: name `\FarTailLangSep` in the abstract.

## Eighteenth pass — 31 August 2026

Graded independently against the CSM matrix of 9 April 2024, on
`Ha_Vien_Mastersthesis_2026.tex` as a **full draft**, not as a submitted copy. The PDF matches the
source (tex 00:00:39, PDF 00:00:50). Declared length is unchanged at **95 pages plus 12 appendix
pages** (115 physical). Title page dated 31 August 2026. Standard applied: a draft that prints
"Not submittable" is not scored as if an examiner had received it.

View formed from the manuscript and the artefacts before this file was re-read. Canvas:
[`thesis-grade-csm-aug31.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-aug31.canvas.tsx).

| Area | 17th pass (30 Aug evening) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Level 5 holds: topic publication-worthy, gap in named prior work, four RQs traced, RQ2 two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Level 5 holds: 109/109 cited, 66% peer-reviewed, search protocol, contrary results engaged |
| 3. Research data and method | 5 | **5** | Level 5 holds: method analysed in depth, data is the canonical bare-metal campaign, description matches |
| 4. Presentation of results | 5 | **5** | Level 5 holds: reporting is well considered and apt, printed abstract matches the tables |
| 5. Discussion and conclusions | 5 | **5** | Level 5 holds: H1--H3 revisited including a refutation, four-way validity, register held |
| 6. Academic text | 4.5 | **4.5** | Level 5's camera-ready clause fails on the unaided switch alone. The 23 pt running-header overflow is closed. Level 4 holds on the whole text |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.92 | **4.92** | |

### Agreement and disagreement with the seventeenth pass

**Agree on areas 1, 2, 3, 4, 5 and 7, and on the number in area 6.** Five areas stay at 5. Area 6
stays at 4.5. The mean does not move. Ten claims sampled from Chapters 1, 6, 7 and 8 still match
the generated tables. No wrong measured value. The printed abstract still matches: seven and
seven, a few microseconds in Rust's favour, 10.91% seam, 0.250% language share, 1.6× on the
operation, Rust 448 / C++ 392, then C++ 1.7× after both have stopped tracking, 20/20.

**Disagree on what still fails level 5 in area 6.** The seventeenth pass recorded two finishing
failures: `\abstractunaidedfalse`, and a 23.0782 pt overflow of §2.2's running header after a
following `\sectionmark` that titlesec does not ship. The source now has
`\section[Latency and predictability]{Latency, throughput, and predictability in real-time software}`.
The TOC prints the short title. Body page 9's header is `2.2. LATENCY AND PREDICTABILITY` with
the page number at the right margin. The log has **zero** `Overfull` of any kind, including
`while \output is active`. Extraction still concatenates title and page number on one baseline,
which is a running header doing its job, not an overflow. Do not re-report `SOFTWARE9`. Do not
recommend another `\sectionmark`.

**The seventeenth pass's housekeeping item on `tab:abbrev` is also closed.** Appendix A now cites
the table from the prose. Five unreferenced labels remain, all sectioning.

### Mechanical evidence

Hard gates pass: no LaTeX errors, no undefined references or citations, no multiply defined labels,
no float too large, no placeholders, no overfull boxes. 109 bibliography entries, all 109 cited, 72
peer-reviewed (66%). `bugden2022rust` is the remaining arXiv load-bearing cite (beside Pereira).
`zhang2026deadlock` is the journal version; the preprint flag is its `note` field. Sentence length
21.4 ± 11.6, zero semicolons. `\abstractunaidedfalse`. Build prints "Not submittable". CCS block
ends 9 pt above the keyword row on page 3, so the 12 cm box holds.

Generated layer: macros and tables were read, not re-derived. Sample: pooled p99.99 89.5 / 92.1 vs
142.0 / 176.4 (widest gap 86.9 against `\FarTailRange` 87, language separation 49.9 against
`\FarTailLangSep` 50); paired median $-1.3$ and $-1.2\,\mu$s; overload 146.7 / 84.5 = 1.74 against
`\OverloadThrRatio` 1.7, CPU per op 1.78 against 1.8, attached to Rust; knees `\TrackingLoadCpp`
392 and `\TrackingLoadRust` 448; RSS paired $+1.4$ and $+2.5$ MiB against allocator 1.5--2.4;
deadlock 5/12 matching `taxonomy.csv`; `tab:adoption` first-party CPU 35.9 vs 29.6 s against
`\BuildAllFirstPartyCpuRatio` 0.8, dependency share 54%. `fig:loadsweep`'s caption names 448 kops/s
as the only load at which the languages differ in throughput *with Rust ahead*, which is the
correct scope. `fig:tailpct` still stops at p99.9.

Nothing was edited in the thesis source during this pass.

### Per-area notes

**1, carries 5.** Unchanged. Gap located in Karlback, Arvidsson, Emberg. Four RQs, three
hypotheses, RQ2 built to fail.

**2, carries 5.** Unchanged. Written protocol including the DiVA/Finna step. Gonzalez 0.19% used
to keep statistical and operational significance apart. Karlback's opposite RSS sign is reconciled
as a concurrency-runtime comparison, not a language one.

**3, carries 5.** Unchanged. The method half is still the pattern of refusals: reading rule kept,
448 kops/s descriptive, pooled statistic with no fallback. Ethics section present.

**4, carries 5.** Unchanged. The printed abstract still matches the tables. The optional
compression of the far tail is recorded in the lift list and is not a cap.

**5, carries 5.** Unchanged. H1 supported below saturation, refuted above it, then declared
ill-posed. §7.2 still refuses a single overload verdict.

**6, 4.5.** The split is named: writing is 5, finishing is 4, and finishing now fails on one
clause rather than two. Level 4 holds on the whole text. Level 5 asks for presentation that is
technically camera-ready with excellent finishing polish, and the build still prints Not
submittable.

### Outstanding

1. **Look at page 3, then set `\abstractunaidedtrue`.** Author only. Facts and the header are
   closed. This is now the only item that holds any assessable area off 5.
2. **Transparent-hugepage experiment.** Named in Chapter 8. Converts a candidate into a finding.
   Not required for the current grades.

Housekeeping, not capping: replace `bugden2022rust`. Examiners still `\censors` when faculty
assigns them. Optional: name `\FarTailLangSep` in the abstract. The §2.2 short title and the
`tab:abbrev` reference are **done**. Do not re-report them.

## Nineteenth pass — 31 August 2026 (afternoon)

Graded independently against the CSM matrix of 9 April 2024, on
`Ha_Vien_Mastersthesis_2026.tex` as a **full draft**, scored as the manuscript an examiner would
receive if submitted today. The PDF matches the source (tex 11:43, PDF 15:39). Declared length is
unchanged at **95 pages plus 12 appendix pages** (115 physical). Title page dated 31 August 2026.
Standard applied: the document no longer prints "Not submittable", so it is no longer scored down
for that finishing failure. It is still not supervisor-approved.

View formed from the manuscript, the PDF, and the artefacts before this file was re-read. Canvas:
[`thesis-grade-csm-aug31-rev2.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-aug31-rev2.canvas.tsx).

| Area | 18th pass (31 Aug morning) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Level 5 holds: topic publication-worthy, gap in named prior work, four RQs traced, RQ2 two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Level 5 holds: 109/109 cited, 66% peer-reviewed, search protocol, contrary results engaged |
| 3. Research data and method | 5 | **5** | Level 5 holds: method analysed in depth, data is the canonical bare-metal campaign, description matches |
| 4. Presentation of results | 5 | **5** | Level 5 holds: reporting is well considered and apt, printed abstract matches the tables |
| 5. Discussion and conclusions | 5 | **5** | Level 5 holds: H1--H3 revisited including a refutation, four-way validity, register held |
| 6. Academic text | 4.5 | **5** | Level 5's camera-ready clause now holds: `\abstractunaidedtrue`, printed unaided, no Not submittable, zero Overfull |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.92 | **5.00** | |

### Agreement and disagreement with the eighteenth pass

**Agree on areas 1, 2, 3, 4, 5 and 7.** Five areas stay at 5. Twelve claims sampled from the printed
abstract and Chapters 1, 6, 7 and 8 still match the generated tables. No wrong measured value. The
printed abstract still matches: seven and seven, a few microseconds in Rust's favour, 10.91% seam,
0.250% language share, 1.6× on the operation, Rust 448 / C++ 392, then C++ 1.7× after both have
stopped tracking, 20/20. Header geometry on body page 9: title ends at x=293.7, page number starts
at x=518.6 (225 pt gap). CCS still ends 9 pt above the keyword row.

**Disagree on area 6.** The eighteenth pass held 4.5 because level 5's camera-ready clause failed on
`\abstractunaidedfalse` (every build printed Not submittable). The switch is now true. Page 96
prints "The abstract was accordingly written by the author unaided." The PDF contains no Not
submittable. The eighteenth pass itself said that after the switch, nothing on the finishing list
would remain. This pass verified that claim rather than taking it: zero `Overfull` of any kind,
including `while \output is active`; AI declaration internally consistent; abstract facts still
match. A manuscript grader can check consistency, not authorship. Authenticity of the unaided
rewrite is the author's attestation, which is what the gate was built to record. A model did not
flip the switch in this pass.

### Mechanical evidence

Hard gates pass: no LaTeX errors, no undefined references or citations, no multiply defined labels,
no float too large, no placeholders, no overfull boxes. 109 bibliography entries, all 109 cited, 72
peer-reviewed (66%). `bugden2022rust` is the remaining arXiv load-bearing cite (beside Pereira).
`zhang2026deadlock` is the journal version; the preprint flag is its `note` field. Sentence length
21.4 ± 11.6, zero semicolons. `\abstractunaidedtrue`. CCS block ends 9 pt above the keyword row on
page 3, so the 12 cm box holds.

Generated layer: macros and tables were read, not re-derived. Sample: pooled p99.99 89.5 / 92.1 vs
142.0 / 176.4 (widest gap 86.9 against `\FarTailRange` 87, language separation 49.9 against
`\FarTailLangSep` 50); paired median $-1.3$ and $-1.2\,\mu$s; overload 146.7 / 84.5 = 1.74 against
`\OverloadThrRatio` 1.7, CPU per op 1.78 against 1.8, attached to Rust at four summary sites;
knees `\TrackingLoadCpp` 392 and `\TrackingLoadRust` 448; RSS paired $+1.4$ and $+2.5$ MiB against
allocator 1.5--2.4; deadlock 5/12 matching `taxonomy.csv`; `tab:adoption` first-party CPU 35.9 vs
29.6 s against `\BuildAllFirstPartyCpuRatio` 0.8, dependency share 54%, shipped 106 vs 723 with
ordering reversed under matched static (1577 vs 723) and matched dynamic (106 vs 269);
`tab:budget` 34.5 vs 21.3 ns against `\BudgetCoreRatio` 1.6, share 0.250%. `fig:tailpct` panel (b)
title is generated from whether the interval/spread ratio crosses one.

Nothing was edited in the thesis source during this pass.

### Per-area notes

**1, carries 5.** Unchanged. Gap located in Karlback, Arvidsson, Emberg. Four RQs, three
hypotheses, RQ2 built to fail.

**2, carries 5.** Unchanged. Written protocol including the DiVA/Finna step. Gonzalez 0.19% used
to keep statistical and operational significance apart. Karlback's opposite RSS sign is reconciled
as a concurrency-runtime comparison, not a language one.

**3, carries 5.** Unchanged. The method half is still the pattern of refusals: reading rule kept,
448 kops/s descriptive, pooled statistic with no fallback. Ethics section present.

**4, carries 5.** Unchanged. The printed abstract still matches the tables. The optional
compression of the far tail is recorded in the lift list and is not a cap.

**5, carries 5.** Unchanged. H1 supported below saturation, refuted above it, then declared
ill-posed. §7.2 still refuses a single overload verdict.

**6, 5.** The split that held this at 4.5 is closed. Writing was already 5. Finishing failed on
the camera-ready clause; that clause now holds. Longest sentences still run to about 83 words,
which is not a failing clause once the declaration, the overflow, and the overfull boxes are gone.
Examiners remain unfilled and the class prints that field nowhere.

### Outstanding

No item holds an assessable area off 5.

1. **Transparent-hugepage experiment.** Named in Chapter 8. Converts a candidate into a finding.
   Not required for the current grades.
2. Optional: replace `bugden2022rust`. Optional: name `\FarTailLangSep` in the abstract.
   Housekeeping: `\censors` when faculty assigns examiners.

The unaided switch, the §2.2 short title, and the `tab:abbrev` reference are **done**. Do not
re-report them as grade caps.

## Twentieth pass — 3 September 2026

Graded independently against the CSM matrix of 9 April 2024, on
`Ha_Vien_Mastersthesis_2026.tex` as a **full draft**, scored as the manuscript an examiner would
receive if submitted today. The PDF matches the source (tex 10:53, PDF 10:54 on 1 September 2026).
Declared length is unchanged at **95 pages plus 12 appendix pages** (115 physical). Title page dated
1 September 2026. Standard applied: the document does not print "Not submittable", so it is not
scored down for that finishing failure. It is still not supervisor-approved.

View formed from the manuscript, the PDF, and the artefacts before this file was re-read. Canvas:
[`thesis-grade-csm-sep03.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-sep03.canvas.tsx).

| Area | 19th pass (31 Aug afternoon) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Level 5 holds: topic publication-worthy, gap in named prior work, four RQs traced, RQ2 two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Level 5 holds: 109/109 cited, 66% peer-reviewed, search protocol, contrary results engaged |
| 3. Research data and method | 5 | **5** | Level 5 holds: method analysed in depth, data is the canonical bare-metal campaign, description matches |
| 4. Presentation of results | 5 | **5** | Level 5 holds: reporting is well considered and apt, printed abstract matches the tables |
| 5. Discussion and conclusions | 5 | **5** | Level 5 holds: H1--H3 revisited including a refutation, four-way validity, register held |
| 6. Academic text | 5 | **5** | Level 5's camera-ready clause still holds on the later PDF: `\abstractunaidedtrue`, printed unaided, no Not submittable, zero Overfull |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 5.00 | **5.00** | |

### Agreement and disagreement with the nineteenth pass

**Agree on areas 1, 2, 3, 4, 5, 6 and 7.** This is a hold, not a move. The 1 September source is two
days newer than the nineteenth pass, so the check that mattered was whether those edits reopened a
descriptor. They did not. Fourteen claims sampled from the printed abstract and Chapters 1, 6, 7
and 8 still match the generated tables. No wrong measured value. The printed abstract still
matches: seven and seven, a few microseconds in Rust's favour, 10.91% seam, 0.250% language share,
1.6× on the operation, Rust 448 / C++ 392, then C++ 1.7× after both have stopped tracking, 20/20.
Header geometry on body page 9: title ends at x=293.7, page number starts at x=518.6 (225 pt gap).
CCS last content line sits 19 pt above the keyword heading. Threats table last line at y=748 of 842,
so it still fits.

**No disagreement.** The nineteenth pass set area 6 to 5 when the unaided switch was set. This pass
re-checked that clause rather than taking it: page 96 still prints "The abstract was accordingly
written by the author unaided." The PDF contains no Not submittable. Zero `Overfull` of any kind,
including `while \output is active`. A manuscript grader can check consistency, not authorship. A
model did not flip the switch in this pass.

`Thesis_v2.tex` was edited on 2 September. It is the supervisor skeleton, not the document graded
here. The citation-next-to-clause read after a compression pass remains a process item for that
file (TODO L), not an area-2 cap on the full draft.

### Mechanical evidence

Hard gates pass (`texaudit.py` exit 0): no LaTeX errors, no undefined references or citations, no
multiply defined labels, no float too large, no placeholders, no overfull boxes. 109 bibliography
entries, all 109 cited, 72 peer-reviewed (66%). `bugden2022rust` is the remaining arXiv load-bearing
cite (beside Pereira). `zhang2026deadlock` is the journal version; the preprint flag is its `note`
field. Sentence length 21.4 ± 11.7, zero semicolons. `\abstractunaidedtrue`.

Generated layer: macros and tables were read, not re-derived. Sample: pooled p99.99 89.5 / 92.1 vs
142.0 / 176.4 (widest gap 86.9 against `\FarTailRange` 87, language separation 49.9 against
`\FarTailLangSep` 50); paired median $-1.3$ and $-1.2\,\mu$s; overload 146.7 / 84.5 = 1.74 against
`\OverloadThrRatio` 1.7, CPU per op 1.78 against 1.8, attached to Rust at five summary sites;
knees `\TrackingLoadCpp` 392 and `\TrackingLoadRust` 448, with "all four track to `\TrackingLoad`"
meaning they all still track at 392; RSS paired $+1.4$ and $+2.5$ MiB against allocator 1.5--2.4,
and C++ jemalloc 12.6 coinciding with Rust system 12.5 as the caption claims; deadlock 5/12 matching
`taxonomy.csv`; `tab:budget` 34.5 vs 21.3 ns against `\BudgetCoreRatio` 1.6, share 0.250%.
`fig:tailpct` panel (b) title on the PDF is "The comparison stays resolvable at every percentile"
with ratios 0.2, 0.2, 0.5, 0.6. `fig:overload` bars 147 / 146 / 85 / 84 match the table.

Stale-claim sweep: none of the thirteenth/fourteenth-pass phrases (`for want of hardware counters`,
`replaces these numbers`, `median latency matches`, `all five injected`, `allocator effect is the
larger one`, inverted 1.8× CPU) is in the source.

Nothing was edited in the thesis source during this pass.

### Per-area notes

**1, carries 5.** Unchanged. Gap located in Karlback, Arvidsson, Emberg. Four RQs, three
hypotheses, RQ2 built to fail.

**2, carries 5.** Unchanged. Written protocol including the DiVA/Finna step. Emmerich's slower
driver is stated as more instructions per packet, not literally free. Gonzalez 0.19% used to keep
statistical and operational significance apart. Karlback's opposite RSS sign is reconciled as a
concurrency-runtime comparison, not a language one.

**3, carries 5.** Unchanged. The method half is still the pattern of refusals: reading rule kept,
448 kops/s descriptive, pooled statistic with no fallback. Ethics section present.

**4, carries 5.** Unchanged. The printed abstract still matches the tables. The optional
compression of the far tail is recorded in the lift list and is not a cap. `\PFiftyMedian` 70 is
nearest-ten rounding of table medians 72.1--73.7, generated on purpose as a scale figure.

**5, carries 5.** Unchanged. H1 supported below saturation, refuted above it, then declared
ill-posed. §7.2 still refuses a single overload verdict.

**6, carries 5.** Unchanged. Writing and finishing both hold on the later PDF. Longest sentences
still run to about 83 words, which is not a failing clause once the declaration, the overflow, and
the overfull boxes are gone. Examiners remain unfilled and the class prints that field nowhere.

### Outstanding

No item holds an assessable area off 5.

1. **Author proofread.** Process, not a matrix clause. The only remaining risk no grader can close
   from the PDF.
2. **Transparent-hugepage experiment.** Named in Chapter 8. Converts a candidate into a finding.
   Not required for the current grades.
3. Optional: replace `bugden2022rust`. Optional: name `\FarTailLangSep` in the abstract.
   Housekeeping: `\censors` when faculty assigns examiners.

The unaided switch, the §2.2 short title, and the `tab:abbrev` reference remain **done**. Do not
re-report them as grade caps.


## Twenty-first pass — 7 September 2026

Graded independently against the CSM matrix of 9 April 2024, on `Ha_Vien_Mastersthesis_2026.tex`
as a **full draft**, scored as the manuscript an examiner would receive if submitted today.
**Build verified rather than assumed**: the `.tex` timestamps are newer than the PDFs (draft
09:50 on 7 September against a PDF of 12:23 on 6 September), but `latexmk -pdf` reports
`Nothing to do` for both the draft and `Thesis_v2`, so latexmk's content hashes match and the
newer timestamps are no-op re-saves. Declared length **96 pages plus 12 appendix pages** (118
physical), unchanged since the 4 September acronym pass. Standard applied: the document prints no
"Not submittable", so it is not scored down for that. It is still not supervisor-approved.

View formed from the manuscript, both PDFs, and the artefacts before this file was re-read.
Canvas: [`thesis-grade-csm-sep07.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-sep07.canvas.tsx).

| Area | 20th pass (3 Sep) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Level 5 holds. RQ1's metric list is still exactly `tab:latency`'s columns, RQ2 still two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Level 5 holds. 109/109 cited, 66% peer-reviewed, contrary results named as such |
| 3. Research data and method | 5 | **5** | Level 5 holds. Considered and rejected a drop: see the note below |
| 4. Presentation of results | 5 | **4.5** | Level 5's "well considered and apt". `tab:testbed`'s caption is contradicted by its own Toolchain row, §6.4.7 hand-types a wrong compiler version, `tab:findings`' RQ3 cell cannot pick out a host |
| 5. Discussion and conclusions | 5 | **5** | Level 5 holds. None of this pass's findings is in Chapter 7 |
| 6. Academic text | 5 | **4.5** | Level 4's "consistent ... description of research setup" (three toolchain-parity sites) and level 5's "excellent finishing polish" (a broken ellipsis in §1.4 of both documents) |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 5.00 | **4.83** | |

### The finding: toolchain parity with the guest is claimed and false

**`\GuestGpp` is 15.1.1 and `\MainGpp` is 15.2.1**, each generated from its own campaign's
environment capture (`env-20260812-154523.txt` and `env-20260827-151925.txt`). `rustc` does match
at 1.97.1. The container pins the `gcc-toolset` major version and not the point release, so a
rebuild between the guest campaign and the 27 August canonical repeat moved g++ by one patch
release. Four sites do not know this:

1. **§6.1 l. 2209–2211.** "Both implementations are built and run inside a pinned container image
   carrying `\MainDistro` with `g++ \MainGpp` and `rustc \MainRustc`, **which is the same userspace
   and compiler pair the earlier virtualised campaign used**." The macro in the same sentence
   prints 15.2.1 and the guest's prints 15.1.1.
2. **§6.4.5 l. 2997.** "at the same shard count, the same fourteen load levels, the same
   `\GuestRepeats` repeats and **the same toolchain**. Two campaigns that differ in **the machine
   alone** are an opportunity a single-host study does not get."
3. **§6.4.5 l. 3131.** "The reported sweep and the virtualised one share a design and **differ in
   the machine**."
4. **`tab:testbed`'s caption, l. 4573–4575.** "The columns are arranged so that **each adjacent
   pair isolates one change**. Reported sweep against virtualised host: the same design on a
   different machine." Its own Toolchain row, l. 4591, prints `g++ 15.2.1` against `g++ 15.1.1`
   against `g++ 13.3.0, rustc 1.98, so a compiler change is tested too`.

**The second bare-metal column carries the disclosure and the guest column does not.** That is
calibration pattern 3, half a pair fixed, at one remove: the eleventh pass found this exact defect
for the confirmation host (item 3h), the remediation of 26 August fixed it by saying "four ways and
not three", and nobody asked the same question of the guest comparison. Confirmed in the shipped
PDF by text extraction, not only in the source.

**Severity, stated plainly so a future pass does not over- or under-read it.** Nothing measured
moves. A GCC patch release is not a plausible confound for any effect the thesis reports, and the
honest repair *adds* a disclosure rather than withdrawing a claim, exactly as the `\Bm` column's
did. What fails is the thesis's own standard: a table designed so each adjacent pair isolates one
change, captioned as doing so, with a row that shows two changes.

### The second finding: a wrong hand-typed compiler version

**§6.4.7 l. 3162** reads "That C++ toolchain is the local development machine's and not the
measurement host's `g++~15.1.1`". The measurement host is **15.2.1**. 15.1.1 is the *guest's*
value. It was correct while the August campaigns were the main dataset and was not re-read when
the canonical repeat replaced them, which is the pattern `AGENT.md` §2 says cost this thesis a
grade point twice in two days. The fault-injection versions in the same two sentences (`g++ 13.3`,
`rustc 1.97`) are hand-typed too and are **correct**, matching `faults/results/taxonomy.md`.

**Why seven passes missed both.** `texaudit.py`'s prose-number heuristic requires a unit, so a bare
dotted version number is invisible to it. Both values sit in the safety subsection and an appendix
table rather than in the performance prose a pass reads first. And the generated layer was clean at
every check, which is when a pass is most tempted to skip reading the sentences around it. This is a
detector gap, and the fifth lift closes it.

### The third finding: an editing pass broke an ellipsis in the introduction

**§1.4, draft l. 683 and `Thesis_v2.tex` l. 488.** "On resources the Rust process holds a few MiB
more resident memory, again under both allocators, in the same direction and the same order of
magnitude on all three machines measured. **How it compares against the cost of the allocator
choice is not:**" The `is not` has no predicate to elide. Traced through `git log -L`:

- `a0e9122` wrote "**That effect is the same size on all three machines measured.** How it compares
  against the cost of the allocator choice **is not**:" — grammatical, the copula is right there.
- `ed6debe`, the fourteenth pass's scope-attachment fix, folded that clause into a prepositional
  phrase hanging off "holds ... resident memory" and deleted the copula.

So a fix introduced it, and it is in the introduction of both documents. `AGENT.md` already records
that about 25 of the 69 August defects were introduced by the editing passes themselves; this is one
more, and the sync rule applies because the passage is shared.

### The fourth, minor: a guest-era phrase in `tab:findings`

The RQ3 evidence cell reads "CPU: resolved in both regimes, opposite signs, and resolved with one
sign **on bare metal** below saturation". The reported host is *also* bare metal now, so the phrase
cannot pick out the confirmation host it means, and the main campaign's own CPU rows clear Holm
under both allocators anyway. Ambiguous rather than wrong.

### Mechanical evidence

Hard gates pass (`texaudit.py` exit 0): no LaTeX errors, no undefined references or citations, no
multiply defined labels, no float too large, no placeholders, **zero `Overfull` of any kind
including `while \output is active`**, 0 underfull. Every float label referenced from the body. 109
entries, all 109 cited, 72 peer-reviewed (66%). The one prose-number hit is Gonzalez's `0.19 \%`, a
literature value and a known false positive.

**`.acronyms.py` passes both documents**: `not written out at first use: 0` against 57 declared
entries in the draft and 26 in the skeleton, with 5 waivers in the draft and 1 in the skeleton each
printed with its reason, and 2 declared-without-bare-use names in the skeleton, both explained. The
`UndefinedBehaviorSanitizer (UBSan)` expansion the gate was written to find ships in the PDF. The
skeleton writes the sanitiser names out in full and never uses the acronyms, so nothing is owed
there.

**`.aitells.py`**: zero semicolons, both colon-capitalisation checks at **0**, sentence length
21.5 ± 11.8 (range 3–83). Nine dash hits, all correct typography. The one `not just ... but` hit is
the known `\emph`-stripping artefact. `rather than` at **72 instances, 20.3 per 10k**, up from the
53 and 14.9 recorded in `CALIBRATION.md` item 4 at flat word count; part of the sentence
lengthening is the acronym pass writing names out at first use.

**Generated layer re-derived, not read.** `plot_figures.py --outdir /tmp/scratchgen` reproduced
`gen_macros.tex` and **all 12 `tab_*.tex` byte-identical** to the shipped copies. Fourteenth
consecutive pass with no wrong measured value, and the first since the fourteenth to re-derive
rather than read. Spot-checks against definitions rather than values: `\PFiftyMedian` 70 is
nearest-ten rounding of medians 72.1–73.7; `\BmFarTailSepHi` 96 **is** a load (`max` of the loads
below the held-out top), so "between 32 and 96 kops/s" is right; `\OverloadCpuPerOpRatio` 1.8
attaches to Rust at all five summary sites; every `\SatKnee` use is qualified as the lowest of the
four and every "where an arm stops coping" sentence uses `\TrackingLoad{Cpp,Rust}`;
`\BmRssLargerEffect` exists and is quoted nowhere.

**Two sweeps run and clean.** A split-word detector over both rendered PDFs found **0 genuine
hits**: the `safe`/`ty` defect the author fixed in the uncommitted diff was the only instance, and
every candidate my fragment list flagged (`less`, `ships`, `like`, `some`, `fully`) is a real word.
British spelling is held (behaviour 26/0, optimisation 9/0, analyse 6/0); `artifact` appears 9 times
and **every one is the ACM-sense research deliverable** while `artefact` appears 14 times and none
is, so it reads as a deliberate convention and was **not** scored as drift. Worth one confirmation
from the author.

Nothing was edited in the thesis source during this pass.

### Per-area notes

**1, carries 5.** Unchanged and untouched by these findings. Gap in named prior work, four RQs
traced, RQ2 built to fail, RQ1's metric list still exactly `tab:latency`'s columns.

**2, carries 5.** Unchanged. Arvidsson's tail is called a challenge it would be dishonest to omit.
The five Ericsson theses are declared neither peer-reviewed nor indexed and cited as a record of
vendor attempts rather than results.

**3, holds 5, and the rejection is on the record.** A drop was considered, because
`CALIBRATION.md`'s area-3 4.5 anchor is a *description* failure and this pass found one. Rejected:
that anchor was set by load-bearing description defects (a reading rule contradicted by its own
results section, a pinned load rule misdescribed), and a GCC patch release mis-described is not that
weight. The method is untouched: the reading rule is kept where it costs nothing and said to be kept
for that reason, the 448 rung is described and not tested, the pooled statistic returns `None`
rather than falling back, ethics is present. **Do not read this hold as agreement that the finding
is harmless to area 3 if it grows**: if a future pass finds the same shape on a variable that could
move a result, area 3 is where it lands.

**4, drops to 4.5.** Level 4 holds fully and is not in question. Level 5's aptness clause fails on
three sites, above. The half grade encodes that the *evidence* reads at 5 (whole generated layer
byte-identical, evidence status per RQ, printed abstract matching) and the *reporting* at 4.

**5, carries 5.** Unchanged. All four toolchain-parity sites are in Chapter 6 and Appendix D, so
this is not the area-4 finding counted twice, which is the same discipline the eleventh pass used in
reverse. H1 to H3 revisited individually, fifteen-row threats table with a live residual per row,
the single-author threat evidenced by Emberg and Wadsten's reversal rather than conceded.

**6, drops to 4.5.** The half grade splits writing from consistency-and-finishing, which is what
`CALIBRATION.md` says a 4.5 here means. Writing reads at 5 and the build is camera-ready. Level 4's
clause on consistent description of the research setup is nicked by the three toolchain sites, and
level 5's finishing polish by the §1.4 ellipsis in both documents. **The 83-word sentence is not
counted**: the twentieth pass ruled it not a failing clause and that ruling is respected.

### Outstanding

1. **The three toolchain sites plus `tab:testbed`'s caption.** ~30 minutes. This is what holds
   areas 4 and 6 at 4.5. Repair by disclosure, the way the `\Bm` column already does.
2. **§6.4.7's `g++~15.1.1`.** ~20 minutes, use `\MainGpp`.
3. **§1.4's ellipsis**, draft and skeleton together. ~5 minutes.
4. **`tab:findings`' RQ3 evidence cell.** ~10 minutes, name the host.
5. **The durable fix, ~1 hour.** Generate the fault-catalogue toolchain into `gen_artefacts.tex`
   from `taxonomy.md`, and teach `texaudit.py` to flag bare dotted version numbers in prose. Items
   1 and 2 recur without this.
6. **Author proofread.** Process, not a matrix clause.
7. Optional, no grade effect: `rather than` back down toward 15 per 10k; jitter's idle
   `tab_jitter.tex` machinery; replace `bugden2022rust`. **New measurement**: the
   transparent-hugepage experiment, about one machine-hour, still the only item needing an
   instrument.
8. **Not checked this pass**: the slide deck against the thesis. No campaign moved, so the risk is
   low, but no gate in the repository sees it.

The unaided switch, the ten abstract defects, the §2.2 short title, `SOFTWARE9` extraction, the
bare-metal tail campaign, the pooled far tail with no per-run fallback, and the 448 rung's threats
row remain **done**. Do not re-report them as grade caps.

## Twenty-second pass — 7 September 2026, afternoon

Graded against the CSM matrix of 9 April 2024 on `Ha_Vien_Mastersthesis_2026.tex` as a **full
draft**, scored as the manuscript an examiner would receive if submitted today. **Second pass of
the same day.** The twenty-first graded the 09:50 source; eleven commits have landed since, and
one of them put a **new abstract into `Thesis_v2.tex`**, so this is a pass over changed prose and
not a restatement. Build verified: both sources and both PDFs carry 15:21 to 15:25 timestamps and
`git status` is clean. Declared length **96 pages plus 12 appendix pages** (118 physical), read
from the `.aux`, unchanged.

Canvas: [`thesis-grade-csm-sep07-rev2.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-sep07-rev2.canvas.tsx).

| Area | 21st pass (7 Sep, morning) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Level 5 holds. Gap in named flaws of five vendor theses, four RQs traced, RQ2 two-sided, H1 refuted and then declared ill-posed |
| 2. Scholarly framework and sources | 5 | **5** | Level 5 holds. 109/109 cited, 66% peer-reviewed, Arvidsson and Emmerich and Emberg engaged as contrary |
| 3. Research data and method | 5 | **5** | Level 5 holds. Nothing in this pass's findings touches the method or the data |
| 4. Presentation of results | 4.5 | **4.5** | Level 5's "well considered and apt". The same three sites, re-read in today's source and unchanged |
| 5. Discussion and conclusions | 5 | **5** | Level 5 holds. A drop was considered on the H1 revisit's wording and rejected, below |
| 6. Academic text | 4.5 | **4.5** | Level 4's "consistent … description of research setup" and level 5's finishing polish. Same two clauses |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.83 | **4.83** | |

### The four standing items were re-read, not taken on trust

All four are unchanged in the shipped source. Line numbers are current as of the 15:21 file.

1. **Toolchain parity, three prose sites.** §6.1 l. 2213 still reads "which is the same userspace
   and compiler pair the earlier virtualised campaign used", and l. 2217 "differ in the hardware
   alone". §6.4.5 l. 3000 "the same toolchain … differ in the machine alone". §6.4.5 l. 3134
   "share a design and differ in the machine". `tab:testbed`'s caption l. 4576 still promises that
   each adjacent pair isolates one change, over a Toolchain row at l. 4594 printing `\MainGpp`
   against `\GuestGpp`.
2. **§6.4.7 l. 3165** still hand-types "the measurement host's `g++~15.1.1`".
3. **§1.4's ellipsis**, draft l. 686 and skeleton l. 516, still has no predicate.
4. **`tab:findings`' RQ3 cell**, l. 3594, still says "on bare metal".

The eleven commits since the morning went to the skeleton's abstract, to acronym capitalisation,
and to `AGENT.md`, `README.md` and the grading skill. **None of them touched a site that holds a
grade**, which is why the mean is a hold rather than a movement.

### New finding: the word *operation* carries two referents a factor of 400 apart

§6.4.1 l. 2574–2578 defines the term and the whole §`sec:budget` argument rests on the definition:
"The operation is $\BudgetCoreCpp$~ns in C++ … The work the languages actually perform is
therefore at most $\BudgetCoreShareMax\%$ of what the sweep measures." That is the sentence which
licenses the thesis's non-negotiable refusal to bound a language effect from the sweep.

Three later sites attach the same bare noun to the **end-to-end round-trip** instead:

- **§7.1 l. 3621**, the RQ1 discussion: "the median gap is a fraction of a $\PFiftyMedian\,\mu$s
  **operation**", where `\PFiftyMedian` is 70, the round-trip.
- **§7.1 l. 3623**: "roughly the width of a whole median **operation**".
- **§7.3 l. 3863**, the H1 revisit: "about a microsecond on an **operation** of
  $\PFiftyMedian\,\mu$s".

Line 3629, eight lines below the first of them, then reads "The operation the languages execute is
$\BudgetCoreShareMax\%$ of what the sweep measures", and l. 3571 and l. 4173 both use bare
"operation" for the *inner* quantity. §1.4 l. 672 gets it right and writes "end-to-end
**round-trip** of $\PFiftyMedian\,\mu$s", which is the wording the three sites want.

**Why it is worth fixing and why it did not drop an area.** It is `CALIBRATION.md`'s
wrong-scope class, and it lands in two of the four places that file says a grader looks: the RQ
discussion and the hypothesis revisit. But its direction is conservative, since it compares the
gap against a number 400 times larger than the correct comparator and so understates the language
effect, and no reliability judgement rests on it. Area 5 was therefore held after considering a
drop, on the same discipline the twenty-first pass used to hold area 3. Area 6's consistency
clause is already failing for the toolchain sites and this is nicked by the same clause rather
than a new one.

**The transferable part.** The twenty-first pass checked `\PFiftyMedian` and recorded, correctly,
that 70 is nearest-ten rounding of medians 72.1–73.7. It checked the *value*. The referent of the
noun beside it went unread. `CALIBRATION.md` already says to check a macro's definition and not
only its value; this pass adds that the sentence's own nouns need the same treatment.

### The skeleton's new abstract, written after the twenty-first pass

`37cc871` added an abstract to `Thesis_v2.tex`, and four further commits numbered and clarified
it. It is good work and the numbering is an improvement on the draft's run-on Results paragraph.
Three items came in with it, all in l. 139:

- **Point (3) drops a denominator.** "any extra time on a real call is at most
  $\FfiOpBoundPct\%$". `plot_figures.py:2388` defines the macro as
  `100 * op_seam_delta_hi_ns / native`, so the percentage is *of the native operation*, and the
  draft's abstract says so ("costs at most $\FfiOpBoundPct\%$ of one operation"). A bare
  percentage has no referent.
- **Point (5) attributes the full path to a language.** Point (4) says "that clock cannot
  attribute a gap to C++ or Rust", and point (5) then says "Below overload the full path is a few
  microseconds faster in Rust". Same clock. The draft joins the two claims in one sentence with
  "yet" and attributes the difference to the *test* rather than to the path, which is the register
  the rest of the thesis holds.
- **"mixed-order repeats" for "interleaved repeats".** Interleaving is a named fairness control.
  The draft writes "interleaved" 34 times and "mixed-order" never, and §1.4 of the skeleton itself
  states the identical claim as "in \OverloadThrAgree{} interleaved repeats" 372 lines below the
  abstract.

Separately, **the two abstracts have diverged**: the skeleton now carries the better version and
the draft, which is the submission document, carries the older one. The sync rule of `AGENT.md` §1
exists for this. None of the four is folded into a grade, under rule 1 of the grading skill: an
examiner receives one manuscript and it is not this one. They are lifts.

### Mechanical evidence

**The generated layer was re-derived, not read.** `plot_figures.py --outdir /tmp/rederive`
reproduced `gen_macros.tex` and **all 12 `tab_*.tex` byte-identical** to the shipped copies, in 24
seconds. Fifteenth consecutive pass with no wrong measured value.

Hard gates pass (`texaudit.py` exit 0): no LaTeX errors, no undefined references or citations, no
multiply defined labels, no float too large, no placeholders, 118 pages, **zero `Overfull` of any
kind**, 0 underfull. Every float label referenced from the body. 109 entries, all cited, 72
peer-reviewed (66%). The single prose-number hit is Gonzalez's `0.19 \%`, the known literature
value.

`.aitells.py`: **0 semicolons** and both colon checks at **0** in both documents. Draft 21.5 ± 11.8
words per sentence, skeleton 17.3 ± 11.1, both in the human band. Nine dash hits in the draft and
seven in the skeleton, all numeric ranges or compound proper names. `.acronyms.py`: `not written
out at first use: 0` on both, waivers printed.

**Today's editing round in the draft is clean, which is unusual here.** `c3cf0e6` rewrote 58 lines
standardising acronym expansions to sentence case, and it was checked in both directions: "radio
access network" is lowercase at all six body sites across both documents and "UE Context
Management" is capitalised at all twenty, so the list and the prose agree and no split was
introduced.

**One candidate defect was read and discounted.** l. 3205's "Safe Rust rejects the double release
with `\texttt{E0382}`" sits in the seam double-free paragraph, whose `tab:taxonomy` row reads
"compiles, aborts". The sentence describes the **in-guarantee** class, which `taxonomy.csv` records
as "compile-time prevented (E0382)", and the clause immediately after it explains that handing a C
caller a raw pointer is what ends that tracking. The prose is correct and should not be "fixed".

**Headline claims read against each other**, not one at a time: far tail (resolved, Rust lower),
overload throughput (C++ $1.7\times$, 20/20), overload CPU per completed operation (Rust
$1.8\times$), peak RSS direction and size with a host named at every ratio, and the two tracking
loads (448 against 392) agree across the abstract, the introduction, §6.4, Chapter 7 and Chapter 8.
No inverted participle at any of the five summary sites.

### Per-area notes

**1, carries 5.** Untouched. The gap is located rather than asserted at l. 1110–1116, which names
the flaw in each of the five vendor theses. Noted and not scored: RQ4 names *effort* and *risk*,
and `tab:design` gives neither a primary metric, so those two axes are answered qualitatively in
§7.6 where the other three are measured. Level 5 does not require it and the qualitative treatment
is honest about being qualitative.

**2, carries 5.** Untouched. Contrary results are engaged as challenges rather than mentioned. The
"operation" referent is a concept-definition wobble on one term at three sites, which is not enough
to fail "excellent in-depth command".

**3, carries 5.** Untouched. Nothing in this pass reaches the method or the data. The refusals that
earn the level are all still in place.

**4, holds 4.5.** The same three sites, re-read. Level 4 holds fully. The evidence half still reads
at 5, with the whole generated layer byte-identical.

**5, holds 5, and the rejection is on the record.** A drop was considered on the H1 revisit's
"operation of 70 µs", since chapter-7 wording is exactly what took this area to 4.5 at the eleventh
pass. Rejected: that anchor was a discussion one section behind its own results, and a noun used
loosely in a conservative direction is not that weight. **Do not read the hold as agreement that
the wording is harmless if it spreads.**

**6, holds 4.5.** Same two clauses. The half grade still splits writing from
consistency-and-finishing. The 83-word sentence is **not** counted, per the twentieth pass, and a
later pass does not relitigate a ruling on unchanged text.

### Outstanding

1. **The three toolchain sites plus `tab:testbed`'s caption.** ~30 minutes. Holds areas 4 and 6.
2. **§6.4.7's `g++~15.1.1`.** ~20 minutes, use `\MainGpp`.
3. **§1.4's ellipsis**, both documents together. ~5 minutes.
4. **`tab:findings`' RQ3 evidence cell.** ~10 minutes, name the host.
5. **Hold "operation" to one referent**, l. 3621, l. 3623 and l. 3863. ~15 minutes. §1.4 already
   has the wording to copy. New this pass.
6. **The skeleton's abstract**: restore the denominator in (3), restore the test-attribution
   register in (5), put "interleaved" back, and port the numbered version to the draft so the two
   documents agree again. ~15 minutes. New this pass.
7. **The durable fix, ~1 hour.** Generate the fault-catalogue toolchain into `gen_artefacts.tex`,
   and teach `texaudit.py` to flag bare dotted version numbers in prose. Items 1 and 2 recur
   without it.
8. **Author proofread.** Process, not a matrix clause.
9. **Not checked this pass**: the slide deck against the thesis, for the second consecutive pass.
   No campaign moved so the risk is low, but no gate in the repository sees the deck.

Nothing was edited in the thesis source during this pass. The closed items listed at the end of the
twenty-first pass remain closed and must not be re-reported as grade caps.

## Twenty-third pass — 10 September 2026

Graded independently against the CSM matrix of 9 April 2024, on **`Thesis_v3.tex` / `Thesis_v3.pdf`**,
the supervisor-facing eight-chapter argument. Chapter 1 is the draft introduction. Chapters 2 to 8
are five argument paragraphs each, with twelve figures. **Standard applied:** an examiner who
received this 57-page PDF, not the 118-page full draft. The five-paragraph contract is named, not
used as a free pass on level 5 aptness. The full draft was not re-read. Its standing grade remains
the twenty-second pass.

**Build verified.** `Thesis_v3.tex` 18:15, PDF and `build/Thesis_v3.log` 20:26 on 10 September, so
the PDF is current. `texaudit.py Thesis_v3.tex --macros figures/gen_macros.tex` exits 0: no LaTeX
errors, no undefined references or citations, no multiply defined labels, no float too large, **zero
Overfull of any kind**, 0 underfull, 57 pages. Every float label referenced from the body. 111 bib
entries, 59 cited in this document (52 uncited, expected on a shared `.bib`), 74 peer-reviewed
venues (67%). One placeholder warning: `Thesis_v3.tex:29`, `\examiners{Prof. Keijo Heljanko, TBD}`.
One prose-number hit with a unit: l. 393, Meneely's 58.2%, a literature value.

Canvas: [`thesis-grade-csm-sep10.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-sep10.canvas.tsx).

| Area | 22nd pass (draft, 7 Sep) | This pass (skeleton) | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Level 5 holds. Gap in named flaws of five vendor theses, four RQs, H1 refuted and declared ill-posed, RQ2 two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Level 5 holds. Contrary results engaged. Background is three sections by contract; the gap section carries the command |
| 3. Research data and method | 5 | **5** | Level 5 holds. The refusals (no `isolcpus`, 448 described not tested, pooled p99.99 out of the family) are in the five-paragraph method chapter |
| 4. Presentation of results | 4.5 | **4.5** | Level 5's "well considered and apt". Different sites: abstract (4) vs (5), `\CpuDiffAbsMax` scope, no numeric result table |
| 5. Discussion and conclusions | 5 | **5** | Level 5 holds. Compressed chapter still revisits H1–H3, names the single-author threat, and refuses the “safe = concurrency-safe” reading |
| 6. Academic text | 4.5 | **4.5** | Level 4 consistency (mixed-order vs interleaved, bare FFI percentage) and level 5 finishing (`TBD` on the title page). Toolchain prose and the §1.4 ellipsis are **closed** in this PDF |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.83 | **4.83** | Same number. The clauses that set 4.5 moved |

### Closed in this PDF, do not re-report as skeleton caps

1. **Toolchain parity with the guest.** The testbed section names `\MainGpp` 15.2.1 against
   `\GuestGpp` 15.1.1, and the kernel difference beside it. No “same toolchain” sentence survives.
2. **§1.4 “is not:” with no predicate.** Grep finds no hit. The twenty-second pass still had it at
   skeleton l. 516 on 7 September.
3. **`tab:testbed`, §6.4.7, `tab:findings`.** Not in this document. They remain the full draft's
   caps, last confirmed on the afternoon of 7 September.

### What holds 4.5 on this PDF

1. **Abstract (3).** “any extra time on a real call is at most `\FfiOpBoundPct\%`”. The macro is
   `100 * op_seam_delta_hi_ns / native`. The figure caption still says “of one operation”. The
   abstract does not. The twenty-second pass listed this as a lift because it was grading the draft.
   An examiner of this PDF reads this abstract, so it folds into area 4 and area 6.
2. **Abstract (5) after (4).** (4) says the round-trip clock cannot attribute a gap to C++ or Rust.
   (5) then says “Below overload the full path is a few microseconds faster in Rust.” Same clock.
   The draft's §1.4 joins the two with the test as the subject. This abstract does not.
3. **“mixed-order repeats”** in the abstract against “interleaved” in the method chapter and the
   rest of the thesis. Interleaving is a named fairness control.
4. **`\CpuDiffAbsMax` (5.1 pp)** attached to “while the service copes”.
   `write_generated_macros()` builds it from `cpu_rows` at `point == "repr"`. Same wrong-scope class
   as the draft's `tab:findings` RQ3 cell.
5. **`\examiners{Prof. Keijo Heljanko, TBD}`.** `texaudit.py` flags it as a template leftover. The
   draft's corresponding line is Heljanko only.

### Mechanical evidence

`.readability.py`: 571 sentences, 8641 words, mean 15.1 ± 8.3, Flesch 55.0, grade 9.3. Short
sentences 56.7% (target 25–35%), which is the five-paragraph compression. Three paragraphs of three
or more sentences with no sentence under 15 words, including the research-gap paragraph at l. 518.
`.aitells.py`: 0 semicolons, both colon checks at 0, 10 dash hits all numeric ranges or compound
proper names (Herfindahl–Hirschman, Fowler–Noll–Vo). Two counting stubs: l. 239 “Three terms recur
throughout” (a tell, not a cap) and l. 766 “Both versions follow it” (states the fairness control).
`.acronyms.py`: not written out at first use 0, five printed waivers.

Headline macros checked against `figures/gen_macros.tex` and siblings, not remembered: tracking
loads 448 against 392, `\SatKnee` 392 qualified as the lowest of the four, overload `\OverloadThrRatio`
1.7 with C++ faster in 20/20, `\PFiftyDiffAbsMax` 1.3 µs, RSS 1.4–2.5 against 1.5–2.4 MiB,
`\BudgetCoreShareMax` 0.250%, `\FfiOpBoundPct` 10.91, `\DeadlockTsanHits` 5 of `\DeadlockTsanRuns`
12. No measured value is wrong.

### Per-area notes

**1, carries 5.** Untouched. The gap is located rather than asserted. RQ2 still includes classes
safe Rust is expected not to prevent.

**2, carries 5.** Command of the topic is in the gap section and the introduction, which is what
this document has. 59 cited keys is enough for the skeleton. A drop for the three-section
background was considered and rejected: level 5 asks for command and critical maturity, not for a
page count matching the draft.

**3, carries 5.** The method chapter still states the frozen spec, the Holm family, the floors, the
448 exclusion, the pooled far tail kept out, and why `isolcpus` is refused.

**4, holds 4.5.** Level 4 holds: findings grouped by RQ, figures with intervals, generalisability
pondered, no wrong measured value. Level 5 fails on the abstract's two register hits, the CPU
macro's scope, and the absence of a numeric result table in this PDF.

**5, carries 5.** H1 is allowed to fail and then declared ill-posed. Karlback is reconciled as two
runtimes. Ethics refuses the marketing reading of RQ2. A drop for missing `tab:threats` was
considered and rejected: §standing names the three load-bearing threats.

**6, holds 4.5.** Writing and the build read at 5. The toolchain consistency clause that capped the
draft is **closed** here. What remains is mixed-order vs interleaved, the bare FFI percentage, and
TBD on the title page. Short-sentence share 56.7% is noted as compression, not as a grammar fail.

### Outstanding on this PDF

1. **Abstract (3), (5), and “mixed-order”.** ~15 minutes. Holds areas 4 and 6 on the skeleton.
2. **`\CpuDiffAbsMax` scope in the resource paragraph.** ~10 minutes.
3. **Title-page `TBD`.** ~5 minutes, or name the second examiner.
4. **The full draft's four standing items**, last confirmed 7 September afternoon. They are not
   this PDF's caps and were not re-read today.

Nothing was edited in the thesis source during this pass. Do not report the draft's toolchain
sites as defects in the skeleton, and do not report the skeleton's abstract defects as already
folded into the draft's grade. They were lifts on 7 September because that pass was grading the
other file.

## Twenty-fourth pass — 11 September 2026

Graded independently against the CSM matrix of 9 April 2024, on **`Thesis_v3.tex` / `Thesis_v3.pdf`**,
the supervisor-facing eight-chapter argument. Chapter 1 is the draft introduction. Chapters 2 to 8
are five argument paragraphs each, with twelve figures and `tab:latency`. **Standard applied:** an
examiner who received this 50-page PDF, not the 115-page full draft. The five-paragraph contract is
named, not used as a free pass on level 5. The full draft was not re-read. Its standing grade
remains the twenty-second pass.

**Build verified.** `Thesis_v3.tex` 15:37:23, PDF 15:37:46 on 11 September, so the PDF is current.
`texaudit.py Thesis_v3.tex --macros figures/gen_macros.tex` exits 0: no LaTeX errors, no undefined
references or citations, no multiply defined labels, no float too large, **zero Overfull of any
kind** (including `while \output is active`), 0 underfull, 50 pages. Every float label referenced
from the body. 111 bib entries, 61 cited in this document (50 uncited, expected on a shared `.bib`),
74 peer-reviewed venues (67%). **No placeholders.** One prose-number hit with a unit: l. 422,
Meneely's 58.2%, a literature value.

The source was still being edited when the pass started. The grade is of the 15:37 build after it
had been stable for more than 90 seconds.

Canvas: [`thesis-grade-csm-sep11.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-sep11.canvas.tsx).

| Area | 23rd pass (skeleton, 10 Sep) | This pass (skeleton) | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Hold. Gap in named flaws of five vendor theses, four RQs, H1 refuted and declared ill-posed, RQ2 two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Hold. Contrary results engaged. Background is three sections by contract |
| 3. Research data and method | 5 | **5** | Hold. The refusals (no `isolcpus`, 448 described not tested, pooled p99.99 out of the family) are in the five-paragraph method chapter |
| 4. Presentation of results | 4.5 | **5** | Yesterday's three aptness hits are closed. `tab:latency` is present. `\CpuDiffAbsMax` is scoped to `\ReprLoad`. Abstract (5) refuses to bound a language effect from the end-to-end median |
| 5. Discussion and conclusions | 5 | **5** | Hold. Compressed chapter still revisits H1–H3, names the single-author threat, and refuses the “safe = concurrency-safe” reading |
| 6. Academic text | 4.5 | **5** | Yesterday's consistency and finishing hits are closed: interleaved, FFI denominator, no `TBD`, date frozen to 11 September 2026. Toolchain prose and the §1.4 ellipsis stay closed |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.83 | **5.00** | Areas 4 and 6 lift. The bar did not move |

### Closed since the twenty-third pass, do not re-report as skeleton caps

1. **Abstract (3) bare `\FfiOpBoundPct`.** Abstract, H3, `fig:ffiseam`, and the conclusion all read
   “of that call”. The macro is `100 * op_seam_delta_hi_ns / native` (an upper bound). “At most”
   is the right verb.
2. **Abstract (5) after (4).** (5) now says the paired median gap of `\PFiftyDiffAbsMax` µs is too
   small to bound a language effect, then reports tracking loads and overload. The clock (4)
   disqualified is not the clock (5) uses to rank.
3. **“mixed-order repeats”.** Abstract and method chapter both write “interleaved”.
4. **`\CpuDiffAbsMax` (5.1 pp) attached to “while the service copes”.** The resource paragraph now
   names the representative load of `\ReprLoad` kops/s. That is `write_generated_macros()`'s scope
   (`cpu_rows` at `point == "repr"`). It matches `tab_significance` (−5.1 / −4.6).
5. **`\examiners{… TBD}`.** The line is Heljanko only. `\date` is frozen to 11 September 2026.
   `texaudit.py` reports no placeholders.
6. **No numeric result table.** `tab:latency` sits in the below-saturation subsection. Its p50
   cells give C++ 73.7 / 73.5 against Rust 72.4 / 72.1, which is `\PFiftyDiffAbsMax` 1.3 µs. Pooled
   p99.99 176.4 against 89.5 is `\FarTailRange` 87. Slowest Rust 92.1 against fastest C++ 142.0 is
   `\FarTailLangSep` 50.

Still closed, as of the twenty-third pass: toolchain disclosure, the §1.4 ellipsis, and the
absence of the draft's `tab:testbed` / §6.4.7 / `tab:findings` sites from this document.

### Mechanical evidence

`.readability.py`: 690 sentences, 8939 words, mean 13.0 ± 6.5, Flesch 62.4, grade 7.8. Short
sentences 67.7% (target 25–35%), which is the five-paragraph compression after a shortening pass
(23rd pass: 15.1 ± 8.3, 56.7% short, Flesch 55.0). No paragraph of three or more sentences lacks a
sentence under 15 words. `.aitells.py`: 0 semicolons, both colon checks at 0, 10 dash hits all
numeric ranges or compound proper names (Herfindahl–Hirschman, Fowler–Noll–Vo). Two counting stubs:
l. 268 “Three terms recur throughout” (a tell, not a cap) and l. 797 “Both versions follow it”
(states the fairness control). `.acronyms.py`: not written out at first use 0, five printed waivers,
36 declared (six added since yesterday: ASN.1, DPDK, GCC, KPI, kops/s, KVM).

Headline macros checked against `figures/gen_macros.tex`, `tab_latency.tex`, and siblings, not
remembered: tracking loads 448 against 392, `\SatKnee` 392 qualified as the lowest of the four,
overload `\OverloadThrRatio` 1.7 with C++ faster in 20/20 (`\OverloadThrCpp` 147 / `\OverloadThrRust`
84), `\PFiftyDiffAbsMax` 1.3 µs, RSS 1.4–2.5 against 1.5–2.4 MiB, `\BudgetCoreShareMax` 0.250%,
`\FfiOpBoundPct` 10.91, `\DeadlockTsanHits` 5 of `\DeadlockTsanRuns` 12, `\NTailSignificant` 4
(both p99 rows and both p99.9 rows). No measured value is wrong. No remaining comparative claim
attaches a correct macro to the wrong scope.

### Per-area notes

**1, carries 5.** Untouched. The gap is located rather than asserted. RQ2 still includes classes
safe Rust is expected not to prevent.

**2, carries 5.** Command of the topic is in the gap section and the introduction. 61 cited keys.
A drop for the three-section background was considered and rejected, as on 10 September.

**3, carries 5.** The method chapter still states the frozen spec, the Holm family, the floors, the
448 exclusion, the pooled far tail kept out, and why `isolcpus` is refused. The confirmation sweep
is now described as those changes together, not as a change of design rather than of machine.

**4, lifts 4.5 → 5.** Level 4 already held yesterday. Level 5's “well considered and apt” failed on
the abstract's two register hits, the CPU macro's scope, and the absence of a numeric result table.
All three are closed. Holding 4.5 on the new caption's “sits above” was considered and rejected:
`\mci` literally prints the median above the interval, which is the draft's layout sentence
compressed, not a caption refuted by its own cells. The 21st pass's 4.5 needed a wrong
configuration value. This is not that class.

**5, carries 5.** H1 is allowed to fail and then declared ill-posed. Karlback is reconciled as two
runtimes. Ethics refuses the marketing reading of RQ2.

**6, lifts 4.5 → 5.** Writing and the build already read at 5 yesterday. Level 4 consistency
(mixed-order vs interleaved, bare FFI percentage) and level 5 finishing (`TBD`) are closed. Sentence
stdev 6.5 sits below the house screen's ~8 band, and the design chapter is 89.1% short sentences.
That is the five-paragraph contract after a shortening pass. The twenty-third pass refused to cap
on 56.7% short, and this pass does not newly cap on the same contract because the number moved.
The matrix does not name that screen.

### Outstanding

1. **Optional, this PDF.** `tab:latency` caption: copy the draft's “is printed above its
   nonparametric bootstrap 95% confidence interval”. Minutes. Does not move an area.
2. **The full draft's four standing items**, last confirmed 7 September afternoon. They are not
   this PDF's caps and were not re-read today.

Nothing in `Thesis_v3.tex` was edited by this pass. The closures it confirms were already in the
15:37 source. Do not copy this 5.00 onto `Ha_Vien_Mastersthesis_2026.tex`. Do not re-open the
skeleton's abstract, `\CpuDiffAbsMax` scope, mixed-order, or `TBD` items.

## Twenty-fifth pass — 14 September 2026

Graded independently against the CSM matrix of 9 April 2024, on **`Thesis_v3.tex` / `Thesis_v3.pdf`**,
the supervisor-facing eight-chapter argument. Chapter 1 is the draft introduction. Remaining
chapters are compressed, with twelve figures and `tab:latency`. **Standard applied:** an examiner
who received this 50-page PDF, not the 115-page full draft. The full draft was not re-read. Its
standing grade remains the twenty-second pass.

**What is new.** Six commits after `9c8b02e` (the 11 September close that the twenty-fourth pass
graded) rewrote evaluation, discussion, and conclusion: 316 insertions, 320 deletions. That is
the class this repository introduces defects with. The pass spent its budget on those pages, then
re-checked the headline macros against `figures/gen_macros.tex` and `tab:latency`.

**Build verified.** `Thesis_v3.tex` 00:40:08, PDF and `build/Thesis_v3.log` 00:40:34 on 13
September, so the PDF is current. The root-level `Thesis_v3.log` is stale (11 September) and was
ignored; `.latexmkrc` writes the log to `build/`. `texaudit.py Thesis_v3.tex --macros figures/gen_macros.tex`
exits 0: no LaTeX errors, no undefined references or citations, no multiply defined labels, no
float too large, **zero Overfull of any kind** (including `while \output is active`), 0 underfull,
50 pages. Every float label referenced from the body. 111 bib entries, 61 cited in this document
(50 uncited, expected on a shared `.bib`), 74 peer-reviewed venues (67%). **No placeholders.** One
prose-number hit with a unit: l. 416, Meneely's 58.2%, a literature value.

Compiler versions checked by hand, because the heuristic needs a unit: `\MainGpp` 15.2.1,
`\GuestGpp` 15.1.1, `\BmGpp` 13.3.0. The testbed names all three. No site types 15.1.1 as the
measurement host's compiler.

Canvas: [`thesis-grade-csm-sep14.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-sep14.canvas.tsx).

| Area | 24th pass (skeleton, 11 Sep) | This pass (skeleton) | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Hold. Gap in named flaws of five vendor theses, four RQs, H1 refuted and declared ill-posed, RQ2 two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Hold. Contrary results engaged. Background is three sections by contract |
| 3. Research data and method | 5 | **5** | Hold. The refusals (no `isolcpus`, 448 described not tested, pooled p99.99 out of the family) are in the method chapter |
| 4. Presentation of results | 5 | **5** | Hold. Headline numbers still match. A 4.5 for “source file” in place of “translation unit” was considered and rejected |
| 5. Discussion and conclusions | 5 | **5** | Hold. H1–H3 still revisited. The conclusion's “how late the tail is” is register, not a missing verdict |
| 6. Academic text | 5 | **5** | Hold. Build and house screens still pass. Flesch moved 62.4 → 71.4; stdev 6.3 is the compression contract, not a new cap |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 5.00 | **5.00** | Hold. The bar did not move |

### Mechanical evidence

`.readability.py`: 709 sentences, 9063 words, mean 12.8 ± 6.3, Flesch 71.4, grade 6.5 (24th pass:
13.0 ± 6.5, Flesch 62.4, grade 7.8). Short sentences 68.4% (target 25–35%). No paragraph of three
or more sentences lacks a sentence under 15 words. `.aitells.py`: 0 semicolons, both colon checks
at 0, 10 dash hits all numeric ranges or compound proper names (Herfindahl–Hirschman,
Fowler–Noll–Vo). Two counting stubs: l. 262 “Three terms recur throughout” and l. 791 “Both
versions follow it” (the fairness control). `.acronyms.py`: not written out at first use 0, five
printed waivers, 36 declared. `.vocab.py`: 0 replaceable hard words.

Headline macros checked against `figures/gen_macros.tex`, `tab_latency.tex`, `tab_significance.tex`,
`tab_overload.tex`, `tab_contention.tex`, `tab_adoption.tex`, `gen_guest.tex`, and
`gen_baremetal.tex`, not remembered: tracking loads 448 against 392, `\SatKnee` 392 qualified as
the lowest of the four, overload `\OverloadThrRatio` 1.7 with C++ faster in 20/20
(`\OverloadThrCpp` 147 / `\OverloadThrRust` 84), `\PFiftyDiffAbsMax` 1.3 µs, RSS 1.4–2.5 against
1.5–2.4 MiB, guest allocator-over-language `\GuestRssAllocOverLang` 13, confirmation far-tail
ranges 147–228 against 88–115 µs and they do not meet, `\BudgetCoreShareMax` 0.250%,
`\FfiOpBoundPct` 10.91 of that call at every site, `\CpuDiffAbsMax` 5.1 pp scoped to `\ReprLoad`,
`\DeadlockTsanHits` 5 of `\DeadlockTsanRuns` 12, `\NTailSignificant` 4, `\BuildAllFirstPartyCpuRatio`
0.8 (29.6 / 35.9 s). No measured value is wrong. No remaining comparative claim attaches a
correct macro to the wrong load, host, or family.

### Precision losses from the wording pass, not scored

These are the residual risk of rewriting 636 lines after a 5.00. None fails a descriptor clause.
They are listed so the next pass does not rediscover them as if they were new.

1. **“Translation unit” became “one source file”** at the two RQ4 summary sites (discussion and
   conclusion). `tab:adoption` (not in this PDF) has C++ faster on a `.cpp` edit (1.2 against
   3.6 s) and Rust faster on a header edit (5.8 against 3.6 s). A hostile reading of “source
   file” covers the header row. The old noun did not. A 4.5 on area 4's aptness clause was
   considered and rejected: this is a secondary axis, both sites agree with each other, and it
   is not a wrong measured value. Restore the noun if an opponent has the table open.
2. **Arvidsson now “times this split”.** The source carries a p99 blow-up past a threshold, not
   the C++/Rust two-way ranking the preceding paragraph has just named. The next sentences still
   make the valid argument (the shape appeared with no async runtime). The 11 September source
   said “this quantity”.
3. **Moved-from “unspecified” became “unset”** in §safetyresults. The taxonomy claim (no
   sanitiser flags use-after-move) still holds.
4. **Contention microbenchmark.** “That order is not significant” is true (`p` 0.226) and omits
   the sign reversal the draft states explicitly (Rust 58.7 against C++ 55.0 kops/s, opposite
   the overload order). The cause inference still holds.
5. **Conclusion opens “how late the tail is”.** Register drop from “tail-latency predictability”.
   The macros in the following paragraphs still state the findings.

### Per-area notes

**1, carries 5.** Untouched. The gap is located rather than asserted. RQ2 still includes classes
safe Rust is expected not to prevent.

**2, carries 5.** Command of the topic is in the gap section and the introduction. 61 cited keys.
A drop for the three-section background was considered and rejected, as on 10 and 11 September.

**3, carries 5.** The method chapter still states the frozen spec, the Holm family, the floors, the
448 exclusion, the pooled far tail kept out, and why `isolcpus` is refused. Toolchain and kernel
differences stay disclosed.

**4, carries 5.** Level 5's aptness held on 11 September because `tab:latency` was present and the
macros matched. They still match. The wording pass did not introduce a wrong number or a
correct macro on the wrong load. RSS, CPU, taxonomy, and adoption still have no numeric table in
this PDF. Those remain polish, as on 11 September.

**5, carries 5.** H1 is allowed to fail and then declared ill-posed. Karlback is reconciled as two
runtimes. Ethics refuses the marketing reading of RQ2. A drop for the conclusion's opening
register was considered and rejected: the evaluations that follow are still to the point.

**6, carries 5.** Writing and the build already read at 5 on 11 September. The wording pass made
the compressed chapters simpler (Flesch 62.4 → 71.4) and left Chapter 1 in the draft's register.
That dual register is the document's contract, not a new inconsistency. Sentence stdev 6.3 sits
below the house screen's ~8 band. The twenty-third and twenty-fourth passes refused to cap on
that screen, and this pass does not newly cap because the number moved. The matrix does not name
it.

### Outstanding

1. **Optional, this PDF.** Restore “translation unit” (or “implementation file, not a header”) at
   the two RQ4 summary sites, and “unspecified” for the moved-from object. Minutes. Does not
   move an area.
2. **Optional, this PDF.** `tab:latency` caption: copy the draft's “is printed above its
   nonparametric bootstrap 95% confidence interval”. Unchanged since the twenty-fourth pass.
3. **The full draft's four standing items**, last confirmed 7 September afternoon. They are not
   this PDF's caps and were not re-read today.

This pass did not edit `Thesis_v3.tex`. Do not copy this 5.00 onto `Ha_Vien_Mastersthesis_2026.tex`.
Do not re-open the skeleton's abstract, `\CpuDiffAbsMax` scope, mixed-order, or `TBD` items. They
are still closed after the wording pass.

## Twenty-sixth pass — 16 September 2026

Graded independently against the CSM matrix of 9 April 2024, on **`Thesis_v3.tex` / `Thesis_v3.pdf`**,
the supervisor-facing eight-chapter argument. Chapter 1 is the draft introduction. Remaining
chapters are compressed, with fourteen figures and `tab:latency`. **Standard applied:** an examiner
who received this 48-page PDF, not the 115-page full draft. The full draft was not re-read. Its
standing grade remains the twenty-second pass.

**What is new.** Fifteen commits after `1c3e97b` (the 14 September morning record of the
twenty-fifth pass) added `fig:e2eclock` and `fig:loadmap`, removed the uncited
`Predictability and the two languages` background section, renamed arm to variant, clarified
the saturation knee and the workload mix, fitted the abstract form, and kept the FFI figure
with its subsection. That is the class this repository introduces defects with. The pass
formed its view from the current PDF before reading the twenty-fifth pass, then reconciled.

**Build verified.** `Thesis_v3.tex` 11:17:56, PDF and `build/Thesis_v3.log` 11:18:28 on 15
September, so the PDF is current. The root-level `Thesis_v3.log` is stale (14 September 15:59)
and was ignored; `.latexmkrc` writes the log to `build/`. `texaudit.py Thesis_v3.tex --macros figures/gen_macros.tex`
exits 0: no LaTeX errors, no undefined references or citations, no multiply defined labels, no
float too large, **zero Overfull of any kind** (including `while \output is active`), 48 pages.
Every float label referenced from the body. 111 bib entries, 61 cited in this document
(50 uncited, expected on a shared `.bib`), 74 peer-reviewed venues (67%). **No placeholders.** One
prose-number hit with a unit: l. 426, Meneely's 58.2%, a literature value.

Compiler versions checked by hand, because the heuristic needs a unit: `\MainGpp` 15.2.1,
`\GuestGpp` 15.1.1, `\BmGpp` 13.3.0. The testbed names all three. No site types 15.1.1 as the
measurement host's compiler.

Page 3 of the PDF was rendered and read: the abstract form fits, CCS paths and the keyword
heading are both visible, and `(3)` still writes `10.91% of that call`. Body page 23 carries
the FFI subsection with its figure. `diagrams/check_labels.py` is clean on the 21 included
drawings.

Canvas: [`thesis-grade-csm-sep16.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-sep16.canvas.tsx).

| Area | 25th pass (skeleton, 14 Sep) | This pass (skeleton) | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Hold. Gap in named flaws of five vendor theses, four RQs, H1 refuted and declared ill-posed, RQ2 two-sided |
| 2. Scholarly framework and sources | 5 | **5** | Hold. Contrary results engaged. A drop for chapter 2 now having two sections was considered and rejected: the deleted section carried no citations |
| 3. Research data and method | 5 | **5** | Hold. The refusals (no `isolcpus`, 448 described not tested, pooled p99.99 out of the family) are in the method chapter |
| 4. Presentation of results | 5 | **5** | Hold. Headline numbers and both new diagrams still match. A 4.5 for “look the same in delay” was considered and rejected |
| 5. Discussion and conclusions | 5 | **5** | Hold. H1–H3 still revisited. Scored from the discussion chapter, so the resource-section opener is not counted twice |
| 6. Academic text | 5 | **5** | Hold. Build and house screens still pass. Abstract form fits. Dual register and stdev 6.4 remain the compression contract |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 5.00 | **5.00** | Hold. The bar did not move |

**Agreement with the twenty-fifth pass.** All six assessable areas agree. The twenty-fifth pass
graded a 50-page PDF of 13 September. This pass grades a 48-page PDF of 15 September with two
added figures and one fewer background section. The descriptor clauses that held 5 still hold.
The five precision losses it listed are still present and still not caps. Three new ones join
them, all from the 14–15 September edits.

### Mechanical evidence

`.readability.py`: 675 sentences, 8859 words, mean 13.1 ± 6.4, Flesch 71.2, grade 6.6 (25th pass:
12.8 ± 6.3, Flesch 71.4, grade 6.5). Short sentences 66.2% (target 25–35%). No paragraph of three
or more sentences lacks a sentence under 15 words. `.aitells.py`: 0 semicolons, both colon checks
at 0, 10 dash hits all numeric ranges or compound proper names (Herfindahl–Hirschman,
Fowler–Noll–Vo). Two counting stubs: l. 269 “Three terms recur throughout” and l. 780 “Both
versions follow it” (the fairness control). `.acronyms.py`: not written out at first use 0, five
printed waivers, 36 declared. `.vocab.py`: 0 replaceable hard words.

Headline macros checked against `figures/gen_macros.tex`, `tab_latency.tex`, `gen_guest.tex`,
`gen_baremetal.tex`, `gen_adoption.tex`, `gen_artefacts.tex`, and the SVG text of
`diagrams/30_load_regimes.svg` and `diagrams/31_e2e_clock.svg`, not remembered: tracking loads
448 against 392, `\SatKnee` 392 qualified as the lowest of the four, overload `\OverloadThrRatio`
1.7 with C++ faster in 20/20 (`\OverloadThrCpp` 147 / `\OverloadThrRust` 84), `\PFiftyDiffAbsMax`
1.3 µs (max of the paired differences; the jemalloc column medians differ by 1.4, which is a
different statistic), RSS 1.4–2.5 against 1.5–2.4 MiB, guest allocator-over-language
`\GuestRssAllocOverLang` 13, confirmation far-tail ranges 147–228 against 88–115 µs and they do
not meet, `\BudgetCoreShareMax` 0.250%, `\FfiOpBoundPct` 10.91 of that call at every site,
`\CpuDiffAbsMax` 5.1 pp scoped to `\ReprLoad`, `\DeadlockTsanHits` 5 of `\DeadlockTsanRuns` 12,
`\NTailSignificant` 4, `\BuildAllFirstPartyCpuRatio` 0.8. Load-regime ticks 56, 392, 448, 784 and
bars 448/162 and 147/84 match the macros. No measured value is wrong. No remaining comparative
claim attaches a correct macro to the wrong load, host, or family.

### Precision losses, not scored

The first three are new since 14 September. The rest are carried from the twenty-fifth pass.

1. **Meneely “vulnerabilities” became “product bugs”** in §1.4 (`f8d3951`). The source estimates
   58.2% of historical vulnerabilities, and the classified denominator is 2,257 CWE-tagged
   vulns. `docs/Sources_evidence.md` already tells the thesis to write “classified
   vulnerabilities”. The number and the citation still match. Restore the noun.
2. **“The four variants look the same in delay”** opens §5.3.3 (`da95c18`). At `\ReprLoad` the
   paired median gap is 1.3 µs and `tab:latency`'s p99.99 still splits 50 µs. A 4.5 on area 4's
   aptness clause was considered and rejected: it is a contrastive opener for RSS/CPU, not a
   tabulated claim, and the previous subsection already reports the far-tail split. Restore a
   scoped opener if an opponent has the table open.
3. **`fig:e2eclock` is not at true proportion.** The labels read 0.250% / 99.750% correctly. The
   6 px language bar is about 0.9% of the drawn bar. `fig:loadmap`'s caption says “not to scale”;
   this one does not, and it sits on the same folio as `fig:budget` (a), which is at true
   proportion. The exaggeration weakens the author's point rather than reversing it. Add the
   four words.
4. **“Translation unit” became “one source file”** at the two RQ4 summary sites. Unchanged
   since the twenty-fifth pass.
5. **Arvidsson “times this split”.** Unchanged since the twenty-fifth pass.
6. **Moved-from “unspecified” became “unset”.** Unchanged since the twenty-fifth pass.
7. **Contention microbenchmark omits the sign reversal.** Unchanged since the twenty-fifth pass.
8. **Conclusion opens “how late the tail is”.** Unchanged since the twenty-fifth pass.

### Per-area notes

**1, carries 5.** Untouched. The gap is located rather than asserted. RQ2 still includes classes
safe Rust is expected not to prevent.

**2, carries 5.** Command of the topic is in the gap section and the introduction. 61 cited keys.
The deleted background section stated open-loop sending, the Send/Sync limit, and the C ABI
with no citations. Those points still sit next to Schroeder, Zhang, and the RQ4 discussion.
`source_audit_v3` still lists the six detached-citation defects as closed.

**3, carries 5.** The method chapter still states the frozen spec, the Holm family, the floors, the
448 exclusion, the pooled far tail kept out, and why `isolcpus` is refused. Toolchain and kernel
differences stay disclosed. The knee sentence now names `\SatKnee` as the lowest of the four
and the per-language tracking loads as the knees. That is the clarification, not a new claim.

**4, carries 5.** Level 5's aptness held on 11 September because `tab:latency` was present and the
macros matched. They still match, and the two new diagrams match as well. The wording “look
the same in delay” is listed above and was not scored.

**5, carries 5.** H1 is allowed to fail and then declared ill-posed. Karlback is reconciled as two
runtimes. Ethics refuses the marketing reading of RQ2. The resource-section opener lives in
the results chapter, so it is not an area-5 finding counted twice.

**6, carries 5.** Writing and the build already read at 5 on 11 September. This pass confirmed the
abstract form fits and that last-in-chapter floats stay with the citing text. The class prints
the build day (15 September) on the title page rather than the unused `\date{11 September 2026}`
in the source. Title and abstract form agree with each other, so it is not a three-dates
defect. Sentence stdev 6.4 sits below the house screen's ~8 band. The matrix does not name it.

### Outstanding

1. **Optional, this PDF.** Restore “classified vulnerabilities” in the Meneely paragraph, scope
   the resource opener, and add “not to scale” to `fig:e2eclock`. Minutes. Does not move an area.
2. **Optional, this PDF.** Restore “translation unit” (or “implementation file, not a header”) at
   the two RQ4 summary sites, and “unspecified” for the moved-from object. Carried from the
   twenty-fifth pass.
3. **Optional, this PDF.** `tab:latency` caption: copy the draft's “is printed above its
   nonparametric bootstrap 95% confidence interval”. Generate `fig:loadmap` tick and bar labels
   from the macros so a campaign move cannot stale the SVG.
4. **The full draft's four standing items**, last confirmed 7 September afternoon. They are not
   this PDF's caps and were not re-read today.

This pass did not edit `Thesis_v3.tex`. Do not copy this 5.00 onto `Ha_Vien_Mastersthesis_2026.tex`.
Do not re-open the skeleton's abstract, `\CpuDiffAbsMax` scope, mixed-order, or `TBD` items. They
are still closed after the 14–15 September edits.

## Twenty-seventh pass — 21 September 2026

Graded independently against the CSM matrix of 9 April 2024, on
**`Thesis_v3.tex` / `Thesis_v3.pdf`**, after the coordinated-omission recorder
diagnostics were added. Standard applied: a supervisor receiving the current
50-page PDF. The plan was checked and rebuilt. The full draft was checked for
claim sync and build gates, but was not graded as a second manuscript.

**What is new.** The overload section now compares the campaign clock with a
deferred-fill clock, `fig:overload` shows both at 448 and 784 kops/s, and the
discussion and conclusion attribute both campaign gaps to histogram-recorder
work. This pass formed its view from the source, generated macros, raw
environment captures, and the diagnostic analysis code before reconciling with
the twenty-sixth pass.

**Build verified.** A forced `latexmk` rebuild produced 50 pages.
`texaudit.py Thesis_v3.tex --macros figures/gen_macros.tex` exits 0: no LaTeX
errors, undefined references or citations, multiply defined labels, floats too
large, or overfull boxes. Every float is referenced. The bibliography has 113
entries, 63 cited in this document, and 75 peer-reviewed venues. The only
prose-number hit is Meneely's cited 58.2% literature value. The abstract page
was rendered and fits its form. `diagrams/check_labels.py` passes all 21
reader-visible diagrams. The plan also rebuilds cleanly at seven pages.

Canvas: [`thesis-grade-csm-sep21.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-sep21.canvas.tsx).

| Area | 26th pass (16 Sep) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Hold. Four traceable RQs, three prior hypotheses, and the two-sided 7 + 7 RQ2 catalogue remain intact |
| 2. Scholarly framework and sources | 5 | **5** | Hold. Contrary findings and primary method sources remain engaged |
| 3. Research data and method | 5 | **4.5** | Split. The main campaign remains at 5. The new diagnostic analysis uses 16 of 20 pairs and a different statistic, and the stored captures do not isolate fill timing as the only changed variable |
| 4. Presentation of results | 5 | **4** | Several surfaces disagree: stale abstract, undisclosed mixed-host figure, omitted jemalloc result, representative-load values generalized to a regime, and one canonical RSS range assigned to all hosts |
| 5. Discussion and conclusions | 5 | **4** | The discussion overstates the causal control, promotes a biased no-fill p99, gives H1 a partial acceptance the tests do not support, and does not state that overload service latency remains unresolved |
| 6. Academic text | 5 | **4** | Level 4's whole-text consistency clause fails across the abstract, motivation, method, implementation, results summaries, hypothesis revisit, and conclusion |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 5.00 | **4.42** | The method half remains strong, but the new finding has not been integrated consistently enough for areas 4 to 6 to hold 4.5 |

### Findings that move the grade

1. **The abstract did not move with the result.** `Thesis_v3.tex` lines
   125--130 still report Rust tracking to 448 kops/s, C++ to 392, then a
   1.7-times C++ lead after both fall behind. The body now says both are
   campaign-recorder effects. The full draft's abstract carries the same stale
   account. Because `ai_statement.tex` says the abstract was written unaided,
   this pass does not supply replacement prose. The author has to rewrite both
   abstracts.

2. **The diagnostic p-values do not use the thesis's declared test.**
   `bench/probe_facts.py` truncates each allocator comparison to the first 16
   pairs, despite 20 repeats, and applies a median-difference sign test. The
   canonical analysis uses all 20 pairs and the mean paired difference as its
   permutation statistic. Recomputing the same diagnostic data with that test
   gives system-allocator \(p=0.0750\), not `\ProbeAfterThrPSystem` 0.070, and
   jemalloc \(p=0.0000038\). The generated diagnostic macro reports 0.004 from
   the truncated alternate test. The prose reports only the system allocator.
   The large 1.7-times collapse still disappears, but a smaller Rust lead under
   jemalloc resolves and must be stated.

3. **The fill is not isolated as the only changed variable.** The canonical
   capture `env-20260827-151643.txt` records an AMD EPYC 7443, root UUID
   `a9c...`, and `nohz_full=2-17`. The diagnostic capture
   `env-20260920-213438.txt` records an AMD EPYC 7443P, root UUID `d381...`,
   and no `nohz_full`. No ordinary intended-origin, in-run-fill baseline was
   run on the diagnostic setup. The two diagnostic clocks strengthen the
   recorder explanation, but they do not justify “only the timing of the work
   moves” or “the fill is the cause”. A same-setup baseline would establish
   that. Without one, the result has to be written as evidence consistent with
   recorder work and the host/configuration confound has to be named.

4. **One old mechanism survives in the implementation chapter.**
   `Thesis_v3.tex` lines 891--897 say the bounded queue and reply handle carry
   the overload result. The results chapter now says the isolated primitives do
   not reproduce it and replacing Rust's reply handle does not move the floor.
   Those forced idioms are candidates that were ruled out alone, not carriers
   of the result.

5. **RQ1's overload-latency clause is not answered at the supported
   strength.** RQ1 asks for median through maximum under overload. Campaign
   percentiles include recorder work and deferred-fill percentiles are schedule
   drift, so neither supports a service-latency comparison after saturation.
   The discussion answers the capacity-ranking question instead of stating this
   negative result. Clock A's no-fill p99 is then repeated at three sites
   without its defining limitation: it reintroduces coordinated-omission bias.

6. **Several old scopes became visible when the result was read end to end.**
   `\PFiftyRange`, `\PFiftySpread`, `\PNineNineRange`,
   `\PNineNineMaxCI`, and `\PFiftyDiffAbsMax` are computed at
   `\ReprLoad`, but four sites introduce them as the whole below-saturation
   regime. The summary assigns the canonical 1.4--2.5 MiB RSS range to all
   three hosts, whose generated ranges are 1.8--3.5 and 0.7--1.8 MiB on the
   other two. The direction travels. The exact range does not.

7. **The method summary and figures contain two further contradictions.**
   The statistics paragraph says only jitter and pooled p99.99 stay out of the
   family, while maximum, representative-load throughput, and all overload
   percentiles are also excluded for distinct reasons. The latency-table caption
   says maximum is excluded for the same reason as pooled p99.99 even though
   maximum has repeat-wise intervals. `fig:loadsweep` still titles one panel
   “the saturation knee” although the generated evidence says the knee is not
   shared.

8. **The integration missed the front and back of the argument.** The
   motivation still advertises the widest post-saturation language gap. The
   method table calls the contaminated high-load clock the round-trip a
   deployment experiences. H1 is partially accepted despite no equivalence
   margin and resolved median, p99, and p99.9 differences. The engineering
   guideline says only to sweep past the service knee, omitting the new lesson
   that producer-side recorder work must be kept outside that timed path.

9. **Three source and register fixes are required.** The coordinated-omission
   correction sentence cites Schroeder's open/closed-system paper but omits the
   HDR correction source (`tene_hdrhistogram`). The Arvidsson sentence says it
   times “this split”, where it reports similar degradation past a threshold,
   not recorder against service. H3's call-cost bound is measured, while the
   learning-cost clause is a literature-backed implication and not a measured
   result.

### Per-area reconciliation

**1, holds 5.** No RQ, hypothesis, catalogue boundary, or objective changed.
The overload finding changes the answer to RQ1, not whether the question is
significant and testable.

**2, holds 5.** The new section's only literature comparison is Arvidsson's
threshold degradation, and the text correctly says that its asynchronous
runtime explanation cannot carry into a thread-per-shard design. The earlier
precision note that “times this split” is broader than the source remains
optional wording work.

**3, moves 5 to 4.5.** The frozen main campaign, exact paired family, Holm
correction, pooled far tail, parity controls, and refusal of `isolcpus` still
read at 5. The diagnostic branch does not: it silently drops four pairs, changes
the statistic, and compares against a campaign with a different captured
configuration while calling timing the only change. This is a split between the
main method and the new causal diagnostic.

**4, moves 5 to 4.** `fig:overload` is clear and its bar values match the
logs. Level 4 holds because the generated layer is correct, every figure is
referenced, and the questions still have identifiable findings. The next half
step does not: the abstract is one evidence state behind, the body omits the
significant jemalloc contrast, the figure mixes captures without saying so,
several representative-load values are generalized, and the RSS summary assigns
one host's exact range to all three.

**5, moves 5 to 4.** The discussion still shows substantial independent input,
revisits H1 to H3, and preserves RQ2's boundary. It does not yet deeply
internalise the new finding: it promotes a cross-setup diagnostic into a
one-variable cause, repeats a deliberately biased p99 as a finding, and partly
accepts H1 without an equivalence margin. RQ1's honest overload answer is that
service latency cannot be compared with either current percentile clock.

**6, moves 5 to 4.** The build is camera-ready and the prose gates pass:
Flesch 70.6, no semicolons, no acronym first-use failures, and no paragraph of
three or more sentences without a short sentence. Level 4 nevertheless asks for
the whole text to be consistent on setup, findings and conclusions. The
abstract, motivation, method table, forced-idiom paragraph, no-fill summaries,
H1 revisit and conclusion do not yet describe one evidence state. The abstract
must remain the author's own work.

### Ranked work before sending

1. **Author edit, minutes:** rewrite both abstracts to remove the two
   campaign-clock gaps as service rankings and state the diagnostic evidence at
   the strength the controls permit. Areas 4 and 6.
2. **Analysis edit, under an hour:** make `probe_facts.py` use the canonical
   20-pair test, regenerate `gen_probes.tex`, and report both allocators. Areas 3
   and 4.
3. **Either new measurement or weaker prose:** run an in-run-fill baseline on
   the diagnostic setup, or rerun deferred fill on the canonical setup. If
   neither is possible, replace causal wording throughout with a qualified
   cross-setup finding and name the configuration difference. Areas 3 and 5.
4. **Argument edit, hours:** state RQ1's overload-latency answer as unresolved,
   remove the biased no-fill p99 from the findings summaries, give H1 and H3
   verdicts at their supported strength, and answer RQ3 axis by axis without
   assigning whole-implementation effects to the safety model. Areas 4 and 5.
5. **Integration edit, hours:** sync the motivation, method table, forced-idiom
   paragraph, saturation language, guidelines, threats, and conclusion. Add
   Tene to the correction sentence and narrow the Arvidsson clause. Areas 4 to
   6.
6. **Scope edit, under an hour:** attach representative-load macros to
   `\ReprLoad`, report host-specific RSS ranges, describe every statistical
   exclusion for its own reason, and rename the singular knee title. Areas 3,
   4, and 6.
7. **Rebuild and independent read:** rerun all four prose screens, the CSM
   audit, render the abstract and overload pages, and re-read the abstract,
   results, findings summary, hypothesis revisit, threats, and conclusion
   against each other.

This pass changed no thesis prose. It rebuilt `Thesis_v3.pdf` and
`Thesis_Plan_v2.pdf`, created the grading canvas, and appended this record.

## Twenty-eighth pass — 29 September 2026

Graded independently against the CSM matrix of 9 April 2024, on
**`Thesis_v5.tex` / `Thesis_v5.pdf`**, after the coordinated-omission account
had been rewritten. Standard applied: a supervisor reading the current 60-page
PDF, not a submitted maturity test. The full draft was not re-read. This pass
formed its view from the source, the generated macros, the latency table, and
the 24 September environment captures before reconciling with the
twenty-seventh pass.

**Build verified.** A forced `latexmk -g` rebuild produced 60 physical pages.
The abstract form reports 44 pages plus 8 appendix pages, which matches the
front matter, the numbered body, and appendices A and B. `texaudit.py` fails
one hard gate: `tab:testbed` is 111.47 pt too large for its page, and
`tab:params` is 5.40 pt too large. No LaTeX errors, undefined references,
undefined citations, or overfull boxes. Two float labels are never referenced:
`tab:jitter` and `tab:resident`. The bibliography has 113 entries and 63 cites
in this file. The only prose-number hit is Meneely's cited 58.2%, a literature
value. `zhang2026deadlock` is the journal article. `bugden2022rust` is not
cited here. Prose screens: Flesch 66.9, grade 7.4, no paragraph of three or
more sentences without a sentence under 15 words, acronym gate clean, no
semicolons. The dash hits are numeric ranges and Herfindahl--Hirschman.

The class prints `\today` on the abstract form, so this rebuild stamped
29 September 2026. The source `\date` is still 11 September 2026.

Canvas: [`thesis-grade-csm-sep29.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-sep29.canvas.tsx).

| Area | 27th pass (21 Sep) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Hold. Named gap, four traceable questions, three prior hypotheses, 7 + 7 catalogue |
| 2. Scholarly framework and sources | 5 | **5** | Hold. Contrary findings engaged, primary standards and method sources used |
| 3. Research data and method | 4.5 | **5** | The diagnostic half now matches the main method: 20 pairs, the canonical permutation, and a same-host fill control |
| 4. Presentation of results | 4 | **5** | Headline claims match the generated tables, and each clock states what it cannot rank |
| 5. Discussion and conclusions | 4 | **5** | H1 is not accepted as written, overload service latency is left unresolved, and the discussion matches the results |
| 6. Academic text | 4 | **4.5** | Consistency holds at level 4. Level 5's camera-ready clause fails on the host table and two grammar errors |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.42 | **4.92** | Five areas at 5. Finishing is the only assessable cap |

### What closed the twenty-seventh pass

Checked against the current source and the 24 September captures, not against
the old note.

1. The abstract qualifies the 1.7× lead as the in-window fill, says the
   same-host deferred fill removes that gap and leaves a smaller Rust lead,
   and says overload service latency stays unresolved.
2. `probe_facts.py` calls `paired_permutation_test` on the full pair list.
   `\ProbeAfterPairsSystem` and `\ProbeAfterPairsJemalloc` are 20.
   `EXACT_MAX` is 20, so the test is exact. Both allocator results are in the
   prose, at `p < 0.001`.
3. `env-20260924-083349.txt` and `env-20260924-100058.txt` share the CPU, pin,
   kernel, `nohz_full`, governor, toolchain, and hugepage policy. They differ
   by container id and the instantaneous MHz reading. "Only the fill moves"
   is earned for Clock B. Clock A is described as an earlier host and is not
   used as a tail result.
4. The forced-idiom paragraph calls the queue and the reply handle candidates
   that do not explain the smaller lead that remains.
5. Motivation, method table, guidelines, H1, and the conclusion state the same
   limit: the large high-load gaps move with the fill, and neither overload
   clock ranks service latency.
6. Representative-load latency figures are attached to `\ReprLoad` in the
   results and the discussion. The three hosts have three RSS ranges. The
   statistics section gives the maximum, the pooled far tail, jitter, and
   post-saturation percentiles separate reasons for staying out of the family.
   `fig:loadsweep` panel (a) is titled "Below the knee", not a shared knee.

### Claims checked, and none disagreed

Read from the generated macros and `figures/tab_latency.tex`.

- Median span `\PFiftyRange` 1.6 µs, table 73.9 to 72.3. Paired gap
  `\PFiftyDiffAbsMax` 1.5 µs.
- p99 band `\PNineNineMaxCI` 0.8 µs against gap `\PNineNineRange` 1.8 µs.
  Guest `\GuestPNineNineMaxCI` 1480 against `\GuestPNineNineRange` 293, the
  other way.
- Far-tail separation `\FarTailLangSep` 22 µs (110.0 minus 87.9). Second host
  Rust `\BmFarTailRustLo`--`\BmFarTailRustHi` 88–115 against C++ 147–228.
- Campaign overload `\OverloadThrCpp` 140 against `\OverloadThrRust` 84,
  ratio 1.7, C++ faster, Rust the higher CPU per call.
- Deferred fill: system 412/434 = 0.95, jemalloc 413/450 = 0.92, both
  `p < 0.001`, CPU ratio 1.03 with C++ higher.
- Peak RSS on this host: language 1.6–2.5 MiB, allocator 1.5–2.3 MiB. Guest
  allocator effect `\GuestRssAllocOverLang` 13 times the language effect.
  The prose says same order on both bare-metal hosts and does not say the
  allocator effect is the larger one.
- Toolchain row prints `\MainGpp` 15.2.1, `\GuestGpp` 15.1.1, `\BmGpp` 13.3.0,
  and the caption names the release gap.

### Per-area notes

**1, holds 5.** The gap is located in named limits of the five Ericsson theses
and of Emberg and Wadsten's stateless pair. RQ1's overload half is answered
by saying the available clocks cannot rank service latency.

**2, holds 5.** Critical use of contrary results is intact, including the
reading of Karlbäck's memory sign as two concurrency runtimes. The search for
the vendor theses is described as a hand search of university archives.

**3, moves 4.5 to 5.** The main campaign was already at 5. The half grade was
the diagnostic. That half now uses the declared test on all 20 pairs, and the
fill control is the same machine and the same `nohz_full`. Ethics remain in
the discussion.

**4, moves 4 to 5.** Level 5's aptness clause holds: the figures and tables
that carry the findings agree with the prose, and the findings are specific
enough to use. Two unreferenced appendix tables and one signed-delta sentence
were not used to move the grade, because neither reverses a result and the
captions say what the tables are for.

**5, moves 4 to 5.** H1 is not accepted as written, because no equivalence
margin was defined and the paired test resolves a median gap. H2 is limited
to memory safety and data races. H3's call-cost bound is measured, and the
learning cost is marked as structural. The one-variable fill claim is now
backed by the captures.

**6, moves 4 to 4.5.** Level 4's consistency clause holds. The abstract,
motivation, method, results, hypothesis revisit, and conclusion describe one
evidence state. Level 5 fails on finishing polish. The host table's last row,
"Adequate for", sits in the bottom margin of appendix page ii. The problem
statement hyphenates "unknow" and uses "classes that affects". The half grade
is consistency at 5 and finishing at 4.

The AI statement truthfully says the abstract has not been rewritten unaided.
That blocks this PDF as the maturity test. It is not a false declaration, and
under the supervisor-reading standard it does not set the grade.

### What is outstanding

1. **Editing, minutes.** "unknow" and "that affects" in the problem statement.
   Area 6.
2. **Editing, about an hour.** Make `tab:testbed` and `tab:params` fit the
   text block. Area 6. This is the item that blocks a 5.
3. **Editing, minutes, does not move the current grade.** Cite `tab:resident`
   from the resources section. Cite `tab:jitter` or delete the sentence that
   says the main text cites the tables that follow.
4. **Polish.** The resident-set sentence prints a signed delta and a direction
   word together ("−0.16 MiB less"). Both point the same way.
5. **Author, unaided.** Rewrite the abstract and set
   `\abstractunaidedtrue` in the shared statement. A model must not draft that
   page. This is a submission rule, not the cap on this pass.

This pass changed no thesis prose. It rebuilt `Thesis_v5.pdf`, which moved the
abstract-form date to 29 September 2026, created the grading canvas, and
appended this record.

---

## Twenty-ninth pass — 8 October 2026

Graded independently against the CSM matrix of 9 April 2024, on
**`Thesis_v5.tex` / `Thesis_v5.pdf`**, after grammar, scope, and layout fixes
applied earlier on 8 October 2026. Standard applied: a supervisor reading the
current 71-page PDF, not a submitted maturity test. The full draft was not
re-read.

**Build verified.** `latexmk -pdf Thesis_v5.tex` produced 71 physical pages.
`texaudit.py` passes every hard gate: no LaTeX errors, undefined references or
citations, floats too large, or overfull boxes. `tab:jitter` is still never
referenced from the body. Prose screens: Flesch 59.1, acronym gate clean, no
semicolons. The AI statement truthfully says the abstract has not been
rewritten unaided.

Canvas: [`thesis-grade-csm-oct08.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-oct08.canvas.tsx).

| Area | 28th pass (29 Sep) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Hold. Named gap, four traceable questions, three prior hypotheses |
| 2. Scholarly framework and sources | 5 | **5** | Hold. Contrary findings engaged, primary standards and method sources |
| 3. Research data and method | 5 | **5** | Hold. Canonical bare-metal campaign, exact permutation, same-host fill control |
| 4. Presentation of results | 5 | **4.5** | Level 5 aptness fails: abstract reports pipeline and overload leads without host or clock scope |
| 5. Discussion and conclusions | 5 | **5** | Hold. H1 not accepted, throughput kept separate from campaign delay |
| 6. Academic text | 4.5 | **4.5** | Finishing improved to level 5; abstract consistency still blocks level 5 |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.92 | **4.83** | Four areas at 5, two at 4.5 |

### What closed since the twenty-eighth pass

1. `tab:testbed` and `tab:params` fit their pages after `\scriptsize` and caption tightening.
2. Problem-statement grammar: "unknown" and "classes that affect" are correct.
3. Tracking limits name the shared floor and the Rust jemalloc extension.
4. Fairness interleaving paragraph is no longer self-contradictory.
5. Discussion separates completed throughput from campaign-clock delay.
6. Signed resident-set deltas no longer print a direction word beside the sign.
7. Hardware-counter prose uses `\BmInstrDelta`, `\BmCycleDelta`, and `\BmMissDelta`.

### What caps the grade now

1. **Abstract scope (areas 4 and 6).** The body scopes the pipeline experiment to a
   separate host (`\PipeCpu{}`) and outside the tested family. The abstract reports the
   allocator-dependent wait without that qualification. The body quotes deferred-fill
   throughput (`\ProbeAfterThr*`) when it says Rust completes more calls past saturation.
   The abstract uses `\OverloadLoad` without naming that clock. Campaign in-window macros
   (`\OverloadThrCpp` 140, `\OverloadThrRust` 84) are not quoted in this file and would
   read the other way.
2. **Abstract wording (area 4).** "Of the time taken by a request" should name the measured
   end-to-end round trip. The FFI bound should read "of one signalling request's measured
   cost", as the conclusion already does.
3. **Maturity test (submission, not this grade).** `ai_statement.tex` keeps
   `\abstractunaidedfalse`. The author must rewrite the abstract without a model before
   submission.
4. **`tab:jitter` (minor).** Still unreferenced. Does not move the grade on its own.

### Reconciliation with the twenty-eighth pass

I agree on areas 1, 2, 3, 5, and on area 6 at 4.5. I disagree on area 4: the
twenty-eighth pass held it at 5 because the abstract then qualified the fill and left
overload service latency unresolved. The current abstract was simplified and no longer
carries those qualifications, so area 4 drops to 4.5. Area 6 finishing improved because
the table overflow and grammar errors are closed, but the abstract cap remains.

### What is outstanding

1. **Editing, minutes.** Fix the abstract scope and wording. Areas 4 and 6.
2. **Author, unaided.** Rewrite the abstract and set `\abstractunaidedtrue`. Submission rule.
3. **Editing, minutes, does not move the current grade.** Cite `tab:jitter` or leave the
   appendix sentence as supporting measurements only.

## Thirtieth pass — 14 October 2026

Graded against the CSM matrix of 9 April 2024 on **`Thesis_v5.tex` /
`Thesis_v5.pdf`** after rebuilding the current source. Standard applied: the
current manuscript as a submission candidate. This pass grades the document,
not evidence that exists only in the repository.

**Build verified.** `latexmk -pdf -interaction=nonstopmode -halt-on-error
Thesis_v5.tex` produced 73 physical pages. There are no LaTeX errors,
undefined citations, oversized floats, or placeholders. Two references to
`sec:rustsafety` are undefined because the source label is
`*sec:rustsafety*`. Four `Crash/corruption` cells in `tab:defectmap` overrun
their columns by 12.5 pt. The acronym gate reports ABI at first use. The
shared AI statement still sets `\abstractunaidedfalse` and prints that the
document is not submittable.

Canvas: [`thesis-grade-csm-oct14.canvas.tsx`](/home/vienha/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grade-csm-oct14.canvas.tsx).

| Area | 29th pass (8 Oct) | This pass | Clause that sets it |
| --- | --- | --- | --- |
| 1. Objective and research questions | 5 | **5** | Hold. Named gap, four traceable questions, falsifiable seven-plus-seven RQ2 catalogue |
| 2. Scholarly framework and sources | 5 | **5** | Hold. Contrary findings engaged, primary standards and method sources |
| 3. Research data and method | 5 | **5** | Hold. Frozen specification, parity oracle, bare-metal campaign, exact paired tests and Holm correction |
| 4. Presentation of results | 4.5 | **5** | The abstract now carries the host and clock qualifications that the previous pass found missing |
| 5. Discussion and conclusions | 5 | **4.5** | The resident-set explanation in the discussion contradicts the results section |
| 6. Academic text | 4.5 | **4.5** | Scientific presentation reads at level 5; camera-ready finishing does not |
| 7. Work during the thesis process | n/a | **n/a** | Not assessable from a manuscript |
| **Mean of the six assessable** | 4.83 | **4.83** | Area 7 excluded |

### 1. Thesis objective and research questions — 5

**Carries it.** The research gap is located in named weaknesses of the closest
telecom studies. The four questions trace to methods, artefacts, and metrics.
RQ2 can disconfirm its own premise through seven defect classes inside safe
Rust's guarantee and seven outside it. Three hypotheses were fixed before
measurement, and H1 is later rejected as written.

**Caps it.** Nothing in the level-5 descriptor fails. The topic and design are
strong enough to support a scientific publication.

### 2. Scholarly framework and use of sources — 5

**Carries it.** Primary 3GPP standards ground the network domain. The review
engages contrary findings on tail latency, throughput, and memory instead of
listing only work favourable to Rust. Primary method sources support the
statistical treatment and fault injection. Every citation used in this
manuscript resolves.

**Caps it.** Nothing in the level-5 descriptor fails. The 50 unused entries
belong to the shared bibliography and do not appear as references in this
manuscript.

### 3. Research data and method — 5

**Carries it.** The method combines a frozen specification, an independent
parity oracle, interleaved variants, a 1,120-run bare-metal campaign, exact
paired permutation tests over 20 repeats, Holm correction, and a pooled far
tail kept outside the paired family. Descriptive follow-up experiments are
identified as such, and the text states what each clock cannot establish.

**Caps it.** Nothing in the level-5 descriptor fails. The methods and data
selection are analysed in depth rather than merely listed.

### 4. Presentation of thesis results — 5

**Carries it.** The abstract now names the same-host deferred-fill clock,
states that its overload delay is schedule drift, and scopes the
allocator-dependent pipeline result to a further host outside the tested
family. This closes the twenty-ninth pass's cap. Generated macros and tables
carry the measured quantities, and the main text separates campaign delay,
completed throughput, isolated core time, and several-requests-in-flight
delay.

**Caps it.** No level-5 clause fails. `tab:jitter` remains unreferenced from
the body, but its caption marks it as supporting evidence rather than an
answer to a research question. That isolated defect does not move the area.

### 5. Discussion and conclusions — 4.5

**Carries it.** The discussion revisits all three hypotheses. H1 is not
accepted without an equivalence margin, H2 is narrowed to safe Rust and the
tested classes, and H3 rests on an upper bound rather than a non-significant
test. The chapter keeps completed throughput separate from overload delay,
engages contrary prior work, names residual risks, and includes an ethical
reflection.

**Caps it.** Level 5 asks for clear and reliable conclusions and evaluations.
Lines 2008–2009 say that the quieter-host memory cost is largely explained by
the allocator itself. Lines 1681–1691 report the opposite result: allocator-
resident memory is lower in Rust while process peak RSS is higher, so the
difference sits outside the allocator as a fixed process-level cost. The
reasoning otherwise reads at level 5, while this reliability inconsistency
reads at level 4. The split sets 4.5.

### 6. The thesis as an academic text — 4.5

**Carries it.** The argument is readable and well structured. Terms are
defined, citations resolve, figures and tables are integrated with the
argument, and the build has no oversized float. The prose screens report
Flesch 59.9, no semicolons, and no sentences longer than 50 words.

**Caps it.** Level 5 requires technically camera-ready presentation and
excellent finishing polish. Two printed internal references are undefined,
four cells overrun the defect table, and ABI is not written out at first body
use. The memory explanation also contradicts the results. The declaration
states that the abstract has not been rewritten unaided and marks the PDF as
not submittable. Scientific presentation reads at level 5, while finishing
reads at level 4. That named split sets 4.5.

### 7. Work during the thesis process — n/a

The manuscript cannot show how the author used feedback, worked
independently, or followed the schedule. Supervisors assess this area.

### Reconciliation with the twenty-ninth pass

I agree on areas 1, 2, and 3. Area 4 returns to 5 because the revised abstract
now supplies the separate-host and deferred-fill-clock scope that was missing
on 8 October. I disagree on area 5 because the current discussion contradicts
the resident-set decomposition beside it. Area 6 holds at 4.5: the current PDF
has undefined references, overfull result cells, a first-use acronym failure,
an internal results contradiction, and an explicit not-submittable
declaration, but the scientific presentation itself remains at level 5.

An independent source-only read placed areas 1 to 5 at 5 and area 6 at 4.5,
for a mean of 4.92. I agree with its area-6 calibration. I retain area 5 at
4.5 because its reading did not reconcile the statement that the allocator
explains the quieter-host memory cost with the results section's conclusion
that Rust's extra peak RSS sits outside allocator-resident memory.

### Work that raises the grade, cheapest first

1. **Author, unaided.** Rewrite the abstract without model assistance and set
   `\abstractunaidedtrue` only after that work is complete. This closes the
   submission gate.
2. **Editing, minutes.** Rename the malformed Rust-safety label so its two
   references resolve. Area 6.
3. **Editing, minutes.** Widen or reword the Result column in
   `tab:defectmap` so `Crash/corruption` fits. Area 6.
4. **Editing, minutes.** Replace the discussion's allocator explanation with
   the conclusion supported by the resident-set decomposition. Areas 5 and 6.
5. **Editing, minutes.** Write out application binary interface at the first
   body use before ABI. Area 6.
6. **Optional.** Cite `tab:jitter` from the body or remove it if it adds no
   claim. This protects area 4 but does not move the present grade.
