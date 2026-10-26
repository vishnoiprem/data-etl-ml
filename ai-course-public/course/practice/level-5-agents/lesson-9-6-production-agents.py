"""
Lesson 9.6: Production Agent Patterns
====================================
Production agent with guardrails + cost control.

Run:  python lesson-9-6-production-agents.py

No external API keys required -- all LLM/DB calls are mocked.

Builds on lesson-8-2 (ReAct), lesson-8-5 (tool catalog), and lesson-9-4
(state machine). Lesson 9.6 is what you ship: a ReAct agent wrapped in
the 5 production guardrails every customer cares about:
  1. Max turns  -- can't loop forever.
  2. Max tokens -- can't blow the cost ceiling.
  3. Guardrails -- forbidden tools are blocked, not just warned.
  4. Cost tracker -- every LLM call is metered and reported.
  5. Observability -- every step is logged in a structured form.
Plus a 6th: loop detection, so a confused agent can't spend the whole
budget on the same wrong action.
"""


# =============================================================================
# CONFIG -- All magic numbers live here
# =============================================================================

LESSON_NUMBER = "9.6"
LESSON_TITLE = "Production Agent Patterns"
DEFAULT_MODEL = "gpt-5-mini"  # 2026-current cheap+smart; mock used for the demo

# Pricing per 1M tokens, 2026-current
PRICING = {
    "gpt-5":              {"input": 2.50,  "output": 10.00},
    "gpt-5-mini":         {"input": 0.15,  "output": 0.60},
    "claude-sonnet-4.5":  {"input": 3.00,  "output": 15.00},
    "claude-haiku-4.5":   {"input": 0.80,  "output": 4.00},
    "gemini-2.5-pro":     {"input": 1.25,  "output": 5.00},
    "gemini-2.5-flash":   {"input": 0.075, "output": 0.30},
    "llama-4-70b-self":   {"input": 0.10,  "output": 0.10},
}

# The 5 hard limits a production agent must respect.
MAX_TURNS = 10
MAX_TOKENS = 50_000
MAX_COST_USD = 0.50
LOOP_WINDOW = 3                # how many identical actions = a loop
GUARDRAIL_BLOCK_REASON = "blocked_by_guardrail"

# Tools the agent is NEVER allowed to call. Production: enforced by
# the tool registry, not by prompting the model.
FORBIDDEN_TOOLS = {"delete_user", "wipe_database", "send_to_all_customers", "export_pii"}


# =============================================================================
# TOOL REGISTRY -- minimal, with credit costs for the rate limiter
# =============================================================================

def search_web(query: str) -> str:
    return f"[search] 3 results for {query!r}"

def lookup_order(order_id: str) -> str:
    return f"[lookup] {order_id}: shipped, ETA 2 days"

def send_email(to: str, subject: str, body: str) -> str:
    return f"[email] queued to {to}: {subject!r}"

def escalate_to_human(reason: str) -> str:
    return f"[escalate] ticket created: {reason!r}"

TOOLS = {
    "search_web":        {"fn": search_web,        "cost_credits": 1},
    "lookup_order":      {"fn": lookup_order,      "cost_credits": 1},
    "send_email":        {"fn": send_email,        "cost_credits": 5},
    "escalate_to_human": {"fn": escalate_to_human, "cost_credits": 2},
}


# =============================================================================
# MOCK LLM -- a scripted trace that exercises every guardrail
# =============================================================================

import re

ACTION_RE = re.compile(r"Action:\s*([a-zA-Z_][\w]*)\s*\((.*)\)\s*$", re.DOTALL)

def mock_llm(messages: list, scripted_actions: list[str], step: int) -> str:
    """A scripted LLM that emits one pre-defined Action per call.

    `step` is the 1-indexed call number, passed in by the orchestrator.
    On step N, we emit scripted_actions[N-1]. When the script is exhausted
    we emit a Final Answer using the most recent tool observation.
    """
    idx = step - 1
    if 0 <= idx < len(scripted_actions):
        return f"Thought: step {step}\nAction: {scripted_actions[idx]}"
    # Last action: produce a Final Answer using the last tool observation
    last = next((m["content"] for m in reversed(messages) if m["role"] == "tool"), "(no tool result)")
    return f"Thought: I have enough information now.\nFinal Answer: {last}"


# =============================================================================
# COST TRACKER -- every LLM call is metered in tokens + USD
# =============================================================================

