#!/usr/bin/env python3
"""Find hard general-purpose words that have plain equivalents.

Two kinds of hard word need opposite treatment:
  REPLACE  - Latinate vocabulary carrying no technical content ("peripheral")
  KEEP     - domain terms of art that must stay precise ("disaggregated"),
             but which need a gloss on first use

This script only looks for the REPLACE kind. Terms of art are listed separately
at the bottom so their first-use gloss can be checked by hand.
"""
import re
import sys
from collections import defaultdict

SRC = sys.argv[1] if len(sys.argv) > 1 else "Ha_Vien_Mastersthesis_2026.tex"
lines = open(SRC, encoding="utf-8").read().split("\n")

# hard word -> plain equivalents
REPLACE = {
    "peripheral": "minor, side",
    "utilise": "use", "utilize": "use", "utilizing": "using", "utilising": "using",
    "commence": "begin", "ameliorate": "improve", "endeavour": "try",
    "elucidate": "explain", "facilitate": "help, allow",
    "necessitate": "require", "necessitates": "requires",
    "constitute": "be, form", "constitutes": "is, forms",
    "comprise": "consist of", "comprises": "consists of",
    "terminate": "end", "subsequent": "later, next", "subsequently": "later",
    "prior to": "before", "in order to": "to", "with respect to": "for, about",
    "in the event that": "if", "approximately": "about", "sufficient": "enough",
    "numerous": "many", "additional": "more, extra",
    "attributable to": "caused by", "consequently": "so",
    "nonetheless": "even so", "notwithstanding": "despite", "albeit": "though",
    "whereby": "by which", "thereby": "so", "hitherto": "until now",
    "aforementioned": "this, above", "canonical": "standard",
    "corroborated": "confirmed", "corroborates": "confirms",
    "afflict": "affect, hit", "afflicts": "affects", "afflicting": "affecting",
    "manifest": "show up, appear", "perturbed": "disturbed",
    "apportioned": "divided, assigned", "delimited": "bounded, marked out",
    "residual": "remaining", "ubiquitous": "widespread", "leverage": "use",
    "myriad": "many", "plethora": "many", "salient": "main, key",
    "orthogonal": "independent", "germane": "relevant",
    "concomitant": "accompanying", "requisite": "required",
    "efficacious": "effective", "obviate": "avoid, remove",
    "predicated on": "based on", "cognisant": "aware",
    "heterogeneous": "mixed, varied", "homogeneous": "uniform",
    "eschew": "avoid", "extant": "existing", "nascent": "early, new",
    "paucity": "shortage", "modality": "mode, method",
    "operationalisation": "how it is measured",
    "operationalised": "measured as",
    "instantiate": "create", "instantiated": "created",
    "enumerate": "list", "enumerated": "listed",
    "encompass": "cover, include", "encompasses": "covers",
    "delineate": "set out", "delineates": "sets out",
    "expound": "explain", "adjudicate": "decide", "promulgate": "publish",
    "juxtapose": "place side by side", "disparate": "different, unrelated",
    "veracity": "truth", "amenable": "open, suited",
    "tractable": "manageable", "intractable": "unmanageable",
    "vis-\\`a-vis": "compared with", "inter alia": "among others",
}

# Domain terms of art: KEEP, but each needs a gloss on first use.
TERMS_OF_ART = [
    "disaggregated", "disaggregation", "tail latency", "coordinated omission",
    "borrow checker", "ownership", "aliasing", "saturation", "jitter",
    "percentile", "bootstrap", "permutation test", "Holm", "nonparametric",
    "cyclomatic", "shard", "idiomatic", "zero-cost", "soft real-time",
    "monomorphisation", "trait object", "resident set size", "arena",
]

body_start = next((i for i, l in enumerate(lines) if l.startswith(r"\chapter{Introduction}")), 0)

hits = defaultdict(list)
for i, raw in enumerate(lines[body_start:], body_start + 1):
    if raw.strip().startswith("%"):
        continue
    low = raw.lower()
    for w in REPLACE:
        for m in re.finditer(r"\b" + re.escape(w) + r"\b", low):
            hits[w].append((i, raw.strip()))

total = sum(len(v) for v in hits.values())
print("=" * 78)
print(f"REPLACEABLE HARD WORDS in {SRC}: {total} occurrences, "
      f"{len(hits)} distinct")
print("=" * 78)
for w, occ in sorted(hits.items(), key=lambda kv: -len(kv[1])):
    print(f"\n{w!r} ({len(occ)}x)  ->  {REPLACE[w]}")
    for ln, txt in occ[:4]:
        snippet = txt[:120]
        print(f"    L{ln}: {snippet}")
    if len(occ) > 4:
        print(f"    ... and {len(occ)-4} more")

print("\n" + "=" * 78)
print("TERMS OF ART: keep these, but check each is glossed on first use")
print("=" * 78)
for t in TERMS_OF_ART:
    first = None
    n = 0
    for i, raw in enumerate(lines[body_start:], body_start + 1):
        if re.search(r"\b" + re.escape(t) + r"\b", raw, re.I):
            n += 1
            if first is None:
                first = (i, raw.strip())
    if first:
        print(f"\n{t!r}: {n}x, first at L{first[0]}")
        print(f"    {first[1][:150]}")
