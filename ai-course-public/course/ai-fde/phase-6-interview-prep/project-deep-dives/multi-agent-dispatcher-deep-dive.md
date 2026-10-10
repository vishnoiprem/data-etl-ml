# The Multi-Agent Dispatcher Deep Dive (the 45-minute script, alt #1)

> **This is the alt-#1 deep-dive script.** Use it when the company wants a multi-agent or distributed-systems angle instead of a single-service angle. The signal: a candidate who can deliver this script without notes, in 45 minutes, with a working LangGraph trace, is showing they can own a multi-agent system at scale.

---

## Slide 1: Title (1 min)

> "Today I'm going to walk you through the multi-agent dispatcher I built for PacificFreight in Phase 4. It's a LangGraph orchestrator with 3 sub-agents: a CS drafter, an ops summarizer, and a cost/risk monitor. It went from a single LLM call in Phase 2 to a 3-agent orchestration that handles multi-shipment cases end-to-end. The result: Mei clicks 1 button instead of 5, Sarah gets an auto-generated ops summary, and Daniel sees the cost/risk note before the customer does."

**Cue:** 1 minute. Don't go over.

---

## Slide 2: The customer (2 min)

> "Same PacificFreight team — Mei (CS), Sarah (ops), Daniel (IT). The Phase 2 drafter handled single-shipment cases: 1 email, 1 shipment, 1 draft. By Phase 4, ~30% of emails mentioned 2+ shipments: a customer asks 'where are SF-1003 and SF-1004?' or 'refund SF-1003 and redirect SF-1004 to Singapore.' Mei was clicking the drafter button 3-5 times per case. Each click was a separate draft, with no shared context between them. The customer-facing metric: clicks per case. The ops metric: consistency across drafts. The IT metric: orchestrator latency."

**The signal:** same 3 stakeholders, 3 metrics, 3 roles. The new pain is the multi-shipment case.

---

## Slide 3: The problem (3 min)

> "Multi-shipment cases are different from single-shipment. (1) They need shared state: which shipments are in scope, what's the customer asking, what has each agent done so far. (2) They need routing: which agents run, in what order, with what handoff. (3) They need escalation: if the cost/risk threshold is exceeded, Daniel needs to be looped in. (4) They need observability: a trace that shows the full decision path. Mei's 5 clicks per case was the symptom; the disease was the lack of orchestration."

**The signal:** the 4 problems (state, routing, escalation, observability). A senior FDE names all 4.

---

## Slide 4: The constraint (1 min)

> "The orchestrator must add < 500ms to the existing P95 (1.8s → < 2.3s). It must respect the existing $0.50/week cost ceiling. It must not break the existing eval set: 30-row golden set, 91% faithfulness, 88% answer relevance. The orchestrator's eval set: 20-row multi-shipment cases (3-5 shipments each), graded on consistency (do the drafts reference the same shipment correctly?) and routing (does the right agent run?)."

**The signal:** the constraint, the math, the eval set. A senior FDE names the boundary.

---

## Slide 5: The architecture (5 min, with diagram)

```
[Customer Email: 3-shipment case]
      ↓
[Dispatcher: LangGraph orchestrator]
      ↓
  ┌──────────┼──────────┐
  ↓          ↓          ↓
[MeiAgent] [SarahAgent] [DanielAgent]
  CS drafter Ops summary Cost/risk
  ↓          ↓          ↓
[State: shared in-memory dict]
      ↓
[Combined Response: Mei draft + Sarah summary + Daniel note]
```

**The 5 design choices:**

1. **LangGraph StateGraph** for the orchestrator (declarative, easier to reason about than hand-rolled state machines).
2. **In-memory shared state** (a Python dict), scoped to the request. Phase 4 has no Redis; we add it in Phase 5 if traffic demands.
3. **Per-agent circuit breaker** so a Mei failure doesn't block Daniel.
4. **Routing rule:** Mei always runs first; Sarah runs if multi-shipment; Daniel runs if cost/risk threshold exceeded.
5. **Trace logging** to `usage.jsonl` with `agent_path` field showing the full decision path.

