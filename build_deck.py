#!/usr/bin/env python3
"""Build a Nokia-branded slide deck for the master's thesis.

Thesis: Performance, Safety, and Engineering Trade-offs of Rust and C++
        in Nokia RAN Control-Plane Systems (Ha Vien).

Uses the Nokia 2026 PPT toolkit v2.12 clean template. Light theme, PPT-native figures.
"""
import os
import sys

SKILL = os.path.expanduser("~/thesis.local/create-pptx-master-thesis")
sys.path.insert(0, os.path.join(SKILL, "scripts"))

from datetime import date
from pptx import Presentation
from pptx.util import Cm, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

from pptx_lib import fill_placeholder, remove_template_slides

TEMPLATE = os.path.join(SKILL, "references", "NokiaTemplate_v2.12_clean.pptx")
OUT = os.path.expanduser("~/thesis.local/Rust_vs_Cpp_Nokia_RAN_thesis.pptx")

# ---- Nokia palette ----
BLUE = RGBColor(0x00, 0x5A, 0xFF)
BLACKBLUE = RGBColor(0x00, 0x11, 0x35)
TEAL = RGBColor(0x23, 0xAB, 0xB6)
GREEN = RGBColor(0x37, 0xCC, 0x73)
AMBER = RGBColor(0xF7, 0xB7, 0x37)
ORANGE = RGBColor(0xF4, 0x7F, 0x31)
RED = RGBColor(0xE2, 0x3B, 0x3B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY300 = RGBColor(0xEB, 0xEB, 0xEB)
GRAY800 = RGBColor(0x66, 0x66, 0x66)
LIGHTBLUE = RGBColor(0xE6, 0xEE, 0xFF)
LIGHTGREEN = RGBColor(0xE3, 0xF7, 0xEA)
LIGHTAMBER = RGBColor(0xFD, 0xF2, 0xD9)

BODY_FONT = "Nokia Pure Text Light"
HEAD_FONT = "Nokia Pure Headline Light"

PRESENTER = "Ha Vien"
TITLE = ("Performance, Safety, and Engineering Trade-offs of Rust and C++ "
         "in Nokia RAN Control-Plane Systems")
DECK_DATE = date.today().strftime("%Y-%m-%d")

prs = Presentation(TEMPLATE)
prs.slide_width = Cm(25.4)
prs.slide_height = Cm(14.288)
if len(prs.slides._sldIdLst):
    remove_template_slides(prs)


def L(i):
    return prs.slide_layouts[i]


def _emu(v):
    return Emu(int(v.emu if hasattr(v, "emu") else v))


def set_body_bullets(slide, idx, items, size=16, color=BLACKBLUE):
    """Fill a body placeholder with bullet paragraphs (template supplies markers)."""
    tf = slide.placeholders[idx].text_frame
    tf.clear()
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if isinstance(it, tuple):
            text, lvl = it
        else:
            text, lvl = it, 0
        p.text = text
        p.level = lvl
        p.font.size = Pt(size if lvl == 0 else max(12, size - 2))
        p.font.name = BODY_FONT
        p.font.color.rgb = color
        p.space_after = Pt(6)
    return tf


def add_textbox(slide, left, top, width, height, text, size=14, color=BLACKBLUE,
                bold=False, align=PP_ALIGN.LEFT, font=BODY_FONT, anchor=None):
    tb = slide.shapes.add_textbox(_emu(left), _emu(top), _emu(width), _emu(height))
    tf = tb.text_frame
    tf.word_wrap = True
    if anchor is not None:
        tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font
    return tb


def add_box(slide, left, top, width, height, text, fill, line=None,
            font_color=WHITE, size=13, bold=True, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sp = slide.shapes.add_shape(shape, _emu(left), _emu(top), _emu(width), _emu(height))
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if line is not None:
        sp.line.color.rgb = line
        sp.line.width = Pt(1)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    tf = sp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = font_color
    p.font.name = BODY_FONT
    return sp


def add_arrow(slide, x1, y1, x2, y2, color=GRAY800, width=1.75):
    cn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, _emu(x1), _emu(y1),
                                    _emu(x2), _emu(y2))
    cn.line.color.rgb = color
    cn.line.width = Pt(width)
    ln = cn.line._get_or_add_ln()
    tail = ln.makeelement(qn('a:tailEnd'), {'type': 'triangle', 'w': 'med', 'len': 'med'})
    ln.append(tail)
    return cn


# =====================================================================
# Slide 1 — Front cover
# =====================================================================
s = prs.slides.add_slide(L(27))  # 3 N Blue green cover
s.shapes.title.text = "Rust vs. C++ for Nokia RAN control plane"
tf = s.placeholders[12].text_frame
tf.clear()
tf.paragraphs[0].text = PRESENTER
p2 = tf.add_paragraph()
p2.text = DECK_DATE
# match presenter font size for the date line
sz = tf.paragraphs[0].font.size
if sz is not None:
    p2.font.size = sz

# =====================================================================
# Slide 2 — Agenda
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "What this talk covers"
fill_placeholder(s, 10, "From the industrial problem to controlled evidence for Rust in the RAN")
set_body_bullets(s, 15, [
    "Context: the softwarizing RAN control plane and why memory safety matters",
    "Problem and four research questions (predictability, safety, overhead, migration)",
    "Method: two parity-tested implementations from one frozen specification",
    "Design: shared-nothing, thread-per-shard architecture and the UE lifecycle",
    "Results: safety, performance, and migration findings",
    "Conclusions and future work",
])

# =====================================================================
# Slide 3 — Motivation and industrial context
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "Cloud-native RAN raises the premium on software quality"
fill_placeholder(s, 10, "Two trends make a Rust-versus-C++ comparison timely for the control plane")
set_body_bullets(s, 15, [
    "The gNB-CU-CP is a large, stateful, highly concurrent control plane under millisecond budgets",
    "It runs on commodity servers, evolves continuously, and coordinates millions of connected devices",
    "C++ dominates for performance, but manual memory and concurrency management is error-prone",
    "Roughly 70% of serious security vulnerabilities at major vendors stem from memory-safety defects",
    "Policy now pushes vendors toward memory-safe languages, yet direct RAN evidence is missing",
    "This work is carried out at Nokia on a subsystem modeled on a real gNB-CU-CP component",
])

# =====================================================================
# Slide 4 — Problem statement
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "The gap: no controlled evidence for the RAN control plane"
fill_placeholder(s, 10, "Existing Rust-versus-C++ evidence is general-purpose and average-case")
set_body_bullets(s, 15, [
    "Can Rust match modern C++ in tail latency and predictability under overload, not just averages?",
    "Do Rust's compile-time guarantees actually eliminate the defect classes that afflict C++ code?",
    "What does incremental adoption cost inside a large existing C++ codebase?",
    "These three questions stay open for a representative, stateful, concurrent subsystem",
    "We answer them under controlled, reproducible conditions on a UE Context Management service",
])

# =====================================================================
# Slide 5 — Research questions (2 columns)
# =====================================================================
s = prs.slides.add_slide(L(4))  # 2 col bullets
s.shapes.title.text = "Four research questions"
fill_placeholder(s, 10, "Ordered to put predictability and migration ahead of raw average speed")
set_body_bullets(s, 15, [
    "RQ1 - Predictability",
    "Mean, p99, p99.9 tail latency and jitter under increasing load and overload",
    "RQ2 - Safety",
    "Which C++ defect classes are eliminated at compile time, and how are the rest caught?",
], size=16)
set_body_bullets(s, 16, [
    "RQ3 - Overhead",
    "Cost of Rust's safety model on throughput, CPU utilisation, and memory behaviour",
    "RQ4 - Migration",
    "Effort, FFI interoperability, and risk of adopting Rust incrementally within C++",
], size=16)

# =====================================================================
# Slide 6 — Methodology
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "One frozen spec, two implementations, three methods"
fill_placeholder(s, 10, "Empirical and constructive: build the artifact, then measure it fairly")
set_body_bullets(s, 15, [
    "A single language-agnostic specification is frozen before any code is written",
    "Modern C++ (C++23) and Rust versions share algorithms, concurrency model, allocator, and build flags",
    "RQ1/RQ3: deterministic load sweep to overload, matched HDR histograms, bootstrap confidence intervals",
    "RQ2: controlled fault injection of a five-defect catalogue against the Rust compiler",
    "RQ4: a working C++-to-Rust FFI prototype measuring seam size, unsafe scope, and per-call cost",
    "Fairness is a first-class concern; the spec is the primary control against implementation bias",
])

# =====================================================================
# Slide 7 — UE lifecycle state machine (figure only)
# =====================================================================
s = prs.slides.add_slide(L(1))  # figure/table headline
s.shapes.title.text = "The UE context lifecycle both versions encode identically"
fill_placeholder(s, 10, "Illegal transitions return a typed error instead of mutating state")

# boxes
by = Cm(5.2)
bh = Cm(1.5)
bw = Cm(4.4)
idle = add_box(s, Cm(1.6), by, bw, bh, "Idle", LIGHTBLUE, font_color=BLACKBLUE)
conn = add_box(s, Cm(8.3), by, bw, bh, "Connected", BLUE, font_color=WHITE)
reconf = add_box(s, Cm(15.0), by, bw, bh, "Reconfiguring", TEAL, font_color=WHITE)
rel = add_box(s, Cm(8.3), Cm(9.6), bw, bh, "Released", GRAY800, font_color=WHITE)

# Idle -> Connected
add_arrow(s, Cm(6.0), Cm(5.95), Cm(8.3), Cm(5.95), color=BLUE)
add_textbox(s, Cm(6.0), Cm(4.45), Cm(2.3), Cm(0.7), "setup", size=12, color=BLUE,
            bold=True, align=PP_ALIGN.CENTER)
# Connected -> Reconfiguring (upper)
add_arrow(s, Cm(12.7), Cm(5.55), Cm(15.0), Cm(5.55), color=TEAL)
add_textbox(s, Cm(12.7), Cm(4.35), Cm(2.3), Cm(0.7), "begin", size=12, color=TEAL,
            bold=True, align=PP_ALIGN.CENTER)
# Reconfiguring -> Connected (lower)
add_arrow(s, Cm(15.0), Cm(6.35), Cm(12.7), Cm(6.35), color=TEAL)
add_textbox(s, Cm(12.2), Cm(6.45), Cm(3.6), Cm(0.7), "complete / abort", size=11,
            color=TEAL, bold=True, align=PP_ALIGN.CENTER)
# Connected -> Released
add_arrow(s, Cm(10.5), Cm(6.7), Cm(10.5), Cm(9.6), color=GRAY800)
add_textbox(s, Cm(10.7), Cm(7.6), Cm(2.6), Cm(0.7), "release", size=12, color=GRAY800,
            bold=True, align=PP_ALIGN.LEFT)
# Idle -> Released (elbow along the left/bottom, clear of boxes)
add_arrow(s, Cm(3.8), Cm(6.7), Cm(3.8), Cm(10.35), color=GRAY800)
add_arrow(s, Cm(3.8), Cm(10.35), Cm(8.3), Cm(10.35), color=GRAY800)
add_textbox(s, Cm(4.0), Cm(8.2), Cm(3.0), Cm(0.7), "release", size=12, color=GRAY800,
            bold=True, align=PP_ALIGN.LEFT)
# in-place operations note on Connected (single line, arrow points down into the box)
add_textbox(s, Cm(7.0), Cm(3.5), Cm(7.0), Cm(0.7), "signal / add_drb handled in place",
            size=12, color=BLACKBLUE, bold=True, align=PP_ALIGN.CENTER)
add_arrow(s, Cm(10.5), Cm(4.3), Cm(10.5), Cm(5.15), color=BLACKBLUE, width=1.25)

# =====================================================================
# Slide 8 — Architecture (figure only)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "Shared-nothing, thread-per-shard architecture"
fill_placeholder(s, 10, "Blocking on a full queue is what makes overload observable as tail latency")

# producers group
add_box(s, Cm(1.4), Cm(4.4), Cm(4.3), Cm(4.6), "Load generators\n(producers)", LIGHTBLUE,
        font_color=BLACKBLUE, size=13)
# routing caption, placed in the clear band below the producer block
add_textbox(s, Cm(1.2), Cm(9.35), Cm(4.7), Cm(0.9), "requests routed by hash(ue_id)",
            size=11, color=GRAY800, bold=True, align=PP_ALIGN.CENTER)

lane_defs = [(Cm(4.55), "Shard 1", "Worker 1"), (Cm(9.35), "Shard N", "Worker N")]
qx, wx, sx = Cm(9.2), Cm(13.4), Cm(17.6)
qw, ww, sw = Cm(3.4), Cm(3.4), Cm(3.6)
bh2 = Cm(1.5)
for ly, sname, wname in lane_defs:
    add_box(s, qx, ly, qw, bh2, "MPSC queue", GRAY300, font_color=BLACKBLUE, size=12, bold=False)
    add_box(s, wx, ly, ww, bh2, wname, BLUE, font_color=WHITE, size=12)
    add_box(s, sx, ly, sw, bh2, sname, GREEN, font_color=WHITE, size=12,
            shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    ymid = ly + Cm(0.75)
    # producers -> queue
    add_arrow(s, Cm(5.7), Cm(6.7), qx, ymid, color=GRAY800)
    # queue -> worker
    add_arrow(s, qx + qw, ymid, wx, ymid, color=GRAY800)
    # worker -> shard (owns)
    add_arrow(s, wx + ww, ymid, sx, ymid, color=GRAY800)

add_textbox(s, Cm(9.2), Cm(3.35), Cm(12.0), Cm(0.7),
            "shard-owning threads: no shared mutable state, no locks", size=12,
            color=BLACKBLUE, bold=True, align=PP_ALIGN.CENTER)
# one-shot completion note
add_textbox(s, Cm(1.4), Cm(11.4), Cm(20.0), Cm(0.8),
            "One-shot completion: each worker writes the result back to the waiting producer",
            size=11, color=BLUE, bold=True, align=PP_ALIGN.CENTER)

# =====================================================================
# Slide 9 — Fairness baseline and implementation
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "Fairness by construction, then parity by testing"
fill_placeholder(s, 10, "Any measured difference should be the language, not the design")
set_body_bullets(s, 15, [
    "Frozen spec fixes the API, UE state machine, data structures, sharding, locking, and concurrency model",
    "Both link the same jemalloc allocator; Rust release is pinned to opt-level 2 to match C++ -O2",
    "Identical HDR histogram configuration and pinned SplitMix64 / FNV-1a hashing on both sides",
    "The Rust core contains no unsafe code; the C++ version is verified data-race free under ThreadSanitizer",
    "A language-neutral conformance suite diffs op-for-op transcripts; both implementations pass and agree",
])

# =====================================================================
# Slide 10 — Safety results (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "RQ2: every injected defect is a compile error in safe Rust"
fill_placeholder(s, 10, "g++ 13.3 with ASan/TSan versus rustc 1.96 (edition 2021)")

rows = [
    ("Defect class", "ASan", "TSan", "Rust outcome"),
    ("Use-after-free", "detected", "detected", "prevented (E0499)"),
    ("Double-free", "detected", "-", "prevented (E0382)"),
    ("Iterator invalidation", "detected", "detected", "prevented (E0502)"),
    ("Data race", "-", "detected", "prevented (E0373)"),
    ("Unguarded shared mutation", "-", "detected", "prevented (E0502)"),
]
tleft, ttop, twidth, theight = Cm(1.6), Cm(4.3), Cm(22.2), Cm(7.4)
gtbl = s.shapes.add_table(len(rows), 4, _emu(tleft), _emu(ttop), _emu(twidth), _emu(theight))
tbl = gtbl.table
tbl.columns[0].width = _emu(Cm(7.2))
tbl.columns[1].width = _emu(Cm(4.0))
tbl.columns[2].width = _emu(Cm(4.0))
tbl.columns[3].width = _emu(Cm(7.0))
for r, row in enumerate(rows):
    for c, val in enumerate(row):
        cell = tbl.cell(r, c)
        cell.margin_left = Cm(0.2)
        cell.margin_right = Cm(0.2)
        cell.margin_top = Cm(0.08)
        cell.margin_bottom = Cm(0.08)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = cell.text_frame.paragraphs[0]
        para.text = val
        para.font.name = BODY_FONT
        para.alignment = PP_ALIGN.LEFT if c in (0, 3) else PP_ALIGN.CENTER
        if r == 0:
            para.font.bold = True
            para.font.size = Pt(15)
            para.font.color.rgb = WHITE
            cell.fill.solid(); cell.fill.fore_color.rgb = BLUE
        else:
            para.font.size = Pt(14)
            para.font.color.rgb = BLACKBLUE
            if c == 3:
                cell.fill.solid(); cell.fill.fore_color.rgb = LIGHTGREEN
            elif c in (1, 2):
                if val == "detected":
                    cell.fill.solid(); cell.fill.fore_color.rgb = LIGHTAMBER
                else:
                    cell.fill.solid(); cell.fill.fore_color.rgb = GRAY300
            else:
                cell.fill.solid(); cell.fill.fore_color.rgb = WHITE

# =====================================================================
# Slide 11 — Performance results
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "RQ1/RQ3: the two languages track each other up to saturation"
fill_placeholder(s, 10, "Preliminary development-environment (WSL2) measurements; testbed figures pending")
set_body_bullets(s, 15, [
    "Medians (p50) agree to within a few microseconds across all four build variants",
    "p99 latencies lie within roughly 20% of one another below the overload cliff",
    "Languages diverge only in the far tail (p99.9 and max), where the allocator matters as much as the language",
    "Throughput follows the ideal line until saturation near 40-45 kops/s, then falls back as queues fill",
    "Peak RSS and CPU utilisation are comparable; jemalloc trades a few MiB of RSS for a shorter tail",
    "Bare-metal testbed numbers are the single most important remaining step for the tail claims",
])

# =====================================================================
# Slide 12 — Migration results (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "RQ4: incremental adoption is technically cheap"
fill_placeholder(s, 10, "A C++ host drives an unmodified Rust core across a thin C-ABI seam")

frows = [
    ("Metric", "Value"),
    ("C-ABI entry points", "12 (~230 lines of Rust)"),
    ("C header", "66 lines, no generated bindings"),
    ("unsafe in the core library", "none (confined to the seam crate)"),
    ("Per-call crossing cost", "sub-nanosecond (an indirect call)"),
    ("Relative to one signaling op", "about 5 orders of magnitude smaller"),
    ("Dominant adoption cost", "API design and the learning curve"),
]
tleft, ttop, twidth, theight = Cm(2.4), Cm(4.3), Cm(20.6), Cm(7.2)
gtbl = s.shapes.add_table(len(frows), 2, _emu(tleft), _emu(ttop), _emu(twidth), _emu(theight))
tbl = gtbl.table
tbl.columns[0].width = _emu(Cm(9.6))
tbl.columns[1].width = _emu(Cm(11.0))
for r, row in enumerate(frows):
    for c, val in enumerate(row):
        cell = tbl.cell(r, c)
        cell.margin_left = Cm(0.25)
        cell.margin_right = Cm(0.2)
        cell.margin_top = Cm(0.08)
        cell.margin_bottom = Cm(0.08)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = cell.text_frame.paragraphs[0]
        para.text = val
        para.font.name = BODY_FONT
        para.alignment = PP_ALIGN.LEFT
        if r == 0:
            para.font.bold = True
            para.font.size = Pt(15)
            para.font.color.rgb = WHITE
            cell.fill.solid(); cell.fill.fore_color.rgb = BLUE
        else:
            para.font.size = Pt(14)
            para.font.color.rgb = BLACKBLUE
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if r % 2 else GRAY300

# =====================================================================
# Slide 13 — Summary of findings (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "Summary of findings and evidence strength"
fill_placeholder(s, 10, "Safety and migration are final; performance is preliminary until the testbed run")

srows = [
    ("RQ", "Headline finding", "Evidence"),
    ("RQ1", "Rust and C++ track closely up to saturation; differences only in the far tail", "Preliminary"),
    ("RQ2", "All five injected C++ defect classes are prevented at compile time in safe Rust", "Final"),
    ("RQ3", "Peak RSS and CPU are comparable; allocator is a bigger lever than language", "Preliminary"),
    ("RQ4", "Thin, unsafe-isolated FFI seam with no measurable per-call tax", "Final"),
]
tleft, ttop, twidth, theight = Cm(1.6), Cm(4.3), Cm(22.2), Cm(7.0)
gtbl = s.shapes.add_table(len(srows), 3, _emu(tleft), _emu(ttop), _emu(twidth), _emu(theight))
tbl = gtbl.table
tbl.columns[0].width = _emu(Cm(2.4))
tbl.columns[1].width = _emu(Cm(15.6))
tbl.columns[2].width = _emu(Cm(4.2))
for r, row in enumerate(srows):
    for c, val in enumerate(row):
        cell = tbl.cell(r, c)
        cell.margin_left = Cm(0.25)
        cell.margin_right = Cm(0.2)
        cell.margin_top = Cm(0.1)
        cell.margin_bottom = Cm(0.1)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = cell.text_frame.paragraphs[0]
        para.text = val
        para.font.name = BODY_FONT
        para.alignment = PP_ALIGN.LEFT if c == 1 else PP_ALIGN.CENTER
        if r == 0:
            para.font.bold = True
            para.font.size = Pt(15)
            para.font.color.rgb = WHITE
            cell.fill.solid(); cell.fill.fore_color.rgb = BLUE
        else:
            para.font.size = Pt(14)
            para.font.color.rgb = BLACKBLUE
            cell.fill.solid()
            if c == 2:
                cell.fill.fore_color.rgb = LIGHTGREEN if val == "Final" else LIGHTAMBER
            else:
                cell.fill.fore_color.rgb = WHITE if r % 2 else GRAY300

# =====================================================================
# Slide 14 — Conclusions
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "The barrier to Rust here is people, not performance"
fill_placeholder(s, 10, "Three conclusions from a parity-tested C++ and Rust pair")
set_body_bullets(s, 15, [
    "Safety is a difference of kind: safe Rust rejects all five defect classes at compile time",
    "Migration cost is dominated by API design and the learning curve, not run-time overhead",
    "Performance is equivalent in the operationally relevant region below saturation",
    "The deliverables: a frozen spec, two implementations, a benchmarking framework, and a defect taxonomy",
    "Confirming the tail behaviour on a bare-metal testbed is the main remaining step",
])

# =====================================================================
# Slide 15 — Future work
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "Future work"
fill_placeholder(s, 10, "Extending the evidence beyond a single synthetic subsystem")
set_body_bullets(s, 15, [
    "Replay captured, anonymised production traces instead of a synthetic workload",
    "Scale the comparison to more control-plane subsystems and to the data-heavy L2/PHY path",
    "Evaluate Rust async runtimes against the thread-per-shard model used here",
    "Run a longer-term migration case study tracking defect density and review effort in production",
])

# =====================================================================
# Slide 16 — End slide
# =====================================================================
prs.slides.add_slide(L(71))  # End slide Blue

prs.save(OUT)
print("Saved", OUT, "with", len(prs.slides._sldIdLst), "slides")
