# Lesson 1 — Prompts as Code

> **Type:** Article + Worked Example · Course 3
> Why prompts belong in version-controlled Python files, not in chat boxes. And a complete A/B test framework for prompt engineering at scale.

---

## The thesis

**Prompts are production code.** They have versions, owners, eval gates, and SLAs. Treating them as "magic strings a developer typed into a chat box" is how you ship silent regressions.

The shift is from **prompt-as-message** to **prompt-as-template**:

```
   prompt-as-message:                     prompt-as-template:
   ──────────────────                     ────────────────────
   "Hey Claude, classify this             chat_prompt = ChatPromptTemplate.from_messages([
   email as billing or auth..."               ("system", SYSTEM_PROMPT),
                                              ("human", "Email:\n{email_text}\n\nLabel:"),
                                          ])
                                          response = chain.invoke({"email_text": email})
```

The template is version-controlled, testable, and reusable. The message is not.

---

## The anatomy of a production prompt

```
   ┌──────────────────────────────────────────────────────────┐
   │  PRODUCTION PROMPT                                        │
   │                                                          │
   │   SYSTEM (role + constraints + edge cases + few-shot)     │
   │      │                                                   │
   │      ├──► Role          "You are an email classifier"    │
   │      ├──► Task          "Classify into one of N labels"  │
   │      ├──► Constraints   "Return only the label, no prose"│
   │      ├──► Edge cases    "If unclear, return 'unknown'"   │
   │      └──► Few-shot      3-5 examples, dynamically loaded│
   │                                                          │
   │   USER (the actual input)                                │
   │      │                                                   │
   │      ├──► Context       any retrieved docs / data        │
   │      └──► Question      the actual task                 │
   │                                                          │
   │   (optional) ASSISTANT prefill                          │
   │      │                                                   │
   │      └──► "Label: "    controls the start of output     │
   │                                                          │
   └──────────────────────────────────────────────────────────┘
```

Every part is a lever. The system prompt is the lever most teams under-use.

---

## ChatPromptTemplate — the canonical structure

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", """You classify customer support emails for a SaaS company.

LABELS:
- billing:    questions about invoices, refunds, payment failures
- auth:       login, password reset, MFA, account lockout
- bug:        reports of broken behavior with reproducible steps
- how_to:     questions about using a feature
- feature_request: suggestions for new functionality
- unknown:    anything you can't classify confidently

CONSTRAINTS:
- Return ONLY the label, lowercase, no punctuation
- If the email is ambiguous, return "unknown"
- Do not invent categories

{format_instructions}"""),
    ("human", """From: {sender}
Subject: {subject}

{body}

Label:"""),
])
```

Three properties this prompt has:
1. **Explicit constraints.** No "be brief" or "be careful"; concrete rules.
2. **Edge case handled.** "ambiguous → unknown" prevents hallucination.
3. **Output format fixed.** `{format_instructions}` from the parser is injected.

---

## Partials — variables resolved at chain build time

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert in {domain}."),
    ("human", "{question}"),
])

# Resolve {domain} once at startup
specialized_prompt = prompt.partial(domain="Stripe payments API")

# At call time, only {question} is required
specialized_prompt.invoke({"question": "What is a PaymentIntent?"})
```

Use `partial` for:
- Environment-specific values (`{today_date}`, `{model_version}`)
- Long, static context (`{company_policy_text}`)
- Constants resolved at deploy time

Don't use it for per-request values (those stay as runtime variables).

---

## Few-shot — dynamically loaded from a dataset

The mistake most teams make:

```python
# BAD: hardcoded few-shot examples in the prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "..."),
    # Examples baked in forever, version-controlled separately from data
    ("human", "Example 1 input..."),
    ("ai", "billing"),
    ("human", "Example 2 input..."),
    ("ai", "auth"),
    # ... 8 more
    ("human", "{actual_input}"),
])
```

The better way:

```python
# GOOD: few-shot examples loaded from a dataset at chain-build time
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

examples = load_jsonl("data/email_examples.jsonl")  # 200 hand-labeled emails

selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    OpenAIEmbeddings(model="text-embedding-3-small"),
    Chroma,
    k=3,                          # pick 3 most similar to the input
)

dynamic_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
] + selector.select_examples(...)  # populated at runtime
).partial(format_instructions=parser.get_format_instructions())
```

The dynamic selector picks the 3 most similar examples to the input email. Better coverage, less prompt bloat, and **the examples evolve with the data**.

---

## Jinja templating — when static templates aren't enough

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("""
{% for doc in documents -%}
Source {{ loop.index }}: {{ doc.title }}
{{ doc.content }}
{% endfor -%}

