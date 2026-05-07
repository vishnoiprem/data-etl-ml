"""CLI: convert raw_labels.jsonl into instruction.jsonl and classification.jsonl."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table

from src.data_prep import (
    load_jsonl, write_jsonl, to_instruction_record, to_classification_record,
)

ROOT = Path(__file__).resolve().parent.parent
console = Console()


def main():
    raw = load_jsonl(ROOT / "sample_data" / "raw_labels.jsonl")
    out_dir = ROOT / "data" / "processed"

    instr = [to_instruction_record(r) for r in raw]
    cls = [to_classification_record(r) for r in raw]

    write_jsonl(instr, out_dir / "instruction.jsonl")
    write_jsonl(cls, out_dir / "classification.jsonl")

    table = Table(title="Data preparation")
    table.add_column("Output", style="cyan")
    table.add_column("Records", style="bold")
    table.add_row(str(out_dir / "instruction.jsonl"), str(len(instr)))
    table.add_row(str(out_dir / "classification.jsonl"), str(len(cls)))
    console.print(table)

    # Show one example so you can see the format
    console.print("\n[bold]Example instruction record:[/bold]")
    import json
    console.print_json(json.dumps(instr[0]))


if __name__ == "__main__":
    main()
