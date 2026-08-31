#!/usr/bin/env python3
"""Print the publisher-deposited abstract for a set of entries, beside the claim each carries.

Purpose is to move entries off evidence level C. Level C means the metadata is confirmed and
the supporting passage sits behind a paywall, so it was never read. A deposited abstract is
weaker than the passage but stronger than nothing, and where it states the claim outright the
entry can move to level B without university access.

    .bibaudit/abstract_sweep.py                # every level-C entry
    .bibaudit/abstract_sweep.py key1 key2      # named entries
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_audit as B  # noqa: E402

UA = {"User-Agent": "thesis-bib-audit/1.0 (mailto:ha.vien@helsinki.fi)"}


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))


def openalex(doi):
    j = get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi))
    inv = j.get("abstract_inverted_index")
    text = None
    if inv:
        pos = {}
        for word, ixs in inv.items():
            for i in ixs:
                pos[i] = word
        text = " ".join(pos[k] for k in sorted(pos))
    oa = (j.get("open_access") or {})
    return text, oa.get("oa_status"), oa.get("oa_url")


def crossref_abstract(doi):
    m = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
    ab = m.get("abstract")
    return re.sub(r"<[^>]+>", " ", ab).strip() if ab else None


def main():
    bib = B.parse_bib(B.read(B.BIB))
    records = B.build_records(bib)
    keys = sys.argv[1:] or sorted(k for k, r in records.items() if r.get("level") == "C")

    sites = {}
    for tex, tag, label in B.DOCUMENTS:
        for s in B.cite_sites(B.ROOT / tex):
            for k in s["keys"]:
                sites.setdefault(k, []).append((label, s))

    for key in keys:
        doi = bib[key]["fields"].get("doi", "")
        print("=" * 100)
        print(f"{key}   doi={doi or '(none)'}")
        claim = records.get(key, {}).get("claim", "")
        if claim:
            print(f"  CLAIM RECORDED: {re.sub(r'`|[*]', '', claim)[:260]}")
        for label, s in sites.get(key, [])[:3]:
            print(f"  CITED {label} {s['section']}: {re.sub(chr(92)+'s+', ' ', s['sentence'])[:230]}")
        if not doi:
            print("  no DOI, cannot query")
            continue
        text = status = oaurl = None
        try:
            text, status, oaurl = openalex(doi)
        except Exception as e:
            print(f"  openalex error: {e}")
        if not text:
            try:
                text = crossref_abstract(doi)
            except Exception:
                pass
        print(f"  open access: {status}  {oaurl or ''}")
        print(f"  ABSTRACT: {text[:1400] if text else '(none deposited anywhere)'}")
        print()


if __name__ == "__main__":
    main()
