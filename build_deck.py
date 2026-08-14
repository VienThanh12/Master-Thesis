#!/usr/bin/env python3
"""Build a Nokia-branded slide deck for the master's thesis.

Thesis: Performance, Safety, and Engineering Trade-offs of Rust and C++
        in Nokia RAN Control-Plane Systems (Ha Vien).

Uses the Nokia 2026 PPT toolkit v2.12 clean template. Light theme, PPT-native figures.

Every measured number on these slides is read at build time from the artefacts that
bench/refresh_thesis.sh regenerates: figures/gen_macros.tex, figures/gen_complexity.tex,
the figures/tab_*.tex table bodies the thesis itself \\input, faults/results/taxonomy.csv,
and the newest bench/results/env-*.txt environment capture. Nothing is transcribed, so a
rerun of the campaign cannot leave the deck contradicting the thesis. A macro the deck
asks for and the data does not provide is a hard error rather than a stale literal.
"""
import csv
import glob
import os
import re
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

ROOT = os.path.expanduser("~/thesis.local")
FIGURES = os.path.join(ROOT, "figures")
TEMPLATE = os.path.join(SKILL, "references", "NokiaTemplate_v2.12_clean.pptx")
OUT = os.path.join(ROOT, "Rust_vs_Cpp_Nokia_RAN_thesis.pptx")

REFRESH_HINT = "run bench/refresh_thesis.sh to regenerate it"

# =====================================================================
# Generated data: macros, table bodies, taxonomy, environment capture
# =====================================================================

