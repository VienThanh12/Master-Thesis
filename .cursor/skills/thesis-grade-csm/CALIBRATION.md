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

## Standing blockers on this thesis

State as of the seventh pass, 20 August 2026. The seventh pass found eleven of the sixth pass's
twelve items untouched, so treat this list as durable rather than as a snapshot, and check each
item against the source before reporting it.

1. **Rewrite the abstract unaided, then set `\abstractunaidedtrue`.** Blocking for submission and
   for area 6, and it cannot be delegated. Open since the fourth pass. Until it is set, every
   build prints `ai_statement: ... Not submittable` and the printed declaration says the summary
   has not yet been rewritten unaided. Drop the abstract's "median latency matches" in the same
   edit: the paired test resolves −1.1 and −1.6 µs under the two allocators, both clearing Holm.
2. **Bare-metal tail campaign, with hardware counters and allocation profiles on the same visit**
   (`bench/TESTBED.md`). The only thing holding area 3's data half at 4, and the only lift no
   amount of editing reaches. What it buys is narrow and specific: far-tail ordering below
   saturation, plus a mechanism for the peak-RSS effect and for the operation-level gap.
3. **Eight hand-typed values, and all eight are wrong.** These are the whole of area 4's cap, and
   four of them are places where the manuscript contradicts evidence it ships:
   - the TSan deadlock rate, printed as "four of twelve" in the prose and "$4$ of $12$" in Table
     7.6's footnote, against `TSan reported in 7/12 runs` in `faults/results/taxonomy.csv`;
   - both lost-update pairs, printed as 35,030/4,970 for Rust and 25,448/14,552 for C++, against
     28,914/11,086 and 27,788/12,212 in `lost_update.rust.log` and `lost_update.tsan.log`;
   - the conformance campaign at L3051–3052, `$9\,006$` against `summary.json`'s 792,964, beside a
     hand-typed `$223$`, both of which have macros (`\ConfGenOps`, `\ConfHandOps`) used correctly
     forty lines earlier. **Search for `9\\,006`**: the LaTeX thin space defeats a `9,006` or
     `9006` grep, which is how the seventh pass briefly mis-scored this as closed;
   - "twenty-five Rust tests" at L3051, against 27 from `cargo test --release -- --list`;
   - "four of the ten classes untouched" at L2957, against two `undetected` rows in
     `taxonomy.csv` (three if the intermittent deadlock is counted, never four);
   - Table 6.4's C++ column, nine rows summing to 668 against a printed `\CppRawLines` of 674 and
     a delta column summing to +94 against a printed +88 (the Rust column sums correctly);
   - the §7.5.1 p50 sentence, which says each interval "contains" the others' point estimates
     when no interval contains a cross-language median and the true claim is "overlaps";
   - the 99.9 % complement of `\BudgetCoreShareMax` = 0.250, whose complement is 99.750 %.
   §7.2's "no value is hand-copied ... the text and the data cannot drift apart" is falsified by
   all eight and should be narrowed to the claim that is true and strong on its own.
4. **§5.5 describes instrumentation the reported campaign did not have**: pooled far-tail figures,
   directly measured jitter, and p99.99 "reported descriptively". §7.5.1 says the campaign predates
   it. Put the three sentences in the conditional, and either drop jitter from the abstract's list
   of open dimensions or mark it as future work.
5. **`figures/tab_equivalence.tex` is generated on every refresh and `\input` by no document.** An
   unrealised asset rather than a defect: it holds the equivalence-bound reading of RQ1, which is
   the strongest available answer to the half of RQ1 the host cannot resolve.
6. **Diagram labels breach the house style, and nothing gates them.** `.aitells.py` reads `.tex`
   only and `build_deck.py`'s `check_prose_style` covers the deck only, so the figures are the one
   reader-visible prose surface with no check. Of the eleven diagrams the thesis includes, five
   carry a dash aside in a label, panel title or in-figure footer (fourteen occurrences:
   `17_guarantee_boundary` 5, `04_request_lifecycle_sequence` 4, `08_borrow_checker_uaf` 2,
   `27_workload_timeline` 2 literal, `16_coordinated_omission` 1) and five carry a prose semicolon
   (`17_guarantee_boundary` 2, `29_research_gap`, `07_ffi_seam`, `12_concurrency_models`,
   `15_overload_cliff`). Fix the `diagrams/` sources, re-render, then extend the gate.
7. **Prose:** "rather than" carries 154 sentences at 4.7 per thousand words, which `.aitells.py`
   scores at 44 per ten thousand against a next-highest pattern of 1.2. With dashes and semicolons
   clean in the `.tex`, this is the remaining machine-uniformity signal there.
8. **§8.2 says Figure 8.1 "states the whole result in one picture"** while the figure draws two of
   the five boundary classes. The caption discloses the gap, so the prose is the part to fix.

**Resolved, do not re-report.** The class file is now the department's own `HYthesisML.cls` with
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
  *rate printed in the thesis* is a separate matter and is stale: see standing blocker 3.
- Peak resident set size is a real language effect that reproduces under both allocators, but the
  **allocator effect is the larger one**. Neither half may be dropped.
- The end-to-end sweep is dominated by the cross-thread handoff, and the operation is a fraction
  of a percent of it, so a median comparison on that path **cannot** bound a language effect.
  The thesis saying so is a strength.
- Rust eliminates data races and aliasing errors, **not** race conditions or lock-order
  deadlocks. The distinction is held consistently and must stay that way.
- Half grades of 4.5 encode a split between method and data, or between writing and finishing.
  Do not round them; rewrite the reasoning or leave them alone.
