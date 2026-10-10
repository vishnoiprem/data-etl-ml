# L4.2: Few-shot examples and chain-of-thought

> **FDE framing in one line:** few-shot examples are the most reliable way to teach output format and behavior; chain-of-thought is the lever for multi-step reasoning. Together, they turn a generic LLM into a domain-specific agent without changing the model.

## The 3 things you'll learn

1. The 3 few-shot patterns: zero-shot (no examples), one-shot (1 example), few-shot (2-5 examples) — and when each is appropriate.
2. The chain-of-thought (CoT) pattern: explicit reasoning before the action, used to teach multi-step planning.
3. The "examples are part of the contract" pattern: the FDE's test set is the source of truth for what good behavior looks like.

## Concept

Few-shot examples are the most reliable way to teach the model what good behavior looks like. The model is a pattern-matcher; a worked example is a more powerful teaching signal than a verbal description. The empirical observation: a model that sees 2-3 worked examples produces the desired output 95% of the time; a model that sees only a verbal description produces the desired output 70% of the time. **The few-shot examples are the most reliable way to teach output format and behavior; the verbal description is a complement, not a substitute.**

The 3 few-shot patterns:

1. **Zero-shot (no examples).** The system prompt contains only the role, tools, output format, and guardrails. The model is expected to infer the behavior from the description. Use when: the task is simple, the output format is straightforward, and the model has been trained on similar tasks.
2. **One-shot (1 example).** The system prompt contains one worked example. The model is shown the format and behavior once, and is expected to generalize. Use when: the task is non-trivial, the output format has subtleties, or the model has not been trained on similar tasks.
3. **Few-shot (2-5 examples).** The system prompt contains 2-5 worked examples covering the main cases. The model is shown the format and behavior in multiple contexts, and is expected to handle edge cases. Use when: the task is complex, the output format has multiple valid shapes, or the model needs to learn the boundary between cases.