---

## Slide 6: The Mei agent (3 min)

> "The Mei agent is a wrapped drafter: it takes the customer email + the retrieved context + the shared state (which shipments are in scope), and produces a draft. It uses the same hybrid retriever (BM25 + dense + RRF), the same GPT-4o-mini inference, the same eval set. The wrap: the agent emits a `tool_call` for any shipment-level action (refund, redirect, escalate) instead of a free-text draft. The MCP server (Phase 4 P1) executes the call. The result is fed back into the prompt. The agent produces the final reply."

**The signal:** the Mei agent reuses Phase 2 + Phase 3 + Phase 4 P1. No code rewrite; the agent is a thin wrapper.

---

## Slide 7: The Sarah agent (3 min)

> "The Sarah agent is a new addition. It runs after Mei and only if `len(shipment_ids) > 1`. It produces a 1-paragraph ops summary: '3 shipments in scope: SF-1003 (in-transit, ETA Friday), SF-1004 (delivered), SF-1005 (customs hold, refund issued).' The summary is appended to Mei's draft. The customer sees: Mei's reply + a 'Summary' block with Sarah's note. Sarah (the human) sees the same draft in her inbox, so she can spot-check the summary without re-reading 3 shipment pages."

**The signal:** the Sarah agent adds value by reducing Sarah's reading time, not by replacing her.

---

## Slide 8: The Daniel agent (3 min)

> "The Daniel agent is a cost/risk monitor. It runs after Mei + Sarah and only if the cost/risk threshold is exceeded (e.g., refund > $100, or 3+ tool calls in 60 seconds, or any `escalate.to_human` call). It produces a 1-paragraph note: 'Cost estimate: $0.04 (Mei $0.02 + Sarah $0.01 + tool calls $0.01). Risk: medium (refund > $100). Recommend: human review before sending.' Daniel sees the note in his dashboard; he can approve, edit, or escalate."

**The signal:** the Daniel agent is the safety net. It catches the cases that would otherwise break the customer.

---

## Slide 9: The trace (3 min, with diagram)

```
$ python3 -c "
from agents import Dispatcher
d = Dispatcher()
result = d.run(email='I need to know where SF-1003 and SF-1004 are. Also refund SF-1005.')
print(result['agent_path'])
"
# Output: ['mei', 'sarah', 'daniel']
print(result['usage_log'])
# Output: {'mei': {...}, 'sarah': {...}, 'daniel': {...}}
```

**The signal:** the trace is a first-class artifact. Every orchestrator run is logged with `agent_path`, latency per agent, cost per agent, and the final response. The trace is the debugging tool.

---

## Slide 10: The eval set (3 min)

> "The orchestrator's eval set is 20 multi-shipment cases (3-5 shipments each). The metrics: (1) routing accuracy (does the right agent run?). (2) consistency (do Mei and Sarah reference the same shipment the same way?). (3) cost (does the total cost stay under the ceiling?). (4) latency (does the orchestrator stay under 2.3s P95?). The eval set runs on every PR. If any metric drops > 5%, the deploy is blocked. The eval set is the regression check."

**The signal:** the eval set is the spec. 20 multi-shipment cases, 4 metrics, CI gate.

---

## Slide 11: The numbers (3 min)

> "The numbers from the 4-week pilot: (1) clicks per case: 5 → 1 (80% reduction). (2) Mei's reading time per case: 4 min → 1 min (75% reduction). (3) cost per case: $0.04 (vs $0.05 single-shipment baseline; +$0.01 for Sarah + Daniel). (4) P95 latency: 1.8s → 2.1s (+16%). (5) escalations: 0.5/case → 0.05/case (90% reduction, because Daniel is auto-notified). The CFO's reaction: 'this is the system we should have had 6 months ago.'"

**The signal:** the numbers are concrete. 5 → 1 clicks, 4 min → 1 min reading, $0.04/case, 2.1s P95.

---

## Slide 12: The handoff (3 min)

