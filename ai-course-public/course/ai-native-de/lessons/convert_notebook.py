"""Convert the fake `<cell id=...>...</cell id=...>` notebook format to real
Jupyter JSON. Run from the lessons/ directory.

Usage:
    python3 convert_notebook.py <fake.ipynb> <output_real.ipynb>
    python3 convert_notebook.py --all
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CELL_OPEN = re.compile(r'<cell\s+id="cell-(\d+)"\s*>', re.IGNORECASE)
CELL_TYPE = re.compile(r'<cell_type>(\w+)</cell_type>', re.IGNORECASE)
# Closing tags come in two flavors across modules:
#   </cell id="cell-N">       (proper, M11-M19)
#   </cell id="cell-N>        (missing close quote, M03-M10)
CELL_CLOSE = re.compile(r'</cell\s+id="cell-\d+"?\s*>', re.IGNORECASE)


def parse_fake_format(text: str) -> list[dict]:
    """Return a list of {cell_type, source_lines} from the fake XML-ish format."""
    # Tokenize: find each <cell id="cell-N"> ... </cell id="cell-N"> block
    cells: list[dict] = []
    pos = 0
    while pos < len(text):
        m = CELL_OPEN.search(text, pos)
        if not m:
            break
        n = int(m.group(1))
        start = m.end()
        # find matching close
        close_m = CELL_CLOSE.search(text, start)
        if not close_m:
            break
        body = text[start:close_m.start()]
        # extract cell type, if any
        type_m = CELL_TYPE.search(body)
        if type_m:
            cell_type = type_m.group(1).lower()
            # remove the cell_type tag from the body
            body = body[:type_m.start()] + body[type_m.end():]
        else:
            cell_type = "code"
        # strip leading/trailing blank lines
        body = body.strip("\n")
        # split into source lines (preserve single trailing \n per line)
        lines = body.split("\n")
        # remove empty leading/trailing
        while lines and lines[0].strip() == "":
            lines.pop(0)
        while lines and lines[-1].strip() == "":
            lines.pop()
        # add trailing newline to each line so nbformat is happy
        source = [ln + "\n" for ln in lines]
        # nbformat wants the last line to NOT have a trailing newline
        if source:
            source[-1] = source[-1].rstrip("\n")
        cells.append({"cell_type": cell_type, "source": source, "_n": n})
        pos = close_m.end()
    # sort by id
    cells.sort(key=lambda c: c["_n"])
    return cells


def to_ipynb(cells: list[dict]) -> dict:
    """Build a real Jupyter notebook dict."""
    nb_cells = []
    for c in cells:
        if c["cell_type"] == "markdown":
            nb_cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": c["source"],
            })
        else:  # code
            nb_cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": c["source"],
            })
    return {
        "cells": nb_cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.10",
                "mimetype": "text/x-python",
                "file_extension": ".py",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def convert_file(src: Path, dst: Path) -> int:
    text = src.read_text()
    cells = parse_fake_format(text)
    nb = to_ipynb(cells)
    dst.write_text(json.dumps(nb, indent=1))
    return len(cells)


def main() -> None:
    if len(sys.argv) >= 3:
        n = convert_file(Path(sys.argv[1]), Path(sys.argv[2]))
        print(f"  wrote {sys.argv[2]} ({n} cells)")
        return
    if len(sys.argv) == 2 and sys.argv[1] == "--all":
        lessons = Path(__file__).resolve().parent
        for m_dir in sorted(lessons.iterdir()):
            if not m_dir.is_dir() or not m_dir.name.startswith("m"):
                continue
            for ipynb in m_dir.glob("*.ipynb"):
                cells = parse_fake_format(ipynb.read_text())
                # skip if already real JSON
                try:
                    json.loads(ipynb.read_text())
                    continue  # already real
                except Exception:
                    pass
                nb = to_ipynb(cells)
                ipynb.write_text(json.dumps(nb, indent=1))
                print(f"  converted: {ipynb.relative_to(lessons)}  ({len(cells)} cells)")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
