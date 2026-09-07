#!/usr/bin/env python3
"""Point references at the surviving body section that now carries the material.

Each deleted appendix whose content is summarised by a body section is mapped
to that section, and the label word before the reference changes from Appendix
to Section. References with no surviving destination are left alone and listed
so they can be edited by hand.
"""
import re
import sys

PATH = "Ha_Vien_Mastersthesis_2026_short.tex"
MAP = {
    "appendix:background": "sec:bgbrief",
    "sec:predictability": "sec:bgbrief",
    "sec:cpplatency": "sec:bgbrief",
    "sec:interop": "sec:bgbrief",
    "appendix:rantail": "sec:uecm",
    "sec:defects": "sec:uecm",
    "appendix:methods": "sec:methodbrief",
    "sec:methodperf": "sec:methodbrief",
    "sec:methodfaults": "sec:methodbrief",
    "sec:methodffi": "sec:methodbrief",
    "sec:controls": "sec:controlsbrief",
    "sec:stats": "sec:statsbrief",
    "chapter:design": "sec:designbrief",
    "sec:concurrency": "sec:designbrief",
    "sec:impldetails": "sec:designbrief",
    "sec:tagged": "sec:designbrief",
    "sec:parity": "sec:designbrief",
    "sec:idioms": "sec:designbrief",
    "sec:fairness": "sec:designbrief",
    "sec:relatedwork": "sec:gap",
    "sec:threats": "sec:standing",
    "appendix:adoption": "sec:rqdiscussion",
}

src = open(PATH).read()
n = 0
for old, new in MAP.items():
    pat = re.compile(r"(Appendix|Appendices|Section|Chapter)(~?\s*)\\ref\{" + re.escape(old) + r"\}")

    def sub(m):
        global n
        n += 1
        return f"Section{m.group(2)}\\ref{{{new}}}"

    src = pat.sub(sub, src)
    # a bare \ref with no label word before it
    src, k = re.subn(r"\\ref\{" + re.escape(old) + r"\}", f"\\\\ref{{{new}}}", src)
    n += k

dead = set(open("/tmp/dead_labels.txt").read().split())
left = [m.group(1) for m in re.finditer(r"\\(?:page)?ref\{([^}]+)\}", src) if m.group(1) in dead]

if "--apply" in sys.argv:
    open(PATH, "w").write(src)
    print(f"retargeted {n} references, {len(left)} left for hand editing")
    import collections
    for lab, c in collections.Counter(left).most_common():
        print(f"  {c:>3}x  {lab}")
else:
    print(f"dry run: {n} references would be retargeted, {len(left)} would remain")
