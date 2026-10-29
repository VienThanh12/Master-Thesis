#!/usr/bin/env python3
"""Flag prose words a CEFR B2 reader is unlikely to know.

Companion to .vocab.py, which checks a hand-written list of about sixty hard
words and so cannot report anything it was not told about. This one measures
every word in the document instead.

The proxy for CEFR level is corpus frequency. wordfreq gives a Zipf score, a
log scale where 7 is "the" and 1 is a word almost nobody meets. Vocabulary
research puts a B2 reader at roughly the commonest 4000 to 5000 word families,
which lands near Zipf 3.6, so the bands below are cut there. The mapping is
approximate and the script says so: it produces a list to read, not a verdict.

An inflected form is scored at its most common relative, because "widened" is
not a harder word than "widen".

Three exemptions keep the signal readable. Terms of art are the vocabulary the
thesis exists to use, so they are reported apart and the question for them is
whether first use glosses them. Acronyms are already gated by .acronyms.py.
Identifiers in \texttt are code, not prose.

    python3 .b2.py                              # the submission manuscript
    python3 .b2.py Ha_Vien_Mastersthesis_2026_draft.tex --band c1      # one band only
    python3 .b2.py --context                    # every line, not just four
"""
import re
import sys
from collections import defaultdict

try:
    from wordfreq import zipf_frequency
except ImportError:
    sys.exit("needs wordfreq:  pip install --user --break-system-packages wordfreq")

args = [a for a in sys.argv[1:] if not a.startswith("-")]
flags = [a for a in sys.argv[1:] if a.startswith("-")]
SRC = args[0] if args else "Ha_Vien_Mastersthesis_2026.tex"
BAND = next((a.split("=")[-1] for a in flags if a.startswith("--band")), None)
FULL = "--context" in flags

# Zipf cut points. Above B2_OK a B2 reader almost certainly knows the word.
B2_OK = 4.0      # roughly the commonest 2500 words
B2_EDGE = 3.6    # roughly 5000; the upper edge of B2
C1 = 3.0         # taught at C1, met in broadsheet prose
# below C1 is C2 or specialist

BANDS = [
    ("beyond C2", -1.0, 2.2, "a B2 reader will not know this and probably has to look it up"),
    ("C2", 2.2, C1, "a B2 reader will not reliably know this"),
    ("C1", C1, B2_EDGE, "a strong B2 reader may know this, a typical one will not"),
    ("B2 edge", B2_EDGE, B2_OK, "at the limit of B2, fine if the sentence around it is plain"),
]

# Vocabulary the thesis exists to use. Keep, but gloss on first use.
TERMS_OF_ART = {
    "disaggregated", "disaggregation", "latency", "percentile", "percentiles",
    "borrow", "checker", "ownership", "aliasing", "saturation", "saturated",
    "saturates", "saturating", "jitter", "bootstrap", "permutation",
    "nonparametric", "cyclomatic", "shard", "shards", "sharded", "sharding",
    "idiomatic", "idiom", "idioms", "arena", "arenas", "allocator",
    "allocators", "allocation", "allocations", "deallocation", "monomorphisation",
    "trait", "traits", "resident", "throughput", "concurrency", "concurrent",
    "mutex", "mutexes", "semaphore", "atomics", "atomicity", "sanitiser",
    "sanitisers", "sanitizer", "sanitizers", "instrumentation", "instrumented",
    "virtualised", "virtualisation", "hypervisor", "kernel", "compiler",
    "compilers", "compile", "compiled", "compilation", "runtime", "runtimes",
    "binary", "binaries", "linkage", "linker", "toolchain", "benchmark",
    "benchmarks", "benchmarking", "workload", "workloads", "scheduler",
    "scheduling", "thread", "threads", "threading", "deadlock", "deadlocks",
    "mutability", "mutable", "immutable", "borrowing", "borrowed", "lifetimes",
    "dereference", "dereferencing", "pointer", "pointers", "heap", "stack",
    "cache", "caches", "cached", "prefetch", "pipeline", "pipelined",
    "telecom", "telecommunications", "radio", "cellular", "handover",
    "handovers", "subscriber", "subscribers", "provisioning", "orchestration",
    "orchestrator", "containerised", "container", "containers", "hardware",
    "middleware", "codebase", "repository", "repositories", "commit", "commits",
    "quantile", "quantiles", "variance", "median", "medians", "confidence",
    "interval", "intervals", "statistically", "significance", "hypothesis",
    "hypotheses", "falsifiable", "falsifiability", "replicable",
    "reproducibility", "reproducible", "taxonomy", "taxonomies",
    "empirical", "empirically", "methodology", "methodological",
    "longitudinal", "correlational", "confound", "confounded", "confounder",
    "confounders", "confounding", "covariate", "heteroscedasticity",
}

