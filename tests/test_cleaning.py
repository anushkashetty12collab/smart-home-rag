from app.ingestion.cleaning import clean_pages, fix_hyphenation, normalize_whitespace


def test_fix_hyphenation():
    assert fix_hyphenation("config-\nuration") == "configuration"


def test_normalize_whitespace():
    assert normalize_whitespace("a   b\n\n\n\nc ") == "a b\n\nc"


def test_repeated_header_and_page_number_removed():
    pages = [f"ACME Thermostat Manual\nReal content number {i} with enough text here.\n{i}" for i in range(5)]
    cleaned = clean_pages(pages)
    assert all("ACME Thermostat Manual" not in p for p in cleaned)
    assert all(p.endswith("here.") for p in cleaned)


def test_empty_page_dropped_but_alignment_kept():
    pages = ["Header\nGood content that is long enough to keep.", "Header\n", "Header\nMore good content long enough to keep."]
    cleaned = clean_pages(pages, min_chars=20)
    assert len(cleaned) == 3 and cleaned[1] == ""
