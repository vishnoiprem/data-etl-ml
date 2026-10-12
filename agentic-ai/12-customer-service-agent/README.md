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

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
