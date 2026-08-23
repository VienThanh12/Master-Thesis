---
name: thesis-grade-csm
description: >-
  Grades a master's thesis against the official Computer Science (CSM) seven-area assessment
  matrix on the Finnish 1-5 scale, area by area, naming the descriptor clause that caps each
  grade and the cheapest work that lifts it. Produces a grading canvas and a dated pass in
  docs/ASSESSMENT.md. Use when the user asks what grade the thesis would get, how an examiner,
  supervisor, or opponent would assess it, what blocks a 5 in an area, whether an edit protects
  the grade, or for an examiner-style review of Ha_Vien_Mastersthesis_2026.tex, Thesis_v2.tex,
  Thesis_Plan_v2.tex, or an external manuscript.
---

# Grading a thesis against the CSM matrix

The matrix is in [CRITERIA.md](CRITERIA.md). Read it before grading; do not grade from memory of
what a good thesis looks like. Level-boundary anchors from earlier passes, the checks with the
highest historical yield, and the false positives to discount are in
[CALIBRATION.md](CALIBRATION.md).

## Two modes

| Mode | Subject | Record |
| --- | --- | --- |
| **Own thesis** | `Ha_Vien_Mastersthesis_2026.tex` unless told otherwise. Read `AGENT.md` first for document roles and non-negotiable claims. | Canvas plus a dated pass appended to `docs/ASSESSMENT.md`. |
| **External manuscript** | A PDF or `.tex` the author is reviewing or opposing. | Canvas only. Never write another author's thesis into `docs/ASSESSMENT.md`; that file is the record for this thesis. |

## The three rules that govern every grade

1. **Grade the document, not the repository.** An examiner sees the manuscript. Evidence that
   exists in `spec/`, `bench/`, `faults/`, or `ffi/` but is not visible in the text earns
   nothing. Where the gap is large, report it as an unrealised asset in the lift list rather
   than folding it into the grade.
2. **A level is awarded only when every clause of its descriptor holds.** Quote the clause that
   fails. "Area 6 is 4.5 because level 5 asks for technically camera-ready with excellent
   finishing polish, and the build has a float overflowing its page" is a grade. "Area 6 feels
   like a 4.5" is not.
3. **Form your own view before reading the previous passes.** `docs/ASSESSMENT.md` records four
   passes and one of them disagreed with its predecessor. Read it after you have graded, then
   state agreement or disagreement per area explicitly. Do not let the author's self-assessment
   set the number.

## Workflow

Copy this checklist and work through it:

```
- [ ] 1. Establish the document set and build state
- [ ] 2. Mechanical evidence pass
- [ ] 3. Read the thesis for argument, per area
- [ ] 4. Assign each grade clause by clause
- [ ] 5. Write carries and caps per area
- [ ] 6. Rank the lifts by cost
- [ ] 7. Reconcile with previous passes
- [ ] 8. Emit canvas and record
```

### 1. Establish the document set and build state

Identify which file is being graded and whether its PDF is current. A grade that describes a
stale build is worthless: check the `.log` timestamp against the `.tex`, and rebuild with
`latexmk -pdf <file>.tex` if they diverge. For the own-thesis mode, `AGENT.md` §1 states which
documents are supervisor-facing and which are drafts; a draft is not graded as if it were
submitted, but say what standard you applied.

### 2. Mechanical evidence pass

Run the audit script first, because it costs seconds and it finds the defects that cap areas 4
and 6:

```bash
.cursor/skills/thesis-grade-csm/scripts/texaudit.py Ha_Vien_Mastersthesis_2026.tex --macros figures/gen_macros.tex
```

It reports LaTeX errors, undefined references and citations, overfull boxes, floats too large,
page count, bibliography composition and cite coverage, uncited and undefined keys, preprint
entries, float labels never referenced from the body, placeholder markers, and prose lines that
appear to carry a hand-typed measured number. Exit code is non-zero when a hard gate fails. For a
manuscript that exists only as a PDF, skip the script and take the same evidence by reading, in
the order given in `CALIBRATION.md`.

Then the two checks no script can do:

- **Every number in the results prose against the table it describes.** This has the highest
  yield of any check in the file. In one external manuscript roughly 28 quoted values
  disagreed with their own tables, one of them reversing the direction of a change. Sample at
  least a dozen values, and if any disagree, check all of them.
- **Every figure against the result it illustrates.** A schematic presented as measured data,
  or a diagram left stale after the claim moved, is an area 4 and area 6 defect at once.

For prose quality run the repo's own tools rather than judging by eye:
`./.aitells.py`, `./.vocab.py`, `./.readability.py`.

### 3. Read the thesis for argument, per area

Areas 1, 2, and 5 cannot be audited mechanically. Read for:

- **Area 1**: is the gap located in a named flaw of specific prior work, or asserted? Does every
  research question have a stated method, artefact, and metric? Are the questions answerable as
  worded, and do the reported metrics match the ones the question names?
- **Area 2**: are contrary and negative findings engaged, or is the review a summary? Are
  concepts defined once and then held to? What is the peer-reviewed share of load-bearing cites?
