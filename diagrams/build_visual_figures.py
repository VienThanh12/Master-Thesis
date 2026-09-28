#!/usr/bin/env python3
"""Visual-first review figures for Thesis_v4.

Short labels only. No paragraph cards. Numbers from generated macros.

Usage:  .venv-pptx/bin/python diagrams/build_visual_figures.py
"""

from __future__ import annotations

import os
import re
import sys
from xml.sax.saxutils import quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from dsl import (  # noqa: E402
    AMBER, AMBER_CHIP, AMBER_DEEP, AMBER_EDGE, AMBER_FILL,
    BLUE, BLUE_CHIP, BLUE_DEEP, BLUE_EDGE, BLUE_FILL,
    BODY, FAINT, GREY_EDGE, GREY_FILL,
    GREEN, GREEN_CHIP, GREEN_DEEP, GREEN_EDGE, GREEN_FILL,
    MUTED, NAVY, ORANGE, ORANGE_DEEP, ORANGE_FILL,
    RED, RED_CHIP, RED_DEEP, RED_EDGE, RED_FILL,
    WHITE, Diagram,
)

FIGURES = os.path.join(HERE, os.pardir, "figures")
OUT = os.path.join(HERE, "review", "visual")
MACRO_FILES = (
    "gen_macros.tex", "gen_artefacts.tex", "gen_adoption.tex",
    "gen_complexity.tex", "gen_baremetal.tex", "gen_guest.tex",
)


