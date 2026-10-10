# L2.7: Combining the seven ingredients

> **FDE framing in one line:** a production agent is 7 ingredients composed inside 5 guardrails. The ingredients are necessary; the guardrails are sufficient. The candidate who can name all 7 ingredients and all 5 guardrails is the candidate who passes the centerpiece round.

## The 3 things you'll learn

1. The 7 ingredients composed: model + tools + memory + cost ceiling + system prompt + parser + loop driver.
2. The 5 guardrails wrapped: loop detector + schema validator + cost ceiling + idempotency + audit log.
3. The "shipping agent" reference implementation: 200 lines of stdlib-only Python that composes all 7 ingredients and all 5 guardrails.

## Concept

The seven ingredients compose in a single canonical pattern. The pattern is the shipping agent; the shipping agent is what the FDE writes once and reuses across customers. The pattern has three concentric layers:

- **Inner layer — the 7 ingredients.** The model (decision function), the tools (action space), the memory (state across steps), the cost ceiling (budget enforcement), the system prompt (contract with the model), the parser (extractor of structured actions), the loop driver (the for-loop that bounds the run).
- **Middle layer — the 5 guardrails.** The loop detector (catches confused iterations), the schema validator (catches malformed tool calls), the cost ceiling (catches budget blowouts), idempotency (prevents double-writes), the audit log (the artifact the on-call reads).
- **Outer layer — the 5 cross-process FDE patterns.** The cost-ceiling-as-score (dashboard), the circuit breaker (cross-process fault isolation), the per-tenant rate limiter (per-customer resource budget), the audit log (cross-process observability), the "FDE has left" test (handoff verification).

The three layers compose. The inner layer is necessary; without the 7 ingredients, there is no agent. The middle layer is necessary; without the 5 guardrails, the agent is a prototype that fails in production. The outer layer is necessary; without the 5 cross-process patterns, the agent is a local service that does not scale across customers. **An FDE candidate who can name all three layers is the candidate who can ship a production agent.**

The 7 ingredients composed in 1 mental model:

```python
def run_agent(goal: str, agent: Agent) -> dict:
    """The shipping agent. 7 ingredients + 5 guardrails in 200 lines."""
    # 1. System prompt (rendered at startup from tool registry)
    # 2. Memory (three-tier: short-term + long-term + episodic)
    # 3. Cost ceiling (per-run, per-tenant, per-process)
    # 4. Loop driver (the for-loop below)
    # 5. Parser (extracts structured action from model output)
    # 6. Tool registry (the dispatch table)
    # 7. Model (the decision function)
    messages = agent.memory.compose_prompt(goal)
    for turn in range(1, agent.max_turns + 1):
        # Guardrail 1: cost ceiling
        if agent.cost_tracker.run_cost > agent.cost_tracker.max_run_usd:
            return {"error": "cost_ceiling_breached", "turns": turn, "cost_usd": agent.cost_tracker.run_cost}
        # Decision (the model call)
        output = agent.llm(messages)
        agent.cost_tracker.record_llm_call(agent.model, count_tokens(messages), count_tokens(output))
        messages.append({"role": "assistant", "content": output})
        # Parse
        step = agent.parser(output)
        if step["type"] == "final":
            agent.memory.append_episode(summarize(messages))  # Memory update
            agent.audit_log.record("final", turn=turn, cost=agent.cost_tracker.run_cost)
            return {"answer": step["answer"], "turns": turn, "cost_usd": agent.cost_tracker.run_cost}
        if step["type"] == "malformed":
            # Guardrail: structured error observation (no crash)
            messages.append({"role": "tool", "content": json.dumps({"_ok": False, "_err": "malformed", "hint": step["hint"]})})
            continue
        # Guardrail 2: schema validator (tool call)
        result = agent.tool_registry.call(step["tool"], step["args"])  # validates + dispatches
        if not result["_ok"]:
            # Guardrail 3: idempotency on write tools (the registry handles this)
            pass
        # Guardrail 4: loop detector (track recent tool calls)
        if agent.loop_detector.record(step["tool"]):
            return {"error": "loop_detected", "tool": step["tool"], "turns": turn}
        # Observation
        messages.append({"role": "tool", "content": json.dumps(result)})
        # Guardrail 5: audit log (record every step)
        agent.audit_log.record("tool_call", turn=turn, tool=step["tool"], args=step["args"], result=result, cost=agent.cost_tracker.run_cost)
    return {"error": f"max_turns_reached", "turns": agent.max_turns, "cost_usd": agent.cost_tracker.run_cost}
```

