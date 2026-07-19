#!/usr/bin/env python3
"""Render every diagrams/*.svg to PNG (preview) and PDF (LaTeX inclusion).

Usage:  .venv-pptx/bin/python diagrams/render.py
"""
import glob
import os
import sys

import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
PNG_DIR = os.path.join(HERE, "png")
PDF_DIR = os.path.join(HERE, "pdf")
os.makedirs(PNG_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)


def main():
    svgs = sorted(glob.glob(os.path.join(HERE, "*.svg")))
    if not svgs:
        print("no SVGs found")
        return 1
    for svg in svgs:
        name = os.path.splitext(os.path.basename(svg))[0]
        png = os.path.join(PNG_DIR, name + ".png")
        pdf = os.path.join(PDF_DIR, name + ".pdf")
        # scale=2 gives crisp PNG previews
        cairosvg.svg2png(url=svg, write_to=png, scale=2.0)
        cairosvg.svg2pdf(url=svg, write_to=pdf)
        print(f"rendered {name}: png + pdf")
    print(f"\nDone: {len(svgs)} diagram(s) -> {PNG_DIR} and {PDF_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
