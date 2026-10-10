# L1.2: LLM call vs. agent — reactive vs. proactive

> **FDE framing in one line:** an LLM call is reactive (you ask, it answers); an agent is proactive (it plans, acts, observes, iterates toward a goal). The shift from reactive to proactive is the entire reason agents exist as a distinct abstraction.

## In 60 seconds

> "The cleanest distinction is not 'with tools vs without tools' — it's **who initiates the next step**. In an LLM call, the user initiates every step. In an agent, the model initiates the next step based on the goal. Four differences: initiative, time horizon, state, side effects. The cost of agency: a proactive system needs guardrails that a reactive one doesn't — a cost ceiling, a loop detector, a schema validator. The wrong choice is to think of an agent as an LLM call with more steps. The right choice is to think of an agent as a goal-seeking loop, with the LLM as the decision function. **Agents are what you get when you give an LLM a goal and a budget.**"

**The wrong choice is to read past this block.** The right choice is to recite the four differences (initiative, time horizon, state, side effects) before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The four differences between an LLM call and an agent: initiative, time horizon, state, and side effects.
2. The cost of agency: why a proactive system needs guardrails that a reactive one doesn't.
3. The "next big thing" framing: agents are what you get when you give an LLM a goal and a budget.

## Concept

The cleanest distinction between an LLM call and an agent is not "with tools vs without tools." Lots of LLM calls have tools (function calling, structured outputs, retrieval). The cleanest distinction is **who initiates the next step.**

In an LLM call, the user initiates every step. You ask, the model answers. You ask again, the model answers again. Each call is independent; the model has no memory of the last call unless you put it in the prompt. The model is a function: `answer = LLM(prompt)`. It does not know what it said last turn; it does not know what tool it called last turn; it does not know whether the user is happy with the answer.

In an agent, the model initiates steps toward a goal. The user states the goal once. The model plans, calls a tool, observes the result, decides what to do next, calls another tool, observes, decides, and so on — until it has enough information to emit a `Final Answer` or it hits a budget. The agent is a loop: `while not done: action = LLM(state); execute(action); update(state)`. The model owns the iteration.

This is the reactive-vs-proactive distinction. The LLM call is *reactive* — it responds when prompted, and only then. The agent is *proactive* — it acts on the goal between prompts, without being asked each time.

The four concrete differences, in order of operational impact:

1. **Initiative.** The LLM call has none — the user drives every step. The agent has full initiative within the budget — the model drives the iteration. This is the single biggest behavioral difference.
2. **Time horizon.** The LLM call is bounded by the prompt length and the model's context window. The agent is bounded by the budget (turns, tokens, USD, time) and the tool latency. An agent that takes 10 minutes and 50 tool calls to answer a question is a perfectly valid agent; the same question as a single LLM call would be impossible.
3. **State.** The LLM call has no state between calls. The agent has state — the messages list, the long-term memory, the episodic memory, the tool cache. The state is what lets the agent pick up where it left off after a tool call.
4. **Side effects.** The LLM call has none (assuming no retrieval-augmented generation with side-effecting retriever). The agent has side effects — every tool call may write to a database, send an email, or move money. Side effects are what make the cost of agency nonzero.

The cost of agency is the operational consequence of the proactive loop. A reactive LLM call cannot loop forever (the user is the only driver). A proactive agent can — and will — loop forever if the model is confused, the tool is broken, or the budget is unbounded. **This is why every shipping agent has a cost ceiling, a loop detector, and an audit log.** The proactive loop is a feature; the side effects of a confused loop are a liability.

## The pattern

The reactive-vs-proactive distinction is a pattern in disguise. It is the pattern of "who owns the iteration," and it appears in three forms across software:

| Reactive (caller-driven) | Proactive (system-driven) |
|---|---|
| LLM call | Agent loop |
| HTTP request/response | Long-running job with state |
| SQL query | Database transaction |
| Function call | Event-driven worker |

