#!/usr/bin/env python3
"""Extract reviewer annotations from a commented PDF.

Recovers the text behind each highlight, the reviewer's typed comment, and the
section the mark falls in (read from the PDF outline), so a supervisor pass can
be triaged against the sources.

    ./pdfannots.py docs/review/Thesis_v2_supervisor.pdf
    ./pdfannots.py docs/review/commented.pdf --json docs/review/annots.json
"""

import argparse
import json
import pathlib
import sys

try:
    import fitz
except ImportError:
    sys.exit("PyMuPDF is required: pip install pymupdf")

# Annotation types that mark a run of text and so carry quadpoints.
MARKUP = {"Highlight", "Underline", "StrikeOut", "Squiggly"}


def marked_text(page, annot):
    """Text under a markup annotation, taken one quad (line fragment) at a time."""
    points = annot.vertices or []
    quads = [fitz.Quad(points[i:i + 4]) for i in range(0, len(points) - 3, 4)]
    if not quads:
        return " ".join(page.get_textbox(annot.rect).split())
    fragments = (" ".join(page.get_textbox(q.rect).split()) for q in quads)
    return " ".join(f for f in fragments if f)


def line_context(page, annot):
    """Text on the line a point annotation sits on, for notes with no span."""
    rect = annot.rect
    band = fitz.Rect(0, rect.y0 - 4, page.rect.x1, rect.y1 + 4)
    return " ".join(page.get_textbox(band).split())


def section_labels(doc):
    """For each 0-based page, the last outline entry starting at or before it."""
    toc = doc.get_toc()
    labels = [""] * doc.page_count
    cursor = ""
    pointer = 0
    for index in range(doc.page_count):
        while pointer < len(toc) and toc[pointer][2] - 1 <= index:
            cursor = toc[pointer][1]
            pointer += 1
        labels[index] = cursor
    return labels


def collect(doc):
    labels = section_labels(doc)
    found = []
    for index in range(doc.page_count):
        page = doc[index]
        for annot in page.annots() or []:
            kind = annot.type[1]
            info = annot.info
            found.append({
                "page": index + 1,
                "section": labels[index],
                "type": kind,
                "author": (info.get("title") or "").strip(),
                "comment": (info.get("content") or "").strip(),
                "quoted": marked_text(page, annot) if kind in MARKUP
                          else line_context(page, annot),
                "date": (info.get("modDate") or "").strip(),
            })
    return found


def report(found):
    page = None
    for n, item in enumerate(found, 1):
        if item["page"] != page:
            page = item["page"]
            heading = f"page {page}"
            if item["section"]:
                heading += f"  ({item['section']})"
            print(f"\n{'=' * 72}\n{heading}\n{'=' * 72}")
        who = item["author"] or "unknown"
        print(f"\n[{n}] {item['type']} by {who}")
        if item["quoted"]:
            print(f"    text : {item['quoted']}")
        if item["comment"]:
            print(f"    note : {item['comment']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--json", metavar="PATH", help="also write the raw records")
    args = ap.parse_args()

    pdf = pathlib.Path(args.pdf)
    if not pdf.is_file():
        sys.exit(f"no such file: {pdf}")

    doc = fitz.open(pdf)
    found = collect(doc)

    if not found:
        sys.exit(
            f"{pdf.name}: {doc.page_count} pages, no annotations.\n"
            "The comments may have been flattened on export, or the reviewer's\n"
            "marks may live only in their own copy. Ask for the original file."
        )

    report(found)
    print(f"\n{len(found)} annotations over {doc.page_count} pages.")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(found, indent=2))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
