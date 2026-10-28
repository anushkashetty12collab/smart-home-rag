import re
from collections import Counter

_HYPHEN = re.compile(r"(\w)-\n(\w)")
_PAGE_NUM = re.compile(r"^\s*(page\s*)?\d+(\s*(of|/)\s*\d+)?\s*$", re.I)


def fix_hyphenation(text: str) -> str:
    return _HYPHEN.sub(r"\1\2", text)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def find_repeated_lines(pages: list[str], threshold: float = 0.4) -> set[str]:
    """Short lines that appear on many pages are headers/footers."""
    if len(pages) < 3:
        return set()
    counts: Counter[str] = Counter()
    for page in pages:
        counts.update({ln.strip() for ln in page.splitlines() if 0 < len(ln.strip()) < 80})
    return {ln for ln, c in counts.items() if c / len(pages) >= threshold}


def clean_pages(pages: list[str], threshold: float = 0.4, min_chars: int = 30) -> list[str]:
    """Return cleaned text per page (empty string for dropped pages, so page numbers stay aligned)."""
    repeated = find_repeated_lines(pages, threshold)
    out = []
    for page in pages:
        lines = [
            ln for ln in page.splitlines()
            if ln.strip() not in repeated and not _PAGE_NUM.match(ln)
        ]
        text = normalize_whitespace(fix_hyphenation("\n".join(lines)))
        out.append(text if len(text) >= min_chars else "")
    return out
