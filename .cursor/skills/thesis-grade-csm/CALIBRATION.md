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
| 5 | 5 → 4.5 | The eleventh pass took it back the day a new results section landed. Everything above still held, and three sentences in the discussion chapter said an instrument "was not collected" that the results chapter reported the output of, while the revisit of the hypothesis about the far tail did not use the campaign that resolved the far tail. **A discussion one section behind its own results fails the reliability sub-factor even when the reasoning in it is excellent.** Scored from chapter-7 sites only, so it is not the area-4 finding counted twice. |
| 5 | 2 | No discussion chapter. Own results never compared with previous research, reliability never assessed, ethics absent, and a contribution claimed that the preface credits to the partner. |
| 6 | 5 → 4.5 | The third pass gave 5 for the writing. The fourth took it back, because level 5 asks for presentation that is technically camera-ready with excellent finishing polish and the *finishing* failed: the printed AI declaration asserted the abstract was written unaided while a source comment recorded it as model-drafted, alongside a float overflowing its page, two overfull boxes, and sentences of 93 and 86 words. Writing quality does not carry this area on its own. |
| 6 | 4.5 → 4.0 | The eleventh pass, on **level 4's** clause and not level 5's: the whole text logical and consistent on the description of the research setup, findings and conclusions. Four sites failed it after one integration, none of them the abstract, which is graded separately for the reason the tenth pass gives. The pattern to expect: a new results section falsifies the methodology section that said the metric was unavailable, the data section that promised a replacement, the reproducibility section that promised byte-identical reruns, and a table caption that promised the protocol was met. |
| 3 | 4.5, data half now 5 | The thirteenth pass. The canonical repeat closed the data half, and the half grade **changed sides**: what holds it is the *description* of the method. §4.5 fixes a reading rule in advance and names dropping it for the convenient block as the failure it exists to prevent, and §6.4.1 then does exactly that. And `REPR_LOAD_OPS` is pinned in the generator for a documented reason while §6.2 still states the derived rule the code abandoned. **A 4.5 in this area no longer means "the hardware was inadequate".** Read which half before quoting the number. |
| 4 | 4.5 → 4.0 | The thirteenth pass, on level 5's aptness clause. Thirteen prose statements disagreed with the artefact beside them, and **six were wrong rather than stale** (see the new defect class below). Level 4 held because no value in any table or figure was wrong, six passes running, and the structure, per-question evidence status and generalisability discussion were intact. |
| 6 | 2 | Template dummies surviving on the abstract page, three different dates, duplicated and undefined labels, a stray Cyrillic word in the results, dense grammar errors, and no statement of AI use in the document. |
| 4 | 5 → 4.5 | The twenty-first pass, on level 5's aptness clause, and **the smallest defect ever to move an area here**. `tab:testbed`'s caption says the columns are arranged so each adjacent pair isolates one change, and its own Toolchain row prints `g++ 15.2.1` for the reported sweep against `g++ 15.1.1` for the guest. A caption refuted by a row of its own table is the same shape as a figure title refuted by its own bars. Beside it, one hand-typed compiler version that is simply wrong, and one guest-era phrase (`on bare metal`) that can no longer pick out a host. **Calibration point: a single wrong configuration value plus a caption over-claim is a 4.5, not a 4.0.** The thirteenth pass's 4.0 took thirteen disagreeing statements, six of them wrong. |
| 6 | 5 → 4.5 | The twenty-first pass, on **both** level 4's "consistent … description of research setup" (three prose sites claiming toolchain parity that an appendix table refutes) and level 5's finishing polish (an elliptical `is not` with no predicate, in §1.4 of both documents). The half grade splits writing from consistency-and-finishing, which is what a 4.5 means here. **The 83-word sentence was explicitly not counted**, because the twentieth pass ruled it not a failing clause and a later pass does not relitigate a ruling on unchanged text. |
| 3 | 5 → 4.5, test program not host | The thirty-first pass. The host was clean bare metal, and the half grade came back from the **test program**. Each sender sleeps at ordinary priority, so up to 50 µs of timer slack sits inside a clock whose median is about 73 µs and whose core call is 34 ns. Past saturation, the planned comparison timed the sender's own recording. All of it is disclosed and none of it is rerun. **The same anchor shape as the guest: an instrument effect the size of the quantity measured.** Editing cannot lift it. |
| 2 | 5 → 4.5, plain words | The thirty-first pass. A plain-words rewrite raised Flesch and removed "coordinated omission" from the body, the field's term for the problem the main overload result turns on. It coined "histogram fill" instead. With a 1,600-word background and no C++-side safety position, level 5's "in-depth command" failed. **Keep the plain sentence and add the term of art once, cited.** The plain-label rule covers diagrams, slides and chat, not the body. |
| 7 | n/a | Every pass. The manuscript cannot settle it. |

## The defect class the thirteenth pass added

**A new dataset does not only make claims stale. It can make them false in the opposite direction.**
Until the thirteenth pass every drop came from prose describing an *older, weaker* state of the
evidence, which a sweep for "virtualised", "unresolved" or "not collected" finds. Three of that pass's
findings were not that shape:

- "every pair of confidence intervals overlaps, so the table on its own separates nothing". The new
  table separates every C++/Rust pair.
- "peak resident set size under jemalloc is the one upper-block row that does not clear it". All 14
  now clear, and the same sentence prints 14 of 14 before naming the exception.
- "the knee also sits at the same place for all four variants". The Rust arms track a full rung
  further, which the figure draws and which hides a result in the author's favour.

None contains a staleness keyword. Each was *true of the guest*. The only check that finds them is
reading every numeric and comparative claim in the results section against the generated table or
figure beside it, one at a time. **A promotion pass is most tempted to skip that check precisely when
it is most needed, because the macros all regenerated cleanly.** A clean regeneration says the numbers
are right and says nothing about the sentences around them.

