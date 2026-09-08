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
| **`Thesis_v2.pdf`** | `Thesis_v2.tex` | **Reviewed — supervisor-facing** | Supervisor read-through of the eight-chapter argument. Chapter 1 is the full introduction from the draft (copied 27 Aug 2026, cross-refs retargeted). Chapters 2 to 8 keep five argument paragraphs each, as plain prose rather than itemize. Cut from nine chapters to eight on 26 Aug 2026, when the standalone `Objectives` chapter was folded into the introduction to match the draft (§4). Carries **15 of the draft's 22 figures** since 7 Sep 2026, with a list of figures in the front matter (§4). This is what goes to the supervisor alongside the plan. |
| **`Ha_Vien_Mastersthesis_2026.pdf`** | `Ha_Vien_Mastersthesis_2026.tex` | **Full draft — not yet final** | Canonical long-form thesis. At 26 Aug 2026, after the bare-metal campaign and a priced length pass: abstract form declaring **101 pages + 6 appendix pages** (115 physical). **Re-measured 31 Aug 2026 it declares 95 + 12 at the same 115 physical**, because the appendix list of §4 has grown to seven: the total is unchanged and six pages sit on the other side of the `\appendix` boundary. Read the split from the `.aux` and never from this line. It peaked at 105 when the `je` decomposition landed, and the length pass took it to 101 by the only two levers that return anything (a `\scriptsize` bibliography and §5.4.1's state-machine narration, whose two semantic commitments moved to §5.5). **Do not go looking for more: §5, *Length and layout*, now records every lever measured, and all but the bibliography return zero.** Before the campaign, the same day, it read 99 + 6 (113 physical). It read 100 and 102 on 25 Aug, 105 from 23 to 24 Aug, and 99 before the RQ4 adoption-cost axes landed (`tab:adoption`) and `tab:equivalence` was placed. Six pages came back across three §6.4 passes on 25 and 26 August and none of them cost an argument: three from layout, two from cutting re-derived argument, and one from merging two single-panel figures into `fig:loadsweep`. Chapter 6 went 27 pages to 25 over the same work. See §5, *Length and layout*, for the ordering rule that made each of them pay. A snapshot, not a budget. Rich figures, generated numbers, full argument. **Everything still needs review** before submission. The filename is the UH submission format `Lastname_Firstname_Mastersthesis_Year` (ASCII), and the build writes it directly, so no second copy has to be kept in step. Called `Thesis_POC` until 19 August 2026, which is the name older notes and commits use. |
| **`Ha_Vien_Mastersthesis_2026_short.pdf`** | `Ha_Vien_Mastersthesis_2026_short.tex` | **Compression pass, in progress** | A shorter cut of the full draft off the same class, macros, figures and bibliography. Measured 8 September 2026 it declares **55 pages with the same 12 appendix pages** (76 physical) against the draft's 97 and 12, and it is `oneside` where the draft is `twoside,openright`. Material is relocated to appendices or merged rather than deleted, which is why its appendix count has not moved. **It is neither supervisor-facing nor a submission candidate**, and no claim may be edited into it that is not in the draft. Its tooling is `.compress/`, and `.compress/shortcheck.py` is the check that a pass dropped no citation key, label, cross-reference or generated macro. Run it after every compression edit, because a dropped label is exactly the defect no build gate catches |
| `ai_statement.tex` | — | **Declaration in the author's name** | Required statement on generative-AI use, `\input` by `Ha_Vien_Mastersthesis_2026.tex` and `Thesis_v2.tex` before the bibliography. Shared on purpose: edit this file, never a copy. It must keep describing what actually happened, so revise it whenever the workflow changes. |
| `archive/*` | earlier variants | Superseded / stale | `plain_thesis.tex`, `thesis-vi.tex`, `thesis_wbm_full_backup.tex`, the pre-cuts `Thesis_POC.tex.bak-before-cuts`, the v1 plan PDF, and since 8 September 2026 the retired `UH_DS_MSc.cls` with the `UH-logo.png` only that class loaded, plus the dated `rollback-20260827-220354/` snapshot. See `archive/README.md`. They resolve `figures/` and `diagrams/` from the repository root, so they no longer build in place. Do not edit unless explicitly asked. |
| Artefacts | `spec/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/` | Implementation + evidence | Must stay consistent with claims in `Ha_Vien_Mastersthesis_2026.tex`. |

### Sync rule

When you change **claims, RQs, scope, methodology, or contributions**:

1. Update **`Thesis_v2.tex`** if the supervisor skeleton should reflect it.
2. Update **`Thesis_Plan_v2.tex`** if the plan’s status, timeline, or framing changes.
3. Update **`Ha_Vien_Mastersthesis_2026.tex`** for the full argument, figures, tables, and cross-references.
4. Rebuild affected PDFs and run the verification steps in §5.

When you change **measured numbers**:

1. Regenerate via `bench/refresh_thesis.sh` (never hand-edit `figures/gen_macros.tex`,
   `figures/gen_complexity.tex`, `figures/gen_artefacts.tex`, `figures/gen_baremetal.tex`, or
   `figures/gen_guest.tex`).
2. Re-read every prose claim that cites those macros (Chapters 7–9, abstract, discussion).
3. Check `docs/ASSESSMENT.md` and `docs/TODO.md` “after bare-metal campaign” items if tail or RSS claims move.

### Which dataset is which (read before touching any measured claim)

**Three campaigns exist and the macro prefix is what keeps them apart. A sentence that quotes the
wrong prefix is wrong in a way no build gate catches.**

| Dataset | Macros | Role |
| --- | --- | --- |
| `bench/results/campaign-20260827-151927.jsonl` — bare metal, 7 shards, 7 producers, 20 repeats, 14 loads | **unprefixed**, `gen_macros.tex` | **Canonical. Every result the thesis reports.** AMD EPYC 7443, SMT off, `performance` + boost off, `nohz_full`, no hypervisor, toolchain pinned in the Rocky container |
| `bench/results/campaign-20260812-154528.jsonl` — KVM guest, identical design | `\Guest*`, `gen_guest.tex` | The measurement-validity comparison in §`sec:hostcompare`. Same code, same design, a host that could not resolve the far tail. `g++` is one patch apart (`\GuestGpp` 15.1.1, `\MainGpp` 15.2.1). `rustc` matches at 1.97.1. Do not write that they share a toolchain |
| `bench/results-baremetal/campaign-20260826-*.jsonl` — bare metal, 8/8, 15 repeats, 8 loads | `\Bm*`, `gen_baremetal.tex` | Whether findings survive a change of shard count, load grid, repeat count and compiler |

Host descriptions are generated too: `\Main*` from the reported campaign's own environment capture
(matched by timestamp, not by taking the newest file), `\Guest*` and `\Bm*` from theirs.

**`\MainDistro` is the container image's userland and `\MainHostDistro` is the machine's**, added 8
September 2026 because the capture beside the reported campaign was written inside the container:
its `distro:` line reads Rocky Linux 8.10 from the image while every other field around it, the
kernel included, describes an Ubuntu 24.04.4 LTS host. `_host_distro()` in `bench/plot_figures.py`
therefore reads the host's name from the capture taken *outside* the container in the same session
(`env-20260827-151643.txt`), and matches candidates on the kernel, since a container shares the
host's and a capture from another machine cannot pass that test. Two things follow. The value is
`unknown`, visibly, when no such capture sits beside the campaign, rather than a guess. And
`bench/results/` is in `.gitignore`, so that capture was copied there from
`bench/results-canonical2/` and needs `git add -f` to survive a fresh checkout, the way the three
guest-era captures under `bench/results/` are tracked.

`bench/results-canonical/` holds an **invalid** 1120-run campaign from 27 Aug, kept on purpose as a
worked example. Never quote it. See §3 item 8.

**`ReprLoad` is pinned, not derived.** `REPR_LOAD_OPS = 56000` in `bench/plot_figures.py`. The old
rule (`deadline_limited_load()`, retained for diagnosis) took the busiest load holding p99 under
5 ms, which located the host's noise floor on the guest and the saturation knee on a quiet host. Do
not restore it as the operating point.

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

**Current grades are the twenty-first pass's, 7 September 2026: mean 4.83.** Areas 1, 2, 3 and 5
at 5, areas 4 and 6 at **4.5**. The twentieth pass, 3 September, held 5.00. What moved is not a
number but a claim: **§6.1, §6.4.5 twice, and `tab:testbed`'s caption say the virtualised campaign
ran the same toolchain as the reported one, and `\GuestGpp` 15.1.1 against `\MainGpp` 15.2.1 says
otherwise.** The same table prints both on one row under a caption claiming each adjacent column
pair isolates one change, and §6.4.7 then hand-types 15.1.1 as *the measurement host's* compiler,
which is wrong. Nothing measured moves and a GCC patch release confounds nothing, but the `\Bm`
column already carries this disclosure and the guest column does not. About an hour of editing
returns both areas to 5.

**Those sites were repaired on 7 September 2026**, in the session that set the acronym list to
sentence case. §6.1 and the host-comparison opening now disclose the compiler difference, and the
kernel one beside it. `tab:testbed`'s caption records both exceptions instead of promising one
change per column pair, and the table grew the **Kernel** row its caption had always claimed to
generate. §6.4.7 quotes `\MainGpp` where it had hand-typed 15.1.1 as the measurement host's
compiler. `tab:findings`' RQ3 cell names the second bare-metal host where it read only "on bare
metal". And §1.4's `is not:` regained a predicate in both documents, as "does not travel", which is
how §7.2 already words the same claim. An **independent reader given only the artefacts found two
further defects in those same passages**, both now closed and both of the shapes this file already
warns about. The enumeration of what the two campaigns differ in omitted the kernel, which the
container takes from the host, and the hosts differ (`\MainKernel` 6.17.0-23-generic against
`\GuestKernel` 7.0.2-1.el8.elrepo.x86_64). And `tab:findings`' RQ3 cell read `\CpuDiffAbsMax` as a
bound over the whole below-saturation regime where `write_generated_macros()` scopes it to the
representative load alone, which §6.4.3 words correctly and the summary cell did not: **a generated
macro that is the wrong quantity for the sentence holding it**, for the third time on record. The
grade is deliberately not restated here, because a remediation pass must not grade its own work.

One latent bug surfaced with it. `\GuestKernel` carried a raw `x86_64`, whose underscore is math
mode, so the macro could not be typeset and no document had ever quoted it. The three kernel grabs
in `guest_facts.py`, `baremetal_facts.py` and `plot_figures.py` now escape it, using the idiom
`complexity.py` and `adoption_cost.py` already had. `detex()` in `build_deck.py` converts `\_` back,
so the slide reading `\BmKernel` is unaffected. **A generated macro no document quotes is not
checked by anything**, which is the same lesson `diagrams/26_contributions` taught. The 23 pt running-header overflow on §2.2 remains **closed**:
`\section[Latency and predictability]{...}` ships, the log has zero `Overfull`, including during
`\output`. Area 7 is not assessable.

**The twenty-second pass, the same afternoon, held 4.83 on the 15:21 source and re-read all four
sites rather than trusting the record. All four are unchanged.** It added two items neither of
which moves an area. First, **the word *operation* carries two referents a factor of 400 apart**:
§6.4.1 defines it as the nanosecond-scale inner quantity that is `\BudgetCoreShareMax`% of the
sweep, and §7.1 l. 3621, l. 3623 and §7.3 l. 3863 then attach the bare noun to the
`\PFiftyMedian`-microsecond end-to-end round-trip. §1.4 l. 672 has the right wording
("end-to-end round-trip") to copy. Second, **`Thesis_v2.tex`'s new abstract has diverged from the
draft's** and carries three items of its own: a bare `\FfiOpBoundPct`% with the denominator
dropped, a point (5) attributing the full path to a language after point (4) said that clock
cannot, and "mixed-order repeats" for the named *interleaved* control that §1.4 of the same file
still calls interleaved. The skeleton's numbered form is otherwise better than the draft's and
should be ported back rather than reverted. The generated layer re-derived byte-identical for the
fifteenth consecutive pass.

**Every one of the 69 was prose disagreeing with an artefact that was itself correct.** The generated
layer re-derived byte for byte at all four checks. About 25 were introduced by the editing passes
themselves, including one fix that created a fresh instance of the class it was fixing. **So the
operating rule for this repository is now: run a reader who was not told what changed, and do it
after every editing round, not once at the end.** Two sessions editing and grading in sequence do not
substitute for one. The last such audit examined thirty changed passages and found eight defects.
The fifteen edits that closed those eight were read the same day (eight further defects, all closed)
and the residual-risk sites were re-checked on 30 August and still closed.

Three defect shapes defeated every gate and every macro recomputation, and they are now first-rank
checks in `.cursor/skills/thesis-grade-csm/CALIBRATION.md`: **a correct statement attached to the
wrong scope**, a claim right where it is derived and wrong at every site that summarises it (the
overload CPU ratio was inverted at five sites in two documents while the owning section had it
right), and a figure title asserting a conclusion its own bars refute.

**A fourth shape joined them on 31 August 2026: a citation detached from the clause it supports.**
Six sentences cited a work that does not carry the claim they make, and **four existed only in
`Thesis_v2.tex` where the full draft had them right**, which names the cause. Compressing a chapter
into five paragraphs moves clauses together and leaves each citation where the sentence boundary
fell. No gate sees it, because the key still resolves and the number still prints. All six are
closed, and the reader-facing record is `source_audit.pdf` with the durable one in
`docs/Sources_evidence.md`. **After any compression pass, re-read what each surviving citation now
sits next to.**

| # | Criterion | Target | Current (21st pass, 7 Sep 2026) | What still blocks a 5 |
| --- | --- | --- | --- | --- |
| **1** | **Thesis objective and research questions** | Clear gap, traceable RQs, falsifiable design | **5** | Nothing outstanding. Keep RQ2 two-sided (7 inside + 7 outside guarantee). The RQ1 alignment item is **closed**: RQ1 now names p99.99 in the draft, in `Thesis_v2.tex` and in `Thesis_Plan_v2.tex`, and §7.7 says the question was widened rather than claiming it always named the metric. |
| **2** | **Scholarly framework and use of sources** | Auditable literature search, critical maturity, consistent concepts | **5** | Optional: replace the remaining arXiv load-bearing cite (`Bugden`) with a peer-reviewed equivalent. The `Zhang` deadlock cite is now the journal version (`zhang2026deadlock`). |
| **3** | **Research data and method** | Sound method + decision-grade data | **5** | Nothing. The canonical repeat closed the data half (7/7/14/20, 1120 runs, no hypervisor, SMT off, `nohz_full`, zero errors) and the description half is repaired and independently re-checked. What earns the level is a pattern of refusals: the pre-committed reading rule is kept on a host where it costs nothing and said to be kept for that reason, the 448 kops/s rung is described and not tested because its operating point was found after the data, and the pooled and per-repeat statistics are held apart hard enough that the generator returns `None` rather than falling back and `fig:tailpct` was narrowed so the figure could not quote the disowned statistic either. **Do not add `isolcpus`. Do not restore the derived load rule. Do not let a fallback to the per-run `p9999` back in.** |
| **4** | **Presentation of thesis results** | Honest, reproducible, figure–table consistency | **4.5** | Level 5's "well considered and apt" fails at three sites. `tab:testbed`'s caption says each adjacent column pair isolates one change while its own Toolchain row prints `g++ 15.2.1` against `g++ 15.1.1`. §6.4.7 hand-types 15.1.1 as the measurement host's compiler, where `\MainGpp` and the campaign's own capture say 15.2.1 and 15.1.1 is the *guest's*. `tab:findings`' RQ3 cell says "resolved with one sign on bare metal" where the reported host is also bare metal. All editing. The printed abstract still matches the tables and the whole generated layer re-derived byte-identical. |
| **5** | **Discussion and conclusions** | Validity analysis, no over-claiming, hypotheses revisited | **5** | Nothing. All four chapter-7 sites that described a virtual machine are synced, and §7.2 now refuses a verdict on RQ1's overload half: it reports that the two effects run in opposite directions and names which deployment question each answers. Maintain register: “cannot tell” ≠ “equivalent”, the memory result is *located* and not *attributed to a call site*, the counters explain the operation-level timing and nothing about the footprint, and the 448 kops/s rung is described and not tested. |
| **6** | **Academic text** | Precise prose, no contradictions, clean structure | **4.5** | Two clauses, one each, and the half grade splits writing from consistency-and-finishing. Level 4's "consistent … description of research setup": three prose sites claim toolchain parity with the guest that Appendix D's own table refutes. Level 5's "excellent finishing polish": §1.4 of **both** documents carries "How it compares against the cost of the allocator choice is not:" with no predicate to elide, because `ed6debe`'s scope fix deleted the copula `a0e9122` had put there. Writing itself reads at 5 and the build is camera-ready: zero `Overfull` of any kind, zero semicolons, both colon checks at 0, `.acronyms.py` clean on both documents. The 83-word sentence is **not** counted, per the twentieth pass. Housekeeping: `\censors{}{}{}` when faculty assigns examiners. |

**Overall mean (unweighted): 4.83** at the twenty-first pass, 7 September 2026, down from 5.00.
**The lesson is the one this record keeps rediscovering in a new place: the values that regenerate
are safe and the ones a human typed beside them are not.** Every quantity in the twenty-first
pass's findings has a generated twin the document already uses correctly elsewhere, and both
survived seven passes because `texaudit.py`'s prose-number heuristic requires a unit and a bare
dotted version number has none. The durable fix is a generator plus that heuristic, not the three
sentences. The twentieth pass, 3 September, held 5.00. The nineteenth, 31
August afternoon, was the first 5.00, when area 6 moved from 4.5. The eighteenth that morning had
held 4.92. The header overflow that shared the area-6 cap is closed. Area 4
had been the only area that moved on the 30 August evening pass, from 4.5 to 5. The fifteenth was the first
figure on record confirmed by readers who wrote none of the work behind it. The sixteenth held
4.83 and withdrew the claim that the abstract is the only finishing item. The thirteenth pass, on the
night of 27 August, put it at 4.50. The history before that: 26 August went 4.67 to 4.50 (eleventh pass, after the
first bare-metal campaign landed and the document lagged it) to 4.67 (second remediation) to 4.58
(twelfth pass, which audited that remediation and found it had over-credited itself) to 4.75 (third
remediation), and then to 4.50 on 27 August, when the canonical repeat became the main dataset
and the same lag reappeared at larger scale. **That pattern cost this thesis a grade point twice in
two days, both times for the same reason.** A campaign lands, its macros regenerate cleanly, and the
sentences around them are not re-read. A clean regeneration says the numbers are right. It says
nothing about the prose. What closed the gap on 28 August was not more editing but **69 defects found
across seven reviews, 49 of them by readers given only the artefacts**. Five lessons are worth more
than the number.

1. **The bare-metal campaign removed the thesis's largest ceiling and briefly cost it two criteria,
   because the rest of the document had not caught up.** When a new results section lands, sync the
   summary tables, the threats table, the hypothesis revisit and the statistical-treatment section in
   the same pass: those four are where a grader looks and those four are what got missed.
2. **A remediation pass must not grade its own work.** The two failures it is most likely to make are
   invisible from inside it: propagating a claim it did not originate, and fixing one half of a pair.
   Both happened, and the twelfth pass found them. This applies to the third remediation too, which
   has not yet been audited.
3. **Before believing a limitation, check whether the dataset already refutes it.** The largest single
   improvement of the day came from reading seven fields that had sat in 480 campaign records while
   four places in the thesis said the instrument did not exist. Cost: two hours, no measurement.
4. **A new dataset does not only make claims stale, it can make them false in the opposite
   direction.** The thirteenth pass's new finding. "Every pair of intervals overlaps", "the one row
   that does not clear the correction" and "the knee sits at the same place for all four variants"
   were all true of the guest and are all reversed by the bare-metal data. None of them contains the
   word virtualised or unresolved, so a staleness sweep misses every one. The only check that finds
   them is reading each numeric claim in §6.4 against the generated table beside it.
5. **Run a reader who was not told what changed, after every editing round.** The single most
   productive thing done on 28 August. Four such readers found 49 of the day's 69 defects, including
   a results paragraph stating the opposite of the figure beside it, a headline claim inverted at
   five sites while the section that owns it was correct, and an unsupported number in a table whose
   own capture recorded zero. The self-audits were careful and caught 20. A session that knows which
   claims it changed reads for those claims. **Budget one audit per editing round, not one at the
   end**: the last round's audit found eight defects in thirty changed passages, a rate near one in
   four. Those closing edits were themselves read the same day.

Criteria 4 and 6 sit at 4.5 as of 7 September 2026 and the rest at 5, so all six are within about
an hour of editing of 5.00 (the twenty-first pass in `docs/ASSESSMENT.md` lists the sites).
Criterion 6 reached 5 once the unaided switch was set and the printed
declaration matched it. Criterion 4 reached 5 once the printed abstract caught up with the body.
Criterion 3 reached 5 once the method's *description* caught up with the method. The class-file item is **done**:
the document builds on the department's own `HYthesisML.cls`, and the reconstructed `UH_DS_MSc.cls`
is no longer loaded by anything and moved to `archive/` on 8 September 2026.

**The unaided switch is set.** The abstract's ten factual defects are **closed** in the 30 August
evening PDF. The §2.2 header overflow is **closed** in the 31 August PDF (optional short title
ships). `\abstractunaidedtrue` ships as of the nineteenth pass: page 96 prints that the abstract
was written by the author unaided, and the PDF contains no Not submittable. A model may not flip
it. The fifteenth pass's "one rewrite puts all six at 5" was reached at the nineteenth and held
through the twentieth; the twenty-first found two half-grade defects, so the mean of the six
assessable areas reads 4.83 and area 7 remains n/a. The independent read of the fifteen edits after 11:15
on 28 August was done the same day (eight further defects, all closed; residual-risk sites re-checked
on 30 August and still closed). The remaining measurement is **the transparent-hugepage experiment**,
about one machine-hour, already named in Chapter 8 as the priority. The allocation profile in
`bench/results-baremetal/alloc_profile-20260826-110718/` was analysed and **returns a negative
result**: it cannot attribute the footprint to a call site, because the profiling build reverses the
sign of the peak-RSS difference it was collected to explain, it runs past the saturation plateau,
and both flat rankings collapse onto frames that allocate nothing. Two positive results survived and
are reported (histogram parity to the byte, and the worker path's open-addressed-versus-node-based
shape). The collected jitter is reported descriptively in the same section. **The p99.99 column
`tab:latency` carries is pooled as of 27 August night**, read from
`campaign-20260827-151927.hist.pooled.csv` by `pooled_far_tail()` in `bench/plot_figures.py`, printed
without an interval because pooling makes the operation the unit of analysis, and marked with a dagger
whose caption says so. `refresh_thesis.sh` now pools `bench/results/` too. Do not reintroduce a
fallback to the per-run `p9999` field: that fallback is what let two sections describe a statistic the
pipeline was not computing. The
canonical-configuration bare-metal repeat is **done as of 27 August 2026** and closed criterion 3's
data half. The deck costs no grade and was the
last stale artefact in the repository. It is **resynced as of 26 August 2026, evening**: it reads
`gen_baremetal.tex` and `tab_resident.tex`, carries a far-tail slide and a resident-set slide, names
both hosts on one slide, and the five passages that contradicted the thesis are corrected. The one
worth remembering is `diagrams/26_contributions`, which no `.tex` includes, so nothing checked it:
it still showed the pre-catalogue counts of five injected classes and two boundary ones long after
the thesis said seven and seven. A diagram only the deck uses is outside every gate the thesis has.

**The deck's host labels were resynced again on 8 September 2026, and the defect class is worth the
paragraph.** Four slides described the virtualised guest while printing the reported host's numbers,
because the resync of 26 August predated the bare-metal repeat of 27 August by a day. Slide 16 read
its left column from `ENV`, which follows the newest campaign in `bench/results/`, so its values
moved to bare metal and its labels did not: it printed the host's 48 threads as "48 cores, 1
sockets" and the string "none guest" on the timing-floor row. It reads `\Main*` now, the values
Appendix D prints, and its OS row splits `\MainHostDistro` from the image's `\MainDistro`. Slide 23
compared guest against bare metal with no `\Guest*` macro in scope, so its guest column held
unprefixed values with the guest's outcome typed beside them in words, which after the repeat meant
a bare-metal microsecond under a heading reading virtualised guest. `gen_guest.tex` is now a deck
macro source and that column reads `\GuestPNineNineMaxCI` against `\GuestPNineNineRange`, the
interval swamping the spread, which is what "cannot resolve" means in numbers. The guest campaign
recorded no histogram buckets, so the two pooled rows say there is nothing there to pool rather than
reporting a null. Slides 22 and 28 claimed the allocator effect was an order of magnitude larger
than the language effect, the claim this file and the rules forbid: both now read comparable here
and `\GuestRssAllocOverLang` times it on the guest, matching `tab:findings`. Two lessons. A column
whose heading names one host and whose cells come from another is the cell no gate can catch, and a
raw capture read through `ENV` is a path that silently repoints when a campaign lands.

**Slide PNGs do export on this machine, through Windows PowerPoint.** The deck skill requires a
visual pass over rendered slides and neither LibreOffice nor Poppler is installed here, so earlier
sessions checked the deck with the geometry and prose gates alone and said so. WSL can reach the
host's Office instead. Copy the deck and
`.cursor/skills/create-pptx-master-thesis/scripts/export_slides.ps1` to a Windows-visible directory
such as `/mnt/c/temp/`, run `powershell.exe -ExecutionPolicy Bypass -File ... -PptxPath ...
-OutDir ...`, and copy the PNGs back to `slides_preview/` (gitignored, 32 slides at about 7 MiB).
The whole export takes some 15 seconds. It is worth the trouble because
`check_slide_text_overflows()` is a conservative estimate rather than a renderer, and it is wrong in
both directions. It has flagged the same ten shapes for several builds and the render shows every one
of them fitting, so judge a flag by the PNG and treat a *new* flag as the signal it is meant to be.
It also missed two real collisions, both a title or subtitle wrapping onto the shape below it, and
one of them had been in the deck for as long as the slide had. Titles and subtitles are the exposure,
because a wrap there lands on the table header or the figure rather than in white space, and the
limit is rendered width and not a character count: the 62-character title on slide 10 holds one line
while slide 18's 65-character one did not. Lengthen either and look at the render.

The same pass corrected two deck-only diagrams, the class this section already warns about.
`01_ngran_architecture.svg` drew E1 outside the dashed gNB-CU box with both arrowheads stopping at
elbow bends, and E1 is internal to the central unit, so the artwork put a standardised interface in
the wrong container and contradicted `fig:ngran`, whose TikZ draws it straight down from `cp.south`
to `up.north`. The box is now tall enough to hold that arrow between the two planes, and F1 and NG
stop three units short of the dashed border so the dashes no longer cut through their heads. In
`23_stats_pipeline` the permutation count read `2^20`, a caret where the prose typesets
$2^{\NRepeats}$, so `build_new_diagrams.py` now translates the exponent's digits to Unicode
superscripts. Note what caught neither: `check_labels.py` does cover both files, since its scope
includes what `build_deck.py` names, and `check_fit.py` reports no tight label in either. Geometry
and notation are outside what both gates read.

An audit of every number typed into a slide string followed, since the build only fails on a macro
it cannot find and a literal is invisible to it. Four survive, and three are design facts that match
their sources: `C++23` matches `CMAKE_CXX_STANDARD`, the two condition variables match
`bounded_queue.hpp`, and capacity 1024 matches the default in `bench/queue_contention.sh`. The
fourth was wrong in the way this file cares about. Slide 4 read that roughly 70 per cent of serious
security vulnerabilities *at major vendors* are memory-safety defects, and the figure is Microsoft's
own reporting of its own CVEs, which is how §2.1 states and cites it. The slide names the vendor now.
Generalising a single-vendor number to an industry is the same defect as a column heading naming one
host over another host's numbers, and neither the layout gate nor the prose gate can see either.

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
5. **Peak RSS** — a real language effect that reproduces under both allocators **and on all three hosts measured** (1.4–3.5 MiB everywhere). The **allocator effect is host-dependent** and this is the one headline claim the 27 Aug 2026 canonical repeat overturned: it measured 32.5–34.3 MiB on the KVM guest and 1.5–2.4 MiB on both bare-metal hosts, so the two effects are *comparable* on adequate hardware and the guest's order-of-magnitude gap belonged to that machine. **Do not restore “the allocator effect is the larger one”** and do not drop the language effect either. The transparent-hugepage policy differed between the hosts (`always` on the guest, `madvise` on both bare-metal ones) and only the system-allocator arm inherits it, so it is the named candidate, but the study never varied it with everything else fixed and **must not claim causation**. Quote the generated macros: `\RssLangDiff*` and `\RssAllocDiff*` for the reported host, `\GuestRss*` for the guest, `\BmRss*` for the second bare-metal host.
6. **FFI** — interleaved native vs seam calls; tax bounded, not “free”; `unsafe` confined to seam; core stays `unsafe`-free.
6a. **Adoption cost beyond the seam** (`bench/adoption_cost.py`, §7.6, added 21 Aug 2026). Three axes, and two of them are easy to break by “simplifying”:
   - **Never quote the shipped binary-size ratio on its own.** g++ leaves libstdc++ to the loader and rustc links libstd in, so the default-vs-default figure compares two linkage policies. The ordering *reverses* between matched-static and matched-dynamic, so all three rows have to stay, and so does the row reporting what each dynamic build leaves on the host.
   - **Never quote the full-build time without the decomposition.** Most of the Rust clean build is third-party code; with the dependency tree warm the project's own source compiles for *less* CPU than g++ needs. Dropping the decomposition turns a real finding into the folk objection it refutes.
   - **The C++ `unsafe` cell is empty on purpose.** The language marks no such region, so a zero would be a category error, not a win for C++. Keep it as `---`.
   - Build time is the **one host-sensitive axis** here. Absolutes describe the machine, the paired ratio travels. Do not let a sync pass restore the blanket claim that RQ4 is environment-insensitive.
7. **No over-claim on Rust** — eliminates data races and aliasing errors, not race conditions or lock-order deadlocks.
8. **Never boot a measurement host with `isolcpus`.** It gives the cleanest tails and it also removes those cores from every scheduling domain, which switches off load balancing across them. `bench/campaign.sh` pins to a *range* with `taskset -c 2-17` and relies on the kernel to spread `N_SHARDS + producers` threads over it, so with no balancer they all inherit the first allowed CPU. On 27 Aug 2026 that put **all 1120 runs of a campaign on `cpu2` alone**: `cpu_pct` flat at 100.1% at every load, `cpu3`–`cpu17` at 0.0% busy under sampling, plateau 84 kops/s against 336 and 448 on the other hosts. **Every record looked individually plausible**, and it was caught only by comparing three campaigns against each other. Use `nohz_full` and `rcu_nocbs` instead, and run `bench/canonical_repeat.sh check-spread` before any long campaign: it refuses to start below 150% `cpu_pct` on a probe run (broken config reads 100%, healthy reads ~688%). The dead dataset is kept at `bench/results-canonical/`.
9. **Do not claim the guest and reported campaigns share a toolchain.** The container pins the `gcc-toolset` major version, not the point release. `\GuestGpp` is 15.1.1 and `\MainGpp` is 15.2.1. `rustc` matches at 1.97.1. The `\Bm` column already discloses its compiler change. Four prose sites and `tab:testbed`'s caption said the machine was the only difference (twenty-first pass, 7 Sep 2026) and were repaired by disclosure on the same day, the way the `\Bm` column does. Quote `\MainGpp` / `\GuestGpp` / `\BmGpp`, never a typed version. **The compiler is not the only unpinned difference**: the container takes the kernel from the host, so the guest campaign also ran `\GuestKernel` against `\MainKernel`, and `tab:testbed` now prints that row. An enumeration of what the two campaigns differ in has to name both.

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
| App. A–G | Key terms, literature search protocol, statistical design, host and campaign configuration, fault-injection example, implementation of the two cores, engineering guidelines for incremental adoption | 2, 3, 4 |

**Acronyms live in the front matter, not in Appendix A, as of 4 September 2026.** A `List of
acronyms` follows the list of tables in `Ha_Vien_Mastersthesis_2026.tex` and the contents in
`Thesis_v2.tex`, titled from the class's own `\nomname` and set as a `longtable` so it can run
past a page without floating away from its heading. It carries no `\caption`, or a front-matter
table would be announced in a list of tables printed before it. Appendix A keeps only the terms
that are not acronyms and is retitled to match. Three things follow for any edit. Every acronym
is written out at its first use in the body, so adding one means adding both the expansion and
the row. The scoped list in `Thesis_v2.tex` is a subset, so an acronym added there needs its own
row. And `consistency.py --acronyms` from the `academic-writing` skill now reads the list itself
as prose and reports each row as an unexpanded first use, so scope it past the `longtable` before
believing its output. **Expansions are sentence case as of 7 September 2026**, on the author's
decision and matching Appendix A's key-terms table, so the first letter is capitalised unless the
phrase's own spelling forbids it. The four `gNB` rows keep a lowercase g and `3GPP` opens on a
digit, and a comment above each table records it, because a mechanical sweep of the column would
write `GNB central unit`. Capitalisation beyond the first letter still follows the phrase: proper
nouns keep their capitals and generic terms gain none, which is why `Amazon Web Services` sits
beside `Application binary interface`. **The abstract's argument stays as the author wrote it.** On 7 September
2026 the author asked for `UE`, `gNB-CU-CP` and `FFI` to be glossed there, because the abstract
form is read before the list of acronyms. `\abstractunaidedtrue` still ships. Do not rewrite the
claims, and do not gloss further unless asked.

**The skeleton and the full draft carry the same chapter list again, resolved 26 August 2026 on
the author's decision.** `Thesis_v2.tex` had nine chapters, because it kept a standalone
`Objectives` chapter between problem context and methodology where the draft has eight and no
such chapter. **The draft was the canonical list**, and the archive is why: `archive/plain_thesis.tex`
and `archive/thesis_wbm_full_backup.tex` both carry an `Objectives` chapter with live
cross-references to it, so the draft once had that chapter and folding it into the introduction
was a deliberate earlier decision the skeleton never followed. Do not propose adding it back.

The skeleton is now eight chapters matching the draft title for title. Its `Objectives` bullets
went where the draft already keeps that material. The hypotheses became a chapter 1 bullet placed
directly after the RQ bullet, mirroring §1.3, which is the only one that needed a bullet of its
own because the skeleton had stated H1 to H3 nowhere except its discussion revisit. The
documented literature search folded into the evidence-gap bullet, and the evidence standard and
the scope exclusions folded into the contributions bullet, mirroring §1.4. **The numbered
objectives O1 to O5 are gone on purpose**, because the draft has no numbered objectives anywhere
and keeping them would have re-opened the divergence in a different form.

`Thesis_v2.tex` still has one argument move per paragraph, but it is no longer an itemize
skeleton. On 27 August 2026 the author asked for the draft Chapter 1 in full and for plain
prose in every chapter. Chapter 1 is therefore the introduction from
`Ha_Vien_Mastersthesis_2026.tex`, with appendix and later-section references retargeted to
the chapter labels this file has. Chapters 2 to 8 keep **five argument paragraphs** each,
the same five moves they had as bullets. Do not add a sixth paragraph to those chapters, and
do not expand them into the full draft's chapter prose. The document has no appendix and
needs none. Chapters 5 to 8 were first filled at the author's explicit request on 20 August
2026, when the fold had not happened and they were numbered 6 to 9.

Older notes in this file, in `docs/ASSESSMENT.md` and in `.cursor/rules/thesis-quality.mdc` that
call the evaluation chapter 7 or the discussion chapter 8 are using the retired nine-chapter
numbering. The assessment passes are historical records and were left as written.

**The skeleton carries figures as of 7 September 2026**, on the author's decision: 15 of the
draft's 22, chosen as one per argument move that has a figure, with a `\listoffigures` after
the contents and no list of tables, because the document has no tables. Four rules govern any
change to them. **They are floats and not paragraphs**, so each sits between two paragraphs
and the five-paragraph rule above is unaffected: a paragraph count that reads six means a
blank line landed inside one. **The image and TikZ sources are shared with the draft, not
copied**, so both documents resolve `diagrams/pdf/` and `figures/` from the repository root
and a regenerated plot reaches both. **The captions are trimmed to two to four sentences**
against the draft's six to fifteen, because a five-paragraph chapter cannot carry captions
that argue, and the short `\caption[...]` titles are the draft's verbatim so the two lists of
figures agree. And **a caption's cross-references had to be retargeted or dropped**, since the
draft's captions point at sections and tables this document does not have. Chapter 6 holds
seven of the fifteen and chapters 4 and 8 hold none, which follows the draft. The five
acronyms the figures introduced (FIFO, MPSC, RSS, gNB-CU-UP, gNB-DU) were added to the
front-matter list in the same edit, with the draft's wording, and written out in the prose
that cites each figure rather than in the caption, because `.acronyms.py` reads a TikZ node
label as a use and the labels come before the caption in source order.

Because the results chapters and now the figure captions quote measured values,
`Thesis_v2.tex` `\input`s the same six generated macro files as the full draft (`gen_macros`,
`gen_complexity`, `gen_artefacts`, `gen_adoption`, `gen_baremetal`, `gen_guest`). It therefore
has to be rebuilt whenever those are regenerated, not only when its own source changes, and
`bench/refresh_thesis.sh` does **not** rebuild it, so that step is manual.

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
./.acronyms.py             # every front-matter acronym written out at first use
```

The first three report counts rather than errors, so read them as frequency. Hard rules for
thesis prose:

All four default to `Ha_Vien_Mastersthesis_2026.tex` and take any other `.tex` file as their
one argument.

**`.acronyms.py` is a gate and not a count**, added 6 September 2026, and it exits non-zero on a
hit. It enforces the promise the front matter makes in so many words, that each listed acronym is
also written out where the text first uses it. The front-matter `longtable` is the source of
truth, so an acronym cannot be checked without being declared and the script also names a
declared acronym the body never uses. Four things about it are load-bearing. It reads from
`\mainmatter` **to the end of the file**, because the appendices sit after `\printbibliography`
here and stopping at the bibliography reported the literature-search protocol's own acronyms
(ACM, DBLP, DiVA, IEEE, USENIX) as unused. It strips citation keys, labels and cross-references
first, since an acronym inside `\cite{ieee...}` is not a use a reader sees and counting it moves
first use to the wrong page. It asks only for the **first three words** of the gloss, because
demanding the whole entry rejected `FNV-1a, the Fowler--Noll--Vo hash` for lacking the word
"function". And its exemptions are an explicit list that the output **prints rather than hides**,
in the manner of `diagrams/check_labels.py`, so waiving one is on the record. Five are waived
today and the reason travels with each. When it found the real defect, a loose heuristic would
have passed it.

1. **No em dashes**, neither `---` nor a literal `—`. Re-counted 6 September 2026: `.aitells.py`
   reports **9 hits in the draft and 7 in the skeleton**, and all sixteen are correct typography.
   The draft's are the Herfindahl--Hirschman Index and eight numeric ranges, most of them the
   peak-RSS figures in MiB, which is why the figure is no longer the four recorded on 17 August.
   The skeleton's are that same name, four ranges, and **Fowler--Noll--Vo counted twice**, because
   the pattern counts occurrences rather than names and that one carries two dashes. Those two
   arrived with the acronym pass of 5 September, which put the hash's full name into body prose.
   If the figure rises again the new ones are yours, but check for a compound proper name before
   deleting a dash: two of the sixteen are one name, and a third of a name is not an improvement.
2. **No semicolons.** Use a full stop, a comma, a colon, or two sentences instead. Semicolons in
   thesis prose read as stiff and are easy to spot on review.
3. **Capitalise after a colon when what follows begins a unit of its own.** The supervisor asked for
   this on 4 September 2026 and it is the APA convention. Two shapes qualify and both were fixed
   the same day, 14 sites across the two documents. A **run-in label** such as `\textbf{H1:}` stands
   outside the sentence's grammar, so the sentence begins after the colon and takes a capital:
   `\textbf{H1:} For this workload the two languages are performance-equivalent`. The argument that
   settles it is internal, not a style guide: `\item[RQ1] How do Rust and modern C++ compare` sits
   four lines above and has always been capitalised, and the hypotheses are the same construct. All
   six bold label colons in the repository were the H1 to H3 statements and all six were lowercase,
   so there was no counter-example to preserve. A colon introducing a **question or a series of
   them** also takes a capital: `comparison itself: Which defect classes a compiler can rule out`,
   three items that restate RQ2 to RQ4 against an RQ list that capitalises them. Five more colons
   of that shape were found and moved with it, so the two documents agree.
   **Everything else stays lowercase**, which is the large majority: a colon amplifying a clause
   that already began, a list, or a phrase. The single-clause case is where the guides split, APA
   capitalising and Chicago not, and the thesis keeps its 17 such sites in `Thesis_v2.tex`
   lowercase. Do not sweep them without being asked. Display type (titles, captions, `\paragraph`
   headings) takes the capital as the chapter titles do, and the draft has **13 that do not**,
   deferred deliberately on 4 September. `.aitells.py` reports `lowercase after a label colon` and
   `lowercase question after a colon`, both at **0** after the fix, and both skip display type
   because `is_prose()` drops any line starting with a backslash.
4. **`artefact` and `artifact` are both correct here, and the sense decides which.** Counted 7
   September 2026: the draft carries 12 prose uses of `artefact` against 9 of `artifact`, and the
   split is deliberate rather than drift. `artifact` is the research deliverable, the
   design-science sense used by §1.4's contributions, §4.1, `tab:design`'s column, §5.6's own
   heading *Reproducibility and research artifacts*, §7.6 and the conclusion, and it is the
   spelling ACM's badging programme uses. `artefact` is the compiled binary or a measurement
   artefact, which is why `bench/artefact_facts.py` and `figures/gen_artefacts.tex` carry the
   British spelling.    `consistency.py` reports the pair on every run and it is a false positive by
   design. Do not normalise either spelling without being asked, and when adding a sentence, pick
   by sense.
5. **A sentence that is only a count and a label is scaffolding, not prose.** `Three are results.`
   opened §1.4's contribution list in both documents until 7 September 2026, ahead of one sentence
   per result, and it is now folded into the first of them (`Three are results, and the first is a
   comparison of latency and resource behaviour`). The test is deletability: a sentence that can go
   without taking a claim with it was an outline heading. The family runs on through `Two risks
   remain.`, `Three limitations remain.`, `Three are load-bearing.` and `Two responsibilities
   follow.` **Length is not the test and treating it as one makes the prose worse**, because
   `.readability.py` asks for 25 to 35 per cent of sentences under 15 words as recovery points, and
   `Both implementations follow it.` is that width while carrying the fairness control.
   `.aitells.py` counts the shape as `counting stub`, a count subject inside four words, reading
   **2 in the skeleton and 12 in the draft**. Neither is a target and both lists hold sentences that
   earn their place, so judge each hit rather than lengthening it.

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
change moves the declared figure. It reads **98 with 13 appendix pages** (121 physical), measured
8 September 2026, after `tab:testbed` grew an operating-system row. That row and its caption
sentence are the whole of the appendix page: the committed source ahead of them built 98 with 12,
measured the same day for the comparison. It read 96 with 12 (118 physical) on 4 September 2026
after the acronym pass, one declared page of which came from writing acronyms out at first use and
two physical ones from the front-matter list, which sits outside `\pagesCount`. It
read 95 with 12 (115 physical) on 31 August 2026. The appendices span the last 13 physical pages, which is where the 13 comes from.

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
  `tab:adoption` closed short pages at no cost. Three were measured and reverted, so do not retry
  them: `tab:defectmap` at `[tp]` *added* a page, `tab:findings` at `[H]` was mixed, and
  `tab:params` at `[tp]` returned nothing on 8 September 2026. After any
  such change, check that no converted table drifted past the page that cites it.
  `tab:testbed` moved to `[tp]` the same day and is the case where the setting buys shape rather
  than pages. The row added to it made the table too tall for what `[ht]` had left of its page, so
  it floated one page on and left 303pt of whitespace between two paragraphs. At `[tp]` it returns
  to the top of the page its reference sits on, the four pages before the appendix tail repack, and
  the overflow is three lines on a tail page instead. Appendix D is 13 pages either way, and
  closing that tail page would cost three lines of the allocation-profile paragraph, which is a
  negative result the thesis argues from.

Measured cost of the layout settings, cumulative, at unchanged content: 1.5 spacing 22 pages,
full-width figures 4, `twoside,openright` 15 blank versos, loose heading and float gaps 3, and a
12pt bibliography with default item gaps 4. That is 48 pages of layout, so the settings are worth
keeping whatever the target is, and any of them can be handed back deliberately if the author
prefers the looser look to the shorter document.

**Every remaining layout lever is now measured, and all but one return nothing.** Asked on 26 August
2026 to reach under 90 declared pages, each candidate was applied, built and reverted. Do not re-run
these:

| Lever | Declared pages saved |
| --- | --- |
| Every figure from `0.78\linewidth` to `0.62` (all 19 images) | **0** |
| `\textfloatsep`, `\floatsep`, `\intextsep` all to 8pt | **0** |
| Wider margins via `geometry` after the class | **0**, the class fixes the text block and overrides it |
| Global `\arraystretch{1.0}` on every table | **0** |
| Deleting all 11 hand-drawn diagrams | 2, and it orphans 11 references |
| Bibliography `\footnotesize` to `\scriptsize` | **2** |

The mean vertical fill across the body is 104 per cent and only twelve pages sit under 72 per cent,
almost all of them chapter or appendix opening pages the class creates by rule. **There is no
density left to harvest.** The `\scriptsize` bibliography was taken on 26 August and is legible.

**Deletion is also priced, and the exchange rate is poor.** Whole-section deletions measured: §7.5
Related work 2792 words for 7 pages, §5.4 Implementation details 3388 words for 7, §3.3 Tail latency
in RAN 421 words for 1, §2.3 C++ for latency-critical systems 655 words for 1. Roughly 400 to 500
words per page, and only the two large sections yield at all.

**The important half of that pricing is what the cuts cost, and it is why 90 is not reachable.**
Every candidate is named by a grade descriptor:

- **§7.5 Related work** holds `tab:related`, the Arvidsson reconciliation and the contrary results.
  Area 2's level 5 requires "contrary results engaged rather than omitted" and area 5's requires
  "contradictory prior results reconciled mechanically". Deleting it drops both from 5.
- **§5.4.2** describes the pinned FNV-1a hashing, which area 3's level-5 anchor names, and the
  hand-built bounded queue, which is one of the two forced-idiom entries the overload attribution
  rests on.
- **§5.4.3** contains the lifecycle-gap defect found by design review, which the calibration file
  calls area 5's strongest single passage.
- **§3.3** owns `fig:cliff`, which §6.4.2's overload prose depends on.
- **§2.3** is the only citation site for four sources, so deleting it creates uncited entries and
  breaks area 2's "every entry cited" property.

So the ladder is **101 at no grade cost** (taken), 94 only by dropping the diagrams that helped area
4 reach 4.5, and 87 only by deleting §7.5 and paying about a third of a grade point. If a sub-90
figure is ever required, the honest route is to move material into appendices, since `\pagesCount`
counts main matter only. That changes the declared number and not the document, and it should be
labelled as such.

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

The skeleton's chapter list is no longer the outlier it was here: it matches the draft's eight
since 26 August 2026 (§4).

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
- `./.aitells.py` on every file whose prose changed: no em-dash asides introduced, no semicolons
  introduced, both colon checks still at zero, and no counting stub added (the count may fall, and
  a rise means an edit announced a list instead of making one).
- Figure/table macros in prose match `figures/gen_macros.tex`.
- No figure contradicts its table (see `docs/ASSESSMENT.md` refinement pass for past failures).
- `diagrams/check_labels.py` reports “Diagram labels: no em dash, dash aside, or semicolon”. Run by
  `refresh_thesis.sh`; re-render and read any figure whose label you changed.
- `./.acronyms.py` on any document whose front matter or first-use prose changed: `not written out
  at first use: 0`, and no new name under `declared but never used`.
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
- **Do not** write that the guest and reported campaigns share a toolchain. `\GuestGpp` is 15.1.1 and `\MainGpp` is 15.2.1.
- **Do not** remove boundary defect classes or sanitiser-only C++ outcomes to tidy the narrative.
- **Do not** expand `Thesis_v2.tex` chapters 2--8 beyond five argument paragraphs, or replace Chapter 1 with a shorter skeleton. Chapter 1 is the draft introduction. The rest stay a five-move skeleton, now in plain prose rather than itemize, and the document is supervisor-facing.
- **Do not** treat `Ha_Vien_Mastersthesis_2026_short.pdf` as a deliverable or let a claim reach it that is not in the full draft. It is a compression pass over that draft and the draft stays canonical. Run `.compress/shortcheck.py` after editing it.
- **Do not** move the document sources, the four prose checks, or `bibliography.bib` out of the repository root. Every document resolves `figures/`, `diagrams/pdf/` and `template/figures/` from there, which is why `archive/` no longer builds, and `refresh_thesis.sh`, `diagrams/check_labels.py`, the grading skill and `.cursor/rules/thesis-quality.mdc` all name the checks by path.
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
| `docs/Sources_evidence.md` | The citation audit's durable record: per entry, whether the metadata matches the publisher, what claim the citation carries, and the page or clause the supporting passage was read from, graded A (passage located), B (deposited record carries it) or C (metadata only). 80 entries have a full record, 7 more are covered by the 24 August pass, and the rest are reached through `LITERATURE_NOTES.md` |
| `.bibaudit/build_audit.py` | Generates **`source_audit.tex`**, the source-checking document: all 109 entries, ordered by the number each carries in `Ha_Vien_Mastersthesis_2026`'s reference list, with every citing sentence beside the source's own words. **Scoped to that document by default**, which loses no entry because it cites all 109, and means a number in the audit is always the submission document's own. `--all-documents` widens to `Thesis_v2` and the plan, adding columns for the numbers those give the same work. Reads `bibliography.bib`, the `.bbl` of each document in scope, their `.tex` sources, and the two `docs/` records. **Never hand-edit `source_audit.tex`, with one exception: Part 1's last column is the author's review tick**, and changing a `$\square$` to a `$\blacksquare$` there is how the source-checking pass records progress. The generator reads those ticks back out of the previous document before overwriting it and mirrors them to `.bibaudit/reviewed.txt`, so they survive a regeneration and a delete, and unticking a row is respected. It reports `review ticks: N of 109 entries marked reviewed, carried over` on every run. **Read that line after regenerating**: on 1 September 2026 a regeneration silently wiped 22 ticks, and they were recovered only from the editor's local history. Everything else in the file is derived and a hand edit to it is lost on the next run. Three further things about it are load-bearing. It prints references through `\fullcite` rather than retyping them, so it cannot disagree with the thesis bibliography. It takes printed numbers from `\entry{}` order in each `.bbl` and **refuses to run when a `.bbl` disagrees with its source's cite keys**, because stale numbers would defeat the document's whole purpose (`--allow-stale` overrides and should not be used). And it rewrites em dashes and prose semicolons in its own prose while passing quoted source text through untouched, since altering a quotation misquotes it, so `.aitells.py` hits inside a quotation are expected and Part 0 says so. Rebuild with `.bibaudit/build_audit.py && latexmk -pdf source_audit.tex` |
| `bench/TESTBED.md` | Bare-metal protocol (only path to criterion 3/4 → 5 on tail) |
| `bench/artefact_facts.py` | Generates `figures/gen_artefacts.tex`: record sizes (compiled probes), parity-suite coverage, conformance campaign size, FFI seam size, **fault-catalogue outcomes** (deadlock detection rate, lost-update counts, undetected-class count) and **suite size** (C++ binaries, Rust tests). Anything measured that no campaign log holds belongs here, not in the prose. The deadlock rate is read from `taxonomy.csv` *and* recounted from the per-run logs, and a mismatch is a hard error |
| `bench/complexity.py` | Generates `figures/tab_complexity.tex`, **`figures/tab_loc.tex`** and `gen_complexity.tex`. The `CONCERNS` partition decomposes the line-count gap and the script refuses to write the table unless every measured file is assigned to exactly one row and each column sums to its measured total. That check is why Table 5.4 can no longer go six lines short of its own printed total |
| `diagrams/check_labels.py` | Prose-style gate over diagram labels, the third surface beside `.aitells.py` and the deck's `check_prose_style`. Scope computed from the documents; run by `refresh_thesis.sh` |
| `.acronyms.py` | Gate over the front matter's own promise that every listed acronym is written out at first use. Takes the acronym list as the source of truth, reads `\mainmatter` to end of file so the appendices count, strips citation keys before deciding what first use means, and prints its five waivers instead of hiding them. Added 6 September 2026, when it found `UndefinedBehaviorSanitizer` shipped without `(UBSan)` beside `AddressSanitizer (ASan)` and `ThreadSanitizer (TSan)` |
| `.compress/` | One-shot tooling for `Ha_Vien_Mastersthesis_2026_short.tex`, invoked from the repository root the way `bench/` scripts are. `shortcheck.py` diffs two sources for citation keys, labels, cross-references and generated macros the short cut dropped, and is the gate for that document. `lengthprice.py` prices words, floats and page span per division and takes any `.tex` as its argument, so it is useful on the full draft too. `reloc.py` and `movapp.py` move blocks into or within the appendices, and `strip.py`, `deref.py` and `retarget.py` delete relocated material and repoint what referenced it. The last three carry the short document's filename as a module constant, so read the top of one before running it. `drafts/` holds rewritten chapter candidates and the pre-relocation backup |
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
2. `Thesis_v2.pdf` — supervisor read-through: full Chapter 1, five prose paragraphs in each of chapters 2--8, and 15 figures (52 physical pages, 41 declared, measured 7 September 2026 after the figures landed). The skeleton's class writes no `\pagesCount`, so read its declared length from the printed folios: arabic 1 sits on physical page 11 and the last body page prints 41. It read 46 physical and 38 declared before the figures.
3. Optionally reference `Ha_Vien_Mastersthesis_2026.pdf` as the **working full draft** (clearly labelled not final).

Port supervisor feedback into `Thesis_v2.tex` and `Ha_Vien_Mastersthesis_2026.tex` in the same
edit pass so the two do not diverge.

---

*A third remediation pass on the night of 26 August closed the twelfth pass's list, and the item that
mattered was the two-hour one. `bench/baremetal_facts.py` now reads `jemalloc`'s own accounting into
26 macros and `figures/tab_resident.tex`, and §`sec:baremetal` reports the resident set decomposed
rather than bounded by elimination. **The result relocates the RQ3 memory finding.** Arena metadata
costs the Rust build $+2.07$ MiB more and drifts by $0.5\%$ across the whole load range, so it is a
constant of the process, and Rust holds $0.16$ MiB *less* live allocation, which settles that the
larger resident set is not more application data. But `jemalloc`'s own resident bytes are $1.92$ MiB
*lower* in the Rust build while its peak is $1.74$ MiB higher, and paired inside each run the
footprint outside the allocator's mappings differs by $+3.8$ MiB. **So the peak-RSS language effect is
not an allocator effect**: it is the standard library and runtime a Rust process carries before it
allocates. A third reading is a negative result about the guest: the $31$ MiB bimodality that costs
peak RSS under `jemalloc` its row does not appear on the quiet host, where no arm spans more than
$1.7$ MiB, so that defect belonged to the machine. Two caveats are in the text, not left to a reader:
peak RSS is a `getrusage` maximum against sampled `je` figures, and the derived row is a median of
per-run differences, so the table's column does not sum exactly and the caption says why. The counter
over-claim is gone from all four sites and §7.2 is rebuilt around three bounds. Criterion 4 left 4.0
for the first time since the ninth pass and criterion 5 returned to 5. **Two layout lessons.** The
stranded appendix page was caused by `[H]` forbidding reflow, and the fix was to *float* the table to
`[ht]`, which is the reverse of every earlier length pass in this repository, so diagnose before
choosing a direction. And a two-line prose addition to §5.6 stranded a chapter-tail page, recovered by
tightening the same passage. See the third remediation pass in `docs/ASSESSMENT.md`.*

*The twelfth grading pass, late on 26 August, audited the second remediation instead of taking a fresh
look, and found the two things a self-graded pass cannot see. It **propagated a claim it did not
originate**: §6.4.4's "less work and worse locality is one account of both RQ3 results at once" came
in with the bare-metal integration, and the remediation carried it into §7.2, `tab:findings` and
`tab:threats` without asking whether an operation's cache-miss rate can explain a fixed allocator and
runtime footprint. It cannot, and §6.4.3 says so in its own words. And it **fixed one half of a
pair**: `tab:testbed`'s caption now lists the three protocol rows the confirmation host missed, while
the paragraph four lines above it still says the campaign "satisfies" that column. Criterion 5 went
back to 4.5, mean 4.58. **The pass also found the largest unrealised asset in the repository, and it
is not the allocation profile.** Both bare-metal campaigns record jemalloc's own statistics in every
run of their jemalloc arms, 480 runs, through instrumentation built for exactly this purpose. The
seven fields decompose the resident set into live allocation against arena bookkeeping against
retained-but-unmapped, which is word for word the split §7.2 calls unresolved and pins on an
instrument the study supposedly lacks. No generator reads them and §6.3 does not list them. The
answer in them is better than the placeholder: Rust holds **less** live data and less
allocator-resident memory while its process peak is higher, so the difference is neither application
data nor fully inside `jemalloc`, which points at the Rust runtime's own fixed pages. Two hours of
reading, no new measurement. See the twelfth pass in `docs/ASSESSMENT.md`.*

*A remediation pass on the evening of 26 August closed the whole editing tier of the eleventh pass
except the abstract, and restored criterion 5 to 5 and criterion 6 to 4.5. All six statements
denying an instrument the study used are rewritten, four of the five far-tail sites are synced (the
abstract is the fifth and is the author's), the toolchain is named in §`sec:baremetal` and
`tab:testbed`'s caption now lists the three protocol rows the confirmation host missed instead of
claiming it met them, H1's revisit uses the campaign that settles H1's own clause, and the
peak-RSS order-of-magnitude phrasing carries a host at five sites. All five figure defects are
closed, including two that had been open since the ninth pass. Six new generated macros retire the
last typed measured values in Chapter 6. Two lessons are worth keeping. `bbox_inches="tight"` did
**not** fix `fig:effects`' clipped label, because a tight bbox crops to the artists it can measure
and the overhang was not one of them: one shared `fig.supxlabel` did, and it is better design
anyway. And rewriting diagram 07's band first made things worse, typing eight measured values into a
hand-authored SVG where two had been, before the statistics moved to the caption as macros. When
editing a hand-drawn diagram, count the numbers you leave behind. Also: `refresh_thesis.sh` now
pools the bare-metal histogram sidecars, which it previously did not, so the far-tail macros can no
longer keep stale values silently. See the remediation pass in `docs/ASSESSMENT.md`.*

*The eleventh grading pass, 26 August 2026 evening, is the first on record to lower two areas at
once, and the cause is worth carrying because it will recur. The bare-metal campaign closed the
instrumentation ceiling that had held criterion 3's data half at 4 since the third pass: zero CPU
steal over 60 sampling intervals, `perf` counters at the operation scope, pooled histograms giving
360 000 to 5 761 198 operations per group, and a far tail that separates the two languages with Rust
lower. Twenty of its macros were recomputed from the raw logs and every one matched, so that is
three consecutive passes with no wrong measured value. **Then the pass found fourteen places still
describing a study with less evidence than this one has.** Six deny an instrument that was used, and
the worst of those is falsified ninety lines later in its own chapter (§6.4.3 says the gap is
unexplained "for want of hardware counters" and §`sec:baremetal` reports the counters). Five summary
sites still call the far tail unresolved, including `tab:findings`'s RQ1 row and the abstract. §6.3
promises the bare-metal run "replaces these numbers" where §`sec:baremetal` says confirmation and
not replacement, and §5.6's promise that a rerun "regenerates the artifacts verbatim" is now
falsified by the thesis's own new section rather than merely unenforceable. Two further findings are
not staleness but substance. The confirmation changed a **fifth** variable nobody named, the
toolchain, so §`sec:baremetal`'s "changes one thing that matters, the machine" is false as written
and `tab:testbed`'s caption promises a protocol the host missed on four rows. And the peak-RSS
allocator effect fell from 32.9--34.4 MiB to 1.9--3.2 MiB with the allocator configuration matched,
so the "order of magnitude" gap between the allocator and language effects did not survive the
change of host, which three summary sites state without attaching a host. Criterion 5 went 5 to 4.5
on the three Chapter 7 sites and H1's revisit, criterion 6 went 4.5 to 4.0 on the level-4
consistency clause and not on the abstract. **The lesson for the next integration: sync the summary
tables, the threats table, the hypothesis revisit and the statistical-treatment section in the same
pass as the new results section, because those four are where a grader looks and they are the four
that were missed.** See the eleventh pass in `docs/ASSESSMENT.md` for the site list with line
numbers. Current open work is `docs/TODO.md` § *Do now*.*

*Last updated: 27 August 2026. Open checklist rewritten in `docs/TODO.md` (*Do now*). Prior note: Four length passes on 24, 25 and 26 August took the declared figure
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
