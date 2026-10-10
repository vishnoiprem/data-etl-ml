# L3.8: Picking the right topology — the 4-axis rubric

> **FDE framing in one line:** the right agent is the simplest one that satisfies the 4-axis topology rubric. Pick reactive before proactive, single-purpose before general-purpose, reflex before deliberative, single-agent before hierarchy. Add complexity only when the rubric demands it.

## In 60 seconds

> "Four axes: tool count, plan depth, agent count, latency budget. Six canonical shapes: reactive one-shot (1 tool, 1 step, 1 agent, < 1s), single-purpose loop (1-3 tools, 2-5 steps, 1 agent, 1-10s), general-purpose loop (4-7 tools, 6-10 steps, 1 agent, 10-60s), plan-and-execute (4-10 tools, 6-10 steps, 1 agent with explicit plan), hierarchical (1 orchestrator + 2-3 sub-agents, parallel sub-tasks), multi-agent (3+ agents, peer-to-peer, rare). **Default to the simplest; escalate only when the rubric fails.** The escalation path: 1 → 2 → 3 → 4 → 5 → 6. The wrong choice is the most complex topology from the start (over-engineering, 5-10× cost). The wrong choice is the simplest for a complex task (under-engineering, 60% accuracy). The right choice is the simplest that satisfies the rubric."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The 4-axis topology rubric: tool count, plan depth, agent count, latency budget — and which axis dominates for which task.
2. The "simplest topology that works" pattern: start with single-agent reactive reflex; escalate only when the rubric fails.
3. The 6 canonical topology shapes and when to use each: reactive one-shot, single-purpose loop, general-purpose loop, plan-and-execute, hierarchical, multi-agent.

## Concept

The 4-axis topology rubric is the FDE's primary design decision for an agent. The 4 axes:

1. **Tool count.** How many tools does the task require? ≤ 1 = single-purpose; 2-7 = minimum viable set; 8+ = consider sub-agents to maintain accuracy.
2. **Plan depth.** How many steps does the task typically take? 1 = reflex; 2-5 = plan-and-execute; 6+ = plan-and-replan; 10+ = consider HTN or hierarchy.
3. **Agent count.** How many distinct roles does the task require? 1 = single-agent; 2-3 = hierarchy; 4+ = consider multi-agent.
4. **Latency budget.** How fast does the user need the answer? < 1s = reactive; 1-10s = single-purpose loop; 10-60s = general-purpose loop; 60s+ = hierarchical with parallelism.

The "simplest topology that works" pattern is the FDE default. The candidate who proposes the most complex topology (multi-agent, HTN, hierarchical with sub-sub-agents) is over-engineering; the candidate who proposes the simplest (reactive one-shot) for a complex task is under-engineering. **The right answer is the simplest topology that satisfies all 4 axes.**

The 6 canonical topology shapes, in order of complexity:

1. **Reactive one-shot.** 1 LLM call, 0-1 tool calls, no loop, no state. For: classification, extraction, single-step Q&A, simple transformations.
2. **Single-purpose loop.** 1 agent, 1-3 tools, reactive inner, proactive outer (ReAct or PaE). For: 80% of FDE use cases (CS drafter, ops dashboard, cost analyzer).
3. **General-purpose loop.** 1 agent, 4-7 tools, plan-and-execute, hybrid (proactive outer + reactive inner). For: research agents, code generators, complex multi-tool tasks.
4. **Plan-and-execute (PaE).** 1 agent, 4-10 tools, plan-first then execute, replan on contradiction. For: tasks with clear sub-steps (book a flight, file a tax return).
5. **Hierarchical.** 1 orchestrator + 2-3 sub-agents, each with its own system prompt + tool list + circuit breaker. For: multi-role workflows (CS + ops + cost), parallel sub-tasks, context isolation.
6. **Multi-agent.** 3+ agents, peer-to-peer message passing or shared blackboard, no central manager. For: rare cases — MoE, debate, simulation.

The FDE's job is to pick the simplest shape that satisfies the rubric. The escalation path: 1 → 2 → 3 → 4 → 5 → 6. The candidate who can articulate the rubric and the escalation path is the candidate who demonstrates the topology-mindset.

## The pattern