The 200-line shipping agent is the answer to the centerpiece-round "walk me through the architecture of a production agent" question. The candidate who can sketch this loop in 60 seconds and name every ingredient and every guardrail is the candidate who demonstrates the FDE mindset.

## The pattern

The 7 ingredients as a class:

```python
@dataclass
class Agent:
    """The 7 ingredients, composed. The shipping agent."""
    # 1. The decision function
    model: str
    llm: Callable

    # 2. The tool registry (the action space)
    tool_registry: ToolRegistry

    # 3. The memory layer
    memory: MemoryStore

    # 4. The cost ceiling (the budget)
    cost_tracker: CostTracker

    # 5. The system prompt (the contract)
    system_prompt: str  # rendered at startup from tool_registry

    # 6. The parser (the action extractor)
    parser: Callable

    # 7. The loop driver (the for-loop)
    max_turns: int = 10

    # Guardrails (wrapping the loop)
    loop_detector: LoopDetector = field(default_factory=LoopDetector)
    audit_log: AuditLog = field(default_factory=AuditLog)
```

The class is the single source of truth. The FDE writes `agent = Agent(model="gpt-5-mini", tool_registry=TOOLS, memory=memory, ...)` and the agent is ready. The `run_agent(goal, agent)` function is a method on the class; the 7 ingredients are constructor args; the 5 guardrails are instance state.

The pattern that wins interviews is the "7 ingredients + 5 guardrails in 200 lines" pattern. The candidate who says "the 7 ingredients compose into a single class, the 5 guardrails wrap the loop driver, the run_agent function is 30 lines, the whole shipping agent is 200 lines, the FDE writes it once and reuses it across customers" is the candidate who demonstrates the production mindset.

## Code or example

The shipping agent, stdlib-only, 200 lines:

```python
import re, json, time, hashlib
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

# === INGREDIENT 5: The system prompt (rendered at startup) ===================

def render_system_prompt(tools: dict) -> str:
    lines = [f"- {n}({', '.join(s['input_schema'].keys())}) -> {s.get('output_description', 'see fn')}"
             for n, s in tools.items()]
    return f"""You are an agent. Use Thought/Action/Observation to solve the goal.
Tools:
{chr(10).join(lines)}
Format: Thought: ... | Action: tool(args) | Final Answer: ...
"""

# === INGREDIENT 6: The parser =================================================

ACTION_RE = re.compile(r"^Action:\s*([a-zA-Z_]\w*)\s*\((.*)\)\s*$", re.DOTALL | re.MULTILINE)
FINAL_RE  = re.compile(r"^Final Answer:\s*(.+)$", re.DOTALL | re.MULTILINE)

def parse_step(output: str) -> dict:
    m = FINAL_RE.search(output)
    if m: return {"type": "final", "answer": m.group(1).strip()}
    m = ACTION_RE.search(output)
    if m: return {"type": "action", "tool": m.group(1), "args_raw": m.group(2).strip()}
    return {"type": "malformed", "raw": output[:500], "hint": "expected Action: tool(args) or Final Answer: ..."}

# === INGREDIENT 2: The tool registry (with schema validator + idempotency) ===

class ToolRegistry:
    def __init__(self, tools: dict):
        self.tools = tools
        self.idempotency_cache = {}  # sha256(args) -> result

    def call(self, name: str, args: dict) -> dict:
        if name not in self.tools:
            return {"_ok": False, "_err": "unknown_tool", "tool": name}
        # Idempotency: same args -> same result, no double-write
        arg_hash = hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()
        if arg_hash in self.idempotency_cache:
            return {"_ok": True, "result": self.idempotency_cache[arg_hash], "_idempotent": True}
        # Schema validation (simplified)
        schema = self.tools[name].get("input_schema", {})
        for field in schema:
            if field not in args:
                return {"_ok": False, "_err": "schema_violation", "violations": [f"missing field: {field}"]}
        try:
            result = self.tools[name]["function"](args)
            # Cache the result for idempotency
            if self.tools[name].get("idempotent", False):
                self.idempotency_cache[arg_hash] = result
            return {"_ok": True, "result": result}
        except Exception as e:
            return {"_ok": False, "_err": "tool_exception", "message": str(e)}

# === INGREDIENT 3: The memory layer (three-tier, simplified) ===================

class MemoryStore:
    def __init__(self):
        self.short_term = []
        self.long_term = {}  # text -> embedding (simplified)
        self.episodes = []

    def compose_prompt(self, goal: str, system_prompt: str) -> list:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": goal},
        ]

    def append_episode(self, summary: dict):
        self.episodes.append(summary)

# === INGREDIENT 4: The cost ceiling ==========================================

PRICING = {"gpt-5-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000}}

class CostTracker:
    def __init__(self, max_run_usd: float = 0.50):
        self.run_cost = 0.0
        self.max_run_usd = max_run_usd

    def record_llm_call(self, model, input_tokens, output_tokens):
        self.run_cost += PRICING[model]["input"] * input_tokens + PRICING[model]["output"] * output_tokens

    def record_tool_call(self, cost_credits):
        self.run_cost += cost_credits * 0.001

# === GUARDRAIL: The loop detector ===========================================

class LoopDetector:
    def __init__(self, window: int = 3):
        self.recent = deque(maxlen=window)
    def record(self, tool: str) -> bool:
        self.recent.append(tool)
        return len(self.recent) == self.recent.maxlen and len(set(self.recent)) == 1

# === GUARDRAIL: The audit log ===============================================

class AuditLog:
    def __init__(self):
        self.entries = []
    def record(self, event: str, **kwargs):
        self.entries.append({"ts": time.time(), "event": event, **kwargs})

# === THE 7 INGREDIENTS + 5 GUARDRAILS COMPOSED ===============================

@dataclass
class Agent:
    model: str
    llm: Callable
    tool_registry: ToolRegistry
    memory: MemoryStore
    cost_tracker: CostTracker
    system_prompt: str
    parser: Callable = parse_step
    max_turns: int = 10
    loop_detector: LoopDetector = field(default_factory=LoopDetector)
    audit_log: AuditLog = field(default_factory=AuditLog)

    def run(self, goal: str) -> dict:
        messages = self.memory.compose_prompt(goal, self.system_prompt)
        for turn in range(1, self.max_turns + 1):
            if self.cost_tracker.run_cost > self.cost_tracker.max_run_usd:
                return {"error": "cost_ceiling_breached", "turns": turn}
            output = self.llm(messages)
            self.cost_tracker.record_llm_call(self.model, len(str(messages)) // 4, len(output) // 4)
            messages.append({"role": "assistant", "content": output})
            step = self.parser(output)
            self.audit_log.record("step", turn=turn, type=step["type"])
            if step["type"] == "final":
                self.memory.append_episode({"goal": goal, "answer": step["answer"]})
                return {"answer": step["answer"], "turns": turn, "cost_usd": self.cost_tracker.run_cost}
            if step["type"] == "malformed":
                messages.append({"role": "tool", "content": json.dumps({"_ok": False, "_err": "malformed", "hint": step["hint"]})})
                continue
            result = self.tool_registry.call(step["tool"], parse_args_best_effort(step["args_raw"]))
            self.cost_tracker.record_tool_call(self.tool_registry.tools.get(step["tool"], {}).get("cost_credits", 0))
            if self.loop_detector.record(step["tool"]):
                return {"error": "loop_detected", "tool": step["tool"]}
            messages.append({"role": "tool", "content": json.dumps(result)})
        return {"error": "max_turns_reached", "turns": self.max_turns}
```

