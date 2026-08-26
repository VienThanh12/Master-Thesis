# Calibration

Anchors from grading passes already on record, so a new pass lands on the same scale rather than
inventing one. Sources: the four passes in `docs/ASSESSMENT.md`, the grading canvases in
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
- **`pdftotext` on `diagrams/pdf/*.pdf` extracts nothing.** The included diagrams render their
  text as paths, so any dash, semicolon or staleness check routed through `pdftotext` returns zero
  on every file and proves nothing. Read the `.svg` and `.drawio` sources, and search for the
  literal `—` **and** the `&#8212;` entity, because the sources use both.
- **Semicolons in verbatim code inside a diagram**, which the house style exempts explicitly.
  `08_borrow_checker_uaf` carries five in C++ and Rust statements, `05_data_model` one in
  `[u8; 32]`. Do not count these against the style gate.
- **A hand-typed number written with a LaTeX thin space.** `9\,006` and `35\,030` match neither
  `9,006` nor `9006`. Grep for the `\\,` form or the audit will report a defect as closed.
- **`.aitells.py`'s longest sentence coming from a table row.** Its `is_prose` filter drops lines
  starting with a backslash but keeps a table row like `RQ1 & The answer divides…`, so the reported
  maximum is a table-cell artefact. The ninth pass recorded 63 words and the tenth 71, and neither
  is a prose sentence. Read the standard deviation instead: 11.0 at the tenth pass, comfortably in
  the human band.
- **`.aitells.py` reporting a sentence with a gap in it**, such as l. 708's "not just at nominal
  load but , which is why". `strip_latex` removes `\emph{...}` contents. The source is fine.
- **Peak RSS under `jemalloc`: interval `[+3.3, +3.5]` against $p$ 0.727.** Reads as a statistical
  contradiction and is not one. §6.4.3 explains it in mechanism, a handful of contaminated runs
  dominating a statistic built on a mean of paired differences, and the threats table records the
  pre-committed reading rule as costing that row. This is the rule working, which is area 3 and
  area 5 evidence.
- **The contended-primitive microbenchmark has Rust ahead where the full service under overload has
  C++ ahead.** The sign genuinely reverses between the two experiments, the thesis says so
  explicitly, and that reversal is the finding that rules the primitives out as the whole
  explanation.
- **`texaudit.py`'s prose-number heuristic firing on a value quoted from a cited paper.** The one
  hit it reports today, `0.19 \%` at l. 3909, is the kernel driver's slowdown from
  `gonzalez2023rustudp`, quoted to make a point about statistical against operational significance.
  A literature value is not a hand-typed measurement of this study. Check the citation on the line
  before scoring it.
- **Filtering the campaign JSONL on the `rate` field.** `offered_load(row)` in
  `bench/plot_figures.py` is `row["rate"] * row["producers"]`, and there are seven producers, so
  the representative load of 56 kops/s is `rate == 8000`. Filtering on `rate == 56000` lands in the
  **overload region**, where the peak-RSS sign agreement and the direction of the CPU result both
  genuinely reverse. The eighth pass burned time scoring two correct claims as defects this way,
  "18 of the 20 paired repeats agree" and "Rust draws slightly less CPU"; both are right. Pair by
  position after filtering on `offered_load`, which is what `_paired_effect` does and documents.
  When a computed check disagrees with a generated artefact, suspect the check first: rerunning
  `plot_figures.py` into a scratch `--outdir` and diffing settles it in a minute.

## Standing blockers on this thesis

State as of the **tenth pass, 26 August 2026**. Two passes running have found **no wrong measured
value anywhere**, and both verified the generated layer still holds. The defect class that moved
area 4 from 4.5 to 4.0 at the ninth pass is claims about the evidence that the evidence does not
support, listed as items 3a to 3e below. 3a is now **closed**. Read the "resolved" section before
reporting anything from the numbered list, and check every item against the source.

1. **Rewrite the abstract unaided, then set `\abstractunaidedtrue`.** Blocking for submission and
   for area 6, and it cannot be delegated. Open since the fourth pass. Until it is set, every
   build prints `ai_statement: ... Not submittable` and the printed declaration says the summary
   has not yet been rewritten unaided. Drop the abstract's "median latency matches" in the same
   edit: the paired test resolves −1.1 and −1.6 µs under the two allocators, both clearing Holm.
2. **Bare-metal tail campaign, with hardware counters and allocation profiles on the same visit**
   (`bench/TESTBED.md`). The only thing holding area 3's data half at 4, and the only lift no
   amount of editing reaches. What it buys is narrow and specific: far-tail ordering below
   saturation, plus a mechanism for the peak-RSS effect and for the operation-level gap.
