# Section 2: Essential ingredients for building AI agents (7 lectures, 16 min)

> **The seven lectures in this section decompose the four preconditions from L1.3 into their engineering parts and add the two practical layers (system prompt, parser) the four preconditions don't cover.** This is the section the FDE candidate must internalize — every centerpiece-round architecture question is "how do you build the agent" and the answer is "the seven ingredients, with the five guardrails wrapped around them."

## In 60 seconds

The five named taxonomies you must recite from this section:

1. **7 ingredients:** model, tools, memory, cost ceiling, system prompt, parser, loop driver.
2. **5 guardrails:** loop detector, schema validator, cost ceiling, idempotency, audit log.
3. **3-tier cost ceiling:** per-run ($0.50 default), per-tenant per-day ($5), per-process per-month ($1,000).
4. **4 RAGAS metrics:** faithfulness, answer relevance, context precision, context recall.
5. **3 memory tiers:** short-term (in prompt), long-term (vector DB), episodic (summarized past sessions).

The synthesis lecture is **L2-7** — it wraps all 7 ingredients + all 5 guardrails in one 200-line shipping agent. **If you only read one lecture in this section, read L2-7.** It is the closest thing to a complete answer in the whole course.

## The 7 lectures in this section

| # | File | Topic | Read time | Interview signal |
|---|---|---|---|---|
| L2.1 | `L2-1-the-decision-function.md` | The LLM as decision function: what it can decide, where it fails, how to pick. | ~2 min | "How do you choose the model for an agent?" |
| L2.2 | `L2-2-the-tool-protocol.md` | Function-calling vs ReAct. The tool registry. Schema validation. | ~2 min | "What is the tool-use protocol?" |
| L2.3 | `L2-3-the-memory-layer.md` | Short-term (window), long-term (vector), episodic (summary). | ~3 min | "How does the agent remember across steps?" |
| L2.4 | `L2-4-the-cost-ceiling.md` | The cost ceiling as a first-class FDE pattern. Per-run, per-tenant, per-day. | ~2 min | "How do you prevent cost blowouts?" |
| L2.5 | `L2-5-the-system-prompt.md` | The system prompt as the contract between the model and the agent. | ~2 min | "How do you write a good agent system prompt?" |
| L2.6 | `L2-6-parsing-structured-output.md` | The parser as the contract between the model output and the tool dispatcher. | ~2 min | "How do you handle malformed model output?" |
| L2.7 | `L2-7-combining-the-ingredients.md` | The 7 ingredients assembled into the canonical ReAct loop. The shipping agent. | ~3 min | "Walk me through the architecture of a production agent." |

## The 1-sentence framing

A production agent is **7 ingredients** (model, tools, memory, cost ceiling, system prompt, parser, loop driver) **wrapped in 5 guardrails** (loop detector, schema validator, cost ceiling, idempotency, audit log) **and deployed behind 5 cross-process FDE patterns** (cost-ceiling-as-score, circuit breaker, per-tenant limits, audit log, "FDE has left" test).

## How to read this section

1. Read `L2-1` first — the model is the decision function; everything else is plumbing.
2. Then `L2-2` — the tool protocol is the second most important ingredient; it defines the agent's action space.
3. Then `L2-3` — the memory layer is what makes the agent multi-step instead of single-step.
4. Then `L2-4` — the cost ceiling is the first guardrail the FDE writes; it is non-negotiable.
5. Then `L2-5` and `L2-6` — system prompt + parser are the practical layers the four preconditions don't cover.
6. Then `L2-7` — the synthesis. The 7 ingredients composed into the canonical shipping agent.

## The Phase 1-5 cross-reference

This section maps to **Phase 1 (Foundations) + Phase 2 (Applications) + Phase 3 (Deployment)** of the FDE curriculum. The LLM choice in L2.1 is implemented in `course/practice/level-2-prompt-engineering/lesson-3-1-craft-framework.py` (the model selection rubric). The tool protocol in L2.2 is implemented in `course/practice/level-5-agents/lesson-8-5-tool-design.py`. The memory layer in L2.3 is implemented in `course/practice/level-5-agents/lesson-8-6-agent-memory.py`. The cost ceiling in L2.4 is implemented across `course/practice/level-6-production/`. The system prompt in L2.5 is implemented in `course/practice/level-2-prompt-engineering/lesson-3-5-system-prompts.py`. The parser in L2.6 is implemented in `course/practice/level-5-agents/lesson-8-2-first-agent.py`. The synthesis in L2.7 is implemented in `course/practice/level-5-agents/lesson-9-6-production-agents.py`.

## What this section preps you for

- Anthropic FDE: § 3 take-home is "build an agent with the 7 ingredients and the 5 guardrails"
- LangChain FDE: § 2 design round is "explain each ingredient and how they compose"
- OpenAI: warm-up is "what are the components of an agent"
- Databricks AI FDE: decomposition question #2 is "which ingredient handles X"
- Sierra AI: § 2-3 take-home is "build + demo an agent with memory and tools"

## The thesis

**The 7 ingredients are necessary; the 5 guardrails are sufficient.** An agent without the 7 ingredients is not an agent. An agent with the 7 ingredients but without the 5 guardrails is a prototype that will fail in production. The FDE candidate who can name all 7 ingredients AND all 5 guardrails is the candidate who passes the centerpiece round.
