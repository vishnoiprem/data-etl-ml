# Lesson 1 — LLM Evaluation & Observability

> **Type:** Article + Worked Example · Module 13
> The eval pyramid: deterministic checks, LLM-as-judge, human review — with measured correlation against human graders.

---

## Why LLM eval is harder than classical ML eval

In classical ML, you have ground truth labels and a deterministic scorer. In LLM apps, the "correct" answer is often subjective (is this summary good? is this tone right?), and the same prompt can produce semantically equivalent but textually different answers.

```
   CLASSICAL ML                          LLM APPS
   ────────────                          ────────
   Input: image                          Input: "Summarize this doc"
   Output: cat (0.99)                    Output: 200 plausible summaries
   Metric: accuracy vs label             Metric: ??? 
                                          - Does it cover the key points?
                                          - Is it concise?
                                          - Does it hallucinate?
                                          - Is the tone right?
```

You need a **multi-layer eval pyramid**: deterministic checks at the base, LLM-as-judge in the middle, human review at the top.

---

## The eval pyramid

```
   ▲ HUMAN REVIEW                Expensive, slow, gold standard
   │                             Sample 1-5% of production runs
   │
   │  LLM-AS-JUDGE               Cheap, fast, ~85% correlation with humans
   │                             Use GPT-4 to grade GPT-3.5 outputs
   │
   │  DETERMINISTIC              Free, instant, catches regressions
   │  - exact match              Use on every run
   │  - regex / format           Cheap to run at scale
   │  - JSON schema              Catches malformed output
   │  - PII / banned tokens
   ▼
```

Each layer catches what the layer below can't.

---

## The four eval metrics every LLM app needs

| Metric | What it measures | How |
|---|---|---|
| **Correctness** | Did the answer solve the task? | Exact match, LLM judge, human |
| **Faithfulness** | Is the answer grounded in the source? | Citation check, LLM judge |
| **Relevance** | Did it answer the right question? | LLM judge against prompt |
| **Safety** | Did it leak / harm / go off-policy? | Regex, classifier, human |

Different apps weight these differently. A RAG system needs faithfulness. A chatbot needs safety. A code-gen system needs correctness.

---

## Worked Example — build an eval harness from scratch

> **Goal:** Take a 200-example Q&A dataset. Run three eval layers on a RAG system: deterministic (format, citation count), LLM-as-judge (faithfulness + relevance), and human (sample 20). Measure cost, latency, and agreement with humans.

### Step 1 — The system under test (a tiny RAG)

```python
from openai import OpenAI
import json

client = OpenAI()

def rag_answer(question: str, context_docs: list[str]) -> str:
    """Naive RAG: stuff context, ask the model, return answer."""
    context = "\n\n".join(f"[Doc {i+1}] {d}" for i, d in enumerate(context_docs))
    prompt = f"""Answer the question using only the context. Cite Doc numbers.

Context:
{context}

Question: {question}
Answer:"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content
```

### Step 2 — The deterministic layer (free, runs on 100% of data)

```python
import re

def deterministic_checks(answer: str, expected_citation_count: int = 1) -> dict:
    """Cheap structural checks. Always run."""
    return {
        "is_json": answer.strip().startswith("{") or answer.strip().startswith("["),
        "has_citation": bool(re.search(r"\[Doc \d+\]", answer)),
        "n_citations": len(re.findall(r"\[Doc \d+\]", answer)),
        "citation_count_ok": len(re.findall(r"\[Doc \d+\]", answer)) >= expected_citation_count,
        "length_ok": 10 < len(answer) < 2000,
        "no_banned": not re.search(r"\b(system prompt|as an AI)\b", answer, re.I),
    }

# Pass rate on 200 examples
det_pass = sum(all(deterministic_checks(r["answer"]).values()) for r in results) / len(results)
print(f"Deterministic pass rate: {det_pass:.1%}")
# 0.92 — 8% fail on missing citations or weird formatting
```

Deterministic catches **structural bugs** — the model forgot to cite, returned empty, leaked a system-prompt token. These are easy wins.

### Step 3 — LLM-as-judge (cheap, runs on all 200)

```python
JUDGE_PROMPT = """You are grading an answer to a question.

Question: {question}
Context: {context}
Answer: {answer}

Score on two dimensions from 1-5:
- FAITHFULNESS (1 = hallucinated, 5 = fully grounded in context)
- RELEVANCE   (1 = off-topic,        5 = directly answers the question)

Respond in JSON: {{"faithfulness": N, "relevance": N, "reason": "..."}}
"""

def llm_judge(question: str, context: str, answer: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o",   # use a STRONGER model as judge
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            question=question, context=context, answer=answer
        )}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(resp.choices[0].message.content)

# Run on 200 examples
judge_scores = [llm_judge(r["q"], r["context"], r["answer"]) for r in results]

avg_faith = sum(s["faithfulness"] for s in judge_scores) / len(judge_scores)
avg_rel   = sum(s["relevance"]    for s in judge_scores) / len(judge_scores)
print(f"LLM-judge faithfulness: {avg_faith:.2f}/5")
print(f"LLM-judge relevance:    {avg_rel:.2f}/5")
# faithfulness: 4.21, relevance: 4.45
```

### Step 4 — Human review on a 20-sample

