"""
Visualizer - Auto-pick chart type and render to Plotly JSON
===========================================================
Given a result DataFrame (as list of dicts), pick the best chart:
  - 0-1 numeric column: bar
  - 2+ numeric columns: scatter
  - time-indexed: line
  - many rows: aggregate first

Returns a Plotly figure dict (JSON-serializable) that the frontend renders.
"""

import logging
from typing import Optional

logger = logging.getLogger("data-analyst.viz")

MAX_CHART_ROWS = 1000


def _to_numeric(rows: list[dict]) -> tuple[list[dict], list[str]]:
    """Return (rows, numeric_column_names)."""
    if not rows:
        return rows, []
    cols = list(rows[0].keys())
    numeric = []
    for c in cols:
        sample = next((r[c] for r in rows if r.get(c) is not None), None)
        if isinstance(sample, (int, float)):
            numeric.append(c)
    return rows, numeric


def pick_and_render_chart(rows: list[dict]) -> Optional[dict]:
    """Pick a chart type and return Plotly figure JSON. None if no chart possible."""
    if not rows:
        return None
    rows, numeric = _to_numeric(rows)
    if not numeric:
        return None

    # Aggregate if too many rows
    if len(rows) > MAX_CHART_ROWS:
        # simple top-N by first numeric column
        first_num = numeric[0]
        rows = sorted(rows, key=lambda r: r.get(first_num) or 0, reverse=True)[:MAX_CHART_ROWS]
        rows = list(reversed(rows))

    # Heuristic: if there's a date-like or string index, x = that, y = first numeric
    cols = list(rows[0].keys())
    x_col = next((c for c in cols if c not in numeric), cols[0])
    y_col = numeric[0]

    if len(numeric) == 1:
        # bar chart
        return _bar(rows, x_col, y_col)
    elif len(numeric) == 2:
        return _scatter(rows, x_col, y_col)
    else:
        return _line(rows, x_col, y_col)


def _bar(rows: list[dict], x: str, y: str) -> dict:
    return {
        "data": [{
            "type": "bar",
            "x": [str(r.get(x, "")) for r in rows],
            "y": [r.get(y) for r in rows],
            "name": y,
        }],
        "layout": {
            "title": {"text": f"{y} by {x}"},
            "xaxis": {"title": x},
            "yaxis": {"title": y},
            "margin": {"l": 40, "r": 20, "t": 40, "b": 80},
        },
    }


def _scatter(rows: list[dict], x: str, y: str) -> dict:
    cols = list(rows[0].keys())
    numeric_cols = [c for c in cols if c not in (x,)]
    y_col = next((c for c in numeric_cols if c != y), y)
    return {
        "data": [{
            "type": "scatter",
            "mode": "markers",
            "x": [r.get(x) for r in rows],
            "y": [r.get(y) for r in rows],
            "name": f"{y} vs {x}",
        }],
        "layout": {
            "title": {"text": f"{y} vs {x}"},
            "xaxis": {"title": x},
            "yaxis": {"title": y},
            "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        },
    }


def _line(rows: list[dict], x: str, y: str) -> dict:
    cols = list(rows[0].keys())
    numeric_cols = [c for c in cols if c not in (x,)]
    return {
        "data": [{
            "type": "scatter",
            "mode": "lines+markers",
            "x": [str(r.get(x, "")) for r in rows],
            "y": [r.get(c) for r in rows],
            "name": c,
        } for c in numeric_cols],
        "layout": {
            "title": {"text": f"Trends by {x}"},
            "xaxis": {"title": x},
            "yaxis": {"title": "value"},
            "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        },
    }
