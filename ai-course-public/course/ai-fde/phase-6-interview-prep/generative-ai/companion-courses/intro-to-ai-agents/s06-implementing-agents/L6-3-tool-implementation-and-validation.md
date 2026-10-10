# L6.3: Tool implementation and validation

> **FDE framing in one line:** the tool registry is the action space, the schema validator is the contract, the idempotency cache is the safety net. A bad tool implementation is the difference between a 95%-accurate agent and a 70%-accurate one.

## The 3 things you'll learn

1. The 4 parts of a production tool: name, description (the prompt), input schema, output schema. The description is the most important.
2. The 3 levels of tool validation: schema (shape), semantic (intent), policy (who can call). The validator catches the first; the dispatcher enforces the second and third.
3. The idempotency pattern: write tools key on sha256(args); a retry produces the same side effect or none. The model can safely retry on transient errors.

## Concept

The tool implementation is the second layer of the shipping agent (after the system prompt). The tool registry is the action space; the schema validator is the contract between the model's intent and the function's parameters; the idempotency cache is the safety net for retries. **A bad tool implementation is the difference between a 95%-accurate agent and a 70%-accurate one** — the model picks the wrong tool, calls it with the wrong args, or produces the wrong side effect.

The 4 parts of a production tool:

1. **Name.** A unique, self-describing identifier (`tracker.lookup`, `refund.create`). The name is the contract between the model's intent and the agent's dispatch. The model reads the name in the tool catalog and decides whether to call it.
2. **Description.** A natural-language sentence (or two) the model reads to decide when to call the tool. **The description is the most important part of the tool definition.** The description should answer: what the tool does, when to call it, when NOT to call it, what it returns, and what errors to expect. A good description makes the model call the right tool 95% of the time; a bad description makes the model call the wrong tool 30% of the time.
3. **Input schema.** A JSON-Schema-like spec of the arguments. The model is constrained to emit only the fields in the schema. A model that tries to add an extra field is rejected by the schema validator. The schema is the contract between the model's args and the function's parameters.
4. **Output schema.** A JSON-Schema-like spec of the return value. Most production tools skip the output schema and document the return shape in the description instead — the model is robust to natural-language output descriptions.

The 3 levels of tool validation:

1. **Schema validation (shape).** Does the args dict match the input schema? Missing fields, wrong types, regex mismatches. The validator catches these before the function runs. The agent framework gets a structured 403; the model reads the violation and retries.
2. **Semantic validation (intent).** Is the args dict semantically valid? E.g., a refund amount > the shipment value, a date in the past, a quantity > the inventory. The validator catches these after the schema check. The model reads the semantic violation and corrects.
3. **Policy validation (who can call).** Is the user authorized to call this tool? E.g., a `cs_mei` user cannot call `refund.create` for amounts > $100. The policy file (YAML) is the source of truth; the dispatcher enforces it. The agent framework gets a structured 403; the model reads the policy violation and escalates.

The idempotency pattern is the safety net for write tools. Every write tool (`refund.create`, `send_email`, `create_ticket`) keys on a stable hash of the canonical args: `arg_hash = sha256(json.dumps(args, sort_keys=True))`. The dispatcher caches the result for each `arg_hash`; a retry produces the cached result, not a new side effect. **The model can safely retry on transient errors; the customer cannot get double-refunded, double-emailed, or double-ticketed.**

## The pattern

The production tool, as a class:

```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class Tool:
    name: str
    description: str           # The most important part
    input_schema: dict         # JSON-Schema-like
    output_description: str    # Natural-language output description
    cost_credits: int
    function: Callable
    risk: str = "read_only"    # read_only | write_idempotent | write_side_effect
    requires_approval_above_usd: float = 0.0
    idempotent: bool = False

# Example: the production tracker.lookup
TOOL_TRACKER_LOOKUP = Tool(
    name="tracker.lookup",
    description=(
        "Look up a PacificFreight shipment by ID. "
        "Use ONLY when the customer asks about the status, location, or ETA of a specific shipment. "
        "The shipment_id must match the pattern ^PF-\\d{4,6}$ "
        "(e.g., 'PF-1003'). "
        "DO NOT call this for refund requests (use refund.create), "
        "translation requests (use translate.to), or escalations (use escalate.to_human). "
        "Returns: {shipment_id, status, eta, last_known_location, last_updated_at}. "
        "Errors: 'unknown_shipment' (the ID does not exist)."
    ),
    input_schema={"shipment_id": {"type": "string", "pattern": r"^PF-\d{4,6}$"}},
    output_description="dict with keys: shipment_id, status, eta, last_known_location, last_updated_at",
    cost_credits=1,
    function=tracker_lookup_fn,
    risk="read_only",
)
```

