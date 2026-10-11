# 61. Nabla

- **Role:** AI Engineer (Medical LLMs)
- **Tech stack:** Python, PyTorch, Hugging Face Transformers, FastAPI, Postgres, AWS HealthLake, HIPAA-compliant infra
- **Comp band:** $180K-$380K base + equity (Series B, Paris/NYC)
- **Cumulative pass rate:** ~3-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Mission fit, clinical background, comp alignment | 30 min | ~50% |
| 2. Technical phone screen | Coding + ML basics + healthcare data | 60 min | ~40% |
| 3. Onsite (3 rounds) | Coding, system design, clinical ML | 3-4 hrs | ~30% |
| 4. Founder/CMO chat | Mission alignment, ethics of medical AI | 45 min | ~70% |
| 5. Offer | Team match, equity refresh | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why medical AI?"
**Answer:** "I want to build systems that reduce clinician burnout. The average doctor spends 16 minutes per patient on the EHR, and Nabla's ambient scribe flips that. I'm excited by the 2025 Epic partnership and the multi-tenant de-identification pipeline — that's hard infra to build."
**Tip:** Show you've read at least one Nabla research blog post and name a clinician you'd actually interview.

### Q1.2: "How do you handle PHI in training data?"
**Answer:** "De-id with Philter or a custom NER, never store raw notes beyond 30 days, use BAA-covered cloud regions, and run on-device ASR for the audio path so audio never leaves the device. Logs are scrubbed before they hit the analytics pipeline."
**Tip:** HIPAA is non-negotiable. A vague answer fails the screen.

## Stage 2: Technical phone screen

### Q2.1: Reverse a linked list.
**Answer:**
```python
def reverse(head):
    prev, cur = None, head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev
```
**Tip:** Don't over-engineer; Nabla's coding screens are LeetCode-easy-to-medium.

### Q2.2: Build a SOAP-note generator using a 7B open LLM.
**Answer:** Wrap the model with vLLM, prompt with a templated instruction containing the transcript + system prompt "You are a clinical scribe. Output Subjective/Objective/Assessment/Plan JSON." Add guardrails: regex-check that no fabricated meds appear, and log every prompt for QA sampling.
**Tip:** They care about hallucination controls more than raw accuracy.

## Stage 3: Onsite

### Round 3.1: Coding
**Q:** Implement a sliding-window word tokenizer for clinical notes with custom abbreviations ("q.d." → "once daily").
**Answer:** Build a regex tokenizer with a special-cases dict and a fastText fallback for OOV; unit-test on MIMIC-III.

### Round 3.2: System design
**Q:** Design a multi-tenant ambient scribe service.
**Answer:** WebRTC audio → ON-device Whisper → PHI scrubber → LLM SOAP → clinician review UI → FHIR push to EHR. Use tenant-isolated model adapters and a per-tenant audit log.

### Round 3.3: Clinical ML
**Q:** How would you evaluate a model that drafts clinical notes?
**Answer:** Pairwise clinician preference + edit-distance to final signed note + factuality via MedNLI + safety panel for hallucinations. Cite Nabla's 2025 ambient scribe RCT.

### Round 3.4: Behavioral
**Q:** Tell me about a time you pushed back on a metric.
**Answer:** Use STAR: refused to ship a model whose ROUGE was high but hallucination rate was 18% in private eval; proposed a factuality-weighted score; shipped after it improved by 9 pts.

## Stage 4: Hiring committee
A panel of 3 engineers + 1 clinician reviews your system design for safety, the ML round for clinical plausibility, and the bar-raiser for general engineering rigor. They explicitly screen for HIPAA mindset.

## Stage 5: Offer
Series B equity refreshers vest over 4 years. They counter-offer aggressively for candidates with Epic/Cerner integration experience.

## Tips for the Nabla loop
- Read at least 2 Nabla research blog posts and 1 whitepaper.
- Memorize HIPAA Safe Harbor vs Expert Determination.
- Practice SOAP-note and ICD-10 basics.
- Be ready to defend every "would you redact?" decision.
- Show you've talked to a real clinician about burnout.
- Don't oversell accuracy — emphasize safety, auditability, and clinician-in-the-loop.

## Real candidate report
> "The screen was almost entirely mission/ethics. They asked me to role-play a doctor calling about a hallucinated medication — they wanted to see if I'd be honest vs. hedge. Got the offer after 2 weeks." — Glassdoor, ML Engineer, 2025

## Sources
- [Nabla careers](https://www.nabla.com/careers)
- [Levels.fyi — Nabla](https://www.levels.fyi/companies/nabla)
- [Glassdoor — Nabla interviews](https://www.glassdoor.com/Interview/Nabla-Interview-Questions-E3521858.htm)
- [Nabla research blog](https://www.nabla.com/blog)
- [Reddit r/MachineLearning — Nabla thread](https://reddit.com/r/MachineLearning)
