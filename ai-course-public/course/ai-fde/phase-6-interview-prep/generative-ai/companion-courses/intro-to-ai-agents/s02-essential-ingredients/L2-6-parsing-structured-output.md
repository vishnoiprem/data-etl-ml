# L2.6: Parsing structured model output

> **FDE framing in one line:** the parser is the contract between the model output and the tool dispatcher. A good parser turns a malformed output into a structured error the model can read; a bad parser crashes the loop on the first weird output and burns the cost ceiling.

## In 60 seconds

> "Three failure modes. Malformed format: the model emits something the parser cannot recognize. Valid format but missing fields: the schema validator catches it. Valid format but invalid values: the schema validator catches it. **The parser never crashes; the parser returns a structured error with the raw output and a hint; the model reads the observation, corrects, and retries; the loop continues; the cost ceiling catches the loop.** The wrong choice is to let the parser raise an exception (the loop aborts on the first weird output). The wrong choice is to return None (the loop has no way to recover). The right choice is the structured-error observation pattern: every parse failure is a typed tool result the model can read."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The three failure modes of parsing: malformed format, valid format but missing fields, valid format but invalid field values.
2. The regex-based parser for ReAct: handle whitespace, escaping, multi-line args, and the "Final Answer:" boundary.
3. The structured-error pattern: every parse failure returns a structured observation the model can read; the loop continues; the cost ceiling catches the loop.

## Concept

The model emits text. The agent framework executes actions. The parser is the bridge. **The parser is a contract** — the model promises to emit a specific format (ReAct or function-calling); the parser promises to extract the structured action from the text. When the model breaks the contract, the parser returns a structured error; the model reads the error and retries; the loop continues.

The three failure modes of parsing:

1. **Malformed format.** The model emits something the parser cannot recognize: free-text with no `Action:` line, an extra newline that breaks the regex, a typo (`Actoin:` instead of `Action:`). The parser returns `{"_ok": False, "_err": "malformed_format", "raw": output}`.
2. **Valid format but missing fields.** The model emits `Action: tracker.lookup()` with no args. The schema validator returns `{"_ok": False, "_err": "schema_violation", "violations": ["missing field: shipment_id"]}`.
3. **Valid format but invalid field values.** The model emits `Action: tracker.lookup(shipment_id=12345)` (int instead of str) or `Action: tracker.lookup(shipment_id='INVALID')` (regex mismatch). The schema validator returns `{"_ok": False, "_err": "schema_violation", "violations": ["shipment_id: expected string, got int", ...]}`.

The three failure modes compose. A malformed format is the parser's responsibility; missing fields and invalid values are the schema validator's responsibility. The agent framework treats both as structured errors that the model reads as observations. **The model is the recovery mechanism; the parser is the diagnoser.**

The regex-based parser for ReAct is the canonical example. The parser handles:

- **Whitespace.** `Action:\s*tool_name\s*\((.*)\)\s*$` allows any amount of whitespace before the tool name, after the colon, around the parens.
- **Escaping.** Args may contain parentheses (e.g., `(amount=1.50)`) and quotes. The parser uses `re.DOTALL` to match across lines and handles escaped quotes inside the args.
- **Multi-line args.** A model may emit `Action: send_email(\n  to='alice@example.com',\n  body='Hi',\n)` across multiple lines. The parser uses `re.DOTALL` and stops at the closing `)` followed by end-of-line.
- **The "Final Answer:" boundary.** The parser distinguishes between `Action: tool_name(args)` (continue the loop) and `Final Answer: ...` (return the answer). The regex for Final Answer is `r"Final Answer:\s*(.+)$"` with `re.DOTALL` to capture multi-line final answers.

The structured-error pattern is the recognition that **every parse failure returns a structured observation the model can read**. The model reads the observation, diagnoses the error (missing field, invalid value, malformed format), corrects its output, and retries. The loop continues; the cost ceiling catches the loop. The parser never crashes; the parser never returns None; the parser never raises an exception that propagates out of the loop.

```python
# Bad: the parser crashes on malformed output; the loop aborts.
action_match = re.search(r"Action: (\w+)\((.*)\)", output)
tool_name = action_match.group(1)  # AttributeError if match is None

# Good: the parser returns a structured error; the loop continues.
def parse_step(output: str) -> dict:
    m = ACTION_RE.search(output)
    if m: return {"type": "action", "tool": m.group(1), "args": m.group(2).strip()}
    m = FINAL_RE.search(output)
    if m: return {"type": "final", "answer": m.group(1).strip()}
    return {"type": "malformed", "raw": output, "hint": "expected 'Action: tool(args)' or 'Final Answer: ...'"}
```

The pattern that wins interviews is the "parser as structured-error diagnoser" pattern. The candidate who says "the parser never crashes; the parser returns a structured error with the raw output and a hint; the model reads the observation and retries; the cost ceiling catches the loop" is the candidate who demonstrates the production mindset.

## The pattern

The robust parser, in 30 lines:

