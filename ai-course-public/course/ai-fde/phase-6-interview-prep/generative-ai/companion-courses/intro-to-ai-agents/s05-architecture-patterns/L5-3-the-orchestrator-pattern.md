# L5.3: The orchestrator pattern

> **FDE framing in one line:** the orchestrator + sub-agents is the FDE's default multi-agent pattern. The supervisor dispatches; the workers execute; the orchestrator synthesizes. Per-agent circuit breakers mean a Mei failure does not block Daniel.

## The 3 things you'll learn

1. The 3 components of the orchestrator pattern: orchestrator (the supervisor), sub-agents (the workers), shared state (the context).
2. The 3 escalation triggers from single agent to orchestrator: tool count > 7, role count > 1, tool selection accuracy < 85%.
3. The per-agent circuit breaker pattern: each sub-agent has its own breaker; the orchestrator's breaker is the parent.

## Concept

The orchestrator pattern is the FDE's default multi-agent pattern. The orchestrator is a single agent that receives the goal, decomposes it into sub-tasks, dispatches each sub-task to a sub-agent, and synthesizes the results. The sub-agents are specialists: each has its own system prompt, tool list, memory, and cost ceiling. The orchestrator does not execute the sub-tasks itself; it manages the workflow.

The 3 components of the orchestrator pattern:

1. **Orchestrator (the supervisor).** A single agent that decomposes, dispatches, and synthesizes. The orchestrator's system prompt names the sub-agents and their roles; the orchestrator's tool list includes a `dispatch(sub_agent_name, sub_goal)` tool that calls the sub-agent.
2. **Sub-agents (the workers).** Specialist agents that execute sub-tasks. Each has its own system prompt (role-specific), tool list (role-specific), memory (isolated from other sub-agents), and cost ceiling (per-sub-agent). The sub-agents are the same 7-ingredient + 5-guardrail composition from L5.1.
3. **Shared state (the context).** A data structure that all sub-agents read/write. The orchestrator initializes the state with the goal; each sub-agent updates the state with its result; the orchestrator reads the state for synthesis. The shared state is the contract between the orchestrator and the sub-agents.

The 3 escalation triggers from single agent to orchestrator (revisited from L5.1):

1. **Tool count > 7.** A single agent with 8+ tools picks the wrong tool 30% of the time. The orchestrator dispatches to sub-agents with 4-5 tools each; each sub-agent has 95% tool selection accuracy.
2. **Role count > 1.** A single agent with 3 roles in one system prompt is a wall of text; the model is confused about which role to play. The orchestrator dispatches to role-specific sub-agents; each sub-agent has a clear role.
3. **Tool selection accuracy < 85%.** When the production metrics show tool selection accuracy dropping below 85%, the orchestrator is the fix. Sub-agents with fewer tools each have higher accuracy.

The per-agent circuit breaker pattern is the FDE addition that makes the orchestrator production-safe. Each sub-agent has its own circuit breaker; a Mei failure does not block Daniel. The orchestrator's breaker is the parent: if the orchestrator itself fails (decomposition error, synthesis error), the parent breaker trips and the workflow aborts.

## The pattern

The orchestrator + sub-agents class:

```python
class Orchestrator:
    """The orchestrator + sub-agents pattern. The FDE default for multi-agent."""

    def __init__(self, orchestrator_agent: SingleAgent, sub_agents: dict[str, SingleAgent]):
        self.orchestrator = orchestrator_agent
        self.sub_agents = sub_agents
        self.parent_breaker = CircuitBreaker(name="orchestrator", failure_threshold=3)
        self.shared_state = {}

    def run(self, goal: str) -> dict:
        if not self.parent_breaker.allow():
            return {"error": "orchestrator_breaker_open"}

        # Step 1: Decompose
        decomposition = self.orchestrator.run(
            f"Decompose: {goal}\nSub-agents: {list(self.sub_agents.keys())}"
        )
        if decomposition.get("error"):
            self.parent_breaker.record_failure()
            return decomposition

        # Step 2: Dispatch (sequential or parallel)
        results = {}
        for sub_task in parse_decomposition(decomposition):
            agent_name = sub_task["agent"]
            sub_agent = self.sub_agents[agent_name]
            if not sub_agent.breaker.allow():
                results[agent_name] = {"error": "sub_agent_breaker_open"}
                continue
            try:
                results[agent_name] = sub_agent.run(sub_task["goal"])
                sub_agent.breaker.record_success()
            except Exception as e:
                sub_agent.breaker.record_failure()
                results[agent_name] = {"error": str(e)}

        # Step 3: Synthesize
        return self.orchestrator.run(
            f"Synthesize: {goal}\nSub-results: {results}"
        )
```

The PacificFreight orchestrator (the canonical FDE use case):

```python
ORCHESTRATOR = Orchestrator(
    orchestrator_agent=SingleAgent(
        model=Model("gpt-5-mini", openai_chat, PRICING["gpt-5-mini"]),
        tools=ToolRegistry([
            Tool("dispatch", "Dispatch to a sub-agent.", {"sub_agent": str, "sub_goal": str}, 1, dispatch),
            Tool("synthesize", "Synthesize sub-results.", {"results": dict}, 1, synthesize),
        ]),
        memory=Memory(),
        cost=CostCeiling(max_run_usd=0.05),
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    ),
    sub_agents={
        "mei": MEI_AGENT,      # CS drafter (4 tools)
        "sarah": SARAH_AGENT,  # Ops summarizer (2 tools)
        "daniel": DANIEL_AGENT,  # Cost analyst (3 tools)
    },
)
```

