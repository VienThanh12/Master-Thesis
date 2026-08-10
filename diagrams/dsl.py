#!/usr/bin/env python3
"""Drawing primitives that emit one diagram in two formats at once.

Every figure built with this module produces a hand-editable ``.drawio`` source
and an SVG in the same house style as the hand-authored diagrams alongside it.
The SVG is what ``render.py`` turns into the PDF the thesis includes; the
``.drawio`` is what a human opens to move a box.

Text is never auto-wrapped: callers pass an explicit list of lines, exactly as
the hand-authored SVGs do, so that line breaks stay under the author's control.
``Diagram.warnings`` collects lines estimated to overflow their box.
"""

from xml.sax.saxutils import escape, quoteattr

NAVY = "#12233a"
INK = "#243447"
BODY = "#33475b"
MUTED = "#5b6b7b"
FAINT = "#8794a3"
WHITE = "#ffffff"

BLUE = "#2f6db3"
BLUE_FILL = "#eef3fa"
BLUE_DEEP = "#1c4e86"
BLUE_EDGE = "#bcd0e8"
BLUE_CHIP = "#dce8f7"

GREEN = "#2e8b57"
GREEN_FILL = "#f4fbf6"
GREEN_DEEP = "#1f6b41"
GREEN_EDGE = "#a8d7bb"
GREEN_CHIP = "#d9f0dd"

RED = "#a5281b"
RED_FILL = "#fdf1f0"
RED_DEEP = "#8c2a20"
RED_EDGE = "#e6b3ad"
RED_CHIP = "#fbdedb"

AMBER = "#d99413"
AMBER_FILL = "#fdf6e9"
AMBER_DEEP = "#a5700c"
AMBER_EDGE = "#c8860d"
AMBER_CHIP = "#fdecc8"

ORANGE = "#d35400"
ORANGE_FILL = "#fff3ec"
ORANGE_DEEP = "#a04000"
ORANGE_EDGE = "#e0975a"
ORANGE_CHIP = "#fbe0cb"

GREY_FILL = "#f1f4f7"
GREY_EDGE = "#d7dde3"
GREY_DEEP = "#4a5b6b"

SVG_FONT = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
MX_FONT = "Segoe UI"

# Segoe UI averages a little over half the point size per glyph; used only to
# warn about overflow and to give drawio text cells a sensible box.
_WIDTH_RATIO = 0.545


def _w(text, size):
    return _WIDTH_RATIO * size * len(text)


def _html(text):
    return escape(text)


