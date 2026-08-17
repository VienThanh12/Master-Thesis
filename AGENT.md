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
| **`Thesis_Plan_v2.pdf`** | `Thesis_Plan_v2.tex` | **Reviewed — supervisor-facing** | Approved plan: gap, RQs, methodology, timeline, contributions. Keep in sync with `Thesis_v1.tex`. |
| **`Thesis_v1.pdf`** | `Thesis_v1.tex` | **Reviewed — supervisor-facing** | One-bullet-per-argument chapter skeleton for supervisor read-through. This is what goes to the supervisor alongside the plan. |
| **`Thesis_POC.pdf`** | `Thesis_POC.tex` | **Full draft — not yet final** | Canonical long-form thesis (~113–127 pages). Rich figures, generated numbers, full argument. **Everything still needs review** before submission. |
| `ai_statement.tex` | — | **Declaration in the author's name** | Required statement on generative-AI use, `\input` by `Thesis_POC.tex` and `Thesis_v1.tex` before the bibliography. Shared on purpose: edit this file, never a copy. It must keep describing what actually happened, so revise it whenever the workflow changes. |
| `plain_thesis.tex` / `thesis-vi.tex` | variants | Secondary / stale | Do not edit unless explicitly asked. `thesis-vi.tex` is broken (missing bib). |
| Artefacts | `spec/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/` | Implementation + evidence | Must stay consistent with claims in `Thesis_POC.tex`. |

### Sync rule

When you change **claims, RQs, scope, methodology, or contributions**:

1. Update **`Thesis_v1.tex`** if the supervisor skeleton should reflect it.
2. Update **`Thesis_Plan_v2.tex`** if the plan’s status, timeline, or framing changes.
3. Update **`Thesis_POC.tex`** for the full argument, figures, tables, and cross-references.
4. Rebuild affected PDFs and run the verification steps in §5.

When you change **measured numbers**:

1. Regenerate via `bench/refresh_thesis.sh` (never hand-edit `figures/gen_macros.tex`,
   `figures/gen_complexity.tex`, or `figures/gen_artefacts.tex`).
2. Re-read every prose claim that cites those macros (Chapters 7–9, abstract, discussion).
3. Check `ASSESSMENT.md` and `TODO.md` “after bare-metal campaign” items if tail or RSS claims move.

---

## 2. Grade criteria (Finnish 1–5 scale)

