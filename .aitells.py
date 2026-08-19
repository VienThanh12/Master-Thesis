#!/usr/bin/env python3
"""Flag stylistic fingerprints of language-model prose.

Companion to .vocab.py, which looks for hard Latinate words. This one looks for
the patterns that make text read as machine-written even when every word is
plain: dash asides, antithesis frames, transition openers, promotional
adjectives, and uniform sentence length.

Nothing here is wrong on its own. Frequency is the signal, so the report is
counts with line numbers, not a list of errors.

    ./.aitells.py Ha_Vien_Mastersthesis_2026.tex
"""
import re
import statistics
import sys
from collections import defaultdict

SRC = sys.argv[1] if len(sys.argv) > 1 else "Ha_Vien_Mastersthesis_2026.tex"
raw_lines = open(SRC, encoding="utf-8").read().split("\n")

# Chapter 1 onwards: the preamble is configuration, not prose.
body_start = next(
    (i for i, l in enumerate(raw_lines) if l.startswith(r"\chapter{Introduction}")), 0
)

# Environments whose contents are code, data, or drawing commands.
SKIP_ENV = re.compile(r"\\(begin|end)\{(lstlisting|tikzpicture|tabular|verbatim|figure|table)\}")


def is_prose(line):
    s = line.strip()
    return bool(s) and not s.startswith("%") and not s.startswith("\\")


def strip_latex(line):
    """Reduce a source line to the words a reader sees."""
    s = re.sub(r"\\(texttt|textbf|textit|emph|ref|cite\w*|label|SI|num)\{[^}]*\}", " ", line)
    s = re.sub(r"\$[^$]*\$", " NUM ", s)
    s = re.sub(r"\\[A-Za-z@]+\*?", " ", s)
    s = re.sub(r"[{}~&\\]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


PATTERNS = {
    "em/en dash aside in prose": r"(?<!\$)---?(?!\$)",
    "'not (only|just|merely) X but Y'": r"\bnot (only|just|merely|simply)\b[^.]{0,80}\bbut\b",
    "'X is not Y, it is Z'": r"\bis not\b[^.]{0,40},\s*(it|they)\s+(is|are)\b",
    "'rather than' antithesis": r"\brather than\b",
    "transition opener": r"(?m)(^|\.\s+)(Moreover|Furthermore|Additionally|Notably|Importantly|"
                         r"Crucially|Ultimately|Indeed|Overall|In essence|In summary|"
                         r"That said|Nevertheless|Nonetheless)\b",
    "hedge preamble": r"\b(it is worth noting|it is important to note|it should be noted|"
                      r"it is worth mentioning)\b",
    "promotional adjective": r"\b(seamless\w*|robust\w*|crucial\w*|pivotal|vital|paramount|"
                             r"cornerstone|comprehensive|holistic|intricate|nuanced|"
                             r"cutting-edge|state-of-the-art|powerful|significant leap)\b",
    "LLM signature verb/noun": r"\b(delve\w*|leverag\w+|underscor\w+|showcas\w+|harness\w+|"
                               r"navigat\w+|foster\w+|garner\w+|bolster\w+|streamlin\w+|"
                               r"empower\w+|unlock\w+|realm|landscape|tapestry|testament)\b",
    "'plays a role' / 'serves as'": r"\b(plays? an? [a-z]+ role|serves? as|stands? as)\b",
    "'the fact that'": r"\bthe fact that\b",
    "triadic anaphora (A, A, and A)": r"\b(\w+) \w+, \1 \w+, and \1 \b",
}

hits = defaultdict(list)
sentences = []
skip = False

for i, raw in enumerate(raw_lines[body_start:], body_start + 1):
    if SKIP_ENV.search(raw):
        skip = "begin" in raw
        continue
    if skip or not is_prose(raw):
        continue
    text = strip_latex(raw)
    if not text:
        continue
    for name, pat in PATTERNS.items():
        for _ in re.finditer(pat, text, re.I):
            hits[name].append((i, text[:110]))
    sentences.append(text)

# Sentence-length spread. Human academic prose varies more than model prose.
joined = " ".join(sentences)
lengths = [len(s.split()) for s in re.split(r"(?<=[.!?]) +", joined) if len(s.split()) > 2]
colons = joined.count(":")
semis = joined.count(";")
words = len(joined.split())

print("=" * 78)
print(f"LANGUAGE-MODEL STYLE FINGERPRINTS in {SRC}")
print(f"{words} words of prose, {len(lengths)} sentences")
print("=" * 78)

for name, occ in sorted(hits.items(), key=lambda kv: -len(kv[1])):
    per_10k = 10000 * len(occ) / max(words, 1)
    print(f"\n{name}: {len(occ)}x  ({per_10k:.1f} per 10k words)")
    for ln, txt in occ[:5]:
        print(f"    L{ln}: {txt}")
    if len(occ) > 5:
        print(f"    ... and {len(occ) - 5} more")

print("\n" + "=" * 78)
print("RHYTHM AND PUNCTUATION DENSITY")
print("=" * 78)
print(f"  sentence length: mean {statistics.mean(lengths):.1f} words, "
      f"stdev {statistics.stdev(lengths):.1f}, range {min(lengths)}-{max(lengths)}")
print(f"    (stdev below ~8 reads as machine-uniform; human academic prose is usually 10-16)")
print(f"  colons:     {colons} ({10000 * colons / words:.1f} per 10k words)")
print(f"  semicolons: {semis} ({10000 * semis / words:.1f} per 10k words)")
