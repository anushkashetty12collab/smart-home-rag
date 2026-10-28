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
