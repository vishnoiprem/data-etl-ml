# Capstone presentation script — PacificFreight drafter (live demo)

> **Total time: 10 minutes.** This is the slide-by-slide script for
> the live demo to the evaluation panel. Each slide has a time
> budget; the transitions are scripted. The rehearsal checklist
> ([`REHEARSAL-CHECKLIST.md`](./REHEARSAL-CHECKLIST.md)) is the
> 10-minute pre-demo.

## Setup (before the demo starts)

- `uvicorn service.app:app --host 0.0.0.0 --port 8000` running
- `ollama` running with `pf-drafter` imported
- `python3 slm/serve.py` running on port 8001
- The dashboard loaded (the Prometheus UI or a custom dashboard)
- 3 sample emails pre-loaded (in a `sample_emails.md` file the
  panel can see)
- 1 SEV-1 scenario pre-loaded (the week-11 hallucination incident
  from [`engagement-3-postmortem.md`](./engagement-3-postmortem.md))

## Slide 1 — The FDE pattern (1 minute)

**Goal:** orient the panel. What is an FDE? What's the pattern?

**Talking points:**
- "I'm a Forward-Deployed Engineer. I embed with a customer,
  build something they use, and leave them in steady state."
- "The pattern that emerged from my engagements: **eval-set-as-spec,
  runbook-as-contract, cost-ceiling-as-score.**"
- "Today I'm going to demo the PacificFreight drafter, the system
  I built over 12 weeks with a 12-person Singapore-Vietnam logistics
  SMB."

**Transition:** "Let me show you the system in action."

## Slide 2 — The drafter live demo (3 minutes)

**Goal:** show the drafter working. 3 emails, dashboard updating
in real-time.

**Setup:** open the browser to `http://localhost:8000/docs` (the
FastAPI Swagger UI).

**Action 1 (45s):** Send email #1 — "Hi, where is my shipment
PF-1003? — Mei Lin"
- Show the LLM call returning a draft that mentions "held at
  Singapore customs pending duty payment"
- Show the eval set running against this draft (faithfulness
  should be 0.94)
- Show the cost: $0.0005 for the GPT-4o-mini call

**Action 2 (45s):** Send email #2 — "PF-1002 stuck in transit??
Please advise."
- This is a multi-shipment case (the email mentions 2 shipments:
  PF-1002 and the inferred PF-1003). The drafter auto-routes
  to `/dispatch` (the multi-agent endpoint).
- Show the 3-agent response: Mei's draft, Sarah's summary,
  Daniel's note.
- Show the dispatcher trace in the dashboard.

**Action 3 (45s):** Send email #3 — "I'd like a refund for
PF-1003. Charged twice."
- Mei (cs_junior) cannot authorize the refund → 403 from the MCP
  server.
- The drafter falls back to a free-text draft that says
  "I'll escalate to a senior colleague to process the refund."
- Show the audit log entry: `tool=refund.create, status=403,
  role=cs_junior`.

**Action 4 (45s):** Show the dashboard.
- 150 drafts/day, 82% thumbs-up, P95 1.8s, $0.50/week.
- The cost model: $0.0005/draft × 150 = $0.075/day = $0.525/week.
- The eval set: last run was Monday 09:00 SGT; faithfulness 0.94,
  ansrel 0.91, ctxp 0.90, ctxr 0.93.

**Transition:** "That's the Phase 3 drafter. Now let me show you
the Phase 4 lifts."

## Slide 3 — The MCP server live demo (2 minutes)

**Goal:** show the MCP server in action. 4 tools, RBAC, rate limit.

**Setup:** open a terminal with `python3 service/mcp_server.py`
ready to run the CLI demo.

**Action 1 (45s):** Run the CLI demo. Show:
- `tracker.lookup` as Mei (cs_junior) → 200, cost=1 credit
- `refund.create` as Mei → 403, error="role not authorized"
- `refund.create` as Alice (cs_senior) → 200, ticket=REF-...
- `translate.to` as Mei → 200, translation prefixed with `[VI]`
- 6 `refund.create`s as Alice → first 5 allowed, 6th returns 429
  (60 credits/min budget, 10 credits/refund)

**Action 2 (45s):** Open `mcp_policies.yaml` in the editor. Show
the structure:
- 5 roles (`cs_junior`, `cs_senior`, `ops`, `it`, `system`)
- 4 tools with `cost_credits` (1, 10, 5, 1)
- Rate limits per_user_per_min
- Budget: 60 credits/min

**Action 3 (30s):** Edit the YAML to add a 5th tool, `label.print`.
Show the policy change is the only thing needed — no Python change.

**Transition:** "That's the MCP lift. Now let me show you the
multi-agent orchestrator."

## Slide 4 — The multi-agent orchestrator trace (1 minute)