_MACRO_RE = re.compile(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$")
_MCI_RE = re.compile(r"\\mci\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}")
_TEX_CMD_RE = re.compile(r"\\(?:texttt|emph|textbf|rlap|mathrm)\{([^}]*)\}")


def detex(s):
    """Strip the LaTeX the generated tables carry into plain slide text."""
    s = s.strip()
    s = re.sub(r"\\\\\s*$", "", s)
    s = re.sub(r"\\multicolumn\{[^}]*\}\{[^}]*\}\{([^}]*)\}", r"\1", s)
    s = _TEX_CMD_RE.sub(r"\1", s)
    s = s.replace("\\textmu s", "\u00b5s").replace("\\textmu", "\u00b5")
    s = s.replace("\\%", "%").replace("\\,", " ").replace("\\quad", "   ")
    s = s.replace("\\_", "_").replace("\\&", "&")
    s = s.replace("$", "").replace("---", "\u2014").replace("--", "\u2013")
    return re.sub(r"\s+", " ", s).strip()


def read_macros(*paths):
    """Parse \\newcommand definitions from the generated macro files."""
    macros = {}
    for path in paths:
        if not os.path.exists(path):
            raise SystemExit(f"missing {os.path.relpath(path, ROOT)}: {REFRESH_HINT}")
        with open(path) as f:
            for line in f:
                m = _MACRO_RE.match(line.strip())
                if m:
                    macros[m.group(1)] = detex(m.group(2))
    return macros


MACROS = read_macros(os.path.join(FIGURES, "gen_macros.tex"),
                     os.path.join(FIGURES, "gen_complexity.tex"))


def M(name):
    """A generated macro, or a hard error naming what is missing.

    Failing loudly is the point: a silently absent number is how the previous
    deck came to contradict the thesis it was summarising.
    """
    try:
        return MACROS[name]
    except KeyError:
        raise SystemExit(
            f"macro \\{name} is not in figures/gen_macros.tex; {REFRESH_HINT}") from None


def read_table(stem):
    """Read a generated tab_*.tex body into rows of cells.

    A \\mci{median}{lo}{hi} cell becomes a ``(median, "[lo, hi]")`` pair, which
    add_data_table renders as the median above its interval, exactly as the
    thesis tables print it. Every other cell is de-TeXed to plain text.
    """
    path = os.path.join(FIGURES, f"{stem}.tex")
    if not os.path.exists(path):
        raise SystemExit(f"missing figures/{stem}.tex: {REFRESH_HINT}")
    rows = []
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("\\hline"):
                continue
            cells = []
            for cell in re.sub(r"\\\\\s*$", "", line).split("&"):
                mci = _MCI_RE.search(cell)
                if mci:
                    med, lo, hi = (v.strip() for v in mci.groups())
                    cells.append((med, f"[{lo}, {hi}]"))
                else:
                    cells.append(detex(cell))
            rows.append(cells)
    if not rows:
        raise SystemExit(f"figures/{stem}.tex is empty: {REFRESH_HINT}")
    return rows


#: How the fault-injection runner spells an outcome, and how a slide should.
#: "clean" means the sanitiser ran and reported nothing, which is the point of
#: the row, so it is spelled out rather than left as a dash.
_SANITISER_LABEL = {"detected": "detected", "clean": "no report", "hung": "hung"}

#: Display name and UECM incarnation per catalogue entry, keyed on the identifier
#: faults/results/taxonomy.csv uses. Both the catalogue slide and the results
#: slide read this, so they cannot come to disagree about a class.
DEFECTS = {
    "use_after_free": ("Use-after-free",
                       "A signaling message dereferences a context a concurrent release already erased"),
    "double_free": ("Double-free",
                    "A non-idempotent release runs twice for the same UE"),
    "iterator_invalidation": ("Iterator invalidation",
                              "A data-radio-bearer list is mutated while being iterated"),
    "data_race": ("Data race",
                  "Two workers update the same context field without synchronisation"),
    "unguarded_shared_mutation": ("Unguarded shared mutation",
                                  "A context shared across threads is mutated without a lock"),
    "lock_order_deadlock": ("Lock-order deadlock",
                            "Two procedures take the same two shard locks in opposite orders"),
    "lost_update": ("Lost update",
                    "A counter's read-modify-write is split across two critical sections"),
}


def read_taxonomy():
    """Read the fault-injection outcomes, in-guarantee classes first.

    The two boundary classes are carried through with a flag rather than
    dropped: a catalogue showing only what Rust prevents would confirm its own
    premise, and RQ2 is written so that it cannot.
    """
    path = os.path.join(ROOT, "faults", "results", "taxonomy.csv")
    if not os.path.exists(path):
        raise SystemExit("missing faults/results/taxonomy.csv: run faults/run_faults.sh")
    rows = []
    with open(path) as f:
        for rec in csv.DictReader(f):
            key = rec["defect"].strip()
            if key not in DEFECTS:
                raise SystemExit(
                    f"defect class {key!r} is in the taxonomy but has no name and UECM "
                    "incarnation in build_deck.py: add it to DEFECTS")
            name, incarnation = DEFECTS[key]
            rust = rec["rust_compile"].replace("compile-time prevented", "prevented")
            rust = re.sub(r"not prevented \(compiles; (.*)\)", r"not prevented (\1)", rust)
            rows.append({
                "defect": name,
                "incarnation": incarnation,
                "asan": _SANITISER_LABEL.get(rec["cpp_asan"].strip(), rec["cpp_asan"]),
                "tsan": _SANITISER_LABEL.get(rec["cpp_tsan"].strip(), rec["cpp_tsan"]),
                "rust": rust.replace(",", ", "),
                "boundary": rec["rust_expected"].strip() == "not-prevented",
            })
    return rows


def read_env():
    """Extract host facts from the newest environment capture.

    The capture is written beside every campaign, so the testbed slide states
    the machine the reported numbers came from rather than a remembered one.
    """
    caps = sorted(glob.glob(os.path.join(ROOT, "bench", "results", "env-*.txt")))
    if not caps:
        raise SystemExit("no bench/results/env-*.txt capture: run bench/campaign.sh")
    env = {"_path": caps[-1]}
    patterns = {
        "distro": r"^distro:\s*(.+)$",
        "gpp": r"^(g\+\+ \(GCC\) \S+)",
        "rustc": r"^(rustc \S+)",
        "cpu_model": r"^Model name:\s*(.+)$",
        "cpus": r"^CPU\(s\):\s*(\d+)",
        "sockets": r"^Socket\(s\):\s*(\d+)",
        "numa": r"^NUMA node\(s\):\s*(\d+)",
        "smt": r"^smt/control:\s*(.+)$",
        "virt": r"^virtualisation:\s*(.+)$",
        "isolcpus": r"^isolcpus:\s*(.+)$",
        "nohz": r"^nohz_full:\s*(.+)$",
        "governor": r"^governors:\s*(.+)$",
    }
    with open(caps[-1]) as f:
        for line in f:
            line = line.strip()
            for key, pat in patterns.items():
                if key not in env:
                    m = re.match(pat, line)
                    if m:
                        env[key] = m.group(1).strip()
    with open(caps[-1]) as f:
        kernel = re.search(r"^Linux \S+ (\S+)", f.read(), re.M)
    env["kernel"] = kernel.group(1) if kernel else "unknown"
    return env


LATENCY = read_table("tab_latency")
RESOURCE = read_table("tab_resource")
OVERLOAD = read_table("tab_overload")
BUDGET = read_table("tab_budget")
CONTENTION = read_table("tab_contention")
FFI = read_table("tab_ffi")
TAXONOMY = read_taxonomy()
ENV = read_env()

IN_GUARANTEE = [d for d in TAXONOMY if not d["boundary"]]
BOUNDARY = [d for d in TAXONOMY if d["boundary"]]

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
LIGHTRED = RGBColor(0xFC, 0xE6, 0xE6)

BODY_FONT = "Nokia Pure Text Light"
HEAD_FONT = "Nokia Pure Headline Light"

# Template content bounds (see create-pptx-master-thesis/scripts/pptx_lib.py):
# manually placed shapes must start below the header band and end above the footer.
SLIDE_W_CM = 25.4
SLIDE_H_CM = 14.288
TOP_MARGIN_CM = 2.94
BOTTOM_MARGIN_CM = 1.2

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


def add_caption(slide, top, text, size=12, color=GRAY800, height=None):
    """A reading note under a table, in the gray the template uses for asides.

    The height defaults to whatever remains above the template's bottom margin,
    so a caption is never given a box that ends below the footer.
    """
    if height is None:
        height = Cm(SLIDE_H_CM - BOTTOM_MARGIN_CM) - _emu(top)
    return add_textbox(slide, Cm(1.3), top, Cm(22.8), height, text, size=size, color=color)


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


def add_data_table(slide, rows, col_widths_cm, left=Cm(1.3), top=Cm(4.0),
                   height=None, aligns=None, header_fill=BLUE,
                   header_size=14, body_size=13, sub_size=9, cell_fill=None,
                   row_height_cm=None):
    """Generic table helper. `rows` is a list of tuples (row 0 = header).

    A body cell may be a plain value or a ``(main, sub)`` pair; the pair renders
    the second element beneath the first in smaller gray type, which is how the
    thesis prints a median above its confidence interval.

    `col_widths_cm` is a list of column widths in cm (their sum is the table
    width). `aligns` is an optional per-column PP_ALIGN list applied to every
    row. `cell_fill(r, c, main)` may return an RGBColor to override the default
    zebra striping for a body cell (return None to fall back to striping).
    """
    ncols = len(col_widths_cm)
    if height is None:
        if row_height_cm is None:
            two_line = any(isinstance(v, tuple) for row in rows[1:] for v in row)
            row_height_cm = 0.95 if two_line else 0.68
        height = Cm(len(rows) * row_height_cm)
    total_w = Cm(sum(col_widths_cm))
    gtbl = slide.shapes.add_table(len(rows), ncols, _emu(left), _emu(top),
                                  _emu(total_w), _emu(height))
    tbl = gtbl.table
    tbl.first_row = False
    tbl.horz_banding = False
    for c, w in enumerate(col_widths_cm):
        tbl.columns[c].width = _emu(Cm(w))
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            main, sub = val if isinstance(val, tuple) else (val, None)
            cell = tbl.cell(r, c)
            cell.margin_left = Cm(0.2)
            cell.margin_right = Cm(0.15)
            cell.margin_top = Cm(0.06)
            cell.margin_bottom = Cm(0.06)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            para = cell.text_frame.paragraphs[0]
            para.text = str(main)
            para.font.name = BODY_FONT
            para.alignment = aligns[c] if aligns else PP_ALIGN.LEFT
            if r == 0:
                para.font.bold = True
                para.font.size = Pt(header_size)
                para.font.color.rgb = WHITE
                cell.fill.solid(); cell.fill.fore_color.rgb = header_fill
                continue
            para.font.size = Pt(body_size)
            para.font.color.rgb = BLACKBLUE
            if sub:
                sp = cell.text_frame.add_paragraph()
                sp.text = str(sub)
                sp.font.name = BODY_FONT
                sp.font.size = Pt(sub_size)
                sp.font.color.rgb = GRAY800
                sp.alignment = aligns[c] if aligns else PP_ALIGN.LEFT
            fill = cell_fill(r, c, main) if cell_fill else None
            if fill is None:
                fill = WHITE if (r % 2 == 1) else GRAY300
            cell.fill.solid(); cell.fill.fore_color.rgb = fill
    return gtbl, top + height


# =====================================================================
# Slide 1: Front cover
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
# Slide 2: Agenda
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "What this talk covers"
fill_placeholder(s, 10, "From the industrial problem to controlled evidence for Rust in the RAN")
set_body_bullets(s, 15, [
    "Context: the softwarizing RAN control plane and why memory safety matters",
    "Problem and four research questions (predictability, safety, overhead, migration)",
    "Method: two parity-tested implementations from one frozen specification",
    "Design: shared-nothing, thread-per-shard architecture and the UE lifecycle",
    "Evidence: what the host can carry, and how the comparison is tested",
    "Results: safety, the latency budget, overload, resources, and migration",
    "Conclusions, open questions, and future work",
])

# =====================================================================
# Slide 3: Motivation and industrial context
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
# Slide 4: Problem statement and the gap
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "The gap: no controlled evidence for the RAN control plane"
fill_placeholder(s, 10, "In the closest prior work the language varies together with the runtime")
set_body_bullets(s, 15, [
    "Can Rust match modern C++ in tail latency and predictability under overload, not just averages?",
    "Do Rust's compile-time guarantees actually eliminate the defect classes that afflict C++ code?",
    "What does incremental adoption cost inside a large existing C++ codebase?",
    "Two vendor RAN theses reach this domain, but vary runtime and concurrency model with the language",
    "So a measured difference cannot be attributed to the language rather than the framework on it",
    "The contribution is the control: hold spec, algorithms, and concurrency model fixed, then sweep past saturation",
])

# =====================================================================
# Slide 5: Key terms and abbreviations (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "Key terms for readers outside telecom"
fill_placeholder(s, 10, "The vocabulary that recurs throughout the talk")
add_data_table(
    s,
    [
        ("Term", "Meaning"),
        ("gNB-CU-CP", "Control-plane part of the 5G base-station central unit"),
        ("UECM", "UE Context Management: the per-UE state subsystem studied here"),
        ("Tail latency", "High-percentile latency (p99, p99.9), the worst-case metric"),
        ("Saturation", "The load beyond which the service stops meeting the offered rate"),
        ("RRC", "Radio Resource Control, the UE-to-gNB signaling protocol"),
        ("DRB", "Data Radio Bearer, a per-UE user-plane data channel"),
        ("FFI", "Foreign Function Interface: calling Rust from C++ over a C ABI"),
        ("HDR histogram", "High-Dynamic-Range histogram for accurate latency capture"),
    ],
    col_widths_cm=[5.0, 18.0],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=0.82,
)

# =====================================================================
# Slide 6: Four research questions (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "Four research questions"
fill_placeholder(s, 10, "Ordered to put predictability and migration ahead of raw average speed")
add_data_table(
    s,
    [
        ("RQ", "Focus", "Question"),
        ("RQ1", "Predictability", "Mean, p99, p99.9 tail latency and jitter under load and overload"),
        ("RQ2", "Safety", "Which C++ defect classes are eliminated at compile time, and how are the rest caught?"),
        ("RQ3", "Overhead", "Cost of Rust's safety model on throughput, CPU utilisation, and memory"),
        ("RQ4", "Migration", "Effort, FFI interoperability, and risk of adopting Rust incrementally within C++"),
    ],
    col_widths_cm=[2.4, 5.0, 15.6],
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=1.1,
    cell_fill=lambda r, c, v: LIGHTBLUE if c == 0 else None,
)

# =====================================================================
# Slide 7: Methodology
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "One frozen spec, two implementations, four measurements"
fill_placeholder(s, 10, "Empirical and constructive: build the artifact, then measure it fairly")
set_body_bullets(s, 15, [
    "A single language-agnostic specification is frozen before any code is written",
    "Modern C++ (C++23) and Rust share algorithms, concurrency model, allocator, and build flags",
    f"RQ1/RQ3: load sweep to overload, {M('NRepeats')} interleaved repeats, matched HDR histograms",
    "RQ1/RQ3: the operation is also measured apart from the cross-thread handoff that delivers it",
    f"RQ2: fault injection of {len(TAXONOMY)} defect classes, {len(IN_GUARANTEE)} inside Rust's guarantee and {len(BOUNDARY)} deliberately outside it",
    "RQ4: a C++-to-Rust FFI prototype measuring seam size, unsafe scope, and per-call cost",
])

# =====================================================================
# Slide 8: Research design (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "How each research question is answered"
fill_placeholder(s, 10, "Every question is tied to a method, an artifact, and a primary metric")
add_data_table(
    s,
    [
        ("RQ", "Method", "Artifact / data", "Primary metric"),
        ("RQ1", "Load sweep to overload, interleaved repeats", "Benchmark harness; latency histograms", "p99/p99.9 tail latency and jitter vs. load"),
        ("RQ3", "Same sweep, resource capture", "getrusage samples per run", "peak RSS, CPU utilisation, throughput"),
        ("RQ1, RQ3", "Component decomposition: core direct, then through the service", "Matched microbenchmark pair", "operation cost vs. cross-thread handoff"),
        ("RQ1", "Contended primitives in isolation", "Queue + completion microbenchmark", "sustained throughput under contention"),
        ("RQ2", "Controlled fault injection", "Defect catalogue; ASan/TSan and rustc logs", "defect-class taxonomy"),
        ("RQ4", "FFI migration prototype", "C++ host + Rust C-ABI seam", "seam size, unsafe scope, per-call cost"),
    ],
    col_widths_cm=[2.6, 6.4, 6.4, 7.8],
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=1.16,
    body_size=11,
    cell_fill=lambda r, c, v: LIGHTBLUE if c == 0 else None,
)

# =====================================================================
# Slide 9: UE lifecycle state machine (figure only)
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
add_textbox(s, Cm(12.1), Cm(6.9), Cm(3.5), Cm(0.7), "complete / abort", size=11,
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
# Slide 10: Architecture (figure only)
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
# Slide 11: Fairness controls (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "Fairness by construction: what is held identical"
fill_placeholder(s, 10, "Any measured difference should be the language, not the design")
add_data_table(
    s,
    [
        ("Level", "Held identical across C++ and Rust"),
        ("Specification", "API, UE state machine, data structures, sharding, locking, concurrency model"),
        ("Runtime substrate", "Same jemalloc allocator, system allocator kept as a control; Rust opt-level 2 matched to C++ -O2"),
        ("Hashing", "Pinned SplitMix64 shard split and FNV-1a keying, bit-verified equal"),
        ("Measurement", f"Identical HDR histogram config; {M('NVariants')} variants interleaved within each of {M('NRepeats')} repeats"),
        ("Behaviour", "Language-neutral conformance suite; canonical transcripts diffed operation by operation"),
        ("Deviations", "Unavoidable language differences logged in a forced-idiom record"),
    ],
    col_widths_cm=[5.0, 18.0],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=1.0,
)

# =====================================================================
# Slide 12: Language-forced idioms (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "Where the two languages must diverge"
fill_placeholder(s, 10, "The forced-idiom log: same requirement, idiomatic in each language")
_, tbl_bottom = add_data_table(
    s,
    [
        ("Concern", "Modern C++ (C++23)", "Rust (stable)"),
        ("Result type", "std::expected<T, OpError>", "Result<T, OpError>"),
        ("Request", "tagged struct, every argument field (160 B)", "enum, one variant per operation (96 B)"),
        ("Response", "std::variant of four result types", "each variant carries a sender of its own type"),
        ("Bounded queue", "hand-written mutex + two condition variables", "sync_channel(capacity)"),
        ("One-shot completion", "std::promise / std::future", "a fresh mpsc::channel() per request"),
        ("Per-shard map", "std::unordered_map (node-based)", "HashMap (open-addressed)"),
    ],
    col_widths_cm=[4.6, 9.2, 9.2],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=0.93,
    body_size=12,
)
add_caption(s, tbl_bottom + Cm(0.3), size=11, text=
            f"Rust is {M('NlocRise')}% longer in code lines ({M('RustNloc')} against {M('CppNloc')} NLOC) "
            f"but {M('CcnTotalDrop')}% lower in total cyclomatic complexity ({M('RustCcnTotal')} against "
            f"{M('CppCcnTotal')}). The C++ {M('CppCcnMaxFn')} scores {M('CppCcnMax')} against Rust's worst "
            f"of {M('RustCcnMax')}: the extra lines buy back branching where review is hardest.")

# =====================================================================
# Slide 13: Defect classes in UECM (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "The catalogue spans both sides of Rust's guarantee"
fill_placeholder(s, 10, f"{len(IN_GUARANTEE)} classes Rust claims to prevent, and {len(BOUNDARY)} chosen because it does not")
_, tbl_bottom = add_data_table(
    s,
    [("Defect class", "Incarnation in UE Context Management")] +
    [(d["defect"], d["incarnation"]) for d in TAXONOMY],
    col_widths_cm=[5.8, 17.2],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=0.86,
    cell_fill=lambda r, c, v: LIGHTRED if r > len(IN_GUARANTEE) else None,
)
add_caption(s, tbl_bottom + Cm(0.3),
            "The last two rows are the boundary group. A catalogue containing only defects Rust "
            "prevents would confirm its own premise, so RQ2 is built to be able to fail.")

# =====================================================================
# Slide 14: Safety results (table, generated from the taxonomy)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "RQ2: a difference of kind, with a definite edge"
fill_placeholder(s, 10, f"{ENV.get('gpp', 'g++')} with ASan/TSan versus {ENV.get('rustc', 'rustc')}")


def _taxonomy_fill(r, c, v):
    if r > len(IN_GUARANTEE):
        return LIGHTRED
    if c == 3:
        return LIGHTGREEN
    if c in (1, 2):
        return LIGHTAMBER if v == "detected" else GRAY300
    return WHITE


_, tbl_bottom = add_data_table(
    s,
    [("Defect class", "ASan", "TSan", "Rust outcome")] +
    [(d["defect"], d["asan"], d["tsan"], d["rust"]) for d in TAXONOMY],
    col_widths_cm=[6.0, 3.4, 3.4, 10.4],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT],
    row_height_cm=0.86,
    body_size=12,
    cell_fill=_taxonomy_fill,
)
add_caption(s, tbl_bottom + Cm(0.28), size=11, text=
            f"All {len(IN_GUARANTEE)} in-guarantee classes are compile errors in safe Rust; in C++ each compiles "
            "and is caught, if at all, only at runtime and by no single sanitiser. The guarantee stops at the "
            "boundary rows: Rust removes data races, not race conditions, and aliasing errors, not lock-ordering "
            "errors.")

# =====================================================================
# Slide 15: The measurement host (from the environment capture)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "What the measurement host can and cannot carry"
fill_placeholder(s, 10, "Dedicated and server-class, but virtualised: this is where the tail claim stops")
_, tbl_bottom = add_data_table(
    s,
    [
        ("Aspect", "This host, from the environment capture stored with every run"),
        ("CPU", f"{ENV.get('cpu_model', 'unknown')} \u2014 {ENV.get('cpus', '?')} cores, "
                f"{ENV.get('sockets', '?')} sockets, {ENV.get('numa', '?')} NUMA node, SMT {ENV.get('smt', 'unknown')}"),
        ("OS / kernel", f"{ENV.get('distro', 'unknown')}, kernel {ENV.get('kernel', 'unknown')}"),
        ("Toolchains", f"{ENV.get('gpp', 'unknown')} and {ENV.get('rustc', 'unknown')}"),
        ("Virtualisation", f"{ENV.get('virt', 'unknown')} guest; frequency governor {ENV.get('governor', 'unknown')} "
                           "and turbo host-controlled, so stability is assumed rather than enforced"),
        ("Core isolation", f"isolcpus {ENV.get('isolcpus', 'unknown')}, nohz_full {ENV.get('nohz', 'unknown')}: "
                           "a benchmark thread can still lose its core"),
        ("Campaign size", f"{M('NRepeats')} repeats \u00d7 {M('NLoadLevels')} load levels \u00d7 "
                          f"{M('NVariants')} variants = {M('NRuns')} runs"),
    ],
    col_widths_cm=[4.2, 18.8],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=0.92,
    body_size=12,
)
add_caption(s, tbl_bottom + Cm(0.28), size=11, text=
            "Adequate for parity, fault injection, the FFI seam, the saturation knee, the overload comparison, "
            "and the resource comparisons \u2014 but not for the far tail below saturation, which needs the "
            "bare-metal protocol in bench/TESTBED.md.")

# =====================================================================
# Slide 16: Statistical treatment, fixed in advance
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "How the comparison is tested, decided before the results"
fill_placeholder(s, 10, "Interleaving buys a matched design; the reading rule is pre-committed")
set_body_bullets(s, 15, [
    f"The {M('NVariants')} variants run back to back inside every repeat, so interference common to a block cancels in the paired difference",
    "Medians with nonparametric bootstrap 95% intervals, printed in full because they are strongly asymmetric",
    f"Exact two-sided paired permutation test over all 2^{M('NRepeats')} sign assignments, Holm-corrected across the family of {M('NTests')} tests",
    f"Attainable floors quoted rather than left implicit: {M('MinAttainableP')} uncorrected, {M('CorrectedFloor')} after correction",
    f"{M('NSignificant')} of the {M('NTests')} comparisons survive the correction",
    "Rule fixed in advance: an interval is read as a finding only where pairing removes the interference \u2014 medians and run-level counters, never high percentiles",
    f"The allocator control doubles as a replication check: {M('NCrossAllocReversed')} of the compared effects reverse sign",
])

# =====================================================================
# Slide 17: RQ1 latency below saturation (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = f"RQ1: latency at {M('ReprLoad')} kops/s, below saturation"
fill_placeholder(s, 10, f"Microseconds; median over {M('NRepeats')} repeats above its bootstrap 95% interval")
_, tbl_bottom = add_data_table(
    s,
    [("Variant", "p50", "p99", "p99.9", "max")] + LATENCY,
    col_widths_cm=[5.6, 4.4, 4.4, 4.4, 4.4],
    aligns=[PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * 4,
    row_height_cm=0.98,
    body_size=13,
)
add_caption(s, tbl_bottom + Cm(0.3),
            f"Read at two levels of confidence. At the median the four variants sit within "
            f"{M('PFiftyRange')} \u00b5s of one another ({M('PFiftySpread')}%). Above it the host runs out of "
            f"resolution: p99 differs by {M('PNineNineRange')} \u00b5s across variants while the widest 95% "
            f"interval on a single variant's own p99 spans {M('PNineNineMaxCI')} \u00b5s. When the uncertainty "
            "about one variant exceeds the gap between all of them, no ordering can be read off.")

# =====================================================================
# Slide 18: What the end-to-end number is made of (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "What the end-to-end number is actually made of"
fill_placeholder(s, 10, f"Medians over {M('BudgetRepeats')} interleaved repeats, with the paired test on the difference")
_, tbl_bottom = add_data_table(
    s,
    [("Component", "C++", "Rust", "paired p")] + BUDGET,
    col_widths_cm=[9.6, 4.4, 4.4, 4.8],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
    row_height_cm=1.0,
    body_size=12,
)
add_caption(s, tbl_bottom + Cm(0.3),
            f"The work the languages perform is {M('BudgetCoreShareMax')}% of what the sweep measures; the rest is a "
            f"cross-thread handoff the operating system performs. So the end-to-end null bounds the design, not the "
            f"language: the paired bound is {M('BudgetBoundVsCore')}\u00d7 the operation's own cost. Measured apart, the "
            f"operation is {M('BudgetCoreRatio')}\u00d7 faster in {M('BudgetCoreFaster')} \u2014 traceable to hash-map "
            "layout, not to the safety model.")

# =====================================================================
# Slide 19: RQ1 past saturation (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "RQ1 past saturation: the languages are not equivalent"
fill_placeholder(s, 10, f"At {M('OverloadLoad')} kops/s offered, well beyond the {M('SatKnee')} kops/s knee")
_, tbl_bottom = add_data_table(
    s,
    [("Variant", "sustained throughput (kops/s)", "CPU (%)")] + OVERLOAD,
    col_widths_cm=[7.0, 8.6, 7.6],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
    row_height_cm=1.0,
)
add_caption(s, tbl_bottom + Cm(0.3),
            f"{M('OverloadSustainedFaster')} sustains {M('OverloadThrRatio')}\u00d7 the throughput of "
            f"{M('OverloadSustainedSlower')} in {M('OverloadThrAgree')} repeats under both allocators, at the "
            f"corrected floor of the whole family (Holm p = {M('OverloadThrHolm')}), while drawing "
            f"{M('OverloadCpuPerOpRatio')}\u00d7 the CPU per completed operation. Effort spent without completing "
            "work, not idleness. CPU is summed across threads, so 600% is six busy cores of the fourteen pinned.")

# =====================================================================
# Slide 20: Testing the mechanism (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "Testing the mechanism: the primitives on their own"
fill_placeholder(s, 10, f"{M('ContentionProducers')} producers on one bounded queue, capacity 1024, no operation work in the path")
_, tbl_bottom = add_data_table(
    s,
    [("Language", "throughput (kops/s)", "ns per completed op", "paired p")] + CONTENTION,
    col_widths_cm=[5.0, 6.6, 6.0, 5.6],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
    row_height_cm=1.05,
)
add_caption(s, tbl_bottom + Cm(0.35),
            f"The overload gap was attributed to the bounded queue and the completion handle. Isolated, they "
            f"do not reproduce it: {M('ContentionThrCpp')} against {M('ContentionThrRust')} kops/s is only "
            f"{M('ContentionRatio')}\u00d7 at p = {M('ContentionP')}, against {M('OverloadThrRatio')}\u00d7 in the full "
            "service. So the mechanism involves more of the handoff path than these two primitives \u2014 and "
            "nothing here implicates the borrow checker, bounds checking, or ownership.")

# =====================================================================
# Slide 21: Resource use (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "RQ3: memory follows the language and the allocator both"
fill_placeholder(s, 10, f"At {M('ReprLoad')} kops/s; median over {M('NRepeats')} repeats above its bootstrap 95% interval")
_, tbl_bottom = add_data_table(
    s,
    [("Variant", "throughput (kops/s)", "peak RSS (MiB)", "CPU (%)")] + RESOURCE,
    col_widths_cm=[6.4, 5.8, 5.6, 5.4],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
    row_height_cm=1.0,
)
add_caption(s, tbl_bottom + Cm(0.3),
            f"The Rust build carries {M('RssLangDiffLo')}\u2013{M('RssLangDiffHi')} MiB more peak RSS under "
            f"both allocators, interval [{M('RssLangCILo')}, {M('RssLangCIHi')}] MiB: a real language effect "
            f"that replicates. Linking jemalloc costs {M('RssAllocDiffLo')}\u2013{M('RssAllocDiffHi')} MiB in either "
            "language, an order of magnitude more, so the allocator is the larger lever. The effect is "
            "established but unexplained: attributing it needs hardware counters this guest cannot provide.")

# =====================================================================
# Slide 22: Migration results (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "RQ4: incremental adoption is technically cheap"
fill_placeholder(s, 10, "A C++ host drives an unmodified Rust core across a thin C-ABI seam: "
                        "unsafe-free at compile time, still exposed at run time")
_, tbl_bottom = add_data_table(
    s,
    [("Metric", "Value")] + FFI,
    col_widths_cm=[9.6, 13.4],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=0.63,
    body_size=11,
    cell_fill=lambda r, c, v: (LIGHTGREEN if c == 1 else None) if r in (4, 10) else None,
)
add_caption(s, tbl_bottom + Cm(0.25), size=11, text=
            f"No cost detected (p = {M('FfiOpP')}) over {M('FfiOpRepeats')} interleaved repeats against the same "
            f"operation called natively, and the interval bounds any tax at {M('FfiOpBoundPct')}% of one operation. "
            "The bound, not the failure to detect a difference, is what supports the claim.")

# =====================================================================
# Slide 23: Summary of findings (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "Summary of findings and evidence strength"
fill_placeholder(s, 10, "Safety and migration are final; the performance answer divides at saturation")
add_data_table(
    s,
    [
        ("RQ", "Headline finding", "Evidence"),
        ("RQ1", f"Equivalent at the median below saturation, and the end-to-end number is only "
                f"{M('BudgetCoreShareMax')}% operation; past saturation {M('OverloadSustainedFaster')} sustains "
                f"{M('OverloadThrRatio')}\u00d7 the throughput",
         "Overload and operation resolved; far tail unresolved"),
        ("RQ2", f"All {len(IN_GUARANTEE)} in-guarantee classes are compile errors in safe Rust; the "
                f"{len(BOUNDARY)} boundary classes compile in both languages", "Final"),
        ("RQ3", f"{M('RssLangDiffLo')}\u2013{M('RssLangDiffHi')} MiB more peak RSS in Rust under both allocators, "
                f"an order of magnitude less than the allocator's own "
                f"{M('RssAllocDiffLo')}\u2013{M('RssAllocDiffHi')} MiB", "Resolved, unexplained"),
        ("RQ4", f"Thin, unsafe-isolated seam; no cost detected and any tax bounded at "
                f"{M('FfiOpBoundPct')}% of an operation", "Final"),
    ],
    col_widths_cm=[2.0, 14.6, 6.4],
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=1.7,
    body_size=12,
    cell_fill=lambda r, c, v: (LIGHTGREEN if v == "Final" else LIGHTAMBER) if c == 2 else None,
)

# =====================================================================
# Slide 24: Hypotheses versus verdict (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "The three prior hypotheses against the evidence"
fill_placeholder(s, 10, "Stated up front so the evaluation could refute them, and two of the three needed refining")
add_data_table(
    s,
    [
        ("Hypothesis", "Statement, and what the evidence did to it", "Verdict"),
        ("H1", "Equivalent below saturation with any difference in the far tail. The first half holds; "
               "the second is refuted \u2014 the difference is in overload, not the tail. \u201cPerformance-"
               "equivalent\u201d also names three quantities that answer differently.",
         "Split, and too loosely worded"),
        ("H2", "Safe Rust prevents the classes C++ leaves to best-effort detection. Exact for the "
               f"{len(IN_GUARANTEE)} injected classes; the boundary classes are concurrency defects it does not prevent.",
         "Supported precisely, refuted loosely"),
        ("H3", "Interop cost is negligible against the operations invoked. Supported by the measured "
               "bound, once the seam was compared against the same operation called natively.",
         "Supported"),
    ],
    col_widths_cm=[2.6, 14.2, 6.2],
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=2.1,
    body_size=12,
    cell_fill=lambda r, c, v: (LIGHTGREEN if v == "Supported" else LIGHTAMBER) if c == 2 else None,
)

# =====================================================================
# Slide 25: Scope and boundaries (table)
# =====================================================================
s = prs.slides.add_slide(L(1))
s.shapes.title.text = "Scope and boundaries"
fill_placeholder(s, 10, "Boundaries drawn to protect the internal validity of the comparison")
add_data_table(
    s,
    [
        ("In scope", "Out of scope"),
        ("UE Context Management subsystem", "Full gNB and other control-plane domains"),
        ("Shared-nothing concurrency design", "PHY/L2 and the user-plane data path"),
        ("Load sweep to overload", "Real captured production traffic traces"),
        (f"{len(TAXONOMY)}-class fault-injection catalogue", "Managed-language alternatives (GC pauses)"),
        ("C++-to-Rust FFI migration prototype", "Production deployment and operations"),
    ],
    col_widths_cm=[11.5, 11.5],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=0.92,
    body_size=13,
    cell_fill=lambda r, c, v: LIGHTGREEN if c == 0 else LIGHTAMBER,
)

# =====================================================================
# Slide 26: Conclusions
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "At nominal load the choice is about defects, not speed"
fill_placeholder(s, 10, "Three conclusions from a parity-tested C++ and Rust pair")
set_body_bullets(s, 15, [
    f"Safety is a difference of kind: safe Rust rejects all {len(IN_GUARANTEE)} in-guarantee classes at compile time, and neither language prevents the other {len(BOUNDARY)}",
    f"Migration cost is API design and the learning curve, not run-time overhead: any tax is bounded at {M('FfiOpBoundPct')}% of an operation",
    "Performance divides twice: by what is measured, and by whether the service is still coping",
    f"Below saturation the languages are equivalent at the median; the operation itself is only {M('BudgetCoreShareMax')}% of the round-trip",
    f"Past saturation they are not: {M('OverloadSustainedFaster')} sustains {M('OverloadThrRatio')}\u00d7 the throughput, for reasons in the concurrency plumbing rather than either safety model",
    "What the thesis offers is an instrument rather than a verdict: frozen spec, parity-tested pair, reproducible harness, defect catalogue with its boundary",
])

# =====================================================================
# Slide 27: Open questions and future work
# =====================================================================
s = prs.slides.add_slide(L(3))
s.shapes.title.text = "What is still open, and what comes next"
fill_placeholder(s, 10, "Each item is the direct remedy to a limitation named in the talk")
set_body_bullets(s, 15, [
    "Bare-metal campaign (bench/TESTBED.md): the far tail below saturation is the one result this host cannot resolve",
    "Hardware counters and allocation profiles on the same visit: two results are established but unexplained",
    "Localise the overload mechanism further along the handoff path, now that the isolated primitives are ruled out",
    "Replay captured, anonymised production traces so the operation mix is validated rather than spec-justified",
    "Extend to further control-plane subsystems and to the data-heavy L2/PHY path",
    "Evaluate Rust async runtimes against the thread-per-shard model, to separate the runtime from the language",
])

# =====================================================================
# Slide 28: End slide
# =====================================================================
prs.slides.add_slide(L(71))  # End slide Blue

EMU_PER_CM = 360000


def check_layout(presentation):
    """Report manually placed shapes that fall outside the template's content band.

    Placeholders are exempt because the layout owns their geometry. This catches
    the failure mode a generated deck is prone to: a table or caption that grew
    with the data and now runs under the footer.
    """
    floor = Cm(SLIDE_H_CM - BOTTOM_MARGIN_CM)
    ceiling = Cm(TOP_MARGIN_CM)
    problems = []
    for i, slide in enumerate(presentation.slides, start=1):
        for shape in slide.shapes:
            if shape.is_placeholder or shape.top is None or shape.height is None:
                continue
            text = shape.text_frame.text.strip() if shape.has_text_frame else ""
            label = (text.splitlines() or [str(shape.shape_type)])[0][:38]
            bottom = shape.top + abs(shape.height)
            if bottom > floor:
                problems.append(f"slide {i}: {label!r} ends "
                                f"{(bottom - floor) / EMU_PER_CM:.2f} cm below the footer")
            elif shape.top < ceiling:
                problems.append(f"slide {i}: {label!r} starts "
                                f"{(ceiling - shape.top) / EMU_PER_CM:.2f} cm inside the header band")
    return problems


prs.save(OUT)
print("Saved", OUT, "with", len(prs.slides._sldIdLst), "slides")
print("Data read from:")
print("  figures/gen_macros.tex, figures/gen_complexity.tex "
      f"({len(MACROS)} macros)")
print("  figures/tab_{latency,resource,overload,budget,contention,ffi}.tex")
print(f"  faults/results/taxonomy.csv ({len(IN_GUARANTEE)} in-guarantee "
      f"+ {len(BOUNDARY)} boundary classes)")
print(f"  {os.path.relpath(ENV['_path'], ROOT)}")
print(f"Campaign: {M('NRepeats')} repeats, {M('NRuns')} runs, "
      f"representative load {M('ReprLoad')} kops/s, overload {M('OverloadLoad')} kops/s")

_layout = check_layout(prs)
if _layout:
    print("\nLayout problems:")
    for problem in _layout:
        print(" ", problem)
    sys.exit(1)
print("Layout: all added shapes inside the template content band")
