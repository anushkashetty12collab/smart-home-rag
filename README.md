# smart-home-rag

RAG support assistant over smart-home device manuals and FAQs.

## Phase 1 quickstart
```bash
uv sync
cp .env.example .env
# put PDFs in data/raw/pdf, HTML in data/raw/html, and list them in data/raw/manifest.csv
uv run python -m app.ingestion.run_phase1   # -> data/processed/blocks.jsonl
uv run pytest && uv run ruff check .
```
