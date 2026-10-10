"""
Lesson 8.2: Building Your First Agent
====================================
ReAct agent with parser + error recovery.

Run:  python lesson-8-2-first-agent.py

No external API keys required -- all LLM/DB calls are mocked.
"""


# =============================================================================
# CONFIG -- All magic numbers live here
# =============================================================================

LESSON_NUMBER = "8.2"
LESSON_TITLE = "Building Your First Agent"
DEFAULT_MODEL = "gpt-5-mini"  # 2026-current cheap+smart; mock used for the demo

# Pricing per 1M tokens, 2026-current (per OpenAI, Anthropic, Google public pricing, Q4 2026)
PRICING = {
    "gpt-5":              {"input": 2.50,  "output": 10.00},
    "gpt-5-mini":         {"input": 0.15,  "output": 0.60},
    "claude-sonnet-4.5":  {"input": 3.00,  "output": 15.00},
    "claude-haiku-4.5":   {"input": 0.80,  "output": 4.00},
    "gemini-2.5-pro":     {"input": 1.25,  "output": 5.00},
    "gemini-2.5-flash":   {"input": 0.075, "output": 0.30},
    "llama-4-70b-self":   {"input": 0.10,  "output": 0.10},
}

MAX_TURNS = 10
REPETITION_WINDOW = 3  # how many identical last actions before we treat as a loop


# =============================================================================
# TOOL REGISTRY -- 3 tools: calculator, web_search_mock, get_current_time
# =============================================================================

def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression. Supports + - * / ( ) and integers.

    Reject anything that is not a pure arithmetic expression. No variables,
    no function calls, no attribute access. This is a hard blocklist on the
    eval expression as a defense in depth.
    """
    import ast
    import operator
    binops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    unaryops = {ast.UAdd: operator.pos, ast.USub: operator.neg}
    tree = ast.parse(expression, mode="eval")
    def _eval(node):
        if isinstance(node, ast.Expression): return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in binops:
            return binops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in unaryops:
            return unaryops[type(node.op)](_eval(node.operand))
        raise ValueError(f"disallowed node: {type(node).__name__}")
    try:
        return str(_eval(tree))
    except Exception as e:
        return f"calculator error: {e}"


def web_search_mock(query: str) -> str:
    """Mock web search. Returns canned results for a few known queries."""
    canned = {
        "tokyo time": "Current time in Tokyo (JST, UTC+9): 14:32.",
        "weather tokyo": "Tokyo weather: 18C, partly cloudy, humidity 64%.",
        "usd to sgd": "USD/SGD: 1.34 (mid-market, 2026-10-10).",
        "python version": "Python 3.13 is the current stable release (2026).",
    }
    q = query.strip().lower()
    for k, v in canned.items():
        if k in q:
            return v
    return f"(no results for query: {query!r})"


def get_current_time(timezone: str = "UTC") -> str:
    """Return the current time in a given IANA timezone (UTC, Asia/Tokyo, ...)."""
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"get_current_time error: {e}"


TOOLS = {
    "calculator":       {"fn": calculator,       "args": "expression: str"},
    "web_search_mock":  {"fn": web_search_mock,  "args": "query: str"},
    "get_current_time": {"fn": get_current_time, "args": "timezone: str = 'UTC'"},
}


# =============================================================================
# MOCK LLM -- produces a scripted Thought/Action stream for known questions
# =============================================================================

def mock_llm(messages: list, question: str) -> str:
    """Return a single-model-step output (Thought + Action or Final Answer).

    The mock reads the question + the most recent tool observation, and
    returns the right ReAct trace. In real use, this is replaced by an
    OpenAI / Anthropic call. The interface is intentionally minimal:
    messages in, string out.
    """
    q = question.lower().strip()
    # If the last message is a tool observation, we have what we need to finalize.
    last_role = messages[-1]["role"] if messages else None
    last_content = messages[-1]["content"] if messages else ""
    if last_role == "tool":
        # Use the observation as the answer.
        return f"Thought: I now have enough information to answer.\nFinal Answer: {last_content}"
    if "25 * 17" in q or "25*17" in q or "what is 25" in q:
        return "Thought: I should compute 25 * 17 directly.\nAction: calculator(25 * 17)"
    if "tokyo" in q and "time" in q:
        return "Thought: I need to look up the current time in Tokyo.\nAction: get_current_time('Asia/Tokyo')"
    if "weather" in q and "tokyo" in q:
        return "Thought: I should search for the current Tokyo weather.\nAction: web_search_mock('weather tokyo')"
    if "usd" in q and "sgd" in q:
        return "Thought: I should look up the USD/SGD rate.\nAction: web_search_mock('usd to sgd')"
    # Default: produce a partial-thought output to test the parser
    return "Thought: I'm not sure how to answer that from the available tools.\nFinal Answer: I don't have a tool that can answer that question."


# =============================================================================
# PARSER -- extract Action: tool_name(args) or Final Answer: ...
# =============================================================================

import re

ACTION_RE = re.compile(r"Action:\s*([a-zA-Z_][\w]*)\s*\((.*)\)\s*$", re.DOTALL)
FINAL_RE = re.compile(r"Final Answer:\s*(.+)$", re.DOTALL)


def parse_step(output: str) -> dict:
    """Parse one model step into {type, ...}.

    Returns one of:
      {"type": "action",  "tool": str, "args": str}
      {"type": "final",   "answer": str}
      {"type": "malformed", "raw": str}
    """
    m = ACTION_RE.search(output)
    if m:
        return {"type": "action", "tool": m.group(1), "args": m.group(2).strip().strip("'\"")}
    m = FINAL_RE.search(output)
    if m:
        return {"type": "final", "answer": m.group(1).strip()}
    return {"type": "malformed", "raw": output}


# =============================================================================
# SYSTEM PROMPT -- teach the format
# =============================================================================

SYSTEM_PROMPT = """You are an agent. You have access to the following tools:

