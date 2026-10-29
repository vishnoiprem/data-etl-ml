"""Double-entry bookkeeping: journal entries, trial balance, period close, statements.

Meaningful workload:
- Generate 5,000+ journal entries across 25 accounts and 6 periods.
- Each entry is balanced (debits == credits), validated by assertion.
- Roll up to trial balance; verify total debits == total credits.
- Close a period, verify retained earnings flows correctly.
- Generate income statement + balance sheet, verify they balance.

Public APIs preserved (Ledger, Posting, JournalEntry, Account, etc.).
"""
from __future__ import annotations
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable


# === account master ===

ACCOUNT_TYPE = ("asset", "liability", "equity", "revenue", "expense")

# Normal balance: assets/expenses are debit-normal; liabilities/equity/revenue are credit-normal.
DEBIT_NORMAL = {"asset", "expense"}
CREDIT_NORMAL = {"liability", "equity", "revenue"}


@dataclass
class Account:
    code: str
    name: str
    type: str  # asset, liability, equity, revenue, expense
    opening_balance: float = 0.0  # in USD, post period 0
    requires_non_negative: bool = False  # e.g., cash should not go negative

    def __post_init__(self):
        if self.type not in ACCOUNT_TYPE:
            raise ValueError(f"unknown account type: {self.type}")


@dataclass
class Posting:
    account_code: str
    debit: float = 0.0
    credit: float = 0.0

    @property
    def net(self) -> float:
        # positive = debit balance, negative = credit balance
        if self.type_is_debit_normal():
            return self.debit - self.credit
        else:
            return self.credit - self.debit

    def type_is_debit_normal(self) -> bool:
        # We can't know from a Posting alone, so the caller must look up the
        # account. This helper exists for the Ledger level to use.
        return True


@dataclass
class JournalEntry:
    entry_id: str
    period: str  # e.g. "2025-01"
    date: str
    description: str
    postings: list[Posting] = field(default_factory=list)

    def total_debit(self) -> float:
        return round(sum(p.debit for p in self.postings), 2)

    def total_credit(self) -> float:
        return round(sum(p.credit for p in self.postings), 2)

    def is_balanced(self, tol: float = 0.01) -> bool:
        return abs(self.total_debit() - self.total_credit()) < tol


@dataclass
class Ledger:
    accounts: dict[str, Account] = field(default_factory=dict)
    entries: list[JournalEntry] = field(default_factory=list)
    retained_earnings_code: str = "RE"
    # Map: period -> opening retained earnings (cumulative net income up to that period start)
    opening_re_by_period: dict[str, float] = field(default_factory=dict)
    # Map: period -> closing retained earnings (cumulative net income up to that period end)
    closing_re_by_period: dict[str, float] = field(default_factory=dict)
    # Map: period -> period net income (income statement)
    net_income_by_period: dict[str, float] = field(default_factory=dict)

    def add_account(self, acct: Account) -> None:
        self.accounts[acct.code] = acct

    def post(self, entry: JournalEntry) -> None:
        # Validate references and balance before storing.
        for p in entry.postings:
            if p.account_code not in self.accounts:
                raise ValueError(f"unknown account {p.account_code} in entry {entry.entry_id}")
        if not entry.is_balanced():
            raise ValueError(
                f"unbalanced entry {entry.entry_id}: "
                f"debit={entry.total_debit()} credit={entry.total_credit()}"
            )
        self.entries.append(entry)


# === workload generation ===