**A third shape, added by the fourteenth pass, and it is the subtlest of the three.** Auditing its own
overnight remediation, that pass found four defects and three shared a form: **a correct statement
attached to the wrong scope.** A caption said peak RSS "separates the two languages" where that holds
for the paired comparison and fails for the unpaired envelopes, which overlap. A sentence said "5 of
its 14 rows" where the family has 14 tests and the table it named shows 10. A caption called one load
"the one place the two languages part company" where it is the one place the ordering favours *Rust*,
the languages also parting company at two deeper loads. **None is a wrong number**, so a macro
recompute passes every one of them, and a reader checking the value finds nothing. The check that
catches this class is to ask of every comparative claim exactly **which set it quantifies over**:
paired or unpaired, family or table, all loads or one direction.

Two corollaries worth carrying:

- **Check the macro's definition, not just its value.** `\SatKnee` is the *minimum* achieved
  throughput across variants, so it reported a shared knee where the variants differ by 14 per cent,
  and the prose then asserted the sharing. `\PNineNinePreCliff` divided by 1000 and printed `:.0f`, so
  on a quiet host it rendered as "0 ms". A macro can be correctly generated and still be the wrong
  quantity for the sentence holding it. The remediation of 27 August found two more of exactly this
  shape, and **neither was visible in the source**: `\JitterVsMedian` was a percentage that the prose
  printed as a multiple ("jitter at p99 is $2\times$ the median operation", where the macro was 2 per
  cent of the median and was the *median* jitter, not the p99), and `\JitterRange` held `1--2` inside a
  sentence that wrapped it in math mode for the `\mu`, so the built PDF read "spans 1 − −2 µs".
  **Render the page.** A range macro should be a Lo/Hi pair and a percentage macro should say `Pct` in
  its name, which is how both are now emitted.
- **A method claim can go false while the result stays true.** §4.5 and §6.4.1 say the p99.99 is
  pooled across repeats; `write_latency_table()` takes a median of the per-run values, which §4.5
  itself calls meaningless. The pooled figures make the finding *stronger*. Verify how a headline
  statistic is computed, not only what it says.

## Checks ranked by historical yield

1. **Every number in the results prose against its table.** Found 28 contradictions in one
   manuscript and about nine hand-typed values in the other. Nothing else has this hit rate.
   **Extended by the thirteenth pass to every comparative claim, not only every number**: "intervals
   overlap", "separates cleanly", "the one row that fails", "the knee is shared" are all checkable
   against a generated table and all four were wrong.
   **Extended again on 28 August: check the claim at its summary sites, not only where it is
   derived.** The clause "the C++ build sustains 1.7 times the throughput of the Rust build while
   drawing 1.8 times the CPU per completed operation" attaches the participle to C++, where the data
   has Rust drawing 1.8 times. It was **right in the section that owns the result** and wrong at
   every one of the five summary sites, across two documents. A reviewer working table by table sees
   the correct version each time and never reaches the wrong one. Read the introduction, the
   discussion and the conclusion *against each other* on each headline claim, and check which noun a
   participle attaches to when two subjects are in play.
2. **Every figure against the claim it illustrates.** Three figures here contradicted the results
   tables after the claims moved: a defect class marked not injected while the table injected it,
   a stale toolchain version, and a schematic asserting a finding the study never obtained.
   **Extended on 28 August to the figure's own generated titles and annotations.** `fig:tailpct`
   panel (b) printed the ratios 0.2, 0.2, 0.5, 0.6 and 0.7 above its bars while its hard-coded title
   read "Where the host stops resolving the comparison" and the paragraph beside it said "from p90
   upward the interval wins". The bars, the annotations, the title and the prose were four surfaces
   and two of them were wrong. A title that states a conclusion must be generated from the data like
   any other claim, and this one now is.
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
  large do. The converse is a false *negative*: `texaudit.py` reports `PASS no overfull boxes`
  while ignoring `Overfull \hbox ... while \output is active`. Those are running headers. The
  sixteenth pass found a 23 pt overflow on body page 9 (`SOFTWARE9` jammed against the page
  number) that every earlier pass recorded as clean. Grep the log for `while \\output is active`
  before calling the finishing camera-ready.
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
- **`bench/results-baremetal/latency_budget.json` is not bare-metal evidence.** It is byte-identical
  to `bench/results/latency_budget.json` (md5 `634e0b11…`), so it is a copied guest file and
  `\BudgetCoreRatio` remains a guest number. `bench/latency_budget.sh` was **not** re-run on the
  visit. Do not credit the decomposition to bare metal, and do not report the copy as a defect in
  the results either: what the visit did deliver for that claim is better, namely the op-scope
  counters. The file's presence in that directory is misleading and worth removing.
- **`env-20260812-*.txt` inside `bench/results-baremetal/`.** The directory holds copies of three
  guest campaigns and their environment captures alongside the two bare-metal ones.
  `baremetal_facts.py` reads `sorted(glob(env-*.txt))[-1]`, so it correctly takes the newest, but a
  grader eyeballing the directory can easily read a Rocky Linux capture as the confirmation host's.
  The confirmation host is `env-20260826-102012.txt`, `touched-reptile`, Ubuntu 24.04.4.
- **The four bare-metal `\Bm*` values that look like they contradict the main sweep.** They are
  supposed to differ: 1.64 against 1.8 for the overload ratio, 0.5--1.1 against 1.6 µs for the
  median, 2.8 against 1480 µs for the widest p99 interval. The `Bm` prefix exists so the two
  datasets cannot be confused, and a value moving between hosts is the confirmation working. The one
  genuine finding in that family is the peak-RSS *ratio*, item 3h.
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

