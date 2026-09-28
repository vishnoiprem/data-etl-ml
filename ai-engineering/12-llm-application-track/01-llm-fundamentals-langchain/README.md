# Course 1 — LLM Application Fundamentals with LangChain

> Source: Data Vidhya — LLM Application Fundamentals with LangChain
> Level: Intermediate | Prereqs: Python, familiarity with at least one LLM API

---

## Course Promise

> "Move from `client.messages.create(...)` to a chain you can compose, stream, observe, and test."

LangChain is the most-deployed LLM framework in production. It is also the most-misunderstood. This course teaches you what LangChain is actually doing under the hood — and when to use it, when to bypass it, and when to leave it.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [The LangChain mental model](./01-langchain-mental-model.md) | Article + Worked Example | Chains, runnables, LCEL, and the "LangChain tax" |
| 2 | Models & message types | Article | ChatModel vs LLM, providers, message roles |
| 3 | Prompt templates | Article | ChatPromptTemplate, partials, composition |
| 4 | Output parsers | Article | StrOutputParser, Pydantic, JSON, XML |
| 5 | LCEL — the composition language | Article | `|` operator, `RunnablePassthrough`, `RunnableParallel` |
| 6 | Streaming & async | Article | `stream()`, `astream()`, `astream_events()` |
| 7 | Memory & chat history | Article | ConversationBufferMemory, summary, trimming |
| 8 | Tracing & observability | Article | LangSmith tracing, Callbacks, debug mode |

---

## What "good" looks like after this course

You should be able to:

1. Read an LCEL expression and predict its runtime behavior.
2. Decide whether a task needs a chain, an agent, or a plain function call.
3. Wire tracing, retry, fallback, and cost tracking into any chain in <50 lines.
4. Explain the "LangChain tax" and where the abstractions leak.
5. Write a chain that streams, parses to Pydantic, and falls back on parse failure — all in one expression.

---

## The Lead Lesson

> **Lesson 1 — [The LangChain mental model](./01-langchain-mental-model.md)** — start here. Includes a worked example that builds a production-grade structured-extraction chain end-to-end with streaming, retries, fallback, eval, and cost tracking.

The lead lesson's worked example builds a **support-ticket triage chain** that:
- Accepts raw ticket text
- Extracts structured fields (priority, category, sentiment, summary)
- Falls back to a smaller model on parse failure
- Streams tokens to the client
- Logs every trace to LangSmith
- Costs ~$0.0008 per ticket at scale

That single chain touches every concept in the course. Read it first; the other lessons fill in the why.
