#!/usr/bin/env python3
"""Generate a citation-audit document: every cited work, the sentence citing it, and the source's words.

The document exists so a reader can check a citation without opening the paper: block [17]
carries reference [17] of the scoped thesis, the sentence that cites it, and the passage in the
source that was read to support that sentence.

Nothing here is transcribed. References are printed by biblatex from bibliography.bib through
\\fullcite, printed citation numbers come from each document's .bbl, the citing sentences come
from the .tex sources, and the per-entry evidence comes from docs/Sources_evidence.md with
docs/LITERATURE_NOTES.md as the fallback. A key with no record is reported as having none.

    .bibaudit/build_audit.py                     # write source_audit.tex (full draft)
    .bibaudit/build_audit.py --document v5       # write source_audit_v5.tex (Thesis_v5)
    .bibaudit/build_audit.py --dump records      # inspect the parsed evidence records
    .bibaudit/build_audit.py --dump sites        # inspect cite sites and printed numbers

Exit status is 1 when a .bbl disagrees with its source's cite keys, because the printed
numbers would then be stale and the whole point of the document is that its numbers match.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "bibliography.bib"
EVIDENCE = ROOT / "docs" / "Sources_evidence.md"
SWEEPS = ROOT / "docs" / "LITERATURE_NOTES.md"
HERE = Path(__file__).resolve().parent

# Part 1's tick column is the one thing in the generated document a human writes, so it is the
# one thing a regeneration must not destroy. The ticks are read back out of the previous
# audit .tex and mirrored to a sidecar, so an accidental delete or a checkout does not lose them.
REVIEWED_KEYS: set[str] = set()

# Matches a Part 1 row far enough to recover its key and its tick, and nothing else.
TICK_ROW = re.compile(r"(?m)^\d+ [^\n]*?\\texttt\{\\small ([^}]+)\}[^\n]*?"
                      r"\$\\(square|blacksquare)\$ \\\\$")

# The three documents that cite this bibliography, with the short label used in the audit and
# the .bbl that fixes their printed numbering. The first of ACTIVE is the audit's spine: its
# printed numbers are the ones in square brackets, and its citing sentences are the ones shown.
DOCUMENTS = [
    ("Ha_Vien_Mastersthesis_2026.tex", "draft", "Full draft"),
    ("Thesis_v5.tex", "v5", "Thesis_v5"),
    ("Thesis_Plan_v2.tex", "plan", "Plan"),
]
DOCUMENT_ALIASES = {"v4": "v5"}  # Thesis_v4 renamed Thesis_v5, 15 Oct 2026
BY_TAG = {tag: doc for doc in DOCUMENTS for tag in [doc[1]]}
AUDIT_OUT = {
    "draft": ROOT / "source_audit.tex",
    "v5": ROOT / "source_audit_v5.tex",
    "plan": ROOT / "source_audit_plan.tex",
}
AUDIT_REVIEWED = {
    "draft": HERE / "reviewed.txt",
    "v5": HERE / "reviewed_v5.txt",
    "plan": HERE / "reviewed_plan.txt",
}
COL_HEADER = {"draft": "dr", "v5": "v5", "plan": "pl"}

# The audit covers the canonical draft by default. It cites all 111 entries, so scoping to it
# loses no entry, and the numbers a reader checks against are the submission document's own.
# --document v5 (or plan) scopes the spine to that file and writes a sibling audit beside it.
# --all-documents widens to the other two, which number the same works differently.
ACTIVE = DOCUMENTS[:1]
OUT = AUDIT_OUT["draft"]
REVIEWED = AUDIT_REVIEWED["draft"]
SPINE_TAG = "draft"
N_BIB = 0


def multi() -> bool:
    return len(ACTIVE) > 1


def other_docs() -> list:
    """Documents in DOCUMENTS that are not the spine, in the table's usual order."""
    return [d for d in DOCUMENTS if d[1] != SPINE_TAG]


def configure(tag: str, all_documents: bool) -> None:
    """Set the spine document, the output path, and which sources contribute citing sentences."""
    global ACTIVE, OUT, REVIEWED, SPINE_TAG
    tag = DOCUMENT_ALIASES.get(tag, tag)
    if tag not in BY_TAG:
        raise SystemExit(f"unknown --document {tag!r}; choose from {', '.join(BY_TAG)}")
    spine = BY_TAG[tag]
    rest = [d for d in DOCUMENTS if d[1] != tag]
    ACTIVE = [spine] + rest if all_documents else [spine]
    OUT = AUDIT_OUT[tag]
    REVIEWED = AUDIT_REVIEWED[tag]
    SPINE_TAG = tag


def rebuild_cmd() -> str:
    flag = "" if SPINE_TAG == "draft" else f" --document {SPINE_TAG}"
    return f".bibaudit/build_audit.py{flag} && latexmk -pdf {OUT.name}"


