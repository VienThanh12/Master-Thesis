#!/usr/bin/env python3
"""Remove parenthetical cross-references to deleted appendix material.

Only the shapes whose removal cannot change a sentence's grammar are handled:
a whole parenthetical holding nothing but dead references, and a dead
reference listed alongside live ones inside a parenthetical.
"""
import re
import sys

PATH = "Ha_Vien_Mastersthesis_2026_short.tex"
dead = set(open("/tmp/dead_labels.txt").read().split())
src = open(PATH).read()
before = src


def all_dead(body):
    refs = re.findall(r"\\(?:page)?ref\{([^}]+)\}", body)
    return refs and all(r in dead for r in refs)


# a parenthetical whose entire content is dead references, optionally with a
# leading label word and separators, e.g. "(Appendix~\ref{x})" or
# "(Appendix~\ref{x}, Appendix~\ref{y})"
def drop_paren(match):
    body = match.group(1)
    if not all_dead(body):
        return match.group(0)
    if re.fullmatch(r"(?:(?:Appendix|Appendices|Section|Sections|see\s+)?~?\s*"
                    r"\\(?:page)?ref\{[^}]+\}[,;]?\s*)+", body):
        return ""
    return match.group(0)


src = re.sub(r"\s*\(([^()]*?)\)", lambda m: drop_paren(m) or "", src)
# a dead reference sitting in a list with live ones: "(Appendix~\ref{a} and \ref{b})"
src = re.sub(r"(\([^()]*?)(?:,\s*|\s+and\s+)(?:Appendix|Section)~\\ref\{("
             + "|".join(re.escape(d) for d in dead) + r")\}", r"\1", src)
# tidy the space a removed parenthetical can leave before punctuation
src = re.sub(r" +([.,;:])", r"\1", src)
src = re.sub(r"[ \t]+\n", "\n", src)

remaining = sum(1 for m in re.finditer(r"\\(?:page)?ref\{([^}]+)\}", src) if m.group(1) in dead)
if "--apply" in sys.argv:
    open(PATH, "w").write(src)
    print(f"applied: {len(before)} -> {len(src)} chars, {remaining} dead refs left")
else:
    print(f"dry run: would remove {before.count('ref{') - src.count('ref{')} refs, "
          f"{remaining} dead refs would remain")
