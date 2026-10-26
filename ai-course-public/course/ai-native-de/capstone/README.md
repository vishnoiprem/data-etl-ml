# M19 Capstone: Secure Enterprise AI Assistant

> **Promise:** Wire the 18 prior modules into one working "Ask the company docs" assistant. Skip any one of the four wrappers and you ship a vulnerability.

**Audience:** Engineers who have finished M1-M18 and want to prove they can ship a production-shaped AI system end-to-end.

**Bar:** Defensible, runnable, testable — not a research artifact.

---

## What you'll build

A `secure-enterprise-ai-assistant` Python project that exposes a single
`/ask` endpoint backed by:

1. **Ingestion** (M5) — fixed-window chunker, hash dedupe, DLQ
2. **Embedding** (M3) — hash-based fake embedder (no API keys)
3. **Retrieval** (M7) — top-K cosine with ACL pre-filter
4. **Security** (M12) — prompt-injection sanitizer + audit log
5. **RAG** (M9) — prompt template + mock LLM
6. **Cost ceiling** (M11) — per-user budget, raise on overrun
7. **Observability** (M11) — structured per-call log (user_id, retrieved_ids, n_redactions, cost_ms)

The full architecture diagram and wiring is in [`lessons/m19-capstone/L19-capstone.md`](../lessons/m19-capstone/L19-capstone.md) and the runnable demo is `lessons/m19-capstone/L19-capstone.py`.

---

## The four wrappers (required)

Any "ask your docs" assistant must have **all four** of these — not three, not two:

| Wrapper | Module | Why required |
|---|---|---|
| **ACL** at retrieval time | M12 | Once a chunk is in the prompt, the LLM will read it. Filter before retrieval. |
| **Prompt-injection sanitizer** | M12 | `ignore previous instructions` must never reach the LLM. Strip patterns, log redactions. |
| **Per-user cost ceiling** | M11 | A runaway agent loop can burn $10K in an afternoon. Budget, raise on overrun, alert on breach. |
| **Structured audit log** | M11 | No log = no debug, no audit, no compliance. Every call: user_id, retrieved_ids, cost_ms. |

A raw LLM call without these four wrappers is a **prototype**, not a product. It cannot ship.

---

## Project architecture

```
secure-enterprise-ai-assistant/
├── README.md                # 90-second walkthrough
├── pyproject.toml           # pinned deps
├── docker-compose.yml       # optional: postgres + chroma + ollama
├── src/
│   ├── ingest/              # PDF/HTML/text -> chunks -> embeddings
│   ├── retrieval/           # BM25 + dense + RRF + ACL
│   ├── generation/          # prompt assembly + citation
│   ├── agent/               # tool-use agent with approval gate
│   ├── eval/                # golden set + metrics
│   ├── observability/       # OTel + token accounting
│   └── api/                 # FastAPI routes
├── tests/                   # pytest
├── data/
│   ├── raw/                 # 10-100 synthetic docs
│   └── golden/              # 50 labeled Q/A pairs
└── notebooks/               # exploratory work
```

---

## Evaluation rubric (0-100)

| Dimension | Weight | What we look for |
|---|---:|---|
| Correctness (code runs, tests pass) | 25 | All pytest pass; smoke test of the API works |
| RAG quality (retrieval + answer) | 20 | Recall@10 ≥ 0.7 on golden; answer faithfulness ≥ 0.8 |
| System design (architecture) | 15 | Mermaid diagram; clear separation of ingest / retrieve / generate |
| Security (ACLs, PII, prompt-injection) | 15 | ACL filter at query time; injection test suite passes |
| Observability (traces, metrics, cost) | 10 | OpenTelemetry traces show retrieval+gen steps; cost per query |
| Code quality (readability, tests, types) | 10 | Type hints, docstrings, tests for the hot paths |
| Documentation (README, walkthrough) | 5 | 90-second walkthrough is concrete and accurate |

**Passing bar:** ≥ 70. **Stretch bar:** ≥ 85. **Anything < 70 means a specific weak dimension, not a global rewrite.**

---

## How to start

```bash
# 1. From the course root
cd course/ai-native-de

# 2. Read the spec (this file) and the architecture in the lesson
lessons/m19-capstone/L19-capstone.md

# 3. Run the reference implementation
python3 lessons/m19-capstone/L19-capstone.py

# 4. The notebook version walks through the same code interactively
jupyter nbconvert --to notebook --execute \
  lessons/m19-capstone/L19-capstone.ipynb --output exec_test
```

The reference implementation in `lessons/m19-capstone/L19-capstone.py` uses
**no external API keys** — the LLM is a deterministic mock. Swap in a real
LLM by replacing `MockLLM` with an `OpenAILLM` (or equivalent) client; the
four wrappers stay unchanged.

---

## Reference

- Lesson module: `../lessons/m19-capstone/L19-capstone.py`
- Lesson doc: `../lessons/m19-capstone/L19-capstone.md`
- Lesson notebook: `../lessons/m19-capstone/L19-capstone.ipynb`
- 100-iteration review: `../results/M19.CAPSTONE.review.json`
- Syllabus section: `../SYLLABUS.md` → "Project architecture (capstone)"

---

*Last updated: 2026-10-16*
*License: MIT*