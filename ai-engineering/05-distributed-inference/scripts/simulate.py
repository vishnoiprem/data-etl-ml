"""CLI: run the cost-optimization simulation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.simulator import (
    make_workload, run_baseline_opus, run_router_only, run_router_with_cache,
)

console = Console()


def main():
    workload = make_workload(n=400)
    console.rule(f"[bold cyan]Inference cost simulation — {len(workload)} requests[/bold cyan]")

    s1 = run_baseline_opus(workload)
    s2 = run_router_only(workload)
    s3 = run_router_with_cache(workload)

    table = Table(title="Strategy comparison")
    table.add_column("Strategy", style="cyan")
    table.add_column("Cost USD", style="bold")
    table.add_column("p50 ms")
    table.add_column("p95 ms")
    table.add_column("Cache hits")
    table.add_column("Mix")
    for s in (s1, s2, s3):
        mix_str = ", ".join(f"{k}={v}" for k, v in sorted(s.by_model.items(), key=lambda x: -x[1]))
        table.add_row(
            s.strategy, f"${s.cost_usd:.3f}", f"{s.p50_latency_ms:.0f}", f"{s.p95_latency_ms:.0f}",
            f"{s.cache_hits}/{s.n_requests}", mix_str,
        )
    console.print(table)

    save_router = (s1.cost_usd - s2.cost_usd) / s1.cost_usd if s1.cost_usd else 0
    save_full = (s1.cost_usd - s3.cost_usd) / s1.cost_usd if s1.cost_usd else 0
    console.print(Panel.fit(
        f"Router only:   [bold]{save_router:.0%}[/bold] cost reduction vs always-Opus\n"
        f"Router+cache:  [bold]{save_full:.0%}[/bold] cost reduction vs always-Opus\n"
        f"Cache hit rate: {s3.cache_hits / s3.n_requests:.0%}\n"
        f"Annualized at 16M qps/yr: baseline ${s1.cost_usd / s1.n_requests * 16_000_000:,.0f}, "
        f"optimized ${s3.cost_usd / s3.n_requests * 16_000_000:,.0f}",
        title="Savings",
    ))


if __name__ == "__main__":
    main()
