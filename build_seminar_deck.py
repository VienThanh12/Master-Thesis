#!/usr/bin/env python3
"""University of Helsinki thesis-seminar deck.

15-minute talk for a general computer-science audience, plus backup slides
for questions. Visual language follows the Faculty of Science PowerPoint
theme: grey panel, science-orange flame, uppercase titles, trilingual
footer, Arial, slide numbers as n / N.

Every measured number is read from the files bench/refresh_thesis.sh
regenerates. A missing macro is a hard error.
"""

import os
import re
import sys

from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

ROOT = os.path.dirname(os.path.abspath(__file__))
FIGURES = os.path.join(ROOT, "figures")
LOGO = os.path.join(ROOT, "template", "figures", "HY-logo-ml.png")
OUT = os.path.join(ROOT, "Ha_Vien_Thesis_Seminar_UH.pptx")
FONT_PATH = "/mnt/c/Windows/Fonts/arial.ttf"
FONT_BOLD = "/mnt/c/Windows/Fonts/arialbd.ttf"

# Widescreen, integer EMU. 12192000 / 914400 = 13.333... in, 6858000 = 7.5 in.
SW = 12192000
SH = 6858000

BLACK = RGBColor(0x00, 0x00, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREY = RGBColor(0xF4, 0xF4, 0xF4)
ORANGE = RGBColor(0xFC, 0xA3, 0x11)  # Faculty of Science
ORANGE_DK = RGBColor(0xC4, 0x78, 0x00)
INK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x55, 0x55, 0x55)
LINE = RGBColor(0xDD, 0xDD, 0xDD)
PALE = RGBColor(0xFF, 0xF6, 0xE8)
ROW_ALT = RGBColor(0xF7, 0xF7, 0xF7)

BANNED = ("\u2014", "\u2013", "\u2212", ";", "---", "--")


def emu(inches):
    return Emu(int(round(inches * 914400)))


def inches_of(length):
    return length / 914400


