from collections import Counter
from pathlib import Path

import pymupdf as fitz
from bs4 import BeautifulSoup

from app.ingestion.cleaning import clean_pages, normalize_whitespace
from app.ingestion.models import Block


def _body_font_size(doc: fitz.Document) -> float:
    sizes: Counter[float] = Counter()
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for s in line["spans"]:
                    sizes[round(s["size"], 1)] += len(s["text"])
    return sizes.most_common(1)[0][0] if sizes else 10.0


def _page_lines(page: fitz.Page, body: float) -> list[tuple[str, bool]]:
    """(line_text, is_heading) for each line on the page."""
    result = []
    for b in page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            if not text:
                continue
            size = max(s["size"] for s in line["spans"])
            bold = all(s["flags"] & 16 for s in line["spans"])
            is_heading = len(text) < 100 and (size >= body * 1.15 or (bold and size >= body))
            result.append((text, is_heading))
    return result


def parse_pdf(path: Path, meta: dict, threshold: float = 0.4, min_chars: int = 30) -> list[Block]:
    doc = fitz.open(path)
    body = _body_font_size(doc)
    raw_pages = [page.get_text() for page in doc]
    cleaned = clean_pages(raw_pages, threshold, min_chars)
    kept = {i: set(c.splitlines()) for i, c in enumerate(cleaned) if c}

    blocks: list[Block] = []
    section = "Introduction"
    for i, page in enumerate(doc):
        if i not in kept:
            continue
        buf: list[str] = []

        def flush(page_no=i + 1):
            nonlocal buf
            text = normalize_whitespace("\n".join(buf))
            if text:
                blocks.append(Block(text=text, source=path.name, page=page_no, section=section, **meta))
            buf = []

        for text, is_heading in _page_lines(page, body):
            if text not in kept[i]:  # removed as header/footer/page number
                continue
            if is_heading:
                flush()
                section = text
            else:
                buf.append(text)
        flush()
    return blocks


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
        if len(text) >= 30:
            blocks.append(Block(text=text, source=path.name, page=None, section=section, **meta))
        buf = []

    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "td"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if el.name.startswith("h"):
            flush()
            section = text
        else:
            buf.append(text)
    flush()
    return blocks
