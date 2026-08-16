#!/usr/bin/env python3
"""Pull publisher-deposited abstracts from Crossref for every DOI in the bibliography."""
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

BIB = Path("/home/vienha/thesis.local/bibliography.bib").read_text()
UA = "thesis-bib-audit/1.0 (mailto:ha.vien@helsinki.fi)"

entries = []
for m in re.finditer(r"^@(\w+)\{([^,]+),", BIB, re.M):
    start = m.start()
    nxt = BIB.find("\n@", start + 1)
    body = BIB[start: nxt if nxt > 0 else len(BIB)]
    doi = re.search(r"doi\s*=\s*\{([^}]+)\}", body)
    entries.append((m.group(2).strip(), doi.group(1).strip() if doi else None))

for key, doi in entries:
    if not doi:
        continue
    try:
        req = urllib.request.Request(
            "https://api.crossref.org/works/" + urllib.parse.quote(doi),
            headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            msg = json.load(r)["message"]
    except Exception as e:
        print(f"== {key}: FETCH FAIL {e}\n")
        continue
    abstract = msg.get("abstract", "")
    abstract = re.sub(r"<[^>]+>", " ", abstract)
    abstract = html.unescape(re.sub(r"\s+", " ", abstract)).strip()
    print(f"== {key} [{doi}]")
    print(f"   {abstract[:1400] if abstract else '(no abstract deposited)'}")
    print()
    time.sleep(0.3)
