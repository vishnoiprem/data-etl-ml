# Course 5 — LLM Tool Use with LangChain

> Source: Data Vidhya — LLM Tool Use with LangChain
> Level: Intermediate-Advanced | Prereqs: Course 1, Python typing

---

## Course Promise

> "Let the model call your code. Safely, deterministically, with retries, timeouts, and observability."

Function calling (a.k.a. tool use) is the moment an LLM stops being a chatbot and becomes a **system**. This course teaches you how to expose your code as tools the model can invoke, validate the calls, execute them safely, and feed the results back.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [Function calling, end-to-end](./01-function-calling-end-to-end.md) | Article + Worked Example | Tool schemas, parallel calls, execution, error handling |
| 2 | Tool design patterns | Article | One tool per action vs. one tool per resource |
| 3 | The OpenAI tools API | Article | `tool_choice`, parallel calls, structured output |
| 4 | The Anthropic tools API | Article | `tool_use` blocks, input_schema, multi-turn |
| 5 | Tool execution & error handling | Article | Timeouts, retries, idempotency, observability |
| 6 | Tool routing & selection | Article | When the model picks, when the router picks |
| 7 | Tool security | Article | Sandboxing, input validation, rate limits, audit |
| 8 | Multi-tool workflows | Article | Chained tools, parallel tools, dependencies |

---

## What "good" looks like after this course

1. You can expose any Python function as a tool the model can call.
2. You validate the model's arguments before executing.
3. You handle the four tool-call failure modes (malformed, denied, timeout, side-effect).
4. You know when to use parallel vs sequential tool calls.
5. You can route the model to specific tools based on context.

---

## The Lead Lesson

> **Lesson 1 — [Function calling, end-to-end](./01-function-calling-end-to-end.md)** — the canonical build. A complete "ops assistant" that lets an SRE ask natural-language questions and have the LLM call real tools: `query_logs`, `get_metric`, `page_oncall`, `create_ticket`. Includes schema design, parallel execution, error handling, and the eval harness.
