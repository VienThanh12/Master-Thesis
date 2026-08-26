# Agent guide — Master's thesis repository

Instructions for AI agents (and human collaborators) working on this repository.
**Every change to thesis text, figures, data, or artefacts must be judged against the
grade criteria and quality checklist below.** The bar is submission quality, not “good
enough for a draft.”

Author: **Ha Vien** · University of Helsinki, Software study track · Nokia internship  
Title: *Performance, Safety, and Engineering Trade-offs of Rust and C++ in Nokia RAN Control-Plane Systems*

---

## 1. Document roles (read this first)

Not every PDF in this repo has the same status. **Do not treat them as interchangeable.**

| Document | Source | Status | Role |
| --- | --- | --- | --- |
| **`Thesis_Plan_v2.pdf`** | `Thesis_Plan_v2.tex` | **Reviewed — supervisor-facing** | Approved plan: gap, RQs, methodology, timeline, contributions. Keep in sync with `Thesis_v2.tex`. |
| **`Thesis_v2.pdf`** | `Thesis_v2.tex` | **Reviewed — supervisor-facing** | One-bullet-per-argument chapter skeleton for supervisor read-through, all nine chapters populated since 20 Aug 2026. This is what goes to the supervisor alongside the plan. |
| **`Ha_Vien_Mastersthesis_2026.pdf`** | `Ha_Vien_Mastersthesis_2026.tex` | **Full draft — not yet final** | Canonical long-form thesis. At 26 Aug 2026: abstract form declaring **99 pages + 6 appendix pages** (113 physical). It read 100 and 102 on 25 Aug, 105 from 23 to 24 Aug, and 99 before the RQ4 adoption-cost axes landed (`tab:adoption`) and `tab:equivalence` was placed. Six pages came back across three §6.4 passes on 25 and 26 August and none of them cost an argument: three from layout, two from cutting re-derived argument, and one from merging two single-panel figures into `fig:loadsweep`. Chapter 6 went 27 pages to 25 over the same work. See §5, *Length and layout*, for the ordering rule that made each of them pay. A snapshot, not a budget. Rich figures, generated numbers, full argument. **Everything still needs review** before submission. The filename is the UH submission format `Lastname_Firstname_Mastersthesis_Year` (ASCII), and the build writes it directly, so no second copy has to be kept in step. Called `Thesis_POC` until 19 August 2026, which is the name older notes and commits use. |
| `ai_statement.tex` | — | **Declaration in the author's name** | Required statement on generative-AI use, `\input` by `Ha_Vien_Mastersthesis_2026.tex` and `Thesis_v2.tex` before the bibliography. Shared on purpose: edit this file, never a copy. It must keep describing what actually happened, so revise it whenever the workflow changes. |
| `archive/*` | earlier variants | Superseded / stale | `plain_thesis.tex`, `thesis-vi.tex` (broken, missing bib), `thesis_wbm_full_backup.tex`, the pre-cuts `Thesis_POC.tex.bak-before-cuts`, the v1 plan PDF. Kept for reference under their original names. They resolve `figures/` and `diagrams/` from the repository root, so they no longer build in place. Do not edit unless explicitly asked. |
| Artefacts | `spec/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/` | Implementation + evidence | Must stay consistent with claims in `Ha_Vien_Mastersthesis_2026.tex`. |

### Sync rule

When you change **claims, RQs, scope, methodology, or contributions**:

1. Update **`Thesis_v2.tex`** if the supervisor skeleton should reflect it.
2. Update **`Thesis_Plan_v2.tex`** if the plan’s status, timeline, or framing changes.
3. Update **`Ha_Vien_Mastersthesis_2026.tex`** for the full argument, figures, tables, and cross-references.
4. Rebuild affected PDFs and run the verification steps in §5.

When you change **measured numbers**:

1. Regenerate via `bench/refresh_thesis.sh` (never hand-edit `figures/gen_macros.tex`,
   `figures/gen_complexity.tex`, or `figures/gen_artefacts.tex`).
2. Re-read every prose claim that cites those macros (Chapters 7–9, abstract, discussion).
3. Check `docs/ASSESSMENT.md` and `docs/TODO.md` “after bare-metal campaign” items if tail or RSS claims move.

---

## 2. Grade criteria (Finnish 1–5 scale)

The thesis is assessed on **six criteria** (simplified from the UH data-science master's
matrix). Current self-assessment is in **`docs/ASSESSMENT.md`** (durable record; keep aligned
with any grading canvas if present).

The **official CSM matrix (9 April 2024) has seven areas**, the seventh being work during the
thesis process, which no manuscript can settle. It is reproduced as issued in
`.cursor/skills/thesis-grade-csm/CRITERIA.md`; the grading procedure, the level anchors from the
four passes on record, and the build-gate script live in the same skill. Use it for any new
grading pass so passes stay comparable.

