# LLM Application Track — Complete Course Notes

> Source: Data Vidhya — LLM Application Track (6 courses)
> Audience: Engineers building real production LLM applications
> Tech: Python · LangChain · LangSmith · LangGraph · Vector DBs · Claude / GPT / OSS models

---

## Track Promise

> "From `ChatPromptTemplate.from_messages(...)` to a multi-agent system with eval gates, eval harness, observability, and cost guardrails — every layer a senior engineer actually owns."

This is the **applied LLM engineering** curriculum. The companion track to `11-learn-ai-data/` (which is AI for *data engineering*) — this one is **LLM engineering as a discipline**: prompt design, evaluation, retrieval, tool use, and agents.

---

## Course Map

| # | Course | Theme | Stack |
|---|--------|-------|-------|
| 1 | [LLM Application Fundamentals with LangChain](./01-llm-fundamentals-langchain/) | Models, prompts, parsers, chains, streaming, memory | LangChain · LCEL |
| 2 | [LLM Application Evaluation with LangSmith](./02-llm-evaluation-langsmith/) | Datasets, evaluators, experiment comparison, regression detection | LangSmith · LangChain |
| 3 | [Prompt Engineering with LangChain](./03-prompt-engineering-langchain/) | Few-shot, CoT, structured output, prompt templating at scale | LangChain · Jinja |
| 4 | [Retrieval-Augmented Generation with LangChain](./04-rag-langchain/) | Loaders, splitters, retrievers, rerankers, agents over RAG | LangChain · Vector DB |
| 5 | [LLM Tool Use with LangChain](./05-llm-tool-use-langchain/) | Function calling, structured tool schemas, parallel/sequential tool calls | LangChain · OpenAI tools · Anthropic tools |
| 6 | [Agentic Systems with LangGraph](./06-agentic-systems-langgraph/) | Stateful graphs, cycles, human-in-the-loop, multi-agent orchestration | LangGraph · LangChain |

---

## How to Use These Notes

Each course folder follows the same convention as `11-learn-ai-data/`:
```
NN-course-name/
├── README.md                  # Course overview + lesson index
├── 01-lead-lesson.md          # Article-style notes (lead lesson has a worked example)
├── 02-...
└── ...
```

Each lead lesson ends with a **Worked Example** section — a complete, code-first build that takes you from a blank repo to a working system. Examples are deliberately principal-engineer-grade: they include the eval harness, the failure modes, and the cost numbers, not just the happy path.

---

## The Shared Mental Model Across All 6 Courses

```
   ┌──────────────────────────────────────────────────────────┐
   │   THE LLM APP STACK                                      │
   │                                                          │
   │   USER INTENT                                            │
   │       │                                                  │
   │       ▼                                                  │
   │   PROMPT (template + variables + few-shot + tools)        │  Course 3
   │       │                                                  │
   │       ▼                                                  │
   │   MODEL (Claude / GPT / OSS)                             │  Course 1
   │       │                                                  │
   │       ▼                                                  │
   │   PARSER (JSON / Pydantic / XML)                         │  Course 1
   │       │                                                  │
   │       ▼                                                  │
   │   CHAIN (LCEL: | prompt | model | parser)                │  Course 1
   │       │                                                  │
   │       ▼                                                  │
   │   TOOLS (function calling, retrieval, code exec)         │  Course 5
   │       │                                                  │
   │       ▼                                                  │
   │   AGENT (decide → act → observe → loop)                  │  Course 6
   │       │                                                  │
   │       ▼                                                  │
   │   EVAL (LangSmith: traces, datasets, evaluators)          │  Course 2
   │       │                                                  │
   │       ▼                                                  │
   │   RETRIEVAL (loaders, splitters, retrievers, rerank)     │  Course 4
   │                                                          │
   └──────────────────────────────────────────────────────────┘
```

Every layer compounds. Course 6 (agents) reuses prompts (3), models (1), tools (5), retrieval (4), and is judged by eval (2). The order of the curriculum is the order of dependencies.

---

## Cross-Cutting Themes

These show up in every course:

1. **Eval-first, not eval-last.** Course 2 is dedicated to it, but every course assumes you can measure quality before you ship.
2. **The 60/40 rule.** 60% of LLM engineering is *generation*; 40% is *verification, retries, fallbacks, and observability*. If your plan only covers generation, it will fail at scale.
3. **The "LangChain tax."** LangChain saves you 2 days at the start and costs you 2 weeks at scale if you don't understand what it's doing under the hood. Each course calls out where LCEL's abstractions leak.
4. **Cost is a feature.** Every course ends with a cost roll-up. If you can't write down "$X per 1K requests," you don't understand the system.
5. **The eval set is the moat.** A 200-query curated eval set is worth more than 10K-star repo. Course 2 makes this concrete.

---

## Prerequisites

- Python (intermediate)
- Comfortable with `requests`, `pydantic`, `pytest`
- Familiarity with at least one LLM API (Claude / OpenAI / Gemini)
- Helpful: the `11-learn-ai-data/` track (RAG, vector DBs, feature stores)

---

## After This Track

The natural next steps are:

- **Production-grade deployment** (covered in `01-enterprise-rag-platform/`, `08-llmops-platform/`)
- **Fine-tuning & alignment** (covered in `02-llm-fine-tuning/`)
- **Multi-agent orchestration** (covered in `03-multi-agent-platform/`)
- **Evaluation at scale** (covered in `04-fm-evaluation/`)

This track is the **builder's foundation** — the courses that turn "I can call an LLM" into "I can ship, eval, and operate an LLM application."
