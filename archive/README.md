# Archive

Superseded document variants, kept because they record work that was really done, not because
they are maintained. Nothing here is a deliverable, and none of it is checked by
`bench/refresh_thesis.sh` or the prose scripts.

| File | What it was | Why it stopped |
| --- | --- | --- |
| `plain_thesis.tex` / `.pdf` | Plain-language variant of the full draft (121 pages) for a reader with no 5G background. Same argument, same data, same generated macros | Superseded by `Thesis_POC.tex`, which is the reference version |
| `thesis-vi.tex` / `.pdf` | Vietnamese translation (~108 pages + appendices) | Rebuilt 24 Aug 2026 from `Ha_Vien_Mastersthesis_2026.tex` via modular `archive/vi/ch*.tex` fragments. Uses `figures/gen_macros.tex` and generated tables. Build from repo root: `latexmk -xelatex -output-directory=build archive/thesis-vi.tex`, then copy `build/thesis-vi.pdf` here. |
| `thesis_wbm_full_backup.tex` / `.pdf` | Backup of the skeleton before the bibliography move | One word different from `Thesis_v2.tex` and still on `\bibliographystyle{abbrv}` |
| `Thesis_POC.tex.bak-before-cuts` | `Thesis_POC.tex` as it stood before the August length cuts | Snapshot only. Git history holds the same content |
| `Thesis_Plan.pdf` | First thesis plan | Superseded by `Thesis_Plan_v2.pdf`. Its source is no longer in the repository |

These sources resolve `figures/`, `diagrams/`, and `ai_statement.tex` relative to the repository
root, so they do not build from this directory. Reviving one means fixing those paths and, for
`thesis-vi.tex`, keeping the `archive/vi/` chapter fragments in sync when the English thesis changes.
