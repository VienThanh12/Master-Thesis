#!/usr/bin/env python3
"""Measure the software-quality proxies the evaluation reports for the two cores.

Section 7.3 commits to reporting lines of code and cyclomatic complexity as
proxies alongside the performance and safety results. Both are produced here, by
one tool applied identically to both implementations, so the comparison is not
confounded by two languages' native tooling counting different things: `lizard`
parses C++ and Rust with the same complexity definition (one plus the number of
decision points in a function), which is what makes the numbers comparable at
all.

Only the two cores are measured. Benchmark drivers, test binaries, the
conformance runners, and the FFI seam are excluded, because the parity contract
constrains the cores alone and the drivers exist to be equal by construction.
The attribution probes of specification section 12 are excluded for the same
reason -- they are not compared configurations -- which takes a filter rather
than a file list, because their conditional blocks sit inside compared files.

Usage:
    python3 complexity.py [--outdir ../figures]
"""
from __future__ import annotations

import argparse
import os
import statistics

import lizard

CPP_FILES = [
    "cpp/include/uecm/bounded_queue.hpp",
    "cpp/include/uecm/config.hpp",
    "cpp/include/uecm/error.hpp",
    "cpp/include/uecm/hash.hpp",
    "cpp/include/uecm/message.hpp",
    "cpp/include/uecm/service.hpp",
    "cpp/include/uecm/shard_core.hpp",
    "cpp/include/uecm/types.hpp",
    "cpp/src/service.cpp",
    "cpp/src/shard_core.cpp",
]

RUST_FILES = [
    "rust/src/config.rs",
    "rust/src/error.rs",
    "rust/src/hash.rs",
    "rust/src/lib.rs",
    "rust/src/message.rs",
    "rust/src/service.rs",
    "rust/src/shard_core.rs",
    "rust/src/types.rs",
]


# The two attribution probes of specification section 12 -- the C++ open-addressed
# intra-shard map and the Rust mutex-and-condvar shard queue -- are switched on by a
# build flag, so their scaffolding lives inside files that are otherwise part of the
# compared core. Counting it would report neither configuration: not the one the
# campaign measures, and not the probe either. The rule below is purely syntactic, so
# that the numbers can be checked by eye against the source: a conditional directive
# naming a probe goes, the branch it selects goes, and the branch the compared build
# takes stays. Comments are left alone; a comment explaining a build option belongs to
# the compared source as much as to the probe.
PROBE_SYMBOLS = ("UECM_FLAT_MAP", "UECM_RING_QUEUE", 'feature = "mutex-queue"')


def mentions_probe(line):
    return any(sym in line for sym in PROBE_SYMBOLS)


def strip_probe_cpp(text):
    out, in_probe_branch, inside = [], False, False
    for line in text.splitlines(keepends=True):
        s = line.strip()
        if s.startswith("#ifdef") and mentions_probe(s):
            inside, in_probe_branch = True, True
            continue
        if inside and s.startswith("#else"):
            in_probe_branch = False
            continue
        if inside and s.startswith("#endif"):
            inside, in_probe_branch = False, False
            continue
        if in_probe_branch:
            continue
        out.append(line)
    return "".join(out)


def strip_probe_rust(text):
    out, drop_guarded_item = [], False
    for line in text.splitlines(keepends=True):
        s = line.strip()
        if s.startswith("#[cfg(") and mentions_probe(s):
            # `#[cfg(feature = "mutex-queue")]` guards the probe, so the attribute
            # and the item under it both go; `#[cfg(not(...))]` guards the compared
            # build, so only the attribute goes.
            drop_guarded_item = "not(" not in s
            continue
        if drop_guarded_item:
            if not s.endswith(";"):
                raise SystemExit(
                    "complexity.py: a probe #[cfg] now guards a multi-line item "
                    f"({s!r}); teach strip_probe_rust about it before trusting "
                    "the proxies")
            drop_guarded_item = False
            continue
        out.append(line)
    return "".join(out)


def compared_source(root, rel):
    """The file as the compared configuration sees it (probe scaffolding removed)."""
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        text = fh.read()
    strip = strip_probe_cpp if rel.endswith((".hpp", ".cpp")) else strip_probe_rust
    text = strip(text)
    leftover = [ln for ln in text.splitlines() if mentions_probe(ln)
                and (ln.strip().startswith("#[cfg(") or ln.strip().startswith("#if"))]
    if leftover:
        raise SystemExit(
            f"complexity.py: {rel} still contains probe conditionals after "
            f"filtering: {leftover}")
    return text