def read_review_marks() -> set[str]:
    """Recover the author's review ticks from the document about to be overwritten.

    The previous audit .tex wins when it exists, because that is where the ticks are
    made and it is the only copy that can record one being taken back. The sidecar is the
    fallback, for when the document has been deleted rather than edited.
    """
    held: set[str] = set()
    if REVIEWED.exists():
        held = {line.strip() for line in REVIEWED.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")}
    if OUT.exists():
        rows = TICK_ROW.findall(OUT.read_text(encoding="utf-8"))
        if rows:
            printed = {key for key, _ in rows}
            ticked = {key for key, tick in rows if tick == "blacksquare"}
            # A key that had a row and lost its tick was unticked deliberately, so it does not
            # come back from the sidecar. A key with no row at all was out of scope last run,
            # and its tick is held so that recovering the citation recovers the review too.
            return ticked | (held - printed)
    return held


def write_review_marks(keys: set[str]) -> None:
    header = (f"# Entries ticked as reviewed in Part 1 of {OUT.name}.\n"
              "# Mirrored by .bibaudit/build_audit.py so the ticks survive the document being\n"
              f"# regenerated or deleted. Edit the tick in {OUT.name}, not here.\n")
    REVIEWED.write_text(header + "".join(k + "\n" for k in sorted(keys)), encoding="utf-8")

CITE = re.compile(r"\\(?:cite|citep|citet|textcite|parencite|autocite|footcite)\*?"
                  r"(?:\[[^\]]*\])*\{([^}]*)\}")

# Sections of docs/LITERATURE_NOTES.md that carry the verified record for a key whose name the
# section never mentions, so no search can find it. A pointer table, not transcribed evidence:
# the generator still reads the section body out of the file.
SWEEP_SECTIONS = {
    "bensalem2005deadlock": "B.5 Bensalem and Havelund",
    "bornholt2021shardstore": "B.1 Bornholt et al., SOSP 2021",
    "pearce2026rustmc": "The anchor: Pearce, Lange and O'Keeffe, FORTE 2026",
    "tsandeadlock": "B.6 The two tool records, as tool records",
    "clangtidyuseaftermove": "C.9 clang-tidy",
    "lu2008mistakes": "C.1 Lu, Park, Seo and Zhou, ASPLOS 2008",
    "dietz2015overflow": "C.2 Dietz, Li, Regehr and Adve, TOSEM 2015",
    "cui2024rcanary": "C.3 Cui, Xu, Tian and Zhou, TSE 2024",
    "naylor2026cherisimt": "F.0b Naylor et al., ASPLOS 2026",
}


# --------------------------------------------------------------------------- helpers

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_tex(s: str) -> str:
    # Accents come in two shapes and both have to go, or a surname keeps the mark as a
    # literal character: \v S and \'a are letter commands, \"a and \^o are not.
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
    s = re.sub(r"""\\['"`^~=.]""", "", s)
    for ch in "{}\\~":
        s = s.replace(ch, "")
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


# --------------------------------------------------------------------------- bibliography

def parse_bib(text: str) -> dict:
    """key -> {type, fields} with brace-balanced field values."""
    entries = {}
    for m in re.finditer(r"(?m)^@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        kind, key = m.group(1).lower(), m.group(2)
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
        for fm in re.finditer(r"(\w+)\s*=\s*[{\"]", body):
            name = fm.group(1).lower()
            open_at = fm.end() - 1
            if body[open_at] == "{":
                d = 0
                for i in range(open_at, len(body)):
                    if body[i] == "{":
                        d += 1
                    elif body[i] == "}":
                        d -= 1
                        if d == 0:
                            fields[name] = re.sub(r"\s+", " ", body[open_at + 1:i]).strip()
                            break
            else:
                close = body.find('"', open_at + 1)
                if close > 0:
                    fields[name] = re.sub(r"\s+", " ", body[open_at + 1:close]).strip()
        entries[key] = {"type": kind, "fields": fields}
    return entries


def source_kind(entry: dict) -> str:
    """What sort of thing the reader is being asked to trust.

    Read from the fields rather than from the URL host alone: a conference talk archived in a
    GitHub repository is a talk, not a tool record, so the repository check applies only when
    the entry declares no venue of its own.
    """
    kind, f = entry["type"], entry["fields"]
    if kind in ("article", "inproceedings", "incollection"):
        return "peer reviewed"
    if kind == "techreport":
        return "standard"
    if kind == "mastersthesis":
        return "thesis"
    if kind == "book":
        return "book"
    how, note, url = (f.get("howpublished", "").lower(), f.get("note", "").lower(),
                      f.get("url", "").lower())
    if "wg21" in how or "open-std" in url or "isocpp" in url:
        return "committee draft"
    if "official journal" in how:
        return "regulation"
    if any(w in how or w in note for w in ("documentation", "repository", "software")):
        return "tool record"
    if not how and any(h in url for h in ("github.com", "pypi.org")):
        return "tool record"
    return "grey"


def is_corporate(entry: dict) -> bool:
    """True when the author field is one institutional name that must not be split on 'and'.

    The test is that the whole value sits inside one brace group, which is how such names are
    written. A leading brace alone is not enough: an accented surname like {\\v S}koudlil opens
    with one too, and reading that as institutional prints the entire author list as a name.
    """
    au = entry["fields"].get("author", "")
    if not au.startswith("{") or not au.endswith("}"):
        return False
    depth = 0
    for i, ch in enumerate(au):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i == len(au) - 1
    return False


def first_author(entry: dict) -> str:
    au = entry["fields"].get("author", "")
    if not au:
        return ""
    if is_corporate(entry):
        return strip_tex(au)
    first = strip_tex(au.split(" and ")[0])
    if "," in first:
        return first.split(",")[0].strip()
    return first.split()[-1] if first.split() else ""


def checklist_label(key: str, entry: dict, cap: int = 30) -> str:
    """The source label for the checklist column, truncated to one line.

    Institutional names run to fifty characters and wrap to three or four rows, which makes the
    table hard to scan. Nothing is lost: the cite key beside it already identifies the issuer,
    and Part 2 prints the reference in full.
    """
    label = short_label(key, entry)
    if len(label) <= cap:
        return label
    year = re.search(r"\b(\d{4})$", label)
    head = label[:cap].rsplit(" ", 1)[0].rstrip(",")
    return f"{head}\\ldots{{}} {year.group(1)}" if year else head + "\\ldots{}"


def short_label(key: str, entry: dict) -> str:
    who = first_author(entry) or key
    year = entry["fields"].get("year", "")
    if not is_corporate(entry):
        au = entry["fields"].get("author", "")
        if au and len(re.split(r"\s+and\s+", au)) > 2:
            who += " et al."
    return f"{who} {year}".strip()


# --------------------------------------------------------------------------- printed numbers

def printed_numbers(stem: str) -> list:
    """Keys in printed order, read from the .bbl that biber wrote."""
    for candidate in (ROOT / "build" / f"{stem}.bbl", ROOT / f"{stem}.bbl"):
        if candidate.is_file():
            return re.findall(r"\\entry\{([^}]+)\}", read(candidate))
    return []


# --------------------------------------------------------------------------- cite sites

def structure_at(lines: list) -> list:
    """For each source line, the division label in force there.

    Handles both of the document classes in this repository: the thesis class, where
    \\chapter is the top level and \\appendix switches the counter to letters, and the
    article class the plan uses, where \\section is the top level.
    """
    body = "\n".join(lines)
    chaptered = bool(re.search(r"(?m)^\s*\\chapter\{", body))
    letters = "ABCDEFGHIJKLMNOP"
    labels, chap, sec, sub, in_appendix = [], 0, 0, 0, False

    for raw in lines:
        s = raw.lstrip()
        if s.startswith("\\begin{appendices}"):
            in_appendix, chap, sec, sub = True, 0, 0, 0
        elif re.match(r"\\appendix\{", s):
            # The full draft redefines \appendix to take the title where \chapter would, so
            # here it is a heading and not merely the switch into appendix numbering.
            in_appendix, sec, sub = True, 0, 0
            chap += 1
        elif s.startswith("\\appendix"):
            in_appendix, chap, sec, sub = True, 0, 0, 0
        elif re.match(r"\\chapter(\*)?\{", s):
            if "\\chapter*" not in s:
                chap += 1
            sec = sub = 0
        elif re.match(r"\\section(\*)?[\[{]", s):
            if "\\section*" not in s:
                sec += 1
            sub = 0
        elif re.match(r"\\subsection(\*)?[\[{]", s):
            if "\\subsection*" not in s:
                sub += 1

        if chaptered:
            if not chap:
                label = "front matter"
            else:
                stem = letters[chap - 1] if in_appendix else str(chap)
                if sub:
                    label = f"Section {stem}.{sec}.{sub}"
                elif sec:
                    label = f"Section {stem}.{sec}"
                else:
                    label = ("Appendix " if in_appendix else "Chapter ") + stem
        else:
            if not sec:
                label = "front matter"
            elif sub:
                label = f"Section {sec}.{sub}"
            else:
                label = f"Section {sec}"
        labels.append(label)
    return labels


FLOAT_JUNK = re.compile(
    r"\\(?:begin|end)\{[^}]*\}(?:\[[^\]]*\])?"
    r"|\\(?:centering|small|footnotesize|scriptsize|tiny|normalsize|raggedright|raggedleft"
    r"|toprule|midrule|bottomrule|hline|arraybackslash|noindent)\b"
    r"|\\(?:renewcommand|setlength)\{[^}]*\}\{[^}]*\}"
    r"|\\label\{[^}]*\}"
    r"|\\multicolumn\{\d+\}\{[^}]*\}"
)


def brace_arg(text: str, start: int):
    """Span of the {...} argument beginning at or after start, skipping an optional [...]."""
    i = start
    while i < len(text) and text[i] in " \t":
        i += 1
    if i < len(text) and text[i] == "[":
        depth = 0
        while i < len(text):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
    while i < len(text) and text[i] in " \t":
        i += 1
    if i >= len(text) or text[i] != "{":
        return None
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return i + 1, j
    return None


def sentence_of(paragraph: str, cite_span: tuple) -> tuple:
    """The smallest readable unit of a joined paragraph that holds the citation.

    Most citations sit in running prose and the unit is a sentence. A citation inside a float
    needs narrowing first, or the extracted text drags in column specifications and rule
    commands: a caption narrows to its own argument, and a table entry narrows to its cell.
    Returns (text, kind) so the audit can say which of the three it is showing.
    """
    kind, lo, hi = "prose", 0, len(paragraph)

    for m in re.finditer(r"\\caption(?:of\{[^}]*\})?", paragraph):
        arg = brace_arg(paragraph, m.end())
        if arg and arg[0] <= cite_span[0] < arg[1]:
            lo, hi, kind = arg[0], arg[1], "caption"
            break
    text, off = paragraph[lo:hi], cite_span[0] - lo

    if re.search(r"\\\\|&", text):
        seps = list(re.finditer(r"\\\\|&", text))
        starts = [0] + [m.end() for m in seps]
        ends = [m.start() for m in seps] + [len(text)]
        for s, e in zip(starts, ends):
            if s <= off < e:
                if kind == "prose":
                    kind = "table cell"
                text, off = text[s:e], off - s
                break

    bounds = [0] + [m.end() for m in re.finditer(r"(?<=[.!?])\s+(?=[A-Z\\`(])", text)] + [len(text)]
    for i in range(len(bounds) - 1):
        if bounds[i] <= off < bounds[i + 1]:
            text = text[bounds[i]:bounds[i + 1]]
            break

    text = FLOAT_JUNK.sub(" ", text)
    return re.sub(r"\s{2,}", " ", text).strip(" &\\"), kind


def cite_sites(path: Path) -> list:
    """Every citation in a document: keys, the carrying sentence, line and section."""
    raw_lines = read(path).splitlines()
    labels = structure_at(raw_lines)
    sites = []
    para, para_lines = [], []
    def flush():
        if not para:
            return
        joined = " ".join(para)
        offsets = []  # (char offset in joined, source line number)
        pos = 0
        for text, lineno in zip(para, para_lines):
            offsets.append((pos, lineno))
            pos += len(text) + 1
        for m in CITE.finditer(joined):
            lineno = para_lines[0]
            for off, ln in offsets:
                if off <= m.start():
                    lineno = ln
            sentence, kind = sentence_of(joined, m.span())
            sites.append({
                "keys": [k.strip() for k in m.group(1).split(",") if k.strip()],
                "sentence": sentence,
                "kind": kind,
                "line": lineno,
                "section": labels[lineno - 1] if lineno - 1 < len(labels) else "",
            })
        para.clear()
        para_lines.clear()

    # A heading is not part of the paragraph that follows it, and the thesis does not always
    # leave a blank line between the two. Without this break the heading text is pulled into
    # the first extracted sentence of the section.
    heading = re.compile(r"\\(?:chapter|section|subsection|subsubsection|paragraph|appendix)"
                         r"\*?[\[{]|\\(?:chapter|section|subsection)mark\{")

    for i, raw in enumerate(raw_lines, 1):
        stripped = raw.strip()
        if stripped.startswith("%"):
            continue
        if not stripped or heading.match(stripped):
            flush()
            continue
        para.append(stripped)
        para_lines.append(i)
    flush()
    return sites


# --------------------------------------------------------------------------- evidence records

FIELD = re.compile(r"(?m)^\*\*([^*\n]+?)\*\*\s*")


def is_field_label(text: str) -> bool:
    """Whether a bold run at the start of a line is a field label or emphasis inside a value.

    The records mark their fields as **Metadata**, **Cited**, **Evidence -- level A** and so on,
    and they also bold phrases inside a quotation. When a bolded phrase happens to fall at the
    start of a wrapped line it looks exactly like a label, and reading it as one silently moves
    the rest of the quotation into a field of its own. Seven entries were affected.

    Real labels are short, capitalised, carry no digits, and do not end in sentence
    punctuation. The capitalisation rule is what separates a label from a bolded phrase
    lifted out of a quotation, which reads as running prose.
    """
    text = text.strip()
    return (len(text) <= 40
            and text[:1].isupper()
            and not re.search(r"\d", text)
            and not text.endswith((".", ",", ":", ";")))


def split_fields(body: str) -> list:
    """[(label, text)] for a run of **Label** paragraphs."""
    marks = [m for m in FIELD.finditer(body) if is_field_label(m.group(1))]
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        out.append((m.group(1).strip(), body[m.end():end].strip()))
    return out


def parse_evidence(text: str) -> dict:
    """key -> record, from the '### `key` — Title' sections of Sources_evidence.md."""
    records = {}
    chunks = re.split(r"(?m)^### ", text)
    for chunk in chunks[1:]:
        head, _, body = chunk.partition("\n")
        km = re.match(r"`([^`]+)`\s*(?:[-—]{1,2}\s*(.*))?", head.strip())
        if not km:
            continue
        key = km.group(1)
        # A section ends at the next heading of any level.
        body = re.split(r"(?m)^#{2,4}\s", body)[0]
        body = re.split(r"(?m)^---\s*$", body)[0]
        rec = {"key": key, "title": (km.group(2) or "").strip(),
               "origin": "Sources_evidence.md, entry record",
               "level": None, "claim": "", "metadata": "", "evidence": "",
               "verdict": "", "extra": []}
        for label, value in split_fields(body):
            lm = re.match(r"Evidence\s*(?:[-—]{1,2}\s*)?level\s*([ABC])", label, re.I)
            if lm:
                rec["level"] = lm.group(1).upper()
                rec["evidence"] = value
            elif label.lower().startswith("evidence"):
                rec["evidence"] = value
            elif label.lower() == "metadata":
                rec["metadata"] = value
            elif label.lower() == "cited":
                rec["claim"] = strip_site_refs(value)
            elif label.lower() == "verdict":
                rec["verdict"] = value
            else:
                rec["extra"].append((label, value))
        records[key] = rec
    return records


def strip_site_refs(value: str) -> str:
    """Keep the claim description from a **Cited** field, drop the reference list.

    The field is written as a list of file and line references, then a dash, then the claim.
    Splitting on the dash is what keeps the claim intact: scrubbing the references out instead
    leaves the separators and any count phrase behind them stranded.

    The line numbers are dropped rather than reported because they go stale, and this document
    recomputes every citation site from the sources anyway.
    """
    parts = re.split(r"\s+[—–]\s+|\s+--\s+", value.strip(), maxsplit=1)
    claim = parts[1] if len(parts) > 1 else parts[0]
    claim = re.sub(r"`[^`]*\.tex:[^`]*`", "", claim)
    claim = re.sub(r"^\s*(?:cited\s+)?(?:\w+\s+times,?\s*)?(?:incl\.?|including)?[\s;,.]*", "",
                   claim, flags=re.I)
    return claim.strip(" ;,.")


def parse_reverified(text: str) -> dict:
    """The 24 August bullet pass: '- `key` — **level A.** ...' entries."""
    records = {}
    for m in re.finditer(r"(?m)^- `([^`]+)` [-—]{1,2} \*\*level ([ABC])[.,]?\*\*"
                         r"(.*?)(?=(?:\n- `)|(?:\n\n?###)|(?:\n\n?##)|\Z)",
                         text, re.S):
        key, level, body = m.group(1), m.group(2), m.group(3)
        records[key] = {
            "key": key, "title": "", "origin": "Sources_evidence.md, 24 August verification pass",
            "level": level, "claim": "", "metadata": "",
            "evidence": re.sub(r"\s+", " ", body).strip(" .,"),
            "verdict": "", "extra": [],
        }
    return records


def sweep_sections(text: str) -> dict:
    """heading -> body, for every '###'/'####' section of LITERATURE_NOTES.md."""
    out = {}
    marks = list(re.finditer(r"(?m)^#{3,4}\s+(.*)$", text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[m.group(1).strip()] = text[m.end():end].strip()
    return out


def section_label(heading: str) -> str:
    """A pointer to a sweep section: its number and name, without the VERIFIED verdict."""
    return re.split(r"\s+[—–]\s+|\s+--\s+", heading)[0].strip()


def sweep_list_items(text: str) -> list:
    """[(lead_in, whole_item)] for numbered list items opening with a bold author and venue.

    The third literature sweep records its eight peer-reviewed additions this way, one numbered
    item each, and no item names the cite key. Matching on the author and year in the bold
    lead-in reaches them without a hand-written table.
    """
    items = []
    for m in re.finditer(r"(?m)^\d+\.\s+\*\*([^*]+)\*\*(.*?)(?=(?:\n\d+\.\s+\*\*)|(?:\n\n)|\Z)",
                         text, re.S):
        items.append((m.group(1), (m.group(1) + m.group(2))))
    return items


def match_list_item(items: list, surname: str, year: str) -> str | None:
    """The one list item that names this author, disambiguated by year when the name repeats."""
    if not surname:
        return None
    hits = [whole for lead, whole in items if re.search(r"\b" + re.escape(surname) + r"\b", lead)]
    if len(hits) > 1 and year:
        hits = [h for h in hits if year in h]
    return re.sub(r"\s*\n\s*", " ", hits[0]).strip() if len(hits) == 1 else None


def sweep_mentions(text: str, key: str) -> list:
    """Table rows and prose lines of LITERATURE_NOTES.md that name the key, outside code fences."""
    hits, fenced = [], False
    for raw in text.splitlines():
        if raw.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced or f"`{key}`" not in raw:
            continue
        line = raw.strip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            line = ". ".join(c for c in cells if c and not set(c) <= set("-: "))
        line = re.sub(r"^[>\-\d.*\s]+", "", line).strip()
        if len(line) > 40:
            hits.append(line)
    return hits


def build_records(bib: dict) -> dict:
    ev_text, sw_text = read(EVIDENCE), read(SWEEPS)
    records = parse_evidence(ev_text)
    for key, rec in parse_reverified(ev_text).items():
        records.setdefault(key, rec)

    sections = sweep_sections(sw_text)
    items = sweep_list_items(sw_text)
    for key in bib:
        if key in records:
            continue
        wanted = SWEEP_SECTIONS.get(key)
        heading = body = None
        if wanted:
            for head, text in sections.items():
                if wanted in head:
                    heading, body = head, text
                    break
        if body:
            records[key] = {
                "key": key, "title": "", "claim": "", "metadata": "", "verdict": "", "extra": [],
                "level": "A" if "VERIFIED" in heading else None,
                "origin": f"LITERATURE_NOTES.md, section {section_label(heading)}",
                "evidence": trim_sweep_body(body),
            }
            continue
        item = match_list_item(items, first_author(bib[key]), bib[key]["fields"].get("year", ""))
        if item:
            records[key] = {
                "key": key, "title": "", "claim": "", "metadata": "", "verdict": "", "extra": [],
                "level": "B", "evidence": item,
                "origin": "LITERATURE_NOTES.md, peer-reviewed additions of the third sweep",
            }
            continue
        mentions = sweep_mentions(sw_text, key)
        if mentions:
            records[key] = {
                "key": key, "title": "", "claim": "", "metadata": "", "verdict": "", "extra": [],
                "level": None, "evidence": " ".join(mentions[:3]),
                "origin": "LITERATURE_NOTES.md, sweep notes",
            }

    # A record whose key is not in the bibliography describes a renamed or dropped entry. It can
    # never be printed, so report it rather than carrying it silently.
    orphans = sorted(set(records) - set(bib))
    for key in orphans:
        print(f"NOTE: evidence record for {key!r}, which is not a bibliography key. "
              f"Renamed or dropped entry.", file=sys.stderr)
        del records[key]
    return records


def trim_sweep_body(body: str, limit: int = 1800) -> str:
    """The opening of a sweep section, cut at a paragraph boundary.

    A sweep section can run for pages. Truncation drops a trailing lead-in, since a paragraph
    ending in a colon promises a list that the cut has just removed.
    """
    body = re.split(r"(?m)^#{2,4}\s", body)[0].strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    kept, total = [], 0
    for p in paragraphs:
        if total + len(p) > limit and kept:
            break
        kept.append(p)
        total += len(p)
    while kept and kept[-1].rstrip().endswith(":"):
        kept.pop()
    return "\n\n".join(kept)


# --------------------------------------------------------------------------- markdown to LaTeX

DASH_KEPT = 0
SEMI_KEPT = 0


def protect(text: str) -> tuple:
    """Pull `code` and $math$ out of reach of the escaper."""
    store = []

    def stash(m, wrap):
        store.append((wrap, m.group(1)))
        return f"\x00{len(store) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: stash(m, "code"), text)
    text = re.sub(r"\$([^$]+)\$", lambda m: stash(m, "math"), text)
    return text, store


VERBATIM_ESCAPES = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$",
                    "&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_",
                    "^": r"\textasciicircum{}", "~": r"\textasciitilde{}"}


def restore(text: str, store: list) -> str:
    """Put the protected spans back, escaping code spans so \\texttt can set them literally."""
    def put(m):
        wrap, body = store[int(m.group(1))]
        if wrap == "math":
            return f"${body}$"
        body = re.sub(r"[\\{}$&%#_^~]", lambda c: VERBATIM_ESCAPES[c.group(0)], body)
        return "\\texttt{" + body + "}"
    return re.sub(r"\x00(\d+)\x00", put, text)


def rewrite_asides(text: str) -> str:
    """Replace em-dash asides and prose semicolons outside quotations.

    The repository forbids both wherever a reader sees them. Quoted source text is exempt,
    because changing a quotation's punctuation misquotes it, so quotations are split out
    first and passed through untouched.
    """
    global DASH_KEPT, SEMI_KEPT
    parts = re.split(r'("[^"]*")', text)
    for i, part in enumerate(parts):
        if part.startswith('"') and part.endswith('"') and len(part) > 1:
            DASH_KEPT += len(re.findall(r"[—–]|--", part))
            SEMI_KEPT += part.count(";")
            continue
        part = re.sub(r"\s*[—]\s*(?=[a-z0-9`(])", ", ", part)
        part = re.sub(r"\s*[—]\s*", ". ", part)
        part = re.sub(r";\s+(?=[a-z`(])", ", ", part)
        part = re.sub(r";\s+", ". ", part)
        parts[i] = part
    return "".join(parts)


ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "#": r"\#",
           "_": r"\_", "{": r"\{", "}": r"\}", "^": r"\textasciicircum{}"}

# Characters the notes use freely and pdflatex will not set without help.
UNICODE = {"✔": "[verified]", "⚠": "[nit]", "✖": "[wrong]", "→": "$\\rightarrow$",
           "←": "$\\leftarrow$", "§": "\\S{}", "≈": "$\\approx$", "×": "$\\times$",
           "≤": "$\\leq$", "≥": "$\\geq$", "±": "$\\pm$", "∼": "$\\sim$", "−": "$-$",
           "µ": "$\\mu$", "…": "\\ldots{}", "’": "'", "‘": "'", "“": "``", "”": "''",
           "–": "--", "―": "--", "•": "\\textbullet{}", "\u00a0": " ", "\u2009": "\\,",
           "\u200b": ""}


def md_to_tex(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s*\n\s*", " ", text.strip())
    # Line numbers written into the records go stale as the sources are edited, and this
    # document recomputes every citation site anyway. Keep the filename, drop the numbers.
    # Has to happen before protect(), since these sit inside backticks.
    text = re.sub(r"(\.tex):[\d,\s]*\d", r"\1", text)
    # The notes quote thesis source, so an ellipsis reaches this point as LaTeX. Fold it back
    # to the character, which the escaper then re-emits as \ldots rather than printing it.
    text = re.sub(r"\\ldots\{\}|\\ldots\b|\\dots\b", "…", text)
    text = rewrite_asides(text)
    text, store = protect(text)

    # One pass, so that the braces of \textbackslash{} are not themselves escaped.
    text = re.sub(r"[\\&%#_{}^]", lambda m: ESCAPES[m.group(0)], text)
    text = re.sub("|".join(re.escape(c) for c in UNICODE),
                  lambda m: UNICODE[m.group(0)], text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"\\emph{\1}", text)
    text = re.sub(r'"([^"]*)"', r"\\enquote{\1}", text)
    text = re.sub(r"<(https?://[^>]+)>", r"\\url{\1}", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\\href{\2}{\1}", text)
    return restore(text, store).strip()


# --------------------------------------------------------------------------- thesis sentences

def sentence_to_tex(sentence: str, numbering: dict) -> str:
    """A citing sentence, verbatim, with \\cite replaced by the printed number it prints as."""
    def swap(m):
        keys = [k.strip() for k in m.group(1).split(",") if k.strip()]
        nums = [str(numbering[k]) for k in keys if k in numbering]
        return "\\citemark{" + ", ".join(nums) + "}" if nums else "\\citemark{?}"

    text = CITE.sub(swap, sentence)
    text = re.sub(r"\\(?:auto|c|C|page|name|full|Full)?ref\{([^}]+)\}", r"\\refmark{\1}", text)
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = re.sub(r"\\(?:chapter|section|subsection|paragraph)mark\{[^}]*\}", "", text)
    text = re.sub(r"~", "\\\\,", text) if False else text
    return text.strip()


# --------------------------------------------------------------------------- LaTeX emission

PREAMBLE = r"""%% GENERATED FILE. Do not edit, with one exception.
%% Written by .bibaudit/build_audit.py. Regenerate instead of correcting by hand:
%%     .bibaudit/build_audit.py && latexmk -pdf source_audit.tex
%%
%% The exception is Part 1's last column, which is the author's review tick. Change a
%% $\square$ to a $\blacksquare$ to record that an entry has been checked. The generator
%% reads those ticks back before it overwrites this file and reprints them, and mirrors
%% them to .bibaudit/reviewed.txt so they survive the file being deleted. Everything else
%% here is derived, so a hand edit to it is lost on the next run.
%%
%% Every reference below is printed by biblatex from bibliography.bib. Every printed
%% citation number is read from the corresponding .bbl. Every citing sentence is copied
%% from the thesis source. None of it is retyped here, so this document cannot disagree
%% with the thesis about what a reference says or which number it carries.
\documentclass[10pt,a4paper]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[a4paper,margin=22mm,bottom=24mm]{geometry}
\usepackage{microtype}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{array}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{enumitem}
\usepackage{csquotes}
\usepackage{xcolor}
\usepackage{fancyhdr}

%% The thesis's own biblatex configuration, so \fullcite formats a reference with the same
%% code that formats the thesis bibliography.
\usepackage[style=numeric,bibstyle=numeric,backend=biber,natbib=true,
            sorting=none,sortcites=true,maxbibnames=99,giveninits=true,uniquename=init]{biblatex}
\addbibresource{bibliography.bib}
\DeclareNameAlias{sortname}{family-given}

\usepackage[colorlinks=true,linkcolor=black,citecolor=black,urlcolor=blue!55!black]{hyperref}

%% The generated macro files the thesis reads. A citing sentence that quotes a measured
%% value therefore prints the value, not the macro name.
\input{figures/gen_macros.tex}
\input{figures/gen_complexity.tex}
\input{figures/gen_artefacts.tex}
\input{figures/gen_adoption.tex}
\input{figures/gen_baremetal.tex}
\input{figures/gen_guest.tex}

%% A citation inside a quoted sentence prints as the number the thesis prints, and a
%% cross-reference prints as its label, since this document has no such target of its own.
\newcommand{\citemark}[1]{\textbf{[#1]}}
\newcommand{\refmark}[1]{\textsl{#1}}

\newcommand{\entryrule}{\par\medskip\noindent\textcolor{black!35}{\rule{\linewidth}{0.6pt}}\par\nobreak\smallskip}
\newcommand{\auditentry}[3]{%
  \entryrule
  \phantomsection\addcontentsline{toc}{subsection}{[#1] #2}%
  \noindent{\large\textbf{[#1]}}\quad\texttt{\textbf{#2}}\hfill{\small #3}\par\nobreak\smallskip}
\newcommand{\afield}[2]{\par\noindent\textbf{#1.}\enspace #2\par}
\newenvironment{saidquote}%
  {\begin{quote}\small\itshape}%
  {\end{quote}}
\newenvironment{citedsentence}%
  {\begin{quote}\small}%
  {\end{quote}}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.45em}

%% Quoted passages carry long identifiers and URLs that cannot be hyphenated, so give the
%% line breaker room rather than leaving overfull boxes in a document meant to be read.
\sloppy
\emergencystretch=3em

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small Citation audit}
\fancyhead[R]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}

\title{Citation audit\\[2pt]\large Every cited work, the sentence citing it, and where the
claim sits in the source}
\author{Ha Vien}
"""


def emit_preamble() -> str:
    """The LaTeX header. The draft path returns the template unchanged so a default
    regeneration cannot drift from the document already on disk."""
    if SPINE_TAG == "draft":
        return PREAMBLE
    stem = ACTIVE[0][0].replace(".tex", "").replace("_", r"\_")
    text = PREAMBLE
    text = text.replace(
        ".bibaudit/build_audit.py && latexmk -pdf source_audit.tex",
        rebuild_cmd())
    text = text.replace(".bibaudit/reviewed.txt", f".bibaudit/{REVIEWED.name}")
    text = text.replace(
        r"\fancyhead[L]{\small Citation audit}",
        r"\fancyhead[L]{\small Citation audit of " + ACTIVE[0][2].replace("_", r"\_") + "}")
    text = text.replace(
        "\\title{Citation audit\\\\[2pt]\\large Every cited work, the sentence citing it, and where the\n"
        "claim sits in the source}",
        "\\title{Citation audit of \\texttt{" + stem + "}\\\\[2pt]\\large Every work it "
        "cites, the sentence citing it, and where the\nclaim sits in the source}")
    return text


def tex_escape_plain(s: str) -> str:
    for ch in ("\\", "&", "%", "#", "_", "{", "}"):
        s = s.replace(ch, {"\\": "\\textbackslash{}"}.get(ch, "\\" + ch))
    return s


def build_document(bib, records, sites_by_doc, numbering, spine) -> str:
    out = [emit_preamble(), f"\\date{{Generated {date.today().isoformat()}}}",
           "", "\\begin{document}", "\\maketitle", ""]

    total_sites = Counter()
    per_key_sites = defaultdict(list)
    for tex_name, tag, label in ACTIVE:
        for site in sites_by_doc[tag]:
            for key in site["keys"]:
                per_key_sites[key].append((tag, label, site))
                total_sites[key] += 1

    levels = Counter((records[k]["level"] or "none") if k in records else "absent" for k in spine)
    unlocated = [k for k in spine if k not in records or not records[k]["level"]]
    level_c = [k for k in spine if k in records and records[k]["level"] == "C"]

    out.append(part0(bib, spine, numbering, levels, unlocated))
    out.append(part1(bib, records, spine, numbering, total_sites))
    out.append(part2(bib, records, spine, numbering, per_key_sites))
    out.append(part3(bib, records, spine, numbering, unlocated, level_c))
    n_commands = sum(len(v) for v in sites_by_doc.values())
    out.append(part4(bib, records, spine, numbering, levels, total_sites, n_commands))

    out.append("\\end{document}")
    return "\n".join(out)


def status_of(rec) -> str:
    if rec is None:
        return "no record"
    verdict = rec.get("verdict", "")
    if verdict.upper().startswith("OK"):
        return "ok"
    if verdict:
        return "note"
    return "ok" if rec.get("level") else "sweep"


def part0(bib, spine, numbering, levels, unlocated) -> str:
    if multi():
        others = " or ".join(r"\texttt{" + tex_escape_plain(d[0].replace(".tex", "")) + "}"
                             for d in other_docs())
        scope = (rf"""Where a work is also cited by
{others}, the number it carries in those documents is given as well,
because their lists are shorter and number the same work differently.""")
        opener = (r"""This document lists every work in \texttt{bibliography.bib}. It is ordered by the number the
work carries in the thesis's reference list, so entry \textbf{[17]} here is reference
\textbf{[17]} there and the two can be read side by side. """)
    elif SPINE_TAG == "draft":
        scope = (r"""It covers
\texttt{Ha\_Vien\_Mastersthesis\_2026} alone, which is the submission document and the only one
that cites every entry, so a number here is always that document's number and never needs
translating.""")
        opener = (r"""This document lists every work in \texttt{bibliography.bib}. It is ordered by the number the
work carries in the thesis's reference list, so entry \textbf{[17]} here is reference
\textbf{[17]} there and the two can be read side by side. """)
    else:
        stem = tex_escape_plain(ACTIVE[0][0].replace(".tex", ""))
        n_unused = N_BIB - len(spine)
        scope = (rf"""It covers
\texttt{{{stem}}} alone. The shared \texttt{{bibliography.bib}} holds {N_BIB} entries and this
document cites {len(spine)} of them. The remaining {n_unused} are used by the full draft and
biblatex keeps them out of this PDF's reference list. A number here is always that document's
number and never needs translating.""")
        opener = (rf"""This document lists every work that \texttt{{{stem}}} cites. It is ordered by the number the
work carries in that document's reference list, so entry \textbf{{[17]}} here is reference
\textbf{{[17]}} there and the two can be read side by side. """)

    regen = (rebuild_cmd().replace("_", r"\_").replace("&", r"\&")
             .replace("--", r"-{}-"))
    coverage = (f"{len(spine)} entries, every one of them cited in the thesis.\n"
                f"{levels['A']} at level~A, {levels['B']} at level~B, {levels['C']} at level~C, and\n"
                f"{len(unlocated)} with no located passage.\n")
    if SPINE_TAG != "draft":
        coverage = (f"{len(spine)} entries cited in this document, out of {N_BIB} in the shared "
                    f"bibliography.\n"
                    f"{levels['A']} at level~A, {levels['B']} at level~B, {levels['C']} at level~C, and\n"
                    f"{len(unlocated)} with no located passage.\n")
    extra = ""
    if multi():
        extra = "".join(
            f"\\texttt{{{tex_escape_plain(label)}}} cites {len(numbering.get(tag, {}))} of them. "
            if tag != SPINE_TAG else ""
            for _, tag, label in other_docs()
        )
        extra = extra.replace(". ", ".\n") if extra else extra
        # Keep the historical two-document sentence when the spine is the draft.
        if SPINE_TAG == "draft":
            extra = (f"""\\texttt{{Thesis\\_v5}} cites
{len(numbering.get('v5', {}))} of them and the plan {len(numbering.get('plan', {}))}.
""")

    return r"""
\section*{How to read this document}
\addcontentsline{toc}{section}{How to read this document}

""" + opener + scope + r"""

Each entry answers three questions in order. What is the source. Which sentences cite it, printed
as they stand in the thesis with the citation shown as \citemark{n}. And what the source itself
says, quoted with the page or clause it was read from. When the three agree, the citation is
sound. When the quoted passage does not carry the sentence above it, that is the defect this
document is built to expose.

\textbf{Checking one entry.} Read the citing sentence, then read the quotation under
\emph{Source says}. Ask only whether the second supports the first. The evidence level tells you
how far to trust the quotation without opening the paper yourself.

\begin{description}[leftmargin=2.4em,style=nextline,itemsep=1pt,topsep=2pt]
  \item[Level A] The source was opened and the supporting passage located. A page, clause or
        section is given. Nothing further is needed.
  \item[Level B] A publisher-deposited record, such as a Crossref abstract or an official
        landing page, carries the claim. The full text was not opened.
  \item[Level C] Bibliographic metadata is confirmed and the passage sits behind a paywall.
        Worth opening through the university proxy if the claim is load-bearing.
  \item[No level] The record is a literature-sweep note rather than a located passage, so it
        gives no page or clause. Part~3 lists these together and they are the ones to close
        first.
\end{description}

\textbf{Provenance.} Nothing in this document is typed by hand. References are printed by
biblatex from \texttt{bibliography.bib}. Printed citation numbers are read from the thesis's own
\texttt{.bbl}, which is what biber wrote, and the generator refuses to run when a
\texttt{.bbl} disagrees with its source. Citing sentences are copied from the \texttt{.tex}
sources with the generated measurement macros resolved, so a sentence quoting a measured value
shows the value. Evidence comes from \texttt{docs/Sources\_evidence.md}, with
\texttt{docs/LITERATURE\_NOTES.md} as the fallback, and the origin is named under each entry.
Regenerate with:

\begin{quote}\ttfamily\small
""" + regen + r"""
\end{quote}

\textbf{One note on punctuation.} The thesis style forbids em dashes and prose semicolons
anywhere a reader sees them, and this document follows that rule in its own prose. Quotations
from cited sources keep their original punctuation, because altering a quotation misquotes it.
Any dash or semicolon below therefore sits inside quoted source material and is deliberate.

\vspace{0.6em}
\textbf{Coverage.} """ + coverage + extra


RIGHT = ">{\\raggedleft\\arraybackslash}"
CENTRE = ">{\\centering\\arraybackslash}"


def part1(bib, records, spine, numbering, total_sites) -> str:
    # Columns are built rather than fixed, because the cross-document number columns only
    # exist when more than one document is in scope. The freed width goes to the key.
    cols = [(RIGHT + "p{7mm}", r"\textbf{\#}")]
    if multi():
        for _, tag, _ in other_docs():
            cols.append((RIGHT + "p{6mm}", r"\textbf{" + COL_HEADER[tag] + "}"))
    cols += [("p{%dmm}" % (44 if multi() else 50), r"\textbf{key}"),
             ("p{%dmm}" % (25 if multi() else 31), r"\textbf{source}"),
             ("p{20mm}", r"\textbf{kind}"),
             (RIGHT + "p{7mm}", r"\textbf{cit}"),
             (CENTRE + "p{6mm}", r"\textbf{ev}"),
             ("p{14mm}", r"\textbf{status}"),
             (CENTRE + "p{5mm}", "")]
    colspec = "@{}" + "".join(c for c, _ in cols) + "@{}"
    head = " & ".join(h for _, h in cols) + r" \\"

    rows = []
    for key in spine:
        rec = records.get(key)
        entry = bib[key]
        # A blank cell says "not cited by that document" and "no level assigned". A dash would
        # read as punctuation, and this repository reserves that mark for ranges and names.
        level = rec["level"] if rec and rec["level"] else ""
        cells = [str(numbering[SPINE_TAG][key])]
        if multi():
            for _, tag, _ in other_docs():
                n = numbering.get(tag, {}).get(key)
                cells.append(str(n) if n else "")
        cells += [
            "\\texttt{\\small " + tex_escape_plain(key) + "}",
            "{\\small " + checklist_label(key, entry) + "}",
            "{\\small " + source_kind(entry) + "}",
            str(total_sites[key]),
            level,
            "{\\small " + status_of(rec) + "}",
            "$\\blacksquare$" if key in REVIEWED_KEYS else "$\\square$",
        ]
        rows.append(" & ".join(cells) + r" \\")

    if multi() and SPINE_TAG == "draft":
        scope = (r"""\textbf{v5} and \textbf{pl} give
the number the same work carries in \texttt{Thesis\_v5} and in the plan, and a blank means that
document does not cite it. \textbf{cit} counts the places the work is cited across all three
documents.""")
    elif multi():
        bits = " and ".join(r"\textbf{" + COL_HEADER[tag] + "}" for _, tag, _ in other_docs())
        scope = (bits + r""" give
the number the same work carries in the other documents, and a blank means that
document does not cite it. \textbf{cit} counts the places the work is cited across all three
documents.""")
    else:
        scope = r"""\textbf{cit} counts the places the thesis cites it."""
    return (r"""
\clearpage
\section*{Part 1. Master checklist}
\addcontentsline{toc}{section}{Part 1. Master checklist}

One row per entry, ordered by the thesis's reference number. """ + scope + r"""
\textbf{ev} is the evidence level, blank where no passage was located, and
\textbf{status} reads \emph{ok} where the verdict is clean, \emph{note} where the record raises
something, and \emph{sweep} where the only record is a literature-sweep note. Tick the last
column as you check.

\begin{small}
\setlength{\tabcolsep}{3pt}
\begin{longtable}{""" + colspec + r"""}
\toprule
""" + head + r"""
\midrule
\endfirsthead
\toprule
""" + head + r"""
\midrule
\endhead
\bottomrule
\endfoot
""" + "\n".join(rows) + r"""
\end{longtable}
\end{small}
""")


def part2(bib, records, spine, numbering, per_key_sites) -> str:
    out = [r"""
\clearpage
\section*{Part 2. Entry records}
\addcontentsline{toc}{section}{Part 2. Entry records}

Entry \textbf{[n]} is reference \textbf{[n]} of the thesis. Citing sentences are printed as
they stand, with the citation shown as \citemark{n} and a cross-reference as \refmark{label},
each located by the chapter or section it sits in.
"""]
    for key in spine:
        entry = bib[key]
        rec = records.get(key)
        num = numbering[SPINE_TAG][key]
        also = []
        for _, tag, label in other_docs():
            if key in numbering.get(tag, {}):
                also.append(f"{tex_escape_plain(label)} [{numbering[tag][key]}]")
        badge = tex_escape_plain(source_kind(entry))
        if rec and rec["level"]:
            badge += f", level~{rec['level']}"
        elif not rec:
            badge += ", no evidence record"
        if also:
            badge += " \\textperiodcentered\\ " + ", ".join(also)

        out.append(f"\\auditentry{{{num}}}{{{tex_escape_plain(key)}}}{{{badge}}}")
        out.append(f"\\afield{{Reference}}{{\\fullcite{{{key}}}}}")

        ident = []
        fields = entry["fields"]
        if fields.get("doi"):
            doi = fields["doi"]
            ident.append(f"DOI \\href{{https://doi.org/{doi}}}{{\\texttt{{{tex_escape_plain(doi)}}}}}")
        elif fields.get("url"):
            ident.append(f"\\href{{{fields['url']}}}{{source page}}")
        if fields.get("note"):
            # A note field is already LaTeX, since biblatex prints it into the thesis
            # bibliography. Escaping it here would print its own markup.
            ident.append(fields["note"].rstrip("."))
        if ident:
            out.append(f"\\afield{{Entry}}{{{'. '.join(ident)}.}}")

        sites = per_key_sites.get(key, [])
        if sites:
            out.append(f"\\afield{{Cited in}}{{{len(sites)} "
                       f"{'place' if len(sites) == 1 else 'places'}.}}")
            for tag, label, site in sites:
                # With one document in scope its name on every line is noise, so the section
                # alone locates the sentence.
                where = (f"{tex_escape_plain(label)}, " if multi() else "") + \
                    tex_escape_plain(site["section"])
                if site["kind"] != "prose":
                    where += f", {site['kind']}"
                out.append(f"\\begin{{citedsentence}}\\textbf{{\\small {where}.}}\\enspace "
                           f"{sentence_to_tex(site['sentence'], numbering[tag])}"
                           f"\\end{{citedsentence}}")

        if rec:
            if rec["claim"]:
                out.append(f"\\afield{{Claim it carries}}{{{md_to_tex(rec['claim'])}}}")
            if rec["evidence"]:
                out.append("\\afield{Source says}{}")
                out.extend(render_evidence(rec["evidence"]))
            if rec["metadata"]:
                out.append(f"\\afield{{Metadata}}{{{md_to_tex(rec['metadata'])}}}")
            for label, value in rec["extra"]:
                out.append(f"\\afield{{{md_to_tex(label)}}}{{{md_to_tex(value)}}}")
            if rec["verdict"]:
                out.append(f"\\afield{{Verdict}}{{{md_to_tex(rec['verdict'])}}}")
            out.append(f"\\afield{{Record}}{{{tex_escape_plain(rec['origin'])}.}}")
        else:
            out.append(r"\afield{Source says}{No entry-by-entry evidence record exists for this "
                       r"entry. Metadata is verified in \texttt{docs/LITERATURE\_NOTES.md}. The "
                       r"supporting passage has not been located and quoted. Part~3 lists these "
                       r"together.}")
    return "\n".join(out)


def render_evidence(text: str) -> list:
    """Evidence as quote blocks, keeping any markdown bullet list as a list.

    Several records locate a claim per bullet, one page reference each. Flattening those into
    a paragraph runs the page numbers together and loses which quotation supports which claim.
    """
    out = []
    for block in (b for b in re.split(r"\n\s*\n", text) if b.strip()):
        lines = block.split("\n")
        lead, bullets, current = [], [], None
        for line in lines:
            m = re.match(r"\s*[-*]\s+(.*)", line)
            if m:
                if current is not None:
                    bullets.append(current)
                current = m.group(1)
            elif current is not None:
                current += " " + line.strip()
            else:
                lead.append(line.strip())
        if current is not None:
            bullets.append(current)

        if lead and any(lead):
            out.append(f"\\begin{{saidquote}}{md_to_tex(' '.join(lead))}\\end{{saidquote}}")
        if bullets:
            items = "\n".join(f"\\item {md_to_tex(b)}" for b in bullets)
            out.append("\\begin{saidquote}\\begin{itemize}"
                       "[leftmargin=1.2em,itemsep=1pt,topsep=1pt]\n"
                       + items + "\n\\end{itemize}\\end{saidquote}")
    return out


NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
                8: "eight", 9: "nine", 10: "ten"}

# Citations found sitting on a claim their source does not make, and what closed each one.
# Kept after the fix rather than deleted: the pattern is the reusable finding, and four of the
# six existed only in the compressed skeleton while the full draft had them right.
DEFECTS_CLOSED_ON = "31 August 2026"
ATTACHMENT_DEFECTS = [
    ("klabnik2023rust, jung2018rustbelt",
     "Chapter 1, on Rust promising performance competitive with C++",
     "RustBelt is a machine-checked safety proof and makes no performance claim. The type-system "
     "half of the sentence was carried by the book. Nothing in the pair supported the performance "
     "half. The same sentence was in the full draft, because this chapter was copied from it, and "
     "in the plan in a different wording.",
     "The pair now carries only the compile-time guarantee, phrased as enforced \\enquote{on "
     "machine-checked foundations}, and the performance clause carries "
     "\\texttt{balasubramanian2017rust}, which is the source the full draft already uses for that "
     "framing. The plan's sentence drops the performance claim, which its next paragraph states "
     "and cites on its own."),
    ("3gpp38913",
     "Chapter 1, on thousands of procedures per second at a budget of a few milliseconds",
     "TR 38.913 clause 7.4 sets a control-plane latency target. It states no procedure rate, so "
     "the citation covered the second half of a compound sentence only.",
     "The sentence now reads that each procedure has to complete inside the millisecond-scale "
     "budget the 5G system sets for control-plane signalling, which is what clause 7.4 gives. The "
     "rate stands as this study's own workload assumption, in the wording already used later in "
     "the same chapter."),
    ("natella2016fault",
     "Chapter 6, second use, on the seven boundary classes being chosen because safe Rust is "
     "expected not to prevent them",
     "Natella's survey of software fault injection is the right source for the method sentence in "
     "Chapter 4. It says nothing about the boundary of Rust's guarantee, and Chapter 3 already "
     "states the catalogue is this study's own. The full draft never had this one.",
     "The citation is dropped. The method sentence in Chapter 4 keeps it."),
    ("bornholt2021shardstore",
     "Chapter 6, on the boundary defects being re-imported against the checker's own primitives "
     "and shrunk to model size",
     "ShardStore is the peer-reviewed account of Loom and Shuttle and supports the division of "
     "labour between them, which is how the full draft uses it. The rewrite and the shrink are "
     "this study's own measured cost.",
     "The citation moves onto the division of labour, naming Loom and Shuttle as the full draft "
     "does, and the rewrite cost is left as the study's own finding."),
    ("evans2020rust",
     "Chapter 7, on confining unsafe to a seam crate making the reviewable surface a countable "
     "thing",
     "Evans et al.\\ report that fewer than 30 per cent of crates use unsafe directly and that "
     "more than half cannot be fully checked because of unsafe in the call chain. All five sites "
     "in the full draft cite that for dependency propagation. The countability of the surface is "
     "this thesis's own guideline.",
     "The citation moves onto the dependency-propagation clause, matching the full draft, and the "
     "countable surface follows as the guideline it is."),
    ("emberg2023asn1",
     "Chapter 7, on the parity suite bounding behaviour and not performance",
     "That limitation is this study's own, and both places the full draft states it carry no "
     "citation. Emberg and Wadsten compared matched C++ and Rust ASN.1 decompilers on "
     "performance.",
     "The citation is dropped. The entry's other use, on no earlier study isolating the language "
     "for a stateful concurrent subsystem, was sound and stands."),
]

BENIGN = [
    ("Crossref year against issue year", "Crossref dates the POPL 2018 and POPL 2020 issues a "
     "year early because the deposit precedes the issue. The entries follow what ACM prints."),
    ("Article-number page ranges", "\\texttt{66:1--66:34} against Crossref's \\texttt{1-34}, and "
     "eight more like it. ACM prints the article number and the entries follow ACM."),
    ("Author names that differ from the publisher record",
     "D'Oro, O'Keeffe, Tao Wei, Garc\\'ia S\\'anchez-Torija and di Luzio all differ between the "
     "publisher record and the paper's own title page. The entries follow the papers."),
    ("Semicolons in 3GPP titles", "\\texttt{NG-RAN; Architecture description} and four like it "
     "keep their semicolons, because the punctuation is part of the official title. Changing "
     "them would misquote the standard."),
    ("HTTP 403 and 202 on publisher links", "Bot blocking rather than dead links. Every one of "
     "those DOIs resolves through the Crossref API."),
]


def part3(bib, records, spine, numbering, unlocated, level_c) -> str:
    def keylist(keys):
        if not keys:
            return "None."
        items = []
        for k in sorted(keys, key=lambda k: numbering[SPINE_TAG][k]):
            marks = f"[{numbering[SPINE_TAG][k]}]"
            if SPINE_TAG == "draft" and k in numbering.get("v5", {}):
                marks += f", v5 [{numbering['v5'][k]}]"
            items.append(f"\\item \\texttt{{{tex_escape_plain(k)}}}\\hfill {marks}")
        return ("\\begin{itemize}[leftmargin=1.4em,itemsep=0pt,topsep=2pt]\n"
                + "\n".join(items) + "\n\\end{itemize}")

    defects = []
    for keys, where, why, fix in ATTACHMENT_DEFECTS:
        nums = []
        for k in [x.strip() for x in keys.split(",")]:
            if SPINE_TAG == "draft":
                if k in numbering.get("v5", {}):
                    nums.append(f"\\texttt{{{tex_escape_plain(k)}}}, \\texttt{{Thesis\\_v5}} "
                                f"[{numbering['v5'][k]}], thesis [{numbering['draft'][k]}]")
                else:
                    nums.append(f"\\texttt{{{tex_escape_plain(k)}}}, thesis [{numbering['draft'][k]}]")
            else:
                n = numbering.get(SPINE_TAG, {}).get(k)
                if n:
                    nums.append(f"\\texttt{{{tex_escape_plain(k)}}}, this document [{n}]")
                else:
                    nums.append(f"\\texttt{{{tex_escape_plain(k)}}}, not cited in this document")
        defects.append(f"\\item \\textbf{{{where}.}}\\par {'. '.join(nums)}.\\par {why}"
                       f"\\par\\textit{{Closed.}} {fix}")

    benign = "\n".join(f"\\item \\textbf{{{name}.}} {text}" for name, text in BENIGN)

    v5_unlocated = [k for k in unlocated if k in numbering.get("v5", {})]
    if not unlocated:
        unlocated_blurb = "None. This list is closed."
    elif SPINE_TAG == "draft":
        unlocated_blurb = (
            f'''These {len(unlocated)} entries carry a sweep note rather than a located passage, so no page or
clause is given and no evidence level is assigned. {len(v5_unlocated)} of them are cited by
\\texttt{{Thesis\\_v5}}.''')
    else:
        unlocated_blurb = (
            f'''These {len(unlocated)} entries carry a sweep note rather than a located passage, so no page or
clause is given and no evidence level is assigned.''')

    if SPINE_TAG == "draft" or "bugden2022rust" in numbering.get(SPINE_TAG, {}):
        preprint = r"""
\subsection*{The one preprint still load-bearing}

\texttt{bugden2022rust} is the last arXiv-only entry carrying weight. It is cited twice and both
times beside a peer-reviewed source. Replacing it with a peer-reviewed equivalent is optional.
"""
    else:
        preprint = r"""
\subsection*{The one preprint still load-bearing}

\texttt{bugden2022rust} is the last arXiv-only entry carrying weight in the full draft. This
document does not cite it.
"""
    return (r"""
\clearpage
\section*{Part 3. Findings and open items}
\addcontentsline{toc}{section}{Part 3. Findings and open items}

\subsection*{Citations that were attached to a claim the source does not make}

""" + f"""All {NUMBER_WORDS.get(len(ATTACHMENT_DEFECTS), len(ATTACHMENT_DEFECTS))} are closed as of
{DEFECTS_CLOSED_ON}, and they are kept
here because the pattern recurs. In every case the work itself was sound and cited correctly
elsewhere, so each was closed by moving or dropping the citation rather than by replacing the
source. No source was added that the bibliography did not already hold.

Four of the six existed only in \\texttt{{Thesis\\_v5}} and the full draft had them right, which
locates the cause: compressing a chapter into five paragraphs detaches a citation from the clause
it was attached to. The two that reached the full draft are both in Chapter~1, which
\\texttt{{Thesis\\_v5}} carries as a copy. So the rule for the next compression pass is to re-read
what each surviving citation now sits next to.""" + r"""

\begin{enumerate}[leftmargin=1.6em,itemsep=4pt]
""" + "\n".join(defects) + r"""
\end{enumerate}

\subsection*{Entries whose supporting passage was never located}

""" + unlocated_blurb + r"""

The list was six entries until 31 August 2026, all of them student theses or a paywalled paper, and
three of the defects above sat on three of those keys. Where nobody had written down what the
source says, the prose drifted. Closing it took one afternoon, because five of the six were openly
deposited with full PDFs. The correlation is the reason to keep this list at zero.

""" + ("" if not unlocated else keylist(unlocated)) + r"""

\subsection*{Level C, metadata confirmed and passage not opened}

""" + f"""These {len(level_c)} entries could not be closed without university access, and each is
used for a title-level claim or inside a list. Three have no abstract deposited anywhere, so there
is nothing short of the full text to read. Three have no DOI because the claim is a specification
clause or a book chapter rather than a finding, and in each of those the citation sits beside a
verified one that carries the same point.

""" + keylist(level_c) + preprint + r"""

\subsection*{Differences that look like defects and are not}

Recorded so no later pass \enquote{corrects} them.

\begin{itemize}[leftmargin=1.4em,itemsep=2pt]
""" + benign + r"""
\end{itemize}
""")


def part4(bib, records, spine, numbering, levels, total_sites, n_commands) -> str:
    kinds = Counter(source_kind(bib[k]) for k in spine)
    kind_rows = "\n".join(
        f"{name} & {n} & {100 * n / len(spine):.0f}\\,\\% \\\\" for name, n in kinds.most_common())
    peer = kinds["peer reviewed"]
    # A citation command can name several works, so the two counts differ and the difference
    # is the number of grouped citations.
    key_occurrences = sum(total_sites.values())
    unused = [k for k in bib if k not in numbering.get(SPINE_TAG, {})]
    if unused:
        cite_para = (
            f"The shared bibliography holds {N_BIB} entries. This document cites {len(spine)} of "
            f"them, so there is no citation without an entry. The remaining {len(unused)} stay out "
            f"of the printed list, which is what biblatex is meant to do on a shared "
            f"\\texttt{{.bib}}. The document carries {n_commands} citation commands naming "
            f"{key_occurrences} works between them, since one command often cites several.\n"
            f"{peer} of the cited entries ({100 * peer / len(spine):.0f}\\,\\%) are in "
            f"peer-reviewed venues.\n")
        unused_rows = "\n".join(
            "\\texttt{\\small " + tex_escape_plain(k) + "} & {\\small " +
            source_kind(bib[k]) + "} & {\\small " + checklist_label(k, bib[k]) + r"} \\"
            for k in unused)
        unused_block = r"""
\vspace{1em}
\subsection*{Not cited in this document}
The """ + str(len(unused)) + r""" keys below are in \texttt{bibliography.bib} and the full draft
cites every one of them. They do not appear in this document's reference list.

\begin{small}
\setlength{\tabcolsep}{4pt}
\begin{longtable}{@{}p{58mm}p{28mm}p{70mm}@{}}
\toprule
\textbf{key} & \textbf{kind} & \textbf{source} \\
\midrule
\endfirsthead
\toprule
\textbf{key} & \textbf{kind} & \textbf{source} \\
\midrule
\endhead
\bottomrule
\endfoot
""" + unused_rows + r"""
\end{longtable}
\end{small}
"""
    else:
        cite_para = (
            f"Every entry in the bibliography is cited, so there is no orphan and no citation "
            f"without an\nentry. The thesis carries {n_commands} citation commands naming "
            f"{key_occurrences} works between\nthem, since one command often cites several.\n"
            f"{peer} entries ({100 * peer / len(spine):.0f}\\,\\%) are in peer-reviewed venues.\n")
        unused_block = ""
    extra = ""
    if multi() and SPINE_TAG == "draft":
        extra = (f"""\\texttt{{Thesis\\_v5}} cites
{len(numbering.get('v5', {}))} of the {len(spine)} and the plan {len(numbering.get('plan', {}))}.
""")
    return (r"""
\clearpage
\section*{Part 4. Coverage}
\addcontentsline{toc}{section}{Part 4. Coverage}

\begin{tabular}{@{}lrr@{}}
\toprule
\textbf{Source kind} & \textbf{n} & \textbf{share} \\
\midrule
""" + kind_rows + r"""
\midrule
""" + f"""\\textbf{{total}} & \\textbf{{{len(spine)}}} & \\\\
\\bottomrule
\\end{{tabular}}

\\vspace{{1em}}

\\begin{{tabular}}{{@{{}}lr@{{}}}}
\\toprule
\\textbf{{Evidence}} & \\textbf{{n}} \\\\
\\midrule
Level A, passage located & {levels['A']} \\\\
Level B, deposited record carries it & {levels['B']} \\\\
Level C, metadata only & {levels['C']} \\\\
No located passage & {levels['none'] + levels['absent']} \\\\
\\midrule
\\textbf{{total}} & \\textbf{{{len(spine)}}} \\\\
\\bottomrule
\\end{{tabular}}

\\vspace{{1em}}

""" + cite_para + extra + unused_block)


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dump", choices=["records", "sites"], help="inspect parsed input")
    ap.add_argument("--allow-stale", action="store_true",
                    help="emit even when a .bbl disagrees with its source (numbers may be wrong)")
    ap.add_argument("--document", choices=[d[1] for d in DOCUMENTS], default="draft",
                    help="spine document whose printed numbers the audit uses "
                         "(default: draft, writes source_audit.tex)")
    ap.add_argument("--all-documents", action="store_true",
                    help="also cover the other thesis documents, with their own printed numbers")
    args = ap.parse_args()

    configure(args.document, args.all_documents)

    global N_BIB
    bib = parse_bib(read(BIB))
    bib_keys = list(bib)
    N_BIB = len(bib_keys)

    sites_by_doc, numbering, stale = {}, {}, []
    for tex_name, tag, label in ACTIVE:
        path = ROOT / tex_name
        sites = cite_sites(path)
        sites_by_doc[tag] = sites
        cited = {k for s in sites for k in s["keys"]}
        order = printed_numbers(Path(tex_name).stem)
        if not order:
            stale.append(f"{tex_name}: no .bbl found, build the document first")
            order = [k for s in sites for k in s["keys"]]
            order = list(dict.fromkeys(order))
        elif set(order) != cited:
            only_bbl = sorted(set(order) - cited)
            only_src = sorted(cited - set(order))
            stale.append(f"{tex_name}: .bbl disagrees with the source. "
                         f"in .bbl only {only_bbl}, in source only {only_src}")
        numbering[tag] = {k: i + 1 for i, k in enumerate(order)}
        missing = sorted(cited - set(bib_keys))
        if missing:
            stale.append(f"{tex_name}: cited keys absent from bibliography.bib: {missing}")

    if stale and not args.allow_stale:
        print("REFUSING to generate: printed numbers would be stale.", file=sys.stderr)
        for line in stale:
            print("  " + line, file=sys.stderr)
        print("\n  Rebuild the affected document, or pass --allow-stale to override.",
              file=sys.stderr)
        return 1
    for line in stale:
        print("WARNING: " + line, file=sys.stderr)

    records = build_records(bib)
    if SPINE_TAG == "draft":
        spine = sorted(bib_keys, key=lambda k: numbering["draft"].get(k, 10**6))
    else:
        spine = [k for k, _ in sorted(numbering[SPINE_TAG].items(), key=lambda kv: kv[1])]

    if args.dump == "records":
        origins = Counter(r["origin"] for r in records.values())
        for origin, n in origins.most_common():
            print(f"{n:4d}  {origin}")
        print(f"\n{len(records)} of {len(bib_keys)} keys have a record")
        for k in bib_keys:
            if k not in records:
                print(f"  no record: {k}")
        for k in bib_keys:
            r = records.get(k)
            if r and not r["evidence"]:
                print(f"  record without evidence text: {k}")
        return 0

    if args.dump == "sites":
        for tex_name, tag, label in ACTIVE:
            print(f"\n=== {tex_name}: {len(sites_by_doc[tag])} citation sites")
            for s in sites_by_doc[tag][:6]:
                print(f"  L{s['line']} {s['section']}: {s['sentence'][:150]}")
        return 0

    global REVIEWED_KEYS
    REVIEWED_KEYS = read_review_marks()

    OUT.write_text(build_document(bib, records, sites_by_doc, numbering, spine), encoding="utf-8")
    write_review_marks(REVIEWED_KEYS)
    n_rec = sum(1 for k in spine if k in records)
    scope = ", ".join(label for _, _, label in ACTIVE)
    n_unused = N_BIB - len(spine)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(spine)} entries, {n_rec} with an evidence record, "
          f"{sum(len(v) for v in sites_by_doc.values())} citation sites"
          + (f", {n_unused} in the shared bibliography but not cited here" if n_unused else ""))
    carried = len(REVIEWED_KEYS & set(spine))
    held = len(REVIEWED_KEYS) - carried
    print(f"review ticks: {carried} of {len(spine)} entries marked reviewed, carried over"
          + (f" ({held} held for keys not currently cited)" if held else ""))
    others = ", ".join(label for _, tag, label in other_docs())
    print(f"scope: {scope}"
          + ("" if multi() else f"  (pass --all-documents to add {others})"))
    print(f"prose style: {DASH_KEPT} dashes and {SEMI_KEPT} semicolons left standing inside "
          f"quoted source material, where rewriting them would misquote the source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
