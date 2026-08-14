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

# The colloquium deck quotes the same generated macros and table bodies as the
# prose, so it is rebuilt here for the same reason: a fresh campaign must not
# leave a slide contradicting the thesis. It drifted once already.
echo "== rebuilding the colloquium deck =="
if [ -x "$root/.venv-pptx/bin/python" ]; then
  "$root/.venv-pptx/bin/python" "$root/build_deck.py" || echo "  WARN: deck build failed"
else
  echo "  SKIP: .venv-pptx not present; keeping existing Rust_vs_Cpp_Nokia_RAN_thesis.pptx"
fi

echo "== rebuilding thesis.pdf =="
cd "$root"
latexmk -pdf -interaction=nonstopmode thesis.tex >/dev/null 2>&1 || true

echo
if grep -qE '^!|LaTeX Error' thesis.log 2>/dev/null; then
  echo "FAIL: LaTeX reported errors -- see thesis.log"
  grep -nE '^!|LaTeX Error' thesis.log | head
  exit 1
fi
if grep -q 'LaTeX Warning' thesis.log 2>/dev/null; then
  echo "WARN: unresolved LaTeX warnings (undefined refs/citations?):"
  grep -n 'LaTeX Warning' thesis.log | head
fi
echo "OK: thesis.pdf rebuilt."
echo
echo "Campaign numbers now in the prose (figures/gen_macros.tex):"
sed -n 's/\\newcommand{\\\([A-Za-z]*\)}{\(.*\)}/  \1 = \2/p' figures/gen_macros.tex
