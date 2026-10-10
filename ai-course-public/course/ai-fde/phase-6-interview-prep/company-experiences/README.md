# Module 10 — Real Interview Experiences (what candidates actually saw)

> **The 9 modules in Phase 6 prep you for the 8 interview rounds. This module shows you what the rounds actually look like at specific companies.** Each entry is a real candidate report (with the source attribution), distilled into the 4 questions every FDE candidate cares about: (1) what was the loop? (2) what was the take-home / case study? (3) what did they test? (4) what would the candidate do differently?

---

## Why this module exists

The 9 modules in Phase 6 are general. The reality is: **every company tweaks the loop.** OpenAI's FDE loop is a 1-week take-home + a 1-hour case-study walkthrough + an AI-enabled LeetCode screen. Palantir's loop is decomposition-heavy (the 5 questions, 60 min each). AWS FDE is 5-6 rounds including a customer simulation. Anthropic is 4-5 rounds with a GenAI depth round. **Reading the real reports is the difference between generic prep and company-specific prep.**

The signal in each report: **what the candidate would do differently.** That's the lesson.

---

## The 5 questions every report answers

1. **What was the loop?** (number of rounds, length, who you talked to)
2. **What was the take-home / case study?** (the prompt, the time budget, the deliverables)
3. **What did they test?** (the rubric, the signals, the anti-patterns)
4. **What would the candidate do differently?** (the lesson, distilled)
5. **What's the Phase 6 module that preps it?** (the cross-reference)

## The 12 most useful companies to prep for

Based on the reports in this module, the 12 most useful FDE loops to understand are:

1. **Palantir** — invented the FDE loop. If you can pass Palantir, you can pass any FDE loop. The 4-step framework (Clarify → Decompose → Design → Tradeoffs) is the spine. AI is prohibited; behavioral is embedded in every round.
2. **OpenAI** — the take-home is "basically the job." The AI-enabled coding screen is the new norm. Customer-facing explanation is the differentiator.
3. **Anthropic** — the customer simulation is the highest-signal round. Constitutional AI + Responsible Scaling Policy are testable depth signals. Reference checks happen during the cycle.
4. **AWS FDE** — 6 rounds with a dedicated customer scenario round. The Well-Architected Framework (6 pillars) is the AWS-specific depth signal. Defend the simplest design that meets constraints.
5. **Databricks** — the data-platform FDE loop. Spark + SQL + Delta Lake + Unity Catalog + RAG-over-enterprise-data + MLflow. The signature differentiator: can you do RAG over an enterprise data lake?
6. **Scale AI** — the AI-data-infrastructure FDE loop. Messy data unification + eval frameworks + RLHF pipelines + government/defense/enterprise stakeholders. 3 variants (GenAI, Enterprise, Defense).
7. **Meta** — the open-weight + on-device + safety variant. PyTorch + ONNX + ExecuTorch + Llama Serving. The signature differentiator: can you ship a Llama model to a customer's hardware with the safety eval set as the regression check?
8. **Google** — the data-plane + Vertex AI + grounding variant. Vertex AI Agent Engine + BigQuery grounding + Vector Search + IAM + CMEK. The signature differentiator: can you ground an agent on an enterprise BigQuery data warehouse with PCI-DSS?
9. **Microsoft** — the M365 + Azure OpenAI + Copilot Studio + enterprise variant. Copilot Studio + Azure OpenAI (PTU) + Graph API + M365 audit log + Entra ID. The signature differentiator: can you ship a Copilot that respects M365 permissions with EU data residency?
10. **Stripe** — the payments-infrastructure + AI-for-developers + financial-services variant. Stripe Connect + idempotency keys + ACID + circuit breaker + Stripe Radar. The signature differentiator: can you design a payment flow that never double-charges with the audit log as the contract?
11. **Hugging Face** — the open-source + Hub + transformers + enterprise variant. transformers + PEFT/LoRA + Inference Endpoints + model card + license. The signature differentiator: can you fine-tune an open-weight model on customer data with the eval set as the spec?
12. **LangChain / Sierra AI / Rippling / startups** — take-home-first loops. Sierra's "interviewers run your code before the demo" is the unique differentiator. LangChain's "interview is the job" is the founding-FDE pattern. The 4-step framework + a project deep dive is enough.

