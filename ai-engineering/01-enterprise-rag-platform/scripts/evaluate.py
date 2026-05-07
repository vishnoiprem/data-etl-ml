"""CLI: run the evaluation harness.

Usage:
    python scripts/evaluate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table

from src.eval.ragas_eval import DEFAULT_GOLDEN, run_eval
from src.generation.rag_pipeline import RagPipeline

console = Console()


def main():
    console.rule("[bold cyan]Evaluation[/bold cyan]")
    pipeline = RagPipeline()
    report = run_eval(pipeline, DEFAULT_GOLDEN)

    table = Table(title="Eval Report", show_lines=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold")
    table.add_column("Target", style="dim")
    rows = [
        ("Items evaluated", str(report.n_items), "-"),
        ("Recall@5", f"{report.recall_at_5:.2%}", "≥ 85%"),
        ("MRR@10", f"{report.mrr_at_10:.3f}", "≥ 0.700"),
        ("Faithfulness (lite)", f"{report.avg_faithfulness:.2%}", "≥ 80%"),
        ("Coverage", f"{report.avg_coverage:.2%}", "≥ 70%"),
        ("Refusal rate", f"{report.refusal_rate:.2%}", "< 20%"),
        ("Avg latency (ms)", f"{report.avg_total_ms:.0f}", "< 2500"),
    ]
    for r in rows:
        table.add_row(*r)
    console.print(table)


if __name__ == "__main__":
    main()