| # | Criterion | Target | Current (post-refinement) | What still blocks a 5 |
| --- | --- | --- | --- | --- |
| **1** | **Thesis objective and research questions** | Clear gap, traceable RQs, falsifiable design | **5** | Nothing outstanding. Keep RQ2 two-sided (5 inside + 5 outside guarantee). |
| **2** | **Scholarly framework and use of sources** | Auditable literature search, critical maturity, consistent concepts | **5** | Optional: replace the remaining arXiv load-bearing cite (`Bugden`) with a peer-reviewed equivalent. The `Zhang` deadlock cite is now the journal version (`zhang2026deadlock`). |
| **3** | **Research data and method** | Sound method + decision-grade data | **4.5** | **A matched bare-metal campaign.** The far tail, the counters and the allocation profiles were all collected on bare metal on 26 Aug 2026 (§`sec:baremetal`), so the instrumentation gap is closed. What is not closed is that the confirmation run changed the shard count (8 against 7), the load grid (8 levels against 14) and the repeat count (15 against 20) alongside the host, so it corroborates the main sweep and cannot replace it. Repeating it at the canonical configuration is the remaining work. |
| **4** | **Presentation of thesis results** | Honest, reproducible, figure–table consistency | **4.0** | **Figure-and-claim consistency, plus RQ1's far tail.** The eleven hand-typed values are closed and no measured value is wrong (verified 23 and 26 August, two passes running). What holds this at 4.0 instead is statements *about* the evidence: three figures misstate the result they illustrate (`fig:borrowuaf`'s "only under AddressSanitizer", diagram 07's retracted FFI framing, diagram 11's inverted fan-out label) and reproducibility claims that outrun their artefacts. The §7.4 claim is **closed** by generating `tab:taxonomy`, but two survive and one is new: §5.6 still says "every figure and table in the evaluation", which covers two hand-drawn diagrams, and §6.3 promises that every measured quantity the chapter quotes is a generated macro while §6.4.3 types two of them ("18 of the 20 paired repeats agree", "some 30 MiB low"). The median-equivalence sites are **fixed as of 23 August** in §1.4, §9 and `Thesis_v2.tex`, leaving only the abstract. Under two and a half hours of edits restore 4.5. Do not reintroduce a measured number as prose, and do not restate the median result as a bare null: name the resolved difference and call the equivalence practical. |
| **5** | **Discussion and conclusions** | Validity analysis, no over-claiming, hypotheses revisited | **5** | Maintain register: “cannot tell” ≠ “equivalent”. H1 is *ambiguous in framing*, not simply supported. |
| **6** | **Academic text** | Precise prose, no contradictions, clean structure | **4.5** | **Rewrite the abstract unaided**, then set `\abstractunaidedtrue`: until then the build prints “Not submittable”, and a document that declares itself unsubmittable is not camera-ready. That clause alone holds the criterion. Behind it, “excellent finishing polish” also wants the ninth pass's small defects closed: the clipped `fig:effects` axis label, the `fig:budget` and `fig:borrowuaf` caption overstatements, and the one derivable number still typed (the 15-repeat *p*-floor). §5.5 is conditional as of 22 August, the AI declaration no longer overstates the method, and the diagram labels are clean and gated. Housekeeping: `\censors{}{}{}` when faculty assigns examiners. |

**Overall mean (unweighted): 4.67** — criterion 3 is held at 4.5 **deliberately** until bare-metal
tail evidence exists, criterion 6 at 4.5 until the abstract is rewritten unaided, and criterion 4
returned to 4.0 in the ninth pass of 23 August. That last movement is a disagreement with the
remediation pass and is argued in `docs/ASSESSMENT.md`: no measured value is wrong any more, but
figure-and-claim consistency fails in five places and two reproducibility claims are unenforced. A
remediation edit the same day closed the three editable median-equivalence sites, and the grade was
deliberately **not** lifted for it, since the abstract and both other findings remain.
Do not round the half-grades in prose without updating the reasoning in `docs/ASSESSMENT.md`. The
class-file item is **done**: the document builds on the department's own `HYthesisML.cls`, and the
reconstructed `UH_DS_MSc.cls` in the root is no longer loaded.

**Two items are open, and neither of them is editing.** The abstract must be rewritten by the
author unaided, because in this programme it is the maturity test and a model may not touch it.
That rewrite is now overdue on substance and not only on style: the abstract still ends
"The far tail below saturation cannot be settled on a virtualised host", which §`sec:baremetal`
contradicts, and no model may fix it. A matched bare-metal repeat needs a rented machine.
The eight figure-and-caption fixes behind criterion 4 are listed in the ninth pass's outstanding
section.

The third item is **done as of 24 August 2026**: `figures/tab_taxonomy.tex` is now generated from
`faults/results/taxonomy.csv` by `write_taxonomy_table()` in `bench/plot_figures.py`, so Table 7.6
is no longer hand-maintained and §7.3's claim that table and figure come from the same log is
enforced rather than asserted. Two things about that generator are load-bearing. It groups rows on
`rust_expected`, the expectation recorded *before* the run, and not on what the compiler did:
grouping on the result would make the table's structure a restatement of it. And it refuses to
write a boundary row whose misbehaviour the runner did not record, so a cell cannot go blank
quietly. Row labels and the misbehaviour phrasing are declared in `faults/run_faults.sh` beside
the expectation the runner enforces, not in the LaTeX.

### Criterion checklist (apply to every thesis edit)

Before considering a change done, ask:

**1 — Objectives & RQs**

- [ ] Does the edit preserve the precise gap (language isolated; spec + concurrency model fixed)?
- [ ] Are all four RQs still answered in the right chapter with the right artefact?
- [ ] Does RQ2 still include the seven boundary classes (deadlock, lost update, reference-cycle leak, release-build overflow, worker-failure blast radius, seam double-free, forgotten lock guard) that can refute the premise?

**2 — Sources**

- [ ] Is every new claim cited with a defensible source?
- [ ] Are contrary results (e.g. Arvidsson tail, Emmerich slower driver) acknowledged, not omitted?
- [ ] Are distinctions (data race vs race condition; compile-time vs run-time) used consistently?

**3 — Method & data**

- [ ] Does the edit respect the frozen spec, matched pair, interleaved design, Holm correction?
- [ ] Is the virtualised host's limit stated wherever tail latency is discussed?
- [ ] If claiming significance: exact paired permutation test, pre-committed interval-vs-*p* rule (§5.5)?

**4 — Results presentation**

