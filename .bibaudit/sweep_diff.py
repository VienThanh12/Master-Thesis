#!/usr/bin/env python3
"""Which BibTeX keys proposed in docs/LITERATURE_NOTES.md never reached bibliography.bib."""
import re
from pathlib import Path

ROOT = Path("/home/vienha/thesis.local")
bib = ROOT / "bibliography.bib"
notes = ROOT / "docs" / "LITERATURE_NOTES.md"
tex = ROOT / "Thesis_POC.tex"

bib_text = bib.read_text()
bib_keys = {m.group(2).strip() for m in re.finditer(r"^@(\w+)\{([^,]+),", bib_text, re.M)}
notes_keys = {m.group(2).strip() for m in re.finditer(r"^@(\w+)\{([^,]+),", notes.read_text(), re.M)}

cited = set()
for m in re.finditer(r"\\cite[tp]?\{([^}]*)\}", tex.read_text()):
    cited.update(k.strip() for k in m.group(1).split(","))

print(f"bibliography.bib: {len(bib_keys)} entries   cited in Thesis_POC.tex: {len(cited)}")
print(f"proposed in LITERATURE_NOTES.md: {len(notes_keys)}\n")

missing = sorted(notes_keys - bib_keys)
print(f"-- proposed but NOT in bibliography.bib ({len(missing)}) --")
for k in missing:
    print(f"   {k}")

orphans = sorted(bib_keys - cited)
print(f"\n-- in bibliography.bib but never cited ({len(orphans)}) --")
for k in orphans:
    print(f"   {k}")

undefined = sorted(cited - bib_keys)
print(f"\n-- cited but missing from bibliography.bib ({len(undefined)}) --")
for k in undefined:
    print(f"   {k}")