# --------------------------------------------------------------------- macros
_MACRO_RE = re.compile(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$")
_MCI_RE = re.compile(r"\\mci\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}")


def read_macros(*names):
    found = {}
    for name in names:
        path = os.path.join(FIGURES, name)
        if not os.path.exists(path):
            raise SystemExit(f"missing figures/{name}")
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                m = _MACRO_RE.match(line.strip())
                if m:
                    found[m.group(1)] = m.group(2).replace("\\,", " ").replace("\\%", "%")
    return found


MACROS = read_macros(
    "gen_macros.tex",
    "gen_baremetal.tex",
    "gen_guest.tex",
    "gen_handoff.tex",
    "gen_artefacts.tex",
    "gen_adoption.tex",
    "gen_probes.tex",
)


def M(name):
    try:
        value = MACROS[name]
    except KeyError:
        raise SystemExit(f"macro \\{name} is missing from the generated files") from None
    for bad in BANNED:
        if bad in value:
            raise SystemExit(f"macro \\{name}={value!r} contains {bad!r}")
    return value


def parse_latency():
    """Median (or the lone pooled value) for each column of tab_latency.tex."""
    path = os.path.join(FIGURES, "tab_latency.tex")
    rows = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("%"):
                continue
            cells = [c.strip() for c in re.sub(r"\\\\\s*$", "", line).split("&")]
            values = []
            for cell in cells[1:]:
                mci = _MCI_RE.search(cell)
                values.append(mci.group(1).strip() if mci else cell.strip())
            rows.append((cells[0], values))
    if len(rows) != 4 or any(len(v) != 5 for _, v in rows):
        raise SystemExit(f"tab_latency.tex did not parse into 4x5, got {rows!r}")
    return rows


def paired_medians(prefix):
    """Rust-minus-C++ median differences for rows whose metric starts with prefix.

    Returns a list of floats. Negative means Rust is lower.
    """
    path = os.path.join(FIGURES, "tab_significance.tex")
    out = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line.startswith(prefix):
                continue
            cells = [c.strip() for c in line.split("&")]
            mci = _MCI_RE.search(cells[2])
            if not mci:
                raise SystemExit(f"no paired median in {line!r}")
            out.append(float(mci.group(1)))
    if len(out) != 2:
        raise SystemExit(f"expected 2 rows for {prefix!r}, got {out}")
    return out


def plain_gap(diffs, unit):
    """A spoken gap from two Rust-minus-C++ differences that share a sign."""
    if all(d < 0 for d in diffs):
        direction = "Rust lower"
    elif all(d > 0 for d in diffs):
        direction = "Rust higher"
    else:
        raise SystemExit(f"mixed signs in {diffs}, refuse a single sentence")
    shown = [f"{abs(d):.1f}" for d in diffs]
    return f"{shown[0]} and {shown[1]} {unit}, {direction}"


# ------------------------------------------------------------------- logo crop
def flame_png():
    im = Image.open(LOGO).convert("RGBA")
    px = im.load()
    w, h = im.size
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 200:
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
    cropped = im.crop((minx, miny, maxx + 1, maxy + 1))
    dest = os.path.join(ROOT, ".seminar-assets")
    os.makedirs(dest, exist_ok=True)
    path = os.path.join(dest, "uh-science-flame.png")
    cropped.save(path)
    return path


FLAME = flame_png()


# --------------------------------------------------------------------- deck
prs = Presentation()
prs.slide_width = Emu(SW)
prs.slide_height = Emu(SH)
prs.core_properties.title = (
    "Performance, Safety, and Engineering Trade-offs of Rust and C++ "
    "in Nokia RAN Control-Plane Systems"
)
prs.core_properties.author = "Ha Vien"
prs.core_properties.subject = "Master's thesis seminar, University of Helsinki"
prs.core_properties.category = "Faculty of Science"

BLANK = prs.slide_layouts[6]
if "blank" not in BLANK.name.lower():
    raise SystemExit(f"expected a blank layout, got {BLANK.name!r}")


def style_run(run, size, bold, color):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = False
    run.font.color.rgb = color
    run.font.name = "Arial"
    rPr = run._r.get_or_add_rPr()
    for tag in ("latin", "ea", "cs"):
        el = rPr.find(qn(f"a:{tag}"))
        if el is None:
            el = rPr.makeelement(qn(f"a:{tag}"), {})
            rPr.append(el)
        el.set("typeface", "Arial")


def add_text(slide, text, l, t, w, h, size, bold=False, color=BLACK,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(emu(l), emu(t), emu(w), emu(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    try:
        tf._txBody.bodyPr.set("anchor", {MSO_ANCHOR.TOP: "t",
                                         MSO_ANCHOR.MIDDLE: "ctr",
                                         MSO_ANCHOR.BOTTOM: "b"}[anchor])
    except Exception:
        pass
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        p.line_spacing = 1.0
        run = p.add_run()
        run.text = line
        style_run(run, size, bold, color)
    return box


def panel(slide):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(0.28), emu(0.16),
                                   emu(12.78), emu(6.22))
    shape.fill.solid()
    shape.fill.fore_color.rgb = GREY
    shape.line.fill.background()
    # Keep the panel behind later shapes. python-pptx paints in z-order of addition.
    sp = shape._element
    sp.getparent().remove(sp)
    slide.shapes._spTree.insert(2, sp)
    return shape


def add_flame(slide, l, t, size):
    pic = slide.shapes.add_picture(FLAME, emu(l), emu(t), emu(size), emu(size))
    pic._element.nvPicPr.cNvPr.set("descr",
                                   "University of Helsinki flame, Faculty of Science")
    return pic


def footer(slide, number, total):
    add_text(slide, "HELSINGIN YLIOPISTO\nHELSINGFORS UNIVERSITET\nUNIVERSITY OF HELSINKI",
             0.32, 6.50, 4.55, 0.88, 12, bold=True, color=BLACK, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Computer Science", 5.00, 6.72, 2.35, 0.42, 16, bold=False)
    add_text(slide, "Ha Vien", 7.40, 6.72, 1.55, 0.42, 16, bold=False)
    add_text(slide, "13 November 2026", 8.95, 6.72, 2.35, 0.42, 16, bold=False)
    add_text(slide, f"{number} / {total}", 11.35, 6.68, 1.65, 0.48, 20, bold=True,
             align=PP_ALIGN.RIGHT)


def new_slide():
    slide = prs.slides.add_slide(BLANK)
    # White background. The grey panel is a shape, not a theme fill.
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(0), Emu(0), Emu(SW), Emu(SH))
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE
    bg.line.fill.background()
    sp = bg._element
    sp.getparent().remove(sp)
    slide.shapes._spTree.insert(2, sp)
    panel(slide)
    return slide


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# Specs are collected first so the footer can print n / N.
SPECS = []


def add_title_slide(bullets_unused, title_lines, sublines, notes):
    SPECS.append({"kind": "title", "title": title_lines, "sub": sublines, "notes": notes,
                  "visible": title_lines + sublines})


def add_bullets(title, bullets, notes, size=24):
    SPECS.append({"kind": "bullets", "title": title, "bullets": bullets,
                  "notes": notes, "size": size,
                  "visible": [title] + bullets})


def add_table(title, intro, headers, rows, note, notes):
    SPECS.append({"kind": "table", "title": title, "intro": intro, "headers": headers,
                  "rows": rows, "note": note, "notes": notes,
                  "visible": [title, intro, note] + headers + [c for r in rows for c in r]})


def add_bars(title, caption, categories, values, unit_note, notes):
    SPECS.append({"kind": "bars", "title": title, "caption": caption,
                  "categories": categories, "values": values, "unit_note": unit_note,
                  "notes": notes,
                  "visible": [title, caption, unit_note] + categories + [f"{v}" for v in values]})


# ==================================================================== content
P50 = paired_medians("p50 latency")
CPU = paired_medians("CPU utilisation")
RSS = paired_medians("Peak RSS")
LAT = parse_latency()
# Column order in tab_latency.tex: p50, p99, p99.9, p99.99, max.
FAR = [float(vals[3]) for _, vals in LAT]
FAR_LABELS = ["C++\nsystem", "C++\njemalloc", "Rust\nsystem", "Rust\njemalloc"]

add_title_slide(
    None,
    ["Performance, safety, and engineering trade-offs",
     "of Rust and C++ in a Nokia RAN control plane"],
    ["Master's thesis seminar",
     "Ha Vien",
     "Master's Programme in Computer Science",
     "Faculty of Science, University of Helsinki",
     "Supervisors: Prof. Keijo Heljanko and Christoph Lüneburg",
     "13 November 2026"],
    "20 seconds. Open with the title, your name, and the two supervisors. "
    "Say the talk is 15 minutes and that extra plots sit after the questions slide.",
)

add_bullets(
    "What this thesis is about",
    [
        "A base station is the radio site a phone connects to. The control plane is the software that sets up a call and moves it between cells.",
        "That software is written in C++. C++ is fast, and it compiles a program that uses memory after freeing it.",
        "Rust rejects many of those mistakes before the program runs. It is meant to stay close to C++ in speed.",
        "This thesis builds the same small service in both languages and compares them.",
    ],
    "75 seconds, about 1:35. Define the control plane in one sentence before any acronym. "
    "The service keeps one record per phone. Do not open the research questions yet.",
)

add_bullets(
    "Four words for the rest of the talk",
    [
        "Control plane. It sets up a call and moves it. The phone's data travels on a different path.",
        "Phone record. One stored entry per connected phone. The service keeps these records and answers signalling messages.",
        "Tail latency. The time the slowest calls take. A site can look fine on average and still miss its time budget on those calls.",
        "Memory safety. The program does not use memory after freeing it, and it does not free the same block twice.",
    ],
    "50 seconds, about 2:25. Read the four labels and one gloss each. "
    "Offer to come back to a word if it returns later.",
)

add_bullets(
    "Why this comparison matters now",
    [
        "This software now runs on ordinary servers. A crash, or a slow tail, reaches every phone on the site.",
        "Large C and C++ systems trace most of their serious security bugs to memory mistakes. New rules push vendors to reduce that risk, and the rules name no language.",
        "Earlier studies use general tests, or radio code built in different ways. They disagree on memory use. A controlled comparison of this service was missing.",
        "The work is at Nokia, where this code is C++ today. The useful outcome is which bugs disappear, what speed and memory change, and what one Rust piece costs inside a C++ system.",
    ],
    "90 seconds, about 3:55. Three beats: why the software is exposed now, "
    "why the language question is live, and why earlier work does not settle this service. "
    "If asked who disagreed on memory, go to the earlier-comparisons backup.",
)

add_bullets(
    "What I set out to do",
    [
        "Four questions were fixed before any measurement.",
        "How late are ordinary calls and the slowest calls, including after the service stops keeping up?",
        "Which memory and concurrency mistakes does the Rust compiler reject, and which still compile?",
        "What do the safety checks add in processor time and memory, and what does a call from C++ into Rust cost?",
        "The thesis also leaves a fixed specification, two implementations that pass the same tests, and a harness that drives the service past the load where it stops keeping up.",
    ],
    "70 seconds, about 5:05. Stress that the questions and the bug list were frozen first. "
    "The three leftovers are things another person can rerun.",
)

add_bullets(
    "Both versions follow one specification",
    [
        f"The same tests decide whether the two versions behave alike. The reported sweep is {M('NRepeats')} repeats on a physical server, an {M('MainCpu')}, with no virtual machine.",
        f"Four builds run interleaved: C++ and Rust, each with two libraries that hand out memory. The compilers are g++ {M('MainGpp')} and rustc {M('MainRustc')}.",
        f"The load of {M('ReprLoad')} thousand calls a second was chosen before the campaign. So were the {M('NTests')} comparisons, which are corrected together for the number of tests.",
        "A second physical server checks that the main directions are not an accident of one computer.",
    ],
    "55 seconds, about 6:00. Fairness in one breath: one spec, same tests, interleaved builds, "
    "questions fixed first. Leave the core list and the virtual-machine compiler for backup.",
)

add_bullets(
    "Below that load, Rust is slightly faster",
    [
        f"At {M('ReprLoad')} thousand calls a second, the median gap is at most {M('PFiftyDiffAbsMax')} microseconds and favours Rust.",
        f"The slowest calls favour Rust by more. On the pooled far tail, the slowest Rust build sits {M('FarTailLangSep')} microseconds under the fastest C++ build.",
        f"The timer starts at the planned send time. It includes a late wake-up and the pass between threads. The service's own work, timed on the virtual machine, is at most {M('BudgetCoreShareMax')}% of that round trip.",
        "The gap describes the whole path. It is not a measurement of the compiler alone.",
    ],
    "80 seconds, about 7:20. Say the 1.5 microseconds out loud and let it sound small. "
    "Then say the far tail is larger, and that the clock times the path, not only the service. "
    "The 22 microsecond figure has no interval because the repeats are pooled. Offer the table if asked.",
)

add_bullets(
    "Past that load, the queue decides",
    [
        f"C++ keeps up through {M('TrackingLoadCpp')} thousand calls a second, and Rust through {M('TrackingLoadRust')}. The Rust build that uses jemalloc keeps up through {M('TrackingLoadRustJemalloc')}.",
        f"In the planned run, {M('OverloadSustainedFaster')} finishes {M('OverloadThrRatio')} times as many calls. That timer also includes the sender writing extra samples.",
        "With that writing moved outside the timer, Rust finishes more calls. On another server with the same processor, giving Rust the C++ queue removes the lead.",
        "The gap sits in how work passes between threads.",
    ],
    "70 seconds, about 8:30. Do not call the stopping point shared. "
    "jemalloc is a library that hands out memory. The punchline is the queue, not a language ranking.",
)

add_bullets(
    "Seven classes stop at compile time",
    [
        "The bug list was fixed first. Seven classes sit inside Rust's guarantee, and seven sit on its edge.",
        "Safe Rust rejects the first seven before a program exists. The same seven compile in C++. A test tool reports one only when a test reaches that path.",
        "The other seven compile in both languages and then fail when the program runs. They include a deadlock from lock order, a lost update, and a double-free written through unsafe.",
        "unsafe is Rust's explicit escape hatch. Memory mistakes and data races are rejected at compile time. Deadlocks still compile.",
    ],
    "75 seconds, about 9:45. The result is the edge, not only the seven that fail to compile. "
    "If someone asks for the list, use the two backup slides. "
    "The lock-order tool report is intermittent. Do not quote a fraction.",
)

add_bullets(
    "Memory, and a call from C++",
    [
        f"Rust uses more memory on all three machines. On the reported server the gap is {M('RssLangDiffLo')} to {M('RssLangDiffHi')} MiB.",
        "On the physical servers, changing the memory library also moves the result by a few megabytes. The much larger library gap belongs to the virtual machine.",
        f"A C++ program can call the Rust service, and the Rust code of the service stays as it is. The upper end of the interval is {M('FfiOpBoundPct')}% of one call. The test does not show a difference, so that figure is a bound.",
        "C++ still builds faster. The hours a team spends learning Rust were not measured.",
    ],
    "65 seconds, about 10:50. Do not say the memory library costs more than the language. "
    "Say the two gaps are both a few megabytes on the physical servers, and name the virtual machine before the large gap. "
    "10.91% is the top of the interval, not a measured overhead of 10.91%.",
)

add_bullets(
    "What is still open",
    [
        "The measurement campaign is done. The thesis text answers the four questions, with a limit written next to each answer.",
        "Still open: whether large memory pages explain the memory gap. The setting was not the same on every machine, so the study can name it and cannot test it.",
        "Still open: whether a real call mix matches the synthetic one, whether an asynchronous design changes the tail, and how much time people spend learning and reviewing.",
        "Those are future work. They are not missing runs from this campaign.",
    ],
    "45 seconds, about 11:35. Separate finished work from open questions. "
    "Do not promise a production ranking.",
)

add_bullets(
    "What I learned",
    [
        "The outcome follows the questions that were fixed first. Where a result is weak, the limit is written in the same place.",
        f"A gap of {M('PFiftyDiffAbsMax')} microseconds can be detectable. No margin for the same speed was set, so equivalence was not tested.",
        "One recording step changed which language finished more calls, depending on whether it sat inside the timer.",
        "The seven classes that still compile are part of the safety result. A team that hears only memory-safe can under-review deadlocks.",
    ],
    "60 seconds, about 12:35. This is the reflection, in the first person. "
    "The equivalence point is the one to say slowly.",
)

add_bullets(
    "Advice for the next thesis",
    [
        "Set the margin for the same speed before measuring. Keep the test's own writing outside the timer. Rotate which language runs first.",
        "Freeze the questions, the bug list, and the fair comparison before the first number. A pattern noticed afterwards stays a description.",
        "Publish the specification, and run both versions on the same tests, so someone else can check the work.",
        "In the same paragraph as a result, write what that result cannot support.",
    ],
    "60 seconds, about 13:35. End on the last bullet. It is the habit the thesis is built on. "
    "Then stop.",
)

add_bullets(
    "Questions",
    [
        "I can take questions on the method, the slowest calls, or the bug list.",
        "The slides after this one are backup. The 15-minute talk ends here.",
    ],
    "Stop. You should be here by about 14 minutes. Take questions. "
    "Open a backup slide only when a question needs the plot or the list. "
    "Slide numbers are in the bottom right.",
)

add_bullets(
    "These slides are for questions",
    [
        "They are not part of the 15 minutes.",
        "Each one answers a question the talk left off the main path.",
        "The slide number is in the bottom right corner.",
    ],
    "Do not present this unless you are already in questions and need a map.",
)

add_bullets(
    "The reported machine",
    [
        f"Reported sweep: {M('MainCpu')}, {M('MainCores')} cores, one socket. Simultaneous multithreading (SMT) is off. There is no hypervisor.",
        f"Compilers: g++ {M('MainGpp')} and rustc {M('MainRustc')}, pinned in a container image. {M('NRepeats')} repeats, {M('NLoadLevels')} load levels, {M('NRuns')} runs.",
        f"The earlier virtual machine is kept for the host comparison only. Its g++ is {M('GuestGpp')}, so the two machines do not share a compiler.",
        "Core isolation with isolcpus was left off on purpose. An earlier campaign that turned it on ran the whole sweep on one core.",
    ],
    "If asked where the numbers come from, or whether the virtual machine used the same compiler. "
    "Do not add isolcpus to a future run.",
)

# Latency table. Medians only. Far tail is the pooled column.
lat_headers = ["Build", "Median", "99 of 100", "999 of 1,000", "Far tail"]
lat_names = [
    "C++, system allocator",
    "C++, jemalloc",
    "Rust, system allocator",
    "Rust, jemalloc",
]
lat_rows = []
for name, (_, vals) in zip(lat_names, LAT):
    lat_rows.append([name, vals[0], vals[1], vals[2], vals[3]])

add_table(
    "Latency at the chosen load",
    f"Microseconds at {M('ReprLoad')} thousand calls a second. Each cell except the far tail is the median of the repeats.",
    lat_headers,
    lat_rows,
    "The far tail pools every repeat, so that column has no interval. "
    f"The paired median gaps are {plain_gap(P50, 'microseconds')}.",
    "Walk the columns before the numbers. Median, then 99 of 100, then the far tail. "
    "Say the axis-from-zero problem: a bar chart of the median would hide a 1.5 microsecond gap. "
    "The next slide shows the far tail, where the gap is large enough to see.",
)

add_bars(
    "The far tail is where the gap shows",
    f"Pooled time of the slowest 0.01% of calls, in microseconds, at {M('ReprLoad')} thousand calls a second. The axis starts at zero. This column has no interval.",
    FAR_LABELS,
    FAR,
    f"The slowest Rust bar sits {M('FarTailLangSep')} microseconds under the fastest C++ bar. "
    "jemalloc is one library that hands out memory. The system allocator is the other.",
    "Point at the axis starting at zero. Point at 22 microseconds between the slowest Rust bar "
    "and the fastest C++ bar. Remind them this is pooled.",
)

add_bullets(
    "What the timer includes",
    [
        "The end-to-end clock starts at the planned send time and stops when the reply arrives.",
        "That interval holds a late wake-up, the queue, the reply, and the service's own work.",
        f"On the virtual machine, the service's own work is at most {M('BudgetCoreShareMax')}% of the round trip, and that core alone is {M('BudgetCoreRatio')} times faster in {M('BudgetCoreFaster')}.",
        "A faster core on that clock does not decide the end-to-end ranking. The end-to-end ranking also compares the two sleep paths and the two queues.",
    ],
    "Use this if someone treats the median gap as a compiler result.",
)

add_bullets(
    "Seven classes the compiler rejects",
    [
        "Use-after-free. A message reads a record that a concurrent release already deleted.",
        "Double-free. The same record is released twice.",
        "Iterator invalidation. A list of bearers is changed while it is being walked.",
        "Data race. Two workers write one field with no synchronisation.",
        "Unguarded shared mutation. A record shared across threads is changed with no lock.",
        "Use-after-move. The service answers from a record it has already handed off.",
        "A handle that is not safe across threads is given to two workers.",
    ],
    "Read only the class the question names. All seven fail to compile in safe Rust "
    "and compile in C++. Say that once, then the row.",
    size=22,
)

add_bullets(
    "Seven classes that still compile",
    [
        "Lock-order deadlock. Two procedures take the same two locks in opposite orders. The C++ report of this one is intermittent.",
        "Lost update. A write disappears even though every access is synchronised.",
        "Reference-cycle leak. Two objects keep each other alive.",
        "Integer overflow in a release build. A number wraps instead of being rejected.",
        "Worker-failure blast radius. One worker dies and its share of the phones goes with it.",
        "Double-free through unsafe. The same bug, rewritten through Rust's escape hatch.",
        "Forgotten lock guard. A lock is taken and never released.",
    ],
    "Same rule: answer the class you were asked about. "
    "Stress unsafe on the double-free row, and the intermittent report on the deadlock. "
    "Do not quote a run count for that report.",
    size=20,
)

add_bullets(
    "Memory on the three machines",
    [
        f"Language gap, Rust higher. Reported server: {M('RssLangDiffLo')} to {M('RssLangDiffHi')} MiB. Second physical server: {M('BmRssLangLo')} to {M('BmRssLangHi')} MiB. Virtual machine: {M('GuestRssLangLo')} to {M('GuestRssLangHi')} MiB.",
        f"On the reported server the memory-library gap is {M('RssAllocDiffLo')} to {M('RssAllocDiffHi')} MiB. On the second physical server it is {M('BmRssAllocLo')} to {M('BmRssAllocHi')} MiB.",
        f"On the virtual machine the library gap is {M('GuestRssAllocLo')} to {M('GuestRssAllocHi')} MiB. That size belongs to that machine.",
        f"Processor time below the chosen load: {plain_gap(CPU, 'percentage points')}.",
        "The study does not claim that large memory pages cause the language gap. The page setting was not held fixed.",
    ],
    "Name the machine before any gap. Do not rank the language gap against the library gap. "
    "The percentage points are Rust minus C++, and Rust is the lower one.",
    size=22,
)

add_bullets(
    "The three hypotheses",
    [
        f"Speed. The hypothesis expected a match below the heavy load, with any gap only among the slowest calls. The median gap is detectable, up to {M('PFiftyDiffAbsMax')} microseconds, so that second claim fails. Equivalence was not tested, because no margin was set.",
        "Safety. It holds for the seven classes inside the guarantee, and only in safe Rust. Deadlocks, lost updates, and anything written through unsafe stay outside it.",
        f"Adoption. The upper end of the interval is {M('FfiOpBoundPct')}% of one call. Small was not defined beforehand. The claim that the real cost is engineering effort was not measured.",
    ],
    "Walk the one hypothesis the question names. Do not upgrade a bound into a measured overhead.",
)

add_bullets(
    "Calling Rust from C++",
    [
        f"The boundary has {M('FfiEntryPoints')} entry points. All unsafe code is in {M('FfiUnsafeFns')} functions there. The service core has no unsafe sites.",
        f"On the virtual machine the paired test does not show a difference. The upper end of the interval is {M('FfiOpBoundPct')}% of one signalling call.",
        "C++ builds faster. Most of the extra Rust build time is third-party libraries, not this service's own source.",
        "The shipped-size ordering follows the linkage policy. Match the policy before comparing the two binaries.",
    ],
    "Use this for an adoption question. Do not quote a build-time ratio or a binary-size ratio.",
)

add_bullets(
    "Earlier comparisons",
    [
        "General benchmarks find Rust close to C++ on ordinary speed. That is a different claim from the tail of a stateful service.",
        "Vendor theses on radio software disagree, and memory is where they disagree most.",
        "One of them finds Rust using less memory. Its C++ side uses a fiber library and its Rust side uses an asynchronous runtime, so the gap is also a gap in design.",
        "This study keeps one thread design for both languages and writes down the places where the languages still have to differ.",
    ],
    "Use this when someone cites a thesis that found the opposite memory result.",
)

add_bullets(
    "What this result cannot support",
    [
        "A production base station. The result covers one subsystem, one thread design, and one processor family.",
        "A defect hunt inside the running service. The bugs are small standalone programs.",
        "Equal effort in the two languages. One author directed both, and language models drafted much of the code.",
        "A ranking from the delay after the service stops keeping up. That delay is schedule drift.",
        f"A shared toolchain with the virtual machine. Its g++ is {M('GuestGpp')} and the reported server's g++ is {M('MainGpp')}.",
    ],
    "This is the slide to open if a question turns a limit into a rollout claim.",
)

# ==================================================================== render
TOTAL = len(SPECS)


def check_visible(text, where):
    for bad in BANNED:
        if bad in text:
            raise SystemExit(f"{where} contains {bad!r}: {text}")


def paint_bullets(slide, bullets, top, height, size):
    box = slide.shapes.add_textbox(emu(0.55), emu(top), emu(12.22), emu(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.margin_left = emu(0.04)
    tf.margin_right = emu(0.04)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    for i, text in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.level = 0
        p.space_before = Pt(0)
        p.space_after = Pt(8 if size >= 24 else 4)
        p.line_spacing = 1.0
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(int(emu(0.38))))
        pPr.set("indent", str(int(emu(-0.38))))
        mark = p.add_run()
        mark.text = "\u25cf  "
        style_run(mark, size - 4, False, ORANGE)
        run = p.add_run()
        run.text = text
        style_run(run, size, False, BLACK)
    return box


def shade_cell(cell, color):
    cell.fill.solid()
    cell.fill.fore_color.rgb = color
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for edge in ("lnL", "lnR", "lnT", "lnB"):
        tag = qn(f"a:{edge}")
        ln = tcPr.find(tag)
        if ln is None:
            ln = tcPr.makeelement(tag, {"w": "6350", "cap": "flat", "cmpd": "sng", "algn": "ctr"})
            tcPr.append(ln)
        else:
            ln.set("w", "6350")
        for child in list(ln):
            ln.remove(child)
        solid = ln.makeelement(qn("a:solidFill"), {})
        srgb = solid.makeelement(qn("a:srgbClr"), {"val": "E4E4E4"})
        solid.append(srgb)
        ln.append(solid)


def write_cell(cell, text, size, bold, fill, align):
    cell.text = ""
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    style_run(run, size, bold, BLACK)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = emu(0.08)
    cell.margin_right = emu(0.08)
    cell.margin_top = emu(0.04)
    cell.margin_bottom = emu(0.04)
    shade_cell(cell, fill)


def paint_table(slide, spec, top):
    headers = spec["headers"]
    rows = spec["rows"]
    n_rows = 1 + len(rows)
    n_cols = len(headers)
    width = 12.22
    height = 0.62 * n_rows
    table_shape = slide.shapes.add_table(n_rows, n_cols, emu(0.55), emu(top),
                                         emu(width), emu(height))
    table = table_shape.table
    # First column wider.
    first = int(emu(3.5))
    rest = int((emu(width) - first) / (n_cols - 1))
    table.columns[0].width = Emu(first)
    for i in range(1, n_cols):
        table.columns[i].width = Emu(rest)
    for c, head in enumerate(headers):
        write_cell(table.cell(0, c), head, 18, True, ORANGE,
                   PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER)
    for r, row in enumerate(rows):
        fill = WHITE if r % 2 == 0 else ROW_ALT
        for c, value in enumerate(row):
            write_cell(table.cell(r + 1, c), value, 20, False, fill,
                       PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER)
    return top + height


def paint_bars(slide, spec, top):
    values = spec["values"]
    labels = spec["categories"]
    axis_max = 180.0
    left, width, height = 1.35, 11.15, 3.15
    bottom = top + height
    for tick in (0, 40, 80, 120, 160):
        y = bottom - (tick / axis_max) * height
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(left), emu(y),
                                      emu(width), emu(0.012))
        line.fill.solid()
        line.fill.fore_color.rgb = LINE if tick else BLACK
        line.line.fill.background()
        add_text(slide, str(tick), 0.42, y - 0.16, 0.82, 0.32, 18, align=PP_ALIGN.RIGHT)
    n = len(values)
    slot = width / n
    bar_w = slot * 0.48
    colors = [INK, MUTED, ORANGE, ORANGE_DK]
    for i, (value, label) in enumerate(zip(values, labels)):
        bh = (value / axis_max) * height
        x = left + slot * i + (slot - bar_w) / 2
        y = bottom - bh
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(x), emu(y), emu(bar_w), emu(bh))
        bar.fill.solid()
        bar.fill.fore_color.rgb = colors[i]
        bar.line.fill.background()
        # Value sits inside the bar so it cannot collide with the caption.
        add_text(slide, f"{value:.1f}",
                 x - 0.05, y + 0.08, bar_w + 0.10, 0.36,
                 20, bold=True, color=BLACK if i >= 2 else WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, label, x - 0.20, bottom + 0.06, bar_w + 0.40, 0.62,
                 18, align=PP_ALIGN.CENTER)


for index, spec in enumerate(SPECS, start=1):
    for text in spec["visible"]:
        check_visible(text, f"slide {index}")
    check_visible(spec["notes"], f"notes {index}")
    slide = new_slide()
    if spec["kind"] == "title":
        add_flame(slide, 0.48, 0.36, 1.45)
        # Title block sits to the right of the flame and then full width below it.
        add_text(slide, spec["title"][0], 2.10, 0.48, 10.55, 0.85, 28, bold=True)
        add_text(slide, spec["title"][1], 2.10, 1.28, 10.55, 0.85, 28, bold=True)
        y = 2.40
        sizes = [26, 24, 22, 22, 22, 22]
        for line, size in zip(spec["sub"], sizes):
            add_text(slide, line, 0.70, y, 12.00, 0.46, size, bold=(size >= 24),
                     align=PP_ALIGN.CENTER)
            y += 0.50
    else:
        add_flame(slide, 0.42, 0.26, 0.78)
        add_text(slide, spec["title"].upper(), 1.35, 0.34, 11.45, 0.72, 26, bold=True)
        if spec["kind"] == "bullets":
            paint_bullets(slide, spec["bullets"], 1.28, 4.85, spec["size"])
        elif spec["kind"] == "table":
            add_text(slide, spec["intro"], 0.55, 1.22, 12.22, 0.70, 20)
            used = paint_table(slide, spec, 2.00)
            add_text(slide, spec["note"], 0.55, used + 0.18, 12.22, 0.85, 20)
        elif spec["kind"] == "bars":
            add_text(slide, spec["caption"] + " " + spec["unit_note"],
                     0.55, 1.16, 12.22, 0.95, 20)
            paint_bars(slide, spec, 2.20)
    footer(slide, index, TOTAL)
    set_notes(slide, spec["notes"])


# ---------------------------------------------------------------- prose screen
def write_candidate():
    dest_dir = os.path.join(ROOT, ".prose-scratch")
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, "candidate.tex")
    lines = ["\\chapter{Introduction}", ""]
    for spec in SPECS:
        if spec["kind"] == "title":
            continue
        lines.append(spec["title"] + ".")
        lines.append("")
        if spec["kind"] == "bullets":
            for b in spec["bullets"]:
                lines.append(b if b.endswith(".") else b + ".")
                lines.append("")
        elif spec["kind"] == "table":
            lines.append(spec["intro"])
            lines.append("")
            lines.append(spec["note"])
            lines.append("")
        elif spec["kind"] == "bars":
            lines.append(spec["caption"])
            lines.append("")
            lines.append(spec["unit_note"])
            lines.append("")
    lines.append("\\bibliography{bibliography}")
    lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


prs.save(OUT)
candidate = write_candidate()
print(f"wrote {OUT}")
print(f"slides {TOTAL}")
print(f"prose {candidate}")
print(f"p50 gaps {P50}")
print(f"cpu gaps {CPU}")
print(f"rss gaps {RSS}")
print(f"far tail {list(zip(FAR_LABELS, FAR))}")