**Read at least 3 reports before your loop.** General prep gets you past the resume screen. Company-specific prep gets you past the onsite.

## The 6 most useful FDE signature rounds to prep for

Beyond the 5 most useful companies, the 6 most useful FDE signature rounds to understand are:

1. **Decomposition (Palantir)** — the signature round. The 4-step framework is the spine. Practice out loud.
2. **Take-home demo walkthrough (Sierra AI / LangChain)** — the centerpiece. The eval set is the differentiator.
3. **Customer simulation (AWS FDE / Anthropic)** — the highest-signal round at AWS FDE. Calm under pressure + no overpromising + trade-off explanation.
4. **Constitutional AI / safety depth (Anthropic)** — the disqualifier round. Read the Constitutional AI paper + the Responsible Scaling Policy.
5. **AI-enabled coding screen (OpenAI)** — the new norm. Plan, prompt, and verify — not just the final answer.
6. **Well-Architected Framework system design (AWS FDE)** — the 6 pillars (security / reliability / cost / performance / operational excellence / sustainability) are the testable depth signal.

**Each report in this directory maps to one or more of these signature rounds.** A complete FDE prep covers all 6.

---

## The company-specific reports (1 file per report)

| File | Company | Loop | Lesson |
|---|---|---|---|
| `openai-semantic-search.md` | OpenAI | 1-week take-home + 1-hr case-study + AI-enabled LeetCode | "Don't over-index on hard LeetCode. Practice explaining technical choices in plain English, especially customer-facing." |
| `palantir-fde-decomposition.md` | Palantir | 4 stages: recruiter + technical screen + 3-of-5 onsite (decomposition, learning, coding, re-engineering, system design) + hiring manager | "Practice decomposition out loud. AI is prohibited. Behavioral is embedded in every round." |
| `langchain-deployed-engineer.md` | LangChain | 3 stages: recruiter + 20-min product presentation + build-an-agent take-home with a Slack channel | "The interview is the job. Use every resource they give you (Academy, docs, Slack). Cover ALL product benefits. Be receptive to feedback without ego." |
| `anthropic-fde-customer-simulation.md` | Anthropic | 5 stages: recruiter + tech screen + **customer simulation** (signature) + take-home + system design + HM | "Customer simulation is the highest-signal round. Read Constitutional AI + Responsible Scaling Policy. Reference checks happen during the cycle." |
| `aws-fde-customer-simulation.md` | AWS FDE | 6 rounds: recruiter + phone screen + take-home + coding + system design + **customer scenario** (signature) | "Customer scenario filters the most candidates. Read the Well-Architected Framework (6 pillars). Defend the simplest design that meets constraints." |
| `sierra-ai-agent-engineer.md` | Sierra AI | 5 stages: recruiter + **1-week take-home** (centerpiece) + demo walkthrough + customer simulation + HM | "Interviewers run your code before the demo. Demo in 5-10 min, then defend the choices. Eval set is the differentiator." |
| `databricks-ai-fde.md` | Databricks | 5-6 rounds: recruiter + HM screen + Spark/SQL coding + RAG-over-data-lake system design + decomposition (signature) + data-team customer sim | "The customer is a data team. Practice Spark + Delta Lake + Unity Catalog + MLflow. RAG over enterprise data is the signature question." |
| `scale-ai-fde.md` | Scale AI | 4-6 rounds: recruiter + technical screen + eval-harness take-home + RLHF system design + decomposition (signature) + government/defense customer sim | "3 variants (GenAI, Enterprise, Defense). Messy data unification + eval frameworks + RLHF. The customer is a program manager, not a CTO." |
| `meta-fde-ai-engineer.md` | Meta | 5-6 rounds: recruiter + coding + Llama Deployment (signature) + customer sim + decomposition + HM/behavioral | "Open-weight + on-device + safety. PyTorch → ONNX → ExecuTorch + Llama Guard. The signature question: ship Llama-3-8B to a bank on 2×H100 with 50 ms latency and SOC2." |
| `google-ai-engineer.md` | Google | 5-6 rounds: recruiter + coding + Vertex AI Agent Design (signature) + customer sim + BigQuery/data plane + HM/behavioral | "Data plane + Vertex AI + grounding. BigQuery slots + Vector Search + IAM/CMEK. The signature question: design a Vertex AI agent grounded on BigQuery with PCI-DSS." |
| `microsoft-ai-engineer.md` | Microsoft | 5-6 rounds: recruiter + coding + Copilot/Azure OpenAI Design (signature) + customer sim + Azure data plane + HM/behavioral | "M365 + Azure OpenAI + Copilot Studio + enterprise. PTU + Graph API + M365 audit log + Entra ID. The signature question: design a Copilot for a bank's M365 tenant with EU residency and audit log." |
| `stripe-fde-payments.md` | Stripe | 5-6 rounds: recruiter + coding + Payments System Design (signature) + customer sim + Stripe API deep dive + HM/behavioral | "Payments infrastructure + AI for fraud + financial services. Stripe Connect + idempotency keys + ACID + circuit breaker + Radar. The signature question: design a marketplace payment flow with split-payment + never-double-charge." |
| `huggingface-fde-open-source.md` | Hugging Face | 5-6 rounds: recruiter + coding + Hub + Model Selection (signature) + customer sim + open-source deployment + HM/behavioral | "Open-source + Hub + transformers + enterprise. PEFT/LoRA + Inference Endpoints + model card + license. The signature question: fine-tune a fraud classifier with PEFT/LoRA + deploy on Inference Endpoints + no data leaves AWS." |

