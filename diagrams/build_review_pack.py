#!/usr/bin/env python3
"""Build a review-only diagram pack for Thesis_v3.tex.

These pages explain the skeleton's argument in more detail than the five
paragraphs per chapter can. They are not inserted into any .tex file. Numbers
come from the generated macros, never from typed literals.

Usage:  python3 diagrams/build_review_pack.py
"""

from __future__ import annotations

import os
import re
import sys
from xml.sax.saxutils import escape, quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from dsl import (  # noqa: E402
    AMBER, AMBER_CHIP, AMBER_DEEP, AMBER_EDGE, AMBER_FILL,
    BLUE, BLUE_CHIP, BLUE_DEEP, BLUE_EDGE, BLUE_FILL,
    BODY, FAINT, GREY_DEEP, GREY_EDGE, GREY_FILL,
    GREEN, GREEN_CHIP, GREEN_DEEP, GREEN_EDGE, GREEN_FILL,
    MUTED, NAVY, ORANGE, ORANGE_CHIP, ORANGE_DEEP, ORANGE_EDGE,
    ORANGE_FILL, RED, RED_CHIP, RED_DEEP, RED_EDGE, RED_FILL,
    WHITE, Diagram,
)

FIGURES = os.path.join(HERE, os.pardir, "figures")
OUT = os.path.join(HERE, "review")
MACRO_FILES = (
    "gen_macros.tex",
    "gen_artefacts.tex",
    "gen_adoption.tex",
    "gen_complexity.tex",
    "gen_baremetal.tex",
    "gen_guest.tex",
)


def load_macros():
    values = {}
    for name in MACRO_FILES:
        path = os.path.join(FIGURES, name)
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$", line)
                if m:
                    values[m.group(1)] = plain(m.group(2))
    return values


def plain(s):
    """Strip TeX that a diagram label cannot typeset."""
    s = s.replace(r"\,", ",")
    s = s.replace(r"\%", "%")
    s = s.replace(r"\_", "_")
    s = s.replace(r"\texttt{", "").replace("}", "")
    return s


def wrap(text, width):
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


M = load_macros()


def chip_row(d, x, y, items, fill, color, stroke, h=28, gap=12, size=11):
    cx = x
    centres = []
    for i, (label, w) in enumerate(items):
        d.chip(cx, y, w, h, label, fill, color, size=size, rx=6, stroke=stroke)
        centres.append(cx + w / 2)
        if i < len(items) - 1:
            mid = y + h / 2
            d.arrow(cx + w + 2, mid, cx + w + gap - 2, mid, color=color, sw=1.6)
        cx += w + gap
    return centres


# --------------------------------------------------------------------------
def how_to_read():
    d = Diagram(
        "30_how_to_read", 880, 620,
        "How to read Thesis_v3, in one page",
        "Chapter 1 is the draft introduction. Chapters 2 to 7 keep five "
        "argument paragraphs each.",
    )
    chapters = [
        ("Ch. 1", "Introduction", "Why the comparison, four RQs, three hypotheses written first", BLUE),
        ("Ch. 2", "Background", "NG-RAN placement, what each language guarantees, the research gap", BLUE),
        ("Ch. 3", "Methodology", "UECM, three methods, fairness, statistics, artefacts", GREEN),
        ("Ch. 4", "Design", "Frozen spec, shared-nothing shards, forced-idiom log, parity", GREEN),
        ("Ch. 5", "Evaluation", "Hosts, two workloads, then results by load and by question", AMBER_DEEP),
        ("Ch. 6", "Discussion", "RQ answers, hypothesis verdicts, guidelines, what it cannot support", ORANGE_DEEP),
        ("Ch. 7", "Conclusion", "Narrow claim, then named next experiments", RED),
    ]
    y = 78
    for num, title, body, color in chapters:
        d.chip(20, y, 72, 44, num, WHITE, color, size=12, weight=700, rx=7,
               stroke=color)
        d.card(104, y, 756, 44, title, wrap(body, 88), fill=WHITE,
               stroke=GREY_EDGE, rx=7, title_size=13, body_size=11,
               pad=10, gap=16, lh=14)
        y += 52

    d.rect(20, y + 4, 840, 92, BLUE_FILL, BLUE, rx=9, sw=1.7)
    d.text(36, y + 28, "This pack is for review, not for the PDF yet", 13,
           BLUE_DEEP, weight=700)
    d.lines(36, y + 48, [
        "Each later page unpacks one move the skeleton has to make in five "
        "paragraphs. Open the combined .drawio and step the tabs.",
        "Nothing here is cited by Thesis_v3.tex. Pick a page, then we can "
        "shrink it to a thesis figure if it earns a caption.",
    ], 11.5, BODY, lh=16)
    d.footer([
        "Green in later pages marks a compiler or source fact. Amber marks a "
        "host-sensitive measurement. Red marks a refusal or a boundary.",
    ], y=598)
    return d


# --------------------------------------------------------------------------
def three_trends():
    d = Diagram(
        "31_three_trends", 880, 600,
        "Three trends that make the language choice timely",
        "They meet in one production component: UE Context Management inside "
        "a Nokia gNB-CU-CP",
    )
    cards = [
        (20, BLUE, BLUE_FILL, BLUE_DEEP, "1.  Cloud-native RAN", [
            "Control-plane functions now run on",
            "ordinary servers. Open-RAN turns the",
            "base station into virtualised,",
            "multi-vendor software on open",
            "interfaces.",
            "",
            "A latency spike or a memory defect is",
            "then a network-wide risk, not a local",
            "fault on purpose-built hardware.",
        ]),
        (307, AMBER_EDGE, AMBER_FILL, AMBER_DEEP, "2.  AI as a neighbour", [
            "IMT-2030 lists AI as a usage scenario,",
            "not only as a tuner. AI-RAN puts radio",
            "work and inference on one accelerated",
            "server.",
            "",
            "The control plane no longer has",
            "the host to itself. When the",
            "neighbour takes capacity,",
            "saturation arrives sooner.",
        ]),
        (594, GREEN, GREEN_FILL, GREEN_DEEP, "3.  Memory-safe languages", [
            "Vendors report that most serious",
            "bugs are memory-safety errors.",
            "Agencies urge a move away from",
            "C and C++. The EU Cyber Resilience",
            "Act adds duties from 2026 and 2027.",
            "",
            "The Act names no language. Direct",
            "RAN evidence is still missing.",
        ]),
    ]
    for x, stroke, fill, deep, title, body in cards:
        d.card(x, 76, 266, 268, title, body, fill=fill, stroke=stroke, sw=1.8,
               rx=10, title_color=deep, body_size=11, pad=14, lh=15, gap=22)

    d.arrow(286, 210, 300, 210, color=NAVY, sw=1.8)
    d.arrow(573, 210, 587, 210, color=NAVY, sw=1.8)

    d.rect(20, 362, 840, 168, GREY_FILL, GREY_EDGE, rx=10, sw=1.6)
    d.text(36, 386, "Where they land in this thesis", 13, NAVY, weight=700)
    d.card(36, 404, 250, 108, "Industrial setting", [
        "Nokia is an end-to-end RAN vendor.",
        "UECM is modelled on a live gNB-CU-CP",
        "part, specified in public, not copied",
        "from proprietary source.",
    ], fill=WHITE, stroke=BLUE_EDGE, rx=8, title_size=12, body_size=10.5,
        pad=12, lh=14, gap=18)
    d.card(304, 404, 250, 108, "A generational horizon", [
        "3GPP Release 20 and 21 cover 6G",
        "studies and normative work. A control",
        "plane written now is maintained next",
        "to that generation, not retired.",
    ], fill=WHITE, stroke=AMBER_EDGE, rx=8, title_size=12, body_size=10.5,
        pad=12, lh=14, gap=18)
    d.card(572, 404, 268, 108, "A concrete failure mode", [
        "A mobility storm frees a UE context",
        "while an in-flight message still refers",
        "to it. C++ compiles. Safe Rust rejects",
        "the dangling reference.",
    ], fill=WHITE, stroke=RED_EDGE, rx=8, title_size=12, body_size=10.5,
        pad=12, lh=14, gap=18)
    d.footer([
        "The study measures both safety (which defects are prevented, and when) "
        "and predictability (tail latency under overload).",
    ], y=568)
    return d


