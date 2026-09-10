#!/usr/bin/env python3
"""Enforce the thesis prose style on diagram labels.

The house style bans em dashes, spaced en dashes used as an aside, and prose
semicolons anywhere a reader sees one, and it names figure labels explicitly.
Two gates already cover the other two surfaces: `.aitells.py` reads the thesis
`.tex` and `build_deck.py`'s `check_prose_style` walks the saved deck. Neither
looks at a diagram, so until this script existed the figures were the one
reader-visible prose surface in the project with nothing checking it, and a
grading pass found about two dozen breaches sitting there.

Scope is the diagrams a reader can actually reach, computed rather than listed:
every diagram included by a LaTeX document or referenced by the deck builder. A
diagram nobody includes is reported as unchecked instead of failing the build,
and it starts being checked the moment a document includes it.

The exemption list below is explicit on purpose. Verbatim source code keeps its
semicolons, which the house style says outright, but a heuristic that guessed at
"this looks like code" would also wave through the prose that matters. Each
exemption therefore names the diagram and the exact string, so adding one is a
decision and not an accident.

Usage:
    python3 diagrams/check_labels.py            # gate the reader-visible set
    python3 diagrams/check_labels.py --all      # gate every diagram source
"""
from __future__ import annotations

import argparse
import glob
import html
import os
import re
import sys

EM_DASH = "\u2014"
EN_DASH = "\u2013"

# Verbatim code, which the house style exempts. Keyed by diagram stem; a label is
# exempt when it contains one of the listed fragments.
CODE_EXEMPT = {
    "05_data_model": ["[u8; 32]"],
    "08_borrow_checker_uaf": [
        "std::unordered_map", "ctxs[1001]", "ctxs.at(", "ctxs.erase(",
        "messages_handled", "HashMap::new()", "ctxs.insert(", "ctxs.get_mut(",
        "ctxs.remove(",
    ],
}


def labels(path):
    """Every visible text run in an SVG, entities decoded, markup stripped."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        source = fh.read()
    for run in re.findall(r"<(?:text|tspan)[^>]*>(.*?)</(?:text|tspan)>", source, re.S):
        text = html.unescape(re.sub(r"<[^>]+>", "", run)).strip()
        if text:
            yield re.sub(r"\s+", " ", text)


def offences(stem, label):
    """What the style forbids in this label, or nothing."""
    exempt = any(frag in label for frag in CODE_EXEMPT.get(stem, ()))
    found = []
    if EM_DASH in label:
        found.append("em dash")
    # An en dash between numbers is a range and legitimate. Spaced, it is an
    # aside, which is the construction the style rejects.
    if re.search(rf"\s{EN_DASH}\s", label):
        found.append("spaced en dash")
    if ";" in label and not exempt:
        found.append("semicolon")
    return found


def reader_visible(root):
    """Diagram stems a reader can reach, from the documents themselves."""
    seen = set()
    for tex in glob.glob(os.path.join(root, "*.tex")):
        with open(tex, encoding="utf-8", errors="replace") as fh:
            seen.update(re.findall(r"diagrams/pdf/([0-9]+_[a-z0-9_]+)", fh.read()))
    # The deck names a diagram by stem through one helper, so match the call and
    # not a bare filename pattern: the template's own name contains a run of
    # digits that a looser pattern reads as a diagram.
    deck = os.path.join(root, "build_deck.py")
    if os.path.exists(deck):
        with open(deck, encoding="utf-8", errors="replace") as fh:
            seen.update(re.findall(r"""diagram\(\s*["']([0-9]+_[a-z0-9_]+)["']""", fh.read()))
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="check every diagram source, not only the included ones")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, ".."))
    sources = sorted(glob.glob(os.path.join(here, "*.svg")))
    visible = reader_visible(root)

    checked, skipped, hits = 0, [], 0
    for path in sources:
        stem = os.path.splitext(os.path.basename(path))[0]
        if not args.all and stem not in visible:
            skipped.append(stem)
            continue
        checked += 1
        for label in labels(path):
            for kind in offences(stem, label):
                hits += 1
                print(f"{stem}: {kind} in {label[:100]!r}")

    scope = "every diagram" if args.all else f"{checked} reader-visible diagram(s)"
    if hits:
        print(f"\nFAIL: {hits} style breach(es) across {scope}.", file=sys.stderr)
        print("Fix the diagrams/ source (or diagrams/build_new_diagrams.py "
              "for generated diagrams), re-render, and rerun.", file=sys.stderr)
        return 1
    print(f"Diagram labels: no em dash, dash aside, or semicolon in {scope}")
    if skipped:
        print(f"  not checked, included by no document: {', '.join(sorted(skipped))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
