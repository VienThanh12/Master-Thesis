# Intermediate files (.aux, .log, .bbl, .bcf, .fls, .toc) are written to build/,
# so the repository root shows sources rather than eighty regenerated artefacts.
# The PDF and its SyncTeX index still land beside the sources, where the editor,
# bench/refresh_thesis.sh, and the tracked submission copy expect them.
$aux_dir = 'build';
$out_dir = '.';

# AGENT.md documents `latexmk -pdf <doc>.tex`; default to the same engine so a
# bare `latexmk <doc>.tex` cannot silently produce a DVI instead.
$pdf_mode = 1;
