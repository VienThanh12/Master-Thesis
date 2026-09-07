#!/usr/bin/env python3
"""Delete relocated material from the short version's appendix.

Keeps the seven blocks that were appendices in the original document and
restores each to a top-level \\appendix chapter. Splits only at \\appendix and
\\section, so a surviving section keeps its own subsections.
"""
import re
import sys

PATH = "Ha_Vien_Mastersthesis_2026_short.tex"
KEEP = {
    "appendix:terms": "Key terms",
    "appendix:search": "Literature search protocol",
    "appendix:code": "Fault-injection example",
    "appendix:stats": "Statistical design: family membership and resolving power",
    "appendix:config": "Host and campaign configuration",
    "appendix:impl": "Implementation of the two cores",
    "appendix:guidelines": "Engineering guidelines for incremental adoption",
}

lines = open(PATH).read().split("\n")
start = next(i for i, l in enumerate(lines) if l.startswith("\\appendix{"))
heads = [i for i in range(start, len(lines)) if re.match(r"\\(appendix|section)[\{\[]", lines[i])]

segs = []
for n, i in enumerate(heads):
    end = heads[n + 1] if n + 1 < len(heads) else len(lines)
    head = "\n".join(lines[i : min(i + 3, end)])
    m = re.search(r"\\label\{([^}]+)\}", head)
    segs.append((m.group(1) if m else None, i, end))


def words(text):
    text = re.sub(r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}", "", text, flags=re.S)
    text = re.sub(r"\\[A-Za-z@]+\*?", "", text)
    text = re.sub(r"[{}$~&\\%]", " ", text)
    return len([w for w in text.split() if any(c.isalpha() for c in w)])


out = lines[:start]
dead_labels = set()
report = []
for lab, a, b in segs:
    block = lines[a:b]
    if lab in KEEP:
        # restore as a top-level appendix chapter with its original title
        block = [f"\\appendix{{{KEEP[lab]}\\label{{{lab}}}}}"] + block[1:]
        # a heading whose label sat on its own following line no longer needs it
        if block[1].strip() == f"\\label{{{lab}}}":
            del block[1]
        out += block
        report.append(("KEEP", lab, words("\n".join(block))))
    else:
        dead_labels |= set(re.findall(r"\\label\{([^}]+)\}", "\n".join(block)))
        report.append(("DROP", lab, words("\n".join(block))))

if "--apply" not in sys.argv:
    for kind, lab, w in report:
        print(f"  {kind}  {w:>6}w  {lab}")
    kept = sum(w for k, _, w in report if k == "KEEP")
    dropped = sum(w for k, _, w in report if k == "DROP")
    print(f"\nkeep {kept} words, drop {dropped} words, {len(dead_labels)} labels die")
    sys.exit(0)

open(PATH, "w").write("\n".join(out))
open("/tmp/dead_labels.txt", "w").write("\n".join(sorted(dead_labels)))
print(f"wrote {PATH}: {len(lines)} -> {len(out)} lines, {len(dead_labels)} labels removed")
