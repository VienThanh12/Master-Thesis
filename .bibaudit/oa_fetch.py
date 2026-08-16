#!/usr/bin/env python3
"""Locate and download open-access copies of DOI-bearing bibliography entries."""
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

BIB = Path("/home/vienha/thesis.local/bibliography.bib").read_text()
OUT = Path("/tmp/srcs")
OUT.mkdir(exist_ok=True)
EMAIL = "ha.vien@helsinki.fi"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")

entries = []
for m in re.finditer(r"^@(\w+)\{([^,]+),", BIB, re.M):
    nxt = BIB.find("\n@", m.start() + 1)
    body = BIB[m.start(): nxt if nxt > 0 else len(BIB)]
    doi = re.search(r"doi\s*=\s*\{([^}]+)\}", body)
    if doi:
        entries.append((m.group(2).strip(), doi.group(1).strip()))


def jget(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=90, context=ssl.create_default_context()) as r:
        data = r.read()
    if data[:4] != b"%PDF":
        return None
    dest.write_bytes(data)
    return len(data)


for key, doi in entries:
    dest = OUT / f"oa_{key}.pdf"
    if dest.exists():
        print(f"cached {key}")
        continue
    url = None
    try:
        up = jget(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={EMAIL}")
        loc = up.get("best_oa_location") or {}
        url = loc.get("url_for_pdf") or loc.get("url")
        if not url:
            for l in up.get("oa_locations", []):
                url = l.get("url_for_pdf") or l.get("url")
                if url:
                    break
    except Exception as e:
        print(f"unpaywall fail {key}: {e}")
    if not url:
        # fall back to OpenAlex, which sometimes has a landing PDF Unpaywall lacks
        try:
            oa = jget(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}")
            url = ((oa.get("best_oa_location") or {}).get("pdf_url")
                   or (oa.get("primary_location") or {}).get("pdf_url"))
        except Exception as e:
            pass
    if not url:
        print(f"NO OA   {key}  ({doi})")
        continue
    try:
        n = download(url, dest)
        print(f"{'OK     ' if n else 'NOT PDF'} {key}  {url}  {n or ''}")
    except Exception as e:
        print(f"DL FAIL {key}: {e}  <- {url}")
    time.sleep(0.3)
