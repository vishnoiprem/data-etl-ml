"""Run all three eval sets across all four strategies; print a Markdown table."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer
from rich.console import Console
from rich.markdown import Markdown

from src.config import get_settings
from src.pipeline import GraphRAGPipeline


app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    sample_data_dir: Path = typer.Option(None, help="Dir with eval_*.jsonl files"),
    output_jsonl: Path = typer.Option(None, help="Optional path to write per-row results"),
) -> None:
    s = get_settings()
    sample_data_dir = sample_data_dir or s.sample_data_dir
    console.rule("[bold]Loading pipeline[/bold]")
    pipeline = GraphRAGPipeline()
    try:
        pipeline.load()
    except FileNotFoundError as e:
        console.print(f"[red]No persisted indices found[/red] ({e}).")
        console.print("Run [bold]make ingest[/bold] first.")
        raise typer.Exit(code=1)

    eval_files = [
        ("single-hop", sample_data_dir / "eval_golden.jsonl"),
        ("two-hop", sample_data_dir / "eval_twohop.jsonl"),
        ("adversarial", sample_data_dir / "eval_adversarial.jsonl"),
    ]
    full_report = None
    for label, path in eval_files:
        if not path.exists():
            console.print(f"[yellow]Skipping {label}: {path} not found[/yellow]")
            continue
        console.rule(f"[bold]Eval: {label} ({path.name})[/bold]")
        report = pipeline.eval(path)
        if full_report is None:
            full_report = report
        else:
            full_report.rows.extend(report.rows)

    if full_report is None or not full_report.rows:
        console.print("[red]No eval sets found.[/red]")
        raise typer.Exit(code=1)

    console.rule("[bold]Strategy comparison[/bold]")
    table_md = full_report.markdown_table()
    console.print(Markdown(table_md))
    # Also print the raw markdown so it can be pasted into the README
    print()
    print(table_md)
    print()

    if output_jsonl is None:
        output_jsonl = s.data_dir / "eval_report.jsonl"
    full_report.save_jsonl(output_jsonl)
    console.print(f"Wrote per-row report to [bold]{output_jsonl}[/bold]")


if __name__ == "__main__":
    app()
