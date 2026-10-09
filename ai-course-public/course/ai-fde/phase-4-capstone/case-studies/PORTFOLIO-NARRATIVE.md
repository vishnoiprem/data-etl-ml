# Portfolio narrative

> **TL;DR.** I build AI services that survive the customer. Across
> 12 weeks with PacificFreight and a parallel 4-week engagement
> with Acme Analytics, I shipped 4 projects (MCP, multi-agent,
> SLM, data analyst), 5 case studies, a 13/13 test suite that
> hasn't regressed in 8 weeks, and a runbook the customer can
> follow without me. **The lesson that ties them together:**
> the FDE pattern is *eval-set-as-spec, runbook-as-contract,
> cost-ceiling-as-score.*

---

## The FDE pattern

I work as a Forward-Deployed Engineer. My job is to embed with a
customer, build something they use, and leave them in steady state.

The pattern that emerged from my engagements:

1. **Start with the eval set, not the prompt.** The eval set is
   the spec; everything else follows.
2. **Ship the simplest thing that passes the eval set.** No
   gold-plating. No premature optimization.
3. **Add the operational boundaries around it.** Rate limit,
   circuit breaker, redaction, audit log. These are the things
   that survive the customer's first SEV-1.
4. **Let the iteration cadence carry the project forward.** The
   cadence runs every week; the eval set catches regressions;
   the customer knows what to do when it goes red.
5. **Write the runbook before the first SEV-1.** The runbook is
   the contract. The 5-question "FDE has left" test is the rubric.
6. **Leave the customer in steady state.** The cost is under
   the ceiling. The eval set is green. The on-call rotation is
   staffed. The runbook is up to date.

That's the FDE pattern. The 4 projects + 5 case studies are the
proof.

## The 4 projects (the proof)

### Project 1 — MCP-tooled PacificFreight drafter

**What it is:** 4 MCP-callable tools (tracker, refund, translate,
escalate) gated by a YAML policy file. The drafter goes from
"single-purpose LLM call" to "tool-using agent."

**What it proves:** the policy file is the contract. A new role
is a 1-line addition to the YAML. A new tool is 30 lines of code
+ 1 paragraph in the YAML. The drafter doesn't change.

**The artifact:** [`projects/01-mcp-drafter/`](../projects/01-mcp-drafter/) —
the MCP server (`mcp_server.py`), the policy file
(`mcp_policies.yaml`), the 4 tests (`test_mcp.py`), the
design doc (`ARCHITECTURE.md`).

### Project 2 — Multi-agent PacificFreight dispatcher

**What it is:** 3 sub-agents (Mei, Sarah, Daniel) that share a
single state object and route multi-shipment cases end-to-end.
Each agent has its own circuit breaker; the orchestrator's
breaker is the parent.

**What it proves:** the shared state object is the contract.
A new agent is a new field on the state and a new node in the
graph. The orchestrator doesn't change.

**The artifact:** [`projects/02-multi-agent-dispatcher/`](../projects/02-multi-agent-dispatcher/) —
the agents (`agents.py`), the shared state (`agents_state.py`),
the 3 tests (`test_agents.py`).

### Project 3 — Distilled SLM (Qwen2.5-1.5B)

**What it is:** a LoRA-fine-tuned 1.5B model that drafts customer
replies at 5% of GPT-4o-mini's cost. The drafter's frontend
doesn't change — the SLM is a new option in the model dropdown.

**What it proves:** the cost ceiling is the spec. A model that's
62% of the larger model's quality at 5% of the cost is the right
tradeoff for an SMB. The eval set is the test.

**The artifact:** [`projects/03-distilled-slm/`](../projects/03-distilled-slm/) —
the dataset prep (`dataset.py`), the LoRA fine-tune (`train.py`),
the serve (`serve.py`), the eval (`eval.py`), the model card
(`model_card.md`), the 2 tests (`test_slm.py`).

### Project 4 — AI Data Analyst (sandboxed code execution)

**What it is:** a fresh-engagement AI Data Analyst that takes a
natural-language question, asks the LLM to write pandas code,
and runs the code in a sandboxed subprocess. The security
boundary is a hard blocklist (28 regex patterns) + a subprocess
sandbox (timeout + memory cap + no-network env).

**What it proves:** the FDE pattern transfers to a different
customer, a different domain, a different security model.
Phases 1-3 are all about the PacificFreight drafter. Project 4
is about a different customer (Acme Analytics, a placeholder
for a 20-person SaaS company). The sandbox is a fresh failure
mode (code execution) that the PF drafter doesn't have.

**The artifact:** [`projects/04-ai-data-analyst/`](../projects/04-ai-data-analyst/) —
the blocklist (`security.py`), the sandbox (`sandbox.py`), the
3 tests (`test_sandbox.py`), the design doc (`ARCHITECTURE.md`).

## The 5 case studies (the lessons)

