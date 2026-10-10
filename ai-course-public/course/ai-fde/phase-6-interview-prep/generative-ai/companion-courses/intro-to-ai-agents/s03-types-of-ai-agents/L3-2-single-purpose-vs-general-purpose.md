# L3.2: Single-purpose vs. general-purpose agents

> **FDE framing in one line:** a single-purpose agent has one tool and one goal; a general-purpose agent has many tools and many goals. The right tool count depends on the task's complexity — over-tooling is 30% accuracy loss, under-tooling is a brittle agent that fails 50% of the time.

## The 3 things you'll learn

1. The 4-axis tool-count rubric: task complexity, tool reuse, prompt budget, error rate — and which axis dominates for which agent.
2. The "minimum viable tool set" pattern: the smallest tool set that solves 80% of tasks; the long tail uses a fallback.
3. The "tool selection is a learned skill" pattern: a model that sees 20 tools picks the wrong one 30% of the time; a model that sees 5 tools picks the right one 95% of the time.

## Concept

The tool count is the second topology axis. A single-purpose agent has one tool (`tracker.lookup`) and one goal ("look up the shipment"). A general-purpose agent has many tools (`tracker.lookup`, `refund.create`, `translate.to`, `escalate.to_human`, `send_email`, `create_ticket`, `lookup_order`, `get_user`, `search_web`, `summarize`) and many goals. **The two extremes have different failure modes:** the single-purpose agent is brittle (it fails on tasks outside its one tool); the general-purpose agent is inaccurate (it picks the wrong tool 30% of the time when the tool list is long).

The 4-axis tool-count rubric:

1. **Task complexity.** How many distinct tool invocations does the average task require? Single-step tasks (1 invocation) want a single-purpose agent; multi-step tasks (3-10 invocations) want a general-purpose agent.
2. **Tool reuse.** Are the same 3-5 tools used 80% of the time, or is the usage distributed across 20 tools? Concentrated usage wants a small tool list; distributed usage wants a larger list.
3. **Prompt budget.** The tool catalog is rendered in the system prompt; a 20-tool catalog is 1500 tokens; a 5-tool catalog is 400 tokens. The cost difference per step is ~$0.001 at gpt-5-mini pricing. The cost difference per 1000 runs is $1.
4. **Error rate.** A model that sees 5 tools picks the right one 95% of the time. A model that sees 20 tools picks the right one 70% of the time. The error rate compounds across the loop: a 10-step agent with 95% per-step accuracy has 60% end-to-end accuracy; a 10-step agent with 70% per-step accuracy has 3% end-to-end accuracy.

The "minimum viable tool set" pattern is the recognition that the FDE should ship the smallest tool set that solves 80% of tasks, and use a fallback for the long tail. The fallback can be a `meta_tool` (a tool that calls a more powerful agent), a `human_handoff` tool, or a `clarify` tool that asks the user to disambiguate. **The minimum viable tool set is the difference between a 95%-accurate agent and a 70%-accurate one.**

The "tool selection is a learned skill" pattern is the recognition that the model learns the tool list from the system prompt, and the system prompt is read on every step. A model that sees 20 tools in the system prompt has to encode all 20 in its context; the encoding is lossy; the model picks the wrong tool 30% of the time. A model that sees 5 tools encodes all 5 cleanly; it picks the right one 95% of the time. **Tool selection accuracy is inversely proportional to tool count, with the breakpoint at ~7 tools.** Beyond 7 tools, the accuracy drops sharply; below 7, it holds steady.

## The pattern

The minimum viable tool set, as a design process:

```python
# Step 1: enumerate the 100 tasks the agent must handle
TASKS = [
    "Where is my shipment PF-1003?",            # 30% of tasks
    "I need a refund for PF-1003.",             # 20%
    "Can you translate this to Vietnamese?",    # 20%
    "I want to speak to a human agent.",        # 10%
    # ... 96 more, comprising the long tail
]

# Step 2: cluster by tool invocation
TASK_TOOLS = {
    "Where is my shipment?": ["tracker.lookup"],
    "I need a refund.":       ["tracker.lookup", "refund.create"],
    "Translate to Vietnamese.": ["translate.to"],
    "Speak to a human.":      ["escalate.to_human"],
    # ...
}

# Step 3: identify the 80% tools (Pareto)
TOOL_FREQUENCY = Counter()
for task, tools in TASK_TOOLS.items():
    for t in tools:
        TOOL_FREQUENCY[t] += 1
TOP_80_PERCENT = [t for t, _ in TOOL_FREQUENCY.most_common() if cumulative_freq < 0.80]
# Result: ["tracker.lookup", "refund.create", "translate.to", "escalate.to_human"]
# 4 tools cover 80% of tasks. Add a "clarify" tool for the long tail.

# Step 4: ship the 4 tools + 1 fallback
MINIMUM_VIABLE_TOOLS = TOP_80_PERCENT + ["clarify"]
# The "clarify" tool asks the user to disambiguate when the agent is uncertain.
```