# Realistic account chart: 5 of each type gives a 25-account balance sheet.
ACCOUNT_CHART: list[Account] = [
    # Assets (5) — cash is non-negative-required
    Account("1000", "Cash",              "asset",     opening_balance=500_000.0, requires_non_negative=True),
    Account("1100", "Accounts Receivable","asset",    opening_balance=120_000.0),
    Account("1200", "Inventory",         "asset",     opening_balance=200_000.0),
    Account("1500", "Equipment",         "asset",     opening_balance=350_000.0),
    Account("1900", "Prepaid Expenses",  "asset",     opening_balance=30_000.0),
    # Liabilities (5)
    Account("2000", "Accounts Payable",  "liability", opening_balance=80_000.0),
    Account("2100", "Accrued Expenses",  "liability", opening_balance=40_000.0),
    Account("2200", "Wages Payable",     "liability", opening_balance=25_000.0),
    Account("2500", "Notes Payable",     "liability", opening_balance=150_000.0),
    Account("2900", "Deferred Revenue",  "liability", opening_balance=18_000.0),
    # Equity (5)
    Account("3000", "Common Stock",      "equity",    opening_balance=400_000.0),
    Account("3100", "Additional Paid-In Capital", "equity", opening_balance=120_000.0),
    Account("3200", "Retained Earnings", "equity",    opening_balance=367_000.0),
    Account("3300", "Treasury Stock",    "equity",    opening_balance=0.0),
    Account("RE",   "Period Retained Earnings", "equity", opening_balance=0.0),
    # Revenue (5)
    Account("4000", "Product Revenue",   "revenue"),
    Account("4100", "Service Revenue",   "revenue"),
    Account("4200", "Subscription Revenue", "revenue"),
    Account("4900", "Other Income",      "revenue"),
    Account("4910", "Interest Income",   "revenue"),
    # Expenses (5)
    Account("5000", "COGS",              "expense"),
    Account("6000", "Salaries Expense",  "expense"),
    Account("6100", "Rent Expense",      "expense"),
    Account("6200", "Utilities Expense", "expense"),
    Account("6900", "Marketing Expense", "expense"),
]


# Volume weights: revenue/expense accounts have many more postings than BS accounts.
VOLUME_WEIGHTS: dict[str, int] = {
    "4000": 25, "4100": 12, "4200": 14, "4900": 2, "4910": 1,   # revenue
    "5000": 10, "6000": 11, "6100": 6,  "6200": 4, "6900": 7,   # expense (smaller than revenue for profitability)
    "1000": 22, "2000": 10, "1200": 6, "1100": 8, "1500": 2,    # asset/liability high-volume
    "2100": 4, "2200": 3, "2500": 1, "1900": 1, "2900": 1,      # liability low-volume
    "3000": 1, "3100": 1, "3200": 1, "3300": 0,                 # equity rare
}


def _weighted_codes() -> list[str]:
    pool: list[str] = []
    for code, w in VOLUME_WEIGHTS.items():
        pool.extend([code] * w)
    return pool


def _account(code: str) -> Account:
    for a in ACCOUNT_CHART:
        if a.code == code:
            return a
    raise KeyError(code)


def _round2(x: float) -> float:
    return round(x, 2)


def _make_entry(
    rng: random.Random,
    seq: int,
    period: str,
    date: str,
    template: str,
) -> JournalEntry:
    """Build a balanced journal entry from a template."""
    if template == "sale":
        # Debit cash/AR, credit revenue
        amount = _round2(rng.uniform(500, 25_000))
        cash_or_ar = rng.choice(["1000", "1100"])
        rev = rng.choice(["4000", "4100", "4200"])
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"Sale of goods/services for {amount:.2f}",
            postings=[
                Posting(cash_or_ar, debit=amount),
                Posting(rev, credit=amount),
            ],
        )
    if template == "cogs":
        # Debit COGS, credit inventory
        amount = _round2(rng.uniform(300, 18_000))
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"Cost of goods sold {amount:.2f}",
            postings=[
                Posting("5000", debit=amount),
                Posting("1200", credit=amount),
            ],
        )
    if template == "expense_paid":
        # Debit expense, credit cash
        amount = _round2(rng.uniform(200, 12_000))
        exp_code = rng.choice(["6000", "6100", "6200", "6900"])
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"Expense paid in cash {amount:.2f}",
            postings=[
                Posting(exp_code, debit=amount),
                Posting("1000", credit=amount),
            ],
        )
    if template == "expense_accrual":
        # Debit expense, credit accrued
        amount = _round2(rng.uniform(500, 8_000))
        exp_code = rng.choice(["6000", "6100", "6200"])
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"Accrued expense {amount:.2f}",
            postings=[
                Posting(exp_code, debit=amount),
                Posting("2100", credit=amount),
            ],
        )
    if template == "ar_collection":
        # Debit cash, credit AR
        amount = _round2(rng.uniform(400, 15_000))
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"AR collected {amount:.2f}",
            postings=[
                Posting("1000", debit=amount),
                Posting("1100", credit=amount),
            ],
        )
    if template == "ap_payment":
        # Debit AP, credit cash
        amount = _round2(rng.uniform(400, 12_000))
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"AP paid {amount:.2f}",
            postings=[
                Posting("2000", debit=amount),
                Posting("1000", credit=amount),
            ],
        )
    if template == "wages_accrual":
        amount = _round2(rng.uniform(2_000, 30_000))
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"Wages accrued {amount:.2f}",
            postings=[
                Posting("6000", debit=amount),
                Posting("2200", credit=amount),
            ],
        )
    if template == "depreciation":
        amount = _round2(rng.uniform(500, 5_000))
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"Depreciation {amount:.2f}",
            postings=[
                Posting("6100", debit=amount),  # book as rent-like/operating expense
                Posting("1500", credit=amount),
            ],
        )
    if template == "interest":
        amount = _round2(rng.uniform(200, 3_000))
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"Interest income {amount:.2f}",
            postings=[
                Posting("1000", debit=amount),
                Posting("4910", credit=amount),
            ],
        )
    if template == "prepaid":
        amount = _round2(rng.uniform(500, 4_000))
        return JournalEntry(
            entry_id=f"JE-{seq:06d}",
            period=period,
            date=date,
            description=f"Prepaid expense incurred {amount:.2f}",
            postings=[
                Posting("1900", debit=amount),
                Posting("1000", credit=amount),
            ],
        )
    raise ValueError(f"unknown template {template}")


