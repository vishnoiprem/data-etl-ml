"""
cost.py — telemetry for Foundation Model API + DBU spend.

Two purposes:

  1. **Track** per-iteration spend:
     * FM API: counted from the agent's `usage` field
       (prompt_tokens, completion_tokens). We tag every
       call with the model name and the cost.
     * DBU: read from the system.billing.usage table on
       Databricks (Free Edition exposes a daily-aggregate
       view; production has per-job granularity).

  2. **Guard** the loop. A `BudgetGuard` raises when:
     * daily spend > $X (default $5)
     * hourly token spend > Y (default 200k tokens)
     * DBU consumption > Z DBU/day (default 5)

  The driver catches `BudgetExceeded` and exits the loop
  early with a clear log line. This is the safety brake
  for the Free Edition "fair use" cap.

Pricing reference (Databricks Foundation Model API, USD):

  databricks-meta-llama-3.3-70b-instruct:
    input:  $1.00 / 1M tokens
    output: $5.00 / 1M tokens

  databricks-dbrx-instruct:
    input:  $0.75 / 1M tokens
    output: $1.50 / 1M tokens

  databricks-meta-llama-3.1-8b-instruct:
    input:  $0.15 / 1M tokens
    output: $0.30 / 1M tokens

DBU pricing (Free Edition):
  * Serverless Jobs / DLT: free
  * Foundation Model API: pay-per-token (above)
  * SQL Warehouse: 1× 2X-Small free
  * Lakebase: 1 project free (scale-to-zero)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# Pricing (USD)
# ============================================================

# (input_per_1m, output_per_1m) keyed by model name
PRICING: dict[str, tuple[float, float]] = {
    "databricks-meta-llama-3.3-70b-instruct": (1.00, 5.00),
    "databricks-dbrx-instruct":               (0.75, 1.50),
    "databricks-meta-llama-3.1-8b-instruct":  (0.15, 0.30),
    "databricks-mixtral-8x7b-instruct":       (0.50, 1.00),
    "databricks-claude-3-7-sonnet":          (3.00, 15.00),
}

DEFAULT_MODEL = "databricks-meta-llama-3.3-70b-instruct"


def cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Return the dollar cost for one FM API call."""
    in_price, out_price = PRICING.get(model, PRICING[DEFAULT_MODEL])
    return (prompt_tokens / 1_000_000.0) * in_price + \
           (completion_tokens / 1_000_000.0) * out_price


# ============================================================
# Telemetry record
# ============================================================

@dataclass
class CostRecord:
    """One spend event."""
    iter_no: int
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    dbu: float = 0.0  # populated by `read_dbu_for_iter` when available

    def to_dict(self) -> dict:
        return {
            "iter_no": self.iter_no,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "dbu": self.dbu,
        }


# ============================================================
# Telemetry ledger
# ============================================================

class CostLedger:
    """Per-iteration spend. Persisted to a Delta table in production."""

    def __init__(self):
        self.records: list[CostRecord] = []

    def record(
        self,
        *,
        iter_no: int,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        dbu: float = 0.0,
    ) -> CostRecord:
        cr = CostRecord(
            iter_no=iter_no,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd(model, prompt_tokens, completion_tokens),
            dbu=dbu,
        )
        self.records.append(cr)
        return cr

    def total(self) -> tuple[float, int, int]:
        """Returns (total_usd, total_prompt_tokens, total_completion_tokens)."""
        usd = sum(r.cost_usd for r in self.records)
        pt = sum(r.prompt_tokens for r in self.records)
        ct = sum(r.completion_tokens for r in self.records)
        return usd, pt, ct

    def since(self, since_iter: int) -> tuple[float, int, int]:
        """Same as `total`, but only for iters >= since_iter."""
        recent = [r for r in self.records if r.iter_no >= since_iter]
        usd = sum(r.cost_usd for r in recent)
        pt = sum(r.prompt_tokens for r in recent)
        ct = sum(r.completion_tokens for r in recent)
        return usd, pt, ct


# ============================================================
# Budget guard
# ============================================================

class BudgetExceeded(Exception):
    """Raised when the daily / hourly / DBU budget is hit."""


class BudgetGuard:
    """Safety brake. Throws BudgetExceeded when the loop has spent too much.

    All defaults are tuned for Free Edition. Pass higher values if you're
    on a paid workspace.
    """

    def __init__(
        self,
        *,
        max_daily_usd: float = 5.0,
        max_hourly_tokens: int = 200_000,
        max_daily_dbu: float = 5.0,
    ):
        self.max_daily_usd = max_daily_usd
        self.max_hourly_tokens = max_hourly_tokens
        self.max_daily_dbu = max_daily_dbu

    def check(self, ledger: CostLedger, current_iter: int) -> None:
        """Inspect the ledger. Raise if the budget is hit.

        `current_iter` is used to scope the "hourly" check to the
        last 10 iterations (proxy for the last hour at our 6-min
        cadence).
        """
        usd, pt, ct = ledger.total()
        if usd > self.max_daily_usd:
            raise BudgetExceeded(
                f"daily FM-API cost ${usd:.2f} > ${self.max_daily_usd:.2f} cap"
            )
        recent_usd, recent_pt, recent_ct = ledger.since(max(0, current_iter - 10))
        recent_tokens = recent_pt + recent_ct
        if recent_tokens > self.max_hourly_tokens:
            raise BudgetExceeded(
                f"recent-window token spend {recent_tokens:,} > "
                f"{self.max_hourly_tokens:,}/window cap"
            )
        dbu = sum(r.dbu for r in ledger.records)
        if dbu > self.max_daily_dbu:
            raise BudgetExceeded(
                f"daily DBU consumption {dbu:.2f} > {self.max_daily_dbu:.2f}"
            )


# ============================================================
# DBU reader (production)
# ============================================================

def read_dbu_for_iteration(
    spark,
    *,
    iter_no: int,
    run_id: Optional[str] = None,
) -> float:
    """Read DBU consumption for an iteration from system.billing.usage.

    Returns 0.0 if the table isn't accessible (e.g. local smoke test).
    The query is approximate — billing data is usually a few minutes
    behind. We use the iter_no's date as the filter.
    """
    try:
        result = spark.sql("""
            SELECT COALESCE(SUM(usage_quantity), 0) AS dbu
            FROM system.billing.usage
            WHERE usage_date = CURRENT_DATE
              AND usage_unit = 'DBU'
        """).first()
        return float(result["dbu"] or 0.0) if result else 0.0
    except Exception as e:
        logger.warning("read_dbu_for_iteration failed: %s", e)
        return 0.0


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    # Demo: log a few calls, run the guard. We deliberately blow
    # past the $1 daily cap so the demo shows the guard firing.
    ledger = CostLedger()
    ledger.record(iter_no=0, model=DEFAULT_MODEL,
                  prompt_tokens=2_000_000, completion_tokens=500_000)  # ~$4.50
    ledger.record(iter_no=1, model=DEFAULT_MODEL,
                  prompt_tokens=3_000_000, completion_tokens=800_000)  # ~$7.00
    usd, pt, ct = ledger.total()
    print(f"Total: ${usd:.4f}  ({pt:,} prompt + {ct:,} completion tokens)")

    guard = BudgetGuard(max_daily_usd=1.0)  # tight cap for the demo
    try:
        guard.check(ledger, current_iter=1)
    except BudgetExceeded as e:
        print(f"budget hit: {e}")
