# Section 6: Implementing AI agents in practice (10 lectures, 24 min)

> **The ten lectures in this section dive into the implementation: which framework to pick, how to write the production-grade agent, how to test it, how to deploy it, how to monitor it, and how to debug it.** The 7 ingredients from Section 2, the topologies from Section 3, the levers from Section 4, and the 6 patterns from Section 5 give the FDE the theory; Section 6 gives the FDE the practice.

## The 10 lectures in this section

| # | File | Topic | Read time | Interview signal |
|---|---|---|---|---|
| L6.1 | `L6-1-the-agent-framework-ecosystem.md` | LangChain, LangGraph, LlamaIndex, AutoGen, CrewAI — when to pick which. | ~2 min | "Which agent framework do you use?" |
| L6.2 | `L6-2-building-the-minimum-viable-agent.md` | The 200-line shipping agent: 7 ingredients, 5 guardrails, stdlib-only. | ~3 min | "Walk me through your minimum viable agent." |
| L6.3 | `L6-3-tool-implementation-and-validation.md` | The tool registry, schema validation, idempotency, error envelopes. | ~3 min | "How do you handle malformed tool calls?" |
| L6.4 | `L6-4-memory-implementation.md` | The 3-tier memory: short-term, long-term, episodic. Production patterns. | ~2 min | "How do you implement agent memory?" |
| L6.5 | `L6-5-guardrails-and-cost-control.md` | The 5 production guardrails + the 3-level cost ceiling. | ~2 min | "What guardrails do you ship with an agent?" |
| L6.6 | `L6-6-testing-and-evaluation.md` | The eval set, contract tests, regression checks, A/B testing. | ~3 min | "How do you test a production agent?" |
| L6.7 | `L6-7-deployment-and-scaling.md` | The deployment patterns: serverless, container, dedicated VM. The scaling levers. | ~2 min | "How do you deploy and scale an agent?" |
| L6.8 | `L6-8-monitoring-and-observability.md` | The metrics, the logs, the traces, the alerts. The 3am dashboard. | ~2 min | "How do you monitor an agent in production?" |
| L6.9 | `L6-9-error-handling-and-recovery.md` | The 4 error categories: transient, permanent, model, tool. The retry/replan strategies. | ~2 min | "How do you handle errors in an agent?" |
| L6.10 | `L6-10-debugging-the-production-agent.md` | The audit log, the trace, the replay. The 3am debugging playbook. | ~3 min | "How do you debug an agent at 3am?" |

## The 1-sentence framing

The 10 lectures cover the FDE's implementation playbook: pick a framework (L6.1), build the 200-line shipping agent (L6.2), implement tools (L6.3), memory (L6.4), guardrails (L6.5), test (L6.6), deploy (L6.7), monitor (L6.8), handle errors (L6.9), debug (L6.10). The candidate who can speak fluently to all 10 is the candidate who can ship a production agent.

## How to read this section

1. Read `L6-1` first — pick the right framework before writing code.
2. Then `L6-2` — the 200-line shipping agent is the foundation.
3. Then `L6-3`, `L6-4`, `L6-5` — the 3 implementation layers (tools, memory, guardrails).
4. Then `L6-6` — the eval set is the spec; the tests are the gate.
5. Then `L6-7`, `L6-8` — deployment and monitoring are the cross-cutting concerns.
6. Then `L6-9`, `L6-10` — error handling and debugging are the 3am skills.

## The Phase 1-5 cross-reference

This section maps to **Phase 1 (Foundations) + Phase 2 (Applications) + Phase 3 (Deployment)** of the FDE curriculum. The framework choice in L6.1 is the patterns source for `course/practice/level-5-agents/`. The shipping agent in L6.2 is implemented in `course/practice/level-5-agents/lesson-9-6-production-agents.py`. The tool implementation in L6.3 is in `course/practice/level-5-agents/lesson-8-5-tool-design.py`. The memory in L6.4 is in `course/practice/level-5-agents/lesson-8-6-agent-memory.py`. The guardrails in L6.5 are in `course/practice/level-5-agents/lesson-9-6-production-agents.py`. The testing in L6.6 is in `course/practice/level-6-production/lesson-12-4-debugging.py`. The deployment in L6.7 is in `course/ai-fde/phase-2-core-build/`. The monitoring in L6.8 is in `course/ai-fde/phase-2-core-build/service/telemetry.py`. The error handling in L6.9 is in `course/ai-fde/phase-1-foundations/README.md`. The debugging in L6.10 is the 3am playbook.

## What this section preps you for

- Anthropic FDE: § 3 take-home is "build + ship + monitor a production agent"
- LangChain FDE: § 2-3 take-home is "build with the framework, deploy, monitor"
- OpenAI: warm-up is "how do you implement an agent"
- Databricks AI FDE: decomposition question #6 is "what's the production-ready agent stack"
- Sierra AI: § 2-3 take-home is "build + demo + monitor"

## The thesis

**The implementation is 10 layers, each with a first-class artifact.** Framework choice is a config decision (L6.1). The shipping agent is a 200-line class (L6.2). Tools are a registry with schema validation (L6.3). Memory is a 3-tier store (L6.4). Guardrails are 5 layers around the loop (L6.5). The eval set is the spec (L6.6). Deployment is a 3-line Dockerfile (L6.7). Monitoring is 4 metrics on a dashboard (L6.8). Error handling is a 4-category taxonomy (L6.9). Debugging is a 5-step playbook (L6.10). **The FDE candidate who can name all 10 layers and the artifact for each is the candidate who can ship a production agent end-to-end.**