The pattern repeats: the proactive form owns a budget (time, money, retries), holds state across iterations, and can have side effects. The reactive form is bounded by a single call, has no state, and is side-effect-free by construction. **Every proactive form needs the four FDE guardrails: budget, state, idempotency, audit. Every reactive form needs none of them.**

The "next big thing" framing is the recognition that the LLM is mature enough to be the decision function in a proactive loop. Until 2022, the decision function in an agent had to be a hand-written rules engine, a reinforcement-learned policy, or a symbolic planner. None of these were general-purpose. The LLM is the first general-purpose decision function that can read a tool description, pick the right tool, parse the observation, and decide what to do next — across arbitrary domains. **The LLM is the missing piece that made agents practical.** The rest of the agent framework (the loop, the tools, the memory, the guardrails) is the same as it was in 1995; only the decision function changed.

## Code or example

The reactive form, in 5 lines:

```python
# Reactive: the user drives every step.
def llm_call(prompt: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
```

The proactive form, in 25 lines:

```python
# Proactive: the model drives the iteration.
def run_agent(goal: str, tools: dict, llm, max_turns: int = 10, max_cost_usd: float = 0.50):
    messages = [{"role": "user", "content": goal}]
    cost = 0.0
    for turn in range(1, max_turns + 1):
        output = llm(messages)
        cost += estimate_cost(output)  # cost ceiling
        if cost > max_cost_usd:
            return {"error": f"cost ceiling breached (${cost:.4f})", "turns": turn}
        step = parse_step(output)
        if step["type"] == "final":
            return {"answer": step["answer"], "turns": turn, "cost": cost}
        if step["tool"] not in tools:
            messages.append({"role": "tool", "content": f"unknown tool: {step['tool']}"})
            continue
        try:
            obs = tools[step["tool"]](step["args"])
        except Exception as e:
            obs = f"error: {e}"
        messages.append({"role": "tool", "content": str(obs)})
    return {"error": f"max turns ({max_turns}) reached", "turns": max_turns, "cost": cost}
```

The 20 extra lines are the cost of agency: the loop driver, the cost ceiling, the parser, the error envelope, the tool registry. None of those exist in the reactive form.

## Production addendum

The reactive-vs-proactive distinction is the cleanest way to explain the FDE additions to a non-technical stakeholder. The script:

> "An LLM call is like a search engine: you ask, it answers. An agent is like an employee: you give it a goal, it figures out what to do, it asks you if it's stuck, and it tells you when it's done. The employee costs money, makes mistakes, and needs supervision. The search engine doesn't. Agents cost money, make mistakes, and need supervision — that's why we ship them with a cost ceiling, an audit log, and a human-in-the-loop approval step for anything that costs more than $100."

This 30-second pitch is the difference between a candidate who says "I built an agent" and a candidate who says "I built an agent, and here's the operational boundary it ships inside." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-2-first-agent.py` — the full ReAct agent.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/` — the cost ceiling + audit log as first-class FDE patterns.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — three proactive sub-agents with shared state.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/company-experiences/anthropic-fde-customer-simulation.md` — the customer-simulation round is exactly the reactive-vs-proactive test in costume.

## The 3 questions this lecture preps you for

1. **"What's the difference between an LLM call and an agent?"** Answer: who initiates the next step. LLM = reactive (user drives). Agent = proactive (model drives within a budget). The four operational consequences: initiative, time horizon, state, side effects.
2. **"Why are agents the next layer above LLMs?"** Answer: the LLM is the first general-purpose decision function that can read a tool, pick the right one, and decide what to do next across arbitrary domains. The agent framework (loop, tools, memory, guardrails) is the same as 1995; only the decision function changed.
3. **"What's the cost of agency?"** Answer: a confused agent can loop forever and rack up side effects. The four FDE guardrails that don't exist in the reactive form: budget, state, idempotency, audit.

## Read next

`L1-3-why-agents-now.md` — the "why now" framing is what separates an engineer who uses agents from an engineer who understands them.