**Add a new file per real report you find.** The pattern: copy this README's structure, fill in the 5 questions, link back to the Phase 6 module that preps each round.

---

## How to use this module

1. **Pick your target company.** Read that company's report first.
2. **Read the Phase 6 module that matches each round.** The cross-reference in the report tells you which module to study.
3. **Rehearse the take-home prompt.** The OpenAI semantic-search take-home is in `../take-home/01-prototype.md`; the Labelbox RLHF take-home is in `../take-home/02-pipeline.md`.
4. **Practice explaining choices in plain English.** The OpenAI candidate's #1 tip: "I would spend way more time practicing how to explain technical choices in plain English, especially in a customer-facing context."
5. **Add new reports as you find them.** Each report is a `.md` in this directory. The pattern is the 5 questions above.

---

## The thesis

The 9 modules teach the framework. The 10th module shows you what the framework looks like in the wild. **Reading 3-5 real reports is the difference between "I prepped for FDE interviews" and "I prepped for OpenAI FDE interviews."**

**The 13 FDE signature round → company matrix:**

| Signature round | The company that tests it hardest | Cross-reference |
|---|---|---|
| **Decomposition (90-day scoping)** | Palantir + Databricks + Scale AI (all three) | `../decomposition/README.md` |
| **Customer simulation** | Anthropic + AWS FDE (dedicated round) | `../customer-simulation/README.md` |
| **Constitutional AI / safety depth** | Anthropic (disqualifier round) | `../company-experiences/anthropic-fde-customer-simulation.md` |
| **Well-Architected Framework system design** | AWS FDE | `../company-experiences/aws-fde-customer-simulation.md` |
| **Take-home demo walkthrough** | Sierra AI + LangChain (take-home-first loops) | `../take-home/01-prototype.md` |
| **AI-enabled coding screen** | OpenAI (new norm) | `../practical-coding/README.md` |
| **RAG over enterprise data lake** | Databricks | `../company-experiences/databricks-ai-fde.md` |
| **Eval framework + RLHF pipeline** | Scale AI | `../company-experiences/scale-ai-fde.md` |
| **Open-weight + on-device Llama deployment** | Meta | `../company-experiences/meta-fde-ai-engineer.md` |
| **Vertex AI agent grounded on BigQuery** | Google | `../company-experiences/google-ai-engineer.md` |
| **Copilot grounded on M365 with audit log** | Microsoft | `../company-experiences/microsoft-ai-engineer.md` |
| **Stripe Connect + idempotency + circuit breaker** | Stripe | `../company-experiences/stripe-fde-payments.md` |
| **Hub + PEFT/LoRA + Inference Endpoints** | Hugging Face | `../company-experiences/huggingface-fde-open-source.md` |

**Each company tests a different signature round.** A complete FDE prep covers all 13.

**General prep gets you past the resume screen. Company-specific prep gets you past the onsite.**