- [ ] Do figures, tables, and prose agree (no schematic presented as measured result)?
- [ ] Are CIs asymmetric where needed (no impossible negative latencies)?
- [ ] Does `bench/refresh_thesis.sh` regenerate every quoted number?

**5 — Discussion**

- [ ] Is evidence status stated (final vs preliminary) per RQ?
- [ ] Are threats to validity and residual risks named, not hand-waved?
- [ ] Does the conclusion avoid upgrading “not measurable” to “equivalent”?

**6 — Academic text**

- [ ] No duplicated sections; signposting clear; sentences not overloaded.
- [ ] Terminology matches earlier definitions (UECM, open-loop, coordinated omission, etc.).
- [ ] Abstract box on page 3: visually check after edits (CCS block overflows easily).

---

## 3. Non-negotiable scientific commitments

These are load-bearing for the whole thesis. **Do not weaken them in edits.**

1. **Frozen specification** — both implementations built from one language-neutral spec; forced-idiom log for unavoidable divergences (`spec/SPECIFICATION.md`).
2. **Fairness controls** — same algorithms, shard count, SplitMix64/FNV-1a hashing, jemalloc + system-allocator control, matched `-O2` / `opt-level = 2`, conformance transcripts diffed line by line.
3. **RQ2 is falsifiable** — seven in-guarantee defect classes + **seven** boundary classes; catalogue must not contain only defects Rust prevents. Two boundary classes (reference-cycle leak, release-build integer overflow) came back with the **C++ tooling ahead**; do not drop them to tidy the narrative. Two in-guarantee classes carry mechanism coverage the others do not: `use_after_move` is the only one no C++ sanitiser reports (state the `clang-tidy` caveat wherever it is quoted), and `thread_unsafe_sharing` is the only `E0277` rejection, so it is the table's evidence for the `Send`/`Sync` discipline rather than the borrow checker. `seam_double_free` is not a new class but `double_free` rewritten through `unsafe`, which is the point: keep the C++ half of that pair unchanged so the Rust column is the only thing that moves. The lock-order deadlock is detected by TSan **intermittently**, not reliably and not never. Take the rate from `faults/results/taxonomy.csv` and never from memory or from prose: it is genuinely unstable, with 4, 5, 7 and 9 hits of 12 recorded across runs, so do not let prose call it a majority or a minority without re-reading the artefact. Fix the prose to match the artefact, not the artefact to match the prose.
4. **Honest performance claims** — the end-to-end sweep is dominated by the cross-thread handoff and the operation is a fraction of a percent of it (`\BudgetCoreShareMax`), so a median comparison on that path cannot bound a language effect. The far tail is unresolvable on the KVM guest and **is** resolved on bare metal (`\BmFarTail*`, §`sec:baremetal`), where Rust's pooled p99.99 sits below C++'s at every load the two separate. Past saturation the languages *do* diverge (`\OverloadThrRatio`), and that result is resolved on the guest and reproduced on bare metal at `\BmOverloadThrRatio`. Never quote a `\Bm*` macro as if it came from the main sweep: the prefix exists so the two datasets cannot be confused.
5. **Peak RSS** — a real language effect that reproduces under both allocators, but the **allocator effect is the larger one**; do not revert to “allocator only” or drop the language effect. Quote the generated macros rather than remembered numbers.
6. **FFI** — interleaved native vs seam calls; tax bounded, not “free”; `unsafe` confined to seam; core stays `unsafe`-free.
6a. **Adoption cost beyond the seam** (`bench/adoption_cost.py`, §7.6, added 21 Aug 2026). Three axes, and two of them are easy to break by “simplifying”:
   - **Never quote the shipped binary-size ratio on its own.** g++ leaves libstdc++ to the loader and rustc links libstd in, so the default-vs-default figure compares two linkage policies. The ordering *reverses* between matched-static and matched-dynamic, so all three rows have to stay, and so does the row reporting what each dynamic build leaves on the host.
   - **Never quote the full-build time without the decomposition.** Most of the Rust clean build is third-party code; with the dependency tree warm the project's own source compiles for *less* CPU than g++ needs. Dropping the decomposition turns a real finding into the folk objection it refutes.
   - **The C++ `unsafe` cell is empty on purpose.** The language marks no such region, so a zero would be a category error, not a win for C++. Keep it as `---`.
   - Build time is the **one host-sensitive axis** here. Absolutes describe the machine, the paired ratio travels. Do not let a sync pass restore the blanket claim that RQ4 is environment-insensitive.
7. **No over-claim on Rust** — eliminates data races and aliasing errors, not race conditions or lock-order deadlocks.

---

## 4. Chapter map (`Ha_Vien_Mastersthesis_2026.tex`)

| Ch. | Title | Primary criterion |
| --- | --- | --- |
| 1 | Introduction | 1 |
| 2 | Background | 2 |
| 3 | Problem context (UECM) | 1, 2 |
| 4 | Research methodology | 3 |
| 5 | Design and implementation | 3 |
| 6 | Experimental setup and evaluation | 3, 4 |
| 7 | Discussion | 5 |
| 8 | Conclusion and future work | 5 |
| App. A–E | Abbreviations and key terms, literature search protocol, statistical design, host and campaign configuration, fault-injection example | 2, 3, 4 |

**The skeleton and the full draft no longer carry the same chapter list, and that is unresolved
as of 25 August 2026.** `Thesis_v2.tex` has nine chapters, because it keeps a standalone
`Objectives` chapter between problem context and methodology. The full draft has eight and no
such chapter: that material sits in §1.3 (research questions and hypotheses) and §1.4
(contributions, results, limitations), which is why its evaluation chapter is 6 and not 7.
Nothing is broken, since no cross-reference in the full draft points at `chapter:objectives` and
the build reports no undefined reference, but the sync rule of §1 is not satisfied, and the
author has to decide which list is canonical before either document goes to the supervisor again.
Older notes in this file and in `.cursor/rules/thesis-quality.mdc` that call the evaluation
chapter 7 or the discussion chapter 8 are using the skeleton's numbering.

