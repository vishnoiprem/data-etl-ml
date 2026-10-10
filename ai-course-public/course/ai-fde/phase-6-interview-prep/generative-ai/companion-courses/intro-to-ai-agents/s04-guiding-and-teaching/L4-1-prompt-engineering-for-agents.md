# L4.1: Prompt engineering for agents — the system prompt as the contract

> **FDE framing in one line:** the system prompt is the contract between the agent framework and the model. The 5 sections (role, tools, output format, guardrails, examples) are the structure; the FDE's job is to write each section well and version-control the whole.

## In 60 seconds

> "Five sections. Role: one sentence naming the agent's purpose. Tools: the full catalog rendered as a markdown list with args and return shape. Output format: the exact text format the model must emit. Guardrails: the behavioral boundaries — forbidden tools, error handling, PII redaction. Examples: one or two worked examples teaching the output format. **The system prompt is rendered at startup from the tool registry, frozen for the duration of the run, and version-controlled in the codebase with a changelog.** The contract tests run in CI; a prompt change that breaks a test is a breaking change. The wrong choice is to hand-edit the prompt at runtime (drift). The wrong choice is to skip the examples (model produces malformed output 10% of the time). The right choice is the 5 sections, rendered at startup, version-controlled, with contract tests."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The 5 sections of a production system prompt: role, tools, output format, guardrails, examples — and what each section is for.
2. The "render at startup, never edit at runtime" pattern: the prompt is built from the tool registry, frozen, and version-controlled.
3. The contract test pattern: the system prompt is testable via a (prompt, request, expected output) test set.

## Concept

The system prompt is the single highest-leverage string in the agent codebase. A bad system prompt is the difference between an agent that works and an agent that loops, hallucinates, or refuses. The 5 sections of a production system prompt are not arbitrary; they correspond to the 5 things the model must know to do the right thing:

1. **Role.** What kind of agent is this? What is its purpose? The role is what the model anchors on when the goal is ambiguous. Without it, the model defaults to "helpful assistant" and may produce off-task behavior.
2. **Tools.** What can the agent do? The tool catalog rendered as a markdown list. The model reads the catalog and decides which tool to call. The catalog is the agent's action space.
3. **Output format.** What does the model's output look like? The exact text format (ReAct: `Thought/Action/Final Answer`; function-calling: JSON in `tool_calls`). The output format is the parser's contract with the model.
4. **Guardrails.** What must the model not do? The behavioral boundaries: forbidden tools, error handling, PII redaction, escalation triggers. The guardrails are what prevent the model from doing something the agent framework would reject.
5. **Examples.** How does the model use the format on a real task? One or two worked examples that show the model receiving a user request, calling a tool, observing the result, and emitting the final answer. The examples are the most reliable way to teach the output format.

The "render at startup, never edit at runtime" pattern is the recognition that the system prompt is derived from the tool registry at startup and frozen for the duration of the run. If a tool is added to the registry, the system prompt is regenerated; if the system prompt is hand-edited at runtime, it drifts from the registry and the model emits tool calls the registry rejects. **The system prompt is the agent's API; the registry is the implementation; the API is rendered from the implementation at startup.**

The contract test pattern is the recognition that the system prompt is testable. The FDE writes a test set of (system prompt + user request + expected output) and asserts the model produces the expected output for each. The test set covers: every tool is invoked correctly, every guardrail is respected, every example's output format is matched, no PII appears in the final answer. **The system prompt is the contract; the contract tests are the CI gate; a prompt change that breaks a test is a breaking change.**

## The pattern

The 5-section system prompt template:

```python
def render_system_prompt(tools: dict, role: str, output_format: str,
                          guardrails: list[str], examples: list[dict]) -> str:
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

    return f"""You are {role}.

## Tools
You have access to the following tools:
{tool_block}

## Output format
{output_format}

## Guardrails
{guardrail_lines}

## Examples
{chr(10).join(example_blocks)}
"""
```

