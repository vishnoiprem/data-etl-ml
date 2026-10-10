# L3.1: Reactive vs. proactive agents

> **FDE framing in one line:** a reactive agent is one-shot (LLM call + maybe one tool); a proactive agent is a loop (model drives iteration within a budget). The reactive agent is the search engine; the proactive agent is the employee. Pick the simplest one that solves the problem.

## The 3 things you'll learn

1. The four operational differences between reactive and proactive agents: initiative, time horizon, state, side effects.
2. The "default to reactive, escalate to proactive" pattern: a reactive agent fails → proactive agent retries with planning.
3. The hybrid topology: a proactive loop that falls back to a reactive one-shot when the model is confident.

## Concept

The reactive-vs-proactive distinction is the simplest topology axis. A reactive agent answers one prompt with one (or zero) tool calls. A proactive agent pursues a goal across many steps with many tool calls, bounded by a budget. **The two topologies compose: most production agents are hybrid — a proactive outer loop that calls a reactive inner agent when the inner task is single-step.**

The four operational differences, recapitulated from L1.2 in the topology frame:

1. **Initiative.** A reactive agent has no initiative — the user drives the one step. A proactive agent has full initiative within the budget — the model drives the iteration. The reactive agent is a function (`answer = LLM(prompt)`); the proactive agent is a loop.
2. **Time horizon.** A reactive agent is bounded by the prompt length and the model's context window. A proactive agent is bounded by the budget (turns, tokens, USD, time). The reactive agent is fast; the proactive agent is slow.
3. **State.** A reactive agent has no state between calls. A proactive agent has state — the messages list, the long-term memory, the episodic memory. The reactive agent is stateless; the proactive agent is stateful.
4. **Side effects.** A reactive agent has none (assuming no retrieval-augmented generation with side-effecting retriever). A proactive agent has side effects — every tool call may write to a database, send an email, or move money. The reactive agent is safe; the proactive agent needs the 5 guardrails.

The "default to reactive, escalate to proactive" pattern is the recognition that **most tasks are single-step and most tasks are not agent tasks**. The FDE candidate who proposes a multi-agent system for a single-tool, single-step task is over-engineering. The FDE candidate who proposes a single LLM call for a 10-tool, 10-step task is under-engineering. **The right topology is the simplest one that solves the problem; escalate when the simpler one fails.**

The hybrid topology is the canonical 2026 production pattern. The outer loop is proactive (the agent has a goal, a budget, and the initiative to iterate). The inner calls are reactive (a single LLM call to summarize, classify, or extract). The proactive loop calls the reactive inner agent as a tool; the reactive agent returns a result; the proactive loop decides what to do next. **The hybrid is the best of both worlds: the model drives the high-level plan, the reactive inner agent executes the low-level steps.**

## The pattern

The reactive agent, in 5 lines:

```python
def reactive_agent(prompt: str, llm) -> str:
    """One-shot LLM call. No loop, no state, no initiative."""
    return llm([{"role": "user", "content": prompt}]).choices[0].message.content
```

The proactive agent, in 30 lines:

```python
def proactive_agent(goal: str, agent: Agent) -> dict:
    """Proactive loop. Model drives iteration within a budget."""
    return agent.run(goal)  # the 7-ingredient shipping agent from L2.7
```

The hybrid agent, in 50 lines:

```python
def hybrid_agent(goal: str, agent: Agent, reactive_fn: callable) -> dict:
    """Proactive outer loop; reactive inner calls as a 'tool'."""
    # Add the reactive inner agent as a tool in the registry
    def call_reactive(args):
        return {"_ok": True, "result": reactive_fn(args["prompt"])}
    agent.tool_registry.tools["react_inner"] = {
        "description": "Call a reactive inner agent for single-step subtasks.",
        "input_schema": {"prompt": {"type": "string"}},
        "cost_credits": 5,
        "function": lambda a: a,  # wrapped in call_reactive
    }
    return agent.run(goal)
```

