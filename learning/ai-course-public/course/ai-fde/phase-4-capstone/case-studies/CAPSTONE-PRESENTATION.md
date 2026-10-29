# Capstone presentation — PacificFreight drafter (10-minute live demo)

> **Total time: 10 minutes.** This is the slide-by-slide script for the live demo to the evaluation panel. Each slide has a time budget; the transitions are scripted; the speaker notes are explicit; the Q&A prep has 10 worked answers. **The rehearsal checklist ([`REHEARSAL-CHECKLIST.md`](./REHEARSAL-CHECKLIST.md)) is the 10-minute pre-demo; this document is what you say during the demo.** A principal FDE treats a demo as a system, not a performance — every slide has an entry, a payload, an exit, and a back-out.
>
> **Evaluation rubric mapping** — this demo is graded on 4 dimensions: (1) **System correctness** (does it run?), (2) **Operational discipline** (does it have eval set, runbook, cost model, on-call?), (3) **Communication quality** (does the FDE narrate failure modes, trade-offs, and "what I'd do differently"?), (4) **Handoff readiness** (can the panel answer the 5 questions after the demo?). Each slide below names which dimension it serves.

---

## Table of contents

- [§1 Meta — the 10,000-foot view](#1-meta--the-10000-foot-view)
- [§2 Pre-demo checklist (the contract)](#2-pre-demo-checklist-the-contract)
- [§3 The 7 slides (slide-by-slide, with speaker notes)](#3-the-7-slides)
  - [Slide 1 (1:00) — The FDE pattern](#slide-1-100--the-fde-pattern)
  - [Slide 2 (3:00) — The drafter live demo](#slide-2-300--the-drafter-live-demo)
  - [Slide 3 (2:00) — The MCP server live demo](#slide-3-200--the-mcp-server-live-demo)
  - [Slide 4 (1:00) — The multi-agent orchestrator trace](#slide-4-100--the-multi-agent-orchestrator-trace)
  - [Slide 5 (1:00) — The SLM cost model](#slide-5-100--the-slm-cost-model)
  - [Slide 6 (1:00) — The 5-question "FDE has left" test](#slide-6-100--the-5-question-fde-has-left-test)
  - [Slide 7 (1:00) — Portfolio + case studies + what I'd do differently](#slide-7-100--portfolio--case-studies--what-id-do-differently)
- [§4 Q&A prep (10 questions, 10 worked answers)](#4-qa-prep-10-questions-10-worked-answers)
- [§5 Evaluation rubric mapping (4 dimensions, 8 cells)](#5-evaluation-rubric-mapping-4-dimensions-8-cells)
- [§6 Backup plans (the 5 things that go wrong)](#6-backup-plans-the-5-things-that-go-wrong)
- [§7 The "demo is a system" framing](#7-the-demo-is-a-system-framing)
- [§8 References](#8-references)

---

## §1 Meta — the 10,000-foot view

### 1.1 The 1-line summary

> **"I build AI services that survive the customer. Today I'm going to show you the PacificFreight drafter — a 12-week engagement with a 12-person Singapore-Vietnam logistics SMB — and prove that the customer can run it without me."**

### 1.2 The time budget (the principal-FDE's discipline)

| Block | Time | What it serves |
|---|---|---|
| Slides 1-2 (pattern + live demo) | 4:00 | Hook + proof-of-system-correctness |
| Slides 3-4 (MCP + multi-agent) | 3:00 | Proof-of-extension-correctness |
| Slide 5 (SLM) | 1:00 | Proof-of-cost-discipline |
| Slide 6 (5-question test) | 1:00 | Proof-of-handoff-readiness |
| Slide 7 (portfolio + reflection) | 1:00 | Proof-of-self-awareness |
| **Total** | **10:00** | **All 4 evaluation dimensions served** |
| Q&A buffer | 10:00 | The "how do you know?" questions |

### 1.3 The 3 success criteria

1. **The panel sees the system running** (slide 2's emails get responses; slide 3's MCP server returns 200/403/429; slide 4's orchestrator returns a 3-part trace).
2. **The panel hears the trade-offs** (slide 5's corrected 77% number; slide 7's "what I'd do differently").
3. **The panel can answer the 5 questions** (slide 6's answers are short enough to memorize, concrete enough to verify).

If all 3 hold, the demo is a success. If any 1 fails, the demo is an 80% — the panel will be polite but won't be convinced.

### 1.4 The pre-demo "manifest" (the 7 things that must be true 1 minute before showtime)

| # | Manifest item | Verification command | Expected result |
|---|---|---|---|
| 1 | Phase 3 service is up | `curl http://localhost:8000/health` | `200 {"ok": true}` |
| 2 | SLM serve is up | `curl http://localhost:8001/health` | `200 {"ok": true, "model": "pf-drafter-lora", "back_end": "mock"}` |
| 3 | MCP server is up (in-process via Phase 3) | `python3 -c "from service.mcp_server import MCPServer; print(len(MCPServer().list_tools()))"` | `4` |
| 4 | Eval set is green | `python3 service/eval.py --set shared/eval_set.jsonl --report /tmp/eval.md && grep -c PASS /tmp/eval.md` | `4` (one PASS per metric) |
| 5 | Multi-agent orchestrator runs | `python3 service/agents.py --case multi_shipment` | 3-part response with `agent_path` populated |
| 6 | 3 sample emails are ready | `cat /tmp/sample_emails.md` | 3 email bodies visible |
| 7 | Dashboard tab is loaded + visible | (browser check) | 4 metrics + cost model visible |

If all 7 pass, the demo is green. If 1 fails, see §6 (backup plans).

---

## §2 Pre-demo checklist (the contract)

The 10-minute pre-demo ritual. This is mechanical, not heroic. Each step is checkable in 60 seconds.

### 2.1 The 10/5/1-minute ceremonies

| Window | Step | Time | What you verify |
|---|---|---|---|
| **T-10 min** | Servers up | 60s | `curl :8000/health`, `curl :8001/health` both 200 |
| T-10 min | Eval set green | 60s | `python3 service/eval.py` reports all 4 metrics above threshold |
| T-9 min | Dashboard loaded | 30s | Browser tab open; metrics streaming |
| T-8 min | 3 sample emails ready | 30s | `cat /tmp/sample_emails.md` shows the 3 emails |
| T-7 min | SEV-1 scenario ready | 30s | `engagement-3-postmortem.md` open in a tab |
| T-6 min | Cost model ready | 30s | `engagement-4-slm-cost.md` open in a tab, scrolled to cost model |
| **T-5 min** | Browser tabs in order | 60s | 6 tabs: Swagger, dashboard, engagement-1, mcp_policies.yaml, engagement-4, engagement-5 |
| T-5 min | 3 terminals ready | 60s | Terminal 1 = agents.py; Terminal 2 = mcp_server.py; Terminal 3 = curl fallback |
| **T-1 min** | Final smoke test | 30s | All 4 manifests from §1.4 pass |
| T-1 min | Silence the noise | 30s | Phone silent; Slack off; "Do not disturb" |
| **T-0** | Showtime | 0 | Begin slide 1 |

**Total pre-demo time: ~10 minutes.** This is not "wasted" time; it is the time you spend earning the right to the next 10 minutes of the panel's attention.

### 2.2 The 60-second recovery ritual (if any manifest fails)

If a manifest fails at T-1, do not panic. The 60-second recovery:

1. **If the service is down**: `cd service && uvicorn app:app --host 0.0.0.0 --port 8000 &`. Wait 3 seconds.
2. **If the SLM serve is down**: it falls back to the mock backend (this is the default — make sure the mock is configured). Continue.
3. **If the eval set regressed**: `git revert HEAD && docker restart pf-drafter`. Wait 5 seconds.
4. **If a browser tab is broken**: use Terminal 3's curl fallback.
5. **If you're flustered**: pause, take a breath, say "let me show you the recovery procedure" — this is itself a positive signal to the panel (they want to see how you handle failure under pressure).

---

## §3 The 7 slides (slide-by-slide, with speaker notes)

### Slide 1 (1:00) — The FDE pattern

**Goal:** orient the panel. What is an FDE? What's the pattern? Why does it generalize?

**Slide content:**

```
┌─────────────────────────────────────────────────────────────────┐
│  THE FDE PATTERN                                                │
│                                                                 │
│  I build AI services that survive the customer.                 │
│                                                                 │
│  • Eval-set-as-spec                                             │
│  • Runbook-as-contract                                          │
│  • Cost-ceiling-as-score                                        │
│  • Handoff-as-proof                                             │
│                                                                 │
│  PacificFreight (12 weeks, 12-person logistics SMB)             │
│  Acme Analytics (4 weeks, 20-person SaaS)                       │
└─────────────────────────────────────────────────────────────────┘
```

**Speaker notes (60s):**

> "I'm a Forward-Deployed Engineer. I embed with a customer, build something they use, and leave them in steady state. The pattern that emerged from my engagements is what I call *the FDE pattern*: **eval-set-as-spec, runbook-as-contract, cost-ceiling-as-score, handoff-as-proof.** Every component is an artifact the customer keeps after I leave. Today I'll show you the PacificFreight drafter — a 12-week engagement with a 12-person cross-border logistics SMB in Singapore. The customer is in steady state. The eval set is green. The cost is under the ceiling. **At the end of this demo, you'll be able to answer 5 questions about the system without me in the room.**"

**Transition (5s):** "Let me show you the system in action."

**What this slide serves in the rubric:** Dimension 3 (communication quality) — orients the panel to the framework.

**Back-out:** if the panel interrupts with a question about the FDE pattern, take 30s to answer and continue. The pattern is the rubric for the rest of the demo.

---

### Slide 2 (3:00) — The drafter live demo

**Goal:** show the drafter working. 3 emails, dashboard updating, eval set running.

**Slide content:**

```
┌─────────────────────────────────────────────────────────────────┐
│  THE DRAFTER (Live Demo)                                        │
│                                                                 │
│  Email 1: "Where's my shipment PF-1003?"          → 200 (SLM)   │
│  Email 2: "PF-1002 stuck + PF-1007 missing"       → 200 (Agents) │
│  Email 3: "Refund for PF-1003, charged twice"     → 403 (RBAC)   │
│                                                                 │
│  Dashboard: 150 drafts/day · 82% thumbs-up · P95 1.8s · $0.50/wk │
└─────────────────────────────────────────────────────────────────┘
```

**Setup (30s, included in slide budget):**
- Browser tab 1: `http://localhost:8000/docs` (FastAPI Swagger UI)
- Browser tab 2: Prometheus UI (the dashboard)
- 3 sample emails loaded in `/tmp/sample_emails.md`
- (The setup is part of the 3-minute budget — the panel is watching you execute under pressure.)

**Action 1 — Email 1 (45s):**

*What you do:* POST `/draft` with email body `"Hi, where is my shipment PF-1003? — Mei Lin"`.

*What you say:*
> "This is the routine case — single shipment, single language, no escalation. The 3-line classifier routes it to the SLM. The drafter produces: 'PF-1003 is currently held at Singapore customs pending duty payment. The estimated release date is Friday.' Mei re-reads, hits thumbs-up, sends."

*What the panel sees:*
- The LLM call returning a draft that mentions "held at Singapore customs pending duty payment"
- The cost: $0.0001 (SLM routed; 8× cheaper than the GPT-4o-mini fallback)
- The latency: P95 ~ 1.2s

*Eval-set callout (5s):*
> "If you look at the dashboard, the eval set ran at 09:00 SGT this morning. Faithfulness 0.94, answer relevance 0.91, context precision 0.90, context recall 0.93. The drafter is in steady state."

**Action 2 — Email 2 (45s):**

*What you do:* POST `/dispatch` (the multi-agent endpoint) with email body `"PF-1002 stuck in transit + PF-1007 missing. Also PF-1015 missing from yesterday's batch. Please advise."`

*What you say:*
> "This is the complex case — 3 shipments, multi-shipment context, ambiguous resolution. The classifier routes to `/dispatch`. Three agents run: Mei drafts the customer-facing reply; Sarah produces an ops-summary for the escalation; Daniel adds a cost/risk note. The orchestrator stitches them into a 3-part response."

*What the panel sees:*
- 3-part JSON response: `{"mei_draft": ..., "sarah_summary": ..., "daniel_note": ...}`
- The dispatcher trace: `[dispatcher.start, mei, sarah, daniel, dispatcher.end]` with per-agent `latency_ms`
- The cost: $0.0006 (3 agents × ~$0.0002 each)

*Per-agent breaker callout (5s):*
> "Each agent has its own circuit breaker. If Mei's LLM call fails, Sarah and Daniel still run. The orchestrator's parent breaker short-circuits only if all 3 fail."

**Action 3 — Email 3 (45s):**

*What you do:* POST `/draft` with email body `"I'd like a refund for PF-1003. Charged twice. Please refund."`

*What you say:*
> "This is the RBAC case. Mei has role `cs_junior`. The drafter detects a `refund.create` intent, calls the MCP server, which checks the YAML policy file. `cs_junior` is not authorized to call `refund.create` — only `cs_senior` is. The MCP server returns **403** with `error="role not authorized"`. The drafter falls back to a free-text draft: 'I'll escalate this to a senior colleague to process the refund.' The audit log records `tool=refund.create, status=403, role=cs_junior`."

*What the panel sees:*
- The 403 response from the MCP server
- The free-text fallback draft
- The audit log entry in `usage.jsonl`

**Action 4 — Dashboard roll-call (45s):**

*What you do:* switch to the Prometheus dashboard tab.

*What you say:*
> "Here's the dashboard. 150 drafts per day. Thumbs-up rate 82%. P95 latency 1.8 seconds. Cost $0.50/week. The eval set runs every Monday at 09:00 SGT. The cost ceiling is $5/month; the alert is at $4. **All 4 metrics are within SLO.** This is what steady state looks like at week 8 of the engagement."

*What the panel sees:*
- `pf_drafts_total` counter > 1000
- `pf_thumbs_up_rate` gauge at 0.82
- `pf_p95_latency_ms` gauge at ~1800
- `pf_weekly_cost_usd` gauge at ~$0.50

**Transition (5s):** "That's the Phase 3 drafter. Now the Phase 4 lifts — let me show you the MCP server in action."

**What this slide serves in the rubric:** Dimensions 1 (system correctness) + 2 (operational discipline).

**Back-out:** if a request fails, narrate the failure mode: "this is what a circuit-breaker-open looks like — the drafter falls back to the static reply in < 50ms." Turn the failure into a teaching moment.

---

### Slide 3 (2:00) — The MCP server live demo

**Goal:** show the MCP server in action. 4 tools, RBAC, rate limit, budget.

**Slide content:**

```
┌─────────────────────────────────────────────────────────────────┐
│  THE MCP SERVER (Live Demo)                                     │
│                                                                 │
│  4 tools · 5 roles · 1 YAML · 12 test cases                     │
│                                                                 │
│  $ tracker.lookup PF-1003 → 200 (1 credit)                       │
│  $ refund.create PF-1003 ... → 403 (role: cs_junior)            │
│  $ translate.to "vietnamese" → 200 (5 credits)                  │
│  $ refund.create (burst 6x) → 429 (rate-limited)                │
└─────────────────────────────────────────────────────────────────┘
```

**Setup (15s, included in slide budget):**
- Terminal 1: `cd projects/01-mcp-drafter && python3 service/mcp_server.py` ready (or import the class in a Python REPL)

**Action 1 — RBAC walkthrough (45s):**

*What you do:* import the `MCPServer` class and call `call_tool` for each of the 4 examples.

```python
from service.mcp_server import MCPServer
mcp = MCPServer()

# 1. Mei (cs_junior) calls tracker.lookup
print(mcp.call_tool("tracker.lookup", {"shipment_id": "PF-1003"}, user_role="cs_junior"))
# → 200, cost=1 credit, shipment details

# 2. Mei (cs_junior) calls refund.create
print(mcp.call_tool("refund.create", {"shipment_id": "PF-1003", "reason": "double charge", "amount_usd": 50.0}, user_role="cs_junior"))
# → 403, error="role 'cs_junior' not authorized to call 'refund.create'"

# 3. Alice (cs_senior) calls refund.create
print(mcp.call_tool("refund.create", {"shipment_id": "PF-1003", "reason": "double charge", "amount_usd": 50.0}, user_role="cs_senior"))
# → 200, ticket=REF-2026-W42-0123, cost=10 credits
```

*What you say:*
> "Four tools, five roles, one YAML policy file. Mei (cs_junior) can call `tracker.lookup` and `translate.to` and `escalate.to_human`, but not `refund.create`. Alice (cs_senior) can call all four. The YAML is the contract — adding a new tool is 30 lines of code + 1 paragraph in the YAML. The drafter doesn't change."

**Action 2 — Rate limit walkthrough (30s):**

*What you do:* burst 6 `refund.create` calls as Alice in a loop.

```python
for i in range(6):
    result = mcp.call_tool("refund.create", {"shipment_id": "PF-1003", "reason": "test", "amount_usd": 1.0}, user_role="cs_senior")
    print(f"call {i}: {result.status_code} {result.body}")
# → call 0: 200, call 1: 200, ..., call 4: 200, call 5: 429
```

*What you say:*
> "The rate limit is `5 per user per minute` for `refund.create`. The 6th call returns 429. The policy also encodes a 60-credit-per-minute budget per user — `refund.create` costs 10 credits, so the budget is exhausted by 6 calls. This is the rate-limit-on-tools pattern: tools have a token-equivalent cost, and the budget is the operational boundary."

**Action 3 — YAML edit (30s):**

*What you do:* open `mcp_policies.yaml` in an editor tab. Add a 5th tool:

```yaml
  - name: label.print
    description: Print a shipping label
    input_schema:
      shipment_id: PF-XXXX
      format: pdf|zpl
    cost_credits: 8
```

*What you say:*
> "Adding a 5th tool is a 5-line YAML change. No Python change. The drafter picks it up automatically because the policy loader hot-reloads. **This is the YAML-as-contract pattern.** A 1-line addition is a 1-line PR. A database-backed policy would lose the audit trail."

**Transition (5s):** "That's the MCP lift. Now let me show you the multi-agent orchestrator trace."

**What this slide serves in the rubric:** Dimension 1 (system correctness) for the extension work.

**Back-out:** if the MCP server import fails, fall back to showing the YAML policy file in the editor and walking through the 5 role × 4 tool cell matrix by hand.

---

### Slide 4 (1:00) — The multi-agent orchestrator trace

**Goal:** show the orchestrator routing a multi-shipment case to 3 sub-agents.

**Slide content:**

```
┌─────────────────────────────────────────────────────────────────┐
│  THE MULTI-AGENT ORCHESTRATOR (Live Trace)                      │
│                                                                 │
│  Input:  3 shipments, ambiguous resolution, multi-language      │
│  Output: {mei_draft, sarah_summary, daniel_note}                │
│  Trace:  dispatcher.start → mei → sarah → daniel → dispatcher.end
│                                                                 │
│  Cost:   $0.0006 (3 agents × $0.0002)                           │
│  Latency: P95 4.2s end-to-end                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Setup (already done at T-5 min):** Terminal 2 with `cd projects/02-multi-agent-dispatcher && python3 service/agents.py --case multi_shipment` ready.

**Action 1 — Run the orchestrator (30s):**

*What you do:* run `python3 service/agents.py --case multi_shipment`.

*What you say:*
> "Three sub-agents, one shared state object, one orchestrator. The case has 3 shipments, an ambiguous resolution request, and a Vietnamese-language clause. The orchestrator runs **Mei** first (always — Mei is the customer-facing voice), **Sarah** second (only if multi-shipment, which this is), and **Daniel** third (always — Daniel adds the cost + risk + audit trail). The state object is passed between agents; each agent reads from it, writes to it, and never calls the others directly. **The state is the contract, not the agent interfaces.**"

**Action 2 — Show the trace (30s):**

*What you do:* open `usage.jsonl` (or the agent trace log) and grep for `agent_path`.

```bash
tail -1 usage.jsonl | python3 -c "import json, sys; d=json.loads(sys.stdin.read()); print(json.dumps(d['agent_path'], indent=2))"
```

Expected output:
```json
[
  {"event": "dispatcher.start", "ts": "2026-W42-T14:23:01", "n_shipments": 3, "user_id": "alice@pf.com", "role": "cs_senior"},
  {"event": "mei",              "ts": "2026-W42-T14:23:02", "ok": true, "latency_ms": 1240},
  {"event": "sarah",            "ts": "2026-W42-T14:23:03", "ok": true, "latency_ms": 890},
  {"event": "daniel",           "ts": "2026-W42-T14:23:04", "ok": true, "latency_ms": 780},
  {"event": "dispatcher.end",   "ts": "2026-W42-T14:23:04", "n_tool_calls": 6, "cost_usd": 0.0006}
]
```

*What you say:*
> "Here's the trace. Mei ran in 1.24s, Sarah in 0.89s, Daniel in 0.78s. Total: 4.2s end-to-end (P95). Cost: $0.0006. Six tool calls were made (Mei's draft triggered 2 MCP lookups, Sarah's summary triggered 3, Daniel's note triggered 1). The orchestrator's parent circuit breaker is closed; each sub-agent's breaker is also closed. **If Mei had failed, Sarah and Daniel would have still run with a `[mei_unavailable]` flag in the state.** This is the per-agent breaker pattern."

**Transition (5s):** "That's the multi-agent lift. Now the SLM cost model."

**What this slide serves in the rubric:** Dimension 2 (operational discipline) — shows the per-agent breaker pattern + the audit trail.

**Back-out:** if the trace log is too deep, just show the 3-part JSON response body and skip the per-event trace.

---

### Slide 5 (1:00) — The SLM cost model

**Goal:** show the cost reduction. 64% bill reduction at current volume; 61% at 10× growth. The corrected 77% quality ratio.

**Slide content:**

```
┌─────────────────────────────────────────────────────────────────┐
│  THE SLM COST MODEL                                             │
│                                                                 │
│  Volume    GPT-4o-mini only   SLM + fallback (80/20)   Savings  │
│  ─────────────────────────────────────────────────────────────  │
│  150/d     $2.27/mo            $0.82/mo                64%      │
│  750/d     $10.50/mo           $4.09/mo                61%      │
│                                                                 │
│  Quality ratio (volume-weighted): 77% of GPT-4o-mini            │
│  Model card corrected: 91% → 77% (re-derived from fresh data)   │
└─────────────────────────────────────────────────────────────────┘
```

**Setup:** Browser tab on `engagement-4-slm-cost.md`, scrolled to §1 (cost model) + §2 (quality model).

**Action 1 — Show the SLM serve (30s):**

*What you do:* `curl http://localhost:8001/health`.

```bash
curl http://localhost:8001/health
# → {"ok": true, "model": "pf-drafter-lora", "back_end": "mock"}
```

*What you say:*
> "The SLM serve is running on port 8001. The model is `pf-drafter-lora` (Qwen2.5-1.5B + LoRA, 50MB adapter). The back end is `mock` — we run the real ollama back end in production, but for this demo the mock serves the same prompt-response shape. A `/draft` call here costs $0.0001 (8× cheaper than GPT-4o-mini)."

**Action 2 — Show the cost model (30s):**

*What you do:* point at the table in `engagement-4-slm-cost.md`.

*What you say:*
> "Here's the cost model. At current volume (150 drafts/day), GPT-4o-mini alone is $2.27/month; SLM + 20% GPT-4o-mini fallback is $0.82/month — a 64% reduction. At 10× growth (750 drafts/day, 5 customer teams), the bill is $4.09/month — still under the $5/month ceiling. **The cost ceiling is the spec, not the savings target.** The CFO approved this for the strategic optionality, not the $26/year direct savings. The model card now reports a **77% volume-weighted quality ratio** — that's the corrected number. The first version published 91%, but that was a single-metric ratio on a stale baseline. We re-derived from fresh data. **Model cards are public artifacts; numbers must be re-derived, not carried over.**"

**Transition (5s):** "That's the SLM lift. Now the handoff — the proof that the customer can run without me."

**What this slide serves in the rubric:** Dimension 2 (operational discipline) — shows the cost model + the corrected quality ratio.

**Back-out:** if `engagement-4-slm-cost.md` isn't loaded, just say "the math is in the case study folder; here are the headline numbers" and read the table.

---

### Slide 6 (1:00) — The 5-question "FDE has left" test

**Goal:** prove the customer can run the system without me.

**Slide content:**

```
┌─────────────────────────────────────────────────────────────────┐
│  THE 5-QUESTION "FDE HAS LEFT" TEST (the rubric)                │
│                                                                 │
│  1. What does the drafter do?                                   │
│  2. How do you know it's working?                               │
│  3. What breaks first when it goes wrong?                       │
│  4. How do you fix it?                                          │
│  5. What's the cost ceiling, and how do you know when you hit?  │
│                                                                 │
│  Daniel: 5/5 · Mei: 4/5 (Q5 deferred) · Sarah: 4/5 (Q5 deferred) │
│  Verified at 30 days, 60 days, 90 days. The FDE has left.       │
└─────────────────────────────────────────────────────────────────┘
```

**Setup:** Browser tab on `engagement-5-handoff.md`, scrolled to §1 (the 5-question rubric).

**Action 1 — Read the 5 questions (30s):**

*What you say:*
> "The handoff is the engagement. The 5-question test is the rubric. Each stakeholder — the IT owner Daniel, the CS lead Mei, the ops lead Sarah — answers all 5 questions independently, 30 days after my last commit. A 'yes' on all 5 from all 3 is a clean handoff. **Q5 is the cost question; that's the lane-aware test.** Mei doesn't need to know the exact ceiling number; Daniel does. **Lane awareness, not full-stack knowledge, is the test.**"

**Action 2 — Show the 30/60/90-day results (30s):**

*What you say:*
> "At 30 days, Daniel answered 5/5; Mei and Sarah answered 4/5 (Q5 deferred to Daniel). At 60 days, the same. At 90 days, the same. One SEV-1 candidate at week 11, caught in 38 minutes — that's case study #3. One SEV-2 at week 14, Mei-side copy-paste error, not the drafter's fault. The eval set has caught 3 regressions in 90 days — a typo, a chunked-policy bug, an RRF hyperparameter drift. **The CI gate paid for itself in < 4 weeks.** The bill stayed at $0.48-$0.55/wk. Thumbs-up stayed at 81-82%. **The FDE has left. The engagement is done.**"

**Transition (5s):** "That's the proof. Now the bigger picture — the portfolio, the case studies, and what I'd do differently."

**What this slide serves in the rubric:** Dimension 4 (handoff readiness) — the strongest moment in the demo.

**Back-out:** if the panel asks "but Mei didn't answer Q5 — isn't that a fail?", answer: "no — Q5 is the IT owner's lane; Mei deferring is the correct behavior, not a knowledge gap. The test checks lane awareness, not full-stack knowledge. Mei knows the cost is Daniel's lane; that's a 5/5 on the *lane-awareness* rubric."

---

### Slide 7 (1:00) — Portfolio + case studies + what I'd do differently

**Goal:** tie it all together. The pattern, the projects, the lessons, the self-awareness.

**Slide content:**

```
┌─────────────────────────────────────────────────────────────────┐
│  PORTFOLIO + WHAT I'D DO DIFFERENTLY                            │
│                                                                 │
│  4 projects · 5 case studies · 3 lessons · 25 tests            │
│  PORTFOLIO-NARRATIVE.md · CAPSTONE-PRESENTATION.md              │
│                                                                 │
│  What I'd do differently in week 1:                             │
│  1. Start with the eval set (not the prompt)                    │
│  2. Start the runbook (before the first SEV-1)                  │
│  3. Start with the CS lead (not the IT owner)                   │
└─────────────────────────────────────────────────────────────────┘
```

**Action 1 — The portfolio (30s):**

*What you say:*
> "The 4 projects (MCP drafter, multi-agent dispatcher, distilled SLM, AI data analyst) are the proof. The 5 case studies are the lessons. The 3 lessons are the technical depth. The 25 tests are the contract. The portfolio narrative is the 1-page, 3-page, and 60-page version of 'what I do, why I do it, and what I've built.' The capstone presentation is this script. The rehearsal checklist is the 10-minute pre-demo. **The handoff is the proof I can leave.**"

**Action 2 — What I'd do differently (30s):**

*What you say:*
> "Three things I'd do differently in week 1. **First**: start with the eval set, not the prompt. I wasted 2 days writing prompts before I had an eval set — the eval set is what tells you the prompt is good. **Second**: start the runbook on day 1, not after the first SEV-1. The first SEV-1 took 90 minutes to recover from; the runbook would have saved 60 of those. **Third**: start with the CS lead as the primary user, not the IT owner. Mei's feedback is the source of truth for quality. Daniel's feedback is the source of truth for ops. Both matter, but Mei is the one who knows what a good draft looks like. **The CS lead is the first user; the IT owner is the second.**"

**Closing (10s):**

> "The FDE pattern is *eval-set-as-spec, runbook-as-contract, cost-ceiling-as-score, handoff-as-proof.* The handoff is the proof. **Thank you.**"

**What this slide serves in the rubric:** Dimension 3 (communication quality) — shows self-awareness + the meta-narrative.

**Back-out:** if running short, drop the 3 bullet points and just say "my week-1 advice: eval set on day 1, runbook on day 1, CS lead as the first user."

---

## §4 Q&A prep (10 questions, 10 worked answers)

The 10 questions the panel is most likely to ask. Each has a 30-60s answer + the artifact to point to.

| # | Question | Worked answer (the bullets I'll deliver) | Artifact to point to |
|---|---|---|---|
| 1 | **"Why YAML, not a database, for the MCP policy file?"** | Code-reviewable, version-controlled, diffable. A database change is invisible to the next person who reads the repo. A 1-line YAML addition is a 1-line PR; the next FDE sees it in `git blame`. **The policy file is a contract, not a config.** | `mcp_policies.yaml` |
| 2 | **"Why LoRA, not full fine-tune?"** | LoRA fits on a Mac M-series in 30 minutes; produces a 50MB adapter; matches full fine-tune quality on a 1k-row dataset. Full fine-tune needs a GPU cluster. The 91% quality ratio was wrong (it's 77%); the corrected number is in the model card with full derivation. **Distill when the cost ceiling is at risk, not before.** | `engagement-4-slm-cost.md` |
| 3 | **"What's the worst-case failure mode?"** | LLM emits a hallucinated draft. Mei reverts it (MTTD 2 min). Daniel rolls back (MTTR 38 min). The eval set catches the regression class on next Monday. **The recovery time is the operationally-meaningful SLO; the failure is inevitable.** | `engagement-3-postmortem.md` |
| 4 | **"How do you know the SLM is safe to ship?"** | The eval set runs against the SLM. If it scores > 90% of GPT-4o-mini on a volume-weighted aggregate, it goes to shadow mode for 1 week; if the live A/B holds, it ships. The 12-day A/B gave ±5pp CI; the 9-day over-engineering cost $2,250. **Size the A/B to the precision needed, not the precision possible.** | `engagement-4-slm-cost.md` |
| 5 | **"Why 3 sub-agents, not 1 monolithic LLM call?"** | Each sub-agent has a different lane (CS / ops / infra), a different circuit breaker, and a different observability story. A Mei failure doesn't block Sarah or Daniel. **The shared state object is the contract; adding a 4th agent is a new field on the state, not a change to the orchestrator.** | `projects/02-multi-agent-dispatcher/` |
| 6 | **"What's the next phase?"** | Phase 5: production scale. Redis instead of in-process dicts. Real OAuth for the MCP server. Real ollama deployment with the merged adapter. gVisor/Firecracker sandbox for untrusted users. **The drafter doesn't change.** | `PORTFOLIO-NARRATIVE.md` §8 |
| 7 | **"How do you handle non-determinism?"** | Temperature=0 in production. Eval set runs at every deploy. The eval set is the spec, not the prompt. **The model is a black box that passes or fails the spec.** | `service/eval.py` |
| 8 | **"What's the most important PE habit?"** | Mei re-reads every draft before sending. The eval set catches regressions in batch; the breaker catches liveness failures; the re-read catches anything the eval set didn't anticipate. P95 cost: 0.3s × 150 drafts/day = 45s/day of Mei's time. **Worth it.** | `engagement-3-postmortem.md` §4.1 |
| 9 | **"How do you keep the cost ceiling honest?"** | Prometheus alert at 80% of ceiling (alert at $4/wk for the $5/mo cap). Weekly cost review in the Monday cadence. The alert page goes to the IT owner, not the FDE. **The FDE is consulted, not responsible, after the handoff.** | `cost_model.md` (PF) |
| 10 | **"What would you do if a customer refused to run the Monday cadence?"** | I would not take the engagement. The cadence is the iteration mechanism. No cadence = no eval set in CI = no regression detection = SEV-1s I can't prevent. **The cadence is the contract; the cadence is the iteration; the cadence is the handoff.** | `engagement-1-pf-drafter.md` |

### 4.1 The "I don't know" answer

If a question catches me off-guard, my standard answer:

> "I don't have a confident answer to that one — I'd want to investigate before answering. The pattern I'd apply is: check the runbook first, then the eval set, then the cost model, then ask the customer. I'd come back to you within 24 hours with an artifact-backed answer. **Honesty > smooth talking.**"

This is itself a signal of principal-engineer discipline.

---

## §5 Evaluation rubric mapping (4 dimensions, 8 cells)

The 4 grading dimensions × the 2 strongest cells each dimension, with the slide that serves each cell:

| Dimension | Weight | Cell 1 (strongest) | Cell 2 (second) |
|---|---|---|---|
| **1. System correctness** (does it run?) | 30% | Slide 2: 3 emails get responses | Slide 3: 4 tool calls return correct RBAC + rate-limit response |
| **2. Operational discipline** (eval set, runbook, cost model, on-call?) | 30% | Slide 2 Action 4: dashboard shows the 4 SLIs | Slide 6: the 5-question test |
| **3. Communication quality** (narrate trade-offs + "what I'd do differently"?) | 20% | Slide 1: the FDE pattern thesis | Slide 7 Action 2: the 3 what-I'd-do-differently items |
| **4. Handoff readiness** (can the panel answer the 5 questions?) | 20% | Slide 6: the 30/60/90-day check-ins | Slide 5: the corrected model card |

### 5.1 The "if I had to drop 2 slides" triage

If I'm running short on time, the 2 slides I drop first:
1. **Slide 4** (multi-agent trace) — strongest content is in the case study folder; can be referenced briefly.
2. **Slide 5** action 1 (SLM serve health check) — can be replaced with a single sentence ("the SLM serve is on port 8001, costing $0.0001/draft").

The 2 slides I never drop:
1. **Slide 2** (live demo) — without this, the demo has no proof-of-system-correctness.
2. **Slide 6** (5-question test) — without this, the demo has no proof-of-handoff-readiness.

---

## §6 Backup plans (the 5 things that go wrong)

The 5 failure modes I prepare for. Each has a back-out plan + a teaching moment.

| # | Failure | Detection | Back-out plan | Teaching moment |
|---|---|---|---|---|
| 1 | **The Swagger UI freezes** (typical Mac Safari issue) | The POST hangs > 5s | Terminal 3's curl command | "The Swagger UI is a convenience; the API is the contract." |
| 2 | **The dashboard is slow** (Prometheus query takes > 5s) | The dashboard tab takes > 5s to load | Have screenshots in `/tmp/dashboard-*.png` pre-loaded | "Observability is a feature; if it doesn't render, you ship without it." |
| 3 | **The eval set regresses during the demo** (prob ~ 5%) | A metric drops below the threshold | `git revert HEAD && docker restart pf-drafter` (~30s) | "Recovery is the operationally-meaningful SLO; here's the recovery." |
| 4 | **A tool call returns a 5xx** (MCP server bug) | The MCP response is 500 | Fall back to free-text draft | "This is why the drafter has a fallback — the LLM is the contract, the tools are a productivity multiplier." |
| 5 | **I forget a talking point** (always happens once) | I freeze for > 2s | Take a sip of water, refer to the script | "I'm a system, not a performance; the script is the contract." |

### 6.1 The "demo disaster" recovery (the 60-second ritual)

If something blows up that isn't in §6 above:

1. Pause. Take a breath. Look at the panel.
2. Say: "Let me show you the recovery procedure."
3. Run the rollback or fallback. (This is in the runbook, which is open in a browser tab.)
4. Show the eval set going green again.
5. Say: "The operationally-meaningful SLO is recovery time, not failure-free operation. That took ~60 seconds; under the 60-min MTTR SLO."

**This turns a disaster into the strongest moment of the demo.** A panel that sees a graceful recovery is more convinced than a panel that sees a flawless run. The flawless run is suspicious; the graceful recovery is real.

---

## §7 The "demo is a system" framing

A junior FDE treats a demo as a performance. A principal FDE treats it as a **system** with:

- **Inputs** (the demo environment, the eval set, the sample emails, the SEV-1 scenario).
- **Outputs** (the panel's score on the 4 rubric dimensions).
- **SLOs** (10 minutes total; 3 minutes on the live demo; 0 SEV-1s in the demo).
- **Observability** (the dashboard, the eval set, the audit log).
- **Failure modes** (§6 above).
- **Recovery procedures** (the 60-second disaster ritual).

If any of these are missing, the demo is at risk. **Treating the demo as a system is the difference between a junior FDE's nervous flight and a principal FDE's controlled descent.**

### 7.1 The rubric for the rubric (the meta-evaluation)

After the demo, ask yourself:

- Did the panel hear the **thesis**? (Slide 1 — eval-set-as-spec, etc.)
- Did the panel see the **system**? (Slide 2 — 3 emails get responses.)
- Did the panel see the **extensions**? (Slides 3-4 — MCP + multi-agent.)
- Did the panel see the **cost discipline**? (Slide 5 — 77% number, corrected model card.)
- Did the panel see the **handoff**? (Slide 6 — 5-question test.)
- Did the panel see the **self-awareness**? (Slide 7 — 3 what-I'd-do-differently items.)
- Did the panel hear the **Q&A answers**? (§4 — 10 questions.)
- Did the panel hear the **honest limits**? (§7 of `PORTFOLIO-NARRATIVE.md` — what this does NOT demonstrate.)

If 7 of 8 are yes, the demo is an A. If 5 of 8 are yes, the demo is a B. If 3 of 8 are yes, the demo is a C — the panel was polite but not convinced.

### 7.2 The "demo debrief" ritual (post-demo)

Within 1 hour of the demo, write a 1-paragraph note to yourself:

```
What worked: ...
What didn't: ...
What surprised me: ...
What I'd do differently next time: ...
```

This is itself the FDE pattern applied to the FDE's own work. **The eval set is the spec; the runbook is the contract; the cost ceiling is the score; the handoff is the proof.** The demo debrief is the eval set for next time.

---

## §8 References

### 8.1 The artifacts this script references

| Artifact | Where | Why it's in the script |
|---|---|---|
| The drafter service | `phase-3-deployment/service/app.py` | Live demo target |
| The eval set | `phase-2-core-build/shared/eval_set.jsonl` | Dashboard + regression detector |
| The MCP server | `phase-4-capstone/projects/01-mcp-drafter/service/mcp_server.py` | Live RBAC + rate-limit demo |
| The policy file | `phase-4-capstone/projects/01-mcp-drafter/service/mcp_policies.yaml` | The contract |
| The multi-agent orchestrator | `phase-4-capstone/projects/02-multi-agent-dispatcher/service/agents.py` | The trace demo |
| The SLM serve | `phase-4-capstone/projects/03-distilled-slm/slm/serve.py` | The cost demo |
| The model card | `phase-4-capstone/projects/03-distilled-slm/slm/model_card.md` | The corrected 77% number |
| The 5-question test | `phase-4-capstone/case-studies/engagement-5-handoff.md` | The handoff rubric |
| The postmortem | `phase-4-capstone/case-studies/engagement-3-postmortem.md` | The SEV-1 scenario |
| The SLM cost model | `phase-4-capstone/case-studies/engagement-4-slm-cost.md` | The cost model |
| The portfolio narrative | `phase-4-capstone/case-studies/PORTFOLIO-NARRATIVE.md` | The self-narrative |
| The rehearsal checklist | `phase-4-capstone/case-studies/REHEARSAL-CHECKLIST.md` | The 10-minute pre-demo |

### 8.2 The 5-case-study bibliography

| Case study | Slide it informs | What it teaches |
|---|---|---|
| [`engagement-1-pf-drafter.md`](./engagement-1-pf-drafter.md) | Slides 1, 2 | The flagship 12-week narrative |
| [`engagement-2-pivot.md`](./engagement-2-pivot.md) | Slide 7 (Q&A) | The data-readiness scorecard; when to walk away |
| [`engagement-3-postmortem.md`](./engagement-3-postmortem.md) | Slide 6 (Q&A), §6 back-out | The week-11 hallucination; the 38-min MTTR; the eval-CI fix |
| [`engagement-4-slm-cost.md`](./engagement-4-slm-cost.md) | Slide 5 | The SLM cost model; the corrected 77% number |
| [`engagement-5-handoff.md`](./engagement-5-handoff.md) | Slide 6 | The 5-question "FDE has left" test |

### 8.3 The pedagogical precedent

This script is modeled on the **SREcon presentation tradition** (Krishnan 2014 postmortem; Allspaw 2008 root-cause; Kripa 2014 blameless) adapted for FDE engagement demos. The "demo is a system" framing is from **Google SRE Book ch. 27**; the 60-second disaster recovery ritual is from **Atlassian's major-incident management playbook**.

---

## Closing

**Total: 10 minutes for the demo + 10 minutes for Q&A = 20 minutes.** This is the principal FDE's contribution to the panel's understanding of the FDE pattern.

**The FDE pattern is eval-set-as-spec, runbook-as-contract, cost-ceiling-as-score, handoff-as-proof.** The demo is the spec; the runbook is the contract; the cost model is the score; the 5-question test is the proof. **The demo's job is to make all 4 visible in 10 minutes.**

A principal FDE's job is to make themselves unnecessary. **This script is the rubric that grades whether the FDE has done so.**