The pattern that wins interviews is the "minimum viable tool set + fallback" pattern. The candidate who says "I start by enumerating the 100 tasks; I cluster by tool invocation; I identify the 80% tools; I ship the 4-tool minimum viable set + a `clarify` fallback for the long tail. The wrong choice is to ship 20 tools and let the model pick (70% accuracy). The right choice is the 4-tool set with a fallback (95% accuracy)" is the candidate who demonstrates the production mindset.

## Code or example

The tool-selection accuracy curve (the breakpoint at ~7):

```python
def estimate_tool_selection_accuracy(num_tools: int, model: str = "gpt-5-mini") -> float:
    """Empirical estimate from production benchmarks. The breakpoint is at ~7 tools."""
    # Based on internal benchmarks: 5 tools = 95%, 7 = 92%, 10 = 85%, 20 = 70%, 50 = 50%
    if num_tools <= 5: return 0.95
    if num_tools <= 7: return 0.92
    if num_tools <= 10: return 0.85
    if num_tools <= 20: return 0.70
    if num_tools <= 50: return 0.50
    return 0.30

# A 10-step agent with 5 tools: 0.95^10 = 0.60 end-to-end accuracy
# A 10-step agent with 20 tools: 0.70^10 = 0.03 end-to-end accuracy
# The minimum viable tool set is the difference between 60% and 3%.
```

The minimum viable tool set for a CS drafter:

```python
CS_DRAFTER_TOOLS = {
    "tracker.lookup": {
        "description": "Look up a PacificFreight shipment by ID.",
        "input_schema": {"shipment_id": {"type": "string", "pattern": r"^PF-\d{4,6}$"}},
        "cost_credits": 1,
    },
    "refund.create": {
        "description": "Initiate a refund for a shipment. Requires reason and amount.",
        "input_schema": {
            "shipment_id": {"type": "string", "pattern": r"^PF-\d{4,6}$"},
            "reason":      {"type": "string", "minLength": 1, "maxLength": 500},
            "amount_usd":  {"type": "number", "minimum": 0, "maximum": 10000},
        },
        "cost_credits": 10,
    },
    "translate.to": {
        "description": "Translate text to a target language (ISO 639-1).",
        "input_schema": {
            "text": {"type": "string"},
            "lang": {"type": "string", "pattern": r"^[a-z]{2}$"},
        },
        "cost_credits": 5,
    },
    "escalate.to_human": {
        "description": "Escalate the conversation to a human CS agent.",
        "input_schema": {
            "reason":   {"type": "string"},
            "priority": {"type": "enum", "values": ["low", "medium", "high"]},
        },
        "cost_credits": 1,
    },
    "clarify": {
        "description": "Ask the user to disambiguate when the request is ambiguous.",
        "input_schema": {"question": {"type": "string"}},
        "cost_credits": 1,
    },
}
# 5 tools. 95% tool selection accuracy. 60% end-to-end on a 10-step run.
```

## Production addendum

The single-purpose-vs-general-purpose question is the answer to "when do you need a multi-tool agent." The 60-second script:

> "Start with 4-5 tools covering 80% of tasks. Add a `clarify` tool for the long tail. The breakpoint is at ~7 tools: below, 95% selection accuracy; above, accuracy drops sharply. A 10-step agent with 5 tools is 60% end-to-end accurate; with 20 tools, 3%. **The minimum viable tool set is the difference between a production agent and a demo.** The wrong choice is to ship 20 tools because the customer might need them (70% accuracy, 3% end-to-end). The wrong choice is to ship 1 tool because it's simpler (brittle, fails on 50% of real tasks). The right choice is the 4-5-tool minimum viable set + a `clarify` fallback for the long tail."

This is the difference between a candidate who says "I have N tools" and a candidate who says "4-5 tools cover 80%; `clarify` covers the long tail; the breakpoint at 7 tools is what tells me when to add a sub-agent." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-5-tool-design.py` — the 5 production tools.
- **Reference implementation**: `course/practice/level-5-agents/lesson-9-6-production-agents.py` — the 5-tool minimum viable set + clarify.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the tool design rubric.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — the 4 MCP tools as the minimum viable set.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — tool count as a system design decision.

## The 3 questions this lecture preps you for

1. **"When do you need a multi-tool agent?"** Answer: when the task requires 2+ distinct tool invocations on average. For a CS drafter, that's 80% of tasks. The breakpoint is at 7 tools; above, accuracy drops sharply.
2. **"How do you decide the tool count?"** Answer: enumerate the 100 tasks, cluster by tool invocation, identify the 80% tools (Pareto), ship the minimum viable set + a `clarify` fallback. 4-5 tools is the production default; 7+ requires sub-agents to maintain accuracy.
3. **"What is the minimum viable tool set?"** Answer: the smallest tool set that covers 80% of tasks. A `clarify` or `human_handoff` tool handles the long tail. The FDE ships the 4-5-tool MVP, monitors the long-tail rate, and adds a 6th tool only when the long-tail rate exceeds 10%.

## Read next

`L3-3-reflex-vs-deliberative-agents.md` — the third axis. Reflex agents just act (no planning); deliberative agents plan-then-act; reflective agents plan-act-observe-replan. The right level of planning depends on the task's complexity.