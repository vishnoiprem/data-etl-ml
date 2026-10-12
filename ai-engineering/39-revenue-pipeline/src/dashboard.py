"""
dashboard.py — Render the revenue dashboard from the SQLite pipeline.

Numbers the consultant cares about, every week:

    $$/week closed     = (won count) × (avg deal size $)
    Pipeline $         = Σ (deal_usd × score/100) for open opps
    Time-to-cash       = median days from first_seen → closed_at (won only)
    Conversion rate    = won / (won + lost)
    Top source by $    = source with the highest weighted pipeline $

Why a text dashboard and not a web app?  Two reasons:
  1. The consultant can `make dashboard` over SSH and pipe it to a log.
  2. Same numbers feed a future Streamlit page (dashboard.data() is the
     pure data layer; render() is the pretty-printer).
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from typing import Any

from pipeline import Pipeline


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # Python's fromisoformat handles "...+00:00" in 3.11+; tolerate trailing Z.
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute(p: Pipeline) -> dict[str, Any]:
    """Pure data layer: aggregate every number the dashboard renders.

    The returned dict is JSON-safe and deterministic for a given DB state.
    Tests assert on its shape, not the printed string.
    """
    stats = p.stats()
    total = stats.get("total") or 0
    won = stats.get("won") or 0
    lost = stats.get("lost") or 0
    won_usd = stats.get("won_usd") or 0
    pipeline_usd = stats.get("pipeline_usd") or 0

    # Average deal size on closed-won (defaults to 0 if no wins)
    avg_deal_usd = int(won_usd / won) if won else 0

    # Conversion rate over closed deals only
    closed = won + lost
    conversion_rate = (won / closed) if closed else None

    # Median time-to-cash (days) for closed-won rows
    ttc_days: list[int] = []
    with p._conn() as c:  # type: ignore[attr-defined]
        rows = c.execute(
            "SELECT first_seen_at, closed_at FROM opportunities "
            "WHERE status='won' AND first_seen_at IS NOT NULL "
            "AND closed_at IS NOT NULL"
        ).fetchall()
    for r in rows:
        seen = _parse_iso(r["first_seen_at"])
        closed_at = _parse_iso(r["closed_at"])
        if seen and closed_at:
            ttc_days.append(int((closed_at - seen).total_seconds() // 86400))
    median_ttc = int(statistics.median(ttc_days)) if ttc_days else None

    # Top source by weighted pipeline $
    by_source_rows: list[dict] = []
    with p._conn() as c:  # type: ignore[attr-defined]
        rows = c.execute(
            """
            SELECT source,
                   COUNT(*) AS n,
                   COALESCE(SUM(weighted_usd), 0) AS weighted,
                   COALESCE(SUM(CASE WHEN status='won' THEN won_usd ELSE 0 END), 0) AS won
            FROM opportunities
            GROUP BY source
            ORDER BY weighted DESC
            """
        ).fetchall()
    by_source_rows = [dict(r) for r in rows]
    top_source = by_source_rows[0] if by_source_rows else None

    # Top opportunities (for drill-down)
    top_opps = p.top_opportunities(limit=5)

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "leads": total,
            "won": won,
            "lost": lost,
            "open": (total - closed) if total else 0,
        },
        "money": {
            "won_usd": int(won_usd),
            "pipeline_usd": int(pipeline_usd),
            "avg_deal_usd": int(avg_deal_usd),
        },
        "rates": {
            "conversion": conversion_rate,
            "median_ttc_days": median_ttc,
        },
        "by_source": by_source_rows,
        "top_source": top_source,
        "top_opportunities": top_opps,
    }


# ------------------------------------------------------------ formatting
def _usd(n: int | float) -> str:
    return f"${n:,.0f}"


def _pct(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x * 100:.0f}%"


def render(data: dict[str, Any]) -> str:
    """Pretty-print the dashboard as a fixed-width text block.

    Output is stable for snapshot tests — no random ordering, no timestamps
    in the body (as_of is its own line).
    """
    money = data["money"]
    totals = data["totals"]
    rates = data["rates"]
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("  REVENUE PIPELINE — DASHBOARD")
    lines.append(f"  as_of: {data['as_of']}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("  Money")
    lines.append(f"    $ won (lifetime)        : {_usd(money['won_usd'])}")
    lines.append(f"    $ open in pipeline      : {_usd(money['pipeline_usd'])}")
    lines.append(f"    avg deal size (won)     : {_usd(money['avg_deal_usd'])}")
    lines.append("")
    lines.append("  Funnel")
    lines.append(f"    leads                   : {totals['leads']}")
    lines.append(f"      won                   : {totals['won']}")
    lines.append(f"      lost                  : {totals['lost']}")
    lines.append(f"      open                  : {totals['open']}")
    lines.append("")
    lines.append("  Rates")
    lines.append(f"    conversion (won/closed) : {_pct(rates['conversion'])}")
    ttc = rates["median_ttc_days"]
    lines.append(f"    median time-to-cash     : "
                 f"{ttc if ttc is not None else 'n/a'} days")
    lines.append("")
    lines.append("  By source")
    if not data["by_source"]:
        lines.append("    (no data)")
    else:
        lines.append(f"    {'source':<20} {'n':>4} {'weighted $':>14} {'won $':>10}")
        for row in data["by_source"]:
            lines.append(
                f"    {row['source']:<20} {row['n']:>4} "
                f"{_usd(row['weighted']):>14} {_usd(row['won']):>10}"
            )
    lines.append("")
    lines.append("  Top opportunities (qualified/sent/replied, score ≥ 40)")
    if not data["top_opportunities"]:
        lines.append("    (none yet)")
    else:
        for opp in data["top_opportunities"]:
            lines.append(
                f"    • [{opp['status']:<9}] score={opp['score']:>3}  "
                f"${opp['weighted_usd']:>7} weighted  "
                f"{opp['company']} — {opp['title'][:50]}"
            )
    lines.append("=" * 60)
    return "\n".join(lines)


def print_dashboard(db_path: str = "pipeline.db") -> None:
    """Convenience: compute + render + print. For `make dashboard`."""
    p = Pipeline(db_path=db_path)
    data = compute(p)
    print(render(data))


def as_json(db_path: str = "pipeline.db") -> str:
    """For piping into `jq`, dashboards, etc."""
    p = Pipeline(db_path=db_path)
    return json.dumps(compute(p), indent=2, default=str)


if __name__ == "__main__":  # pragma: no cover
    print_dashboard()
