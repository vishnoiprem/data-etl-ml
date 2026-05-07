"""CLI: run all sample applications and summarize."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.orchestrator import run_orchestrator

ROOT = Path(__file__).resolve().parent.parent
console = Console()


def main():
    apps = [json.loads(l) for l in (ROOT / "sample_data" / "applications.jsonl").read_text().splitlines() if l]
    console.rule(f"[bold cyan]Running {len(apps)} loan applications[/bold cyan]")

    decisions = []
    for a in apps:
        d = run_orchestrator(a)
        decisions.append(d)

    summary = Table(title="Decision summary")
    summary.add_column("App", style="cyan")
    summary.add_column("Name")
    summary.add_column("Amount")
    summary.add_column("Decision", style="bold")
    summary.add_column("Steps")
    summary.add_column("Reasons", style="dim")
    for a, d in zip(apps, decisions):
        color = {"approve": "green", "decline": "red", "refer": "yellow"}.get(d.decision, "white")
        summary.add_row(
            a["app_id"], a["name"], f"${a['amount']:,}",
            f"[{color}]{d.decision}[/{color}]",
            str(d.cost_steps),
            "; ".join(d.reasons)[:60],
        )
    console.print(summary)

    counts = Counter(d.decision for d in decisions)
    auto = counts.get("approve", 0) + counts.get("decline", 0)
    stp_rate = auto / len(decisions) if decisions else 0.0
    console.print(Panel.fit(
        f"Decisions: {dict(counts)}\n"
        f"Straight-through rate (approve+decline / total): [bold]{stp_rate:.0%}[/bold]\n"
        f"Avg steps per decision: [bold]{sum(d.cost_steps for d in decisions)/len(decisions):.1f}[/bold]",
        title="KPIs",
    ))

    # Show one full trace for inspection
    console.print(Panel.fit(
        "Showing full trace for first application…", title="Trace example",
    ))
    for s in decisions[0].trace[:8]:
        console.print(f"  [{s['agent']}] {s['action']}({s['args']}) → ok={s['ok']}")


if __name__ == "__main__":
    main()
