#!/usr/bin/env python3
"""Price the length of a thesis .tex per division.

Reports prose words, float count and the declared page span of every chapter,
section and subsection, so a length pass can be planned against measured cost.
Usage: .lengthprice.py [file.tex]
"""
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "Ha_Vien_Mastersthesis_2026.tex")
TOC = SRC.with_suffix(".toc")
lines = SRC.read_text().splitlines()

DIV = re.compile(r"^\\(chapter|section|subsection|appendix)\*?(?:\[[^\]]*\])?\{(.*)")
FLOAT = re.compile(r"^\\begin\{(figure|table|longtable|lstlisting)\}")
ORDER = {"chapter": 0, "appendix": 0, "section": 1, "subsection": 2}


def strip_comment(s):
    i = 0
    while i < len(s):
        if s[i] == "%" and (i == 0 or s[i - 1] != "\\"):
            return s[:i]
        i += 1
    return s


def clean_title(t):
    t = re.sub(r"\\label\{[^}]*\}", "", t)
    t = re.sub(r"\\[a-zA-Z@]+\*?", "", t)
    return t.replace("{", "").replace("}", "").strip()


divs = []
for n, raw in enumerate(lines, 1):
    m = DIV.match(raw.strip())
    if m:
        divs.append({"kind": m.group(1), "title": clean_title(m.group(2)),
                     "line": n, "words": 0, "floats": 0})

for i, d in enumerate(divs):
    end = divs[i + 1]["line"] - 1 if i + 1 < len(divs) else len(lines)
    for raw in lines[d["line"]:end]:
        s = strip_comment(raw).strip()
        if not s:
            continue
        if FLOAT.match(s):
            d["floats"] += 1
        if s.startswith("\\") and not re.match(r"\\(text|emph|cite|ref|noindent|item|paragraph)", s):
            continue
        txt = re.sub(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?", " ", s)
        txt = re.sub(r"[{}$&\\]", " ", txt)
        d["words"] += len(re.findall(r"[A-Za-z][A-Za-z'-]+", txt))

# Numbered page from the .toc, keyed by division title
toc_pages = {}
if TOC.exists():
    for raw in TOC.read_text().splitlines():
        m = re.search(r"\\contentsline \{(chapter|section|subsection)\}"
                      r"\{(?:\\numberline \{[^}]*\})?(.*)\}\{(\d+|[ivxl]+)\}\{", raw)
        if m:
            toc_pages.setdefault(clean_title(m.group(2)), m.group(3))

# Aggregate a chapter's own words as the sum of its subordinate divisions
totals = []
for i, d in enumerate(divs):
    if ORDER[d["kind"]] == 0:
        w, f = d["words"], d["floats"]
        for e in divs[i + 1:]:
            if ORDER[e["kind"]] == 0:
                break
            w += e["words"]
            f += e["floats"]
        totals.append((d["title"], w, f))

print(f"{'kind':<11} {'page':>5} {'words':>6} {'flt':>4}  title")
print("-" * 90)
for d in divs:
    pg = toc_pages.get(d["title"], "")
    indent = "  " * ORDER[d["kind"]]
    print(f"{d['kind']:<11} {pg:>5} {d['words']:>6} {d['floats']:>4}  {indent}{d['title'][:58]}")

print("\n" + "=" * 90)
print(f"{'CHAPTER TOTALS':<58} {'words':>7} {'floats':>7}")
for t, w, f in totals:
    print(f"{t[:58]:<58} {w:>7} {f:>7}")
print(f"{'ALL':<58} {sum(t[1] for t in totals):>7} {sum(t[2] for t in totals):>7}")
