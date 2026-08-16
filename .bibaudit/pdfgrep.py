#!/usr/bin/env python3
"""Search a PDF and report page numbers for each hit: .pdfgrep.py FILE REGEX [context_chars]"""
import re
import sys
from pypdf import PdfReader

path, pattern = sys.argv[1], sys.argv[2]
ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 220
rx = re.compile(pattern, re.I | re.S)
reader = PdfReader(path)
print(f"# {path}: {len(reader.pages)} pages")
hits = 0
for i, page in enumerate(reader.pages, 1):
    try:
        text = page.extract_text() or ""
    except Exception as e:
        continue
    flat = re.sub(r"[ \t]+", " ", text)
    for m in rx.finditer(flat):
        s = max(0, m.start() - ctx)
        e = min(len(flat), m.end() + ctx)
        snippet = flat[s:e].replace("\n", " ⏎ ")
        print(f"\n--- PDF page {i} ---\n...{snippet}...")
        hits += 1
        if hits > 25:
            print("\n[truncated: >25 hits]")
            sys.exit(0)
if not hits:
    print("NO MATCH")