**`Ha_Vien_Mastersthesis_2026.tex` only, thirty-second pass, 12 November 2026. Mean 4.67,
graded as the deposit manuscript.** Area 1 at 5, areas 2 to 6 at 4.5. The numbers did not
move. Do not re-report an empty abstract or a body that never names coordinated omission.

- **Area 2.** Coordinated omission is named, with Schroeder and HdrHistogram. The background
  is still short, and `sutter2025profiles`, `vandevoorde2026profiles` and `baxter2024safecpp`
  are still uncited.
- **Area 3, which needs a rerun.** Unchanged. The clock carries the sender's wake-up lateness
  below saturation, a 2.4% window error past it, and a fixed build order.
- **Area 4.** The findings summary says the largest gap is at the median and that p99 and
  p99.9 are smaller. `tab:significance` has p99.9 at 4 µs and 3 µs against medians of 1.2 µs
  and 1.5 µs. `31_e2e_clock` and `32_same_handoff` still label the core or the queue as the
  language.
- **Area 5.** The H1 revisit still omits the sleep-path caveat. One sentence still says the
  results show no slowdown for bounds checks. The summary ranking above is the new cause.
- **Area 6.** The abstract is back and its claims match. `\abstractunaidedfalse` still warns,
  and that warning is not scored. Short sentences are 52%, spread 7.0. The plain rewrite left
  agreement errors.

**`Thesis_v5.tex` only, thirty-first pass, 27 October 2026. Mean 4.67, graded as the deposit
manuscript.** Historical. Area 1 at 5, areas 2 to 6 at 4.5. The caps below are the ones the
thirty-second pass closed or replaced. Do not grade from this block.

- **Area 2.** Coordinated omission is never named. The plain-words pass removed it. There is no
  C++-side safety position, although Sutter, Vandevoorde and Baxter are in the bibliography.
- **Area 3, which needs a rerun.** RQ1's clock carries the sender's wake-up lateness below
  saturation and a 2.4% window error past it, and the build order is fixed.
- **Area 4.** `31_e2e_clock` and `32_same_handoff` credit "the language" with what the text
  credits to two handoff designs.
- **Area 5.** The H1 revisit drops the sleep-path caveat.
- **Area 6.** Basic terms are re-defined in the body, and the sentence rhythm is out of band.

The abstract box is empty and `\abstractunaidedfalse` ships. Following the tenth pass, that is
not scored. Do not re-report the thirtieth pass's five items.

**`Thesis_v5.tex` only, twenty-eighth pass, 29 September 2026. Mean 4.92.** Areas 1 to 5 at 5,
area 6 at 4.5. The twenty-seventh pass's caps are closed in this PDF: Clock B is the same host
and `nohz_full` as the campaign, the probe tests use all 20 pairs and the canonical paired
permutation, and the abstract, motivation, hypotheses, guidelines, and conclusion describe that
evidence. Area 6 fails level 5's camera-ready clause: `tab:testbed` is 111 pt too large for its
page, `tab:params` overruns by 5 pt, and the problem statement prints "unknow" and "that
affects". Do not copy this mean onto the draft. Do not re-open the twenty-seventh pass's closed
items as if they were still in the source.

**`Thesis_v3.tex` only, twenty-sixth pass, 16 September 2026. Mean 5.00, a hold.** Fifteen commits
after the twenty-fifth pass added two diagrams, removed the uncited predictability section, and
renamed arm to variant. The macros still match, including the new SVG labels. Do not reopen the
five clauses that held the skeleton at 4.83 on 10 September (bare `\FfiOpBoundPct`, abstract (5)
ranking the full path, “mixed-order”, `\CpuDiffAbsMax` on the coping regime, title-page `TBD`).
`tab:latency` is in that PDF. Do not re-report them as skeleton caps. Eight precision losses
(three new: Meneely “bugs”, “look the same in delay”, `fig:e2eclock` not to scale; five carried
from the twenty-fifth pass) are listed in the twenty-sixth pass and are not caps. Blockers 3 and
4 below remain the **full draft's**.

**Updated at the twenty-first pass, 7 September 2026, for `Ha_Vien_Mastersthesis_2026.tex`. Mean
4.83: areas 1, 2, 3 and 5 at 5, areas 4 and 6 at 4.5.** One live blocker on the draft, and it is
editing:

**Blocker 3, OPEN. Toolchain parity with the guest is claimed and false.** `\GuestGpp` is 15.1.1
and `\MainGpp` is 15.2.1, each generated from its own campaign's environment capture. `rustc`
matches at 1.97.1. The container pins the `gcc-toolset` major version, not the point release, so a
rebuild between the guest campaign and the 27 August canonical repeat moved g++ by one patch. Four
sites do not know it: §6.1 l. 2211 ("the same userspace and compiler pair the earlier virtualised
campaign used"), §6.4.5 l. 2997 ("the same toolchain … differ in the machine alone"), §6.4.5
l. 3131 ("share a design and differ in the machine"), and `tab:testbed`'s caption l. 4574 ("each
adjacent pair isolates one change"), whose own Toolchain row at l. 4591 prints the contradiction.
Separately **§6.4.7 l. 3162 hand-types 15.1.1 as *the measurement host's* g++**, which is wrong;
the fault-run versions in the same sentence (`g++ 13.3`, `rustc 1.97`) are hand-typed and correct.

Three things about it are the transferable part.

- **It is `AGENT.md` §3 item 3h's defect on the other host.** The eleventh pass found exactly this
  for the confirmation host and the 26 August remediation fixed it by saying "four ways and not
  three". Nobody asked the same question of the guest comparison. Half a pair fixed, at one remove:
  **when a pass fixes a claim about one comparison host, check the other one in the same edit.**
- **No gate could see it.** `texaudit.py`'s prose-number heuristic requires a unit, and a bare
  dotted version number has none. Both values sit in the safety subsection and an appendix table
  rather than in the performance prose a pass reads first. Teach the heuristic dotted versions.
- **Repair is by disclosure, not withdrawal.** A GCC patch release confounds nothing the thesis
  reports, so the honest fix *adds* a caveat exactly as the `\Bm` column's did, and costs no claim.

**Blocker 4, OPEN, five minutes.** §1.4 of *both* documents (draft l. 683, skeleton l. 488) reads
"How it compares against the cost of the allocator choice **is not**:" with no predicate to elide.
`a0e9122` wrote "That effect **is** the same size on all three machines measured" and `ed6debe`,
the fourteenth pass's scope-attachment fix, folded that clause into a prepositional phrase and
deleted the copula. **An editing pass introduced it and seven grading passes read past it.**

**Two findings a twenty-first-pass sweep cleared, so do not re-open them.** A split-word detector
over both rendered PDFs found **0** genuine hits, the author's `safe`/`ty` fix having been the only
instance. And `artifact`/`artefact` is **not** drift: all 9 `artifact` uses are the ACM-sense
research deliverable and none of the 14 `artefact` uses is, so it reads as a deliberate convention.

**The generated layer was re-derived, not read**, for the first time since the fourteenth pass:
`plot_figures.py --outdir` reproduced `gen_macros.tex` and all 12 `tab_*.tex` byte-identical. Do
that rather than reading tables; it costs 24 seconds and settles the whole layer.

*Historical, from the twentieth pass, 3 September 2026:* a hold at 5.00 on the 1 September PDF.
Blocker 2 remains closed. Blocker 1 is **CLOSED**, facts and declaration: the
printed abstract matches the tables, `\abstractunaidedtrue` ships, page 96 prints that the abstract
was written by the author unaided, and the PDF contains no Not submittable. Area 6 is 5. The §2.2
running-header overflow remains **CLOSED**: the source has
`\section[Latency and predictability]{Latency, throughput, and predictability in real-time software}`,
the TOC and the header on body page 9 ship the short title, and the log has zero `Overfull`,
including `while \output is active`. Extraction still concatenates title and page number on one
baseline (`PREDICTABILITY9`). That is not an overflow. Do not re-report `SOFTWARE9`. Do not
recommend another `\sectionmark`. Do not re-open the unaided switch as a grade cap.

**Updated at the thirteenth pass, 27 August 2026 night. Read this block before the numbered list
below, which is a day out of date in one important respect.**

**Blocker 2 is CLOSED.** The canonical-configuration bare-metal repeat ran on 27 August:
`bench/results/campaign-20260827-151927.jsonl`, 1120 runs at 7 shards, 7 producers, 14 load levels,
20 repeats, `virtualisation: none`, SMT off, `performance` governor with boost off, `nohz_full` on the
pinned cores, toolchain pinned in a container, zero errors. It is now the thesis's **main** dataset,
not a confirmation campaign. Area 3's data half is 5. The far tail is resolved on the main sweep in
Rust's favour, `\NSignificant` is 14 of 14, `\NEqvUnresolved` is 0, and `tab:latency` has a p99.99
column. **Never again report blocker 2 as open.** Two things about the new state:

- **`isolcpus` must never be added.** The first attempt on 27 August booted with `isolcpus=2-17`,
  which removes those cores from every scheduling domain, so the benchmark's 14 threads all inherited
  `cpu2` and an entire 1120-run campaign measured one core. Every record looked individually
  plausible. `bench/canonical_repeat.sh` now hard-fails on it.
- **`bench/results-canonical/` holds that invalid campaign** and is kept as a worked example. Never
  quote it. The valid one is in `bench/results/` and `bench/results-canonical2/`, byte-identical.

**Blocker 1 is CLOSED as of the nineteenth pass, 31 August 2026 afternoon. Do not
re-report the ten defects, and do not re-open the unaided switch as a grade cap.** Page 3 prints
seven and seven, a few microseconds in Rust's favour, no host, Rust 448 / C++ 392, then C++ 1.7×
after both have stopped tracking, and "timed alone" covering only the operation.
`\abstractunaidedtrue` ships. Page 96 prints that the abstract was written by the author unaided.
The PDF contains no Not submittable.

**The running header of §2.2 is CLOSED as of the eighteenth pass, 31 August 2026. Do not
re-report.** The optional short title is in the source, the TOC, and the shipped header. The log
has zero `Overfull`. Nothing on the finishing list remains as a grade cap.

**Both of the thirteenth pass's analysis items are CLOSED by the remediation of 27 August night, and
neither may be re-reported.** They are kept here with the fix, because the fixes are the transferable
part:

- **The pooled far tail.** `pooled_far_tail()` in `bench/plot_figures.py` reads
  `<campaign>.hist.pooled.csv` and returns `None` rather than falling back to the per-run `p9999`
  field, so a missing pooling step now removes the column loudly instead of printing the statistic
  §4.5 disowns. The cell prints without an interval and carries a dagger, because pooling makes the
  operation the unit of analysis. `refresh_thesis.sh` pools `bench/results/` too. `\FarTailRange` went
  52 to **87 µs**, so the fix strengthened the finding.
- **The 448 kops/s rung is reported**, descriptively, with `\KneeGapAgree` at 40/40, plus a
  `tab:threats` row naming the threat: an operating point chosen after seeing the data. It is
  deliberately **not** in the Holm family. `\SatKneeCpp`, `\SatKneeRust`, `\TrackingLoadCpp`,
  `\TrackingLoadRust` and `\KneeShared` sit beside `\SatKnee`, which is a `min` across variants and is
  what concealed the difference.

**Read the remediation entry in `docs/ASSESSMENT.md` before grading, then verify rather than believe
it.** Two claims it wrote in one pass and a fresh pass should check: the pooled-p99.99 statement, now
at six sites, and the knee finding, now at eight.

*Historical state below, as of the remediation pass of 26 August 2026 evening, which followed the
eleventh grading pass the same evening and closed its whole editing tier except the abstract.*

**Items 3b, 3d, 3f, 3g, 3h, 3i, 3j and 3k are CLOSED.** They are kept below with the fix against
each, because the fixes are the transferable part. **The claims-about-the-evidence class is empty as
of the third remediation of 26 August, for the first time since the eighth pass** (3i, 3j and 3k
were its last members and all three were closed that night). The second remediation also claimed the
class was empty and was wrong, so **verify before believing this**: grep for the phrases in 3i and
3j and check that §7.2 and both summary tables read as the fixes describe. Read the "resolved"
section before reporting anything from the numbered list, and check every item against the source.

**The pattern to expect on the next pass.** Every drop since the ninth has come from prose
describing a different state of the evidence than the artefacts hold, and every one has been an edit.
Three shapes, in the order they were discovered:

1. **Prose behind the artefacts.** A new results section lands and the four places that get missed
   are the summary-of-findings table, the threats table, the hypothesis revisit, and the methodology
   section that said the metric was unavailable. Check those four first and the rest of the pass gets
   cheap.
2. **A claim propagated rather than checked.** A remediation pass rewrites every *sentence* that says
   X while never asking whether X is true. This is how the counter over-claim (3i) spread from one
   site to four. When a pass reports "all N sites rewritten", check whether the claim they now share
   is sound.
3. **Half a pair fixed.** A caption is corrected and the paragraph introducing it is not (3j). After
   any caption edit, read the sentence above the float.

**Two numbers from 28 August that calibrate every future estimate of remaining risk.** Editing rounds
on this project introduce defects at roughly **one per two to four changed passages**, and the
session doing the editing **under-estimates that rate by about half**: the fifteenth pass predicted
two to four undiscovered defects in its own last fifteen edits and an audit found eight. Budget one
independent read per editing round, and when a pass tells you what its residual risk is, double it.

**A defect class no gate in this repository can see: the slide deck.** `build_deck.py`'s
tail-percentile slide carried the title "the host runs out of resolution" and an annotation saying
the uncertainty exceeds the gap, beside the two macros that say the opposite, and it displayed a
regenerated figure whose own panel title contradicted it. `texaudit.py` does not read the deck,
`.aitells.py` does not read the deck, and the deck's own two gates check layout and punctuation, not
agreement with the data. **Check the deck against the thesis whenever a campaign moves**, and
remember `AGENT.md`'s older warning that a diagram only the deck uses is outside every gate too.

**A rule this thesis has now demonstrated three times: a remediation pass must not grade its own
work.** The two failures above are invisible from inside the pass that made them. Grade the
remediation separately, and ask specifically what it propagated and what it half-fixed.

**And the strongest version of that rule, from 28 August: run a second reader with no context.** The
fourteenth pass audited its own overnight remediation and found four defects, which was worth doing.
An independent audit of the *same* claims, run in parallel from the artefacts alone, found **five
more**, including a results paragraph stating the exact opposite of the figure beside it. Both
self-audits missed it for the same reason: they were reading for the claims they knew had changed,
and this one had not changed since the guest campaign. The independent reader also re-derived every
artefact into a scratch directory and confirmed `gen_macros.tex` and all eleven `tab_*.tex` reproduce
byte for byte, which is the cheapest possible proof that the generated layer is not the problem. Two
sessions editing and grading in sequence are not a substitute for one reader who was not told what to
expect.

**The one thing to internalise before grading this thesis again.** Its failure mode is not wrong
numbers and never has been. It is **prose that describes an older state of the evidence than the
artefacts hold.** Every pass since the ninth has found more of it and no pass has found a wrong
measured value. So budget the pass accordingly: spot-check a dozen macros to confirm the generated
layer still holds, then spend the time on the four places a new result has to reach and usually does
not, namely the summary-of-findings table, the threats table, the hypothesis revisit, and the
methodology section that said the metric was unavailable.

1. **CLOSED 31 August 2026 afternoon.** `\abstractunaidedtrue` ships. Do not re-report the ten
   defects, and do not re-open the switch as a grade cap. Optional: the far-tail gap is not in the
   abstract.
2. **Bare-metal tail campaign. RUN on 26 August 2026, and the item has changed shape.** Two 480-run
   sweeps on a rented AMD EPYC 7443P, `virtualisation: none`, 0 of 60 sampling intervals with any
   steal. It delivered everything this item promised: pooled p99.99 separating the languages over 32
   to 96 kops/s with Rust lower, `perf` counters at the operation scope giving the mechanism
   (11 % fewer instructions, 15 % fewer cycles, 29 % more cache misses per thousand instructions),
   and a jemalloc allocation profile. Area 3's data half moved 4 to 4.5 for it. **What is left is
   two things.** The run used the `TESTBED.md` example configuration (8 shards, 8 producers, 8
   loads, 15 repeats) against the canonical 7/7/14/20, **and it changed the toolchain too**
   (`g++ 13.3.0`/`rustc 1.98.0` against `g++ 15.1.1`/`rustc 1.97`), so it corroborates and cannot
   replace. And the allocation profile sits unanalysed in
   `bench/results-baremetal/alloc_profile-20260826-110718/`, which is why RQ3's memory result is
   still "resolved, unexplained" in `tab:findings`. Do not report this item as an open measurement
   without saying which half is open.
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

3b. **CLOSED 26 August 2026, remediation pass. Do not re-report.** All five are fixed and each fix
   is worth carrying. `fig:borrowuaf`'s caption now says "only under a sanitiser on a path a test
   exercises", which matches `taxonomy.csv`. Diagram 07's band shows the direct A/B the harness runs
   (same operation native against through the seam) instead of the disowned
   crossing-against-round-trip ratio, and the two bars are almost the same length because that is
   the finding. Diagram 11 now reads "so a 1-in-100 per-op delay is a 1-in-25 procedure delay",
   which is $1-0.99^4$ over the four ops its own panel draws, so the label finally argues the
   amplification the heading claims. `fig:budget`'s caption carries "language". And **`fig:effects`
   was not fixed by `bbox_inches="tight"`**, which was tried and failed, because a tight bbox crops
   to the artists it can measure and the overhang was not one of them. One shared `fig.supxlabel`
   fixed it, and it is better design since both panels plot the same normalised quantity. Two
   method notes. Re-render and **read** any diagram edited here, since the style gate checks
   punctuation and not sense. And count the numbers you leave in a hand-authored SVG: the first
   rewrite of diagram 07's band typed eight measured values where two had been, before the
   statistics moved to the caption as macros.

   *Original text, kept for the reasoning:* `fig:borrowuaf`'s caption (l. 827) says
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

3d. **CLOSED 26 August 2026, remediation pass. Do not re-report.** Six new generated macros retire
   every typed measured value in Chapter 6: `\RssAgree` 18/20, `\RssLowRunOffset` 31,
   `\PFiftyMedian` 80, `\PNineNineLightest` 245, `\PNineNinePreCliff` 6 and `\BudgetFloor`
   0.000061, plus `\BmPFiftyMedian` 74 in `baremetal_facts.py`. All seven were recomputed from the
   raw logs and match. Two of the generators are worth knowing about. `rss_low_run_offset()` splits
   each variant's repeats at their largest gap rather than at a threshold, refuses a variant whose
   runs are unimodal or whose low group is not a minority, and returns `None` when none qualifies,
   so the macro is absent rather than zero on a campaign without the defect. `\BudgetFloor` comes
   from the same `attainable_floor()` as `\MinAttainableP`, so changing `BudgetRepeats` moves it.
   §5.6's scope claim was rewritten in the same pass to name its two exclusions, hand-drawn
   schematics and the fact that a rerun on another host regenerates by procedure and not to the same
   values. Diagram 07 now types only the two bar lengths, which a bar chart cannot avoid.

   *Original text, kept for the reasoning:* l. 2323 makes the claim. l. 2894–2895 quote "$18$ of the $20$ paired repeats agree"
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

3f. **CLOSED 26 August 2026, remediation pass. Do not re-report.** Reworded at all four sites. The
   sweep now "tracks the ideal line up to an offered `\TrackingLoad` kops/s, where it plateaus at an
   achieved `\SatKnee` kops/s", and the prose adds that the rate ladder brackets the knee rather
   than pinning it, since the next rung is where the arms stop tracking. `fig:loadsweep`'s caption
   no longer lists a knee marker panel (b) does not draw, `tab:params`'s row is relabelled "Measured
   throughput plateau", and `Thesis_v2.tex` follows. The macro names were left alone deliberately:
   renaming one used in six places plus the deck buys nothing that the wording does not.
   §`sec:baremetal` had already done this correctly, bracketing its own knee between `\BmKneeLo` and
   `\BmKneeHi`, and supplied the pattern.

   *Original text, kept for the reasoning:* `plot_figures.py:1652`
   defines it as the highest achieved throughput in the sweep, minimised across variants, so it
   belongs to the vertical axis. `\TrackingLoad` is an offered load. §6.4.1 l. 2702 prints them as
   tracking to 336 kops/s and saturating at 335, and `fig:loadsweep`'s caption lists "the knee at
   335 kops/s" among things a dotted line marks, where panel (b) draws no knee marker. Opened by the
   tenth pass, still open at the eleventh. **The fix pattern is now inside the document**:
   §`sec:baremetal` brackets its own knee between `\BmKneeLo` 448 and `\BmKneeHi` 512 because the
   sweep steps over it, which is the honest form. Copy that.

3g. **CLOSED 26 August 2026, remediation pass. Do not re-report.** All six rewritten, and the honest
   half was preserved rather than dropped: the allocation profile is now described in the thesis as
   captured and unanalysed, so the gap stays visible in the document instead of only in this file.
   `tab:threats`'s RQ3 row reads "Counters on the confirmation host" against "Direction accounted
   for, the split inside the resident set not". §4.4 says the main campaign reports neither metric
   and the confirmation campaign carries both. **Note the table overflowed its page while this row
   was being lengthened**, which cost several rebuild cycles: `tab:threats` is the densest table in
   the thesis and sits within a few points of its page, so measure after any row edit. One number
   the eleventh pass had wrong is corrected in the remediation record: the bare-metal CPU result
   *confirms* the guest's below-saturation CPU finding rather than resolving a non-result, and the
   "reverses under jemalloc" reading came from a stale `docs/TODO.md` note about an earlier campaign.

   *Original text, kept for the reasoning, and the largest single finding on the eleventh pass:* The bare-metal visit collected `perf` counters at both
   scopes and a jemalloc allocation profile for both languages, and §`sec:baremetal` reports the
   counters under the heading *A mechanism, from counters the guest did not expose*. Yet §6.4.3
   l. 2930 says the gap is unexplained "for want of hardware counters and allocation profiles",
   §7.2 l. 3704 says the split "needs the allocation profiles and hardware counters this study did
   not collect", §7.6 l. 4281 says "no hardware counters or allocation profiles were collected", and
   `tab:threats`'s RQ3-origin row has a control column reading "None available on this host". The
   first is falsified ninety lines later in its own chapter. Two more of the same shape on the other
   metric: §5.5 l. 1597 says "Neither is reported in Chapter 6" of p99.99 and jitter where p99.99 is
   reported, and §7.6 l. 4263 says both "postdate the reported campaign". Jitter genuinely is still
   unreported, so that sentence needs splitting rather than deleting. **This is what took area 5 off
   5**, because three of the six are chapter-7 text.

3h. **CLOSED 26 August 2026 except the abstract, which is item 1. Do not re-report the other four.**
   `tab:findings`'s RQ1 row, §7.1, `tab:threats`'s non-determinism row and §6.3 are synced. §6.3's
   "provisionally ... replaces these numbers" paragraph became a description of the fourth dataset,
   which §6.3 had not described at all, and its opening count went from three campaigns to four. The
   peak-RSS ratio carries a host at five sites, and §`sec:baremetal` now flags the collapse itself
   with the arena count noted as pinned identically, so it cannot be read as the fairness control
   moving. §7.2 states the general form: the ordering travels and the ratio does not. The toolchain
   is named in §`sec:baremetal`'s list of differences, which now says four ways and not three, and
   `tab:testbed`'s caption lists the three protocol rows the confirmation host missed instead of
   claiming it met the column. Two caveats were added that no pass asked for: no `isolcpus` or
   `nohz_full` on the confirmation host, and the jitter sidecar was on for that campaign and off for
   the sweep, so the two hosts' paired differences are comparable and their absolute footprints are
   not.

   *Original text, kept for the reasoning:* The integration reached §1.4, §6.4, §7.2, the conclusion,
   `tab:threats`'s virtualised-host row, `tab:testbed`, `Thesis_v2.tex` and `Thesis_Plan_v2.tex`,
   and missed the abstract (l. 245), `tab:findings`'s RQ1 row ("no tail ordering is resolvable"),
   §7.1 l. 3506, `tab:threats`'s non-determinism row, and §6.3 l. 2389 (which promises the
   bare-metal run "replaces these numbers" where §`sec:baremetal` says confirmation and not
   replacement). Separately: the peak-RSS allocator effect fell from `\RssAllocDiff` 32.9--34.4 MiB
   to `\BmRssAlloc` 1.9--3.2 MiB with `thp:never,narenas:16` matched on both hosts, so the "order of
   magnitude" gap between allocator and language effects did not survive the change of host. §1.4,
   `tab:findings`'s RQ3 row and the conclusion state it with no host attached. **The non-negotiable
   claim is untouched**: both effects are real and the allocator's is still larger. Only the
   phrasing needs a host. Also §`sec:baremetal` claims the campaign "changes one thing that matters,
   the machine" while the toolchain changed too, and `tab:testbed`'s caption claims the confirmation
   host met a protocol column it missed on four rows.

