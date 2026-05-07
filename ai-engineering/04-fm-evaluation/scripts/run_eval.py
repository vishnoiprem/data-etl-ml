"""CLI: run baseline vs candidate model and produce regression verdict."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.eval_runner import detect_regression, evaluate_model, load_jsonl
from src.models import BaselineModel, RegressionModel

ROOT = Path(__file__).resolve().parent.parent
console = Console()


def main():
    console.rule("[bold cyan]FM Evaluation Framework[/bold cyan]")
    golden = load_jsonl(ROOT / "sample_data" / "golden.jsonl")
    adv = load_jsonl(ROOT / "sample_data" / "adversarial.jsonl")

    baseline_rep = evaluate_model(BaselineModel(), golden, adv)
    candidate_rep = evaluate_model(RegressionModel(), golden, adv)

    # Per-model summary
    for rep in (baseline_rep, candidate_rep):
        table = Table(title=f"Model: {rep.model_name}", show_lines=False)
        table.add_column("Metric", style="cyan")
        table.add_column("N")
        table.add_column("Mean", style="bold")
        for m, vals in rep.by_metric().items():
            table.add_row(m, str(len(vals)), f"{vals.mean():.2%}")
        table.add_row("[dim]latency_ms p50[/dim]", "-", f"{int(__import__('numpy').median(rep.latencies()))}")
        console.print(table)

    # Regression verdicts
    verdicts = detect_regression(baseline_rep, candidate_rep, threshold=0.05)
    table = Table(title="Regression detection (candidate - baseline)")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline")
    table.add_column("Candidate")
    table.add_column("Δ (95% CI)")
    table.add_column("Verdict", style="bold")
    any_regression = False
    for v in verdicts:
        verdict = "[red]REGRESSION[/red]" if v.regression else "[green]ok[/green]"
        if v.regression:
            any_regression = True
        table.add_row(
            v.metric,
            f"{v.baseline_mean:.2%}",
            f"{v.candidate_mean:.2%}",
            f"{v.delta:+.3f}  [{v.delta_lo:+.3f}, {v.delta_hi:+.3f}]",
            verdict,
        )
    console.print(table)

    if any_regression:
        console.print(Panel.fit(
            "[bold red]GATE FAILED[/bold red] — at least one metric regressed.\n"
            "Promotion blocked. Review the candidate before retrying.",
            title="Promotion decision",
        ))
    else:
        console.print(Panel.fit(
            "[bold green]GATE PASSED[/bold green] — no significant regressions.",
            title="Promotion decision",
        ))


if __name__ == "__main__":
    main()
