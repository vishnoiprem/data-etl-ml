# L3.6: Tool-using agents — the action space as the contract

> **FDE framing in one line:** every agent uses tools, but the depth varies. The tool-using agent's job is to map intents to actions; the contract is the tool catalog; the failure mode is the wrong tool or the wrong args.

## The 3 things you'll learn

1. The 3 levels of tool complexity: read-only (look up), write-with-idempotency (create with a key), write-with-side-effects (send email, move money).
2. The "tool description is a prompt" pattern: the description is what the model reads to decide which tool to call; a bad description makes the model call the wrong tool.
3. The "tool selection as a learned skill" pattern: 5 tools = 95% accuracy, 7 = 92%, 10 = 85%, 20 = 70%. The minimum viable tool set is the FDE's primary design decision.

## Concept

The tool-using agent is the canonical agent shape: it has a tool catalog (1-10 tools), a system prompt that describes the tools, and a loop driver that dispatches the model-selected tool call. Every agent in Sections 4-9 is a tool-using agent; the variations are in topology (Sections 3.1-3.5) and planning (L3.7). This lecture focuses on the tool layer: how to design the tools, how to describe them, and how to validate the calls.

The 3 levels of tool complexity, in order of risk:

1. **Read-only (look up).** The tool returns information; no side effects. Examples: `tracker.lookup`, `web_search`, `get_user`, `database_query`. The risk is low: a wrong call returns wrong data, but no state changes. The cost is low: 1 credit per call. The agent can call these freely.
2. **Write-with-idempotency (create with a key).** The tool creates a new resource with a stable key; a retry produces the same resource or none. Examples: `refund.create(idempotency_key=...)`, `create_ticket(external_id=...)`, `upsert_customer(customer_id=...)`. The risk is medium: a wrong key creates a wrong resource, but the idempotency key prevents duplicates. The cost is medium: 5-10 credits per call. The agent can call these with the idempotency key in the args.
3. **Write-with-side-effects (send, move, delete).** The tool has irreversible side effects. Examples: `send_email(to=..., body=...)`, `move_money(from=..., to=..., amount=...)`, `delete_user(user_id=...)`. The risk is high: a wrong call sends a wrong email, moves money to the wrong account, deletes the wrong user. The cost is high: 10-100 credits per call, plus the operational cost of the side effect. The agent must get human approval before calling these.

The "tool description is a prompt" pattern is the recognition that the tool description is the most important string in the tool definition. The model reads the description to decide which tool to call. A bad description makes the model call the wrong tool 30% of the time; a good description makes the model call the right tool 95% of the time. **The description is a prompt for the model, not a comment for the developer.** It should answer: what the tool does, when to call it, what it returns, and what errors to expect.

The "tool selection as a learned skill" pattern (revisited from L3.2) is the recognition that the model learns the tool list from the system prompt. The accuracy curve is empirically: 5 tools = 95%, 7 = 92%, 10 = 85%, 20 = 70%, 50 = 50%. **The FDE's primary design decision for a tool-using agent is the minimum viable tool set.** Too few tools = the agent is brittle; too many = the agent picks the wrong tool. The sweet spot is 4-7 tools covering 80% of tasks.

## The pattern

The 3-level tool taxonomy, as a decorator:

```python
from enum import Enum

class ToolRisk(Enum):
    READ_ONLY = "read_only"
    WRITE_IDEMPOTENT = "write_idempotent"
    WRITE_SIDE_EFFECT = "write_side_effect"

def tool(name: str, description: str, input_schema: dict, risk: ToolRisk,
         cost_credits: int, requires_approval_above_usd: float = 0.0,
         idempotent: bool = False):
    """Decorator that registers a tool with its risk profile."""
    def decorator(func):
        TOOLS[name] = {
            "description": description,
            "input_schema": input_schema,
            "risk": risk,
            "cost_credits": cost_credits,
            "requires_approval_above_usd": requires_approval_above_usd,
            "idempotent": idempotent,
            "function": func,
        }
        return func
    return decorator

# Read-only tool
@tool("tracker.lookup", "Look up a PacificFreight shipment by ID.",
      {"shipment_id": {"type": "string", "pattern": r"^PF-\d{4,6}$"}},
      risk=ToolRisk.READ_ONLY, cost_credits=1)
def tracker_lookup(args): return db.lookup(args["shipment_id"])

# Write-with-idempotency
@tool("refund.create", "Initiate a refund for a shipment.",
      {"shipment_id": {"type": "string"}, "amount_usd": {"type": "number"}, "idempotency_key": {"type": "string"}},
      risk=ToolRisk.WRITE_IDEMPOTENT, cost_credits=10, idempotent=True)
def refund_create(args): return refund_api.create(**args)

# Write-with-side-effects (requires human approval above $100)
@tool("send_email", "Send an email to a customer.",
      {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
      risk=ToolRisk.WRITE_SIDE_EFFECT, cost_credits=5, requires_approval_above_usd=100.0)
def send_email(args): return email_api.send(**args)
```

The dispatcher that respects the risk profile:

```python
def call_tool(name: str, args: dict, state: dict) -> dict:
    """Dispatch with risk-aware checks."""
    tool_spec = TOOLS[name]

    # Risk check 1: requires human approval?
    if tool_spec["risk"] == ToolRisk.WRITE_SIDE_EFFECT:
        if args.get("amount_usd", 0) > tool_spec["requires_approval_above_usd"]:
            return {"_ok": False, "_err": "approval_required", "amount_usd": args.get("amount_usd")}

    # Risk check 2: idempotency key on write tools
    if tool_spec["idempotent"] and "idempotency_key" not in args:
        return {"_ok": False, "_err": "missing_idempotency_key"}

    # Risk check 3: cost ceiling on this call
    state["cost_tracker"].record_tool_call(tool_spec["cost_credits"])
    if state["cost_tracker"].run_cost > state["cost_tracker"].max_run_usd:
        return {"_ok": False, "_err": "cost_ceiling_breached"}

    # Dispatch
    return tool_spec["function"](args)
```

The pattern that wins interviews is the "3-level tool taxonomy + risk-aware dispatcher" pattern. The candidate who says "I classify tools into read-only, write-with-idempotency, and write-with-side-effects; the dispatcher enforces approval thresholds, idempotency keys, and cost ceilings; the agent can call read-only freely but must request human approval for side-effect tools above $100" is the candidate who demonstrates the risk-mindset.

## Code or example

The tool description quality rubric:

```python
# Bad description (the model can't decide when to call this):
"refund.create: Creates a refund."

# Good description (the model knows when to call it and what to pass):
"refund.create: Initiate a refund for a PacificFreight shipment. "
"Use ONLY when the customer explicitly requests a refund AND has provided "
"a shipment_id matching ^PF-\\d{4,6}$ AND a reason. The amount_usd must be "
"a positive number not exceeding the shipment value. Returns a refund_id "
"and estimated processing time. DO NOT call for status-only questions — "
"use tracker.lookup instead."

# Why the good description works:
# - "Use ONLY when..." (negative constraints)
# - "AND has provided..." (prerequisites)
# - "The amount_usd must be..." (arg validation hint)
# - "Returns..." (output shape)
# - "DO NOT call for..." (boundary with other tools)
```

The tool selection accuracy curve (5 → 95%, 7 → 92%, 10 → 85%, 20 → 70%):

```python
def tool_selection_accuracy(num_tools: int) -> float:
    """Empirical accuracy from production benchmarks."""
    if num_tools <= 5: return 0.95
    if num_tools <= 7: return 0.92
    if num_tools <= 10: return 0.85
    if num_tools <= 20: return 0.70
    return 0.50

# For a 10-step agent:
# 5 tools:  0.95^10 = 0.60 end-to-end
# 7 tools:  0.92^10 = 0.43
# 10 tools: 0.85^10 = 0.20
# 20 tools: 0.70^10 = 0.03
# The 5-tool minimum viable set is 20× more accurate than the 20-tool general-purpose set.
```

## Production addendum

The tool-using question is the answer to "how does an agent use tools." The 60-second script:

> "Three risk levels. Read-only: look up, no side effects, the agent calls freely. Write-with-idempotency: create with a stable key, the agent can retry safely. Write-with-side-effects: send, move, delete, the agent must request human approval above a threshold (e.g., $100). **The dispatcher enforces the risk profile: approval, idempotency, cost ceiling.** The tool description is a prompt for the model, not a comment for the developer; a good description makes the model call the right tool 95% of the time, a bad description makes it call the wrong tool 30% of the time. The minimum viable tool set is 4-7 tools covering 80% of tasks. Beyond 7, accuracy drops sharply. The wrong choice is to ship 20 tools because the customer might need them. The right choice is 4-7 tools with risk-aware dispatch."

This is the difference between a candidate who says "the agent has tools" and a candidate who says "3 risk levels, risk-aware dispatcher, the description is a prompt, the minimum viable set is 4-7 tools." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-5-tool-design.py` — the 5 production tools.
- **Reference implementation**: `course/practice/level-5-agents/lesson-9-6-production-agents.py` — the risk-aware dispatcher.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the tool design rubric.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — the 4 MCP tools with policy file.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — tool design as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How does an agent use tools?"** Answer: the model reads the tool catalog in the system prompt, decides which tool to call based on the description, emits a structured action; the agent framework dispatches via the tool registry with schema validation, cost tracking, and idempotency. The tool description is a prompt; the registry is the contract.
2. **"What is the difference between a read-only tool and a write tool?"** Answer: read-only returns information with no side effects (low risk, the agent calls freely); write-with-idempotency creates a resource with a stable key (medium risk, retry is safe); write-with-side-effects has irreversible effects (high risk, requires human approval above a threshold). The dispatcher enforces the risk profile.
3. **"How do you write a good tool description?"** Answer: as a prompt for the model. Include: what the tool does, when to call it (positive constraints), when NOT to call it (negative constraints), the args it requires (with format hints), the output shape, and the boundary with other tools. A good description makes the model call the right tool 95% of the time; a bad description makes it call the wrong tool 30% of the time.

## Read next

`L3-7-planning-agents.md` — the seventh lecture. The plan-and-execute pattern, the HTN pattern, the replan-on-contradiction pattern. The right planning depth depends on the task's dynamism and reversibility.