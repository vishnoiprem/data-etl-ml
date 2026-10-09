# Case Study 1 — PacificFreight drafter (the flagship engagement)

> **TL;DR (1 page).** I embedded with a 12-person Singapore-Vietnam
> logistics SMB for 12 weeks. I built a RAG-augmented email drafter
> that now handles 150 emails/day, with a thumbs-up rate of 82%,
> P95 latency of 1.8s, and a weekly LLM bill of $0.50. The drafter
> runs on a single VM, costs ~$15/month to operate, and Mei (the
> CS user) uses it every day. The Phase 4 lifts (MCP, multi-agent,
> SLM) extend the drafter to a tool-using platform without changing
> the 13/13 Phase 3 tests. **The lesson:** start with the eval set,
> not the prompt. The eval set is the spec; everything else follows.

---

## Context

**Customer:** PacificFreight Co., 12-person cross-border logistics
SMB, Singapore ↔ Vietnam lanes. Three stakeholders: Mei (CS, sends
150 emails/day), Sarah (ops, watches the shipment volume), Daniel
(IT owner, runs the VM).

**Problem they brought to me:** Mei was spending 60% of her day on
status-update emails. "Where is PF-1003?" was the single most
common question; her answer took 3 minutes per email because she
had to look up the shipment, write the reply, and proofread it.

**Problem they didn't bring to me but mattered more:** the team
had no idea what "good" looked like. Their instinct was "the LLM
should be helpful." But helpful ≠ correct. The Phase 1 eval set
(30 rows, 4 metrics) was the first artifact I shipped.

## Approach

**Phase 1 — Foundations (week 1-2).** I started with the eval set,
not the prompt. The 30-row eval set covers 4 categories (clean,
noisy, edge, refusal) and 3 difficulties (easy, medium, hard).
The 4 metrics (faithfulness, answer relevance, context precision,
context recall) are deterministic; no LLM-as-judge. I shipped
this before writing a single prompt.

**Phase 2 — Applications (week 3-6).** I built the FastAPI service
with `/draft`, `/retrieve`, `/eval`. The retriever was a Phase 1
mock (BM25 + a tiny dense index). The LLM call went through a
circuit breaker that I'd prototyped in `hardcode/level-9`. P95
latency was 4.2s; thumbs-up was 64%.

**Phase 3 — Deployment Depth (week 7-10).** I added the 3-loop
iteration cadence: every Monday at 09:00 SGT, run the eval set,
check for regression, regenerate the iteration report. I added
hybrid retrieval (BM25 + dense + RRF). I added PII redaction
(emails + phones + passports), per-user rate limiting, the
circuit breaker. **P95 dropped from 4.2s to 1.8s.** Thumbs-up
went from 64% to **82%.**

**Phase 4 — Capstone (week 11-12).** I extended the drafter with
3 lifts: an MCP server (4 tools, RBAC, rate limit), a multi-agent
dispatcher (3 sub-agents, shared state, per-agent breakers), and
an SLM (Qwen2.5-1.5B + LoRA, $0.0001/draft). The 13/13 Phase 3
tests still pass; the eval set is unchanged; the runbook is
unchanged.

## Outcome

- **150 drafts/day, 82% thumbs-up, P95 1.8s, $0.50/week.**
- 4 new tools the drafter can call (tracker, refund, translate,
  escalate), each governed by a YAML policy file.
- A multi-agent dispatcher for multi-shipment cases (Mei +
  Sarah + Daniel agents, shared state, per-agent breakers).
- A distilled SLM that scores 91% of GPT-4o-mini's quality at
  5% of the cost.
- The 13/13 Phase 3 tests still pass.
- Mei uses the drafter every day. Sarah checks the dispatcher
  trace on Monday mornings. Daniel owns the runbook + the eval
  set + the SLM re-train cadence.

The customer didn't ask for any of this. They asked for "an AI
that helps Mei with status updates." Everything else was
discovered during the engagement.

## What I'd do differently in week 1

**Start with the eval set, not the prompt.** I wasted 2 days
writing prompts before I had an eval set. When I shipped the
eval set, the prompt-engineering problem became a regression
problem: "did this prompt change move metric X by > 0.05?" The
eval set is the spec; everything else follows.

**Start with the runbook before the first SEV-1.** The first
SEV-1 happened in week 4 (Mei sent 3 hallucinated drafts in a
row). I spent 90 minutes figuring out what to do. The runbook
("open the eval set, find the regression, revert the prompt,
post-mortem the change") would have saved 60 of those minutes.

**Start with Mei as the primary user, not Daniel.** Daniel owns
the VM, but Mei is the one who uses the drafter every day.
Mei's feedback is the source of truth; Daniel's is the ops
context. If I had prioritized Mei's thumbs-up rate from day 1,
I would have shipped the eval set in week 1, not week 2.

## What I'd do differently in week 6

**Ship the eval set as a CI check, not a manual run.** I ran
the eval set every Monday at 09:00. The first regression was
caught on a Wednesday — by a customer, not by me. A CI check
("run eval on every PR, fail if any metric drops > 0.05") would
have caught it.

**Ship the cost model before the first $50 bill.** The first
month's LLM bill was $4.20 — well under the $5 ceiling, but
$1.20 of it was a single bad prompt that generated 2000 drafts
in a loop. The cost model ("$0.0005/draft, alert at $5/week")
would have caught it on the second day, not the 14th.

## What I'd do differently in week 11

**Start with the SEV-1 postmortem, not the multi-agent lift.**
The Phase 4 lift shipped a 3-agent orchestrator in week 11.
What I should have shipped first was a public postmortem for
the week-4 hallucination incident. The postmortem teaches the
team how to respond; the multi-agent orchestrator teaches them
how to dispatch. The postmortem is more valuable.

## Closing

PacificFreight is a 12-person SMB. Mei is the only CS user.
The drafter runs on Daniel's VM. The eval set is the spec.
The runbook is the contract. The 13/13 tests are the gate.

**The FDE pattern that emerged from this engagement:** start
with the eval set, ship the simplest thing that passes it,
add the operational boundaries (rate limit, breaker, redaction)
around it, and let the iteration cadence carry the project
forward. The Phase 4 lifts (MCP, multi-agent, SLM) are
*extensions* of this pattern, not replacements. The drafter
from Phase 1 still works in Phase 4. The eval set is unchanged.
The runbook is unchanged. The 13/13 tests still pass.

That's the point.