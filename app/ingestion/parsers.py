import copy
import re
from collections import Counter
from pathlib import Path

import pymupdf as fitz
from bs4 import BeautifulSoup

from app.ingestion.cleaning import (
    clean_pages,
    find_repeated_lines,
    fix_hyphenation,
    is_page_number,
    normalize_whitespace,
)
from app.ingestion.models import Block

MARGIN = 0.07  # top/bottom 7% of a page = running header/footer zone
DOT_LEADER = re.compile(r"(\.\s*){4,}")  # table-of-contents lines: "Setup . . . . . 12"
SKIP_SECTIONS = {"contents", "table of contents"}


def _norm(s: str) -> str:
    return " ".join(s.split())


def pdf_text_chars(path: Path) -> int:
    return sum(len(_norm(p.get_text())) for p in fitz.open(path))


def diagnose_pdf(path: Path) -> str:
    """Why did a PDF produce no blocks? Returns a short reason string."""
    doc = fitz.open(path)
    if doc.needs_pass:
        return "encrypted/password-protected"
    chars = [len(p.get_text().strip()) for p in doc]
    images = sum(len(p.get_images()) for p in doc)
    if sum(chars) < 30 * max(len(doc), 1):
        return f"no text layer ({images} images, {len(doc)} pages): scanned PDF, run OCR first"
    return "text exists but was filtered out (check header/footer threshold or heading detection)"


def _body_font_size(doc: fitz.Document) -> float:
    sizes: Counter[float] = Counter()
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for s in line["spans"]:
                    sizes[round(s["size"], 1)] += len(s["text"])
    return sizes.most_common(1)[0][0] if sizes else 10.0


def classify_lines(page: fitz.Page, body: float) -> list[dict]:
    """Every line on the page with the properties used for decisions (also used by debug tool)."""
    h = page.rect.height
    out = []
    for b in page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            spans = [s for s in line["spans"] if s["text"].strip()]
            text = "".join(s["text"] for s in line["spans"]).strip()
            if not spans or not text:
                continue
            total = sum(len(s["text"].strip()) for s in spans)
            big = sum(len(s["text"].strip()) for s in spans if s["size"] >= body * 1.15)
            bold = sum(len(s["text"].strip()) for s in spans if s["flags"] & 16)
            y0, y1 = line["bbox"][1], line["bbox"][3]
            in_margin = (y1 < h * MARGIN or y0 > h * (1 - MARGIN)) and len(text) < 80
            letters = sum(c.isalpha() for c in text)
            styled = big / total >= 0.8 or bold / total >= 0.8
            sentence_like = text.endswith((".", ":", ";", ",")) or text[0].islower()
            is_heading = (
                styled and len(text) < 100 and not sentence_like
                and letters >= 3 and letters / len(text) >= 0.5  # not codes like "01 1", "A-1"
            )
            out.append({"text": text, "heading": is_heading, "margin": in_margin,
                        "toc": bool(DOT_LEADER.search(text)),
                        "size": round(max(s["size"] for s in spans), 1),
                        "bold_pct": round(bold / total, 2), "y": round(y0)})
    return out


def parse_pdf(path: Path, meta: dict, threshold: float = 0.4, min_chars: int = 30) -> list[Block]:
    doc = fitz.open(path)
    body = _body_font_size(doc)
    raw_pages = [page.get_text() for page in doc]
    repeated = find_repeated_lines(raw_pages, threshold)
    cleaned = clean_pages(raw_pages, threshold, min_chars)

    blocks: list[Block] = []
    section = "Introduction"
    for i, page in enumerate(doc):
        start = len(blocks)
        buf: list[str] = []

        def flush(page_no=i + 1):
            nonlocal buf
            text = normalize_whitespace(fix_hyphenation("\n".join(buf)))
            if len(text) >= min_chars and section.lower() not in SKIP_SECTIONS:
                blocks.append(Block(text=text, source=path.name, page=page_no, section=section, **meta))
            buf = []

        for ln in classify_lines(page, body):
            n = _norm(ln["text"])
            if ln["margin"] or ln["toc"] or n in repeated or is_page_number(n):
                continue
            if ln["heading"]:
                flush()
                section = ln["text"]
            else:
                buf.append(ln["text"])
        flush()

        # Never silently lose a page: it has real text but produced no block -> keep cleaned text
        if len(blocks) == start and len(cleaned[i]) >= 100 and section.lower() not in SKIP_SECTIONS:
            blocks.append(Block(text=normalize_whitespace(cleaned[i]), source=path.name,
                                page=i + 1, section=section, **meta))
    return blocks


def _own_text(el) -> str:
    """Text of an element without its nested lists/paragraphs (those are visited separately)."""
    clone = copy.copy(el)
    for nested in clone.find_all(["ul", "ol", "table", "p", "li", "div"]):
        nested.decompose()
    return clone.get_text(" ", strip=True)


def _row_text(tr) -> str:
    cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
    cells = [c for c in cells if c]
    if not cells:
        return ""
    return " ".join(cells) if cells[0].endswith(":") else " | ".join(cells)


def parse_html(path: Path, meta: dict) -> list[Block]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    root = soup.find("main") or soup.body or soup

    blocks: list[Block] = []
    section = (soup.title.get_text(strip=True) if soup.title else "Introduction")
    buf: list[str] = []

    def flush():
        nonlocal buf
        text = normalize_whitespace("\n".join(buf))
        if len(text) >= 30 and section.lower() not in SKIP_SECTIONS:
            blocks.append(Block(text=text, source=path.name, page=None, section=section, **meta))
        buf = []

    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "tr"]):
        if el.name != "tr" and el.find_parent("tr"):
            continue  # already covered by its table row
        text = _row_text(el) if el.name == "tr" else (
            el.get_text(" ", strip=True) if el.name.startswith("h") else _own_text(el))
        if not text or text.lower().startswith(("illustration shows", "illustration of")):
            continue  # image alt-text descriptions are noise
        if el.name.startswith("h"):
            flush()
            section = text
        else:
            buf.append(text)
    flush()
    return blocks
