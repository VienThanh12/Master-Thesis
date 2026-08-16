#!/usr/bin/env python3
"""Field-by-field comparison of bibliography.bib against Crossref/DataCite records."""
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

BIB = Path("/home/vienha/thesis.local/bibliography.bib")
UA = "thesis-bib-audit/1.0 (mailto:ha.vien@helsinki.fi)"


def parse_bib(text):
    entries = []
    for m in re.finditer(r"^@(\w+)\{([^,]+),", text, re.M):
        start = m.start()
        depth = 0
        i = text.index("{", start)
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    body = text[i + 1 : j]
                    break
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{", body):
            k = fm.group(1).lower()
            d = 0
            st = body.index("{", fm.start(1) + len(fm.group(1)))
            for p in range(st, len(body)):
                if body[p] == "{":
                    d += 1
                elif body[p] == "}":
                    d -= 1
                    if d == 0:
                        fields[k] = re.sub(r"\s+", " ", body[st + 1 : p]).strip()
                        break
        entries.append({"type": m.group(1).lower(), "key": m.group(2).strip(), "fields": fields})
    return entries


def strip_tex(s):
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
    s = s.replace("{", "").replace("}", "").replace("\\", "").replace("~", " ")
    s = s.replace('"', "").replace("'", "").replace("`", "")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip()


def norm(s):
    s = strip_tex(s).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def crossref(doi):
    return fetch("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]


def datacite(doi):
    return fetch("https://api.datacite.org/dois/" + urllib.parse.quote(doi))["data"]["attributes"]


def bib_authors(s):
    return [strip_tex(a.split(",")[0].strip()) for a in re.split(r"\s+and\s+", s)] if s else []


def report(e, rec, src):
    f = e["fields"]
    out = []
    if src == "crossref":
        rtitle = " ".join(rec.get("title", []))
        rauth = [a.get("family", a.get("name", "")) for a in rec.get("author", [])]
        ryear = str((rec.get("issued", {}).get("date-parts") or [[None]])[0][0])
        rvol, riss, rpages = rec.get("volume", ""), rec.get("issue", ""), rec.get("page", "")
        rcont = " / ".join(rec.get("container-title", []) or []) or rec.get("institution", [{}])[0].get("name", "") if rec.get("institution") else " / ".join(rec.get("container-title", []) or [])
        rtype = rec.get("type", "")
    else:
        titles = rec.get("titles") or [{}]
        rtitle = titles[0].get("title", "")
        rauth = [a.get("familyName") or a.get("name", "") for a in rec.get("creators", [])]
        ryear = str(rec.get("publicationYear", ""))
        rvol = (rec.get("container") or {}).get("volume", "")
        riss = (rec.get("container") or {}).get("issue", "")
        rpages = ""
        rcont = (rec.get("container") or {}).get("title", "") or rec.get("publisher", "")
        rtype = ((rec.get("types") or {}).get("resourceTypeGeneral", ""))

    def cmp(label, mine, theirs, fuzzy=False):
        if not mine and not theirs:
            return
        a, b = norm(str(mine)), norm(str(theirs))
        if not mine:
            out.append(f"    MISSING {label}: record has '{theirs}'")
        elif a == b or (fuzzy and (a in b or b in a)):
            out.append(f"    ok  {label}: {strip_tex(str(mine))}")
        else:
            out.append(f"    MISMATCH {label}: bib='{strip_tex(str(mine))}' | record='{theirs}'")

    cmp("title", f.get("title", ""), rtitle, fuzzy=True)
    mine_auth = bib_authors(f.get("author", ""))
    theirs_auth = [strip_tex(x) for x in rauth]
    if norm(" ".join(mine_auth)) == norm(" ".join(theirs_auth)):
        out.append(f"    ok  authors ({len(mine_auth)}): {'; '.join(mine_auth)}")
    else:
        out.append(f"    MISMATCH authors: bib={mine_auth}")
        out.append(f"                    record={theirs_auth}")
    cmp("year", f.get("year", ""), ryear)
    cmp("volume", f.get("volume", ""), rvol)
    cmp("number", f.get("number", ""), riss)
    mine_pages = f.get("pages", "").replace("--", "-")
    cmp("pages", mine_pages, rpages)
    cmp("venue", f.get("journal") or f.get("booktitle") or f.get("institution") or "", rcont, fuzzy=True)
    out.append(f"    record-type: {rtype} | published: {ryear} | src: {src}")
    return out


def main():
    entries = parse_bib(BIB.read_text())
    print(f"# bibliography.bib — {len(entries)} entries\n")
    for e in entries:
        doi = e["fields"].get("doi", "")
        print(f"== {e['key']}  [@{e['type']}]")
        if not doi:
            print("    NO DOI — needs manual primary-source check")
            print(f"    url: {e['fields'].get('url','(none)')}")
            print(f"    note: {e['fields'].get('note','')}")
            print()
            continue
        rec, src = None, None
        for getter, name in ((crossref, "crossref"), (datacite, "datacite")):
            try:
                rec, src = getter(doi), name
                break
            except Exception as ex:
                last = f"{name}: {ex}"
        if rec is None:
            print(f"    DOI NOT RESOLVED via Crossref/DataCite: {doi}  ({last})")
            print()
            continue
        print(f"    doi: {doi}")
        for line in report(e, rec, src):
            print(line)
        print()
        time.sleep(0.4)


if __name__ == "__main__":
    main()
