"""Cross-check cited bibliography entries in Thesis_Plan_v2 against Crossref."""
import json
import re
import subprocess
import sys
import urllib.parse

BIB = "bibliography.bib"
AUX = "Thesis_Plan_v2.aux"


def cited_keys():
    text = open(AUX, encoding="utf-8").read()
    keys = []
    for m in re.finditer(r"\\citation\{([^}]*)\}", text):
        for k in m.group(1).split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
    return keys


def entries():
    text = open(BIB, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),", text):
        start = m.start()
        depth, i = 0, text.index("{", start)
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        out[m.group(2).strip()] = (m.group(1), text[start:i + 1])
    return out


def field(body, name):
    m = re.search(r"\b" + name + r"\s*=\s*", body, re.I)
    if not m:
        return None
    i = m.end()
    if body[i] == "{":
        depth, j = 0, i
        while j < len(body):
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        val = body[i + 1:j]
    else:
        val = re.match(r"[^,\n}]*", body[i:]).group(0)
    return re.sub(r"\s+", " ", val).strip()


def clean(s):
    s = re.sub(r"[{}\\]|\$", "", s or "")
    return re.sub(r"\s+", " ", s).strip()


def get(url):
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", "40", "-H",
             "User-Agent: ref-check (mailto:thesis@example.org)", url],
            capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout) if r.stdout.strip().startswith("{") else None
    except Exception:
        return None


for key in cited_keys():
    kind, body = entries().get(key, (None, None))
    if body is None:
        print(f"\n### {key}: NOT FOUND IN BIB")
        continue
    title, doi = clean(field(body, "title")), field(body, "doi")
    year, pages = field(body, "year"), clean(field(body, "pages"))
    print(f"\n### {key}  [@{kind}]")
    print(f"  bib title : {title}")
    print(f"  bib year/pages/doi : {year} | {pages} | {doi}")
    if doi:
        d = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
        if not d:
            print("  crossref  : DOI NOT RESOLVED")
            continue
        m = d["message"]
    else:
        d = get("https://api.crossref.org/works?rows=1&query.bibliographic="
                + urllib.parse.quote(title))
        items = (d or {}).get("message", {}).get("items") or []
        if not items:
            print("  crossref  : no match by title")
            continue
        m = items[0]
        print("  (matched by title search)")
    parts = m.get("published-print", m.get("published-online", m.get("issued", {})))
    cy = (parts.get("date-parts") or [[None]])[0][0]
    print(f"  crossref  : {clean((m.get('title') or [''])[0])}")
    print(f"  venue/year/pages/doi : {clean((m.get('container-title') or [''])[0])}"
          f" | {cy} | {m.get('page')} | {m.get('DOI')}")