def measure(root, files):
    nloc = 0
    raw = 0
    functions = []
    for rel in files:
        source = compared_source(root, rel)
        raw += len(source.splitlines())
        analysis = lizard.analyze_file.analyze_source_code(rel, source)
        nloc += analysis.nloc
        functions.extend(analysis.function_list)
    ccns = [f.cyclomatic_complexity for f in functions]
    worst = max(functions, key=lambda f: f.cyclomatic_complexity)
    return {
        "files": len(files),
        "raw": raw,
        "nloc": nloc,
        "functions": len(functions),
        "ccn_total": sum(ccns),
        "ccn_mean": statistics.mean(ccns),
        "ccn_median": statistics.median(ccns),
        "ccn_max": worst.cyclomatic_complexity,
        # lizard qualifies C++ names with their namespace and class; the bare
        # function name is what the prose refers to, so both sides read alike.
        "ccn_max_name": worst.name.split("::")[-1],
    }


def tex_name(name):
    return "\\texttt{" + name.replace("_", "\\_") + "}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="../figures")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, ".."))
    outdir = args.outdir if os.path.isabs(args.outdir) else os.path.abspath(
        os.path.join(here, args.outdir))
    os.makedirs(outdir, exist_ok=True)

    cpp = measure(root, CPP_FILES)
    rust = measure(root, RUST_FILES)

    rows = [
        ("Files", f"{cpp['files']}", f"{rust['files']}"),
        ("Functions", f"{cpp['functions']}", f"{rust['functions']}"),
        ("Lines of code (blank and comment lines excluded)",
         f"{cpp['nloc']}", f"{rust['nloc']}"),
        ("Total cyclomatic complexity",
         f"{cpp['ccn_total']}", f"{rust['ccn_total']}"),
        ("Mean complexity per function",
         f"{cpp['ccn_mean']:.1f}", f"{rust['ccn_mean']:.1f}"),
        ("Median complexity per function",
         f"{cpp['ccn_median']:.0f}", f"{rust['ccn_median']:.0f}"),
        ("Most complex function",
         f"{cpp['ccn_max']} ({tex_name(cpp['ccn_max_name'])})",
         f"{rust['ccn_max']} ({tex_name(rust['ccn_max_name'])})"),
    ]
    tab = os.path.join(outdir, "tab_complexity.tex")
    with open(tab, "w") as f:
        f.write(" \\\\\n".join(f"{a} & {b} & {c}" for a, b, c in rows) + "\n")

    macros = {
        "CppFuncs": f"{cpp['functions']}",
        "RustFuncs": f"{rust['functions']}",
        # Raw lines including blanks and comments: the basis of Table tab:loc, which
        # is decomposed by concern by hand. Emitted so the prose and the table cannot
        # quote different totals, which they have twice.
        "CppRawLines": f"{cpp['raw']}",
        "RustRawLines": f"{rust['raw']}",
        "LocGap": f"{rust['raw'] - cpp['raw']}",
        "RawRise": f"{100.0 * (rust['raw'] / cpp['raw'] - 1):.0f}",
        "CppNloc": f"{cpp['nloc']}",
        "RustNloc": f"{rust['nloc']}",
        "CppCcnTotal": f"{cpp['ccn_total']}",
        "RustCcnTotal": f"{rust['ccn_total']}",
        "CppCcnMean": f"{cpp['ccn_mean']:.1f}",
        "RustCcnMean": f"{rust['ccn_mean']:.1f}",
        "CppCcnMax": f"{cpp['ccn_max']}",
        "RustCcnMax": f"{rust['ccn_max']}",
        "CppCcnMaxFn": tex_name(cpp["ccn_max_name"]),
        "RustCcnMaxFn": tex_name(rust["ccn_max_name"]),
        "CcnTotalDrop": f"{100.0 * (1 - rust['ccn_total'] / cpp['ccn_total']):.0f}",
        "NlocRise": f"{100.0 * (rust['nloc'] / cpp['nloc'] - 1):.0f}",
    }
    gen = os.path.join(outdir, "gen_complexity.tex")
    with open(gen, "w") as f:
        f.write("% Generated by bench/complexity.py -- do not edit by hand.\n")
        for k, v in macros.items():
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

    print(f"C++ : {cpp}")
    print(f"Rust: {rust}")
    for p in (tab, gen):
        print("wrote", os.path.relpath(p, here))


if __name__ == "__main__":
    main()
