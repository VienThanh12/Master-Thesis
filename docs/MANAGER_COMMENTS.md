# Nokia instructor comments on `Thesis_v5`

**Date:** 20 September 2026
**Resolved in `Thesis_v5`:** 21 September 2026
**Name:** the annotated PDF was `Thesis_v3`. The skeleton was renamed `Thesis_v5` on 28 September 2026.
**Source:** annotation layer of the commented PDF (44 physical pages). Pages with
markup: 11, 13, 14, 17, 21, 23, 25, 26, 27, 29, 30, 31, 33, 34, 44. Other pages
had none.
**Ticked against:** `Thesis_v5.tex` (the annotated document; now longer than 44
pages) and `Ha_Vien_Mastersthesis_2026.tex` (full draft). The draft was not the
file that was marked up. It still carries several of the same sentences, so it
is ticked too.

Status:

| Mark | Meaning |
| --- | --- |
| **Done** | The request is met in that source. |
| **Partial** | Some of it is met. A reader could still ask the same question. |
| **Open** | The comment still applies. |

The 12–16 September wording pass on the skeleton closed many of the compressed
phrases without these comments in hand. The remaining work is the methodology
cluster (pages 21, 23, 26, 27) and, in the full draft, the Chapter 1
contribution and results preview the skeleton no longer prints.

---

## Scoreboard

| Where | Done | Partial | Open |
| --- | --- | --- | --- |
| `Thesis_v5.tex` | 46 | 0 | 0 |
| Full draft | 15 | 19 | 12 |

Forty-six numbered comments, matching the markup list (p.13 items 3–5 counted
separately, p.44 counted once). The two documents do not share a score:
several p.13–14 items are **Done** in the skeleton because Chapter 1 no longer
prints the contribution and results preview, and **Open** in the draft because
that preview is still there.

---

## Resolution in `Thesis_v5`

All 46 comments are resolved in the skeleton. The 21 September pass:

1. removes the three marked uses of “which”;
2. lists and defines the seven boundary classes;
3. defines the FFI seam and Resource Acquisition Is Initialization (RAII);
4. names the reported host and the KVM guest userland, kernel, and hypervisor;
5. states the cache and branch-predictor controls and their residual limit;
6. places the overload floor in the open-loop histogram fill, while keeping
   the campaign macros unchanged;
7. distinguishes overload CPU from the operation-scope instruction and cycle
   counters;
8. rewrites the memory, H3, safety, seam, and timing explanations in direct
   language.

`Thesis_v5.pdf` rebuilds to 49 pages with no LaTeX errors, undefined
references, undefined citations, overfull boxes, or float errors.

**On the full draft (`Ha_Vien_Mastersthesis_2026.tex`), same comments**

The skeleton dropped the Chapter 1 contribution and results preview. The draft
still has it, so the p.13–14 cluster is **open there even where v3 is done.**
Fix that section before anyone reads the long PDF: contribution count, “Three
are results,” “boundary classes,” “FFI seam,” “natively,” “final,” “divides
twice,” and the instruction to move results talk until after the setup.

---

## Page 11 — wording

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | Crossed-out “which” | Minor | **Done** | **Open** | Skeleton replaces all three marked clauses with direct sentences. |

---

## Page 13 — research questions and contributions

Eleven marks. This was one of the two pages the instructor wanted rewritten.

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | Cite *Just Use Rust* (Meneely et al., SVM@ICSE 2025) | Must | **Done** | **Done** | `\cite{meneely2025justuserust}` after the CWE mapping paragraph in both Chapter 1s, in the plan, and in `bibliography.bib`. Same cite on p.44. |
| 2 | Spell out FFI at first use | Must | **Done** | **Done** | Abstract: “foreign function interface (FFI) prototype.” RQ4: “foreign function interface (FFI).” Acronyms list carries it. |
| 3–5 | Crossed-out “for”, “S”, “T” on the hypotheses | Minor | **Done** | **Done** | Hypotheses rewritten as full sentences. H1 no longer leans on a hanging “for.” |
| 6 | “What do you mean by this?” on “H2 is stated so that it can fail.” | Should | **Done** | **Done** | Phrase gone. Both documents now say the catalogue spans seven classes safe Rust is expected to stop and seven it is not, so the study can locate the boundary. |
| 7 | “Avoid very short sentences like this” on “Three are results.” | Should | **Done** | **Open** | Gone from `Thesis_v5.tex`. Draft §1.4 still opens with “Three are results, and the first is…” |
| 8 | Contributions paragraph does not follow from the text before it | Should | **Done** | **Open** | Skeleton Chapter 1 ends at the RQs and the Meneely paragraph. No contribution list. Draft still has the six-contribution block immediately after the hypotheses. |
| 9 | “Do you mean: This work has three main contributions?” | Should | **Done** | **Open** | Same as 7–8. Draft still counts two artefacts, three results, and “the last” guidelines. |
| 10 | “What do you mean by this?” on the attribution bound | Should | **Done** | **Partial** | Skeleton defines both clocks: the end-to-end round-trip includes the queue, wake-up, and core call; the second measurement removes the queue and handoff. Draft Chapter 1 still compresses that into one sentence before the setup. |
| 11 | “Is this a fourth contribution?” on the migration guidelines | Must | **Done** | **Open** | Skeleton has no numbered contribution list. Guidelines live in Chapter 6. Draft still says six contributions and then “the last is” after “three are results,” which is the inconsistency that was marked. |