class Diagram:
    def __init__(self, name, width, height, title=None, subtitle=None):
        self.name = name
        self.w = width
        self.h = height
        self.svg = []
        self.cells = []
        self.warnings = []
        self._id = 1
        self._markers = {}
        self.svg.append(
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="{WHITE}"/>'
        )
        if title:
            self.text(width / 2, 32, title, 22, NAVY, weight=700, anchor="middle")
        if subtitle:
            self.text(width / 2, 54, subtitle, 12.5, MUTED, anchor="middle")

    # ---------------------------------------------------------------- helpers
    def _next_id(self):
        self._id += 1
        return f"n{self._id}"

    def _cell(self, style, x, y, w, h, value="", vertex=True):
        self.cells.append(
            {
                "id": self._next_id(),
                "value": value,
                "style": style,
                "x": round(x, 2),
                "y": round(y, 2),
                "w": round(w, 2),
                "h": round(h, 2),
                "vertex": vertex,
            }
        )

    def _check(self, lines, size, inner_w, where):
        for line in lines:
            if _w(line, size) > inner_w:
                self.warnings.append(
                    f"{self.name}: {where}: line may overflow "
                    f"({_w(line, size):.0f}px > {inner_w:.0f}px): {line!r}"
                )

    def _marker(self, color):
        if color not in self._markers:
            mid = f"a{len(self._markers)}"
            self._markers[color] = mid
        return self._markers[color]

    # ------------------------------------------------------------- primitives
    def text(self, x, y, s, size=11.5, color=BODY, weight=400, anchor="start",
             italic=False):
        """One line of text. ``y`` is the SVG baseline, as in the hand SVGs."""
        attrs = [f'x="{x}"', f'y="{y}"', f'font-size="{size}"', f'fill="{color}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if weight != 400:
            attrs.append(f'font-weight="{weight}"')
        if italic:
            attrs.append('font-style="italic"')
        self.svg.append(f'<text {" ".join(attrs)}>{escape(s)}</text>')

        est = _w(s, size)
        left = {"start": x, "middle": x - est / 2, "end": x - est}[anchor]
        align = {"start": "left", "middle": "center", "end": "right"}[anchor]
        style = (
            f"text;html=1;strokeColor=none;fillColor=none;whiteSpace=nowrap;"
            f"align={align};verticalAlign=middle;fontSize={size};fontColor={color};"
            f"fontFamily={MX_FONT};"
        )
        if weight != 400:
            style += "fontStyle=1;"
        elif italic:
            style += "fontStyle=2;"
        self._cell(style, left, y - size * 0.95, max(est, 10), size * 1.5,
                   value=_html(s))

    def lines(self, x, y, items, size=11.5, color=BODY, lh=15, weight=400,
              anchor="start"):
        """A run of text lines, ``y`` being the baseline of the first."""
        for i, item in enumerate(items):
            self.text(x, y + i * lh, item, size, color, weight=weight,
                      anchor=anchor)

    def rect(self, x, y, w, h, fill, stroke=None, rx=0, sw=1.0, dashed=False,
             opacity=None):
        attrs = [f'x="{x}"', f'y="{y}"', f'width="{w}"', f'height="{h}"']
        if rx:
            attrs.append(f'rx="{rx}"')
        attrs.append(f'fill="{fill}"')
        if stroke:
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{sw}"')
        if dashed:
            attrs.append('stroke-dasharray="6 4"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.svg.append(f'<rect {" ".join(attrs)}/>')

        style = f"rounded={1 if rx else 0};whiteSpace=wrap;html=1;"
        if rx:
            style += f"absoluteArcSize=1;arcSize={rx * 2};"
        style += f"fillColor={fill if fill != 'none' else 'none'};"
        style += f"strokeColor={stroke or 'none'};"
        if stroke:
            style += f"strokeWidth={sw};"
        if dashed:
            style += "dashed=1;"
        if opacity is not None:
            style += f"opacity={int(opacity * 100)};"
        self._cell(style, x, y, w, h)

    def card(self, x, y, w, h, title=None, body=(), fill=WHITE, stroke=BLUE_EDGE,
             rx=7, sw=1.0, title_size=11.5, title_color=NAVY, body_size=11,
             body_color=MUTED, pad=14, lh=14.5, gap=20, dashed=False):
        """A titled box. Emits one editable drawio shape carrying its own text."""
        self.rect(x, y, w, h, fill, stroke, rx=rx, sw=sw, dashed=dashed)
        self.cells.pop()  # replace the plain rect with a text-bearing shape

        cy = y + pad + title_size * 0.55
        if title:
            self.text(x + pad, cy + 4, title, title_size, title_color, weight=700)
            cy += gap
        else:
            cy = y + pad + body_size * 0.4
        for i, line in enumerate(body):
            self.text(x + pad, cy + 4 + i * lh, line, body_size, body_color)

        # Drop the per-line drawio cells the two calls above created, and put a
        # single rich shape in their place so the .drawio stays editable.
        drop = (1 if title else 0) + len(body)
        for _ in range(drop):
            self.cells.pop()

        html = ""
        if title:
            html += f"<b>{_html(title)}</b>"
            if body:
                html += "<br><br>"
        html += "<br>".join(_html(b) for b in body)
        style = (
            f"rounded={1 if rx else 0};whiteSpace=wrap;html=1;"
            + (f"absoluteArcSize=1;arcSize={rx * 2};" if rx else "")
            + f"fillColor={fill};strokeColor={stroke or 'none'};strokeWidth={sw};"
            f"align=left;verticalAlign=top;spacingLeft={pad - 4};spacingTop={pad - 10};"
            f"spacingRight=6;fontSize={body_size};fontColor={body_color};"
            f"fontFamily={MX_FONT};"
        )
        if dashed:
            style += "dashed=1;"
        self._cell(style, x, y, w, h, value=html)
        if title:
            self._check([title], title_size, w - 2 * pad, "card title")
        self._check(list(body), body_size, w - 2 * pad, "card body")

    def panel(self, x, y, w, h, header, fill, stroke, rx=11, sw=2.0,
              header_color=None, header_text=WHITE, header_h=34,
              header_size=14.5):
        """A bordered region with a solid header bar across its top.

        The SVG needs a second rect to square off the header's lower corners;
        the drawio side collapses the whole thing to two editable shapes.
        """
        header_color = header_color or stroke
        self.rect(x, y, w, h, fill, stroke, rx=rx, sw=sw)
        self.rect(x, y, w, header_h, header_color, rx=rx)
        self.rect(x, y + header_h - rx, w, rx, header_color)
        self.text(x + w / 2, y + header_h / 2 + 5, header, header_size,
                  header_text, weight=700, anchor="middle")
        for _ in range(4):  # two rects, the corner-squaring rect, and the label
            self.cells.pop()
        body_style = (
            f"rounded=1;absoluteArcSize=1;arcSize={rx * 2};whiteSpace=wrap;"
            f"html=1;fillColor={fill};strokeColor={stroke};strokeWidth={sw};"
            "verticalAlign=top;align=center;"
        )
        self._cell(body_style, x, y, w, h)
        head_style = (
            f"rounded=1;absoluteArcSize=1;arcSize={rx * 2};whiteSpace=wrap;"
            f"html=1;fillColor={header_color};strokeColor=none;"
            f"align=center;verticalAlign=middle;fontSize={header_size};"
            f"fontColor={header_text};fontStyle=1;fontFamily={MX_FONT};"
        )
        self._cell(head_style, x, y, w, header_h, value=_html(header))

    def chip(self, x, y, w, h, label, fill, color, size=11.5, rx=5, weight=400,
             stroke=None):
        self.rect(x, y, w, h, fill, stroke, rx=rx)
        self.cells.pop()
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size, color,
                  weight=weight, anchor="middle")
        self.cells.pop()
        style = (
            f"rounded=1;absoluteArcSize=1;arcSize={rx * 2};whiteSpace=wrap;html=1;"
            f"fillColor={fill};strokeColor={stroke or 'none'};"
            f"align=center;verticalAlign=middle;fontSize={size};fontColor={color};"
            f"fontFamily={MX_FONT};" + ("fontStyle=1;" if weight != 400 else "")
        )
        self._cell(style, x, y, w, h, value=_html(label))
        self._check([label], size, w - 10, "chip")

    def badge(self, cx, cy, r, label, fill=BLUE, color=WHITE, size=13):
        self.svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>')
        self.text(cx, cy + size * 0.37, label, size, color, weight=700,
                  anchor="middle")
        self.cells.pop()
        style = (
            f"ellipse;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=none;"
            f"align=center;verticalAlign=middle;fontSize={size};fontColor={color};"
            f"fontStyle=1;fontFamily={MX_FONT};"
        )
        self._cell(style, cx - r, cy - r, 2 * r, 2 * r, value=_html(label))

    def arrow(self, x1, y1, x2, y2, color=BLUE, sw=2.0, dashed=False,
              head=True):
        mid = self._marker(color)
        attrs = [
            f'x1="{x1}"', f'y1="{y1}"', f'x2="{x2}"', f'y2="{y2}"',
            f'stroke="{color}"', f'stroke-width="{sw}"',
        ]
        if dashed:
            attrs.append('stroke-dasharray="6 4"')
        if head:
            attrs.append(f'marker-end="url(#{mid})"')
        self.svg.append(f'<line {" ".join(attrs)}/>')

        style = (
            f"html=1;rounded=0;strokeColor={color};strokeWidth={sw};"
            f"endArrow={'block' if head else 'none'};endFill=1;"
            + ("dashed=1;" if dashed else "")
        )
        self.cells.append(
            {
                "id": self._next_id(),
                "value": "",
                "style": style,
                "edge": True,
                "sx": x1, "sy": y1, "tx": x2, "ty": y2,
            }
        )

    def elbow(self, points, color=BLUE, sw=2.0, dashed=False, head=True):
        """A polyline through ``points`` with the arrowhead on the last leg."""
        d = " ".join(
            ("M" if i == 0 else "L") + f"{px},{py}"
            for i, (px, py) in enumerate(points)
        )
        mid = self._marker(color)
        attrs = [f'd="{d}"', 'fill="none"', f'stroke="{color}"',
                 f'stroke-width="{sw}"', 'stroke-linejoin="round"']
        if dashed:
            attrs.append('stroke-dasharray="6 4"')
        if head:
            attrs.append(f'marker-end="url(#{mid})"')
        self.svg.append(f'<path {" ".join(attrs)}/>')

        style = (
            f"html=1;rounded=1;strokeColor={color};strokeWidth={sw};"
            f"endArrow={'block' if head else 'none'};endFill=1;edgeStyle=none;"
            + ("dashed=1;" if dashed else "")
        )
        self.cells.append(
            {
                "id": self._next_id(),
                "value": "",
                "style": style,
                "edge": True,
                "sx": points[0][0], "sy": points[0][1],
                "tx": points[-1][0], "ty": points[-1][1],
                "waypoints": points[1:-1],
            }
        )

    def divider(self, x, y1, y2, color=NAVY, sw=2.5, dash="9 5"):
        self.svg.append(
            f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{sw}" stroke-dasharray="{dash}"/>'
        )
        style = (f"html=1;rounded=0;strokeColor={color};strokeWidth={sw};"
                 f"dashed=1;endArrow=none;")
        self.cells.append({
            "id": self._next_id(), "value": "", "style": style, "edge": True,
            "sx": x, "sy": y1, "tx": x, "ty": y2,
        })

    def footer(self, lines, y=None, size=11.5, color=FAINT, lh=16):
        y = y if y is not None else self.h - 16 - lh * (len(lines) - 1)
        self.lines(self.w / 2, y, lines, size, color, lh=lh, anchor="middle")

    # ---------------------------------------------------------------- output
    def to_svg(self):
        defs = ""
        if self._markers:
            marks = "".join(
                f'<marker id="{mid}" markerWidth="9" markerHeight="9" refX="7" '
                f'refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" '
                f'fill="{color}"/></marker>'
                for color, mid in self._markers.items()
            )
            defs = f"  <defs>{marks}</defs>\n"
        body = "\n".join("  " + s for s in self.svg)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} '
            f'{self.h}" width="{self.w}" height="{self.h}" '
            f'font-family="{SVG_FONT}">\n{defs}{body}\n</svg>\n'
        )

    def to_drawio(self):
        out = [
            '<mxGraphModel dx="1100" dy="800" grid="0" gridSize="10" '
            'guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
            f'page="1" pageScale="1" pageWidth="{self.w}" '
            f'pageHeight="{self.h}" math="0" shadow="0" adaptiveColors="auto">',
            "  <root>",
            '    <mxCell id="0"/>',
            '    <mxCell id="1" parent="0"/>',
        ]
        for c in self.cells:
            if c.get("edge"):
                out.append(
                    f'    <mxCell id="{c["id"]}" value={quoteattr(c["value"])} '
                    f'style={quoteattr(c["style"])} edge="1" parent="1">'
                )
                out.append('      <mxGeometry relative="1" as="geometry">')
                out.append(
                    f'        <mxPoint x="{c["sx"]}" y="{c["sy"]}" '
                    'as="sourcePoint"/>'
                )
                out.append(
                    f'        <mxPoint x="{c["tx"]}" y="{c["ty"]}" '
                    'as="targetPoint"/>'
                )
                if c.get("waypoints"):
                    out.append('        <Array as="points">')
                    for px, py in c["waypoints"]:
                        out.append(f'          <mxPoint x="{px}" y="{py}"/>')
                    out.append("        </Array>")
                out.append("      </mxGeometry>")
                out.append("    </mxCell>")
            else:
                out.append(
                    f'    <mxCell id="{c["id"]}" value={quoteattr(c["value"])} '
                    f'style={quoteattr(c["style"])} vertex="1" parent="1">'
                )
                out.append(
                    f'      <mxGeometry x="{c["x"]}" y="{c["y"]}" '
                    f'width="{c["w"]}" height="{c["h"]}" as="geometry"/>'
                )
                out.append("    </mxCell>")
        out += ["  </root>", "</mxGraphModel>", ""]
        return "\n".join(out)
