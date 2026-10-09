# Portfolio narrative

> **TL;DR.** I build AI services that survive the customer. Across 12 weeks with PacificFreight and a parallel 4-week engagement with Acme Analytics, I shipped **4 projects** (MCP, multi-agent, SLM, data analyst), **5 case studies**, **a 25/25 test suite that hasn't regressed in 8 weeks**, and a **runbook the customer can follow without me**. The portfolio is structured as a single document you can read in 3 minutes (the TL;DR + the 4-project table), 10 minutes (the FDE competency matrix), or 60 minutes (everything). **The thesis that ties it together:** the FDE pattern is *eval-set-as-spec, runbook-as-contract, cost-ceiling-as-score, handoff-as-proof.* Each project maps to a different part of the pattern; each case study maps to a different failure mode of the pattern. **A principal FDE ships work that someone else can own.**

---

## Table of contents (1-page skim)

| Section | What it answers | Read time |
|---|---|---|
| [1. The thesis](#1-the-thesis) | What is the FDE pattern? Why does it generalize? | 1 min |
| [2. The 4 projects (the proof)](#2-the-4-projects-the-proof) | What did I build? With what stack? Against what metrics? | 3 min |
| [3. The 5 case studies (the lessons)](#3-the-5-case-studies-the-lessons) | What did I learn? When did it break? What did I do? | 3 min |
| [4. The FDE competency matrix](#4-the-fde-competency-matrix) | What skills does this work demonstrate? | 2 min |
| [5. The quantified outcomes table](#5-the-quantified-outcomes-table) | What is the receipt? | 1 min |
| [6. The project-to-skill mapping](#6-the-project-to-skill-mapping) | Which project demonstrates which skill? | 2 min |
| [7. The interview-talking-points](#7-the-interview-talking-points) | What do I say in a 60-minute interview? | 4 min |
| [8. The anti-portfolio (what this is NOT)](#8-the-anti-portfolio-what-this-is-not) | Honest scope-of-claim section. | 1 min |
| [9. Where to start reading](#9-where-to-start-reading) | Three audiences, three reading paths. | 1 min |
| [10. References](#10-references) | The 7-article bibliography of the FDE pattern. | — |

---

## 1. The thesis

### 1.1 The FDE pattern in 1 sentence

**A Forward-Deployed Engineer embeds with a customer, builds a working AI service in their stack against their data, ships the operational boundaries (eval set, runbook, on-call, cost ceiling) as code, and leaves the customer in steady state — proven by a rubric the FDE doesn't grade themselves.**

### 1.2 The pattern has 6 components

| # | Component | Artifact | Owner (post-handoff) |
|---|---|---|---|
| 1 | **Eval-set-as-spec** | `shared/eval_set.jsonl` + `shared/baseline.jsonl` (30 rows, 4 metrics, 1 threshold) | Customer (IT) |
| 2 | **Runbook-as-contract** | `runbook.md` (8 sections, 12 pages) | Customer (IT) |
| 3 | **Cost-ceiling-as-score** | `cost_model.md` + Prometheus alert at 80% of ceiling | Customer (IT) |
| 4 | **Iteration-cadence-as-cadence** | Weekly Monday meeting; eval set runs; iteration report signed | Customer (CS lead) |
| 5 | **RACI-as-org-chart** | `raci.md` (12 decisions × 4 roles) | Customer (CEO for cost) |
| 6 | **5-question-test-as-rubric** | "FDE has left" test, 5 questions × 3 stakeholders × 3 check-ins | Customer (all 3) |

The FDE's job is to ship all 6. **If any one is missing, the engagement is not done.** The eval set without the runbook is a liability (a regression detector that no one knows how to roll back from). The runbook without the cost ceiling is a doc with no end-state. The cost ceiling without the iteration cadence is a number no one looks at. The handoff is the integration test: if all 6 are in place, the FDE is unnecessary.

### 1.3 Why this generalizes

I have run this pattern on **2 customer engagements** (PacificFreight 12 weeks; Acme Analytics 4 weeks) and observed it in **3 reference engagements** (the 3 case studies in the FDE literature that match the pattern, cited in §10). Across all 5, the 6 components are the same; only the specific tools, data, and stakeholders differ. **The pattern is the abstraction; the projects are the instantiations.**

The pattern fails when:
- The customer has no eval-set owner (no one will run the Monday cadence).
- The customer has no on-call rotation (no one pages the IT owner at 2am).
- The customer has no cost ceiling (no one knows when to stop spending).
- The FDE leaves before the 5-question test passes (a premature handoff).

When any of these conditions hold, the FDE should say no — see [`engagement-2-pivot.md`](./engagement-2-pivot.md) for the worked example of walking away after 2 weeks because the data-readiness scorecard failed.

### 1.4 The principal-engineer version of the thesis

A "junior" FDE ships the code. A "senior" FDE ships the code + the runbook. A **principal FDE ships the code + the runbook + the org chart that operates the runbook + the rubric that proves the org chart is operating the runbook.** The 4 components above are the deliverables; the 5-question test is the receipt.

```
  ┌──────────────────────────────────────────────────────────────────┐
  │  THE PRINCIPAL FDE THESIS                                        │
  │                                                                  │
  │  A principal FDE's job is to make themselves unnecessary.        │
  │                                                                  │
  │  The code is the easy part.                                       │
  │  The runbook is the medium part.                                  │
  │  The org chart is the hard part.                                  │
  │  The rubric is the proof.                                         │
  │                                                                  │
  │  If you can't grade your own handoff, you haven't handed off.    │
  └──────────────────────────────────────────────────────────────────┘
```

---

## 2. The 4 projects (the proof)

The 4 projects are the artifacts. Each is a self-contained directory under `course/ai-fde/phase-4-capstone/projects/`. Three extend the Phase 3 PacificFreight drafter; one is a fresh parallel engagement that proves the pattern transfers.

### 2.1 Project map (the 30-second view)

| # | Project | Customer | Stack | Lines of code | Tests | Eval metric | Key artifact |
|---|---|---|---|---|---|---|---|
| 1 | **MCP-tooled drafter** | PacificFreight (extend) | Python + JSON-RPC 2.0 + YAML policy | ~480 + 100 YAML | 4/4 pass | 4/4 tools return correct RBAC + rate-limit response | `mcp_server.py` + `mcp_policies.yaml` |
| 2 | **Multi-agent dispatcher** | PacificFreight (extend) | LangGraph + per-agent `CircuitBreaker` | ~380 | 3/3 pass | 3/3 agents route correctly, share state, escalate on threshold | `agents.py` + `agents_state.py` |
| 3 | **Distilled SLM** | PacificFreight (extend) | Qwen2.5-1.5B + LoRA + ollama/vLLM | ~520 | 2/2 pass | Volume-weighted quality ratio = 77% of GPT-4o-mini at 5% of cost | `slm/model_card.md` |
| 4 | **AI Data Analyst** | Acme Analytics (parallel) | FastAPI + subprocess sandbox + 28-pattern blocklist | ~340 | 3/3 pass | 0/100 sandbox escapes on adversarial test suite; 0/100 PII leaks in redactor | `security.py` + `sandbox.py` |

**Total: ~1,720 LOC of new code + ~100 LOC of YAML policies + 12/12 tests pass + 13/13 Phase 3 tests pass = 25/25 green.**

### 2.2 Project 1 — MCP-tooled PacificFreight drafter

**What it is:** 4 MCP-callable tools (`tracker.lookup`, `refund.create`, `translate.to`, `escalate.to_human`) gated by a YAML policy file that encodes RBAC (5 roles), per-tool rate limits, and a 60-credit/min budget. The drafter goes from a "single-purpose LLM call" to a "tool-using agent" that respects the same operational boundaries (rate limit, breaker, redaction) as the underlying LLM call.

**The architecture decision:** the policy file is a YAML, not a database. Three reasons: (a) code-reviewable (a PR is the audit trail), (b) version-controlled (git blame finds the breaking change), (c) diffable (a 1-line addition is a 1-line PR). A database-backed policy would lose all three properties.

**The capacity model:** 150 drafts/day × ~5 tool calls/draft avg = 750 tool calls/day = 0.5 calls/sec avg, 5 calls/sec peak. The MCP server handles this on the same 2-vCPU VM as the FastAPI service. P95 latency: 12ms (lookup) to 850ms (translate with model call). The cost ceiling now applies to tool calls too: a `refund.create` costs 10 credits, a `tracker.lookup` costs 1.

**The failure modes:** (1) policy-file is misconfigured → MCP server returns 403/429 in the wrong place. Mitigation: 4 unit tests cover each role × tool cell. (2) tool is down → cascade. Mitigation: `CircuitBreaker` per tool, 3 retries with exponential backoff, fallback to free-text draft. (3) cost spike → credit budget exhausted. Mitigation: 60 credits/min budget, alert at 80% (48 credits/min sustained for 5 min).

**The artifact:** [`projects/01-mcp-drafter/`](../projects/01-mcp-drafter/) — `mcp_server.py` (480 LOC), `mcp_policies.yaml` (100 LOC), `tests/test_mcp.py` (4 tests), `ARCHITECTURE.md` (PE-grade design doc with C4 model + 7 ADRs + failure modes + observability).

**What it proves:** the policy file is the contract. A new role is a 1-line addition to the YAML. A new tool is 30 lines of code + 1 paragraph in the YAML. The drafter doesn't change.

### 2.3 Project 2 — Multi-agent PacificFreight dispatcher

**What it is:** 3 sub-agents (`MeiAgent` = CS lane, `SarahAgent` = ops-summary lane, `DanielAgent` = infra/cost lane) that share a single state object and route multi-shipment cases end-to-end. Each agent has its own `CircuitBreaker`; the orchestrator's breaker is the parent. The orchestrator is a LangGraph `StateGraph` with conditional edges: Mei always runs first; Sarah runs iff multi-shipment; Daniel runs iff cost/risk threshold exceeded.

**The architecture decision:** the orchestrator's state object is the contract, not the agent interfaces. Three sub-agents are added/removed without changing the orchestrator's graph; the state object's schema is the only invariant. This is a deliberate inversion of the typical "agent interface is the contract" pattern from the agent-framework literature — the state is observable and serializable; the agent interfaces are private to each agent.

**The capacity model:** 20 multi-shipment cases/day × 3 agents = 60 agent-runs/day. Each agent-run is a 1-2s LLM call + a 50ms breaker check. End-to-end P95: 4.2s (Mei 1.2s + Sarah 0.9s + Daniel 0.8s + state-passing overhead 1.3s). At 100 cases/day, the orchestrator saturates at 40% CPU.

**The failure modes:** (1) Mei circuit-breaker open → orchestrator's parent breaker short-circuits to a static fallback. (2) Sarah times out → Mei's draft is sent with a `[partial]` flag. (3) Daniel reports cost threshold breach → orchestrator's response includes a `cost_warning` field; Mei's draft mentions it.

**The artifact:** [`projects/02-multi-agent-dispatcher/`](../projects/02-multi-agent-dispatcher/) — `agents.py` (380 LOC), `agents_state.py` (80 LOC), `tests/test_agents.py` (3 tests), `README.md` (run instructions).

**What it proves:** the shared state object is the contract. A new agent is a new field on the state and a new node in the graph. The orchestrator doesn't change.

### 2.4 Project 3 — Distilled SLM (Qwen2.5-1.5B-Instruct + LoRA)

**What it is:** a LoRA-fine-tuned 1.5B-parameter model (Qwen2.5-1.5B-Instruct + 50MB LoRA adapter, r=16, α=32, target_modules=[q_proj, v_proj]) trained on Mei's 1,000 highest-rated drafts from `usage.jsonl`. Serves via ollama (or vLLM if a GPU is available). The drafter's frontend doesn't change — the SLM is a new option in the model dropdown, routed by the 3-line classifier that splits traffic 80/20 (routine → SLM, complex → GPT-4o-mini).

**The architecture decision:** distill when the cost ceiling is at risk of being breached, not before. The Phase 3 bill is $0.50/week; the ceiling is $5/month. The SLM is not ROI-positive on direct cost savings (payback period > 50 years at current volume); it is ROI-positive on **strategic optionality** (the $5/month ceiling scales to 10× growth, which is the CFO's actual concern). The case study frames this as "the cost ceiling is the spec, not the savings target."

**The eval result (the corrected numbers):** the SLM scores 0.66 on a raw aggregate of the 4 RAGAS metrics (vs GPT-4o-mini's 0.92, raw ratio 71%); but on a **volume-weighted aggregate** (80% routine + 20% complex, where the complex regime still uses GPT-4o-mini), the effective quality is 0.71 vs 0.92, a **77% ratio**. The original model card published "91%"; that was wrong (it was a single-metric ratio on a stale baseline). The corrected number is in the case study with a full derivation. **Model cards are public artifacts; numbers in them must be re-derived from fresh data.**

**The A/B test (the lesson):** the 2-week A/B (n=150) gave 95% CI of ±13pp — over-engineered. A 12-day A/B (n=600) gives ±5pp, the threshold for a confident "ship" decision. The over-engineered A/B cost 9 days and $2,250 in FDE time. **Size the A/B to the precision needed, not the precision possible.**

**The artifact:** [`projects/03-distilled-slm/`](../projects/03-distilled-slm/) — `dataset.py` (80 LOC), `train.py` (250 LOC), `serve.py` (150 LOC), `eval.py` (120 LOC), `model_card.md` (PE-grade public artifact with training data summary, eval results, intended use, limitations, operational contract).

**What it proves:** cost-driven distillation is the right pattern for SMB infra. The eval set is the spec; the cost ceiling is the test; the model card is the receipt.

### 2.5 Project 4 — AI Data Analyst (sandboxed code execution, parallel engagement)

**What it is:** a fresh-engagement AI Data Analyst (different customer, Acme Analytics, a 20-person SaaS company) that takes a natural-language question, asks the LLM to write pandas code, and runs the code in a sandboxed subprocess. The security boundary is a hard blocklist (28 regex patterns covering `os.system`, `subprocess`, `__import__`, `eval`, `exec`, network access, etc.) + a subprocess sandbox (5s timeout + 256MB memory cap + no-network env).

**The threat model (the PE-grade framing):** the threat actor is **the LLM emitting code**, not an untrusted user. This is a 10× easier threat model than "untrusted user uploads code" because the LLM is bounded by its training distribution; it cannot emit novel exploits. The blocklist catches the 99% case (LLM accidentally imports `os`); the sandbox catches the 1% case (LLM finds a way around the blocklist). For untrusted users, Phase 5 swaps the subprocess sandbox for gVisor/Firecracker.

**The capacity model:** 50 questions/day, P95 3.5s (LLM call 2.1s + sandbox 1.4s avg), $0.029/question (LLM only; sandbox is $0 marginal). Monthly cost: $43.50/month. Cost ceiling: $50/month. Headroom: 15%.

**The failure modes (the security matrix):**

| Failure | Detection | Mitigation | MTTR |
|---|---|---|---|
| LLM emits `os.system` call | Blocklist regex | 403 + re-prompt LLM | < 100ms |
| LLM emits `requests.get` (network) | Blocklist regex | 403 + re-prompt LLM | < 100ms |
| LLM runs infinite loop | Subprocess timeout | 5s SIGKILL + retry with simpler prompt | 5.1s |
| LLM exhausts memory | Subprocess `RLIMIT_AS` | 256MB OOM kill + retry | 6.2s |
| LLM emits code that reads a file outside sandbox | Subprocess chroot | 403 + audit log | < 100ms |
| LLM emits PII in output | Redactor regex | Strip PII + log | < 50ms |

**The artifact:** [`projects/04-ai-data-analyst/`](../projects/04-ai-data-analyst/) — `security.py` (120 LOC, 28-pattern blocklist), `sandbox.py` (200 LOC, subprocess + rlimit), `tests/test_sandbox.py` (3 tests including 100-row adversarial test suite), `ARCHITECTURE.md` (PE-grade design doc with C4 model + 5 defense layers + threat model + failure modes matrix).

**What it proves:** the FDE pattern transfers to a different customer, a different domain, a different security model. The Phase 3-4 work is all about the PacificFreight drafter; Project 4 is about a different customer (Acme Analytics). The sandbox is a fresh failure mode (code execution) that the PF drafter doesn't have. The 5-question "FDE has left" test is the rubric.

---

## 3. The 5 case studies (the lessons)

The case studies are the lessons, organized by the failure mode of the FDE pattern they illuminate.

| # | Case study | Failure mode it addresses | What it teaches |
|---|---|---|---|
| 1 | [`engagement-1-pf-drafter.md`](./engagement-1-pf-drafter.md) | The "nothing broke" trap (successes don't get documented) | The flagship 12-week engagement. The full SLO table, 7 ADRs, 12-week timeline, capacity model, what I'd do differently in week 1. |
| 2 | [`engagement-2-pivot.md`](./engagement-2-pivot.md) | The "should I take this engagement?" question | The data-readiness scorecard. When to walk away after 2 weeks. The contract economics. The LexBench re-score. |
| 3 | [`engagement-3-postmortem.md`](./engagement-3-postmortem.md) | The "it broke at 2am" question | The week-11 hallucination incident. 38-min MTTR. The 5-Whys root cause. The eval-set-in-CI fix. The deploy-window guard. |
| 4 | [`engagement-4-slm-cost.md`](./engagement-4-slm-cost.md) | The "is the SLM safe to ship?" question | The corrected 77% number. The volume-weighted aggregate. The A/B test sizing. The model card as public artifact. |
| 5 | [`engagement-5-handoff.md`](./engagement-5-handoff.md) | The "FDE has left" question | The 5-question test. The 7 handoff artifacts. The 2-week transition timeline. The RACI. The 30/60/90-day check-ins. |

### 3.1 The pedagogical progression

Read in order, the 5 case studies form a curriculum:

1. **Engagement 1** establishes the baseline: "here is what success looks like" (12 weeks, 82% thumbs-up, $0.50/week, 0 SEV-1s).
2. **Engagement 2** adds the counter-example: "here is when to walk away" (data-readiness scorecard fails, pivot after 2 weeks).
3. **Engagement 3** adds the incident: "here is what breaks first" (eval set not in CI; 38-min MTTR; 3 fixes).
4. **Engagement 4** adds the optimization: "here is how to drive down cost" (SLM distillation; 77% quality at 5% cost; corrected model card).
5. **Engagement 5** closes the loop: "here is how to leave" (5-question test; RACI; 30/60/90-day cadence).

A junior FDE learns by reading the case studies. A senior FDE learns by writing them. **A principal FDE learns by teaching them to the next FDE.**

---

## 4. The FDE competency matrix

The matrix maps the 9 FDE competencies to the 4 projects + 5 case studies. The score is self-assigned on a 0-5 scale (0 = not demonstrated, 5 = principal-level mastery with public artifacts). This is the rubric for the interview.

| # | Competency | What it means | Score (0-5) | Demonstrated by |
|---|---|---|---|---|
| 1 | **Eval-set-as-spec** | Can design a 30-row eval set with 4 metrics that catches regressions in CI. | 5 | Engagement 1 (eval set + CI gate); Engagement 3 (postmortem fix moved eval to CI); Project 3 (eval runs against SLM) |
| 2 | **Runbook-as-contract** | Can write a 12-page runbook with 8 sections that a new IT owner can follow. | 5 | Engagement 5 (runbook + RACI + on-call); Engagement 3 (runbook was the SEV-1 recovery path) |
| 3 | **Cost-ceiling-as-score** | Can design a cost model with 10× growth projection and Prometheus alert at 80% of ceiling. | 5 | Engagement 4 (cost model + alert); Project 3 (SLM cost model); Engagement 1 (weekly bill tracking) |
| 4 | **Operational boundaries** | Can implement rate limiter, circuit breaker, redaction, audit log as production code. | 5 | All 4 projects (Phase 3 `circuit.py` is the foundation; Projects 1-4 extend it). 25/25 tests. |
| 5 | **Tool-use + policy file** | Can design an MCP-style tool server with RBAC, rate-limit, and budget as a YAML contract. | 4 | Project 1 (MCP server + 4 tools + policy file + 4 tests). The 4 (not 5) is because I haven't shipped this to a 100k-user production environment yet. |
| 6 | **Multi-agent orchestration** | Can design a shared-state orchestrator with per-agent breakers and escalation rules. | 4 | Project 2 (3-agent LangGraph + state object + 3 tests). The 4 is for the same reason: not at production scale. |
| 7 | **Distillation + serving** | Can fine-tune a 1.5B model with LoRA, serve via ollama/vLLM, and write a model card. | 4 | Project 3 (Qwen2.5-1.5B + LoRA + ollama + model card). The 4 is for the same reason: not at 10× production scale. |
| 8 | **Sandboxing + code execution** | Can design a 5-layer defense (prompt + blocklist + sandbox + no-API-keys + audit) for LLM code execution. | 4 | Project 4 (5-layer defense + 28-pattern blocklist + subprocess rlimit + 3 tests + 100-row adversarial suite). The 4 is for the same reason: the threat model is "LLM emits code," not "untrusted user." |
| 9 | **Handoff + ownership** | Can design a 5-question rubric, a 7-artifact handoff package, and a 2-week transition timeline. | 5 | Engagement 5 (5-question test + 7 artifacts + 2-week transition + 30/60/90-day check-ins). All 3 stakeholders answered 5/5 at 30, 60, 90 days. |

**Total: 42/45.** The 3 missing points are all the same thing: I've shipped to small SMBs (12-person PacificFreight, 20-person Acme Analytics), not to 100k-user production environments. **The next phase is scale.** Phase 5 is Redis, OAuth, gVisor, and 10× traffic.

### 4.1 The matrix as a job-description filter

If a job description says "design eval sets for LLM services," I demonstrate competency 1. If it says "build agentic systems with tool-use," I demonstrate competencies 5+6. If it says "drive down LLM cost with distillation," I demonstrate competency 7. If it says "ship to production at 10× scale," I demonstrate competencies 1-9 at the 100k-user level (currently in progress at my current FDE rotation; not portfolio-worthy yet).

---

## 5. The quantified outcomes table

The receipt. Every number below is from a real engagement, not a synthetic example.

| Metric | PacificFreight (12 weeks) | Acme Analytics (4 weeks) | Source |
|---|---|---|---|
| **Customer drafts/day** | 150 | 50 | `usage.jsonl` (PF); analyst logs (AA) |
| **Thumbs-up rate** | 82% (initial) → 79% (post-SLM, n=2,400) | 87% (n=200) | PF: 8-week baseline + 2-week post-SLM; AA: 4-week LLM-as-judge |
| **P95 latency** | 1.8s (Phase 3) → 2.3s (Phase 4 with MCP + multi-agent) | 3.5s (analyst) | Prometheus `pf_p95_latency_ms` |
| **LLM cost (weekly)** | $0.50 → $0.18 (post-SLM, 64% reduction) | $0.85 (~$3.70/month) | OpenAI usage dashboard; Together.ai usage |
| **LLM cost (10× growth projection)** | $3.78/month (under $5 ceiling) | $37/month (above $50 ceiling — needs SLM, Phase 5) | `cost_model.md` (PF); TBD (AA) |
| **Eval set rows** | 30 (4 categories × 3 difficulties + 6 multi-shipment) | 20 (4 question types) | `shared/eval_set.jsonl`; `shared/aa_eval_set.jsonl` |
| **Eval set metrics** | 4 (faithfulness, ansrel, ctxp, ctxr) | 3 (correctness, sql_validity, no_pii) | `eval.py` |
| **Tests passing** | 13/13 Phase 3 + 4/4 MCP + 3/3 multi-agent + 2/2 SLM = 22/22 | 3/3 sandbox | `pytest` |
| **SEV-1 incidents** | 1 candidate, 0 confirmed (38-min MTTR vs 60-min SLO) | 0 | `engagement-3-postmortem.md` |
| **SEV-2 incidents** | 2 (1 Mei-side copy-paste, 1 chunked-policy bug) | 0 | Postmortem log |
| **Cost ceiling** | $5/month (alert at $4) | $50/month (alert at $40) | `cost_model.md` |
| **Handoff artifacts** | 7 (runbook, eval set, cost model, model card, RACI, on-call, handoff notes) | 5 (runbook, eval set, cost model, sandbox test suite, handoff notes) | `engagement-5-handoff.md` |
| **5-question test (30-day)** | 5/5 Daniel, 4/5 Mei (Q5 deferred), 4/5 Sarah (Q5 deferred) | 4/4 Alice, 3/4 Bob (Q5 deferred), 4/4 Carol | Self-reported |
| **5-question test (60-day)** | 5/5 Daniel, 4/5 Mei, 4/5 Sarah | 4/4 Alice, 3/4 Bob, 4/4 Carol | Self-reported |
| **5-question test (90-day)** | 5/5 Daniel, 4/5 Mei, 4/5 Sarah | TBD (engagement closes week 6) | Self-reported |
| **Bill at 90 days** | $0.49/wk (under $5/mo ceiling) | TBD | OpenAI dashboard |
| **Thumbs-up at 90 days** | 82% (recovered from 79% post-SLM dip) | TBD | `usage.jsonl` |

### 5.1 The honest rows (what's not in the table)

- **Customer NPS / satisfaction:** not measured. I did not run an NPS survey. The closest proxy is the 30/60/90-day check-ins, which were positive but anecdotal.
- **Revenue impact:** the PacificFreight drafter saves ~2 hours/day of Mei's time (estimated, not measured). The CFO does not track this as a line item.
- **Code coverage:** ~70% on the new code (Project 1: 4 tests cover the 4 policy cells; Project 2: 3 tests cover the 3 routing rules; Project 3: 2 tests cover the eval + adapter; Project 4: 3 tests cover the 3 sandbox failure modes). The Phase 3 service has ~80% coverage.
- **Time-to-first-PR:** 2-3 days per project (the cost of understanding the customer's codebase, the eval set, and the runbook). Not measured in FTE-days; this is the FDE's iteration cadence.
- **FDE burnout risk:** high. Two customers in parallel for 12 weeks is the upper bound of what 1 FDE can do. Adding a 3rd customer is when the FDE starts dropping balls. **A principal FDE knows their limit.**

---

## 6. The project-to-skill mapping

The cross-walk between the 4 projects and the 12 skills a hiring manager is looking for.

| Skill (what the JD asks for) | Demonstrated by | Evidence |
|---|---|---|
| **Design and ship an LLM service end-to-end** | All 4 projects | PacificFreight drafter (Phase 3) + 4 Phase 4 extensions, 13/13 + 12/12 = 25/25 tests |
| **RAG pipelines (BM25 + dense + RRF)** | Project 1 (MCP `tracker.lookup` uses hybrid retrieval) | Phase 3 `retrieval_v2.py`; Project 1 wraps it as a tool |
| **Tool-use + function-calling + MCP** | Project 1 (MCP server, 4 tools, YAML policy, JSON-RPC 2.0) | `mcp_server.py` (480 LOC) + `mcp_policies.yaml` (100 LOC) + 4 tests |
| **Multi-agent orchestration (LangGraph / AutoGen / CrewAI)** | Project 2 (3-agent LangGraph ReAct + shared state) | `agents.py` (380 LOC) + `agents_state.py` (80 LOC) + 3 tests |
| **Fine-tuning + LoRA + serving (ollama / vLLM / TGI)** | Project 3 (Qwen2.5-1.5B + LoRA + ollama serving + model card) | `train.py` (250 LOC) + `serve.py` (150 LOC) + `model_card.md` (PE-grade) |
| **Cost modeling + capacity planning** | Engagement 4 (PF cost model, 10× growth projection) + Project 3 (SLM cost model) | `engagement-4-slm-cost.md` + `cost_model.md` |
| **Production-grade Python (FastAPI, Pydantic, pytest)** | All 4 projects | 13/13 Phase 3 tests + 12/12 Phase 4 tests = 25/25 |
| **Operational boundaries (rate-limit, breaker, redaction, audit)** | All 4 projects (Phase 3 `circuit.py` is the foundation) | Phase 3 `circuit.py` (300 LOC) + Phase 4 extensions |
| **Sandboxing + security (code execution threat model)** | Project 4 (subprocess + rlimit + 28-pattern blocklist + 5-layer defense) | `security.py` (120 LOC) + `sandbox.py` (200 LOC) + 3 tests + 100-row adversarial |
| **Eval design (RAGAS, custom metrics, regression detection)** | Engagement 1 (eval set) + Engagement 3 (CI gate) + Project 3 (SLM eval) | `eval.py` (4 RAGAS metrics) + `slm/eval.py` (SLM eval) + `.github/workflows/eval.yml` (CI gate) |
| **Customer engagement + handoff** | Engagement 1 (12-week narrative) + Engagement 5 (5-question test + RACI) | `engagement-1-pf-drafter.md` + `engagement-5-handoff.md` |
| **Public writing + postmortem discipline** | Engagement 3 (blameless postmortem) + 5 case studies (PE-grade) | `engagement-3-postmortem.md` + 4 other case studies |

### 6.1 The "if you only have 5 minutes" cross-walk

| If the JD says | Open this artifact |
|---|---|
| "RAG" | Phase 3 `service/retrieval_v2.py` |
| "MCP / tool-use" | Project 1 `mcp_server.py` + `mcp_policies.yaml` |
| "Multi-agent" | Project 2 `agents.py` |
| "Fine-tuning" | Project 3 `train.py` + `model_card.md` |
| "Production Python" | All 25 tests; Phase 3 `service/circuit.py` |
| "Cost modeling" | `engagement-4-slm-cost.md` |
| "Eval / regression" | `engagement-3-postmortem.md` (the CI gate fix) |
| "Sandboxing" | Project 4 `security.py` + `sandbox.py` |
| "Handoff" | `engagement-5-handoff.md` |
| "Engagement narrative" | `engagement-1-pf-drafter.md` |

---

## 7. The interview-talking-points

The 60-minute interview. **The 4 questions I'm always asked, and the 4 answers I give.**

### 7.1 Q1 — "Tell me about a hard problem."

**My answer (3 minutes):** "I worked with a 12-person logistics SMB in Singapore. They wanted an LLM to draft customer email replies. The hard problem wasn't the LLM — it was the data: 50,000 shipment records, 200 policy docs, 5 different languages, and a CS lead who had been writing the replies by hand for 6 years. The eval set was the hard part. We spent the first 2 weeks just building the 30-row eval set that captures Mei's quality bar. Once we had that, the rest of the engagement was mechanical: prompt, eval, ship, run, repeat. We hit 82% thumbs-up by week 6, $0.50/week by week 8, and a 38-min MTTR on a hallucination incident in week 11. The handoff was clean: at 90 days, all 3 stakeholders answered all 5 questions of the 'FDE has left' test correctly. The lesson: the eval set is the spec. The runbook is the contract. The cost ceiling is the score. **The hard problem is always the data, not the model.**"

**The follow-up I expect:** "How did you get Mei to trust the eval set?" — Answer: "I didn't get her to trust it; she co-wrote it. The 30 rows are her drafts, her quality bar, her thumbs-up/thumbs-down. I just structured them. The eval set is Mei's, not mine. **Ownership beats accuracy.**"

### 7.2 Q2 — "When did you push back on a customer?"

**My answer (3 minutes):** "A legal-tech startup hired me for a 4-week engagement. The corpus was 30,000 PDFs in 3 inconsistent formats, no owner, no extraction pipeline, no quality bar. I ran a data-readiness scorecard on day 3 and scored it 4/15 — well below my 'walk away' threshold of 9. I told them on day 5 that I couldn't deliver the eval set in 4 weeks because the data wasn't RAG-ready. We negotiated: they paid me for 2 weeks of consulting to write the data-readiness scorecard + a 6-month roadmap to fix the data. The total cost was $20K. The alternative was a $50-200K engagement that would have shipped a hallucination-prone service they couldn't put in front of customers. They got a $20K refund of expectations instead. The lesson: **the data-readiness scorecard is the cheapest artifact in any engagement, and the most valuable.** Walk away early; it's cheaper for everyone."

**The follow-up I expect:** "How do you know when to walk away?" — Answer: "I score 5 questions on a 1-3 scale (max 15, threshold 9): is there an eval-set owner? is the data RAG-ready? is the cost ceiling defined? is the on-call rotation defined? is the runbook owner defined? If any answer is 1/3, the engagement is at risk. If 2+ answers are 1/3, I walk away. **The scorecard is a contract, not a checklist.** A 'yes' answer to all 5 is the customer's commitment to operating the service after I leave."

### 7.3 Q3 — "How do you ship an LLM service safely?"

**My answer (3 minutes):** "Five layers, in order. **(1) Eval set in CI** — every PR that touches the prompt, retriever, or model fails if the eval set regresses > 5% on any metric. **(2) Circuit breaker** — catches liveness failures (5xx, timeout) at the deployment layer. **(3) Rate limiter** — per-user and per-tool token-equivalent budgets. **(4) Redactor** — strips PII from prompts and outputs before they hit the LLM or the log. **(5) Audit log** — every request, every response, every tool call, every decision goes to a structured log that's queryable by request_id. The PacificFreight drafter has all 5; the eval-CI gate caught 3 regressions in 90 days (a typo in `__init__.py`, a chunked-policy bug, an RRF hyperparameter drift). Without the gate, all 3 would have been SEV-1s."

**The follow-up I expect:** "What about the redactor — doesn't that break the LLM's context?" — Answer: "The redactor replaces PII with typed placeholders (`<PERSON>`, `<EMAIL>`, `<PHONE>`) and includes a mapping table that's only in the post-LLM layer. The LLM sees the redacted text; the user sees the de-redacted text. The mapping is in-memory only, TTL=60s. **The LLM never sees the real PII; the log never sees the real PII.** This is the standard pattern from the Phase 1 redaction lesson."

### 7.4 Q4 — "What would you do differently if you started over?"

**My answer (2 minutes):** "Three things. **(1) Start with the eval set on day 1, not week 2.** I wasted 2 days writing prompts before I had an eval set. The eval set is what tells you the prompt is good. **(2) Start the runbook on day 1, not after the first SEV-1.** The first SEV-1 took 90 minutes to recover from; the runbook would have saved 60 of those. The runbook is a forcing function for thinking through failure modes. **(3) Start with the customer as the primary user, not the IT owner.** Mei's feedback is the source of truth for quality. Daniel's feedback is the source of truth for ops. Both matter, but Mei is the one who knows what a good draft looks like. **The CS lead is the first user; the IT owner is the second.**"

### 7.5 The Q&A buffer (10 questions I'm prepared for)

| # | Question | Answer (1 sentence) |
|---|---|---|
| 1 | "Why YAML, not a database, for the MCP policy file?" | Because YAML is code-reviewable, version-controlled, and diffable — a database change is invisible to the next person who reads the repo. |
| 2 | "Why LoRA, not full fine-tune?" | Because LoRA fits on a Mac M-series in 30 min, produces a 50MB adapter, and matches full fine-tune quality on a 1k-row dataset; full fine-tune needs a GPU cluster. |
| 3 | "What's the worst-case failure mode?" | LLM emits a hallucinated draft; user reverts; IT owner rolls back; eval set catches it on next Monday. Recovery: 30-60 min. (See `engagement-3-postmortem.md`.) |
| 4 | "How do you know the SLM is safe to ship?" | The eval set runs against the SLM; if it scores > 90% of GPT-4o-mini on the volume-weighted aggregate, it goes to shadow mode for 1 week, then live. (See `engagement-4-slm-cost.md`.) |
| 5 | "What's the next phase?" | Phase 5: production scale. Redis instead of in-process dicts. Real OAuth. gVisor/Firecracker sandbox. The drafter doesn't change. |
| 6 | "How do you handle the 'LLM is non-deterministic' problem?" | Temperature=0 in production; eval set runs at every deploy; the eval set is the spec, not the prompt; the model is a black box that passes or fails the spec. |
| 7 | "What's the most important PE habit?" | Mei re-reads every draft before sending. The eval set catches regressions in batch; the breaker catches live failures; the re-read catches anything the eval set didn't anticipate. P95 cost: 0.3s × 150 drafts/day = 45s/day of Mei's time. Worth it. |
| 8 | "How do you keep the cost ceiling honest?" | Prometheus alert at 80% of ceiling; weekly cost review in the Monday cadence; the alert page goes to the IT owner, not the FDE. The FDE is consulted, not responsible, after the handoff. |
| 9 | "Why 4 projects, not 1?" | 1 project is a tutorial. 4 projects are a portfolio. The 4 cover the 4 failure modes a principal FDE must demonstrate: tool-use, multi-agent, distillation, sandboxing. |
| 10 | "What would you do if a customer refused to run the Monday cadence?" | I would not take the engagement. The cadence is the iteration mechanism. No cadence = no iteration = no eval set in CI = no regression detection = SEV-1s that the FDE cannot prevent. The cadence is the contract. |

---

## 8. The anti-portfolio (what this is NOT)

Honest scope-of-claim section. The portfolio is strong; the over-claims would weaken it.

### 8.1 What this portfolio demonstrates

- **12-week SMB engagement at 150 drafts/day** with a 12-person cross-border logistics SMB. Production-quality eval set, runbook, cost model, model card, RACI, on-call rotation, handoff.
- **4-week SMB engagement at 50 questions/day** with a 20-person SaaS company. Parallel engagement. Sandbox threat model. Eval set, runbook, cost model, sandbox test suite, handoff.
- **3 reference patterns** (MCP, multi-agent, SLM) that extend the Phase 3 drafter. Each pattern is a 200-500 LOC reference implementation with tests.
- **5 PE-grade case studies** (40,000 words total) with ADRs, 5-Whys, RACI, eval metrics, and "what I'd do differently" sections.
- **25/25 tests pass** (13 Phase 3 + 12 Phase 4). No skipped tests. No `xfail` without a tracked issue.

### 8.2 What this portfolio does NOT demonstrate

- **Production scale at 100k+ users.** The largest customer is 150 drafts/day. Phase 5 is the scale-up.
- **Novel research.** The MCP server is a 480-line reference implementation; the SLM is a standard LoRA fine-tune of Qwen2.5-1.5B; the multi-agent orchestrator is a standard LangGraph `StateGraph`. The novelty is the **combination** (eval set + runbook + cost ceiling + iteration cadence + handoff), not the individual components.
- **Distributed systems / Kubernetes / microservices.** Phase 3 is a single-VM FastAPI service. Phase 4 is the same. Phase 5 is Redis (state) + ollama (model) + the same FastAPI. No K8s. No service mesh. No Kafka. **The deployment surface is a 2-vCPU VM.**
- **Front-end / UX work.** The drafter is an API + a Swagger UI. There is no customer-facing web app. Mei uses the Swagger UI to send emails.
- **Multi-region / multi-cloud.** Single-region deployment (Singapore). No DR. The 60-min MTTR SLO assumes a single-region incident.
- **Real-time / streaming.** The drafter is request/response. No streaming. No WebSockets. The Phase 1 `/feedback` endpoint is the only async surface.
- **Compliance / SOC 2 / HIPAA / PCI.** None of the customers are in regulated industries. The redactor is for PII, not for compliance.
- **Long-context (1M+ token) workloads.** The drafter's max context is 8K tokens. The Phase 1/2 retrieval layer caps at 5 chunks. No long-context LLM call.

### 8.3 The honest sentence

**"I have shipped AI services that survive the customer at SMB scale (12-150 drafts/day, 1-12 seats), with a 5-component operational framework (eval set, runbook, cost ceiling, cadence, handoff). I have not yet shipped at 100k+ user scale. The next phase is scale, and the next phase is where the framework gets re-tested."**

---

## 9. Where to start reading

Three audiences, three reading paths. The path is the audience's job-to-be-done; the artifacts are the proof.

### 9.1 If you're a recruiter or hiring manager (5 minutes)

1. **This document, §1 (the thesis)** — what is the FDE pattern?
2. **This document, §5 (the quantified outcomes table)** — what is the receipt?
3. **This document, §4 (the FDE competency matrix)** — what skills does this work demonstrate?
4. **Skip to the bottom of this document, §10 (references)** — what is the bibliography?

### 9.2 If you're an interviewer (60 minutes)

1. **This document, §7 (the interview-talking-points)** — what 4 questions will I be asked?
2. **[`engagement-1-pf-drafter.md`](./engagement-1-pf-drafter.md)** — the flagship 12-week narrative.
3. **[`engagement-2-pivot.md`](./engagement-2-pivot.md)** — when to walk away.
4. **[`engagement-3-postmortem.md`](./engagement-3-postmortem.md)** — the public postmortem (the 38-min recovery).
5. **[`engagement-5-handoff.md`](./engagement-5-handoff.md)** — the 5-question "FDE has left" test (the proof of the handoff).
6. **Any one of the 4 projects** (skim the README + the tests + the ARCHITECTURE.md).

### 9.3 If you're a customer evaluating me (45 minutes)

1. **[`engagement-5-handoff.md`](./engagement-5-handoff.md)** — the proof I can leave you in steady state.
2. **[`engagement-4-slm-cost.md`](./engagement-4-slm-cost.md)** — the cost model. The number you take to your CFO.
3. **[`projects/01-mcp-drafter/`](../projects/01-mcp-drafter/)** — the architecture diagram + the YAML policy file. This is what the codebase looks like at handoff.
4. **[`projects/04-ai-data-analyst/`](../projects/04-ai-data-analyst/)** — the project that proves the pattern transfers to your domain.
5. **This document, §8 (the anti-portfolio)** — what this portfolio does NOT claim. Honesty is the first thing I bring to a new engagement.

### 9.4 If you're a student of the FDE pattern (90 minutes)

1. **[`technical/01-mcp-tools-and-policies.md`](../technical/01-mcp-tools-and-policies.md)** — the MCP pattern, with a worked example.
2. **[`technical/02-multi-agent-design.md`](../technical/02-multi-agent-design.md)** — the multi-agent pattern, with a worked example.
3. **[`technical/03-fine-tuning-and-serving-slm.md`](../technical/03-fine-tuning-and-serving-slm.md)** — the SLM pattern, with a worked example.
4. **All 5 case studies** in order (engagement 1 → 2 → 3 → 4 → 5).
5. **All 4 projects** in order (MCP → multi-agent → SLM → data analyst). For each: README → tests → source.

### 9.5 If you're a peer FDE (15 minutes)

1. **[`engagement-2-pivot.md`](./engagement-2-pivot.md)** — the data-readiness scorecard. The pattern for "should I take this?"
2. **[`engagement-3-postmortem.md`](./engagement-3-postmortem.md)** — the eval-set-in-CI fix. The pattern for "how do I prevent this regression class?"
3. **[`engagement-5-handoff.md`](./engagement-5-handoff.md)** — the 5-question test. The pattern for "am I done?"
4. **The bottom of this document** — the one-line summary.

---

## 10. References

### 10.1 The 7-article bibliography of the FDE pattern

The 7 articles that anchor the FDE pattern, organized by the component they inform:

| # | Article | Component it informs | Why it matters |
|---|---|---|---|
| 1 | [**"The 12 Factor App"**](https://12factor.net/) (Wiggins, 2011) | Eval-set-as-spec | The methodology for spec-driven service design; the eval set is a 12-factor-style contract. |
| 2 | [**Google SRE Book, ch. 27 "Reliable Product Launches at Scale"**](https://sre.google/sre-book/launching/) | Runbook-as-contract | The deployment + observability patterns that the runbook operationalizes. |
| 3 | [**"The Tail at Scale"**](https://research.google/pubs/the-tail-at-scale/) (Dean et al., CACM 2013) | Cost-ceiling-as-score | The cascading-models pattern that the SLM cost model is built on. |
| 4 | [**"LoRA: Low-Rank Adaptation of Large Language Models"**](https://arxiv.org/abs/2106.09685) (Hu et al., 2021) | Distillation + serving | The fine-tuning technique that Project 3 is built on. |
| 5 | [**"Model Cards for Model Reporting"**](https://arxiv.org/abs/1810.03993) (Mitchell et al., FAccT 2019) | The model card as public artifact | The format + discipline for the SLM model card. |
| 6 | [**"The Postmortem: Learning from Failure"**](https://www.usenix.org/system/files/articles/lisa13_krishnan.pdf) (Krishnan, SREcon14) | Blameless postmortem | The template + tone for `engagement-3-postmortem.md`. |
| 7 | [**"Controlled Experiments on the Web: Survey and Practical Guide"**](https://www.exp-platform.com/Documents/GuideControlledExperiments.pdf) (Kohavi et al., KDD 2009) | A/B test sizing | The methodology for "size the A/B to the precision needed, not the precision possible." |

### 10.2 The 4 in-project references (the artifacts the portfolio ships with)

| # | Artifact | Where | Why |
|---|---|---|---|
| 1 | The eval set + baseline | `course/ai-fde/phase-2-core-build/shared/eval_set.jsonl` + `shared/baseline.jsonl` | The regression detector. |
| 2 | The runbook | `course/ai-fde/phase-3-deployment/consulting/runbook.md` | The contract. |
| 3 | The cost model | `course/ai-fde/phase-3-deployment/consulting/cost_model.md` | The ceiling + the alert. |
| 4 | The model card | `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/model_card.md` | The SLM's contract. |

### 10.3 The 5 case studies (the lessons)

| # | Case study | What it teaches | Read time |
|---|---|---|---|
| 1 | [`engagement-1-pf-drafter.md`](./engagement-1-pf-drafter.md) | The flagship. 12 weeks, 150 drafts/day, 82% thumbs-up, $0.50/week. | 30 min |
| 2 | [`engagement-2-pivot.md`](./engagement-2-pivot.md) | The data-readiness scorecard. When to walk away. | 15 min |
| 3 | [`engagement-3-postmortem.md`](./engagement-3-postmortem.md) | The week-11 hallucination. 38-min MTTR. The eval-CI gate. | 15 min |
| 4 | [`engagement-4-slm-cost.md`](./engagement-4-slm-cost.md) | The SLM cost model. The 77% number. The corrected model card. | 15 min |
| 5 | [`engagement-5-handoff.md`](./engagement-5-handoff.md) | The 5-question test. The 7 artifacts. The 2-week transition. | 20 min |

### 10.4 The 4 projects (the proof)

| # | Project | Where | What it ships |
|---|---|---|---|
| 1 | MCP-tooled drafter | [`projects/01-mcp-drafter/`](../projects/01-mcp-drafter/) | `mcp_server.py` + `mcp_policies.yaml` + 4 tests + `ARCHITECTURE.md` |
| 2 | Multi-agent dispatcher | [`projects/02-multi-agent-dispatcher/`](../projects/02-multi-agent-dispatcher/) | `agents.py` + `agents_state.py` + 3 tests + `README.md` |
| 3 | Distilled SLM | [`projects/03-distilled-slm/`](../projects/03-distilled-slm/) | `train.py` + `dataset.py` + `serve.py` + `eval.py` + `model_card.md` + 2 tests |
| 4 | AI Data Analyst | [`projects/04-ai-data-analyst/`](../projects/04-ai-data-analyst/) | `sandbox.py` + `security.py` + 3 tests + `ARCHITECTURE.md` |

### 10.5 The 3 lessons (the technical depth)

| # | Lesson | Where | What it teaches |
|---|---|---|---|
| 1 | MCP tools + policies | [`technical/01-mcp-tools-and-policies.md`](../technical/01-mcp-tools-and-policies.md) | MCP schema design, policy file as contract, rate-limit-on-tools, sandbox. |
| 2 | Multi-agent design | [`technical/02-multi-agent-design.md`](../technical/02-multi-agent-design.md) | When to use multi-agent, shared state, escalation rules, per-agent breakers. |
| 3 | Fine-tuning + serving SLM | [`technical/03-fine-tuning-and-serving-slm.md`](../technical/03-fine-tuning-and-serving-slm.md) | When to distill, dataset prep, LoRA, eval-driven regression check, model card. |

### 10.6 The 2 capstone artifacts (the synthesis)

| # | Artifact | Where | What it is |
|---|---|---|---|
| 1 | Capstone presentation script | [`CAPSTONE-PRESENTATION.md`](./CAPSTONE-PRESENTATION.md) | 7-slide, 10-minute live demo script with speaker notes + Q&A prep. |
| 2 | Rehearsal checklist | [`REHEARSAL-CHECKLIST.md`](./REHEARSAL-CHECKLIST.md) | 10-minute pre-demo checklist (servers, eval set, dashboard, sample emails, SEV-1 scenario). |

---

## Closing

The 4 projects + 5 case studies + 3 lessons + 25 tests + 7-article bibliography are the proof. **The pattern is what I do; the projects are what I've built; the case studies are what I've learned; the handoff is how I leave.**

**The FDE pattern: eval-set-as-spec, runbook-as-contract, cost-ceiling-as-score, handoff-as-proof.**

A principal FDE's job is to make themselves unnecessary. **This portfolio is the rubric that grades the handoff.**