---

## Page 14 — results preview in the introduction

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “This sentence does not make sense” on findings found while reading results planned differently | Should | **Done** | **Open** | Phrase gone from the skeleton. Draft §1.4 still has “Both were found while reading results the study had planned to report differently.” |
| 2–3 | “out of bounds memory access classes?” / “Or something else?” on “boundary classes” | Must | **Done** | **Partial** | Skeleton lists all seven at first use and states that safe Rust is expected not to stop them. They are not out-of-bounds classes. |
| 4 | “What do you mean by this?” on the RQ4 paragraph (seam, unsafe, core, adoption cost, API) | Should | **Done** | **Partial** | Skeleton defines the boundary, names the three adoption-cost axes, and gives the unsafe scope and per-call denominator after the setup. Draft §1.4 still piles them into the introduction. |
| 5 | “What is an ‘FFI seam’?” | Must | **Done** | **Partial** | Skeleton defines it as the thin C-ABI layer that converts between the C++ host and unchanged Rust core. |
| 6 | Name the three costs beyond the seam | Should | **Done** | **Open** | Skeleton migration subsection names them. Draft §1.4 still says “Three costs beyond the seam are measured” without listing them there. |
| 7 | “in C++???” on “called natively” | Must | **Done** | **Open** | Skeleton: “the same signal call made directly” and the figure caption “directly” vs “through the seam.” Draft §1.4 and `tab:findings` still say “called natively.” |
| 8 | “Final in what sense?” | Should | **Done** | **Open** | Skeleton replaces *final* with “complete for the fourteen-class catalogue set in advance and host-independent.” Draft still uses *final*. |
| 9 | “On performance the answer divides twice” | Should | **Done** | **Open** | Skeleton results split into below-saturation, past-saturation, and the end-to-end vs core-timed-apart clocks, with `fig:loadmap`. Draft §1.4 still uses the compressed opener. |
| 10 | End-to-end median vs isolated operation | Should | **Done** | **Partial** | Skeleton: “This sweep cannot bound a language effect” next to `fig:e2eclock` and `fig:budget`. Draft Chapter 1 still has to carry that before the reader has seen those figures. |
| 11 | “Discussion all of this does not make sense before the setup is discussed. Please move elsewhere.” | Must | **Done** | **Open** | Strongest structural mark. Skeleton Chapter 1 no longer previews findings. Draft §1.4 is still a results-and-interpretation section in the introduction. |

---

## Page 17 — C++ background

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “Please explain what RAII is.” | Must | **Done** | **Done** | Skeleton expands Resource Acquisition Is Initialization and explains that cleanup is tied to object lifetime, so leaving scope destroys the guard and releases its lock. |

---

## Page 21 — experimental setup

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “What is the underlying operating system?” | Must | **Done** | **Done** | Skeleton names `\MainHostDistro{}` and `\MainKernel{}` for the reported host and `\GuestDistro{}` and `\GuestKernel{}` for the guest. |
| 2 | “For both setups both host, hypervisor, and guest OS.” | Must | **Done** | **Done** | Skeleton states that the reported campaign has no hypervisor and names the KVM guest's CPU, hypervisor capture, userland, and kernel. |

The reported campaign is bare metal. There is no guest OS to name for that
column. The instructor’s wording assumed two virtualised setups. The honest
fix is the draft table: host OS, hypervisor (or none), and, for the KVM
column only, guest userland.

---

