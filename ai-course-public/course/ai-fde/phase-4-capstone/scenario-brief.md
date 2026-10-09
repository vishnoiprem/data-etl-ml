# Phase 4 scenario brief — the 4-engagement narrative

> **Continues from Phase 1-2-3.** The PacificFreight drafter is a 5-month-old production system. Mei sends 150 emails/day. The thumbs-up rate is 82%. The FDE is preparing to exit. This is what the customer asks for next.

---

## Where Phase 3 left us

| | End of Phase 3 |
|---|---|
| **Customer** | PacificFreight Co. — 12-person cross-border logistics SMB, Singapore ↔ Vietnam |
| **Operator** | Mei (CS lead) — 150 emails/day |
| **Reviewer** | Sarah (ops manager) — weekly iteration report |
| **Owner** | Daniel (IT) — VM, model, cost, security |
| **Service** | 10 endpoints, hybrid retrieval, circuit breaker, rate limiter, redactor |
| **Eval** | 30-row frozen eval set, RAGAS 4 metrics, CI regression check |
| **Cadence** | Monday iteration report → Friday ship (one experiment/week) |
| **Handoff** | Runbook + RACI + on-call rotation, 5-question "FDE has left" test |

The 5 Phase 2 dangling commitments are closed. 13/13 pytest tests pass. The system is in production.

---

## What the customer asks for in Phase 4

Three new asks from Mei + Daniel, and one new customer for breadth.

### Ask 1 (Mei): "I want the drafter to do more than draft."

> "When a customer says 'I want a refund,' the drafter just writes a reply telling them to email refunds@pacificfreight.com. Can it actually create the refund ticket? And when a customer writes in Vietnamese, can it draft in Vietnamese without me copy-pasting into Google Translate?"

The MCP lift: the drafter gains 4 callable tools (`tracker.lookup`, `refund.create`, `translate.to`, `escalate.to_human`), each gated by a **policy file** that says which CS user can call what. A `cs_mei` user can call `translate.to` and `escalate.to_human` but NOT `refund.create` — only `cs_senior` can. The drafter becomes a tool-using agent. The cost ceiling now applies to tool calls too.

→ **Project 1: MCP-tooled drafter** (`projects/01-mcp-drafter/`)

### Ask 2 (Mei): "Multi-shipment cases take me 5 clicks."

> "When a customer asks 'what's the status of my 3 shipments?', I have to look up each one, copy the status, paste it into a reply, then check whether the total value triggers an insurance clause. Can the drafter do this end-to-end?"

The multi-agent lift: a LangGraph ReAct orchestrator with 3 sub-agents — `MeiAgent` (CS-drafter), `SarahAgent` (ops-summary), `DanielAgent` (cost + circuit visibility). The orchestrator routes a multi-shipment case to the right sub-agent(s) and stitches their outputs. Each agent has its own circuit breaker; a Mei failure doesn't block Daniel.

→ **Project 2: Multi-agent dispatcher** (`projects/02-multi-agent-dispatcher/`)

### Ask 3 (Daniel): "The bill is going to grow."

> "We're at $0.50/week now. If we onboard 5 more customers, the bill is $5/week = $20/month. That's over my $5/month ceiling. Can we use a smaller model?"

The SLM lift: a LoRA fine-tune of Qwen2.5-1.5B-Instruct on Mei's 4-week usage.jsonl. The adapter is 50MB. The training takes 30 minutes on a Mac M-series (MPS). The serving uses ollama. The eval set is the spec; the success criterion is ≥ 90% of GPT-4o-mini's quality at < 10% of the cost. **The model card is the artifact that survives.**

→ **Project 3: Distilled SLM** (`projects/03-distilled-slm/`)

### Ask 4 (new customer): "We're a 20-person SaaS. We need a data analyst."

> "We want to ask 'what were last quarter's signups by region?' in plain English and get a chart back. The LLM writes pandas code; we run it on a copy of our Postgres."

The fresh engagement: Acme Analytics (placeholder name; the learner substitutes their own). The LLM generates pandas code; a subprocess sandbox runs it with a 5-second timeout + 256MB memory cap + no network; a regex blocklist rejects `os.system`, `subprocess`, `__import__`, `eval`, `exec`. The security boundary is the lesson.

→ **Project 4: AI Data Analyst** (`projects/04-ai-data-analyst/`)

---

## The 4-engagement story (for the portfolio narrative)

The FDE's narrative is:

> "I built one production AI service for PacificFreight over 4 phases (Engagement 1, 4 projects). Along the way I learned when to say no (Engagement 2 — a healthcare engagement I declined because their data wasn't RAG-ready), how to write a public postmortem (Engagement 3 — the SEV-1 from Phase 3), how to distill a model when the cost ceiling is the constraint (Engagement 4 — the SLM), and how to hand off a running system to a team that doesn't include me (Engagement 5 — the C3 'FDE has left' test)."

The 4 projects are the **proof**. The 5 case studies are the **lessons**. The portfolio narrative is the **story**.

---

## Week-by-week plan (Phase 4 is ~4 weeks of study)

| Week | Focus | Output |
|---|---|---|
| **Week 1** | Project 1 (MCP) | `mcp_server.py` + 4 tests + `ARCHITECTURE.md` |
| **Week 2** | Project 2 (multi-agent) | `agents.py` + 3 tests + `README.md` |
| **Week 3** | Project 3 (SLM) | `train.py` + `serve.py` + `eval.py` + `model_card.md` + 2 tests |
| **Week 4** | Project 4 (data analyst) + 5 case studies + portfolio | `sandbox.py` + 3 tests + `ARCHITECTURE.md` + 5 case studies + `PORTFOLIO-NARRATIVE.md` + `CAPSTONE-PRESENTATION.md` + `REHEARSAL-CHECKLIST.md` |

Week 4 is the heaviest — the synthesis week. The FDE presents the capstone on Friday.

---

## What the evaluation panel sees

The panel is 3 instructors + 2 peer FDEs. The FDE presents for 10 minutes:

1. **Slide 1** — the FDE pattern (1 min)
2. **Slide 2** — the PacificFreight drafter live demo (3 min)
3. **Slide 3** — the MCP server live demo (2 min)
4. **Slide 4** — the multi-agent trace (1 min)
5. **Slide 5** — the SLM cost model (1 min)
6. **Slide 6** — the 5-question "FDE has left" test (1 min)
7. **Slide 7** — the portfolio + 5 case studies + what I'd do differently (1 min)

Then 5 minutes of Q&A. The panel asks: "When did you say no?" (Engagement 2), "Show me the SEV-1" (Engagement 3), "Why this SLM?" (Engagement 4), "What does Mei do when you're gone?" (Engagement 5).

The artifact that gets the FDE hired is the 1-page version of `PORTFOLIO-NARRATIVE.md`. The artifact that gets the FDE the next engagement is the running system + the 4 projects.
