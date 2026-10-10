# L3.5: Multi-agent systems — collaboration without an orchestrator

> **FDE framing in one line:** a multi-agent system has multiple agents collaborating without a single orchestrator. The agents pass messages to each other; the system emerges from the peer-to-peer protocol. Pick this topology when the task is fundamentally collaborative, not decomposable.

## The 3 things you'll learn

1. The collaboration pattern: peer-to-peer message passing, shared blackboard, or consensus protocol.
2. The 3 failure modes of multi-agent: message loops, deadlocks, emergent miscoordination.
3. The "hierarchy first, multi-agent only when forced" pattern: the FDE picks hierarchy when the task is decomposable; multi-agent when no single agent can decompose.

## Concept

A multi-agent system has multiple agents that collaborate without a single orchestrator. Each agent has its own goal, its own system prompt, its own tool list. The agents communicate via message passing (Agent A sends a message to Agent B), shared state (a blackboard both agents read/write), or a consensus protocol (agents vote on the next action). **The system has no central manager; the behavior emerges from the peer-to-peer interaction.**

The three collaboration patterns:

1. **Peer-to-peer message passing.** Agent A sends a message to Agent B; Agent B receives it, decides what to do, sends a message to Agent C; etc. The protocol is a directed graph; the agents are nodes. The canonical example: AutoGen's group chat pattern.
2. **Shared blackboard.** All agents read/write a shared state object. Agent A writes its partial result to the blackboard; Agent B reads it, adds its partial result; Agent C reads both, synthesizes. The protocol is a tuple space; the agents are producers + consumers.
3. **Consensus protocol.** All agents vote on the next action; the action with the most votes is executed. The protocol is a voting round; the agents are voters. The canonical example: Mixture of Experts (MoE) where each expert votes on the output token.

The three failure modes that decide whether a multi-agent system succeeds or fails:

1. **Message loops.** Agent A sends a message to Agent B; Agent B sends it back to Agent A. The system loops forever. The fix: a message counter per edge; abort after N round-trips.
2. **Deadlocks.** Agent A is waiting for Agent B's response; Agent B is waiting for Agent A's. Neither proceeds. The fix: a timeout on every message; if no response in T seconds, the agent proceeds without it.
3. **Emergent miscoordination.** The agents coordinate in a way the FDE did not anticipate: Agent A and Agent B both write to the blackboard at the same time, the writes conflict, the state is corrupted. The fix: a transaction layer on the blackboard (read-modify-write with optimistic concurrency).

The "hierarchy first, multi-agent only when forced" pattern is the FDE default. Hierarchy is simpler (single orchestrator), easier to debug (one log file), and easier to test (deterministic decomposition). Multi-agent is harder (no central control), harder to debug (emergent behavior), and harder to test (non-deterministic interaction). **The FDE picks hierarchy when the task is decomposable; multi-agent only when the task is fundamentally collaborative and no single agent can decompose it.**

The candidate examples for multi-agent are rare in production:
- **MoE language models** (the experts are agents; they vote on the next token)
- **Debate-style agents** (two agents argue; a judge decides; the argument surfaces uncertainty)
- **Simulation environments** (each agent is a market participant; the simulation emerges from their interaction)
- **Collaborative research** (multiple agents explore different aspects of a problem in parallel; they synthesize the result)

For 90% of FDE use cases (CS drafters, ops dashboards, cost analyzers, code generators), hierarchy is the right answer.

## The pattern

The multi-agent system, as a message-passing protocol:

```python
class MultiAgentSystem:
    """Peer-to-peer message passing. No central orchestrator."""

    def __init__(self, agents: dict[str, Agent]):
        self.agents = agents
        self.message_log = []
        self.max_round_trips = 10

    def run(self, goal: str, initiator: str) -> dict:
        """The initiator starts; agents pass messages peer-to-peer."""
        current_agent = initiator
        current_message = {"from": "user", "content": goal}
        round_trips = 0

        while round_trips < self.max_round_trips:
            # The current agent receives the message, decides what to do
            response = self.agents[current_agent].run(current_message["content"])
            self.message_log.append({"from": current_agent, "to": response.get("to"), "content": response.get("content")})

            if response.get("type") == "final":
                return {"answer": response["content"], "round_trips": round_trips}

            # Pass to the next agent (or back to the initiator)
            if response.get("to") not in self.agents:
                return {"error": "unknown_recipient", "agent": response.get("to")}

            current_message = {"from": current_agent, "content": response.get("content")}
            current_agent = response["to"]
            round_trips += 1

        return {"error": "max_round_trips_reached", "round_trips": round_trips}
```

The pattern that wins interviews is the "hierarchy first, multi-agent when forced" pattern. The candidate who says "I default to hierarchy because it's simpler, easier to debug, and easier to test. Multi-agent is for the rare cases where the task is fundamentally collaborative and no single agent can decompose it — MoE, debate, simulation. The wrong choice is multi-agent for a decomposable task (over-engineering, 5× cost). The right choice is hierarchy for decomposable; multi-agent only for collaborative" is the candidate who demonstrates the topology-mindset.

## Code or example

