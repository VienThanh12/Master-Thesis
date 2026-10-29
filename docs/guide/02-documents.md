# 02 Documents

The PDFs in this repository do not share a status. Treat them as different
objects that happen to live in one tree.

The source of truth for status is [`AGENT.md` §1](../../AGENT.md). This page
is a working map: what to open, what to rebuild, what not to confuse.

## The four thesis PDFs

| File | Source | Status | Role |
| --- | --- | --- | --- |
| `Thesis_Plan_v2.pdf` | `Thesis_Plan_v2.tex` | **Reviewed, supervisor-facing** | Approved plan: gap, RQs, methodology, timeline, contributions. Keep in sync with `Ha_Vien_Mastersthesis_2026.tex`. |
| `Ha_Vien_Mastersthesis_2026.pdf` | `Ha_Vien_Mastersthesis_2026.tex` | **Submission manuscript** | University filename (`Lastname_Firstname_Mastersthesis_Year`). Called `Thesis_v5` until 29 October 2026. Chapter 1 is the full introduction. Chapter 2 is a related-work spine as of 21 September 2026. Chapters 3-8 are five argument paragraphs each, in plain prose. |
| `Ha_Vien_Mastersthesis_2026_draft.pdf` | `Ha_Vien_Mastersthesis_2026_draft.tex` | **Draft, not for submission** | The previous file of the university name, retired 29 October 2026. Not a copy of the submission manuscript. |
| `Ha_Vien_Mastersthesis_2026_short.pdf` | `Ha_Vien_Mastersthesis_2026_short.tex` | Compression pass, in progress | Shorter cut of the **same** draft. Neither supervisor-facing nor a submission candidate. No claim may appear here that is not in the full draft. |

## Shared pieces

| File | Role |
| --- | --- |
| `ai_statement.tex` | `\input` by the submission manuscript, the draft, and the short cut, before the bibliography. One file. Keep it describing what actually happened. |
| `bibliography.bib` | Shared bibliography. |
| `HYthesisML.cls` | Class. Loaded from the repository root. |
| `template/` | Cover dictionaries and HY logo the class loads by path. |
| `figures/gen_*.tex` | Generated number macros. The skeleton and both drafts `\input` the same six files. |
| `figures/tab_*.tex`, `figures/fig_*.pdf` | Generated tables and plots. |
| `diagrams/pdf/` | Diagrams included by the documents. |

## How the submission manuscript is shaped

- **Chapter 1** of `Ha_Vien_Mastersthesis_2026.tex` is the full introduction, with later-section
  and appendix references retargeted to labels this file actually has.
- **Chapter 2** is a related-work spine as of 21 September 2026. Do not
  compress it back to five paragraphs.
- **Chapters 3-8** stay five argument paragraphs. Do not add a sixth. Do not
  put Chapter 1 back to a short skeleton.
- Key terms sit in the front matter, after the list of acronyms. The manuscript
  carries one appendix, Host and campaign configuration (`appendix:config`).
- `bench/refresh_thesis.sh` rebuilds `Ha_Vien_Mastersthesis_2026.pdf`.
  A prose-only rebuild is `latexmk -pdf Ha_Vien_Mastersthesis_2026.tex`.
  The draft is not rebuilt.

Older notes that call the evaluation chapter 7 or the discussion chapter 8
are using a retired nine-chapter numbering. The draft and the skeleton have
matched eight-chapter lists since 26 August 2026.

## Other PDFs at the root

| File | Role |
| --- | --- |
| `source_audit.pdf` | Every bibliography entry, ordered as in the full draft's reference list, with the citing sentence beside the source's own words. Built by `.bibaudit/build_audit.py`. See [07 Tooling](07-tooling.md). |
| `source_audit_v5.pdf` | The same audit scoped to the submission manuscript. `--document v5`. |
| `Rust_vs_Cpp_Nokia_RAN_thesis.pptx` | Colloquium deck. Gitignored. Built by `build_deck.py`. |

## How to rebuild

```bash
latexmk -pdf Ha_Vien_Mastersthesis_2026.tex   # submission manuscript
latexmk -pdf Thesis_Plan_v2.tex               # plan
.bibaudit/build_audit.py && latexmk -pdf source_audit.tex
.bibaudit/build_audit.py --document v5 && latexmk -pdf source_audit_v5.tex
bench/refresh_thesis.sh                       # regenerate figures + macros + submission PDF + deck
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
`Ha_Vien_Mastersthesis_2026.pdf`. The draft is
`Ha_Vien_Mastersthesis_2026_draft.pdf`, and it is not the deposit.
