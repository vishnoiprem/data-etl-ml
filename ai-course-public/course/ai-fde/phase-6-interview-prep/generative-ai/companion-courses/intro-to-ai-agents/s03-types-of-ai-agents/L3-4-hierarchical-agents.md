# L3.4: Hierarchical agents — the orchestrator pattern

> **FDE framing in one line:** a hierarchical agent has an orchestrator (the manager) and sub-agents (the workers). The orchestrator delegates; the sub-agents execute. Use hierarchy when the task naturally decomposes into roles; avoid when one agent can do it all.

## In 60 seconds

> "Three signals. Role separation: the task decomposes into roles (CS drafter, ops, cost analyst) with different system prompts and tool lists. Parallelism: the sub-tasks are independent and can run concurrently. Context isolation: the sub-tasks require different context windows or memory backends. **When all three signals are present, use a hierarchy. When only one or two are present, use a single agent with multiple tools.** The orchestrator decomposes, dispatches, and synthesizes. Each sub-agent has its own system prompt, tool list, cost ceiling, and circuit breaker. The orchestrator's breaker is the parent. Per-agent breakers mean a Mei failure does not block Daniel. The wrong choice is a hierarchy for a single-role, single-step task (over-engineering, 5× cost). The wrong choice is a single agent for a 3-role, 3-parallel-task workflow (under-engineering, 1 agent with 15 tools has 70% accuracy). The right choice is hierarchy when the 3 signals are present."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The orchestrator-subagent topology: when the manager dispatches to workers, when the workers report back, when the manager synthesizes.
2. The 3 signals you need a hierarchy: role separation, parallelism, context isolation — and which signal dominates for which task.
3. The "per-agent circuit breaker" pattern: a Mei failure does not block Daniel; the orchestrator's breaker is the parent.

## Concept

A hierarchical agent has two or more levels. The top level is the orchestrator: it receives the goal, decomposes it into sub-tasks, dispatches each sub-task to a sub-agent, and synthesizes the results. The sub-agents are specialists: each has its own system prompt, tool list, memory, and cost ceiling. The orchestrator does not execute the sub-tasks itself; it manages the workflow.

The three signals you need a hierarchy:

1. **Role separation.** The task naturally decomposes into roles (CS drafter, ops summarizer, cost analyst). Each role has a different system prompt, tool list, and behavioral contract. A single agent with all three roles in one system prompt is harder to maintain than three sub-agents with one role each.
2. **Parallelism.** The sub-tasks are independent and can run concurrently. The orchestrator dispatches in parallel; the total latency is `max(sub_task_latency)` instead of `sum(sub_task_latency)`. A 3-sub-agent hierarchy on 3 independent sub-tasks is 3× faster than 1 single-purpose agent.
3. **Context isolation.** The sub-tasks require different context windows, different memory backends, or different tool registries. A CS-drafter sub-agent and a cost-analyst sub-agent have different tool lists; merging them into one agent makes the tool list 10+ items, which drops tool-selection accuracy to 70%.

When **all three signals are present, a hierarchy is the right topology**. When only one or two are present, a single agent with multiple tools is simpler. The candidate who proposes a hierarchy for a single-role, single-step task is over-engineering; the candidate who proposes a single agent for a 3-role, 3-parallel-task workflow is under-engineering.

The "per-agent circuit breaker" pattern is the FDE addition that makes hierarchy production-safe. Each sub-agent has its own circuit breaker; a Mei failure does not block Daniel. The orchestrator's breaker is the parent: if the orchestrator itself fails (decomposition error, synthesis error), the parent breaker trips and the workflow aborts. **Per-agent circuit breakers are the difference between a hierarchy that fails gracefully and one that cascades.**

## The pattern

The orchestrator-subagent topology, as a class:

```python
class HierarchicalAgent:
    """Orchestrator + sub-agents. The supervisor pattern."""

    def __init__(self, orchestrator: Agent, sub_agents: dict[str, Agent]):
        self.orchestrator = orchestrator
        self.sub_agents = sub_agents
        self.parent_breaker = CircuitBreaker(name="orchestrator", failure_threshold=3)

    def run(self, goal: str) -> dict:
        """The orchestrator decomposes, dispatches, synthesizes."""
        if not self.parent_breaker.allow():
            return {"error": "orchestrator_breaker_open"}

        # Step 1: orchestrator decomposes the goal
        decomposition = self.orchestrator.run(
            f"Decompose this goal into sub-tasks: {goal}\n"
            f"Available sub-agents: {list(self.sub_agents.keys())}"
        )

        # Step 2: dispatch sub-tasks (in parallel if independent)
        results = {}
        for sub_task in parse_sub_tasks(decomposition):
            agent_name = sub_task["agent"]
            sub_agent = self.sub_agents[agent_name]
            # Per-agent circuit breaker
            if not sub_agent.breaker.allow():
                results[agent_name] = {"error": "breaker_open"}
                continue
            try:
                results[agent_name] = sub_agent.run(sub_task["goal"])
                sub_agent.breaker.record_success()
            except Exception as e:
                sub_agent.breaker.record_failure()
                results[agent_name] = {"error": str(e)}

        # Step 3: orchestrator synthesizes
        return self.orchestrator.run(
            f"Synthesize the final answer.\n"
            f"Sub-task results: {results}"
        )
```

