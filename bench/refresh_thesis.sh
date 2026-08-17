#!/usr/bin/env bash
# Regenerate every figure, table, and quoted number in the thesis from the raw
# measurement logs, then rebuild the PDF.
#
# Run this after a campaign (bench/campaign.sh), a latency-budget decomposition
# (bench/latency_budget.sh), a queue-contention microbenchmark
# (bench/queue_contention.sh), an FFI prototype run (ffi/build.sh), or a
# fault-injection run (faults/run_faults.sh). Nothing in the thesis prose is
# hand-copied from the data: the campaign summary numbers land in
# figures/gen_macros.tex and the prose refers to them by name, so this one
# command keeps text and data in step.
#
# Usage:
#   bench/refresh_thesis.sh                 # newest campaign in bench/results/
#   bench/refresh_thesis.sh --campaign bench/results/campaign-....jsonl
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"

echo "== regenerating figures, tables, and generated macros =="
python3 "$here/plot_figures.py" "$@"

# Diagrams 20-29 quote campaign numbers straight out of figures/gen_macros.tex,
# so they are rebuilt here for the same reason the prose is: a fresh campaign
# must not leave a stale figure behind. Diagrams 01-19 are hand-authored SVG
# and are only re-rendered, not regenerated.
echo "== regenerating diagrams that quote campaign numbers =="
python3 "$root/diagrams/build_new_diagrams.py"
if "$root/.venv-pptx/bin/python" -c 'import cairosvg' 2>/dev/null; then
  "$root/.venv-pptx/bin/python" "$root/diagrams/render.py" >/dev/null
elif python3 -c 'import cairosvg' 2>/dev/null; then
  python3 "$root/diagrams/render.py" >/dev/null
else
  echo "  SKIP: cairosvg not installed; keeping existing diagrams/pdf/*.pdf"
fi

# Source-level proxies come from the code rather than from a campaign log, so
# they are regenerated here too and are the one part of this script that stays
# valid without a fresh measurement run.
echo "== regenerating size and complexity proxies =="
if "$root/.venv-pptx/bin/python" -c 'import lizard' 2>/dev/null; then
  "$root/.venv-pptx/bin/python" "$here/complexity.py"
elif python3 -c 'import lizard' 2>/dev/null; then
  python3 "$here/complexity.py"
else
  echo "  SKIP: lizard not installed (pip install lizard); keeping existing figures/tab_complexity.tex"
fi

# Record sizes, parity-suite coverage, conformance campaign size, and seam size.
# Same reason as the proxies above: they are measurements the prose quotes, and
# they come from the code and the suite rather than from a campaign log.
echo "== regenerating artefact-level measurements =="
python3 "$here/artefact_facts.py"

# The colloquium deck quotes the same generated macros and table bodies as the
# prose, so it is rebuilt here for the same reason: a fresh campaign must not
# leave a slide contradicting the thesis. It drifted once already.
echo "== rebuilding the colloquium deck =="
if [ -x "$root/.venv-pptx/bin/python" ]; then
  "$root/.venv-pptx/bin/python" "$root/build_deck.py" || echo "  WARN: deck build failed"
else
  echo "  SKIP: .venv-pptx not present; keeping existing Rust_vs_Cpp_Nokia_RAN_thesis.pptx"
fi

echo "== rebuilding Thesis_POC.pdf =="
cd "$root"
latexmk -pdf -interaction=nonstopmode Thesis_POC.tex >/dev/null 2>&1 || true

echo
if grep -qE '^!|LaTeX Error' Thesis_POC.log 2>/dev/null; then
  echo "FAIL: LaTeX reported errors -- see Thesis_POC.log"
  grep -nE '^!|LaTeX Error' Thesis_POC.log | head
  exit 1
fi
if grep -q 'LaTeX Warning' Thesis_POC.log 2>/dev/null; then
  echo "WARN: unresolved LaTeX warnings (undefined refs/citations?):"
  grep -n 'LaTeX Warning' Thesis_POC.log | head
fi
echo "OK: Thesis_POC.pdf rebuilt."
echo
echo "Campaign numbers now in the prose (figures/gen_macros.tex):"
sed -n 's/\\newcommand{\\\([A-Za-z]*\)}{\(.*\)}/  \1 = \2/p' figures/gen_macros.tex