FLOAT = r"(figure|table|tabular|lstlisting|verbatim|equation|align|tikzpicture)"
DROP_BEGIN = re.compile(r"\\begin\{" + FLOAT + r"\*?\}")
DROP_END = re.compile(r"\\end\{" + FLOAT + r"\*?\}")

# Suffix rules for finding a word's commonest relative. Order matters.
STRIP = [
    ("ies", "y"), ("ied", "y"), ("ier", "y"), ("iest", "y"), ("ily", "y"),
    ("ations", "ate"), ("ation", "ate"), ("ising", "ise"), ("izing", "ize"),
    ("ements", "e"), ("ement", "e"), ("ements", ""), ("ement", ""),
    ("ingly", ""), ("edly", ""), ("ness", ""), ("less", ""), ("ally", "al"),
    ("ing", ""), ("ing", "e"), ("ed", ""), ("ed", "e"), ("es", ""), ("s", ""),
    ("ly", ""), ("er", ""), ("est", ""), ("ity", "e"), ("ity", ""),
]


def stem_candidates(w):
    out = [w]
    for suf, rep in STRIP:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            out.append(w[: -len(suf)] + rep)
    return out


def level(w):
    """Zipf of the word's commonest morphological relative."""
    return max(zipf_frequency(c, "en") for c in stem_candidates(w))


def strip_latex(s):
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = re.sub(r"\\texttt\s*\{[^}]*\}", " CODE ", s)
    s = re.sub(r"\\(cite|citep|citet|ref|eqref|label|input|includegraphics|autoref)"
               r"\s*(\[[^\]]*\])?\{[^}]*\}", " X ", s)
    s = re.sub(r"\$[^$]*\$", " N ", s)
    s = re.sub(r"\\[a-zA-Z@]+\*?", " ", s)
    s = s.replace("{", "").replace("}", "").replace("~", " ")
    return re.sub(r"\s+", " ", s).strip()


text = open(SRC, encoding="utf-8").read()
lines = text.split("\n")
body = text.find(r"\chapter{Introduction}")
body_line = text[:body].count("\n") + 1 if body > 0 else 1
bib_line = next((i for i, l in enumerate(lines, 1)
                 if l.startswith((r"\bibliography", r"\printbibliography"))), len(lines))

# Acronyms are .acronyms.py's business, so drop anything with an internal capital.
seen = defaultdict(list)
depth = 0
nwords = 0
for i, raw in enumerate(lines, 1):
    if DROP_BEGIN.search(raw):
        depth += 1
    if DROP_END.search(raw):
        depth = max(0, depth - 1)
        continue
    if depth or not (body_line <= i < bib_line):
        continue
    if raw.strip().startswith("\\") or not raw.strip():
        continue
    clean = strip_latex(raw)
    for m in re.finditer(r"\b[A-Za-z][a-z'’-]{3,}\b", clean):
        w = m.group(0)
        nwords += 1
        low = w.lower().replace("’", "'")
        if "-" in low or "'" in low:
            continue
        if w[0].isupper() and not raw.lstrip().startswith(w):
            continue          # likely a proper noun mid-sentence
        seen[low].append(i)

terms, hard = {}, {}
for w, occ in seen.items():
    if w in TERMS_OF_ART:
        terms[w] = occ
        continue
    z = level(w)
    if z < B2_OK:
        hard[w] = (z, occ)


def line_of(n):
    return strip_latex(lines[n - 1]).strip()


print("=" * 78)
print(f"ABOVE-B2 VOCABULARY in {SRC}")
print(f"{nwords} prose words, {len(seen)} distinct, {len(hard)} below Zipf {B2_OK}")
print("Frequency is a proxy for CEFR level, so read the list, do not trust the band.")
print("=" * 78)

for name, lo, hi, note in BANDS:
    if BAND and BAND.lower() not in name.lower().replace(" ", ""):
        continue
    band = {w: v for w, v in hard.items() if lo <= v[0] < hi}
    if not band:
        continue
    n = sum(len(v[1]) for v in band.values())
    print(f"\n{'-' * 78}\n{name}: {len(band)} words, {n} uses")
    print(f"  {note}\n{'-' * 78}")
    for w, (z, occ) in sorted(band.items(), key=lambda kv: (kv[1][0], -len(kv[1][1]))):
        print(f"\n  {w}  (zipf {z:.2f}, {len(occ)}x)")
        for ln in (occ if FULL else occ[:4]):
            print(f"    L{ln}: {line_of(ln)[:110]}")
        if not FULL and len(occ) > 4:
            print(f"    ... and {len(occ) - 4} more")

print("\n" + "=" * 78)
print(f"TERMS OF ART: {len(terms)} in use. Keep them. Check first use glosses each.")
print("=" * 78)
print("  " + ", ".join(f"{w}({len(o)})" for w, o in
                       sorted(terms.items(), key=lambda kv: -len(kv[1]))))
