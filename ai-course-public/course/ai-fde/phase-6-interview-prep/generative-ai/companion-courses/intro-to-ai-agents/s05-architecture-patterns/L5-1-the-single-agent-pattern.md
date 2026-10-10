# L5.1: The single-agent pattern

> **FDE framing in one line:** the single-agent pattern is 1 decision function, 1 tool list, 1 loop. It is the foundation; every other architecture pattern composes it. The FDE default for 80% of use cases.

## The 3 things you'll learn

1. The 4 components of the single-agent pattern: model, tools, memory, cost ceiling — composed in 200 lines.
2. The "single agent is enough until it isn't" heuristic: the escalation triggers to multi-agent.
3. The 7-ingredient + 5-guardrail composition as a single class.

## Concept

The single-agent pattern is the canonical 7-ingredient + 5-guardrail composition from L2.7. The pattern has four components: the model (the decision function), the tool list (the action space), the memory (the state across steps), and the cost ceiling (the budget). The loop driver ties them together; the 5 guardrails wrap the loop. **The single-agent pattern is the FDE default; every other architecture pattern composes it.**

The "single agent is enough until it isn't" heuristic is the FDE's primary design decision. The single agent is enough when:

1. **The task is single-role.** The system prompt, the tool list, and the cost ceiling can describe the agent's job in one paragraph. If the agent's job requires 3 different roles (CS drafter + ops summarizer + cost analyst), the system prompt becomes a wall of text and the tool list exceeds 7 tools.
2. **The plan depth is ≤ 5 steps.** A 10-step plan fits in the model's context window; the agent can reason about the future without explicit planning. A 20-step plan needs an explicit plan-and-execute pattern.
3. **The tool count is ≤ 7.** Below 7, the model picks the right tool 95% of the time. Above 7, accuracy drops sharply. A 15-tool agent needs a sub-agent for context isolation.
4. **The latency budget is ≤ 60s.** A 10-step agent at ~3s/step is 30s. A 30-step agent at ~3s/step is 90s — over budget.

When any of these conditions fails, escalate to multi-agent. **The escalation triggers are objective; the FDE measures the failure and picks the next pattern.**

## The pattern

The single-agent class (200 lines, stdlib-only):

```python
import re, json, time, hashlib
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

# Component 1: The model (decision function)
@dataclass
class Model:
    name: str
    fn: Callable
    pricing: dict  # {"input": float, "output": float} per 1M tokens

# Component 2: The tool list (action space)
@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    cost_credits: int
    function: Callable
    idempotent: bool = False

class ToolRegistry:
    def __init__(self, tools: list[Tool]):
        self.tools = {t.name: t for t in tools}
        self.idempotency_cache = {}

    def call(self, name: str, args: dict) -> dict:
        if name not in self.tools:
            return {"_ok": False, "_err": "unknown_tool"}
        tool = self.tools[name]
        # Schema validation (simplified)
        for field_name in tool.input_schema:
            if field_name not in args:
                return {"_ok": False, "_err": "missing_field", "field": field_name}
        # Idempotency check
        arg_hash = hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()
        if tool.idempotent and arg_hash in self.idempotency_cache:
            return {"_ok": True, "result": self.idempotency_cache[arg_hash], "_idempotent": True}
        # Dispatch
        try:
            result = tool.function(args)
            if tool.idempotent:
                self.idempotency_cache[arg_hash] = result
            return {"_ok": True, "result": result}
        except Exception as e:
            return {"_ok": False, "_err": "exception", "message": str(e)}

# Component 3: The memory (state across steps)
class Memory:
    def __init__(self):
        self.short_term = []  # messages
        self.long_term = {}   # key -> value
        self.episodes = []    # past sessions

# Component 4: The cost ceiling (budget)
class CostCeiling:
    def __init__(self, max_run_usd: float = 0.50):
        self.run_cost = 0.0
        self.max_run_usd = max_run_usd

    def record(self, model: Model, input_tokens: int, output_tokens: int):
        self.run_cost += model.pricing["input"] * input_tokens + model.pricing["output"] * output_tokens

    def breached(self) -> bool:
        return self.run_cost > self.max_run_usd

# The single-agent class
@dataclass
class SingleAgent:
    model: Model
    tools: ToolRegistry
    memory: Memory
    cost: CostCeiling
    system_prompt: str
    max_turns: int = 10
    loop_window: int = 3

    def run(self, goal: str) -> dict:
        messages = [{"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": goal}]
        recent_tools = deque(maxlen=self.loop_window)
        for turn in range(1, self.max_turns + 1):
            if self.cost.breached():
                return {"error": "cost_ceiling_breached", "turns": turn}
            output = self.model.fn(messages)
            self.cost.record(self.model, len(str(messages)) // 4, len(output) // 4)
            messages.append({"role": "assistant", "content": output})
            step = parse_step(output)
            if step["type"] == "final":
                return {"answer": step["answer"], "turns": turn, "cost_usd": self.cost.run_cost}
            if step["type"] == "malformed":
                messages.append({"role": "tool", "content": json.dumps({"_ok": False, "_err": "malformed"})})
                continue
            result = self.tools.call(step["tool"], step["args"])
            # Loop detection
            recent_tools.append(step["tool"])
            if len(recent_tools) == self.loop_window and len(set(recent_tools)) == 1:
                return {"error": "loop_detected", "tool": step["tool"]}
            messages.append({"role": "tool", "content": json.dumps(result)})
        return {"error": "max_turns_reached", "turns": self.max_turns}
```