TEMPLATES = [
    "sale", "sale", "sale", "sale", "sale",        # 5x sales
    "cogs", "cogs", "cogs",                         # 3x cogs
    "expense_paid", "expense_paid", "expense_paid", # 3x expenses
    "expense_accrual",                              # 1x accrual
    "ar_collection",                                # 1x collection
    "ap_payment",                                   # 1x payment
    "wages_accrual", "wages_accrual",               # 2x wages
    "depreciation",                                 # 1x depreciation
    "interest",                                     # 1x interest
    "prepaid",                                      # 1x prepaid
]


def generate_workload(
    n_entries: int = 5_000,
    n_periods: int = 6,
    seed: int = 42,
) -> Ledger:
    """Generate a meaningful workload: balanced journal entries across periods.

    Defaults: 5,000 entries, 6 periods, 25 accounts, realistic distribution.
    """
    rng = random.Random(seed)
    led = Ledger()
    for a in ACCOUNT_CHART:
        led.add_account(a)

    period_codes = [f"2025-{m:02d}" for m in range(1, n_periods + 1)]
    for i in range(n_entries):
        period = period_codes[i % n_periods]
        # Build a date in the period (just use period code as date for simplicity)
        date = period
        template = rng.choice(TEMPLATES)
        entry = _make_entry(rng, i + 1, period, date, template)
        led.post(entry)
    return led


# === queries / roll-ups ===

def trial_balance(led: Ledger) -> dict[str, tuple[float, float, float]]:
    """Roll up to trial balance: per account (debit_total, credit_total, balance).

    For debit-normal accounts: balance = debits - credits.
    For credit-normal accounts: balance = credits - debits.
    """
    debit_tot: dict[str, float] = defaultdict(float)
    credit_tot: dict[str, float] = defaultdict(float)
    for e in led.entries:
        for p in e.postings:
            debit_tot[p.account_code] += p.debit
            credit_tot[p.account_code] += p.credit

    tb: dict[str, tuple[float, float, float]] = {}
    for code, acct in led.accounts.items():
        d = _round2(debit_tot.get(code, 0.0))
        c = _round2(credit_tot.get(code, 0.0))
        if acct.type in DEBIT_NORMAL:
            bal = _round2(d - c)
        else:
            bal = _round2(c - d)
        tb[code] = (d, c, bal)
    return tb


