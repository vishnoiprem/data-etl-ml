"""CLI: ask a question.

Usage:
    python scripts/query.py "What is our PTO policy?"
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.generation.rag_pipeline import RagPipeline

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(question: str = typer.Argument(..., help="Question to ask")):
    pipeline = RagPipeline()
    result = pipeline.ask(question)

    console.print(Panel.fit(f"[bold cyan]{result.question}[/bold cyan]", title="Question"))

    if result.refused:
        console.print(Panel(
            f"[yellow]I don't know based on available documents.[/yellow]\n\n"
            f"[dim]Reason: {result.refusal_reason}[/dim]",
            title="[red]Refused[/red]",
        ))
    else:
        console.print(Panel(result.answer, title="[green]Answer[/green]"))

        # Sources
        sources = Table(title="Sources", show_lines=False)
        sources.add_column("#")
        sources.add_column("Title", style="cyan")
        sources.add_column("Source", style="magenta")
        sources.add_column("Score", style="bold")
        sources.add_column("chunk_id", style="dim")
        for i, s in enumerate(result.sources, 1):
            sources.add_row(str(i), s.title, s.source, f"{s.score:.3f}", s.chunk_id)
        console.print(sources)

    # Telemetry
    t = result.telemetry
    tel = Table(title="Telemetry", show_header=False, show_lines=False)
    tel.add_column(style="cyan")
    tel.add_column(style="bold")
    for k in ("mode", "model", "retrieve_top_k", "retrieve_ms", "llm_ms", "total_ms", "in_tokens", "out_tokens"):
        if k in t:
            tel.add_row(k, str(t[k]))
    console.print(tel)


if __name__ == "__main__":
    app()
