# 39. Scale AI

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual. Color: company brand color as accent. Headline on image: "SCALE AI / DATA ENGINE / 2026".

> **TL;DR:** Scale's loop is **data-centric and operational** — the company is the data layer of the AI revolution, and every answer bends toward labeling quality, eval rigor, and consensus. The signature stack is **Data Engine + SEAL + GenAI Platform**, and the winning candidate shows that "data is the moat" by reflex.

```
Recruiter (50%) → Phone (40%) → Onsite (30%) → Tech Panel (55%) → Offer
```

- **Role:** ML Engineer / Applied Scientist (Data Engine, Fine-tuning, Evaluation, RLHF, SEAL)
- **Tech stack:** Python, PyTorch, CUDA, Ray, Kubernetes, Kafka, Postgres, React/Typescript (full-stack)
- **Comp band:** $200K-$600K total comp (L3-L5) | RSUs 4-year, 1-year cliff + cash; senior crosses $800K+
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Mission alignment (data is the moat), comp, fit | 1 week | ~50% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~30% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~55% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

Scale's loop is operationally flavored — the panel wants to see that you can ship a system that survives contact with thousands of annotators and petabytes of data. "Build Trust" is a primary signal, not a vibe.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Scale for ML?"
**Answer:** "Scale is the data layer of the AI revolution. The *Donate* / *Outlier* / *Rapid* businesses are the largest human-in-the-loop ML pipelines in the world. The *SEAL* team is doing frontier research on private model evaluation. I want to work on the *infrastructure that decides* which models get deployed."
**Tip:** Reference *Scale Data Engine*, *Scale GenAI Platform*, *SEAL* (Safety, Evaluation, Alignment Lab), *Defense* — distinct teams.

### Q1.2: "Tell me about a data-centric ML project you shipped"
**Answer:** STAR with focus on *data quality*, *labeling pipelines*, and *eval-driven iteration*. Scale is data-obsessed.
**Tip:** Show you understand the "bitter lesson" — data and eval are the moat.

## Stage 2: Technical phone screens (90 min)

The phone screens are where Scale quietly tests for *data-centric* thinking — if your labeling design doesn't reach for consensus, adjudication, and gold-standard injections, you're missing the Scale frame. Distributed-systems questions are common.

### Q2.1: Coding: "Build a task queue with retries and dead-letter"
**Answer:** Producer → queue (Kafka) → consumer with retry policy → DLQ on failure.
```python
def enqueue(task, max_retries=3):
    payload = json.dumps({"task": task, "retries": 0, "max": max_retries})
    kafka.send('tasks', payload.encode())
def consume():
    for msg in kafka.consume('tasks'):
        try: process(msg)
        except Exception:
            if msg.retries < msg.max: enqueue(msg, retries=msg.retries+1)
            else: kafka.send('dlq', msg)
```
**Tip:** Distributed-systems questions are common. Be ready for queue + worker pool design.

### Q2.2: ML: "Design Scale's data labeling pipeline for a code-generation eval"
**Answer:** (1) Task definition — code prompt, test cases, rubric; (2) Annotator qualification — code tests on seed problems; (3) Multi-annotator + adjudication; (4) Quality control — gold-standard injections, attention checks, calibration; (5) Reward model training on labels; (6) Eval pipeline — held-out human-rated set; (7) Drift monitoring.
**Tip:** Scale's *core* is labeling quality. Show you understand consensus, calibration, annotator bias.

## Stage 3: Onsite (4 rounds)

The onsite is dense and data-pipeline-flavored. Coding, then RLHF/SEAL system design, then ML deep-dive (often eval design or rubric design), then "Build Trust" behavioral last.

### Round 3.1: Coding (60 min, 2 questions)
- Q: Implement a thread-safe rate limiter.
- Q: Top K frequent items in a stream.
- Optional 3rd: Distributed-systems question on consistency or idempotency.

### Round 3.2: System design (60 min)
- Q: Design Scale's RLHF data pipeline. Prompt sourcing, response generation, human preference labeling, reward model training, and the iterative loop.
- Q: Design a private model eval system (SEAL). Confidential benchmarks, customer model ingestion, evaluation harness, red-team pipeline, and reporting.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you evaluate a frontier LLM for a customer's enterprise use case? Build a domain-specific eval set, run human + LLM-as-judge, calibrate, and deliver a report.
- Q: How would you design a labeling rubric for a subjective task (writing quality)? Anchor examples, paired comparisons, rater training, inter-rater reliability, and drift monitoring.

### Round 3.4: Behavioral (60 min)
- Q: Tell me about a time you dealt with a labeling quality issue at scale. Scale deals with thousands of annotators.
- Q: A time you worked with operations to fix a pipeline.
- Q: Disagreement with a PM on data quality vs speed.

## Stage 4: Hiring committee
A panel of senior engineers + product reviews. They look for: (1) ML bar for the level, (2) data-centric thinking, (3) Scale values (Move Fast, Build Trust, Own Outcomes, Work Together), (4) operational excellence. Vote is "Strong Hire / Hire / No Hire / Strong No Hire."

## Stage 5: Offer
Cash + RSUs. Scale is competitive — below FAANG top-of-band but with strong equity upside. Negotiation is moderate. Team match after loop. SF HQ is main hub; some roles remote-US.

## Tips for the Scale loop
- Reference *Data Engine*, *GenAI Platform*, *SEAL*, *Defense*, *Public Sector* — distinct teams.
- For ML rounds, emphasize *data quality* and *eval rigor* — Scale's lifeblood.
- For system design, RLHF + labeling pipeline are the bread-and-butter.
- Scale has a strong *operational* culture — show you can ship reliable systems.
- For behavioral, "Build Trust" stories score well — Scale's reputation depends on data integrity.
- For SEAL roles, expect frontier-model evaluation depth.
- For Defense roles, expect clearance + on-site (DC area) requirements.

## Real candidate report
> "Loop for SEAL (private model eval). 4 rounds in 1 day. The system design was a confidential benchmark pipeline for a customer's GPT-class model. The ML deep-dive was on building a domain-specific eval set. Behavioral was 'move fast' flavored. Offer at L4, ~$420K total, 4 weeks." — Blind, 2025-09

## See also

- [Labelbox](./40-labelbox.md) — direct data-labeling competitor
- [Weights & Biases](./41-wandb.md) — same ML tooling category
- [Comet](./42-comet.md) — same ML platform
- [Hugging Face](./11-huggingface.md) — same ML data + tooling

## Sources
- [Scale AI Careers](https://scale.com/careers)
- [Levels.fyi Scale AI salaries](https://www.levels.fyi/companies/scale-ai/salaries)
- [Scale AI Engineering blog](https://scale.com/blog/category/engineering)
- [SEAL research](https://scale.com/seal)
- [Glassdoor Scale AI interviews](https://www.glassdoor.com/Interview/Scale-AI-Interview-Questions-E3299049.htm)

---

## The 1 thing to remember

At Scale, "data is the moat" is the frame — name Data Engine, SEAL, and GenAI Platform, and reach for consensus, gold-standard injections, and eval rigor by reflex, because labeling quality is the company's reputation.
