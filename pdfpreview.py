#!/usr/bin/env python3
"""Render PDF pages to PNGs under .pdf-preview/.

Cursor's built-in PDF webview does not work in this WSL setup, so pages are
rasterised to images that the editor can open directly.

    ./pdfpreview.py Thesis_v1.pdf             # all pages
    ./pdfpreview.py Ha_Vien_Mastersthesis_2026.pdf 1-5   # the thesis, page range
    ./pdfpreview.py Ha_Vien_Mastersthesis_2026.pdf 12 --dpi 200   # one page, higher zoom
"""

import argparse
import pathlib
import sys

try:
    import fitz
except ImportError:
    sys.exit("PyMuPDF is required: pip install pymupdf")

OUT_DIR = pathlib.Path(__file__).parent / ".pdf-preview"


def parse_pages(spec, page_count):
    if not spec:
        return range(page_count)
    if "-" in spec:
        first, last = spec.split("-", 1)
        start, stop = int(first), int(last)
    else:
        start = stop = int(spec)
    if not 1 <= start <= stop <= page_count:
        sys.exit(f"page range {spec} outside 1-{page_count}")
    return range(start - 1, stop)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("pages", nargs="?", help="page number or range, e.g. 3 or 1-10")
    ap.add_argument("--dpi", type=int, default=120)
    args = ap.parse_args()

    pdf = pathlib.Path(args.pdf)
    if not pdf.is_file():
        sys.exit(f"no such file: {pdf}")

    doc = fitz.open(pdf)
    OUT_DIR.mkdir(exist_ok=True)

    for index in parse_pages(args.pages, doc.page_count):
        out = OUT_DIR / f"{pdf.stem}_p{index + 1:03d}.png"
        doc[index].get_pixmap(dpi=args.dpi).save(out)
        print(out)


if __name__ == "__main__":
    main()
