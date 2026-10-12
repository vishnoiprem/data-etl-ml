"""
dashboard.py — Revenue dashboard across all 4 streams.

Renders:
  - Lifetime revenue + total events
  - Per-stream revenue bar chart
  - Daily revenue sparkline (last 14 days)
  - Per-day table with best/worst day flagged
  - Average $ / day and best stream
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ledger import Ledger


def compute(ledger: Ledger) -> dict[str, Any]:
    by_stream = ledger.by_stream()
    total = ledger.total()
    by_day = ledger.by_day(days=14)

    # Best/worst day from by_day
    best_day = max(by_day, key=lambda d: d["usd"]) if by_day else None
    worst_day = min(by_day, key=lambda d: d["usd"]) if by_day else None

    # Average $/day over the window (excluding empty days)
    active_days = [d for d in by_day if d["usd"] > 0]
    avg_per_active_day = (
        sum(d["usd"] for d in active_days) / len(active_days)
        if active_days else 0.0
    )
    avg_overall = total / 14 if total else 0.0

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "usd": round(total, 2),
            "events": sum(s["events"] for s in by_stream),
        },
        "by_stream": {s["stream"]: {
            "usd": round(s["usd"], 2),
            "units": s["units"],
            "events": s["events"],
        } for s in by_stream},
        "by_day": by_day,
        "best_stream": max(by_stream, key=lambda s: s["usd"])["stream"] if by_stream else None,
        "best_day": best_day,
        "worst_day": worst_day,
        "avg_per_active_day": round(avg_per_active_day, 2),
        "avg_overall": round(avg_overall, 2),
    }


def _bar(usd: float, max_usd: float, width: int = 24) -> str:
    if max_usd <= 0:
        return ""
    # Cap the scale at 90th percentile so a single outlier doesn't
    # make every other bar invisible.
    sorted_max = sorted([max_usd, usd])
    cap = sorted_max[-1]  # use absolute max (caller already picked it)
    scale = cap if cap > 0 else 1
    filled = int(round((usd / scale) * width))
    return "█" * filled + "·" * (width - filled)


def _capped_scale(values: list[float], percentile: float = 0.90) -> float:
    """Return a scale value that's the Nth percentile (to ignore outliers)."""
    if not values:
        return 1.0
    s = sorted(values)
    idx = max(0, min(len(s) - 1, int(len(s) * percentile) - 1))
    cap = s[idx]
    return cap if cap > 0 else max(s) or 1.0


def _sparkline(values: list[float], width: int = 14) -> str:
    """Tiny inline sparkline using block characters.

    Uses a median+IQR-style scale (so a single huge spike doesn't
    compress the rest of the line into invisibility). We compute the
    75th percentile as the scale; any value above that just renders
    as the tallest block.
    """
    if not values:
        return ""
    chars = " ▁▂▃▄▅▆▇█"
    if len(set(values)) == 1:
        return chars[0] * len(values)
    # 75th percentile is a more aggressive outlier filter than 90th.
    sorted_v = sorted(values)
    cap_idx = max(0, int(len(sorted_v) * 0.75) - 1)
    cap = sorted_v[cap_idx] or 1
    if len(values) > width:
        bucket = len(values) / width
        sampled = [
            sum(values[int(i * bucket):int((i + 1) * bucket)]) /
            max(1, int((i + 1) * bucket) - int(i * bucket))
            for i in range(width)
        ]
    else:
        sampled = values
    return "".join(
        chars[min(len(chars) - 1,
                  int((min(v, cap) / cap) * (len(chars) - 1)))]
        for v in sampled
    )


def render(data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=" * 64)
    lines.append("  AI SIDE HUSTLE — REVENUE DASHBOARD")
    lines.append(f"  as_of: {data['as_of']}")
    lines.append("=" * 64)
    lines.append("")
    lines.append(f"  Lifetime revenue         : ${data['totals']['usd']:,.2f}")
    lines.append(f"  Total events recorded    : {data['totals']['events']}")
    lines.append(f"  Avg $/day (last 14)      : ${data['avg_overall']:,.2f}")
    if data['avg_per_active_day']:
        lines.append(f"  Avg $/active day         : ${data['avg_per_active_day']:,.2f}")
    if data["best_stream"]:
        lines.append(f"  Best stream (so far)     : {data['best_stream']}")
    if data["best_day"]:
        lines.append(
            f"  Best day                 : {data['best_day']['day']} "
            f"(${data['best_day']['usd']:.2f})"
        )
    if data["worst_day"]:
        lines.append(
            f"  Worst day                : {data['worst_day']['day']} "
            f"(${data['worst_day']['usd']:.2f})"
        )
    lines.append("")
    lines.append("  By stream")
    streams = data["by_stream"]
    if not streams:
        lines.append("    (no revenue yet — run `make demo` to seed projections)")
    else:
        max_usd = max(s["usd"] for s in streams.values()) or 1
        for name in ("seo", "saas", "product", "merch"):
            s = streams.get(name)
            if not s:
                continue
            lines.append(
                f"    {name:<8} ${s['usd']:>9,.2f}  "
                f"units={s['units']:<5}  {_bar(s['usd'], max_usd)}"
            )
    lines.append("")
    lines.append("  Daily revenue (last 14 days)")
    days = data["by_day"]
    if not days:
        lines.append("    (none)")
    else:
        day_values = [d["usd"] for d in days]
        scale = _capped_scale(day_values, percentile=0.90)
        # Sparkline of all 14 days
        spark = _sparkline(day_values, width=14)
        lines.append(f"    sparkline: {spark}")
        lines.append(f"    {'date':<12} {'$':>10}  {'units':>5}  bar")
        for d in days:
            lines.append(
                f"    {d['day']:<12} ${d['usd']:>9,.2f}  {d['units']:>5}  "
                f"{_bar(d['usd'], scale, width=20)}"
            )
    lines.append("=" * 64)
    return "\n".join(lines)


def print_dashboard(db_path: str = "ledger.db") -> None:
    l = Ledger(db_path=db_path)
    print(render(compute(l)))


def as_json(db_path: str = "ledger.db") -> str:
    return json.dumps(compute(Ledger(db_path=db_path)), indent=2)


if __name__ == "__main__":  # pragma: no cover
    print_dashboard()