The 4-axis rubric as a function:

```python
@dataclass
class TopologyDecision:
    tool_count: int          # 1, 2-7, 8+
    plan_depth: int          # 1, 2-5, 6-10, 10+
    agent_count: int         # 1, 2-3, 4+
    latency_budget_s: float  # < 1, 1-10, 10-60, 60+

def pick_topology(d: TopologyDecision) -> str:
    """The simplest topology that satisfies all 4 axes."""
    # Hard rules first
    if d.tool_count == 1 and d.plan_depth == 1 and d.agent_count == 1:
        return "reactive_one_shot"
    if d.tool_count <= 7 and d.plan_depth <= 5 and d.agent_count == 1 and d.latency_budget_s <= 10:
        return "single_purpose_loop"
    if d.tool_count <= 7 and d.plan_depth <= 10 and d.agent_count == 1:
        return "general_purpose_loop"
    if d.tool_count <= 10 and d.plan_depth <= 10 and d.agent_count == 1 and d.latency_budget_s <= 60:
        return "plan_and_execute"
    if d.agent_count <= 3 and d.tool_count <= 15 and d.latency_budget_s <= 60:
        return "hierarchical"
    if d.agent_count >= 4 or d.tool_count >= 20:
        return "multi_agent"
    return "general_purpose_loop"  # default
```

The escalation rule:

```python
def should_escalate(current: str, failures: dict) -> str:
    """Escalate to the next topology when the current one fails the rubric."""
    if failures.get("accuracy", 1.0) < 0.85 and current == "reactive_one_shot":
        return "single_purpose_loop"
    if failures.get("tool_selection_accuracy", 1.0) < 0.85 and current == "single_purpose_loop":
        return "general_purpose_loop"  # add planning
    if failures.get("end_to_end_accuracy", 1.0) < 0.85 and current == "general_purpose_loop":
        return "plan_and_execute"  # add explicit planning
    if failures.get("role_separation_needed", False) and current == "plan_and_execute":
        return "hierarchical"  # add sub-agents
    if failures.get("fundamentally_collaborative", False) and current == "hierarchical":
        return "multi_agent"  # last resort
    return current
```

The pattern that wins interviews is the "simplest topology that works + escalation only on failure" pattern. The candidate who says "I start with reactive one-shot; I escalate to single-purpose loop when the task is multi-step; I escalate to general-purpose loop when the tool count is 4-7; I escalate to plan-and-execute when the plan is non-trivial; I escalate to hierarchical when 3 roles are present; I escalate to multi-agent only when the task is fundamentally collaborative. **The wrong choice is the most complex topology from the start** (over-engineering, 5-10× cost). The right choice is the simplest topology that satisfies the 4-axis rubric" is the candidate who demonstrates the topology-mindset.

## Code or example

The 6 canonical topology shapes with their typical use cases:

```python
TOPOLOGY_USE_CASES = {
    "reactive_one_shot": [
        ("Classify this email as spam or not", "spam_classifier"),
        ("Extract the shipment_id from this email", "extractor"),
        ("Translate this text to Vietnamese", "translator"),
    ],
    "single_purpose_loop": [
        ("CS drafter for PacificFreight", "cs_drafter"),
        ("Ops dashboard summarizer", "ops_summarizer"),
        ("Cost analyzer for a single tenant", "cost_analyzer"),
    ],
    "general_purpose_loop": [
        ("Research agent (search + summarize + cite)", "researcher"),
        ("Code generator (read + write + test)", "coder"),
        ("Data analyst (query + plot + report)", "analyst"),
    ],
    "plan_and_execute": [
        ("Book a flight (search + compare + book)", "travel_agent"),
        ("File a tax return (gather + compute + submit)", "tax_agent"),
        ("Onboard a new customer (KYC + setup + welcome)", "onboarder"),
    ],
    "hierarchical": [
        ("Multi-role workflow (CS + ops + cost)", "dispatcher"),
        ("Parallel sub-tasks (3 lookups in parallel)", "parallel_researcher"),
        ("Context isolation (3 different tool lists)", "multi_tenant_agent"),
    ],
    "multi_agent": [
        ("Mixture of experts (MoE)", "moe_router"),
        ("Debate (argue + judge)", "debater"),
        ("Simulation (market participants)", "simulator"),
    ],
}
```

