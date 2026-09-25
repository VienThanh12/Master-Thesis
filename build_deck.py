#!/usr/bin/env python3
"""Build a Nokia-branded slide deck for the master's thesis.

Thesis: Performance, Safety, and Engineering Trade-offs of Rust and C++
        in Nokia RAN Control-Plane Systems (Ha Vien).

Uses the Nokia 2026 PPT toolkit v2.12 clean template. Light theme.

The deck is figure-first. A slide carries a picture wherever the thesis already
owns one that makes the point: the generated result plots under figures/, and
the hand-authored and generated diagrams under diagrams/. Prose survives only as
a short reading note beside the picture, because a slide the audience must read
is a slide they are not listening through.

Every measured number is read at build time from the artefacts that
bench/refresh_thesis.sh regenerates: figures/gen_macros.tex,
figures/gen_complexity.tex, figures/gen_baremetal.tex, figures/gen_probes.tex, the figures/tab_*.tex
table bodies the thesis itself \\input, faults/results/taxonomy.csv, and the
environment capture belonging to the campaign the figures were plotted from.
Nothing is transcribed, so a rerun of the campaign cannot leave the deck
contradicting the thesis. A macro the deck asks for and the data does not
provide is a hard error rather than a stale literal, and a diagram whose own
labels disagree with the macros is refused before it can reach a slide.

Two campaigns are reported and they are kept apart. The reported sweep carries
the unprefixed macros and has run on bare metal since the canonical repeat of
27 August 2026, and the second bare-metal host carries the Bm ones. A slide
quoting a Bm value names its host, because the confirmation changes the shard
count, the load grid, the repeat count and the toolchain along with the machine.
The virtualised guest the sweep ran on before that repeat carries the Guest
macros, read here since 8 September 2026 so that the two slides comparing hosts
can print its values instead of describing it in words beside another host's.
"""
import csv
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(ROOT, ".cursor", "skills", "create-pptx-master-thesis")
sys.path.insert(0, os.path.join(SKILL, "scripts"))

from datetime import date
from pptx import Presentation
from pptx.util import Cm, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR, MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

from pptx_lib import fill_placeholder, remove_template_slides

FIGURES = os.path.join(ROOT, "figures")
DIAGRAMS = os.path.join(ROOT, "diagrams")
ASSETS = os.path.join(ROOT, ".deck-assets")
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
    s = s.replace("$", "")
    # The thesis tables print --- in a cell that has no value. On a slide that
    # would come out as an em dash, which the deck does not use, so the marker is
    # spelled out and any other --- is refused rather than converted (check_dashes).
    if s == "---":
        return "n/a"
    if "---" in s:
        raise SystemExit(f"em dash in generated LaTeX {s!r}: rewrite it in the "
                         "source table, the deck does not print em dashes")
    s = s.replace("--", "\u2013")
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


#: The bare-metal campaign keeps its own file, and every macro in it carries the
#: Bm prefix, because the two campaigns must not be quotable as one. A slide
#: naming a Bm value has to say which host it belongs to.
#:
#: gen_guest.tex joined them on 8 September 2026, for the reason the Guest prefix
#: exists. Slide 23 compared the retired guest against a bare-metal host and had
#: no guest values to compare with, so it filled that column from the unprefixed
#: macros and typed the guest's outcome in words beside them. Once the reported
#: sweep moved to bare metal those unprefixed values became the quiet host's, and
#: the column printed 1 microsecond under a heading reading virtualised guest,
#: against a typed cell saying no ordering was readable. A host described in
#: prose next to another host's numbers is the cell nothing checks.
MACROS = read_macros(os.path.join(FIGURES, "gen_macros.tex"),
                     os.path.join(FIGURES, "gen_complexity.tex"),
                     os.path.join(FIGURES, "gen_baremetal.tex"),
                     os.path.join(FIGURES, "gen_guest.tex"),
                     os.path.join(FIGURES, "gen_probes.tex"))


def M(name):
    """A generated macro, or a hard error naming what is missing.

    Failing loudly is the point: a silently absent number is how the previous
    deck came to contradict the thesis it was summarising.
    """
    try:
        return MACROS[name]
    except KeyError:
        raise SystemExit(
            f"macro \\{name} is in none of figures/gen_"
            f"{{macros,complexity,baremetal}}.tex; {REFRESH_HINT}") from None


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
#: the row, so it is spelled out rather than left as a dash. "flaky" is kept
#: separate from "detected": the lock-order case is reported on a minority of
#: runs because TSan closes a cycle only from acquisitions that succeed, and a
#: detector that fires sometimes is a different proposition from one that fires.
_SANITISER_LABEL = {"detected": "detected", "clean": "no report", "hung": "hung",
                    "flaky": "intermittent"}

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
    "use_after_move": ("Use-after-move",
                       "Admission answers from the context it has just moved into the store"),
    "thread_unsafe_sharing": ("Thread-unsafe handle shared",
                              "A handle whose refcount is not atomic is passed to two shard workers"),
    "lock_order_deadlock": ("Lock-order deadlock",
                            "Two procedures take the same two shard locks in opposite orders"),
    "lost_update": ("Lost update",
                    "A counter's read-modify-write is split across two critical sections"),
    "leak_cycle": ("Leak through a reference cycle",
                   "A context and its handover peer hold owning references to each other"),
    "integer_overflow": ("Integer overflow in a release build",
                         "A bearer's TEID stride computation exceeds the width of its type"),
    "worker_failure_blast_radius": ("Worker failure blast radius",
                                    "One shard worker fails mid-procedure and the others do not survive it"),
    "seam_double_free": ("Double-free across the seam",
                         "The C++ host releases an opaque Rust handle twice"),
    "forgotten_guard": ("Forgotten lock guard",
                        "A validation failure returns without releasing the context lock"),
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
                "ubsan": _SANITISER_LABEL.get(rec.get("cpp_ubsan", "").strip(),
                                              rec.get("cpp_ubsan", "")),
                "rust": rust.replace(",", ", "),
                "boundary": rec["rust_expected"].strip() == "not-prevented",
            })
    return rows


def read_env():
    """Extract host facts from the environment capture belonging to the campaign.

    Not simply the newest capture on disk: ``bench/capture_env.sh`` can be run
    on its own, on any machine, and a stray capture taken on a laptop would
    otherwise have the deck name the wrong measurement host. The capture chosen
    here is the last one written at or before the campaign that
    ``bench/plot_figures.py`` plotted, which is the one the campaign script
    wrote beside it.
    """
    results = os.path.join(ROOT, "bench", "results")
    campaigns = sorted(glob.glob(os.path.join(results, "campaign-*.jsonl")))
    if not campaigns:
        raise SystemExit("no bench/results/campaign-*.jsonl: run bench/campaign.sh")
    stamp = re.search(r"campaign-(\d{8}-\d{6})", os.path.basename(campaigns[-1]))
    if not stamp:
        raise SystemExit(f"cannot read a timestamp from {os.path.basename(campaigns[-1])}")
    caps = []
    for p in glob.glob(os.path.join(results, "env-*.txt")):
        m = re.search(r"env-(\d{8}-\d{6})", os.path.basename(p))
        if m and m.group(1) <= stamp.group(1):
            caps.append(p)
    caps.sort()
    if not caps:
        raise SystemExit(
            f"no bench/results/env-*.txt written at or before campaign {stamp.group(1)}: "
            "the campaign that produced the figures has no environment capture beside it")
    env = {"_path": caps[-1], "_campaign": campaigns[-1]}
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
    # The kernel spells its own sysfs tokens without spaces, and "SMT
    # notsupported" on a slide reads as a spelling mistake rather than as a
    # verbatim value. The fact is unchanged, only its spacing.
    env["smt"] = {"notsupported": "not supported",
                  "forceoff": "forced off"}.get(env.get("smt", ""), env.get("smt", "unknown"))
    return env