3i. **CLOSED 26 August 2026, third remediation. Do not re-report.** §`sec:baremetal` now calls the
   counters "a mechanism for the operation-level result" and adds the sentence that was missing: the
   worse locality is not evidence about the resident set, because a larger footprint is a reason to
   miss cache more often and the two are related in the opposite direction. `tab:findings` reads
   "located outside the allocator by its own accounting", and `tab:threats`'s residual is narrowed to
   the honest gap, which is call-site attribution. §7.2 is rebuilt around three bounds.
   **The transferable part:** the conclusion was right and the instrument was wrong, which is the
   hardest version of this defect to spot, because nothing the sentence asserts is false on its face.
   When a pass reports "all N sites rewritten", ask what instrument the shared claim rests on.

   *Original text, kept for the reasoning:* §6.4.4
   l. 3056 ("less work and worse locality is one account of both RQ3 results at once"), §7.2 l. 3761
   ("a plausible account of a larger resident set and a faster operation at once"),
   `tab:findings`'s RQ3 status ("direction accounted for by counters") and `tab:threats`'s RQ3 row.
   An operation-scope cache-miss rate cannot explain a fixed allocator and runtime footprint, and
   §6.4.3 says in its own words that the gap is arena and runtime overhead and a fixed cost rather
   than a per-context one. If anything the arrow runs the other way: a larger resident set is a
   reason to miss cache more often. The **conclusion** is right, the direction *is* accounted for,
   but by the allocator statistics of 3j and not by the counters. The first site came in with the
   bare-metal integration (`240346a`) and the remediation propagated it to the other three, which is
   pattern 2 above. Hedged with "one account" and "plausible", so score it as an imprecision, but the
   pairing with 3j in one paragraph is what took area 5 off 5.

