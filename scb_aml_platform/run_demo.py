"""
SCB AML Platform — Interactive Demo
Demonstrates all platform capabilities with dummy data.

Run: python run_demo.py
"""

import sys
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

console = Console()


def section(title: str):
    console.print(f"\n[bold cyan]{'─'*60}[/bold cyan]")
    console.print(f"[bold yellow]{title}[/bold yellow]")
    console.print(f"[bold cyan]{'─'*60}[/bold cyan]")


def run_demo():
    console.print(Panel(
        Text(
            "SCB AML Platform — Interactive Demo\n"
            "Standard Chartered Bank | Group Financial Crime Compliance\n"
            "Built by: Prem Vishnoi, Big Data Consultant (2016-2018)\n"
            "Coverage: 15 Countries | 50M+ Daily Transactions | T+1 SLA",
            justify="center"
        ),
        style="bold green",
    ))

    # ── 1. Run the full pipeline
    section("STEP 1: Run Full AML Pipeline (all 9 steps)")
    console.print("Running pipeline... this may take 60-120 seconds.")
    from scb_aml_platform.orchestration.pipeline_orchestrator import run_pipeline
    run_pipeline()

    # ── 2. Show risk distribution
    section("STEP 2: Customer Risk Band Distribution")
    try:
        import pandas as pd
        profiles = pd.read_parquet(
            Path(__file__).parent / "data" / "processed" / "customer_risk_profiles.parquet"
        )
        table = Table(title="Customer Risk Profiles", show_header=True)
        table.add_column("Risk Band", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Pct", justify="right")

        dist = profiles["risk_band"].value_counts()
        total = len(profiles)
        for band, cnt in dist.items():
            color = {"CRITICAL": "red", "HIGH": "orange3", "MEDIUM": "yellow", "LOW": "green"}.get(band, "white")
            table.add_row(f"[{color}]{band}[/{color}]", str(cnt), f"{cnt/total*100:.1f}%")
        console.print(table)
    except Exception as e:
        console.print(f"[yellow]Risk profiles not available: {e}[/yellow]")

    # ── 3. Demo Lucid Search
    section("STEP 3: Lucid Search — Use Case 1: Mohammed Al-Rahman")
    try:
        from scb_aml_platform.lucid_search.api.search_engine import LucidSearchEngine
        engine = LucidSearchEngine()

        result = engine.search("Mohammed Al-Rahman", max_results=5)
        console.print(f"Query: 'Mohammed Al-Rahman'")
        console.print(f"Results: {result['total']} | Time: {result['search_time_ms']}ms | Backend: {result['backend']}")

        if result["results"]:
            table = Table(show_header=True)
            table.add_column("Entity ID")
            table.add_column("Name")
            table.add_column("Country")
            table.add_column("Risk")
            table.add_column("PEP")
            table.add_column("Match%")

            for r in result["results"][:5]:
                risk = str(r.get("risk_band") or r.get("risk_rating") or "")
                color = {"CRITICAL": "red", "HIGH": "orange3", "high": "orange3",
                         "MEDIUM": "yellow", "medium": "yellow",
                         "LOW": "green", "low": "green"}.get(risk, "white")
                table.add_row(
                    str(r.get("entity_id") or r.get("customer_id", ""))[:16],
                    str(r.get("customer_name", ""))[:30],
                    str(r.get("country_code", "")),
                    f"[{color}]{risk}[/{color}]",
                    str(r.get("pep_flag", "")),
                    f"{r.get('match_score', 0):.0f}%",
                )
            console.print(table)
    except Exception as e:
        console.print(f"[yellow]Lucid Search demo: {e}[/yellow]")

    # ── 4. Show alerts
    section("STEP 4: AML Alert Summary")
    try:
        import pandas as pd
        alerts = pd.read_parquet(
            Path(__file__).parent / "output" / "alerts" / "aml_alert_master.parquet"
        )
        table = Table(title="AML Alerts Generated", show_header=True)
        table.add_column("Rule")
        table.add_column("Alert Type")
        table.add_column("Count", justify="right")
        table.add_column("Avg Score", justify="right")

        for (rule, atype), grp in alerts.groupby(["rule_id", "alert_type"]):
            table.add_row(rule, atype, str(len(grp)), f"{grp['alert_score'].mean():.0f}")
        console.print(table)
    except Exception as e:
        console.print(f"[yellow]Alerts not available: {e}[/yellow]")

    # ── 5. Lucid Search API instructions
    section("STEP 5: Start Lucid Search API")
    console.print("""
[bold]To start the Lucid Search REST API:[/bold]

  cd scb_aml_platform/lucid_search/api
  uvicorn app:app --host 0.0.0.0 --port 8000 --reload

[bold]Then open:[/bold]
  http://localhost:8000/docs          (Swagger UI)
  http://localhost:8000/search?q=Mohammed+Al-Rahman
  http://localhost:8000/demo/use-case-1
  http://localhost:8000/demo/use-case-2
  http://localhost:8000/stats
""")

    console.print(Panel(
        "[bold green]Demo Complete![/bold green]\n"
        "All pipeline steps have run successfully.\n"
        "Check output/ and data/processed/ for all generated files.",
        style="green"
    ))


if __name__ == "__main__":
    run_demo()
