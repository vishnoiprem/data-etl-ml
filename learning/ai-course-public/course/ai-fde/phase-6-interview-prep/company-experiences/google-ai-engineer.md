# Google — AI Engineer / Customer Engineer (Vertex AI / Gemini)

> Google's AI Engineer / Customer Engineer role is the **Vertex AI + Gemini + BigQuery + data-platform** variant. Unlike Anthropic / OpenAI / Sierra (pure model API), Google's FDE ships **Vertex AI Agents + Gemini + BigQuery + the customer's data warehouse** — they care about the **data plane** as much as the model. The FDE signal: a candidate who can talk about **Vertex AI Agent Engine + BigQuery + Gemini + grounding on the customer's data lake** — is signaling they can own an enterprise AI deployment on GCP.

---

## TL;DR (1 page)

**Google's AI Engineer / Customer Engineer (CE) role** sits between Sales Engineering and Applied AI. The work: ship **Vertex AI Agent Engine + Gemini + BigQuery + grounding on the customer's data warehouse** into a Google Cloud customer (retail, banking, telco). The interview loop tests 4 things: (1) can you design an agent that grounds on BigQuery? (2) can you reason about the **data plane** (BigQuery cost, BigTable throughput, GCS latency)? (3) can you handle the **stakeholder map** (data team, ML team, security team, finance)? (4) can you own the handoff to the customer's data team? The candidate who names the **Vertex AI Agent Engine + grounding + the eval set as the regression check + the BigQuery cost model** — is signaling they can own an enterprise AI deployment on GCP.

---

## Why Google is the right target

The 4 reasons a Google AI Engineer / CE interview is different from a generic FDE loop:

1. **The data plane is the model.** Vertex AI customers care about **where the data lives** (BigQuery, GCS, Bigtable) and **how the agent gets to it** (grounding, retrieval, function calling). The candidate who can talk about BigQuery slots, GCS lifecycle policies, and Bigtable throughput is signaling they understand enterprise data.
2. **Vertex AI is opinionated.** Vertex AI Agent Engine, Vector Search, Model Garden, Gemini. The candidate who names the **Vertex AI Agent Engine for orchestration + Vector Search for retrieval + Gemini for generation + Model Garden for model selection** is showing they know the GCP stack.
3. **The customer is data-rich but AI-poor.** Most Vertex AI customers are enterprises with a data team (BigQuery, Looker) and an ML team (Vertex AI Pipelines, Model Registry). They want AI but they have **legacy data models, slow SQL, and strict IAM**. The FDE has to land AI in that reality.
4. **The agent framework matters.** Vertex AI Agent Engine + LangChain on Vertex + Agent Builder (formerly Gen App Builder). The candidate who names the **Agent Engine's session management + grounding + the eval set as the regression check** is signaling they can ship an enterprise agent.

---

## The Google AI Engineer / CE loop (5-6 rounds)

The typical Google AI Engineer / Customer Engineer loop:

| Round | Format | Duration | Tests |
|---|---|---|---|
| 1. Recruiter | Phone (behavioral + resume) | 30 min | Communication, motivation, Googleyness |
| 2. Coding (technical screen) | Google Docs (collaborative) | 60 min | Algorithms + Python + SQL |
| 3. **Vertex AI Agent Design** (signature) | Live system design | 60 min | Agent orchestration + grounding + data plane |
| 4. **Customer Sim** | Live roleplay | 45 min | Stakeholder handling, scoping, IAM conversation |
| 5. **BigQuery / Data Plane** | Live technical | 60 min | BigQuery, GCS, Bigtable, IAM |
| 6. HM / Behavioral | Final loop | 60 min | Google values + ownership + handoff story |

**Total time-spend:** 5-8 hours over 3-5 weeks. **Pass rate:** 4-6% (most candidates fail the Vertex AI Agent Design round — the grounding + data plane + BigQuery cost is what Google cares about).

---

## The 5 things Google tests that other FDE loops don't

