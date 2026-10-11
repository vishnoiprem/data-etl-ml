# Section 5: AI agent architecture patterns (6 lectures, 16 min)

> **The six lectures in this section decompose agents by architecture: how the 7 ingredients from Section 2, the topologies from Section 3, and the levers from Section 4 compose into 6 canonical architecture patterns.** The patterns are: single agent, sequential pipeline, orchestrator + sub-agents, parallel fan-out / fan-in, hierarchical task network, and human-in-the-loop. The FDE candidate who can name all 6 and explain when to use each is the candidate who can architect a production agent system.

## In 60 seconds

The 5 named patterns you must recite (one lecture per pattern + the synthesis):

1. **Single agent** — one LLM, one tool set, one memory. Use for <5 tools, single role.
2. **Sequential pipeline** — fixed DAG; each step's output is the next step's input.
3. **Orchestrator** — runtime dispatch; the LLM picks the sub-agent per case. **The FDE default for multi-step.**
4. **Parallel fan-out / fan-in** — independent sub-tasks run concurrently; results merged.
5. **HTN + HITL** — hierarchical task networks for complex decomposition; human-in-the-loop for high-stakes outputs.

The decision heuristic: **start with single agent; graduate to orchestrator when 3+ stakeholder audiences need different contexts; add HITL when stakes exceed $1K per output.** **If you only read one lecture, read L5-3** (the orchestrator).

## The 6 lectures in this section

| # | File | Topic | Read time | Interview signal |
|---|---|---|---|---|
| L5.1 | `L5-1-the-single-agent-pattern.md` | The single-agent pattern: 1 decision function, 1 tool list, 1 loop. The simplest production shape. | ~2 min | "When do you need more than one agent?" |
| L5.2 | `L5-2-the-sequential-pipeline-pattern.md` | The sequential pipeline: agent A's output is agent B's input. For workflows with clear handoffs. | ~3 min | "When do you use a pipeline vs a loop?" |
| L5.3 | `L5-3-the-orchestrator-pattern.md` | The orchestrator + sub-agents pattern. The supervisor dispatches; the workers execute. | ~3 min | "How do you decompose a complex task across agents?" |
| L5.4 | `L5-4-the-parallel-fanout-pattern.md` | The parallel fan-out / fan-in pattern: N agents run concurrently, results are merged. | ~3 min | "When do you parallelize agent work?" |
| L5.5 | `L5-5-the-hierarchical-task-network.md` | The HTN pattern: plans are trees, not lists. Recursive sub-plans for hierarchical tasks. | ~2 min | "When do you need a hierarchical plan?" |
| L5.6 | `L5-6-the-human-in-the-loop-pattern.md` | The human-in-the-loop pattern: the agent pauses for approval before irreversible side effects. | ~3 min | "How do you put a human in the agent's loop?" |

## The 1-sentence framing

The 6 canonical architecture patterns are: (1) single agent (1 decision function, 1 tool list, 1 loop), (2) sequential pipeline (agent A's output is agent B's input), (3) orchestrator + sub-agents (supervisor dispatches, workers execute), (4) parallel fan-out / fan-in (N agents run concurrently, results are merged), (5) hierarchical task network (plans are trees), (6) human-in-the-loop (the agent pauses for approval). The FDE picks the simplest pattern that satisfies the task's structure; add complexity only when the simpler pattern fails.

## How to read this section

1. Read `L5-1` first — the single-agent pattern is the foundation; every other pattern composes it.
2. Then `L5-2` — the sequential pipeline is the simplest multi-agent pattern.
3. Then `L5-3` — the orchestrator is the FDE's default multi-agent pattern.
4. Then `L5-4` — the parallel fan-out / fan-in is the pattern for concurrent work.
5. Then `L5-5` — the HTN is the pattern for hierarchical tasks.
6. Then `L5-6` — the human-in-the-loop is the pattern for irreversible side effects.

## The Phase 1-5 cross-reference

This section maps to **Phase 2 (Applications) + Phase 4 (Capstone)** of the FDE curriculum. The single-agent pattern in L5.1 is implemented in `course/practice/level-5-agents/lesson-8-2-first-agent.py`. The sequential pipeline in L5.2 is implemented in `course/practice/level-5-agents/lesson-9-2-crewai.py`. The orchestrator in L5.3 is implemented in `course/practice/level-5-agents/lesson-9-4-langgraph.py` and `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/`. The parallel fan-out / fan-in in L5.4 is implemented in `course/practice/level-5-agents/lesson-9-3-autogen.py`. The HTN in L5.5 is implemented in `course/hardcode/level-5-agentic-workflows/10-multi-agent-orchestrator.py`. The human-in-the-loop in L5.6 is implemented in `course/practice/level-5-agents/lesson-9-4-langgraph.py` (the interrupt pattern).

## What this section preps you for

- Anthropic FDE: § 3 take-home is "design the agent architecture for this task" (pattern choice is 50% of the grade)
- LangChain FDE: § 2 design round is "which pattern fits this use case"
- OpenAI: warm-up is "what are the agent architecture patterns"
- Databricks AI FDE: decomposition question #5 is "which pattern is the right one"
- Sierra AI: § 2-3 take-home is "build + demo the simplest pattern that works"

## The thesis

**The right pattern is the simplest one that solves the problem.** Single agent for 80% of FDE use cases. Sequential pipeline for workflows with clear handoffs. Orchestrator for multi-role workflows. Parallel fan-out for concurrent sub-tasks. HTN for hierarchical plans. Human-in-the-loop for irreversible side effects. **The FDE candidate who can name all 6 patterns and explain the escalation rule is the candidate who can architect a production system.**
