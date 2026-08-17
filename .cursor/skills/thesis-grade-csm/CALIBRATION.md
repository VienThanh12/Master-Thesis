# Calibration

Anchors from grading passes already on record, so a new pass lands on the same scale rather than
inventing one. Sources: the four passes in `ASSESSMENT.md`, the grading canvases in
`~/.cursor/projects/home-vienha-thesis-local/canvases/`, and one external manuscript graded with
the same matrix (a VLM image-tagging thesis, canvas `grade-vlm-tagging-thesis.canvas.tsx`).

Update the standing-blockers section when a pass changes it. Leave the anchors alone: their value
is that they are fixed points.

## What the levels have looked like

| Area | Grade | The observation that set it |
| --- | --- | --- |
| 1 | 5 | Gap located in a named flaw of the closest prior work rather than asserted. Four research questions traced question to method to artefact to metric to verdict. Three hypotheses fixed before measurement, one later refuted by the author's own data. |
| 1 | 3 | Level 4 asks for a research setup described in suitable detail; the setup was described inconsistently, so the level failed on that clause alone. One question asked what literature exists, which is a review task. "Significantly improve" was never given a threshold. |
| 2 | 5 | Every bibliography entry cited, concentrated in top venues, domain grounded in primary standards rather than secondary summaries, an auditable written search protocol, and contrary results (Arvidsson's tail, Emmerich's slower driver) engaged rather than omitted. |
| 2 | 3 | Recent sources and concepts defined before use, but the review summarises rather than argues, cites no contrary or negative finding, mixes citation styles, and leaves quantitative claims uncited. |
| 3 | 4.5 | Method reads at 5: frozen specification before code, forced-idiom log, allocator control as a replication check, exact paired permutation over every sign assignment, Holm family, attainable p-floors quoted, and a reading rule fixed in advance that costs the author a row rather than rescuing one. Data reads at 4: the host is a KVM guest whose CPU steal is of the same order as the tail being measured, and no hardware counters, so the peak-RSS result is established but unexplained. |
| 3 | 2 | Train and test boundary not established, every fine-tuning hyperparameter stated twice with different values, the actual contribution given no equations or thresholds, no statistical test despite repeated use of "significantly", one annotator with no agreement measure, no ethics discussion at all. |
| 4 | 4.5 | Every campaign result reaches the page through a generated macro rebuilt from raw logs, so headline numbers cannot drift from the data. Evidence status stated per research question, and the one schematic says in its own caption that it is not this study's data. Capped by a research question half-answered only in the negative, one table never referenced from the body, and about nine measured values still typed into prose by hand. |
| 4 | 2 | Roughly 28 values quoted in the results prose disagreed with the tables they described, one reversing the direction of change. A promised baseline and a promised condition were never reported. No result figures at all. |
| 5 | 5 | Hypotheses revisited individually, including one the author declares ill-posed. Four-way validity analysis with residual risk graded per row. Contradictory prior results reconciled mechanically. The study records its own methodological errors. Register held: "cannot tell" never becomes "equivalent". |
| 5 | 2 | No discussion chapter. Own results never compared with previous research, reliability never assessed, ethics absent, and a contribution claimed that the preface credits to the partner. |
| 6 | 5 → 4.5 | The third pass gave 5 for the writing. The fourth took it back, because level 5 asks for presentation that is technically camera-ready with excellent finishing polish and the *finishing* failed: the printed AI declaration asserted the abstract was written unaided while a source comment recorded it as model-drafted, alongside a float overflowing its page, two overfull boxes, and sentences of 93 and 86 words. Writing quality does not carry this area on its own. |
| 6 | 2 | Template dummies surviving on the abstract page, three different dates, duplicated and undefined labels, a stray Cyrillic word in the results, dense grammar errors, and no statement of AI use in the document. |
| 7 | n/a | Every pass. The manuscript cannot settle it. |

## Checks ranked by historical yield

