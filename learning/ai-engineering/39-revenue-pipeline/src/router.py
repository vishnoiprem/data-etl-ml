"""
router.py — Pluggable LLM router.

The project ships with `StubRouter` so the demo runs without an API key.
Swap to `AnthropicRouter` or `OpenAIRouter` for production use.

All routers expose the same interface:

    router.complete(prompt: str, system: str = "", max_tokens: int = 1024) -> str
    router.json(prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict
"""

from __future__ import annotations

import json
import re
from typing import Protocol


class LLMRouter(Protocol):
    """Common interface for all LLM providers."""

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str: ...
    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict: ...


# ============================================================
# StubRouter — deterministic, offline, no API key.
# Used by `make demo` and the test suite.
# ============================================================
class StubRouter:
    """Offline router. Returns rule-based responses suitable for demos/tests.

    The "qualifier" stub scores leads by simple keyword heuristics
    (budget signals, urgency words, AI/data terms). The "outreach"
    stub returns a templated cold email with the lead's company
    name stitched in. Both are predictable, so the dashboard math
    is reproducible in CI.
    """

    name = "stub"

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        # Use the system prompt as the primary signal (most reliable),
        # then fall back to prompt sniffing. Outreach calls in this project
        # always pass OUTREACH_SYSTEM; qualify calls don't pass a system.
        s = (system or "").lower()
        if "cold-email writer" in s or "outreach" in s or "cold email" in s:
            return self._stub_outreach(prompt)
        p = prompt.lower()
        if "outreach" in p or "cold email" in p or "subject:" in p:
            return self._stub_outreach(prompt)
        return self._stub_qualify_text(prompt)

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        # The stub always returns valid JSON for json() calls.
        # Decide intent from the schema_hint first (most reliable), then
        # fall back to sniffing the prompt for "qualif"/"score" vs
        # "outreach"/"email".
        hint = schema_hint.lower()
        if "score" in hint or "deal_usd" in hint:
            return self._stub_qualify_json(prompt)
        p = prompt.lower()
        if "qualif" in p or "score" in p:
            return self._stub_qualify_json(prompt)
        if "outreach" in p or "cold email" in p or "subject:" in p:
            return {"text": self._stub_outreach(prompt)}
        return {"text": self._stub_qualify_json(prompt)}

    # --- internal stubs ---
    @staticmethod
    def _stub_qualify_text(prompt: str) -> str:
        p = prompt.lower()
        score = 50
        reasons = []
        if any(w in p for w in ("budget", "approved", "funded", "series b", "series c")):
            score += 25
            reasons.append("explicit budget signal")
        if any(w in p for w in ("urgent", "asap", "immediate", "q4", "this quarter")):
            score += 10
            reasons.append("urgency keyword")
        if any(w in p for w in ("ai", "ml", "llm", "data", "rag", "agent", "vector")):
            score += 10
            reasons.append("matches my service niche")
        if any(w in p for w in ("junior", "intern", "entry", "graduate")):
            score -= 30
            reasons.append("junior-level — likely low budget")
        score = max(0, min(100, score))
        return (
            f"Probability of close: {score}/100. "
            f"Reasons: {'; '.join(reasons) or 'no strong signals'}."
        )

    @staticmethod
    def _stub_qualify_json(prompt: str) -> dict:
        p = prompt.lower()
        score = 50
        reasons: list[str] = []
        if any(w in p for w in ("budget", "approved", "funded", "series b", "series c")):
            score += 25
            reasons.append("explicit budget signal")
        if any(w in p for w in ("urgent", "asap", "immediate", "q4", "this quarter")):
            score += 10
            reasons.append("urgency keyword")
        if any(w in p for w in ("ai", "ml", "llm", "data", "rag", "agent", "vector")):
            score += 10
            reasons.append("matches my service niche")
        if any(w in p for w in ("junior", "intern", "entry", "graduate")):
            score -= 30
            reasons.append("junior-level — likely low budget")
        score = max(0, min(100, score))
        # Estimate deal size: budget signal + niche match = $5-15k
        if score >= 70:
            deal_usd = 12000
        elif score >= 50:
            deal_usd = 5000
        else:
            deal_usd = 1500
        return {
            "score": score,
            "deal_usd": deal_usd,
            "reasons": reasons or ["no strong signals"],
        }

    @staticmethod
    def _stub_outreach(prompt: str) -> str:
        # Try to extract a company name from the prompt
        m = re.search(r"company[:\s]+([A-Z][\w&.\- ]{2,40})", prompt)
        co = (m.group(1).strip() if m else "your team")
        return (
            f"Subject: Quick AI/data project for {co}?\n\n"
            f"Hi — I saw the {co} posting and your stack looks like a fit for "
            f"the kind of work I do (LLM/RAG/agent/data-pipeline consulting, "
            f"short engagements, 4-12 weeks, $5-15k).\n\n"
            f"Two questions:\n"
            f"  1. Is the budget approved, or still pre-approval?\n"
            f"  2. What's the latest you could start and the target ship date?\n\n"
            f"If useful, I can send 2-3 relevant case studies in the next 5 min.\n\n"
            f"— Prem"
        )


# ============================================================
# AnthropicRouter — real API. Requires `anthropic` SDK + key.
# ============================================================
class AnthropicRouter:
    """Real Anthropic API. `pip install anthropic` and set ANTHROPIC_API_KEY."""

    name = "anthropic"

    def __init__(self, model: str = "claude-3-5-haiku-20241022") -> None:
        try:
            import anthropic  # type: ignore
        except ImportError as e:
            raise ImportError(
                "AnthropicRouter requires `pip install anthropic`"
            ) from e
        self._client = anthropic.Anthropic()
        self._model = model

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system or "You are a concise, expert sales assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text  # type: ignore[index]

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        # Claude can return JSON when asked explicitly. We constrain the
        # response by appending the schema hint and post-validating.
        text = self.complete(
            prompt=prompt
            + (f"\n\nRespond with valid JSON matching: {schema_hint}" if schema_hint else
               "\n\nRespond with valid JSON only, no prose."),
            system="You output strictly valid JSON.",
            max_tokens=max_tokens,
        )
        # Strip any markdown code fences
        text = re.sub(r"^```(?:json)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text.strip())
        return json.loads(text)


# ============================================================
# OpenAIRouter — real API. Requires `openai` SDK + key.
# ============================================================
class OpenAIRouter:
    """Real OpenAI API. `pip install openai` and set OPENAI_API_KEY."""

    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        try:
            import openai  # type: ignore
        except ImportError as e:
            raise ImportError(
                "OpenAIRouter requires `pip install openai`"
            ) from e
        self._client = openai.OpenAI()
        self._model = model

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system or "You are a concise, expert sales assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You output strictly valid JSON."},
                {"role": "user", "content": prompt + (
                    f"\n\nSchema: {schema_hint}" if schema_hint else "")},
            ],
        )
        return json.loads(resp.choices[0].message.content or "{}")


def get_default_router() -> LLMRouter:
    """Pick the best available router. Stub → Anthropic → OpenAI."""
    try:
        return AnthropicRouter()
    except (ImportError, Exception):  # noqa: BLE001
        pass
    try:
        return OpenAIRouter()
    except (ImportError, Exception):  # noqa: BLE001
        pass
    return StubRouter()
