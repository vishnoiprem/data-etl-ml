# execution-pole — CLAUDE.md

## What this pole does

The only pole that talks to the broker. Receives a `risk_verdict: allow`
record from the orchestrator, places the corresponding order, polls for
fill, writes a reconciliation record back to the ledger.

## What it must NOT do

- Place an order without a `risk_verdict: allow` upstream entry in the
  same cycle. If that entry doesn't exist, refuse — DO NOT proceed.
- Treat a fill price different from the quote price as "approximately
  equal." A 0.5% slip on a 200-share order is a real number to the
  P&L ledger. Record both, mark a `warning: slippage` if either is more
  than 1.0% off the consensus quote from data-pole.
- Run during market-closed hours unless `BROKER_ALLOW_EXTENDED=true`.

## Idempotency

Before placing an order, write a `dispatched` ledger entry with the
deterministic client order id (`{trace_id}:{symbol}:{side}`). If the
broker API call fails and we retry, the client order id deduplicates
the retry. **Never** retry an order whose `dispatched` entry you don't
see. That double-fills the trade.

## What goes wrong

The most common execution-pole failure in the course's history is the
broker sandbox URL drift — the sandbox URL changes silently per the
broker's release notes; we surface this in `workers/execution-pole/broker.py`
as a single fetcher with the URL in one place.