1. **BigQuery cost model.** BigQuery is **slot-based**, not query-based. The candidate who names **slots + reservation + the on-demand vs flat-rate tradeoff** is showing they understand the GCP billing model. The candidate who only knows "BigQuery is fast" is signaling they haven't shipped to enterprise.
2. **Grounding on the customer's data lake.** The customer wants the agent to answer questions about **their** data (sales, churn, fraud). The candidate who names **Vertex AI Vector Search + BigQuery as the data source + the grounding pattern (retrieve → augment → generate)** is showing they understand the data plane.
3. **IAM + VPC-SC + customer-managed encryption keys (CMEK).** Enterprise customers care about who can access what. The candidate who names **IAM roles + VPC Service Controls + CMEK + the audit log** is signaling they understand enterprise security.
4. **The agent lifecycle.** Vertex AI Agent Engine handles **session state, memory, tool calling, evaluation, deployment**. The candidate who names the **Agent Engine's session management + the eval set as the regression check + the staging-to-prod promotion** is showing they can ship a production agent.
5. **The Google values + the data-platform signal.** Google loves data. The candidate who treats the customer's data warehouse as a **first-class artifact** (data quality, freshness, lineage) — instead of just a source for the LLM — is signaling they fit the data-platform culture.

---

## The signature question

> "Design a Vertex AI agent for a retail bank. The agent answers questions about customer accounts (balance, transactions, fraud alerts) by grounding on the bank's BigQuery warehouse. 10K queries/day, 2-second P95 latency, and PCI-DSS compliance. The agent must cite its sources and respect row-level security."

**The FDE answer shape:**

1. **Clarify (5 min):** What's the workload? (10K customer-facing queries/day, grounded on BigQuery, PCI-DSS). What's the latency budget? (2-second P95). What's the compliance boundary? (PCI-DSS — no data leaves the bank's VPC). What's the eval set? (precision + recall on a held-out set of customer questions). What's the timeline? (PoC in 4 weeks; full deploy in 12 weeks).
2. **Decompose (10 min):** Entities (Query, Response, Citation, BigQueryResult, EvalResult). Services (AgentEngine, GroundingService, BigQueryClient, EvalRunner). Flows (customer question → AgentEngine routes → GroundingService queries BigQuery (with row-level security) → LLM generates response with citations → EvalRunner checks faithfulness).
3. **Design (15 min):** API (POST /agent/query returns answer + citations). Data model (queries + responses + citations + eval runs). Deployment (Vertex AI Agent Engine + Gemini + BigQuery as the data source + Vector Search for semantic retrieval + GCS for citation storage). Monitoring (Cloud Monitoring + Cloud Logging + eval-set-as-spec regression check).
4. **Tradeoffs (10 min):** (a) **Vertex AI Agent Engine vs LangChain on Vertex.** Agent Engine is managed and Google-aligned. LangChain is open-source and portable. Pick Agent Engine for Google-aligned deployments. (b) **BigQuery SQL grounding vs Vector Search.** SQL grounding is precise (deterministic). Vector Search is semantic (handles paraphrases). Pick SQL grounding for structured questions ("what was my balance last week?"); pick Vector Search for unstructured questions ("what's the policy on overdraft fees?"). (c) **Gemini 2.0 Flash vs Gemini 2.0 Pro.** Flash is faster and cheaper. Pro is more capable. Pick Flash for 80% of queries; pick Pro for the long-tail 20% that need reasoning.
5. **Closing line:** "For 10K queries/day with 2-second P95 and PCI-DSS, I'd use Vertex AI Agent Engine + Gemini 2.0 Flash + BigQuery as the data source (with row-level security for PCI) + Vector Search for unstructured grounding + citations in every response. The cost is $X/month (BigQuery slots + Agent Engine + Gemini + GCS), under the $X ceiling. The failure mode is hallucination; the mitigation is citations + the eval-set-as-spec regression check. The compliance boundary is the customer's VPC + CMEK + the audit log."

---

## The Google prep plan (8 weeks)

**Weeks 1-2: GCP + Vertex AI literacy**
- Set up a GCP free-tier project. Run a BigQuery query on a public dataset (e.g., `bigquery-public-data.chicago_crime.crime`). **Measure the slot cost** of the query. The candidate who has measured slot cost is signaling they understand BigQuery.
- Deploy a Vertex AI Agent Engine agent that uses Gemini 2.0 Flash + a simple tool (e.g., a weather API). Run the agent end-to-end. Measure the latency.
- Read the Vertex AI Agent Engine documentation. Read the BigQuery documentation (slots, reservations, IAM).

