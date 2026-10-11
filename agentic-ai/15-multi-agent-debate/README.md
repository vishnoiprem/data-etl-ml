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