`Thesis_v2.tex` mirrors its own structure as **one bullet per argument move** per chapter. All
nine of its chapters carry bullets: chapters 6–9 were filled at the author's explicit request on
20 August 2026, five bullets each, matching chapters 2–5 (chapter 1 has six). Keep that shape.
The skeleton has no appendix and needs none.

Because the results chapters quote measured values, `Thesis_v2.tex` now `\input`s the same
three generated macro files as the full draft (`gen_macros`, `gen_complexity`,
`gen_artefacts`). It therefore has to be rebuilt whenever those are regenerated, not only when
its own source changes.

---

## 5. Verification workflow (run after substantive changes)

```bash
# Parity and tests
spec/conformance/run.sh          # 3 phases: oracle, hand-written vectors, generated vectors
cd cpp && ctest --test-dir build --output-on-failure
cd rust && cargo test --release
faults/run_faults.sh             # ~4 min: two boundary cases hang by construction
faults/run_model_checking.sh     # Loom + Shuttle on the two concurrency boundary classes (fast)
faults/run_miri.sh               # Miri on the unsafe boundary class + its control (fast)
ffi/build.sh   # CAUTION: this re-measures; see the note below before running it

# Deeper checks (slower; categorical, so safe on the virtualised host)
spec/conformance/run.sh --random 60 --ops 2000   # ~800k generated ops, ~9 min
cpp/sanitise.sh                  # whole suite under ASan+UBSan / TSan / UBSan, ~50 s
rust/miri.sh                     # needs `rustup toolchain install nightly --component miri`
cpp/coverage.sh                  # gcov line coverage of the parity suite
rust/coverage.sh                 # needs `cargo install cargo-llvm-cov --locked`

# Regenerate figures/tables and rebuild canonical thesis
bench/refresh_thesis.sh

# Supervisor documents (when their sources changed)
latexmk -pdf Thesis_v2.tex
latexmk -pdf Thesis_Plan_v2.tex
```

**`ffi/build.sh` is a measurement, not just a test.** It overwrites the tracked
`ffi/results/metrics.json` and `op_cost.jsonl` with numbers from whatever host it
runs on, and those feed `tab_ffi.tex` and every `\Ffi*` macro. Run on a busy
development machine it will quietly replace the RQ4 evidence with noise — a run
during this work reported the operation round-trip as 63 µs against the recorded
12.7 µs and flipped the sign of the seam delta. If you run it only to check that it
still builds and passes, restore the evidence afterwards:

```bash
git checkout -- ffi/results/metrics.json ffi/results/op_cost.jsonl
```

`faults/run_faults.sh` is safe by comparison: its outcomes are categorical
(compile-time prevented, sanitiser-detected, undetected) and do not move with host
load.

**Prose checks (run after any writing, not just after measurement)**

```bash
./.aitells.py              # language-model fingerprints: dash asides, transition openers,
                           # promotional adjectives, sentence-length uniformity
python3 .vocab.py          # hard Latinate words (not executable, needs the interpreter)
python3 .readability.py    # sentence and paragraph load (same)
```

All three report counts rather than errors, so read them as frequency. Hard rules for thesis
prose:

All three default to `Ha_Vien_Mastersthesis_2026.tex` and take any other `.tex` file as their
one argument.

1. **No em dashes**, neither `---` nor a literal `—`. As of 17 August 2026 `.aitells.py`
   reports four dash hits in the thesis source, all correct typography (one compound proper
   name, three numeric ranges). If that number rises, the new ones are yours.
2. **No semicolons.** Use a full stop, a comma, a colon, or two sentences instead. Semicolons in
   thesis prose read as stiff and are easy to spot on review.

The full style constraint is in the prose-style section of `.cursor/rules/thesis-quality.mdc`.

**Both rules cover diagram labels as well**, and `diagrams/check_labels.py` is the gate over that
surface, run by `refresh_thesis.sh` beside the other two. It walks every text run in the diagram
sources and refuses em dashes, spaced en dashes and prose semicolons. Its scope is computed from
the documents themselves, every diagram a `.tex` file includes or `build_deck.py` names, so a
diagram no document uses is listed as unchecked and starts being gated the moment one includes it
(`--all` checks every source). Verbatim code is exempt through an explicit list in the script, not
a heuristic. Three things to know when it fails. Diagrams 20 to 29 are generated, so fix
`diagrams/build_new_diagrams.py` and not the SVG. The generator writes its dashes as `\u2014`
escapes, so grep for the escape. And **the gate checks punctuation, not sense**: removing a dash
or a semicolon frequently leaves a comma splice or a label that overruns its panel, and nine of
them did in the pass that introduced the gate, so re-render and read the figure afterwards.

**Both rules cover the slide deck as well**, which is why `build_deck.py` ends with a
`check_prose_style` gate beside `check_layout`. It walks every text run, table cell, and grouped
shape in the saved deck, and refuses em dashes, spaced en dashes, and semicolons. Three things to
know before editing deck prose. The source writes its dashes as `\u2014` escapes, so grep for the
escape and not for the character or a search comes back empty on a deck that is full of them. An
en dash stays legal between numbers (`1.9–3.4 MiB`) and is refused when spaced, because that is an
aside. And a generated table cell holding `---` marks a value that does not exist, which `detex()`
turns into `n/a` rather than the em dash the thesis table prints, so fix such a cell in the deck's
converter and never by hand-editing `figures/tab_*.tex`. The semicolon check has no exception for
source code because no slide shows any. Add one deliberately if that changes.