# --------------------------------------------------------------------------
def problem_rqs_hs():
    d = Diagram(
        "32_problem_rqs_hs", 880, 640,
        "The problem, the four questions, and the three hypotheses",
        "Hypotheses were written down before any measurement. Chapter 6 says "
        "how each one came out.",
    )
    d.panel(16, 72, 848, 118, "THE OPEN PROBLEM", RED_FILL, RED, header_h=32,
            header_size=13)
    d.lines(32, 120, [
        "Vendors are under technical and regulatory pressure to adopt "
        "memory-safe languages, yet they lack a direct, controlled test of a",
        "stateful, concurrent RAN control-plane part. Average-throughput "
        "comparisons leave three dimensions open.",
    ], 12, BODY, lh=16)
    chip_row(
        d, 32, 154,
        [("Tail latency under overload", 220),
         ("Defects stopped at compile time", 236),
         ("Incremental adoption cost", 210)],
        WHITE, RED_DEEP, RED_EDGE, h=26, gap=14, size=11,
    )

    rqs = [
        ("RQ1", "Latency predictability",
         "Median, p99, p99.9, p99.99 and the maximum, from light load through overload."),
        ("RQ2", "Defect scope",
         f"{M['FaultClassesPrevented']} classes inside the guarantee, "
         f"{M['FaultClassesBoundary']} on the boundary. When is each caught, and at what cost."),
        ("RQ3", "Safety-model overhead",
         "Bounds checks, copies, abstraction cost: throughput, CPU, and peak RSS."),
        ("RQ4", "Incremental adoption",
         "Effort, FFI interoperability, and risk of adding Rust a piece at a time."),
    ]
    y = 208
    d.text(16, y, "RESEARCH QUESTIONS", 11, FAINT, weight=700)
    y += 10
    for rq, title, body in rqs:
        d.chip(16, y, 64, 52, rq, BLUE_CHIP, BLUE_DEEP, size=13, weight=700,
               rx=7)
        d.card(90, y, 370, 52, title, wrap(body, 48), fill=WHITE,
               stroke=BLUE_EDGE, rx=7, title_size=12, body_size=10.5,
               pad=10, gap=15, lh=13)
        y += 60

    d.card(480, 218, 384, 84, "H1  Performance below saturation", [
        "The two languages are performance-equivalent",
        "below saturation, with any difference only in",
        "the far tail.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, rx=9, sw=1.6,
        title_color=AMBER_DEEP, body_size=11.5, pad=14, lh=15, gap=20)
    d.card(480, 312, 384, 84, "H2  Compile-time prevention", [
        "Safe Rust prevents at compile time the memory-",
        "safety and concurrency classes that C++ only",
        "tries to catch after the program is built.",
    ], fill=GREEN_FILL, stroke=GREEN, rx=9, sw=1.6,
        title_color=GREEN_DEEP, body_size=11.5, pad=14, lh=15, gap=20)
    d.card(480, 406, 384, 84, "H3  Interop cost is not run time", [
        "The extra time when C++ calls into Rust is",
        "small next to the operations themselves. The",
        "real cost is engineering work, not speed.",
    ], fill=BLUE_FILL, stroke=BLUE, rx=9, sw=1.6,
        title_color=BLUE_DEEP, body_size=11.5, pad=14, lh=15, gap=20)

    d.rect(16, 512, 848, 80, GREY_FILL, GREY_EDGE, rx=9, sw=1.5)
    d.text(32, 536, "How RQ2 stays falsifiable", 12.5, NAVY, weight=700)
    d.lines(32, 556, [
        f"The catalogue is two-sided on purpose: {M['FaultClassesPrevented']} "
        f"classes safe Rust is expected to prevent, and "
        f"{M['FaultClassesBoundary']} it is expected not to.",
        "A previous study mapped CWE types onto a list. This one builds and "
        "runs a program for each class.",
    ], 11.5, BODY, lh=16)
    d.footer([
        "H1 does double duty for RQ1 and RQ3. Chapter 6 finds that wording "
        "to be the hypothesis's main weakness.",
    ], y=620)
    return d


# --------------------------------------------------------------------------
def three_methods():
    d = Diagram(
        "33_three_methods", 880, 560,
        "Three methods, one planned variable: the language",
        "A weakness in one method does not carry into the rest of the claims",
    )
    methods = [
        (16, BLUE, BLUE_FILL, BLUE_DEEP, "RQ1 and RQ3", "Load sweep", [
            "Open-loop send schedule from light",
            "load to well past saturation.",
            f"{M['NVariants']} variants interleaved inside",
            f"each of {M['NRepeats']} repeats.",
            "",
            "A second timing splits the core",
            "operation from the cross-thread",
            "handoff. A third times the contended",
            "queue and the reply handle alone.",
            "",
            "Metric: median, p99, p99.9, p99.99,",
            "maximum, peak RSS, CPU, throughput.",
        ]),
        (306, GREEN, GREEN_FILL, GREEN_DEEP, "RQ2", "Fault injection", [
            f"{M['FaultClasses']} small programs, one per",
            "class, in both languages.",
            "",
            "C++ under AddressSanitizer,",
            "ThreadSanitizer, and",
            "UndefinedBehaviorSanitizer.",
            "Safe Rust compiled, and run under a",
            "bounded timeout where it builds.",
            "",
            "No static analyser is run, on purpose.",
            "The C++ columns report the tooling",
            "this study ran, not a ceiling on C++.",
        ]),
        (596, ORANGE, ORANGE_FILL, ORANGE_DEEP, "RQ4", "FFI prototype", [
            "A C++ host calls an unchanged Rust",
            "core across a C ABI, the direction a",
            "real migration takes.",
            "",
            "Per-call cost is measured on a real",
            "signalling operation, not inferred",
            "from an empty crossing.",
            "",
            "Memory bugs that cross a language",
            "sit at that seam. All unsafe stays",
            "there. The core is left free of it.",
        ]),
    ]
    for x, stroke, fill, deep, rq, title, body in methods:
        d.chip(x, 76, 108, 24, rq, WHITE, deep, size=11, weight=700, rx=5,
               stroke=stroke)
        d.card(x, 108, 268, 336, title, body, fill=fill, stroke=stroke, sw=1.8,
               rx=10, title_color=deep, body_size=11, pad=14, lh=15, gap=22)

    d.rect(16, 460, 848, 58, AMBER_FILL, AMBER_EDGE, rx=8, sw=1.6)
    d.text(32, 478, "The common control", 12.5, AMBER_DEEP, weight=700)
    d.lines(196, 474, [
        "both versions are built from one frozen spec. A gap between two",
        "independently written programs would also carry design, libraries, and skill.",
    ], 11.5, BODY, lh=15)
    d.footer([
        "Where a question can be answered with numbers, it uses numbers. "
        "Where it cannot, the answer is still by a fixed plan, in words.",
    ], y=542)
    return d


# --------------------------------------------------------------------------
def fairness_controls():
    d = Diagram(
        "34_fairness_controls", 880, 580,
        "Fairness is a controlled variable, not a claim after the fact",
        "The spec is frozen before either version exists. Where the languages "
        "cannot be written alike, the gap is logged.",
    )
    matched = [
        ("Public API and state machine", "Same operations, same illegal-op errors"),
        ("Thread model", "Shared-nothing, thread-per-shard, bounded MPSC"),
        ("Allocator and arena count", "jemalloc on both, system allocator as control"),
        ("Optimisation level", "Never tuned per side"),
        ("Hashing", "SplitMix64 for the shard, FNV-1a inside the map"),
        ("Histogram and load schedule", "One HDR setup, one open-loop send plan"),
    ]
    d.panel(16, 76, 430, 380, "MATCHED ACROSS BOTH SIDES", BLUE_FILL, BLUE,
            header_h=34)
    y = 126
    for title, sub in matched:
        d.card(34, y, 394, 48, title, [sub], fill=WHITE, stroke=BLUE_EDGE,
               rx=7, title_size=12, body_size=11, pad=12, gap=16)
        y += 54

    d.panel(462, 76, 402, 232, "LOGGED, NOT RESOLVED", AMBER_FILL, AMBER_EDGE,
            header_color=AMBER_DEEP, header_h=34)
    idioms = [
        ("Bounded queue", "Rust sync_channel. C++ mutex and two condition variables."),
        ("Reply handle", "std::promise against a fresh mpsc channel per request."),
        ("Per-shard map", "Each language's own standard hash map."),
        ("Request encoding", f"C++ tagged struct {M['CppRequestBytes']} B, "
                            f"Rust enum {M['RustRequestBytes']} B."),
    ]
    y = 126
    for title, sub in idioms:
        d.card(480, y, 366, 40, None, wrap(f"{title}: {sub}", 48), fill=WHITE,
               stroke=AMBER_EDGE, rx=6, body_size=10.5, body_color=BODY,
               pad=10, lh=13)
        y += 44

    d.panel(462, 324, 402, 132, "NOT CONTROLLED", RED_FILL, RED, header_h=34)
    d.lines(480, 376, [
        "One person wrote both versions and is",
        "not equally expert in both. Parity bounds",
        "what the code does. It does not bound",
        "speed. This is the main internal threat.",
    ], 11.5, BODY, lh=16)

    d.footer([
        f"The two overload-carrying gaps are the queue and the reply handle. "
        f"The core-operation gap is the hash map. Rust is {M['NlocRise']}% "
        f"longer and {M['CcnTotalDrop']}% simpler.",
    ], y=556)
    return d


# --------------------------------------------------------------------------
def parity_oracle():
    d = Diagram(
        "35_parity_oracle", 880, 520,
        "Parity is tested, not assumed",
        "A cross-diff of two logs cannot tell both-correct from both-wrong "
        "in the same way. A third version exists for that.",
    )
    steps = [
        ("1", "Frozen spec", "API, states, data layout, locks, shard size, thread model"),
        ("2", "Two implementations", "C++ and Rust, both following the spec, forced gaps logged"),
        ("3", "Language-neutral vectors", "Same operations, same seeds, logs diffed line by line"),
        ("4", "Python oracle", f"{M['ConfHandOps']} hand-derived expectations must hold before it may generate"),
        ("5", "Generated campaign", f"{M['ConfGenOps']} generated operations, no mismatch"),
        ("6", "Sanitisers on the path taken", "C++: ASan, TSan, UBSan. Rust: Miri. A clean result is bounded by the code that ran."),
    ]
    y = 80
    for num, title, body in steps:
        d.badge(48, y + 22, 18, num, fill=BLUE, color=WHITE, size=13)
        d.card(80, y, 780, 52, title, wrap(body, 92), fill=WHITE,
               stroke=BLUE_EDGE, rx=8, title_size=13, body_size=12,
               pad=12, gap=17, lh=15)
        if num != "6":
            d.arrow(48, y + 48, 48, y + 60, color=BLUE_EDGE, sw=1.6)
        y += 62

    d.footer([
        "Illegal operations return a typed error and leave the context unchanged.",
        "That closed set is what lets the same tests drive both versions along the same paths.",
    ], y=488)
    return d


# --------------------------------------------------------------------------
def four_variants():
    d = Diagram(
        "36_four_variants", 880, 520,
        "Four arms, interleaved so host noise is shared",
        f"{M['NLoadLevels']} offered-load levels up to {M['MaxOfferedLoad']} "
        f"kops/s, {M['NRepeats']} repeats, {M['NRuns']} measured runs",
    )
    d.text(230, 92, "jemalloc", 13, FAINT, weight=700, anchor="middle")
    d.text(650, 92, "system allocator (control)", 13, FAINT, weight=700,
           anchor="middle")
    d.text(28, 168, "C++", 16, BLUE_DEEP, weight=700, anchor="middle")
    d.text(28, 288, "Rust", 16, GREEN_DEEP, weight=700, anchor="middle")

    d.card(80, 112, 300, 108, "C++ + jemalloc", [
        "Production-like heap.",
        "Compared with Rust + jemalloc",
        "to isolate the language.",
    ], fill=BLUE_FILL, stroke=BLUE, sw=1.8, rx=10, title_color=BLUE_DEEP,
        body_size=12, pad=14, lh=16, gap=22)
    d.card(500, 112, 300, 108, "C++ + system", [
        "Control heap.",
        "Compared with C++ + jemalloc",
        "to isolate the allocator.",
    ], fill=BLUE_FILL, stroke=BLUE_EDGE, sw=1.6, rx=10, title_color=BLUE_DEEP,
        body_size=12, pad=14, lh=16, gap=22, dashed=True)
    d.card(80, 248, 300, 108, "Rust + jemalloc", [
        "Production-like heap.",
        "The pair that answers RQ1 and",
        "RQ3 under a matched allocator.",
    ], fill=GREEN_FILL, stroke=GREEN, sw=1.8, rx=10, title_color=GREEN_DEEP,
        body_size=12, pad=14, lh=16, gap=22)
    d.card(500, 248, 300, 108, "Rust + system", [
        "Control heap.",
        "A language effect that reverses",
        "here is reported as unresolved.",
    ], fill=GREEN_FILL, stroke=GREEN_EDGE, sw=1.6, rx=10,
        title_color=GREEN_DEEP, body_size=12, pad=14, lh=16, gap=22,
        dashed=True)

    d.rect(80, 380, 720, 80, AMBER_FILL, AMBER_EDGE, rx=9, sw=1.6)
    d.text(96, 404, "Inside each repeat the four arms run back to back", 13,
           AMBER_DEEP, weight=700)
    d.lines(96, 426, [
        "Interference common to a block is then shared rather than assigned "
        "to one variant. A load picked after seeing the sweep cannot enter",
        "the tested family. That is why the 448 kops/s tracking gap is shown "
        "and not tested.",
    ], 11.5, BODY, lh=16)
    d.footer([
        "The representative resource load is a chosen value "
        f"({M['ReprLoad']} kops/s), not one derived from the sweep.",
    ], y=496)
    return d


# --------------------------------------------------------------------------
def three_campaigns():
    d = Diagram(
        "37_three_campaigns", 880, 600,
        "Three campaigns, kept apart by prefix",
        "A sentence that quotes the wrong prefix is wrong in a way no build "
        "gate catches",
    )
    cols = [
        (16, GREEN, GREEN_FILL, GREEN_DEEP, "CANONICAL  (unprefixed)", [
            f"Bare metal, {M['MainCpu']}.",
            f"SMT {M['MainSmt']}. Governor {M['MainGovernor']}.",
            "Boost off. nohz_full. No hypervisor.",
            "isolcpus is refused: it pinned a whole",
            "earlier campaign onto one core.",
            "",
            f"g++ {M['MainGpp']}, rustc {M['MainRustc']}.",
            "The image pins the gcc-toolset major,",
            "not the point release.",
            "",
            "Role: every result the thesis reports.",
            "This is the only dataset in Chapter 5",
            "unless a caption says otherwise.",
        ]),
        (306, AMBER_EDGE, AMBER_FILL, AMBER_DEEP, "GUEST  (Guest*)", [
            f"KVM on {M['GuestCpu']}.",
            "Same design, same code.",
            f"g++ {M['GuestGpp']}, one GCC 15 release",
            "earlier. rustc matches.",
            "",
            "On that host the 95% band on one",
            "arm's p99 was larger than the gap",
            "between all four arms.",
            "",
            "Role: measurement-validity",
            "comparison. It could not resolve",
            "the far tail. It is kept, not dropped,",
            "so host-owned findings have a",
            "counter-example sitting beside them.",
        ]),
        (596, BLUE, BLUE_FILL, BLUE_DEEP, "SECOND HOST  (Bm*)", [
            f"Bare metal, {M['BmCpu']}.",
            "New shard count, load grid, run",
            "count, and compiler as a set.",
            "",
            "Role: whether findings survive those",
            "changes together, not any one of",
            "them on its own.",
            "",
            "The far-tail ranges do not meet.",
            "The language RSS gap keeps its",
            "sign and size. The allocator-to-",
            "language RSS ratio does not travel.",
        ]),
    ]
    for x, stroke, fill, deep, title, body in cols:
        d.card(x, 76, 268, 420, title, body, fill=fill, stroke=stroke, sw=1.8,
               rx=10, title_color=deep, title_size=12.5, body_size=11,
               pad=14, lh=15, gap=22)
    d.footer([
        "Do not write that the guest and the reported campaign share a "
        "toolchain. An image still uses the kernel of the host it sits on.",
    ], y=576)
    return d


# --------------------------------------------------------------------------
def load_regimes():
    d = Diagram(
        "38_load_regimes", 880, 620,
        "RQ1 splits at saturation, then splits again past it",
        "Four operating points, two of them tested, one shown because it was "
        "found after the data was in hand",
    )
    # axis
    d.rect(40, 110, 800, 8, GREY_EDGE, rx=4)
    points = [
        (80, f"{M['ReprLoad']}", "Chosen load", "Below saturation. Medians agree. Far tail readable.", GREEN),
        (280, f"{M['TrackingLoadCpp']}", "C++ tracks to here", "C++ arms stop keeping up.", BLUE),
        (500, f"{M['TrackingLoadRust']}", "Rust tracks to here", "Shown, not tested. Found after seeing the sweep.", AMBER_DEEP),
        (760, f"{M['OverloadLoad']}", "Deep overload", "Order flips. Largest tested language effect.", RED),
    ]
    for x, load, title, body, color in points:
        d.rect(x - 8, 106, 16, 16, color, rx=8)
        d.chip(x - 44, 84, 88, 22, f"{load} kops/s", WHITE, color, size=10,
               weight=700, rx=5, stroke=color)

    bands = [
        (40, 160, 196, GREEN, GREEN_FILL, GREEN_DEEP, "A.  Below saturation", [
            f"Four medians within {M['PFiftyRange']} us",
            f"({M['PFiftySpread']}%). Paired test still",
            f"finds {M['PFiftyDiffAbsMax']} us for Rust.",
            "Too small to bound a language",
            "effect. Far tail: slowest Rust",
            f"arm is {M['FarTailLangSep']} us below the",
            "fastest C++ one. Pooled, not a",
            "median of per-run p99.99.",
        ]),
        (252, 160, 196, BLUE, BLUE_FILL, BLUE_DEEP, "B.  C++ knee", [
            f"C++ holds to {M['TrackingLoadCpp']}",
            "kops/s. Rust still tracks.",
            "",
            f"SatKnee is the min across arms",
            f"({M['SatKnee']}). Do not quote it as",
            "where an arm stops coping.",
            "Quote each language's tracking",
            "load instead.",
        ]),
        (464, 160, 196, AMBER_EDGE, AMBER_FILL, AMBER_DEEP, "C.  Descriptive gap", [
            f"At {M['KneeGapLoad']} kops/s offered,",
            f"{M['KneeGapFaster']} still serves",
            f"{M['KneeGapThrFast']} where {M['KneeGapSlower']}",
            f"has fallen to {M['KneeGapThrSlow']}.",
            "",
            "Shown, not tested. Found after",
            "the data, so it cannot enter",
            "the Holm family.",
        ]),
        (676, 160, 164, RED, RED_FILL, RED_DEEP, "D.  Overload flip", [
            f"At {M['OverloadLoad']} kops/s,",
            f"{M['OverloadSustainedFaster']} finishes",
            f"{M['OverloadThrRatio']}x as much as",
            f"{M['OverloadSustainedSlower']}.",
            "",
            f"{M['OverloadThrAgree']} repeats,",
            "both heaps. Holm p",
            "at the family floor.",
        ]),
    ]
    for x, y, w, stroke, fill, deep, title, body in bands:
        d.card(x, y, w, 252, title, body, fill=fill, stroke=stroke, sw=1.8,
               rx=9, title_color=deep, title_size=12, body_size=10.5,
               pad=12, lh=14, gap=20)

    d.rect(40, 430, 800, 128, GREY_FILL, GREY_EDGE, rx=9, sw=1.5)
    d.text(56, 454, "Two deployment picks, pointing at opposite sides", 13,
           NAVY, weight=700)
    d.card(56, 472, 372, 70, "Sized to run below each arm's knee", [
        "Pick the arm that holds its sent rate further.",
        "That pick is shown, not tested.",
    ], fill=WHITE, stroke=GREEN_EDGE, rx=7, title_size=12, body_size=11,
        pad=12, gap=17, lh=14)
    d.card(448, 472, 376, 70, "A signal storm will drive past each knee", [
        "Pick the arm that still finishes more work then.",
        "That pick is tested. It is C++ here.",
    ], fill=WHITE, stroke=RED_EDGE, rx=7, title_size=12, body_size=11,
        pad=12, gap=17, lh=14)
    d.footer([
        "A test that stopped at a load the service still meets would have "
        "pointed the other way with the same setup.",
    ], y=596)
    return d


# --------------------------------------------------------------------------
def what_clock_measures():
    d = Diagram(
        "39_what_clock_measures", 880, 560,
        "What the end-to-end clock can and cannot say",
        "An operation in this design is a fraction of a percent of the "
        "round-trip. That clock cannot bound a language effect.",
    )
    d.panel(16, 76, 848, 160, "ONE END-TO-END ROUND-TRIP", BLUE_FILL, BLUE,
            header_h=34)
    # proportional bar, core is tiny
    d.text(36, 132, "Language work (the core)", 12, BLUE_DEEP, weight=700)
    d.rect(36, 144, 8, 28, GREEN, rx=3)
    d.text(52, 162, f"{M['BudgetCoreShareMax']}% of the sweep", 12, GREEN_DEEP,
           weight=700)
    d.text(36, 196, "Cross-thread handoff (operating system)", 12, BLUE_DEEP,
           weight=700)
    d.rect(36, 208, 790, 14, BLUE, rx=3)
    d.text(36, 236, f"the remaining {M['BudgetCoreShareRest']}%", 12, MUTED)

    d.card(16, 256, 270, 200, "What the sweep times", [
        "Producer to shard queue to worker",
        "to one-shot reply. Most of that time",
        "is passing work between threads.",
        "",
        f"Paired median gap: {M['PFiftyDiffAbsMax']} us.",
        "Real, and too small to attribute.",
    ], fill=WHITE, stroke=BLUE_EDGE, rx=9, sw=1.6, title_color=BLUE_DEEP,
        body_size=11.5, pad=14, lh=15, gap=21)
    d.card(304, 256, 270, 200, "What the microbench times", [
        "The core called directly, with no",
        "queue and no reply handle.",
        "",
        f"{M['BudgetCoreFaster']} is "
        f"{M['BudgetCoreRatio']}x faster.",
        "Likely cause: stock hash-map layout,",
        "not the safe-code model.",
        "",
        f"Both sit inside the sweep's blind",
        f"zone by a factor of {M['BudgetBoundVsCore']}.",
    ], fill=GREEN_FILL, stroke=GREEN, rx=9, sw=1.6, title_color=GREEN_DEEP,
        body_size=11.5, pad=14, lh=15, gap=21)
    d.card(592, 256, 272, 200, "What this forbids", [
        "Bounding a language effect from",
        "the end-to-end median.",
        "",
        "Calling the two languages",
        "equivalent because the sweep",
        "cannot tell them apart.",
        "",
        "cannot tell is not equivalent.",
    ], fill=RED_FILL, stroke=RED, rx=9, sw=1.6, title_color=RED_DEEP,
        body_size=11.5, pad=14, lh=15, gap=21)
    d.footer([
        "Point (5) of the abstract is written this way on purpose: the "
        "paired gap is reported, then refused as a bound.",
    ], y=536)
    return d


# --------------------------------------------------------------------------
def holm_family():
    d = Diagram(
        "40_holm_family", 880, 580,
        "The tested family is fixed before the campaign",
        f"Exact paired permutation tests over {M['NRepeats']} interleaved "
        f"repeats, Holm-corrected across {M['NTests']} comparisons",
    )
    d.panel(16, 76, 420, 380, "IN THE FAMILY", GREEN_FILL, GREEN, header_h=34)
    inside = [
        ("Median, p99, p99.9 at the chosen load", "Unit is the run. Pairing can cancel shared noise."),
        ("Overload throughput and CPU per finished call", "The largest language effect in the family."),
        ("Peak RSS language and allocator contrasts", "A run-level max, so a handful of stalls do not move it."),
        ("Allocator held fixed inside each comparison", "A result that reverses across heaps is unresolved."),
    ]
    y = 126
    for title, sub in inside:
        d.card(34, y, 384, 72, title, wrap(sub, 46), fill=WHITE,
               stroke=GREEN_EDGE, rx=7, title_size=12, body_size=11,
               pad=12, gap=17, lh=14)
        y += 80

    d.panel(452, 76, 412, 380, "KEPT OUT, WITH A REASON", RED_FILL, RED,
            header_h=34)
    outside = [
        ("Jitter from one call to the next", "No research question asks for it."),
        ("Pooled p99.99 far tail", "Unit is the operation, not the run. No across-repeat interval to test. No fallback to per-run p9999."),
        ("The 448 kops/s tracking gap", "Operating point found after the data. Shown, not tested."),
        ("Achieved throughput below saturation", "Pinned to offered load by construction, so it cannot express a language effect."),
    ]
    y = 126
    for title, sub in outside:
        d.card(470, y, 376, 72, title, wrap(sub, 44), fill=WHITE,
               stroke=RED_EDGE, rx=7, title_size=12, body_size=11,
               pad=12, gap=17, lh=14)
        y += 80

    d.rect(16, 472, 848, 64, AMBER_FILL, AMBER_EDGE, rx=8, sw=1.6)
    d.text(32, 496, "Floors, quoted so a null can be told from a math limit",
           12.5, AMBER_DEEP, weight=700)
    d.text(32, 518, f"Uncorrected floor p = {M['MinAttainableP']}. "
                    f"Holm-corrected floor {M['CorrectedFloor']}. "
                    f"When interval and p-value disagree, pairing decides.",
           11.5, BODY)
    d.footer([
        "Applying the reading rule to the block that suits the argument, "
        "and dropping it for the other, is the failure pre-commitment exists "
        "to prevent.",
    ], y=560)
    return d


# --------------------------------------------------------------------------
def rq2_catalogue():
    d = Diagram(
        "41_rq2_catalogue", 880, 700,
        "RQ2 is two-sided: seven inside the guarantee, seven outside it",
        "The seam double-free is the in-guarantee double-free rewritten "
        "through unsafe, not a new class",
    )
    d.panel(16, 72, 420, 430, "INSIDE: compile error in safe Rust",
            GREEN_FILL, GREEN, header_h=36, header_size=13)
    inside = [
        ("Use-after-free", "C++: ASan + TSan at runtime"),
        ("Double-free", "C++: ASan at runtime"),
        ("Iterator invalidation", "C++: ASan + TSan at runtime"),
        ("Data race", "C++: TSan at runtime"),
        ("Unguarded shared mutation", "C++: TSan at runtime"),
        ("Use-after-move", "C++: no sanitiser flags it. A moved-from object is still valid."),
        ("Thread-unsafe handle shared", "C++: TSan at runtime"),
    ]
    y = 124
    for title, sub in inside:
        d.card(34, y, 384, 48, title, wrap(sub, 50), fill=WHITE,
               stroke=GREEN_EDGE, rx=6, title_size=12, body_size=10.5,
               pad=10, gap=15, lh=13)
        y += 52

    d.panel(452, 72, 412, 430, "OUTSIDE: compiles and fails in both",
            RED_FILL, RED, header_h=36, header_size=13)
    outside = [
        ("Lock-order deadlock", f"TSan hit {M['DeadlockTsanHits']} of {M['DeadlockTsanRuns']} runs. Rate jumps. Do not quote it from memory."),
        ("Lost update", "Each access is synced, so TSan has no race to find. Silent in both."),
        ("Reference-cycle leak", "Leaks are safe in Rust by design. LeakSanitizer flags C++."),
        ("Integer overflow (release)", "Rust defines wrap. UBSan flags C++."),
        ("Worker-failure blast radius", "A failed worker takes its shard. Undetected on both sides."),
        ("Forgotten lock guard", "RAII removes the plain missed-unlock. Both forgotten-guard programs hang."),
        ("Seam double-free", "Same C++ half. Only the Rust column moves. Miri flags it. The C++ host is out of Miri's reach."),
    ]
    y = 124
    for title, sub in outside:
        d.card(470, y, 376, 48, title, wrap(sub, 48), fill=WHITE,
               stroke=RED_EDGE, rx=6, title_size=12, body_size=10.5,
               pad=10, gap=15, lh=13)
        y += 52

    d.rect(16, 518, 848, 128, GREY_FILL, GREY_EDGE, rx=9, sw=1.5)
    d.text(32, 542, "How the rest are caught, when they are caught", 13, NAVY,
           weight=700)
    d.card(32, 558, 260, 72, "Without a rewrite", [
        "LeakSanitizer and UBSan flag on",
        "the C++ programs as written.",
    ], fill=WHITE, stroke=BLUE_EDGE, rx=7, title_size=12, body_size=11,
        pad=10, gap=16, lh=14)
    d.card(308, 558, 260, 72, "After a recast", [
        "Loom and Shuttle flag the two",
        "concurrency boundary cases only",
        "once rewritten into their parts.",
    ], fill=WHITE, stroke=AMBER_EDGE, rx=7, title_size=12, body_size=11,
        pad=10, gap=16, lh=14)
    d.card(584, 558, 260, 72, "What this is not", [
        "Rust does not drop race conditions,",
        "lock order, leaks, wrapping, or the",
        "blast radius of a failed worker.",
    ], fill=WHITE, stroke=RED_EDGE, rx=7, title_size=12, body_size=11,
        pad=10, gap=16, lh=14)
    d.footer([
        "A compiler that will not build a program rules the defect out of "
        "each run. A sanitiser rules it out only of the runs a sanitiser "
        "test happens to take.",
    ], y=678)
    return d


# --------------------------------------------------------------------------
def hypothesis_verdicts():
    d = Diagram(
        "42_hypothesis_verdicts", 880, 600,
        "How the three hypotheses came out",
        "Saying this in public is what sets a test apart from a sketch",
    )
    d.card(16, 76, 848, 148, "H1  The median clause holds. The far-tail clause does not. Overload was never named.", [
        f"The paired test resolves {M['PFiftyDiffAbsMax']} us, too small to bound a language effect.",
        "The reported campaign now resolves the far tail, in Rust's favour.",
        "A second bare-metal host agrees on the direction.",
        "H1 was right about where a below-saturation gap would show up,",
        "and wrong that it was the only place. It was also not well posed.",
        "Performance-equivalent reads as one quantity and names at least three.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, sw=1.8, rx=10,
        title_color=AMBER_DEEP, body_size=12, pad=16, lh=15, gap=20)

    d.card(16, 240, 270, 130, "Quantity 1", [
        "Delivered round-trip below",
        "saturation. Practically a tie.",
        "Cannot bound a language effect.",
    ], fill=WHITE, stroke=AMBER_EDGE, rx=8, title_color=AMBER_DEEP,
        body_size=12, pad=14, lh=16, gap=20)
    d.card(304, 240, 270, 130, "Quantity 2", [
        "Code the compilers emit. Core",
        f"call {M['BudgetCoreRatio']}x faster in "
        f"{M['BudgetCoreFaster']}.",
        "Hash-map layout, not checks.",
    ], fill=WHITE, stroke=AMBER_EDGE, rx=8, title_color=AMBER_DEEP,
        body_size=12, pad=14, lh=16, gap=20)
    d.card(592, 240, 272, 130, "Quantity 3", [
        "Sustained work under overload.",
        f"{M['OverloadSustainedFaster']} holds "
        f"{M['OverloadThrRatio']}x the rate.",
        "The largest tested effect.",
    ], fill=WHITE, stroke=AMBER_EDGE, rx=8, title_color=AMBER_DEEP,
        body_size=12, pad=14, lh=16, gap=20)

    d.card(16, 388, 416, 140, "H2  Holds for its seven. Fails the looser reading.", [
        "Accepted for memory safety and data-race",
        "freedom. Rejected for concurrency correctness",
        "at large. A claim about safe Rust only.",
        "The seam case shows the same class returning",
        "inside unsafe.",
    ], fill=GREEN_FILL, stroke=GREEN, sw=1.8, rx=10, title_color=GREEN_DEEP,
        body_size=12, pad=14, lh=16, gap=21)
    d.card(448, 388, 416, 140, "H3  Supported by a bound, not by a miss.", [
        f"Any per-call tax is bounded at {M['FfiOpBoundPct']}% of",
        "that signalling call. That is support from a bound",
        "on a cost the measurement could have missed.",
        "The claim that the real cost is design and training",
        "is supported structurally, not statistically.",
    ], fill=BLUE_FILL, stroke=BLUE, sw=1.8, rx=10, title_color=BLUE_DEEP,
        body_size=12, pad=14, lh=16, gap=21)
    d.footer([
        "Chapter 6 revisits all three against the facts. The abstract's "
        "conclusions paragraph is the short form of this page.",
    ], y=576)
    return d


# --------------------------------------------------------------------------
def rss_two_effects():
    d = Diagram(
        "43_rss_two_effects", 880, 560,
        "Peak RSS: two real effects of the same order on bare metal",
        "Never write that the allocator effect is the larger one. Never quote "
        "their ratio without naming a host.",
    )
    d.card(16, 76, 416, 220, "Language effect (travels)", [
        f"Rust uses {M['RssLangDiffLo']} to {M['RssLangDiffHi']} MiB more",
        "peak RAM than C++ under either heap.",
        "Same sign and size on all three hosts.",
        "",
        "It is a fixed cost, not a cost per UE. The",
        "quiet host is where that can be seen.",
        "jemalloc's own counts put the extra past",
        "the heap, in the runtime a Rust process",
        "carries before it gets RAM.",
    ], fill=GREEN_FILL, stroke=GREEN, sw=1.8, rx=10, title_color=GREEN_DEEP,
        body_size=12, pad=16, lh=16, gap=22)
    d.card(448, 76, 416, 220, "Allocator effect (host-dependent ratio)", [
        f"Linking jemalloc at all costs {M['RssAllocDiffLo']} to",
        f"{M['RssAllocDiffHi']} MiB in either language.",
        "",
        f"On the guest that extra was "
        f"{M['GuestRssAllocOverLang']} times the",
        "language effect. On both bare-metal hosts",
        "the two are comparable.",
        "",
        "The transparent hugepage policy is the",
        "named candidate. The study does not claim",
        "causation. Future work can vary it.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, sw=1.8, rx=10,
        title_color=AMBER_DEEP, body_size=12, pad=16, lh=16, gap=22)

    d.card(16, 314, 270, 160, "CPU below saturation", [
        f"At {M['ReprLoad']} kops/s Rust uses at",
        f"most {M['CpuDiffAbsMax']} percentage points",
        "less. Scoped to that load, not to",
        "the whole below-saturation band.",
    ], fill=BLUE_FILL, stroke=BLUE, rx=9, sw=1.6, title_color=BLUE_DEEP,
        body_size=12, pad=14, lh=16, gap=21)
    d.card(304, 314, 270, 160, "CPU past saturation", [
        f"The slower arm spends "
        f"{M['OverloadCpuPerOpRatio']}x",
        "the CPU per finished call. That is",
        "effort spent without finishing.",
        "The sign of CPU hangs on the load.",
    ], fill=RED_FILL, stroke=RED, rx=9, sw=1.6, title_color=RED_DEEP,
        body_size=12, pad=14, lh=16, gap=21)
    d.card(592, 314, 272, 160, "A contrary result, reread", [
        "Karlbäck reports Rust lowest on",
        "RAM. Those arms are two",
        "concurrency runtimes (Boost.Fibers",
        "vs Tokio), not two languages.",
    ], fill=WHITE, stroke=GREY_EDGE, rx=9, sw=1.6, title_color=NAVY,
        body_size=12, pad=14, lh=16, gap=21)
    d.footer([
        "A single number for the CPU cost of Rust's safe-code model would "
        "mix two loads that move in opposite ways.",
    ], y=536)
    return d


# --------------------------------------------------------------------------
def adoption_axes():
    d = Diagram(
        "44_adoption_axes", 880, 580,
        "RQ4: cheap in the machine, costly in the people",
        f"A C++ host can call an unchanged Rust core. All unsafe stays in "
        f"{M['FfiUnsafeFns']} functions. The core has {M['CoreUnsafe']} "
        f"unsafe sites.",
    )
    axes = [
        (16, GREEN, GREEN_FILL, GREEN_DEEP, "Seam structure", [
            f"{M['FfiEntryPoints']} C entry points in",
            f"{M['FfiSeamLines']} lines of Rust.",
            f"{M['FfiUnsafeFns']} functions hold all",
            "raw pointers. Core is clean.",
            "",
            "Final. Read off the code.",
            "Does not depend on host.",
        ]),
        (232, BLUE, BLUE_FILL, BLUE_DEEP, "Per-call tax", [
            f"Native {M['FfiOpNative']} us.",
            f"Through the seam {M['FfiOpSeam']} us.",
            f"Bound: {M['FfiOpBoundPct']}% of that call.",
            "",
            "Timed on a real signal, not",
            "an empty crossing. A no-op",
            "crossing bounds itself.",
        ]),
        (448, AMBER_EDGE, AMBER_FILL, AMBER_DEEP, "Build time", [
            f"{M['BuildDepShareCpu']}% of the Rust clean",
            "build is third-party code.",
            "Own source builds in",
            f"{M['BuildAllFirstPartyCpuRatio']}x the CPU g++ needs.",
            "",
            "The host-sensitive axis.",
            "Quote the paired ratio.",
        ]),
        (664, ORANGE, ORANGE_FILL, ORANGE_DEEP, "Shipped size", [
            f"The {M['FootShippedRatio']}x gap compares",
            "two linkage policies. Order",
            "flips if policy is matched.",
            "",
            f"Compared part: {M['DepsCore']} crates,",
            f"{M['CoreUnsafe']} unsafe sites. Never",
            "quote that ratio alone.",
        ]),
    ]
    for x, stroke, fill, deep, title, body in axes:
        d.card(x, 76, 200, 300, title, body, fill=fill, stroke=stroke, sw=1.8,
               rx=10, title_color=deep, body_size=10.5, pad=12, lh=14, gap=20)

    d.rect(16, 396, 848, 120, GREY_FILL, GREY_EDGE, rx=9, sw=1.5)
    d.text(32, 420, "Where C++ still leads, and the limit of the seam", 13,
           NAVY, weight=700)
    d.lines(32, 444, [
        "The edit and compile loop for a change that stays inside one source "
        "file is faster in C++. That is the one axis of outright lead.",
        "Keeping unsafe at the seam bounds what has to be checked, not what "
        "can be corrupted. Host and part share one address space.",
        f"A vendor worried about build time or footprint should audit its "
        f"crate budget ({M['BuildDepShareCpu']}% of CPU is dependencies) "
        f"before blaming the compiler.",
    ], 12, BODY, lh=18)
    d.footer([
        "The C++ unsafe cell stays blank on purpose. The language marks no "
        "such region.",
    ], y=556)
    return d


# --------------------------------------------------------------------------
def guidelines():
    d = Diagram(
        "45_guidelines", 880, 560,
        "Engineering guidelines, each carrying the limit of its finding",
        "These are the practical form of Chapter 6, not a vendor playbook "
        "detached from the evidence",
    )
    rules = [
        ("1", "Choose a first part for how thin its API is, not for its size.",
         "The rewrite of a rich interface is the schedule risk. The edge itself is not."),
        ("2", "Keep the C ABI in its own crate and the core free of unsafe.",
         "That keeps unsafe out of the crate chains it spreads through."),
        ("3", "Leave the concurrency review budget where it is.",
         "Taking Rust drops data races. It leaves the class that fails in silence."),
        ("4", "Prefer a shared-nothing structure in either language.",
         "The strongest concurrency result here belongs to the design and to neither compiler."),
        ("5", "Plan the learning curve as a training cost and track it.",
         "H3's human-cost claim is structural, not statistical."),
        ("6", "Time the part as well as the round-trip. Sweep past the knee.",
         "The rule this study would most like to have used from the start."),
    ]
    y = 78
    for num, title, limit in rules:
        d.badge(40, y + 24, 16, num, fill=BLUE, color=WHITE, size=12)
        d.card(68, y, 792, 60, title, wrap(limit, 92), fill=WHITE,
               stroke=BLUE_EDGE, rx=8, title_size=13, body_size=12,
               pad=12, gap=17, lh=15)
        y += 68
    d.footer([
        "A plan that reads memory-safe as concurrency-safe would mis-budget "
        "its review effort. Memory-safety bugs in Rust involve unsafe.",
    ], y=536)
    return d


# --------------------------------------------------------------------------
def cannot_support():
    d = Diagram(
        "46_cannot_support", 880, 620,
        "What this study cannot support, and what it would do next",
        "The first professional duty is not to claim too much. The second is "
        "how far the data reaches.",
    )
    d.panel(16, 72, 848, 196, "THREE THREATS THAT STILL MATTER", RED_FILL, RED,
            header_h=34)
    d.card(32, 120, 260, 128, "Single-author skill", [
        "One person wrote both versions.",
        "In this field a code review then",
        "more speed work flipped a printed",
        "verdict from comparable to Rust",
        "worse by 85 to 91%.",
    ], fill=WHITE, stroke=RED_EDGE, rx=8, title_size=12.5, body_size=11,
        pad=12, lh=14, gap=18)
    d.card(308, 120, 260, 128, "The clock times the design", [
        "End-to-end answers the question a",
        "vendor sizing a node would ask.",
        "It answers the language question",
        "hardly at all. The core timing is",
        "the supplement, and it is narrower.",
    ], fill=WHITE, stroke=RED_EDGE, rx=8, title_size=12.5, body_size=11,
        pad=12, lh=14, gap=18)
    d.card(584, 120, 260, 128, "One subsystem, one mix", [
        "Call mix is not a public cell mix.",
        "A different mix moves both sides",
        "the same way. It limits how far",
        "the numbers travel. It does not",
        "make the test unfair.",
    ], fill=WHITE, stroke=RED_EDGE, rx=8, title_size=12.5, body_size=11,
        pad=12, lh=14, gap=18)

    d.panel(16, 284, 848, 248, "NAMED NEXT EXPERIMENTS", BLUE_FILL, BLUE,
            header_h=34)
    nexts = [
        ("Hugepage policy", "Vary it on one host with all else fixed. The three hosts disagree about the allocator-to-language RSS ratio."),
        ("Production traces", "Replay anonymised traces to check the call mix."),
        ("Shared mutable state", "A part that is not shared-nothing would work the two sides in a way this design does not."),
        ("Async vs thread-per-shard", "Split the runtime from the language in the tail result."),
        ("Two heaps in one process", "Price what keeping a core free of unsafe is worth."),
        ("Longer case study", "Track defect counts and review effort while adding Rust a piece at a time."),
    ]
    positions = [(32, 332), (308, 332), (584, 332), (32, 420), (308, 420),
                 (584, 420)]
    for (x, y), (title, body) in zip(positions, nexts):
        d.card(x, y, 260, 80, title, wrap(body, 34), fill=WHITE,
               stroke=BLUE_EDGE, rx=7, title_size=12, body_size=10.5,
               pad=10, gap=16, lh=13)
    d.footer([
        "A deadlocked control plane is an outage. A lost counter update that "
        "stays silent can misinform a mobility decision. Nothing shown here "
        "stops either.",
    ], y=596)
    return d


# --------------------------------------------------------------------------
def claim_register():
    d = Diagram(
        "47_claim_register", 880, 600,
        "A register of what a sentence is allowed to say",
        "The defect that costs a grade is a correct statement attached to "
        "the wrong scope",
    )
    rows = [
        (GREEN, GREEN_FILL, GREEN_DEEP, "FINAL", [
            "compilers and source",
            "",
            "RQ2 compile outcomes",
            "Seam size, unsafe sites",
            "Size and complexity",
            "Transcript parity",
        ]),
        (AMBER_EDGE, AMBER_FILL, AMBER_DEEP, "HOST-SENSITIVE", [
            "say which host",
            "",
            "Tail latency, overload",
            "CPU (sign hangs on load)",
            "Absolute build times",
            "Allocator / language RSS",
        ]),
        (BLUE, BLUE_FILL, BLUE_DEEP, "TRAVELS", [
            "all three hosts agree",
            "",
            "Language RSS, a few MiB",
            "Far-tail direction on",
            "both bare-metal hosts",
            "Paired build-time ratio",
        ]),
        (RED, RED_FILL, RED_DEEP, "REFUSED", [
            "do not write",
            "",
            "equivalent from cannot tell",
            "isolcpus as a tuning step",
            "Guest and main share a",
            "toolchain",
            "Shipped size as language",
            "TSan rate from memory",
        ]),
    ]
    x = 16
    for stroke, fill, deep, title, items in rows:
        d.card(x, 76, 208, 360, title, items, fill=fill, stroke=stroke,
               sw=1.8, rx=10, title_color=deep, title_size=11, body_size=11,
               pad=12, lh=20, gap=22)
        x += 216

    d.rect(16, 456, 848, 92, GREY_FILL, GREY_EDGE, rx=9, sw=1.5)
    d.text(32, 480, "Three live traps for a generated macro", 13, NAVY,
           weight=700)
    d.lines(32, 502, [
        "A Pct macro read as a multiple. A lo-hi range wrapped in math mode, "
        "which typesets as two minus signs. A quantity that is right where it",
        "is derived and wrong at every site that summarises it (CpuDiffAbsMax "
        "is scoped to ReprLoad, not to the whole below-saturation regime).",
    ], 12, BODY, lh=18)
    d.footer([
        "These pages quote the same macros the prose does. If a fresh "
        "campaign moves a number, rebuild this pack with the same command.",
    ], y=576)
    return d


# --------------------------------------------------------------------------
def ngran_two_splits():
    d = Diagram(
        "48_ngran_two_splits", 880, 560,
        "The gNB is split twice. UECM sits in one of those boxes.",
        "The first split is central versus distributed. The second is "
        "control versus user plane inside the central unit.",
    )
    d.chip(20, 76, 72, 88, "UE", GREY_FILL, NAVY, size=16, weight=700, rx=10,
           stroke=GREY_EDGE)
    d.chip(140, 76, 100, 88, "gNB-DU", BLUE_CHIP, BLUE_DEEP, size=15,
           weight=700, rx=10, stroke=BLUE)
    d.arrow(96, 120, 136, 120)

    d.rect(280, 68, 380, 200, GREY_FILL, GREY_EDGE, rx=12, sw=1.6, dashed=True)
    d.text(470, 90, "gNB-CU", 13, FAINT, weight=700, anchor="middle")
    d.card(300, 104, 340, 72, "gNB-CU-CP  (this thesis)", [
        "RRC, mobility, UE context.",
        "UE Context Management lives here.",
    ], fill=BLUE_FILL, stroke=BLUE, sw=1.8, rx=8, title_color=BLUE_DEEP,
        body_size=12, pad=12, gap=18, lh=15)
    d.card(300, 184, 340, 68, "gNB-CU-UP", [
        "User-plane forwarding. Not measured.",
    ], fill=GREEN_FILL, stroke=GREEN_EDGE, rx=8, title_color=GREEN_DEEP,
        body_size=12, pad=12, gap=18, lh=15)

    d.chip(700, 76, 160, 88, "5G Core", GREY_FILL, NAVY, size=15, weight=700,
           rx=10, stroke=GREY_EDGE)
    d.arrow(244, 120, 276, 120)
    d.arrow(664, 120, 696, 120)
    d.text(118, 178, "Uu", 11, MUTED, anchor="middle")
    d.text(258, 178, "F1", 11, MUTED, anchor="middle")
    d.text(682, 178, "NG", 11, MUTED, anchor="middle")
    d.text(470, 268, "E1 between CU-CP and CU-UP", 11, MUTED, anchor="middle")

    d.card(20, 300, 270, 168, "Why this part", [
        "UECM owns per-UE control state.",
        "Many UEs at once. Strict lifecycle.",
        "Millisecond-scale signalling budgets.",
        "Small enough to specify in full and",
        "build twice. Hard enough to stand in",
        "for this class of service.",
    ], fill=WHITE, stroke=BLUE_EDGE, rx=9, title_color=BLUE_DEEP,
        body_size=12, pad=14, lh=16, gap=20)
    d.card(306, 300, 270, 168, "What the splits buy", [
        "DU sits close to the radio.",
        "CU-CP can run on ordinary servers.",
        "Open-RAN lets each box come from",
        "a different vendor.",
        "A defect here is then network-wide,",
        "not local to one vendor's metal.",
    ], fill=WHITE, stroke=AMBER_EDGE, rx=9, title_color=AMBER_DEEP,
        body_size=12, pad=14, lh=16, gap=20)
    d.card(592, 300, 268, 168, "What this is not", [
        "Not the user plane.",
        "Not PHY or layer 2.",
        "Not a packet processor.",
        "Findings travel to other stateful,",
        "partitionable control-plane",
        "services of this kind.",
    ], fill=WHITE, stroke=RED_EDGE, rx=9, title_color=RED_DEEP,
        body_size=12, pad=14, lh=16, gap=20)
    d.footer([
        "Figure ngran in the thesis is the compact form. This page is the "
        "reading aid for the two-axis split.",
    ], y=536)
    return d


# --------------------------------------------------------------------------
def open_loop():
    d = Diagram(
        "49_open_loop", 880, 560,
        "The sender keeps to its plan, even when the service is late",
        "A closed-loop sender stops while a stall is in progress. It then "
        "never records the delay of that stall.",
    )
    d.panel(16, 76, 416, 280, "CLOSED LOOP  (not used)", RED_FILL, RED,
            header_h=34)
    d.lines(36, 128, [
        "1. Send a request.",
        "2. Wait for the reply.",
        "3. Only then send the next one.",
    ], 13, BODY, lh=22)
    d.card(36, 210, 376, 120, "What goes wrong", [
        "During a stall the sender is idle.",
        "The histogram never sees the wait.",
        "Overload looks milder than it is.",
        "That is coordinated omission.",
    ], fill=WHITE, stroke=RED_EDGE, rx=8, title_color=RED_DEEP,
        body_size=12, pad=12, lh=16, gap=18)

    d.panel(448, 76, 416, 280, "OPEN LOOP  (this study)", GREEN_FILL, GREEN,
            header_h=34)
    d.lines(468, 128, [
        "1. Keep the send times on a schedule.",
        "2. Do not wait for replies.",
        "3. Time from the intended send time.",
    ], 13, BODY, lh=22)
    d.card(468, 210, 376, 120, "What that records", [
        "A stall still occupies its slot.",
        "The HDR histogram is corrected so",
        "missing replies cannot hide delay.",
        "Overload shows up as delay.",
    ], fill=WHITE, stroke=GREEN_EDGE, rx=8, title_color=GREEN_DEEP,
        body_size=12, pad=12, lh=16, gap=18)

    d.rect(16, 376, 848, 124, BLUE_FILL, BLUE, rx=9, sw=1.6)
    d.text(32, 400, "The queue is bounded on purpose", 13, BLUE_DEEP,
           weight=700)
    d.lines(32, 424, [
        "When it is full the caller blocks. A drop rule would hide overload.",
        "This study needs overload to show up as delay, not as lost work the",
        "histogram never sees. The same reason the send schedule is open-loop.",
    ], 12.5, BODY, lh=18)
    d.footer([
        "Schroeder and Harchol-Balter: an open arrival process is what a "
        "control plane under a storm actually looks like.",
    ], y=536)
    return d


# --------------------------------------------------------------------------
def request_path():
    d = Diagram(
        "50_request_path", 880, 520,
        "One request, from the producer to the reply",
        "Most of this path is passing work between threads. That is why the "
        "end-to-end clock cannot bound a language effect.",
    )
    steps = [
        ("Producer", "Load generator.\nHashes ue_id.\nWaits on a one-shot\nreply handle."),
        ("MPSC queue", "Bounded. FIFO.\nBlocks when full.\nOne queue per shard."),
        ("Worker", "The only thread\nthat may touch this\nshard. No lock on\ncontext state."),
        ("Shard map", "Language's own\nhash map. This is\nthe core the second\nclock times."),
        ("Reply", "Result goes back\non the one-shot\nhandle. Producer\nunblocks."),
    ]
    xs = [16, 188, 360, 532, 704]
    for x, (title, body) in zip(xs, steps):
        d.card(x, 88, 160, 188, title, body.split("\n"), fill=BLUE_FILL,
               stroke=BLUE, sw=1.7, rx=10, title_color=BLUE_DEEP,
               body_size=11.5, pad=12, lh=16, gap=20)
    for x in xs[:-1]:
        d.arrow(x + 164, 182, x + 184, 182)

    d.rect(16, 300, 332, 140, GREEN_FILL, GREEN, rx=9, sw=1.6)
    d.text(32, 324, "Timed apart: the core", 13, GREEN_DEEP, weight=700)
    d.lines(32, 348, [
        "Shard map only. No queue.",
        f"{M['BudgetCoreFaster']} is {M['BudgetCoreRatio']}x faster.",
        f"{M['BudgetCoreShareMax']}% of the round-trip.",
        "Likely hash-map layout.",
    ], 12, BODY, lh=18)

    d.rect(364, 300, 500, 140, AMBER_FILL, AMBER_EDGE, rx=9, sw=1.6)
    d.text(380, 324, "Timed together: the round-trip", 13, AMBER_DEEP,
           weight=700)
    d.lines(380, 348, [
        "Producer to queue to worker to map to reply.",
        f"Paired median gap {M['PFiftyDiffAbsMax']} us. Real, too small to attribute.",
        "The rest is operating-system handoff.",
        "That clock answers a vendor sizing a node, not a language comparison.",
    ], 12, BODY, lh=18)
    d.footer([
        "The only shared mutable state either version allows is one atomic "
        "counter. No control flow depends on its value.",
    ], y=496)
    return d


# --------------------------------------------------------------------------
def one_repeat():
    d = Diagram(
        "51_one_repeat", 880, 500,
        "Inside one repeat the four arms run back to back",
        f"{M['NRepeats']} repeats. {M['NLoadLevels']} loads. "
        f"{M['NRuns']} measured runs. Interleaving makes host noise common "
        "to a block.",
    )
    d.text(440, 88, "ONE REPEAT, ONE LOAD", 12, FAINT, weight=700,
           anchor="middle")
    arms = [
        (40, BLUE, BLUE_FILL, BLUE_DEEP, "C++  jemalloc"),
        (250, BLUE, BLUE_CHIP, BLUE_DEEP, "C++  system"),
        (460, GREEN, GREEN_FILL, GREEN_DEEP, "Rust  jemalloc"),
        (670, GREEN, GREEN_CHIP, GREEN_DEEP, "Rust  system"),
    ]
    for x, stroke, fill, deep, title in arms:
        d.card(x, 104, 190, 80, title, ["same seed, same ops"], fill=fill,
               stroke=stroke, sw=1.7, rx=9, title_color=deep, body_size=12,
               pad=12, gap=18, lh=16)
    for x in (234, 444, 654):
        d.arrow(x, 144, x + 12, 144)

    d.card(40, 212, 400, 160, "What pairing can cancel", [
        "A noisy minute of the host hits all four",
        "arms in that block. The paired test then",
        "sees the language difference, not the",
        "noise. That is why the family is exact",
        f"permutation tests over {M['NRepeats']} pairs.",
    ], fill=GREEN_FILL, stroke=GREEN, rx=9, sw=1.6, title_color=GREEN_DEEP,
        body_size=12.5, pad=14, lh=17, gap=21)
    d.card(460, 212, 380, 160, "What pairing cannot cancel", [
        "A stall that hits only the high tail of",
        "one arm. p99 is computed from exactly",
        "those operations. The far tail is pooled",
        "across repeats, so it has no across-run",
        "interval and stays out of the family.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, rx=9, sw=1.6,
        title_color=AMBER_DEEP, body_size=12.5, pad=14, lh=17, gap=21)
    d.footer([
        "A load picked after seeing the sweep cannot enter the family. That "
        f"is why the tracking gap at {M['KneeGapLoad']} kops/s is shown and not tested.",
    ], y=476)
    return d


# --------------------------------------------------------------------------
def three_concurrency_words():
    d = Diagram(
        "52_three_concurrency_words", 880, 560,
        "Three words that are not synonyms",
        "Taking Rust drops one class of concurrency defect and leaves in "
        "place the class that fails in silence.",
    )
    d.card(16, 76, 272, 300, "Data race", [
        "Two threads, one location,",
        "no synchronisation, one write.",
        "",
        "Safe Rust: compile error",
        "(Send / Sync).",
        "C++: TSan, if the test hits it.",
        "",
        "This is inside the guarantee.",
        "H2 holds here.",
    ], fill=GREEN_FILL, stroke=GREEN, sw=1.8, rx=10, title_color=GREEN_DEEP,
        body_size=12.5, pad=14, lh=17, gap=22)
    d.card(304, 76, 272, 300, "Race condition", [
        "Each access is synced. The",
        "composed step is still not atomic.",
        "Example: lost update.",
        "",
        "The borrow checker is silent.",
        "TSan is silent. There is no",
        "unsynced access to find.",
        "",
        "Outside the guarantee.",
        "H2's looser reading fails here.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, sw=1.8, rx=10,
        title_color=AMBER_DEEP, body_size=12.5, pad=14, lh=17, gap=22)
    d.card(592, 76, 272, 300, "Lock-order deadlock", [
        "Two threads take two locks",
        "in opposite orders and wait.",
        "",
        "A Mutex guard whose life the",
        "borrow checker tracks well",
        "says nothing about order.",
        "",
        f"TSan hit {M['DeadlockTsanHits']} of "
        f"{M['DeadlockTsanRuns']} runs.",
        "Do not quote that rate from",
        "memory. It jumps.",
    ], fill=RED_FILL, stroke=RED, sw=1.8, rx=10, title_color=RED_DEEP,
        body_size=12.5, pad=14, lh=17, gap=22)

    d.rect(16, 396, 848, 104, GREY_FILL, GREY_EDGE, rx=9, sw=1.5)
    d.text(32, 420, "A plan that reads memory-safe as concurrency-safe", 13,
           NAVY, weight=700)
    d.lines(32, 440, [
        "would mis-budget its review effort. About a third of the non-deadlock",
        "concurrency bugs in Lu's field study broke the order the writers meant,",
        "not their locking. Static deadlock checks for Rust are still open research.",
    ], 12, BODY, lh=16)
    d.footer([
        "Leave the concurrency review budget where it is. That is guideline 3.",
    ], y=536)
    return d


# --------------------------------------------------------------------------
def checked_by_default():
    d = Diagram(
        "53_checked_by_default", 880, 520,
        "One case reached past the fault programs",
        "A spec gap let a call be sent outside the service running window. "
        "Every test missed it, because nothing ever called that path.",
    )
    d.card(16, 80, 200, 220, "1.  Spec gap", [
        "A call was legal in the",
        "written spec at a time",
        "the service was not",
        "running.",
        "",
        "Both versions inherited",
        "the hole. The method",
        "left each to fail in its",
        "own idiom.",
    ], fill=GREY_FILL, stroke=GREY_EDGE, sw=1.6, rx=10, title_color=NAVY,
        body_size=12, pad=14, lh=16, gap=20)
    d.card(232, 80, 200, 220, "2.  What missed it", [
        "Parity vectors.",
        "Generated campaign.",
        "ASan, TSan, UBSan.",
        "Miri.",
        "",
        "Nothing called that",
        "path, so nothing had",
        "a failure to report.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, sw=1.6, rx=10,
        title_color=AMBER_DEEP, body_size=12, pad=14, lh=16, gap=20)
    d.card(448, 80, 200, 220, "3.  What caught it", [
        "A plain bounds check",
        "on the Rust side.",
        "Undefined behaviour",
        "became a catchable",
        "failure.",
        "",
        "Not a proof.",
        "Checked by default.",
    ], fill=GREEN_FILL, stroke=GREEN, sw=1.6, rx=10, title_color=GREEN_DEEP,
        body_size=12, pad=14, lh=16, gap=20)
    d.card(664, 80, 200, 220, "4.  What to plan for", [
        "Do not budget as if",
        "compile time had ruled",
        "the hole out.",
        "",
        "A ban stated without a",
        "way behind it leaves",
        "each version to fail in",
        "its own idiom.",
    ], fill=BLUE_FILL, stroke=BLUE, sw=1.6, rx=10, title_color=BLUE_DEEP,
        body_size=12, pad=14, lh=16, gap=20)
    for x in (220, 436, 652):
        d.arrow(x, 190, x + 8, 190)

    d.rect(16, 324, 848, 128, RED_FILL, RED, rx=9, sw=1.6)
    d.text(32, 348, "The root cause belongs to the method", 13, RED_DEEP,
           weight=700)
    d.lines(32, 372, [
        "Parity bounds the paths the suite drives. A clean sanitiser result is "
        "bounded by the code that actually ran.",
        "RQ2's injected catalogue is still final for the fourteen programs. This "
        "case is why the thesis also talks about checked-by-default,",
        "not only ruled-out-at-compile-time.",
    ], 12.5, BODY, lh=18)
    d.footer([
        "Chapter 6, after the guarantee-boundary figure. It is part of the "
        "answer to RQ2, not a footnote.",
    ], y=496)
    return d


# --------------------------------------------------------------------------
def testbed_protocol():
    d = Diagram(
        "54_testbed_protocol", 880, 560,
        "What the measurement host does, and what it refuses",
        f"One socket, {M['MainCpu']}. The program runs on the machine "
        "itself, not inside a virtual machine.",
    )
    d.panel(16, 76, 420, 320, "DONE", GREEN_FILL, GREEN, header_h=34)
    y = 126
    for item in [
        f"SMT {M['MainSmt']}. One thread per core.",
        f"Governor {M['MainGovernor']}. Boost off.",
        "nohz_full on the pinned cores.",
        f"{M['MainPinnedCount']} pinned cores, 2 to 17.",
        "Clock held fixed.",
        "Rocky image pins gcc-toolset major.",
        f"g++ {M['MainGpp']}, rustc {M['MainRustc']}.",
    ]:
        d.chip(36, y, 380, 28, item, WHITE, GREEN_DEEP, size=12, rx=6,
               stroke=GREEN_EDGE)
        y += 34

    d.panel(452, 76, 412, 320, "REFUSED", RED_FILL, RED, header_h=34)
    d.card(470, 126, 376, 100, "isolcpus", [
        "It also stops the kernel sharing work",
        "across the allowed cores. Each test",
        "thread then lands on one core. An",
        "earlier campaign ran that way. Void.",
    ], fill=WHITE, stroke=RED_EDGE, rx=8, title_color=RED_DEEP,
        body_size=12, pad=12, lh=16, gap=18)
    d.card(470, 240, 376, 130, "A derived representative load", [
        "The old rule took the busiest load",
        "holding p99 under 5 ms. On the guest",
        "that was the host noise floor. On a",
        f"quiet host it climbs to the knee.",
        f"ReprLoad is pinned at {M['ReprLoad']} kops/s.",
    ], fill=WHITE, stroke=RED_EDGE, rx=8, title_color=RED_DEEP,
        body_size=12, pad=12, lh=16, gap=18)

    d.rect(16, 416, 848, 84, AMBER_FILL, AMBER_EDGE, rx=9, sw=1.6)
    d.text(32, 440, "The image still uses the kernel of the host it sits on",
           13, AMBER_DEEP, weight=700)
    d.lines(32, 460, [
        "So the guest sweep and the reported sweep differ in hardware, kernel,",
        "and one GCC 15 point release. Do not write that they share a toolchain.",
    ], 12, BODY, lh=16)
    d.footer([
        "bench/TESTBED.md is scripted and published. Executing the protocol "
        "and rerunning the same scripts is the only step between hosts.",
    ], y=536)
    return d


# --------------------------------------------------------------------------
def list_vs_built():
    d = Diagram(
        "55_list_vs_built", 880, 520,
        "A list of bug types is not a program that was built",
        "Meneely mapped CWE types onto what safe Rust would stop. This thesis "
        "asks the same question of programs that compile and run.",
    )
    d.card(16, 80, 400, 280, "Prior estimate (a list)", [
        "Take the Common Weakness Enumeration.",
        "Mark each type as one safe Rust would",
        "stop, or would not.",
        "Count real product bugs in 68 open-",
        "source C projects.",
        "",
        "58.2% sat in types that safe Rust would",
        "have made almost impossible.",
        "",
        "That share is a best case. It assumes",
        "the new code stays in safe Rust. A type",
        "counts as stopped if the mapping says so.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, sw=1.8, rx=10,
        title_color=AMBER_DEEP, body_size=12.5, pad=16, lh=17, gap=22)
    d.card(448, 80, 416, 280, "This thesis (programs)", [
        f"{M['FaultClasses']} small programs, two groups of seven.",
        "Each expectation recorded before the run.",
        "C++ built and run under three sanitisers.",
        "Safe Rust compiled, and run if it builds.",
        "",
        "The study can then say when the types",
        "still open are caught, and what it costs",
        "to catch them.",
        "",
        "That is why RQ2 is two-sided. A one-sided",
        "catalogue can only confirm the guarantee.",
    ], fill=GREEN_FILL, stroke=GREEN, sw=1.8, rx=10, title_color=GREEN_DEEP,
        body_size=12.5, pad=16, lh=17, gap=22)
    d.rect(16, 380, 848, 80, BLUE_FILL, BLUE, rx=9, sw=1.6)
    d.text(32, 404, "What this adds", 13, BLUE_DEEP, weight=700)
    d.text(32, 428, "Not a larger percentage. A stage and a cost for each "
                    "class that still compiles: sanitiser, model checker after "
                    "a rewrite, or undetected.", 12.5, BODY)
    d.footer([
        "Chapter 1, after the hypotheses. The 58.2% figure is theirs. Do not "
        "treat it as a result of this study.",
    ], y=496)
    return d


# --------------------------------------------------------------------------
def one_address_space():
    d = Diagram(
        "56_one_address_space", 880, 520,
        "Keeping unsafe at the seam bounds review, not corruption",
        "Host and part share one address space. A compile-time property of "
        "the Rust core bounds nothing at run time once a pointer has crossed.",
    )
    d.panel(16, 76, 260, 250, "C++ HOST", BLUE_FILL, BLUE, header_h=34)
    d.chip(36, 128, 220, 36, "opaque handle", BLUE_CHIP, BLUE_DEEP, size=13,
           rx=6, stroke=BLUE_EDGE)
    d.chip(36, 176, 220, 36, "status codes only", BLUE_CHIP, BLUE_DEEP,
           size=13, rx=6, stroke=BLUE_EDGE)
    d.chip(36, 224, 220, 36, "same process", BLUE_CHIP, BLUE_DEEP, size=13,
           rx=6, stroke=BLUE_EDGE)

    d.panel(310, 76, 260, 250, "SEAM  (unsafe lives here)", ORANGE_FILL,
            ORANGE, header_color=ORANGE_DEEP, header_h=34)
    d.chip(330, 128, 220, 36, f"{M['FfiEntryPoints']} C entry points",
           WHITE, ORANGE_DEEP, size=13, rx=6, stroke=ORANGE_EDGE)
    d.chip(330, 176, 220, 36, f"{M['FfiUnsafeFns']} unsafe functions",
           WHITE, ORANGE_DEEP, size=13, rx=6, stroke=ORANGE_EDGE)
    d.chip(330, 224, 220, 36, f"{M['FfiSeamLines']} lines of Rust",
           WHITE, ORANGE_DEEP, size=13, rx=6, stroke=ORANGE_EDGE)

    d.panel(604, 76, 260, 250, "RUST CORE", GREEN_FILL, GREEN, header_h=34)
    d.chip(624, 128, 220, 36, f"{M['CoreUnsafe']} unsafe sites", GREEN_CHIP,
           GREEN_DEEP, size=13, rx=6, stroke=GREEN_EDGE)
    d.chip(624, 176, 220, 36, "unchanged by the host", GREEN_CHIP, GREEN_DEEP,
           size=13, rx=6, stroke=GREEN_EDGE)
    d.chip(624, 224, 220, 36, "Send / Sync still apply", GREEN_CHIP,
           GREEN_DEEP, size=13, rx=6, stroke=GREEN_EDGE)

    d.arrow(280, 200, 306, 200, color=RED, sw=2.2)
    d.arrow(574, 200, 600, 200, color=RED, sw=2.2)
    d.text(440, 348, "one address space", 12, RED, weight=700, anchor="middle")

    d.rect(16, 372, 848, 88, RED_FILL, RED, rx=9, sw=1.6)
    d.text(32, 396, "What a vendor could misread", 13, RED_DEEP, weight=700)
    d.lines(32, 420, [
        "The RQ2 result is not a licence to describe a moved part as safe. "
        "The seam double-free is the in-guarantee class returning inside unsafe.",
        "Guideline 2 keeps the C ABI in its own crate so unsafe does not spread "
        "through crate chains. It does not sandbox the host.",
    ], 12, BODY, lh=18)
    d.footer([
        f"Per-call tax bounded at {M['FfiOpBoundPct']}% of a real signal call. "
        f"A do-nothing crossing bounds only itself.",
    ], y=496)
    return d


# --------------------------------------------------------------------------
def findings_one_page():
    d = Diagram(
        "57_findings_one_page", 880, 560,
        "What each research question returned",
        "The answer to RQ1 splits at saturation. RQ2 is final. RQ3 splits by "
        "resource. RQ4 is cheap in the machine.",
    )
    d.card(16, 76, 416, 200, "RQ1  Latency", [
        f"Below saturation: medians within {M['PFiftyRange']} us.",
        f"Paired gap {M['PFiftyDiffAbsMax']} us. Too small to bound.",
        f"Far tail: Rust lower by {M['FarTailLangSep']} us, pooled.",
        f"Rust tracks to {M['TrackingLoadRust']} kops/s, C++ to "
        f"{M['TrackingLoadCpp']}.",
        f"At {M['OverloadLoad']} kops/s, C++ finishes "
        f"{M['OverloadThrRatio']}x as much.",
        "Those two picks point at opposite sides.",
    ], fill=BLUE_FILL, stroke=BLUE, sw=1.7, rx=10, title_color=BLUE_DEEP,
        body_size=12, pad=14, lh=17, gap=21)
    d.card(448, 76, 416, 200, "RQ2  Defects", [
        f"All {M['FaultClassesPrevented']} in-guarantee classes: compile error.",
        f"All {M['FaultClassesBoundary']} boundary classes: compile and fail.",
        "On two of them C++ tools flag what Rust's do not.",
        "Rust drops data races and aliasing errors.",
        "It does not drop race conditions, lock order,",
        "leaks, wrapping, or a failed worker's blast.",
    ], fill=GREEN_FILL, stroke=GREEN, sw=1.7, rx=10, title_color=GREEN_DEEP,
        body_size=12, pad=14, lh=17, gap=21)
    d.card(16, 292, 416, 176, "RQ3  Resources", [
        f"Language RSS {M['RssLangDiffLo']} to {M['RssLangDiffHi']} MiB, all hosts.",
        f"Allocator {M['RssAllocDiffLo']} to {M['RssAllocDiffHi']} MiB, either language.",
        "Comparable on bare metal. Guest ratio does not travel.",
        f"CPU at {M['ReprLoad']} kops/s: Rust at most "
        f"{M['CpuDiffAbsMax']} pp less.",
        "CPU past saturation: sign flips. Do not mix the two.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, sw=1.7, rx=10,
        title_color=AMBER_DEEP, body_size=12, pad=14, lh=17, gap=21)
    d.card(448, 292, 416, 176, "RQ4  Adoption", [
        f"Seam: {M['FfiEntryPoints']} entries, "
        f"{M['FfiUnsafeFns']} unsafe functions.",
        f"Per-call bound {M['FfiOpBoundPct']}% of a real signal.",
        f"{M['BuildDepShareCpu']}% of the Rust build is crates.",
        "Size gap is a linkage policy. Order flips if matched.",
        "C++ leads the single-file edit and compile loop.",
    ], fill=ORANGE_FILL, stroke=ORANGE, sw=1.7, rx=10, title_color=ORANGE_DEEP,
        body_size=12, pad=14, lh=17, gap=21)
    d.footer([
        "Taken as a set these support a narrow claim, for stateful, concurrent, "
        "partitionable control-plane services of this kind.",
    ], y=536)
    return d


# --------------------------------------------------------------------------
def instrument_not_verdict():
    d = Diagram(
        "58_instrument_not_verdict", 880, 500,
        "What the thesis adds is an instrument, not a verdict",
        "At loads where the service still meets its sent rate, the choice is "
        "which defects a team will make impossible to write.",
    )
    items = [
        ("Frozen spec", "The main control against writer bias. Public. Both sides follow it."),
        ("Parity-tested pair", "Same paths, same seeds, a Python oracle, sanitisers on the path taken."),
        ("Harness past the knee", "Open-loop, interleaved, Holm family fixed before the campaign."),
        ("A split of the round-trip", "Says how much of what it times the language can own."),
        ("A defect catalogue", "Maps where the guarantee stops, with a stage and a cost."),
        ("A thin C-ABI seam", "Shows a C++ host can drive an unchanged Rust core."),
    ]
    y = 80
    n = 1
    for title, body in items:
        d.badge(40, y + 18, 14, str(n), fill=BLUE, color=WHITE, size=11)
        d.card(64, y, 796, 48, title, wrap(body, 88), fill=WHITE,
               stroke=BLUE_EDGE, rx=7, title_size=13, body_size=12,
               pad=10, gap=16, lh=14)
        y += 56
        n += 1
    d.footer([
        "Past the knee it is a speed choice as well. A nominal-load test "
        "would not have exposed the gap.",
    ], y=476)
    return d


# --------------------------------------------------------------------------
def guest_could_not_resolve():
    d = Diagram(
        "59_guest_could_not_resolve", 880, 520,
        "The guest could not resolve the far tail. Bare metal can.",
        "The earlier KVM sweep is kept so host-owned findings have a "
        "counter-example sitting beside them.",
    )
    d.card(16, 80, 416, 280, "KVM guest", [
        f"p99 noise on one arm: {M['GuestPNineNineMaxCI']} us.",
        f"Gap between all four arms: {M['GuestPNineNineRange']} us.",
        "Noise on one arm was larger than the",
        "gap between all four. The far tail could",
        "not be read.",
        "",
        f"g++ {M['GuestGpp']}. Same rustc.",
        "No core controls. Hypervisor in the way.",
        "Kept, not dropped. Same design, same code.",
    ], fill=AMBER_FILL, stroke=AMBER_EDGE, sw=1.8, rx=10,
        title_color=AMBER_DEEP, body_size=13, pad=16, lh=18, gap=22)
    d.card(448, 80, 416, 280, "Bare metal (reported)", [
        f"p99 noise on one arm: {M['PNineNineMaxCI']} us.",
        f"Gap between all four arms: {M['PNineNineRange']} us.",
        "Noise is smaller than the gap. Both p99",
        "rows and both p99.9 rows clear Holm,",
        f"{M['NTailSignificant']} rows in all.",
        "",
        f"Far tail pooled, {M['FarTailSamplesMin']} to "
        f"{M['FarTailSamplesMax']} calls.",
        f"Slowest Rust arm {M['FarTailLangSep']} us below fastest C++.",
        "A second bare-metal host agrees.",
    ], fill=GREEN_FILL, stroke=GREEN, sw=1.8, rx=10, title_color=GREEN_DEEP,
        body_size=13, pad=16, lh=18, gap=22)
    d.rect(16, 380, 848, 80, BLUE_FILL, BLUE, rx=9, sw=1.6)
    d.text(32, 404, "What this licences", 13, BLUE_DEEP, weight=700)
    d.lines(32, 424, [
        "Speed and RSS results name the host. RQ2 and the seam structure do not.",
        "Tail delay numbers from any single host are a thinner basis for a roll-out than they look.",
    ], 12.5, BODY, lh=16)
    d.footer([
        "That is why the earlier guest sweep is kept, not dropped. "
        "Chapter 6, ethical and professional reflection.",
    ], y=496)
    return d


# --------------------------------------------------------------------------
PAGES = [
    ("How to read Thesis_v3", how_to_read),
    ("Three trends", three_trends),
    ("Problem, RQs, hypotheses", problem_rqs_hs),
    ("Three methods", three_methods),
    ("Fairness controls", fairness_controls),
    ("Parity and the oracle", parity_oracle),
    ("Four variants", four_variants),
    ("Three campaigns", three_campaigns),
    ("Load regimes (RQ1)", load_regimes),
    ("What the clock measures", what_clock_measures),
    ("Holm family", holm_family),
    ("RQ2 catalogue", rq2_catalogue),
    ("Hypothesis verdicts", hypothesis_verdicts),
    ("RSS and CPU (RQ3)", rss_two_effects),
    ("Adoption axes (RQ4)", adoption_axes),
    ("Engineering guidelines", guidelines),
    ("Limits and next work", cannot_support),
    ("Claim register", claim_register),
    ("gNB two splits", ngran_two_splits),
    ("Open loop", open_loop),
    ("One request path", request_path),
    ("One interleaved repeat", one_repeat),
    ("Three concurrency words", three_concurrency_words),
    ("Checked by default", checked_by_default),
    ("Testbed protocol", testbed_protocol),
    ("List versus programs", list_vs_built),
    ("One address space", one_address_space),
    ("Findings one page", findings_one_page),
    ("Instrument, not verdict", instrument_not_verdict),
    ("Guest could not resolve", guest_could_not_resolve),
]


def write_gallery(built):
    """A browser page so the diagrams are pictures, not XML."""
    cards = []
    for i, (title, d) in enumerate(built, 1):
        cards.append(
            f'<section class="page" id="{escape(d.name)}">'
            f'<h2><span class="n">{i:02d}</span> {escape(title)}</h2>'
            f'<p class="file">{escape(d.name)}.png</p>'
            f'<img src="png/{escape(d.name)}.png" alt="{escape(title)}">'
            f"</section>"
        )
    nav = " ".join(
        f'<a href="#{escape(d.name)}">{i:02d}</a>'
        for i, (title, d) in enumerate(built, 1)
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thesis_v3 diagram review</title>
<style>
  :root {{
    --navy: #12233a;
    --body: #33475b;
    --muted: #5b6b7b;
    --line: #d7dde3;
    --chip: #eef3fa;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    color: var(--navy);
    background: #f7f9fb;
  }}
  header {{
    position: sticky;
    top: 0;
    z-index: 2;
    background: #fff;
    border-bottom: 1px solid var(--line);
    padding: 16px 24px 12px;
  }}
  h1 {{ margin: 0 0 6px; font-size: 22px; }}
  .lead {{ margin: 0 0 12px; color: var(--muted); font-size: 14px; }}
  nav {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }}
  nav a {{
    display: inline-block;
    padding: 4px 8px;
    background: var(--chip);
    color: var(--navy);
    text-decoration: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
  }}
  nav a:hover {{ background: #dce8f7; }}
  main {{ max-width: 960px; margin: 0 auto; padding: 16px 16px 64px; }}
  .page {{
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 16px;
    margin: 20px 0;
  }}
  h2 {{ margin: 0 0 4px; font-size: 18px; }}
  h2 .n {{ color: #2f6db3; margin-right: 8px; }}
  .file {{ margin: 0 0 12px; color: var(--muted); font-size: 12px; }}
  img {{
    width: 100%;
    height: auto;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #fff;
  }}
</style>
</head>
<body>
<header>
  <h1>Thesis_v3 diagram review</h1>
  <p class="lead">
    {len(built)} pages. Scroll, or use the numbers to jump.
    This pack is not in the PDF. The .drawio files are for editing.
  </p>
  <nav>{nav}</nav>
</header>
<main>
{"".join(cards)}
</main>
</body>
</html>
"""
    path = os.path.join(OUT, "index.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return path


def as_mxfile(pages):
    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<mxfile host="app.diagrams.net" agent="Thesis_v3 review pack" '
        'version="22.1.0" type="device">',
    ]
    for title, diag in pages:
        chunks.append(
            f'  <diagram id={quoteattr(diag.name)} name={quoteattr(title)}>'
        )
        chunks.append(diag.to_drawio().rstrip())
        chunks.append("  </diagram>")
    chunks.append("</mxfile>")
    return "\n".join(chunks) + "\n"


def style_offences(text):
    found = []
    if "\u2014" in text or "---" in text:
        found.append("em dash")
    if re.search(r"\s\u2013\s", text):
        found.append("spaced en dash")
    if ";" in text:
        found.append("semicolon")
    return found


def main():
    os.makedirs(OUT, exist_ok=True)
    png_dir = os.path.join(OUT, "png")
    os.makedirs(png_dir, exist_ok=True)

    built = []
    warnings = []
    hits = []
    for title, fn in PAGES:
        d = fn()
        svg_path = os.path.join(OUT, d.name + ".svg")
        dio_path = os.path.join(OUT, d.name + ".drawio")
        with open(svg_path, "w", encoding="utf-8") as fh:
            fh.write(d.to_svg())
        with open(dio_path, "w", encoding="utf-8") as fh:
            fh.write(d.to_drawio())
        built.append((title, d))
        warnings += d.warnings
        for kind in style_offences(d.to_svg()):
            hits.append(f"{d.name}: {kind}")
        print(f"built {d.name}: svg + drawio  ({d.w}x{d.h})")

    combined = os.path.join(OUT, "thesis_v3_review.drawio")
    with open(combined, "w", encoding="utf-8") as fh:
        fh.write(as_mxfile([(t, d) for t, d in built]))
    print(f"\ncombined {len(built)} pages -> {combined}")

    if warnings:
        print(f"\n{len(warnings)} line(s) may overflow their box:")
        for w in warnings:
            print("  " + w)
    if hits:
        print(f"\nFAIL style: {len(hits)} breach(es)", file=sys.stderr)
        for h in hits:
            print("  " + h, file=sys.stderr)
        return 1
    print("Review labels: no em dash, dash aside, or semicolon")

    try:
        import cairosvg
    except ImportError:
        print("cairosvg not installed, skipping PNG preview")
        return 0
    for title, d in built:
        svg_path = os.path.join(OUT, d.name + ".svg")
        png_path = os.path.join(png_dir, d.name + ".png")
        cairosvg.svg2png(url=svg_path, write_to=png_path, scale=2.0)
        print(f"rendered {d.name}.png")
    gallery = write_gallery(built)
    print(f"gallery -> {gallery}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
