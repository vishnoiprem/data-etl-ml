"""Standardized CSV reading and writing.

The whole course uses these three functions so exercises can swap
files for in-memory lists without rewriting code. We intentionally
avoid pandas: a course on data engineering should show what
``csv.DictReader`` and ``csv.DictWriter`` look like.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Iterator, List, Union

PathLike = Union[str, Path]


def read_csv(path: PathLike) -> List[Dict[str, str]]:
    """Read a CSV file, return a list of dicts keyed by header row.

    >>> import io, tempfile, os
    >>> tmp = tempfile.NamedTemporaryFile('w', delete=False, suffix='.csv')
    >>> _ = tmp.write("a,b\\n1,2\\n3,4\\n"); tmp.close()
    >>> read_csv(tmp.name)
    [{'a': '1', 'b': '2'}, {'a': '3', 'b': '4'}]
    >>> os.unlink(tmp.name)
    """
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def write_csv(path: PathLike, rows: List[Dict[str, Any]]) -> None:
    """Write ``rows`` to ``path`` using the first row's keys as header.

    All rows are coerced to ``str`` so a mix of ints/floats/dates round-trips.
    """
    if not rows:
        # Write an empty file — caller decides whether to add a header.
        Path(path).write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _coerce(row.get(k)) for k in fieldnames})


def stream_csv(path: PathLike) -> Iterator[Dict[str, str]]:
    """Stream a CSV one row at a time — useful for large files."""
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield dict(row)


def write_jsonl(path: PathLike, rows: List[Dict[str, Any]]) -> None:
    """Write ``rows`` to ``path`` as JSON-Lines (one JSON object per line)."""
    import json
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=str))
            f.write("\n")


def read_jsonl(path: PathLike) -> List[Dict[str, Any]]:
    """Read a JSON-Lines file, returning a list of dicts."""
    import json
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _coerce(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return str(v)