The PacificFreight case study (topology decisions over time):

```python
# Phase 1: Reactive one-shot. 1 LLM call, 1 tool (tracker.lookup).
# Use case: "Where is my shipment PF-1003?" — 30% of emails.
# Topology: reactive_one_shot. Latency: < 1s. Cost: $0.001.

# Phase 2: Single-purpose loop. 1 agent, 3 tools (lookup, refund, escalate).
# Use case: CS drafter for status + refund + escalation — 80% of emails.
# Topology: single_purpose_loop. Latency: 5-10s. Cost: $0.01-0.05.

# Phase 3: Hierarchical. 1 orchestrator (Mei) + 2 sub-agents (Sarah, Daniel).
# Use case: Multi-shipment + multi-role workflows — 10% of emails.
# Topology: hierarchical. Latency: 10-30s. Cost: $0.05-0.20.

# Phase 4 (capstone): All 5 topologies coexist. Each email routed to the simplest
# topology that satisfies the rubric. Total cost: $0.50/week for 150 emails/day.
```

## Production addendum

The "how do you pick the right agent topology" question is the synthesis of L3.1-L3.7. The 60-second script:

> "Four axes: tool count, plan depth, agent count, latency budget. Six canonical shapes: reactive one-shot (1 tool, 1 step, 1 agent, < 1s), single-purpose loop (1-3 tools, 2-5 steps, 1 agent, 1-10s), general-purpose loop (4-7 tools, 6-10 steps, 1 agent, 10-60s), plan-and-execute (4-10 tools, 6-10 steps, 1 agent with explicit plan), hierarchical (1 orchestrator + 2-3 sub-agents, parallel sub-tasks), multi-agent (3+ agents, peer-to-peer, rare). **Default to the simplest; escalate only when the rubric fails.** The escalation path: 1 → 2 → 3 → 4 → 5 → 6. The wrong choice is the most complex topology from the start (over-engineering, 5-10× cost). The wrong choice is the simplest for a complex task (under-engineering, 60% accuracy). The right choice is the simplest that satisfies the rubric."

This is the difference between a candidate who says "I built a multi-agent system" and a candidate who says "I picked the simplest topology that satisfied the 4-axis rubric; I escalated only when the simpler one failed; the production system has 3 topologies coexisting, each email routed to the right one." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-6-production-agents.py` — the topology router.
- **Reference implementation**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the 3-topology coexistence (reactive, single-purpose, hierarchical).
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the topology rubric as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the canonical topology coexistence.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — topology as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How do you pick the right agent topology?"** Answer: 4-axis rubric (tool count, plan depth, agent count, latency budget) → 6 canonical shapes (reactive, single-purpose, general-purpose, plan-and-execute, hierarchical, multi-agent). Default to the simplest; escalate only when the rubric fails. The escalation path: 1 → 2 → 3 → 4 → 5 → 6.
2. **"What is the simplest topology that works?"** Answer: depends on the task. For 30% of CS-drafter emails, the simplest is reactive one-shot (1 LLM call, 1 tool, < 1s). For 80% of CS-drafter emails, single-purpose loop (1 agent, 3 tools, 5-10s). For 10% (multi-shipment), hierarchical (1 orchestrator + 2 sub-agents, 10-30s). **The right topology is the simplest that satisfies the rubric; multiple topologies coexist in production, each email routed to the right one.**
3. **"When do you escalate from single-purpose to general-purpose?"** Answer: when the tool count exceeds 7 (accuracy drops below 85%) or the plan depth exceeds 5 (the agent cannot reason about the future without explicit planning). Escalation adds: more tools, more planning, possibly a sub-agent for context isolation. The cost is 2-5×; the accuracy gain is 10-20 percentage points.

## Read next

`S4-guiding-and-teaching/L4-1-prompt-engineering-for-agents.md` — Section 4 dives into the third precondition: how to teach the agent what to do. The 7 ingredients from Section 2 compose into topologies from Section 3; the question Section 4 answers is "how do you write the system prompt + the few-shot examples + the chain-of-thought that makes the model do the right thing."
