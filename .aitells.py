#!/usr/bin/env python3
"""Flag stylistic fingerprints of language-model prose.

Companion to .vocab.py, which looks for hard Latinate words. This one looks for
the patterns that make text read as machine-written even when every word is
plain: dash asides, antithesis frames, transition openers, promotional
adjectives, counting stubs, and uniform sentence length.

Nothing here is wrong on its own. Frequency is the signal, so the report is
counts with line numbers, not a list of errors.

The counting stub is the one check whose test is not the pattern it matches. A
sentence of `Three are results.` announces a list the next sentences then give,
so deleting it costs no claim, and that is what makes it scaffolding rather
than prose. Length cannot stand in for that test, because .readability.py asks
for short sentences and rewards them: `Both of these results are final.` is the
same width and states something. So the check asks for a count subject inside
four words, which is where the deletable ones sit, and it will still report a
few sentences that earn their place.

Two checks are house style rather than model tells, and they are the only place
where zero is the target. House style capitalises the first word after a colon
when that word begins a unit of its own, so both look for a lowercase word where
a capital belongs. One covers the run-in label, `\\textbf{H1:} for this workload`,
where the label sits outside the sentence's grammar and the sentence therefore
starts after the colon. The other covers a colon introducing a question,
`comparison itself: which defect classes`. Everything else after a colon stays
lowercase and neither check looks at it.

Three things to know if either fires. They run case-sensitively, unlike every
pattern above. The label check reads the raw line, because `strip_latex` removes
`\\textbf{...}` and takes the colon with it. And `when` and `where` are left out
of the question words on purpose, since `dominates user-visible behaviour: when
the system stalls` subordinates rather than asks. Display type is out of scope
for both, which `is_prose()` already delivers by dropping any line that starts
with a backslash, so captions and `\\paragraph` headings are never counted.

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
SKIP_ENV = re.compile(
    r"\\(begin|end)\{(lstlisting|tikzpicture|tabular|longtable|verbatim|figure|table)\}"
)


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

# Colon capitalisation, case-sensitive and checked against the stripped text.
# Only a question word counts, because only a question starts a unit of its own
# without a label in front of it. `when` and `where` are omitted deliberately:
# after a colon they usually subordinate rather than ask.
CASE_PATTERNS = {
    "lowercase question after a colon": r": (?:which|what|how|why|whether|who|whom)\b",
}

# The same rule over run-in labels, which has to read the raw line because
# strip_latex() deletes \textbf{...} and the colon inside it goes too.
RAW_PATTERNS = {
    "lowercase after a label colon": r"\\(?:textbf|textit|emph)\{[^}]*:\}\s+[a-z]",
}

# A count in the subject and a verb that only links it to a label. Anything
# longer than four words has usually acquired a predicate worth keeping, so the
# budget is what separates the shape from a legitimate short sentence.
STUB_SUBJECT = re.compile(
    r"^(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Both|Neither|Either|Several"
    r"|The (?:first|second|third|fourth|last|two|three|four))\b"
)
STUB_BUDGET = 4

hits = defaultdict(list)
for name in (*CASE_PATTERNS, *RAW_PATTERNS):
    hits[name]  # report the zero, so a clean run says so rather than staying silent
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
    for name, pat in CASE_PATTERNS.items():
        for m in re.finditer(pat, text):
            hits[name].append((i, text[max(0, m.start() - 60):m.end() + 20]))
    for name, pat in RAW_PATTERNS.items():
        for m in re.finditer(pat, raw):
            hits[name].append((i, raw[max(0, m.start() - 40):m.end() + 30]))
    sentences.append((i, text))

# Sentence-length spread. Human academic prose varies more than model prose.
# `line_at` maps a character offset in the joined prose back to the line it came
# from, which the stub check needs and the length statistics below do not. The
# separator takes the number of the line that follows it, so a sentence opening
# a line is attributed to that line and not to the one before it.
parts, line_at = [], []
for ln, text in sentences:
    if parts:
        parts.append(" ")
        line_at.append(ln)
    parts.append(text)
    line_at.extend([ln] * len(text))
joined = "".join(parts)
lengths = [len(s.split()) for s in re.split(r"(?<=[.!?]) +", joined) if len(s.split()) > 2]

# Runs here rather than in the line loop because a sentence can span lines. The
# decimal point in `p99.99` is not a sentence end, and splitting there
# manufactures a `Neither p99.` that matches the shape without being prose, so
# hide it first. The substitution is the same width, which keeps `line_at`
# aligned and lets the report quote the untouched text.
probe = re.sub(r"(?<=\d)\.(?=\d)", "_", joined)
for m in re.finditer(r"[^.!?]+[.!?]", probe):
    sent = joined[m.start():m.end()].strip()
    if len(sent.split()) <= STUB_BUDGET and STUB_SUBJECT.match(sent):
        hits["counting stub (a count and a label, no claim)"].append((line_at[m.start()], sent))
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