The chain-of-thought (CoT) pattern is the lever for multi-step reasoning. The model emits a `Thought:` line before each `Action:` line; the thought explains the reasoning, the action commits to the next step. The ReAct pattern is the canonical CoT for agents. **CoT reduces loops (the model can read its own history and notice it's going in circles) and surfaces errors (the model can read an error observation and adjust its strategy).**

The "examples are part of the contract" pattern is the recognition that the FDE's test set is the source of truth for what good behavior looks like. The test set is a list of (user request, expected action, expected final answer) tuples; the worked examples in the system prompt are a subset of the test set. **The test set is the spec; the examples are the documentation; the model is the implementation.**

## The pattern

The 3 few-shot patterns, as a function:

```python
def render_examples(examples: list[dict], mode: str = "few_shot") -> str:
    """Render the examples section of the system prompt."""
    if mode == "zero_shot":
        return ""  # No examples
    if mode == "one_shot":
        examples = examples[:1]
    elif mode == "few_shot":
        examples = examples[:5]  # Cap at 5 to keep the prompt bounded

    blocks = []
    for ex in examples:
        blocks.append(
            f"User: {ex['user']}\n"
            f"Thought: {ex['thought']}\n"
            f"Action: {ex['action']}\n"
            f"Observation: {ex['observation']}\n"
            f"Final Answer: {ex['final_answer']}"
        )
    return "\n\n".join(blocks)
```

The chain-of-thought scaffolding:

```python
COT_FORMAT = """Always respond in this format:
Thought: <your reasoning about what to do next, citing the previous observation if relevant>
Action: tool_name(arg1=value1, arg2=value2)
Observation: <the tool's output, provided by the system>
... (repeat Thought/Action/Observation as needed)
Final Answer: <your final response to the customer, in plain English>

The Thought line should:
- Restate the goal in your own words
- Reference the previous observation if any
- Explain why you chose this action (not another action)
- Anticipate the next observation"""
```

The example selection rubric:

```python
def select_examples(test_set: list[dict], k: int = 3) -> list[dict]:
    """Select k examples that cover the main cases."""
    # Cluster test_set by intent
    clusters = cluster_by_intent(test_set)
    # Pick one example from each of the k largest clusters
    selected = []
    for cluster in sorted(clusters, key=len, reverse=True)[:k]:
        selected.append(pick_representative(cluster))
    return selected
```

The pattern that wins interviews is the "few-shot + CoT + examples-as-contract" pattern. The candidate who says "I use 2-5 worked examples that cover the main cases; the examples are part of the contract; chain-of-thought scaffolds multi-step reasoning; the model reads the examples + the CoT format and produces the desired output 95% of the time" is the candidate who demonstrates the prompt-engineering mindset.

## Code or example

The few-shot example selector (the canonical CS-drafter test set):

```python
CS_DRAFTER_TEST_SET = [
    # Case 1: Status lookup (30% of emails)
    {
        "user": "Where is my shipment PF-1003?",
        "thought": "Customer asks about PF-1003 status. Look it up.",
        "action": "tracker.lookup(shipment_id='PF-1003')",
        "observation": "{'status': 'in_transit', 'eta': '2026-10-12'}",
        "final_answer": "PF-1003 is in transit, expected to arrive October 12.",
    },
    # Case 2: Refund request (20% of emails)
    {
        "user": "I need a refund for PF-1003, $50.",
        "thought": "Customer requests a refund. I have shipment_id, reason (implied), amount. Call refund.create with idempotency key.",
        "action": "refund.create(shipment_id='PF-1003', reason='customer request', amount_usd=50, idempotency_key='PF-1003-50-2026-10-10')",
        "observation": "{'refund_id': 'R-9876', 'status': 'processing'}",
        "final_answer": "Refund of $50 initiated. Refund ID R-9876, processed in 5 business days.",
    },
    # Case 3: Translation request (20% of emails)
    {
        "user": "Can you translate 'Your shipment has arrived' to Vietnamese?",
        "thought": "Customer asks for translation. Call translate.to with the text and lang='vi'.",
        "action": "translate.to(text='Your shipment has arrived', lang='vi')",
        "observation": "{'translation': 'Đơn hàng của bạn đã đến nơi'}",
        "final_answer": "In Vietnamese: 'Đơn hàng của bạn đã đến nơi'",
    },
    # Case 4: Escalation (10% of emails)
    {
        "user": "This is the third time I'm asking about my package! I want to speak to a manager.",
        "thought": "Customer is frustrated and requests a manager. Call escalate.to_human with priority='high'.",
        "action": "escalate.to_human(reason='customer requested manager after 3 follow-ups', priority='high')",
        "observation": "{'ticket_id': 'T-5432', 'estimated_response_min': 15}",
        "final_answer": "I've escalated your case to a senior agent. They'll reach out within 15 minutes. Apologies for the frustration.",
    },
    # Case 5: Out-of-scope (10% of emails)
    {
        "user": "Do you have any open positions for a logistics coordinator?",
        "thought": "Customer asks about careers — out of scope. Emit Final Answer with the out-of-scope guardrail.",
        "action": "<no action>",
        "observation": "<n/a>",
        "final_answer": "I can only help with shipment, refund, translation, and escalation requests. For careers, please visit pacificfreight.com/careers.",
    },
]

# Select 3 examples (one per major case) for the system prompt
CS_DRAFTER_EXAMPLES = select_examples(CS_DRAFTER_TEST_SET, k=3)
# Result: [case_1, case_2, case_3] (the 3 largest clusters)
```

The CoT before/after comparison:

```python
# WITHOUT chain-of-thought (the model just emits an action):
# Thought: (none)
# Action: refund.create(shipment_id='PF-1003', amount_usd=50)
# Result: 60% accuracy on the test set; the model often picks the wrong tool or wrong args.

# WITH chain-of-thought (the model explains before acting):
# Thought: The customer explicitly requests a refund. I have the shipment_id (PF-1003)
#          and the amount ($50). The reason is implied ("customer request"). I should
#          call refund.create with an idempotency key to prevent double-refunds on retry.
# Action: refund.create(shipment_id='PF-1003', reason='customer request', amount_usd=50, idempotency_key='PF-1003-50-2026-10-10')
# Result: 95% accuracy on the test set; the model reasons through edge cases and includes the idempotency key.
```

## Production addendum

The few-shot + CoT question is the answer to "when do you use few-shot examples vs zero-shot." The 60-second script:

> "Zero-shot for simple tasks where the output format is obvious. One-shot when the format has subtleties. Few-shot (2-5 examples) for complex tasks where the model needs to learn the boundary between cases. **Chain-of-thought scaffolds multi-step reasoning: the model emits a Thought line before each Action, citing the previous observation, explaining the choice, anticipating the next.** CoT reduces loops and surfaces errors. The few-shot examples are part of the contract — the test set is the source of truth, the examples are a subset, the model is the implementation. The wrong choice is zero-shot for a complex task (60% accuracy). The wrong choice is 20 examples (prompt bloat, diminishing returns). The right choice is 2-5 examples covering the main cases, with CoT scaffolding, version-controlled, with contract tests."

This is the difference between a candidate who says "I prompted the model" and a candidate who says "2-5 examples covering the main cases, CoT scaffolding, examples are part of the contract, contract tests in CI." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-3-prompt-engineering/lesson-3-4-few-shot.py` — the few-shot selector and CoT scaffolding.
- **Reference implementation**: `course/practice/level-5-agents/lesson-8-2-first-agent.py` — the production ReAct agent with 2-3 examples and CoT.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/03-the-system-prompt.md` — the system prompt + examples as a single artifact.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/` — per-agent examples as the orchestrator's expression.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — prompt engineering as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you use few-shot examples vs zero-shot?"** Answer: zero-shot for simple tasks where the output format is obvious; one-shot when the format has subtleties; few-shot (2-5 examples) for complex tasks where the model needs to learn the boundary between cases. The diminishing returns kick in at ~5 examples; beyond that, the prompt bloats and accuracy plateaus.
2. **"What is chain-of-thought and why does it help?"** Answer: CoT is the model emitting a Thought line before each Action, citing the previous observation, explaining the choice, and anticipating the next. CoT reduces loops (the model reads its own history) and surfaces errors (the model reads an error observation and adjusts). CoT is the lever for multi-step reasoning; it is the difference between 60% and 95% accuracy on complex tasks.
3. **"How do you select the few-shot examples?"** Answer: cluster the test set by intent, pick one example from each of the k largest clusters. The selected examples cover the main cases; the unselected examples become the contract tests. The examples are part of the contract — the test set is the source of truth, the examples are a subset, the model is the implementation.

## Read next

`L4-3-fine-tuning-and-distillation.md` — the third lever. Fine-tuning and distillation are the levers of last resort; the FDE escalates to them only when prompt engineering has been exhausted and the cost ceiling is binding. The SLM at 10× cost reduction is the canonical example.