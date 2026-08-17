# Thesis assessment and refinement record

Assessment of **Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia
RAN Control-Plane Systems** against the six-criterion assessment matrix (simplified from the
data science master's thesis matrix), on the Finnish 1–5 scale.

Two states are recorded per criterion: the grade on first reading, and the grade after a
refinement pass. Source material was `Thesis_POC.pdf` and the supporting artefacts in `spec/`,
`bench/`, `faults/`, `ffi/`, and `diagrams/`.

An interactive version of this document exists as a Cursor canvas at
`~/.cursor/projects/home-vienha-thesis-local/canvases/thesis-grading.canvas.tsx`. This file is
the durable copy; keep the two in step if you revise either.

> **A second, independent review followed this one and disagreed with it.** It held criteria 3
> and 4 at 4 rather than 4.5, on the grounds that this document treats "everything analysis
> could contribute" as done when three analysis items were still available on the existing
> dataset. Those three were then carried out, along with two new measurements. The record is in
> "Second pass" at the end of this file, and in
> `~/.cursor/projects/home-vienha-thesis-local/canvases/thesis-examiner-review.canvas.tsx`.
> Where the two disagree, the second pass is current.

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
C++" but the specific observation that in both closest prior works — Karlbäck and Orö, and
Arvidsson and Kaller — the language co-varies with the runtime and concurrency model, so no
measured difference can be attributed to the language. The entire study design follows from
that critique.

RQ2 is constructed so that it can refute itself: five defect classes from inside Rust's
guarantee and two chosen from outside it. Building in cases that can disturb the expected answer
is a graduate-level instinct.

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
proper institutional attribution of the two Ericsson master's theses.

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
| `Thesis_POC.tex` | New significance and complexity tables with their discussion; corrected RQ3 finding in Chapters 7, 8, 9 and the abstract; Section 5.5 rewritten; 3.3 and 4.1 de-duplicated; contents trimmed; long sentences broken up. |
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

Re-read of `Thesis_POC.tex` / `Thesis_POC.pdf` against the same six-criterion matrix. Source:
full document (Chapters 1–9, abstract, tables, generated macros in `figures/gen_macros.tex`),
plus spot-check of `spec/`, `bench/`, `faults/`, `ffi/`. Build: `latexmk -pdf Thesis_POC.tex`
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
six-criterion simplification used above, and **from `Thesis_POC.tex` alone** — no artefact
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
  `Thesis_v1.tex`'s abstract is still a placeholder.
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
3. **Align RQ1's metric list** with what is reported, or report jitter. RQ1 names "mean, p99,
   p99.9 tail latency, and jitter"; the mean is deliberately replaced by the median and jitter is
   absent. Note that amending the RQ means syncing the plan and `Thesis_v1.tex`, and the plan is
   supervisor-approved.
4. **Optional:** the use-after-free example is worked three times (introduction, background,
   appendix). Defensible layering for a reader without telecom background — left as the author's
   call rather than cut.
5. **Housekeeping:** examiners on the title page, official class file.