**Weeks 3-4: The data plane + grounding**
- Build a grounding pipeline: a customer's question → BigQuery SQL generation (via Gemini) → BigQuery query (with row-level security) → answer. Validate the SQL on a 100-row eval set.
- Build a Vector Search pipeline: a customer's question → embedding → Vector Search → top-5 chunks → answer. Validate on a 100-row eval set.
- **The canonical artifact:** a `grounding_guide.md` that walks a customer through the BigQuery grounding + Vector Search grounding + the eval set as the regression check.

**Weeks 5-6: The customer sim + decomposition drills**
- Practice 5 customer sims: (a) bank wants PCI-DSS + CMEK + VPC-SC; (b) retailer wants BigQuery + Looker + the agent to respect Looker permissions; (c) telco wants to ground on a 100TB data lake; (d) startup wants Gemini 2.0 Pro for everything and won't pay for Flash; (e) healthcare wants HIPAA + BigQuery + the agent to never log PII.
- Practice 3 decomposition questions: ship an agent grounded on BigQuery, debug a hallucination, scale the agent to 100K queries/day.
- **The closing line:** "For X workload at Y scale with Z constraint, I'd use Vertex AI Agent Engine + Gemini + BigQuery (with row-level security) + Vector Search + citations in every response + the eval set as the regression check. The compliance boundary is the customer's VPC + CMEK + the audit log. The handoff is the grounding_guide.md + the runbook + the on-call rotation."

**Weeks 7-8: Mock loop + STAR rehearsal**
- Mock the 5-round loop with an AI assistant. Time yourself at 60 min per round.
- Rehearse 5 STAR stories: (1) shipped an agent grounded on a customer's BigQuery; (2) handled a PCI-DSS conversation with a bank; (3) debugged a hallucination caused by stale BigQuery data; (4) wrote a grounding guide for a customer; (5) handed off an agent to a customer's data team.

---

## The 5 anti-patterns for Google

1. **Treating BigQuery as "just a database."** BigQuery is **slot-based, columnar, serverless, and integrated with IAM**. The candidate who doesn't mention slots is signaling they haven't shipped to enterprise.
2. **Skipping the grounding story.** The candidate who doesn't mention **BigQuery grounding + Vector Search + the retrieval-augmented generation (RAG) pattern** is signaling they don't understand enterprise AI.
3. **Skipping the IAM / VPC-SC / CMEK story.** The candidate who doesn't mention **row-level security + VPC Service Controls + customer-managed encryption keys** is signaling they don't understand enterprise security.
4. **Skipping the agent lifecycle.** The candidate who doesn't mention **session management + eval set + staging-to-prod promotion** is signaling they don't think about production AI.
5. **Skipping the handoff story.** The candidate who doesn't mention the **handoff artifact (grounding_guide.md + runbook + on-call rotation)** is signaling they don't own the delivery.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you handle row-level security for PCI-DSS?" | "BigQuery row-level access policies. The agent generates SQL that includes the customer_id filter. The IAM policy enforces the filter at the data layer. The agent never sees data it shouldn't." |
| 2. "What if BigQuery is too slow (10-second queries)?" | "BigQuery BI Engine for sub-second queries on frequently-accessed data. Materialized views for aggregations. Reservation scaling for more slots. The latency budget is enforced by the agent's timeout (e.g., 5 seconds), and queries that exceed it fall back to a cached response." |
| 3. "How do you handle data drift in BigQuery?" | "BigQuery column-level lineage + freshness monitoring (Cloud Monitoring). Eval-set-as-spec regression check on a weekly cadence. If the eval metrics drop > 5%, alert the customer's data team." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../system-design/09-agentic-ai.md` | The grounding + retrieval-augmented generation pattern |
| `../system-design/04-distributed-storage.md` | The BigQuery + GCS + Bigtable data plane |
| `../decomposition/README.md` | The 4-step framework applied to a Vertex AI agent |

---

## The thesis

**Google's AI Engineer / Customer Engineer role is the data-plane + Vertex AI + grounding variant.** The candidate who names **Vertex AI Agent Engine + BigQuery grounding + Vector Search + IAM + CMEK + the eval set as the regression check** — is signaling they can own an enterprise AI deployment on GCP.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The signature question — "design a Vertex AI agent for a bank grounded on BigQuery with PCI-DSS" — is the worked example. Practice it out loud, time yourself at 60 minutes, and rehearse with an AI assistant.

**General prep gets you past the resume screen. Google prep gets you past the centerpiece round at Google Cloud Customer Engineering, Vertex AI, and Google Applied AI.**
