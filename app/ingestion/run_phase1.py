"""Phase 1 CLI: parse + clean everything in data/raw -> data/processed/blocks.jsonl

Run:  uv run python -m app.ingestion.run_phase1
"""
import csv
import json
import logging
from pathlib import Path

from app.core.config import settings
<<<<<<< HEAD
from app.ingestion.parsers import diagnose_pdf, parse_html, parse_pdf, pdf_text_chars
=======
from app.ingestion.parsers import parse_html, parse_pdf
>>>>>>> 12a01701187fe81b02a6d357ae9cc59f9a71b514

log = logging.getLogger("ingest")


def load_manifest(raw_dir: Path) -> dict[str, dict]:
    path = raw_dir / "manifest.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        return {row["filename"]: row for row in csv.DictReader(f)}


def meta_for(path: Path, manifest: dict[str, dict]) -> dict:
    row = manifest.get(path.name, {})
    return {
        "device_model": row.get("device_model") or path.stem,
        "device_type": row.get("device_type") or "unknown",
        "doc_type": row.get("doc_type") or "other",
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    manifest = load_manifest(settings.raw_dir)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = settings.processed_dir / "blocks.jsonl"

    total = 0
    with out_path.open("w", encoding="utf-8") as out:
        for path in sorted(settings.raw_dir.rglob("*")):
            suffix = path.suffix.lower()
            if suffix not in {".pdf", ".html", ".htm"}:
                continue
            meta = meta_for(path, manifest)
            try:
                if suffix == ".pdf":
                    blocks = parse_pdf(path, meta, settings.header_footer_threshold, settings.min_page_chars)
                else:
                    blocks = parse_html(path, meta)
            except Exception:
                log.exception("Failed to parse %s", path.name)
                continue
<<<<<<< HEAD
            if not blocks:
                reason = diagnose_pdf(path) if suffix == ".pdf" else "no <p>/<li>/<h*> text found (JS-rendered page?)"
                log.warning("ZERO BLOCKS %s -> %s", path.name, reason)
                continue
            for b in blocks:
                out.write(b.model_dump_json() + "\n")
            total += len(blocks)
            msg = f"{path.name} -> {len(blocks)} blocks"
            if suffix == ".pdf":
                raw = pdf_text_chars(path) or 1
                kept = sum(len(b.text) for b in blocks) / raw
                msg += f", {kept:.0%} of text kept"
                if kept < 0.6:
                    log.warning("LOW COVERAGE %s (run debug_pdf on a page to see why)", msg)
            log.info(msg)
=======
            for b in blocks:
                out.write(b.model_dump_json() + "\n")
            total += len(blocks)
            log.info("%s -> %d blocks", path.name, len(blocks))
>>>>>>> 12a01701187fe81b02a6d357ae9cc59f9a71b514
    log.info("Wrote %d blocks to %s", total, out_path)


if __name__ == "__main__":
    main()