- **Area 5**: are hypotheses revisited individually, including any the data refuted? Is validity
  analysed by type with residual risk named? Is "cannot tell" kept distinct from "equivalent"?
  Is ethics discussed at all?

### 4. Assign each grade clause by clause

For each area, walk the descriptors upward until one fails, and record which clause failed. Area
5 has a merged 3-4 cell, so a 3 or 4 there must be argued from the sub-factors.

**Half grades** are permitted and are used in this record, but only to encode a split that the
matrix cannot express, and the split has to be named: area 3 sits at 4.5 because the method
reads at 5 and the data at 4. Never round a half grade away without rewriting the reasoning
behind it.

**Area 7 is `n/a`.** Say why: nothing in a manuscript settles feedback uptake, independence, or
schedule adherence.

Report the unweighted mean of the assessable areas, state that it excludes area 7, and note that
the matrix makes overall impression the verdict and allows compensation across areas, so the
mean is an aid. If any area would be 0, say plainly that the proposed grade is fail.

### 5. Write carries and caps per area

Two paragraphs per area, in this shape, because it is what past passes used and what makes a
grade actionable:

- **Carries it**: the specific, verifiable things that earn the level, with counts where counts
  exist (entries, pages, repeats, coverage, corrected defects).
- **Caps it**: what blocks the next level, phrased as the failing clause plus the observation.

Both should be concrete enough that a reader can check them without your help. "Strong
methodology" is not evidence; "exact paired permutation over every sign assignment, Holm family,
attainable p-floors quoted, and a reading rule fixed in advance that costs the author a row
rather than rescuing one" is.

### 6. Rank the lifts by cost

A table of the work that raises a grade, ordered by cost, each row naming the areas it moves.
Distinguish three kinds:

1. **Editing** can fix it (hours). Prose, figures, alignment between claim and evidence.
2. **Analysis on data already in hand** can fix it (a day). This category is easy to miss and
   was the whole substance of the second pass: three criticisms said to need new measurement
   were answerable from the existing dataset.
3. **Only new measurement** can fix it. Name the instrument and what it buys.

### 7. Reconcile with previous passes

For the own thesis, compare against the latest pass in `docs/ASSESSMENT.md` area by area. Where you
disagree, say so and give the reason; a disagreement recorded honestly is worth more than a
number that matches. Check whether items listed as outstanding in the previous pass are done,
still open, or now moot.

### 8. Emit canvas and record

**Canvas.** Read `~/.cursor/skills-cursor/canvas/SKILL.md` before writing any `.canvas.tsx`.
Write to `~/.cursor/projects/home-vienha-thesis-local/canvases/` using the established naming:
`thesis-grade-csm-<mon><dd>.canvas.tsx` for this thesis (add `-rev2` for a second pass the same
day), `grade-<topic>-thesis.canvas.tsx` for an external manuscript. Structure that has worked:

- A seven-row matrix table: area, title, grade, carries, caps, with tone per row.
- Headline stats: mean of the assessable areas, page count, count of areas at 5.
- The ranked lift table with cost and the areas each row moves.
- One section per finding that needed evidence, for example claimed against tabulated values as
  a paired bar chart, or the build-gate results.
- A closing callout naming the single blocking item.

**Record.** For the own thesis, append a pass to `docs/ASSESSMENT.md` in the existing form: heading
`## Nth pass — DD Month YYYY`, what the pass covered and from what source, a summary table with
the previous pass beside the current one, per-area notes, what was fixed during the pass, and
what is outstanding. Keep the canvas and `docs/ASSESSMENT.md` in step, and treat the file as the
durable copy. If the grade of any area moved, update the criterion table in `AGENT.md` §2 too.

**Chat summary.** Lead with the mean and the one item that blocks the most. Then per-area
movement, then the lift list. No preamble.

## Grading discipline

- **Do not inflate.** Level 5 in this matrix is demanding by design: area 1 asks for a topic
  significant enough to warrant a scientific publication, area 6 for camera-ready presentation.
  A generous grade is a useless grade, since the point of the exercise is to find what an
  examiner will find first.
- **Do not deflate on mechanical noise.** Check `CALIBRATION.md` for the false positives that
  have wasted a pass before, hyphenation variants being the standard one.
- **Separate the unfinished from the unfinishable.** Work that editing can fix belongs in the
  lift list. Work that no editing can fix, because it needs an instrument the author does not
  have, belongs in the grade as a stated ceiling.
- **Quote generated macros, not remembered numbers.** When the grading text cites a measured
  value from this thesis, cite it through `figures/gen_macros.tex`. If a number in the grade
  came from your reading rather than from a generated artefact, say so.
- **No em dashes if any output lands in a `.tex` file.** The grading canvas and `docs/ASSESSMENT.md`
  are internal notes and exempt, but anything ported into thesis prose must follow the prose
  rules in `.cursor/rules/thesis-quality.mdc`, and `./.aitells.py` must be run on the file after.

## Additional resources

- [CRITERIA.md](CRITERIA.md): the official seven-area matrix, all levels, as issued.
- [CALIBRATION.md](CALIBRATION.md): level anchors from earlier passes, high-yield checks,
  false positives, and this thesis's standing blockers.
- `scripts/texaudit.py`: mechanical build, bibliography, and cross-reference audit.
