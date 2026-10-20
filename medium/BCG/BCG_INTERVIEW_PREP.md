# BCG PLATINION — DATA & AI ARCHITECTURE: WHO PASSES, WHO FAILS, WHAT TO SAY (20 Oct 2026)

> **Role (from recruiter Pearson Carter brief):** BCG Platinion, Data & AI Architecture, Southeast Asia. Hiring Manager → Director, preference for **Senior Manager (L3), Principal / Lead Principal (L4), Director**. Sectors: Banking, Insurance, Energy, Industrial Goods, Telco. Skills: Data & AI, Enterprise Architecture, legacy modernisation, cloud, tech strategy, **AWS, Databricks, GenAI/OpenAI**. Wants: strong communicator, C-suite comfort, technically credible + commercially minded, can anchor and lead engagements, writes executive briefs.
> Interview process for this role is not public — the structure below is inferred from the brief and typical BCG practice. Not confirmed.

## A. Fit scorecard (honest, from your CV)
| Requirement in brief | Your evidence | Status |
|---|---|---|
| Data & AI | Databricks lakehouse 10B+ rows/day, production GenAI (Text-to-SQL), ML (pricing, forecasting) | ✅ Strong |
| AWS, Databricks | AWS SA Associate (Dec 2023), Databricks at Makro | ✅ Strong |
| GenAI / OpenAI | Chat-with-Data, RAG, agentic AI certificate | ✅ Good |
| Banking sector | Standard Chartered AML (15+ countries), DBS, PayPal | ✅ Strong |
| Legacy modernisation | Hadoop/Hive → lakehouse at SCB/DBS/PayPal; legacy → Databricks at Makro | ✅ Good (have 2 stories ready) |
| C-suite comfort | Executive dashboards for CEO/CFO/COO; stakeholders to CEO/CIO/CDO | 🟡 Good, needs a named story |
| Enterprise Architecture | Designed platforms, but **no EA framework / certification (TOGAF)**, no enterprise-wide target-state work named | 🟠 Gap |
| Technology consulting background / top-tier firm | **None** — all in-house | 🔴 Biggest gap |
| Insurance, Energy, Industrial, Telco | None named | 🟠 Gap (retail/e-commerce/banking only) |
| Anchor and lead engagements, commercial sense | Led teams and budget ($3M), not billable client engagements | 🟠 Gap |
| Executive briefs | Medium writing helps; need a sample one-pager | 🟡 Prepare |

**Level reality:** best fit **Senior Manager / Principal (L3–L4)**. Director would need proof you can win and lead client engagements — a stretch without consulting history. Ask the recruiter which level they're submitting you for; don't claim Director in the interview unless they offer it.

## B. Who succeeds / who fails at this interview
**Succeeds**
- Talks like an advisor: answer first, structure, trade-offs, a recommendation and a next step.
- Shows architecture **and** business value (cost, risk, time-to-value) in every answer.
- Has 3 crisp client-style stories with numbers (modernisation, GenAI in production, executive influence).
- Admits gaps calmly ("I haven't worked in Telco; the pattern I'd apply is…").
- Asks sharp questions about the client problem before solving.
- Brings a one-page executive brief example.

**Fails**
- Answers like an engineer: tools and details, no business "so what".
- Rambles; no structure; can't summarise in 30 seconds.
- Claims consulting or EA experience they can't evidence; bluffs on sectors.
- Pitches as a hands-on builder only ("I'm a Head of Data Engineering, hands-on") when the role is advisory-leading.
- Over-sells numbers or can't explain the baseline (e.g. the 40% cost cut appears under Makro and Xendit — expect a probe).
- Criticises previous employers or the client's legacy.
- Doesn't link tech to the client's regulators and operating model.
- Weak on "why consulting, why BCG Platinion, why now".

## C. Answers that make you pass (use these)