{tool_list}

To use a tool, output exactly one line in this format:
  Action: tool_name(arg1, arg2, ...)

When you have enough information to answer, output:
  Final Answer: <your answer>

Always begin with a single line:  Thought: <your reasoning>

Do not output anything else. One Action per turn.
"""


def render_system_prompt() -> str:
    tool_lines = [f"- {name}({meta['args']})" for name, meta in TOOLS.items()]
    return SYSTEM_PROMPT.format(tool_list="\n".join(tool_lines))


# =============================================================================
# REACT LOOP -- the agent run
# =============================================================================

def run_agent(question: str, max_turns: int = MAX_TURNS) -> dict:
    """Run the ReAct loop on `question` using the mock LLM.

    Returns a dict with: question, turns, trace, answer, finished, error.
    The trace is a list of {role, content, step} dicts -- the FDE
    observability artifact.
    """
    messages = [
        {"role": "system", "content": render_system_prompt()},
        {"role": "user",   "content": question},
    ]
    trace = []
    recent_actions = []
    answer = None
    error = None
    finished = False
    for turn in range(1, max_turns + 1):
        output = mock_llm(messages, question)
        trace.append({"turn": turn, "role": "assistant", "content": output})
        step = parse_step(output)
        if step["type"] == "final":
            answer = step["answer"]
            finished = True
            break
        if step["type"] == "malformed":
            error = f"turn {turn}: malformed output: {output!r}"
            break
        # Action: dispatch
        tool_name = step["tool"]
        tool_args = step["args"]
        if tool_name not in TOOLS:
            obs = f"error: unknown tool {tool_name!r}. Available: {list(TOOLS)}"
            trace.append({"turn": turn, "role": "tool", "content": obs})
            continue
        # Repetition detector
        recent_actions.append(tool_name)
        if len(recent_actions) > REPETITION_WINDOW:
            recent_actions.pop(0)
        if len(recent_actions) == REPETITION_WINDOW and len(set(recent_actions)) == 1:
            error = f"loop detected: {tool_name} called {REPETITION_WINDOW} times in a row"
            break
        # Execute
        try:
            obs = TOOLS[tool_name]["fn"](tool_args) if tool_args else TOOLS[tool_name]["fn"]()
        except Exception as e:
            obs = f"error: {e}"
        trace.append({"turn": turn, "role": "tool", "content": obs})
        # Feed the observation back to the LLM
        messages.append({"role": "tool", "content": obs})
    return {
        "question": question,
        "turns": turn,
        "trace": trace,
        "answer": answer,
        "finished": finished,
        "error": error,
    }


# =============================================================================
# DEMO
# =============================================================================

def demo():
    print("=" * 70)
    print(f"  LESSON {LESSON_NUMBER}: {LESSON_TITLE}")
    print("=" * 70)
    print()
    print("  ReAct agent: 3 tools, parser, repetition detector, 10-turn cap.")
    print()
    for q in ["What is 25 * 17?", "What is the time in Tokyo?"]:
        print(f"  Q: {q}")
        result = run_agent(q)
        for step in result["trace"]:
            tag = step["role"].upper()
            content = step["content"].replace("\n", " | ")
            print(f"    [{tag}] {content}")
        if result["finished"]:
            print(f"  A: {result['answer']}")
        elif result["error"]:
            print(f"  ! {result['error']}")
        print(f"  ({result['turns']} turn(s))")
        print()

    print("  Cost model (per 1M tokens, 2026):")
    for model, p in PRICING.items():
        print(f"    {model:<22} in=${p['input']:>6.3f}  out=${p['output']:>6.3f}")
    print()
    print("  Trade-offs (mock vs real API):")
    print("    Mock:  Fast, free, deterministic. Use for design + tests.")
    print("    Real:  Real quality, real cost, real errors. Use for validation.")
    print()
    print("=" * 70)


if __name__ == "__main__":
    demo()