3. **Closed 22 August: the eleven hand-typed values, §7.2's reproducibility claim, the
   declaration's false method sentence, §5.5's indicative instrumentation, the unplaced
   equivalence table, §8.2's Figure 8.1 overclaim, and the diagram labels.** All seven are in the
   resolved list below with the mechanism that keeps each shut. Do not re-report them from
   memory of an earlier pass. The ninth pass confirmed all seven mechanisms hold:
   `gen_artefacts.tex` regenerates byte-identical, `tab_loc`'s columns sum to 674 / 762 / +88 with
   the generator asserting it, `figures/tab_loc.tex` is `\input`, and `check_labels.py` is clean
   over 19 diagrams. Note that `bench/complexity.py` needs `lizard` from `bench/requirements.txt`
   and will not run without it.

3a. **Closed 24 August 2026.** `figures/tab_taxonomy.tex` is generated by `write_taxonomy_table()`
   in `bench/plot_figures.py` and `\input` like the other twelve result tables, so the safety
   section's no-drift claim is enforced rather than asserted. It grouped on `rust_expected`, the
   expectation recorded before the run, and it refuses to write a boundary row whose misbehaviour
   the runner did not record. Verified at the tenth pass. **Do not re-report.** §5.6 was reworded
   in the same period to name `bench/refresh_thesis.sh` instead of claiming one script, which
   answers the count objection but not the scope one: see 3d.

3b. **Three figures misstate the result they illustrate.** `fig:borrowuaf`'s caption (l. 827) says
   the C++ use-after-free is caught "only under AddressSanitizer" where `taxonomy.csv` and
   Table 7.9 both record ASan *and* TSan. `diagrams/07_ffi_seam.svg`'s bottom band is headed
   "Per-call cost" and shows the empty-crossing-against-round-trip ratio that §7.6 disowns and
   §8.3 records as right-answer-wrong-reason. `diagrams/11_tail_latency_concept.svg` says "a p99
   per-op delay becomes a p99 per-procedure delay", the opposite of the amplification its own panel
   heading and caption argue. Smaller: `fig:budget`'s caption drops the word "language" that makes
   its claim true, and `fig:effects`'s right-panel axis label is clipped because
   `plot_figures.py:1260` omits `bbox_inches="tight"`. Opened by the ninth pass. **Re-render and
   read any diagram edited for these**: the style gate checks punctuation, not sense.

