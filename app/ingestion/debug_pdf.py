"""Show how every line of one PDF page is classified.

Run:  uv run python -m app.ingestion.debug_pdf data/raw/pdf/file.pdf 130
"""
import sys

import pymupdf

from app.ingestion.parsers import _body_font_size, classify_lines


def main() -> None:
    path, page_no = sys.argv[1], int(sys.argv[2])
    doc = pymupdf.open(path)
    body = _body_font_size(doc)
    print(f"body font size = {body}\n")
    print(f"{'kind':8} {'size':>5} {'bold%':>5} {'y':>4}  text")
    for ln in classify_lines(doc[page_no - 1], body):
        kind = "MARGIN" if ln["margin"] else "HEADING" if ln["heading"] else "body"
        print(f"{kind:8} {ln['size']:>5} {ln['bold_pct']:>5} {ln['y']:>4}  {ln['text'][:90]}")


if __name__ == "__main__":
    main()