The 200-line agent is the synthesis. The FDE writes it once. The FDE reuses it across customers by changing the tool registry, the system prompt, the model, the memory backend, and the cost ceiling. **The agent is the platform; the customer is the configuration.**

## Production addendum

The "walk me through the architecture of a production agent" answer is the synthesis of L2.1 through L2.6. The 60-second script:

> "Seven ingredients. Model (the decision function, picked by the 4-axis rubric: capability, latency, cost, context). Tools (the action space, defined by name, description, input schema, output schema; the registry validates every call). Memory (three tiers: short-term in the prompt, long-term in a vector DB, episodic in summaries). Cost ceiling (three levels: per-run, per-tenant, per-process). System prompt (the contract with the model, five sections, rendered at startup, version-controlled). Parser (the action extractor, never crashes, returns structured errors the model reads as observations). Loop driver (the for-loop that bounds the run). **Five guardrails wrap the loop:** loop detector (catches confused iterations), schema validator (catches malformed tool calls, returns structured 403), cost ceiling (catches budget blowouts), idempotency (prevents double-writes on retries), audit log (the artifact the on-call reads at 3am). The whole agent is 200 lines. The FDE writes it once. The customer is the configuration: tool registry + system prompt + cost ceiling + memory backend."

This 60-second pitch is the difference between a candidate who says "I built an agent" and a candidate who says "7 ingredients, 5 guardrails, 200 lines, the customer is the configuration." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-6-production-agents.py` — the full shipping agent with all 5 guardrails.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/09-react-agent-tools.py` — production-grade ReAct with 5+ tools, error recovery, stuck detector, iteration budget, cost + time tracking, structured logging.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/` — the 7 ingredients and 5 guardrails as FDE patterns.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/` — three sub-agents each composed of 7 ingredients + 5 guardrails.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the centerpiece system design pattern.

## The 3 questions this lecture preps you for

1. **"What are the 7 ingredients of a production agent?"** Answer: (1) model (decision function, 4-axis rubric), (2) tools (action space, name + description + input schema + output schema), (3) memory (three tiers: short-term + long-term + episodic), (4) cost ceiling (three levels: per-run + per-tenant + per-process), (5) system prompt (contract with the model, five sections), (6) parser (action extractor, never crashes), (7) loop driver (the for-loop that bounds the run).
2. **"What are the 5 guardrails?"** Answer: (1) loop detector (catches confused iterations on the same tool), (2) schema validator (catches malformed tool calls, returns structured 403), (3) cost ceiling (catches budget blowouts at three levels), (4) idempotency (prevents double-writes on retries via sha256(args) cache), (5) audit log (the artifact the on-call reads at 3am; records every step with type + tool + args + result + cost).
3. **"Walk me through the architecture of a production agent."** Answer: 7 ingredients composed in 200 lines. The agent is a class; the constructor takes the 7 ingredients; the `run(goal)` method is the 30-line loop driver; the 5 guardrails are instance state. The FDE writes the class once; the customer is the configuration (tool registry, system prompt, cost ceiling, memory backend). **The agent is the platform; the customer is the configuration.**

## Read next

`S3-types-of-ai-agents/L3-1-reactive-vs-proactive-agents.md` — Section 3 decomposes agents by topology. The 7 ingredients compose into different agent types: reactive (one-shot), proactive (loop), hybrid (loop with a reactive fallback), hierarchical (orchestrator + sub-agents), and multi-agent (multiple agents sharing state). The 7 ingredients are invariant; the topology is the variable.