The pattern that wins interviews is the "single agent is enough until it isn't" pattern. The candidate who says "I start with a single agent. I measure the failure modes: tool selection accuracy, plan depth, latency, role complexity. I escalate to multi-agent only when one of the 4 conditions fails. The single agent is the FDE default for 80% of use cases" is the candidate who demonstrates the architecture-mindset.

## Code or example

The escalation decision rubric:

```python
@dataclass
class SingleAgentMetrics:
    tool_selection_accuracy: float
    plan_depth_p95: int
    tool_count: int
    latency_p95_s: float
    role_count: int

def should_escalate(m: SingleAgentMetrics) -> str:
    """Decide whether to stay with single agent or escalate to multi-agent."""
    if m.tool_count > 7:
        return "orchestrator"  # Tool count too high; sub-agents for context isolation
    if m.plan_depth_p95 > 5:
        return "plan_and_execute"  # Plan depth too high; explicit planning
    if m.role_count > 1:
        return "orchestrator"  # Multiple roles; sub-agents for role separation
    if m.latency_p95_s > 60:
        return "parallel"  # Latency too high; parallel sub-tasks
    if m.tool_selection_accuracy < 0.85:
        return "orchestrator"  # Tool selection failing; sub-agents for fewer tools each
    return "single_agent"  # All conditions met; stay with single agent
```

The single-agent CS drafter (the canonical FDE use case):

```python
CS_DRAFTER_AGENT = SingleAgent(
    model=Model("gpt-5-mini", openai_chat, {"input": 0.15/1e6, "output": 0.60/1e6}),
    tools=ToolRegistry([
        Tool("tracker.lookup", "Look up a shipment.", {"shipment_id": str}, 1, tracker_lookup),
        Tool("refund.create", "Initiate a refund.", {"shipment_id": str, "amount_usd": float, "idempotency_key": str}, 10, refund_create, idempotent=True),
        Tool("translate.to", "Translate text.", {"text": str, "lang": str}, 5, translate_to),
        Tool("escalate.to_human", "Escalate to human.", {"reason": str, "priority": str}, 1, escalate),
        Tool("clarify", "Ask for clarification.", {"question": str}, 1, clarify),
    ]),
    memory=Memory(),
    cost=CostCeiling(max_run_usd=0.10),
    system_prompt=CS_DRAFTER_SYSTEM_PROMPT,
    max_turns=10,
)

# Result: handles 80% of PacificFreight emails. The other 20% are multi-shipment
# cases that escalate to the orchestrator pattern (L5.3).
```

## Production addendum

The single-agent question is the answer to "when do you need more than one agent." The 60-second script:

> "Single agent is the FDE default — 1 model, 1 tool list, 1 memory, 1 cost ceiling, 1 loop. It handles 80% of use cases. The escalation triggers: tool count > 7 (sub-agents for context isolation), plan depth > 5 (explicit planning), role count > 1 (sub-agents for role separation), latency p95 > 60s (parallel sub-tasks), tool selection accuracy < 85% (sub-agents for fewer tools each). **The escalation is objective: measure the failure mode, pick the next pattern.** The single agent is composed in 200 lines as a class. The 7 ingredients are constructor args; the 5 guardrails are instance state. The wrong choice is to start with multi-agent (5-10× cost, 3× complexity). The right choice is single agent, measure, escalate."

This is the difference between a candidate who says "I built a multi-agent system" and a candidate who says "single agent is the default; I measured the failure modes; I escalated to orchestrator when tool count exceeded 7; I escalated to plan-and-execute when plan depth exceeded 5." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-2-first-agent.py` — the canonical single-agent ReAct.
- **Reference implementation**: `course/practice/level-5-agents/lesson-9-6-production-agents.py` — the production single-agent with all 5 guardrails.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/02-the-fde-loop.md` — the single-agent loop.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/` — the single agent is the building block for the orchestrator.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — single agent as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you need more than one agent?"** Answer: when the single agent fails one of 4 conditions — tool count > 7, plan depth > 5, role count > 1, latency p95 > 60s, or tool selection accuracy < 85%. The escalation is objective; measure the failure mode, pick the next pattern.
2. **"What are the 4 components of the single-agent pattern?"** Answer: (1) model (the decision function), (2) tool list (the action space, 1-7 tools), (3) memory (state across steps: short-term + long-term + episodic), (4) cost ceiling (the budget). Composed in 200 lines as a class. The 5 guardrails wrap the loop.
3. **"How do you compose the single-agent pattern?"** Answer: as a class with 7 constructor args (model, tools, memory, cost ceiling, system prompt, max_turns, loop_window). The `run(goal)` method is the loop driver: compose prompt → for each turn → check cost ceiling → call model → parse → dispatch tool → detect loop → record observation. The wrong choice is a 1000-line god-object with 15 tools and 3 memory backends. The right choice is the 200-line class, single agent, measure, escalate.

## Read next

`L5-2-the-sequential-pipeline-pattern.md` — the second pattern. The sequential pipeline is agent A's output is agent B's input. For workflows with clear handoffs (e.g., research → summarize → translate). The pipeline is simpler than the orchestrator but more rigid.