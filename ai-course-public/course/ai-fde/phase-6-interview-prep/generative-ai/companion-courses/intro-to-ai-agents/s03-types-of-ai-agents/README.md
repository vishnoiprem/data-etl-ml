# Section 3: Types of AI agents — from simple to complex structures (8 lectures, 15 min)

> **The eight lectures in this section decompose agents by topology: how the 7 ingredients from Section 2 compose into different agent shapes.** The 7 ingredients are invariant; the topology is the variable. The FDE candidate who can pick the right topology for the right task is the candidate who ships the right agent the first time.

## The 8 lectures in this section

| # | File | Topic | Read time | Interview signal |
|---|---|---|---|---|
| L3.1 | `L3-1-reactive-vs-proactive-agents.md` | Reactive (one-shot), proactive (loop), hybrid (loop with reactive fallback). | ~2 min | "When do you need an agent vs a single LLM call?" |
| L3.2 | `L3-2-single-purpose-vs-general-purpose.md` | Single-purpose (one tool, one goal) vs general-purpose (many tools, many goals). | ~2 min | "When do you need a multi-tool agent?" |
| L3.3 | `L3-3-reflex-vs-deliberative-agents.md` | Reflex (no planning, just act), deliberative (plan-then-act), reflective (plan-act-observe-replan). | ~2 min | "When do you need planning in the agent?" |
| L3.4 | `L3-4-hierarchical-agents.md` | Orchestrator + sub-agents. The supervisor pattern. | ~2 min | "When do you need an orchestrator?" |
| L3.5 | `L3-5-multi-agent-systems.md` | Multiple agents sharing state. The collaboration pattern. | ~2 min | "When do you need multiple agents vs one?" |
| L3.6 | `L3-6-tool-using-agents.md` | Agents that use tools (function-calling + ReAct). | ~2 min | "How does an agent use tools?" |
| L3.7 | `L3-7-planning-agents.md` | Plan-and-execute, plan-and-replan, hierarchical task network (HTN). | ~2 min | "When do you need explicit planning?" |
| L3.8 | `L3-8-picking-the-right-topology.md` | The 4-axis topology rubric: tool count, plan depth, agent count, latency budget. | ~1 min | "How do you pick the right agent topology?" |

## The 1-sentence framing

The 7 ingredients from Section 2 compose into 6 agent topologies: reactive (one-shot), proactive (loop), single-purpose (one tool), general-purpose (many tools), hierarchical (orchestrator + sub-agents), multi-agent (multiple agents collaborating). The 4-axis topology rubric (tool count, plan depth, agent count, latency budget) tells the FDE which topology to pick.

## How to read this section

1. Read `L3-1` first — reactive vs proactive is the simplest axis and the most common interview question.
2. Then `L3-2` — single-purpose vs general-purpose is the second axis (how many tools does the agent need).
3. Then `L3-3` — reflex vs deliberative is the third axis (does the agent need to plan).
4. Then `L3-4` and `L3-5` — hierarchical and multi-agent are the complex topologies the FDE rarely needs but must understand.
5. Then `L3-6` and `L3-7` — tool-using and planning are the orthogonal axes (every agent uses tools, some agents plan).
6. Then `L3-8` — the synthesis. The 4-axis rubric tells the FDE which topology to pick for which task.

## The Phase 1-5 cross-reference

This section maps to **Phase 2 (Applications) + Phase 4 (Capstone)** of the FDE curriculum. The reactive/proactive distinction in L3.1 is the conceptual frame for the loop driver in `course/practice/level-5-agents/lesson-8-2-first-agent.py`. The single-purpose vs general-purpose distinction in L3.2 is implemented in `course/practice/level-5-agents/lesson-8-5-tool-design.py` (5 tools, single agent). The reflex vs deliberative distinction in L3.3 is implemented in `course/practice/level-5-agents/lesson-9-4-langgraph.py` (the plan-and-execute pattern with conditional branches). The hierarchical orchestrator in L3.4 is implemented in `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/`. The multi-agent collaboration in L3.5 is the conceptual frame for the `course/practice/level-5-agents/lesson-9-5-agent-comms.py` patterns.

## What this section preps you for

- Anthropic FDE: § 3 take-home is "build the right agent for this task" (topology choice is 50% of the grade)
- LangChain FDE: § 2 design round is "when do you use orchestrator vs single agent"
- OpenAI: warm-up is "what are the types of agent"
- Databricks AI FDE: decomposition question #3 is "where does the agent boundary sit, and is the topology right"
- Sierra AI: § 2-3 take-home is "build + demo the simplest topology that works" (over-engineering is a fail signal)

## The thesis

**The right agent is the simplest agent that solves the problem.** A reactive one-shot agent is better than a proactive loop when the task is single-step. A single-purpose agent is better than a general-purpose agent when the tool list is bounded. A single agent is better than a multi-agent system when the state fits in one prompt. **The FDE picks the simplest topology that satisfies the 4-axis rubric (tool count, plan depth, agent count, latency budget) and adds complexity only when the rubric demands it.**