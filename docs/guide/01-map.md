# 01 Map of the repository

Everything that sits at the root of `thesis.local`, including hidden tools.
Paths are from the repository root. Gitignored items still appear on a working
tree. They are marked.

**Do not move the document sources, the prose screens, or `bibliography.bib`
out of the root.** Every `.tex` file resolves `figures/`, `diagrams/pdf/`,
`template/figures/`, and `ai_statement.tex` from here. That is why
`archive/` no longer builds in place.

## Thesis documents (edit these)

| Path | What it is |
| --- | --- |
| `Ha_Vien_Mastersthesis_2026.tex` | Canonical **full draft**. UH submission filename. Not supervisor-approved. |
| `Thesis_v3.tex` | Supervisor-facing skeleton: full Chapter 1, five argument paragraphs in chapters 2-8. |
| `Thesis_Plan_v2.tex` | Supervisor-facing plan. |
| `Ha_Vien_Mastersthesis_2026_short.tex` | Compression pass of the full draft. Not a deliverable. Tooling in `.compress/`. |
| `ai_statement.tex` | Shared declaration on generative-AI use. Edit this file, never a copy. |
| `source_audit.tex` | Generated citation-audit document for the full draft. Only the Part 1 review tick is hand-edited. |
| `source_audit_v3.tex` | Same audit scoped to `Thesis_v3`. Own numbering, own tick sidecar (`.bibaudit/reviewed_v3.txt`). |
| `bibliography.bib` | Hand-written BibTeX. Not bulk-exported from Scholar. |
| `HYthesisML.cls` | Department class file all of the above build on. |
| `AGENT.md` | Working contract for edits. |
| `README.md` | Public map and quick start. |

Matching `.pdf` files sit beside the sources. Matching `.aux`, `.log`, `.bbl`
and so on at the root are leftovers from an editor that ignored `.latexmkrc`.
Safe to delete. Intermediates belong in `build/`.

## Evidence (must match thesis claims)

| Path | What it is |
| --- | --- |
| `spec/` | Frozen specification and the language-neutral conformance suite. |
| `cpp/` | C++23 UECM implementation. |
| `rust/` | Rust UECM implementation, structurally mirrored with `cpp/`. |
| `bench/` | Latency, throughput, resource harness, plotting, and `refresh_thesis.sh`. |
| `faults/` | RQ2 fault-injection catalogue plus Loom, Shuttle, and Miri. |
| `ffi/` | RQ4 C++ host over a Rust component via a C ABI. |
| `docker/` | Rocky 8.10 image with the campaign toolchain pinned. Not itself a testbed. |
| `figures/` | Generated plots, tables, and LaTeX macros. Do not hand-edit. |
| `diagrams/` | Source diagrams (SVG, drawio), rendered PDF/PNG, label gate. |

Each of `spec/conformance/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/`, and
`docker/` has its own `README.md`.

## Notes, archive, template

| Path | What it is |
| --- | --- |
| `docs/` | This documentation folder. See [`../README.md`](../README.md). Working notes include the grading record, the open-work list, and `CODE_REVIEW.md` (agent pass, 16 September 2026; not TODO item D2). The C++ reading path is [`../cpp-guide/`](../cpp-guide/README.md). |
| `archive/` | Superseded variants. Not maintained. See `archive/README.md`. |
| `template/` | Cover-page dictionaries and HY logo that `HYthesisML.cls` loads by path. `template/upstream/` is the pristine CSM template the class was taken from. |
| `build/` | latexmk intermediates. Gitignored. Safe to delete. |

## Root scripts

| Path | What it is |
| --- | --- |
| `build_deck.py` | Nokia-branded slide deck. Reads generated artefacts. Never transcribe numbers into it. |
| `pdfpreview.py` | Rasterise PDF pages into `.pdf-preview/` (WSL webview shows none). |
| `pdfannots.py` | Pull highlights and notes out of a commented PDF in `docs/review/`. |

## Prose screens (root, leading-dot)

| Path | What it is |
| --- | --- |
| `.aitells.py` | Language-model fingerprints and house style (em dash, semicolon, colon capital). Counts, except four house-style zeros. |
| `.vocab.py` | Hard Latinate words with plain equivalents. |
| `.b2.py` | CEFR-frequency vocabulary via `wordfreq`. Companion to `.vocab.py`. |
| `.readability.py` | Flesch, Flesch-Kincaid, Fog, sentence-length mix. Whole document. |
| `.chapter_readability.py` | Same counters, per chapter. Writes `docs/CHAPTER_READABILITY.md`. |
| `.acronyms.py` | **Gate**: every front-matter acronym written out at first use. |

Details: [06 Prose screens](06-prose.md).

## Hidden tooling directories

| Path | What it is | Git |
| --- | --- | --- |
| `.bibaudit/` | Builds `source_audit.tex` (full draft) and `source_audit_v3.tex` (`--document v3`) from the bibliography, `.bbl`, and the evidence notes. `reviewed.txt` and `reviewed_v3.txt` mirror Part 1 ticks. | Tracked |
| `.compress/` | One-shot tools for the short cut. Run from the repository root. | Tracked |
| `.cursor/rules/thesis-quality.mdc` | Cursor rule: read `AGENT.md` before thesis edits. | Tracked |
| `.cursor/skills/` | `thesis-grade-csm`, `create-pptx-master-thesis`, `drawio`, `code-visualizer-thesis`. | Tracked (pptx toolkit path is gitignored) |
| `.latexmkrc` | Sends `.aux` and friends to `build/`, PDF to the root. | Tracked |
| `.dockerignore` | What the campaign image leaves out. | Tracked |
| `.gitignore` | See list below. | Tracked |
| `.prose-scratch/` | Disposable candidate paragraphs for the screens. | Gitignored |
| `.pdf-preview/` | Rasterised PDF pages. | Gitignored |
| `.deck-assets/` | PNG rasters of `figures/*.pdf` for the deck. | Gitignored |
| `.venv-pptx/` | Local Python env for `python-pptx`. | Gitignored |
| `slides_preview/` | Slide renders for visual review. | Gitignored |
| `docs/review/` | Commented reviewer PDFs. | Gitignored |
| `.vscode/` | Editor settings. | Gitignored |
| `.git/` | Version control. | — |

## Generated or local products at the root

| Path | What it is | Git |
| --- | --- | --- |
| `Ha_Vien_Mastersthesis_2026.pdf` (and the other PDFs) | Built documents. | Tracked when they are the current deliverable |
| `Rust_vs_Cpp_Nokia_RAN_thesis.pptx` | Colloquium deck from `build_deck.py`. | Gitignored |
| `source_audit.pdf` | Citation-audit PDF of the full draft. | Tracked |
| `source_audit_v3.pdf` | Same audit scoped to `Thesis_v3`. | Tracked |

## What `.gitignore` is protecting

Campaign logs in `bench/results/` (the working copy). HDR sidecars over 100 MB
(`*.hist.jsonl`). C++ and Rust build trees. FFI host binaries. Fault-injection
built binaries. Docker scratch. latexmk junk. The files in the gitignored table
above.

`bench/results-canonical/` and `bench/results-canonical2/` are **tracked
snapshots**. `bench/results/` is the live directory the refresh script prefers
and is gitignored, so a fresh checkout needs the canonical campaign copied in
(or `git add -f` of the capture files `AGENT.md` names).
