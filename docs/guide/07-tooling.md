# 07 Tooling

Build, audit, deck, compression, Cursor, and PDF helpers. Run paths from the
repository root unless a component README says otherwise.

## LaTeX

| Piece | Role |
| --- | --- |
| `.latexmkrc` | `$aux_dir = 'build'`, PDF at the root, `$pdf_mode = 1`. |
| `HYthesisML.cls` | Department class. |
| `template/` | Cover-page dictionaries (English, Finnish, Swedish) and HY logo. |
| `template/upstream/` | Pristine CSM template the class was taken from. Do not edit as if it were the thesis. |
| `build/` | Intermediates. Gitignored. |

```bash
latexmk -pdf Thesis_v3.tex
```

An editor that overrides the aux directory will still drop `.aux` and `.log`
at the root. Safe to delete. `refresh_thesis.sh` already falls back to those
copies.

## Docker (pinned toolchain, not a testbed)

| Path | Role |
| --- | --- |
| `docker/Dockerfile` | Rocky Linux 8.10, `gcc-toolset-15`, rustc 1.97.1, jeprof, perf, prof-enabled jemalloc. |
| `docker/run.sh` | `build`, `check`, `campaign`, smoke. |
| `docker/entrypoint.sh`, `preflight.sh` | Inside the image. |
| `docker/VALIDATION.md`, `docker/validation/` | Image checks. |
| `docker/.scratch/` | Gitignored smoke outputs, so a test run cannot become "the newest campaign". |

```bash
docker/run.sh build
docker/run.sh check
docker/run.sh campaign --repeats 20 --duration 3
```

The container pins the **compiler major**. It shares the host kernel. See
[`docker/README.md`](../../docker/README.md). Do not write that the guest and
reported campaigns share a toolchain: `\GuestGpp` 15.1.1 vs `\MainGpp` 15.2.1.

## Slide deck

```bash
python3 build_deck.py    # -> Rust_vs_Cpp_Nokia_RAN_thesis.pptx (gitignored)
```

Needs the Nokia toolkit under `.cursor/skills/create-pptx-master-thesis/`
(gitignored path), `python-pptx`, and `pymupdf`. Rasterised plots land in
`.deck-assets/`. Visual-review renders in `slides_preview/`.

Every number is read from generated artefacts. The build refuses a stale
value. `check_prose_style` walks the saved deck.

## Citation audit (`.bibaudit/`)

| Script | Role |
| --- | --- |
| `build_audit.py` | Generates `source_audit.tex` by default (full draft, all 111 keys). `--document v3` writes `source_audit_v3.tex` with `Thesis_v3`'s own numbering (61 cited of 111). `--all-documents` adds the other documents' numbers as extra columns. Refuses to run when a `.bbl` disagrees with cite keys (`--allow-stale` exists and should not be used). |
| `reviewed.txt` | Mirror of Part 1 review ticks for the draft audit. |
| `reviewed_v3.txt` | Same sidecar for `source_audit_v3.tex`. Separate on purpose: a draft tick does not mean the skeleton's citing sentence was checked. |
| `cite_audit.py` | Cite-key helper. |
| `bib_verify.py`, `meta_checks.py`, `link_check.py` | Metadata and URL checks. |
| `fetch_sources.py`, `oa_fetch.py`, `oa_fetch2.py`, `fetch_theses.py` | Retrieve sources. |
| `evidence.py`, `evidence2.py`, `abstracts.py`, `abstract_sweep.py` | Evidence and abstract sweeps. |
| `pdfgrep.py`, `sweep_diff.py`, `verify_candidates.py` | Search and diff helpers. |

**Never hand-edit `source_audit.tex` or `source_audit_v3.tex` except the Part 1 tick** (`$\square$` →
`$\blacksquare$`). The generator reads ticks back before overwriting and
prints `review ticks: N of 111` for the draft (or `N of 61` for `Thesis_v3`). Read that line after every rebuild: a
regeneration silently wiped 22 of them on 1 September 2026.

Quoted source text is passed through, em dashes included, so `.aitells.py`
hits inside a quotation are expected.

Durable records: `docs/Sources_evidence.md`, `docs/LITERATURE_NOTES.md`,
`docs/citation.md`.

```bash
.bibaudit/build_audit.py && latexmk -pdf source_audit.tex
.bibaudit/build_audit.py --document v3 && latexmk -pdf source_audit_v3.tex
```

## Short cut (`.compress/`)

Tools for `Ha_Vien_Mastersthesis_2026_short.tex`. Invoke from the root.

| Script | Role |
| --- | --- |
| `shortcheck.py` | **Gate**: citation keys, labels, refs, macros the short cut dropped. |
| `lengthprice.py` | Price words, floats, page span per division. Takes any `.tex`. |
| `reloc.py`, `movapp.py` | Move a body block into appendices, or reorder them. |
| `strip.py`, `deref.py`, `retarget.py` | Delete relocated material and repoint references. Filename of the short document is a module constant: read the top before running. |
| `drafts/` | Rewritten chapter candidates and the pre-relocation backup. |

Run `shortcheck.py` after every compression edit. A dropped label is exactly
the defect no LaTeX build catches.

## PDF helpers

| Script | Role |
| --- | --- |
| `pdfpreview.py` | Rasterise pages to `.pdf-preview/` for the WSL editor. `./pdfpreview.py Thesis_v3.pdf`, or a page range. |
| `pdfannots.py` | Extract highlights and comments from `docs/review/*.pdf`. |

`docs/review/` is gitignored. Create it locally. A marked-up copy may carry
Nokia-internal comments.

## Cursor

| Path | Role |
| --- | --- |
| `.cursor/rules/thesis-quality.mdc` | Always-applied: read `AGENT.md` before thesis edits. Grade table, prose style, non-negotiable claims. |
| `.cursor/skills/thesis-grade-csm/` | Official CSM seven-area matrix, calibration, `scripts/texaudit.py`. Writes a canvas and a dated pass in `docs/ASSESSMENT.md`. |
| `.cursor/skills/create-pptx-master-thesis/` | Nokia PPTX skill. Toolkit files gitignored. |
| `.cursor/skills/drawio/` | draw.io diagrams. |
| `.cursor/skills/code-visualizer-thesis/` | Code visualiser for this repo. |

`AGENT.md` is the contract those rules point at. The skill does not replace
it.

## Grading canvases

Dated canvases from the CSM grading skill are mentioned in
`docs/ASSESSMENT.md` (`thesis-grade-csm-sep07-rev2`, `thesis-grade-csm-sep11`).
They may live beside the editor's canvas store rather than in git. The durable
copy of every pass is `docs/ASSESSMENT.md`.
