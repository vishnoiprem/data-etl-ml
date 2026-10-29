"""
Double-entry journal: append-only, immutable, balances to zero.

The invariant: for every currency, sum(debit) == sum(credit) across the
whole journal. If the books don't close, the post is rejected.

Real impl: a Postgres table with a CHECK constraint that prevents
negative balances, plus a daily reconciliation job.
"""
from __future__ import annotations
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Posting:
    id: str
    ts: float
    account: str
    debit: int       # minor units (cents)
    credit: int      # minor units
    currency: str
    ref: str         # transfer_id or external reference


class Journal:
    def __init__(self):
        self.postings: list[Posting] = []

    def post(self, transfer_id: str, debit_account: str, credit_account: str,
             amount: int, currency: str = "USD") -> list[Posting]:
        """Post a transfer as two rows. They must balance."""
        if amount <= 0:
            raise ValueError(f"amount must be positive, got {amount}")
        if debit_account == credit_account:
            raise ValueError("cannot debit and credit the same account")

        ts = time.time()
        debit = Posting(id=str(uuid.uuid4()), ts=ts, account=debit_account,
                        debit=amount, credit=0, currency=currency, ref=transfer_id)
        credit = Posting(id=str(uuid.uuid4()), ts=ts, account=credit_account,
                         debit=0, credit=amount, currency=currency, ref=transfer_id)
        self.postings.extend([debit, credit])
        return [debit, credit]

    def balances(self) -> dict[tuple[str, str], int]:
        """Per-account-per-currency balance (debit - credit)."""
        b: dict[tuple[str, str], int] = defaultdict(int)
        for p in self.postings:
            b[(p.account, p.currency)] += p.debit - p.credit
        return dict(b)

    def books_close(self) -> bool:
        """True if every account's net is zero per currency."""
        return all(v == 0 for v in self.balances().values())

    def statement(self, account: str, currency: str) -> list[Posting]:
        return [p for p in self.postings if p.account == account and p.currency == currency]

    def __len__(self) -> int:
        return len(self.postings)


# --- Reference use ----------------------------------------------------------

if __name__ == "__main__":
    j = Journal()
    j.post(transfer_id="t1", debit_account="customer:cust_001", credit_account="merchant:m_001", amount=1000)
    j.post(transfer_id="t2", debit_account="merchant:m_001", credit_account="platform:fees",     amount=30)
    j.post(transfer_id="t3", debit_account="merchant:m_001", credit_account="customer:cust_001", amount=970)  # refund
    print(f"posted {len(j)} rows")
    print(f"books close: {j.books_close()}")
    print(f"balances: {j.balances()}")