**Goal:** show the orchestrator working on a multi-shipment case.

**Setup:** open a terminal with `python3 service/agents.py --case multi_shipment`.

**Action 1 (30s):** Run the CLI. Show the 3-part response:
- Mei's draft (the customer reply)
- Sarah's summary (the cross-shipment aggregate)
- Daniel's note (the cost/risk/audit)

**Action 2 (30s):** Show the trace in `state.trace`:
- `dispatcher.start` (with `n_shipments=3`, `user_id=alice@pf.com`, `role=cs_senior`)
- `mei` (with `ok=True`, `latency_ms=...`)
- `sarah` (with `ok=True`, `latency_ms=...`)
- `daniel` (with `ok=True`, `latency_ms=...`)
- `dispatcher.end` (with `n_tool_calls=6`, `cost_usd=$0.0006`)

**Transition:** "That's the multi-agent lift. Now the SLM."

## Slide 5 — The SLM cost model (1 minute)

**Goal:** show the cost reduction. 64% bill reduction at 10×
volume.

**Setup:** open the browser to `http://localhost:8001/health` (the
SLM serve).

**Action 1 (30s):** Show the SLM serve responding.
- `GET /health` → `{ok: True, model: "pf-drafter-lora", back_end: "mock"}`
- `POST /draft` with email #1 → draft in < 50ms, cost=$0.0001

**Action 2 (30s):** Show the cost model table (from
[`engagement-4-slm-cost.md`](./engagement-4-slm-cost.md)):
- GPT-4o-mini: $0.50/week
- SLM (80% case) + GPT-4o-mini (20% case): $0.19/week (64%
  reduction)
- At 10× volume: $3.78/month (vs $10.50/month for GPT-4o-mini alone)

**Transition:** "That's the SLM lift. Now the handoff."

## Slide 6 — The 5-question "FDE has left" test (1 minute)

**Goal:** show the proof that the customer can run the system
without me.

**Setup:** open [`engagement-5-handoff.md`](./engagement-5-handoff.md)
in the browser.

**Action 1 (30s):** Read the 5 questions:
1. What does the drafter do?
2. How do you know it's working?
3. What breaks first when it goes wrong?
4. How do you fix it?
5. What's the cost ceiling?

**Action 2 (30s):** Show Daniel's, Mei's, and Sarah's answers
(at 30 days and 60 days post-handoff). All 3 answered all 5
correctly. The customer is in steady state.

**Transition:** "That's the proof. Now the bigger picture."

## Slide 7 — Portfolio + case studies + what I'd do differently (1 minute)

**Goal:** tie it all together. The pattern, the projects, the
lessons.

**Action 1 (30s):** The 4 projects + 5 case studies + 3 lessons
+ 25 tests. The eval-set-as-spec, runbook-as-contract,
cost-ceiling-as-score.

**Action 2 (30s):** What I'd do differently in week 1:
- Start with the eval set, not the prompt (I wasted 2 days
  writing prompts before I had an eval set)
- Start with the runbook before the first SEV-1 (the first
  SEV-1 took 90 minutes; the runbook would have saved 60)
- Start with Mei as the primary user, not Daniel (Mei's
  feedback is the source of truth)

**Closing (10s):** "The FDE pattern is eval-set-as-spec,
runbook-as-contract, cost-ceiling-as-score. The handoff is the
proof. Thank you."

## Q&A buffer (10 minutes)

Common questions:

1. **"Why YAML, not a database?"** Because YAML is
   code-reviewable, version-controlled, and auditable. A
   database change is invisible to the next person who reads
   the repo. (See [`01-mcp-tools-and-policies.md`](../technical/01-mcp-tools-and-policies.md).)
2. **"Why LoRA, not full fine-tune?"** Because LoRA fits on a
   Mac M-series in 30 minutes; full fine-tune needs a GPU
   cluster. The 91% quality ratio is the same either way.
   (See [`03-fine-tuning-and-serving-slm.md`](../technical/03-fine-tuning-and-serving-slm.md).)
3. **"What's the worst-case failure mode?"** The drafter
   emits a hallucinated draft. Mei reverts it; Daniel rolls
   back; the eval set catches it. Recovery time: ~30
   minutes. (See [`engagement-3-postmortem.md`](./engagement-3-postmortem.md).)
4. **"How do you know the SLM is safe to ship?"** The eval
   set runs against the SLM. If it scores above 90% of
   GPT-4o-mini, we ship in shadow mode for 1 week. If the
   A/B test holds, we promote. (See [`engagement-4-slm-cost.md`](./engagement-4-slm-cost.md).)
5. **"What's the next phase?"** Phase 5: production. Redis
   instead of in-process dicts. Real OAuth for the MCP
   server. Real ollama deployment with the merged adapter.
   The drafter doesn't change.