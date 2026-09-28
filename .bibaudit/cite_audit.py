#!/usr/bin/env python3
"""Map every bib key to the claims that cite it, across the thesis sources."""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/vienha/thesis.local")
TEX = ["Ha_Vien_Mastersthesis_2026.tex", "Thesis_v4.tex", "Thesis_Plan_v2.tex"]
BIB = ROOT / "bibliography.bib"

keys = re.findall(r"^@\w+\{([^,]+),", BIB.read_text(), re.M)

CITE = re.compile(r"\\(?:cite|citep|citet|textcite|parencite|autocite)\*?(?:\[[^\]]*\])*\{([^}]*)\}")

usage = defaultdict(list)
for name in TEX:
    path = ROOT / name
    if not path.exists():
        continue
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        for m in CITE.finditer(line):
            ctx = line.strip()
            # widen context to the sentence-ish neighbourhood
            before = lines[i - 2].strip() if i >= 2 else ""
            after = lines[i].strip() if i < len(lines) else ""
            for k in (x.strip() for x in m.group(1).split(",")):
                usage[k].append((name, i, before, ctx, after))

print("### KEYS NOT CITED ANYWHERE")
for k in keys:
    if k not in usage:
        print(f"  {k}")

print("\n### CITED KEYS MISSING FROM BIB")
for k in sorted(usage):
    if k not in keys:
        print(f"  {k}")

print("\n### USAGE\n")
for k in keys:
    print(f"=== {k}  ({len(usage.get(k, []))} citation sites)")
    for (name, ln, before, ctx, after) in usage.get(k, []):
        print(f"  -- {name}:{ln}")
        if before:
            print(f"     ^ {before}")
        print(f"     > {ctx}")
        if after:
            print(f"     v {after}")
    print()