def load_macros():
    values = {}
    for name in MACRO_FILES:
        with open(os.path.join(FIGURES, name), encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$", line)
                if m:
                    values[m.group(1)] = (
                        m.group(2).replace(r"\,", ",").replace(r"\%", "%")
                        .replace(r"\_", "_")
                    )
    return values


M = load_macros()


def flow(d, x, y, items, fill, color, stroke, h=44, gap=18, size=13):
    cx = x
    for i, (label, w) in enumerate(items):
        d.chip(cx, y, w, h, label, fill, color, size=size, weight=700, rx=8,
               stroke=stroke)
        if i < len(items) - 1:
            mid = y + h / 2
            d.arrow(cx + w + 2, mid, cx + w + gap - 2, mid, color=color, sw=2)
        cx += w + gap
    return cx


def bar(d, x, y, w, h, fill, stroke, label, color, size=12):
    d.rect(x, y, max(w, 4), h, fill, stroke, rx=4, sw=1.4)
    d.text(x + max(w, 4) + 10, y + h * 0.7, label, size, color, weight=700)


# --------------------------------------------------------------------------
def ngran():
    d = Diagram("F01_ngran", 880, 300, "Where UECM sits")
    d.chip(20, 100, 90, 64, "UE", GREY_FILL, NAVY, size=16, weight=700, rx=10,
           stroke=GREY_EDGE)
    d.chip(150, 100, 110, 64, "gNB-DU", BLUE_CHIP, BLUE_DEEP, size=16,
           weight=700, rx=10, stroke=BLUE)
    d.arrow(114, 132, 146, 132)

    d.rect(300, 72, 340, 140, GREY_FILL, GREY_EDGE, rx=12, sw=1.5, dashed=True)
    d.text(470, 94, "gNB-CU", 12, FAINT, weight=700, anchor="middle")
    d.chip(320, 108, 300, 44, "gNB-CU-CP   UECM", BLUE_FILL, BLUE_DEEP,
           size=15, weight=700, rx=8, stroke=BLUE)
    d.chip(320, 158, 300, 36, "gNB-CU-UP", GREEN_FILL, GREEN_DEEP, size=14,
           rx=8, stroke=GREEN_EDGE)

    d.chip(680, 100, 180, 64, "5G Core", GREY_FILL, NAVY, size=16, weight=700,
           rx=10, stroke=GREY_EDGE)
    d.arrow(264, 132, 296, 132)
    d.arrow(644, 132, 676, 132)
    d.text(132, 182, "Uu", 12, MUTED, anchor="middle")
    d.text(280, 182, "F1", 12, MUTED, anchor="middle")
    d.text(662, 182, "NG", 12, MUTED, anchor="middle")
    d.text(470, 228, "E1", 12, MUTED, anchor="middle")
    d.text(440, 276, "This thesis measures UECM only", 13, BODY,
           anchor="middle")
    return d


# --------------------------------------------------------------------------
def fsm():
    d = Diagram("F02_state_machine", 880, 310, "UE context lifecycle")
    d.badge(120, 120, 42, "Idle", fill=BLUE, color=WHITE, size=13)
    d.badge(360, 130, 48, "Conn.", fill=BLUE, color=WHITE, size=13)
    d.badge(640, 130, 48, "Reconf.", fill=BLUE, color=WHITE, size=12)
    d.badge(360, 240, 44, "Rel.", fill="#6b7c8d", color=WHITE, size=13)
    d.arrow(166, 120, 308, 130)
    d.text(230, 108, "setup", 12, MUTED, anchor="middle")
    d.arrow(412, 118, 588, 118)
    d.text(500, 106, "begin", 12, MUTED, anchor="middle")
    d.arrow(588, 146, 412, 146)
    d.text(500, 168, "complete / abort", 12, MUTED, anchor="middle")
    d.text(360, 68, "signal / add DRB", 12, MUTED, anchor="middle")
    d.arrow(360, 182, 360, 194)
    d.text(378, 200, "release", 12, MUTED)
    d.elbow([(120, 164), (120, 240), (312, 240)], color=BLUE, sw=2)
    d.text(160, 228, "release", 12, MUTED)
    return d


# --------------------------------------------------------------------------
def shards():
    d = Diagram("F03_shards", 880, 340, "Shared-nothing, thread per shard")
    d.chip(20, 88, 130, 40, "Producer 1", BLUE_CHIP, BLUE_DEEP, size=13,
           rx=8, stroke=BLUE)
    d.chip(20, 140, 130, 40, "Producer 2", BLUE_CHIP, BLUE_DEEP, size=13,
           rx=8, stroke=BLUE)
    d.chip(20, 192, 130, 40, "Producer m", BLUE_CHIP, BLUE_DEEP, size=13,
           rx=8, stroke=BLUE)
    d.arrow(154, 108, 196, 116)
    d.arrow(154, 160, 196, 160)
    d.arrow(154, 212, 196, 204)
    d.text(175, 76, "hash", 11, MUTED, anchor="middle")

    d.rect(200, 80, 640, 70, WHITE, GREY_EDGE, rx=10, sw=1.5, dashed=True)
    d.chip(220, 96, 150, 40, "MPSC queue", GREY_FILL, NAVY, size=13, rx=8,
           stroke=GREY_EDGE)
    d.arrow(374, 116, 404, 116)
    d.chip(410, 96, 150, 40, "Worker 1", RED_FILL, RED_DEEP, size=13, rx=8,
           stroke=RED)
    d.arrow(564, 116, 594, 116)
    d.chip(600, 96, 150, 40, "Shard 1", GREEN_FILL, GREEN_DEEP, size=13, rx=8,
           stroke=GREEN)

    d.rect(200, 168, 640, 70, WHITE, GREY_EDGE, rx=10, sw=1.5, dashed=True)
    d.chip(220, 184, 150, 40, "MPSC queue", GREY_FILL, NAVY, size=13, rx=8,
           stroke=GREY_EDGE)
    d.arrow(374, 204, 404, 204)
    d.chip(410, 184, 150, 40, "Worker n", RED_FILL, RED_DEEP, size=13, rx=8,
           stroke=RED)
    d.arrow(564, 204, 594, 204)
    d.chip(600, 184, 150, 40, "Shard n", GREEN_FILL, GREEN_DEEP, size=13, rx=8,
           stroke=GREEN)

    d.elbow([(675, 228), (675, 292), (85, 292), (85, 236)], color=AMBER_DEEP,
            sw=1.8, dashed=True)
    d.text(380, 308, "one-shot reply", 12, AMBER_DEEP, anchor="middle")
    return d


# --------------------------------------------------------------------------
def request_flow():
    d = Diagram("F04_request_path", 880, 220, "One request")
    flow(d, 16, 90, [
        ("Producer", 140),
        ("Queue", 130),
        ("Worker", 130),
        ("Shard map", 150),
        ("Reply", 130),
    ], BLUE_FILL, BLUE_DEEP, BLUE, h=52, gap=22, size=14)
    d.text(86, 168, "submit", 11, MUTED, anchor="middle")
    d.text(270, 168, "FIFO", 11, MUTED, anchor="middle")
    d.text(450, 168, "owns", 11, MUTED, anchor="middle")
    d.text(660, 168, "one-shot", 11, MUTED, anchor="middle")
    d.text(440, 200, "No lock on context state", 13, BODY, anchor="middle")
    return d


# --------------------------------------------------------------------------
def workloads():
    d = Diagram("F05_workloads", 880, 260, "Two workloads")
    d.rect(16, 72, 848, 80, BLUE_FILL, BLUE_EDGE, rx=10, sw=1.5)
    d.text(36, 96, "signal", 16, BLUE_DEEP, weight=700)
    flow(d, 130, 88, [("signal", 110)] * 5, BLUE_CHIP, BLUE_DEEP, BLUE_EDGE,
         h=36, gap=14, size=13)

    d.rect(16, 164, 848, 80, GREEN_FILL, GREEN_EDGE, rx=10, sw=1.5)
    d.text(36, 188, "mixed", 16, GREEN_DEEP, weight=700)
    flow(d, 120, 180, [
        ("create", 86), ("setup", 86), ("signal", 86), ("DRB", 70),
        ("reconf.", 86), ("release", 86),
    ], GREEN_CHIP, GREEN_DEEP, GREEN_EDGE, h=36, gap=12, size=12)
    return d


# --------------------------------------------------------------------------
def four_arms():
    d = Diagram("F06_four_arms", 880, 280, "Four variants, interleaved")
    d.text(250, 88, "jemalloc", 13, FAINT, weight=700, anchor="middle")
    d.text(630, 88, "system (control)", 13, FAINT, weight=700, anchor="middle")
    d.text(40, 140, "C++", 16, BLUE_DEEP, weight=700, anchor="middle")
    d.text(40, 210, "Rust", 16, GREEN_DEEP, weight=700, anchor="middle")
    d.chip(90, 118, 320, 48, "C++  +  jemalloc", BLUE_FILL, BLUE_DEEP,
           size=16, weight=700, rx=10, stroke=BLUE)
    d.chip(470, 118, 320, 48, "C++  +  system", BLUE_CHIP, BLUE_DEEP,
           size=16, weight=700, rx=10, stroke=BLUE_EDGE)
    d.chip(90, 188, 320, 48, "Rust  +  jemalloc", GREEN_FILL, GREEN_DEEP,
           size=16, weight=700, rx=10, stroke=GREEN)
    d.chip(470, 188, 320, 48, "Rust  +  system", GREEN_CHIP, GREEN_DEEP,
           size=16, weight=700, rx=10, stroke=GREEN_EDGE)
    d.text(440, 256, f"{M['NRepeats']} repeats, four variants back to back", 13,
           BODY, anchor="middle")
    return d


# --------------------------------------------------------------------------
def open_loop():
    d = Diagram("F07_open_loop", 880, 280, "Open loop keeps sending")
    d.text(40, 100, "closed", 14, RED_DEEP, weight=700)
    for i in range(4):
        d.rect(130 + i * 28, 88, 10, 28, RED, rx=2)
    d.rect(250, 96, 220, 12, RED_CHIP, rx=2)
    d.text(360, 88, "stall, sender idle", 12, RED_DEEP, anchor="middle")
    for i in range(3):
        d.rect(490 + i * 28, 88, 10, 28, RED, rx=2)

    d.text(40, 180, "open", 14, GREEN_DEEP, weight=700)
    for i in range(18):
        d.rect(130 + i * 36, 168, 10, 28, GREEN, rx=2)
    d.rect(250, 204, 220, 8, GREEN_CHIP, rx=2)
    d.text(360, 232, "stall still occupies its slots", 12, GREEN_DEEP,
           anchor="middle")
    d.text(440, 262, "Queue blocks when full. No drop rule.", 13, BODY,
           anchor="middle")
    return d


# --------------------------------------------------------------------------
def load_map():
    d = Diagram("F08_load_map", 880, 340, "Load regimes")
    # axis
    d.rect(40, 140, 800, 18, GREY_FILL, rx=9)
    d.rect(40, 140, 280, 18, GREEN, rx=9)
    d.rect(320, 140, 140, 18, BLUE, rx=0)
    d.rect(460, 140, 160, 18, AMBER, rx=0)
    d.rect(620, 140, 220, 18, RED, rx=9)

    ticks = [
        (80, f"{M['ReprLoad']}", GREEN_DEEP),
        (360, f"{M['TrackingLoadCpp']}", BLUE_DEEP),
        (520, f"{M['TrackingLoadRust']}", AMBER_DEEP),
        (760, f"{M['OverloadLoad']}", RED_DEEP),
    ]
    for x, lab, color in ticks:
        d.rect(x - 1, 136, 3, 26, color)
        d.text(x, 128, lab, 12, color, weight=700, anchor="middle")

    d.chip(50, 180, 200, 36, "below saturation", GREEN_CHIP, GREEN_DEEP,
           size=13, rx=8, stroke=GREEN_EDGE)
    d.chip(300, 180, 160, 36, "C++ knee", BLUE_CHIP, BLUE_DEEP, size=13,
           rx=8, stroke=BLUE)
    d.chip(470, 180, 150, 36, "shown, not tested", AMBER_CHIP, AMBER_DEEP,
           size=12, rx=8, stroke=AMBER_EDGE)
    d.chip(640, 180, 180, 36, "overload flip", RED_CHIP, RED_DEEP, size=13,
           rx=8, stroke=RED)

    d.text(40, 248, "kops/s finished", 12, FAINT)
    if "KneeGapLoad" in M:
        d.text(40, 278, f"at {M['KneeGapLoad']} (shown)", 12, AMBER_DEEP)
        bar(d, 220, 264, 180, 18, GREEN, GREEN, f"Rust  {M['KneeGapThrFast']}",
            GREEN_DEEP)
        slow = float(M["KneeGapThrSlow"]) / max(float(M["KneeGapThrFast"]), 1.0)
        bar(d, 220, 288, 180 * slow, 18, BLUE, BLUE,
            f"C++  {M['KneeGapThrSlow']}", BLUE_DEEP)
    else:
        d.text(40, 278, f"at {M['KneeSplitLoad']} (shown)", 12, AMBER_DEEP)
        bar(d, 220, 264, 180, 18, AMBER, AMBER,
            f"jemalloc  {M['KneeSplitMedKeep']}", AMBER_DEEP)
        slow = float(M["KneeSplitMedDrop"]) / max(float(M["KneeSplitMedKeep"]), 1.0)
        bar(d, 220, 288, 180 * slow, 18, AMBER, AMBER,
            f"system  {M['KneeSplitMedDrop']}", AMBER_DEEP)

    d.text(500, 278, f"at {M['OverloadLoad']} (tested)", 12, RED_DEEP)
    bar(d, 680, 264, 110, 18, BLUE, BLUE, f"C++  {M['OverloadThrCpp']}",
        BLUE_DEEP)
    bar(d, 680, 288, 64, 18, GREEN, GREEN, f"Rust  {M['OverloadThrRust']}",
        GREEN_DEEP)
    return d


# --------------------------------------------------------------------------
def budget():
    d = Diagram("F09_budget", 880, 280, "What the end-to-end clock times")
    d.text(40, 100, "true scale", 13, NAVY, weight=700)
    d.rect(160, 86, 6, 22, GREEN, rx=2)
    d.rect(168, 86, 670, 22, BLUE, rx=2)
    d.text(180, 76, f"language  {M['BudgetCoreShareMax']}%", 12, GREEN_DEEP,
           weight=700)
    d.text(500, 76, f"handoff  {M['BudgetCoreShareRest']}%", 12, BLUE_DEEP,
           weight=700)

    d.text(40, 168, "core only", 13, NAVY, weight=700)
    rust_w = 200
    cpp_w = int(200 * float(M["BudgetCoreRatio"]))
    d.text(160, 156, "Rust", 12, GREEN_DEEP)
    d.rect(210, 142, rust_w, 20, GREEN, rx=4)
    d.text(160, 188, "C++", 12, BLUE_DEEP)
    d.rect(210, 174, cpp_w, 20, BLUE, rx=4)
    d.text(210 + cpp_w + 12, 190,
           f"Rust {M['BudgetCoreRatio']}x faster", 13, GREEN_DEEP, weight=700)
    d.text(440, 248, "That clock cannot bound a language effect", 14, BODY,
           anchor="middle")
    return d


# --------------------------------------------------------------------------
def rq2_chips():
    d = Diagram("F10_rq2", 880, 360, "Where the guarantee stops")
    d.panel(16, 72, 416, 250, "Safe Rust rejects", GREEN_FILL, GREEN,
            header_h=32, header_size=14)
    inside = [
        "Use-after-free", "Double-free", "Iterator invalidation",
        "Data race", "Unguarded mutation", "Use-after-move",
        "Unsafe handle shared",
    ]
    y = 118
    for name in inside:
        d.chip(36, y, 376, 24, name, GREEN_CHIP, GREEN_DEEP, size=12, rx=6,
               stroke=GREEN_EDGE)
        y += 28

    d.panel(448, 72, 416, 250, "Both still miss", RED_FILL, RED,
            header_h=32, header_size=14)
    outside = [
        "Lock-order deadlock", "Lost update", "Ref-cycle leak",
        "Integer overflow", "Worker blast radius", "Forgotten guard",
        "Seam double-free (unsafe)",
    ]
    y = 118
    for name in outside:
        d.chip(468, y, 376, 24, name, RED_CHIP, RED_DEEP, size=12, rx=6,
               stroke=RED_EDGE)
        y += 28
    d.text(440, 344, "Seven and seven. Seam is a rewrite, not a new class.",
           13, BODY, anchor="middle")
    return d


# --------------------------------------------------------------------------
def ffi():
    d = Diagram("F11_ffi", 880, 260, "C++ host, thin seam, unchanged core")
    d.panel(20, 72, 250, 130, "C++ host", BLUE_FILL, BLUE, header_h=32)
    d.chip(40, 118, 210, 28, "opaque handle", BLUE_CHIP, BLUE_DEEP, size=13,
           rx=6, stroke=BLUE_EDGE)
    d.chip(40, 154, 210, 28, f"{M['FfiEntryPoints']} C entry points",
           BLUE_CHIP, BLUE_DEEP, size=13, rx=6, stroke=BLUE_EDGE)

    d.panel(310, 72, 250, 130, "seam", ORANGE_FILL, ORANGE,
            header_color=ORANGE_DEEP, header_h=32)
    d.chip(330, 118, 210, 28, f"{M['FfiUnsafeFns']} unsafe fns", RED_CHIP,
           RED_DEEP, size=13, weight=700, rx=6, stroke=RED_EDGE)
    d.chip(330, 154, 210, 28, f"{M['FfiSeamLines']} lines", WHITE,
           ORANGE_DEEP, size=13, rx=6, stroke=AMBER_EDGE)

    d.panel(600, 72, 260, 130, "Rust core", GREEN_FILL, GREEN, header_h=32)
    d.chip(620, 118, 220, 28, f"{M['CoreUnsafe']} unsafe", GREEN_CHIP,
           GREEN_DEEP, size=13, weight=700, rx=6, stroke=GREEN_EDGE)
    d.chip(620, 154, 220, 28, "unmodified", GREEN_CHIP, GREEN_DEEP, size=13,
           rx=6, stroke=GREEN_EDGE)

    d.arrow(274, 136, 306, 136, color=NAVY, sw=2)
    d.arrow(564, 136, 596, 136, color=NAVY, sw=2)
    d.text(440, 230, f"same signal: {M['FfiOpNative']} us native, "
                     f"{M['FfiOpSeam']} us through the seam", 13, BODY,
           anchor="middle")
    return d


# --------------------------------------------------------------------------
def interleave():
    d = Diagram("F12_interleave", 880, 220,
                f"One repeat, {M['NVariants']} variants back to back")
    colors = [
        (BLUE_FILL, BLUE, "C++ je"),
        (BLUE_CHIP, BLUE_EDGE, "C++ sys"),
        (GREEN_FILL, GREEN, "Rust je"),
        (GREEN_CHIP, GREEN_EDGE, "Rust sys"),
    ]
    x = 40
    for fill, stroke, lab in colors:
        d.chip(x, 90, 180, 56, lab, fill, NAVY, size=15, weight=700, rx=10,
               stroke=stroke)
        x += 200
        if x < 800:
            d.arrow(x - 18, 118, x - 4, 118, color=NAVY, sw=2)
    d.text(440, 180, "Host noise is shared by the block", 14, BODY,
           anchor="middle")
    return d


# --------------------------------------------------------------------------
def findings():
    d = Diagram("F13_findings", 880, 280, "The four answers, at a glance")
    cells = [
        (16, BLUE, BLUE_FILL, BLUE_DEEP, "RQ1",
         f"{M['PFiftyDiffAbsMax']} us", "median gap, too small"),
        (232, GREEN, GREEN_FILL, GREEN_DEEP, "RQ2",
         f"{M['FaultClassesPrevented']} / {M['FaultClassesBoundary']}",
         "compile error / still open"),
        (448, AMBER_EDGE, AMBER_FILL, AMBER_DEEP, "RQ3",
         f"{M['RssLangDiffLo']}–{M['RssLangDiffHi']} MiB",
         "Rust RSS, all hosts"),
        (664, ORANGE, ORANGE_FILL, ORANGE_DEEP, "RQ4",
         f"{M['FfiOpBoundPct']}%", "bound on a real call"),
    ]
    for x, stroke, fill, deep, rq, value, note in cells:
        d.rect(x, 80, 200, 160, fill, stroke, rx=12, sw=1.8)
        d.text(x + 100, 110, rq, 14, deep, weight=700, anchor="middle")
        d.text(x + 100, 160, value, 22, NAVY, weight=700, anchor="middle")
        d.text(x + 100, 198, note, 12, MUTED, anchor="middle")
    return d


# --------------------------------------------------------------------------
def concurrency():
    d = Diagram("F14_concurrency", 880, 260, "Three words, not synonyms")
    d.rect(16, 80, 272, 140, GREEN_FILL, GREEN, rx=12, sw=1.8)
    d.text(152, 118, "data race", 16, GREEN_DEEP, weight=700, anchor="middle")
    d.text(152, 150, "compile error", 14, GREEN_DEEP, anchor="middle")
    d.text(152, 178, "Send / Sync", 13, MUTED, anchor="middle")

    d.rect(304, 80, 272, 140, AMBER_FILL, AMBER_EDGE, rx=12, sw=1.8)
    d.text(440, 118, "race condition", 16, AMBER_DEEP, weight=700,
           anchor="middle")
    d.text(440, 150, "lost update", 14, AMBER_DEEP, anchor="middle")
    d.text(440, 178, "tools silent", 13, MUTED, anchor="middle")

    d.rect(592, 80, 272, 140, RED_FILL, RED, rx=12, sw=1.8)
    d.text(728, 118, "deadlock", 16, RED_DEEP, weight=700, anchor="middle")
    d.text(728, 150, "lock order", 14, RED_DEEP, anchor="middle")
    d.text(728, 178, "outside the guarantee", 13, MUTED, anchor="middle")
    return d


# --------------------------------------------------------------------------
def hypotheses():
    d = Diagram("F15_hypotheses", 880, 240, "How the hypotheses came out")
    d.rect(16, 80, 272, 120, AMBER_FILL, AMBER_EDGE, rx=12, sw=1.8)
    d.text(152, 112, "H1", 18, AMBER_DEEP, weight=700, anchor="middle")
    d.text(152, 144, "median yes", 14, NAVY, anchor="middle")
    d.text(152, 170, "overload unnamed", 13, MUTED, anchor="middle")

    d.rect(304, 80, 272, 120, GREEN_FILL, GREEN, rx=12, sw=1.8)
    d.text(440, 112, "H2", 18, GREEN_DEEP, weight=700, anchor="middle")
    d.text(440, 144, "seven of seven", 14, NAVY, anchor="middle")
    d.text(440, 170, "not concurrency at large", 13, MUTED, anchor="middle")

    d.rect(592, 80, 272, 120, BLUE_FILL, BLUE, rx=12, sw=1.8)
    d.text(728, 112, "H3", 18, BLUE_DEEP, weight=700, anchor="middle")
    d.text(728, 144, f"bound {M['FfiOpBoundPct']}%", 14, NAVY, anchor="middle")
    d.text(728, 170, "cost is people", 13, MUTED, anchor="middle")
    return d


# --------------------------------------------------------------------------
def rss_bars():
    d = Diagram("F16_rss", 880, 280, "Two RSS effects")
    lang = float(M["RssLangDiffHi"])
    alloc = float(M["RssAllocDiffHi"])
    guest_over = float(M["GuestRssAllocOverLang"])
    px = 48
    d.text(40, 110, "bare metal", 13, NAVY, weight=700)
    d.text(40, 148, "language", 12, GREEN_DEEP)
    d.rect(150, 132, lang * px, 22, GREEN, rx=4)
    d.text(150 + lang * px + 10, 148, f"{M['RssLangDiffLo']} to {M['RssLangDiffHi']} MiB",
           12, GREEN_DEEP, weight=700)
    d.text(40, 186, "allocator", 12, BLUE_DEEP)
    d.rect(150, 170, alloc * px, 22, BLUE, rx=4)
    d.text(150 + alloc * px + 10, 186, f"{M['RssAllocDiffLo']} to {M['RssAllocDiffHi']} MiB",
           12, BLUE_DEEP, weight=700)

    d.text(40, 236, "guest alloc / language", 13, AMBER_DEEP, weight=700)
    d.rect(150, 220, min(guest_over * 18, 520), 22, AMBER, rx=4)
    d.text(150 + min(guest_over * 18, 520) + 10, 236, f"{M['GuestRssAllocOverLang']}x",
           14, AMBER_DEEP, weight=700)
    d.text(440, 268, "Never quote the ratio without naming a host", 13, BODY,
           anchor="middle")
    return d


PAGES = [
    ("Where UECM sits", ngran),
    ("UE context lifecycle", fsm),
    ("Shared-nothing shards", shards),
    ("One request", request_flow),
    ("Two workloads", workloads),
    ("Four variants", four_arms),
    ("Open loop", open_loop),
    ("Load regimes", load_map),
    ("What the clock times", budget),
    ("Where the guarantee stops", rq2_chips),
    ("FFI seam", ffi),
    ("Interleaved repeat", interleave),
    ("Four answers", findings),
    ("Three concurrency words", concurrency),
    ("Hypothesis verdicts", hypotheses),
    ("Two RSS effects", rss_bars),
]


def style_offences(text):
    found = []
    if "\u2014" in text or "---" in text:
        found.append("em dash")
    if re.search(r"\s\u2013\s", text):
        found.append("spaced en dash")
    if ";" in text:
        found.append("semicolon")
    return found


def write_gallery(built):
    cards = []
    for i, (title, diag) in enumerate(built, 1):
        cards.append(
            f'<section class="page" id="{diag.name}">'
            f"<h2>{i:02d}  {title}</h2>"
            f'<img src="{diag.name}.png" alt="{title}">'
            "</section>"
        )
    nav = " ".join(
        f'<a href="#{diag.name}">{i:02d}</a>'
        for i, (_, diag) in enumerate(built, 1)
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Thesis_v4 figures</title>
<style>
  body {{ margin: 0; font-family: "Segoe UI", Arial, sans-serif;
         background: #f7f9fb; color: #12233a; }}
  header {{ position: sticky; top: 0; background: #fff;
            border-bottom: 1px solid #d7dde3; padding: 14px 20px; }}
  h1 {{ margin: 0 0 8px; font-size: 20px; }}
  .lead {{ margin: 0 0 10px; color: #5b6b7b; font-size: 14px; }}
  nav a {{ display: inline-block; margin: 0 4px 4px 0; padding: 4px 8px;
           background: #eef3fa; border-radius: 6px; text-decoration: none;
           color: #1c4e86; font-weight: 700; font-size: 12px; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 12px 16px 48px; }}
  .page {{ background: #fff; border: 1px solid #d7dde3; border-radius: 12px;
           padding: 12px; margin: 16px 0; }}
  h2 {{ margin: 0 0 10px; font-size: 16px; }}
  img {{ width: 100%; height: auto; }}
</style>
</head>
<body>
<header>
  <h1>Thesis_v4 figures</h1>
  <p class="lead">Pictures, not paragraphs. Open this file in a browser.</p>
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


def as_mxfile(built):
    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<mxfile host="app.diagrams.net" agent="Thesis_v4 visual figures" '
        'version="22.1.0" type="device">',
    ]
    for title, diag in built:
        chunks.append(f'  <diagram id={quoteattr(diag.name)} name={quoteattr(title)}>')
        chunks.append(diag.to_drawio().rstrip())
        chunks.append("  </diagram>")
    chunks.append("</mxfile>")
    return "\n".join(chunks) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    built = []
    warnings, hits = [], []
    for title, fn in PAGES:
        diag = fn()
        with open(os.path.join(OUT, diag.name + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(diag.to_svg())
        with open(os.path.join(OUT, diag.name + ".drawio"), "w", encoding="utf-8") as fh:
            fh.write(diag.to_drawio())
        built.append((title, diag))
        warnings += diag.warnings
        for kind in style_offences(diag.to_svg()):
            hits.append(f"{diag.name}: {kind}")
        print(f"built {diag.name} ({diag.w}x{diag.h})")

    with open(os.path.join(OUT, "thesis_v4_figures.drawio"), "w", encoding="utf-8") as fh:
        fh.write(as_mxfile(built))

    if warnings:
        print(f"\n{len(warnings)} overflow warning(s):")
        for w in warnings:
            print("  " + w)
    if hits:
        print("FAIL style", file=sys.stderr)
        for h in hits:
            print("  " + h, file=sys.stderr)
        return 1
    print("Labels: no em dash, dash aside, or semicolon")

    import cairosvg
    for title, diag in built:
        cairosvg.svg2png(
            url=os.path.join(OUT, diag.name + ".svg"),
            write_to=os.path.join(OUT, diag.name + ".png"),
            scale=2.0,
        )
        print(f"rendered {diag.name}.png")
    print("gallery ->", write_gallery(built))
    return 0


if __name__ == "__main__":
    sys.exit(main())