The thesis is assessed on **six criteria** (simplified from the UH data-science master's
matrix). Current self-assessment is in **`ASSESSMENT.md`** (durable record; keep aligned
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
| **3** | **Research data and method** | Sound method + decision-grade data | **4.5** | **Bare-metal tail campaign.** Results come from a dedicated but virtualised KVM Xeon guest, where the far tail below saturation cannot be resolved. Also missing: hardware counters and allocation profiles for the unexplained peak-RSS and operation-level results. |
| **4** | **Presentation of thesis results** | Honest, reproducible, figure–table consistency | **4.5** | RQ1 tail still open; Figures 7.1/7.3 cannot separate curves on current host. Lifts with same campaign as criterion 3. |
| **5** | **Discussion and conclusions** | Validity analysis, no over-claiming, hypotheses revisited | **5** | Maintain register: “cannot tell” ≠ “equivalent”. H1 is *ambiguous in framing*, not simply supported. |
| **6** | **Academic text** | Precise prose, no contradictions, clean structure | **5** | Housekeeping: fill `\censors{}{}{}` when faculty assigns examiners; swap in official `UH_DS_MSc.cls`. |

**Overall mean (unweighted): 4.8** — held at 4.5 on criteria 3 and 4 **deliberately** until
bare-metal tail evidence exists. Do not round those half-grades in prose without updating the
reasoning in `ASSESSMENT.md`.

### Criterion checklist (apply to every thesis edit)

Before considering a change done, ask:

**1 — Objectives & RQs**

- [ ] Does the edit preserve the precise gap (language isolated; spec + concurrency model fixed)?
- [ ] Are all four RQs still answered in the right chapter with the right artefact?
- [ ] Does RQ2 still include the five boundary classes (deadlock, lost update, reference-cycle leak, release-build overflow, worker-failure blast radius) that can refute the premise?

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
3. **RQ2 is falsifiable** — five in-guarantee defect classes + **five** boundary classes; catalogue must not contain only defects Rust prevents. Two boundary classes (reference-cycle leak, release-build integer overflow) came back with the **C++ tooling ahead**; do not drop them to tidy the narrative. The lock-order deadlock is detected by TSan **intermittently** (about 30% of runs), not reliably and not never.
4. **Honest performance claims** — the end-to-end sweep is dominated by the cross-thread handoff and the operation is a fraction of a percent of it (`\BudgetCoreShareMax`), so a median comparison on that path cannot bound a language effect; the far tail still requires bare metal. Past saturation the languages *do* diverge (`\OverloadThrRatio`), and that result is resolved.
5. **Peak RSS** — a real language effect that reproduces under both allocators, but the **allocator effect is the larger one**; do not revert to “allocator only” or drop the language effect. Quote the generated macros rather than remembered numbers.
6. **FFI** — interleaved native vs seam calls; tax bounded, not “free”; `unsafe` confined to seam; core stays `unsafe`-free.
7. **No over-claim on Rust** — eliminates data races and aliasing errors, not race conditions or lock-order deadlocks.

---

## 4. Chapter map (`Thesis_POC.tex`)

| Ch. | Title | Primary criterion |
| --- | --- | --- |
| 1 | Introduction | 1 |
| 2 | Background | 2 |
| 3 | Problem context (UECM) | 1, 2 |
| 4 | Objectives | 1 |
| 5 | Research methodology | 3 |
| 6 | Design and implementation | 3 |
| 7 | Experimental setup and evaluation | 3, 4 |
| 8 | Discussion | 5 |
| 9 | Conclusion and future work | 5 |
| App. | Fault-injection example | 4 |

`Thesis_v1.tex` mirrors this structure as **one bullet per argument move** per chapter.
Chapters 6–9 in `Thesis_v1.tex` are intentionally **empty placeholders** until supervisor
review of the skeleton is complete — do not fill them without explicit author request.

---

## 5. Verification workflow (run after substantive changes)

```bash
# Parity and tests
spec/conformance/run.sh          # 3 phases: oracle, hand-written vectors, generated vectors
cd cpp && ctest --test-dir build --output-on-failure
cd rust && cargo test --release
faults/run_faults.sh
faults/run_model_checking.sh     # Loom + Shuttle on the two boundary classes (fast)
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
latexmk -pdf Thesis_v1.tex
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
./.aitells.py Thesis_POC.tex      # language-model fingerprints: dash asides, transition
                                  # openers, promotional adjectives, sentence-length uniformity
./.vocab.py Thesis_POC.tex        # hard Latinate words
./.readability.py Thesis_POC.tex  # sentence and paragraph load
```

All three report counts rather than errors, so read them as frequency. The one hard rule is the
first: **no em dashes in thesis prose**, neither `---` nor a literal `—`. As of 17 August 2026
`.aitells.py` reports four dash hits in `Thesis_POC.tex`, all correct typography (one compound
proper name, three numeric ranges). If that number rises, the new ones are yours. The full style
constraint is in the prose-style section of `.cursor/rules/thesis-quality.mdc`.

**Acceptance gates**

- `Thesis_POC.log`: **zero errors**, zero undefined references/citations.
- `./.aitells.py` on every file whose prose changed: no em-dash asides introduced.
- Figure/table macros in prose match `figures/gen_macros.tex`.
- No figure contradicts its table (see `ASSESSMENT.md` refinement pass for past failures).
- `build_deck.py` rebuilds and reports “Layout: all added shapes inside the template content band”.
- If abstract changed: visually inspect page 3 (abstract form + CCS + keywords).

---

## 6. What agents should not do

- **Do not** treat `Thesis_POC.pdf` as supervisor-approved; only `Thesis_Plan_v2.pdf` and `Thesis_v1.pdf` are in that bucket today.
- **Do not** hand-edit generated files under `figures/` except source diagrams in `diagrams/`.
- **Do not** transcribe measured numbers into `build_deck.py`; it reads them from the generated artefacts and fails loudly when one is missing.
- **Do not** claim testbed-grade tail latency from the virtualised host.
- **Do not** remove boundary defect classes or sanitiser-only C++ outcomes to tidy the narrative.
- **Do not** expand `Thesis_v1.tex` chapters 6–9 without explicit instruction.
- **Do not** commit secrets, Nokia-internal identifiers, or confidential traces.
- **Do not** create git commits unless the author explicitly asks.

---

## 7. Key reference files

| File | Use |
| --- | --- |
| `ASSESSMENT.md` | Full criterion-by-criterion grading notes and blockers |
| `.cursor/skills/thesis-grade-csm/` | Grading skill: the official seven-area CSM matrix, calibration anchors and discounted false positives from past passes, and `scripts/texaudit.py` for build, cross-reference, bibliography and placeholder gates |
| `TODO.md` | Phase checklist, bare-metal prep, post-campaign re-check list |
| `LITERATURE_NOTES.md` | Citation upgrades and literature gaps |
| `bench/TESTBED.md` | Bare-metal protocol (only path to criterion 3/4 → 5 on tail) |
| `bench/artefact_facts.py` | Generates `figures/gen_artefacts.tex`: record sizes (compiled probes), parity-suite coverage, conformance campaign size, FFI seam size. Anything measured that no campaign log holds belongs here, not in the prose |
| `spec/SPECIFICATION.md` | Fairness baseline; freeze before implementation changes. §11.4–11.5 cover the reference model, generated vectors, sanitisers, Miri and coverage |
| `spec/conformance/model.py` | Independent Python implementation of the spec; the oracle behind the generated vectors. Never derive its expectations from `cpp/` or `rust/` |
| `faults/results/model_checking.md` | Loom/Shuttle outcomes for the boundary classes (RQ2's "at what stage and cost") |
| `README.md` | Repo layout and quick start |

---

## 8. Supervisor submission bundle (current)

When preparing material for **Keijo Heljanko** (supervisor) and Nokia instructors
(**Christoph Luneburg**, **Petteri Kotimaa**):

1. `Thesis_Plan_v2.pdf` — plan, status, timeline (dated; status table must match repo reality).
2. `Thesis_v1.pdf` — chapter skeleton; chapters 1–5 + appendix populated; 6–9 reserved.
3. Optionally reference `Thesis_POC.pdf` as the **working full draft** (clearly labelled not final).

After supervisor feedback on the skeleton, expand `Thesis_v1.tex` chapters 6–9 and port
refinements into `Thesis_POC.tex` in the same edit pass so the two do not diverge.

---

*Last updated: August 2026. Revise this file when supervisor review status, grade blockers, or document roles change.*
