#!/usr/bin/env bash
# Regenerate every figure, table, and quoted number in the thesis from the raw
# measurement logs, then rebuild the PDF.
#
# Run this after a campaign (bench/campaign.sh) or a fault-injection run
# (faults/run_faults.sh). Nothing in the thesis prose is hand-copied from the
# data: the campaign summary numbers land in figures/gen_macros.tex and the
# prose refers to them by name, so this one command keeps text and data in step.
#
# Usage:
#   bench/refresh_thesis.sh                 # newest campaign in bench/results/
#   bench/refresh_thesis.sh --campaign bench/results/campaign-....jsonl
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"

echo "== regenerating figures, tables, and generated macros =="
python3 "$here/plot_figures.py" "$@"

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