3j. **CLOSED 26 August 2026, third remediation, and it was the highest-value two hours in the
   project. Do not re-report.** `je_facts()` and `write_resident_table()` in
   `bench/baremetal_facts.py` emit 26 macros and `figures/tab_resident.tex`, and
   §`sec:baremetal` reports the decomposition in three readings. **The result relocated the finding**:
   arena metadata is $+2.07$ MiB and drifts $0.5\%$ across the load range (so it *measures* the fixed
   cost §6.4.3 argued by elimination), Rust holds $0.16$ MiB less live allocation, but the allocator's
   own resident bytes are $1.92$ MiB *lower* while the peak is $1.74$ MiB higher, so the difference
   sits outside the allocator, in the runtime a Rust process carries before it allocates. A third
   reading is a negative result about the guest: no arm's peak RSS spans more than $1.7$ MiB on bare
   metal, so the $31$ MiB bimodality belonged to the host. Two caveats are in the text: peak RSS is a
   `getrusage` maximum against sampled figures, and the derived row is a median of per-run differences
   so the table's column does not sum exactly (the caption says why, and pairing inside the run is the
   better statistic). **Two transferable lessons.** First, before believing a stated limitation, check
   whether the dataset already refutes it: four places said the instrument did not exist while 480
   records carried it. Second, the obvious reading of this data is wrong, so a future pass should not
   "correct" the write-up back to "metadata explains it".

   *Original text, kept for the reasoning:* Both bare-metal campaigns record jemalloc's own statistics in every run of
   their two jemalloc arms, **480 runs**, through instrumentation built for exactly this purpose
   (`cpp/bench/jestats.hpp` with a weak `mallctl`, `je_stats()` in `rust/examples/bench.rs`, system
   arms emitting nulls and never zeros). The seven fields (`allocated`, `active`, `metadata`,
   `resident`, `mapped`, `retained`, `available`) decompose the resident set into live allocation
   against arena bookkeeping against retained-but-unmapped, **which is word for word the split §7.2
   calls unresolved** and pins on an allocation profile the study supposedly lacks. No generator in
   `bench/` reads them, §6.3 does not list them among the confirmation dataset's fields, and the
   guest campaign has none of them. Medians over 90 runs per arm at steady state, MiB: `allocated`
   0.78 against 0.62, `active` 1.43 against 0.79, `metadata` 4.19 against **6.26**, `resident` 11.02
   against 9.10, peak RSS 15.08 against 16.82. **Read it before writing it up**: Rust holds *less*
   live data and *less* allocator-resident memory while its process peak is higher, so the difference
   is neither application data nor fully inside `jemalloc`, which points at the Rust runtime's own
   fixed pages. That is a sharper finding than the placeholder and it argues the same direction as
   the conclusion. Two caveats: peak RSS is a `getrusage` maximum against sampled `je` figures, and
   the C++ arm links the distribution `jemalloc` while the Rust arm builds 5.3.1 from source
   (`docs/TODO.md` Phase 11 item 3 records the confound). Cost: **two hours**, not the half day
   assigned to the profile, which answers the different question of call-site attribution.

