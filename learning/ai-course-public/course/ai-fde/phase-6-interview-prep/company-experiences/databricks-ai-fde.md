# Databricks AI Forward Deployed Engineer — The Lakehouse FDE

> **Source:** Synthesized from the [awesome-generative-ai-guide FDE interview README](https://github.com/aishwaryanr/awesome-generative-ai-guide/blob/main/interview_prep/roles/forward-deployed-engineer/README.md) + the [Sundeep Teki definitive guide](https://www.sundeepteki.org/advice/the-definitive-guide-to-forward-deployed-engineer-interviews-in-2026) + the FDE role taxonomy (Databricks hires "AI Forward Deployed Engineer," remote-eligible). **This is the FDE loop for the data-platform generation:** the customer is a data team migrating to a lakehouse, and the test is whether you can ship RAG-over-Spark + MLflow-tracked evaluations + Unity Catalog governance in the customer's VPC. **Best for candidates targeting data-platform FDE roles at lakehouse companies (Databricks, Snowflake, AWS).**

---

## Why Databricks is the right target

The Databricks FDE loop is the data-engineering-deep version of the FDE pattern. Every other company on this list (OpenAI, Anthropic, Sierra, LangChain, Palantir) hires FDEs whose customers are application developers. **Databricks hires FDEs whose customers are data teams** — the customer is migrating to a lakehouse, unifying their warehouses, building RAG over their data, deploying MLflow pipelines, and the FDE sits in the room with them.

The implication for your interview prep:

- **The depth signal is Spark + SQL + lakehouse + MLflow + Unity Catalog.** Not "design Twitter." The customer is moving petabytes of data into a Delta lake; the test is whether you understand the table format, the streaming semantics, the catalog governance, and the lineage.
- **The customer-simulation round is a data-team stakeholder.** Not a frustrated executive. The customer is a data engineering lead who needs their RAG-over-Spark to return the right chunks while their Unity Catalog is misconfigured and their MLflow experiment tracking is broken.
- **The take-home is a notebook workshop.** Not a CLI or a service. The customer wants to see you work in their environment — Databricks notebooks, Unity Catalog, Spark SQL — not on your laptop.
- **The signature differentiator: can you do RAG over an enterprise data lake?** If you can, you can pass any data-platform FDE loop.

The pattern: **OpenAI / Anthropic test the AI engineering depth; Databricks tests the data engineering depth + AI test on top.** The complete FDE candidate pairs both.

---

## The loop (5-6 rounds, 3-5 weeks)

The Databricks AI FDE loop runs 5-6 rounds over 3-5 weeks. The loop is similar to other AI FDE loops but with a data-engineering overlay on every round.

### Round 1: Recruiter screen (30 min)

**What they test:** motivation, role fit, customer-facing experience, why Databricks over a pure ML platform.

**The 3 questions they always ask:**

1. **"Why Databricks over a pure ML platform like OpenAI or Anthropic?"** The answer: Databricks is where the customer's data lives. The FDE ships AI where the data is, not the other way around. The full-stack RLHF + RAG + MLflow pipeline lives in the lakehouse; the FDE is the one who makes it work.
2. **"Tell me about a time you worked with a data team."** The answer should name a customer team, the data platform they used, the migration you helped with. If you've never worked with a data team, the transferable signal is "I worked with internal stakeholders on a data migration project."
3. **"What's your experience with Spark + SQL + Delta Lake?"** The answer should name a project, a job, a course. If you've never used Spark, the transferable signal is "I'm comfortable with distributed data processing; I'm ramped on Spark + Delta Lake."

**The FDE signal:** the candidate who can name a real data team and a real migration is showing they understand the customer. The candidate who talks about "Python" generically is not.

**Cross-reference:** `../practical-coding/README.md` (the resume screen + the 5-question cheat sheet).

### Round 2: Hiring manager / technical screen (45-60 min)

**What they test:** depth of past work, ownership, technical judgment, individual contribution.

**The 3 sub-signals:**

1. **Past work depth:** a deep dive on one past project. The HM asks "tell me about a project where you owned the data pipeline end-to-end." The signal is the metric (you see this in the behavioral module too).
3. **"I" vs "we":** the HM is testing you, not your team. Use "I" for the action; use "we" for the result. The Databricks FDE rubric is heavily weighted toward individual contribution.
4. **Sequencing judgment:** "tell me about a time you had to choose between two paths." The answer should show that you sequenced correctly (data first, then ML, then application) and explained why.

**The FDE signal:** a candidate who names a real project with a real metric and explains the sequencing judgment is showing they can own a data engagement.

**Cross-reference:** `../behavioral/README.md` § "The 5 question types" (engagement story telling).

### Round 3: Coding round (45-60 min, live or take-home)

**What they test:** practical engineering on realistic data problems. **The prompt is data-platform flavored:** not "reverse a linked list." The prompt is:

- "Here's a Spark DataFrame with 1B rows. Write a query that returns the top-N most-engaged users per day, with the per-user latency under 5 seconds."
- "Here's a Delta Lake table with a schema evolution scenario. Write the merge statement that handles the new column without breaking the downstream pipeline."
- "Here's a 10K-row RAG eval set. Write the function that computes faithfulness, ansrel, context_precision, context_recall. The eval set is the spec."

**The 3 sub-signals:**

1. **Clarifying questions first:** "Is the data partitioned? What's the cluster size? Is the table streaming or batch?" The questions are the signal.
2. **Clean + tested code:** the candidate writes the function, adds 3-5 tests, walks through the edge cases.
3. **Spark-native thinking:** the candidate uses DataFrame operations, not Python loops. The code should look like a Databricks engineer wrote it.

**The 4 anti-patterns:** jump-to-code, skipping-edge-cases, wrong-data-structure, not-testing-the-code. See `../swe-coding/README.md` § "The 4 SWE coding anti-patterns" — the same list applies.

**Cross-reference:** `../swe-coding/README.md` (the 8 patterns cheat sheet) + `../practical-coding/README.md` (the AI-assisted sub-rounds).

### Round 4: System design / architecture round (60 min)

**What they test:** can you design a real AI system under real data-platform constraints? The prompt is data-lake-flavored:

- **"Design a private, VPC-deployed RAG system for a healthcare customer with HIPAA constraints over 50 million documents."**
- **"Design an evaluation harness for an AI agent that reroutes shipments, targeting 99% on-time delivery."**
- **"A naive RAG endpoint returns in 1.5 seconds. Get it under 100ms. What do you change?"**
- **"Design a Spark + Delta Lake + Unity Catalog pipeline that ingests 100TB/day, with full lineage tracking and per-tenant access control."**

**The 3 sub-signals:**

1. **Start from requirements:** HIPAA + 50M docs + < 100ms latency + per-tenant access. The requirements drive the design.
2. **Thin walking-skeleton MVP:** start with the smallest version that meets the constraints. Don't draw a 10-component system diagram in minute 5.
3. **Explicit trade-off picks:** "I picked Delta Lake over Iceberg because Unity Catalog is the governance primitive and the customer is already on Databricks." The trade-off is the signal.
4. **Eval as release infrastructure:** the design includes an eval set + a regression threshold. The eval set is the contract.
5. **Cover identity, observability, rollback:** the design includes auth (the customer's IdP), metrics (Datadog or CloudWatch), and a rollback path (the previous version of the pipeline).

**The FDE answer (the canonical Databricks RAG-over-Spark design):**

> "For 50M docs in a healthcare customer's VPC under HIPAA, I'd start with Delta Lake + Unity Catalog for the storage and governance, Spark + MLflow for the batch indexing pipeline, and a hybrid retriever (BM25 + dense + RRF) for the online search. The embedding model is OpenAI text-embedding-3-large behind a private endpoint (VPC peering to the customer's IdP). The RAG eval set is 500 hand-labeled queries with faithfulness / ansrel / context_precision / context_recall. The cost is $2,000/month at the customer's scale (50M docs × 1.5KB/chunk × 1536 dims × $X/GB-month storage + 0.3 cents per query). The failure mode is retrieval drift; the mitigation is the eval-set-as-spec regression check."

**Cross-reference:** `../system-design/README.md` § "Pattern 9: Agentic AI systems" + § "Pattern 4: Distributed data storage" (the RAG-over-data-lake case).

### Round 5: Ambiguous case / decomposition round (45-60 min) — THE SIGNATURE ROUND

**What they test:** can you scope a vague enterprise problem into a sequenced plan under uncertainty? The prompt is data-platform flavored:

- **"A logistics customer says their ops team cannot trust the dashboard. Figure out what is wrong and propose a plan. Go."**
- **"A regional bank wants to unify fraud detection across three legacy acquired systems with inconsistent labels. Scope the first 90 days."**
- **"A healthcare network wants to deploy a clinical RAG system over 8M patient records with HIPAA + audit log + per-physician access. Propose the architecture and the first 2 weeks."**

**The 3 sub-signals:**

1. **Clarify goal/metric first:** "What does 'trust the dashboard' mean? Is it stale data, wrong numbers, missing lineage, or all three? What's the success metric?"
2. **Identify stakeholders + map inputs/gaps:** "The ops team is the consumer; the data engineering team is the producer; the compliance team is the gatekeeper. The gap is the lack of data contracts between producer and consumer."
3. **Decompose + sequence + propose MVP + surface risks:** "Week 1: build the data contract. Week 2: instrument the lineage. Week 3: ship the eval set for the dashboard. Week 4: train the ops team on the eval-driven iteration cadence. The risk is the producer team is overcommitted; the mitigation is to scope to one product line first."

**The FDE answer (the canonical Databricks decomposition):**

> "For the regional bank's fraud unification, the first 90 days are: (1) week 1-2: data audit + label reconciliation across the 3 legacy systems (which labels are ground truth, which are noisy, which conflict); (2) week 3-4: build a feature store in Unity Catalog with the canonical fraud label as the source of truth; (3) week 5-8: ship the eval set (500 labeled fraud cases) + the RAGAS-style regression check; (4) week 9-12: train the fraud team on the eval-driven iteration cadence. The MVP is the data contract + the eval set; the dashboard is the polish. The risk is the bank's 3 legacy systems have inconsistent customer identifiers; the mitigation is to build the canonical ID resolver first."

**This round is the differentiator.** Pass rate is ~40%; weight is ~30% of the loop. The candidate who can scope, decompose, sequence, and surface risks in 60 minutes is signaling they can own an FDE engagement.

**Cross-reference:** `../decomposition/README.md` (the 4-step framework: Clarify → Decompose → Design → Tradeoffs).

### Round 6: Customer simulation round (45-60 min)

**What they test:** can you handle a frustrated or non-technical customer? The customer at Databricks is a data engineering lead, not a CTO. The simulation is the data-team-flavored version:

- **"Your deployment slipped 3 weeks. I am the customer's data engineering lead. Tell me."**
- **"I want to disable Unity Catalog governance so my team can move faster. Talk me out of it, or do it."**
- **"My security team will not give you production credentials. Now what?"**
- **"The Spark job is taking 6 hours and the customer wants it under 30 minutes. The customer is asking if we can just throw more money at it."**

**The 3 sub-signals:**

1. **Diagnose before prescribing:** "Tell me more about what changed in the last 3 weeks. Did the scope change? Did the data volume change? Did the customer's team change?"
2. **Acknowledge before pushing back:** "I understand the governance is slowing you down. Let me show you why it's worth the investment." Don't start with "you're wrong."
3. **Offer options with trade-offs:** "Option 1: keep Unity Catalog, add 2 more admins, ship in 2 weeks. Option 2: bypass Unity Catalog, ship in 1 week, but you lose the audit log and your compliance team will block the production launch."
4. **Ownership language without over-promising:** "I'll own the rollback plan. I'll need 48 hours. I can promise that; I can't promise the new feature ships by Friday."

**The FDE answer (the canonical Databricks customer simulation):**

> "For the Unity Catalog bypass question: I understand your team is moving fast. The Unity Catalog governance isn't a tax; it's the audit log your compliance team will demand for the SOC 2 audit in Q3. If we bypass it now, the audit fails in 6 months and your data team is the one rebuilding the catalog under pressure. The compromise: I'll add 2 more admin accounts (you have the credentials), and I'll write a quick-start guide so your team can register tables in 5 minutes instead of 30. The bypass saves you 1 week now and costs you 6 weeks in 6 months."

**Cross-reference:** `../customer-simulation/README.md` (the 9 customer scenarios, the 4 things tested, the 12 specific Q&A).

### Round 7 (optional): Behavioral / mission alignment round (45-60 min)

**What they test:** ownership, ambiguity tolerance, conflict, mission alignment. 6-8 STAR stories, 60-90 seconds each. "I" not "we."

Databricks's mission alignment is "the data + AI platform." The candidate should be ready to answer:

1. **"Why Databricks over a pure ML platform?"** → See Round 1.
2. **"What's your experience with the lakehouse pattern?"** → Name a project.
3. **"Tell me about a time you had to ship a data product under a tight deadline."** → STAR with a metric.

**Cross-reference:** `../behavioral/README.md` (the 3 question types, the STAR format, the 5-question cheat sheet).

---

## The 5 things Databricks tests that other FDE loops don't

1. **Spark + SQL fluency.** The candidate who can't write a Spark DataFrame query loses in Round 3. Study: `../swe-coding/README.md` § "Pattern 5: Graphs" (the DataFrame operations are graph operations under the hood) + `../decomposition/README.md` § "The 3 lists" (entities, services, flows — translated to tables, queries, pipelines).
2. **Delta Lake + Unity Catalog governance depth.** The candidate who doesn't know what a Delta table is loses in Round 4. The catalog + the lineage is the differentiator.
3. **RAG over enterprise data.** Round 4's signature prompt. The candidate who can't design RAG-over-Spark loses. Study: `../system-design/README.md` § "Pattern 9: Agentic AI systems."
4. **Data team stakeholder handling.** Round 6's customer is a data lead, not an executive. The candidate who treats the data lead as an executive is signaling they can't read the room.
5. **MLflow + eval-driven iteration.** The candidate who doesn't know what MLflow is loses in the take-home. The eval-driven iteration cadence is the litmus test.

---

## The 5 things Phase 1-5 adds (the FDE layer)

1. **The eval-set-as-spec.** Databricks tests MLflow + eval-driven iteration; Phase 1-5 teaches the RAGAS 4 metrics + the 30-row eval set as the contract.
2. **The cost ceiling.** Databricks tests scale at $X/month; Phase 1-5 teaches the cost model + the circuit breaker + the rate limiter.
3. **The handoff runbook.** Databricks tests operability; Phase 1-5 teaches the runbook + the "FDE has left" test.
4. **The customer simulation.** Databricks tests data-team stakeholder handling; Phase 1-5 teaches the 5 customer-simulation scenarios + the 12 specific Q&A.
5. **The decomposition framework.** Databricks tests the 90-day scoping round; Phase 1-5 teaches the 4-step framework (Clarify → Decompose → Design → Tradeoffs).

---

## The 8-week Databricks prep plan

| Week | Focus | Activity |
|---|---|---|
| 1 | Spark + Delta Lake fundamentals | Take the free Databricks Spark + Delta Lake course. Build a 100-row RAG eval set in Databricks notebooks. |
| 2 | Unity Catalog + MLflow | Set up a Unity Catalog with 3 schemas, 5 tables, and full lineage tracking. Run an MLflow experiment with 10 model variants. |
| 3 | RAG over enterprise data | Build a RAG pipeline over a sample Delta Lake table. Eval with the 4 RAGAS metrics. Cost model + circuit breaker. |
| 4 | Decomposition round | Practice 3 decomposition prompts. Time yourself: 60 minutes per prompt. Use the 4-step framework. |
| 5 | Customer simulation round | Practice 3 customer-sim scenarios. Time yourself: 45 minutes per scenario. Use the diagnose → acknowledge → offer → own framework. |
| 6 | System design round | Practice 3 system design prompts. Time yourself: 60 minutes per prompt. Use the 4-step framework. |
| 7 | Coding round | Practice 3 Spark + SQL prompts. Time yourself: 45 minutes per prompt. Use the clarifying-questions-first framework. |
| 8 | Behavioral + handoff | Practice 6-8 STAR stories. Memorize the 5-question cheat sheet. Write the handoff runbook for the sample RAG pipeline. |

---

## The 5 most useful interview questions this report prepares you for

1. **"Why Databricks over a pure ML platform?"** → Answer: Databricks is where the customer's data lives. The FDE ships AI where the data is, not the other way around. The full-stack RLHF + RAG + MLflow pipeline lives in the lakehouse; the FDE is the one who makes it work.
2. **"Design a RAG-over-Spark pipeline for a HIPAA customer with 50M docs."** → Answer: Delta Lake + Unity Catalog + Spark + MLflow + hybrid retriever + RAGAS eval set. Cost: $2,000/month. Failure mode: retrieval drift.
3. **"The ops team can't trust the dashboard. Scope the first 90 days."** → Answer: (1) data audit + label reconciliation, (2) feature store in Unity Catalog, (3) eval set + regression check, (4) train the team on the cadence. MVP is the data contract + the eval set.
4. **"Tell me about a time you worked with a data team."** → STAR format. Name the team, the platform, the migration, the metric.
5. **"I want to disable Unity Catalog governance so my team can move faster."** → Answer: I understand your team is moving fast. The governance is the audit log your compliance team will demand. The compromise: add more admins, write a quick-start guide.

---

## The 5-question "what would the candidate do differently" recap

1. **Practice Spark + SQL, not just Python.** The Databricks coding round is Spark-flavored. Build a sample Delta Lake table and run 20 Spark queries.
2. **Build a sample RAG-over-Delta pipeline.** The RAG-over-enterprise-data prompt is the signature question. A working pipeline is worth 100 hours of reading.
3. **Practice decomposition on data-flavored prompts.** The 90-day scoping round is data-platform-specific. Use the 4-step framework.
4. **Read the Databricks blog + the Delta Lake paper.** The depth signal is whether you know the data engineering primitives.
5. **Practice the customer simulation as a data lead, not an executive.** The customer at Databricks is a data engineering lead, not a CTO. Read the room.

---

## The cross-reference: how this maps to Phase 6

| Round | Phase 6 module | The FDE skill it proves |
|---|---|---|
| 1. Recruiter screen | `../practical-coding/README.md` + `../behavioral/README.md` | Motivation + role fit |
| 2. HM screen | `../behavioral/README.md` § "Type 1: Customer interaction" | Past work depth |
| 3. Coding round | `../swe-coding/README.md` + `../practical-coding/README.md` | Spark + SQL fluency |
| 4. System design | `../system-design/README.md` § "Pattern 9: Agentic AI systems" | RAG-over-data-lake design |
| 5. Decomposition (signature) | `../decomposition/README.md` | 90-day scoping |
| 6. Customer simulation | `../customer-simulation/README.md` | Data-team stakeholder handling |
| 7. Behavioral | `../behavioral/README.md` | STAR + metric |

---

## The thesis

**The Databricks AI FDE loop is the data-engineering-deep version of the FDE pattern.** The customer is a data team, not an application developer. The test is whether you can design a RAG-over-Spark pipeline, scope a 90-day data engagement, and handle a data-team stakeholder. **The complete FDE candidate pairs the OpenAI / Anthropic AI engineering depth with the Databricks data engineering depth.**

**General prep gets you past the resume screen. Databricks-specific prep (Spark + Delta Lake + Unity Catalog + MLflow + RAG-over-data-lake) gets you past the centerpiece rounds at Databricks, Snowflake, AWS, and the data-platform FDE loop.**