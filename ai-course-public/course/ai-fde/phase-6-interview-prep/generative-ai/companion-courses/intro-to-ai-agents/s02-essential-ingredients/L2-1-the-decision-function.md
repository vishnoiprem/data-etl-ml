# L2.1: The LLM as decision function

> **FDE framing in one line:** the LLM is the only ingredient in the agent that is hard to replace; everything else is plumbing. Pick the model with the same rigor you pick a database — wrong choice is a 12-month rewrite, not a 5-minute swap.

## The 3 things you'll learn

1. The three properties that make the LLM the agent's decision function: generality, language-following, and tool-following.
2. The 4-axis model selection rubric: capability, latency, cost, and context window — and which axis dominates for which agent task.
3. The model-routing pattern: why a single agent should not use a single model for every step.

## Concept

The decision function is the part of the agent that takes the current state and returns the next action. In every AI textbook since the 1960s, the decision function has been a hand-written rules engine, a reinforcement-learned policy, or a symbolic planner. The LLM is the first decision function that is **general-purpose** — the same model can read a tool description in natural language, pick the right tool, parse the observation, and decide what to do next, across arbitrary domains.

The three properties that make the LLM the first general-purpose decision function:

1. **Generality.** The same model that drafts an email can also file a tax return, given the right tool list. Pre-LLM decision functions were domain-specific: a chess-playing policy could not play Go; a tax-filing rules engine could not draft an email. The LLM is the first decision function whose capability generalizes across the entire text-and-code action space.
2. **Language-following.** The LLM follows instructions expressed in natural language. The tool description, the system prompt, the user request — all are natural language. The pre-LLM decision function required a formal specification; the LLM accepts a paragraph. This is what makes the tool registry a `dict[str, str]` instead of a formal grammar.
3. **Tool-following.** The LLM emits structured tool calls in a protocol (function-calling, ReAct) that the agent framework can parse and dispatch. Pre-LLM decision functions emitted actions in their own internal format; the agent framework had to translate. The tool-use protocol is the contract that made the LLM the canonical decision function.

The LLM is the only ingredient in the agent that is **hard to replace**. The loop driver is 10 lines of Python. The tool registry is a dict. The memory layer is a vector DB call. The system prompt is a string. The cost ceiling is 5 lines. None of these require a domain expert to maintain. The LLM, by contrast, is a 100GB+ artifact that costs millions of dollars to train, requires a domain expert to fine-tune, and degrades in unpredictable ways when the input distribution shifts. **Pick the model with the same rigor you pick a database** — wrong choice is a 12-month rewrite, not a 5-minute swap.

## The pattern

The model selection rubric has 4 axes. The FDE candidate who can name all 4 and explain which axis dominates for which task is the candidate who passes the model-selection interview question.

| Axis | What it measures | Dominates when |
|---|---|---|
| **Capability** | Quality of output on the agent's task (faithfulness, code correctness, reasoning) | The task is hard, the customer cares about quality, and the cost is acceptable |
| **Latency** | p50/p95 time-to-first-token and time-per-step | The agent is user-facing, the user is waiting, and a 2s step is acceptable |
| **Cost** | USD per 1K input/output tokens; USD per agent run | The agent runs at scale (1000s of runs/day) and the budget is fixed |
| **Context window** | Maximum input tokens; effective long-context quality | The agent reads long documents, multi-turn histories, or large tool outputs |

The default 2026 model landscape:

- **gpt-5** ($2.50/$10 per 1M tokens) — the highest-capability model. Use for the hardest steps (planning, synthesis, evaluation) and for the customer-facing "final answer" generation.
- **gpt-5-mini** ($0.15/$0.60 per 1M tokens) — the workhorse. Use for 80% of agent steps: tool selection, observation parsing, retry decisions. 90% of gpt-5's capability at 6% of the cost.
- **claude-sonnet-4.5** ($3/$15 per 1M tokens) — the long-context and code-generation leader. Use when the agent reads 100K+ tokens of context or generates 5K+ lines of code.
- **claude-haiku-4.5** ($0.80/$4 per 1M tokens) — the speed leader. Use for the latency-critical steps in a user-facing agent.
- **gemini-2.5-pro** ($1.25/$0.30 per 1M tokens) — the cost-quality crossover for multimodal agents. Use when the agent reads images, audio, or video.
- **llama-4-70b** (self-hosted, ~$0.10/$0.10 per 1M tokens at scale) — the deployment-flexibility leader. Use when the customer requires on-prem or VPC isolation and the team has MLOps capacity.

The model-routing pattern is the recognition that a single agent should not use a single model for every step. A 10-step agent run that uses gpt-5 for every step costs $0.50. The same run that uses gpt-5 for the 2 hard steps (planning, final answer) and gpt-5-mini for the 8 routine steps (tool selection, observation parsing) costs $0.08. The model router is a 20-line function that picks the model per step. The savings are 5-10× with no quality loss on the routine steps.