Question: {{ question }}

Answer using ONLY the sources above.
""", template_format="jinja2")
```

Jinja is useful for:
- Lists of documents (RAG, multi-source)
- Conditional sections (`{% if has_history %}`)
- Loops over few-shot examples

Use sparingly. Plain `{variable}` is clearer.

---

## The "prompt versioning" practice

```
   prompts/
   ├── email_classifier/
   │   ├── v1/
   │   │   ├── system.txt
   │   │   ├── few_shot.jsonl
   │   │   ├── CHANGELOG.md
   │   │   └── eval_results.json   ← pinned to a LangSmith experiment
   │   ├── v2/
   │   │   ├── system.txt          ← added edge-case handling
   │   │   ├── few_shot.jsonl      ← 50 new examples
   │   │   ├── CHANGELOG.md
   │   │   └── eval_results.json   ← +4pp exact-match
   │   └── PRODUCTION = v2         ← symlink or registry entry
```

Every prompt version is a directory. The eval results are checked in. The "production" pointer moves only after a human review and an eval pass.

This is what "prompts as code" looks like in practice.

---

## Prompt evaluation — the A/B test framework

The single most useful pattern in this course is **multi-arm bandit over prompts**:

```python
# eval/multi_arm_bandit.py
from langsmith import evaluate
from prompts.email_classifier import v1_chain, v2_chain, v3_chain, v4_chain

results = {}
for name, chain in [("v1_zero_shot", v1_chain),
                     ("v2_few_shot", v2_chain),
                     ("v3_cot", v3_chain),
                     ("v4_json_mode", v4_chain)]:
    results[name] = evaluate(
        chain.invoke,
        data="email-classification.v1",
        evaluators=[exact_match, llm_judge],
        experiment_prefix=f"email-{name}",
    )

# Output: leaderboard
#   v1_zero_shot:   exact=0.71  judge=3.4   cost=$0.0001
#   v2_few_shot:    exact=0.83  judge=3.9   cost=$0.0002
#   v3_cot:         exact=0.85  judge=4.1   cost=$0.0006  ← best quality
#   v4_json_mode:   exact=0.84  judge=3.9   cost=$0.0002  ← best quality/cost
```

You ship `v4_json_mode` (best quality-per-dollar). You keep `v3_cot` for the hard cases (route by input difficulty).

---

## Worked Example — customer-email classifier with 4-way A/B test

> **Goal:** Classify inbound customer emails into 6 labels (billing, auth, bug, how_to, feature_request, unknown). Compare 4 prompt strategies on the same 200-email eval set. Ship the winner.

### Step 1 — The eval set

```python
# eval/dataset.py
import json

# 200 hand-labeled emails, hand-curated to match production distribution:
#   - 30% billing, 20% auth, 20% bug, 15% how_to, 10% feature_request, 5% unknown
EMAILS = [json.loads(line) for line in open("data/email_eval_v1.jsonl")]

# Each: {"inputs": {"sender", "subject", "body"}, "outputs": {"label"}}
```

The distribution matches production. The set has 10 deliberately ambiguous emails to test the "unknown" path.

### Step 2 — The four prompt variants

```python
# prompts/email_v1_zero_shot.py
from langchain_core.prompts import ChatPromptTemplate

V1_ZERO_SHOT = ChatPromptTemplate.from_messages([
    ("system", """Classify the email into one of:
