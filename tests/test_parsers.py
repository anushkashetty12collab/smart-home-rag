import pymupdf as fitz

from app.ingestion.parsers import parse_html, parse_pdf

META = {"device_model": "ThermoX-200", "device_type": "thermostat", "doc_type": "manual"}


def make_pdf(path):
    doc = fitz.open()
    for n in range(3):
        page = doc.new_page()
        page.insert_text((50, 30), "ThermoX Manual", fontsize=8)
        page.insert_text((50, 80), ["Setup", "Troubleshooting", "Specifications"][n], fontsize=18)
        for i in range(6):
            page.insert_text((50, 120 + i * 16),
                             f"Body line {i} on page {n + 1}: press and hold the button.", fontsize=11)
    doc.save(path)


def test_parse_pdf_keeps_page_and_section(tmp_path):
    p = tmp_path / "thermo.pdf"
    make_pdf(p)
    blocks = parse_pdf(p, META)
    assert blocks and all(b.source == "thermo.pdf" and b.page for b in blocks)
    assert {b.section for b in blocks} >= {"Setup", "Troubleshooting"}
    assert not any("ThermoX Manual" in b.text for b in blocks)  # header removed
    assert next(b for b in blocks if b.page == 2).section == "Troubleshooting"


def test_parse_html_sections(tmp_path):
    p = tmp_path / "faq.html"
    p.write_text("""<html><head><title>Bulb FAQ</title></head><body><nav>menu</nav>
    <h2>Why is it blinking red?</h2><p>A red blink means the bulb lost Wi-Fi connection.</p>
    <h2>How to reset?</h2><p>Switch the bulb off and on five times to reset it.</p>
    <script>x=1</script></body></html>""")
    blocks = parse_html(p, META)
    assert [b.section for b in blocks] == ["Why is it blinking red?", "How to reset?"]
    assert all(b.page is None and "menu" not in b.text for b in blocks)
<<<<<<< HEAD


def test_scanned_pdf_gives_zero_blocks_and_diagnosis(tmp_path):
    from app.ingestion.parsers import diagnose_pdf

    p = tmp_path / "scan.pdf"
    doc = fitz.open()
    for _ in range(3):
        doc.new_page()  # blank pages = no text layer
    doc.save(p)
    assert parse_pdf(p, META) == []
    assert "scanned" in diagnose_pdf(p)


def test_margin_header_removed_even_if_not_repeated(tmp_path):
    p = tmp_path / "m.pdf"
    doc = fitz.open()
    for n in range(10):
        page = doc.new_page()
        if n in (4, 5):
            page.insert_text((50, 30), "Appendix", fontsize=9)  # only 2/10 pages
        for i in range(5):
            page.insert_text((50, 120 + i * 16), f"Unique body text {n}-{i} for the manual.", fontsize=11)
    doc.save(p)
    assert not any("Appendix" in b.text for b in parse_pdf(p, META))


def test_bold_sentence_with_colon_is_not_a_heading_and_hyphen_is_joined(tmp_path):
    p = tmp_path / "b.pdf"
    doc = fitz.open()
    for n in range(2):
        page = doc.new_page()
        page.insert_text((50, 80), "Setup" if n == 0 else "Codes", fontsize=18)
        page.insert_text((50, 120), "The device prompts you to enter one of these codes:", fontsize=11, fontname="hebo")
        page.insert_text((50, 140), "Check the config-", fontsize=11)
        page.insert_text((50, 156), "uration menu on page %d for details." % (n + 1), fontsize=11)
        for i in range(3):
            page.insert_text((50, 180 + i * 16), f"Filler sentence {n}-{i} to reach body size.", fontsize=11)
    doc.save(p)
    blocks = parse_pdf(p, META)
    assert {b.section for b in blocks} == {"Setup", "Codes"}
    assert any("configuration menu" in b.text for b in blocks)
    assert any("enter one of these codes:" in b.text for b in blocks)


def test_html_nested_list_not_duplicated_and_table_rows_joined(tmp_path):
    p = tmp_path / "oven.html"
    p.write_text("""<html><body><h2>Safety</h2>
    <ul><li>To reduce the risk of fire:<ul><li>Do not overcook food in the oven.</li>
    <li>Keep the door closed if materials ignite.</li></ul></li></ul>
    <h2>Specs</h2><table><tr><td>Model:</td><td>EB544N</td></tr>
    <tr><td>Rated Voltage:</td><td>120 V</td></tr></table>
    <p>Illustration shows a diagram of the oven parts and buttons.</p></body></html>""")
    blocks = parse_html(p, META)
    safety = next(b for b in blocks if b.section == "Safety").text
    assert safety.count("Do not overcook") == 1 and "To reduce the risk of fire:" in safety
    specs = next(b for b in blocks if b.section == "Specs").text
    assert "Model: EB544N" in specs and "Illustration" not in specs


def test_unicode_cleanup():
    from app.ingestion.cleaning import fix_hyphenation, normalize_whitespace

    assert normalize_whitespace("ﬁx the ﬂywheel") == "fix the flywheel"
    assert fix_hyphenation("config\u00ad\nuration") == "configuration"


def test_numeric_codes_are_not_headings(tmp_path):
    p = tmp_path / "t.pdf"
    doc = fitz.open()
    for n in range(2):
        page = doc.new_page()
        page.insert_text((50, 80), ["Parameters", "Wiring"][n], fontsize=18)
        page.insert_text((50, 120), "01 1", fontsize=11, fontname="hebo")
        for i in range(4):
            page.insert_text((50, 140 + i * 16), f"Parameter description {n}-{i} for the thermostat.", fontsize=11)
    doc.save(p)
    assert {b.section for b in parse_pdf(p, META)} == {"Parameters", "Wiring"}
=======
>>>>>>> 12a01701187fe81b02a6d357ae9cc59f9a71b514
