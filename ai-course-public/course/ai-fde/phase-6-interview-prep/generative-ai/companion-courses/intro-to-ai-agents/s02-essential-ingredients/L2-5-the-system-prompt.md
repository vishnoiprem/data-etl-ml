# L2.5: The system prompt as the model's contract

> **FDE framing in one line:** the system prompt is the contract between the agent framework and the model. A bad system prompt is the difference between an agent that works and an agent that loops; the system prompt is the single highest-leverage string in the codebase.

## In 60 seconds

> "Five sections. Role: one sentence naming the agent's purpose. Tools: the full catalog rendered as a markdown list with args and return shape. Output format: the exact text format the model must emit (Thought/Action/Final Answer for ReAct, JSON in tool_calls for function-calling). Guardrails: the behavioral boundaries — what tools are forbidden, what errors should stop the run, what data must never appear in the output. Examples: one or two worked examples teaching the output format. **The system prompt is rendered at startup from the tool registry, frozen for the duration of the run, and version-controlled in the codebase with a changelog.** The wrong choice is to hand-edit the system prompt at runtime (drift between the prompt and the registry). The wrong choice is to skip the examples (model produces malformed output 10% of the time). The right choice is the five sections, rendered at startup, version-controlled, with contract tests."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The five sections every agent system prompt must contain: role, tools, output format, guardrails, examples.
2. The "render at startup, never edit at runtime" pattern: the system prompt is built once from the tool registry and frozen.
3. The "prompt as the agent's API" pattern: the system prompt is the contract; the contract is what makes the agent testable.

## Concept

The system prompt is the message the model receives before any user message, tool call, or observation. It is the only message that is always present; it is the only message the agent framework controls fully; it is the model's first and most reliable instruction. **The system prompt is the contract between the agent framework and the model.** A model that reads the system prompt and decides to ignore it has broken the contract; an agent framework that sends a system prompt the model cannot follow has written a bad contract.

The five sections every agent system prompt must contain:

1. **Role.** One sentence that names the agent's purpose: "You are a customer service agent for PacificFreight. Your goal is to draft helpful replies to customer emails about shipment status, refunds, and translations." The role is what the model anchors on when the goal is ambiguous; without it, the model defaults to "helpful assistant" and may produce off-task behavior (e.g., drafting a refund reply when the customer asked about translation).
3. **Tools.** The full tool catalog rendered as a markdown list: `tracker.lookup(shipment_id: str) -> {status, eta, location}`. Each tool is one line with name, args, and return shape. **The system prompt lists every tool the model can call; the tool registry validates every tool the model does call.** The model reads the list and decides which to invoke; the registry reads the call and decides whether to dispatch.
4. **Output format.** The exact text format the model must emit. For ReAct: `Thought: ...\nAction: tool_name(args)\nObservation: ...\n... (repeat)\nFinal Answer: ...`. For function-calling: the model emits JSON in the `tool_calls` field, not in the text content. **The output format is the parser's contract with the model.** A model that emits the wrong format is a malformed input — the parser returns a 403 and the loop continues.
6. **Guardrails.** The behavioral boundaries: "never call `refund.create` without a confirmed `shipment_id`; never call `escalate.to_human` for status-only questions; if a tool returns an error, retry once then emit `Final Answer: I cannot help with this.`" The guardrails are what prevent the model from doing something the agent framework would reject (e.g., calling a forbidden tool, retrying forever, emitting PII).
8. **Examples.** One or two worked examples of the model receiving a user request, calling a tool, observing the result, and emitting the final answer. The examples are the most reliable way to teach the output format; a model that sees a worked example produces the format more reliably than a model that sees only a schema.

The "render at startup, never edit at runtime" pattern is the recognition that the system prompt is built once from the tool registry and frozen. The tool registry is the source of truth; the system prompt is a derived view. If a tool is added to the registry, the system prompt is regenerated at startup; if the system prompt is hand-edited at runtime, it drifts from the registry. **The system prompt is the agent's API; the registry is the implementation; the API is rendered from the implementation at startup.**

