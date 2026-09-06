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

Expanded means the gloss sits beside the acronym, in either order and with
either kind of bracket, within a window of a few words. The comparison uses the
part of the list entry before its first comma, since the rest is a gloss the
prose is not obliged to repeat, and it tolerates hyphen and case differences so
that "next-generation NodeB" matches "Next-Generation NodeB".

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
    s = line.split("%")[0] if not line.lstrip().startswith("%") else ""
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


def main() -> int:
    acronyms = declared()
    if not acronyms:
        print(f"{SRC}: no front-matter acronym list found")
        return 1

    lo, hi = body_range()
    unexpanded, unused = [], []

    for acr, expansion in acronyms.items():
        # Longer acronyms first would shadow shorter ones, so anchor on word
        # boundaries and require the exact token.
        pat = re.compile(rf"(?<![A-Za-z0-9-]){re.escape(acr)}(?![A-Za-z0-9-])")
        first = None
        for i in range(lo, hi):
            text = visible(lines[i])
            m = pat.search(text)
            if m:
                first = (i + 1, text, m.start())
                break
        if first is None:
            unused.append(acr)
            continue

        ln, text, at = first
        # The gloss may sit on the neighbouring source line, since the body is
        # hard-wrapped and a first use often straddles a break.
        around = " ".join(visible(lines[j]) for j in range(max(lo, ln - 2), min(hi, ln + 2)))
        if loose(core(expansion)) not in loose(around):
            unexpanded.append((acr, ln, core(expansion), text.strip()[:96]))

    print("=" * 78)
    print(f"ACRONYMS WRITTEN OUT AT FIRST USE in {SRC}")
    print(f"{len(acronyms)} declared in the front-matter list, body lines {lo}-{hi}")
    print("=" * 78)

    if unexpanded:
        print(f"\nnot written out at first use: {len(unexpanded)}")
        for acr, ln, exp, snippet in unexpanded:
            print(f"    L{ln:<5} {acr:<10} expects '{exp}'")
            print(f"          {snippet}")
    else:
        print("\nnot written out at first use: 0")

    if unused:
        print(f"\ndeclared but never used in the body: {len(unused)}")
        print("    " + ", ".join(unused))

    return 1 if unexpanded else 0


if __name__ == "__main__":
    sys.exit(main())