1. **[engagement-1-pf-drafter.md](./engagement-1-pf-drafter.md)** —
   the flagship engagement. 12 weeks, PacificFreight, 150
   drafts/day, 82% thumbs-up, P95 1.8s, $0.50/week.
2. **[engagement-2-pivot.md](./engagement-2-pivot.md)** — the
   "we said no after 2 weeks" case study. The legal-tech
   startup with the messy corpus. **Teaches when to walk away.**
3. **[engagement-3-postmortem.md](./engagement-3-postmortem.md)** —
   the week-11 hallucination incident. 38 minutes of recovery
   time. **Teaches incident response in public.**
4. **[engagement-4-slm-cost.md](./engagement-4-slm-cost.md)** —
   the SLM cost model. The 64% bill reduction. **Teaches
   cost-driven distillation.**
5. **[engagement-5-handoff.md](./engagement-5-handoff.md)** —
   the FDE-leaves narrative. The 5-question "FDE has left"
   test. **Teaches ownership transfer.**

## The 3 lessons (the technical depth)

- **[01-mcp-tools-and-policies.md](../technical/01-mcp-tools-and-policies.md)** —
  MCP schema design, the policy file as a YAML-first contract,
  the rate-limit-on-tools pattern (cost_credits), the sandbox
  pattern.
- **[02-multi-agent-design.md](../technical/02-multi-agent-design.md)** —
  when to use multi-agent vs single-agent, the shared state
  object, the escalation rule, the per-agent circuit breaker.
- **[03-fine-tuning-and-serving-slm.md](../technical/03-fine-tuning-and-serving-slm.md)** —
  when to distill (cost ceiling exceeded), dataset prep from
  `usage.jsonl`, LoRA vs full fine-tune, the eval-driven
  regression check, the model card as the artifact.

## The handoff (the proof I can leave)

The 5-question "FDE has left" test is the rubric for the
handoff. Daniel, Mei, and Sarah answered all 5 questions
correctly at 30 days and 60 days post-handoff. The customer is
in steady state. The bill is under the ceiling. The eval set
is green. The on-call rotation is staffed. The runbook is up
to date.

**The FDE has left. The engagement is done.**

## What this portfolio is for

This portfolio is for:

- **A job interview.** I bring the 3-page version to the
  interview. The interviewer asks "tell me about a hard
  problem." I point to engagement-2 (the pivot) or
  engagement-3 (the postmortem).
- **A portfolio site.** I link to the GitHub repo. The
  recruiter sees the 4 projects + 5 case studies + 3 lessons
  + 25 tests. They skim the case studies; they go deep on the
  one that interests them.
- **A customer engagement.** I show this to a new customer
  before I start. They see the pattern; they trust me to
  apply it to their problem.

The portfolio is not for:

- **A research paper.** I'm not claiming novelty. The MCP
  server is a 200-line reference implementation; the SLM is
  a 1.5B Qwen fine-tune; the multi-agent orchestrator is a
  hand-rolled state machine. The novelty is the *combination*:
  the eval set, the runbook, the cost ceiling, the
  iteration cadence, the handoff. That's the FDE pattern.

## The one-line summary

**I build AI services that survive the customer.** The eval
set is the spec. The runbook is the contract. The cost ceiling
is the score. The handoff is the proof.

## Where to start reading

If you're a recruiter or an interviewer, start here:
1. **[engagement-1-pf-drafter.md](./engagement-1-pf-drafter.md)** —
   the flagship. The 12-week PacificFreight story.
2. **[engagement-2-pivot.md](./engagement-2-pivot.md)** —
   the hardest decision. Walking away after 2 weeks.
3. **[engagement-3-postmortem.md](./engagement-3-postmortem.md)** —
   the public postmortem. The 38-minute recovery.

If you're a customer evaluating me, start here:
1. **[engagement-5-handoff.md](./engagement-5-handoff.md)** —
   the proof I can leave you in steady state.
2. **[engagement-4-slm-cost.md](./engagement-4-slm-cost.md)** —
   the cost model. The number you take to your CFO.
3. **[projects/04-ai-data-analyst/](../projects/04-ai-data-analyst/)** —
   the project that proves the pattern transfers to your
   domain.

If you're a student of the FDE pattern, start here:
1. **[technical/01-mcp-tools-and-policies.md](../technical/01-mcp-tools-and-policies.md)** —
   the MCP pattern, with a worked example.
2. **[technical/02-multi-agent-design.md](../technical/02-multi-agent-design.md)** —
   the multi-agent pattern, with a worked example.
3. **[technical/03-fine-tuning-and-serving-slm.md](../technical/03-fine-tuning-and-serving-slm.md)** —
   the SLM pattern, with a worked example.

## Closing

The 4 projects + 5 case studies + 3 lessons + 25 tests are the
proof. The pattern is what I do; the projects are what I've
built; the case studies are what I've learned; the handoff is
how I leave.

**The FDE pattern: eval-set-as-spec, runbook-as-contract,
cost-ceiling-as-score.**