billing, auth, bug, how_to, feature_request, unknown.

Return ONLY the label."""),
    ("human", "Subject: {subject}\n\n{body}\n\nLabel:"),
])

# prompts/email_v2_few_shot.py
V2_FEW_SHOT = ChatPromptTemplate.from_messages([
    ("system", """Classify the email into one of:
billing, auth, bug, how_to, feature_request, unknown.

EXAMPLES:
Email: "My invoice #4421 has the wrong amount"
Label: billing

Email: "I can't log in, getting 'invalid credentials'"
Label: auth

Email: "The dashboard shows 500 error after clicking export"
Label: bug

Email: "How do I invite a teammate?"
Label: how_to

Email: "Would love a dark mode option"
Label: feature_request

Email: "Hi"
Label: unknown"""),
    ("human", "Subject: {subject}\n\n{body}\n\nLabel:"),
])

# prompts/email_v3_cot.py
V3_COT = ChatPromptTemplate.from_messages([
    ("system", """Classify the email into one of:
billing, auth, bug, how_to, feature_request, unknown.

Think step-by-step:
1. What is the user's primary ask?
2. Which category fits best?
3. Are there signals that suggest ambiguity?

Then return ONLY the label, no explanation."""),
    ("human", """Subject: {subject}

{body}

Reasoning:
1. Ask:"""),
])

# prompts/email_v4_json_mode.py
import json
from langchain_core.prompts import ChatPromptTemplate

V4_JSON = ChatPromptTemplate.from_messages([
    ("system", """Classify the email. Return JSON:
{{"label": "<one of: billing, auth, bug, how_to, feature_request, unknown>",
  "confidence": <0.0-1.0>,
  "reason": "<= 10 words>"}}"""),
    ("human", "Subject: {subject}\n\n{body}"),
])
```

### Step 3 — Build four chains

```python
# chains.py
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

from prompts.email_v1_zero_shot import V1_ZERO_SHOT
from prompts.email_v2_few_shot import V2_FEW_SHOT
from prompts.email_v3_cot import V3_COT
from prompts.email_v4_json_mode import V4_JSON

model = ChatAnthropic(model="claude-3-5-haiku-20241022", temperature=0)

chains = {
    "v1_zero_shot":   V1_ZERO_SHOT | model | StrOutputParser(),
    "v2_few_shot":    V2_FEW_SHOT | model | StrOutputParser(),
    "v3_cot":         V3_COT | model | StrOutputParser(),
    "v4_json_mode":   V4_JSON | model | JsonOutputParser(),
}
```

### Step 4 — Evaluators

```python
# evaluators.py
def exact_match(run, example):
    expected = example.outputs["label"].strip().lower()
    actual = run.outputs
    if isinstance(actual, dict):
        actual = actual.get("label", "").strip().lower()
    else:
        actual = actual.strip().lower()
    return {"key": "exact_match", "score": 1.0 if actual == expected else 0.0}

def confidence_calibration(run, example):
    """Did the model's confidence match its accuracy?"""
    if not isinstance(run.outputs, dict):
        return {"key": "calibration", "score": None}
    expected = example.outputs["label"]
    predicted = run.outputs.get("label", "").strip().lower()
    confidence = run.outputs.get("confidence", 0.5)
    correct = (expected == predicted)
    # Score = 1.0 if (correct and conf > 0.7) or (wrong and conf < 0.5)
    score = 1.0 if (correct and confidence >= 0.7) or \
                  (not correct and confidence < 0.5) else 0.0
    return {"key": "calibration", "score": score}
```

### Step 5 — Run the 4-way A/B test

```python
# eval/run_ab.py
from langsmith import evaluate
from chains import chains
from evaluators import exact_match, confidence_calibration