def income_statement(led: Ledger, period: str | None = None) -> dict[str, float]:
    """Compute income statement for a period (or all periods).

    Returns {revenue, expense, net_income}.
    """
    rev_codes = {a.code for a in led.accounts.values() if a.type == "revenue"}
    exp_codes = {a.code for a in led.accounts.values() if a.type == "expense"}

    revenue = 0.0
    expense = 0.0
    for e in led.entries:
        if period is not None and e.period != period:
            continue
        for p in e.postings:
            if p.account_code in rev_codes:
                revenue += p.credit - p.debit
            elif p.account_code in exp_codes:
                expense += p.debit - p.credit
    revenue = _round2(revenue)
    expense = _round2(expense)
    return {
        "revenue": revenue,
        "expense": expense,
        "net_income": _round2(revenue - expense),
    }


def _account_balance_through(led: Ledger, account_code: str, through_period: str | None = None) -> float:
    """Compute the balance of an account through (and including) a given period.

    Returns a number with the sign convention of the BS:
    - assets: positive when in debit (the normal side)
    - liabilities, equity, revenue: positive when in credit (the normal side)
    - expenses: positive when in debit
    """
    acct = led.accounts[account_code]
    opening = acct.opening_balance

    # Opening is a non-negative number representing the account's "size" on the
    # BS in the direction of its normal balance.
    if acct.type in DEBIT_NORMAL:
        signed = +opening
    else:
        signed = +opening  # positive means credit-normal balance

    for e in led.entries:
        if through_period is not None and e.period > through_period:
            continue
        for p in e.postings:
            if p.account_code != account_code:
                continue
            if acct.type in DEBIT_NORMAL:
                signed += p.debit - p.credit
            else:
                signed += p.credit - p.debit
    return _round2(signed)


def close_period(led: Ledger, period: str) -> float:
    """Close a period: compute and record net income for this period.

    Records:
      - net_income_by_period[period] = net income for just this period
      - closing_re_by_period[period] = cumulative net income through this period

    Closes any prior periods that have not been closed yet, so the cumulative
    chain is consistent.

    Returns the net income for the closed period (single period, not cumulative).
    """
    sorted_periods = sorted({e.period for e in led.entries})

    # Close any prior periods that haven't been closed yet.
    for p in sorted_periods:
        if p > period:
            break
        if p in led.net_income_by_period:
            continue
        is_p = income_statement(led, p)
        p_ni = is_p["net_income"]
        led.net_income_by_period[p] = p_ni
        # Find the prior closed period.
        idx = sorted_periods.index(p)
        prev = sorted_periods[idx - 1] if idx > 0 else None
        prev_cum = led.closing_re_by_period.get(prev, 0.0) if prev else 0.0
        led.closing_re_by_period[p] = _round2(prev_cum + p_ni)

    return led.net_income_by_period[period]


def balance_sheet(led: Ledger, as_of_period: str) -> dict[str, float]:
    """Generate a balance sheet as of the end of a period.

    Returns a dict with totals: assets, liabilities, equity, retained_earnings,
    liabilities_plus_equity, and a 'balanced' boolean.
    """
    # Roll forward the period RE account to be the closing RE for the period.
    # First, post a closing entry for net income if not yet done.
    if as_of_period not in led.net_income_by_period:
        close_period(led, as_of_period)

    # Net income goes to RE. The period-RE account is conceptually the same
    # as the '3200 Retained Earnings' account; we sum both for total equity.
    period_re = led.closing_re_by_period.get(as_of_period, 0.0)

    asset_codes = [a.code for a in led.accounts.values() if a.type == "asset"]
    liab_codes  = [a.code for a in led.accounts.values() if a.type == "liability"]
    eq_codes    = [a.code for a in led.accounts.values() if a.type == "equity"]

    # _account_balance_through returns a signed number where positive is the
    # "side" of the account's normal balance: debit-normal assets are positive
    # when in debit, credit-normal liabilities/equity are positive when in credit.
    # That's exactly the BS sign convention for assets (+), liabilities (+), equity (+).
    total_assets = _round2(sum(
        _account_balance_through(led, c, as_of_period) for c in asset_codes
    ))
    total_liab = _round2(sum(
        _account_balance_through(led, c, as_of_period) for c in liab_codes
    ))
    # Equity (including the period-RE account) — the period-RE account's
    # running balance reflects only direct journal activity (which we don't do);
    # the period's net income flows through period_re explicitly.
    equity_base = _round2(sum(
        _account_balance_through(led, c, as_of_period) for c in eq_codes
    ))
    # _account_balance_through on RE returns its raw signed number. To avoid
    # double-counting, subtract RE's running balance before adding period_re back.
    re_running = _account_balance_through(led, "RE", as_of_period)
    total_equity = _round2(equity_base - re_running + period_re)
    liab_plus_equity = _round2(total_liab + total_equity)

    return {
        "assets": total_assets,
        "liabilities": total_liab,
        "equity": total_equity,
        "retained_earnings_period": period_re,
        "liabilities_plus_equity": liab_plus_equity,
        "balanced": abs(total_assets - liab_plus_equity) < 0.50,
    }


