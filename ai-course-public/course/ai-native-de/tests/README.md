# Test Suite

> **The test suite lives in each module.** Every lesson module ships with its own
> `test_*` functions (15-30 per module) and a `_review_100x.py` harness that
> exercises them under a 10-dimension Staff-level rubric.

---

## How to run

```bash
# All 19 modules, single iteration each (~30 seconds total)
cd course/ai-native-de/lessons
for d in m01-foundations m02-vector-math m03-embeddings m04-ann m05-ingestion \
         m06-chunking m07-retrieval m08-llm-fundamentals m09-rag-e2e \
         m10-evaluation m11-observability m12-security m13-agents-mcp \
         m14-data-platforms m15-staff-design m16-fullstack m17-product-metrics \
         m18-leadership m19-capstone; do
  pushd "$d" >/dev/null
  python3 _review_100x.py --iters 1
  popd >/dev/null
done

# One module, 100 iterations (full convergence review)
cd m09-rag-e2e
python3 _review_100x.py --iters 100

# One module, run only the lesson tests (no review harness)
cd m09-rag-e2e
python3 -c "
import sys, types
m = types.ModuleType('_L9'); sys.modules['_L9'] = m
exec(compile(open('L9-rag-end-to-end.py').read(), 'L9-rag-end-to-end.py', 'exec'), m.__dict__)
import inspect
for n, fn in inspect.getmembers(m, inspect.isfunction):
    if n.startswith('test_'):
        fn()
        print(f'  PASS  {n}')
"
```

---

## Per-module coverage

Every module has:

- **15-30 `test_*` functions** covering: correctness, math invariants,
  throughput, latency budgets, determinism, edge cases.
- **`_review_100x.py`** — a Staff-level review harness that scores the
  lesson across 10 dimensions and writes the trajectory to
  `../results/100x_review_<timestamp>.json` + `.md`.

| Module | Tests | Latest review |
|---|---:|---|
| M1 Foundations | 10 | [results/100x_review_2026-10-15T23-28-56Z.json](../results/100x_review_2026-10-15T23-28-56Z.json) |
| M2 Vector Math | 30 | [results/100x_review_2026-10-15T16-00-25Z.json](../results/100x_review_2026-10-15T16-00-25Z.json) |
| M3 Embeddings | 24 | [results/100x_review_2026-10-15T23-28-58Z.json](../results/100x_review_2026-10-15T23-28-58Z.json) |
| M4 ANN Internals | 25 | [results/100x_review_2026-10-15T23-29-00Z.json](../results/100x_review_2026-10-15T23-29-00Z.json) |
| M5 Ingestion | 34 | [results/100x_review_2026-10-15T16-50-15Z.json](../results/100x_review_2026-10-15T16-50-15Z.json) |
| M6 Chunking | 26 | [results/100x_review_2026-10-15T16-51-48Z.json](../results/100x_review_2026-10-15T16-51-48Z.json) |
| M7 Retrieval | 19 | [results/100x_review_2026-10-15T16-53-32Z.json](../results/100x_review_2026-10-15T16-53-32Z.json) |
| M8 LLM Fundamentals | 24 | [results/100x_review_2026-10-15T23-29-01Z.json](../results/100x_review_2026-10-15T23-29-01Z.json) |
| M9 RAG End-to-End | 22 | [results/100x_review_2026-10-15T17-02-01Z.json](../results/100x_review_2026-10-15T17-02-01Z.json) |
| M10 Evaluation | 27 | [results/100x_review_2026-10-15T17-05-25Z.json](../results/100x_review_2026-10-15T17-05-25Z.json) |
| M11 Observability | 22 | [results/100x_review_2026-10-15T17-11-36Z.json](../results/100x_review_2026-10-15T17-11-36Z.json) |
| M12 Security | 30 | [results/100x_review_2026-10-15T17-13-32Z.json](../results/100x_review_2026-10-15T17-13-32Z.json) |
| M13 Agents/MCP | 29 | [results/100x_review_2026-10-15T17-15-08Z.json](../results/100x_review_2026-10-15T17-15-08Z.json) |
| M14 Data Platforms | 25 | [results/100x_review_2026-10-15T17-17-09Z.json](../results/100x_review_2026-10-15T17-17-09Z.json) |
| M15 Staff Design | 29 | [results/100x_review_2026-10-15T23-29-02Z.json](../results/100x_review_2026-10-15T23-29-02Z.json) |
| M16 Full Stack | 30 | [results/100x_review_2026-10-15T23-29-03Z.json](../results/100x_review_2026-10-15T23-29-03Z.json) |
| M17 Product Metrics | 33 | [results/100x_review_2026-10-15T17-23-10Z.json](../results/100x_review_2026-10-15T17-23-10Z.json) |
| M18 Leadership | 34 | [results/100x_review_2026-10-15T17-27-40Z.json](../results/100x_review_2026-10-15T17-27-40Z.json) |
| M19 Capstone | 34 | [results/100x_review_2026-10-15T23-29-04Z.json](../results/100x_review_2026-10-15T23-29-04Z.json) |

Total: ~515 tests across 19 modules, all passing.

---

## What this `tests/` folder is for

This top-level folder is reserved for **cross-module** integration tests
(e.g. an end-to-end test that walks M1→M9→M11 in a single process).
The current curriculum keeps the test suite co-located with each lesson
so a learner running `python3 _review_100x.py` in a lesson folder gets
immediate feedback without searching the repo.

If you're contributing an integration test, place it here as
`test_<scenario>.py` with a `from lessons.m*_... import _L<N>` import path.

---

## Reference

- Review harness spec: see the docstring at the top of any `_review_100x.py`
- 10-dimension rubric (correctness, imports, types, tests, invariants, docs,
  observability, determinism, cost_latency, teachability): see
  `../results/M3.L3.review.json` for an example breakdown
- Capstone test plan: `../capstone/README.md` → "Evaluation rubric"

---

*Last updated: 2026-10-16*
*License: MIT*