# The result tables the slides no longer print are still read: together with the
# macros they define every number the campaign publishes, which is the set a
# diagram's own labels are checked against before it can go on a slide.
LATENCY = read_table("tab_latency")
RESOURCE = read_table("tab_resource")
OVERLOAD = read_table("tab_overload")
BUDGET = read_table("tab_budget")
CONTENTION = read_table("tab_contention")
FFI = read_table("tab_ffi")
RESIDENT = read_table("tab_resident")
TAXONOMY = read_taxonomy()
ENV = read_env()

IN_GUARANTEE = [d for d in TAXONOMY if not d["boundary"]]
BOUNDARY = [d for d in TAXONOMY if d["boundary"]]
#: How many in-guarantee classes each sanitiser fails to report. The point of
#: the safety slide is that no single C++ tool covers the set, so the shortfall
#: is counted from the outcomes rather than asserted.
ASAN_MISSES = sum(1 for d in IN_GUARANTEE if d["asan"] != "detected")
TSAN_MISSES = sum(1 for d in IN_GUARANTEE if d["tsan"] != "detected")
UBSAN_MISSES = sum(1 for d in IN_GUARANTEE if d["ubsan"] != "detected")


def ffi_value(metric):
    """One row of the generated FFI table, by its metric name."""
    for row in FFI:
        if row[0].lower().startswith(metric.lower()):
            return row[1]
    raise SystemExit(f"no row starting {metric!r} in figures/tab_ffi.tex: {REFRESH_HINT}")


# =====================================================================
# Figure assets
#
# Two kinds, both generated elsewhere and only placed here:
#
#   * figures/fig_*.pdf   -- the result plots bench/plot_figures.py writes.
#     PowerPoint will not embed a PDF, so each is rasterised into .deck-assets/
#     and refreshed whenever the source plot is newer.
#   * diagrams/png/*.png  -- the thesis diagrams. Each carries its own title and
#     subtitle for the printed page; on a slide those would duplicate the slide
#     headline, so the band is cropped away by the picture frame rather than by
#     editing the artwork.
# =====================================================================

FIGURE_DPI = 220
os.makedirs(ASSETS, exist_ok=True)


def result_figure(stem):
    """Rasterise a generated result plot, caching until the plot changes."""
    src = os.path.join(FIGURES, f"{stem}.pdf")
    if not os.path.exists(src):
        raise SystemExit(f"missing figures/{stem}.pdf: {REFRESH_HINT}")
    dst = os.path.join(ASSETS, f"{stem}.png")
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise SystemExit(
                "PyMuPDF is needed to place figures/*.pdf on a slide: "
                "pip install pymupdf into .venv-pptx") from None
        with fitz.open(src) as doc:
            doc[0].get_pixmap(dpi=FIGURE_DPI).save(dst)
    return dst


#: Units that only ever appear on a measured quantity. A diagram label carrying
#: one of these has to agree with the generated data, so the numbers behind them
#: are checked before the diagram is allowed onto a slide. Bare percentages and
#: counts are deliberately excluded: "95% interval" and "20 repeats" are prose.
_DIAGRAM_UNIT_RE = re.compile(
    r"(\d[\d\u00a0 ]*(?:\.\d+)?)\s*(ns|\u00b5s|ms|MiB|GiB|kops/s)\b")


def _as_number(text):
    try:
        return float(text.replace("\u00a0", "").replace(" ", "").replace(",", ""))
    except ValueError:
        return None


def _known_numbers():
    """Every number the generated artefacts publish, as floats."""
    values = set(MACROS.values())
    for table in (LATENCY, RESOURCE, OVERLOAD, BUDGET, CONTENTION, FFI, RESIDENT):
        for row in table:
            for cell in row:
                for part in (cell if isinstance(cell, tuple) else (cell,)):
                    values.update(re.findall(r"-?\d[\d.]*", str(part)))
    return {n for n in (_as_number(v) for v in values) if n is not None}


KNOWN_NUMBERS = _known_numbers()

#: SVG text baselines at or above this are the diagram's own title block.
_TITLE_BAND_Y = 70.0
_TITLE_MIN_SIZE = 18.0


def diagram(name):
    """A thesis diagram as (png path, crop fraction hiding its own title block).

    The crop is derived from the artwork rather than tabulated here. A large
    title in the top band means the diagram draws its own heading, so the
    band (title and subtitle together) is cropped away. Diagrams that open
    on the content itself, matching the TikZ figures, are left uncropped.
    """
    svg = os.path.join(DIAGRAMS, f"{name}.svg")
    png = os.path.join(DIAGRAMS, "png", f"{name}.png")
    for path in (svg, png):
        if not os.path.exists(path):
            raise SystemExit(f"missing {os.path.relpath(path, ROOT)}: "
                             "run diagrams/render.py")
    source = open(svg).read()
    height = float(re.search(r"height=\"([\d.]+)\"", source[:400]).group(1))

    for value, unit in _DIAGRAM_UNIT_RE.findall(source):
        number = _as_number(value)
        if number is not None and number not in KNOWN_NUMBERS:
            raise SystemExit(
                f"diagrams/{name}.svg labels a measured quantity as "
                f"{value.strip()} {unit}, which is in no generated artefact. "
                "The diagram is stale against the campaign; correct the artwork "
                "before it goes on a slide or into the thesis.")

    band, has_title = [], False
    for tag in re.finditer(r"<text\b([^>]*)>", source):
        attrs = tag.group(1)
        y_m = re.search(r'\by="(-?[\d.]+)"', attrs)
        s_m = re.search(r'\bfont-size="(-?[\d.]+)"', attrs)
        if not y_m:
            continue
        y = float(y_m.group(1))
        if y > _TITLE_BAND_Y:
            continue
        band.append(y)
        if s_m and float(s_m.group(1)) >= _TITLE_MIN_SIZE:
            has_title = True
    crop = (max(band) + 14.0) / height if has_title and band else 0.0
    return png, crop