## Page 23 — experimental controls

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | SplitMix64 and FNV-1a: cite if public, else drop | Should | **Done** | **Done** | Both cited: Steele et al. 2014 for SplitMix64, RFC 9923 for FNV-1a. Skeleton says why: C++’s default integer hash is often the number itself, Rust’s is strong on purpose, so unpinned they would have been the measurement. |
| 2 | Branch prediction and cache layout: how closely controlled? | Must | **Done** | **Partial** | Skeleton states the matched seeds, operation order, interleaved repeats, and pinned cores. It also states the residual: caches were not flushed and branch predictors were not primed. |

---

## Page 25 — results presentation

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “Please plot these, it is hard to follow from text only.” | Must | **Done** | **Done** | `fig:loadsweep` (latency and throughput vs offered load), `fig:loadmap` (knees and overload point), `fig:overload`, `fig:resources`, `fig:e2eclock`, `fig:budget`. The “within 2 µs at the median” claim is now next to the sweep figure, quoted via macros. |

---

## Page 26 — overload behaviour

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “Any theory why Rust falls back so badly?” | Should | **Done** | **Partial** | Skeleton distinguishes the campaign result from certified follow-up probes and places the floor in the capped open-loop histogram fill. It states that the published ratio is an instrument result, not a maximum-rate language ranking. |
| 2 | “Could its design be changed?” | Must | **Done** | **Partial** | Skeleton reports that closed-loop and fill-disabled runs recover to the closed-loop band, while replacing Rust's reply handle does not move the floor. This identifies the design lever without attributing the floor to Rust itself. |
| 3 | “compiled?” on “Every one of the first seven is a compile error in Rust.” | Must | **Done** | **Done** | Method: each class is a small program in both languages. “The safe-Rust side is compiled and, where it compiles, run under a bounded timeout.” Results: each of the first seven is a compile error in Rust, valid C++. That is an observed `rustc` rejection, not a desk judgement. |

---

## Page 27 — CPU and the FFI bound

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “CPU inverts with the regime.” | Should | **Done** | **Partial** | Skeleton: “CPU changes sign with the load. At the chosen load of `\ReprLoad` kops/s Rust uses at most `\CpuDiffAbsMax` percentage points less. Once the service no longer keeps up, CPU per finished call is much higher.” Draft `tab:findings` still says “CPU inverts across the regimes,” then explains it. |
| 2 | “Did you measure this after the overload?” | Should | **Done** | **Partial** | Skeleton now names both operating points: CPU per finished call at `\OverloadLoad`, and hardware counters only for the isolated core call on the second bare-metal host. |
| 3 | More instructions, or slower instructions? | Must | **Done** | **Partial** | Skeleton quotes `\BmInstrDelta`, `\BmCycleDelta`, and `\BmMissDelta` for the isolated core call and states that no counter split was recorded for the overload path. It therefore answers what the data can settle without transferring the counters to the wrong operating point. |
| 4 | “The Rust overhead over calling C++ natively for any operation is at most 10.91%.” | Must | **Done** | **Partial** | Skeleton scopes the bound to “that signalling call” / “a real signal call,” not “any operation.” Abstract the same. Draft still says “called natively” and “of an operation” in `tab:findings`. The number is `\FfiOpBoundPct`, never typed by hand. |

---

## Page 29 — safety discussion

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “What do you mean by this?” on “the difference is one of kind” | Should | **Done** | **Partial** | Skeleton conclusion now states the stage difference directly: Rust rejects the seven programs before execution; C++ sanitisers can report a defect only when a test executes its path. |

---

## Page 30 — memory / allocator

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “???” on the allocator / jemalloc / host / RSS paragraph | Must | **Done** | **Partial** | Skeleton now separates the language effect, allocator effect, host comparison, allocator accounting, and CPU result. It states that the language effect repeats, the allocator effect's size is host-bound, and the extra process RAM is not more live application data. |

---

## Page 31 — limitations

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “???” on “could have missed, not by the failure to detect one” | Should | **Done** | **Done** | Skeleton now says that H3 is supported by the upper bound on the paired difference and that non-significance alone would not show a small tax. |
| 2 | “What do you mean by ‘countable’?” | Must | **Done** | **Open** | Phrase gone from the skeleton. Guidelines now: “Keeping `unsafe` at the seam bounds what has to be checked.” Draft appendix still has “a fixed, countable thing” and the comparison table “mechanically countable.” Name the metric: `\FfiUnsafeFns` functions, `\CoreUnsafe` unsafe sites in the core. |

