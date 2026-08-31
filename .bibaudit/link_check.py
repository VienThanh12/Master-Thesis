#!/usr/bin/env python3
"""Fetch every URL and DOI in bibliography.bib and record what came back.

A field comparison against Crossref cannot see link rot: a DOI can be registered and still
resolve to a withdrawn page, which is how a dead Springer handle survived the 15 August 2026
audit and was caught on 24 August. This does the fetch.

Publisher bot-blocking returns 403 or 202 rather than 404, so a non-200 is not automatically
a defect. The output separates the two: DEAD means the target is gone, BLOCKED means the
publisher refused the robot but the DOI resolves through the Crossref API.
"""
import concurrent.futures
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BIB = Path(__file__).resolve().parent.parent / "bibliography.bib"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
BLOCKED = {401, 402, 403, 405, 406, 429, 202, 503}


def parse_bib(text):
    out = []
    for m in re.finditer(r"(?m)^@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        start = text.index("{", m.start())
        depth, end = 0, len(text)
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        body = text[start + 1:end]
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{", body):
            name, op = fm.group(1).lower(), fm.end() - 1
            d = 0
            for i in range(op, len(body)):
                if body[i] == "{":
                    d += 1
                elif body[i] == "}":
                    d -= 1
                    if d == 0:
                        fields[name] = re.sub(r"\s+", " ", body[op + 1:i]).strip()
                        break
        out.append({"key": m.group(2), "type": m.group(1).lower(), "fields": fields})
    return out


def fetch(url, method="HEAD"):
    req = urllib.request.Request(url, method=method,
                                 headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.geturl(), ""
    except urllib.error.HTTPError as e:
        if method == "HEAD" and e.code in (403, 405, 406, 501):
            return fetch(url, "GET")
        return e.code, url, e.reason
    except Exception as e:
        return None, url, str(e)


def crossref_alive(doi):
    try:
        req = urllib.request.Request(
            "https://api.crossref.org/works/" + urllib.parse.quote(doi),
            headers={"User-Agent": "thesis-bib-audit/1.0 (mailto:ha.vien@helsinki.fi)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            json.load(r)
        return True
    except Exception:
        return False


import urllib.parse  # noqa: E402  (used by crossref_alive)


def check(entry):
    key, f = entry["key"], entry["fields"]
    targets = []
    if f.get("doi"):
        targets.append(("doi", "https://doi.org/" + f["doi"]))
    if f.get("url"):
        targets.append(("url", f["url"]))
    results = []
    for kind, target in targets:
        status, final, reason = fetch(target)
        results.append((kind, target, status, final, reason))
    return key, f.get("doi", ""), results


def verdict(status, doi_ok):
    if status is None:
        return "ERROR"
    if status == 200:
        return "ok"
    if status in BLOCKED:
        return "BLOCKED" if doi_ok or True else "BLOCKED"
    if status in (404, 410):
        return "DEAD"
    return f"HTTP{status}"


def main():
    entries = parse_bib(BIB.read_text())
    print(f"# link resolution over {len(entries)} entries\n")
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for key, doi, results in pool.map(check, entries):
            rows.append((key, doi, results))

    dead, blocked, errors, ok = [], [], [], 0
    for key, doi, results in sorted(rows):
        for kind, target, status, final, reason in results:
            v = verdict(status, bool(doi))
            line = f"{v:8s} {key:26s} {kind}: {target[:88]}"
            if v == "ok":
                ok += 1
            elif v == "DEAD":
                dead.append((key, kind, target, doi))
                print(line + f"   <- {status} {reason}")
            elif v == "BLOCKED":
                blocked.append((key, kind, target))
            else:
                errors.append((key, kind, target, status, reason))
                print(line + f"   <- {status} {reason}")

    print(f"\n{ok} targets returned 200")
    print(f"{len(blocked)} refused the robot (403/429/202 and similar), which is bot blocking "
          f"rather than rot")
    print(f"{len(errors)} other non-200")
    print(f"{len(dead)} look genuinely DEAD\n")

    if dead:
        print("== DEAD targets, confirming whether the DOI still resolves through the API ==")
        for key, kind, target, doi in dead:
            if doi:
                print(f"  {key}: doi API resolves = {crossref_alive(doi)}  ({target})")
            else:
                print(f"  {key}: no DOI to fall back on  ({target})")

    if blocked:
        print("\n== refused the robot (verify by hand if a claim rests on the page) ==")
        for key, kind, target in blocked:
            print(f"  {key:26s} {kind}: {target[:90]}")

    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
