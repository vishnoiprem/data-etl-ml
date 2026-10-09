# AI FDE — Phase 4: Capstone & Mastery

> **Two full projects, five written case studies, a portfolio narrative, and a capstone system demoed live to the evaluation panel.** ~4 weeks of study.

An **AI FDE at the Phase 4 level** can take a Phase 1-3 service and turn it into a **platform** the customer can extend. MCP for tool use. Multi-agent for complex cases. A distilled SLM for cost. A fresh engagement for breadth. The artifact that survives: the case studies + the portfolio + the runbook-from-day-1.

---

## What you will produce by the end of Phase 4

### 4 projects (2 extensions of the PacificFreight drafter + 1 cost play + 1 fresh engagement)

| # | Project | What it proves | What it produces |
|---|---|---|---|
| 1 | **MCP-tooled drafter** | The drafter can call tools (refund, translate, escalate) instead of just generating text | `mcp_server.py` (4 tools + policy file) + `/mcp/tools` endpoint + 4 tests |
| 2 | **Multi-agent dispatcher** | Complex multi-shipment cases route through Mei (CS) + Sarah (ops) + Daniel (infra) sub-agents | `agents.py` (LangGraph ReAct orchestrator) + `/dispatch` endpoint + 3 tests |
| 3 | **Distilled SLM** | A 1.5B model fine-tuned on Mei's 4-week usage.jsonl hits ≥ 90% of GPT-4o-mini's quality at < 10% of the cost | `train.py` + `serve.py` + `eval.py` + `model_card.md` + 2 tests |
| 4 | **AI Data Analyst** | A fresh engagement with a new customer, new domain, new security model (sandboxed code execution) | `sandbox.py` + `security.py` + `/analyst` endpoint + 3 tests |

### 5 case studies

| # | Case study | What it teaches |
|---|---|---|
| 1 | **The full PacificFreight engagement** (Phase 1→2→3→4 narrative) | The flagship case study. "What I'd do differently in week 1." |
| 2 | **A "we said no" PIVOT engagement** (legal-tech / healthcare) | When to walk away. The data wasn't RAG-ready. |
| 3 | **A production incident postmortem** (Week 11 SEV-1 from PF) | Incident response in public. |
| 4 | **The SLM cost model** (Qwen-1.5B at 0.5% cost, 91% quality) | When to distill. The model card as the artifact. |
| 5 | **The FDE handoff** (C3 "FDE has left" test, with names + dates) | Ownership transfer. |

### The portfolio narrative + capstone presentation

- **`PORTFOLIO-NARRATIVE.md`** (3 pp) — a single document that ties the 4 projects + 5 case studies + Phase 1-3 deliverables into a coherent story. The 1-page version goes on LinkedIn; the 3-page version goes to interviews.
- **`CAPSTONE-PRESENTATION.md`** (6 pp) — a 10-minute live demo script (7 slides) for the evaluation panel.
- **`REHEARSAL-CHECKLIST.md`** — the 10-minute pre-demo checklist that turns a demo into a story.

---

## The scenario (continued from Phase 1-2-3)

**Customer:** PacificFreight Co., the 12-person cross-border logistics SMB (Mei, Sarah, Daniel). Continues from `course/ai-fde/phase-2-core-build/scenario-lift.md` (Phase 1→2) and `course/ai-fde/phase-3-deployment/scenario-lift.md` (Phase 2→3).

**End of Phase 3 state:** Mei sends 150 emails/day through the drafter. Thumbs-up 82%. P95 1.8s. Cost $0.50/week. The 3-loop iteration cadence runs every Monday. Daniel owns the VM and the runbook.

**Phase 4 lift:**
- **Project 1 (MCP):** Mei wants to add tools — refund, translate, escalate — without re-deploying.
- **Project 2 (multi-agent):** Mei wants complex multi-shipment cases handled end-to-end without her clicking 5 buttons.
- **Project 3 (SLM):** Daniel wants the bill lower, and the FDE wants the cost ceiling to be scale-invariant.
- **Project 4 (data analyst):** A fresh engagement to prove the FDE pattern transfers.

---

## How to use this directory

```bash
cd course/ai-fde/phase-4-capstone
ls projects/        # 4 self-contained projects
ls case-studies/    # 5 + portfolio + presentation
ls technical/       # 3 lesson .md files (the why)
```

Each project is **self-contained** — it has its own `service/` (or `slm/`) dir, its own tests, its own `README.md`, and its own `ARCHITECTURE.md` (for projects 1 and 4). The shared base (Phase 1-3 service at `course/ai-fde/phase-2-core-build/service/`) is imported via `sys.path` indirection, not `pip install`.

```bash
# Run a project's tests
cd projects/01-mcp-drafter && python3 -m pytest service/tests/ -v

# Run a project's CLI demo
cd projects/02-multi-agent-dispatcher && python3 service/agents.py --case multi_shipment

# Run a project's eval
cd projects/03-distilled-slm && python3 slm/eval.py --baseline ../../phase-2-core-build/shared/baseline.jsonl
```

---

## What this phase is NOT

- **Not Kubernetes, not Terraform, not Helm.** Phase 4 is about extending the AI surface, not the infra surface.
- **Not LangChain / LlamaIndex as a framework dependency.** Patterns are lifted from `course/practice/level-5-agents/` and applied in plain Python (~200-300 lines). A real deployment would use the official packages.
- **Not a 100K-row training run.** The SLM is a LoRA fine-tune of 1.5B params on 1,000 drafts. The lesson is the *pattern*; production would scale up the data and the parameter count.
- **Not a deploy to AWS/GCP.** Phase 4 assumes the Phase 3 VM is still the deployment target. The capstone demo runs on `localhost`.

---

## What survives the FDE's exit

The 4 projects are the work. The 5 case studies are the *lessons*. The portfolio is the *narrative*. The runbook (Phase 3, `../phase-3-deployment/consulting/04-runbook.md`) is the *operational continuity*.

The artifact that goes on the FDE's LinkedIn is `case-studies/PORTFOLIO-NARRATIVE.md` (the 1-page version). The artifact that goes in a job interview is the same file (the 3-page version, with code links). The artifact that goes in the 10-minute live demo is `case-studies/CAPSTONE-PRESENTATION.md` + the running services.
