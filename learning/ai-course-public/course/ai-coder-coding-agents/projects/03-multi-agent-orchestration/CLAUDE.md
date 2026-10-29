# CLAUDE.md — Multi-agent orchestrator

> This is the **orchestrator's** CLAUDE.md. Each worker pole has its own,
> narrower CLAUDE.md under `workers/<pole>/`.
>
> Treat them like CLAUDE.md files for different services in a microservice
> architecture: different concerns, different blast radius, different writes.

---

## What this project is

A multi-agent equity research pipeline. The orchestrator (this session) does
not write business logic; it dispatches poles and reconciles their results.
Five poles run in parallel:

1. **`data-pole`** — market data ingest, validation, caching.
2. **`research-pole`** — fundamentals + news enrichment.
3. **`strategy-pole`** — signal generation, model inference.
4. **`risk-pole`** — position sizing, drawdown guards, exposure limits.
5. **`execution-pole`** — broker API, order placement, fill reconciliation.

Every pole writes to the shared ledger. Every pole reads from it. There are
no direct pole-to-pole channels; everything goes through the ledger. The
reason is debuggability — when a pole misbehaves, the ledger is the single
place to look. See `notes/orchestration.md` for the full case.

---

## Hard rules

1. **No pole modifies another pole's output.** A pole that needs to disagree
   with another pole writes its disagreement into the ledger under its own
   namespace; the orchestrator reconciles.
2. **No pole calls the broker directly except `execution-pole`.** Every
   `orders.create(...)` outside `execution-pole/` is a bug, full stop.
3. **No pole commits to git on its own.** The orchestrator commits after
   reconciliation. Per-pole commits are un-replayable.
4. **Run the budget gate before any pole dispatch.** `python -m shared.budget
   check <phase>` must return `allow`. If it returns `deny`, stop and report.
5. **Speak the team's log shape.** Every pole writes structured JSON to
   stdout with at minimum `pole`, `phase`, `trace_id`, `event`, `ts`. See
   `contracts/log-event.schema.json`.

---

## Cost awareness

Each pole dispatch is an LLM call. The course's own decision for the capstone:

> Use Haiku for `data-pole`, `risk-pole`, and `execution-pole`.
> Use Sonnet for `research-pole` (needs more reasoning).
> Use Opus for `strategy-pole` only — it's the one that earns it.

This is the budget as the team runs it. If you change it, change
`shared/budget.py` first; the orchestrator reads from there.

---

## Reconciliation protocol

Each cycle:

1. Orchestrator seeds a `trace_id` and writes `cycle_started`.
2. All poles write their results to `shared/notes/ledger/<trace_id>.jsonl`.
3. Orchestrator polls the ledger, waits until all five poles have a final
   entry, then reconciles.
4. If reconciliation produces a trade, dispatch `execution-pole` with the
   reconciliation record. It writes back to the same ledger.
5. Orchestrator records `cycle_completed` and emits a one-line summary.

If a pole doesn't post within its timeout, the orchestrator records
`pole_timeout` and downgrades the cycle to "no-trade". See
`notes/orchestration.md` §"Timeouts" for what *not* to do.

---

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make test           # pytest, no broker required
```

Set `BROKER_API_KEY=test` for the execution-pole tests. They mock the broker.

---

## What this is NOT

- Not a single-agent system. Do not "simplify" by collapsing poles.
- Not a real broker integration. `workers/execution-pole/broker.py` is a stub.
  Replace before trading real money. (The course makes this disclaimer
  loudly — see `orchestrator/pole-contracts.md`.)
- Not horizontally scalable. Each pole is one Claude Code session; to scale
  beyond ~5 poles, see `notes/gas-town-notes.md`.