3k. **CLOSED 26 August 2026, third remediation. Do not re-report.** The intro reads "not fully
   satisfied either" and points at the caption's itemisation. §6.3 names three kinds of addition and
   explains the system arms' nulls. §5.6 says "demonstrates on a campaign of its own design".
   **The layout lesson is the transferable part and it reverses this repository's usual rule:** the
   stranded appendix page was caused by `[H]` forbidding the following text from flowing back into the
   gap, and the fix was to *float* the table to `[ht]`, recovering the page. Every earlier length pass
   here moved tables *to* `[H]`. Diagnose the cause before choosing a direction. A second, smaller
   one: the §5.6 rewrite added two lines and stranded a chapter-tail page, recovered by tightening the
   same passage, which is the "shaving words moves nothing until a whole line comes out" trap.

   *Original text, kept for the reasoning:* Its opening
   paragraph says "Section~\ref{sec:baremetal} reports a campaign that **satisfies** it" where the
   caption four lines below lists three protocol rows the host missed. And that page carries four
   lines of text and is otherwise white, because `tab:testbed` at `[tp]` floats to the next page:
   **this stranded page is what took `\appendixCount` from 6 to 7**, so the fix is a per-table float
   change and not a prose cut. Two smaller descriptions from the same pass: §6.3 calls the
   confirmation dataset "the same record shape as the sweep and two additions" where it adds `je`,
   `jitter_ns`, `p25`, `p75`, `p9999` and `stdev` (this is why 3j was invisible), and §5.6 calls
   §`sec:baremetal` "exactly that exercise" of rerunning the campaign when it is a different design.

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
7. **Unrealised assets. Report these in the lift list, never in the grade** (rule 1: grade the
   document, not the repository). Three results exist in `bench/results-baremetal/` and reach no
   page, and the first two are each worth about half a day.
   - **The allocation profile**, 40 interval heap dumps per arm plus the Rust binary for
     symbolisation. Closes `tab:threats`'s only empty control cell and RQ3's "unexplained".
   - **The CPU result, which resolves.** On the guest it cleared Holm under one allocator and
     reversed under the other, so §6.4.3 reports it unresolved. On bare metal it is significant at
     **16 of 16 points with one sign**: Rust draws less CPU, by 0.3 to 7.6 percentage points,
     monotonically increasing with offered load, under both allocators. `baremetal_facts.py`
     computes no CPU macro at all, so this is the cheapest unreported result in the project.
   - **Jitter**, in all 32 pooled groups. RQ1 does not name it so nothing is promised, and
     `tab_jitter.tex`'s machinery has been idle since 20 August.

   Also: `refresh_thesis.sh` does not call `pool_hist.py`, so `far_tail_facts()` reads a pooled CSV
   the pipeline never regenerates. One line closes it. And the deck passed both its gates in the
   same run that regenerated the bare-metal macros while contradicting the thesis, because those
   gates check layout and punctuation and not agreement with the source.

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
- Peak resident set size is a real language effect that reproduces under both allocators and on all
  three hosts measured, at 1.4 to 3.5 MiB everywhere. **The claim that the allocator effect is the
  larger one is retired and must not be restored**: the 27 August canonical repeat measured
  1.5--2.4 MiB for the allocator against 1.4--2.5 MiB for the language, and the second bare-metal host
  agrees, so the guest's 32.5--34.3 MiB is the outlier of three. Neither effect may be dropped and the
  *ratio* between them must not be quoted without naming a host. `AGENT.md` §3 item 5 is the current
  wording. Note that `.cursor/rules/thesis-quality.mdc` still carries the retired version, so a rule
  the agent is always shown contradicts this file until the author updates it.
- The end-to-end sweep is dominated by the cross-thread handoff, and the operation is a fraction
  of a percent of it, so a median comparison on that path **cannot** bound a language effect.
  The thesis saying so is a strength.
- Rust eliminates data races and aliasing errors, **not** race conditions or lock-order
  deadlocks. The distinction is held consistently and must stay that way.
- Half grades of 4.5 encode a split between method and data, or between writing and finishing.
  Do not round them; rewrite the reasoning or leave them alone.