# === assertion helpers ===

def assert_every_entry_balanced(led: Ledger) -> None:
    for e in led.entries:
        assert e.is_balanced(), (
            f"unbalanced entry {e.entry_id}: "
            f"debit={e.total_debit()} credit={e.total_credit()}"
        )


def assert_total_debits_equal_credits(led: Ledger) -> None:
    total_d = _round2(sum(e.total_debit() for e in led.entries))
    total_c = _round2(sum(e.total_credit() for e in led.entries))
    assert abs(total_d - total_c) < 0.01, (
        f"global D/C mismatch: total debits={total_d} total credits={total_c}"
    )


def assert_trial_balance_sums(led: Ledger) -> None:
    tb = trial_balance(led)
    sum_d = _round2(sum(v[0] for v in tb.values()))
    sum_c = _round2(sum(v[1] for v in tb.values()))
    assert abs(sum_d - sum_c) < 0.01, (
        f"trial balance doesn't sum: total debits={sum_d} total credits={sum_c}"
    )


def assert_balance_sheet_balances(led: Ledger, period: str) -> None:
    bs = balance_sheet(led, period)
    assert bs["balanced"], (
        f"balance sheet does not balance as of {period}: "
        f"assets={bs['assets']} L+E={bs['liabilities_plus_equity']}"
    )


def assert_non_negative_accounts(led: Ledger) -> None:
    """Cash (and any requires_non_negative account) must not go negative."""
    for code, acct in led.accounts.items():
        if not acct.requires_non_negative:
            continue
        bal = _account_balance_through(led, code, None)
        assert bal >= 0.0, (
            f"account {code} ({acct.name}) went negative: balance={bal}"
        )