The pattern that wins interviews is the "orchestrator as manager, sub-agents as workers, per-agent circuit breaker" pattern. The candidate who says "the orchestrator decomposes, dispatches, and synthesizes; each sub-agent has its own system prompt, tool list, memory, cost ceiling, and circuit breaker; the orchestrator's breaker is the parent; a Mei failure does not block Daniel" is the candidate who demonstrates the hierarchy-mindset.

## Code or example

The 3-sub-agent PacificFreight hierarchy:

```python
MEI_AGENT = Agent(
    model="gpt-5-mini",
    system_prompt=CS_DRAFTER_PROMPT,  # Mei's system prompt
    tool_registry={"tracker.lookup", "refund.create", "translate.to", "escalate.to_human"},
    cost_tracker=CostTracker(max_run_usd=0.10),
    breaker=CircuitBreaker(name="mei", failure_threshold=3),
)

SARAH_AGENT = Agent(
    model="gpt-5-mini",
    system_prompt=OPS_SUMMARIZER_PROMPT,  # Sarah's system prompt
    tool_registry={"tracker.lookup", "shipment_aggregate"},
    cost_tracker=CostTracker(max_run_usd=0.05),
    breaker=CircuitBreaker(name="sarah", failure_threshold=3),
)

DANIEL_AGENT = Agent(
    model="gpt-5",
    system_prompt=COST_ANALYST_PROMPT,  # Daniel's system prompt
    tool_registry={"cost_lookup", "circuit_status", "rate_limit_status"},
    cost_tracker=CostTracker(max_run_usd=0.20),
    breaker=CircuitBreaker(name="daniel", failure_threshold=5),
)

DISPATCHER = HierarchicalAgent(
    orchestrator=ORCHESTRATOR_AGENT,
    sub_agents={"mei": MEI_AGENT, "sarah": SARAH_AGENT, "daniel": DANIEL_AGENT},
)
```

The dispatch logic for a multi-shipment case:

```python
# Customer email: "I need status on PF-1003, PF-1004, and PF-1005. Also, can you
# refund PF-1003 ($50) and PF-1004 ($120)?"

# Orchestrator decomposes:
# - sub_task_1: agent="mei", goal="draft reply to customer"
# - sub_task_2: agent="sarah", goal="summarize the 3 shipments"
# - sub_task_3: agent="daniel", goal="verify cost of the 2 refunds"

# Dispatch (sub-tasks 1, 2, 3 are partially parallel; sub-task 3 depends on sub-task 1)
# - sub_task_1 and sub_task_2 can run in parallel
# - sub_task_3 waits for sub_task_1's draft to be ready

# Synthesize: orchestrator combines Mei's draft + Sarah's summary + Daniel's cost note
# into a 3-part response.
```

## Production addendum

The orchestrator-vs-single-agent question is the answer to "when do you need an orchestrator." The 60-second script:

> "Three signals. Role separation: the task decomposes into roles (CS drafter, ops, cost analyst) with different system prompts and tool lists. Parallelism: the sub-tasks are independent and can run concurrently. Context isolation: the sub-tasks require different context windows or memory backends. **When all three signals are present, use a hierarchy. When only one or two are present, use a single agent with multiple tools.** The orchestrator decomposes, dispatches, and synthesizes. Each sub-agent has its own system prompt, tool list, cost ceiling, and circuit breaker. The orchestrator's breaker is the parent. Per-agent breakers mean a Mei failure does not block Daniel. The wrong choice is a hierarchy for a single-role, single-step task (over-engineering, 5× cost). The wrong choice is a single agent for a 3-role, 3-parallel-task workflow (under-engineering, 1 agent with 15 tools has 70% accuracy). The right choice is hierarchy when the 3 signals are present."

This is the difference between a candidate who says "I built a multi-agent system" and a candidate who says "I used a hierarchy because the 3 signals were present: role separation (3 different system prompts), parallelism (3 independent sub-tasks), context isolation (different tool lists)." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-4-langgraph.py` — the LangGraph StateGraph with orchestrator + sub-agents.
- **Reference implementation**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/service/agents.py` — the production 3-sub-agent hierarchy.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the orchestrator pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the canonical hierarchical agent.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — hierarchy as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you need an orchestrator?"** Answer: when 3 signals are present: role separation (different system prompts), parallelism (independent sub-tasks), context isolation (different tool lists or memory backends). When only 1-2 signals are present, a single agent is simpler.
2. **"What is the per-agent circuit breaker pattern?"** Answer: each sub-agent has its own circuit breaker; the orchestrator's breaker is the parent. A Mei failure does not block Daniel. Per-agent breakers mean the hierarchy fails gracefully, not cascades. The orchestrator's breaker trips only when the decomposition or synthesis itself fails.
3. **"What is the difference between a hierarchy and a multi-agent system?"** Answer: hierarchy has a single orchestrator that decomposes and synthesizes; multi-agent has multiple agents that collaborate without a single manager. Hierarchy is the simpler pattern; multi-agent is for problems where no single agent can decompose the task.

## Read next

`L3-5-multi-agent-systems.md` — the fifth axis. Multi-agent systems have multiple agents collaborating without a single orchestrator. The collaboration pattern is the harder one to debug; the FDE picks hierarchy when the task is decomposable, multi-agent when the task is fundamentally collaborative.