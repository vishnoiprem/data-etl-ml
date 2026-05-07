"""CLI: tiny LoRA-style fine-tuning demo on the classifier."""
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
    # Load classification data
    path = ROOT / "data" / "processed" / "classification.jsonl"
    if not path.exists():
        console.print("[red]Run scripts/prepare_data.py first.[/red]")
        return

    records = [json.loads(line) for line in path.read_text().splitlines() if line]
    texts = [r["text"] for r in records]
    labels = np.array([LABEL_TO_IDX[r["label"]] for r in records], dtype=np.int64)

    # Train/test split (80/20)
    rng = np.random.default_rng(42)
    idx = rng.permutation(len(records))
    cut = int(0.8 * len(records))
    tr, te = idx[:cut], idx[cut:]

    X = featurize(texts, dim=256)
    Xtr, ytr = X[tr], labels[tr]
    Xte, yte = X[te], labels[te]

    base = FrozenBaseClassifier.random(feat_dim=256, n_classes=4, seed=7)
    base_acc = evaluate(base, None, Xte, yte)
    console.print(f"[dim]Frozen-base test accuracy:[/dim] {base_acc:.2%}")

    adapter = LoRAAdapter.init(feat_dim=256, n_classes=4, rank=4, seed=0)
    base_params = base.W.size + base.b.size
    adapter_params = adapter.num_params()
    console.print(
        f"[dim]Trainable params:[/dim] adapter={adapter_params}, "
        f"frozen base={base_params} ({adapter_params/base_params:.2%} of base)"
    )

    losses = train_lora(base, adapter, Xtr, ytr, epochs=200, lr=0.5, log_every=40)

    train_acc = evaluate(base, adapter, Xtr, ytr)
    test_acc = evaluate(base, adapter, Xte, yte)

    table = Table(title="LoRA fine-tune result")
    table.add_column("Stage", style="cyan")
    table.add_column("Accuracy", style="bold")
    table.add_row("Pre-tune (frozen base, no adapter)", f"{base_acc:.2%}")
    table.add_row("Post-tune (base + LoRA adapter), train", f"{train_acc:.2%}")
    table.add_row("Post-tune (base + LoRA adapter), test", f"{test_acc:.2%}")
    table.add_row("Final loss", f"{losses[-1]:.4f}")
    console.print(table)


if __name__ == "__main__":
    main()
