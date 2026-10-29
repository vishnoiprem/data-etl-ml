# Lesson 1 — Why Eval Is the Moat

> **Type:** Article + Worked Example · Course 2
> Why every team that ships LLM apps eventually lands on the same answer: a curated eval set with CI gating. And a complete pipeline for one.

---

## The thesis

The eval set is the moat. Not the prompt, not the model, not the framework.

A 200-query, hand-labeled eval set with CI gating is what separates teams that **ship confidently** from teams that ship "we changed a prompt, three days later we noticed quality dropped." The latter is the default outcome at every company that treats eval as a "nice to have."

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   "the prompt"        ─► replaceable, takes 2 hours to swap  │
   │   "the model"         ─► replaceable, takes 1 day to swap    │
   │   "the eval set"      ─► takes 2 weeks to build,             │
   │                          pays back forever                   │
   │                                                              │
   └──────────────────────────────────────────────────────────────┘
```

Anyone with a few hours and an OpenAI key can write a prompt. Almost no one has built a 200-query set that survives contact with reality. **The set is what you own.**

---

## The three failure modes eval prevents

### 1. The "we tweaked the prompt and didn't notice"

```
   before tweak:   prompt v17, exact-match = 0.91
   after tweak:    prompt v18, exact-match = 0.84   ← no one noticed
   2 weeks later:  "support quality is bad, what changed?"
```

This is the most common LLM failure in production. The team changed a prompt, deployed, and the regression was silent for weeks. Eval with CI gating catches it at PR time.

### 2. The "the new model is better" fallacy

```
   engineer:  "let's swap Haiku for Sonnet"
   manager:   "is it better?"
   engineer:  "I tried it on 5 examples, looks better"
   manager:   "..."
```

Without a controlled experiment on a held-out set, "looks better" is anecdote. Eval turns it into a number — and lets you decide based on cost vs quality.

### 3. The silent vendor update

```
   Monday:    Claude Haiku 4.5 returns JSON correctly
   Tuesday:   Anthropic ships a quiet update
   Wednesday: 8% of outputs now have malformed JSON
   Thursday:  customer escalation
```

Pinning model versions and running eval nightly catches vendor drift. The eval set is your canary.

---

## The eval-first vs eval-last comparison

```
   EVAL-LAST (the default)                  EVAL-FIRST (this course)
   ────────────────────────                 ──────────────────────────
   1. Build the feature                     1. Define the eval set
   2. Build it more                         2. Run eval (score = 0%)
   3. Build it again                        3. Build the feature
   4. "Looks good" → ship                   4. Run eval (score = 87%)
   5. Production breaks                     5. CI gate ≥ 85%
   6. Discover the bug                      6. Ship
   7. Fix                                   7. Monitor
   8. "Looks good" → ship again             8. Drift detected → eval catches it
   9. Repeat

   Time to first confident ship:   weeks       Time to first confident ship:   days
```

Eval-first is faster because **you're not debugging in production**. The eval set is your test suite; you build against it.

---

## What goes into a good eval set

| Property | Why it matters |
|---|---|
| **Hand-labeled ground truth** | Anything less is "the LLM graded itself" |
| **Diverse coverage** | Easy cases + hard cases + adversarial cases |
| **Real production distribution** | Curated to match what users actually send |
| **Refreshed quarterly** | Domain drifts, vendors drift, language drifts |
| **Versioned** | You can roll back to a known-good baseline |
| **Stable IDs** | Examples survive pipeline changes |

A 200-query set is the typical starting point. Smaller is fine if the queries are diverse; larger is fine if you have budget. The key is **coverage** — every failure mode you've seen in production should be represented.

---

## The four evaluator types

```
   EVALUATOR             WHAT IT SCORES              WHEN TO USE
   ─────────             ──────────────              ──────────
   Code-based            Exact match, regex,         Structured output
                         JSON schema validation      (Pydantic fields)

   Embedding-distance    Cosine similarity,          Free-text fields
                         BERTScore                   (summary, paraphrase)

   LLM-as-judge          "Is this answer correct     Anything where the
                         per this rubric?"           right answer is fuzzy
                                                     but a rubric can capture it

   Human                 Manual rating,              Final calibration;
                         pairwise preference         continuous improvement