**Length and layout (read before changing either)**

The abstract form's page count is **computed by the class, not typed in**: `HYthesisML.cls`
counts `\mainmatter` pages into `\pagesCount` and appendix pages into `\appendixCount`, and
writes both to `build/Ha_Vien_Mastersthesis_2026.aux`. Read the declared length from there
rather than from the PDF's physical page total, which also includes front matter:

```bash
rg 'gdef.(pagesCount|appendixCount)' build/Ha_Vien_Mastersthesis_2026.aux
```

`\pagesCount` counts the body **plus** the AI statement and the bibliography, so a reference-list
change moves the declared figure. It currently reads 99 with 6 appendix pages (113 physical).

**Under 100 is a preference, not a rule.** The author set it as the target on 19 August 2026 and
may revise it. No University of Helsinki or CSM requirement is behind it, and nothing in the
grade criteria of §2 rewards a shorter thesis. So when length and substance conflict, substance
wins: the bare-metal tail campaign that criteria 3 and 4 wait on will *add* results, figures, and
discussion, and it should be added without first hunting for pages to sacrifice. Report the new
`\pagesCount` and let the author decide whether to spend the difference.

Two traps, both found by measurement on 19 August 2026:

- **Line spacing cannot be set in the preamble.** The class's `\maketitle` calls
  `\onehalfspacing` itself, so a preamble setting is silently overwritten and the PDF comes out
  byte-identical. Body spacing is therefore selected by the `\singlespacing` **after
  `\mainmatter`**. The class's own comment calls 1 to 1.5 the normal range for a one-column
  computer-science thesis, so single spacing is inside the template's norm. Do not "fix" the
  commented-out spacing lines back into the preamble.
- **`[H]` on tables is deliberate, and only a *per-table* change to it pays.** Converting all 23
  tables to `[htbp]` at once made the document *four pages longer*, so never repeat that. The
  mechanism worth knowing is that `[H]` forbids the text after a table from flowing back to fill
  the gap when the table does not fit, which is where most short pages come from. Converting one
  table at a time and rebuilding after each does work: on 25 August 2026 `tab:taxonomy` moved to
  `[tp]` for a whole page, and `tab:equivalence`, `tab:contention`, `tab:budget` and
  `tab:adoption` closed short pages at no cost. Two were measured and reverted, so do not retry
  them: `tab:defectmap` at `[tp]` *added* a page, and `tab:findings` at `[H]` was mixed. After any
  such change, check that no converted table drifted past the page that cites it.

Measured cost of the layout settings, cumulative, at unchanged content: 1.5 spacing 22 pages,
full-width figures 4, `twoside,openright` 15 blank versos, loose heading and float gaps 3, and a
12pt bibliography with default item gaps 4. That is 48 pages of layout, so the settings are worth
keeping whatever the target is, and any of them can be handed back deliberately if the author
prefers the looser look to the shorter document.

If pages are genuinely needed, take them in this order, because it costs no argument: the short
pages `[H]` strands, and the chapter tails that spill a few lines onto a near-empty page. Rank
pages by ink coverage with PyMuPDF (installed, see `pdfpreview.py`) rather than guessing from the
source, and diagnose each short page before editing it, because the two causes take opposite
fixes. A page whose gap sits below its last line of text, with a table opening the next page,
wants a float change. A page holding nothing but the tail of a chapter wants lines removed
upstream.

The contrast between the two is the part worth remembering. The 875 words of duplication cut on
24 and 25 August recovered **no** declared pages on their own, because the freed lines were
absorbed by float whitespace and by the chapter-opening rule. The layout pass that followed
recovered three, from five per-table float changes and 160 words taken off two chapter tails. Cut
duplication because it makes the thesis read better, not because it will shorten it.

The §6.4 pass of 25 August qualifies that, and the qualification is about *order* and not about
the rule. It removed 420 words of restatement and recovered two declared pages, 102 to 100, which
looks like a counterexample and is not one. The first 375 words took one page off downstream and
left body page 70 holding four lines instead of eighteen, and 45 more words then closed that page
outright and took the chapter from 27 pages to 26. So the sequence is what pays. Shorten the
chapter tails by layout first, then cut duplication, and a stranded page that was previously
immovable becomes cheap. Cutting the same 420 words before the layout pass would have bought
nothing. What still does not work is cutting duplication *instead of* fixing layout.

A second §6.4 pass on 26 August found the prose floor. It removed 373 more words, all of it
framing that announced what the next sentence said, and recovered **zero** pages: the freed lines
went into float whitespace, and the chapter stayed at 26 pages with the document at 100. §6.4 was
by then **18.6 pages of prose against 8.0 pages of floats** across 22 floats, which is the
diagnosis: a further page had to come from a float and not from a sentence. **Do not shave §6.4
prose expecting pages from it.**

The third pass took that page from a float and confirms the ordering rule a third time.
`fig:latency-load` and `fig:throughput-load` were two single-panel plots against the same $x$
axis, which the prose already read as a pair, so `fig_load_sweep()` in `bench/plot_figures.py` now
emits them as one two-panel figure and the thesis includes that instead. Chapter 6 went to 25
pages and the document to 99. Four things are worth carrying:

- **The two single-panel generators stay.** `build_deck.py` places them side by side on their own
  slide, where two images are what the layout wants. Deleting them breaks the deck.
- **The merge alone did not deliver the page.** It left body page 69 holding a single line, and
  about twenty words off the §6.4.8 closing paragraph then closed it. Same shape as the 25 August
  pass: the structural change strands a nearly empty tail page, and a small prose cut collects it.
