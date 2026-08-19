#!/usr/bin/env python3
"""Resolve candidate DOIs against Crossref/DataCite and print the depositor's own record.

Usage: verify_candidates.py DOI [DOI ...]
Nothing here is written from memory: the printed fields are what the registration
agency holds, so a candidate that does not resolve is reported as such.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

UA = "thesis-bib-audit/1.0 (mailto:ha.vien@helsinki.fi)"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def show(doi):
    try:
        m = fetch("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
        src = "crossref"
    except Exception:
        try:
            m = fetch("https://api.datacite.org/dois/" + urllib.parse.quote(doi))["data"]["attributes"]
            src = "datacite"
        except Exception as ex:
            print(f"== {doi}\n   UNRESOLVED ({ex})\n")
            return
    if src == "crossref":
        authors = "; ".join(
            f"{a.get('family', a.get('name',''))}, {a.get('given','')}".strip(", ")
            for a in m.get("author", [])
        )
        year = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
        print(f"== {doi}   [{src}]")
        print(f"   type      : {m.get('type','')}")
        print(f"   title     : {' '.join(m.get('title', []))}")
        print(f"   subtitle  : {' '.join(m.get('subtitle', []) or [])}")
        print(f"   authors   : {authors}")
        print(f"   venue     : {' / '.join(m.get('container-title', []) or [])}")
        print(f"   series    : {' / '.join(m.get('short-container-title', []) or [])}")
        print(f"   publisher : {m.get('publisher','')}")
        print(f"   year      : {year}")
        print(f"   volume    : {m.get('volume','')}   issue: {m.get('issue','')}   pages: {m.get('page','')}")
        print(f"   event     : {(m.get('event') or {}).get('name','')}")
    else:
        print(f"== {doi}   [{src}]")
        print(f"   title     : {(m.get('titles') or [{}])[0].get('title','')}")
        print(f"   authors   : {'; '.join(c.get('name','') for c in m.get('creators', []))}")
        print(f"   publisher : {m.get('publisher','')}")
        print(f"   year      : {m.get('publicationYear','')}")
    print()


if __name__ == "__main__":
    for d in sys.argv[1:]:
        show(d)
        time.sleep(0.35)
