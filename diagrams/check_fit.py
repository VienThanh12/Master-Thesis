#!/usr/bin/env python3
"""Report SVG text that renders wider than the box drawn around it.

Text in these diagrams is hand-positioned, so a label that outgrows its rect
fails silently: it just spills over the border in the exported PDF. This
measures every <text> with the same cairo toy-text API cairosvg renders with,
finds the tightest rect enclosing its baseline, and reports the overflow.

    .venv-pptx/bin/python diagrams/check_fit.py            # all diagrams
    .venv-pptx/bin/python diagrams/check_fit.py 12 24      # by number prefix
"""

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

import cairocffi as cairo

HERE = os.path.dirname(os.path.abspath(__file__))
SVG_NS = "{http://www.w3.org/2000/svg}"

# Text that sits deliberately outside any box: a caption under a shape, a note
# beside a lane. Only flag a text when the rect really is meant to contain it,
# which we approximate by requiring the rect to be no more than this many times
# the text's own height -- a page-sized background rect is not a container.
MAX_CONTAINER_HEIGHT = 90.0

# Report on clearance rather than on overflow alone: a label that stops one
# pixel short of the border reads as broken just as a label that crosses it.
MIN_CLEARANCE = 4.0

_surface = cairo.SVGSurface(None, 1000, 1000)
_ctx = cairo.Context(_surface)


def text_width(s, size, bold=False, italic=False):
    _ctx.select_font_face(
        "Segoe UI",
        cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL,
    )
    _ctx.set_font_size(size)
    return _ctx.text_extents(s)[4]  # x_advance


def _num(value, default=None):
    if value is None:
        return default
    m = re.match(r"-?[\d.]+", value.strip())
    return float(m.group()) if m else default


def walk(node, inherited, rects, texts):
    style = dict(inherited)
    for key in ("font-size", "font-weight", "font-style", "text-anchor"):
        if node.get(key) is not None:
            style[key] = node.get(key)

    tag = node.tag.replace(SVG_NS, "")
    if tag == "rect":
        rects.append((
            _num(node.get("x"), 0.0), _num(node.get("y"), 0.0),
            _num(node.get("width"), 0.0), _num(node.get("height"), 0.0),
        ))
    elif tag == "text":
        content = "".join(node.itertext()).strip()
        # A rotated label lives in its own coordinate frame, so its x/y cannot
        # be compared against unrotated rects.
        if content and node.get("transform") is None:
            texts.append((content, style,
                          _num(node.get("x"), 0.0), _num(node.get("y"), 0.0)))
    for child in node:
        walk(child, style, rects, texts)


def check(path):
    root = ET.parse(path).getroot()
    rects, texts = [], []
    walk(root, {"font-size": "16", "font-weight": "400",
                "font-style": "normal", "text-anchor": "start"}, rects, texts)

    problems = []
    for content, style, x, y in texts:
        size = _num(style["font-size"], 16.0)
        weight = style["font-weight"]
        bold = weight in ("bold", "700", "800", "900") or (
            weight.isdigit() and int(weight) >= 600)
        italic = style["font-style"] == "italic"
        width = text_width(content, size, bold, italic)

        anchor = style["text-anchor"]
        x0 = {"start": x, "middle": x - width / 2, "end": x - width}[anchor]
        x1 = x0 + width

        best = None
        for rx, ry, rw, rh in rects:
            if rh > MAX_CONTAINER_HEIGHT or rw <= 0 or rh <= 0:
                continue
            if not (ry <= y <= ry + rh):
                continue
            if x1 <= rx or x0 >= rx + rw:      # no horizontal overlap at all
                continue
            if best is None or rw * rh < best[2] * best[3]:
                best = (rx, ry, rw, rh)
        if best is None:
            continue

        rx, _ry, rw, _rh = best
        clearance = min(x0 - rx, (rx + rw) - x1)
        if clearance < MIN_CLEARANCE:
            problems.append((content, size, width, rw, clearance))
    return problems


def main(argv):
    names = sorted(glob.glob(os.path.join(HERE, "*.svg")))
    if argv:
        names = [n for n in names
                 if os.path.basename(n)[:2] in argv
                 or os.path.basename(n).startswith(tuple(argv))]

    total = 0
    for path in names:
        problems = check(path)
        if not problems:
            continue
        total += len(problems)
        print(f"\n{os.path.basename(path)}")
        for content, size, tw, rw, clearance in problems:
            verdict = (f"OVERFLOWS by {-clearance:.1f}px per side"
                       if clearance < 0 else
                       f"only {clearance:.1f}px clearance")
            snippet = content if len(content) <= 58 else content[:55] + "..."
            print(f"  text {tw:6.1f}px @ {size:>4}px in box {rw:6.1f}px  "
                  f"-- {verdict}")
            print(f"       {snippet!r}")
    print(f"\n{total} tight or overflowing label(s) across "
          f"{len(names)} diagram(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
