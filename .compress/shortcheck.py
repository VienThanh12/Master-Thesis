#!/usr/bin/env python3
"""Compare two thesis sources for content that a compression pass must not drop.

Reports citation keys, labels, cross-references and generated macros present in
the reference document and missing from the short one, plus any reference to a
label the short document no longer defines.

Usage: .compress/shortcheck.py reference.tex short.tex

Run from the repository root, as with the bench/ scripts.
"""
import re
import sys
from pathlib import Path

REF = Path(sys.argv[1] if len(sys.argv) > 1 else "Ha_Vien_Mastersthesis_2026.tex")
SHORT = Path(sys.argv[2] if len(sys.argv) > 2 else "Ha_Vien_Mastersthesis_2026_short.tex")

CITE = re.compile(r"\\(?:cite|fullcite|textcite|parencite)\{([^}]*)\}")
LABEL = re.compile(r"\\label\{([^}]*)\}")
REFER = re.compile(r"\\(?:ref|autoref|pageref|nameref)\{([^}]*)\}")
# Generated macros are camel-case control words with no arguments
MACRO = re.compile(r"\\([A-Z][A-Za-z]{2,})(?![a-zA-Z])")


def keys(pattern, text, split=False):
    out = set()
    for m in pattern.finditer(text):
        if split:
            out.update(k.strip() for k in m.group(1).split(","))
        else:
            out.add(m.group(1).strip())
    return {k for k in out if k}


ref_text = REF.read_text()
short_text = SHORT.read_text()

# Macros the generated files actually define, so prose macros are not confused
# with LaTeX control words such as \Delta or \NG
defined = set()
for gen in Path("figures").glob("gen_*.tex"):
    for m in re.finditer(r"\\newcommand\{?\\([A-Za-z]+)\}?", gen.read_text()):
        defined.add(m.group(1))

fail = 0
for name, pattern, split in (("citation keys", CITE, True),
                             ("labels", LABEL, False)):
    a, b = keys(pattern, ref_text, split), keys(pattern, short_text, split)
    missing = sorted(a - b)
    print(f"{name}: {len(b)} of {len(a)} kept")
    if missing:
        fail = 1
        print(f"  MISSING ({len(missing)}): {', '.join(missing)}")

a = {m for m in keys(MACRO, ref_text) if m in defined}
b = {m for m in keys(MACRO, short_text) if m in defined}
print(f"generated macros used: {len(b)} of {len(a)}")
dropped = sorted(a - b)
if dropped:
    print(f"  dropped ({len(dropped)}): {', '.join(dropped)}")

undefined = sorted(keys(REFER, short_text) - keys(LABEL, short_text))
# Labels defined by inputs (generated tables) are not visible here
undefined = [u for u in undefined if not u.startswith(("tab:params",))]
print(f"references to undefined labels: {len(undefined)}")
if undefined:
    fail = 1
    print(f"  {', '.join(undefined)}")

sys.exit(fail)
