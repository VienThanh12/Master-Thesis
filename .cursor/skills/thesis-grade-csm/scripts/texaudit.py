#!/usr/bin/env python3
"""Mechanical evidence for a CSM grading pass: build gates, cross-references, bibliography.

Covers the part of assessment areas 4 and 6 that a script can settle. What it cannot
settle, and what carries the grade, is whether the prose agrees with the tables.

    texaudit.py Ha_Vien_Mastersthesis_2026.tex
    texaudit.py Ha_Vien_Mastersthesis_2026.tex --macros figures/gen_macros.tex

Exit status is 1 when a hard gate fails (LaTeX error, undefined reference or citation,
multiply defined label, float too large, overfull box), 0 otherwise. Stdlib only.
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

FLOAT_PREFIXES = ("fig", "tab", "lst", "alg", "listing")
REF_CMDS = r"(?:auto|page|name|c|C|eq|v|V|full|Full)?ref"
SKIP_ENV = re.compile(r"\\(begin|end)\{(lstlisting|tikzpicture|tabular|verbatim|figure|table|minted)\*?\}")
# Files whose numbers are written by the refresh pipeline, so literals there are correct.
GENERATED = re.compile(r"(?:^|/)(?:gen_|tab_|fig_)|/figures/")
UNIT = r"(?:\\micro\\second|µs|ms|ns|MiB|GiB|KiB|kops/s|ops/s|pp\b|\\?%)"
LITERAL_UNIT = re.compile(r"(?<![\\{\w.])(\d[\d.,]*)\s*(?:\\[,;: ]|~|\s)*(" + UNIT + ")")
PLACEHOLDERS = {
    "empty \\censors": re.compile(r"\\censors\{\s*\}\{\s*\}\{\s*\}"),
    "TODO/FIXME/XXX": re.compile(r"(?:^|[^A-Za-z])(TODO|FIXME|XXX)(?![A-Za-z])"),
    "\\todo macro": re.compile(r"\\todo\b"),
    "template leftover": re.compile(r"(?i)lorem ipsum|dummy (?:text|title|abstract|content)|"
                                    r"\bTBD\b|PLACEHOLDER|insert [a-z ]+ here|"
                                    r"\bAuthor Name\b|title of (?:the|your) thesis"),
}


def unwrap(text):
    """LaTeX wraps log lines near 79 columns; rejoin so warnings can be matched whole."""
    out = []
    for line in text.split("\n"):
        if out and len(out[-1]) >= 79:
            out[-1] += line
        else:
            out.append(line)
    return out


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def artefact(stem, ext):
    """Locate a build artefact for <stem>.

    A repository may send latexmk's intermediates to a build/ directory (this one
    does, via .latexmkrc) or leave them beside the source. Prefer build/, so that
    a grading pass reads the current log rather than a stale root-level copy.
    """
    root, name = os.path.split(stem)
    in_build = os.path.join(root, "build", name + ext)
    return in_build if os.path.isfile(in_build) else stem + ext


def collect_sources(tex_path):
    """The main file plus everything it \\input or \\include, one level of recursion deep."""
    root = os.path.dirname(os.path.abspath(tex_path))
    seen, queue, sources = set(), [os.path.abspath(tex_path)], {}
    while queue:
        path = queue.pop()
        if path in seen or not os.path.isfile(path):
            continue
        seen.add(path)
        body = read(path)
        sources[path] = body
        for name in re.findall(r"\\(?:input|include)\{([^}]+)\}", body):
            cand = os.path.join(root, name if name.endswith(".tex") else name + ".tex")
            queue.append(os.path.abspath(cand))
    return sources


def prose_lines(sources):
    """Yield (path, lineno, text) for lines a reader sees as prose."""
    for path, body in sources.items():
        skip = False
        for i, raw in enumerate(body.split("\n"), 1):
            if SKIP_ENV.search(raw):
                skip = "begin" in raw
                continue
            s = raw.strip()
            if skip or not s or s.startswith("%") or s.startswith("\\"):
                continue
            yield path, i, raw


def audit_log(stem, tex_path, report):
    log_path = artefact(stem, ".log")
    if not os.path.isfile(log_path):
        report.note("build", f"no {os.path.basename(log_path)}; build before grading")
        return
    if os.path.getmtime(log_path) < os.path.getmtime(tex_path):
        report.note("build", "log is older than the source: this audit describes a stale build")

    lines = unwrap(read(log_path))
    joined = "\n".join(lines)

    errors = [l for l in lines if l.startswith("! ")]
    undef_ref = sorted(set(re.findall(r"Warning: Reference `([^']+)' on page", joined)))
    undef_cite = sorted(set(re.findall(r"Warning: Citation '([^']+)'", joined)))
    multi_label = sorted(set(re.findall(r"Warning: Label `([^']+)' multiply defined", joined)))
    floats = re.findall(r"Float too large for page by ([\d.]+)pt on input line (\d+)", joined)
    overfull = [l for l in lines if l.startswith(("Overfull \\hbox", "Overfull \\vbox"))]
    underfull = [l for l in lines if l.startswith(("Underfull \\hbox", "Underfull \\vbox"))]
    pages = re.search(r"Output written on \S+ \((\d+) pages", joined)

    report.gate("build", "no LaTeX errors", not errors, [l[:100] for l in errors[:5]])
    report.gate("build", "no undefined references", not undef_ref, undef_ref[:8])
    report.gate("build", "no undefined citations", not undef_cite, undef_cite[:8])
    report.gate("build", "no multiply defined labels", not multi_label, multi_label[:8])
    report.gate("build", "no float too large", not floats,
                [f"{pt}pt over on input line {ln}" for pt, ln in floats])
    report.gate("build", "no overfull boxes", not overfull, [l[:90] for l in overfull[:8]])
    report.note("build", f"{len(underfull)} underfull boxes (cosmetic; not a gate)")
    if pages:
        report.note("build", f"{pages.group(1)} pages")


def audit_refs(sources, report):
    labels, refs = {}, set()
    for path, body in sources.items():
        for i, raw in enumerate(body.split("\n"), 1):
            for name in re.findall(r"\\label\{([^}]+)\}", raw):
                labels.setdefault(name, (path, i))
            for group in re.findall(r"\\" + REF_CMDS + r"\*?\{([^}]+)\}", raw):
                refs.update(k.strip() for k in group.split(","))

    unused = sorted(set(labels) - refs)
    floats_unused = [l for l in unused if l.split(":")[0] in FLOAT_PREFIXES]
    other_unused = [l for l in unused if l not in floats_unused]

    report.note("crossrefs", f"{len(labels)} labels, {len(refs)} distinct targets referenced")
    report.gate("crossrefs", "every float label is referenced from the body", not floats_unused,
                [f"{l} ({os.path.basename(labels[l][0])}:{labels[l][1]})" for l in floats_unused],
                hard=False)
    if other_unused:
        report.note("crossrefs", f"{len(other_unused)} unreferenced non-float labels "
                                 f"(sectioning labels are often intentional): "
                                 f"{', '.join(other_unused[:6])}")


def parse_bib(path):
    entries = {}
    body = read(path)
    marks = [(m.start(), m.group(1).lower(), m.group(2).strip())
             for m in re.finditer(r"(?m)^@(\w+)\s*\{\s*([^,\s]+)\s*,", body)]
    for idx, (start, kind, key) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(body)
        entries[key] = (kind, body[start:end])
    return entries


def audit_bib(stem, sources, report):
    root = os.path.dirname(os.path.abspath(stem))
    names = set()
    for body in sources.values():
        names.update(re.findall(r"\\addbibresource\{([^}]+)\}", body))
        for group in re.findall(r"\\bibliography\{([^}]+)\}", body):
            names.update(n.strip() for n in group.split(","))
    paths = [p for p in (os.path.join(root, n if n.endswith(".bib") else n + ".bib")
                         for n in names) if os.path.isfile(p)]
    if not paths:
        report.note("bibliography", "no .bib file found")
        return

    entries = {}
    for p in paths:
        entries.update(parse_bib(p))

    cited = set()
    aux = artefact(stem, ".aux")
    if os.path.isfile(aux):
        aux_body = read(aux)
        cited.update(re.findall(r"\\abx@aux@cite\{\d*\}?\{([^}]+)\}", aux_body))
        cited.update(re.findall(r"\\citation\{([^}]+)\}", aux_body))
    if not cited:
        for body in sources.values():
            for group in re.findall(r"\\[Cc]ite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]+)\}", body):
                cited.update(k.strip() for k in group.split(","))
    cited.discard("*")

    kinds = Counter(kind for kind, _ in entries.values())
    peer = kinds["article"] + kinds["inproceedings"] + kinds["incollection"]
    preprints = sorted(k for k, (_, text) in entries.items()
                       if re.search(r"(?i)arxiv|preprint|eprint", text))
    uncited = sorted(set(entries) - cited)
    missing = sorted(cited - set(entries))

    report.note("bibliography", f"{len(entries)} entries, {len(cited)} cited; "
                                f"{peer} peer-reviewed venues "
                                f"({100 * peer / max(len(entries), 1):.0f}%)")
    report.note("bibliography", ", ".join(f"{k}: {v}" for k, v in kinds.most_common()))
    report.gate("bibliography", "no cited key missing from the bibliography", not missing,
                missing[:8])
    if len(uncited) > 10:
        # A skeleton document sharing the full draft's .bib will leave most entries uncited.
        report.note("bibliography", f"{len(uncited)} entries uncited in this document; expected "
                                    f"when the .bib is shared with a longer one")
    else:
        report.gate("bibliography", "no uncited entry", not uncited, uncited, hard=False)
    if preprints:
        report.note("bibliography", f"{len(preprints)} entries look like preprints; check whether "
                                    f"any carries a load-bearing claim: "
                                    f"{', '.join(preprints[:6])}")


def audit_placeholders(sources, report):
    found = defaultdict(list)
    for path, body in sources.items():
        for i, raw in enumerate(body.split("\n"), 1):
            if raw.strip().startswith("%"):
                continue
            for name, pattern in PLACEHOLDERS.items():
                if pattern.search(raw):
                    found[name].append(f"{os.path.basename(path)}:{i}")
    report.gate("finalisation", "no placeholders or open markers", not found,
                [f"{name}: {', '.join(hits[:4])}" for name, hits in found.items()], hard=False)


def audit_hardcoded(sources, macros_path, report):
    by_value = {}
    if macros_path and os.path.isfile(macros_path):
        for name, value in re.findall(r"\\(?:new|renew|provide)command\*?\{?\\(\w+)\}?\s*\{([^}]*)\}",
                                      read(macros_path)):
            num = re.fullmatch(r"\s*([\d]+(?:[.,]\d+)?)\s*", value)
            if num:
                by_value.setdefault(num.group(1), name)
        report.note("numbers", f"{len(by_value)} generated macros hold a bare numeric value")

    literal, shadowed = [], []
    for path, i, raw in prose_lines(sources):
        if GENERATED.search(path.replace(os.sep, "/")):
            continue
        where = f"{os.path.basename(path)}:{i}"
        for value, unit in LITERAL_UNIT.findall(raw):
            # A round integer is usually a confidence level or a design constant, not a
            # measurement; only decimals and three-digit values are worth a reviewer's time.
            distinctive = "." in value or len(value.replace(",", "")) >= 3
            if not distinctive:
                continue
            literal.append(f"{where}  {value} {unit}")
            if value in by_value:
                shadowed.append(f"{where}  {value} is available as \\{by_value[value]}")

    if shadowed:
        report.gate("numbers", "no measured value typed in prose that a macro already holds",
                    False, shadowed[:10], hard=False)
    if literal:
        report.note("numbers", f"{len(literal)} prose numbers carry a unit (heuristic; ranges and "
                               f"round figures are fine): " + "; ".join(literal[:6]))


class Report:
    def __init__(self):
        self.sections, self.failed_hard = defaultdict(list), []

    def gate(self, section, claim, ok, detail=(), hard=True):
        mark = "PASS" if ok else ("FAIL" if hard else "WARN")
        self.sections[section].append((mark, claim, list(detail)))
        if not ok and hard:
            self.failed_hard.append(claim)

    def note(self, section, text):
        self.sections[section].append(("note", text, []))

    def emit(self):
        for section, rows in self.sections.items():
            print("\n" + section.upper())
            print("-" * 78)
            for mark, text, detail in rows:
                print(f"  {'':>4} {text}" if mark == "note" else f"  {mark:>4} {text}")
                for d in detail:
                    print(f"         {d}")
        print("\n" + "=" * 78)
        if self.failed_hard:
            print("HARD GATES FAILED: " + "; ".join(self.failed_hard))
        else:
            print("HARD GATES PASSED. The prose-against-tables check is still yours to do.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tex")
    ap.add_argument("--macros", help="generated macro file, e.g. figures/gen_macros.tex")
    args = ap.parse_args()

    if not os.path.isfile(args.tex):
        sys.exit(f"texaudit: no such file: {args.tex}")

    stem = os.path.splitext(os.path.abspath(args.tex))[0]
    sources = collect_sources(args.tex)
    report = Report()

    print("=" * 78)
    print(f"CSM GRADING AUDIT: {os.path.basename(args.tex)} "
          f"({len(sources)} source file{'s' if len(sources) != 1 else ''})")
    print("=" * 78)

    audit_log(stem, args.tex, report)
    audit_refs(sources, report)
    audit_bib(stem, sources, report)
    audit_placeholders(sources, report)
    audit_hardcoded(sources, args.macros, report)
    report.emit()
    return 1 if report.failed_hard else 0


if __name__ == "__main__":
    sys.exit(main())
