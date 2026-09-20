# Nokia instructor comments on `Thesis_v3`

**Date:** 20 September 2026
**Source:** annotation layer of the commented PDF (44 physical pages). Pages with
markup: 11, 13, 14, 17, 21, 23, 25, 26, 27, 29, 30, 31, 33, 34, 44. Other pages
had none.
**Ticked against:** `Thesis_v3.tex` (the annotated document; now longer than 44
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
| `Thesis_v3.tex` | 25 | 15 | 6 |
| Full draft | 15 | 19 | 12 |

Forty-six numbered comments, matching the markup list (p.13 items 3–5 counted
separately, p.44 counted once). The two documents do not share a score:
several p.13–14 items are **Done** in the skeleton because Chapter 1 no longer
prints the contribution and results preview, and **Open** in the draft because
that preview is still there.

---

## What is still open (do these)

**On the skeleton (`Thesis_v3.tex`), before sending it back**

1. **p.26–27 overload.** The skeleton still says the cause “sits in the wider
   path that passes work between threads.” The full draft already names the
   open-loop histogram fill. `docs/OVERLOAD_MECHANISM.md` (19 Sep, certified on
   the 7443P) is the evidence. Write the mechanism into Chapter 5 and the
   discussion, including “could the design be changed?”. Do not copy probe
   kops/s into `figures/gen_macros.tex`. Quote the campaign macros. Say that
   closed loop and cap-0 recover the gap, and that the published
   `\OverloadThrRatio` is the campaign instrument.
2. **p.27 instructions vs slower instructions, at overload.** The counters
   (`\BmInstrDelta*`, `\BmCycleDelta*`) are the *operation* microbenchmark on
   the second host, not the overload floor. Either answer with those macros
   and state the operating point, or say the overload path was not counted
   that way.
3. **p.23 branch prediction and cache.** Interleaving, pinning, identical
   seeds, and matched hashing are in the text. A short paragraph should say
   what was *not* controlled (cache warmed naturally, no explicit branch
   priming) so the comment is answered rather than implied.
4. **p.21 guest column.** Name `\GuestDistro{}` and `\GuestVirt{}` next to
   the KVM sentence. The reported host already has `\MainHostDistro{}` and
   “there is no hypervisor.” The draft’s `tab:testbed` is the model. Do not
   add a sixth results paragraph. One sentence, or a small table, is enough.
5. **p.31 H3.** “a bound on a cost the measurement could have missed, not from
   the failure to detect one” is still in `Thesis_v3.tex`. The draft’s H3
   rewrite is the replacement.
6. **p.11 crossed-out “which”.** Two candidates remain in the opening of
   Chapter 1: “each of which the standards call a user equipment” and “each
   of which has to complete”. A third sits in the problem statement:
   “iterator invalidation, which are silent at compile time.”
7. **p.33 “one of kind”.** The conclusion still opens the safety paragraph
   with that phrase. The discussion already explains compile-time rejection
   versus sanitiser coverage in plain language. Copy that explanation up.

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
| 1 | Crossed-out “which” | Minor | **Open** | **Open** | Chapter 1 still has “each of which the standards call a user equipment (UE)” and “each of which has to complete.” Problem statement still has “which are silent at compile time.” |

---

## Page 13 — research questions and contributions

Eleven marks. This was one of the two pages the instructor wanted rewritten.

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | Cite *Just Use Rust* (Meneely et al., SVM@ICSE 2025) | Must | **Done** | **Done** | `\cite{meneely2025justuserust}` after the CWE mapping paragraph in both Chapter 1s, in the plan, and in `bibliography.bib`. Same cite on p.44. |
| 2 | Spell out FFI at first use | Must | **Done** | **Done** | Abstract: “foreign function interface (FFI) prototype.” RQ4: “foreign function interface (FFI).” Acronyms list carries it. |
| 3–5 | Crossed-out “for”, “S”, “T” on the hypotheses | Minor | **Done** | **Done** | Hypotheses rewritten as full sentences. H1 no longer leans on a hanging “for.” |
| 6 | “What do you mean by this?” on “H2 is stated so that it can fail.” | Should | **Done** | **Done** | Phrase gone. Both documents now say the catalogue spans seven classes safe Rust is expected to stop and seven it is not, so the study can locate the boundary. |
| 7 | “Avoid very short sentences like this” on “Three are results.” | Should | **Done** | **Open** | Gone from `Thesis_v3.tex`. Draft §1.4 still opens with “Three are results, and the first is…” |
| 8 | Contributions paragraph does not follow from the text before it | Should | **Done** | **Open** | Skeleton Chapter 1 ends at the RQs and the Meneely paragraph. No contribution list. Draft still has the six-contribution block immediately after the hypotheses. |
| 9 | “Do you mean: This work has three main contributions?” | Should | **Done** | **Open** | Same as 7–8. Draft still counts two artefacts, three results, and “the last” guidelines. |
| 10 | “What do you mean by this?” on the attribution bound | Should | **Partial** | **Partial** | Skeleton now has `fig:e2eclock` and `fig:budget` in the results chapter, with `\BudgetCoreShareMax\%` language work and the rest a cross-thread handoff. Draft Chapter 1 still compresses that into one sentence before the setup. |
| 11 | “Is this a fourth contribution?” on the migration guidelines | Must | **Done** | **Open** | Skeleton has no numbered contribution list. Guidelines live in Chapter 6. Draft still says six contributions and then “the last is” after “three are results,” which is the inconsistency that was marked. |

---

## Page 14 — results preview in the introduction

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “This sentence does not make sense” on findings found while reading results planned differently | Should | **Done** | **Open** | Phrase gone from the skeleton. Draft §1.4 still has “Both were found while reading results the study had planned to report differently.” |
| 2–3 | “out of bounds memory access classes?” / “Or something else?” on “boundary classes” | Must | **Partial** | **Partial** | Defined as the seven classes safe Rust is expected *not* to stop, not as out-of-bounds access. Results name leak, overflow, deadlock, seam double-free. Neither document lists all seven at first use. `fig:taxonomy` does. |
| 4 | “What do you mean by this?” on the RQ4 paragraph (seam, unsafe, core, adoption cost, API) | Should | **Partial** | **Partial** | Skeleton results name the three costs (build-time third-party share, first-party compile CPU, linkage-policy footprint) in the migration subsection, after the setup. Draft §1.4 still piles them into the introduction. |
| 5 | “What is an ‘FFI seam’?” | Must | **Partial** | **Partial** | Draft: “the FFI seam, the thin layer of code where the two languages meet.” Skeleton RQ4 expands FFI, then later says “move seam” and “C-ABI seam.” `fig:ffiseam` is in the skeleton. First use of the word *seam* in the skeleton is still light on definition. |
| 6 | Name the three costs beyond the seam | Should | **Done** | **Open** | Skeleton migration subsection names them. Draft §1.4 still says “Three costs beyond the seam are measured” without listing them there. |
| 7 | “in C++???” on “called natively” | Must | **Done** | **Open** | Skeleton: “the same signal call made directly” and the figure caption “directly” vs “through the seam.” Draft §1.4 and `tab:findings` still say “called natively.” |
| 8 | “Final in what sense?” | Should | **Partial** | **Open** | Skeleton: “RQ2 is final and does not depend on the host.” Still uses *final*. Draft: “Both of these results are final” and `tab:findings` cells marked Final. The draft RQ2 cell is the intended sense (catalogue outcome, host-independent). |
| 9 | “On performance the answer divides twice” | Should | **Done** | **Open** | Skeleton results split into below-saturation, past-saturation, and the end-to-end vs core-timed-apart clocks, with `fig:loadmap`. Draft §1.4 still uses the compressed opener. |
| 10 | End-to-end median vs isolated operation | Should | **Done** | **Partial** | Skeleton: “This sweep cannot bound a language effect” next to `fig:e2eclock` and `fig:budget`. Draft Chapter 1 still has to carry that before the reader has seen those figures. |
| 11 | “Discussion all of this does not make sense before the setup is discussed. Please move elsewhere.” | Must | **Done** | **Open** | Strongest structural mark. Skeleton Chapter 1 no longer previews findings. Draft §1.4 is still a results-and-interpretation section in the introduction. |

---

## Page 17 — C++ background

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “Please explain what RAII is.” | Must | **Partial** | **Done** | Draft §2.2 (`sec:cpplatency`) expands Resource Acquisition Is Initialization and says resource lifetime is tied to object lifetime. The skeleton has no C++-background section (Chapters 2–8 stay five-paragraph). First prose use is in the results, expanded there, and the acronyms list carries it. |

---

## Page 21 — experimental setup

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “What is the underlying operating system?” | Must | **Partial** | **Done** | Skeleton names `\MainHostDistro{}` and `\MainKernel{}` for the reported host. Draft `tab:testbed` has an Operating system row for all three machines. |
| 2 | “For both setups both host, hypervisor, and guest OS.” | Must | **Partial** | **Done** | Reported campaign: host OS named, “there is no hypervisor,” process runs on the machine. Guest campaign: KVM on `\GuestCpu{}`, `\GuestKernel{}` named. `\GuestDistro{}` and `\GuestVirt{}` are generated and used in the draft table, not quoted in the skeleton prose. |

The reported campaign is bare metal. There is no guest OS to name for that
column. The instructor’s wording assumed two virtualised setups. The honest
fix is the draft table: host OS, hypervisor (or none), and, for the KVM
column only, guest userland.

---

## Page 23 — experimental controls

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | SplitMix64 and FNV-1a: cite if public, else drop | Should | **Done** | **Done** | Both cited: Steele et al. 2014 for SplitMix64, RFC 9923 for FNV-1a. Skeleton says why: C++’s default integer hash is often the number itself, Rust’s is strong on purpose, so unpinned they would have been the measurement. |
| 2 | Branch prediction and cache layout: how closely controlled? | Must | **Open** | **Partial** | Held fixed: frozen spec, same workload and seeds, same shard count, CPU pinning, interleaved variants, matched opt level, pinned hash, jemalloc plus a system-allocator control, warm-up excluded from throughput (draft). Not claimed, and not written down in the skeleton: no explicit cache flush or branch priming. Cache state was allowed to evolve. The draft `tab:controls` is the place to add a residual row. Do not claim a control that was not run. |

---

## Page 25 — results presentation

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “Please plot these, it is hard to follow from text only.” | Must | **Done** | **Done** | `fig:loadsweep` (latency and throughput vs offered load), `fig:loadmap` (knees and overload point), `fig:overload`, `fig:resources`, `fig:e2eclock`, `fig:budget`. The “within 2 µs at the median” claim is now next to the sweep figure, quoted via macros. |

---

## Page 26 — overload behaviour

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “Any theory why Rust falls back so badly?” | Should | **Open** | **Partial** | Skeleton: primitives timed alone do not reproduce the order, so the cause is “the wider path that passes work between threads.” Draft: “Mechanism: open-loop histogram fill.” Working note `docs/OVERLOAD_MECHANISM.md` (19 Sep, 7443P): with the campaign cap the floor favours C++; with the cap at 0 both recover to closed loop and the language split goes away. That is a hypothesis with a certified check, not a campaign result. It is not in the skeleton. |
| 2 | “Could its design be changed?” | Must | **Open** | **Partial** | Queue synchronisation, queue allocation, and `sync_channel(1)` oneshot substitutions do not move the floor. Closed loop of the same service is not a C++ win. Future work already names async vs thread-per-shard. The instructor’s question is about whether the *implementation* rather than the language is at fault: the fill-cap result says the published ratio is the open-loop instrument. Skeleton does not say that. |
| 3 | “compiled?” on “Every one of the first seven is a compile error in Rust.” | Must | **Done** | **Done** | Method: each class is a small program in both languages. “The safe-Rust side is compiled and, where it compiles, run under a bounded timeout.” Results: each of the first seven is a compile error in Rust, valid C++. That is an observed `rustc` rejection, not a desk judgement. |

---

## Page 27 — CPU and the FFI bound

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “CPU inverts with the regime.” | Should | **Done** | **Partial** | Skeleton: “CPU changes sign with the load. At the chosen load of `\ReprLoad` kops/s Rust uses at most `\CpuDiffAbsMax` percentage points less. Once the service no longer keeps up, CPU per finished call is much higher.” Draft `tab:findings` still says “CPU inverts across the regimes,” then explains it. |
| 2 | “Did you measure this after the overload?” | Should | **Partial** | **Partial** | CPU-per-operation at overload is at `\OverloadLoad` kops/s. Instruction and cycle counters are the operation microbenchmark on the second host (`\BmInstrDelta*`, `\BmCycleDelta*`), not the overload floor. The skeleton quotes the first and not the second. |
| 3 | More instructions, or slower instructions? | Must | **Open** | **Partial** | Draft host-comparison paragraph: at operation scope Rust retires `\BmInstrDelta\%` fewer instructions and `\BmCycleDelta\%` fewer cycles, and misses cache `\BmMissDelta\%` as often. That answers the question for the *core call*, in the direction “less work.” It does not answer it for overload. The skeleton quotes none of those macros. |
| 4 | “The Rust overhead over calling C++ natively for any operation is at most 10.91%.” | Must | **Done** | **Partial** | Skeleton scopes the bound to “that signalling call” / “a real signal call,” not “any operation.” Abstract the same. Draft still says “called natively” and “of an operation” in `tab:findings`. The number is `\FfiOpBoundPct`, never typed by hand. |

---

## Page 29 — safety discussion

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “What do you mean by this?” on “the difference is one of kind” | Should | **Partial** | **Partial** | Discussion now states: some defects are compile errors, so they never become a runnable program; a sanitiser rules a defect out only of the runs a sanitiser test takes. Conclusion still opens with “On safety the gap is one of kind.” Draft figure caption still has “The difference is one of kind, not degree.” |

---

## Page 30 — memory / allocator

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “???” on the allocator / jemalloc / host / RSS paragraph | Must | **Partial** | **Partial** | Skeleton `sec:resources` now walks: language effect under both heaps, allocator effect, both real, language sign and size on all three hosts, allocator ratio host-bound, extra RAM past the heap on the quiet host, CPU sign-flip last. Draft `sec:hostcompare` has the jemalloc accounting. Still dense. A reader who wants the six-step outline (what was measured, hosts, language, allocator, virtualisation, what can be attributed) can follow it, but it is not labelled as such. |

---

## Page 31 — limitations

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “???” on “could have missed, not by the failure to detect one” | Should | **Open** | **Done** | Exact phrase still in skeleton H3. Draft H3: “What supports the hypothesis is the bound, not the failure to detect a difference,” plus the empty-crossing mistake on the first attempt. |
| 2 | “What do you mean by ‘countable’?” | Must | **Done** | **Open** | Phrase gone from the skeleton. Guidelines now: “Keeping `unsafe` at the seam bounds what has to be checked.” Draft appendix still has “a fixed, countable thing” and the comparison table “mechanically countable.” Name the metric: `\FfiUnsafeFns` functions, `\CoreUnsafe` unsafe sites in the core. |

---

## Page 33 — conclusion

| # | Comment | Pri. | v3 | Draft | Where it stands |
| --- | --- | --- | --- | --- | --- |
| 1 | “???” on “An end-to-end operation here is 0.250% language.” | Must | **Partial** | **Partial** | Both quote `\BudgetCoreShareMax\%`, never the bare number. Skeleton: “The rest is an operating system handoff. So that clock bounds nothing about either compiler,” with `fig:e2eclock` earlier. Still a short conclusion sentence. The figure is the calculation. |
| 2–3 | “measured apart” / “What do you mean by this?” | Should | **Partial** | **Partial** | Skeleton: “The same core timed apart is `\BudgetCoreRatio\times` faster in `\BudgetCoreFaster{}`.” Clearer than before. Still needs the pair “end-to-end round-trip” vs “core call with no queue in the path” in the conclusion itself, not only in Chapter 5. |

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

Most of the “What do you mean by this?” / “???” marks on the skeleton were
rewritten in the 12–16 September pass. The ones that remain in `Thesis_v3.tex`
are H3’s “could have missed,” the conclusion’s “one of kind,” and the overload
cause sentence. The full draft’s Chapter 1 still reads as the annotated pages
13–14.

### 2. Define technical terms

| Term | v3 | Draft |
| --- | --- | --- |
| FFI | **Done** | **Done** |
| FFI seam | **Partial** (“move seam” / “C-ABI seam”) | **Partial** (defined once in §1.4, then reused) |
| RAII | **Partial** (results + acronyms, no C++ section) | **Done** |
| Experimental “arm” | **Done** (now “variant”) | **Done** |
| Boundary classes | **Partial** (defined, not listed at first use) | **Partial** |
| Countable | **Done** (removed) | **Open** |
| Natively | **Done** (“made directly”) | **Open** |
| Final | **Partial** | **Open** |

### 3. Experimental methodology (pages 21, 23, 25, 26, 27)

| Ask | v3 | Draft |
| --- | --- | --- |
| OS / hypervisor / guest OS | **Partial** | **Done** (`tab:testbed`) |
| Branch prediction / cache | **Open** | **Partial** |
| Plots | **Done** | **Done** |
| Why Rust degrades under overload | **Open** | **Partial** (histogram fill named; note not copied into the skeleton) |
| Could the Rust design be changed? | **Open** | **Partial** |
| Where CPU / instruction measurements were taken | **Partial** | **Partial** |
| 10.91% scoped to the measured call | **Done** | **Partial** |
| Language vs implementation vs environment | **Partial** | **Partial** |

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
- Do not expand `Thesis_v3.tex` Chapters 2–8 past five argument paragraphs.
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
