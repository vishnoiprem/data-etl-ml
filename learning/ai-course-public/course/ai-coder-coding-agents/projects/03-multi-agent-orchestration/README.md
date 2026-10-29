# 03 — Multi-agent orchestration

> **Week 3 capstone.** A five-pole multi-agent equity research pipeline.
> The orchestrator dispatches data / research / strategy / risk / execution
> poles; every pole writes to a shared JSONL ledger.

---

## What this is

The course's Week 3 capstone. The pipeline is real in the sense that every
function and schema described below exists and runs — the trading decisions
are *simulated*. A `BROKER_API_KEY=test` environment gets you through the
`execution-pole` test suite. Real money is not the lesson.

The course's three multi-agent comparison builds (Claude Agent Teams, GSD,
Gastown) all reduce to this skeleton in different ways. If you understand
this skeleton, you understand the trade-offs of the three patterns.

---

## Files

```
03-multi-agent-orchestration/
├── CLAUDE.md                       ← orchestrator's contract
├── shared/
│   ├── budget.py                   ← risk gates, pure functions
│   └── notes/
│       ├── README.md               ← ledger rules
│       └── ledger/                 ← JSONL cycle records (gitkeep + per-cycle files)
├── workers/
│   ├── data-pole/CLAUDE.md
│   ├── research-pole/CLAUDE.md
│   ├── strategy-pole/CLAUDE.md
│   ├── risk-pole/CLAUDE.md
│   └── execution-pole/CLAUDE.md
├── contracts/
│   ├── quote.schema.json
│   └── log-event.schema.json
├── tests/
│   └── test_budget.py              ← 22 tests on the risk gates
├── pyproject.toml
├── Makefile
└── notes/
    └── orchestration.md
```

---

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make test          # 22 tests, no broker, no LLM
```

All Week 3 tests are pure (no broker, no LLM) so `make test` is fast in
addition to being thorough.

---

## The reconciliation protocol

1. Orchestrator generates a `trace_id` (8+ lowercase hex chars).
2. Orchestrator dispatches the five poles with the `trace_id` and a
   small, schema-validated payload each.
3. Each pole writes its output to `shared/notes/ledger/<trace_id>.jsonl`.
4. Orchestrator polls until all five poles have a final entry, OR `POLE_TIMEOUT_S`
   elapses (`90s` default).
5. Orchestrator reconciles. If reconciliation produces a trade and the
   `risk-pole` returned `allow`, dispatch `execution-pole` with the
   reconciliation record. Otherwise log `cycle_no_trade` and start cycle N+1.
6. After dispatching `execution-pole`, the orchestrator waits for the
   `filled` entry and closes the cycle.

A full worked example is in the lecture notes (Day 4 — "Multi-Agent Team
Build: Live Trading Dashboard with Claude Opus").

---

## The hard limits

| Limit | Value | Where |
|---|---|---|
| Max position size | 5% of NAV per name | `shared/budget.py:MAX_POSITION_PCT` |
| Max gross exposure | 1.5× NAV | `shared/budget.py:MAX_GROSS_EXPOSURE` |
| Max drawdown (no new longs) | 8% trailing 20-day peak-to-trough | `shared/budget.py:MAX_DRAWDOWN_PCT` |
| Max trades/day | 12 | `shared/budget.py:MAX_TRADES_PER_DAY` |
| Slippage warning | 1.0% drift from consensus quote | `shared/budget.py:SLIPPAGE_WARN_PCT` |
| Per-cycle LLM budget | $5.00 | `shared/budget.py:MAX_CYCLE_COST_USD` |

These numbers are the course's. Changing any of them is a PR with a
backtest notebook, not a config-file edit.

---

## Test status

```
$ make test
22 passed
```

---

## What this is NOT

- **Not a paper-trading system.** The `execution-pole` broker stub returns
  fills at the consensus quote. There is no real broker integration,
  because giving people a working paper-trading script they then point at a
  live account is a worse failure mode than shipping nothing.
- **Not horizontally scalable as-is.** The orchestrator maintains the pole
  contracts in its own context. Five poles is the practical ceiling for one
  Claude Code session. Beyond that, see `notes/gas-town-notes.md`.
- **Not adversarially robust.** The trust model is "poles authored by one
  team." A pole that one team cannot audit should be replaced with a
  validated HTTP service.
- **Not the missing half.** A real trading system needs a backtester, a
  kill-switch, an audit log reviewer, a drawdown dashboard, and a regulator-
  facing journal. None of those are in scope.

---

**Last updated:** 2026-10-21