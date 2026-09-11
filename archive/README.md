# Archive

Superseded document variants, kept because they record work that was really done, not because
they are maintained. Nothing here is a deliverable, and none of it is checked by
`bench/refresh_thesis.sh` or the prose scripts.

| File | What it was | Why it stopped |
| --- | --- | --- |
| `plain_thesis.tex` / `.pdf` | Plain-language variant of the full draft (121 pages) for a reader with no 5G background. Same argument, same data, same generated macros | Superseded by `Ha_Vien_Mastersthesis_2026.tex` (called `Thesis_POC` until 19 August 2026) |
| `Thesis_v3-vi.tex` / `.pdf` | Vietnamese translation of the supervisor skeleton `Thesis_v3.tex` | Snapshot of the 11 September 2026 skeleton. Chapter fragments in `archive/vi-v3/`. Not a deliverable. Build from repo root: `latexmk -xelatex -output-directory=build archive/Thesis_v3-vi.tex`, then copy `build/Thesis_v3-vi.pdf` here. Distinct from `thesis-vi.tex`, which translates the full draft. |
| `thesis-vi.tex` / `.pdf` | Vietnamese translation of the full draft (~108 pages + appendices) | Rebuilt 24 Aug 2026 from `Ha_Vien_Mastersthesis_2026.tex` via modular `archive/vi/ch*.tex` fragments. Uses `figures/gen_macros.tex` and generated tables. Build from repo root: `latexmk -xelatex -output-directory=build archive/thesis-vi.tex`, then copy `build/thesis-vi.pdf` here. |
| `thesis_wbm_full_backup.tex` / `.pdf` | Backup of the skeleton before the bibliography move | One word different from `Thesis_v3.tex` and still on `\bibliographystyle{abbrv}` |
| `Thesis_POC.tex.bak-before-cuts` | `Thesis_POC.tex` as it stood before the August length cuts | Snapshot only. Git history holds the same content |
| `Thesis_Plan.pdf` | First thesis plan | Superseded by `Thesis_Plan_v2.pdf`. Its source is no longer in the repository |
| `UH_DS_MSc.cls` / `UH-logo.png` | Reconstructed data-science master's class and the logo its title page loaded | Superseded by the department's own `HYthesisML.cls`, which no document has loaded since it landed. The class is the only thing that ever referenced the logo, so the two retire together |
| `rollback-20260827-220354/` | Dated snapshot of `AGENT.md`, both thesis sources, `TODO.md` and thirty generated figures and tables, taken before the canonical bare-metal integration | Git history holds the same state at that commit. Moved out of the repository root on 8 September 2026 |

These sources resolve `figures/`, `diagrams/`, and `ai_statement.tex` relative to the repository
root, so they do not build from this directory. Reviving one means fixing those paths. For
`thesis-vi.tex`, keep the `archive/vi/` chapter fragments in sync when the English full draft
changes. For `Thesis_v3-vi.tex`, keep `archive/vi-v3/` in sync when `Thesis_v3.tex` changes.
