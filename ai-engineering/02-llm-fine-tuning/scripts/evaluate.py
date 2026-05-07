"""CLI: pre vs post fine-tune evaluation summary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from rich.console import Console
from rich.table import Table

from src.lora_demo import (
    LABEL_TO_IDX, FrozenBaseClassifier, LoRAAdapter,
    evaluate, featurize, train_lora,
)

ROOT = Path(__file__).resolve().parent.parent
console = Console()


def main():
    path = ROOT / "data" / "processed" / "classification.jsonl"
    if not path.exists():
        console.print("[red]Run scripts/prepare_data.py first.[/red]")
        return

    records = [json.loads(line) for line in path.read_text().splitlines() if line]
    texts = [r["text"] for r in records]
    labels = np.array([LABEL_TO_IDX[r["label"]] for r in records], dtype=np.int64)

    rng = np.random.default_rng(42)
    idx = rng.permutation(len(records))
    cut = int(0.8 * len(records))
    tr, te = idx[:cut], idx[cut:]

    X = featurize(texts, dim=256)
    base = FrozenBaseClassifier.random(feat_dim=256, n_classes=4, seed=7)
    pre_acc = evaluate(base, None, X[te], labels[te])

    adapter = LoRAAdapter.init(feat_dim=256, n_classes=4, rank=4, seed=0)
    train_lora(base, adapter, X[tr], labels[tr], epochs=200, lr=0.5, log_every=1000)
    post_acc = evaluate(base, adapter, X[te], labels[te])

    table = Table(title="Eval Report — pre vs post fine-tune")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold")
    table.add_column("Target", style="dim")
    table.add_row("Pre-tune accuracy", f"{pre_acc:.2%}", "-")
    table.add_row("Post-tune accuracy", f"{post_acc:.2%}", "≥ 92%")
    table.add_row("Lift", f"{(post_acc - pre_acc) * 100:.1f} pts", "≥ 20 pts")
    console.print(table)


if __name__ == "__main__":
    main()
