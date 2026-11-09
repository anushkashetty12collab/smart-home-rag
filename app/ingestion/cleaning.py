import re
<<<<<<< HEAD
import unicodedata
from collections import Counter

_HYPHEN = re.compile(r"(\w)[-\u00ad]\n(\w)")
_PAGE_NUM = re.compile(r"^\s*(page\s*)?\d+(\s*(of|/)\s*\d+)?\s*$", re.I)


def _n(s: str) -> str:
    return " ".join(s.split())


def is_page_number(line: str) -> bool:
    return bool(_PAGE_NUM.match(line))


=======
from collections import Counter

_HYPHEN = re.compile(r"(\w)-\n(\w)")
_PAGE_NUM = re.compile(r"^\s*(page\s*)?\d+(\s*(of|/)\s*\d+)?\s*$", re.I)


>>>>>>> 12a01701187fe81b02a6d357ae9cc59f9a71b514
def fix_hyphenation(text: str) -> str:
    return _HYPHEN.sub(r"\1\2", text)


def normalize_whitespace(text: str) -> str:
<<<<<<< HEAD
    text = unicodedata.normalize("NFKC", text)  # ﬁ -> fi, ﬂ -> fl, ℃ -> °C ...
    text = text.replace("\u00ad", "")  # stray soft hyphens
=======
    text = text.replace("\u00a0", " ")
>>>>>>> 12a01701187fe81b02a6d357ae9cc59f9a71b514
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def find_repeated_lines(pages: list[str], threshold: float = 0.4) -> set[str]:
    """Short lines that appear on many pages are headers/footers."""
    if len(pages) < 3:
        return set()
    counts: Counter[str] = Counter()
    for page in pages:
<<<<<<< HEAD
        counts.update({_n(ln) for ln in page.splitlines() if 0 < len(_n(ln)) < 80})
=======
        counts.update({ln.strip() for ln in page.splitlines() if 0 < len(ln.strip()) < 80})
>>>>>>> 12a01701187fe81b02a6d357ae9cc59f9a71b514
    return {ln for ln, c in counts.items() if c / len(pages) >= threshold}


def clean_pages(pages: list[str], threshold: float = 0.4, min_chars: int = 30) -> list[str]:
    """Return cleaned text per page (empty string for dropped pages, so page numbers stay aligned)."""
    repeated = find_repeated_lines(pages, threshold)
    out = []
    for page in pages:
        lines = [
            ln for ln in page.splitlines()
<<<<<<< HEAD
            if _n(ln) not in repeated and not _PAGE_NUM.match(ln)
=======
            if ln.strip() not in repeated and not _PAGE_NUM.match(ln)
>>>>>>> 12a01701187fe81b02a6d357ae9cc59f9a71b514
        ]
        text = normalize_whitespace(fix_hyphenation("\n".join(lines)))
        out.append(text if len(text) >= min_chars else "")
    return out
