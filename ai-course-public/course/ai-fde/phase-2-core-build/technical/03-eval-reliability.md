# Lesson 03 — Early Evaluation, Reliability, and Application-Layer Patterns

> **The drafter is grounded. Now measure it.** 50 minutes. Hands-on, runnable.

By the end of this lesson you can grade a RAG-augmented drafter against a **30-row eval set** using **4 RAGAS-style metrics**, save the result as a **baseline**, and **trip a regression check** if a future run drops more than 5% on any metric. The eval harness is also a `/eval` endpoint and a CLI — both run against the same code.

This is the lesson that turns "looks right to me" into "the eval says it's 0.83." Without it, every prompt change is a guess. With it, you have a number.

---

## 🎯 You will build

A `service/eval.py` that:
- Implements 4 deterministic metrics: **faithfulness**, **answer relevance**, **context precision**, **context recall**
- Runs the 30-row eval set through the service's `_draft_pipeline`
- Produces a markdown report with per-row + aggregate + per-category + per-difficulty breakdowns
- Saves a `baseline.jsonl` you can compare against
- Trips a regression flag if any metric drops by more than `threshold` vs. baseline
- Exits non-zero (suitable for CI) on regression

Plus a `/eval` endpoint in `app.py` and a CLI in `technical/03-eval-reliability.py` that both use it.

## 🧠 Concept (10 min)

You can't improve what you can't measure. For a RAG drafter, "looks right" doesn't scale — Mei gets tired, she's biased toward "this is good," and she can't grade 30 drafts after every prompt change. You need numbers.

**Four metrics, four questions:**

| Metric | Question it answers | Formula |
|---|---|---|
| **Faithfulness** | Did the model stick to the retrieved context, or did it make stuff up? | fraction of answer content-tokens present in any context |
| **Answer relevance** | Did the answer address the question? | Jaccard overlap between question tokens and answer tokens |
| **Context precision** | Did the retriever return *relevant* chunks? | fraction of retrieved contexts that contain at least one expected-mention |
| **Context recall** | Did the retriever return *all the relevant info*? | fraction of expected-mention tokens found in any retrieved context |

These are **deterministic** — no LLM in the loop, so they run in milliseconds and produce the same number every time. (Phase 3 swaps in an LLM-as-judge for finer-grained faithfulness; the 1000-line version is at `course/hardcode/level-8-evaluation-testing/11-llm-as-judge-eval.py`.)

**The eval set** is 30 rows, each one an (email, expected_intent, expected_shipment_id, expected_mentions) tuple. The `expected_mentions` are the tokens that **must** appear in a correct answer — for PF-1003 that's `["PF-1003", "customs", "duty", "Mei Lin"]`. The metrics check whether the retrieved chunks + the generated draft cover those tokens.

**The regression check** is the part that makes the eval *useful in CI*:

> If today's `context_precision` is 0.62 and last week's was 0.71, the prompt change you made yesterday broke retrieval. **Block the deploy.**

`threshold=0.05` means: trip if a metric dropped by more than 5 percentage points. (Tighten to 0.02 in Phase 3 when the eval set is bigger and the variance is better understood.)

## 🛠️ Build It (35 min)

### Step 1 — read the eval set (5 min)

Open [`../shared/eval_set.jsonl`](../shared/eval_set.jsonl). 30 rows. Categories: 10 clean, 10 messy, 10 edge. Difficulties: 10 easy, 11 medium, 9 hard. All 13 PF IDs the customer references exist in the tracker.

Each row:
```json
{
  "id": "eval-013",
  "category": "messy",
  "difficulty": "medium",
  "email": "PF  - 1003  \nthis has been stuck for a week. when will it move? — Mei Lin",
  "expected_intent": "status_inquiry",
  "expected_shipment_id": "PF-1003",
  "expected_mentions": ["PF-1003", "customs", "Mei Lin"]
}
```

> **FDE tip:** the eval set is **frozen**. Once you commit it, you don't add rows to it (you create a new eval set for the next phase). The point of a frozen set is that today's number is comparable to last week's number.

### Step 2 — implement the 4 metrics (15 min)

[`../service/eval.py`](../service/eval.py), lines 70-130. The two interesting ones:

```python
def context_precision(contexts: list[str], expected_mentions: list[str]) -> float:
    if not contexts:
        return 0.0
    expected = [m.lower() for m in expected_mentions or []]
    if not expected:
        return 0.0
    hits = sum(1 for c in contexts if any(m in c.lower() for m in expected))
    return round(hits / len(contexts), 4)


def context_recall(contexts: list[str], expected_mentions: list[str]) -> float:
    expected = [m.lower() for m in expected_mentions or []]
    if not expected:
        return 0.0
    ctx_text = " ".join(contexts).lower()
    found = sum(1 for m in expected if m in ctx_text)
    return round(found / len(expected), 4)
```

**Precision** asks: of the chunks I retrieved, how many were useful? **Recall** asks: of the facts I needed, how many did I retrieve?

Both are needed. A system can have 100% precision (it always returns the right chunk) but 0% recall (it only ever returns 1 chunk when it should return 3). Vice versa too: 100% recall (it always returns 50 chunks) but 0% precision (most of them are irrelevant).

### Step 3 — implement `run_eval` (10 min)

Same file. The function takes a `draft_fn(row) -> {draft, contexts}` and the eval rows:

```python
def run_eval(draft_fn, rows, *, verbose=False) -> Aggregate:
    per_row = []
    for row in rows:
        try:
            out = draft_fn(row)
            draft = out.get("draft", "") or ""
            contexts = out.get("contexts", []) or []
        except Exception as exc:
            draft, contexts = "", []
            err = f"{type(exc).__name__}: {exc}"
        ...
        result = RowResult(
            id=row["id"], ...
            faithfulness=faithfulness(draft, contexts),
            answer_relevance=answer_relevance(row["email"], draft),
            context_precision=context_precision(contexts, row.get("expected_mentions", [])),
            context_recall=context_recall(contexts, row.get("expected_mentions", [])),
            ...
        )
        per_row.append(result)
    return _aggregate(per_row, ...)
```

> **FDE trap:** the `try/except` around `draft_fn(row)` is intentional. One bad row (e.g. an LLM timeout on row 17) should NOT kill the whole eval. The error gets captured into `row.error`, the eval continues, and the report shows which row failed. **An eval that crashes on the first error is worse than no eval** — it gives the team false confidence.

### Step 4 — implement the regression check (5 min)

Same file, lines 175-200:

```python
def run_regression_check(aggregate, baseline, threshold) -> list[Regression]:
    if baseline is None:
        return []
    metrics = ["faithfulness", "answer_relevance", "context_precision", "context_recall"]
    out = []
    for m in metrics:
        cur = getattr(aggregate, m)
        base = getattr(baseline, m)
        delta = round(cur - base, 4)
        out.append(Regression(
            metric=m, current=cur, baseline=base, delta=delta,
            threshold=threshold, regressed=delta <= -threshold,
        ))
    return out
```

A metric is **regressed** if `current - baseline <= -threshold`. The minus sign is the key: we care about drops, not improvements (improvements don't block deploys, but they're worth flagging in the report).

### Step 5 — write the CLI (5 min)

[`technical/03-eval-reliability.py`](./03-eval-reliability.py) is a 60-line CLI that wraps `eval.py`:

```bash
python3 03-eval-reliability.py --set ../shared/eval_set.jsonl --report eval_report.md
# → faithfulness=0.41  ansrel=0.04  ctxp=0.62  ctxr=0.60
# → wrote report to eval_report.md

python3 03-eval-reliability.py --set ../shared/eval_set.jsonl \
                               --save-baseline baseline.jsonl \
                               --report eval_report.md
# → same metrics + saves baseline.jsonl

python3 03-eval-reliability.py --set ../shared/eval_set.jsonl \
                               --baseline baseline.jsonl --threshold 0.05 \
                               --report eval_report.md
# → exits non-zero if any metric regressed
```

The CLI is what runs in CI: every PR runs the eval, compares to the baseline, and the build fails on regression.

### Step 6 — wire the `/eval` endpoint (5 min)

In `app.py`:

```python
@app.post("/eval")
def run_eval(req: EvalRequest) -> dict:
    rows = [...]
    aggregate = eval_mod.run_eval(_service_draft_fn, rows)
    baseline_agg = ...  # load baseline.jsonl if provided
    regressions = eval_mod.run_regression_check(aggregate, baseline_agg, req.threshold)
    md = eval_mod.render_report(aggregate, regressions, req.threshold)
    return {"ok": True, "faithfulness": aggregate.faithfulness, ...,
            "any_regressed": any(r.regressed for r in regressions),
            "report_markdown": md}
```

Test:
```bash
curl -X POST localhost:8000/eval -H 'Content-Type: application/json' \
     -d '{"set":"../shared/eval_set.jsonl"}' | head -c 800
# → {"ok":true, "n_rows":30, "n_errors":0,
#    "faithfulness":0.41, "answer_relevance":0.04,
#    "context_precision":0.62, "context_recall":0.60,
#    "regressions":[], "any_regressed":false, ...}
```

### Step 7 — write the regression tests (5 min)

[`../service/tests/test_app.py`](../service/tests/test_app.py), lines 95-140. Two regression tests:

```python
def test_eval_runs(eval_set_path):
    r = client.post("/eval", json={"set": str(eval_set_path)})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["n_rows"] == 30
    assert body["n_errors"] == 0

def test_regression_trips(eval_set_path, tmp_path):
    baseline = tmp_path / "high_baseline.jsonl"
    baseline.write_text(...)  # artificially high baseline
    r = client.post("/eval", json={"set": ..., "baseline": ..., "threshold": 0.05})
    body = r.json()
    assert body["any_regressed"] is True
```

Run them:
```bash
cd ../service && pytest tests/ -v
# → 8 passed in 1.13s
```

## 🏛️ FDE Lens

> **What to put in the eval set, and what NOT to put in it.**

The eval set is the FDE's most opinionated deliverable. The right size for Phase 2 is **20-50 rows**. The right shape:

| Bucket | Examples | Why |
|---|---|---|
| **Clean** (10) | "Where is PF-1001?" | Happy path; sets the floor for metrics |
| **Messy** (10) | "PF-1001 missing!" or multi-shipment email | Tests the regex + retrieval |
| **Edge** (10) | Out-of-scope, no ID, angry customer | Tests the policy "never do X" rules |

What NOT to put in it:

- **Don't put synthetic paraphrases** ("Where is my order?" is the same eval as "Where's my parcel?" — pick one)
- **Don't put real customer data** without scrubbing PII (Phase 3's responsibility)
- **Don't put rows the drafter is tuned to ace** (the set must stay hard; tune by improving the drafter, not by tweaking the set)
- **Don't put the entire distribution** — 30 rows is enough to catch a 5% regression; if you want 0.5% precision, you need 1000 rows (Phase 3's problem)

The FDE who writes a frozen, balanced, opinionated eval set in week 1 is the FDE who catches a 5% regression in week 4 — *before the customer does.*

## 🌙 Reflect

Write 3-5 sentences:

1. The eval runs 4 deterministic metrics in ~50ms. Real LLM-as-judge metrics take 5-10 seconds per row. When is the deterministic metric the right call, and when do you need the LLM judge?
2. `context_precision` asks "of the chunks I returned, how many were useful?" — but the mock vector store returns a fixed top-k. What does that mean for the metric's usefulness?
3. The eval captures exceptions into `row.error` instead of crashing. What's the worst-case consequence of NOT doing this?
4. The regression threshold is 0.05 (5 percentage points). Too tight and CI breaks on noise; too loose and you ship regressions. How would you set the right threshold for a NEW eval set you've never run before?
5. The eval set is committed to the repo. The eval baseline is a separate file (`baseline.jsonl`). Why split them?

**What's next** — Phase 3 (next phase) adds the production rollout: streaming responses, real vector DB, auth, rate limiting, observability with LangSmith. The Phase 2 service is the smallest end-to-end thing that proves the system survives a customer pilot; Phase 3 proves it survives a rollout. From here, the existing **`course/hardcode/level-8-evaluation-testing/`** track is the 1000-line production version of this lesson (RAGAS, LLM-as-judge, A/B testing, markdown reports).
