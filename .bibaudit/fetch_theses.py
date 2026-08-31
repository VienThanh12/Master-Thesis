#!/usr/bin/env python3
"""Download the open-access full texts behind the entries whose passage was never located.

The five student theses are deposited in DiVA or BTH, which publish the PDF beside the record,
so the passage supporting each claim can be read rather than taken from an abstract. Writes to
/tmp/srcs so .bibaudit/evidence.py and pdfgrep.py can search them.
"""
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("/tmp/srcs")
OUT.mkdir(parents=True, exist_ok=True)
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")

TARGETS = {
    "olsson2023ranmgmt": "https://urn.kb.se/resolve?urn=urn:nbn:se:kth:diva-325822",
    "olsson2023asyncpackets": "https://urn.kb.se/resolve?urn=urn:nbn:se:liu:diva-197029",
    "emberg2023asn1": "https://urn.kb.se/resolve?urn=urn:nbn:se:liu:diva-195552",
    "sundvisson2026drivers": "https://urn.kb.se/resolve?urn=urn:nbn:se:bth-29775",
    "andersson2026stdmemsafety": "https://urn.kb.se/resolve?urn=urn:nbn:se:liu:diva-226479",
    "karlback2021ran": "https://urn.kb.se/resolve?urn=urn:nbn:se:liu:diva-176307",
    "arvidsson2025async": "https://urn.kb.se/resolve?urn=urn:nbn:se:liu:diva-214746",
}


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        return (data if binary else data.decode("utf-8", "replace")), r.geturl()


def pdf_links(html, base):
    """Full-text links for a DiVA record.

    The record page is JavaServer Faces and carries no direct link, so the useful route is the
    served path, which DiVA builds from the pid: /smash/get/diva2:NNNN/FULLTEXTnn.pdf. Any
    href that does happen to look like a PDF is tried first.
    """
    out = []
    for h in re.findall(r'href="([^"]+)"', html):
        if re.search(r"FULLTEXT\d*\.pdf|\.pdf$|get/diva2|/bitstream/", h, re.I):
            out.append(urllib.parse.urljoin(base, h.replace("&amp;", "&")))

    host = urllib.parse.urlsplit(base)
    pid = re.search(r"pid=(diva2:\d+)", base)
    if pid:
        for n in ("01", "02", "03"):
            out.append(f"{host.scheme}://{host.netloc}/smash/get/{pid.group(1)}/FULLTEXT{n}.pdf")

    seen, uniq = set(), []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def main():
    keys = sys.argv[1:] or list(TARGETS)
    for key in keys:
        url = TARGETS.get(key)
        if not url:
            print(f"{key}: no target recorded")
            continue
        dest = OUT / f"{key}.pdf"
        if dest.exists() and dest.stat().st_size > 40000:
            print(f"{key}: already have {dest} ({dest.stat().st_size} bytes)")
            continue
        try:
            html, final = get(url)
        except Exception as e:
            print(f"{key}: record page failed: {e}")
            continue
        links = pdf_links(html, final)
        if not links:
            print(f"{key}: no PDF link on {final}")
            continue
        for link in links[:6]:
            try:
                blob, _ = get(link, binary=True)
                if not blob.startswith(b"%PDF"):
                    continue
                dest.write_bytes(blob)
                print(f"{key}: {len(blob)} bytes from {link[:95]}")
                break
            except Exception:
                continue
        else:
            print(f"{key}: no usable PDF among {len(links)} candidates")


if __name__ == "__main__":
    main()