## Code or example

The model selection rubric, as a 4-axis scoring function:

```python
from dataclasses import dataclass

@dataclass
class ModelScore:
    capability: float    # 0.0 - 1.0
    latency_p95_ms: int  # lower is better
    cost_per_1k: float   # USD, lower is better
    context_window: int  # tokens, higher is better

MODELS = {
    "gpt-5":          ModelScore(0.95, 1800, 0.012, 200_000),
    "gpt-5-mini":     ModelScore(0.88,  900, 0.0008, 200_000),
    "claude-sonnet-4.5":  ModelScore(0.94, 2200, 0.018, 200_000),
    "claude-haiku-4.5":   ModelScore(0.82,  600, 0.004, 200_000),
    "gemini-2.5-pro":ModelScore(0.91, 1500, 0.001, 1_000_000),
    "llama-4-70b":   ModelScore(0.85, 1200, 0.0001, 128_000),
}

def pick_model(task: str) -> str:
    """Pick the model whose dominant axis matches the task's requirement."""
    if task == "planning":           return "gpt-5"            # capability dominates
    if task == "tool_selection":     return "gpt-5-mini"       # cost dominates
    if task == "long_doc_synthesis": return "claude-sonnet-4.5"  # context dominates
    if task == "user_facing_chat":   return "claude-haiku-4.5"   # latency dominates
    if task == "multimodal":         return "gemini-2.5-pro"   # capability dominates
    if task == "on_prem":            return "llama-4-70b"      # deployment dominates
    return "gpt-5-mini"  # default: cost-quality crossover
```

The model router, as a per-step cost optimization:

```python
def run_step(state, step_kind: str) -> str:
    """Run one agent step. Use the cheap model for tool selection, the
    expensive model for planning and final-answer generation."""
    model = pick_model(step_kind)
    return call_llm(model=model, messages=state.messages)

# A 10-step agent run: 2 hard steps (gpt-5) + 8 routine steps (gpt-5-mini)
# Cost: 2 * $0.05 + 8 * $0.001 = $0.108
# vs all-gpt-5: 10 * $0.05 = $0.500
# Savings: 4.6×
```

## Production addendum

The model selection rubric is the answer to the centerpiece-round "how do you pick the model" question. The 60-second script:

> "Four axes: capability, latency, cost, context window. Capability dominates when the task is hard and the customer cares about quality. Latency dominates when the agent is user-facing. Cost dominates at scale. Context dominates when the agent reads long documents. The 2026 default is gpt-5-mini for 80% of steps and gpt-5 for the 2 hard steps (planning + final answer). The model router is a 20-line function. The savings are 5-10× with no quality loss on the routine steps. The wrong choice is to use the expensive model for every step — 4-5× cost waste. The other wrong choice is to use the cheap model for the hard steps — 10-20% quality loss that compounds across the 10-step run."

This 60-second pitch is the difference between a candidate who says "I used GPT-4" and a candidate who says "I used gpt-5-mini for 8 of 10 steps and gpt-5 for the 2 hard steps, and here is the cost-quality curve." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-3-prompt-engineering/lesson-4-2-model-selection.py` — the 4-axis rubric as a callable function.
- **Reference implementation**: `course/practice/level-5-agents/lesson-9-6-production-agents.py::pick_model()` — the per-step router.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/01-the-fde-pattern.md` — the model as a swappable component.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/03-distilled-slm/` — when the SLM replaces the API model.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the model selection rubric in the centerpiece round.

## The 3 questions this lecture preps you for

1. **"How do you pick the model for an agent?"** Answer: 4-axis rubric (capability, latency, cost, context). The dominant axis depends on the task: capability for hard steps, cost for routine steps, latency for user-facing steps, context for long-doc synthesis. The 2026 default is gpt-5-mini for 80% of steps and gpt-5 for the 2 hard steps.
2. **"Why not use the most capable model for every step?"** Answer: 4-5× cost waste. The capability gap between gpt-5 and gpt-5-mini on routine steps (tool selection, observation parsing) is < 5%; the cost gap is 15×. The model router captures the savings.
3. **"When would you fine-tune or distill instead of using an API model?"** Answer: when the cost ceiling is the binding constraint and the task is well-bounded (the agent's prompt distribution is stable). The SLM is 10-50× cheaper at 90-95% of the API model's quality. The decision tree: API model first, SLM when cost dominates, custom model only when neither suffices.

## Read next

`L2-2-the-tool-protocol.md` — the second ingredient. The tool-use protocol is the contract that makes the LLM's tool-following reliable. Without it, every model call is a regex-parse of markdown.
