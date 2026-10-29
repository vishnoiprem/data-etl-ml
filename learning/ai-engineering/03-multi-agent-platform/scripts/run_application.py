"""CLI: run a single loan application end-to-end."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer
from rich.console import Console
from rich.panel import Panel

from src.orchestrator import run_orchestrator

ROOT = Path(__file__).resolve().parent.parent
console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def main(app_id: str = typer.Argument("APP-001")):
    apps = [json.loads(l) for l in (ROOT / "sample_data" / "applications.jsonl").read_text().splitlines() if l]
    application = next((a for a in apps if a["app_id"] == app_id), None)
    if application is None:
        console.print(f"[red]No app with id {app_id}[/red]")
        raise typer.Exit(1)

    console.print(Panel.fit(json.dumps(application, indent=2), title=f"Application {app_id}"))
    decision = run_orchestrator(application)

    color = {"approve": "green", "decline": "red", "refer": "yellow"}.get(decision.decision, "white")
    console.print(Panel.fit(
        f"[bold {color}]{decision.decision.upper()}[/bold {color}]\n\n" +
        "\n".join(f"• {r}" for r in decision.reasons) +
        f"\n\n[dim]KYC: {decision.kyc}\nCredit: {decision.credit}\nPolicy: {decision.policy}[/dim]",
        title="Decision",
    ))


if __name__ == "__main__":
    app()
