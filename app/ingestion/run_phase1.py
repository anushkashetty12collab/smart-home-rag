"""Phase 1 CLI: parse + clean everything in data/raw -> data/processed/blocks.jsonl

Run:  uv run python -m app.ingestion.run_phase1
"""
import csv
import json
import logging
from pathlib import Path

from app.core.config import settings
from app.ingestion.parsers import parse_html, parse_pdf

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
            for b in blocks:
                out.write(b.model_dump_json() + "\n")
            total += len(blocks)
            log.info("%s -> %d blocks", path.name, len(blocks))
    log.info("Wrote %d blocks to %s", total, out_path)


if __name__ == "__main__":
    main()
