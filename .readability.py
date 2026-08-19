#!/usr/bin/env python3
"""Readability diagnostic for the thesis LaTeX source.

Disposable helper, not part of the thesis build. Re-run after an editing pass to
see whether the numbers moved:  python3 .readability.py Ha_Vien_Mastersthesis_2026.tex

The metric that matters most is "recovery rate": the share of long sentences
followed by a short one. Comprehension depends on the reader getting a footing
after a dense clause, and that is what this document is short of.
"""
import re
import statistics
import sys
from collections import Counter, defaultdict

SRC = sys.argv[1] if len(sys.argv) > 1 else "Ha_Vien_Mastersthesis_2026.tex"
text = open(SRC, encoding="utf-8").read()
lines = text.split("\n")

FLOAT = r"(figure|table|tabular|lstlisting|verbatim|equation|align|tikzpicture|description|itemize|enumerate)"
DROP_BEGIN = re.compile(r"\\begin\{" + FLOAT + r"\*?\}")
DROP_END = re.compile(r"\\end\{" + FLOAT + r"\*?\}")
ABBREV = ["e.g.", "i.e.", "cf.", "et al.", "vs.", "approx.", "resp.", "Fig.", "Sec."]


def strip_latex(s):
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = re.sub(r"\\(cite|citep|citet|ref|eqref|label|input|includegraphics|autoref)"
               r"\s*(\[[^\]]*\])?\{[^}]*\}", " X ", s)
    s = re.sub(r"\$[^$]*\$", " N ", s)
    s = re.sub(r"\\[a-zA-Z@]+\*?", " ", s)
    s = s.replace("{", "").replace("}", "").replace("~", " ")
    return re.sub(r"\s+", " ", s).strip()


def split_sentences(clean):
    prot = clean
    for a in ABBREV:
        prot = prot.replace(a, a.replace(".", "\x00"))
    out = []
    for s in re.split(r"(?<=[.!?])\s+", prot):
        s = s.replace("\x00", ".").strip()
        if not s:
            continue
        wc = len(re.findall(r"[A-Za-z0-9\u00b5%+\-]+", s))
        if wc >= 3:
            out.append((s, wc))
    return out


# ---- collect prose paragraphs (line number, section, text), skipping floats ----
body_start = text.find(r"\chapter{Introduction}")
body_start_line = text[:body_start].count("\n") + 1 if body_start > 0 else 1
bib_line = next((i for i, l in enumerate(lines, 1) if l.startswith(r"\bibliography")), len(lines))

paras, buf, startln, depth = [], [], None, 0
cur_chap = cur_sec = "(front matter)"
for i, raw in enumerate(lines, 1):
    if not (body_start_line <= i < bib_line):
        continue
    if DROP_BEGIN.search(raw):
        depth += 1
    hm = re.search(r"\\(chapter|section|subsection)\*?\{(.+?)\}", raw)
    if hm and depth == 0:
        title = re.sub(r"\\label\{[^}]*\}|\\[a-zA-Z]+|[{}]", "", hm.group(2)).strip()
        if hm.group(1) == "chapter":
            cur_chap = cur_sec = title
        else:
            cur_sec = title
    if depth == 0 and raw.strip() and not raw.strip().startswith("\\"):
        if startln is None:
            startln = i
        buf.append(raw)
    else:
        if buf:
            paras.append((startln, cur_chap, cur_sec, " ".join(buf)))
            buf, startln = [], None
    if DROP_END.search(raw):
        depth = max(0, depth - 1)
if buf:
    paras.append((startln, cur_chap, cur_sec, " ".join(buf)))

runs = []       # (line, chap, sec, [sentence lengths], clean text)
for ln, chap, sec, p in paras:
    clean = strip_latex(p)
    sents = split_sentences(clean)
    if sents:
        runs.append((ln, chap, sec, [w for _, w in sents], clean, sents))

flat = [w for r in runs for w in r[3]]
n = len(flat)

VOWELS = "aeiouy"


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    cnt, prev = 0, False
    for ch in w:
        v = ch in VOWELS
        if v and not prev:
            cnt += 1
        prev = v
    if w.endswith("e") and cnt > 1:
        cnt -= 1
    return max(1, cnt)


all_words = [w for r in runs for s, _ in r[5] for w in s.split()]
syl = sum(syllables(w) for w in all_words)
asl = statistics.mean(flat)
asw = syl / len(all_words)
poly = sum(1 for w in all_words if syllables(w) >= 3)
fre = 206.835 - 1.015 * asl - 84.6 * asw
fk = 0.39 * asl + 11.8 * asw - 15.59
fog = 0.4 * (asl + 100 * poly / len(all_words))