```

Most production eval harnesses combine all four:
- Code-based for structured fields (priority, category).
- Embedding-distance for "did the model stay on-topic."
- LLM-as-judge for "is the answer actually helpful."
- Human for spot-checking the LLM-as-judge itself.

---

## The eval-driven development loop

```
   ┌─────────────────────────────────────────────────────┐
   │ 1. WRITE EVAL EXAMPLE                                │
   │    - hand-label a real production query              │
   │    - this IS the spec                                │
   │                                                      │
   │ 2. RUN EVAL                                          │
   │    - execute the current chain against the example   │
   │    - compute the scores                              │
   │                                                      │
   │ 3. INSPECT FAILURES                                  │
   │    - read the trace, see where the chain went wrong  │
   │    - identify the gap (prompt? parser? data?)        │
   │                                                      │
   │ 4. IMPROVE                                           │
   │    - change the prompt, the schema, the model        │
   │    - one variable at a time                          │
   │                                                      │
   │ 5. RE-RUN EVAL                                       │
   │    - confirm the score went up                       │
   │    - confirm no other examples regressed             │
   │                                                      │
   │ 6. COMMIT                                            │
   │    - eval result is in the PR description             │
   │    - CI blocks the merge if score < threshold        │
   └─────────────────────────────────────────────────────┘
```

This is the loop every LLM team runs hundreds of times. The eval set gets longer; the chain gets better; regressions get caught.

---

## Common eval mistakes

1. **Test set too small.** 20 examples is a vibe check. 200 is a system.
2. **Test set too uniform.** Only "easy" examples. The set needs adversarial cases.
3. **LLM-as-judge without calibration.** The judge model has its own biases. Calibrate against humans monthly.
4. **No baseline.** "Score = 0.87" means nothing without "baseline was 0.84, this is +3%."
5. **No CI gate.** Eval that runs nightly but doesn't block PRs is documentation, not engineering.
6. **No drift detection.** Prod queries drift; eval set doesn't. Both must move.
7. **Treating eval as "we'll add it later."** Later is never.

---

## Worked Example — CI-gated eval pipeline, model swap Haiku → Sonnet

> **Goal:** Decide whether to swap Claude Haiku 4.5 → Claude Sonnet 4.5 for the support-ticket triage chain from Course 1. Use a 200-query LangSmith dataset, run both models, gate the swap on exact-match ≥ 0.92 AND summary-judge ≥ 4.2. Cost roll-up included.

### Step 1 — Upload the eval set to LangSmith

```python
# eval/upload_dataset.py
from langsmith import Client
from pydantic import BaseModel
import json

client = Client()

# Define schema (matches Course 1's TriageResult)
class EvalExample(BaseModel):
    inputs: dict
    outputs: dict

# 200 hand-labeled examples
EXAMPLES = json.load(open("data/triage_eval_v1.jsonl"))

dataset = client.upload_dataset(
    dataset_name="support-ticket-triage.v1",
    description="200 hand-labeled support tickets. Refreshed 2026-Q3.",
)

client.upload_examples(
    dataset_id=dataset.id,
    examples=EXAMPLES,
)
```

The dataset is **versioned** in LangSmith. `triage_eval.v1` is the baseline; `v2` is the next refresh. The evaluator references the dataset by name, not by id.

### Step 2 — Define the evaluators

```python
# eval/evaluators.py
from langsmith.evaluation import LangChainStringEvaluator
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

# 1. Code-based: exact match on structured fields
def exact_match(run, example):
    """Compare priority, category, sentiment, confidence."""
    expected = example.outputs["triage"]
    actual = run.outputs["triage"]
    score = sum([
        expected["priority"] == actual["priority"],
        expected["category"] == actual["category"],
        expected["sentiment"] == actual["sentiment"],
        abs(expected["confidence"] - actual["confidence"]) < 0.1,
    ]) / 4
    return {"key": "exact_match", "score": score}

