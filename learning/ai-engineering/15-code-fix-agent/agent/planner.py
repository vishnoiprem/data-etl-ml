"""Planner — asks the LLM what to do next, given the current state."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from .schemas import AgentDecision


PLANNER_SYSTEM = """You are a code-fix agent. You are given a failing test, error message,
or bug description. Your job is to read the relevant code, propose a minimal patch,
verify it by re-running tests, and either finish (success) or give up (max attempts reached).

OUTPUT FORMAT — respond with valid JSON matching this schema:
{{
  "thought": "<one sentence: what you concluded from the previous step>",
  "next_action": "<one of: read_file, grep, list_dir, apply_edits, run_tests, git_commit, git_push, open_pr, finish>",
  "args": {{...action-specific args...}},
  "is_done": false,
  "final_summary": null
}}

When is_done=true and next_action="finish", set final_summary to a 2-3 sentence summary.

RULES:
- Prefer the smallest possible diff. Do not refactor unrelated code.
- old_text in apply_edits must be UNIQUE in the file. Include surrounding context if needed.
- Never push to main/master unless the user is on it and explicitly asked for it.
- If you've tried 3 edits and tests still fail, finish with is_done=true and explain what you couldn't figure out.
"""


class Planner:
    def __init__(self, model: str = "gpt-4o-mini", max_cost_usd: float = 0.50):
        self.client = OpenAI()
        self.model = model
        self.max_cost_usd = max_cost_usd
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0

    @property
    def cost_usd(self) -> float:
        # gpt-4o-mini prices (input / output per 1M tokens)
        return (
            self.input_tokens / 1e6 * 0.15
            + self.output_tokens / 1e6 * 0.60
        )

    def decide(self, history: list[dict[str, Any]], user_task: str) -> AgentDecision:
        """Ask the model for the next action given the history."""
        if self.cost_usd > self.max_cost_usd:
            return AgentDecision(
                thought="cost cap reached",
                next_action="finish",
                is_done=True,
                final_summary=f"Stopped after spending ${self.cost_usd:.3f} on {self.calls} LLM calls.",
            )

        messages = [
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": f"TASK: {user_task}\n\nHISTORY SO FAR:\n{_format_history(history)}"},
        ]

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        self.input_tokens += resp.usage.prompt_tokens
        self.output_tokens += resp.usage.completion_tokens
        self.calls += 1

        raw = resp.choices[0].message.content
        data = json.loads(raw)
        return AgentDecision.model_validate(data)


def _format_history(history: list[dict[str, Any]]) -> str:
    """Compact human-readable trace of what the agent has done."""
    lines = []
    for i, step in enumerate(history, 1):
        action = step.get("action", "?")
        result = step.get("result", "")
        if isinstance(result, str) and len(result) > 600:
            result = result[:600] + "...[truncated]"
        lines.append(f"  step {i}: {action}\n    → {result}")
    return "\n".join(lines) if lines else "  (no steps yet)"