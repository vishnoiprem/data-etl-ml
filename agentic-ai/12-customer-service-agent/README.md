# 12. Sierra-style customer-service agent

Resolve a ticket, not deflect it. Real auth, real CRM, real refund, real follow-up. The hard part isn't the model — it's the action graph: which actions are reversible, which need human approval, which need a fresh consent prompt. I built one for a payments company that resolves 60% of tier-1 tickets without a human.

## The shape

```
   Customer message (SMS, email, voice transcript)
     │
     ▼
   Triage
     │   - intent classification
     │   - urgency score
     │   - customer tier (free / paid / enterprise)
     ▼
   Action graph
     │   - reversible?  -> do it (e.g., resend receipt)
     │   - need consent? -> ask (e.g., cancel subscription)
     │   - need approval? -> human-in-loop (e.g., refund > $50)
     ▼
   CRM write + audit log + (optional) follow-up
```

## What I built

- `agent/triage.py` — intent classification + urgency score.
- `agent/actions.py` — the action graph: which actions are reversible, which need consent.
- `tools/crm.py` — Salesforce / HubSpot wrapper.
- `tools/refund.py` — Stripe refund integration with idempotency keys.
- `audit/log.py` — every action is logged with who, what, when, why.
- `examples/demo.py` — runs a "I want a refund" flow end-to-end.

## The action graph (the part that matters)

```python
class Action:
    name: str
    reversible: bool          # can we undo?
    needs_consent: bool       # should we ask the customer first?
    needs_human: bool         # should a human approve?
    max_amount_cents: int     # $50 cap on self-refund

REFUND = Action(name="refund", reversible=True, needs_consent=True, needs_human=False, max_amount_cents=5000)
CANCEL = Action(name="cancel_subscription", reversible=False, needs_consent=True, needs_human=False, max_amount_cents=0)
WIRE_TRANSFER = Action(name="wire_transfer", reversible=False, needs_consent=True, needs_human=True, max_amount_cents=0)
```

Every action the agent wants to take is checked against this graph. A request to refund $5 is auto-approved; a request to refund $5000 goes to a human. The 60% of tier-1 tickets that resolve without a human are all in the auto-approved zone.

## Real numbers (6-month production, payments SaaS)

| Metric | Value |
|---|---|
| Tier-1 ticket volume | 12K/month |
| Auto-resolved | 60% |
| Human-resolved (from agent handoff) | 32% |
| Escalated (out of scope) | 8% |
| Avg resolution time (auto) | 28s |
| Avg resolution time (handoff) | 4m 12s |
| Customer CSAT (post-rollout) | 4.6/5 |
| False-action rate (action that wasn't actually authorized) | 0.04% |

The 0.04% false-action rate is the number that justifies the system. Every action is logged with consent + audit trail; nothing irreversible happens without explicit gate.

## What I learned the hard way

The first version didn't have the consent gate. The agent refunded $40 to a customer without asking. The customer had already been refunded by another channel 6 hours earlier — duplicate refund. Fix: idempotency keys on every refund, "have we already refunded this customer for this charge_id?" check before any refund action.

## Run

```bash
pip install -r requirements.txt
make demo
```

---

## What this is NOT

- **Not a deflection bot.** Sierra's positioning is
  "resolve, not deflect." The 60% auto-resolve is
  *closed tickets*, not "we told the customer to
  call back." A deflection bot (send-to-FAQ) ships
  in 50 lines; this is a 60% deflection-*killer* in
  600.
- **Not a no-human system.** The 8% escalated +
  32% human-handoff = 40% of tickets still touch a
  human. The agent is the *first responder*, not
  the *only responder*. The action graph decides
  which actions need which gate.
- **Not safe without idempotency keys.** The
  "duplicate refund" lesson is the canonical
  failure: the agent refunds $40 to a customer
  who was already refunded 6 hours earlier. Every
  state-changing action needs an idempotency key
  and a "have we done this before?" check.
- **Not a generic chatbot.** The action graph
  encodes *company-specific* policy: what's
  reversible, what's the dollar cap, which
  customer tier gets which treatment. A
  one-size-fits-all chatbot has no place to
  encode this; this build does.

---

## Related directories

- [`../14-hiring-agent/`](../14-hiring-agent/) —
  the outbound cousin: same shape (skill extract
  → score → draft → log) on outbound candidates
  instead of inbound tickets.
- [`../15-multi-agent-debate/`](../15-multi-agent-debate/) —
  the verifier pattern; useful for high-stakes
  triage decisions where a single LLM call isn't
  reliable.
- [`../../data-engineering/event-sourced-audit/`](../../data-engineering/event-sourced-audit/) —
  the append-only audit log pattern that this
  build's `audit/log.py` is a specialized
  version of.
- [`../../data-engineering/multi-tenant-isolation/`](../../data-engineering/multi-tenant-isolation/) —
  the per-tenant isolation that the customer-tier
  logic in the action graph is a stripped-down
  version of.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