1. **Every number in the results prose against its table.** Found 28 contradictions in one
   manuscript and about nine hand-typed values in the other. Nothing else has this hit rate.
2. **Every figure against the claim it illustrates.** Three figures here contradicted the results
   tables after the claims moved: a defect class marked not injected while the table injected it,
   a stale toolchain version, and a schematic asserting a finding the study never obtained.
3. **Metrics promised and never reported.** The methodology promised p99.99 and jitter while the
   harness emitted neither; the external manuscript promised a baseline model and a few-shot
   condition and reported neither. This costs areas 4 and 6 at once, because the question and the
   answer no longer match.
4. **Truthfulness of the declarations.** The AI statement, the contribution list, and the
   acknowledgement of others' work. A false declaration about the abstract is worse than any
   prose defect, since the summary doubles as the maturity test.
5. **Build gates.** Errors, undefined references and citations, floats too large, overfull boxes,
   page count against the class file. Mechanical, and level 5 in area 6 depends on them.
6. **Floats and tables never referenced from the body**, and labels defined but unused.
7. **Bibliography composition.** Peer-reviewed share, preprints carrying load-bearing claims,
   and how many of the closest works are unindexed master's theses.
8. **Research question wording against reported metrics.** If the question names the mean and the
   results report the median, either the question or the results are wrong.

## False positives to discount

These have each consumed part of a pass and were wrong.

- **Hyphenation variants.** A mechanical pass flagged about 40 "inconsistencies" of the form
  *memory-safety* against *memory safety* and *compile-time* against *compile time*. English
  hyphenates those compounds attributively and leaves them open otherwise, and the thesis does it
  correctly. Do not report these.
- **British spellings** where the house style is British: *signalling*, *sanitiser*,
  *analysed*. Proper nouns keep their own spelling (AddressSanitizer, LeakSanitizer).
- **"Significant" in its ordinary sense.** Flag it only where a statistical claim is implied
  without a test.
- **Underfull box warnings.** Cosmetic. They do not gate area 6; overfull boxes and floats too
  large do.
- **A worked example repeated across introduction, background, and appendix.** Defensible
  layering for a reader without the domain background. Note it, leave the call to the author.

## Standing blockers on this thesis

State as of the fourth pass, 17 August 2026.

1. **Rewrite the abstract unaided, then set `\abstractunaidedtrue`.** Blocking for submission and
   for area 6, and it cannot be delegated. Until it is set, every build prints
   `ai_statement: ... Not submittable`.
2. **Bare-metal tail campaign, with hardware counters and allocation profiles on the same visit**
   (`bench/TESTBED.md`). The only thing holding areas 3 and 4 at 4.5. What it buys is now
   narrow and specific: far-tail ordering below saturation, plus a mechanism for the peak-RSS
   effect and for the operation-level gap.
3. **Housekeeping**: `\censors{}{}{}` once the faculty assigns examiners, and the official
   `UH_DS_MSc.cls` in place of the reconstructed one.

## Findings a grader must not "correct"

These read like defects and are not. They are load-bearing and deliberate, and `AGENT.md` §3
holds the full list.

- Two boundary defect classes came back with the **C++ tooling ahead**, and the lock-order
  deadlock is detected by ThreadSanitizer **intermittently**, about 30% of runs. Reporting an
  inconvenient result is evidence for area 1 and area 5, not against them.
- Peak resident set size is a real language effect that reproduces under both allocators, but the
  **allocator effect is the larger one**. Neither half may be dropped.
- The end-to-end sweep is dominated by the cross-thread handoff, and the operation is a fraction
  of a percent of it, so a median comparison on that path **cannot** bound a language effect.
  The thesis saying so is a strength.
- Rust eliminates data races and aliasing errors, **not** race conditions or lock-order
  deadlocks. The distinction is held consistently and must stay that way.
- Half grades of 4.5 encode a split between method and data, or between writing and finishing.
  Do not round them; rewrite the reasoning or leave them alone.