```python
import re

ACTION_RE = re.compile(
    r"^Action:\s*([a-zA-Z_]\w*)\s*\((.*)\)\s*$",
    re.DOTALL | re.MULTILINE,
)
FINAL_RE = re.compile(
    r"^Final Answer:\s*(.+)$",
    re.DOTALL | re.MULTILINE,
)
THOUGHT_RE = re.compile(
    r"^Thought:\s*(.+)$",
    re.DOTALL | re.MULTILINE,
)

def parse_step(output: str) -> dict:
    """Parse the model output into a structured step. Never raises."""
    # Try Final Answer first — it's the terminal state.
    m = FINAL_RE.search(output)
    if m:
        return {"type": "final", "answer": m.group(1).strip()}
    # Try Action.
    m = ACTION_RE.search(output)
    if m:
        thought = THOUGHT_RE.search(output)
        return {
            "type": "action",
            "tool": m.group(1).strip(),
            "args_raw": m.group(2).strip(),
            "thought": thought.group(1).strip() if thought else "",
        }
    # Malformed: return a hint so the model can self-correct.
    return {
        "type": "malformed",
        "raw": output[:500],  # cap raw output to avoid prompt bloat
        "hint": "expected format: 'Thought: ...\\nAction: tool_name(args)' or 'Final Answer: ...'",
    }
```

The pattern that wins interviews is the "structured-error observation" pattern. The model emits malformed output; the parser returns a structured observation; the model reads it; the model corrects; the loop continues.

## Code or example

The full parse-and-dispatch loop:

```python
def run_agent(goal: str, tools: dict, llm, max_turns: int = 10):
    """Agent loop with robust parsing."""
    messages = [{"role": "user", "content": goal}]
    for turn in range(1, max_turns + 1):
        output = llm(messages)
        messages.append({"role": "assistant", "content": output})
        step = parse_step(output)

        if step["type"] == "final":
            return {"answer": step["answer"], "turns": turn, "finished": True}

        if step["type"] == "malformed":
            # Return a structured error as an observation. The model reads it.
            messages.append({
                "role": "tool",
                "content": json.dumps({
                    "_ok": False,
                    "_err": "malformed_format",
                    "raw": step["raw"],
                    "hint": step["hint"],
                }),
            })
            continue

        # Valid action: dispatch via the schema validator
        try:
            args = parse_args(step["args_raw"])  # best-effort JSON-like parse
        except Exception as e:
            messages.append({"role": "tool", "content": json.dumps({"_ok": False, "_err": "args_parse_failed", "message": str(e)})})
            continue

        result = call_tool(step["tool"], args)
        messages.append({"role": "tool", "content": json.dumps(result)})

    return {"error": f"max turns ({max_turns}) reached", "turns": max_turns}
```

The parser test suite:

```python
def test_parse_step_final_answer():
    out = "Thought: I have the answer.\nFinal Answer: Hello!"
    assert parse_step(out) == {"type": "final", "answer": "Hello!"}

def test_parse_step_action():
    out = "Thought: I need to look up the tracker.\nAction: tracker.lookup(shipment_id='PF-1003')"
    step = parse_step(out)
    assert step["type"] == "action"
    assert step["tool"] == "tracker.lookup"
    assert "shipment_id" in step["args_raw"]

def test_parse_step_malformed():
    out = "I don't know what to do."
    step = parse_step(out)
    assert step["type"] == "malformed"
    assert "hint" in step
    assert step["raw"] == out[:500]
```

## Production addendum

The parser is the answer to the "how do you handle malformed model output" interview question. The 60-second script:

> "Three failure modes. Malformed format: the model emits something the parser cannot recognize. Valid format but missing fields: the schema validator catches it. Valid format but invalid values: the schema validator catches it. **The parser never crashes; the parser returns a structured error with the raw output and a hint; the model reads the observation, corrects, and retries; the loop continues; the cost ceiling catches the loop.** The wrong choice is to let the parser raise an exception (the loop aborts on the first weird output). The wrong choice is to return None (the loop has no way to recover). The right choice is the structured-error observation pattern: every parse failure is a typed tool result the model can read."

This 60-second pitch is the difference between a candidate who says "we parse the output" and a candidate who says "the parser returns a structured error observation, the model reads it and retries, the cost ceiling catches the loop." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-2-first-agent.py::parse_step()` — the production parser.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/09-react-agent-tools.py::parse_action()` — the production-grade parser with 5+ error modes.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — structured errors as the FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — the MCP server as a parser-fronted dispatcher.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the parser as a system design component.

## The 3 questions this lecture preps you for

1. **"How do you handle malformed model output?"** Answer: the parser returns a structured error observation with the raw output and a hint. The model reads the observation, diagnoses the error, and retries. The loop continues; the cost ceiling catches the loop. The parser never crashes; the parser never returns None.
2. **"What are the three failure modes of parsing?"** Answer: (1) malformed format — the parser cannot extract an Action or Final Answer; (2) valid format but missing fields — the schema validator catches it; (3) valid format but invalid values — the schema validator catches it. All three return structured errors the model reads as observations.
3. **"Why does the parser never crash?"** Answer: because the parser is the recovery mechanism. If the parser crashes, the loop aborts on the first malformed output and the cost ceiling is breached with zero work done. If the parser returns a structured error, the loop continues, the model self-corrects, and the agent recovers. **The parser is the diagnoser; the model is the healer; the loop is the immune system.**

## Read next

`L2-7-combining-the-ingredients.md` — the seventh lecture and the synthesis. The 7 ingredients composed into the canonical shipping agent. The candidate who can name all 7 and explain how they compose is the candidate who passes the centerpiece round.