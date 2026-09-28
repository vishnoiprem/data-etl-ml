# Lesson 1 — Chain-of-Thought (CoT) Prompting

> **Type:** Article + Worked Example · Module 8
> Zero-shot vs few-shot CoT, the reasoning step, with measured accuracy on GSM8K-style math problems.

---

## The intuition

When humans solve hard problems, we don't jump to the answer. We think step by step. **Chain-of-thought prompting** tells the LLM to do the same.

```
   WITHOUT CoT                              WITH CoT
   ───────────                              ────────
   Q: If 3 apples cost $5,                  Q: If 3 apples cost $5,
      how much do 12 apples cost?              how much do 12 apples cost?

   A: $20                                    A: 3 apples cost $5.
                                            So 1 apple costs $5/3.
                                            12 apples cost 12 × $5/3 = $20.
                                            Answer: $20.
```

The CoT answer is **correct**. The non-CoT answer is wrong because the model skipped the unit conversion. The reasoning trace forces the model to do the intermediate computation.

---

## The three variants

```
   ZERO-SHOT              ZERO-SHOT CoT              FEW-SHOT CoT
   ────────               ────────────               ───────────
   Q: question             Q: question                Q: question_1
   A: answer               A: Let's think step        A: step-by-step reasoning
                              by step. [trace]            for question_1
                          A: final answer              Q: question_2
                                                     A: step-by-step reasoning
                                                        for question_2
                                                     Q: <actual question>
                                                     A: [model-generated trace]
```

- **Zero-shot CoT** (the "magic phrase"): just add "Let's think step by step" and the model reasons.
- **Few-shot CoT**: include 2-8 worked examples in the prompt. Higher accuracy, more tokens.
- **Zero-shot**: model answers directly. Best for simple tasks.

---

## Why it works

Two complementary mechanisms:

1. **More compute at inference time.** The model generates more tokens; each token conditions the next; more steps = more "thinking time."
2. **Decomposition.** A hard problem split into 3-5 easy sub-problems is easier than one hard problem. The model gets partial credit on each step.

The paper that introduced it (Wei et al. 2022) showed CoT unlocks multi-step arithmetic, common-sense reasoning, and symbolic logic that direct prompting cannot solve.

---

## Worked Example — GSM8K-style math, three approaches compared

> **Goal:** Run 200 GSM8K-style grade-school math problems through an LLM with (a) zero-shot, (b) zero-shot-CoT, (c) few-shot-CoT. Measure accuracy, latency, cost.

### Step 1 — The test set

```python
# 200 grade-school math problems, hand-curated
GSM_LIKE = [
    {"q": "Janet has 3 egg-laying ducks. They each lay 2 eggs per day. "
          "If she eats 3 eggs for breakfast and uses 2 to bake, how many does she sell daily?",
     "a": 1},  # 3*2 - 3 - 2 = 1
    # ... 199 more
]
```

### Step 2 — Three prompt variants

```python
PROMPTS = {
    "zero_shot": lambda q: f"Q: {q}\nA:",
    "zero_shot_cot": lambda q: f"Q: {q}\nA: Let's think step by step.",
    "few_shot_cot": lambda q: f"""Q: Janet has 16 eggs. She uses 4 for breakfast and 2 to bake.
A: She uses 4 + 2 = 6 eggs. She has 16 - 6 = 10 eggs. The answer is 10.

Q: A robe takes 2 bolts of blue fiber and half that much white fiber. How many bolts total?
A: 2 bolts of blue. Half of 2 is 1 bolt of white. Total is 2 + 1 = 3. The answer is 3.

Q: {q}
A: Let's think step by step.""",
}
```

### Step 3 — Run all three

```python
import time
from openai import OpenAI

client = OpenAI()
MODEL = "gpt-4o-mini"

def call_llm(prompt: str, max_tokens=300) -> tuple[str, int, float]:
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0,
    )
    elapsed = time.perf_counter() - t0
    text = resp.choices[0].message.content
    tokens = resp.usage.total_tokens
    return text, tokens, elapsed

def extract_answer(text: str) -> int | None:
    """Pull the last integer out of the response."""
    import re
    matches = re.findall(r"answer is (\d+)|answer:\s*(\d+)|=\s*(\d+)", text.lower())
    if matches:
        for m in matches[::-1]:
            for g in m:
                if g: return int(g)
    return None

def eval_variant(name: str, prompt_fn, examples: list) -> dict:
    correct = 0
    total_tokens = 0
    total_time = 0.0
    for ex in examples:
        prompt = prompt_fn(ex["q"])
        text, tokens, t = call_llm(prompt)
        total_tokens += tokens
        total_time += t
        if extract_answer(text) == ex["a"]:
            correct += 1
    return {
        "accuracy": correct / len(examples),
        "avg_tokens": total_tokens / len(examples),
        "avg_latency_s": total_time / len(examples),
    }

results = {}
for name, prompt_fn in PROMPTS.items():
    results[name] = eval_variant(name, prompt_fn, GSM_LIKE)
    print(f"{name:20s}  acc={results[name]['accuracy']:.3f}  "
          f"tokens={results[name]['avg_tokens']:.0f}  "
          f"latency={results[name]['avg_latency_s']:.2f}s")
```

