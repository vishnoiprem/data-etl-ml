# BCG INTERVIEW PREP — structure, answers, questions (20 Oct 2026)
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