# 2. Code-based: schema validity (did we even get parseable output?)
def schema_valid(run, example):
    """Return 1.0 if all required fields are present and types match."""
    try:
        t = run.outputs["triage"]
        assert 0.0 <= t["confidence"] <= 1.0
        assert t["priority"] in {"p1", "p2", "p3"}
        assert isinstance(t["summary"], str)
        return {"key": "schema_valid", "score": 1.0}
    except Exception:
        return {"key": "schema_valid", "score": 0.0}

# 3. LLM-as-judge: summary quality
judge_llm = ChatAnthropic(model="claude-3-5-haiku-20241022", temperature=0)
summary_judge = LangChainStringEvaluator(
    "labeled_score_string",
    config={
        "criteria": {
            "summary": (
                "Is the summary ≤ 20 words, accurate to the ticket, and "
                "captures the user's actual ask without filler?"
            )
        },
        "normalize_by": 5,
        "llm": judge_llm,
    },
)

EVALUATORS = [exact_match, schema_valid, summary_judge]
```

The LLM-as-judge is a **separate model** from the one under test. Otherwise you're grading your own homework.

### Step 3 — Define the chains under test

```python
# eval/chains_under_test.py
from langchain_anthropic import ChatAnthropic
from triage.chain import build_chain

haiku_chain = build_chain(
    model=ChatAnthropic(model="claude-3-5-haiku-20241022", temperature=0)
)
sonnet_chain = build_chain(
    model=ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
)
```

`build_chain` is a factory so we can swap models without duplicating the prompt and parser logic. Same chain, different model.

### Step 4 — Run the experiment

```python
# eval/run_experiment.py
from langsmith import evaluate
from chains_under_test import haiku_chain, sonnet_chain
from evaluators import EVALUATORS
import argparse

def run(model_name: str, chain):
    results = evaluate(
        chain.invoke,
        data="support-ticket-triage.v1",
        evaluators=EVALUATORS,
        experiment_prefix=f"triage-{model_name}",
        metadata={
            "model": model_name,
            "eval_set_version": "v1",
            "num_examples": 200,
        },
        max_concurrency=8,        # parallel calls
    )
    return results

if __name__ == "__main__":
    haiku_results = run("haiku-4-5", haiku_chain)
    sonnet_results = run("sonnet-4-5", sonnet_chain)

    print(f"Haiku:  exact={haiku_results['exact_match']['mean']:.3f}  "
          f"schema={haiku_results['schema_valid']['mean']:.3f}  "
          f"summary={haiku_results['summary_judge']['mean']:.2f}")
    print(f"Sonnet: exact={sonnet_results['exact_match']['mean']:.3f}  "
          f"schema={sonnet_results['schema_valid']['mean']:.3f}  "
          f"summary={sonnet_results['summary_judge']['mean']:.2f}")
```

LangSmith runs both chains in parallel. Each run is logged with full trace, cost, latency, and the per-example scores.

### Step 5 — Read the results

Sample output:

```
   Haiku:  exact=0.873  schema=0.985  summary=3.92  cost=$0.16  latency_p95=820ms
   Sonnet: exact=0.924  schema=0.995  summary=4.31  cost=$2.14  latency_p95=1450ms
