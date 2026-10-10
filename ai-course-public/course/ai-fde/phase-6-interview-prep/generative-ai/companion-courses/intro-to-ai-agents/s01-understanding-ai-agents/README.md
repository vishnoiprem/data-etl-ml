# Section 1: Understanding AI Agents (3 lectures, 9 min)

> **The three lectures in this section answer the question "what is an agent, and why is it different from an LLM call?"** This is the most-asked warm-up question in agent interviews. If you can't answer it in 60 seconds with a concrete example, you fail the screening round. The 3 lectures here are the FDE candidate's preparation for that question.

## The 3 lectures in this section

| # | File | Topic | Read time | Interview signal |
|---|---|---|---|---|
| L1.1 | `L1-1-what-is-an-agent.md` | Definition: perceive → decide → act. The agent loop. | ~3 min | "Define an AI agent." |
| L1.2 | `L1-2-llm-vs-agent.md` | LLMs are reactive. Agents are proactive. Why the next abstraction layer matters. | ~3 min | "What's the difference between an LLM call and an agent?" |
| L1.3 | `L1-3-why-agents-now.md` | The "next big thing" framing: tooling, memory, planning, and the cost of agency. | ~3 min | "Why are agents the next layer above LLMs?" |

## The 1-sentence framing

An AI agent is an LLM equipped with tools, memory, and a planning loop that lets it pursue a goal across multiple steps — a system that does work, not just answers questions.

## How to read this section

1. Read `L1-1` first. The agent loop is the foundation.
2. Then `L1-2`. The reactive-vs-proactive distinction is the cleanest way to articulate the difference in an interview.
3. Then `L1-3`. The "why now" framing is what separates an engineer who uses agents from an engineer who understands them.

## The Phase 1-5 cross-reference

This entire section maps to **Phase 1 (Foundations)** of the FDE curriculum. The agent loop in L1.1 is implemented in `course/practice/level-5-agents/lesson-8-2-first-agent.py`. The reactive-vs-proactive distinction in L1.2 is the conceptual frame for the multi-agent dispatcher in `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/`. The "why now" framing in L1.3 is the FDE-business argument for the cost ceiling + eval set + circuit breaker.

## What this section preps you for

- Anthropic FDE: § 3 take-home is "build an agent with this loop"
- LangChain FDE: § 3 take-home is a goal-based agent with memory
- Sierra AI: § 2-3 take-home is "build + demo an agent"
- OpenAI: warm-up is "what is the difference between an LLM call and an agent"
- Databricks AI FDE: decomposition question #1 is "where does the agent boundary sit"
