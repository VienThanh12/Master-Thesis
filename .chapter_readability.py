#!/usr/bin/env python3
"""Write a per-chapter Flesch table as Markdown.

Same counters as .readability.py (naive vowel-group syllables, floats dropped).
Not part of the thesis build.

    python3 .chapter_readability.py Thesis_v3.tex
    python3 .chapter_readability.py Thesis_v3.tex -o docs/CHAPTER_READABILITY.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

FLOAT = r"(figure|table|tabular|lstlisting|verbatim|equation|align|tikzpicture|description|itemize|enumerate)"
DROP_BEGIN = re.compile(r"\\begin\{" + FLOAT + r"\*?\}")
DROP_END = re.compile(r"\\end\{" + FLOAT + r"\*?\}")
ABBREV = ["e.g.", "i.e.", "cf.", "et al.", "vs.", "approx.", "resp.", "Fig.", "Sec."]
VOWELS = "aeiouy"


def strip_latex(s: str) -> str:
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = re.sub(
        r"\\(cite|citep|citet|ref|eqref|label|input|includegraphics|autoref)"
        r"\s*(\[[^\]]*\])?\{[^}]*\}",
        " X ",
        s,
    )
    s = re.sub(r"\$[^$]*\$", " N ", s)
    s = re.sub(r"\\[a-zA-Z@]+\*?", " ", s)
    s = s.replace("{", "").replace("}", "").replace("~", " ")
    return re.sub(r"\s+", " ", s).strip()


def split_sentences(clean: str) -> list[tuple[str, int]]:
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


def syllables(word: str) -> int:
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


def clean_heading(inner: str) -> str:
    inner = re.sub(r"\\label\{[^}]*\}", "", inner)
    inner = re.sub(r"\\[a-zA-Z@]+\*?", " ", inner)
    return re.sub(r"\s+", " ", inner.replace("{", "").replace("}", "")).strip()


def collect_runs(text: str):
    lines = text.split("\n")
    body_start = text.find(r"\chapter{Introduction}")
    body_start_line = text[:body_start].count("\n") + 1 if body_start > 0 else 1
    bib_line = next(
        (i for i, l in enumerate(lines, 1) if l.startswith(r"\bibliography")),
        len(lines),
    )
    paras, buf, startln, depth = [], [], None, 0
    cur_chap = cur_sec = "(front matter)"
    chap_order = []
    for i, raw in enumerate(lines, 1):
        if not (body_start_line <= i < bib_line):
            continue
        if DROP_BEGIN.search(raw):
            depth += 1
        raw_nolabel = re.sub(r"\\label\{[^}]*\}", "", raw)
        hm = re.search(r"\\(chapter|section|subsection)\*?\{(.+?)\}", raw_nolabel)
        if hm and depth == 0:
            title = clean_heading(hm.group(2))
            if hm.group(1) == "chapter":
                cur_chap = cur_sec = title
                if title not in chap_order:
                    chap_order.append(title)
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

    runs = []
    for ln, chap, sec, p in paras:
        clean = strip_latex(p)
        sents = split_sentences(clean)
        if sents:
            runs.append((ln, chap, sec, [w for _, w in sents], sents))
    return chap_order, runs


def metrics(sents_all: list[int], words_all: list[str]) -> dict:
    syl = sum(syllables(w) for w in words_all)
    asl = statistics.mean(sents_all)
    asw = syl / len(words_all)
    poly = sum(1 for w in words_all if syllables(w) >= 3)
    fre = 206.835 - 1.015 * asl - 84.6 * asw
    fk = 0.39 * asl + 11.8 * asw - 15.59
    fog = 0.4 * (asl + 100 * poly / len(words_all))
    short = 100 * sum(1 for w in sents_all if w < 15) / len(sents_all)
    stdev = statistics.stdev(sents_all) if len(sents_all) > 1 else 0.0
    return {
        "n": len(sents_all),
        "words": len(words_all),
        "asl": asl,
        "asw": asw,
        "fre": fre,
        "fk": fk,
        "fog": fog,
        "poly": 100 * poly / len(words_all),
        "short": short,
        "stdev": stdev,
    }


def flesch_band(fre: float) -> str:
    if fre >= 80:
        return "easy (80+)"
    if fre >= 70:
        return "fairly easy"
    if fre >= 60:
        return "standard"
    if fre >= 50:
        return "fairly hard"
    if fre >= 30:
        return "difficult"
    return "very difficult"


def render(src: Path, chap_order, runs) -> str:
    by_chap = defaultdict(list)
    for run in runs:
        by_chap[run[1]].append(run)

    rows = []
    all_sents, all_words = [], []
    for i, chap in enumerate(chap_order, 1):
        sub = by_chap.get(chap, [])
        sents_all, words_all = [], []
        for *_, ls, sents in sub:
            sents_all.extend(ls)
            for s, _ in sents:
                words_all.extend(s.split())
        if not sents_all:
            continue
        m = metrics(sents_all, words_all)
        m["num"] = i
        m["title"] = chap
        rows.append(m)
        all_sents.extend(sents_all)
        all_words.extend(words_all)

    whole = metrics(all_sents, all_words) if all_sents else None
    today = dt.date.today().isoformat()

    lines = [
        f"# Chapter readability: `{src.name}`",
        "",
        f"Generated {today} by `.chapter_readability.py`. Same counters as `.readability.py`.",
        "Floats, tables, and lists are dropped. Syllables are vowel groups, so a few",
        "technical words are over-counted.",
        "",
        "Re-run:",
        "",
        "```bash",
        f"python3 .chapter_readability.py {src.name} -o docs/CHAPTER_READABILITY.md",
        "```",
        "",
        "## Whole document",
        "",
    ]
    if whole:
        lines += [
            f"- Sentences: {whole['n']}",
            f"- Words: {whole['words']}",
            f"- **Flesch Reading Ease: {whole['fre']:.1f}** ({flesch_band(whole['fre'])})",
            f"- Flesch-Kincaid grade: {whole['fk']:.1f}",
            f"- Gunning Fog: {whole['fog']:.1f}",
            f"- Mean sentence length: {whole['asl']:.1f} words (stdev {whole['stdev']:.1f})",
            f"- Mean syllables per word: {whole['asw']:.3f}",
            f"- Short sentences (<15 words): {whole['short']:.1f}%",
            f"- 3+ syllable words: {whole['poly']:.1f}%",
            "",
        ]

    lines += [
        "## Per chapter",
        "",
        "| # | Chapter | Flesch | Band | FK | Fog | Sent. | Words | ASL | ASW | Short | 3+ syl |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for m in rows:
        lines.append(
            f"| {m['num']} | {m['title']} | {m['fre']:.1f} | {flesch_band(m['fre'])} "
            f"| {m['fk']:.1f} | {m['fog']:.1f} | {m['n']} | {m['words']} "
            f"| {m['asl']:.1f} | {m['asw']:.3f} | {m['short']:.1f}% | {m['poly']:.1f}% |"
        )

    lines += [
        "",
        "## What the columns are",
        "",
        "- **Flesch** (Reading Ease): higher is easier. 80+ is the bar used for the",
        "  recent results, discussion, and conclusion pass on `Thesis_v3.tex`.",
        "- **FK**: Flesch-Kincaid grade level (US school grade). Lower is easier.",
        "- **Fog**: Gunning Fog index. Lower is easier.",
        "- **ASL**: average sentence length in words.",
        "- **ASW**: average syllables per word. This is what usually caps Flesch in",
        "  a CS thesis, not sentence length.",
        "- **Short**: share of sentences under 15 words. `.readability.py` asks for",
        "  25-35% as a recovery-point target. Higher than that is what Flesch 80 needs.",
        "",
        "Captions inside `figure`/`table` environments are not counted. Neither is the",
        "hypotheses `description` list in the discussion chapter.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("src", nargs="?", default="Thesis_v3.tex")
    p.add_argument("-o", "--output", default="docs/CHAPTER_READABILITY.md")
    p.add_argument("--stdout", action="store_true", help="print Markdown only, do not write a file")
    args = p.parse_args()
    src = Path(args.src)
    if not src.is_file():
        print(f"not found: {src}", file=sys.stderr)
        return 1
    chap_order, runs = collect_runs(src.read_text(encoding="utf-8"))
    md = render(src, chap_order, runs)
    if args.stdout:
        print(md)
        return 0
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
