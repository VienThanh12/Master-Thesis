# Archive

Superseded document variants, kept because they record work that was really done, not because
they are maintained. Nothing here is a deliverable, and none of it is checked by
`bench/refresh_thesis.sh` or the prose scripts.

| File | What it was | Why it stopped |
| --- | --- | --- |
| `plain_thesis.tex` / `.pdf` | Plain-language variant of the full draft (121 pages) for a reader with no 5G background. Same argument, same data, same generated macros | Superseded by `Thesis_POC.tex`, which is the reference version |
| `thesis-vi.tex` / `.pdf` | Vietnamese translation (75 pages) | Broken and stale. Its 113 citations render as `[?]` because bibtex was never run for it, and it never read `figures/gen_macros.tex`, so its numbers are hand-copied and predate the 15-repeat campaign |
| `thesis_wbm_full_backup.tex` / `.pdf` | Backup of the skeleton before the bibliography move | One word different from `Thesis_v1.tex` and still on `\bibliographystyle{abbrv}` |
| `Thesis_POC.tex.bak-before-cuts` | `Thesis_POC.tex` as it stood before the August length cuts | Snapshot only. Git history holds the same content |
| `Thesis_Plan.pdf` | First thesis plan | Superseded by `Thesis_Plan_v2.pdf`. Its source is no longer in the repository |

These sources resolve `figures/`, `diagrams/`, and `ai_statement.tex` relative to the repository
root, so they do not build from this directory. Reviving one means fixing those paths and, for
`thesis-vi.tex`, porting the generated macros so its numbers come from the campaign rather than
from a hand copy.
