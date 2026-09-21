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

# Pooling comes first, and it now covers the main campaign as well.
#
# The far-tail figures read the pooled CSV and never the campaign JSONL's per-run
# p9999 field: a single run's p99.99 rests on about seventeen operations, so the
# percentile is only a measurement once the repeats are pooled. Both generators
# skip the far tail when the pooled CSV is missing rather than falling back to
# the per-run field, so a missing pooling step leaves a column absent instead of
# quietly printing the statistic the thesis disowns. This loop is what keeps it
# present.
#
# Until 27 August 2026 the loop covered only results-baremetal/, which is how
# tab:latency came to print a per-run figure while two sections described it as
# pooled. Add any new results directory here.
echo "== pooling histogram sidecars =="
for dir in results results-baremetal; do
  for hist in "$root/bench/$dir"/campaign-*.hist.jsonl \
              "$root/bench/$dir"/fair-after-*.hist.jsonl; do
    [ -e "$hist" ] || continue
    python3 "$here/pool_hist.py" "$hist" >/dev/null \
      || echo "  WARN: pooling failed for $(basename "$hist")"
  done
done

# The fair-clock sweeps are diagnostics rather than a replacement campaign.
# Their prefix keeps them out of the unprefixed result layer, while this
# generator makes every value quoted by the overload diagnosis reproducible.
echo "== regenerating fair-clock diagnostic macros =="
python3 "$here/probe_facts.py"

echo "== regenerating figures, tables, and generated macros =="
python3 "$here/plot_figures.py" "$@"

# The bare-metal confirmation campaign is a separate dataset with its own design,
# so it has its own generator rather than a flag on the one above. It describes a
# host that no longer exists, which is the strongest possible reason for its
# numbers to be derived rather than typed.

echo "== regenerating bare-metal confirmation macros =="
python3 "$here/baremetal_facts.py" >/dev/null || echo "  WARN: bare-metal macros not regenerated"

# The virtualised campaign the thesis reported until 27 August 2026. It is no
# longer the primary dataset and it is still quoted, because the contrast between
# what the two hosts could resolve is the measurement-validity argument. Same
# reason as above for generating rather than remembering: a claim about the
# difference between two hosts reads two datasets at once.
echo "== regenerating virtualised-host comparison macros =="
python3 "$here/guest_facts.py" >/dev/null || echo "  WARN: guest macros not regenerated"

# Diagrams 20-31 quote campaign numbers straight out of figures/gen_macros.tex,
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

# The third prose surface. .aitells.py reads the thesis .tex and build_deck.py
# checks the saved deck, so before this gate existed the figure labels were the
# only reader-visible prose in the project with nothing looking at it, and about
# two dozen dash asides and prose semicolons had accumulated there. Scope is the
# diagrams a document actually includes, computed from the documents.
echo "== checking diagram labels against the prose style =="
python3 "$root/diagrams/check_labels.py"

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

# The RQ4 adoption-cost axes: build time, static footprint, and the third-party
# surface each configuration resolves. Called without --measure on purpose. Build
# time moves with host load, so it is replayed from bench/results/adoption-*.json
# rather than re-timed here; running the refresh on a busy machine must not
# quietly replace the recorded figures the way an ffi/build.sh run once did.
# Footprint and supply chain are deterministic and are recomputed.
echo "== regenerating adoption-cost measurements (build time replayed) =="
python3 "$here/adoption_cost.py" || echo "  WARN: adoption-cost regeneration failed"

# The colloquium deck quotes the same generated macros and table bodies as the
# prose, so it is rebuilt here for the same reason: a fresh campaign must not
# leave a slide contradicting the thesis. It drifted once already.
echo "== rebuilding the colloquium deck =="
if [ -x "$root/.venv-pptx/bin/python" ]; then
  "$root/.venv-pptx/bin/python" "$root/build_deck.py" || echo "  WARN: deck build failed"
else
  echo "  SKIP: .venv-pptx not present; keeping existing Rust_vs_Cpp_Nokia_RAN_thesis.pptx"
fi

# The source carries the UH submission filename directly
# (Lastname_Firstname_Mastersthesis_Year, ASCII only), so the build writes the
# submission PDF and there is no second copy to keep in step.
thesis="Ha_Vien_Mastersthesis_2026"

echo "== rebuilding $thesis.pdf =="
cd "$root"
latexmk -pdf -interaction=nonstopmode "$thesis.tex" >/dev/null 2>&1 || true

# .latexmkrc keeps intermediates in build/ so the repository root stays readable.
# Fall back to the root copy in case the last build came from a tool that
# overrode the aux directory.
thesis_log="build/$thesis.log"
[ -f "$thesis_log" ] || thesis_log="$thesis.log"

echo
if grep -qE '^!|LaTeX Error' "$thesis_log" 2>/dev/null; then
  echo "FAIL: LaTeX reported errors -- see $thesis_log"
  grep -nE '^!|LaTeX Error' "$thesis_log" | head
  exit 1
fi
if grep -q 'LaTeX Warning' "$thesis_log" 2>/dev/null; then
  echo "WARN: unresolved LaTeX warnings (undefined refs/citations?):"
  grep -n 'LaTeX Warning' "$thesis_log" | head
fi
echo "OK: $thesis.pdf rebuilt."

echo
echo "Campaign numbers now in the prose (figures/gen_macros.tex):"
sed -n 's/\\newcommand{\\\([A-Za-z]*\)}{\(.*\)}/  \1 = \2/p' figures/gen_macros.tex