The hierarchy-vs-multi-agent decision rubric:

```python
def pick_topology(task: dict) -> str:
    """Pick hierarchy or multi-agent based on the task's structure."""
    decomposable = task.get("decomposable_by_single_agent", True)
    has_orchestrator = task.get("clear_manager_role", True)
    is_collaborative = task.get("fundamentally_collaborative", False)

    if is_collaborative and not decomposable:
        return "multi-agent"  # Force multi-agent only when task cannot be decomposed
    if has_orchestrator and decomposable:
        return "hierarchy"  # Default: hierarchy when decomposable
    return "single-agent"  # Even simpler: single agent when no decomposition needed
```

The 3-agent PacificFreight simulation (for demonstration; not the production default):

```python
# Three agents representing Mei, Sarah, and Daniel — they negotiate a complex case
# via peer-to-peer message passing.

MEI_AGENT = Agent(CS_DRAFTER_PROMPT, ...)
SARAH_AGENT = Agent(OPS_SUMMARIZER_PROMPT, ...)
DANIEL_AGENT = Agent(COST_ANALYST_PROMPT, ...)

PF_MULTI_AGENT = MultiAgentSystem({
    "mei": MEI_AGENT,
    "sarah": SARAH_AGENT,
    "daniel": DANIEL_AGENT,
})

# Customer email about a complex case
result = PF_MULTI_AGENT.run(
    goal="Customer wants status on 3 shipments + 2 refunds + 1 escalation. "
         "What's the best response?",
    initiator="mei",  # Mei starts
)
# Mei -> Sarah (asks for summary) -> Daniel (asks for cost check) -> Mei (synthesizes)
# No manager; the agents figure out the order.
```

The production-default comparison:

```python
# Hierarchy (recommended for PacificFreight):
# - Orchestrator = Mei (CS-drafter role)
# - Sub-agents = Sarah (ops), Daniel (cost)
# - Decomposition is explicit; synthesis is Mei's job
# - Debug log: orchestrator's transcript + each sub-agent's transcript
# - Cost: 1 orchestrator call + 3 sub-agent calls = $0.04

# Multi-agent (NOT recommended for PacificFreight):
# - No orchestrator
# - Agents pass messages peer-to-peer
# - Decomposition is emergent; synthesis is whoever sends the final message
# - Debug log: message_log (hard to follow; non-deterministic order)
# - Cost: 5-8 round-trips × $0.005 = $0.025-0.040
# - Risk: emergent miscoordination, message loops, deadlocks
# - Verdict: over-engineered; use hierarchy instead
```

## Production addendum

The hierarchy-vs-multi-agent question is the answer to "when do you need multiple agents vs one." The 60-second script:

> "Hierarchy first. The orchestrator decomposes, dispatches, and synthesizes. Each sub-agent has its own system prompt, tool list, cost ceiling, and circuit breaker. Hierarchy is simpler, easier to debug, easier to test. Multi-agent is for the rare cases where the task is fundamentally collaborative and no single agent can decompose it: MoE (experts vote on the next token), debate-style agents (two agents argue, a judge decides), simulations (agents are market participants). **For 90% of FDE use cases — CS drafters, ops dashboards, cost analyzers, code generators — hierarchy is the right answer.** The wrong choice is multi-agent for a decomposable task (over-engineering, 5× cost, hard to debug). The wrong choice is a single agent for a fundamentally collaborative task (the agent cannot reason about its peers). The right choice is hierarchy when decomposable; multi-agent only when forced."

This is the difference between a candidate who says "I built a multi-agent system" and a candidate who says "I used hierarchy because the task was decomposable; multi-agent is reserved for the rare cases that demand it." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-5-multi-agent.py` — the multi-agent patterns.
- **Reference implementation**: `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/` — the production hierarchy (NOT multi-agent) with 3 sub-agents.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/07-orchestrator-pattern.md` — hierarchy as the FDE default.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/` — the canonical hierarchy reference.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — multi-agent as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you need multiple agents vs one?"** Answer: multiple when (a) the task is fundamentally collaborative and cannot be decomposed by a single orchestrator, or (b) the parallelism gain is worth the complexity cost. For 90% of FDE use cases, one orchestrator + sub-agents (hierarchy) is simpler than multi-agent.
2. **"What is the difference between hierarchy and multi-agent?"** Answer: hierarchy has a single orchestrator that decomposes and synthesizes; multi-agent has multiple agents collaborating peer-to-peer with no central manager. Hierarchy is deterministic and testable; multi-agent is emergent and harder to debug.
3. **"What are the 3 failure modes of multi-agent?"** Answer: (1) message loops (A→B→A, fix: round-trip counter), (2) deadlocks (A waits for B, B waits for A, fix: per-message timeout), (3) emergent miscoordination (concurrent blackboard writes conflict, fix: optimistic concurrency on the blackboard).

## Read next

`L3-6-tool-using-agents.md` — the sixth lecture. Every agent uses tools, but the depth varies: the canonical tool-using agent has 1-3 tools and a tight loop; the research-grade tool-using agent has 10+ tools and a planner. The depth depends on the task's tool complexity.