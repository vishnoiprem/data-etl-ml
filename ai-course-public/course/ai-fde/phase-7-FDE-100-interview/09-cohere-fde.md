# Cohere — Applied / Forward Deployed FDE (Cohere for AI)

## Company Snapshot
- **HQ**: Toronto / San Francisco
- **Team Size**: ~100–150 FDEs
- **Comp**: $180K–$210K base; Sr $230K–$270K; TC $250K–$640K
- **What they deploy**: Enterprise RAG / fine-tuning for financial + regulated industries
- **Travel**: 30–50%

## Interview Process
1. Recruiter
2. Coding (medium LeetCode)
3. ML system design (heavy emphasis on RAG, retrieval, evals)
4. On-site (3 sessions)
   - Coding 2
   - ML/RAG case
   - Customer scenario (compliance-flavored)

---

## ✅ SUCCESS STORIES

### RAG case
**Q:** *"A bank wants to deploy RAG over their policy & procedure docs. Answer 'can I wire $50K from my personal account for a down payment?' reliably."*
**A (winner):**
- **Hybrid retrieval**: BM25 + Cohere Embed v3, RRF fusion.
- **Reranker**: Cohere Rerank 3 in the loop (cuts top-100 → top-5).
- **Prompt**: force the LLM to cite 3 docs, then say "based on policy X.Y, yes/no/need-approval" + quote.
- **Confidence layer**: if reranker score < 0.4, return *"I don't have evidence — contact compliance."* Never guess.
- **Evals**: 200 hand-labeled Q&As in finance-specific domains; weekly regressions.
- **Compliance**: every Q&A persisted with audit trail for 7 years.
**Why it worked:** Right hybrid retrieval, named Cohere products, hedge-on-low-confidence, audit-trail aware.

---

### Compliance scenario
**Q:** *"Customer needs SOC2 + FINRA compliance. What's our plan?"*
**A (winner):** *"Cohere is already SOC2 Type II + ISO 27001. For FINRA, model serving happens in the customer's VPC via Cohere Private Deployment (no telemetry egress), with logs persisted to S3 in their account. Audit-ready by week 4. I'll bring in our compliance PM at week 1 to map the controls. Aim: SOC2 letter + FINRA evidence collection in 30 days."*
**Why it worked:** Knew the actual Cohere SKU (Private Deployment), named the certs, framed timeline in days.

---

### Coding
**Q:** *"Implement chunked streaming JSON parse."*
**A (winner):** Generator-based, with state for unclosed strings/braces, plus unit tests for nested arrays. Tested with a 200MB mock file before submitting.
**Why it worked:** Streaming + tested + correct on edge cases.

---

## ❌ REJECTION STORIES

### RAG case
**Q:** *"How do you reduce hallucination in RAG?"*
**A (loser):** *"Use a bigger model."*
**Why it failed:** Wrong direction. Bigger ≠ lower hallucination. Missed retrieval, prompting, eval.
**What they should have said:** Better retrieval (hybrid, reranker), grounded prompting with citation enforcement, eval-set-driven iteration, structured-output forces.

---

### Compliance scenario
**Q:** *"Can we use Cohere for HIPAA?"*
**A (loser):** "Sure, we have SOC2."
**Why it failed:** SOC2 ≠ HIPAA. BAA required.
**What they should have said:** "Yes — Cohere Enterprise supports BAA (Business Associate Agreement). For PHI specifically, we recommend Private Deployment so PHI never leaves the customer's VPC. I'd bring in our healthcare PM and the BAA template in week 1."

---

## 📚 Reading List
1. Cohere docs — Rerank, Embed, Private Deployment
2. *"Hybrid search in production"* (Cohere blog)
3. *"RAG evaluation cookbook"* (free on GitHub)
4. SOC 2 + FINRA + HIPAA primer for engineers
5. levels.fyi Cohere debriefs
6. r/MachineLearning "Cohere enterprise" threads