The schema validator (the contract enforcer):

```python
import re

def validate_args(args: dict, schema: dict) -> list[str]:
    """Return a list of schema violations. Empty list = valid."""
    violations = []
    for field, spec in schema.items():
        if field not in args:
            violations.append(f"missing field: {field}")
            continue
        value = args[field]
        expected = spec.get("type")
        if expected == "string" and not isinstance(value, str):
            violations.append(f"{field}: expected string, got {type(value).__name__}")
        elif expected == "number" and not isinstance(value, (int, float)):
            violations.append(f"{field}: expected number, got {type(value).__name__}")
        elif expected == "string" and "pattern" in spec and not re.match(spec["pattern"], value):
            violations.append(f"{field}: does not match pattern {spec['pattern']}")
        elif expected == "number" and "minimum" in spec and value < spec["minimum"]:
            violations.append(f"{field}: below minimum {spec['minimum']}")
        elif expected == "number" and "maximum" in spec and value > spec["maximum"]:
            violations.append(f"{field}: above maximum {spec['maximum']}")
    return violations
```

The idempotency cache (the safety net):

```python
import hashlib, json

class IdempotencyCache:
    """Cache write tool results by sha256(args) to prevent double-writes."""

    def __init__(self):
        self.cache = {}

    def key(self, tool_name: str, args: dict) -> str:
        canonical = json.dumps({"tool": tool_name, "args": args}, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def get(self, tool_name: str, args: dict):
        return self.cache.get(self.key(tool_name, args))

    def put(self, tool_name: str, args: dict, result):
        self.cache[self.key(tool_name, args)] = result
```

The policy file (who can call what):

```yaml
# mcp_policies.yaml
roles:
  cs_mei:
    can_call: [tracker.lookup, translate.to, escalate.to_human]
    max_refund_usd: 100
  cs_senior:
    can_call: [tracker.lookup, refund.create, translate.to, escalate.to_human]
    max_refund_usd: 1000
  ops_sarah:
    can_call: [tracker.lookup]
  it_daniel:
    can_call: [tracker.lookup, refund.create, translate.to, escalate.to_human]
    max_refund_usd: 10000
rate_limits:
  refund.create: { per_user_per_min: 5, per_user_per_day: 50 }
  send_email: { per_user_per_min: 20 }
```

The pattern that wins interviews is the "4 parts + 3 validation levels + idempotency" pattern. The candidate who says "the production tool has 4 parts (name, description, input schema, output description); the description is the most important; the validation has 3 levels (schema, semantic, policy); write tools key on sha256(args) for idempotency; the policy file is the source of truth for who can call what" is the candidate who demonstrates the tool-mindset.

## Code or example

The ToolRegistry with all 3 validation levels:

```python
class ToolRegistry:
    """The production tool registry with 3-level validation + idempotency."""

    def __init__(self, tools: list[Tool], policy: dict, current_user: str):
        self.tools = {t.name: t for t in tools}
        self.policy = policy
        self.current_user = current_user
        self.idempotency = IdempotencyCache()

    def call(self, name: str, args: dict) -> dict:
        tool = self.tools.get(name)
        if not tool:
            return {"_ok": False, "_err": "unknown_tool"}

        # Level 1: Schema validation
        violations = validate_args(args, tool.input_schema)
        if violations:
            return {"_ok": False, "_err": "schema_violation", "violations": violations}

        # Level 2: Semantic validation
        if name == "refund.create":
            if args["amount_usd"] > get_shipment_value(args["shipment_id"]):
                return {"_ok": False, "_err": "amount_exceeds_shipment_value"}

        # Level 3: Policy validation
        user_policy = self.policy["roles"].get(self.current_user, {})
        if name not in user_policy.get("can_call", []):
            return {"_ok": False, "_err": "policy_violation", "user": self.current_user}
        max_refund = user_policy.get("max_refund_usd", 0)
        if name == "refund.create" and args["amount_usd"] > max_refund:
            return {"_ok": False, "_err": "amount_exceeds_user_limit", "limit_usd": max_refund}

        # Idempotency check (write tools only)
        if tool.idempotent:
            cached = self.idempotency.get(name, args)
            if cached is not None:
                return {"_ok": True, "result": cached, "_idempotent": True}

        # Dispatch
        try:
            result = tool.function(args)
            if tool.idempotent:
                self.idempotency.put(name, args, result)
            return {"_ok": True, "result": result}
        except Exception as e:
            return {"_ok": False, "_err": "exception", "message": str(e)}
```

The tool description quality rubric:

```python
# Bad description (the model can't decide when to call this):
"refund.create: Creates a refund."
# Tool selection accuracy: 70%. The model calls it for status questions, for translation requests, etc.

# Good description (the model knows when to call it and what to pass):
"""refund.create: Initiate a refund for a PacificFreight shipment.
Use ONLY when the customer explicitly requests a refund AND has provided:
- A shipment_id matching ^PF-\\d{4,6}$ (e.g., 'PF-1003')
- A reason (non-empty string, max 500 chars)
- An amount_usd (positive number, not exceeding the shipment value)

Returns: {refund_id, status, estimated_processing_days}.
Errors: 'amount_exceeds_shipment_value', 'unknown_shipment', 'policy_violation'.

DO NOT call for:
- Status questions (use tracker.lookup)
- Translation requests (use translate.to)
- General inquiries (use clarify)
"""
# Tool selection accuracy: 95%. The model knows the boundary.
```

## Production addendum

The tool implementation question is the answer to "how do you handle malformed tool calls." The 60-second script:

> "4 parts of a production tool: name, description (the most important), input schema, output description. 3 levels of validation: schema (shape — missing fields, wrong types), semantic (intent — amount > shipment value), policy (who can call — cs_mei cannot call refund.create for > $100). **Idempotency: write tools key on sha256(args); a retry produces the cached result, not a new side effect.** The model can safely retry on transient errors. The wrong choice is to skip the description (70% tool selection accuracy). The wrong choice is to skip the idempotency (double-refund on retry). The right choice is the 4 parts, the 3 levels, the idempotency, the policy file as the source of truth."

This is the difference between a candidate who says "I have tools" and a candidate who says "4 parts (name, description, input schema, output description), 3 validation levels (schema, semantic, policy), idempotency on write tools, policy file as the source of truth." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-5-tool-design.py` — the 5 production tools with all 3 validation levels.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/09-react-agent-tools.py` — the production tool registry with idempotency.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the tool design rubric.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — the MCP server as a tool registry with policy file.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — tool implementation as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How do you handle malformed tool calls?"** Answer: 3 levels of validation. Schema validation catches missing fields and wrong types; semantic validation catches intent violations (amount > value); policy validation catches authorization violations (user cannot call this tool). The validator returns a structured 403 with the violation list; the model reads the violation and corrects.
2. **"What is the most important part of a tool definition?"** Answer: the description. The model reads the description to decide whether to call the tool. A good description (what + when + when not + returns + errors) makes the model call the right tool 95% of the time. A bad description (just the name) makes the model call the wrong tool 30% of the time.
3. **"What is the idempotency pattern for write tools?"** Answer: write tools key on a stable hash of the canonical args (sha256(json.dumps(args, sort_keys=True))). The dispatcher caches the result for each hash; a retry produces the cached result, not a new side effect. The model can safely retry on transient errors. The customer cannot get double-refunded, double-emailed, or double-ticketed.

## Read next

`L6-4-memory-implementation.md` — the 4th lecture. The 3-tier memory: short-term (in the prompt), long-term (in a vector DB), episodic (summarized past sessions). The implementation details that turn the agent from a stateless function into a stateful system.