"""Execute every code cell in the practice notebooks and report failures.

Run from `practice/`:  python notebooks/_verify_notebooks.py
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import sys
import traceback

HERE = pathlib.Path(__file__).resolve().parent


def main() -> int:
    failures = 0
    total_cells = 0

    for path in sorted(HERE.glob("*.ipynb")):
        nb = json.loads(path.read_text(encoding="utf-8"))
        print(f"\n{'=' * 66}\n{path.name}\n{'=' * 66}")
        namespace: dict = {}

        for index, cell in enumerate(nb["cells"]):
            if cell["cell_type"] != "code":
                continue
            total_cells += 1
            source = "".join(cell["source"])
            try:
                with contextlib.redirect_stdout(io.StringIO()) as buffer:
                    exec(compile(source, f"{path.name}:cell{index}", "exec"), namespace)
                output = buffer.getvalue()
                print(f"--- cell {index} OK ---")
                if output:
                    print(output.rstrip())
            except Exception:
                failures += 1
                print(f"!!! cell {index} FAILED")
                traceback.print_exc()

    print(f"\n{'=' * 66}")
    print(f"cells executed: {total_cells}   failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
