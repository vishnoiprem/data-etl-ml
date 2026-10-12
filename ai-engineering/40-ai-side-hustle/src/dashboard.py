"""
dashboard.py — Revenue dashboard across all 3 streams.

Shows:
  - Total $ earned (lifetime)
  - $ by stream
  - Best/worst stream
  - Daily revenue series (last 14 days)
  - Projected vs. actual

Pure data layer: `compute(ledger)` returns a dict. `render(data)`
prints the pretty version. Tests assert on the dict shape.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ledger import Ledger


def compute(ledger: Ledger) -> dict[str, Any]:
    by_stream = ledger.by_stream()
    total = ledger.total()
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
        "by_day": ledger.by_day(days=14),
        "best_stream": max(by_stream, key=lambda s: s["usd"])["stream"] if by_stream else None,
    }


def _bar(usd: float, max_usd: float, width: int = 24) -> str:
    if max_usd <= 0:
        return ""
    filled = int(round((usd / max_usd) * width))
    return "█" * filled + "·" * (width - filled)


def render(data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=" * 64)
    lines.append("  AI SIDE HUSTLE — REVENUE DASHBOARD")
    lines.append(f"  as_of: {data['as_of']}")
    lines.append("=" * 64)
    lines.append("")
    lines.append(f"  Lifetime revenue         : ${data['totals']['usd']:,.2f}")
    lines.append(f"  Total events recorded    : {data['totals']['events']}")
    if data["best_stream"]:
        lines.append(f"  Best stream (so far)     : {data['best_stream']}")
    lines.append("")
    lines.append("  By stream")
    streams = data["by_stream"]
    if not streams:
        lines.append("    (no revenue yet — run `make demo` to seed projections)")
    else:
        max_usd = max(s["usd"] for s in streams.values()) or 1
        for name in ("seo", "saas", "product"):
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
        max_day = max(d["usd"] for d in days) or 1
        lines.append(f"    {'date':<12} {'$':>10}  {'units':>5}  bar")
        for d in days:
            lines.append(
                f"    {d['day']:<12} ${d['usd']:>9,.2f}  {d['units']:>5}  "
                f"{_bar(d['usd'], max_day, width=20)}"
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
