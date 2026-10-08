"""Ingest the sample corpus, build all indices, persist to ./data."""
from __future__ import annotations

import sys
from pathlib import Path

# Make `src` importable when run as `python scripts/ingest.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer
from loguru import logger

from src.config import get_settings
from src.pipeline import GraphRAGPipeline


app = typer.Typer(add_completion=False)


@app.command()
def main(
    corpus_dir: Path = typer.Option(
        None, help="Directory of .md files (defaults to sample_data/corpus)"
    ),
    rebuild: bool = typer.Option(True, help="Rebuild from scratch (vs. load persisted)"),
) -> None:
    s = get_settings()
    corpus_dir = corpus_dir or s.sample_data_dir / "corpus"
    pipeline = GraphRAGPipeline()
    if rebuild or not (s.graph_path().exists()):
        logger.info(f"Building pipeline from {corpus_dir}")
        pipeline.build(corpus_dir)
    else:
        logger.info("Loading persisted pipeline")
        pipeline.load()
    logger.info("Done. Run `make query Q=\"...\"` to ask a question.")


if __name__ == "__main__":
    app()
