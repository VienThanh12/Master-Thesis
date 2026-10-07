# Intermediate files (.aux, .log, .bbl, .bcf, .fls, .toc) are written to build/,
# so the repository root shows sources rather than eighty regenerated artefacts.
# The PDF and its SyncTeX index still land beside the sources, where the editor,
# bench/refresh_thesis.sh, and the tracked submission copy expect them.
$aux_dir = 'build';
$out_dir = '.';

# AGENT.md documents `latexmk -pdf <doc>.tex`; default to the same engine so a
# bare `latexmk <doc>.tex` cannot silently produce a DVI instead.
$pdf_mode = 1;

# tab:pipeline in Thesis_v4.tex inputs figures/tab_pipeline.tex, which is built
# by bench/pipeline_table.py (also run from bench/refresh_thesis.sh).
$pre_tex_code = 'system("python3", "bench/pipeline_table.py") unless -e "figures/tab_pipeline.tex";';