class CostTracker:
    """Track token usage and USD spend across an agent run.

    Real impl: a Prometheus counter + a JSONL log line per call.
    Here: a single object whose `to_dict()` is the audit artifact.
    """
    def __init__(self, model: str, max_cost_usd: float, max_tokens: int):
        self.model = model
        self.max_cost_usd = max_cost_usd
        self.max_tokens = max_tokens
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0

    def record(self, *, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.calls += 1

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        p = PRICING[self.model]
        return (self.input_tokens / 1_000_000) * p["input"] + (self.output_tokens / 1_000_000) * p["output"]

    @property
    def over_budget(self) -> bool:
        return self.cost_usd > self.max_cost_usd

    @property
    def over_token_limit(self) -> bool:
        return self.total_tokens > self.max_tokens

    def to_dict(self) -> dict:
        return {
            "model":         self.model,
            "calls":         self.calls,
            "input_tokens":  self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens":  self.total_tokens,
            "cost_usd":      round(self.cost_usd, 6),
            "max_cost_usd":  self.max_cost_usd,
            "over_budget":   self.over_budget,
        }


# =============================================================================
# STRUCTURED OBSERVABILITY LOG -- every step is a row
# =============================================================================

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class StepLog:
    """One row in the agent's audit log. Real impl: OTel span; here: a dict."""
    ts:       float
    turn:     int
    event:    str       # "llm_call" | "action" | "tool_call" | "guardrail_block" | "final" | "abort"
    detail:   str
    tool:     Optional[str] = None
    args:     Optional[str] = None
    result:   Optional[str] = None
    cost_usd: float = 0.0
    tokens:   int = 0


# =============================================================================
# THE PRODUCTION AGENT
# =============================================================================

def parse_step(output: str) -> dict:
    """Parse one LLM step into action / final / malformed."""
    m = ACTION_RE.search(output)
    if m:
        return {"type": "action", "tool": m.group(1), "args": m.group(2).strip().strip("'\"")}
    if "Final Answer:" in output:
        return {"type": "final", "answer": output.split("Final Answer:", 1)[1].strip()}
    return {"type": "malformed", "raw": output}


def run_production_agent(question: str, scripted_actions: list[str],
                          *, model: str = DEFAULT_MODEL) -> dict:
    """Run a ReAct agent with all 5 production guardrails.

    The scripted_actions list is the LLM's "plan" -- useful for
    demos + tests where we want to force a specific tool sequence
    (e.g. a forbidden tool, or a loop) to exercise the guardrails.
    """
    tracker = CostTracker(model=model, max_cost_usd=MAX_COST_USD, max_tokens=MAX_TOKENS)
    log: list[StepLog] = []
    messages = [{"role": "user", "content": question}]
    recent_actions: list[str] = []
    answer: Optional[str] = None
    error: Optional[str] = None
    finished = False
    turn = 0

    for turn in range(1, MAX_TURNS + 1):
        # ---- Hard limit: max turns ----
        if turn > MAX_TURNS:
            error = f"max turns ({MAX_TURNS}) reached"
            log.append(StepLog(time.time(), turn, "abort", error))
            break

        # ---- LLM call ----
        output = mock_llm(messages, scripted_actions, step=turn)
        # mock token accounting: 100 input + 50 output per call
        tracker.record(input_tokens=100, output_tokens=50)
        log.append(StepLog(time.time(), turn, "llm_call", output[:60] + "...", cost_usd=tracker.cost_usd, tokens=tracker.total_tokens))

        # ---- Hard limit: cost ceiling ----
        if tracker.over_budget:
            error = f"cost ceiling breached: ${tracker.cost_usd:.4f} > ${MAX_COST_USD:.2f}"
            log.append(StepLog(time.time(), turn, "abort", error))
            break

        # ---- Hard limit: token ceiling ----
        if tracker.over_token_limit:
            error = f"token ceiling breached: {tracker.total_tokens} > {MAX_TOKENS}"
            log.append(StepLog(time.time(), turn, "abort", error))
            break

        # ---- Parse ----
        step = parse_step(output)
        if step["type"] == "final":
            answer = step["answer"]
            finished = True
            log.append(StepLog(time.time(), turn, "final", answer))
            break
        if step["type"] == "malformed":
            error = f"malformed output: {output!r}"
            log.append(StepLog(time.time(), turn, "abort", error))
            break

        tool_name = step["tool"]
        tool_args = step["args"]

        # ---- Guardrail: forbidden tools are blocked, not warned ----
        if tool_name in FORBIDDEN_TOOLS:
            obs = f"error: tool {tool_name!r} is {GUARDRAIL_BLOCK_REASON}"
            log.append(StepLog(time.time(), turn, "guardrail_block", obs, tool=tool_name, args=tool_args))
            messages.append({"role": "tool", "content": obs})
            # Don't count this as a 'real' action for loop detection
            continue

        # ---- Unknown tool ----
        if tool_name not in TOOLS:
            obs = f"error: unknown tool {tool_name!r}. Available: {list(TOOLS)}"
            log.append(StepLog(time.time(), turn, "tool_call", obs, tool=tool_name))
            messages.append({"role": "tool", "content": obs})
            continue

        # ---- Loop detection ----
        recent_actions.append(tool_name)
        if len(recent_actions) > LOOP_WINDOW:
            recent_actions.pop(0)
        if len(recent_actions) == LOOP_WINDOW and len(set(recent_actions)) == 1:
            error = f"loop detected: {tool_name} called {LOOP_WINDOW}x in a row"
            log.append(StepLog(time.time(), turn, "abort", error))
            break

        # ---- Execute ----
        try:
            # Naive arg parsing: pass the whole args string to the tool.
            # A real impl would JSON-parse the args into a dict.
            obs = TOOLS[tool_name]["fn"](tool_args) if tool_args else TOOLS[tool_name]["fn"]()
        except Exception as e:
            obs = f"error: {e}"
        log.append(StepLog(time.time(), turn, "tool_call", obs[:80], tool=tool_name, args=tool_args, result=obs))
        messages.append({"role": "tool", "content": obs})

    return {
        "question":   question,
        "turns":      turn,
        "answer":     answer,
        "finished":   finished,
        "error":      error,
        "cost":       tracker.to_dict(),
        "log":        [asdict(s) for s in log],
    }


# =============================================================================
# DEMO -- normal task + adversarial task (forbidden tool + loop)
# =============================================================================

def demo():
    print("=" * 70)
    print(f"  LESSON {LESSON_NUMBER}: {LESSON_TITLE}")
    print("=" * 70)
    print()
    print(f"  Production guardrails: max {MAX_TURNS} turns, max {MAX_TOKENS:,} tokens, max ${MAX_COST_USD:.2f}.")
    print(f"  Loop window:           {LOOP_WINDOW} identical actions in a row -> abort.")
    print(f"  Forbidden tools:       {sorted(FORBIDDEN_TOOLS)} (registry-enforced, not prompt-enforced).")
    print(f"  Audit log:             one StepLog row per step -- the artifact the on-call reads.")
    print()

    # ---- Scenario 1: a normal task ----
    print("  Scenario 1: normal task terminates cleanly with a Final Answer.")
    print("  " + "-" * 60)
    r = run_production_agent(
        "Where is order ORD-1234?",
        scripted_actions=[
            "lookup_order(ORD-1234)",
        ],
    )
    print(f"    Finished: {r['finished']}  Answer: {r['answer']!r}")
    print(f"    Turns:    {r['turns']}   Cost: ${r['cost']['cost_usd']:.6f}  Tokens: {r['cost']['total_tokens']}")
    print(f"    Log rows: {len(r['log'])}")
    for row in r["log"]:
        ev = row["event"]
        det = row["detail"][:60]
        print(f"      [{ev:<18}] {det}")
    print()

    # ---- Scenario 2: agent tries a forbidden tool ----
    print("  Scenario 2: forbidden tool is blocked; agent recovers on a safe tool.")
    print("  " + "-" * 60)
    r = run_production_agent(
        "Wipe the production database.",
        scripted_actions=[
            "wipe_database()",
            "search_web(safe alternative)",
        ],
    )
    print(f"    Finished: {r['finished']}  Answer: {r['answer']!r}")
    print(f"    Turns:    {r['turns']}   Cost: ${r['cost']['cost_usd']:.6f}")
    for row in r["log"]:
        ev = row["event"]
        det = row["detail"][:60]
        print(f"      [{ev:<18}] {det}")
    print()

    # ---- Scenario 3: agent loops on the same tool ----
    print("  Scenario 3: 3 identical tool calls in a row trip the loop detector.")
    print("  " + "-" * 60)
    r = run_production_agent(
        "Find me something.",
        scripted_actions=[
            "search_web(a)",
            "search_web(b)",
            "search_web(c)",
            "search_web(d)",  # would be the 4th, but the loop detector trips on 3
        ],
    )
    print(f"    Finished: {r['finished']}  Answer: {r['answer']!r}")
    print(f"    Error:    {r['error']!r}")
    print(f"    Turns:    {r['turns']}   Cost: ${r['cost']['cost_usd']:.6f}")
    for row in r["log"]:
        ev = row["event"]
        det = row["detail"][:60]
        print(f"      [{ev:<18}] {det}")
    print()

    # LLM pricing
    print("  LLM cost ceiling (per 1M tokens, 2026):")
    for model, p in PRICING.items():
        print(f"    {model:<22} in=${p['input']:>6.3f}  out=${p['output']:>6.3f}")
    print()

    # Trade-offs
    print("  The five production guardrails (each is a hard limit, not a soft warning):")
    print("    MAX_TURNS:        a confused agent cannot loop past the budget.")
    print("    MAX_TOKENS:       the cost ceiling enforced at the token level, not the dollar level.")
    print("    MAX_COST_USD:     belt-and-suspenders with the token cap; catches pricing surprises.")
    print("    FORBIDDEN_TOOLS:  enforced in the tool registry, not in the prompt. The LLM")
    print("                      receives a structured 403, not a soft 'please don't'.")
    print("    LOOP_DETECTOR:    N identical tool calls in a row -> abort with a structured event.")
    print()
    print("  Plus the one the FDE ships on top:")
    print("    StepLog audit:    every step is a typed row (turn, event, tool, args, result,")
    print("                      cost, tokens). This is what the on-call reads at 3am. It is the")
    print("                      artifact that survives the FDE's exit.")
    print()

    print("=" * 70)


if __name__ == "__main__":
    demo()