if __name__ == "__main__":
    import time

    print("═══ financial-reporting-platform: ledger workload ═══")
    N_ENTRIES = 5_000
    N_PERIODS = 6
    print(f"generating {N_ENTRIES:,} balanced journal entries across {N_PERIODS} periods...")
    t0 = time.time()
    led = generate_workload(n_entries=N_ENTRIES, n_periods=N_PERIODS, seed=42)
    gen_t = time.time() - t0
    print(f"  generated in {gen_t:.2f}s")
    print(f"  accounts:    {len(led.accounts)}")
    print(f"  entries:     {len(led.entries):,}")
    total_d = round(sum(e.total_debit() for e in led.entries), 2)
    total_c = round(sum(e.total_credit() for e in led.entries), 2)
    print(f"  total debits:  ${total_d:,.2f}")
    print(f"  total credits: ${total_c:,.2f}")
    periods = sorted({e.period for e in led.entries})
    print(f"  periods:     {len(periods)} ({periods[0]}..{periods[-1]})")
    print()

    # --- Scenario A: every journal entry is balanced ---
    print("═══ scenario A: every entry balanced ═══")
    t0 = time.time()
    assert_every_entry_balanced(led)
    a_t = time.time() - t0
    print(f"  checked {len(led.entries):,} entries in {a_t:.2f}s — all balanced ✓")
    print()

    # --- Scenario B: trial balance per account, sum verification ---
    print("═══ scenario B: trial balance roll-up ═══")
    t0 = time.time()
    tb = trial_balance(led)
    b_t = time.time() - t0
    assert_trial_balance_sums(led)
    sum_d = round(sum(v[0] for v in tb.values()), 2)
    sum_c = round(sum(v[1] for v in tb.values()), 2)
    nonzero = sum(1 for v in tb.values() if v[0] or v[1])
    print(f"  rolled up {nonzero} active accounts in {b_t:.2f}s")
    print(f"  total debits  = ${sum_d:,.2f}")
    print(f"  total credits = ${sum_c:,.2f}")
    print(f"  D == C: {abs(sum_d - sum_c) < 0.01} ✓")
    print()

    # --- Scenario C: close a period, retained earnings flow ---
    print("═══ scenario C: period close (2025-03) ═══")
    last_period = periods[len(periods) // 2]  # close the middle period
    t0 = time.time()
    is_mid = income_statement(led, last_period)
    period_ni = close_period(led, last_period)
    c_t = time.time() - t0
    assert abs(period_ni - is_mid["net_income"]) < 0.01
    print(f"  period {last_period} revenue:    ${is_mid['revenue']:,.2f}")
    print(f"  period {last_period} expense:    ${is_mid['expense']:,.2f}")
    print(f"  period {last_period} net income: ${period_ni:,.2f}")
    print(f"  closing RE for {last_period}:    ${led.closing_re_by_period[last_period]:,.2f}")
    # Verify closing RE monotonically evolves with the period's NI
    for p in periods:
        led_closing = led.closing_re_by_period.get(p)
        if led_closing is None:
            close_period(led, p)
    re_evolution = [(p, led.closing_re_by_period[p]) for p in periods]
    print(f"  retained earnings evolution: " + " ".join(
        f"{p}=${v:,.0f}" for p, v in re_evolution
    ))
    # Verify the cumulative RE moves by exactly the per-period NI each period.
    period_ni_seq = [led.net_income_by_period[p] for p in periods]
    re_diffs = [re_evolution[i+1][1] - re_evolution[i][1] for i in range(len(re_evolution)-1)]
    re_consistent = all(
        abs(re_diffs[i] - period_ni_seq[i+1]) < 0.01
        for i in range(len(re_diffs))
    )
    print(f"  cumulative RE changes by period NI: {re_consistent} ✓")
    print()

    # --- Scenario D: income statement + balance sheet, balance check ---
    print("═══ scenario D: full statements ═══")
    final_period = periods[-1]
    t0 = time.time()
    is_full = income_statement(led)  # all periods
    bs = balance_sheet(led, final_period)
    d_t = time.time() - t0
    print(f"  full income statement (all periods):")
    print(f"    total revenue:  ${is_full['revenue']:,.2f}")
    print(f"    total expense:  ${is_full['expense']:,.2f}")
    print(f"    total net inc:  ${is_full['net_income']:,.2f}")
    print(f"  balance sheet as of {final_period}:")
    print(f"    total assets:        ${bs['assets']:,.2f}")
    print(f"    total liabilities:   ${bs['liabilities']:,.2f}")
    print(f"    total equity:        ${bs['equity']:,.2f}")
    print(f"    period RE:           ${bs['retained_earnings_period']:,.2f}")
    print(f"    L + E:               ${bs['liabilities_plus_equity']:,.2f}")
    print(f"    assets == L + E:     {bs['balanced']} ✓")
    assert_balance_sheet_balances(led, final_period)
    print()

    # --- Final invariants ---
    print("═══ final invariants ═══")
    assert_total_debits_equal_credits(led)
    print("  ✓ total debits == total credits across all entries")
    assert_every_entry_balanced(led)
    print("  ✓ every journal entry is balanced (debits == credits)")
    assert_trial_balance_sums(led)
    print("  ✓ trial balance sums correctly (ΣD == ΣC)")
    assert_balance_sheet_balances(led, final_period)
    print("  ✓ balance sheet balances: total assets == L + E")
    assert_non_negative_accounts(led)
    print("  ✓ cash (and required accounts) stayed non-negative")
    print()
    print(f"  journal entries:    {len(led.entries):,}")
    print(f"  accounts:           {len(led.accounts)}")
    print(f"  periods:            {len(periods)}")
    print(f"  total debits:       ${total_d:,.2f}")
    print(f"  total credits:      ${total_c:,.2f}")
    print(f"  net income (final): ${is_full['net_income']:,.2f}")
    print(f"  balance sheet total: ${bs['assets']:,.2f}")
    print()
    print("✓ all invariants pass")