srt = sorted(flat)
print("=" * 78)
print(f"{SRC}: {n} sentences, {sum(flat)} words, {len(runs)} prose paragraphs")
print("=" * 78)
print("\nSENTENCE LENGTH (words)")
print(f"  mean {asl:.1f}   median {srt[n//2]}   p90 {srt[int(.9*n)]}   "
      f"p99 {srt[int(.99*n)]}   max {srt[-1]}   stdev {statistics.stdev(flat):.1f}")
for thr in (30, 40, 50):
    c = sum(1 for w in flat if w > thr)
    print(f"  over {thr}w: {c:4d}  ({100*c/n:4.1f}%)")

print("\nREADABILITY  (lower Flesch = harder)")
print(f"  Flesch Reading Ease   {fre:6.1f}   30-50 'difficult', under 30 'very difficult'")
print(f"  Flesch-Kincaid grade  {fk:6.1f}")
print(f"  Gunning Fog           {fog:6.1f}")
print(f"  3+ syllable words     {100*poly/len(all_words):5.1f}%")

short = sum(1 for w in flat if w < 15)
print("\nPACING  <-- the load-bearing metric")
print(f"  short sentences (<15w)   {short:4d}  ({100*short/n:4.1f}%)   target 25-35%")
fs = ft = 0
for _, _, _, ls, _, _ in runs:
    for i, w in enumerate(ls[:-1]):
        if w > 35:
            ft += 1
            fs += ls[i + 1] < 15
print(f"  long (>35w) then short   {fs:4d}/{ft}  ({100*fs/max(1,ft):4.0f}%)   target 30-40%")
multi = [r for r in runs if len(r[3]) >= 3]
noshort = [r for r in multi if not any(w < 15 for w in r[3])]
print(f"  3+ sentence paragraphs with NO short sentence: "
      f"{len(noshort)}/{len(multi)}  ({100*len(noshort)/len(multi):.0f}%)")
worst = 0
for _, _, _, ls, _, _ in runs:
    cur = 0
    for w in ls:
        cur = cur + 1 if w > 30 else 0
        worst = max(worst, cur)
print(f"  longest unbroken run of >30w sentences: {worst}")

pw = sorted(sum(r[3]) for r in runs)
print("\nPARAGRAPH LENGTH (words)")
print(f"  mean {statistics.mean(pw):.0f}  median {pw[len(pw)//2]}  max {pw[-1]}"
      f"   over 150w: {sum(1 for x in pw if x>150)}   over 200w: {sum(1 for x in pw if x>200)}")

print("\nPER-CHAPTER")
bych = defaultdict(list)
for _, chap, _, ls, _, _ in runs:
    bych[chap].extend(ls)
for chap, ls in bych.items():
    s = sorted(ls)
    print(f"  {chap[:46]:48s} n={len(ls):4d} mean={statistics.mean(ls):5.1f} "
          f"p90={s[int(.9*len(s))]:3d} short={100*sum(1 for w in ls if w<15)/len(ls):4.1f}%")

prose = " ".join(r[4] for r in runs)
nw = len(prose.split())
print("\nSTYLE TICS (per 1000 words)")
for name, pat in [("rather than", r"\brather than\b"), ("not X but Y", r"\bnot\b[^.]{0,40}\bbut\b"),
                  ("semicolon", r";"), ("colon", r":"), ("which", r"\bwhich\b"),
                  ("passive is/are -ed", r"\b(is|are|was|were|been|being)\s+\w+ed\b"),
                  ("-tion nouns", r"\w{4,}tion\b")]:
    c = len(re.findall(pat, prose))
    print(f"  {name:22s} {c:5d}  ({1000*c/nw:5.1f}/1k)")

print("\n" + "=" * 78)
print("HARDEST PARAGRAPHS  (density x length; no-recovery-point penalised)")
print("=" * 78)
scored = []
for ln, chap, sec, ls, clean, _ in runs:
    if len(ls) < 2 or sum(ls) < 60:
        continue
    has_short = any(w < 15 for w in ls)
    scored.append((sum(ls) * statistics.mean(ls) / 100 * (1.0 if has_short else 1.6),
                   ln, sec, ls, has_short, clean))
for score, ln, sec, ls, has_short, clean in sorted(scored, reverse=True)[:12]:
    print(f"\n  line {ln:5d}  {sec[:54]}")
    print(f"    {len(ls)} sentences, {sum(ls)} words, mean {statistics.mean(ls):.0f}w, {ls}"
          f"{'' if has_short else '   <-- no short sentence'}")
    print(f"    \"{clean[:150]}...\"")
