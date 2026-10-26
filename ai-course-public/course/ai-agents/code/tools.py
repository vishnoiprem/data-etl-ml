"""
================================================================
TOOLS  --  Mock LLM + tool registry for the AI Agents course.
================================================================

Run:    python3 code/tools.py
Keys:   none (mock LLM, no external API)

This is the only file in the course that touches a language model.
Everything else (the agent, the ROI formula, the 1000-cycle review)
runs on synthetic data so the course is fully reproducible without
API keys, network access, or a GPU.

The 5 tools below are the canonical "tool registry" pattern: each
tool is a Python function with a name, a cost in credits, and a
clear signature.  An agent can call any of them; the registry
tracks calls + costs.
"""

from __future__ import annotations

import time
import random
from dataclasses import dataclass, field
from typing import Callable, Any


# =================================================================
# CONFIG  --  All magic numbers live here
# =================================================================

LESSON_NUMBER = "tools.py"
PRICING = {
    # Cost per call in credits.  1 credit = $0.002 in this course.
    "summarize_text": 1,
    "classify_intent": 1,
    "extract_fields": 2,
    "lookup_record": 1,
    "send_email": 3,
}

# =================================================================
# TOOL REGISTRY  --  the canonical pattern
# =================================================================

def summarize_text(text: str, max_words: int = 50) -> str:
    """Mock text summarizer.  Returns the first max_words words."""
    return " ".join(text.split()[:max_words])


def classify_intent(text: str) -> str:
    """Mock intent classifier.  Returns one of {buy, sell, hold, query}."""
    text_l = text.lower()
    if "buy" in text_l or "purchase" in text_l:
        return "buy"
    if "sell" in text_l or "exit" in text_l:
        return "sell"
    if "?" in text_l or "what" in text_l or "how" in text_l:
        return "query"
    return "hold"


def extract_fields(text: str, fields: list[str]) -> dict[str, str]:
    """Mock field extractor.  Returns {field: 'mock_<field>'} for each."""
    return {f: f"mock_{f}" for f in fields}


def lookup_record(key: str) -> dict[str, Any]:
    """Mock database lookup.  Returns a fake record."""
    return {"key": key, "value": f"value_for_{key}", "ts": time.time()}


def send_email(to: str, subject: str, body: str) -> dict[str, str]:
    """Mock email sender.  Returns {status: 'sent'}."""
    return {"status": "sent", "to": to, "subject": subject}


TOOLS: dict[str, dict[str, Any]] = {
    "summarize_text": {"fn": summarize_text, "cost_credits": PRICING["summarize_text"]},
    "classify_intent": {"fn": classify_intent, "cost_credits": PRICING["classify_intent"]},
    "extract_fields": {"fn": extract_fields, "cost_credits": PRICING["extract_fields"]},
    "lookup_record": {"fn": lookup_record, "cost_credits": PRICING["lookup_record"]},
    "send_email": {"fn": send_email, "cost_credits": PRICING["send_email"]},
}


# =================================================================
# COST TRACKER  --  the production pattern
# =================================================================

@dataclass
class CostTracker:
    """Tracks credits spent across tool calls.  Used for the cost
    ceiling guardrail (L3) and for the ROI formula (L1)."""
    credits_per_dollar: float = 500.0  # 1 credit = $0.002
    total_credits: int = 0
    calls: list[dict[str, Any]] = field(default_factory=list)

    def charge(self, tool_name: str, cost_credits: int) -> None:
        self.total_credits += cost_credits
        self.calls.append({"tool": tool_name, "cost": cost_credits, "ts": time.time()})

    @property
    def total_dollars(self) -> float:
        return self.total_credits / self.credits_per_dollar


# =================================================================
# MOCK LLM  --  deterministic, no API key
# =================================================================

@dataclass
class MockLLM:
    """A deterministic mock LLM.  Picks a tool to call based on the
    user request; if none matches, returns a 'final' answer.

    Production pattern: replace this with `openai.ChatCompletion.create`
    or `anthropic.messages.create`.  The agent's interface does not
    change."""
    rng_seed: int = 42

    def decide(self, user_request: str, available_tools: list[str]) -> dict[str, Any]:
        rng = random.Random(self.rng_seed + hash(user_request) % 10_000)
        # 70% chance to call a tool, 30% to answer directly
        if rng.random() < 0.7 and available_tools:
            tool = rng.choice(available_tools)
            return {"action": "tool", "tool": tool, "args": {"text": user_request}}
        return {"action": "final", "answer": f"Mock answer for: {user_request[:60]}"}


# =================================================================
# DEMO
# =================================================================

def demo() -> None:
    """Run a tiny demo to prove the registry works."""
    print("=" * 60)
    print(f"  {LESSON_NUMBER}  --  Tool registry + cost tracker demo")
    print("=" * 60)

    cost = CostTracker()
    llm = MockLLM()

    # Simulate 3 agent steps
    for i, request in enumerate([
        "Summarize the meeting notes from yesterday",
        "Classify the intent of 'should I buy SOXL?'",
        "Send the daily compliance email to ops@acme.com",
    ]):
        decision = llm.decide(request, list(TOOLS.keys()))
        if decision["action"] == "tool":
            tool_name = decision["tool"]
            tool = TOOLS[tool_name]
            result = tool["fn"](**decision.get("args", {}))
            cost.charge(tool_name, tool["cost_credits"])
            print(f"  Step {i+1}: {tool_name} -> {str(result)[:60]}  [cost {tool['cost_credits']} credits]")
        else:
            print(f"  Step {i+1}: FINAL -> {decision['answer']}")

    print("-" * 60)
    print(f"  Total tool calls: {len(cost.calls)}")
    print(f"  Total credits:    {cost.total_credits}")
    print(f"  Total cost:       ${cost.total_dollars:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    demo()
