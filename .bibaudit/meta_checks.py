#!/usr/bin/env python3
"""Metadata checks for entries Crossref cannot settle: DBLP pages, book records, JSTOR-era articles."""
import json
import re
import urllib.parse
import urllib.request

UA = "thesis-bib-audit/1.0 (mailto:ha.vien@helsinki.fi)"


def get(url, accept="application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def dblp(query, want=3):
    url = "https://dblp.org/search/publ/api?q=" + urllib.parse.quote(query) + "&format=json&h=" + str(want)
    try:
        j = json.loads(get(url))
    except Exception as e:
        print(f"  DBLP error: {e}")
        return
    hits = j.get("result", {}).get("hits", {}).get("hit", [])
    if not hits:
        print("  no DBLP hit")
    for h in hits:
        i = h["info"]
        au = i.get("authors", {}).get("author", [])
        au = [a["text"] if isinstance(a, dict) else a for a in (au if isinstance(au, list) else [au])]
        print(f"  - {i.get('title')}")
        print(f"    venue={i.get('venue')} {i.get('volume','')} year={i.get('year')} pages={i.get('pages')} type={i.get('type')}")
        print(f"    authors={'; '.join(au)}")
        if i.get("doi"):
            print(f"    doi={i['doi']}")


CHECKS = [
    ("fulton2021adopting  (SOUPS'21 pages)", "Benefits and Drawbacks of Adopting a Secure Programming Language"),
    ("agache2020firecracker (NSDI'20 pages+authors)", "Firecracker: Lightweight Virtualization for Serverless Applications"),
    ("narayanan2020redleaf (OSDI'20 pages)", "RedLeaf: Isolation and Communication in a Safe Operating System"),
    ("tang2025converos (ATC'25 pages)", "Converos: Practical Model Checking for Verifying Rust OS Kernel"),
    ("li2024rustforlinux (ATC'24 pages)", "An Empirical Study of Rust-for-Linux"),
    ("schroeder2006openclosed (NSDI'06)", "Open Versus Closed: A Cautionary Tale"),
    ("zhou2025oltp (CIDR'25)", "OLTP Through the Looking Glass 16 Years Later"),
    ("holm1979simple (Scand J Statist)", "A Simple Sequentially Rejective Multiple Test Procedure"),
    ("karlback2021ran", "Holistic View on Alternative Programming Languages for Radio Access Network"),
    ("arvidsson2025async", "Evaluating Asynchronous Programming Frameworks for 5G Control Plane"),
    ("xiao2024rpkt (NPC series/volume)", "rpkt: A Generic, Safe, and Efficient Userspace Packet Processing Library"),
    ("harris2023morello (ECOOP pages)", "Rust for Morello: Always-On Memory Safety"),
    ("skoudlil2025asyncrust (ECRTS pages)", "A First Look at ROS 2 Applications Written in Asynchronous Rust"),
    ("watson2025memorysafety (author count)", "It Is Time to Standardize Principles and Practices for Software Memory Safety"),
    ("jung2018rustbelt (article no.)", "RustBelt: securing the foundations of the Rust programming language"),
    ("li2022crosslang (ESORICS pages)", "Detecting Cross-Language Memory Management Issues in Rust"),
]

for label, query in CHECKS:
    print(f"\n== {label}")
    dblp(query)

print("\n== klabnik2023rust (OpenLibrary ISBN 9781718503106)")
try:
    j = json.loads(get("https://openlibrary.org/api/books?bibkeys=ISBN:9781718503106&format=json&jscmd=data"))
    for k, v in j.items():
        print(f"  {k}: {v.get('title')} | {v.get('subtitle','')}")
        print(f"    authors={[a['name'] for a in v.get('authors', [])]}")
        print(f"    publishers={[p['name'] for p in v.get('publishers', [])]} date={v.get('publish_date')}")
        print(f"    identifiers={ {kk: vv for kk, vv in v.get('identifiers', {}).items() if 'isbn' in kk} }")
    if not j:
        print("  no OpenLibrary record for that ISBN")
except Exception as e:
    print(f"  error: {e}")

print("\n== lizard (PyPI author + release date of 1.23.0)")
try:
    j = json.loads(get("https://pypi.org/pypi/lizard/json"))
    print("  author:", j["info"].get("author"), "| home:", j["info"].get("home_page"))
    rel = j["releases"].get("1.23.0", [])
    print("  1.23.0 uploaded:", rel[0]["upload_time"] if rel else "n/a", "| latest:", j["info"]["version"])
except Exception as e:
    print(f"  error: {e}")

print("\n== alsoran (GitHub owner)")
try:
    j = json.loads(get("https://api.github.com/repos/nplrkn/alsoran"))
    o = json.loads(get("https://api.github.com/users/nplrkn"))
    print("  repo:", j["full_name"], "| desc:", j.get("description"))
    print("  archived:", j.get("archived"), "| pushed:", j.get("pushed_at"), "| license:", (j.get("license") or {}).get("spdx_id"))
    print("  owner name:", o.get("name"), "| login:", o.get("login"))
except Exception as e:
    print(f"  error: {e}")

print("\n== google2024securebydesign (OpenAlex lookup)")
try:
    j = json.loads(get("https://api.openalex.org/works?search=Secure%20by%20Design%20Google%20perspective%20on%20memory%20safety&per_page=3"))
    for w in j.get("results", []):
        print("  -", w.get("title"), "|", w.get("publication_year"), "|", (w.get("primary_location") or {}).get("landing_page_url"))
        print("    authors:", [a["author"]["display_name"] for a in w.get("authorships", [])][:8])
except Exception as e:
    print(f"  error: {e}")