results = {}
for name, chain in chains.items():
    results[name] = evaluate(
        chain.invoke,
        data="email-classification.v1",
        evaluators=[exact_match, confidence_calibration],
        experiment_prefix=f"email-{name}",
        max_concurrency=8,
    )

# Print leaderboard
for name, r in results.items():
    print(f"{name:18}  exact={r['exact_match']['mean']:.3f}  "
          f"cal={r['calibration']['mean']:.3f}  "
          f"cost=${r['total_cost']:.2f}")
```

### Step 6 — The results (sample)

```
   v1_zero_shot      exact=0.708  cal=0.612  cost=$0.018
   v2_few_shot       exact=0.834  cal=0.703  cost=$0.024
   v3_cot            exact=0.851  cal=0.728  cost=$0.071    ← 4× cost
   v4_json_mode      exact=0.842  cal=0.811  cost=$0.025    ← best cal
```

### Step 7 — The decision matrix

| Variant | Exact-match | Calibration | Cost/1K | Verdict |
|---|---|---|---|---|
| **v1 zero-shot** | 0.708 | 0.612 | $0.09 | Baseline. Too weak. |
| **v2 few-shot** | 0.834 | 0.703 | $0.12 | Big jump from baseline. **Strong default.** |
| **v3 CoT** | 0.851 | 0.728 | $0.47 | Best raw accuracy but 4× cost. **Route hard cases here.** |
| **v4 JSON-mode** | 0.842 | **0.811** | $0.13 | Best calibration. **Best for downstream automation.** |

**Decision:** ship **v4_json_mode** as default (best calibration → downstream automations trust the output), route to **v3_cot** for emails flagged "complex" by an upstream classifier, retire **v1** and **v2**.

The decision was driven by the eval results, not by vibes. **That's the entire point of this course.**

### Step 8 — Production wiring with prompt versioning

```python
# prompts/registry.py
import json

# PRODUCTION points to the latest, validated prompt version
PRODUCTION = {
    "email_classifier": {
        "default": "v4_json_mode",
        "complex_router": "v3_cot",
        "fallback": "v2_few_shot",
        "approved_at": "2026-09-15",
        "approved_by": "ml-platform@",
        "eval_experiment": "email-v4_json_mode-2026-09-14",
    }
}

def get_prompt_version(task: str, mode: str = "default") -> str:
    return PRODUCTION[task][mode]
```

Every chain in production reads from this registry. Changing prompts is a PR. The PR's CI gate runs the eval; the merge is blocked if the eval fails.

### Step 9 — Cost roll-up

```
   Production: 100K emails/day, classified via v4 (default) + v3 (complex)
   ──────────────────────────────────────────────────────────────────
   v4 default (90%): 90K × $0.00013  = $11.70/day
   v3 complex (10%): 10K × $0.00047  = $4.70/day
   Total: $16.40/day = $492/mo for 3M emails/month

   Per-email cost: $0.00016

   Cheaper than a human triage agent by 1000×.
```

### What this example demonstrates

1. **Four prompt strategies, one eval set, one decision.** A/B testing prompts is the discipline.
2. **Calibration matters as much as accuracy.** A model that knows when it's wrong is more valuable than one that's slightly more often right.
3. **The default is rarely the best.** Production routing uses tiered models (Course 5 covers tool use + routing).
4. **Cost is part of the score.** "Best accuracy" without cost is not a system.
5. **The prompt registry is the contract.** Every chain reads from it; every change is a PR.

Read this example and you understand prompt engineering at scale: not "clever wording," but **versioned templates, dynamic few-shot, eval-driven selection, and tiered production routing.**

---

## What Comes Next

> Lesson 2 — **Zero-shot vs few-shot** — when each shines, the format pitfalls that silently break few-shot, and the "5-shot is usually enough" rule.
