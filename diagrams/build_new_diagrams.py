#!/usr/bin/env python3
"""Build the generated thesis diagrams.

Diagrams 20-31 were added to fill chapter gaps. 07 (FFI seam) and 17
(guarantee boundary) join them so their counts and timings come from the
same generated macros the prose cites, rather than from typed labels.

Each builder emits ``diagrams/NN_name.drawio`` (editable) and
``diagrams/NN_name.svg`` (what render.py turns into the included PDF).

Usage:  python3 diagrams/build_new_diagrams.py
"""

import os
import re
import sys

from dsl import (
    Diagram,
    AMBER, AMBER_CHIP, AMBER_DEEP, AMBER_EDGE, AMBER_FILL,
    BLUE, BLUE_CHIP, BLUE_DEEP, BLUE_EDGE, BLUE_FILL,
    BODY, FAINT, GREY_EDGE, GREY_FILL, MUTED, NAVY, WHITE,
    GREEN, GREEN_CHIP, GREEN_DEEP, GREEN_EDGE, GREEN_FILL,
    ORANGE, ORANGE_CHIP, ORANGE_DEEP, ORANGE_EDGE, ORANGE_FILL,
    RED, RED_CHIP, RED_DEEP, RED_EDGE, RED_FILL,
)

HERE = os.path.dirname(os.path.abspath(__file__))
FIGURES = os.path.join(HERE, os.pardir, "figures")
MACRO_FILES = ("gen_macros.tex", "gen_artefacts.tex", "gen_adoption.tex")