The pattern that wins interviews is the "default to reactive, escalate to proactive, hybrid as the default production shape" pattern. The candidate who says "I start with a reactive one-shot; if the task is single-step and bounded, it works. If the task is multi-step or the model needs to iterate, I escalate. If both shapes are useful, the hybrid is the default production topology" is the candidate who demonstrates the topology-mindset.

## Code or example

The reactive-vs-proactive decision rubric:

```python
def pick_topology(task: str) -> str:
    """Pick reactive, proactive, or hybrid based on the task."""
    single_step_keywords = ["classify", "extract", "summarize one", "translate", "rewrite"]
    if any(kw in task.lower() for kw in single_step_keywords):
        return "reactive"  # one-shot is enough
    multi_step_keywords = ["research", "investigate", "compare across", "find and", "build a"]
    if any(kw in task.lower() for kw in multi_step_keywords):
        return "proactive"  # needs iteration
    return "hybrid"  # default: hybrid for safety
```

The hybrid agent demo (the canonical CS-drafter shape):

```python
# The outer loop is proactive: 7-ingredient shipping agent
# The inner calls are reactive: each tool result is processed by a reactive one-shot
# The drafter runs ~3-5 tool calls per email; each tool call is a reactive inner agent

def cs_drafter_hybrid(email: str, agent: Agent) -> dict:
    """Hybrid agent: proactive outer loop + reactive inner calls."""
    # The outer loop is the shipping agent (proactive)
    return agent.run(goal=f"Draft a reply to: {email}")

# Inside the loop, each tool call is processed reactively:
# - tracker.lookup -> one DB query (reactive)
# - classify_intent -> one LLM call (reactive)
# - draft_reply -> one LLM call (reactive, with retrieved context)
# The outer loop is proactive (3-5 steps); the inner calls are reactive (1 step each).
```

## Production addendum

The reactive-vs-proactive question is the answer to "when do you need an agent vs a single LLM call." The 60-second script:

> "Reactive = one-shot LLM call. Proactive = loop with budget. Reactive is fast (one step), stateless (no memory), safe (no side effects). Proactive is slow (10 steps), stateful (messages + memory), needs the 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log). **Default to reactive; escalate to proactive when the task is multi-step or the model needs to iterate; hybrid is the default production shape.** The hybrid is a proactive outer loop that calls a reactive inner agent as a tool. Most production CS-drafter agents are hybrid: the outer loop plans + iterates (3-5 steps), each inner step is a reactive one-shot. The wrong choice is to build a multi-agent system for a single-step task (over-engineering, 10× cost). The wrong choice is a single LLM call for a 10-tool multi-step task (the model can't iterate, fails 30% of the time). The right choice is the simplest topology that solves it."

This is the difference between a candidate who says "I built an agent" and a candidate who says "I default to reactive; I escalate to proactive when the task is multi-step; I use hybrid as the production default." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-2-first-agent.py` — the proactive ReAct agent.
- **Reference implementation**: `course/practice/level-5-agents/lesson-9-6-production-agents.py` — the hybrid production agent.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the proactive loop driver.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the orchestrator as the proactive outer loop; each sub-agent is reactive inner.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — reactive vs proactive as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you need an agent vs a single LLM call?"** Answer: agent when the task is multi-step, the model needs to iterate, or the task has tool calls with side effects. Single LLM call when the task is single-step, bounded, and has no tool calls. **Default to reactive; escalate to proactive when needed.**
2. **"What is the difference between a reactive and proactive agent?"** Answer: initiative (user drives vs model drives), time horizon (one step vs many steps), state (stateless vs stateful), side effects (none vs tools that write). The proactive agent needs the 5 guardrails; the reactive agent does not.
3. **"What is the hybrid topology?"** Answer: a proactive outer loop that calls a reactive inner agent as a tool. The outer loop plans + iterates; each inner step is a reactive one-shot. The hybrid is the default 2026 production shape: most CS-drafter agents, research agents, and coding agents are hybrid.

## Read next

`L3-2-single-purpose-vs-general-purpose.md` — the second axis. Single-purpose agents have one tool and one goal; general-purpose agents have many tools and many goals. The right tool count depends on the task's complexity.