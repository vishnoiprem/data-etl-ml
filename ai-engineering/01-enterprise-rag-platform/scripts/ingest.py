"""CLI: ingest sample_data/docs into the index.

Usage:
    python scripts/ingest.py
    python scripts/ingest.py --dir /path/to/docs --rebuild
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Ensure project src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer
from rich.console import Console
from rich.table import Table

from src.config import settings
from src.embedding.embedder import get_embedder
from src.ingestion.chunker import RecursiveChunker, chunk_documents
from src.ingestion.loader import load_directory
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.vector_store import get_vector_store

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    dir: Path = typer.Option(None, help="Directory of source docs (default: sample_data/docs)"),
    rebuild: bool = typer.Option(False, help="Wipe existing index before ingesting"),
    chunk_size: int = typer.Option(None, help="Override CHUNK_SIZE"),
    overlap: int = typer.Option(None, help="Override CHUNK_OVERLAP"),
):
    src_dir = Path(dir or settings.SAMPLE_DATA_DIR)
    if rebuild and settings.INDEX_DIR.exists():
        console.print(f"[yellow]Rebuild: clearing {settings.INDEX_DIR}[/yellow]")
        shutil.rmtree(settings.INDEX_DIR)
        settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)

    console.rule(f"[bold cyan]Ingesting {src_dir}[/bold cyan]")

    # 1. Load
    docs = list(load_directory(src_dir))
    console.print(f"Loaded [bold]{len(docs)}[/bold] documents")

    # 2. Chunk
    chunker = RecursiveChunker(
        chunk_size=chunk_size or settings.CHUNK_SIZE,
        overlap=overlap or settings.CHUNK_OVERLAP,
    )
    chunks = chunk_documents(docs, chunker)

    # 3. Embed
    console.print(f"Embedding [bold]{len(chunks)}[/bold] chunks (mode={settings.AI_ENGINEERING_MODE})...")
    embedder = get_embedder()
    vectors = embedder.embed([c.text for c in chunks])

    # 4. Index (vector + BM25)
    vstore = get_vector_store(dim=embedder.dim)
    vstore.upsert(chunks, vectors)

    bm25 = BM25Retriever()
    bm25.fit(chunks)

    # 5. Report
    table = Table(title="Ingestion Summary", show_lines=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold")
    table.add_row("Documents", str(len(docs)))
    table.add_row("Chunks", str(len(chunks)))
    table.add_row("Embedding model", embedder.__class__.__name__)
    table.add_row("Embedding dim", str(embedder.dim))
    table.add_row("Vector store", vstore.__class__.__name__)
    table.add_row("Index dir", str(settings.INDEX_DIR))
    console.print(table)
    console.print("[bold green]✓ Ingestion complete[/bold green]")


if __name__ == "__main__":
    app()