**1. Why consulting / why BCG Platinion?**
> "I've built data and AI platforms inside one company at a time, in banking and in retail. What I'm missing is applying that across industries at the C-suite level, with the architecture and the change leadership together. Platinion sits exactly there: architecture that is tied to business outcomes. I bring fifteen years of building, so my advice comes from having done it."

**2. Tell me about yourself (60 sec).**
> "Fifteen years in data and AI architecture. I started in banking at Standard Chartered and DBS, building audit-grade AML data platforms across 15 countries. At Lazada I led the data platform at consumer-internet scale. Today at Makro I own the data and AI platform for an $8B business across three countries: a Databricks lakehouse at 10 billion rows a day, month-end close from five days to two hours, and production GenAI. I'm now looking to advise senior clients on the same problems, with architecture and delivery together."

**3. How would you approach a legacy modernisation for a bank?**
> "Don't big-bang. First inventory by workload and retire what nobody uses, typically 20–30%. Then rehost, refactor or retain by regulatory and latency constraints. Dual-run and reconcile before cutover, because the real risk is an unexplained regulatory number. Be upfront with the CFO that dual-run costs more for a period. Target: open table formats, governed catalog, CDC instead of nightly loads."

**4. Design an enterprise Data & AI architecture for a bank or insurer.**
Structure aloud: **business outcomes → capabilities → platform (ingest, store, serve, govern) → AI layer (features, models, GenAI with guardrails) → operating model → roadmap and cost**. Close: "I'd sequence by value: one high-pain domain in a quarter, then scale. The 10-20-70 rule applies — most of the effort is adoption."

**5. GenAI in a regulated client — what do you do?**
> "Start with a use case that has a measurable decision, ground the model on governed data with retrieval and citations, add PII controls, human-in-the-loop for high-risk outputs, evaluation before launch, and monitoring for cost and drift. The data foundation matters more than the model."

**6. How do you influence a CEO / CFO?**
> "Lead with the answer, use their numbers, show two or three options with trade-offs, recommend one, and ask for the decision. At Makro I took month-end close from five days to two hours by showing the CFO the cost of delay and the controls that made automation safe."

**7. What if you've never worked in Energy / Telco / Insurance?**
> "The data patterns repeat: customer, transaction, asset, risk. In banking and retail I've solved the same ones — entity resolution, real-time events, regulatory lineage. I'd pair with a sector expert for the domain and bring the architecture."

**8. Why are you leaving a Head role for this?**
> "I want broader impact and exposure to more industries, and I want to advise at executive level while staying technically credible. This role combines both."

**9. Biggest weakness / gap?**
> "I haven't worked inside a consulting firm. I compensate by being structured, outcome-led and used to C-suite stakeholders, and I'd lean on the firm's frameworks while I learn commercial engagement leadership."

**10. Commercial question: how would you scope and price a data platform engagement?**
> "Define the decision and success metric, phase it (discover, pilot, scale), price the pilot fixed and the scale-up on outcomes, protect margin with clear assumptions, and always tie to client business value."

## D. Prepare before the screen
- [ ] **Reply to Pearson Carter yourself** (consent to submit, updated CV). Tell them truthfully if your CV went to BCG in the last 12 months. I haven't replied for you.
- [ ] Ask the recruiter: target level, sectors, interview stages, who interviews, travel, location (Singapore?), compensation range.
- [ ] Update the CV for consulting: lead with 3 quantified client-style outcomes, add sectors, make GenAI and architecture visible, one page of executive summary.
- [ ] Write a **one-page executive brief** (e.g. "Lakehouse modernisation for a retail bank: options, recommendation, 12-month roadmap").
- [ ] Consider a quick architecture credential (TOGAF Foundation) to close the EA gap.
- [ ] Prepare 4 stories (modernisation, GenAI production, executive influence, failure) with numbers and a lesson.
- [ ] Practise 3 mini-cases aloud (bank modernisation; insurer GenAI claims triage; telco real-time churn).

---