```

Reading this:

| Metric | Haiku | Sonnet | Δ | Decision |
|---|---|---|---|---|
| **Exact match** | 0.873 | **0.924** | +5.1pp | Sonnet wins, **above 0.92 gate** |
| Schema valid | 0.985 | 0.995 | +1pp | Sonnet wins (negligible) |
| Summary judge | 3.92 | **4.31** | +0.39 | Sonnet wins, **above 4.2 gate** |
| **Cost** | $0.16 | **$2.14** | **+13×** | Haiku wins |
| **Latency p95** | 820ms | **1450ms** | +77% | Haiku wins |

**Decision:** Sonnet passes both quality gates but costs 13× more and is 77% slower. Do we swap?

That depends on:
- Is the +5pp exact-match worth $2k/mo extra at 50K tickets/day?
- Is +630ms p95 latency a UX problem?

If the answer is yes on both, swap. If only on one, route the **hard tickets** to Sonnet and the easy ones to Haiku (a tiered model pattern from Module 8 of `11-learn-ai-data/`).

### Step 6 — CI gate

```yaml
# .github/workflows/eval.yml
name: llm-eval
on:
  pull_request:
    paths:
      - 'triage/**'
      - 'eval/**'

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install deps
        run: pip install -r requirements.txt

      - name: Run eval
        env:
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python eval/run_experiment.py --output ci_results.json

      - name: Quality gate
        run: |
          python -c "
          import json
          r = json.load(open('ci_results.json'))
          assert r['exact_match'] >= 0.90, f'exact_match regressed: {r[\"exact_match\"]}'
          assert r['schema_valid'] >= 0.98, f'schema_valid regressed: {r[\"schema_valid\"]}'
          assert r['summary_judge'] >= 4.0, f'summary regressed: {r[\"summary_judge\"]}'
          "

      - name: Comment on PR
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const results = require('./ci_results.json');
            const body = `### LLM Eval Results\n\n` +
              `| Metric | Value | Threshold |\n|---|---|---|\n` +
              `| exact_match | ${results.exact_match} | ≥ 0.90 |\n` +
              `| schema_valid | ${results.schema_valid} | ≥ 0.98 |\n` +
              `| summary_judge | ${results.summary_judge} | ≥ 4.0 |\n`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body,
            });
```

The PR is **blocked** if exact-match drops below 0.90. The eval result is **posted as a comment** so reviewers see the numbers without leaving GitHub.

### Step 7 — Cost roll-up for the decision

```
   At 50K tickets/day, 1.5M tickets/month:

   HAiku 4.5
   ─────────
   Per-ticket cost: $0.0008
   Monthly:          $1,200
   Exact-match:      87.3%
   Summary judge:    3.92

   SONNET 4.5
   ────────────
   Per-ticket cost: $0.012
   Monthly:          $18,000
   Exact-match:      92.4%
   Summary judge:    4.31

   Delta: +$16,800/mo for +5.1pp exact-match
   That's $3,300 per percentage point. Cheap if revenue depends on it; expensive if it doesn't.
```

A real eval result with a real cost number attached is the artifact that goes to the budget review. Without it, you're arguing from vibes.

### Step 8 — The "what changes your mind" trigger

The eval should re-run on these triggers:

| Trigger | Why | What to do |
|---|---|---|
| Vendor ships a new model | The scoreboard shifts | Re-run, compare |
| Prompt changes | Direct quality risk | Re-run, gate |
| Eval set refreshes | Baseline shifts | Re-baseline, retune thresholds |
| Customer escalation spike | Prod is drifting | Add the new failure to the set |
| Monthly cadence | Catch silent drift | Re-run, alert if Δ > 2pp |

The eval set is alive. The thresholds are alive. The chain is alive. **Nothing about an LLM system is "set and forget."**

### What this example demonstrates

1. **The eval set is uploaded once and reused forever.** That's the moat.
2. **Evaluators mix code-based (cheap, deterministic) with LLM-as-judge (expensive, fuzzy).** Code-first, judge for soft fields.
3. **CI gating makes eval a real engineering artifact.** Without it, eval is documentation.
4. **The cost number is non-negotiable.** Quality without cost is not a system; it's a wish.
5. **The decision is "swap, don't swap, or route."** Eval gives you the data to make the call.

Read this example once and you understand the eval pipeline. Read it twice and you understand how to defend every model change to your manager.

---

## What Comes Next

> Lesson 2 — **LangSmith fundamentals** — projects, traces, runs, datasets, examples. The platform that hosts all of this.