The contract test:

```python
def test_system_prompt_renders_all_tools():
    prompt = render_system_prompt(TOOLS, ROLE, OUTPUT_FORMAT, GUARDRAILS, EXAMPLES)
    for name in TOOLS:
        assert name in prompt, f"tool {name} missing"

def test_system_prompt_includes_guardrails():
    prompt = render_system_prompt(TOOLS, ROLE, OUTPUT_FORMAT, GUARDRAILS, EXAMPLES)
    for g in GUARDRAILS:
        assert g in prompt, f"guardrail missing: {g}"

def test_system_prompt_includes_output_format():
    prompt = render_system_prompt(TOOLS, ROLE, OUTPUT_FORMAT, GUARDRAILS, EXAMPLES)
    assert "Thought:" in prompt and "Action:" in prompt and "Final Answer:" in prompt

def test_model_produces_expected_output():
    """The integration test: model + system prompt → expected output."""
    for ex in EXAMPLES:
        output = llm([
            {"role": "system", "content": render_system_prompt(TOOLS, ROLE, OUTPUT_FORMAT, GUARDRAILS, EXAMPLES)},
            {"role": "user", "content": ex["user"]},
        ])
        # Assert: the model emitted the expected action and final answer
        assert ex["action"] in output, f"model did not call expected action: {ex['action']}"
```

The pattern that wins interviews is the "5 sections + render at startup + contract tests" pattern. The candidate who says "the system prompt has 5 sections, is rendered at startup from the tool registry, is version-controlled in the codebase with a changelog, and has contract tests in CI" is the candidate who demonstrates the contract-as-code mindset.

## Code or example

The full CS-drafter system prompt:

```python
CS_DRAFTER_ROLE = (
    "a customer service agent for PacificFreight, a cross-border logistics company. "
    "Your goal is to draft helpful, accurate, and concise replies to customer emails "
    "about shipment status, refunds, translations, and escalations."
)

CS_DRAFTER_OUTPUT_FORMAT = """Always respond in this format:
Thought: <your reasoning about what to do next>
Action: tool_name(arg1=value1, arg2=value2)
Observation: <the tool's output, provided by the system>
... (repeat Thought/Action/Observation as needed)
Final Answer: <your final response to the customer, in plain English>"""

CS_DRAFTER_GUARDRAILS = [
    "Never call refund.create without a confirmed shipment_id matching ^PF-\\d{4,6}$.",
    "Never call escalate.to_human for status-only questions — use tracker.lookup first.",
    "If a tool returns an error, retry at most once with corrected args. If still failing, emit Final Answer: I cannot help with this.",
    "Never reveal the customer's email address, payment info, or full tracking history in Final Answer.",
    "Always include the shipment_id from the customer's email in your draft reply for traceability.",
    "If the customer asks about a topic outside your scope (sales, partnerships, careers), emit Final Answer: I can only help with shipment, refund, translation, and escalation requests.",
]

CS_DRAFTER_EXAMPLES = [
    {
        "user": "Hi, where is my shipment PF-1003? It was supposed to arrive yesterday.",
        "thought": "The customer is asking about the status of shipment PF-1003. I should look it up first.",
        "action": "tracker.lookup(shipment_id='PF-1003')",
        "observation": "{'status': 'in_transit', 'eta': '2026-10-12', 'location': 'Ho Chi Minh City hub'}",
        "final_answer": "Hi! Your shipment PF-1003 is currently in transit and is expected to arrive on October 12. It's currently at the Ho Chi Minh City hub. Apologies for the delay!",
    },
    {
        "user": "I need a refund for PF-1003, the package was damaged. $50 should cover it.",
        "thought": "The customer is requesting a refund. I need a confirmed shipment_id, a reason, and an amount. I have all three. I should call refund.create.",
        "action": "refund.create(shipment_id='PF-1003', reason='package damaged', amount_usd=50, idempotency_key='PF-1003-refund-50-2026-10-10')",
        "observation": "{'refund_id': 'R-9876', 'status': 'processing', 'eta_days': 5}",
        "final_answer": "I've initiated a $50 refund for shipment PF-1003. Your refund ID is R-9876 and it should be processed within 5 business days. Apologies for the damaged package!",
    },
]

CS_DRAFTER_SYSTEM_PROMPT = render_system_prompt(
    tools=TOOLS,
    role=CS_DRAFTER_ROLE,
    output_format=CS_DRAFTER_OUTPUT_FORMAT,
    guardrails=CS_DRAFTER_GUARDRAILS,
    examples=CS_DRAFTER_EXAMPLES,
)
```

