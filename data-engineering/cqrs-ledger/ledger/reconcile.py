"""
Daily reconciliation: prove the journal matches the source of truth.

The job:
  1. Sum the journal per (account, currency) -> expected balance.
  2. Fetch the source-of-truth balance (e.g., Stripe API).
  3. Compare. Any drift > 0 is a P1.

In a real system, the source-of-truth is the upstream payment processor
(Stripe, Adyen, etc.) and the journal is our internal record of those
payments. The reconciliation job proves the two agree.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from ledger.journal import Journal, Posting


@dataclass
class Drift:
    account: str
    currency: str
    expected: int      # what the journal says
    actual: int        # what the source of truth says
    diff: int          # actual - expected


def reconcile(journal: Journal, source_of_truth: Callable[[str, str], int]) -> list[Drift]:
    """Returns the list of drifts. Empty = books match."""
    expected = journal.balances()
    drifts: list[Drift] = []
    for (account, currency), exp in expected.items():
        if exp == 0:
            continue
        actual = source_of_truth(account, currency)
        diff = actual - exp
        if diff != 0:
            drifts.append(Drift(account=account, currency=currency,
                                expected=exp, actual=actual, diff=diff))
    return drifts


# --- Toy source of truth ----------------------------------------------------

def toy_source_of_truth(account: str, currency: str) -> int:
    """Returns the expected balance for the toy demo. Real impl: API call."""
    # Match the demo in journal.py
    table = {
        ("customer:cust_001", "USD"): 0,    # refund returned the funds
        ("merchant:m_001",    "USD"): 0,    # paid 1000, fees 30, refund 970 -> 0
        ("platform:fees",     "USD"): 30,   # fees retained
    }
    return table.get((account, currency), 0)


if __name__ == "__main__":
    from ledger.journal import Journal as _J
    j = _J()
    j.post("t1", "customer:cust_001", "merchant:m_001", 1000)
    j.post("t2", "merchant:m_001",    "platform:fees",  30)
    j.post("t3", "merchant:m_001",    "customer:cust_001", 970)
    drifts = reconcile(j, toy_source_of_truth)
    print(f"drifts: {len(drifts)}")
    for d in drifts:
        print(f"  {d.account} {d.currency}: expected {d.expected}, actual {d.actual}, diff {d.diff}")
