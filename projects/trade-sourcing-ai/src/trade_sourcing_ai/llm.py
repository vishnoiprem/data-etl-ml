"""The model layer: a small provider abstraction with a deterministic default.

The agent's *decision* is made in Python. The LLM only ever explains a
decision that has already been made. That keeps three important properties:

1. **Tests are hermetic.** No API key, no network, no flakiness.
2. **The decision is reproducible.** Same quotes in, same supplier out.
3. **The cost is knowable.** The local paths genuinely cost $0 per query.

Three routers are provided:

``StubRouter``
    Deterministic. Parses structured fields out of the prompt with regexes
    rather than returning random text, so it produces a *specific* answer.
    This is what CI runs against and what the demo uses.

``OllamaRouter``
    Optional. Talks to a local Ollama server. Used when
    ``TRADE_AI_LLM_PROVIDER=ollama`` and the server is reachable.

``get_default_router``
    Chooses between them. The provider check reads the environment first —
    it never probes the network at import time.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMRouter(Protocol):
    """The minimal interface the agent needs from a language model."""

    name: str

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        """Return free text for a prompt."""
        ...

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        """Return a JSON object for a prompt."""
        ...


class LLMError(RuntimeError):
    """Raised when a router cannot fulfil a request."""


# --------------------------------------------------------------------------- #
# Stub router
# --------------------------------------------------------------------------- #


class StubRouter:
    """A deterministic stand-in for a real model.

    It reads ``Label: value`` pairs out of the prompt — the same convention
    the repo's side-hustle project uses — so the output tracks the actual
    inputs rather than being random. That makes it useful in tests: assert
    the explanation mentions the right supplier and the right margin.
    """

    name = "stub"

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        supplier = self._extract(prompt, "Supplier")
        margin = self._extract(prompt, "Margin")
        score = self._extract(prompt, "Score")
        conflicts = self._extract(prompt, "Conflicts")

        parts = []
        if supplier and supplier.lower() != "none":
            parts.append(
                f"{supplier} is the recommended supplier"
                + (f", on a modelled margin of {margin}" if margin else "")
                + (f" and a composite score of {score}" if score else "")
                + "."
            )
        else:
            parts.append("No supplier could be recommended from the quotes supplied.")
        if conflicts and conflicts.lower() != "none":
            parts.append(f"Carry these risks into the decision: {conflicts}.")
        return " ".join(parts)

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        supplier = self._extract(prompt, "Supplier")
        margin = self._extract(prompt, "Margin")
        score = self._extract(prompt, "Score")
        conflicts = self._extract(prompt, "Conflicts")

        payload: dict[str, Any] = {
            "recommended_supplier": supplier or None,
            "rationale": self.complete(prompt, max_tokens=max_tokens),
            "key_risks": [c.strip() for c in conflicts.split(";") if c.strip()],
        }
        margin_value = _first_number(margin)
        if margin_value is not None:
            payload["margin_pct"] = margin_value
        score_value = _first_number(score)
        if score_value is not None:
            payload["composite_score"] = score_value
        return payload

    @staticmethod
    def _extract(prompt: str, label: str, default: str = "") -> str:
        """Pull ``Label: value`` out of a prompt, case-insensitively."""
        pattern = rf"^{re.escape(label)}\s*:\s*(.+?)\s*$"
        match = re.search(pattern, prompt, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else default


def _first_number(text: str) -> float | None:
    if not text:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


# --------------------------------------------------------------------------- #
# Ollama router
# --------------------------------------------------------------------------- #


class OllamaRouter:
    """Optional local model backend via an Ollama server.

    Only used when explicitly requested via ``TRADE_AI_LLM_PROVIDER=ollama``.
    If the server is not reachable the caller falls back to the stub.
    """

    name = "ollama"

    def __init__(self, model: str = "qwen2.5:7b-instruct", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")
        self.tokens_used = 0

    def _post(self, path: str, payload: dict[str, Any], timeout: float = 60.0) -> dict:
        import httpx

        try:
            response = httpx.post(f"{self.host}{path}", json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise LLMError(f"Ollama request to {self.host}{path} failed: {exc}") from exc

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        data = self._post(
            "/api/chat",
            {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
        )
        content = data.get("message", {}).get("content", "")
        self.tokens_used += int(data.get("eval_count", 0) or 0)
        return content

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        system = (
            "Respond with a single JSON object and nothing else."
            + (f" The object should contain: {schema_hint}." if schema_hint else "")
        )
        raw = self.complete(prompt, system=system, max_tokens=max_tokens)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise LLMError(f"Ollama did not return a JSON object: {raw[:200]!r}")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMError(f"Ollama returned invalid JSON: {exc}") from exc


# --------------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------------- #


def get_default_router() -> LLMRouter:
    """Pick the router from the environment.

    The environment is read *first* and the provider is matched explicitly.
    We never try to construct a hosted client and wait for it to fail on the
    first request — the SDK constructors do not validate credentials, so an
    auth error would only surface later, at the worst possible moment.
    """
    provider = os.environ.get("TRADE_AI_LLM_PROVIDER", "").strip().lower()

    if provider == "ollama":
        router = OllamaRouter(
            model=os.environ.get("TRADE_AI_OLLAMA_MODEL", "qwen2.5:7b-instruct"),
            host=os.environ.get("TRADE_AI_OLLAMA_HOST", "http://localhost:11434"),
        )
        try:
            router.complete("ping", max_tokens=1)
        except LLMError:
            return StubRouter()
        return router

    return StubRouter()
