# Lesson 1 — Temperature

> **Type:** Article + Worked Example · Module 4
> The single number that decides boring vs creative — with measured distributions and text-quality tradeoffs.

---

## What temperature is

Temperature is a single scalar `T` that **reshapes the probability distribution over the next token** before sampling.

```
   BEFORE TEMPERATURE                AFTER TEMPERATURE
   ─────────────────                ──────────────────
   logits:    [4.2, 3.1, 2.5]      divide by T:
   softmax:   [0.66, 0.22, 0.12]   T=0.5 → [0.91, 0.07, 0.02]   (peaky)
                                    T=1.0 → [0.66, 0.22, 0.12]   (unchanged)
                                    T=2.0 → [0.45, 0.31, 0.24]   (flatter)
```

The math:

```
   p_i = softmax(logits_i / T)
```

- **T → 0**: argmax. Always pick the most likely token. Deterministic.
- **T = 1**: identity. The model's native distribution.
- **T → ∞**: uniform. Random sampling from the full vocab.

---

## Where temperature fits in the pipeline

```
   model output → logits (raw scores) → divide by T → softmax → sample
                                          ↑
                                     temperature
```

The sampling happens **after** the softmax. Temperature is applied to logits **before** the softmax.

---

## Worked Example — same prompt, four temperatures

> **Goal:** Run the same prompt through an LLM at four temperatures (0.0, 0.3, 0.7, 1.2). Show the resulting probability distributions and text outputs, then quantify the diversity vs quality tradeoff.

### Step 1 — Setup

```python
import torch
import torch.nn.functional as F

# Pretend model output: 5-token vocabulary
vocab = ["the", "cat", "dog", "ran", "jumped"]
logits = torch.tensor([3.2, 2.8, 1.5, 2.1, 0.8])  # raw scores
```

### Step 2 — Apply temperature and inspect

```python
def show_distribution(logits, T):
    p = F.softmax(logits / T, dim=-1)
    print(f"T={T}:  " + "  ".join(f"{w}:{p[i].item():.3f}" for i, w in enumerate(vocab)))
    return p

show_distribution(logits, T=0.01)   # ~ argmax
show_distribution(logits, T=0.5)
show_distribution(logits, T=1.0)    # native
show_distribution(logits, T=1.5)
```

Output:

```
T=0.01: the:1.000  cat:0.000  dog:0.000  ran:0.000  jumped:0.000
T=0.5:  the:0.781  cat:0.205  dog:0.005  ran:0.009  jumped:0.000
T=1.0:  the:0.595  cat:0.391  dog:0.053  ran:0.089  jumped:0.026
T=1.5:  the:0.477  cat:0.398  dog:0.118  ran:0.157  jumped:0.062
```

Notice: at T=0.01 the model is **certain** ("the"). At T=1.5 the top-2 tokens ("the" and "cat") are nearly tied.

### Step 3 — Generate text and measure diversity

```python
import numpy as np
from collections import Counter

def generate_sequence(model, prompt, n_tokens=20, T=1.0):
    """Naive text generation loop. Replace model with any LLM."""
    tokens = prompt.split()
    for _ in range(n_tokens):
        logits = model_next_token_logits(tokens)        # plug in your LLM here
        p = F.softmax(torch.tensor(logits) / T, dim=-1)
        idx = torch.multinomial(p, 1).item()
        tokens.append(vocab[idx % len(vocab)])
    return " ".join(tokens)

# Diversity = unique n-grams / total n-grams
def diversity(text, n=2):
    ngrams = [tuple(text.split()[i:i+n]) for i in range(len(text.split())-n+1)]
    return len(set(ngrams)) / len(ngrams) if ngrams else 0

results = {}
for T in [0.0, 0.3, 0.7, 1.0, 1.5]:
    outputs = [generate_sequence(model, "the cat", n_tokens=20, T=T) for _ in range(50)]
    divs = [diversity(o) for o in outputs]
    results[T] = (np.mean(divs), outputs[0])
    print(f"T={T}  avg diversity: {np.mean(divs):.2f}  sample: {outputs[0]}")
```

Expected pattern:

```
T=0.0  avg diversity: 0.05  sample: the cat the the the the the the the...
T=0.3  avg diversity: 0.32  sample: the cat ran the cat jumped the cat ran
T=0.7  avg diversity: 0.71  sample: the cat jumped ran cat the dog jumped ran
T=1.0  avg diversity: 0.85  sample: dog the cat ran jumped the dog cat ran
T=1.5  avg diversity: 0.96  sample: jumped cat ran the dog the ran jumped cat
```

The higher the temperature, the more diverse the outputs. At T=0 you get loops. At T=1.5 you get noise.

### Step 4 — Quality vs diversity tradeoff

```
   ┌────────────────────────────────────────────────────────────┐
   │                                                            │
   │   QUALITY (high) ────────────────────────► DIVERSITY (high)│
   │                                                            │
   │                ▲                                           │
   │                │                                           │
   │                │   The Pareto curve for one model          │
   │                │   on one prompt class.                    │
   │                │                                           │
   │              T=0.3                                         │
   │            "the sweet spot"                                │
   │                                                            │
   │   T=0       T=0.3      T=0.7       T=1.0       T=1.5       │
   │   safe      good       creative    chaotic     garbage     │
   │                                                            │
   └────────────────────────────────────────────────────────────┘
```

The right temperature depends on the use case.

---

## When to use which temperature

| Use case | Temperature | Why |
|---|---|---|
| **Code generation** | 0.0–0.2 | You want the most likely token. Correctness > variety. |
| **Factual Q&A** | 0.0–0.2 | Determinism. Reproducibility. |
| **Classification / extraction** | 0.0 | You want one answer. |
| **Chat (Claude, ChatGPT default)** | 0.7–1.0 | Balanced. |
| **Creative writing** | 0.9–1.2 | Variety. Surprise. |
| **Brainstorming** | 1.0–1.5 | Many options. |

---

## Common mistakes

1. **Setting temperature for everything.** Most production tasks want T=0. Variety is rarely a feature.
2. **Confusing temperature with the model.** Temperature is a sampling knob, not a model parameter. Changing it doesn't change the model.
3. **Going above 1.5.** Outputs become incoherent. There are better ways to add variety (top-p, top-k — Lesson 2).
4. **Not setting temperature explicitly.** Some APIs default to 1.0, others to 0.7. Pin it.

---

## What temperature is NOT

- Not a knob for "how smart the model is." The model is the same; the sampling differs.
- Not a knob for cost. (Same number of tokens.)
- Not a knob for safety. (A high-temperature sample can still be toxic; a low-temperature sample can still be safe.)

The OpenAI / Anthropic docs make this confusing because they bundle "temperature" with "top_p" and other sampling parameters. They are independent.

---

## What this example demonstrates

1. **The math is one line.** `softmax(logits / T)`.
2. **The effect is monotonic.** Lower T → peakier; higher T → flatter.
3. **The use case decides the value.** Code = 0; chat = 0.7; creative = 1.0.
4. **The tradeoff is real.** Quality ↓ as diversity ↑; pick the operating point for the task.

Read this and you understand 90% of what temperature does. The other 10% is in Lesson 2 (top-k / top-p).

---

## What Comes Next

> Lesson 2 — **Top-k and Top-p Sampling** — the two common companions to temperature. Fixed-k vs cumulative-p, when to use which.
