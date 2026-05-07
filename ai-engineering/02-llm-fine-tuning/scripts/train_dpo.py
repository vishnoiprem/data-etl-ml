"""CLI: DPO preference-tuning demo on synthetic preference pairs."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table

from src.dpo_demo import load_pairs, train_dpo

ROOT = Path(__file__).resolve().parent.parent
console = Console()


def main():
    pairs = load_pairs(ROOT / "sample_data" / "preferences.jsonl")
    console.print(f"Loaded [bold]{len(pairs)}[/bold] preference pairs")

    theta, ref, losses, seps = train_dpo(pairs, epochs=200, lr=0.4, beta=0.5)

    table = Table(title="DPO training progress")
    table.add_column("Epoch", style="cyan")
    table.add_column("Loss", style="bold")
    table.add_column("Reward separation (chosen − rejected)", style="green")
    for ep in (0, 49, 99, 149, 199):
        table.add_row(str(ep), f"{losses[ep]:.4f}", f"{seps[ep]:+.3f}")
    console.print(table)
    console.print(
        "[dim]Interpretation: higher reward separation means the policy now "
        "prefers chosen responses over rejected ones, while staying close to "
        "the reference (β=0.5).[/dim]"
    )


if __name__ == "__main__":
    main()
