# L1.1: What is an AI agent?

> **FDE framing in one line:** an agent is a system that perceives its environment through sensors, makes decisions through a model, and takes actions through actuators to achieve a goal — the same definition as classical AI, now rebranded around LLMs.

## The 3 things you'll learn

1. The classical AI definition of an agent (perception → decision → action) and why it survived 70 years.
2. The four parts of any agent: sensors, model, actuators, and goal.
3. The concrete shape of an LLM agent: a tool list, a system prompt, a parser, a loop driver, and a memory.

## Concept

The word "agent" comes from classical AI, where it meant any system that acted on behalf of a user in an environment. The canonical 1990s textbook definition had three parts: **perception** (how the system observes the world), **decision** (how the system chooses what to do), and **action** (how the system affects the world). Add a fourth — **goal** — and you have the four-part definition that has survived every AI winter, every hype cycle, and every framework rebrand.

In 2026, the same four-part definition still applies, but the *decision* part is an LLM. The sensors are tool calls, file reads, API queries. The actuators are tool calls, file writes, message sends. The goal is a user request. The LLM is the decision function. Everything else is plumbing.

This is the cleanest one-sentence definition you can give in an interview:

> An AI agent is a system that perceives its environment (via tool calls), makes decisions (via an LLM), and takes actions (via tool calls) to achieve a goal (a user request).

The four parts:

1. **Sensors** — how the agent observes the world. For an LLM agent, sensors are tool calls that return information: `web_search`, `database_query`, `file_read`, `api_get`. The output of a sensor is fed into the LLM's context as an observation.
2. **Model** — the decision function. For an LLM agent, this is the LLM itself, prompted with the system prompt + the user request + the observation history. The model emits a structured action (or a final answer).
3. **Actuators** — how the agent affects the world. For an LLM agent, actuators are tool calls that have side effects: `send_email`, `create_ticket`, `refund_create`, `database_write`. The model emits the action; the agent framework executes it.
4. **Goal** — what the agent is trying to achieve. For an LLM agent, the goal is the user's request, stated at the start of the loop and (usually) preserved in the system prompt.

The reason this four-part definition has survived is that it composes. You can replace any one part without redesigning the others. You can swap the LLM (decision) for a different model. You can swap the tool list (sensors + actuators) for a different domain. You can swap the goal (a user request) for a scheduled task or a sub-task delegated by another agent. The framework is invariant under substitution.

## The pattern

The concrete shape of an LLM agent is a `for` loop with five components:

```python
# The agent loop, in 10 lines
def run_agent(goal: str, tools: dict, llm, max_turns: int = 10):
    messages = [{"role": "system", "content": render_system_prompt(tools)},
                {"role": "user", "content": goal}]
    for turn in range(max_turns):
        output = llm(messages)                 # 1. decision (the LLM call)
        action = parse_action(output)          # 2. parse the structured action
        if action.type == "final":
            return action.answer
        observation = tools[action.tool](**action.args)  # 3. actuator / sensor
        messages.append({"role": "tool", "content": observation})  # 4. feedback
    return "max turns reached"
```

The five components:

1. **System prompt** — declares the tool catalog and the output format the model must emit. The model is told "you have these tools; respond with `Action: tool_name(args)` or `Final Answer: ...`."
2. **Tool registry** — a dict of `name → (description, args_schema, function)`. The model reads the descriptions to decide which tool to call; the agent framework validates the args and dispatches the function.
3. **Parser** — extracts `Action: tool_name(args)` or `Final Answer: ...` from the model output. The parser is the contract between the LLM and the rest of the system; if it fails, the model gets a structured error observation and retries.
4. **Loop driver** — the `for` loop. It bounds the run with `max_turns`, watches for `Final Answer`, and feeds observations back into the prompt.
5. **Memory** — the `messages` list. Short-term (in the prompt), long-term (in a vector DB), episodic (summarized past sessions). The agent loop is memoryless on its own; the messages list is the memory.

This is the canonical ReAct agent. The name "ReAct" comes from "Reason + Act" — the model first emits a `Thought: ...` line explaining what it's about to do, then an `Action: tool_name(args)` line to do it. The agent framework runs the tool, captures the output as an `Observation: ...`, and feeds it back. The model then emits another `Thought: ...` and either another action or a `Final Answer: ...`.

