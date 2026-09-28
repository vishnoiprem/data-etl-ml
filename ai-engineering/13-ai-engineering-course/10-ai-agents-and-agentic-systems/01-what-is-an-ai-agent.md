# Lesson 1 — What is an AI Agent?

> **Type:** Article + Worked Example · Module 10
> The five core parts, the loop, the failure modes — with a minimal agent built from scratch.

---

## The 30-second definition

An **AI Agent** is an LLM plus (1) a goal, (2) tools it can call, (3) memory of what it has done, and (4) a loop that runs until the goal is reached.

```
   CHATBOT                           AGENT
   ────────                          ──────
   User: "What's the weather?"       User: "Plan my weekend in Paris."
   LLM:  "I don't have access        Agent: [searches flights]
          to real-time data."                 [checks weather]
                                            [finds hotels]
                                            [books restaurant]
                                            "Booked. Here's the
                                             itinerary."
```

The shift is from "answer" to "do work."

---

## The five core parts

```
   ┌──────────────────────────────────────────────────────────┐
   │  AI AGENT                                                   │
   │                                                           │
   │   1. GOAL          What the user wants accomplished        │
   │      "Plan my weekend in Paris"                            │
   │                                                           │
   │   2. MODEL         The LLM brain                           │
   │      GPT-4 / Claude / Llama                                │
   │                                                           │
   │   3. TOOLS         Functions the model can call            │
   │      search_flights, check_weather, book_hotel, ...        │
   │                                                           │
   │   4. MEMORY        What it has done + learned              │
   │      Short-term: current task state                        │
   │      Long-term:  past interactions, user prefs              │
   │                                                           │
   │   5. LOOP          How it gets from goal to done          │
   │      think → act → observe → ... → answer                  │
   │                                                           │
   └──────────────────────────────────────────────────────────┘
```

The loop is the difference between a chatbot and an agent.

---

## The agent loop (the canonical flow)

```
   ┌─────────────────────────────────────────────────────────────┐
   │   while not done and step < MAX_STEPS:                       │
   │       thought = LLM(messages, tools)                        │
   │       if thought has tool_call:                             │
   │           result = execute_tool(tool_call)                   │
   │           messages.append(tool_call, result)                 │
   │       else:                                                 │
   │           return thought.text                               │
   └─────────────────────────────────────────────────────────────┘
```

Each iteration:
1. Send the model the current state (messages + available tools)
2. Model returns either a tool call or a final answer
3. If tool call: execute it, append the result, loop
4. If final answer: return it

---

## When to use an agent (and when not to)

| Use an agent | Don't use an agent |
|---|---|
| Multi-step tasks (3+ steps) | Single LLM call |
| Needs external data / APIs | All info is in the prompt |
| Decisions depend on intermediate results | Linear pipeline |
| Could benefit from retry / self-correction | One-shot generation |
| Long-running workflows | Interactive chat |

**Rule of thumb:** if you can draw the steps on a whiteboard upfront, you don't need an agent. You need a chain. If the steps depend on what previous steps returned, you need an agent.

---

## Worked Example — a minimal agent from scratch (no framework)

> **Goal:** Build an agent in 80 lines of Python. One tool (calculator). One goal ("what's 17 * 23 + (45 / 9)?"). Watch it reason, call the tool, and answer. Plus the eval that catches runaway loops.

### Step 1 — The tool

```python
import json

def calculator(expression: str) -> str:
    """Evaluate a math expression safely."""
    try:
        # Sandboxed: only allow safe characters
        if not all(c in "0123456789+-*/.() " for c in expression):
            return "Error: invalid characters"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"
```

### Step 2 — The agent loop

```python
import openai

client = openai.OpenAI()
MODEL = "gpt-4o-mini"

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate a math expression. Supports +, -, *, /, parentheses.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The math expression to evaluate",
                }
            },
            "required": ["expression"],
        },
    },
}

TOOLS = {"calculator": calculator}

SYSTEM_PROMPT = """You are a math assistant. You have access to a calculator tool.

For any calculation, call the calculator. Do NOT try to do math in your head.
After getting the result, respond to the user.
"""

def run_agent(user_query: str, max_steps: int = 5) -> tuple[str, int]:
    """Returns (final_answer, n_steps)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    for step in range(1, max_steps + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[TOOL_SCHEMA],
            tool_choice="auto",
        )
        msg = response.choices[0].message

        # Append the assistant's message
        messages.append(msg)

        # Did it call a tool?
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"  step {step}: tool={fn_name}({fn_args})")

                # Execute the tool
                result = TOOLS[fn_name](**fn_args)
                print(f"           result={result}")

                # Append the tool result
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        else:
            # No tool call: it's the final answer
            print(f"  step {step}: final answer")
            return msg.content, step

    return "Error: max steps exceeded", max_steps
```

