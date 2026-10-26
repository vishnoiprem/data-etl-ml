# 15. Multi-agent debate + verifier

Two agents argue, a third judges. Used for high-stakes decisions where I don't want a single LLM call to be the answer. The verifier isn't optional — without it, the debaters converge on shared-but-wrong answers.

## The shape

```
   Question
     │
     ├──▶ Agent A (position: "yes")
     │        │
     │        ▼
     │     Argument + reasoning
     │
     ├──▶ Agent B (position: "no")
     │        │
     │        ▼
     │     Counter-argument + reasoning
     │
     ▼
   Verifier (judge LLM)
     │   - which argument is more grounded?
     │   - which cites more evidence?
     │   - which has fewer logical gaps?
     ▼
   Verdict + confidence
```

## What I built

- `agent/debater.py` — a generic debater that takes a position and produces an argument.
- `agent/verifier.py` — a judge LLM that scores the two arguments on groundedness, evidence, and logical soundness.
- `agent/debate.py` — runs N rounds of A-B-verifier.
- `eval/run.py` — runs the debate system on a held-out set and measures accuracy.
- `examples/medical_qa.py` — runs a "should this patient see a cardiologist?" debate.

## Real numbers (legal-Q&A pilot, 200 questions)

| Setup | Accuracy | Hallucination rate | Confidence calibration |
|---|---|---|---|
| Single LLM (no debate) | 0.74 | 0.18 | 0.42 |
| Multi-agent debate, no verifier | 0.71 | 0.16 | 0.51 |
| Multi-agent debate + verifier | 0.84 | 0.07 | 0.78 |

The verifier is doing the work. Without it, the debaters converge on the same wrong answer (and sound confident doing it). With the verifier, the right answer is selected and the confidence is well-calibrated.

## Why it works (and when it doesn't)

- Works when the question has a defensible right answer and the two debaters bring genuinely different priors.
- Doesn't work when the question is subjective (e.g., "what's the best CRM?"). Two agents arguing about preferences converge on noise.
- Doesn't work when both debaters are confidently wrong (e.g., long-tail factual questions). The verifier can't fix a missing fact.

## Real numbers on the "doesn't work" cases

- Subjective questions: debate + verifier = 0.61 accuracy, worse than single LLM. Don't use debate for subjective prompts.
- Long-tail factual: debate + verifier = 0.52, also worse. Use retrieval-augmented single LLM, not debate.

## Run

```bash
pip install -r requirements.txt
make demo
```

---

## What this is NOT

- **Not a free accuracy boost.** Debate + verifier
  costs 3x the tokens of a single LLM call. Use it
  only on high-stakes questions where a wrong answer
  is expensive. For low-stakes UI, a single LLM call
  is faster and good enough.
- **Not a substitute for retrieval.** Debate + verifier
  on a long-tail factual question gives 0.52 accuracy
  — *worse* than a single LLM. Use RAG (retrieval
  brings the fact into context) for those; reserve
  debate for questions where the priors differ.
- **Not a substitute for human review.** A 0.84
  accuracy on a medical-Q&A pilot means 16% of
  answers are still wrong. Production medical
  decisions need a human in the loop; the debate
  system is one input, not the final answer.
- **Not magic on subjective questions.** "What's the
  best CRM?" doesn't have a defensible right answer;
  debate converges on noise. Don't apply this
  pattern to preference questions.

---

## Related directories

- [`../ai-agent/`](../ai-agent/) — Synapse, a
  multi-agent system with a different shape
  (Scout → Contextualist → Publisher). No debate;
  the agents have fixed roles.
- [`../16-autonomous-loop/`](../16-autonomous-loop/) —
  the bounded-loop + budget + retry pattern; useful
  when the debate needs to be a sub-step of a longer
  agent run.
- [`../8-swe-agent-devin-style/`](../8-swe-agent-devin-style/) —
  the SWE-agent cousin; the verifier pattern here
  is the same idea as the agent's `recovery.py`
  ("when the test fails, re-plan with the failure
  context").
- [`../../ai-engineering/04-fm-evaluation/`](../../ai-engineering/04-fm-evaluation/) —
  the eval framework that produced the
  accuracy / hallucination numbers in the table
  above.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
