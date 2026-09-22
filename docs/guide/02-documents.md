# 02 Documents

The PDFs in this repository do not share a status. Treat them as different
objects that happen to live in one tree.

The source of truth for status is [`AGENT.md` §1](../../AGENT.md). This page
is a working map: what to open, what to rebuild, what not to confuse.

## The four thesis PDFs

| File | Source | Status | Role |
| --- | --- | --- | --- |
| `Thesis_Plan_v2.pdf` | `Thesis_Plan_v2.tex` | **Reviewed, supervisor-facing** | Approved plan: gap, RQs, methodology, timeline, contributions. Keep in sync with `Thesis_v3.tex`. |
| `Thesis_v3.pdf` | `Thesis_v3.tex` | **Reviewed, supervisor-facing** | Eight-chapter argument the supervisor reads. Chapter 1 is the draft introduction. Chapters 2-8 are five argument paragraphs each, in plain prose. Quotes generated macros. Abstract dated 11 September 2026. Was `Thesis_v2` until 8 September 2026. |
| `Ha_Vien_Mastersthesis_2026.pdf` | `Ha_Vien_Mastersthesis_2026.tex` | **Full draft, not final** | Canonical long-form thesis. UH submission filename (`Lastname_Firstname_Mastersthesis_Year`). That name says nothing about review. Was `Thesis_POC` until 19 August 2026. |
| `Ha_Vien_Mastersthesis_2026_short.pdf` | `Ha_Vien_Mastersthesis_2026_short.tex` | Compression pass, in progress | Shorter cut of the **same** draft. Neither supervisor-facing nor a submission candidate. No claim may appear here that is not in the full draft. |

## Shared pieces

| File | Role |
| --- | --- |
| `ai_statement.tex` | `\input` by the full draft, the skeleton, and the short cut, before the bibliography. One file. Keep it describing what actually happened. |
| `bibliography.bib` | Shared bibliography. |
| `HYthesisML.cls` | Class. Loaded from the repository root. |
| `template/` | Cover dictionaries and HY logo the class loads by path. |
| `figures/gen_*.tex` | Generated number macros. The skeleton and both drafts `\input` the same six files. |
| `figures/tab_*.tex`, `figures/fig_*.pdf` | Generated tables and plots. |
| `diagrams/pdf/` | Diagrams included by the documents. |

## How the skeleton differs from the full draft

- **Chapter 1** of `Thesis_v3.tex` is the draft introduction, with later-section
  and appendix references retargeted to labels this file actually has.
- **Chapters 2-8** stay five argument paragraphs. Do not add a sixth. Do not
  expand them into the full draft's chapter prose. Do not put Chapter 1 back
  to a short skeleton.
- The skeleton carries two appendices: Key terms (`appendix:terms`) and Host
  and campaign configuration (`appendix:config`), matching the draft's
  Appendices A and D. Cross-references inside the config appendix are
  retargeted to labels this file has. It needs no further appendices.
- It carries a subset of the draft's figures. Captions are trimmed. Image
  sources are shared, not copied.
- `bench/refresh_thesis.sh` rebuilds the **full draft PDF**, not `Thesis_v3.pdf`.
  After macros move, rebuild the skeleton with `latexmk -pdf Thesis_v3.tex`.

Older notes that call the evaluation chapter 7 or the discussion chapter 8
are using a retired nine-chapter numbering. The draft and the skeleton have
matched eight-chapter lists since 26 August 2026.

## Other PDFs at the root

| File | Role |
| --- | --- |
| `source_audit.pdf` | Every bibliography entry, ordered as in the full draft's reference list, with the citing sentence beside the source's own words. Built by `.bibaudit/build_audit.py`. See [07 Tooling](07-tooling.md). |
| `source_audit_v3.pdf` | The same audit scoped to `Thesis_v3`: 61 cited works with that document's numbering, and the 50 shared-`.bib` entries it does not cite. `--document v3`. |
| `Rust_vs_Cpp_Nokia_RAN_thesis.pptx` | Colloquium deck. Gitignored. Built by `build_deck.py`. |

## How to rebuild

```bash
latexmk -pdf Ha_Vien_Mastersthesis_2026.tex   # full draft
latexmk -pdf Thesis_v3.tex                    # supervisor skeleton
latexmk -pdf Thesis_Plan_v2.tex               # plan
.bibaudit/build_audit.py && latexmk -pdf source_audit.tex
.bibaudit/build_audit.py --document v3 && latexmk -pdf source_audit_v3.tex
bench/refresh_thesis.sh                       # regenerate figures + macros + full-draft PDF + deck
```

`.latexmkrc` writes intermediates to `build/` and the PDF beside the source.
Zero LaTeX errors and no undefined references are required after a substantive
change.

## Archive (do not edit unless asked)

`archive/` holds superseded variants: `plain_thesis.tex`, `thesis-vi.tex`
(Vietnamese full draft), `Thesis_v3-vi.tex` (Vietnamese skeleton snapshot),
`thesis_wbm_full_backup.tex`, `Thesis_POC.tex.bak-before-cuts`, the v1 plan
PDF, the retired `UH_DS_MSc.cls`, and `rollback-20260827-220354/`. Details:
[`archive/README.md`](../../archive/README.md).

## Supervisor bundle

When preparing material for the supervisor: `Thesis_Plan_v2.pdf` and
`Thesis_v3.pdf`. Optionally point at `Ha_Vien_Mastersthesis_2026.pdf` as the
working full draft, labelled not final. Port feedback into **both**
`Thesis_v3.tex` and `Ha_Vien_Mastersthesis_2026.tex` in the same pass.