### Step 3 — Run it

```python
print("Query 1:")
answer, steps = run_agent("What's 17 * 23 + (45 / 9)?")
print(f"Answer: {answer}")
print(f"Steps:  {steps}\n")

print("Query 2:")
answer, steps = run_agent("If a shirt costs $45 and is 20% off, and there's a 8% sales tax, what's the final price?")
print(f"Answer: {answer}")
print(f"Steps:  {steps}")
```

Expected output:

```
Query 1:
  step 1: tool=calculator({'expression': '17 * 23 + (45 / 9)'})
           result=396.0
  step 2: final answer
Answer: 17 * 23 = 391. 45 / 9 = 5. 391 + 5 = 396.
Steps:  2

Query 2:
  step 1: tool=calculator({'expression': '45 * 0.8'})
           result=36.0
  step 2: tool=calculator({'expression': '36 * 1.08'})
           result=38.88
  step 3: final answer
Answer: The shirt is $45 with 20% off, so $36. With 8% tax: $38.88.
Steps:  3
```

The agent **decomposed the problem into two calculations**. Without the tool, the model might have gotten the second one wrong.

### Step 4 — The eval harness (catches runaway loops)

```python
# Eval set: 50 questions that need calculation
EVAL_SET = [
    {"q": "What's 17 * 23 + (45 / 9)?", "a": 396.0},
    {"q": "A shirt costs $45 and is 20% off with 8% tax. Final price?", "a": 38.88},
    # ... 48 more, mix of simple, multi-step, edge cases
]

def eval_agent(eval_set, max_steps=5):
    correct, total_steps, failures = 0, [], []
    for ex in eval_set:
        answer, steps = run_agent(ex["q"], max_steps=max_steps)
        total_steps.append(steps)

        # Try to parse the numerical answer
        import re
        nums = re.findall(r"-?\d+\.?\d*", answer)
        if nums and abs(float(nums[-1]) - ex["a"]) < 0.01:
            correct += 1
        else:
            failures.append({"q": ex["q"], "expected": ex["a"], "got": answer, "steps": steps})

    return {
        "accuracy": correct / len(eval_set),
        "avg_steps": sum(total_steps) / len(total_steps),
        "max_steps_used": max(total_steps),
        "failures": failures,
    }

results = eval_agent(EVAL_SET)
print(f"Accuracy:       {results['accuracy']:.3f}")
print(f"Avg steps:      {results['avg_steps']:.1f}")
print(f"Max steps used: {results['max_steps_used']}")
```

Expected:

```
Accuracy:       0.94
Avg steps:      2.6
Max steps used: 4
```

The 6% failure cases are usually:
- The model answered directly without calling the tool (got it wrong)
- The model entered an arithmetic error in the expression
- The question was ambiguous (e.g., "what's the cost?" before tax)

### Step 5 — Common failure modes

| Failure | Symptom | Fix |
|---|---|---|
| Runaway loop | Agent keeps calling tools past `max_steps` | Hard cap + alert |
| Hallucinated tool call | Calls a tool that doesn't exist | Validate tool names |
| Wrong args | Passes the wrong arguments | Schema validation, Pydantic |
| Infinite retry on error | Calls the same tool with the same bad args | Detect repeats, abort |
| Skipped tool | Knows it should use a tool but doesn't | Force `tool_choice="required"` |
| Stuck on plan | Keeps planning, never executes | Time limit, force act |
| Too long | Output is 10K words of reasoning | Trim each step, summarize |

### Step 6 — Production hardening

```python
def run_agent_safe(user_query: str, max_steps: int = 5, timeout_s: float = 30):
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Agent timed out")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout_s))

    try:
        return run_agent(user_query, max_steps=max_steps)
    except TimeoutError:
        return "Sorry, I couldn't complete this in time. Please try a simpler request.", max_steps
    finally:
        signal.alarm(0)
```

The 80-line agent becomes production-ready with three additions:
1. Hard step cap
2. Wall-clock timeout
3. Eval harness

---

## What this example teaches

1. **An agent is a loop.** `while not done: think, act, observe.`
2. **Tools make the model useful.** Without them, the agent is a chatbot.
3. **Eval catches the failure modes.** Runaway loops, wrong args, hallucinated tools.
4. **Hard caps are non-negotiable.** Without `max_steps`, the agent runs forever.
5. **The 80-line version is the production version.** Frameworks (LangChain, LangGraph) add convenience, not capability.

This is the foundation for every later module. Read it once and you understand agents. Read it twice and you understand why the frameworks exist.

---

## What Comes Next

> Lesson 2 — **Function Calling** — the JSON contract, the conversation loop, multi-step and parallel calls.