> "The handoff to Daniel + Sarah + Mei's CS team was 4 weeks. The artifacts: (1) the orchestrator's `README.md` with the agent_path trace + the eval set. (2) the runbook with the 5 most common failure modes (orchestrator timeout, agent crash, MCP server down, cost ceiling breach, eval set regression). (3) the on-call rotation with the 3 escalation tiers (L1: agent failure → Mei's CS team; L2: orchestrator failure → Daniel's IT; L3: customer-impact → Mei + Daniel + me). (4) the 5-question 'FDE has left' test: 5/5 passed. The team can operate it without me."

**The signal:** the handoff is concrete. 4 artifacts, 5/5 questions passed, the team can run it.

---

## The 5 follow-up Q&A

**Q1: "Why LangGraph instead of a hand-rolled state machine?"**

> "LangGraph's StateGraph is declarative — I write the nodes (agents) and the edges (routing rules), and it handles the state management, the trace logging, and the conditional edges. A hand-rolled state machine would be 200 lines of Python with no declarative advantage. LangGraph is the right level of abstraction for a 3-agent orchestrator; below 3 agents, a hand-rolled machine is simpler; above 10 agents, I'd consider a multi-tenant orchestrator with Redis-backed state."

**Q2: "What if the Mei agent crashes mid-run?"**

> "Per-agent circuit breaker. The orchestrator catches the exception, marks Mei as 'failed' in the shared state, and routes to Sarah + Daniel with a note ('Mei agent failed; Sarah + Daniel ran without Mei's draft'). The customer sees: 'I'm having trouble with part of your request. Here's what I can answer.' The Mei agent's failure is logged to `usage.jsonl` with the `error_message` field. The on-call rotation gets paged (L1: Mei's CS team reviews the failed cases)."

**Q3: "How do you scale the orchestrator to 10K cases/day?"**

> "Horizontal scaling behind a load balancer. Each case is independent (no shared state across cases). The orchestrator's state is in-memory per case, not per server. If we add 10× traffic, we add 10× orchestrator instances. The bottleneck is the LLM API rate limit, not the orchestrator. We shard by `tenant_id` so that one customer's traffic doesn't affect another's."

**Q4: "How do you prevent the cost ceiling from being breached?"**

> "The orchestrator checks the running cost after every agent. If the cost > $0.10/case (the per-case ceiling), the orchestrator short-circuits: it skips the next agent and returns Mei's draft + a 'cost limit reached' note. The cost ceiling is enforced at the orchestrator, not the LLM API. The eval set includes 5 high-cost cases that test the ceiling enforcement."

**Q5: "Why not just have Mei handle multi-shipment cases without an orchestrator?"**

> "Mei can, but the 3-agent split gives us 3 benefits: (1) Sarah's summary is consistent across all 3 shipments, even when Mei's draft references only 1. (2) Daniel's cost/risk note is auto-generated, so Mei doesn't have to remember to ask. (3) The trace is a first-class artifact for debugging. The orchestrator is 300 lines of Python; the 3 agents reuse 95% of Phase 2-3 code. The trade-off: +16% latency for +80% reduction in clicks. The customer-facing metric improves; the latency is still under 2.3s."

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../system-design/09-agentic-ai.md` | The multi-agent architecture + the policy file |
| `../company-experiences/databricks-ai-fde.md` | The decomposition + the data plane story |
| `../decomposition/README.md` | The 4-step framework applied to a multi-agent system |

---

## The thesis

**The multi-agent dispatcher deep-dive is the alt-#1 45-minute script.** The signal: a candidate who can deliver it without notes, with a working LangGraph trace, the 20-row multi-shipment eval set, the per-agent circuit breaker, and the 5-question "FDE has left" test — is showing they can own a multi-agent system at scale.

**The 12 slides are the muscle memory.** The 5 follow-up Q&A are the practice bank. The 5-question test is the handoff rubric.

**Use this script when the company wants a multi-agent angle.** The PacificFreight deep-dive (`pacificfreight-deep-dive.md`) is the single-service angle. Choose the one that matches the company's signature round.