The "prompt as the agent's API" pattern is the recognition that the system prompt is the contract the agent framework exposes to the model. The contract is testable: the FDE writes a test set of (system prompt + user request + expected output) and asserts the model produces the expected output for each. The contract is versionable: the system prompt is a string in version control, with a changelog, with rollback. **The system prompt is the single highest-leverage string in the codebase; it deserves version control, test coverage, and a changelog.**

## The pattern

The five sections as a render function:

```python
def render_system_prompt(tools: dict, role: str, guardrails: list[str], examples: list[dict]) -> str:
    """Render the system prompt from the tool registry. Frozen at startup."""
    tool_lines = []
    for name, spec in tools.items():
        args = ", ".join(f"{k}: {v['type']}" for k, v in spec["input_schema"].items())
        ret = spec.get("output_description", "see function")
        tool_lines.append(f"- {name}({args}) -> {ret}")
    tool_block = "\n".join(tool_lines)

    guardrail_lines = "\n".join(f"- {g}" for g in guardrails)

    example_blocks = []
    for ex in examples:
        example_blocks.append(
            f"User: {ex['user']}\n"
            f"Thought: {ex['thought']}\n"
            f"Action: {ex['action']}\n"
            f"Observation: {ex['observation']}\n"
            f"Final Answer: {ex['final_answer']}"
        )
    example_text = "\n\n".join(example_blocks)

    return f"""You are {role}.

## Tools
You have access to the following tools:
{tool_block}

## Output format
Always respond in this format:
Thought: <your reasoning>
Action: tool_name(args)
Observation: <the tool's output>
... (repeat Thought/Action/Observation as needed)
Final Answer: <your final response to the user>

## Guardrails
{guardrail_lines}

## Examples
{example_text}
"""
```

The pattern that wins interviews is the "five sections, rendered at startup, version-controlled" pattern. The candidate who says "the system prompt has five sections — role, tools, output format, guardrails, examples — and it is rendered at startup from the tool registry, frozen for the duration of the run, and version-controlled in the codebase with a changelog" is the candidate who demonstrates the contract-as-code mindset.

## Code or example

The full system prompt for a CS-drafter agent:

```python
CS_DRAFTER_ROLE = "a customer service agent for PacificFreight, drafting helpful responses to customer emails"

CS_DRAFTER_GUARDRAILS = [
    "Never call refund.create without a confirmed shipment_id matching ^PF-\\d{4,6}$.",
    "Never call escalate.to_human for status-only questions — use tracker.lookup instead.",
    "If a tool returns an error, retry at most once with corrected args. If still failing, emit Final Answer: I cannot help with this.",
    "Never reveal the customer's email address, payment info, or tracking number in Final Answer.",
    "Always include the shipment_id from the customer's email in your draft reply for traceability.",
]

CS_DRAFTER_EXAMPLES = [
    {
        "user": "Hi, where is my shipment PF-1003? It was supposed to arrive yesterday.",
        "thought": "The customer is asking about shipment PF-1003. I should look it up first.",
        "action": "tracker.lookup(shipment_id='PF-1003')",
        "observation": "{'status': 'in_transit', 'eta': '2026-10-12', 'location': 'Ho Chi Minh City hub'}",
        "final_answer": "Hi! Your shipment PF-1003 is currently in transit and is expected to arrive on October 12. It's currently at the Ho Chi Minh City hub. Apologies for the delay!",
    },
]

CS_DRAFTER_SYSTEM_PROMPT = render_system_prompt(
    tools=TOOLS,
    role=CS_DRAFTER_ROLE,
    guardrails=CS_DRAFTER_GUARDRAILS,
    examples=CS_DRAFTER_EXAMPLES,
)
```

The contract test:

```python
def test_system_prompt_renders_all_tools():
    """The system prompt must list every tool in the registry."""
    prompt = render_system_prompt(TOOLS, CS_DRAFTER_ROLE, CS_DRAFTER_GUARDRAILS, CS_DRAFTER_EXAMPLES)
    for name in TOOLS:
        assert name in prompt, f"tool {name} missing from system prompt"

def test_system_prompt_includes_guardrails():
    """The system prompt must include every guardrail."""
    prompt = render_system_prompt(TOOLS, CS_DRAFTER_ROLE, CS_DRAFTER_GUARDRAILS, CS_DRAFTER_EXAMPLES)
    for g in CS_DRAFTER_GUARDRAILS:
        assert g in prompt, f"guardrail missing: {g}"

def test_system_prompt_includes_output_format():
    """The system prompt must specify the output format."""
    prompt = render_system_prompt(TOOLS, CS_DRAFTER_ROLE, CS_DRAFTER_GUARDRAILS, CS_DRAFTER_EXAMPLES)
    assert "Thought:" in prompt
    assert "Action:" in prompt
    assert "Final Answer:" in prompt
```

## Production addendum

The system prompt is the answer to the "how do you write a good agent system prompt" interview question. The 60-second script:

> "Five sections. Role: one sentence naming the agent's purpose. Tools: the full catalog rendered as a markdown list with args and return shape. Output format: the exact text format the model must emit (Thought/Action/Final Answer for ReAct, JSON in tool_calls for function-calling). Guardrails: the behavioral boundaries — what tools are forbidden, what errors should stop the run, what data must never appear in the output. Examples: one or two worked examples teaching the output format. **The system prompt is rendered at startup from the tool registry, frozen for the duration of the run, and version-controlled in the codebase with a changelog.** The wrong choice is to hand-edit the system prompt at runtime (drift between the prompt and the registry). The wrong choice is to skip the examples (model produces malformed output 10% of the time). The right choice is the five sections, rendered at startup, version-controlled, with contract tests."

This 60-second pitch is the difference between a candidate who says "I wrote a prompt" and a candidate who says "the system prompt has five sections, is rendered from the tool registry, is version-controlled, and has contract tests." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-2-prompt-engineering/lesson-3-5-system-prompts.py` — the 5-section system prompt template.
- **Reference implementation**: `course/practice/level-5-agents/lesson-8-2-first-agent.py::render_system_prompt()` — the runtime rendering.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the system prompt as a first-class artifact.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — per-agent system prompts as the orchestrator's expression.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the system prompt as a system design pattern.

## The 3 questions this lecture preps you for

1. **"What are the five sections every agent system prompt must contain?"** Answer: (1) Role — one sentence naming the agent's purpose. (2) Tools — the full catalog rendered as a markdown list with args and return shape. (3) Output format — the exact text format the model must emit (Thought/Action/Final Answer for ReAct, JSON in tool_calls for function-calling). (4) Guardrails — the behavioral boundaries. (5) Examples — one or two worked examples teaching the output format.
2. **"Why is the system prompt rendered at startup, not edited at runtime?"** Answer: drift prevention. The tool registry is the source of truth; the system prompt is a derived view. If a tool is added, the prompt is regenerated; if the prompt is hand-edited at runtime, it drifts from the registry and the model emits tool calls the registry rejects. **The system prompt is the agent's API; the registry is the implementation; the API is rendered from the implementation at startup.**
3. **"How do you test a system prompt?"** Answer: contract tests. The FDE writes a test set of (system prompt + user request + expected output) and asserts the model produces the expected output for each. The test set covers: every tool is invoked correctly, every guardrail is respected, every example's output format is matched, no PII appears in the final answer. The contract tests run in CI; a prompt change that breaks a test is a breaking change.

## Read next

`L2-6-parsing-structured-output.md` — the sixth ingredient. The parser is the contract between the model output and the tool dispatcher. A good parser turns a malformed output into a structured error; a bad parser crashes the loop.