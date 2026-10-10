# 59. Hippocratic AI (Healthcare AI)

- **Role:** AI Engineer (Healthcare LLM / Nurse/Clinician AI)
- **Tech stack:** Python, PyTorch, OpenAI/Anthropic APIs, in-house fine-tuned models, PEFT/LoRA, RLHF, vLLM, vector DBs, Postgres, Kubernetes
- **Comp band:** $200K-$450K (well-funded, $3B+ valuation, healthcare AI premium)
- **Cumulative pass rate:** ~2-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation + healthcare background | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60-90 min coding + LLM | 1-2 weeks | ~35% advance |
| 3. **Onsite (4-5 rounds)** | Coding, system design, LLM, clinical/regulatory, founder | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Panel review (often includes clinicians) | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Hippocratic AI?"
**Answer:** Three-bet: (1) Hippocratic AI pioneered the "Polaris" safety-constrained LLM for healthcare — the focus on nurse-role AI (not just clinician copilot) is differentiated, (2) the founding team includes clinicians (Munjal Shah, Alex Morgan) + ex-Stripe AI researchers, so it's dual-domain from day 1, (3) the regulatory-aware safety focus (they care about FDA, HIPAA) is the right bet for healthcare AI.
**Tip:** Mention you've used or read about Hippocratic AI's Polaris model. Show healthcare AI curiosity.

### Q1.2: "Tell me about a healthcare AI project you built (or wanted to build)"
**Answer:** Walk through any healthcare AI project — even a side project. Show you've thought about: HIPAA, PHI, model safety, clinical eval, regulatory constraints.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement a clinical text de-identifier"
**Answer:**
```python
import re
def deidentify(text):
    # Replace names, dates, SSN, MRN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    text = re.sub(r'\b\d{8}\b', '[MRN]', text)
    text = re.sub(r'\bDr\.?\s+[A-Z][a-zA-Z]+', 'Dr. [REDACTED]', text)
    text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '[DATE]', text)
    return text
```
**Tip:** Real de-identification uses ML (NER with HIPAA Safe Harbor or Expert Determination). Mention tools: Philter, Presidio, AWS Comprehend Medical.

### Q2.2: LLM — "How would you build a clinical decision support system with safety constraints?"
**Answer:** Three pillars: (1) **grounded generation** — LLM only answers from retrieved clinical guidelines + patient data, (2) **safety constraints** — explicit refusals for diagnosis, drug dosage, "I cannot recommend..." patterns, (3) **human-in-the-loop** — clinicians must approve before any action.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a sliding window chunker.
- **Q3.1.2:** Build a small agent loop (ReAct).
- **Q3.1.3:** Implement a simple medical NER (regex + ML hybrid).

### Round 3.2: System design
- **Q3.2.1:** "Design Hippocratic's nurse-call agent." Discuss: patient context, real-time conversation, escalation to human nurse, safety filters, audit log, HIPAA compliance.
- **Q3.2.2:** "Design a clinical Q&A system that cites guidelines." Talk: retrieval (vector + BM25 + reranker over UpToDate, Lexicomp, IDSA), grounded generation, citation verification, structured responses.

### Round 3.3: LLM / clinical deep-dive
- **Q3.3.1:** "How do you build safety constraints into a medical LLM?" Discuss: Constitutional AI, RLHF with clinicians, prompt-engineering guardrails, post-hoc verification, escalation to humans.
- **Q3.3.2:** "How do you evaluate a clinical LLM?" Talk: domain benchmarks (MedQA, USMLE), clinician review, hallucination rate, citation accuracy, refusal appropriateness.

### Round 3.4: Clinical / regulatory
- **Q3.4.1:** "Walk me through how a nurse would use Hippocratic's agent in a real patient call. What safety features matter?"
- **Q3.4.2:** "How would you approach FDA submission for a clinical AI feature?" (Hippocratic cares about regulatory strategy.)

### Round 3.5: Founder
- **Q3.5.1:** "Why healthcare AI? Why safety-first?"
- **Q3.5.2:** "Tell me about a time you built something for a non-technical expert."

## Stage 4: Hiring committee
Hippocratic's committee is high-bar and includes clinicians. They look for: (a) LLM/RAG depth, (b) safety-first mindset (you should think about failure modes), (c) healthcare domain curiosity, (d) humility about AI's role in healthcare. Red flags: arrogant about AI replacing clinicians, weak on safety thinking, no healthcare AI exposure.

## Stage 5: Offer
Base is at the high end ($220K-$320K+ for senior), equity is meaningful (private, high valuation). Negotiation: equity, sign-on, level.

## Tips for the Hippocratic AI loop
1. **Brute-force RAG + grounded generation** — this is Hippocratic's foundation.
2. **Learn healthcare AI basics** — HIPAA, PHI, FDA SaMD, clinical workflows.
3. **Have a healthcare AI project to discuss** — even a side project (RAG over clinical guidelines, etc.).
4. **Practice the "design a clinical Q&A system" round** — almost always asked.
5. **Be ready for a founder round** — Munjal Shah is technical and asks about safety.
6. **Read the Hippocratic AI blog and papers** — they publish on Polaris safety.
7. **Have opinions on safety vs capability** — this is Hippocratic's core tension.

## Real candidate report
> "Phone screen was de-identifier coding + clinical Q&A design. Onsite had 4 rounds including a clinical domain round where they asked me to walk through a patient call scenario. I had to know HIPAA, escalation, and safety constraints. Offer: $260K + 0.04% equity, 6 days." — Levels.fyi, 2025

## Sources
- [Hippocratic AI careers](https://www.hippocraticai.com/careers)
- [Hippocratic AI blog](https://www.hippocraticai.com/blog)
- [Polaris safety paper](https://www.hippocraticai.com/safety)
- [Hippocratic AI Glassdoor](https://www.glassdoor.com/Interview/Hippocratic-AI-Interview-Questions-E3509600.htm)
- [Levels.fyi Hippocratic AI](https://www.levels.fyi/companies/hippocratic-ai)