# ---- Nokia palette ----
BLUE = RGBColor(0x00, 0x5A, 0xFF)
BLACKBLUE = RGBColor(0x00, 0x11, 0x35)
TEAL = RGBColor(0x23, 0xAB, 0xB6)
GREEN = RGBColor(0x37, 0xCC, 0x73)
ORANGE = RGBColor(0xF4, 0x7F, 0x31)
RED = RGBColor(0xE2, 0x3B, 0x3B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY300 = RGBColor(0xEB, 0xEB, 0xEB)
GRAY800 = RGBColor(0x66, 0x66, 0x66)
LIGHTBLUE = RGBColor(0xE6, 0xEE, 0xFF)
LIGHTGREEN = RGBColor(0xE3, 0xF7, 0xEA)
LIGHTAMBER = RGBColor(0xFD, 0xF2, 0xD9)

BODY_FONT = "Nokia Pure Text Light"

# Template content bounds (see create-pptx-master-thesis/scripts/pptx_lib.py):
# manually placed shapes must start below the header band and end above the
# footer. The subtitle placeholder runs to 3.07 cm, so content starts below it.
EMU_PER_CM = 360000
SLIDE_W_CM = 25.4
SLIDE_H_CM = 14.288
TOP_MARGIN_CM = 2.94
BOTTOM_MARGIN_CM = 1.2
CONTENT_LEFT_CM = 1.16
CONTENT_W_CM = 23.08
CONTENT_TOP_CM = 3.35
CONTENT_BOTTOM_CM = SLIDE_H_CM - BOTTOM_MARGIN_CM - 0.04
CONTENT_H_CM = CONTENT_BOTTOM_CM - CONTENT_TOP_CM

PRESENTER = "Ha Vien"
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


def headline(layout, title, subtitle):
    """A slide with the template's title and subject line filled in."""
    s = prs.slides.add_slide(L(layout))
    s.shapes.title.text = title
    fill_placeholder(s, 10, subtitle)
    return s


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
        height = Cm(CONTENT_BOTTOM_CM) - _emu(top)
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


def add_figure(slide, asset, left=None, top=None, width=None, height=None,
               crop_top=0.0):
    """Place a picture inside a box, scaled to fit and centred in it.

    Returns the box edge the picture actually reached, so a caption or a row of
    reading notes can sit against the picture rather than against the box.
    """
    left = Cm(CONTENT_LEFT_CM) if left is None else left
    top = Cm(CONTENT_TOP_CM) if top is None else top
    width = Cm(CONTENT_W_CM) if width is None else width
    height = Cm(CONTENT_H_CM) if height is None else height
    pic = slide.shapes.add_picture(asset, _emu(left), _emu(top))
    if crop_top:
        pic.crop_top = crop_top
    px_w, px_h = pic.image.size
    aspect = px_w / (px_h * (1.0 - crop_top))
    w = min(int(width), int(height * aspect))
    h = int(w / aspect)
    pic.width, pic.height = w, h
    pic.left = int(left) + (int(width) - w) // 2
    pic.top = int(top) + (int(height) - h) // 2
    return pic


#: Rough advance width of one character as a fraction of the point size, for
#: regular and bold text. Only used to refuse a note whose text will not fit the
#: box it was given: the deck cannot be rendered here, so overflowing type would
#: otherwise only show up on the projector.
_CHAR_W = {False: 0.50, True: 0.55}
_LINE_H = 1.25
_PT_CM = 0.03528


def _text_height_cm(text, size_pt, width_cm, bold=False):
    per_line = max(8, int(width_cm / (size_pt * _CHAR_W[bold] * _PT_CM)))
    lines = sum(max(1, -(-len(part) // per_line)) for part in text.split("\n"))
    return lines * size_pt * _LINE_H * _PT_CM


def add_notes(slide, items, top, left=None, width=None, height=Cm(2.35),
              gap=Cm(0.4), accent=BLUE, fill=LIGHTBLUE, headline_size=13,
              detail_size=10.5, vertical=False):
    """A row (or column) of short reading notes: a verdict over one line of why.

    This is what replaced the paragraph-length captions the earlier deck put
    under every table. A note is meant to be read in one glance while the
    speaker talks, so it carries a headline and at most a sentence, and text
    that will not fit the box is a build error rather than a surprise on stage.
    """
    left = Cm(CONTENT_LEFT_CM) if left is None else left
    width = Cm(CONTENT_W_CM) if width is None else width
    n = len(items)
    if vertical:
        each_h = (int(height) - int(gap) * (n - 1)) // n
        boxes = [(int(left), int(top) + i * (each_h + int(gap)), int(width), each_h)
                 for i in range(n)]
    else:
        each_w = (int(width) - int(gap) * (n - 1)) // n
        boxes = [(int(left) + i * (each_w + int(gap)), int(top), each_w, int(height))
                 for i in range(n)]
    for (x, y, w, h), item in zip(boxes, items):
        head, detail = item
        inner_w = w / EMU_PER_CM - 0.6
        needed = (_text_height_cm(head, headline_size, inner_w, bold=True)
                  + _text_height_cm(detail, detail_size, inner_w) + 0.4)
        if needed > h / EMU_PER_CM:
            raise SystemExit(
                f"reading note {head!r} needs about {needed:.2f} cm but its box is "
                f"{h / EMU_PER_CM:.2f} cm: shorten the text or give the row more height")
        sp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
        sp.line.color.rgb = accent
        sp.line.width = Pt(1)
        sp.shadow.inherit = False
        tf = sp.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = Cm(0.3)
        tf.margin_top = tf.margin_bottom = Cm(0.15)
        p = tf.paragraphs[0]
        p.text = head
        p.font.size = Pt(headline_size)
        p.font.bold = True
        p.font.color.rgb = accent
        p.font.name = BODY_FONT
        p.space_after = Pt(3)
        q = tf.add_paragraph()
        q.text = detail
        q.font.size = Pt(detail_size)
        q.font.color.rgb = BLACKBLUE
        q.font.name = BODY_FONT
    return int(top) + int(height)


def add_bar_chart(slide, left, top, width, title, rows, baseline=None,
                  label_w=Cm(5.0), value_w=Cm(2.0), bar_h=Cm(0.62),
                  row_gap=Cm(0.22)):
    """A small horizontal bar comparison drawn in PowerPoint shapes.

    `rows` is a list of ``(label, value, printed value, colour)``. Bars are
    drawn from zero against the largest value in the group; `baseline` draws a
    dashed rule at a value that means "no difference", so a pair of ratios
    cannot be made to look further apart than it is.
    """
    add_textbox(slide, left, top, width, Cm(0.62), title, size=12.5,
                color=BLACKBLUE, bold=True)
    track_x = int(left) + int(label_w)
    track_w = int(width) - int(label_w) - int(value_w)
    top_row = int(top) + int(Cm(0.72))
    biggest = max(r[1] for r in rows) or 1.0
    for i, (label, value, printed, colour) in enumerate(rows):
        y = top_row + i * (int(bar_h) + int(row_gap))
        add_textbox(slide, left, y - int(Cm(0.06)), label_w, bar_h, label, size=11,
                    color=BLACKBLUE, anchor=MSO_ANCHOR.MIDDLE)
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, track_x, y,
                                     max(int(track_w * value / biggest), int(Cm(0.1))),
                                     int(bar_h))
        bar.fill.solid()
        bar.fill.fore_color.rgb = colour
        bar.line.fill.background()
        bar.shadow.inherit = False
        add_textbox(slide, track_x + track_w + int(Cm(0.2)), y - int(Cm(0.06)),
                    value_w, bar_h, printed, size=11.5, color=colour, bold=True,
                    anchor=MSO_ANCHOR.MIDDLE)
    bottom = top_row + len(rows) * (int(bar_h) + int(row_gap))
    if baseline is not None:
        x = track_x + int(track_w * baseline / biggest)
        rule = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x, top_row - int(Cm(0.12)),
                                          x, bottom - int(row_gap) + int(Cm(0.06)))
        rule.line.color.rgb = GRAY800
        rule.line.width = Pt(1)
        rule.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return bottom


def add_data_table(slide, rows, col_widths_cm, left=Cm(1.3), top=Cm(4.0),
                   height=None, aligns=None, header_fill=BLUE,
                   header_size=14, body_size=13, sub_size=9, cell_fill=None,
                   row_height_cm=None, header_height_cm=None):
    """Generic table helper. `rows` is a list of tuples (row 0 = header).

    A body cell may be a plain value or a ``(main, sub)`` pair; the pair renders
    the second element beneath the first in smaller gray type, which is how the
    thesis prints a median above its confidence interval.

    `col_widths_cm` is a list of column widths in cm (their sum is the table
    width). `aligns` is an optional per-column PP_ALIGN list applied to every
    row. `cell_fill(r, c, main)` may return an RGBColor to override the default
    zebra striping for a body cell (return None to fall back to striping).

    Row heights are set per row rather than left to the even split a bare table
    gets, because a table with tall body rows would otherwise be given an
    equally tall header band with one word in it.
    """
    ncols = len(col_widths_cm)
    if row_height_cm is None:
        two_line = any(isinstance(v, tuple) for row in rows[1:] for v in row)
        row_height_cm = 0.95 if two_line else 0.68
    if header_height_cm is None:
        header_height_cm = row_height_cm
    if height is None:
        height = Cm(header_height_cm + (len(rows) - 1) * row_height_cm)
    total_w = Cm(sum(col_widths_cm))
    gtbl = slide.shapes.add_table(len(rows), ncols, _emu(left), _emu(top),
                                  _emu(total_w), _emu(height))
    tbl = gtbl.table
    tbl.first_row = False
    tbl.horz_banding = False
    for c, w in enumerate(col_widths_cm):
        tbl.columns[c].width = _emu(Cm(w))
    tbl.rows[0].height = _emu(Cm(header_height_cm))
    for r in range(1, len(rows)):
        tbl.rows[r].height = _emu(Cm(row_height_cm))
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
# Slide 2: Roadmap (drawn, not listed)
# =====================================================================
s = headline(1, "What this talk covers",
             "From the industrial problem to controlled evidence for Rust in the RAN")

stops = [
    ("Context", "the control plane,\nand the gap"),
    ("Questions", "four RQs,\none design"),
    ("Method", "one frozen spec,\ntwo builds"),
    ("Safety", f"{len(TAXONOMY)} injected\ndefect classes"),
    ("Performance", "latency, overload,\nresources"),
    ("Migration", "a C++ host over\na Rust core"),
]
LINE_Y = Cm(6.6)
add_arrow(s, Cm(1.6), LINE_Y, Cm(23.9), LINE_Y, color=GRAY300, width=3.0)
first_x, last_x = 3.1, 22.1
step = (last_x - first_x) / (len(stops) - 1)
for i, (label, detail) in enumerate(stops):
    cx = Cm(first_x + i * step)
    add_box(s, cx - Cm(0.78), LINE_Y - Cm(0.78), Cm(1.56), Cm(1.56), str(i + 1),
            BLUE if i else BLACKBLUE, font_color=WHITE, size=17,
            shape=MSO_SHAPE.OVAL)
    add_textbox(s, cx - Cm(1.85), Cm(7.95), Cm(3.7), Cm(0.8), label, size=14,
                color=BLACKBLUE, bold=True, align=PP_ALIGN.CENTER)
    add_textbox(s, cx - Cm(1.85), Cm(8.75), Cm(3.7), Cm(1.5), detail, size=11,
                color=GRAY800, align=PP_ALIGN.CENTER)

# =====================================================================
# Slide 3: Where the subsystem sits (diagram)
# =====================================================================
s = headline(1, "Where the studied subsystem sits",
             "UE Context Management inside the 5G base station's control plane")
_png, _crop = diagram("01_ngran_architecture")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 4: Why the comparison is timely
# =====================================================================
s = headline(1, "Cloud-native RAN raises the premium on software quality",
             "Two trends make a Rust-versus-C++ comparison timely for the control plane")
add_notes(s, [
    ("A hard place to be wrong",
     "The control plane is large, stateful, and highly concurrent, running on commodity "
     "servers under millisecond budgets while coordinating millions of devices."),
    # The figure is Microsoft's own reporting and the slide said "major
    # vendors", which is a claim no source in the bibliography makes. Section
    # 2.1 names the vendor and cites it, so the slide names it too.
    ("Memory safety dominates the defects",
     "Roughly 70% of the security vulnerabilities reported at Microsoft are "
     "memory-safety defects, the class C++ leaves to the programmer."),
    ("Policy is moving ahead of evidence",
     "Agencies now push vendors toward memory-safe languages, yet no controlled "
     "measurement exists for a RAN control-plane subsystem."),
], top=Cm(5.0), height=Cm(4.6), gap=Cm(0.5))
add_textbox(s, Cm(1.16), Cm(10.3), Cm(23.08), Cm(1.0),
            "Carried out at Nokia on a compact model of gNB-CU-CP per-UE state work",
            size=13, color=BLUE, bold=True, align=PP_ALIGN.CENTER)

# =====================================================================
# Slide 5: Key terms
# =====================================================================
s = headline(1, "Key terms for readers outside telecom",
             "The vocabulary that recurs throughout the talk")
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
# Slide 6: The gap (diagram)
# =====================================================================
s = headline(1, "The gap: no controlled evidence for the RAN control plane",
             "Five theses come close, none holds the concurrency model fixed past saturation")
_png, _crop = diagram("29_research_gap")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 7: Research design (diagram)
# =====================================================================
s = headline(1, "Four questions, each tied to evidence",
             "Predictability and migration ahead of raw average speed")
_png, _crop = diagram("10_rq_method_map")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 8: UE lifecycle state machine (drawn)
# =====================================================================
s = headline(1, "The UE context lifecycle both versions encode identically",
             "Illegal transitions return a typed error instead of mutating state")

by = Cm(5.2)
bh = Cm(1.5)
bw = Cm(4.4)
add_box(s, Cm(1.6), by, bw, bh, "Idle", LIGHTBLUE, font_color=BLACKBLUE)
add_box(s, Cm(8.3), by, bw, bh, "Connected", BLUE, font_color=WHITE)
add_box(s, Cm(15.0), by, bw, bh, "Reconfiguring", TEAL, font_color=WHITE)
add_box(s, Cm(8.3), Cm(9.6), bw, bh, "Released", GRAY800, font_color=WHITE)

add_arrow(s, Cm(6.0), Cm(5.95), Cm(8.3), Cm(5.95), color=BLUE)
add_textbox(s, Cm(6.0), Cm(4.45), Cm(2.3), Cm(0.7), "setup", size=12, color=BLUE,
            bold=True, align=PP_ALIGN.CENTER)
add_arrow(s, Cm(12.7), Cm(5.55), Cm(15.0), Cm(5.55), color=TEAL)
add_textbox(s, Cm(12.7), Cm(4.35), Cm(2.3), Cm(0.7), "begin", size=12, color=TEAL,
            bold=True, align=PP_ALIGN.CENTER)
add_arrow(s, Cm(15.0), Cm(6.35), Cm(12.7), Cm(6.35), color=TEAL)
add_textbox(s, Cm(12.1), Cm(6.9), Cm(3.5), Cm(0.7), "complete / abort", size=11,
            color=TEAL, bold=True, align=PP_ALIGN.CENTER)
add_arrow(s, Cm(10.5), Cm(6.7), Cm(10.5), Cm(9.6), color=GRAY800)
add_textbox(s, Cm(10.7), Cm(7.6), Cm(2.6), Cm(0.7), "release", size=12, color=GRAY800,
            bold=True, align=PP_ALIGN.LEFT)
add_arrow(s, Cm(3.8), Cm(6.7), Cm(3.8), Cm(10.35), color=GRAY800)
add_arrow(s, Cm(3.8), Cm(10.35), Cm(8.3), Cm(10.35), color=GRAY800)
add_textbox(s, Cm(4.0), Cm(8.2), Cm(3.0), Cm(0.7), "release", size=12, color=GRAY800,
            bold=True, align=PP_ALIGN.LEFT)
add_textbox(s, Cm(7.0), Cm(3.5), Cm(7.0), Cm(0.7), "signal / add_drb handled in place",
            size=12, color=BLACKBLUE, bold=True, align=PP_ALIGN.CENTER)
add_arrow(s, Cm(10.5), Cm(4.3), Cm(10.5), Cm(5.15), color=BLACKBLUE, width=1.25)

# =====================================================================
# Slide 9: Architecture (drawn)
# =====================================================================
s = headline(1, "Shared-nothing, thread-per-shard architecture",
             "Blocking on a full queue is what makes overload observable as tail latency")

add_box(s, Cm(1.4), Cm(4.4), Cm(4.3), Cm(4.6), "Load generators\n(producers)", LIGHTBLUE,
        font_color=BLACKBLUE, size=13)
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
    add_arrow(s, Cm(5.7), Cm(6.7), qx, ymid, color=GRAY800)
    add_arrow(s, qx + qw, ymid, wx, ymid, color=GRAY800)
    add_arrow(s, wx + ww, ymid, sx, ymid, color=GRAY800)

add_textbox(s, Cm(9.2), Cm(3.35), Cm(12.0), Cm(0.7),
            "shard-owning threads: no shared mutable state, no locks", size=12,
            color=BLACKBLUE, bold=True, align=PP_ALIGN.CENTER)
add_textbox(s, Cm(1.4), Cm(11.4), Cm(20.0), Cm(0.8),
            "One-shot completion: each worker writes the result back to the waiting producer",
            size=11, color=BLUE, bold=True, align=PP_ALIGN.CENTER)

# =====================================================================
# Slide 10: Fairness controls (diagram)
# =====================================================================
s = headline(1, "Fairness by construction, so the language is the only variable",
             "One frozen specification, two implementations, one thing allowed to differ")
_png, _crop = diagram("18_fairness_controls")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 11: How a reported number is produced (diagram)
# =====================================================================
s = headline(1, "How a reported number is produced",
             "Frozen specification to the macro the prose cites, with nothing hand-copied")
_png, _crop = diagram("20_benchmark_harness")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 12: Language-forced idioms, with the size and complexity they cost
# =====================================================================
s = headline(1, "Where the two languages must diverge",
             "The forced-idiom log: same requirement, idiomatic in each language")
_, tbl_bottom = add_data_table(
    s,
    [
        ("Concern", "Modern C++ (C++23)", "Rust (stable)"),
        ("Result type", "std::expected<T, OpError>", "Result<T, OpError>"),
        ("Request", "tagged struct, every argument field", "enum, one variant per operation"),
        ("Response", "std::variant of four result types", "each variant carries its own sender"),
        ("Bounded queue", "hand-written mutex + 2 condition vars", "sync_channel(capacity)"),
        ("One-shot completion", "std::promise / std::future", "a fresh mpsc::channel() per request"),
        ("Per-shard map", "std::unordered_map (node-based)", "HashMap (open-addressed)"),
    ],
    top=Cm(3.5),
    col_widths_cm=[4.6, 9.2, 9.2],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=0.85,
    body_size=12,
)
_chart_top = tbl_bottom + Cm(0.45)
add_bar_chart(s, Cm(1.3), _chart_top, Cm(11.0), "Code size (lines of code)",
              [("C++", float(M("CppNloc")), M("CppNloc"), BLUE),
               ("Rust", float(M("RustNloc")), M("RustNloc"), ORANGE)])
add_bar_chart(s, Cm(13.1), _chart_top, Cm(11.0), "Branching complexity",
              [("C++", float(M("CppCcnTotal")), M("CppCcnTotal"), BLUE),
               ("Rust", float(M("RustCcnTotal")), M("RustCcnTotal"), ORANGE)])
add_textbox(s, Cm(1.3), Cm(12.35), Cm(22.8), Cm(0.7),
            f"Rust is {M('NlocRise')}% longer but {M('CcnTotalDrop')}% lower in total branching. "
            f"The worst C++ function scores {M('CppCcnMax')} against Rust's {M('RustCcnMax')}",
            size=11, color=GRAY800, align=PP_ALIGN.CENTER)

# =====================================================================
# Slide 13: The defect catalogue (diagram)
# =====================================================================
s = headline(1, "The catalogue spans both sides of Rust's guarantee",
             f"{len(IN_GUARANTEE)} classes Rust claims to prevent, and {len(BOUNDARY)} chosen because it does not")
_png, _crop = diagram("13_defect_families_tree")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 14: RQ2 outcomes (generated figure)
# =====================================================================
s = headline(1, "RQ2: a difference of kind, with a definite edge",
             f"{ENV.get('gpp', 'g++')} with ASan/TSan/UBSan versus {ENV.get('rustc', 'rustc')}")
add_figure(s, result_figure("fig_taxonomy"), width=Cm(12.0), height=Cm(9.2),
           top=Cm(3.5))
add_notes(s, [
    (f"All {len(IN_GUARANTEE)} in-guarantee classes are compile errors",
     "Safe Rust rejects them on every ordinary build, with no test coverage required "
     "for the guarantee to hold."),
    ("In C++ each one compiles",
     f"and is caught, if at all, only at run time and by no single tool: ASan misses "
     f"{ASAN_MISSES} of them, TSan {TSAN_MISSES}, UBSan {UBSAN_MISSES}."),
    (f"The last {len(BOUNDARY)} rows are the boundary",
     "Rust removes data races, not race conditions, lock-order errors, leaks, wrapping "
     "arithmetic or fault containment. On two, the C++ tooling is ahead."),
], top=Cm(3.6), left=Cm(13.6), width=Cm(10.64), height=Cm(9.2), gap=Cm(0.42),
   vertical=True)

# =====================================================================
# Slide 15: Where the guarantee stops (diagram)
# =====================================================================
s = headline(1, "Where the compile-time guarantee stops",
             "Data races and aliasing errors are gone, race conditions and deadlocks are not")
_png, _crop = diagram("17_guarantee_boundary")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 16: The two measurement hosts
#
# Both columns are macros the thesis prints: the left the \Main* set that
# bench/plot_figures.py derives from the reported campaign's own capture, the
# right the \Bm* set from bench/baremetal_facts.py. Neither is typed, so the
# slide cannot come to describe a host the results did not run on.
#
# The left column read the capture directly through ENV until 8 September 2026,
# and its labels called it a virtualised guest, which the main sweep was until
# the canonical bare-metal repeat of 27 August 2026. ENV follows the newest
# campaign in bench/results, so the values moved to the bare-metal host and the
# labels stayed behind: the slide printed that host under a guest heading, with
# "none guest" on the timing-floor row and its 48 threads as "48 cores, 1
# sockets". Reading the macros fixes the class of defect and not just this
# instance, because they are the values Appendix D prints.
#
# The retired guest has no column here, though \Guest* macros are in scope for
# slide 23. Its settings differ on every row, so a third column would make the
# table a specification sheet when what the slide has to establish is that two
# machines agree. The caption carries what the guest settled instead.
# =====================================================================
s = headline(1, "Two bare-metal hosts, so no finding rests on one machine",
             "The reported sweep, and a confirmation campaign that moves the design with the host")
_, tbl_bottom = add_data_table(
    s,
    [
        ("Aspect", "Reported sweep", "Confirmation: second bare-metal host"),
        ("CPU", f"{M('MainCpu')}: {M('MainCores')} cores, {M('MainSockets')} socket, "
                f"{M('MainNumaNodes')} NUMA node, SMT {M('MainSmt')}",
         f"{M('BmCpu')}: {M('BmCores')} cores, {M('BmSockets')} socket, "
         f"{M('BmNumaNodes')} NUMA node, SMT {M('BmSmt')}"),
        ("OS / kernel", f"{M('MainHostDistro')}, kernel {M('MainKernel')}. "
                        f"Image {M('MainDistro')}",
         f"{M('BmDistro')}, kernel {M('BmKernel')}"),
        ("Toolchains", f"g++ {M('MainGpp')} and rustc {M('MainRustc')}, pinned in that image",
         f"g++ {M('BmGpp')} and rustc {M('BmRustc')}, the host's own"),
        ("Timing floor", f"virtualisation {M('MainVirt')}, governor {M('MainGovernor')}, boost off, "
                         "so no timeslice goes to a machine this study cannot observe",
         f"virtualisation {M('BmVirt')}, governor {M('BmGovernor')}, steal in "
         f"{M('BmStealWithSteal')} of {M('BmStealIntervals')} sampling intervals"),
        ("Core isolation", f"nohz_full {M('MainNohzFull')}, isolcpus {M('MainIsolcpus')}, "
                           "omitted on purpose to keep load balancing",
         f"isolcpus {M('BmIsolcpus')}, nohz_full {M('BmNohzFull')}, so this half of the "
         "protocol is unmet here"),
        ("Campaign", f"{M('NRepeats')} repeats \u00d7 {M('NLoadLevels')} loads \u00d7 "
                     f"{M('NVariants')} variants = {M('NRuns')} runs",
         f"{M('BmRepeats')} repeats \u00d7 {M('BmLoadLevels')} loads \u00d7 {M('NVariants')} variants "
         f"= {M('BmRuns')} runs, on {M('BmShards')} shards"),
    ],
    top=Cm(3.45),
    col_widths_cm=[3.4, 10.4, 9.2],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=1.15,
    header_height_cm=0.8,
    body_size=10.5,
)
add_caption(s, tbl_bottom + Cm(0.3), size=11, text=
            "The reported sweep settles every result the thesis reports, the far tail below saturation "
            "included, which the virtualised host this study measured on first could not resolve. The "
            "confirmation campaign moves shard count, load grid, repeats and toolchain along with the host, so "
            "it tests whether the findings depend on those choices rather than replacing them.")

# =====================================================================
# Slide 17: How the comparison is tested (diagram)
# =====================================================================
s = headline(1, "How the comparison is tested, decided before the results",
             "Interleaving buys a matched design. The two reading rules are pre-committed")
_png, _crop = diagram("23_stats_pipeline")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 18: RQ1 below saturation (generated figure)
# =====================================================================
# The title and the third note were written for the virtualised guest, where the
# interval did swamp the spread above the median. On the reported host it never
# does: the figure's own panel (b) annotates ratios below one at every percentile
# it draws. Both now read off the same macros the panel does.
# The title has to hold one line. At 65 characters this one wrapped and the
# wrapped word printed through the subtitle, caught by the PNG review of
# 8 September 2026. The limit is width and not a character count, since the
# 62-character title on slide 10 fits, so check a lengthened title in a render.
s = headline(1, "RQ1 below saturation: resolvable at every percentile",
             f"Latency by percentile at {M('ReprLoad')} kops/s, median over {M('NRepeats')} interleaved repeats")
add_figure(s, result_figure("fig_tail_percentiles"), top=Cm(3.4), height=Cm(6.9))
add_notes(s, [
    (f"Within {M('PFiftyRange')} \u00b5s at the median",
     f"The four sit {M('PFiftySpread')}% apart at p50, and pairing resolves it."),
    (f"p99: {M('PNineNineRange')} \u00b5s vs {M('PNineNineMaxCI')} \u00b5s",
     "The gap between all four exceeds the uncertainty about one, so an ordering reads."),
    (f"Widest ratio {M('TailResolveRatioMax')}x at {M('TailResolveRatioMaxAt')}",
     "Below one everywhere drawn. On the guest it passed one above the median."),
], top=Cm(10.55), height=Cm(2.4))

# =====================================================================
# Slide 19: What the end-to-end number is made of (generated figure)
# =====================================================================
s = headline(1, "What the end-to-end number is actually made of",
             f"Medians over {M('BudgetRepeats')} interleaved repeats, with the paired test on the difference")
add_figure(s, result_figure("fig_budget"), top=Cm(3.4), height=Cm(6.9))
add_notes(s, [
    (f"{M('BudgetCoreShareMax')}% of the round-trip",
     "is the work the language performs. The rest is a cross-thread handoff the OS "
     "performs."),
    (f"{M('BudgetBoundVsCore')}\u00d7 too coarse",
     "The paired bound on the sweep is that many times the operation's own cost, so the "
     "null bounds the design."),
    (f"{M('BudgetCoreRatio')}\u00d7 faster in {M('BudgetCoreFaster')}",
     "measured apart from the handoff. The cause is hash-map layout, not either "
     "safety model."),
], top=Cm(10.55), height=Cm(2.4))

# =====================================================================
# Slide 20: Past saturation (generated instrument comparison)
# =====================================================================
# Both bars are this host. The large gaps move with the fill. A smaller
# Rust lead remains, and the visit does not explain it.
s = headline(1, "Both clocks are this host. Only the fill moves",
             "The large gaps follow the recorder. A smaller Rust lead remains")
add_figure(s, result_figure("fig_overload"), top=Cm(3.25), height=Cm(7.15))
add_notes(s, [
    (f"Heap split at {M('KneeSplitLoad')} kops/s",
     f"{M('KneeSplitKeepHeap')} serves {M('KneeSplitMedKeep')}. "
     f"{M('KneeSplitMeet')} of {M('KneeSplitRepeats')} repeats on the other heap still meet the rate."),
    (f"Overload at {M('OverloadLoad')} kops/s",
     f"After the window, C++ finishes {M('ProbeAfterThrRatioSystem')} and "
     f"{M('ProbeAfterThrRatioJemalloc')} of Rust's throughput."),
    (f"CPU per call falls",
     f"{M('OverloadCpuPerOpHigher')} {M('OverloadCpuPerOpRatio')} times, then "
     f"{M('ProbeAfterCpuPerOpHigher')} {M('ProbeAfterCpuPerOpRatio')} times."),
], top=Cm(10.6), height=Cm(2.4))

# =====================================================================
# Slide 21: Testing the mechanism
# =====================================================================
s = headline(1, "Testing the mechanism: the primitives on their own",
             f"{M('ContentionProducers')} producers on one bounded queue, capacity 1024, no operation work in the path")
_, tbl_bottom = add_data_table(
    s,
    [("Language", "throughput (kops/s)", "ns per completed op", "paired p")] + CONTENTION,
    top=Cm(3.5),
    col_widths_cm=[5.0, 6.6, 6.0, 5.4],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
    row_height_cm=1.0,
)
add_bar_chart(s, Cm(1.3), tbl_bottom + Cm(0.6), Cm(15.0),
              "Gap between the languages, where 1.0\u00d7 is no difference",
              [("primitives in isolation", float(M("ContentionRatio")),
                f"{M('ContentionRatio')}\u00d7 ({M('ContentionFaster')})", GREEN),
               ("campaign clock past saturation", float(M("OverloadThrRatio")),
                f"{M('OverloadThrRatio')}\u00d7 ({M('OverloadSustainedFaster')})", RED)],
              baseline=1.0, label_w=Cm(6.6), value_w=Cm(2.6))
add_caption(s, Cm(10.1), size=11, text=
            f"The bounded queue and the reply handle do not reproduce the gap when timed alone: "
            f"{M('ContentionThrCpp')} against {M('ContentionThrRust')} kops/s is only "
            f"{M('ContentionRatio')}\u00d7 at p = {M('ContentionP')}. A closed loop of the same service is not a "
            f"C++ win. On this host, deferred fill removes the large gap and leaves a smaller "
            f"Rust lead. The queue and channel probes were a different machine, so they do "
            f"not explain that lead.")

# =====================================================================
# Slide 22: RQ3 resources (generated figure)
# =====================================================================
s = headline(1, "RQ3: memory follows the language and the allocator both",
             f"At {M('ReprLoad')} kops/s, median over {M('NRepeats')} interleaved repeats")
add_figure(s, result_figure("fig_resources"), top=Cm(3.4), height=Cm(6.9))
add_notes(s, [
    (f"+{M('RssLangDiffLo')}\u2013{M('RssLangDiffHi')} MiB in Rust",
     f"under both allocators (interval [{M('RssLangCILo')}, {M('RssLangCIHi')}] MiB), a "
     "language effect that replicates."),
    (f"+{M('RssAllocDiffLo')}\u2013{M('RssAllocDiffHi')} MiB for jemalloc",
     f"in either language, comparable to it. On the guest, {M('GuestRssAllocLo')}\u2013"
     f"{M('GuestRssAllocHi')} MiB, {M('GuestRssAllocOverLang')} times its language effect."),
    ("The ordering travels",
     "The ratio does not, so the next two slides read the footprint on a host that can "
     "decompose it."),
], top=Cm(10.55), height=Cm(2.4))

# =====================================================================
# Slide 23: The far tail, on the confirmation host
#
# The two columns are the same statistic computed the same way wherever both
# hosts have it, which is the point: what changes between them is the machine,
# so the null on the left is a property of the host and not of the languages.
# Each column now reads its own campaign's macros, Guest against Bm. The guest
# recorded percentiles per run and no histogram buckets, so there is nothing
# there to pool and the two pooled rows say so rather than reporting an
# outcome. The reported sweep resolves the same percentile and the caption
# carries it, because giving it a third column would mean deriving a range
# across variants that no macro holds.
# =====================================================================
s = headline(1, "The far tail, on a machine quiet enough to hold it",
             # One line only. At 94 characters this wrapped onto the table's header
             # row, which the overflow estimate did not catch and the render did.
             f"An interval wider than the spread cannot order anything. {M('BmRuns')} bare-metal runs")
_, tbl_bottom = add_data_table(
    s,
    [
        ("Below saturation", "Virtualised guest", "Bare metal"),
        ("Widest 95% interval on one variant's p99",
         f"{M('GuestPNineNineMaxCI')} \u00b5s", f"{M('BmPNineNineMaxCI')} \u00b5s"),
        ("Range across the four variants' p99",
         f"{M('GuestPNineNineRange')} \u00b5s", f"{M('BmPNineNineRange')} \u00b5s"),
        ("Pooled p99.99, the two C++ variants", "no histograms to pool",
         f"{M('BmFarTailCppLo')}\u2013{M('BmFarTailCppHi')} \u00b5s"),
        ("Pooled p99.99, the two Rust variants", "no histograms to pool",
         f"{M('BmFarTailRustLo')}\u2013{M('BmFarTailRustHi')} \u00b5s"),
    ],
    top=Cm(3.5),
    col_widths_cm=[9.6, 6.6, 6.8],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
    row_height_cm=0.95,
    header_height_cm=0.8,
)
add_notes(s, [
    ("Rust lower at p99.99",
     f"By {M('FarTailLangSep')} \u00b5s on the reported sweep. Here the ranges part from "
     f"{M('BmFarTailSepLoad')} to {M('BmFarTailSepHi')} kops/s, alike below that."),
    ("The median sharpens too",
     f"{M('BmPFiftyFaster')} lower at {M('BmPFiftySig')} of {M('BmPFiftyTested')} points, by "
     f"{M('BmPFiftyDiffLo')}\u2013{M('BmPFiftyDiffHi')} \u00b5s on a {M('BmPFiftyMedian')} \u00b5s operation."),
    ("One load is held out",
     f"At {M('BmFarTailTopLoad')} kops/s the pooled median falls while every percentile above "
     "it stays flat."),
], top=tbl_bottom + Cm(0.35), height=Cm(2.5))
add_caption(s, Cm(11.35), size=11, text=
            f"Pooling gives {M('BmPoolSamplesMin')} to {M('BmPoolSamplesMax')} operations per group, which is "
            f"what makes p99.99 a measurement and not a handful of draws. The same campaign reproduces the "
            f"in-run fill effect at {M('BmOverloadThrRatio')}\u00d7, and its "
            f"counters show Rust retiring {M('BmInstrDelta')}% {M('BmInstrDeltaDir')} instructions in "
            f"{M('BmCycleDelta')}% {M('BmCycleDeltaDir')} cycles.")

# =====================================================================
# Slide 24: The resident set decomposed
# =====================================================================
s = headline(1, "Where the extra resident set actually sits",
             f"jemalloc's own accounting, read in each of the {M('BmJeRuns')} runs of the two jemalloc variants")
_, tbl_bottom = add_data_table(
    s,
    [("Component of the footprint, median MiB", "C++", "Rust", "Difference")] + RESIDENT,
    top=Cm(3.4),
    col_widths_cm=[10.6, 3.9, 3.9, 4.6],
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
    row_height_cm=0.8,
    header_height_cm=0.75,
    body_size=12,
)
add_notes(s, [
    ("Fixed arena bookkeeping",
     f"Arena metadata is {M('BmJeMetadataDelta')} MiB in the Rust build and drifts "
     f"{M('BmJeMetaDrift')}% across the load range."),
    ("Not more application data",
     f"{M('BmJeLiveLower')} holds less live allocation and fewer resident bytes inside jemalloc, "
     f"and still peaks {M('BmJeRssDelta')} MiB higher."),
    ("So it is not the allocator",
     f"Outside jemalloc's mappings the gap is {M('BmJeOutsideDelta')} MiB: the runtime a Rust "
     "process carries before it allocates."),
], top=tbl_bottom + Cm(0.35), height=Cm(2.5))
add_caption(s, Cm(11.95), size=10, text=
            "Peak RSS is a getrusage maximum against sampled jemalloc figures, so the derived row is an "
            "upper bound and the column does not sum exactly.")

# =====================================================================
# Slide 25: The migration seam (diagram)
# =====================================================================
s = headline(1, "RQ4: a C++ host driving an unmodified Rust core",
             "All unsafe is confined to a thin seam crate. The core stays free of it")
_png, _crop = diagram("07_ffi_seam")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 26: What the seam costs (generated figure)
# =====================================================================
s = headline(1, "RQ4: incremental adoption is technically cheap",
             "Bounded against the same operation called natively, not declared free")
add_figure(s, result_figure("fig_ffi_cost"), top=Cm(3.4), height=Cm(6.9))
add_notes(s, [
    (f"Crossing: {ffi_value('Raw FFI crossing')}",
     f"An indirect call. {ffi_value('C-ABI entry points')} entry points in "
     f"{ffi_value('Seam size')} plus a {ffi_value('Hand-written C header')} header."),
    (f"unsafe: {ffi_value('unsafe functions in core library')} core, "
     f"{ffi_value('unsafe functions in FFI seam')} seam",
     "All raw-pointer work sits under one safety contract."),
    (f"Bounded at {M('FfiOpBoundPct')}%",
     f"No cost detected, p = {M('FfiOpP')} over {M('FfiOpRepeats')} repeats. "
     "The bound is the claim."),
], top=Cm(10.55), height=Cm(2.4))

# =====================================================================
# Slide 27: Migration playbook (diagram)
# =====================================================================
s = headline(1, "A playbook for a first Rust component in a C++ control plane",
             "Each step carries the measurement that justifies it, and what it does not buy")
_png, _crop = diagram("19_migration_playbook")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 28: Summary of findings
# =====================================================================
s = headline(1, "Summary of findings and evidence strength",
             "Safety and migration are final. Overload service time stays unknown")
add_data_table(
    s,
    [
        ("RQ", "Headline finding", "Evidence"),
        ("RQ1", f"Below saturation the median gap is small, and the round-trip is only "
                f"{M('BudgetCoreShareMax')}% language work. Rust's pooled far tail sits lower "
                "at the representative load. On this host the large overload gap moves with "
                "the fill, and a smaller Rust lead remains",
         "Far tail resolved on bare metal. Overload service time is not"),
        ("RQ2", f"All {len(IN_GUARANTEE)} in-guarantee classes are compile errors in safe Rust. The "
                f"{len(BOUNDARY)} boundary classes compile in both languages", "Final"),
        ("RQ3", f"{M('RssLangDiffLo')}\u2013{M('RssLangDiffHi')} MiB more peak RSS in Rust under both allocators, "
                f"same direction on all three machines. The allocator's own "
                f"{M('RssAllocDiffLo')}\u2013{M('RssAllocDiffHi')} MiB is comparable here and was "
                f"{M('GuestRssAllocOverLang')} times the language effect on the virtualised host, so "
                f"their ratio does not travel",
         "Resolved, and located outside the allocator"),
        ("RQ4", f"Thin, unsafe-isolated seam. No cost detected and any tax bounded at "
                f"{M('FfiOpBoundPct')}% of an operation", "Final"),
    ],
    top=Cm(3.6),
    col_widths_cm=[2.0, 14.6, 6.4],
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=2.14,
    header_height_cm=0.8,
    body_size=11.5,
    cell_fill=lambda r, c, v: (LIGHTGREEN if v == "Final" else LIGHTAMBER) if c == 2 else None,
)

# =====================================================================
# Slide 29: Hypotheses versus verdict
# =====================================================================
s = headline(1, "The three prior hypotheses against the evidence",
             "H1 is not accepted as written. H2 holds only for the classes it names")
add_data_table(
    s,
    [
        ("Hypothesis", "Statement, and what the evidence did to it", "Verdict"),
        ("H1", "Equivalent below saturation, with any difference confined to the far tail. No margin was "
               "set, so a small median gap is not equivalence. The far tail favours Rust. After saturation "
               "the clocks do not rank service time. On this host the large gap moves with the fill.",
         "Not accepted as written"),
        ("H2", "Safe Rust prevents the classes C++ leaves to best-effort detection. Exact for the "
               f"{len(IN_GUARANTEE)} injected classes. The boundary classes are concurrency defects it does not prevent.",
         "Supported precisely, refuted loosely"),
        ("H3", "Interop cost is negligible against the operations invoked. Supported by the measured "
               "bound, once the seam was compared against the same operation called natively.",
         "Supported"),
    ],
    top=Cm(3.6),
    col_widths_cm=[3.0, 13.8, 6.2],
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
    row_height_cm=2.85,
    header_height_cm=0.8,
    body_size=11.5,
    cell_fill=lambda r, c, v: (LIGHTGREEN if v == "Supported" else LIGHTAMBER) if c == 2 else None,
)

# =====================================================================
# Slide 30: Threats to validity
#
# diagrams/25_threats_validity carries the full three-column version, but it is
# the tallest artwork in the set and shrinks to about a third of the slide when
# fitted, which puts its body text below what a projector can carry. What is
# left standing on the slide is the last column, the live risk, since the
# controls themselves are the subject of the two method slides.
# =====================================================================
s = headline(1, "Threats to validity, and what each control leaves behind",
             "The controls are on the method slides. What is left here is the residual risk")
_threats = [
    ("Internal: is the language the only difference?",
     "Controlled by the frozen specification, the shared allocator and optimisation level, "
     "and the parity suite. What remains: one author wrote both versions, and parity bounds "
     "behaviour, not performance."),
    ("Construct: do the metrics measure the questions?",
     "The operation is reported apart from the handoff rather than folded into it. "
     "What remains: one operation on one data structure is narrower than the sweep it "
     "supplements, and RQ3's footprint is located outside the allocator but not attributed "
     "to a call site."),
    ("Conclusion: are the differences real, or noise?",
     f"{M('NRepeats')} interleaved repeats, an exact paired permutation test, and the Holm "
     "correction, with the floors quoted. What remains: pairing cancels only what a block "
     "shared, so the far tail below saturation needed a quieter machine."),
    ("External: how far do the results travel?",
     "RQ2 and RQ4 rest on the compilers and the C ABI rather than on the host, so they "
     "travel. What remains: the performance results do not, because shared mutable state "
     "or allocation churn could behave differently."),
]
add_notes(s, _threats[:2], top=Cm(3.9), height=Cm(4.3), gap=Cm(0.5),
          accent=BLUE, fill=LIGHTBLUE)
add_notes(s, _threats[2:], top=Cm(8.6), height=Cm(4.3), gap=Cm(0.5),
          accent=ORANGE, fill=LIGHTAMBER)

# =====================================================================
# Slide 31: Conclusions and what comes next (diagram)
# =====================================================================
s = headline(1, "At nominal load the choice is about defects, not speed",
             "What the thesis concludes, what it leaves behind, and where it goes next")
_png, _crop = diagram("26_contributions")
add_figure(s, _png, crop_top=_crop)

# =====================================================================
# Slide 32: End slide
# =====================================================================
prs.slides.add_slide(L(71))  # End slide Blue


def check_layout(presentation):
    """Report manually placed shapes that fall outside the template's content band.

    Placeholders are exempt because the layout owns their geometry. This catches
    the failure mode a generated deck is prone to: a table, a caption, or a
    picture that grew with the data and now runs under the footer or off the side.
    """
    floor = Cm(SLIDE_H_CM - BOTTOM_MARGIN_CM)
    ceiling = Cm(TOP_MARGIN_CM)
    left_edge = Cm(1.1)
    right_edge = Cm(SLIDE_W_CM - 1.1)
    # A shape laid out flush against a margin lands on it to within rounding, so
    # only a visible excursion counts.
    slack = Cm(0.03)
    problems = []
    for i, slide in enumerate(presentation.slides, start=1):
        for shape in slide.shapes:
            if shape.is_placeholder or shape.top is None or shape.height is None:
                continue
            text = shape.text_frame.text.strip() if shape.has_text_frame else ""
            label = (text.splitlines() or [str(shape.shape_type)])[0][:38]
            bottom = shape.top + abs(shape.height)
            if bottom > floor + slack:
                problems.append(f"slide {i}: {label!r} ends "
                                f"{(bottom - floor) / EMU_PER_CM:.2f} cm below the footer")
            elif shape.top < ceiling - slack:
                problems.append(f"slide {i}: {label!r} starts "
                                f"{(ceiling - shape.top) / EMU_PER_CM:.2f} cm inside the header band")
            if shape.width is None:
                continue
            if shape.left < left_edge - slack:
                problems.append(f"slide {i}: {label!r} starts "
                                f"{(left_edge - shape.left) / EMU_PER_CM:.2f} cm past the left margin")
            elif shape.left + abs(shape.width) > right_edge + slack:
                problems.append(f"slide {i}: {label!r} ends "
                                f"{(shape.left + abs(shape.width) - right_edge) / EMU_PER_CM:.2f} "
                                "cm past the right margin")
    return problems


BANNED_DASHES = {
    "\u2014": "em dash",
    "\u2015": "horizontal bar",
    "\u2012": "figure dash",
    "\u2212": "minus sign",
}


def _readable_text(shapes):
    """Every string a viewer can read, including inside groups and tables."""
    for shape in shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _readable_text(shape.shapes)
            continue
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                yield "".join(run.text for run in para.runs)
        if getattr(shape, "has_table", False) and shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    yield cell.text


def check_prose_style(presentation):
    """Report the punctuation the thesis prose style forbids.

    The deck answers to the same rule as the thesis. The em dash is the tell the
    author removes on sight, and the semicolon reads as stiff on a slide the way
    it does on a page. An en dash between numbers is a range and stays, so only a
    spaced one counts as an aside. No slide in this deck shows source code, which
    is what would make a semicolon legitimate.
    """
    problems = []
    for i, slide in enumerate(presentation.slides, start=1):
        for text in _readable_text(slide.shapes):
            if not text.strip():
                continue
            excerpt = text.strip()[:64]
            for char, name in BANNED_DASHES.items():
                if char in text:
                    problems.append(f"slide {i}: {name} in {excerpt!r}")
            if re.search("\u2013\\s|\\s\u2013", text):
                problems.append(f"slide {i}: en dash used as an aside rather than a "
                                f"range in {excerpt!r}")
            if ";" in text:
                problems.append(f"slide {i}: semicolon in {excerpt!r}")
    return problems


prs.save(OUT)
_pictures = sum(1 for sl in prs.slides for sh in sl.shapes if sh.shape_type == 13)
print("Saved", OUT, "with", len(prs.slides._sldIdLst), "slides")
print(f"Figures placed: {_pictures}")
print("Data read from:")
print("  figures/gen_{macros,complexity,baremetal,guest,probes}.tex "
      f"({len(MACROS)} macros)")
print("  figures/tab_{latency,resource,overload,budget,contention,ffi,resident}.tex")
print("  figures/fig_*.pdf, diagrams/png/*.png")
print(f"  faults/results/taxonomy.csv ({len(IN_GUARANTEE)} in-guarantee "
      f"+ {len(BOUNDARY)} boundary classes)")
print(f"  {os.path.relpath(ENV['_campaign'], ROOT)}")
print(f"  {os.path.relpath(ENV['_path'], ROOT)} "
      f"({ENV.get('cpu_model', 'unknown host')}, {ENV.get('virt', '?')})")
print(f"Campaign: {M('NRepeats')} repeats, {M('NRuns')} runs, "
      f"representative load {M('ReprLoad')} kops/s, overload {M('OverloadLoad')} kops/s")
print(f"Confirmation: {M('BmRepeats')} repeats, {M('BmRuns')} runs on {M('BmCpu')} "
      f"(virtualisation {M('BmVirt')}), pooled p99.99")

_layout = check_layout(prs)
if _layout:
    print("\nLayout problems:")
    for problem in _layout:
        print(" ", problem)
else:
    print("Layout: all added shapes inside the template content band")

_style = check_prose_style(prs)
if _style:
    print("\nProse-style problems:")
    for problem in _style:
        print(" ", problem)
else:
    print("Prose style: no em dash, dash aside, or semicolon on any slide")

if _layout or _style:
    sys.exit(1)