The version control + changelog:

```python
# system_prompt.py
SYSTEM_PROMPT_VERSION = "1.4.2"
SYSTEM_PROMPT_CHANGELOG = """
v1.4.2 (2026-10-08): Added guardrail #6 (out-of-scope handling). Updated example #2 to include idempotency_key.
v1.4.1 (2026-09-22): Tightened guardrail #1 to require regex match on shipment_id.
v1.4.0 (2026-09-15): Added translate.to tool. Updated example #1 to demonstrate lookup + draft flow.
v1.3.0 (2026-08-30): Initial production version.
"""
```

## Production addendum

The system prompt question is the answer to "how do you write a good agent system prompt." The 60-second script:

> "Five sections. Role: one sentence naming the agent's purpose. Tools: the full catalog rendered as a markdown list with args and return shape. Output format: the exact text format the model must emit. Guardrails: the behavioral boundaries — forbidden tools, error handling, PII redaction. Examples: one or two worked examples teaching the output format. **The system prompt is rendered at startup from the tool registry, frozen for the duration of the run, and version-controlled in the codebase with a changelog.** The contract tests run in CI; a prompt change that breaks a test is a breaking change. The wrong choice is to hand-edit the prompt at runtime (drift). The wrong choice is to skip the examples (model produces malformed output 10% of the time). The right choice is the 5 sections, rendered at startup, version-controlled, with contract tests."

This is the difference between a candidate who says "I wrote a prompt" and a candidate who says "the system prompt has 5 sections, is rendered from the tool registry, is version-controlled, and has contract tests." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-2-prompt-engineering/lesson-3-5-system-prompts.py` — the 5-section template.
- **Reference implementation**: `course/practice/level-5-agents/lesson-8-2-first-agent.py::render_system_prompt()` — the runtime rendering.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the system prompt as a first-class artifact.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — per-agent system prompts.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the system prompt as a system design pattern.

## The 3 questions this lecture preps you for

1. **"What are the 5 sections of a production system prompt?"** Answer: (1) Role — one sentence naming the agent's purpose; (2) Tools — the full catalog rendered as a markdown list; (3) Output format — the exact text format the model must emit; (4) Guardrails — the behavioral boundaries; (5) Examples — one or two worked examples teaching the format.
2. **"Why is the system prompt rendered at startup, not edited at runtime?"** Answer: drift prevention. The tool registry is the source of truth; the system prompt is a derived view. If a tool is added, the prompt is regenerated; if the prompt is hand-edited at runtime, it drifts from the registry and the model emits tool calls the registry rejects. The system prompt is the agent's API; the registry is the implementation.
3. **"How do you test a system prompt?"** Answer: contract tests. The FDE writes a test set of (system prompt + user request + expected output) and asserts the model produces the expected output for each. The test set covers: every tool is invoked correctly, every guardrail is respected, every example's output format is matched, no PII appears in the final answer. The contract tests run in CI; a prompt change that breaks a test is a breaking change.

## Read next

`L4-2-few-shot-examples-and-cot.md` — the second lever. Few-shot examples are the most reliable way to teach output format and behavior; chain-of-thought is the lever for multi-step reasoning. Together, they turn a generic LLM into a domain-specific agent.