# GENERAL BCG INTERVIEW PREP — structure, answers, questions (20 Oct 2026)
> Role/date not provided. Assumes BCG X data/AI engineering. Process details are from public interview-prep sites (interviewquery, datainterview, roadtooffer) — **reported by candidates, not BCG-confirmed.**

## 1. Likely process (reported)
Recruiter screen → coding / technical assessment → technical + system-design loops → culture / partner-fit interviews. Expect SQL, Python, data modelling, pipeline and system design, GenAI architecture, plus structured behavioural questions.

## 2. How to talk like a BCG interviewer expects
| Habit | Do |
|---|---|
| **Answer first** (pyramid principle) | "My recommendation is X, for three reasons." |
| **Structure aloud** | "I'll look at it in three parts: data, platform, adoption." |
| **MECE buckets** | Non-overlapping, complete categories. |
| **Quantify** | One number per claim. |
| **Hypothesis-driven** | "My hypothesis is the bottleneck is ingestion; I'd test with X." |
| **Client-ready language** | Tie every tech choice to cost, risk, time-to-value. |
| **Summarise** | End with a 15-second recap and next step. |

## 3. Core questions and tight answers
**Q1. Why BCG / why consulting?**
> "I've spent fifteen years building platforms inside one company at a time. At BCG I'd apply that across industries, with the strategy and change-management layer I don't get in-house. BCG X is where technology is built, not just recommended — that's the part I want."

**Q2. Design a GenAI chatbot on client documents (AWS).**
Structure: requirements → data ingestion/chunking → vector store + retrieval → model (Bedrock) → guardrails (PII, grounding, citations) → evaluation → observability/cost → rollout and change management. Close with: "70% of success is adoption — I'd pilot with one team and measure answer accuracy and time saved."

**Q3. Design a data platform for a client with messy data in 4 weeks.**
"Prove the pattern on one domain: ingest to bronze, conform to silver, serve gold for one decision. Data contracts and quality checks from day one. Hand over a runbook the client team can own."

**Q4. Tell me about a time you influenced without authority.**
STAR-L with a number and a lesson (Makro: persuaded finance to adopt the automated close → 5 days to 2 hours).

**Q5. Tell me about a failure.**
Pick a real one, own it, say what changed (process, not blame).

**Q6. How do you scope when requirements are vague?**
"Clarify the decision the client must make, define success in one metric, list assumptions, build the thinnest slice that tests the riskiest one."

**Q7. How do you handle a client who disagrees with your technical recommendation?**
"Restate their concern, show options with cost/risk on one page, test with a small experiment, escalate the decision not the argument."

**Q8. Hands-on checks (expect):** window functions, joins at scale, SCD2, idempotent pipelines, partitioning, Spark skew, data-quality design, LLM evaluation, cost control.

## 4. Mini case drill (practise aloud, 8 min)
*"A retailer's data team takes 5 days to close the month. Why, and what would you do?"*
Frame: (1) Where does time go — sources, reconciliation, manual steps, approvals? (2) Quick wins — automate reconciliations, data-quality gates. (3) Platform — governed gold layer for finance. (4) People/process — owners, SLAs. (5) Metric — days to close, % automated, errors. (Your Makro result is the proof point.)

## 5. Behavioural bank (prepare 5 stories, 90 sec each)
1. Scaling a team 8 → 30. 2. A delivery that slipped. 3. A conflict with a senior stakeholder. 4. A cost/risk trade-off (40% cloud cut). 5. Learning something new fast (GenAI, agentic AI cert).

## 6. Checklist before the interview
- [ ] Confirm the exact role, office and interviewers (LinkedIn).
- [ ] Re-read BCG_DEEP_DIVE.md numbers: $14.4B, +7%, 33,500 staff, AI > 40% / ~25%, ISO 42001.
- [ ] Rehearse the 70% adoption line and the three-part structure.
- [ ] Prepare 3 questions to ask (deep dive §5).
- [ ] Resolve the CV duplicate "40% cost cut" (Makro vs Xendit) — know which is which.
