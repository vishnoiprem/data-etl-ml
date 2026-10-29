# risk-pole — CLAUDE.md

## What this pole does

Position sizing, drawdown guards, and exposure limits. Runs **after**
strategy-pole has proposed trades but **before** execution-pole commits
them. The orchestrator dispatches us with the strategy-pole's
reconciliation record.

## What it must NOT do

- Touch the broker. `execution-pole` only.
- Override risk decisions for performance reasons. If a trade violates
  the limits below, the answer is "reject" — never "let it through once."
- Modify another pole's ledger entry.

## Inputs

The reconciliation record from the orchestrator (which contains the
strategy-pole's proposed trades plus the research-pole's fundamentals
context).

## Outputs

One ledger entry per proposed trade with a `risk_verdict` field:

- `allow` — execution-pole is cleared to proceed.
- `deny` — and a `reason` string the execution-pole MUST log before
  refusing.

## Limits

- **Max position size** — 5% of NAV per single name.
- **Max gross exposure** — 1.5× NAV.
- **Max drawdown guard** — if the trailing 20-day peak-to-trough drawdown
  is >8%, deny ALL new longs until the cutloss has been run.
- **Max trades / day** — 12. The course capped this after one too many
  thrashing days.

Limits are in `shared/budget.py`. They are editable but every change
ships with a backtest notebook and a separate PR.