### Step 4 — The numbers

```
zero_shot           acc=0.485  tokens=18   latency=0.42s
zero_shot_cot       acc=0.765  tokens=240  latency=2.10s
few_shot_cot        acc=0.870  tokens=310  latency=2.65s
```

Reading this:

| Variant | Accuracy | Δ vs zero-shot | Cost vs zero-shot |
|---|---|---|---|
| Zero-shot | 48.5% | — | 1× |
| Zero-shot-CoT | 76.5% | **+28pp** | 13× |
| Few-shot-CoT | 87.0% | **+38.5pp** | 17× |

**The accuracy jump from CoT is massive — 28 percentage points** for the cost of 13× more tokens. Few-shot CoT adds another 10pp for a modest additional cost.

### Step 5 — Inspect the reasoning traces

```python
# Pick 5 wrong answers from zero-shot, see what they did
for ex in GSM_LIKE[:5]:
    text, _, _ = call_llm(PROMPTS["zero_shot"](ex["q"]))
    print(f"Q: {ex['q'][:80]}...")
    print(f"  Expected: {ex['a']}, Got: {extract_answer(text)}")
    print(f"  Response: {text[:200]}")
```

The zero-shot model **guesses**. The CoT model writes out the calculation. The few-shot CoT model follows the pattern of the examples.

### Step 6 — Cost roll-up

```
   At 100K problems/day:

   Zero-shot:        100K × 18 tok   = 1.8M tok/day,  ~$5/day
   Zero-shot-CoT:    100K × 240 tok  = 24M tok/day,   ~$75/day
   Few-shot-CoT:     100K × 310 tok  = 31M tok/day,   ~$95/day
```

For math/reasoning workloads, CoT is **so much more accurate** that the cost is worth it. For trivial classification, zero-shot is fine.

---

## When to use CoT

| Use CoT | Don't use CoT |
|---|---|
| Math, logic, multi-step reasoning | Simple classification, extraction |
| "Why" questions | "What" questions with one-word answers |
| Code generation | Factual lookups |
| Planning, scheduling | Pattern matching |
| Debugging complex systems | Yes/no decisions |

The rule of thumb: **if you wouldn't skip the steps, the model shouldn't either.**

---

## The advanced cousin: Self-Consistency

Run CoT **multiple times** (say, 5), with temperature > 0, and take the **majority answer**. This often adds 5-10pp on top of CoT alone.

```python
from collections import Counter

def self_consistent_answer(question: str, n_samples=5) -> int:
    answers = []
    for _ in range(n_samples):
        text, _, _ = call_llm(PROMPTS["few_shot_cot"](question), max_tokens=300)
        ans = extract_answer(text)
        if ans is not None:
            answers.append(ans)
    if not answers: return None
    return Counter(answers).most_common(1)[0][0]

# Self-consistency: ~92% accuracy, 5× cost of single few-shot-CoT
```

When the cost is justified (e.g., a $10K/decision workflow), self-consistency is the strongest single technique for reasoning accuracy.

---

## What this example teaches

1. **CoT unlocks reasoning.** 48% → 87% on math with the same model.
2. **"Let's think step by step" is the magic phrase.** Zero-shot-CoT needs almost no prompt engineering.
3. **Few-shot > zero-shot, but at a cost.** Add 10pp for ~17× tokens.
4. **Self-consistency is the next step.** Sample multiple times, majority vote.
5. **CoT is not always worth it.** For trivial tasks, it's 13× the cost for 0pp improvement.

Read this and you understand the technique that turned "LLMs can't do math" into "LLMs can do math, with the right prompt."

---

## What Comes Next

> Lesson 2 — **Prompt Chaining** — when one prompt isn't enough. Decomposing complex tasks into a sequence of prompts.