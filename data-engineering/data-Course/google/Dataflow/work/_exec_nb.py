#!/usr/bin/env python3
"""Execute a notebook with nbclient and report the outcome.

This is the same mechanism `jupyter nbconvert --to notebook --execute`
uses: nbformat reads the notebook, nbclient runs every code cell in a
kernel, and the executed notebook is written back out.
"""
import sys
import traceback
from pathlib import Path

import nbformat
from nbclient import NotebookClient

nb_path = Path(sys.argv[1])
out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp") / nb_path.name

nb = nbformat.read(nb_path, as_version=4)
client = NotebookClient(
    nb,
    timeout=900,
    kernel_name="python3",
    resources={"metadata": {"path": str(Path.cwd())}},
    allow_errors=False,
)
try:
    client.execute()
except Exception as exc:
    print("EXECUTION FAILED:", type(exc).__name__)
    message = str(exc)
    print(message[:3000])
    # Show the failing cell's source.
    for i, cell in enumerate(nb.cells):
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                print("=" * 70)
                print(f"ERROR in cell {i}: {output.get('ename')}: {output.get('evalue')}")
                print("-" * 70)
                print("\n".join(output.get("traceback", []))[-2500:])
                sys.exit(1)
    traceback.print_exc()
    sys.exit(1)

out_path.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, str(out_path))
print(f"EXECUTED OK -> {out_path}")
print(f"cells: {len(nb.cells)}")
