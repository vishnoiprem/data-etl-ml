# L6.2: Building the minimum viable agent — 200 lines, 7 ingredients, 5 guardrails

> **FDE framing in one line:** the minimum viable agent is 200 lines of stdlib Python. The 7 ingredients are constructor args; the 5 guardrails are instance state; the `run(goal)` method is the loop driver. The FDE writes it once and reuses it across customers.

## The 3 things you'll learn

1. The 200-line shipping agent: 7 ingredients as constructor args, 5 guardrails as instance state, `run(goal)` as the loop driver.
2. The "agent is the platform, customer is the configuration" pattern: change the tool registry, the system prompt, the model, the cost ceiling — never the loop.
3. The 5 production add-ons that take the agent from prototype to production: structured errors, idempotency, audit log, circuit breaker, cost ceiling.

## Concept

The minimum viable agent is the 200-line class that composes the 7 ingredients and wraps the loop with the 5 guardrails. The FDE writes it once, in stdlib Python (no framework dependencies), and reuses it across customers by changing the constructor args: the model, the tool registry, the memory backend, the cost ceiling, the system prompt. **The agent is the platform; the customer is the configuration.**

The 200-line structure:

1. **Imports (10 lines):** `re`, `json`, `time`, `hashlib`, `collections.deque`, `dataclasses`, `typing.Callable`.
2. **The 7 ingredients as classes (100 lines):** `Model`, `Tool`, `ToolRegistry`, `Memory`, `CostCeiling`, `SystemPrompt`, `Parser`.
3. **The 5 guardrails as classes (50 lines):** `LoopDetector`, `AuditLog`, `IdempotencyCache` (built into ToolRegistry), `SchemaValidator` (built into ToolRegistry), `CostCeiling` (already in #2).
4. **The `SingleAgent` class (40 lines):** the loop driver, the `run(goal)` method.

The 5 production add-ons that take the agent from prototype to production are not optional:

1. **Structured errors.** Every parse failure, every tool exception, every cost-ceiling breach returns a structured `_ok/_err` envelope the model can read. The agent never crashes; the model always knows what went wrong.
2. **Idempotency.** Every write tool keys on a stable hash of the canonical args. A retry produces the same side effect or none. The model can safely retry on transient errors.
3. **Audit log.** Every step is a typed log row: turn, event, tool, args, result, cost, tokens. The audit log is the artifact the on-call reads at 3am.
4. **Circuit breaker.** The agent's circuit breaker trips after N consecutive failures. The agent fails fast instead of spending the customer's budget on a broken service.
5. **Cost ceiling (already in the 7 ingredients, but worth emphasizing).** Three levels: per-run, per-tenant, per-process. The cost ceiling is the first guardrail the FDE writes; it is the first line of the runbook.

## The pattern

The 200-line shipping agent, in stdlib Python:

```python
# === IMPORTS (10 lines) =====================================================
import re, json, time, hashlib
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

# === INGREDIENT 1: The model (decision function) ============================
@dataclass
class Model:
    name: str
    fn: Callable
    pricing: dict  # {"input": float, "output": float} per 1M tokens

# === INGREDIENT 2: The tool list (action space) =============================
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
        self.idempotency_cache = {}  # Guardrail 4: idempotency

    def call(self, name: str, args: dict) -> dict:
        if name not in self.tools:
            return {"_ok": False, "_err": "unknown_tool"}
        tool = self.tools[name]
        # Guardrail 2: schema validation
        for field_name in tool.input_schema:
            if field_name not in args:
                return {"_ok": False, "_err": "missing_field", "field": field_name}
        # Guardrail 4: idempotency check
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

# === INGREDIENT 3: The memory (state across steps) ===========================
class Memory:
    def __init__(self):
        self.short_term = []
        self.long_term = {}
        self.episodes = []

# === INGREDIENT 4: The cost ceiling (budget) ================================
class CostCeiling:
    def __init__(self, max_run_usd: float = 0.50):
        self.run_cost = 0.0
        self.max_run_usd = max_run_usd
    def record(self, model: Model, input_tokens: int, output_tokens: int):
        self.run_cost += model.pricing["input"] * input_tokens + model.pricing["output"] * output_tokens
    def breached(self) -> bool:
        return self.run_cost > self.max_run_usd

# === INGREDIENT 5: The system prompt (contract with the model) ==============
def render_system_prompt(tools: dict, role: str, guardrails: list, examples: list) -> str:
    tool_lines = [f"- {n}({', '.join(s.input_schema.keys())})" for n, s in tools.items()]
    return f"""You are {role}.

## Tools
{chr(10).join(tool_lines)}

## Output format
Thought: <reasoning>
Action: tool_name(args)
Observation: <result>
Final Answer: <final response>

## Guardrails
{chr(10).join(f'- {g}' for g in guardrails)}

## Examples
{chr(10).join(json.dumps(ex) for ex in examples)}
"""

# === INGREDIENT 6: The parser (action extractor) =============================
ACTION_RE = re.compile(r"^Action:\s*([a-zA-Z_]\w*)\s*\((.*)\)\s*$", re.DOTALL | re.MULTILINE)
FINAL_RE  = re.compile(r"^Final Answer:\s*(.+)$", re.DOTALL | re.MULTILINE)

def parse_step(output: str) -> dict:
    m = FINAL_RE.search(output)
    if m: return {"type": "final", "answer": m.group(1).strip()}
    m = ACTION_RE.search(output)
    if m: return {"type": "action", "tool": m.group(1), "args_raw": m.group(2).strip()}
    return {"type": "malformed", "raw": output[:500], "hint": "expected Action: tool(args) or Final Answer: ..."}

# === GUARDRAIL 1: The loop detector =========================================
class LoopDetector:
    def __init__(self, window: int = 3):
        self.recent = deque(maxlen=window)
    def record(self, tool: str) -> bool:
        self.recent.append(tool)
        return len(self.recent) == self.recent.maxlen and len(set(self.recent)) == 1

# === GUARDRAIL 3: The audit log =============================================
class AuditLog:
    def __init__(self):
        self.entries = []
    def record(self, event: str, **kwargs):
        self.entries.append({"ts": time.time(), "event": event, **kwargs})

# === INGREDIENT 7 + THE LOOP DRIVER: The SingleAgent class ==================
@dataclass
class SingleAgent:
    model: Model
    tools: ToolRegistry
    memory: Memory
    cost: CostCeiling
    system_prompt: str
    max_turns: int = 10
    loop_detector: LoopDetector = field(default_factory=LoopDetector)
    audit_log: AuditLog = field(default_factory=AuditLog)

    def run(self, goal: str) -> dict:
        messages = [{"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": goal}]
        for turn in range(1, self.max_turns + 1):
            # Guardrail 5: cost ceiling check
            if self.cost.breached():
                self.audit_log.record("cost_ceiling_breached", turn=turn)
                return {"error": "cost_ceiling_breached", "turns": turn}
            # Decision (the model call)
            output = self.model.fn(messages)
            self.cost.record(self.model, len(str(messages)) // 4, len(output) // 4)
            messages.append({"role": "assistant", "content": output})
            self.audit_log.record("llm_call", turn=turn, cost=self.cost.run_cost)
            # Parse
            step = parse_step(output)
            if step["type"] == "final":
                self.audit_log.record("final", turn=turn, answer=step["answer"])
                return {"answer": step["answer"], "turns": turn, "cost_usd": self.cost.run_cost}
            if step["type"] == "malformed":
                # Guardrail 1: structured error observation
                messages.append({"role": "tool", "content": json.dumps({"_ok": False, "_err": "malformed", "hint": step["hint"]})})
                continue
            # Tool call
            try:
                args = json.loads(step["args_raw"])
            except Exception:
                args = {"raw": step["args_raw"]}
            result = self.tools.call(step["tool"], args)
            # Guardrail 1: loop detection
            if self.loop_detector.record(step["tool"]):
                self.audit_log.record("loop_detected", tool=step["tool"])
                return {"error": "loop_detected", "tool": step["tool"], "turns": turn}
            messages.append({"role": "tool", "content": json.dumps(result)})
            self.audit_log.record("tool_call", turn=turn, tool=step["tool"], args=args, result=result)
        return {"error": "max_turns_reached", "turns": self.max_turns}
```

The pattern that wins interviews is the "200 lines, agent is the platform, customer is the configuration" pattern. The candidate who says "the minimum viable agent is 200 lines of stdlib Python; the 7 ingredients are constructor args; the 5 guardrails are instance state; the FDE writes it once and reuses it across customers by changing the tool registry, the system prompt, the model, the cost ceiling. The 5 production add-ons (structured errors, idempotency, audit log, circuit breaker, cost ceiling) are not optional" is the candidate who demonstrates the shipping-agent mindset.

## Code or example

The customer-as-configuration pattern:

```python
# Customer 1: PacificFreight CS drafter
PF_AGENT = SingleAgent(
    model=Model("gpt-5-mini", openai_chat, {"input": 0.15/1e6, "output": 0.60/1e6}),
    tools=ToolRegistry([
        Tool("tracker.lookup", "Look up a shipment.", {"shipment_id": str}, 1, tracker_lookup),
        Tool("refund.create", "Initiate a refund.", {"shipment_id": str, "amount_usd": float, "idempotency_key": str}, 10, refund_create, idempotent=True),
        # ... 3 more tools
    ]),
    memory=Memory(),
    cost=CostCeiling(max_run_usd=0.10),
    system_prompt=CS_DRAFTER_SYSTEM_PROMPT,
)

# Customer 2: Acme Analytics data analyst (different model, different tools, different cost)
ACME_AGENT = SingleAgent(
    model=Model("gpt-5", openai_chat, {"input": 2.50/1e6, "output": 10/1e6}),  # Different model
    tools=ToolRegistry([
        Tool("pandas_query", "Run a pandas query.", {"code": str}, 5, sandbox_run),
        Tool("plot_chart", "Generate a chart.", {"data": str, "type": str}, 5, plot),
        # ... 2 more tools
    ]),
    memory=Memory(),
    cost=CostCeiling(max_run_usd=0.50),  # Different cost ceiling
    system_prompt=DATA_ANALYST_SYSTEM_PROMPT,  # Different system prompt
)

# Same agent class. Different configuration. The loop, the parser, the guardrails are invariant.
```

The 5 production add-ons (what takes the agent from prototype to production):

```python
# Add-on 1: Structured errors (built into parse_step + ToolRegistry.call)
# Every parse failure, every tool exception returns a typed _ok/_err envelope.

# Add-on 2: Idempotency (built into ToolRegistry.call)
# Write tools with idempotent=True key on sha256(args) and cache the result.

# Add-on 3: Audit log (built into AuditLog class)
# Every step recorded: turn, event, tool, args, result, cost, tokens.

# Add-on 4: Circuit breaker (add as a wrapper)
class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, reset_timeout_s: float = 60.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout_s = reset_timeout_s
        self.failures = 0
        self.opened_at = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.time() - self.opened_at > self.reset_timeout_s:
            self.opened_at = None
            self.failures = 0
            return True
        return False

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = time.time()

    def record_success(self):
        self.failures = 0

# Add-on 5: Cost ceiling (built into CostCeiling class)
# Three levels: per-run, per-tenant, per-process. The CostCeiling class is extended.
```

## Production addendum

The minimum viable agent question is the answer to "walk me through your minimum viable agent." The 60-second script:

> "200 lines of stdlib Python. 7 ingredients as constructor args: model, tools, memory, cost ceiling, system prompt, parser, loop driver. 5 guardrails as instance state: loop detector, audit log, idempotency cache (in tool registry), schema validator (in tool registry), cost ceiling. The `run(goal)` method is the loop driver: compose prompt → for each turn → check cost ceiling → call model → parse → dispatch tool → detect loop → record observation. **The agent is the platform; the customer is the configuration.** Change the tool registry, the system prompt, the model, the cost ceiling — never the loop. The 5 production add-ons (structured errors, idempotency, audit log, circuit breaker, cost ceiling) are not optional. The wrong choice is to start with a framework (5× complexity, hidden bugs). The right choice is stdlib first, then graduate when the requirements demand it."

This is the difference between a candidate who says "I built an agent" and a candidate who says "200 lines of stdlib Python, 7 ingredients as constructor args, 5 guardrails as instance state, the agent is the platform, the customer is the configuration." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-2-first-agent.py` — the canonical stdlib ReAct agent.
- **Reference implementation**: `course/practice/level-5-agents/lesson-9-6-production-agents.py` — the full 200-line shipping agent with all 5 guardrails.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/02-the-fde-loop.md` — the loop driver as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/` — the orchestrator composes 3 shipping agents.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the shipping agent as a system design pattern.

## The 3 questions this lecture preps you for

1. **"Walk me through your minimum viable agent."** Answer: 200 lines of stdlib Python. 7 ingredients as constructor args (model, tools, memory, cost ceiling, system prompt, parser, loop driver). 5 guardrails as instance state (loop detector, audit log, idempotency cache, schema validator, cost ceiling). The `run(goal)` method is the loop driver.
2. **"What is the 'agent is the platform, customer is the configuration' pattern?"** Answer: the FDE writes the agent class once. The customer is the configuration: tool registry, system prompt, model, cost ceiling. Change the configuration, not the loop. The same agent class serves PacificFreight (CS drafter) and Acme Analytics (data analyst) by changing 4-5 args.
3. **"What are the 5 production add-ons?"** Answer: (1) structured errors (typed `_ok/_err` envelopes), (2) idempotency (sha256(args) cache for write tools), (3) audit log (every step recorded: turn, event, tool, args, result, cost, tokens), (4) circuit breaker (trip after N consecutive failures, reset after T seconds), (5) cost ceiling (3 levels: per-run, per-tenant, per-process). All 5 are not optional.

## Read next

`L6-3-tool-implementation-and-validation.md` — the 3rd lecture. The tool registry is the action space; the schema validator is the contract; the idempotency cache is the safety net. The implementation details that turn a 200-line prototype into a production agent.