The reason ReAct won the protocol war over plain function-calling is that the `Thought` line gives the model a place to reason about its previous observation *before* committing to the next action. This reduces loops (the model can read its own history and notice it's going in circles) and surfaces errors (the model can read an error observation and adjust its strategy). Function-calling without the thought line works for trivial cases but degrades on multi-step problems.

## Code or example

The minimal agent loop, stdlib-only:

```python
import re
from typing import Callable

ACTION_RE = re.compile(r"Action:\s*([a-zA-Z_]\w*)\s*\((.*)\)\s*$", re.DOTALL)
FINAL_RE  = re.compile(r"Final Answer:\s*(.+)$", re.DOTALL)

def parse_step(output: str) -> dict:
    m = ACTION_RE.search(output)
    if m: return {"type": "action", "tool": m.group(1), "args": m.group(2).strip()}
    m = FINAL_RE.search(output)
    if m: return {"type": "final", "answer": m.group(1).strip()}
    return {"type": "malformed", "raw": output}

def run_agent(goal: str, tools: dict, llm: Callable, max_turns: int = 10) -> dict:
    """The 10-line agent loop. Returns the final answer or an error."""
    messages = [{"role": "user", "content": goal}]
    for turn in range(1, max_turns + 1):
        output = llm(messages)
        step = parse_step(output)
        if step["type"] == "final":
            return {"answer": step["answer"], "turns": turn, "finished": True}
        if step["type"] == "malformed":
            return {"error": f"turn {turn}: malformed output", "turns": turn}
        # Dispatch the tool
        if step["tool"] not in tools:
            messages.append({"role": "tool", "content": f"unknown tool: {step['tool']}"})
            continue
        try:
            obs = tools[step["tool"]](step["args"])
        except Exception as e:
            obs = f"error: {e}"
        messages.append({"role": "tool", "content": str(obs)})
    return {"error": f"max turns ({max_turns}) reached", "turns": max_turns}
```

The 5 production guardrails that wrap this loop are covered in Section 6 (Implementing AI agents in practice) and the practice lesson `lesson-9-6-production-agents.py`. The 4 production tools that go in the `tools` dict are covered in Section 6 and `lesson-8-5-tool-design.py`. The memory that augments `messages` is covered in Section 2 and `lesson-8-6-agent-memory.py`.

## Production addendum

The 10-line loop is the *prototype*. The shipping agent adds 5 layers:

1. **Tool schema validation** — every tool call is validated against a JSON-Schema-like args spec. The model gets a structured `403` if it tries to call a tool with the wrong args, not a Python `TypeError`. See `lesson-8-5-tool-design.py::validate_args()`.
2. **Cost ceiling** — the loop tracks input/output tokens and aborts if the run exceeds `MAX_COST_USD`. The default behavior of a confused agent is to spend the entire budget; the cost ceiling is the only thing that prevents that.
3. **Loop detector** — if the same tool fires N times in a row, the loop aborts with a structured error. The model is told "you've called `web_search` 3 times in a row; break out and ask the user."
4. **Idempotency on write tools** — every write tool keys on a stable hash of the canonical args. A retry produces the same side effect or none. The model can safely retry on transient errors.
5. **Audit log** — every step is a typed log row (turn, event, tool, args, result, cost, tokens). The audit log is the artifact the on-call reads at 3am. It is the first-class deliverable, not a side effect.

These 5 are the FDE additions to the prototype. They are not optional.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-2-first-agent.py` — the full ReAct agent with 3 tools, parser, and repetition detector.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/09-react-agent-tools.py` — the production-grade ReAct with 5+ tools, error recovery, stuck detector, iteration budget, cost + time tracking, structured logging.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/` — the agent loop in the FDE frame (state externalization, idempotency keys, audit log).
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the agent loop composed across 3 sub-agents.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the canonical agentic AI system design pattern.

## The 3 questions this lecture preps you for

1. **"Define an AI agent in one sentence."** Answer with the four-part definition: perceives via sensors, decides via a model, acts via actuators, toward a goal. Then ground it: "In 2026, the model is an LLM, the sensors and actuators are tool calls, and the goal is a user request."
2. **"What's the difference between an LLM call and an agent?"** Answer: an LLM call is one model invocation; an agent is a loop over many model invocations with tool feedback in between. The LLM is the decision function; the agent is the loop, the tools, the memory, and the cost ceiling.
3. **"What are the four parts of an agent?"** Answer: sensors, model, actuators, goal. The sensors and actuators are tool calls. The model is the LLM. The goal is the user request. Compose them with a loop driver, and you have an agent.

## Read next

`L1-2-llm-vs-agent.md` — the reactive-vs-proactive distinction is the cleanest way to articulate why agents are the next abstraction layer above LLMs.
