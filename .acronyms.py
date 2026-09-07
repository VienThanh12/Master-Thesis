#!/usr/bin/env python3
"""Check that every acronym in the front-matter list is written out at first use.

The front matter promises it in so many words ("Each acronym below is also
written out where the text first uses it"), and nothing enforced that promise.
The list itself is the source of truth, so an acronym cannot be checked here
without being declared there, and the script reports a declared acronym that
the body never uses as well.

First use means the first occurrence in the body, which starts at \\mainmatter
and stops at the bibliography. Citation keys, labels, cross-references, file
paths and verbatim code are stripped first: an acronym buried in \\cite{ieee...}
is not a use a reader sees, and counting it would move first use earlier than
the page it appears on.

Expanded means the gloss sits beside the acronym, within a couple of source
lines either way, because the body is hard-wrapped and a first use often
straddles a break. The comparison takes the part of the list entry before its
first comma or colon, since the rest is a gloss the prose need not repeat, and
then asks only for that phrase's first three words. Requiring the whole phrase
rejected "FNV-1a, the Fowler--Noll--Vo hash" for lacking the word "function",
which is not a defect any reader would recognise.

The exemption list is explicit, in the manner of diagrams/check_labels.py, and
its entries are printed rather than hidden, so waiving one is a decision on the
record instead of a silent pass. A heuristic loose enough to accept them all
would have accepted the one real defect this script found.

    ./.acronyms.py                                  # the full draft
    ./.acronyms.py Thesis_v2.tex                    # any other document
"""
from __future__ import annotations

import re
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "Ha_Vien_Mastersthesis_2026.tex"
WINDOW = 220

lines = open(SRC, encoding="utf-8").read().split("\n")

ENTRY = re.compile(r"^([A-Za-z0-9][A-Za-z0-9./-]*)\s*&\s*(.+?)\s*\\\\\s*$")
STRIP = re.compile(
    r"\\(?:cite\w*|nocite|label|ref|pageref|autoref|eqref|url|href|texttt|verb|"
    r"lstinline|input|include|includegraphics|bibliography|addcontentsline)\s*"
    r"(?:\[[^]]*\])?\{[^}]*\}"
)

# A LaTeX comment starts at an unescaped percent. Splitting on the character
# itself truncated any line carrying \% and hid the expansion of API, which sits
# one line after a \FfiOpBoundPct\% macro.
COMMENT = re.compile(r"(?<!\\)%")

# Acronyms whose gloss the prose supplies in a form this check cannot match.
# Each names the reason, so adding one is a decision and not an accident.
ACCEPTED = {
    "AI-RAN": "the list entry defines the term rather than expanding its letters, "
              "and the prose defines it in a relative clause at first use",
    "gNB-CU": "glossed as 'a central unit (gNB-CU)' in a sentence that has just named the gNB",
    "gNB-DU": "glossed as 'distributed units (gNB-DU)' in the same sentence pattern",
    "gNB-CU-UP": "glossed as 'the user-plane function (gNB-CU-UP)' beside its control-plane twin",
    "RQ": "a column label, and RQ1 to RQ4 are defined by the numbered list in the introduction",
}

# Entries a list carries on purpose although that document's body never uses the
# bare token. Both are stems of something the body does use, and a reader who
# meets the compound looks the stem up, so the entry earns its line. Kept apart
# from an entry nobody asked for, which is a defect and fails the gate.
DECLARED_UNUSED = {
    "RQ": "the body writes RQ1 to RQ4, and a reader meeting those looks up the stem",
    "gNB-CU": "the body writes gNB-CU-CP, whose expansion is built on this one",
}


def declared() -> dict[str, str]:
    """Acronyms from the front-matter longtable, in list order."""
    out: dict[str, str] = {}
    inside = False
    for line in lines:
        s = line.strip()
        if s.startswith(r"\begin{longtable}"):
            inside = True
            continue
        if s.startswith(r"\end{longtable}"):
            break
        if not inside:
            continue
        m = ENTRY.match(s)
        if m and m.group(1) != "Acronym":
            out[m.group(1)] = m.group(2)
    return out


def body_range() -> tuple[int, int]:
    """From \\mainmatter to the end of the file.

    The appendices sit after \\printbibliography in this document and a reader
    reaches them, so stopping at the bibliography would report the literature
    search protocol's own acronyms as never used.
    """
    start = next(i for i, l in enumerate(lines) if l.startswith(r"\mainmatter"))
    return start + 1, len(lines)


def visible(line: str) -> str:
    """What a reader sees, with reference machinery removed."""
    s = COMMENT.split(line)[0]
    s = STRIP.sub(" ", s)
    s = re.sub(r"\$[^$]*\$", " ", s)
    return s


def core(expansion: str) -> str:
    """The part of a list entry the prose has to reproduce.

    A gloss follows a comma in most entries and a colon in a few, and neither
    is something the prose has to repeat.
    """
    return re.split(r",|:| \(", expansion)[0].strip()


def loose(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def sought(expansion: str) -> str:
    """The first three words of the gloss, which is what the prose must carry."""
    return " ".join(loose(core(expansion)).split()[:3])


def main() -> int:
    acronyms = declared()
    if not acronyms:
        print(f"{SRC}: no front-matter acronym list found")
        return 1

    lo, hi = body_range()
    unexpanded, accepted, unused = [], [], []

    for acr, expansion in acronyms.items():
        # A trailing lowercase s is the plural of the acronym, not another token,
        # which is the only form the body uses for KPI.
        pat = re.compile(rf"(?<![A-Za-z0-9-]){re.escape(acr)}s?(?![A-Za-z0-9-])")
        first = None
        for i in range(lo, hi):
            text = visible(lines[i])
            m = pat.search(text)
            if m:
                first = (i + 1, text)
                break
        if first is None:
            unused.append(acr)
            continue

        ln, text = first
        around = " ".join(visible(lines[j]) for j in range(max(lo, ln - 3), min(hi, ln + 2)))
        if sought(expansion) in loose(around):
            continue
        if acr in ACCEPTED:
            accepted.append((acr, ln, ACCEPTED[acr]))
        else:
            unexpanded.append((acr, ln, core(expansion), text.strip()[:96]))

    print("=" * 78)
    print(f"ACRONYMS WRITTEN OUT AT FIRST USE in {SRC}")
    print(f"{len(acronyms)} declared in the front-matter list, body lines {lo}-{hi}")
    print("=" * 78)

    print(f"\nnot written out at first use: {len(unexpanded)}")
    for acr, ln, exp, snippet in unexpanded:
        print(f"    L{ln:<5} {acr:<10} expects '{exp}'")
        print(f"          {snippet}")

    if accepted:
        print(f"\naccepted by an explicit exemption: {len(accepted)}")
        for acr, ln, why in accepted:
            print(f"    L{ln:<5} {acr:<10} {why}")

    deliberate = [a for a in unused if a in DECLARED_UNUSED]
    stray = [a for a in unused if a not in DECLARED_UNUSED]

    if stray:
        print(f"\ndeclared but never used in the body: {len(stray)}")
        print("    " + ", ".join(stray))
    if deliberate:
        print(f"\ndeclared without a bare use, on purpose: {len(deliberate)}")
        for acr in deliberate:
            print(f"    {acr:<10} {DECLARED_UNUSED[acr]}")

    return 1 if unexpanded or stray else 0


if __name__ == "__main__":
    sys.exit(main())