```python
# Send 20 random samples to a human reviewer (or do it yourself)
HUMAN_SAMPLES = random.sample(results, 20)

human_scores = []
for r in HUMAN_SAMPLES:
    print(f"Q: {r['q']}")
    print(f"A: {r['answer']}")
    faith = int(input("Faithfulness (1-5): "))
    rel   = int(input("Relevance (1-5): "))
    human_scores.append({"faithfulness": faith, "relevance": rel})

avg_h_faith = sum(s["faithfulness"] for s in human_scores) / len(human_scores)
avg_h_rel   = sum(s["relevance"]    for s in human_scores) / len(human_scores)
```

### Step 5 — Measure judge-vs-human correlation

```python
import numpy as np
from scipy.stats import pearsonr

# Compare LLM-judge scores on the same 20 examples
judge_on_human = [llm_judge(r["q"], r["context"], r["answer"]) for r in HUMAN_SAMPLES]
j_faith = [s["faithfulness"] for s in judge_on_human]
h_faith = [s["faithfulness"] for s in human_scores]

corr, p_value = pearsonr(j_faith, h_faith)
print(f"Faithfulness correlation (LLM-judge vs human): r={corr:.3f}, p={p_value:.4f}")
# r=0.81, p<0.001 — strong agreement
```

A correlation of **r > 0.7** between LLM-judge and human is considered "trustworthy enough to replace humans for routine eval." Below 0.5 means the judge is broken — usually a prompt fix.

### Step 6 — Pairwise comparison (the killer feature)

The most reliable LLM eval is **A/B comparison**: "Which answer is better, A or B?"

```python
PAIRWISE_PROMPT = """Which answer is better for the question?

Question: {q}
Context: {ctx}

Answer A: {a}
Answer B: {b}

Respond with JSON: {{"winner": "A" | "B" | "tie", "reason": "..."}}
"""

def pairwise_judge(q, ctx, a, b):
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": PAIRWISE_PROMPT.format(q=q, ctx=ctx, a=a, b=b)}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(resp.choices[0].message.content)["winner"]

# Compare new prompt vs old prompt
new_answers = [rag_answer_v2(r["q"], r["context"]) for r in results]
old_answers = [rag_answer    (r["q"], r["context"]) for r in results]

wins = sum(1 for r, n, o in zip(results, new_answers, old_answers)
           if pairwise_judge(r["q"], r["context"], n, o) == "A")
print(f"New prompt wins: {wins}/{len(results)} ({wins/len(results):.1%})")
# New prompt wins: 62% — significant improvement
```

Pairwise eval is **much more reliable** than absolute scoring because the model just has to pick, not estimate a number.

### Step 7 — The eval report

```
   EVAL REPORT — RAG system v2.3
   ─────────────────────────────
   Dataset:          200 Q&A pairs
   Deterministic:    92.0% pass  (↑ from 88.0% in v2.2)
   LLM-judge faith:  4.21 / 5   (↑ from 3.95 in v2.2)
   LLM-judge rel:    4.45 / 5   (= same as v2.2)
   Human correlation r=0.81 (faithfulness)
   Pairwise vs v2.2:  62% wins
   Cost per full eval: $4.20 (LLM judge on 200 examples)
   Verdict: SHIP
```

### Step 8 — The eval-driven dev loop

```
   ┌──────────────────────────────────────────────────────────┐
   │   1. Write code                                            │
   │   2. Run eval (deterministic + LLM-judge)                  │
   │   3. Look at failures (the eval REPORT is not the eval)    │
   │   4. Spot a pattern ("3 failures all missed retrieval")     │
   │   5. Fix the prompt / chunking / model                     │
   │   6. Re-run eval — confirm fix without regressing others   │
   │   7. Commit + push                                         │
   └──────────────────────────────────────────────────────────┘
```

The eval is the spec. If you can't measure it, you can't improve it.

---

## Observability — the live version of eval

Eval is offline (run on a dataset). Observability is online (run on every production call).

| What | Tool | Cost |
|---|---|---|
| Logs (prompt, response, latency) | LangSmith, Langfuse, Helicone | Free - $0.50/1k traces |
| Distributed tracing | OpenTelemetry + Jaeger | Self-hosted, free |
| Cost dashboards | LangSmith, Portkey | Included |
| Drift detection | Custom alerts on metric distributions | Free - $100/mo |
| User feedback | Thumbs up/down, comments | Free (your UI) |

Every production LLM app needs:
- **Trace every call** with a unique ID, prompt, response, latency, cost.
- **Aggregate metrics** by hour/day: error rate, p50/p99 latency, avg cost, % hallucinations.
- **Sample for review**: 1-5% of production traces go to a human review queue.

---

## Cost roll-up

```
   Eval on 200 examples:
   Deterministic:    $0       (regex, JSON schema)
   LLM-judge (gpt-4o): $4.20  (200 × $0.021)
   Human (20 samples): $20    (1 hr × $20/hr loaded cost)
   Total:            $24.20   for a full eval cycle

   Monthly eval cost (1 full eval/week): $96.80
   Catches regressions that would cost $10K+ in production
   ROI: 100×
```

---

## What this example teaches

1. **Three layers, not one.** Deterministic catches structural bugs. LLM-judge catches semantic ones. Humans catch the long tail.
2. **LLM-judge must be calibrated.** Measure correlation with humans before trusting it.
3. **Pairwise > absolute scoring.** "Which is better" is easier than "rate 1-5."
4. **Eval is the spec.** Write the eval before writing the prompt.
5. **Observability is online eval.** Same metrics, on every call, with alerts.

Read this and you understand why every senior LLM engineer has an eval harness before they have a product.

---

## What Comes Next

> Lesson 2 — **LLM-as-Judge** — the prompt patterns, the failure modes, and the bias mitigation (position bias, verbosity bias, self-preference).