def load_macros():
    """Read the campaign numbers the analysis generates.

    The diagrams quote the same values the prose does, so they are taken from
    the generated macro files rather than typed in: a fresh campaign moves
    both. gen_artefacts.tex is read for the catalogue sizes, which the
    fault-injection runner counts and which a diagram must not state from
    memory.
    """
    values = {}
    for name in MACRO_FILES:
        with open(os.path.join(FIGURES, name), encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$", line)
                if m:
                    values[m.group(1)] = m.group(2)
    missing = {"NRepeats", "NLoadLevels", "NRuns", "MaxOfferedLoad", "NTests",
               "MinAttainableP", "CorrectedFloor", "FfiOpBoundPct",
               "BudgetCoreShareMax", "BudgetCoreShareRest", "BudgetCoreRatio",
               "BudgetCoreFaster", "FaultClassesPrevented",
               "FaultClassesBoundary", "FfiEntryPoints", "FfiUnsafeFns",
               "FfiOpNative", "FfiOpSeam", "CoreUnsafe", "ReprLoad",
               "TrackingLoadCpp", "TrackingLoadRust", "OverloadLoad",
               "OverloadThrCpp", "OverloadThrRust"} - values.keys()
    if missing:
        raise SystemExit(f"{' and '.join(MACRO_FILES)} are missing {sorted(missing)}")
    if "KneeGapLoad" not in values and "KneeSplitLoad" not in values:
        raise SystemExit(
            f"{' and '.join(MACRO_FILES)} have neither KneeGapLoad nor KneeSplitLoad"
        )
    return values


M = load_macros()

#: Exponents on a slide have no math mode to fall back on, and a caret is the
#: notation of a source file rather than of a thesis: the prose writes
#: $2^{\NRepeats}$, so the artwork writes the same characters.
SUPERSCRIPT = str.maketrans("0123456789",
                            "\u2070\u00b9\u00b2\u00b3\u2074"
                            "\u2075\u2076\u2077\u2078\u2079")


def wrap(text, width):
    """Greedy wrap to a character budget, so line breaks stay explicit."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if len(trial) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------------------
def benchmark_harness():
    d = Diagram(
        "20_benchmark_harness", 880, 505,
        "How a reported number is produced",
        "From the frozen specification to the macro the prose cites, with no "
        "hand-copied value anywhere on the path",
    )
    stages = [
        ("Frozen specification", [
            "spec/SPECIFICATION.md fixes",
            "the API, state machine, data",
            "structures, and concurrency",
            "model, before any code is",
            "written.",
        ]),
        ("Four build variants", [
            "Two languages crossed with",
            "two allocators. Matched",
            "optimisation levels. Both",
            "sides pin the same shard",
            "and intra-shard hashes.",
        ]),
        ("Deterministic driver", [
            "A fixed SplitMix64 draw",
            "order and a per-slot",
            "expected-state model, so",
            "both versions walk identical",
            "code paths.",
        ]),
        ("Service and capture", [
            "Eight shards, one owning",
            "thread each, 1024-slot",
            "queues. HDR histogram",
            "timed from the intended",
            "send time, not the actual.",
        ]),
    ]
    xs = [15, 231, 447, 663]
    for x, (title, body) in zip(xs, stages):
        d.card(x, 76, 200, 126, title, body, fill=BLUE_FILL, stroke=BLUE,
               sw=1.8, rx=10, body_size=11)
    for x in xs[:-1]:
        d.arrow(x + 202, 139, x + 214, 139)

    d.rect(15, 214, 848, 54, BLUE_CHIP, BLUE_EDGE, rx=8)
    d.text(31, 236, f"Repeated {M['NRepeats']} times, with the four variants "
                    f"interleaved inside each repeat", 12, BLUE_DEEP,
           weight=700)
    d.text(31, 255, f"{M['NLoadLevels']} offered-load levels up to "
                    f"{M['MaxOfferedLoad']} kops/s give {M['NRuns']} measured "
                    f"runs. Interleaving makes the interference common to a "
                    f"block, so it cancels.", 11, BODY)

    row = [
        (15, 196, "Raw measurement logs", [
            "bench/results/*.jsonl, with",
            "the environment record",
            "from capture_env.sh kept",
            "alongside each result set.",
        ]),
        (232, 222, "bench/plot_figures.py", [
            "Median with a bootstrap 95%",
            "confidence interval, an exact",
            "paired permutation test, and",
            "the Holm correction.",
        ]),
        (474, 178, "Generated artifacts", [
            "figures/*.pdf",
            "figures/tab_*.tex",
            "figures/gen_macros.tex",
        ]),
        (672, 186, "Thesis LaTeX source", [
            "The prose refers to",
            "the generated macros",
            "by name, so text and",
            "data cannot drift.",
        ]),
    ]
    for x, w, title, body in row:
        d.card(x, 284, w, 104, title, body, fill=WHITE, stroke=BLUE_EDGE,
               rx=8, body_size=11)
    for x, w, *_ in row[:-1]:
        d.arrow(x + w + 2, 336, x + w + 14, 336)

    d.rect(15, 404, 848, 56, GREEN_FILL, GREEN, rx=8, sw=1.8)
    d.text(31, 425, "Nothing in the evaluation is hand-copied", 12.5,
           GREEN_DEEP, weight=700)
    d.text(31, 444, "bench/refresh_thesis.sh reruns the analysis and rebuilds "
                    "the PDF, so a fresh campaign updates every figure, "
                    "table, and quoted number in one step.", 11, BODY)

    d.footer(["A third party can walk this path without proprietary code: "
              "the specification and the harness are themselves published "
              "artifacts."], y=486)
    return d


# --------------------------------------------------------------------------
def evidence_classes():
    d = Diagram(
        "21_evidence_classes", 880, 568,
        "Which conclusions the measurement host can carry",
        "A result is final if it is a property of the compilers and the "
        "source, and preliminary if it is a property of the machine",
    )
    d.panel(20, 76, 400, 300, "FINAL", GREEN_FILL, GREEN)
    d.text(220, 130, "Unchanged by the host it was measured on", 12.5,
           GREEN_DEEP, anchor="middle")
    final = [
        ("Transcript parity",
         "A conformance suite diffed line by line, not asserted."),
        ("Defect catalogue (RQ2)",
         "Whether a program compiles is a fact about the compiler."),
        ("Seam structure (RQ4)",
         "Entry points, unsafe sites, and lines: read off the code."),
        ("Size and complexity proxies",
         "Counted from the code rather than from a run."),
    ]
    y = 144
    for title, sub in final:
        d.card(38, y, 364, 48, title, [sub], fill=WHITE, stroke=GREEN_EDGE,
               rx=7, sw=1.5, title_size=12, body_size=10.5, pad=14, gap=17)
        y += 56

    d.panel(460, 76, 400, 300, "PRELIMINARY", AMBER_FILL, AMBER_EDGE,
            header_color=AMBER_DEEP)
    d.text(660, 130, "Carries a contribution from the hypervisor", 12.5,
           AMBER_DEEP, anchor="middle")
    prelim = [
        ("Tail latency, p99 and p99.9 (RQ1)",
         "Computed from exactly the operations a stall disturbs."),
        ("Onset of the overload cliff",
         "Where saturation begins depends on the scheduler."),
        ("CPU utilisation (RQ3)",
         "Reverses sign between allocators, reported as unresolved."),
        ("Peak resident set size (RQ3)",
         "A run-level statistic, so pairing rescues it."),
    ]
    y = 144
    for title, sub in prelim:
        d.card(478, y, 364, 48, title, [sub], fill=WHITE, stroke=AMBER_EDGE,
               rx=7, sw=1.5, title_size=12, body_size=10.5, pad=14, gap=17)
        y += 56

    d.divider(440, 68, 392)

    d.rect(20, 404, 840, 104, BLUE_FILL, BLUE, rx=9, sw=1.8)
    d.text(36, 427, "What the bare-metal protocol buys, and only this", 12.5,
           BLUE_DEEP, weight=700)
    cx = 36
    for label in ["Isolated cores (taskset)", "performance governor",
                  "Turbo and SMT disabled", "Hardware counters"]:
        w = 6.4 * len(label) + 24
        d.chip(cx, 440, w, 26, label, WHITE, BLUE_DEEP, size=11,
               stroke=BLUE_EDGE)
        cx += w + 12
    d.lines(36, 484, [
        "bench/TESTBED.md is scripted and published, and the analysis "
        "pipeline does not change: executing the protocol and",
        "rerunning the same scripts is the only step between the two columns.",
    ], 11, BODY, lh=16)

    d.footer(["Every row on which the two columns agree is a property of the "
              "source code. Every row on which they differ is a property of "
              "the machine."], y=540)
    return d


# --------------------------------------------------------------------------
def traceability_map():
    d = Diagram(
        "22_traceability_map", 880, 504,
        "From research question to verdict, grouped by hypothesis",
        "Grouping by hypothesis rather than by question number exposes two "
        "things a row-per-question table can only note in passing",
    )
    for x, w, label in [(22, 128, "QUESTION"), (158, 236, "OBJECTIVE"),
                        (406, 132, "HYPOTHESIS"), (550, 310, "EVIDENCE")]:
        d.text(x + w / 2, 90, label, 10.5, FAINT, weight=700, anchor="middle")

    lanes = [
        ("RQ1", "O1  Quantify the latency distributions to overload, and "
                "locate any divergence",
         "\u00a77.5.1 and \u00a77.5.2: equivalent at the median, "
         "unresolvable at the tail"),
        ("RQ3", "O3  Measure the resource cost of the safety model under "
                "matched conditions",
         "\u00a77.5.4: peak RSS reproduces, CPU does not"),
        ("RQ2", "O2  Determine which defect classes are prevented at compile "
                "time, and when the rest are caught",
         "\u00a77.5.5: five prevented, two compile and misbehave"),
        ("RQ4", "O4  Build and measure an incremental-adoption prototype at "
                "the language boundary",
         f"\u00a77.5.6: bounded at {M['FfiOpBoundPct']}% of the "
         f"operation"),
    ]
    y, lane_y = 102, []
    for rq, obj, ev in lanes:
        lane_y.append(y)
        d.chip(22, y, 128, 64, rq, BLUE_CHIP, BLUE_DEEP, size=15, weight=700,
               rx=7)
        d.card(158, y, 236, 64, None, wrap(obj, 32), fill=WHITE,
               stroke=BLUE_EDGE, rx=7, body_size=10.5, body_color=BODY,
               pad=11, lh=13.5)
        d.card(550, y, 310, 64, None, wrap(ev, 46), fill=GREY_FILL,
               stroke=GREY_EDGE, rx=7, body_size=10.5, body_color=BODY,
               pad=11, lh=13.5)
        d.arrow(396, y + 32, 404, y + 32, color=BLUE_EDGE, sw=1.5)
        d.arrow(540, y + 32, 548, y + 32, color=BLUE_EDGE, sw=1.5)
        y += 76

    d.card(406, lane_y[0], 132, 140, "H1", [
        "Performance-",
        "equivalent below",
        "saturation, with",
        "any difference",
        "confined to the",
        "far tail.",
    ], fill=AMBER_CHIP, stroke=AMBER_EDGE, rx=8, sw=1.6, title_size=14,
        title_color=AMBER_DEEP, body_size=10.5, body_color=BODY, pad=12,
        lh=13.5, gap=20)
    d.card(406, lane_y[2], 132, 64, "H2", [
        "Safe Rust prevents",
        "what C++ leaves",
        "to testing.",
    ], fill=GREEN_CHIP, stroke=GREEN_EDGE, rx=8, sw=1.6, title_size=13,
        title_color=GREEN_DEEP, body_size=10, body_color=BODY, pad=11,
        lh=12.5, gap=17)
    d.card(406, lane_y[3], 132, 64, "H3", [
        "Interop cost is",
        "negligible against",
        "the work invoked.",
    ], fill=BLUE_CHIP, stroke=BLUE_EDGE, rx=8, sw=1.6, title_size=13,
        title_color=BLUE_DEEP, body_size=10, body_color=BODY, pad=11,
        lh=12.5, gap=17)

    d.rect(22, 410, 838, 46, GREEN_FILL, GREEN, rx=8, sw=1.6)
    d.text(38, 432, "O5  Artifacts and guidance", 12, GREEN_DEEP, weight=700)
    d.text(220, 432, "cross-cutting: discharged by the published artifacts "
                     "and the guidelines, not by any single question.",
           11, BODY)

    d.footer([
        "H1 does double duty for RQ1 and RQ3, so a single wording had to "
        "cover equivalence in both its latency and its resource sense",
        "Chapter 8 finds that to be its main weakness.",
    ], y=474)
    return d


# --------------------------------------------------------------------------
def stats_pipeline():
    d = Diagram(
        "23_stats_pipeline", 880, 566,
        "From runs to a defensible comparison",
        "Two decisions about how the family of tests is read are taken here, "
        "before the results, because either could otherwise be fitted to them",
    )
    steps = [
        ("1.  Measure in interleaved blocks", [
            f"{M['NRepeats']} repeats, with the four variants run back to "
            f"back inside",
            "each, so the interference common to a block is shared rather",
            "than assigned to one variant.",
        ]),
        ("2.  Summarise without assuming a shape", [
            "Median with a nonparametric bootstrap 95% interval, reported",
            "in full rather than as a half-width: latency is skewed, and a",
            "symmetric width covering the upper bound would fall below zero.",
        ]),
        ("3.  Test the comparison, not the overlap", [
            "An exact two-sided paired permutation test on the repeat-wise",
            f"differences, with the allocator held fixed. All "
            f"2{M['NRepeats'].translate(SUPERSCRIPT)} sign",
            "assignments are enumerated, so the p-value is exact.",
        ]),
        ("4.  Correct the family", [
            f"Holm step-down across the {M['NTests']} comparisons, "
            f"controlling the",
            "family-wise error rate without assuming the tests independent.",
        ]),
    ]
    y = 84
    for i, (title, body) in enumerate(steps):
        h = 38 + 15 * len(body)
        d.card(20, y, 530, h, title, body, fill=BLUE_FILL, stroke=BLUE, rx=9,
               sw=1.7, body_size=10.5, pad=16, lh=15, gap=21)
        if i < len(steps) - 1:
            d.arrow(285, y + h + 1, 285, y + h + 13)
        y += h + 15

    d.card(20, y, 530, 52, "Resolving power, quoted rather than left implicit",
           [f"An exact test on {M['NRepeats']} pairs floors at p = "
            f"{M['MinAttainableP']}, and at {M['CorrectedFloor']} after "
            f"correction."], fill=GREY_FILL, stroke=GREY_EDGE, rx=8,
           sw=1.5, title_size=11.5, body_size=10.5, pad=15, gap=19)

    pre = [
        ("Which comparisons enter the family", [
            "Achieved throughput is excluded. Below",
            "saturation it is pinned to the offered load",
            "by construction, so it cannot express a",
            "language effect whatever the languages do.",
            "Holm also divides its budget across the",
            "whole family, so two comparisons that",
            "resolve nothing would make the correction",
            "harsher on the ones that can.",
        ]),
        ("Which instrument to believe", [
            "When the interval and the p-value disagree,",
            "which at these repeat counts they routinely",
            "will, the answer turns on whether pairing",
            "cancels the interference that metric is",
            "exposed to. A run-level summary or a central",
            "order statistic is unmoved by a handful of",
            "descheduled operations, so a consistent",
            "paired difference is real. A high percentile",
            "is computed from precisely those operations,",
            "so an interval excluding zero is not read as",
            "a finding however far from zero it sits.",
        ]),
    ]
    d.text(714, 76, "PRE-COMMITTED", 10.5, AMBER_DEEP, weight=700,
           anchor="middle")
    py = 86
    for title, body in pre:
        h = 42 + 14 * len(body)
        d.card(568, py, 292, h, title, body, fill=AMBER_FILL,
               stroke=AMBER_EDGE, rx=9, sw=1.7, title_color=AMBER_DEEP,
               body_size=10.5, pad=15, lh=14, gap=20)
        py += h + 14

    d.footer([
        "Applying the second rule to the block that suits the argument and "
        "quietly dropping it for the other",
        "is the specific failure the pre-commitment exists to prevent.",
    ], y=532)
    return d


# --------------------------------------------------------------------------
def repro_artifacts():
    d = Diagram(
        "24_repro_artifacts", 880, 500,
        "What is published, and what it regenerates",
        "The study is built so that a third party can reproduce it without "
        "access to any proprietary code",
    )
    d.panel(20, 78, 262, 312, "PUBLISHED", BLUE_FILL, BLUE)
    y = 122
    for name, sub in [
        ("spec/", "The frozen specification and the conformance suite"),
        ("cpp/   rust/", "The parity-tested pair of implementations"),
        ("bench/", "Harness, campaign scripts, and the testbed protocol"),
        ("faults/", "The seven-program defect catalogue and its runner"),
        ("ffi/", "The C-ABI seam and its C++ host prototype"),
    ]:
        d.card(38, y, 226, 48, name, wrap(sub, 38), fill=WHITE,
               stroke=BLUE_EDGE, rx=6, title_size=11, body_size=9.5,
               pad=10, gap=14, lh=12)
        y += 52

    d.panel(306, 78, 250, 312, "ONE COMMAND", GREEN_FILL, GREEN)
    d.chip(324, 128, 214, 30, "bench/refresh_thesis.sh", GREEN_CHIP,
           GREEN_DEEP, size=12, weight=700, rx=6)
    d.lines(324, 182, [
        "Reruns the analysis over the raw",
        "logs and rebuilds the PDF, then",
        "fails loudly if LaTeX reports an",
        "error or an unresolved reference.",
    ], 10.5, BODY, lh=14)
    d.arrow(430, 246, 430, 262, color=GREEN)
    d.card(324, 268, 214, 92, "It calls", [
        "plot_figures.py: figures,",
        "tables, and gen_macros.tex",
        "complexity.py: size and",
        "cyclomatic-complexity proxies",
    ], fill=WHITE, stroke=GREEN_EDGE, rx=6, title_size=11.5, body_size=10,
        pad=12, gap=16, lh=13.5)

    d.panel(580, 78, 280, 312, "REGENERATED VERBATIM", AMBER_FILL, AMBER_EDGE,
            header_color=AMBER_DEEP, header_size=13)
    d.lines(598, 130, [
        "Every figure, table, and quoted number",
        "in the evaluation, straight from the logs.",
    ], 10.5, BODY, lh=14)
    oy = 166
    for out in ["figures/*.pdf", "figures/tab_*.tex",
                "figures/gen_macros.tex"]:
        d.chip(598, oy, 244, 26, out, WHITE, AMBER_DEEP, size=11, rx=5,
               stroke=AMBER_EDGE)
        oy += 32
    d.lines(598, 288, [
        "The environment record (CPU model,",
        "kernel, and toolchain versions) is",
        "captured by capture_env.sh and stored",
        "with each result set, so the conditions of",
        "a measurement travel with its data.",
    ], 10.5, MUTED, lh=14)

    d.rect(20, 406, 840, 56, RED_FILL, RED, rx=8, sw=1.7)
    d.text(36, 428, "Not required:", 11.5, RED_DEEP, weight=700)
    d.text(126, 428, "no proprietary source. The implementations are driven "
                     "entirely by the public specification. The", 10.5,
           BODY)
    d.text(36, 447, "service is a 3GPP-shaped model, not a reduced product "
                    "module.", 10.5, BODY)
    d.footer([
        "Separating environment-sensitive results from "
        "environment-insensitive ones is what lets the thesis",
        "label the first preliminary and the second final without ambiguity.",
    ], y=478)
    return d


# --------------------------------------------------------------------------
def threats_validity():
    bands = [
        ("INTERNAL", "Is the language really the only difference?", BLUE, [
            ("Implementation bias between the two versions",
             "Frozen specification, shared allocator and optimisation level, "
             "pinned hash functions, forced-idiom log, transcript parity",
             "Single-author skill asymmetry. Parity bounds behaviour, not "
             "performance", "none"),
        ]),
        ("CONSTRUCT", "Do the metrics measure what the questions ask?",
         ORANGE_DEEP, [
            ("The sweep measures the design, not the language",
             "The operation is measured apart from the handoff and both are "
             "reported",
             "One operation on one data structure is narrower than the sweep "
             "it supplements", "partial"),
            ("A defect catalogue is a sample the author chose",
             "Two classes drawn from outside the guarantee, with "
             "expectations recorded in advance",
             "Seven programs remain seven programs", "partial"),
            ("RQ3 captures resource cost but not its origin",
             "None available on this host",
             "The memory result is established but unexplained", "none"),
            ("RQ4 measures the seam, not the safety of the whole",
             "The distinction is restated wherever the result is quoted",
             "One address space: a compile-time property of the Rust side "
             "bounds nothing at run time", "partial"),
        ]),
        ("CONCLUSION", "Are the differences real, or noise?", GREEN, [
            ("Run-to-run non-determinism",
             f"{M['NRepeats']} interleaved repeats, bootstrap intervals, an "
             f"exact paired permutation test, Holm correction, floors quoted",
             "Pairing cancels only what a block shared, so the tail "
             "percentiles stay unresolved", "partial"),
            ("A corrected p-value that does not replicate",
             "The allocator control runs every comparison twice, and "
             "replication is followed over the p-value",
             "Costs a result where the two disagree: the CPU effect is "
             "reported as unresolved", "good"),
        ]),
        ("EXTERNAL", "How far do the results travel?", AMBER_DEEP, [
            ("One subsystem, one workload, one machine",
             "RQ2 and RQ4 rest on the compilers and the C ABI rather than "
             "on the host",
             "The performance results do not travel: shared mutable state or "
             "allocation churn could behave differently", "partial"),
        ]),
    ]
    shade = {
        "good": (GREEN_CHIP, GREEN_EDGE, GREEN_DEEP),
        "partial": (AMBER_CHIP, AMBER_EDGE, AMBER_DEEP),
        "none": (RED_CHIP, RED_EDGE, RED_DEEP),
    }
    # Lay out first so the canvas is exactly as tall as the content needs.
    plan, total = [], 0
    for label, question, color, rows in bands:
        rh = []
        for threat, control, residual, level in rows:
            n = max(len(wrap(threat, 30)), len(wrap(control, 37)),
                    len(wrap(residual, 40)))
            rh.append(max(34, 16 + n * 12.5))
        bh = max(sum(r + 5 for r in rh) + 3, 20 + 12 * len(wrap(question, 23)))
        plan.append((label, question, color, rows, rh, bh))
        total += bh + 9

    d = Diagram(
        "25_threats_validity", 880, int(total) + 246,
        "Threats to validity, and what each control leaves behind",
        "Shaded by what remains after the control rather than by how the "
        "threat was described",
    )
    d.text(276, 92, "THREAT", 10, FAINT, weight=700, anchor="middle")
    d.text(488, 92, "CONTROL APPLIED", 10, FAINT, weight=700, anchor="middle")
    d.text(732, 92, "WHAT REMAINS", 10, FAINT, weight=700, anchor="middle")

    y = 100
    for label, question, color, rows, rh, bh in plan:
        d.card(20, y, 152, bh, label, wrap(question, 23), fill=GREY_FILL,
               stroke=GREY_EDGE, rx=7, sw=1.4, title_color=color,
               title_size=11.5, body_size=9.8, pad=13, gap=17, lh=12)
        ry = y + 3
        for (threat, control, residual, level), h in zip(rows, rh):
            fill, edge, deep = shade[level]
            d.card(180, ry, 192, h, None, wrap(threat, 30), fill=WHITE,
                   stroke=GREY_EDGE, rx=6, body_size=10, body_color=NAVY,
                   pad=10, lh=12.5)
            d.card(378, ry, 226, h, None, wrap(control, 37), fill=WHITE,
                   stroke=GREY_EDGE, rx=6, body_size=9.8, body_color=BODY,
                   pad=10, lh=12.5)
            d.card(610, ry, 250, h, None, wrap(residual, 40), fill=fill,
                   stroke=edge, rx=6, body_size=9.8, body_color=deep,
                   pad=10, lh=12.5)
            ry += h + 5
        y += bh + 9

    d.rect(20, y + 4, 840, 64, RED_FILL, RED, rx=8, sw=1.7)
    d.text(36, y + 26, "Two of these are load-bearing", 12, RED_DEEP,
           weight=700)
    d.lines(36, y + 45, [
        "The study cannot rule out single-author skill asymmetry, and its "
        "end-to-end instrument answers the question a vendor sizing a node",
        "would ask rather than the one a language comparison asks.",
    ], 10.5, BODY, lh=15)
    d.footer([
        "Only the last column is a live risk. The middle column is what has "
        "already been done about each.",
        "Two rows carry no mitigation at all, and are recorded as such.",
    ], y=y + 100)
    return d


# --------------------------------------------------------------------------
def contributions():
    d = Diagram(
        "26_contributions", 880, 524,
        "What the thesis concludes, and what it leaves behind",
        "The evidence divides by what is being measured before it divides by "
        "resource",
    )
    cards = [
        (15, GREEN, GREEN_FILL, GREEN_DEEP, "Safety: a difference in kind", [
            f"Safe Rust rejects all {M['FaultClassesPrevented']} injected",
            "memory-safety and data-race classes at",
            f"compile time. The {M['FaultClassesBoundary']} boundary",
            "classes, from a deadlock to a forgotten",
            "lock guard, compile and misbehave",
            "exactly as they do in C++.",
            "",
            "Rust eliminates data races, not race",
            "conditions, and aliasing errors, not",
            "lock-ordering errors.",
        ]),
        (301, BLUE, BLUE_FILL, BLUE_DEEP, "Migration: the call tax is bounded", [
            "An unmodified Rust core can be driven",
            "from C++ across a thin seam that",
            "holds every unsafe site. Any call",
            f"tax is bounded at {M['FfiOpBoundPct']}%.",
            "",
            "API design and training time",
            "were not measured.",
        ]),
        (587, AMBER_EDGE, AMBER_FILL, AMBER_DEEP,
         "Performance: two different answers", [
            f"The round-trip is only {M['BudgetCoreShareMax']}%",
            "language work. The median gap is",
            "small. On a quiet host the far",
            "tail sits lower in Rust.",
            "",
            "Timed apart, the core call is",
            f"{M['BudgetCoreRatio']}\u00d7 faster in {M['BudgetCoreFaster']}.",
            "Past saturation, service time",
            "stays unknown.",
        ]),
    ]
    for x, stroke, fill, deep, title, body in cards:
        d.card(x, 76, 278, 218, title, body, fill=fill, stroke=stroke, sw=1.8,
               rx=10, title_color=deep, body_size=10.5, pad=15, lh=14, gap=21)

    d.rect(15, 308, 850, 74, GREY_FILL, GREY_EDGE, rx=9, sw=1.6)
    d.text(31, 330, "What this adds to the decision is an instrument, not a "
                    "verdict", 12.5, NAVY, weight=700)
    cx = 31
    for label in ["A frozen specification", "A parity-tested pair",
                  "A reproducible framework",
                  "A catalogue of what the guarantee misses"]:
        w = 6.1 * len(label) + 22
        d.chip(cx, 344, w, 26, label, WHITE, BODY, size=10.5, rx=5,
               stroke=GREY_EDGE)
        cx += w + 10

    d.rect(15, 396, 850, 78, BLUE_FILL, BLUE, rx=9, sw=1.7)
    d.text(31, 418, "Where it goes next", 12.5, BLUE_DEEP, weight=700)
    d.text(206, 418, "a same-host repeat of in-run and deferred fill, "
                     "so the recorder can be separated from the machine.",
           10.5, BODY)
    cx = 31
    for label in ["Production traces", "Further subsystems",
                  "Call-site attribution", "Extend the catalogue",
                  "Async runtimes", "Isolate the heaps"]:
        w = 6.0 * len(label) + 20
        d.chip(cx, 434, w, 24, label, WHITE, BLUE_DEEP, size=10, rx=5,
               stroke=BLUE_EDGE)
        cx += w + 9

    d.footer(["Where the service still meets the sent rate, the choice is "
              "which defects to make impossible to write."], y=502)
    return d


def _chip_row(d, x, y, items, fill, color, stroke, h=28, gap=16, size=11):
    """Place labelled chips in a row and return each chip's centre x."""
    centres = []
    cx = x
    for i, (label, w) in enumerate(items):
        d.chip(cx, y, w, h, label, fill, color, size=size, rx=6, stroke=stroke)
        centres.append(cx + w / 2)
        if i < len(items) - 1:
            mid = y + h / 2
            d.arrow(cx + w + 2, mid, cx + w + gap - 2, mid, color=color, sw=1.6)
        cx += w + gap
    return centres


def _thru_bar(d, x, y, w, h, fill, stroke, label, color, size=12):
    """A throughput bar with its label to the right, width already scaled."""
    d.rect(x, y, max(w, 4), h, fill, stroke, rx=4, sw=1.4)
    d.text(x + max(w, 4) + 10, y + h * 0.72, label, size, color, weight=700)


# --------------------------------------------------------------------------
def load_regimes():
    """Four operating points on the offered-load axis, plus finished throughput.

    Spacing is schematic. The ticks and bar lengths come from the same macros
    the prose cites. A language knee is shown and not tested. An allocator
    split is shown the same way, and it is not a language knee.
    """
    d = Diagram("30_load_regimes", 880, 280)
    split = "KneeGapLoad" not in M

    d.rect(40, 48, 800, 18, GREY_FILL, rx=9)
    d.rect(40, 48, 280, 18, GREEN, rx=9)
    d.rect(320, 48, 140, 18, BLUE, rx=0)
    d.rect(460, 48, 160, 18, AMBER, rx=0)
    d.rect(620, 48, 220, 18, RED, rx=9)

    if split:
        mid_load = M["TrackingLoadCpp"]
        gap_load = M["KneeSplitLoad"]
        mid_chip = "both track"
        gap_chip = "one heap splits"
    else:
        mid_load = M["TrackingLoadCpp"]
        gap_load = M["TrackingLoadRust"]
        mid_chip = "C++ knee"
        gap_chip = "shown, not tested"
    ticks = [
        (80, M["ReprLoad"], GREEN_DEEP),
        (360, mid_load, BLUE_DEEP),
        (520, gap_load, AMBER_DEEP),
        (760, M["OverloadLoad"], RED_DEEP),
    ]
    for x, lab, color in ticks:
        d.rect(x - 1, 44, 3, 26, color)
        d.text(x, 36, lab, 12, color, weight=700, anchor="middle")

    d.chip(50, 88, 200, 36, "below saturation", GREEN_CHIP, GREEN_DEEP,
           size=13, rx=8, stroke=GREEN_EDGE)
    d.chip(300, 88, 160, 36, mid_chip, BLUE_CHIP, BLUE_DEEP, size=13,
           rx=8, stroke=BLUE)
    d.chip(470, 88, 150, 36, gap_chip, AMBER_CHIP, AMBER_DEEP,
           size=12, rx=8, stroke=AMBER_EDGE)
    d.chip(640, 88, 180, 36, "overload flip" if not split else "overload",
           RED_CHIP, RED_DEEP, size=13, rx=8, stroke=RED)

    d.text(40, 156, "kops/s finished", 12, FAINT)

    if split:
        fast = float(M["KneeSplitMedKeep"])
        slow = float(M["KneeSplitMedDrop"])
        fast_label = f"{'jemalloc' if 'jemalloc' in M['KneeSplitKeepHeap'] else 'system'}  {M['KneeSplitMedKeep']}"
        slow_label = f"{'jemalloc' if 'jemalloc' in M['KneeSplitDropHeap'] else 'system'}  {M['KneeSplitMedDrop']}"
        gap_name = M["KneeSplitLoad"]
    else:
        fast = float(M["KneeGapThrFast"])
        slow = float(M["KneeGapThrSlow"])
        fast_label = f"Rust  {M['KneeGapThrFast']}"
        slow_label = f"C++  {M['KneeGapThrSlow']}"
        gap_name = M["KneeGapLoad"]
    gap_w = 180.0
    d.text(40, 186, f"at {gap_name} (shown)", 12, AMBER_DEEP)
    if split:
        _thru_bar(d, 220, 172, gap_w, 18, AMBER, AMBER, fast_label, AMBER_DEEP)
        _thru_bar(d, 220, 196, gap_w * slow / max(fast, 1.0), 18, AMBER, AMBER,
                  slow_label, AMBER_DEEP)
    else:
        _thru_bar(d, 220, 172, gap_w, 18, GREEN, GREEN, fast_label, GREEN_DEEP)
        _thru_bar(d, 220, 196, gap_w * slow / max(fast, 1.0), 18, BLUE, BLUE,
                  slow_label, BLUE_DEEP)

    cpp = float(M["OverloadThrCpp"])
    rust = float(M["OverloadThrRust"])
    over_w = 110.0
    longer = max(cpp, rust, 1.0)
    d.text(500, 186, f"at {M['OverloadLoad']} (tested)", 12, RED_DEEP)
    _thru_bar(d, 680, 172, over_w * cpp / longer, 18, BLUE, BLUE,
              f"C++  {M['OverloadThrCpp']}", BLUE_DEEP)
    _thru_bar(d, 680, 196, over_w * rust / longer, 18, GREEN, GREEN,
              f"Rust  {M['OverloadThrRust']}", GREEN_DEEP)
    return d


def e2e_clock():
    """End-to-end round-trip, then the core call alone.

    Printed at \\linewidth. Labels are 16 to 18 units, about 8.5 to 10 pt
    on the page. The language sliver is drawn wide enough to see. Its share
    is the label, not the pixel width. The core-only pair is duration, so
    the slower language is the longer bar.
    """
    d = Diagram("31_e2e_clock", 880, 300)
    rest = M["BudgetCoreShareRest"]
    ratio = float(M["BudgetCoreRatio"])
    faster = M["BudgetCoreFaster"]

    bar_x, bar_w, bar_h = 188, 652, 34
    d.text(28, 74, "round-trip", 18, NAVY, weight=700)
    d.rect(bar_x, 52, 10, bar_h, GREEN, rx=2)
    d.rect(bar_x + 10, 52, bar_w - 10, bar_h, BLUE, rx=2)
    d.text(bar_x + 24, 38, f"language  {M['BudgetCoreShareMax']}%", 16,
           GREEN_DEEP, weight=700)
    d.text(bar_x + 280, 38, f"handoff  {rest}%", 16, BLUE_DEEP, weight=700)

    d.text(28, 186, "core only", 18, NAVY, weight=700)
    rust_w = 220
    cpp_w = rust_w * ratio
    d.text(bar_x, 162, "Rust", 16, GREEN_DEEP)
    d.rect(bar_x + 52, 142, rust_w, 28, GREEN, rx=4)
    d.text(bar_x, 214, "C++", 16, BLUE_DEEP)
    d.rect(bar_x + 52, 194, cpp_w, 28, BLUE, rx=4)
    d.text(bar_x + 52 + cpp_w + 14, 216,
           f"{faster} {M['BudgetCoreRatio']}\u00d7 faster", 16, GREEN_DEEP,
           weight=700)
    d.text(440, 268, "That clock cannot bound a language effect", 17, BODY,
           anchor="middle")
    return d


# --------------------------------------------------------------------------
def ffi_seam():
    """C++ host, thin seam, unmodified core: where unsafe sits, and the cost."""
    d = Diagram("07_ffi_seam", 900, 318)
    entries = M["FfiEntryPoints"]
    unsafe = M["FfiUnsafeFns"]
    core_unsafe = M["CoreUnsafe"]
    native = M["FfiOpNative"]
    seam = M["FfiOpSeam"]

    d.panel(20, 16, 248, 168, "C++ host", BLUE_FILL, BLUE, header_h=36)
    d.chip(40, 68, 208, 28, "opaque handle", BLUE_CHIP, BLUE_DEEP, size=12,
           rx=6, stroke=BLUE_EDGE)
    d.chip(40, 104, 208, 28, f"{entries} C entry points", BLUE_CHIP, BLUE_DEEP,
           size=12, rx=6, stroke=BLUE_EDGE)
    d.chip(40, 140, 208, 28, "status codes only", BLUE_CHIP, BLUE_DEEP, size=12,
           rx=6, stroke=BLUE_EDGE)

    d.divider(286, 28, 172, color=RED, sw=1.8, dash="7 5")
    d.text(286, 198, "C ABI", 11, RED, weight=700, anchor="middle")

    d.panel(326, 16, 248, 168, "uecm-ffi", ORANGE_FILL, ORANGE,
            header_color=ORANGE_DEEP, header_h=36)
    d.chip(346, 68, 208, 28, f'{entries} extern "C"', ORANGE_CHIP, ORANGE_DEEP,
           size=12, rx=6, stroke=ORANGE_EDGE)
    d.chip(346, 104, 208, 28, f"{unsafe} unsafe functions", RED_CHIP, RED_DEEP,
           size=12, rx=6, weight=700, stroke=RED_EDGE)
    d.chip(346, 140, 208, 28, "maps errors out", ORANGE_CHIP, ORANGE_DEEP,
           size=12, rx=6, stroke=ORANGE_EDGE)

    d.panel(632, 16, 248, 168, "uecm core", GREEN_FILL, GREEN, header_h=36)
    d.chip(652, 68, 208, 28, "unmodified", GREEN_CHIP, GREEN_DEEP, size=12,
           rx=6, stroke=GREEN_EDGE)
    d.chip(652, 104, 208, 28, f"{core_unsafe} unsafe", GREEN_CHIP, GREEN_DEEP,
           size=12, rx=6, weight=700, stroke=GREEN_EDGE)
    d.chip(652, 140, 208, 28, "safe Rust", GREEN_CHIP, GREEN_DEEP, size=12,
           rx=6, stroke=GREEN_EDGE)

    d.arrow(272, 100, 318, 100, color=NAVY, sw=2.2)
    d.arrow(578, 100, 624, 100, color=NAVY, sw=2.2)
    d.text(601, 90, "safe call", 10.5, BODY, anchor="middle")

    native_us = float(native)
    seam_us = float(seam)
    bar_max = 340.0
    w_seam = bar_max
    w_native = bar_max * native_us / seam_us
    d.rect(20, 214, 860, 86, GREY_FILL, GREY_EDGE, rx=10, sw=1.2)
    d.text(40, 238, "same signalling operation", 12, NAVY, weight=700)
    d.text(268, 262, "native", 11, BODY, anchor="end")
    d.rect(280, 251, w_native, 14, BLUE)
    d.text(280 + w_native + 10, 262, f"{native} \u00b5s", 11, BLUE_DEEP,
           weight=700)
    d.text(268, 286, "through the seam", 11, BODY, anchor="end")
    d.rect(280, 275, w_seam, 14, "#7fa8d4")
    d.text(280 + w_seam + 10, 286, f"{seam} \u00b5s", 11, BLUE_DEEP, weight=700)
    return d


# --------------------------------------------------------------------------
def guarantee_boundary():
    """Two columns: what safe Rust rejects, and what both languages still miss."""
    d = Diagram("17_guarantee_boundary", 860, 400)
    d.panel(16, 16, 400, 348, "Inside the guarantee", GREEN_FILL, GREEN,
            header_h=36)
    d.text(216, 70, "compile error in safe Rust", 12, GREEN_DEEP,
           anchor="middle")

    d.rect(34, 86, 364, 118, WHITE, GREEN_EDGE, rx=9, sw=1.5)
    d.text(48, 108, "Lifetime and aliasing", 13, NAVY, weight=700)
    d.text(48, 126, "ownership and borrowing", 11, MUTED)
    d.chip(48, 140, 162, 26, "Use-after-free", GREEN_CHIP, GREEN_DEEP, size=12,
           rx=5)
    d.chip(222, 140, 160, 26, "Double-free", GREEN_CHIP, GREEN_DEEP, size=12,
           rx=5)
    d.chip(48, 172, 334, 26, "Iterator invalidation", GREEN_CHIP, GREEN_DEEP,
           size=12, rx=5)

    d.rect(34, 216, 364, 100, WHITE, GREEN_EDGE, rx=9, sw=1.5)
    d.text(48, 238, "Unsynchronised access", 13, NAVY, weight=700)
    d.text(48, 256, "data races (Send/Sync)", 11, MUTED)
    d.chip(48, 274, 132, 26, "Data race", GREEN_CHIP, GREEN_DEEP, size=12, rx=5)
    d.chip(192, 274, 190, 26, "Unguarded shared mutation", GREEN_CHIP,
           GREEN_DEEP, size=11, rx=5)

    d.rect(34, 328, 364, 24, GREEN_CHIP, rx=5)
    d.text(216, 345, "No test required", 11.5, GREEN_DEEP, weight=700,
           anchor="middle")

    d.panel(444, 16, 400, 348, "Outside the guarantee", RED_FILL, RED,
            header_h=36)
    d.text(644, 70, "compiles and misbehaves in both", 12, RED_DEEP,
           anchor="middle")

    d.rect(462, 86, 364, 118, WHITE, RED_EDGE, rx=9, sw=1.5)
    d.text(476, 108, "Order of lock acquisition", 13, NAVY, weight=700)
    d.text(476, 126, "neither compiler prevents this", 11, MUTED)
    d.chip(476, 154, 336, 32, "Lock-order deadlock", RED_CHIP, RED_DEEP,
           size=13, rx=5)

    d.rect(462, 216, 364, 100, WHITE, RED_EDGE, rx=9, sw=1.5)
    d.text(476, 238, "Atomicity of a composed operation", 13, NAVY, weight=700)
    d.text(476, 256, "race conditions", 11, MUTED)
    d.chip(476, 276, 336, 26, "Lost update", RED_CHIP, RED_DEEP, size=13, rx=5)

    d.rect(462, 328, 364, 24, RED_CHIP, rx=5)
    d.text(644, 345, "Fails quietly", 11.5, RED_DEEP, weight=700,
           anchor="middle")

    d.divider(430, 16, 364, color=NAVY, sw=2.2, dash="9 5")
    d.rect(366, 372, 128, 22, NAVY, rx=11)
    d.text(430, 388, "the boundary", 12, WHITE, weight=700, anchor="middle")
    return d


# --------------------------------------------------------------------------
def workload_timeline():
    d = Diagram("27_workload_timeline", 880, 252)
    d.rect(16, 12, 848, 108, BLUE_FILL, BLUE_EDGE, rx=10, sw=1.5)
    d.text(36, 36, "signal", 15, BLUE_DEEP, weight=700)
    d.text(118, 36, "hot path only", 12, MUTED)
    _chip_row(
        d, 36, 52,
        [("signal", 108)] * 5,
        BLUE_CHIP, BLUE_DEEP, BLUE_EDGE, h=28, gap=16, size=12,
    )
    d.text(340, 102, "Connected, held for the run", 11, MUTED, anchor="middle")

    d.rect(16, 136, 848, 100, GREEN_FILL, GREEN_EDGE, rx=10, sw=1.5)
    d.text(36, 160, "mixed", 15, GREEN_DEEP, weight=700)
    d.text(118, 160, "one pass per UE", 12, MUTED)
    seq = [
        ("create", 88, "Idle"),
        ("setup", 88, "Connected"),
        ("signal", 88, "Connected"),
        ("add DRB", 92, "Connected"),
        ("begin", 80, "Reconf."),
        ("complete / abort", 124, "Connected"),
        ("release", 88, "Released"),
    ]
    centres = _chip_row(
        d, 28, 176,
        [(op, w) for op, w, _ in seq],
        GREEN_CHIP, GREEN_DEEP, GREEN_EDGE, h=28, gap=14, size=11,
    )
    for cx, (_, _, state) in zip(centres, seq):
        d.text(cx, 222, state, 10, MUTED, anchor="middle")
    return d


# --------------------------------------------------------------------------
def service_lifecycle():
    d = Diagram(
        "28_service_lifecycle", 880, 480,
        "Starting and stopping the service without losing a request",
        "Shutdown is the delicate half: it must stop workers blocked on an "
        "empty queue without abandoning work already in flight",
    )
    d.card(20, 80, 250, 120, "1.  Start", [
        "Allocate the shards, spawn one",
        "worker thread per shard, and hand",
        "each worker exclusive ownership of",
        "its store. Nothing is shared, so",
        "nothing needs locking.",
    ], fill=BLUE_FILL, stroke=BLUE, sw=1.8, rx=10, title_color=BLUE_DEEP,
        body_size=10.5, pad=15, lh=14, gap=21)
    d.card(292, 80, 268, 120, "2.  Run", [
        "A request is moved into the queue",
        "rather than copied, carrying its",
        "completion handle with it, so the",
        "producer and the worker never both",
        "hold a usable reference to it.",
    ], fill=BLUE_FILL, stroke=BLUE, sw=1.8, rx=10, title_color=BLUE_DEEP,
        body_size=10.5, pad=15, lh=14, gap=21)
    d.card(582, 80, 278, 120, "3.  Stop", [
        "Push one Stop sentinel onto each",
        "shard's queue, then join the workers,",
        "so shutdown returns only once every",
        "shard has actually stopped.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, sw=1.8, rx=10,
        title_color=AMBER_DEEP, body_size=10.5, pad=15, lh=14, gap=21)
    d.arrow(272, 140, 288, 140)
    d.arrow(562, 140, 578, 140)

    d.text(440, 238, "Why an in-band sentinel needs no drain API", 12.5, NAVY,
           weight=700, anchor="middle")
    d.rect(30, 258, 396, 46, WHITE, GREY_EDGE, rx=6, sw=1.5)
    d.text(38, 274, "queue head", 9, FAINT)
    qx = 40
    for label, fill, color, bold in [
        ("req", BLUE_CHIP, BLUE_DEEP, 400), ("req", BLUE_CHIP, BLUE_DEEP, 400),
        ("req", BLUE_CHIP, BLUE_DEEP, 400), ("Stop", AMBER_CHIP, AMBER_DEEP, 700),
    ]:
        d.chip(qx, 278, 88, 20, label, fill, color, size=10.5, rx=4,
               weight=bold)
        qx += 94
    d.text(228, 318, "strictly FIFO", 10, MUTED, anchor="middle")
    d.arrow(432, 281, 462, 281, color=GREY_EDGE, sw=1.8)
    d.chip(468, 265, 104, 32, "worker", GREY_FILL, NAVY, size=11.5, rx=6,
           stroke=GREY_EDGE)
    d.lines(586, 272, [
        "The worker observes Stop only after the",
        "three requests ahead of it have run and",
        "completed, so nothing is abandoned.",
    ], 10.5, BODY, lh=14)

    d.card(20, 332, 410, 90, "Tied to object destruction", [
        "The C++ destructor calls shutdown() and Rust's Drop",
        "does the same, so a service that goes out of scope",
        "cannot leave detached threads behind. A running flag",
        "makes the call idempotent on both sides.",
    ], fill=GREEN_FILL, stroke=GREEN, rx=9, sw=1.6, title_size=11.5,
        title_color=GREEN_DEEP, body_size=10.5, body_color=BODY, pad=15,
        lh=13.5, gap=19)
    d.card(450, 332, 410, 90, "The one piece of shared mutable state", [
        "An atomic activity counter, held by reference in C++",
        "and as a cloned Arc<AtomicU64> in Rust, incremented",
        "with relaxed ordering because nothing branches on its",
        "value. Write-only bookkeeping.",
    ], fill=GREY_FILL, stroke=GREY_EDGE, rx=9, sw=1.5, title_size=11.5,
        body_size=10.5, body_color=BODY, pad=15, lh=13.5, gap=19)

    d.footer(["No separate closed flag, timeout, or drain API is required, "
              "and no completion handle is left unfulfilled."], y=452)
    return d


# --------------------------------------------------------------------------
def research_gap():
    # Printed at \linewidth (16 cm). Table labels at 14.5 units come out
    # at about 7.5 pt. The title and subtitle are set larger: title 26
    # (~13 pt), subtitle 20 (~10 pt). The gap callout is one line per
    # sentence, at 16.5 (~8.5 pt), still above the row labels. Six short
    # lines beside the label left the right half of the box empty.
    W = 880
    head_y, head_h = 144, 112
    row_h, row_gap, n_rows = 54, 5, 6
    box_h, bottom = 116, 12
    by = head_y + head_h + 8 + n_rows * (row_h + row_gap) + 8
    H = by + box_h + bottom
    d = Diagram("29_research_gap", W, H)
    d.lines(
        W / 2, 34,
        [
            "What the neighbouring studies control,",
            "and what they leave varying",
        ],
        26, NAVY, lh=32, weight=700, anchor="middle",
    )
    d.lines(
        W / 2, 104,
        [
            "Each prior result is credible on its own terms, but none isolates",
            "the language for a control-plane subsystem driven into overload",
        ],
        20, MUTED, lh=24, anchor="middle",
    )

    x0, label_w, col_gap, col_w = 12, 198, 4, 128
    head_y, head_h = 144, 112
    name_size, name_lh = 14.5, 17
    who_size, who_lh = 13, 15
    # Every header line is measured to sit inside col_w with 8 px of
    # side pad. The previous wrapping left "Vendor RAN and",
    # "5G frameworks", and the two longest author lines wider than
    # the chip, so they ran into the next column.
    cols = [
        (["Cross-", "language", "benchmarks"], ["Pereira et al."]),
        (["Matched pairs", "in systems", "software"],
         ["Emmerich", "Suchert"]),
        (["Vendor RAN", "and 5G", "frameworks"],
         ["Other Ericsson", "theses"]),
        (["Matched", "telecom pair"], ["Emberg &", "Wadsten"]),
        (["This thesis"], []),
    ]
    col_x = []
    x = x0 + label_w + 6
    for name, who in cols:
        col_x.append(x)
        mine = not who
        d.rect(x, head_y, col_w, head_h,
               BLUE_CHIP if mine else GREY_FILL,
               BLUE if mine else GREY_EDGE, rx=8, sw=1.8 if mine else 1.4)
        block_h = len(name) * name_lh
        if who:
            block_h += 6 + len(who) * who_lh
        y_line = head_y + (head_h - block_h) / 2 + name_size * 0.78
        for i, part in enumerate(name):
            d.text(x + col_w / 2, y_line + i * name_lh, part, name_size,
                   BLUE_DEEP if mine else NAVY, weight=700, anchor="middle")
        if who:
            wy = y_line + len(name) * name_lh + 6
            for i, part in enumerate(who):
                d.text(x + col_w / 2, wy + i * who_lh, part, who_size,
                       MUTED, anchor="middle")
        x += col_w + col_gap

    rows = [
        (["Measures a systems", "language empirically"],
         ["yes", "yes", "yes", "yes", "yes"]),
        (["Holds design and", "concurrency model fixed"],
         ["no", "part", "no", "part", "yes"]),
        (["Latency-critical", "telecom domain"],
         ["no", "part", "yes", "yes", "yes"]),
        (["Stateful and concurrent", "under load"],
         ["no", "part", "yes", "no", "yes"]),
        (["Reports the tail, not", "just the average"],
         ["no", "no", "part", "no", "yes"]),
        (["Drives the system", "into overload"],
         ["no", "no", "no", "no", "yes"]),
    ]
    mark = {
        "yes": ("\u2713", GREEN_CHIP, GREEN_DEEP),
        "part": ("\u2013", AMBER_CHIP, AMBER_DEEP),
        "no": ("\u2717", RED_CHIP, RED_DEEP),
    }
    y = head_y + head_h + 8
    row_h, row_gap = 54, 5
    for parts, vals in rows:
        d.card(x0, y, label_w, row_h, None, parts, fill=WHITE, stroke=GREY_EDGE,
               rx=6, body_size=14.5, body_color=BODY, pad=8, lh=18,
               align="center")
        for cx, val in zip(col_x, vals):
            glyph, fill, color = mark[val]
            d.chip(cx, y, col_w, row_h, glyph, fill, color, size=20, rx=6,
                   weight=700)
        y += row_h + row_gap

    # One sentence per line, across the box. The old six-line column
    # stopped about two thirds of the way across and left the rest empty.
    if y + 8 != by:
        raise RuntimeError(f"gap box drifted: rows end at {y + 8}, canvas uses {by}")
    d.rect(x0, by, W - 2 * x0, box_h, BLUE_FILL, BLUE, rx=9, sw=1.7)
    label_x = x0 + 16
    gap_lines = [
        "most of the telecom studies change two things at once: the language, and how the program is run.",
        "Emberg and Wadsten keep the design the same, but they still test a stateless program.",
        "None holds the concurrency model fixed and then drives a stateful subsystem past saturation.",
    ]
    gap_size, gap_lh = 16.5, 22
    d.text(label_x, by + 26, "The gap", 20, BLUE_DEEP, weight=700)
    d.lines(label_x, by + 52, gap_lines, gap_size, BODY, lh=gap_lh)
    return d


# --------------------------------------------------------------------------
BUILDERS = [
    ffi_seam, guarantee_boundary,
    benchmark_harness, evidence_classes, traceability_map, stats_pipeline,
    repro_artifacts, threats_validity, contributions, workload_timeline,
    service_lifecycle, research_gap,
    load_regimes, e2e_clock,
]


def main():
    warnings = []
    for build in BUILDERS:
        d = build()
        with open(os.path.join(HERE, d.name + ".svg"), "w",
                  encoding="utf-8") as fh:
            fh.write(d.to_svg())
        with open(os.path.join(HERE, d.name + ".drawio"), "w",
                  encoding="utf-8") as fh:
            fh.write(d.to_drawio())
        warnings += d.warnings
        print(f"built {d.name}: svg + drawio  ({d.w}x{d.h})")
    if warnings:
        print(f"\n{len(warnings)} line(s) may overflow their box:")
        for w in warnings:
            print("  " + w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
