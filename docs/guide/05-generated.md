# 05 Generated layer

Nothing the thesis quotes as a measured number is typed into prose, slides, or
scripts. It is generated into `figures/gen_*.tex` and cited by macro name.

**Never hand-edit** `figures/gen_macros.tex`, `gen_complexity.tex`,
`gen_artefacts.tex`, `gen_adoption.tex`, `gen_baremetal.tex`, or
`gen_guest.tex`. Never transcribe their values into `build_deck.py`.

A generated macro can still be the **wrong quantity** for the sentence holding
it. Check the definition, not just the value. Two live traps: a `Pct` macro
read as a multiple, and a `lo--hi` range macro wrapped in math mode (typesets
as two minus signs).

## What `bench/refresh_thesis.sh` does

After a campaign, a latency-budget run, queue contention, an FFI measurement,
or a fault-injection run:

1. Pool HDR histogram sidecars (`pool_hist.py`) in `bench/results/` and
   `bench/results-baremetal/`, so the far tail is the pooled statistic.
2. `plot_figures.py` → plots, tables, `gen_macros.tex`.
3. `baremetal_facts.py`, `guest_facts.py` → confirmation and guest macros.
4. Re-render diagrams that quote campaign numbers.
5. `diagrams/check_labels.py` — prose-style gate on figure labels.
6. `complexity.py` (if `lizard` is present), `artefact_facts.py`.
7. `adoption_cost.py` **without** `--measure` (replays recorded build time).
8. `build_deck.py`.
9. `latexmk -pdf Ha_Vien_Mastersthesis_2026.tex`.

It does **not** rebuild `Thesis_v3.pdf`, `Thesis_Plan_v2.pdf`,
`source_audit.pdf`, or `source_audit_v3.pdf`.

## `figures/` — plots, tables, macros

### Macro files (generated)

| File | Writer | Prefix / contents |
| --- | --- | --- |
| `gen_macros.tex` | `bench/plot_figures.py` | Unprefixed. Reported campaign. |
| `gen_guest.tex` | `bench/guest_facts.py` | `\Guest*` |
| `gen_baremetal.tex` | `bench/baremetal_facts.py` | `\Bm*` |
| `gen_complexity.tex` | `bench/complexity.py` | LoC / complexity proxies |
| `gen_artefacts.tex` | `bench/artefact_facts.py` | Parity size, seam size, taxonomy outcomes |
| `gen_adoption.tex` | `bench/adoption_cost.py` | RQ4 axes |

### Tables (generated `.tex`, `\input` by the thesis)

`tab_latency.tex`, `tab_resource.tex`, `tab_resident.tex`, `tab_overload.tex`,
`tab_overload_test.tex`, `tab_significance.tex`, `tab_equivalence.tex`,
`tab_jitter.tex`, `tab_budget.tex`, `tab_contention.tex`, `tab_ffi.tex`,
`tab_adoption.tex`, `tab_taxonomy.tex` (from `faults/results/taxonomy.csv`),
`tab_complexity.tex`, `tab_loc.tex`.

### Plots (generated PDF)

`fig_latency_vs_load.pdf`, `fig_throughput_vs_load.pdf`,
`fig_tail_percentiles.pdf`, `fig_load_sweep.pdf`, `fig_overload.pdf`,
`fig_resources.pdf`, `fig_budget.pdf`, `fig_ffi_cost.pdf`,
`fig_taxonomy.pdf`, `fig_effects.pdf`.

## `diagrams/` — figures the prose argues from

| Kind | Files | Notes |
| --- | --- | --- |
| Hand-authored SVG | `01_` … `19_` (plus some `.drawio`) | Edit the SVG or drawio, then render. |
| Generated | `20_` … `29_` | Built by `diagrams/build_new_diagrams.py` / `dsl.py`. 20-29 quote campaign numbers. |
| Rendered | `diagrams/pdf/`, `diagrams/png/` | `diagrams/render.py`. PNG is what the deck reads. |
| Gates | `check_labels.py`, `check_fit.py` | Labels: no em dash, dash aside, or prose semicolon. Scope is diagrams a document actually includes. |

House style on labels is the same as thesis prose. TikZ `--` is path syntax
and must not be "fixed". Numeric ranges use `$2$--$15$`.

## Slide deck

`build_deck.py` writes `Rust_vs_Cpp_Nokia_RAN_thesis.pptx` (gitignored). It
reads macros, table bodies, `taxonomy.csv`, and the environment capture of
the plotted campaign. It fails rather than print a stale value. After save it
runs `check_prose_style` on every text run. A hit exits non-zero.

`detex()` renders a generated table cell of `---` as `n/a`, because a slide
gets no em dash.

## Sync rule when numbers change

1. Regenerate via `bench/refresh_thesis.sh` (never hand-edit macros).
2. Re-read every prose claim that cites those macros in the full draft
   **and** in `Thesis_v3.tex`.
3. Rebuild `Thesis_v3.tex` and the plan if they quote the new macros.
4. Check `docs/ASSESSMENT.md` / `docs/TODO.md` if tail or RSS claims moved.
