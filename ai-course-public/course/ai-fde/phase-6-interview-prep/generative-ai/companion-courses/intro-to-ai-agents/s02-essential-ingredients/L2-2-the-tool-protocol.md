# L2.2: The tool-use protocol

> **FDE framing in one line:** the tool-use protocol is the contract between the model's output and the agent's actions. Without it, every model call is a regex-parse of markdown; with it, the model emits a structured action the agent dispatches deterministically.

## In 60 seconds

> "The schema validator catches malformed tool calls before they reach the function. A model that emits a string where the schema expects a number gets a structured 403 with the violation list. The agent framework appends the violation to the messages list as an observation. The model reads the violation, corrects the args, and retries. The turn counter increments; the cost ceiling catches the loop. **The schema validator turns a Python TypeError into a recoverable model observation.** Without it, every malformed call is a crash; with it, every malformed call is a retry."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The two tool-use protocols in production: function-calling (OpenAI, June 2023) and ReAct (text-based, model-agnostic).
2. The four parts of a tool definition: name, description, input schema, output schema.
3. The schema validator as a first-class FDE pattern: a malformed tool call is a structured 403, not a Python TypeError.

## Concept

Before the tool-use protocols landed in 2023-2024, the model had to emit tool calls as JSON inside a markdown code block, and the application had to parse them with regex. The regex would catch 95% of calls and 5% would silently fail — the model would emit `Action: search_web("Pacific freight")` and the parser would miss the trailing space, the call would silently not happen, the model would re-emit the same call, and the agent would loop. The protocols fixed this: OpenAI's function-calling (June 2023) and Anthropic's tool-use (2024) gave the model a structured way to emit tool calls. The contract is the protocol; the contract is what made the agent framework ecosystem (LangChain, LangGraph, LlamaIndex, AutoGen, CrewAI) possible.

The two protocols in production:

1. **Function-calling** (OpenAI, Anthropic, Google). The model emits a typed JSON object with `name` and `arguments`. The arguments are validated against the JSON Schema the developer provided. The protocol is a separate field in the API response (`tool_calls` array) — the model does not emit tool calls in the text content. The advantage: the application code receives a parsed, validated object. The disadvantage: the model cannot reason about the tool call in natural language before committing to it (the "thought" line is missing).
2. **ReAct** (text-based, model-agnostic). The model emits `Thought: ...\nAction: tool_name(args)\nObservation: ...` in plain text. The application parses with regex. The advantage: the `Thought` line gives the model a place to reason about its previous observation before committing to the next action. The disadvantage: parsing is fragile; the regex must handle whitespace, escaping, and malformed output.

The protocol choice is a tradeoff between reliability and expressiveness. Function-calling wins on reliability (the application receives a parsed object, not a string to parse). ReAct wins on expressiveness (the model can think out loud, which reduces loops on multi-step problems). **The 2026 production default is function-calling for 80% of agents and ReAct for the 20% where the model needs to reason between tool calls (e.g., complex research agents, multi-step coding agents).**

The four parts of a tool definition are invariant across protocols:

1. **Name.** A unique identifier (`tracker.lookup`, `refund.create`, `translate.to`). The name is the contract between the model's intent and the agent's dispatch. The name must be self-describing: a model reading the name in a tool catalog should know what the tool does without reading the description.
2. **Description.** A natural-language sentence the model reads to decide whether to call the tool. The description is the most important part of the tool definition; a model that does not understand the description will not call the tool. The description should answer: what the tool does, when to call it, and what it returns. The description is **not** a comment for the developer; it is a prompt for the model.
3. **Input schema.** A JSON Schema-like spec of the arguments (`{"shipment_id": "PF-XXXX (regex)"}`). The schema is the contract between the model's args and the function's parameters. The model is constrained to emit only the fields in the schema. A model that tries to add an extra field is rejected by the schema validator.
4. **Output schema.** A JSON Schema-like spec of the return value. The output schema is the contract between the tool's result and the model's next observation. The model reads the output schema to know what to expect. **Most production tools skip the output schema and document the return shape in the description instead** — the model is robust to natural-language output descriptions and the JSON Schema overhead is not worth the marginal reliability gain.

The schema validator is the first-class FDE pattern that turns a malformed tool call from a Python TypeError into a structured 403. The pattern:

```python
# Bad: the model emits an int, the function expects a str, the agent crashes.
result = tools["tracker.lookup"](shipment_id=12345)  # TypeError: expected str

# Good: the schema validator catches the type mismatch, returns a structured error.
def call_tool(name, args):
    schema = TOOL_SCHEMAS[name]
    violations = validate_args(args, schema)
    if violations:
        return {"_ok": False, "_err": "schema_violation", "violations": violations}
    return {"_ok": True, "result": tools[name](**args)}
```

The structured 403 is fed back to the model as an observation. The model reads the violation, corrects its args, and retries. The agent framework's loop driver increments the turn counter and continues. **The schema validator is what makes the tool-use protocol a contract and not a prayer.**

## The pattern

The tool registry is the data structure that holds the four parts:

```python
TOOLS = {
    "tracker.lookup": {
        "description": "Look up a PacificFreight shipment by ID. Returns status, ETA, last_known_location.",
        "input_schema": {
            "shipment_id": {"type": "string", "pattern": r"^PF-\d{4,6}$"},
        },
        "cost_credits": 1,  # for the rate limiter
        "function": lambda args: db_lookup(args["shipment_id"]),
    },
    "refund.create": {
        "description": "Initiate a refund for a shipment. Requires reason and amount in USD.",
        "input_schema": {
            "shipment_id": {"type": "string", "pattern": r"^PF-\d{4,6}$"},
            "reason":      {"type": "string", "minLength": 1, "maxLength": 500},
            "amount_usd":  {"type": "number", "minimum": 0, "maximum": 10000},
        },
        "cost_credits": 10,
        "function": lambda args: refund_api.create(**args),
    },
}
```

The registry is the single source of truth. The system prompt renders the descriptions; the schema validator reads the schemas; the rate limiter reads the cost_credits; the function dispatcher reads the function. **The registry is the agent's API; the model is the consumer of the API.**

The pattern that wins interviews is the "schema validator as structured 403" pattern. The candidate who says "if the model emits a malformed tool call, the agent gets a structured 403 with the violation list, the model reads the violation, corrects the args, and retries — turn counter increments, cost ceiling catches the loop" is the candidate who demonstrates the production mindset.

## Code or example

The schema validator, stdlib-only:

```python
import re
from typing import Any

def validate_args(args: dict, schema: dict) -> list[str]:
    """Return a list of schema violations. Empty list = valid."""
    violations = []
    for field, spec in schema.items():
        if field not in args:
            violations.append(f"missing field: {field}")
            continue
        value = args[field]
        expected_type = spec.get("type")
        if expected_type == "string" and not isinstance(value, str):
            violations.append(f"{field}: expected string, got {type(value).__name__}")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            violations.append(f"{field}: expected number, got {type(value).__name__}")
        elif expected_type == "string" and "pattern" in spec:
            if not re.match(spec["pattern"], value):
                violations.append(f"{field}: does not match pattern {spec['pattern']}")
        elif expected_type == "string" and "minLength" in spec:
            if len(value) < spec["minLength"]:
                violations.append(f"{field}: shorter than minLength {spec['minLength']}")
        elif expected_type == "number" and "minimum" in spec:
            if value < spec["minimum"]:
                violations.append(f"{field}: below minimum {spec['minimum']}")
    return violations

# Example
schema = {"shipment_id": {"type": "string", "pattern": r"^PF-\d{4,6}$"}}
print(validate_args({"shipment_id": "PF-1003"}, schema))  # []
print(validate_args({"shipment_id": 12345}, schema))       # ['shipment_id: expected string, got int']
print(validate_args({"shipment_id": "INVALID"}, schema))   # ['shipment_id: does not match pattern ^PF-\\d{4,6}$']
```

The structured tool call envelope:

```python
def call_tool(name: str, args: dict) -> dict:
    """Dispatch a tool call with schema validation. Returns _ok/_err envelope."""
    if name not in TOOLS:
        return {"_ok": False, "_err": "unknown_tool", "tool": name}
    schema = TOOLS[name]["input_schema"]
    violations = validate_args(args, schema)
    if violations:
        return {"_ok": False, "_err": "schema_violation", "violations": violations}
    try:
        result = TOOLS[name]["function"](args)
        return {"_ok": True, "result": result}
    except Exception as e:
        return {"_ok": False, "_err": "tool_exception", "message": str(e)}
```

The model reads the envelope as an observation. The framework appends the observation to the messages list. The model decides what to do next. **The envelope is the contract between the tool layer and the agent loop; every tool call returns one; every observation is one.**

## Production addendum

The schema validator is the answer to the "what happens when the model emits a malformed tool call" interview question. The 60-second script:

> "The schema validator catches malformed tool calls before they reach the function. A model that emits a string where the schema expects a number gets a structured 403 with the violation list. The agent framework appends the violation to the messages list as an observation. The model reads the violation, corrects the args, and retries. The turn counter increments; the cost ceiling catches the loop. **The schema validator turns a Python TypeError into a recoverable model observation.** Without it, every malformed call is a crash; with it, every malformed call is a retry."

This 60-second pitch is the difference between a candidate who says "we handle errors" and a candidate who says "the schema validator returns a structured 403, the model reads the violation and retries, the cost ceiling catches the loop." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-5-tool-design.py` — the 5 production tools with `validate_args()`.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/09-react-agent-tools.py` — the production-grade tool registry with 5+ tools and structured error recovery.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — structured errors as the FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — the MCP server as a tool registry with a policy file.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the tool registry as a first-class system design pattern.

## The 3 questions this lecture preps you for

1. **"What is the tool-use protocol?"** Answer: the contract between the model's output and the agent's actions. Two protocols: function-calling (typed JSON, separate field) and ReAct (text-based, model-agnostic). The 2026 default is function-calling for 80% of agents; ReAct for the 20% where the model needs to reason between tool calls.
2. **"What are the four parts of a tool definition?"** Answer: name (self-describing), description (natural-language prompt for the model), input schema (JSON Schema-like constraint), output schema (often skipped, documented in description instead). The description is the most important part.
3. **"What happens when the model emits a malformed tool call?"** Answer: the schema validator catches it before the function runs and returns a structured 403 with the violation list. The agent framework appends the violation as an observation. The model reads the violation, corrects the args, and retries. The cost ceiling catches the loop.

## Read next

`L2-3-the-memory-layer.md` — the third ingredient. The memory layer is what makes the agent multi-step instead of single-step. Without it, the agent forgets the first observation by the time it makes the 10th call.
