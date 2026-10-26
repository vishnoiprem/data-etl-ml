"""
projections.py — Realistic revenue projection model.

The previous version hard-coded "10 paying customers in month 1",
which is wildly optimistic for any real product. This module gives
each stream a calibrated funnel:

  SEO:     pageviews/day × CTR × $/click
  SaaS:    visitors/mo × trial_rate × paid_rate × price
  Product: impressions × conversion × price

Each projection is a base case + an optimistic + a pessimistic case.
The base case is what the dashboard records; the range is what the
consultant can quote in their head.

Why not just call the LLM for projections?  Two reasons:
  1. LLM numbers are notoriously hand-wavy ("you could make $10k/mo!")
  2. We want the demo numbers to be defensible at a coffee meeting.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class StreamProjection:
    base: float          # expected month-1 $ (what we record)
    pessimistic: float   # 10% case
    optimistic: float    # 90% case
    assumptions: dict    # for the dashboard "assumptions" section


# ---------------------------------------------------------------- SEO
def project_seo_article(
    volume: int,
    difficulty: int,
    cpc_usd: float,
    rank_target: int = 7,            # target top-10 ranking
) -> StreamProjection:
    """Project monthly revenue for a single article.

    Funnel:
      monthly searches (volume)
        × P(rank in top N | difficulty)              (curve by KD)
        × CTR (position-based, ~5–15%)
        × $/click (between ad RPM and affiliate rev)
    """
    # Empirical P(rank in top 10) curve. KD 0→90%, KD 50→40%, KD 80→10%.
    p_rank = max(0.05, 1.0 - difficulty / 110.0)
    # Position-based CTR for top-10 (rough)
    ctr_by_pos = [0.30, 0.15, 0.10, 0.07, 0.05, 0.04, 0.035, 0.03, 0.025, 0.02]
    pos = max(0, min(9, rank_target - 1))
    ctr = ctr_by_pos[pos] * p_rank
    # $/click: take a fraction of CPC (you don't get the full CPC)
    rpc = cpc_usd * 0.30   # 30% of advertiser CPC
    base = volume * ctr * rpc

    return StreamProjection(
        base=round(base, 2),
        pessimistic=round(base * 0.10, 2),
        optimistic=round(base * 2.50, 2),
        assumptions={
            "volume": volume, "difficulty": difficulty, "cpc_usd": cpc_usd,
            "rank_target": rank_target, "p_rank_top10": round(p_rank, 2),
            "ctr": round(ctr, 4), "rpc_usd": round(rpc, 2),
        },
    )


# ---------------------------------------------------------------- SaaS
def project_saas(
    price_usd: int,
    mvp_weeks: int,
    tam_usd: int,
    launch_visitors: int = 500,      # month-1 traffic from PH/HN/Reddit
    trial_rate: float = 0.08,        # 8% of visitors start a trial
    trial_to_paid: float = 0.20,     # 20% of trials convert
) -> StreamProjection:
    """Project month-1 MRR for a freshly-launched micro-SaaS."""
    paying = launch_visitors * trial_rate * trial_to_paid
    base = paying * price_usd
    # MVP speed affects whether you can iterate; longer MVPs → lower conversion
    speed_penalty = max(0.0, (mvp_weeks - 1) * 0.05)
    base *= (1.0 - speed_penalty)

    return StreamProjection(
        base=round(base, 2),
        pessimistic=round(base * 0.20, 2),
        optimistic=round(base * 1.80, 2),
        assumptions={
            "price_usd": price_usd, "mvp_weeks": mvp_weeks,
            "tam_usd": tam_usd, "launch_visitors": launch_visitors,
            "trial_rate": trial_rate, "trial_to_paid": trial_to_paid,
            "paying_customers": round(paying, 1),
        },
    )


# ---------------------------------------------------------------- Digital product
def project_product(
    price_usd: int,
    impressions_per_day: int = 200,  # from Gumroad/Lemon discovery
    conversion_rate: float = 0.015,  # 1.5% of impressions buy
) -> StreamProjection:
    """Project month-1 sales for a digital product listing."""
    days = 30
    sales = impressions_per_day * conversion_rate * days
    base = sales * price_usd

    return StreamProjection(
        base=round(base, 2),
        pessimistic=round(base * 0.15, 2),
        optimistic=round(base * 2.00, 2),
        assumptions={
            "price_usd": price_usd,
            "impressions_per_day": impressions_per_day,
            "conversion_rate": conversion_rate,
            "expected_sales": round(sales, 1),
        },
    )


# ---------------------------------------------------------------- helper
def _confidence_label(base: float, pessimistic: float, optimistic: float) -> str:
    """How wide is the range? Wider = less confident."""
    if pessimistic <= 0:
        return "speculative"
    ratio = optimistic / max(pessimistic, 0.01)
    if ratio < 4:
        return "high"
    if ratio < 10:
        return "medium"
    return "low"


# attach the label to the dataclass
StreamProjection.confidence = property(  # type: ignore[attr-defined]
    lambda self: _confidence_label(self.base, self.pessimistic, self.optimistic)
)


def summarize(stream: str, proj: StreamProjection) -> str:
    """One-line human description for the dashboard."""
    pct_low = (proj.pessimistic / max(proj.base, 0.01)) * 100
    pct_high = (proj.optimistic / max(proj.base, 0.01)) * 100
    return (
        f"{stream:<8} ${proj.base:>8,.2f}/mo  "
        f"(range ${proj.pessimistic:,.2f}–${proj.optimistic:,.2f}, "
        f"confidence: {proj.confidence})"
    )
