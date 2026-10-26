# Scale AI Forward Deployed Engineer — The Data Foundation FDE

> **Source:** Synthesized from the [awesome-generative-ai-guide FDE interview README](https://github.com/aishwaryanr/awesome-generative-ai-guide/blob/main/interview_prep/roles/forward-deployed-engineer/README.md) + the [Sundeep Teki definitive guide](https://www.sundeepteki.org/advice/the-definitive-guide-to-forward-deployed-engineer-interviews-in-2026) + the FDE role taxonomy (Scale AI hires "Forward Deployed Engineer (GenAI)," "Forward Deployed AI Engineer (Enterprise)," and "Forward Deployed Data Scientist," with defense and government + enterprise + GenAI as the three focus areas). **This is the FDE loop for the AI data foundation generation:** the customer is an AI lab, a government agency, or a Fortune 500 building evaluation frameworks, RLHF pipelines, or agent oversight systems, and the test is whether you can ship messy-data-unification + eval-driven iteration + security-adjacent work in a customer's environment. **Best for candidates targeting data-infrastructure FDE roles at AI companies (Scale AI, Labelbox, Surge, Snorkel, Datasaur).**

---

## Why Scale AI is the right target

Scale AI is the canonical "AI data infrastructure" company. The customer is not building an LLM application; the customer is **building the dataset that trains or evaluates the LLM.** The implication for your interview prep:

- **The depth signal is data quality + eval frameworks + RLHF pipelines + messy data unification.** Not "design Twitter." The customer is shipping 1M labeled examples per day; the test is whether you can build the pipeline that ingests, deduplicates, normalizes, and labels them.
- **The customer-simulation round is a government / defense / enterprise stakeholder.** Not a frustrated executive. The customer is a program manager at a federal agency or a data lead at a Fortune 500. The simulation is the procurement-and-compliance-flavored version of the FDE customer sim.
- **The take-home is an eval harness.** Not a service or a notebook. The customer wants to see you build the eval set + the regression check + the cost model that proves the AI system works at scale.
- **The signature differentiator: can you ship a production eval pipeline?** If you can, you can pass any AI-data-infrastructure FDE loop.

Scale AI also has an **Agent Oversight Team** that builds real-time AI agent monitoring for enterprise customers. The FDE on this team ships the dashboard that watches 100K agent conversations per day for hallucination, jailbreak, and quality regression. The test is whether you can build the eval pipeline + the alert + the rollback.

The pattern: **OpenAI / Anthropic test the LLM application layer; Databricks tests the data platform layer; Scale AI tests the AI data infrastructure layer + the eval layer.** The complete FDE candidate pairs all three.

---

## The 3 Scale AI FDE variants (which one are you applying for?)

Scale AI hires 3 distinct FDE variants. The loop varies by variant.

### Variant 1: Forward Deployed Engineer (GenAI)

**Customer:** AI labs building foundation models. The FDE ships the RLHF pipeline, the eval set, the prompt-engineering workflow, and the integration with the lab's training infrastructure.

**The depth signal:** prompt engineering + RLHF + eval-driven iteration + foundation model integration.

**Cross-reference:** `../generative-ai/companion-courses/ed-donner-ai-engineer-core-track.md` (the 8-project cross-reference covers RLHF + eval + fine-tuning).

### Variant 2: Forward Deployed AI Engineer (Enterprise)

**Customer:** Fortune 500 companies deploying AI in production. The FDE ships the RAG pipeline, the agent framework, the eval set, and the integration with the customer's data warehouse.

**The depth signal:** RAG + agents + eval-driven iteration + enterprise security (VPC, SSO, SOC 2, HIPAA).

**Cross-reference:** `../system-design/README.md` § "Pattern 9: Agentic AI systems" + `../take-home/01-prototype.md` (the 4-criteria rubric).

### Variant 3: Forward Deployed Data Scientist (Defense / Government)

**Customer:** Federal agencies (DoD, DoC, intelligence community) and defense primes. The FDE ships the data pipeline, the model training, the eval harness, and the security-compliant deployment.

**The depth signal:** messy data unification + security-adjacent work (FedRAMP, IL5, classified environments) + government procurement + defense-domain knowledge.

**Cross-reference:** `../take-home/02-pipeline.md` (the data-pipeline 4-criteria rubric) + `../behavioral/README.md` § "The 'no experience' answer" (the transferable signal framework).

---

## The loop (4-6 rounds, 3-4 weeks)

The Scale AI FDE loop runs 4-6 rounds over 3-4 weeks. The loop is faster than OpenAI or Anthropic; the bar is "execution velocity" + "messy data unification" + "security-adjacent depth."

### Round 1: Recruiter screen (30 min)

**What they test:** motivation, role fit, customer-facing experience, why Scale AI over a pure ML platform or a pure data-labeling vendor.

**The 3 questions they always ask:**

1. **"Why Scale AI over a pure ML platform like OpenAI or a pure labeling vendor like Labelbox?"** The answer: Scale is the full stack — labeling + eval + fine-tuning + deployment. The FDE ships the entire pipeline, not just one piece. The customer doesn't want 3 vendors; they want one.
2. **"Tell me about a time you worked with messy data."** The answer should name a real project, a real messiness (duplicates, missing labels, schema drift, conflicting ground truth), and a real resolution. Scale AI's customers live in this messiness.
3. **"What's your experience with eval frameworks + RLHF?"** The answer should name a project, a course, a self-built eval set. The candidate who has built an eval set is signaling they understand the core of the FDE pattern.

**The FDE signal:** the candidate who can name a real messy-data project and explain the resolution is showing they can do the work. The candidate who talks about "clean data" generically is not.

**Cross-reference:** `../practical-coding/README.md` (the resume screen + the 5-question cheat sheet).

### Round 2: Technical phone screen (45-60 min)

**What they test:** practical engineering on realistic data + AI problems. The prompt is Scale-AI-flavored:

- **"Here's a 1M-row dataset with 30% duplicate entries and 10% conflicting labels. Write the pipeline that deduplicates, reconciles, and outputs a clean training set."**
- **"Here's a 1000-query eval set for a customer support agent. Write the function that computes tool selection accuracy, response faithfulness, and hallucination rate."**
- **"Here's a customer's RAG pipeline returning wrong answers 20% of the time. Walk me through how you'd debug it."**

**The 3 sub-signals:**

1. **Practical engineering:** the candidate writes working code, not pseudocode. The Scale AI bar is "can you ship this in 2 weeks?"
2. **Data-aware thinking:** the candidate considers duplicates, missing labels, schema drift, conflicting ground truth. The code should look like a data engineer wrote it.
3. **Eval-driven iteration:** the candidate builds the eval set before the fix. The eval set is the spec.

**The 4 anti-patterns:** jump-to-code, skipping-edge-cases, wrong-data-structure, not-testing-the-code. See `../swe-coding/README.md` § "The 4 SWE coding anti-patterns."

**Cross-reference:** `../swe-coding/README.md` (the 8 patterns) + `../practical-coding/README.md` (the 3 AI-assisted sub-rounds).

### Round 3: Take-home or work sample (4-8 hours)

**What they test:** can you ship a working pipeline that handles messy data, with an eval set + a cost model + a handoff runbook? The prompt is Scale-AI-flavored:

- **"Build a data pipeline that ingests 100K rows from a customer (CSV + JSON), deduplicates, normalizes the labels, and outputs a clean training set. Include an eval set of 50 hand-labeled examples + a 4-metric regression check + a cost model + a runbook."**
- **"Build an eval harness for a customer support agent. The agent has 5 tools (lookup, refund, escalate, recommend, translate). Write the eval set + the metric calculation + the cost model."**
- **"Build a RAG pipeline over a customer's 10K internal documents. Include chunking, embedding, retrieval, generation, eval, cost model, and runbook."**

**The 3 sub-signals:**

1. **The 4-criteria rubric:** correctness + observability + cost + handoff. The candidate who ships all 4 is signaling they can do the FDE job. The candidate who ships 2 of 4 is signaling they need coaching.
2. **The eval set as spec:** the candidate builds the 50-row eval set before writing the prompt. The eval set is the contract.
3. **The cost model:** the candidate names $/day, $/month, $/1K queries. The cost ceiling is the litmus test.

**The 4 anti-patterns:** no eval set, no cost tracking, no circuit breaker, no runbook. See `../take-home/01-prototype.md` § "The 5 take-home anti-patterns."

**Cross-reference:** `../take-home/01-prototype.md` (the 4-hour build plan + the 5 most common prompts) + `../take-home/02-pipeline.md` (the data-pipeline variant).

### Round 4: System design / architecture round (60 min)

**What they test:** can you design a real AI system under real Scale-AI-flavored constraints? The prompt is:

- **"Design a private, VPC-deployed RLHF pipeline for a defense customer with IL5 clearance, processing 1M labeled examples per day."**
- **"Design an eval harness for an AI agent that reroutes shipments, targeting 99% on-time delivery."**
- **"Design a real-time AI agent monitoring system for an enterprise customer, watching 100K conversations per day for hallucination, jailbreak, and quality regression."**

**The 3 sub-signals:**

1. **Start from requirements:** IL5 + 1M labels/day + < 24h turnaround + full audit log. The requirements drive the design.
2. **Thin walking-skeleton MVP:** start with the smallest version that meets the constraints. Don't draw a 10-component system diagram in minute 5.
3. **Explicit trade-off picks:** "I picked Spark over Dask because the customer is already on Databricks. I picked Label Studio over Scale's internal UI because the customer's labeling team is already trained on it."
4. **Eval as release infrastructure:** the design includes an eval set + a regression threshold. The eval set is the contract.
5. **Cover security + observability + rollback:** the design includes FedRAMP/IL5, metrics (Datadog or CloudWatch), and a rollback path (the previous version of the pipeline).

**The FDE answer (the canonical Scale AI RLHF pipeline design):**

> "For 1M labels/day under IL5, I'd start with a Spark + Delta Lake pipeline for the ingestion + dedup + normalize layer, Label Studio for the human-in-the-loop labeling UI, and a Ray cluster for the RLHF training + eval layer. The audit log is in Unity Catalog with full lineage tracking. The cost is $15,000/month at the customer's scale (1M labels × $0.005/label × 30 days + 10 GPU nodes × $1,000/month + storage). The failure mode is labeler disagreement; the mitigation is the multi-annotator agreement score + the inter-annotator reliability check."

**Cross-reference:** `../system-design/README.md` § "Pattern 6: Batch processing and data pipelines" + § "Pattern 9: Agentic AI systems."

### Round 5: Ambiguous case / decomposition round (45-60 min) — THE SIGNATURE ROUND

**What they test:** can you scope a vague enterprise problem into a sequenced plan under uncertainty? The prompt is Scale-AI-flavored:

- **"A defense customer says their AI system is 'too unpredictable' for deployment. Figure out what is wrong and propose a plan. Go."**
- **"An AI lab wants to scale their RLHF pipeline from 100K to 10M labels per week without scaling their labeling team linearly. Scope the first 90 days."**
- **"A Fortune 500 customer wants to deploy a customer support agent but their compliance team is blocking the launch. Scope the path from 'no' to 'yes.'"**

**The 3 sub-signals:**

1. **Clarify goal/metric first:** "What does 'too unpredictable' mean? Is it hallucination rate, latency variance, or both? What's the success metric?"
2. **Identify stakeholders + map inputs/gaps:** "The AI lab is the producer; the deployment team is the operator; the compliance team is the gatekeeper. The gap is the lack of an eval set that proves the unpredictability."
3. **Decompose + sequence + propose MVP + surface risks:** "Week 1: build the eval set (1000 hand-labeled examples). Week 2: instrument the eval-driven iteration cadence. Week 3: ship the regression check. Week 4: train the team on the cadence. The risk is the AI lab doesn't have labeling capacity; the mitigation is to bootstrap with synthetic data + human review."

**The FDE answer (the canonical Scale AI decomposition):**

> "For the Fortune 500's compliance-blocked agent launch, the first 90 days are: (1) week 1-2: build the eval set (500 hand-labeled customer queries with ground truth answers + tool selection); (2) week 3-4: ship the eval-driven iteration cadence (every Monday, run the eval set, ship improvements); (3) week 5-6: write the policy file (which user can call which tool, with what rate limit) + the audit log; (4) week 7-8: pilot with 10% of traffic; (5) week 9-12: ramp to 100% with the compliance team watching. The MVP is the eval set + the policy file; the agent is the polish. The risk is the compliance team blocks the pilot; the mitigation is to invite them into the eval set review."

**This round is the differentiator.** Pass rate is ~40%; weight is ~30% of the loop.

**Cross-reference:** `../decomposition/README.md` (the 4-step framework: Clarify → Decompose → Design → Tradeoffs).

### Round 6: Customer simulation round (45-60 min)

**What they test:** can you handle a frustrated or non-technical customer? The customer at Scale AI is a government program manager, a Fortune 500 data lead, or a defense prime's engineering manager. The simulation is the procurement-and-compliance-flavored version of the FDE customer sim:

- **"Your deployment slipped 3 weeks because the customer's security team is slow to provision credentials. I am the customer's program manager. Tell me."**
- **"I want to skip the eval set and ship the model directly to production. Talk me out of it, or do it."**
- **"My labeling team is overworked and missing the 24-hour SLA. I need you to fix it by Friday."**
- **"The defense customer wants the AI system to make autonomous kill-chain decisions. Walk me through how you'd handle that conversation."**

**The 3 sub-signals:**

1. **Diagnose before prescribing:** "Tell me more about the security provisioning process. Is it the customer's team or our team? What's the average wait time?"
2. **Acknowledge before pushing back:** "I understand your team is under pressure. Let me show you why the eval set is worth the 2-week investment."
3. **Offer options with trade-offs:** "Option 1: ship the model without the eval set, save 2 weeks, but the compliance team will block the production launch. Option 2: ship with the eval set, take 2 weeks, but you have the audit log the compliance team needs."
4. **Ownership language without over-promising:** "I'll own the security provisioning escalation. I'll need 48 hours. I can promise that; I can't promise the FedRAMP authorization is done by Friday."

**The FDE answer (the canonical Scale AI customer simulation):**

> "For the autonomous kill-chain question: I understand the operational pressure. The AI system making kill-chain decisions is outside the scope of what Scale AI's safety policy allows us to deploy. I'll redirect the conversation to the customer about the human-in-the-loop pattern: the AI recommends, the human approves. The compromise: I can ship the recommendation system with a 2-week pilot, and we can revisit the autonomy question after the customer has 30 days of eval data."

**Cross-reference:** `../customer-simulation/README.md` (the 9 customer scenarios, the 4 things tested, the 12 specific Q&A).

---

## The 5 things Scale AI tests that other FDE loops don't

1. **Messy data unification.** The candidate who can't deduplicate, normalize, and reconcile conflicting labels loses in Round 2. Study: `../take-home/02-pipeline.md` (the data-pipeline 4-criteria rubric).
2. **Eval framework depth.** The candidate who can't build an eval set with 4 metrics + a regression threshold loses in Round 3. Study: `../take-home/01-prototype.md` § "The 5 most common take-home prompts."
3. **RLHF pipeline design.** The candidate who can't design the Spark + Label Studio + Ray + Unity Catalog pipeline loses in Round 4. Study: `../system-design/README.md` § "Pattern 6: Batch processing and data pipelines."
4. **Government / defense domain knowledge.** The candidate who doesn't know what FedRAMP, IL5, or a CUI marker is loses in Round 5. The defense FDE variant requires security-clearance eligibility (US citizen, no recent foreign travel to certain countries).
5. **Real-time agent monitoring.** The Agent Oversight Team FDE ships the dashboard that watches 100K agent conversations per day. The candidate who can't design the streaming eval pipeline loses. Study: `../system-design/README.md` § "Pattern 2: Event-driven systems" + § "Pattern 7: Real-time and collaborative systems."

---

## The 5 things Phase 1-5 adds (the FDE layer)

1. **The eval-set-as-spec.** Scale AI tests eval frameworks; Phase 1-5 teaches the RAGAS 4 metrics + the 30-row eval set as the contract.
2. **The cost ceiling.** Scale AI tests scale at $X/month; Phase 1-5 teaches the cost model + the circuit breaker + the rate limiter.
3. **The handoff runbook.** Scale AI tests operability; Phase 1-5 teaches the runbook + the "FDE has left" test.
4. **The customer simulation.** Scale AI tests government / defense / enterprise stakeholder handling; Phase 1-5 teaches the 5 customer-simulation scenarios + the 12 specific Q&A.
5. **The decomposition framework.** Scale AI tests the 90-day scoping round; Phase 1-5 teaches the 4-step framework (Clarify → Decompose → Design → Tradeoffs).

---

## The 8-week Scale AI prep plan

| Week | Focus | Activity |
|---|---|---|
| 1 | Messy data unification | Build a 100K-row dataset with 30% duplicates + 10% conflicting labels. Write the dedup + normalize + reconcile pipeline. |
| 2 | Eval framework depth | Build a 1000-query eval set for a customer support agent. Implement faithfulness, ansrel, context_precision, context_recall. Add the regression threshold. |
| 3 | RLHF pipeline design | Sketch the Spark + Label Studio + Ray + Unity Catalog pipeline. Write the ARCHITECTURE.md. Cost model + failure modes + rollback. |
| 4 | Decomposition round | Practice 3 decomposition prompts. Time yourself: 60 minutes per prompt. Use the 4-step framework. |
| 5 | Customer simulation round | Practice 3 customer-sim scenarios (1 government, 1 enterprise, 1 defense). Time yourself: 45 minutes per scenario. |
| 6 | System design round | Practice 3 system design prompts (1 RLHF, 1 eval harness, 1 agent monitor). Time yourself: 60 minutes per prompt. |
| 7 | Coding round | Practice 3 messy-data + AI prompts. Time yourself: 45 minutes per prompt. Use the clarifying-questions-first framework. |
| 8 | Behavioral + handoff | Practice 6-8 STAR stories. Memorize the 5-question cheat sheet. Write the handoff runbook for the dedup pipeline. |

---

## The 5 most useful interview questions this report prepares you for

1. **"Why Scale AI over a pure ML platform or a pure labeling vendor?"** → Answer: Scale is the full stack — labeling + eval + fine-tuning + deployment. The FDE ships the entire pipeline, not just one piece. The customer doesn't want 3 vendors; they want one.
2. **"Design a RLHF pipeline for a defense customer under IL5 with 1M labels/day."** → Answer: Spark + Delta Lake + Label Studio + Ray + Unity Catalog. Cost: $15,000/month. Failure mode: labeler disagreement.
3. **"A Fortune 500's compliance team is blocking the agent launch. Scope the path from 'no' to 'yes.'"** → Answer: (1) eval set, (2) eval-driven cadence, (3) policy file + audit log, (4) pilot, (5) ramp with compliance watching. MVP is the eval set + the policy file.
4. **"Tell me about a time you worked with messy data."** → STAR format. Name the project, the messiness, the resolution, the metric.
5. **"The defense customer wants the AI system to make autonomous kill-chain decisions. Walk me through how you'd handle that conversation."** → Answer: outside the scope of Scale AI's safety policy. Redirect to the human-in-the-loop pattern. Ship the recommendation system first, revisit the autonomy question after 30 days of eval data.

---

## The 5-question "what would the candidate do differently" recap

1. **Build a messy-data pipeline, not a clean-data pipeline.** The Scale AI coding round is messy-data-flavored. Find a real dataset with duplicates + missing labels + conflicting ground truth.
2. **Build a sample eval harness, not a sample RAG pipeline.** The eval harness is the signature deliverable. A working 4-metric eval set is worth 100 hours of reading.
3. **Practice decomposition on Scale-AI-flavored prompts.** The 90-day scoping round is data-infrastructure-specific. Use the 4-step framework.
4. **Read the Scale AI blog + the RLHF paper.** The depth signal is whether you know the data engineering primitives + the RLHF pipeline.
5. **Practice the customer simulation as a government / defense / enterprise stakeholder.** The customer at Scale AI is a program manager, not a CTO. Read the room.

---

## The cross-reference: how this maps to Phase 6

| Round | Phase 6 module | The FDE skill it proves |
|---|---|---|
| 1. Recruiter screen | `../practical-coding/README.md` + `../behavioral/README.md` | Motivation + role fit |
| 2. Technical phone screen | `../swe-coding/README.md` + `../practical-coding/README.md` | Messy data + AI fluency |
| 3. Take-home | `../take-home/01-prototype.md` + `../take-home/02-pipeline.md` | 4-criteria rubric |
| 4. System design | `../system-design/README.md` § "Pattern 6: Batch processing" + § "Pattern 9: Agentic AI" | RLHF + eval harness design |
| 5. Decomposition (signature) | `../decomposition/README.md` | 90-day scoping |
| 6. Customer simulation | `../customer-simulation/README.md` | Government / defense / enterprise stakeholder handling |

---

## The thesis

**The Scale AI FDE loop is the AI-data-infrastructure-deep version of the FDE pattern.** The customer is an AI lab, a government agency, or a Fortune 500, and the test is whether you can ship messy-data-unification + eval-driven iteration + security-adjacent work in a customer's environment. **The complete FDE candidate pairs the OpenAI / Anthropic AI engineering depth with the Databricks data engineering depth and the Scale AI AI-data-infrastructure depth.**

**General prep gets you past the resume screen. Scale-AI-specific prep (messy data + eval frameworks + RLHF pipelines + government / defense domain) gets you past the centerpiece rounds at Scale AI, Labelbox, Surge, Snorkel, and the AI-data-infrastructure FDE loop.**

Sources:
- [awesome-generative-ai-guide FDE interview README](https://github.com/aishwaryanr/awesome-generative-ai-guide/blob/main/interview_prep/roles/forward-deployed-engineer/README.md)
- [The Definitive Guide to Forward Deployed Engineer Interviews in 2026 (Sundeep Teki)](https://www.sundeepteki.org/advice/the-definitive-guide-to-forward-deployed-engineer-interviews-in-2026)