- **Nothing measured moved.** `gen_macros.tex` and every `tab_*.tex` came back byte-identical, so
  the figure count is the only thing that changed. Re-check that after any figure work.
- Figure numbering shifts when a figure is removed, so re-run the citation-distance check. All 21
  remaining chapter 6 floats sit within two pages of a citation.

A fourth pass de-duplicated §6.4's in-place bounding passages against §7.6, which bounds nearly
every one of them a second time (the p99.99 instrumentation gap, the microbenchmark's narrowness,
RQ3's unexplained origin, the `jemalloc` peak-RSS bimodality, the primitives ruled out alone). It
took 154 words and again recovered nothing. Total across the four passes: **960 words out of §6.4,
27 pages to 25**, and the last two passes contributed no pages at all.

**The durable diagnosis, measured 26 August: §6.4 reads long because of how it is divided, not
because of how it is written.**

| RQ | Words | Share | Subsections (before the 26 Aug consolidation) |
| --- | --- | --- | --- |
| RQ1 | 2986 | 39% | **five** (§6.4.1 to §6.4.5) plus 12 of the 21 floats |
| RQ2 | 2507 | 33% | one (§6.4.7), eight paragraphs of per-class narration |
| RQ3 | 523 | 7% | one |
| RQ4 | 1513 | 20% | one |

RQ1's answer arrived in five installments with no single place stating it, and RQ1 and RQ2 together
are 71 per cent of the section. That was the reading problem, and no amount of word-shaving touched
it. RQ2's 33 per cent share is untouched and is the next place to look, but most of that subsection
is protected by §3 item 3.

**That was fixed on 26 August by consolidating §6.4 to the grouping `Thesis_v2.tex` already uses.**
The skeleton organises this chapter as five argument bullets, and the full draft's eight
subsections did not match it. §6.4 is now **five subsections**: below saturation (RQ1, RQ3), past
saturation (RQ1), resource use (RQ3), safety (RQ2), migration (RQ4). RQ1 went from five subsections
to two. Nothing was deleted, no claim, number or float changed, and the chapter stayed at 25 pages,
so this is a **readability** change and not a length one.

Two mechanics matter if this is ever revisited:

- **Demoted labels keep their anchors.** `sec:budget` and `sec:contention` moved from
  `\subsection` to `\paragraph` and kept their `\label`. `\ref` now returns the *enclosing
  subsection* number, so `Section~\ref{sec:budget}` prints 6.4.1 while its `.aux` entry still
  records page 51 and anchors to `paragraph*.44`. PDF links therefore land exactly on the
  paragraph, and only the printed number is coarser. That is tolerable here because all 11
  `sec:budget` references name their target in the sentence. Check that before demoting anything
  else.
- **Merging creates circular references.** Two pointers became self-references the moment their
  subsection absorbed the target (the sweep paragraph citing `sec:perfresults`, and the overload
  prose citing `sec:contention`). The build does not catch these, since the labels resolve fine.
  After any merge, grep each merged range for references to labels now inside it.

Still unresolved, and larger: the skeleton has nine chapters to the draft's eight (§4).

The one float lever left is the author's call because it drops a reader aid rather than a claim:
`tab:taxonomy` and `fig:taxonomy` show the same $14$ outcomes from the same log and cost about 1.1
pages between them. Criterion 4 sits at 4.0 on figure-and-claim consistency, so weigh that before
dropping either.

One trap belongs with the tails. Once the preceding page is full, shaving words moves nothing
until a whole *line* comes out, and the final word of a chapter can sit alone on a page while its
own page is 98 per cent full. Fix that by removing a line from the paragraph, not by rewording
its last sentence.

**What is left after 25 August 2026:** most of the remaining stranded whitespace sits at chapter
boundaries, which is `twoside,openright` behaving as intended rather than a defect.

The §6.4.8 tail page is **closed** as of the §6.4 duplication pass, and how it closed is the
transferable part. It had resisted a direct attack, because closing it needed about four lines out
of the RQ4 adoption-cost prose and every candidate there is protected by §3 item 6a: the three
footprint rows, the build-time decomposition, and the empty C++ `unsafe` cell. That constraint
still holds. What worked instead was taking the lines from *upstream* restatement in §6.4.1,
§6.4.6 and §6.4.7, which pulled the tail forward without touching a protected claim. When a
stranded tail page has no spendable lines of its own, look further up the same chapter before
concluding it cannot move. Do not trade a protected claim for a page.

Compressing load-bearing prose is the last resort. The sentence and paragraph *scans* return only
structural pairs: a hypothesis stated in §1.3 and revisited in §7.3, the abstract against the
conclusion, and prose against its own figure caption. Those are the layering working, not
repetition.

What the scans miss, and the §6.4 pass of 25 August found by reading, is an argument re-derived
from scratch at each site instead of cross-referenced. No two of those passages share enough
wording to pair, so a scan cannot see them. The largest was the claim that this host cannot
resolve the far tail, stated eight times in chapter 6 and derived in full at five of them. The
same shape held for the borrow-checker disclaimer, the environment-insensitivity definition, and
§6.4.6's closing synthesis, which restated a subsection that §7.2 and Table 7.1 then restate
again. **Search for repeated *arguments*, not repeated sentences.** Two things are now closed
that were open: the "N things bound what this licenses" openings have been varied, including the
one that read "Three things *again* bound what the finding licenses", and §6.4's opening no longer
inventories six resolved findings that Table 7.1 tabulates a chapter later.

What is deliberately **not** cut in §6.4.7, and should stay uncut: the boundary group's
"in both languages" clauses. They read as repetitive and they are RQ2's falsifiability evidence,
which is criterion 1's blocker.

**Acceptance gates**

- `build/Ha_Vien_Mastersthesis_2026.log`: **zero errors**, zero undefined references/citations. `.latexmkrc` keeps
  every LaTeX intermediate in `build/`; the PDF and its SyncTeX index still land at the root.
- `./.aitells.py` on every file whose prose changed: no em-dash asides introduced; no semicolons
  introduced.
- Figure/table macros in prose match `figures/gen_macros.tex`.
- No figure contradicts its table (see `docs/ASSESSMENT.md` refinement pass for past failures).
- `diagrams/check_labels.py` reports “Diagram labels: no em dash, dash aside, or semicolon”. Run by
  `refresh_thesis.sh`; re-render and read any figure whose label you changed.
- `build_deck.py` rebuilds and reports both “Layout: all added shapes inside the template content
  band” and “Prose style: no em dash, dash aside, or semicolon on any slide”. Either failure exits
  non-zero, and both are reported in the same run so one rebuild shows everything that is wrong.
- If abstract changed: visually inspect page 3 (abstract form + CCS + keywords).
- Report `\pagesCount` from the `.aux` after any substantial addition. Under 100 is the author's
  **current working preference, not a requirement**, so treat it as a number to surface and not a
  gate to enforce. See *Length and layout* above before trading content for it.

---

## 6. What agents should not do

- **Do not** treat `Ha_Vien_Mastersthesis_2026.pdf` as supervisor-approved. The submission filename says nothing about review status: only `Thesis_Plan_v2.pdf` and `Thesis_v2.pdf` are in that bucket today.
- **Do not** hand-edit generated files under `figures/` except source diagrams in `diagrams/`.
- **Do not** transcribe measured numbers into `build_deck.py`; it reads them from the generated artefacts and fails loudly when one is missing.
- **Do not** leave an em dash or a semicolon where a reader can see it, in the thesis source or on a slide. The deck build refuses to pass one.
- **Do not** claim testbed-grade tail latency from the virtualised host.
- **Do not** remove boundary defect classes or sanitiser-only C++ outcomes to tidy the narrative.
- **Do not** turn `Thesis_v2.tex` into prose or let a chapter drift off five bullets. It is a bullet-per-argument skeleton on purpose, and it is supervisor-facing.
- **Do not** commit secrets, Nokia-internal identifiers, or confidential traces.
- **Do not** create git commits unless the author explicitly asks.

---

## 7. Key reference files

| File | Use |
| --- | --- |
| `docs/ASSESSMENT.md` | Full criterion-by-criterion grading notes and blockers |
| `.cursor/skills/thesis-grade-csm/` | Grading skill: the official seven-area CSM matrix, calibration anchors and discounted false positives from past passes, and `scripts/texaudit.py` for build, cross-reference, bibliography and placeholder gates |
| `docs/TODO.md` | Phase checklist, bare-metal prep, post-campaign re-check list |
| `docs/LITERATURE_NOTES.md` | Citation upgrades and literature gaps |
| `bench/TESTBED.md` | Bare-metal protocol (only path to criterion 3/4 → 5 on tail) |
| `bench/artefact_facts.py` | Generates `figures/gen_artefacts.tex`: record sizes (compiled probes), parity-suite coverage, conformance campaign size, FFI seam size, **fault-catalogue outcomes** (deadlock detection rate, lost-update counts, undetected-class count) and **suite size** (C++ binaries, Rust tests). Anything measured that no campaign log holds belongs here, not in the prose. The deadlock rate is read from `taxonomy.csv` *and* recounted from the per-run logs, and a mismatch is a hard error |
| `bench/complexity.py` | Generates `figures/tab_complexity.tex`, **`figures/tab_loc.tex`** and `gen_complexity.tex`. The `CONCERNS` partition decomposes the line-count gap and the script refuses to write the table unless every measured file is assigned to exactly one row and each column sums to its measured total. That check is why Table 5.4 can no longer go six lines short of its own printed total |
| `diagrams/check_labels.py` | Prose-style gate over diagram labels, the third surface beside `.aitells.py` and the deck's `check_prose_style`. Scope computed from the documents; run by `refresh_thesis.sh` |
| `bench/adoption_cost.py` | Generates `figures/tab_adoption.tex` + `gen_adoption.tex`: RQ4's build time, static footprint, and third-party surface. `--measure` re-times the builds and records to `bench/results/adoption-*.json`; **without it, build time is replayed from the record** and only the deterministic axes are recomputed. `refresh_thesis.sh` calls it without `--measure` deliberately (see §3 item 6a and the `ffi/build.sh` warning in §5) |
| `spec/SPECIFICATION.md` | Fairness baseline; freeze before implementation changes. §11.4–11.5 cover the reference model, generated vectors, sanitisers, Miri and coverage |
| `spec/conformance/model.py` | Independent Python implementation of the spec; the oracle behind the generated vectors. Never derive its expectations from `cpp/` or `rust/` |
| `faults/results/model_checking.md` | Loom/Shuttle outcomes for the boundary classes (RQ2's "at what stage and cost") |
| `README.md` | Repo layout and quick start |

---

## 8. Supervisor submission bundle (current)

When preparing material for **Keijo Heljanko** (supervisor) and Nokia instructors
(**Christoph Luneburg**, **Petteri Kotimaa**):

1. `Thesis_Plan_v2.pdf` — plan, status, timeline (dated; status table must match repo reality).
2. `Thesis_v2.pdf` — chapter skeleton, all nine chapters populated (35 pages).
3. Optionally reference `Ha_Vien_Mastersthesis_2026.pdf` as the **working full draft** (clearly labelled not final).

Port supervisor feedback into `Thesis_v2.tex` and `Ha_Vien_Mastersthesis_2026.tex` in the same
edit pass so the two do not diverge.

---

*Last updated: 26 August 2026. Four length passes on 24, 25 and 26 August took the declared figure
from 105 to **99 pages** and removed no argument. The last three were scoped to §6.4 at the
author's request: 793 words of re-derived argument and framing out, the §6.4.8 tail page closed
twice from upstream, `fig:latency-load` and `fig:throughput-load` merged into `fig:loadsweep`, and
chapter 6 down from 27 pages to 25 with all 21 of its floats still within two pages of a citation.
The lesson is in §5 and it is about ordering rather than volume: layout first, then duplication,
then a float, and each step strands the tail page the next one collects. The middle pass of the
three removed 373 words and bought nothing, which is what located the prose floor. The first cut
875 words of duplication, found by
scanning every sentence and paragraph pair in the document rather than by reading: a claim was
typically stated in three places, such as the environment record in §4.5, §6.1 and §6.3, the
pairing rule in §4.4, §7.6 and Table 7.3, and the frozen specification's contents in §4.3, Table
4.2 and §5.1. Chapter 7's related-work section lost the most, since it re-narrated Chapter 2's
four strands and then re-told the five vendor theses that Table 7.2 already tabulates. Every one
of the 109 citation keys survived, because the technique was to keep the citation clusters and
delete the prose narrating them. Those 875 words bought no pages at all, which is the finding to
carry forward: cut duplication for readability, and expect layout to decide length. The second
pass did the length work, and its findings are in §5: `[H]` pays to change one table at a time
and never in bulk, and 160 words off two chapter tails deleted two pages outright. The standing
two blockers are untouched by any of it. Two defects were found on the way and neither is fixed.
The abstract still says safe Rust rejects "all five injected memory-safety and data-race defect
classes" with "five further classes" outside, where §1.4, §6.4.7, Table 6.9, Table 7.1 and the
conclusion all say seven, so it is the last place in the thesis carrying the old catalogue size,
and a model may not fix it. And §4 now records the second: the skeleton and the full draft
disagree on the chapter list, which the sync rule of §1 is supposed to prevent.*

*The tenth grading pass, 26 August 2026, held every area where the ninth left it and found no wrong
measured value either, so that is now two passes running. It confirmed the taxonomy generator closed
§7.4's claim, and found two more of the same defect class. §6.3 promises that every measured quantity
the chapter quotes reaches the page as a generated macro, and §6.4.3 types two: "18 of the 20 paired
repeats agree" and "some 30 MiB low", which together are the whole justification for reading peak RSS
under jemalloc from its interval. `\OverloadThrAgree` is the same quantity for the overload table and
is generated, so the fix is the generator and not the wording. And `\SatKnee` is an achieved-throughput
value (`plot_figures.py:1652`) used in §6.4.1 and in `fig:loadsweep`'s caption as though it were a
position on the offered-load axis, which prints as tracking to 336 kops/s and saturating at 335. The
pass also put the abstract's catalogue size on the grading record: with "five" and "five" against the
body's seven and seven, plus the median claim and jitter, the unaided rewrite now has four items to
settle rather than one. Area 6 was **not** deflated for it, on the grounds that the build refuses to
call the document submittable and one rewrite closes all four, but submitted as it stands that
abstract puts area 6 at 4.0 and area 4 follows. See the tenth pass in `docs/ASSESSMENT.md`.*

*The ninth grading pass found no wrong measured value anywhere, the
first pass on record to do so, and verified that the generated layer the remediation pass installed
still holds (`gen_artefacts.tex` byte-identical, `tab:loc`'s three column sums asserted, about
thirty macros checked against their tables). It moved criterion 4 from 4.5 down to 4.0 on a
different defect class: figures and captions that misstate the result they illustrate, two
reproducibility claims the artefacts do not enforce, and three summary passages that call the
median equivalent where §7.5.1 resolves it. Every item is editing except the standing two, and the
durable fix is to generate `figures/tab_taxonomy.tex`, the last results table in the thesis with no
generator behind it. See the ninth pass in `docs/ASSESSMENT.md`.*

*The eighth grading pass held every area where the seventh left it
and found one new defect, a false sentence about the method in `ai_statement.tex`. A remediation
pass the same afternoon closed thirteen of its fifteen items and moved criterion 4 from 4.0 back
to 4.5. The durable part of that work is that three classes of defect are now generated rather
than typed: the fault-catalogue and suite figures through `artefact_facts.py`, Table 5.4's
breakdown through `complexity.py` with its column sums asserted, and diagram-label style through
the new `diagrams/check_labels.py`. `tab:equivalence` was placed in §7.5.2, which took the
declared length to 105 pages. Two items remain and neither can be edited away: the abstract, which
the author must rewrite unaided, and the bare-metal campaign.*

*The pass before, on 21 August 2026, measured the three RQ4 adoption-cost axes
(`bench/adoption_cost.py`, `docs/TODO.md` Phase 11 item 7) and wrote them into §7.6, Table 8.1, §8.4,
§5.4 and the conclusion. Declared length moved 99 to 104 pages. Four passages that called RQ4
environment-insensitive without qualification were corrected, since build time is a timing
measurement. The preceding pass, on 20 August, filled `Thesis_v2.tex` chapters 6–9 at the author's
request (five bullets each, 24 pages to 35) and the skeleton began reading the generated macro
files. The pass before that, on 19 August, renamed `Thesis_POC.tex` to
`Ha_Vien_Mastersthesis_2026.tex`, retired the separate submission copy, and brought the declared
page count from 105 to 99 almost entirely through layout. Revise this file when supervisor review
status, grade blockers, document roles, or the length preference change.*