3c. **Median equivalence asserted against §7.5.1. Three of four sites fixed 23 August, the abstract
   left.** There were four, and the fourth was found by applying the sync rule and not by reading
   the thesis: `Thesis_v2.tex` l. 531 carried it too, in the supervisor-facing skeleton. §1.4, §9
   and the skeleton now state the practical equivalence, name the resolved difference through
   `\PFiftyDiffAbsMax`, and add "practical and not statistical". **The abstract (l. 226, "median
   latency matches") is still open** and waits for the unaided rewrite. The paired test resolves
   −1.1 and −1.6 µs, both clearing Holm, and `tab_equivalence` marks both rows "significant". §8.2
   was already correct and supplied the register. This is the mirror of the error the thesis guards
   against, so do not read it as carelessness in the usual direction. **Area 4 was not lifted for
   the partial fix**, because 3a and 3b are untouched.

3d. **§6.3 promises a generated macro for every measured quantity the chapter quotes, and §6.4.3
   types two.** l. 2323 makes the claim. l. 2894–2895 quote "$18$ of the $20$ paired repeats agree"
   and "a resident set some $30$~MiB low", which together are the whole justification for reading
   peak RSS under `jemalloc` from its interval rather than its $p$-value. Neither has a macro, and
   `\OverloadThrAgree` is the identical quantity for the overload family and *is* generated at
   20/20, so `_paired_effect` already computes this shape. Two weaker instances of the same claim
   failing: the AI declaration carries its own version, and `diagrams/07_ffi_seam.svg` has
   `12.7 µs` and `2.54 ns` typed into the drawing. All values are correct today, so these are
   unenforced claims and not live errors, which is what 3a was before it was generated. §5.6's
   surviving overreach is "every figure and table in the evaluation", which covers two hand-drawn
   diagrams, and "regenerates the artifacts verbatim", which cannot hold for a timing measurement
   on another host. Opened by the tenth pass.

3e. **The abstract's catalogue size, new to the grading record.** l. 228 and l. 230 say "all
   **five** injected" classes and "**Five** further classes" where §1.4, §6.4.4, Table 6.9, Figure
   6.9, Table 7.1, the conclusion and `Thesis_v2.tex` all say seven and seven. It understates the
   catalogue that makes RQ2 falsifiable, which is criterion 1's own blocker, on the page an examiner
   reads first. Together with the median claim (3c) and the unreported jitter dimension, the unaided
   rewrite now has four items to settle. **Area 6 was held at 4.5**, because the build refuses to
   call the document submittable and one rewrite closes all four, but say plainly in any pass that
   submitted as it stands this abstract puts area 6 at 4.0 and area 4 follows it.

3f. **`\SatKnee` is a throughput value used as a load-axis position.** `plot_figures.py:1652`
   defines it as the highest achieved throughput in the sweep, minimised across variants, so it
   belongs to the vertical axis. `\TrackingLoad` is an offered load. §6.4.1 l. 2685 prints them as
   tracking to 336 kops/s and saturating at 335, and `fig:loadsweep`'s caption lists "the knee at
   335 kops/s" among things a dotted line marks, where panel (b) draws no knee marker. Opened by the
   tenth pass.

4. **Prose: actioned, and the only item on this list ever to move on prose grounds.**
   "rather than" stood at 154 instances and 44 per ten thousand words at the seventh pass. It now
   reads 53 and 14.9 per ten thousand (raw occurrences 167 to 69), with `.aitells.py` unmodified,
   so the change is in the prose. Sentence length moved from 24.1 ± 13.0 with a maximum of 73 to
   20.4 ± 10.4 with a maximum of 63. Re-measure rather than re-reporting the old figure.
5. **Optional, not blocking:** replace `bugden2022rust`, the one remaining arXiv item, with a
   peer-reviewed equivalent. Area 2 sits at 5 without it, since it is cited twice and both times
   beside a peer-reviewed source.
6. **Optional, not reader-visible:** the ten diagrams no document includes still carry dash asides
   and prose semicolons. `diagrams/check_labels.py --all` lists them. The gate covers any of them
   from the moment a document includes it, so this is housekeeping and not a defect.

**Resolved 22 August 2026, with the mechanism that keeps each shut. Do not re-report.**

| Item | Closed by |
| --- | --- |
| The eleven hand-typed values (deadlock rate in prose, footnote and figure caption, the unsupported "6 of 20" trial, both lost-update pairs, conformance size, Rust test count, untouched-class count, `tab:loc`'s C++ and delta columns, the p50 "contains" sentence, the 99.9 % complement) | Eleven new macros from `bench/artefact_facts.py` (fault catalogue plus suite size), `\BudgetCoreShareRest` from `plot_figures.py`, `\CppBoundedQueueLines` from `complexity.py`, and one reworded sentence. The deadlock rate is cross-checked between `taxonomy.csv` and the per-run logs, and a mismatch is a hard error |
| Table 5.4 (`tab:loc`) six lines short | Generated as `figures/tab_loc.tex`. The `CONCERNS` partition in `complexity.py` must cover both file sets and each column must sum to its measured total, or the script refuses to write |
| §7.2's "no value is hand-copied ... cannot drift apart" | Narrowed to "every measured quantity this chapter quotes reaches the page as a generated macro", which is true and was verified byte-for-byte |
| `ai_statement.tex`'s "no figure is transcribed by hand" | Same narrowing, in the declaration |
| §5.5's indicative pooling, jitter and p99.99 | Conditional throughout, with an explicit sentence that neither is reported in Chapter 7 and a cross-reference to §7.5.1 |
| `figures/tab_equivalence.tex` unplaced | Placed in §7.5.2 as the fourth of five readings of the test family, with a paragraph separating tight bounds from wide ones |
| §8.2's "states the whole result in one picture" | Now "draws the boundary itself", with the two-of-five scope in the prose |
| Diagram labels ungated | `diagrams/check_labels.py`, run by `refresh_thesis.sh`. Scope computed from the documents, verbatim code exempt through an explicit list |

**A method note from that pass.** Six labels came out of the dash and semicolon removal with a
comma splice or a panel overrun, and the gate passed every one, because it checks punctuation and
not sense. Re-render the diagrams and read them.

**Also resolved earlier.** The class file is now the department's own `HYthesisML.cls` with
the pristine template beside it, so the `UH_DS_MSc.cls` item is closed (the file survives in the
root but is not loaded). The AI declaration is gated and truthful. RQ1's metric list matches the
reported columns. `zhang2026deadlock` is the journal version, and a preprint flag on it is a
false positive from its `note` field. The FFI evidence survived the seam-count correction of
`8244901` with all ten quantities in `ffi/results/metrics.json` still matching their macros.
`\censors` housekeeping is closed as written, since the `censored` class option is set and the
class prints examiners nowhere.

## Findings a grader must not "correct"

These read like defects and are not. They are load-bearing and deliberate, and `AGENT.md` §3
holds the full list.

- Two boundary defect classes came back with the **C++ tooling ahead**, and the lock-order
  deadlock is detected by ThreadSanitizer **intermittently**, in 7 of 12 runs per
  `faults/results/taxonomy.csv`. Reporting an inconvenient result is evidence for area 1 and area
  5, not against them. The intermittency *finding* is load-bearing and must not be corrected. The
  *rate printed in the thesis* was a separate matter and was stale until 22 August. It now reads
  through `\DeadlockTsanHits` and `\DeadlockTsanRuns` in all three places, so a rerun moves it.
- Peak resident set size is a real language effect that reproduces under both allocators, but the
  **allocator effect is the larger one**. Neither half may be dropped.
- The end-to-end sweep is dominated by the cross-thread handoff, and the operation is a fraction
  of a percent of it, so a median comparison on that path **cannot** bound a language effect.
  The thesis saying so is a strength.
- Rust eliminates data races and aliasing errors, **not** race conditions or lock-order
  deadlocks. The distinction is held consistently and must stay that way.
- Half grades of 4.5 encode a split between method and data, or between writing and finishing.
  Do not round them; rewrite the reasoning or leave them alone.
