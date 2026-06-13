# Study Guide — Senior Data Engineer, Product Analytics, Payments (Google Singapore / TSC)

> Built from the actual job description. This role is on the **Technical Solutions Consultant (TSC)** ladder and is **AI/ML-heavy** — it expects classic data engineering (the floor) PLUS agentic/LLM analytics systems (the differentiator). Your scheduled "Code Comprehension & Programming" round tests the foundation; the AI/agentic topics matter for later rounds and to stand out. **Confirm with your recruiter how much of the loop is agentic/LLM vs. core DE.**

---

## HOW THE JOB DESCRIPTION MAPS TO STUDY PRIORITIES

| From the JD | What to study | Priority |
|-------------|---------------|----------|
| 5 yrs Python + SQL | Core coding round (your scheduled round) | **P0 — must master** |
| Designing/deploying data pipelines, schemas, volume workflows | Pipeline & data architecture | **P0** |
| ML operations + data architecture design | MLOps basics, data platform design | **P1** |
| "Agentic analytics systems leveraging LLMs" | Agent Development Kit (ADK), agentic workflows | **P1 — the differentiator** |
| Gemini CLI, Cider Agents, LLM Extensions, ADK Agents | Google's agent tooling | **P1** |
| "AI-native analytics workflows" | LLM-in-the-loop analytics patterns | **P1** |
| Data quality, reliability, governance | Data governance concepts | **P2** |
| Partnering with stakeholders, ambiguity, influence | Behavioral / Googleyness | **P1** |
| Payments domain | Payments data basics (fraud, money movement, reconciliation) | **P2** |

---

## TIER P0 — CORE FOUNDATION (your scheduled round; non-negotiable)

### SQL
- Window functions, partitioning, aggregations, joins, **time-series analysis**, edge-case handling.
- Practice: https://datalemur.com  ·  https://www.hackerrank.com/domains/sql (advanced)  ·  https://stratascratch.com
- Reference: https://mode.com/sql-tutorial/

### Python (DSA, data-flavored)
- Arrays, strings, dictionaries, sets; reshaping input into the right structure; time/space complexity.
- Practice: https://leetcode.com (Easy/Medium, Arrays & Hashing)  ·  https://neetcode.io/practice (Arrays, Two Pointers, Sliding Window, Stack, Intervals)
- Code comprehension format (output / complexity / improve): use your own drill doc.

### Data pipelines & schemas
- ETL vs ELT, batch vs streaming, idempotency, late-arriving data, schema evolution, partitioning.
- Reference: *Fundamentals of Data Engineering* (Reis & Housley); https://www.startdataengineering.com/

---

## TIER P1 — THE AI / AGENTIC DIFFERENTIATOR (what makes THIS role unique)

### 1. Agent Development Kit (ADK) — most specifically named skill
ADK is Google's open-source framework to build, evaluate, and deploy AI agents. Core primitives: **Agent** (LlmAgent for reasoning; workflow agents — SequentialAgent, ParallelAgent, LoopAgent — for deterministic control) and **Tool** (lets agents call APIs, search, run code, or call other agents). Strengths: multi-agent hierarchies, rich tool ecosystem, flexible orchestration. Python 2.0 is GA with a graph-based Workflow Runtime (routing, fan-out/fan-in, loops, retry, human-in-the-loop) and a Task API for agent-to-agent delegation.
- **Official docs:** https://google.github.io/adk-docs/
- **Homepage:** https://adk.dev/
- **About / technical overview:** https://google.github.io/adk-docs/get-started/about/
- **GitHub (Python, code-first):** https://github.com/google/adk-python

### 2. Gemini Enterprise Agent Platform + Agents CLI (deployment layer)
Where ADK agents get deployed and managed. Agents CLI is a unified interface for the full agent lifecycle (build → evaluate → deploy to Google Cloud, e.g. Cloud Run).
- **Quickstart (ADK + Agents CLI):** https://docs.cloud.google.com/gemini-enterprise-agent-platform/agents/quickstart-adk
- **Build with ADK overview:** https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk

### 3. Hands-on labs (DO these — speaking from experience beats theory)
- **Build a Google Docs fact-checking agent with ADK** (multi-step reasoning, google_search tool, structured JSON output, deploy + integrate): https://codelabs.developers.google.com/google-docs-adk-agent
- **Google partner skills ADK lab** (agents, tools, sessions, dynamic models): https://partner.skills.google/focuses/125064

### 4. Conceptual frame for agentic workflows
An agent is anything callable that fulfills a purpose (an LLM call, an orchestrator, or a custom function). The core idea: split a big task into smaller specialized agents that call each other — this beats handing one model a single huge task. **For this role, map it to analytics:** an agent that profiles data → one that writes/validates SQL → one that interprets results → one that drafts the narrative, orchestrated together.
- Deep dive (concepts, basic→advanced + case study): https://medium.com/@kamilmatejuk/deep-dive-into-googles-agent-development-kit-73995c803c2d

### 5. Gemini / GenAI on Google Cloud (the model layer under ADK)
- **Vertex AI Generative AI overview:** https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview
- **Gemini API docs:** https://ai.google.dev/gemini-api/docs
- **Prompting / function calling (tool use):** https://ai.google.dev/gemini-api/docs/function-calling
- **Cloud Skills Boost — GenAI learning path:** https://www.cloudskillsboost.google/paths/118

### 6. MLOps for production workflows (a minimum qual)
- **Vertex AI MLOps overview:** https://cloud.google.com/vertex-ai/docs/start/introduction-mlops
- Concepts to know: feature stores, model serving, monitoring/drift, CI/CD for ML, pipelines (Vertex AI Pipelines / Kubeflow).

### Talking points to be fluent in (for system-design + later rounds)
- How you'd design an **agentic analytics system** (multi-agent: ingest → model → query → interpret → narrate).
- **LLM-in-the-loop data quality / governance** — validation, guardrails, evals, human-in-the-loop.
- **When an LLM agent helps vs. when a deterministic pipeline is safer** (great trade-off discussion).
- How you'd **evaluate** an agent's output (correctness, hallucination checks, eval sets).

---

## TIER P2 — SUPPORTING CONTEXT

### Data governance & quality
- Freshness, completeness, accuracy, lineage, reconciliation; data contracts.
- Reference: https://cloud.google.com/dataplex/docs (data governance on GCP)

### GCP data stack (lean on concepts if you're from AWS/Azure — they transfer)
- **BigQuery** (partitioning, clustering, architecture): https://cloud.google.com/bigquery/docs/introduction
- **Dataflow** (Apache Beam, batch + stream): https://cloud.google.com/dataflow/docs
- **Pub/Sub** (messaging/streaming): https://cloud.google.com/pubsub/docs/overview

### Payments domain basics (nice-to-have context)
- Money movement, reconciliation, fraud/risk signals, idempotency in payment events, PCI/sensitive-data handling.

---

## SUGGESTED READING ORDER (given a tight timeline)
1. **P0 daily drills** — SQL + Python (this is your scheduled round; protect this time).
2. **ADK About + homepage** — get the vocabulary (1–2 hrs): adk.dev + the About page.
3. **Do the Google Docs ADK codelab** — hands-on, so you can speak from experience (half a day).
4. **Skim Vertex AI GenAI overview + function calling** — the model/tool-use layer (1–2 hrs).
5. **Skim Vertex AI MLOps overview** — enough to discuss production ML (1 hr).
6. **Prepare 4–5 talking points** on agentic analytics design + LLM-in-the-loop governance.
7. **Confirm scope with your recruiter** — how much of the loop is agentic/LLM vs. core DE.

---

## ONE-LINE SUMMARY
Master Python + SQL (your scheduled round), then layer on **ADK / agentic analytics + Gemini + MLOps** — that AI-native layer is what this specific Payments Analytics TSC role is really about, and what will set you apart.
