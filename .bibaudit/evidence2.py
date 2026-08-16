#!/usr/bin/env python3
"""Page-located evidence for the numeric and verbatim claims in the thesis."""
import re
import sys
from pathlib import Path
from pypdf import PdfReader

SRC = Path("/tmp/srcs")
_cache = {}


def pages(name):
    if name not in _cache:
        r = PdfReader(SRC / name)
        out = []
        for p in r.pages:
            try:
                out.append(re.sub(r"[ \t]+", " ", p.extract_text() or ""))
            except Exception:
                out.append("")
        _cache[name] = out
    return _cache[name]


def q(name, pattern, label, ctx=260, maxhits=2):
    print(f"\n### {label}\n#   [{name}] /{pattern}/")
    try:
        pgs = pages(name)
    except Exception as e:
        print(f"  ERROR: {e}")
        return
    rx = re.compile(pattern, re.I | re.S)
    n = 0
    for i, text in enumerate(pgs, 1):
        for m in rx.finditer(text):
            s, e = max(0, m.start() - ctx), min(len(text), m.end() + ctx)
            print(f"  p.{i}: ...{text[s:e].strip()}...".replace("\n", " | "))
            n += 1
            if n >= maxhits:
                return
    if n == 0:
        print("  NO MATCH")


def front(name, chars=1100):
    print(f"\n### FRONT MATTER [{name}]")
    try:
        print("  " + pages(name)[0][:chars].replace("\n", " | "))
    except Exception as e:
        print(f"  ERROR: {e}")


QUERIES = [
    ("front", "thesis_karlback.pdf"),
    ("thesis_karlback.pdf", r"strengths of each language", "karlback: matched-implementation control (thesis quotes this verbatim)"),
    ("thesis_karlback.pdf", r"C\+\+ (is|remains|would be) (still )?the", "karlback: conclusion on C++"),
    ("thesis_karlback.pdf", r"latency", "karlback: latency results"),
    ("front", "thesis_arvidsson.pdf"),
    ("thesis_arvidsson.pdf", r"Boost\.?\s?Fiber", "arvidsson: Boost.Fibers result"),
    ("thesis_arvidsson.pdf", r"99th percentile|p99", "arvidsson: p99 divergence"),
    ("thesis_arvidsson.pdf", r"context switch", "arvidsson: stackless async/await attribution"),
    ("msrc2019.pdf", r"70%|~70", "msrc: 70% of CVEs are memory safety"),
    ("oa_emmerich2019drivers.pdf", r"63\s?%|63 percent", "emmerich: 63% more instructions"),
    ("oa_emmerich2019drivers.pdf", r"\b4\s?%", "emmerich: 4% slower than C"),
    ("oa_evans2020rust.pdf", r"call chain|transitively|propagat", "evans: unsafe propagation"),
    ("oa_xu2021rustcve.pdf", r"all memory-safety bugs require unsafe|require unsafe code", "xu: all memory-safety bugs involve unsafe"),
    ("oa_qin2020rust.pdf", r"blocking bug|double lock|unsafe code", "qin2020: unsafe use and blocking bugs"),
    ("oa_jung2018rustbelt.pdf", r"machine-checked|first formal", "rustbelt: machine-checked safety proof"),
    ("oa_jung2020stacked.pdf", r"operational semantics|aliasing discipline", "stacked borrows: aliasing semantics"),
    ("oa_jung2021safe.pdf", r"ownership|borrow", "jung2021: ownership and borrowing"),
    ("oa_georges2007rigorous.pdf", r"misleading|prevalent method|erroneous", "georges: single number misleads"),
    ("oa_szekeres2013sok.pdf", r"no (widely deployed )?(solution|defense)|deployed (defenses|mitigations)", "szekeres: mitigations remain partial"),
    ("oa_harris2023morello.pdf", r"bounds check(ing)? elision|removing bounds", "morello: bounds-check elision"),
    ("oa_skoudlil2025asyncrust.pdf", r"maximize throughput", "skoudlil: Tokio optimises throughput not determinism"),
    ("oa_skoudlil2025asyncrust.pdf", r"deadline", "skoudlil: deadline-meeting configuration"),
    ("oa_michaelides2026ranlatency.pdf", r"UE Context Setup", "michaelides: procedure measured"),
    ("oa_michaelides2026ranlatency.pdf", r"120\s?(µ|u|\\u00b5)?s|430", "michaelides: IPsec vs DTLS overhead numbers"),
    ("oa_michaelides2026ranlatency.pdf", r"1,?000 (times|repetitions)|1000 times", "michaelides: repetitions"),
    ("oa_mccormack2026unsafe.pdf", r"foreign function", "mccormack: unsafe at FFI boundaries"),
    ("oa_sharma2024embedded.pdf", r"interoperab|interoperation", "sharma: interop is the open problem"),
    ("oa_zhang2026deadlock_pre.pdf", r"deadlock detection|double lock", "zhang: static deadlock detection for Rust"),
    ("oa_zheng2024security.pdf", r"vulnerab", "zheng: ecosystem security risks"),
    ("oa_crichton2024learning.pdf", r"ownership", "crichton: ownership is where readers drop out"),
    ("oa_polese2023oran.pdf", r"disaggregat|multi-vendor", "polese: O-RAN disaggregation"),
    ("oa_li2014tales.pdf", r"tail latency|sources of", "li2014: sources of tail latency"),
    ("oa_enberg2019tpc.pdf", r"thread-per-core", "enberg: thread-per-core changes tail latency"),
    ("oa_watson2025_tr.pdf", r"standardi", "watson: standardisation argument"),
    ("oa_bugden2022rust.pdf", r"benchmark", "bugden: benchmark survey"),
    ("atc24_rustforlinux.pdf", r"C API|wrapper|abstraction layer|friction|compromise", "li2024: adoption friction"),
    ("oa_szekeres2013sok.pdf", r"memory corruption", "szekeres: memory corruption persistence"),
]

if __name__ == "__main__":
    for item in QUERIES:
        if item[0] == "front":
            front(item[1])
        else:
            q(*item)