---

## Page 33 — conclusion

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “???” on “An end-to-end operation here is 0.250% language.” | Must | **Done** | **Partial** | Skeleton conclusion defines the end-to-end clock and names the queue, wake-up, and core call. It then states that only `\BudgetCoreShareMax\%` is core work, so the clock cannot bound a compiler effect. |
| 2–3 | “measured apart” / “What do you mean by this?” | Should | **Done** | **Partial** | Skeleton conclusion defines the second measurement as the core call with the queue and cross-thread handoff removed before quoting `\BudgetCoreRatio`. |

---

## Page 34 — conclusion / future work

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “???” on “All unsafe is confined to the seam.” | Must | **Done** | **Partial** | Skeleton: “All of the `unsafe` sits in the seam, and the core is checked free of it,” with `\FfiEntryPoints` C entry points, `\FfiSeamLines` lines, `\FfiUnsafeFns` functions, `\CoreUnsafe` sites. Draft still uses “the seam” in the conclusion without repeating those counts. |
| 2 | “arm?” on “only the system-allocator arm inherits it.” | Should | **Done** | **Done** | “Arm” renamed to “variant” in the 14–15 September pass. Skeleton future work: “only the system allocator variant gets it.” |

---

## Page 44 — bibliography

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | Add *Just Use Rust* | Must | **Done** | **Done** | Same as p.13 item 1. Entry `meneely2025justuserust` in `bibliography.bib`. |

---

## The four themes, ticked

### 1. Compressed prose

All “What do you mean by this?” / “???” marks are resolved in the skeleton.
The full draft’s Chapter 1 still reads as the annotated pages 13–14.

### 2. Define technical terms

| Term | v3 | Draft |
| --- | --- | --- |
| FFI | **Done** | **Done** |
| FFI seam | **Done** | **Partial** (defined once in §1.4, then reused) |
| RAII | **Done** | **Done** |
| Experimental “arm” | **Done** (now “variant”) | **Done** |
| Boundary classes | **Done** (defined and listed at first use) | **Partial** |
| Countable | **Done** (removed) | **Open** |
| Natively | **Done** (“made directly”) | **Open** |
| Final | **Done** (replaced with evidence status) | **Open** |

### 3. Experimental methodology (pages 21, 23, 25, 26, 27)

| Ask | v3 | Draft |
| --- | --- | --- |
| OS / hypervisor / guest OS | **Done** | **Done** (`tab:testbed`) |
| Branch prediction / cache | **Done** | **Partial** |
| Plots | **Done** | **Done** |
| Why Rust degrades under overload | **Done** (instrument effect, not a language maximum) | **Partial** |
| Could the Rust design be changed? | **Done** | **Partial** |
| Where CPU / instruction measurements were taken | **Done** | **Partial** |
| 10.91% scoped to the measured call | **Done** | **Partial** |
| Language vs implementation vs environment | **Done** | **Partial** |

### 4. Structure of the argument

| Ask | v3 | Draft |
| --- | --- | --- |
| Move results talk until after the setup | **Done** | **Open** (§1.4) |
| Contribution count internally consistent | **Done** (list removed) | **Open** (2 + 3 + “the last”) |

---

## What not to do while closing the rest

- Do not add `isolcpus`.
- Do not type `\FfiOpBoundPct`, `\BudgetCoreShareMax`, or the overload
  throughputs by hand. Quote the macros.
- Do not copy WSL2 or 7443P probe kops/s into `figures/gen_macros.tex`. Those
  belong to `docs/OVERLOAD_MECHANISM.md`. The campaign macros stay the
  published floor.
- Do not expand `Thesis_v5.tex` Chapters 3-8 past five argument paragraphs, and do not compress Chapter 2 back to five paragraphs.
  A sentence in an existing paragraph, or a small table, is the lever.
- Do not treat “cannot tell” as “equivalent.”
- `seam_double_free` is `double_free` through `unsafe`, not a new class.

---

## How this file relates to the others

| File | Job |
| --- | --- |
| This note | Instructor markup, item by item, ticked against both sources. |
| `docs/OVERLOAD_MECHANISM.md` | Evidence for the p.26–27 overload comments. Not yet in the skeleton. |
| `docs/TODO.md` | Process list. Item **T** points here. |
| `AGENT.md` | Grade criteria and non-negotiables. Wins on claims. |