The pattern that wins interviews is the "orchestrator + per-agent circuit breakers + shared state" pattern. The candidate who says "the orchestrator decomposes, dispatches, synthesizes; each sub-agent has its own system prompt, tool list, memory, cost ceiling, and circuit breaker; the orchestrator's breaker is the parent; a Mei failure does not block Daniel; the shared state is the contract between orchestrator and sub-agents" is the candidate who demonstrates the orchestrator-mindset.

## Code or example

The decomposition prompt (the orchestrator's most important contract):

```python
ORCHESTRATOR_SYSTEM_PROMPT = """You are a customer service orchestrator for PacificFreight.
Your job is to decompose complex cases into sub-tasks and dispatch them to specialist sub-agents.

Available sub-agents:
- mei: CS drafter (drafts replies, handles refunds, escalations)
- sarah: Ops summarizer (summarizes multi-shipment cases)
- daniel: Cost analyst (verifies costs, checks budget impact)

When you receive a complex case:
1. Analyze the case to identify the sub-tasks
2. Dispatch each sub-task to the right sub-agent
3. Synthesize the sub-results into a final response

Output format:
Thought: <your analysis>
Action: dispatch(sub_agent="<name>", sub_goal="<the sub-task>")
... (repeat for each sub-task)
Final Answer: <synthesized response combining all sub-results>

Example:
User: "Customer wants status on PF-1003, PF-1004, PF-1005; refund $50 for PF-1003; refund $120 for PF-1004."
Thought: This is a multi-shipment case. I need Sarah to summarize the 3 shipments, Mei to draft the reply + process the 2 refunds, and Daniel to verify the refund costs.
Action: dispatch(sub_agent="sarah", sub_goal="Summarize status of PF-1003, PF-1004, PF-1005.")
Action: dispatch(sub_agent="mei", sub_goal="Draft reply + process 2 refunds.")
Action: dispatch(sub_agent="daniel", sub_goal="Verify refund costs are within budget.")
Final Answer: <synthesized response>
"""
```

The per-agent circuit breaker in action:

```python
# Scenario: Mei's sub-agent is broken (e.g., OpenAI is down)
# Result: Mei's breaker trips after 3 consecutive failures
# Sarah and Daniel continue to function
# Orchestrator's parent breaker does NOT trip (because the orchestrator itself is working)
# The workflow returns: {mei: {error: "sub_agent_breaker_open"}, sarah: {...}, daniel: {...}}
# The orchestrator synthesizes a response acknowledging Mei's failure
```

The shared state contract:

```python
SHARED_STATE_SCHEMA = {
    "case_id": str,           # The unique case identifier
    "customer_id": str,       # The customer who submitted the case
    "shipment_ids": list,     # The shipments in scope
    "sub_task_results": dict, # {sub_agent_name: result}
    "final_response": str,    # The orchestrator's synthesized response
}

# The orchestrator initializes the state, dispatches with the state as context,
# each sub-agent updates sub_task_results, the orchestrator reads the final state
# for synthesis.
```

## Production addendum

The orchestrator question is the answer to "how do you decompose a complex task across agents." The 60-second script:

> "Orchestrator + sub-agents. The orchestrator decomposes, dispatches, synthesizes. Each sub-agent has its own system prompt, tool list, memory, cost ceiling, and circuit breaker. The orchestrator's breaker is the parent. Per-agent breakers mean a Mei failure does not block Daniel. **The shared state is the contract: orchestrator initializes, sub-agents update, orchestrator reads for synthesis.** The 3 escalation triggers: tool count > 7, role count > 1, tool selection accuracy < 85%. The wrong choice is a single agent with 15 tools (70% accuracy). The wrong choice is a multi-agent system without per-agent breakers (one failure cascades to all). The right choice is the orchestrator with 3 sub-agents, each with 4-5 tools and its own circuit breaker."

This is the difference between a candidate who says "I built a multi-agent system" and a candidate who says "orchestrator + sub-agents, per-agent circuit breakers, shared state as the contract, 3 escalation triggers from single agent." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-4-langgraph.py` — the LangGraph orchestrator with 6 nodes and conditional edges.
- **Reference implementation**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the production PacificFreight orchestrator.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the orchestrator as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the canonical orchestrator reference.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — orchestrator as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How do you decompose a complex task across agents?"** Answer: orchestrator + sub-agents. The orchestrator decomposes the task into sub-tasks, dispatches each to a specialist sub-agent, and synthesizes the results. Each sub-agent has its own system prompt, tool list, memory, and cost ceiling. The shared state is the contract between orchestrator and sub-agents.
2. **"What is the per-agent circuit breaker pattern?"** Answer: each sub-agent has its own circuit breaker; the orchestrator's breaker is the parent. A sub-agent failure trips the sub-agent's breaker, not the parent's. The orchestrator can still synthesize a response acknowledging the failure. **Per-agent breakers are the difference between an orchestrator that fails gracefully and one that cascades.**
3. **"When do you escalate from single agent to orchestrator?"** Answer: when the single agent fails one of 3 conditions — tool count > 7 (sub-agents for context isolation), role count > 1 (sub-agents for role separation), tool selection accuracy < 85% (sub-agents for fewer tools each). The escalation is objective; measure the failure mode, pick the orchestrator.

## Read next

`L5-4-the-parallel-fanout-pattern.md` — the fourth pattern. The parallel fan-out / fan-in runs N agents concurrently and merges the results. The right pattern when sub-tasks are independent and the latency budget is tight.