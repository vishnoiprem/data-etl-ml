# Orchestration notes — Week 3

The Week 3 capstone pits three multi-agent patterns against each other: Claude
Agent Teams, GSD, and Gastown. They differ in shape but share a hard lesson
the course insists on. This file is that lesson, distilled.

---

## The single load-bearing rule

> **One pole writes, one pole owns the truth.** Every other pole that disagrees
> writes its disagreement into its own ledger entry. Reconciliation is the
> orchestrator's job — not a pole's.

If a pole can write to another pole's output, you have a *distributed systems*
problem, not a multi-agent problem. Bugs become unreproducible. Poles that
"helpfully" overwrite each other for "consistency" are the most common Week 3
failure.

---

## Why a JSONL ledger, not Postgres

See `shared/notes/README.md` §"Why a file and not a database." Three reasons:

1. **Replay.** Bytes, not queries.
2. **Diffability.** Git-clean ledgers from notable cycles.
3. **Zero dependency when debugging at midnight.**

When the course surveyed teams after Week 3, every team that had built a
"real" Postgres-backed ledger had migrated back to JSONL by Week 4.

---

## The kind of pole dispatch that goes wrong

```python
# BAD: orchestrator embeds an LLM-generated instruction per pole
poles["strategy-pole"].dispatch(
    instruction="here's a 4000-token essay on what to do this cycle…"
)
```

The "essay" pattern is what produces un-replayable runs — the same `trace_id`
yields different behaviour depending on the orchestrator session's mood. The
course's rule:

```python
# GOOD: each pole gets a small, deterministic request
poles["strategy-pole"].dispatch(
    trace_id=trace_id,
    proposal_record=proposal,           # small JSON, schema-validated
    risk_limits_snapshot=limits,        # the actual numbers, copied
    timeout_s=POLE_TIMEOUT_S,
)
```

No prose. The pole's own CLAUDE.md says what to do. The orchestrator hands
over context, not instructions.

---

## Why the budget module is small and pure

`shared/budget.py` is ~70 lines of plain functions and constants. No I/O, no
state, no LLM. Every pole that needs to make a risk call imports the same
function.

> If your risk code touches the network, your risk code is wrong.

This is not aesthetic. The point of having a pure module is that a test
runner can exercise every risk gate in 0.06 seconds with no broker, no
network, no $5 in LLM spend. See `tests/test_budget.py` — 22 tests, 0.06s.

---

## Idempotency in `execution-pole`

Two-step protocol on every order:

1. **Write `dispatched` to the ledger** with the deterministic id
   `{trace_id}:{symbol}:{side}`. The id is the broker's `client_order_id`.
2. **Place the order.** If the network call fails after we wrote the
   `dispatched` entry, retry — but only on a fresh `trace_id`. If you retry
   on the same `trace_id`, the broker deduplicates (good) but your local
   `dispatched` count for this cycle is off by one (bad).

The failure mode the course saw most: `execution-pole` retries an order
*without* a fresh `trace_id` because the network call returned a generic
`ECONNRESET` and the pole assumed "the order didn't go through." It did.
The retry fills the same order.

---

## Timeouts — the most leaked control

Default: `POLE_TIMEOUT_S = 90.0`. A pole that hasn't written a final entry in
90 seconds has either:

- Hanged (a real LLM context-too-large problem).
- Crashed silently.
- Decided a quiet "no-op" was best.

The right answer in *every* case is the same: **downgrade to no-trade for
this cycle and emit `pole_timeout`.**

The wrong answer is to raise the timeout. A 90-second timeout forces a pole
to fail loudly when it's sick; a 600-second timeout lets a sick pole hold up
the cycle. Always raise the cycle rate, never the per-pole timeout.

---

## Pole-tier scaling

Five poles is the limit for a single orchestrator session. Beyond that, the
LLM doing the orchestration loses the ability to maintain consistent pole
contracts in context.

When you need 8+ poles, the course's pattern is **Gastown** — a second
orchestrator tier that dispatches "pole teams" rather than poles. See
`notes/gas-town-notes.md` (not written yet — defer to the lecture recording).

---

## What this capstone doesn't teach you

- **Adversarial robustness.** A pole that another pole prompts adversarially
  is out of scope. The trust model here is "all poles were authored by the
  same team." Cross-team poles, malicious prompts, prompt injection through
  vendor data: those are Day 5 of a different course.
- **Backtest fidelity.** The risk limits here are real but the data feed is
  simulated. A backtest that respects these limits would need a YearOf-Data
  set that's larger than the course's.
- **Production deployment.** This is a research pipeline, not a hosted
  service. Putting it behind a public webhook would require a separate
  project.

---

**Last updated:** 2026-10-21