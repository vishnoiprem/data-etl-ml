"""The narrative layer — the model writes, Python decides.

This is the whole point of the project's architecture, expressed in one
module: **the model may only write prose.** It cannot change a
severity, a dollar figure, a basis, a confidence, a recommendation, or
a finding's identity. The finding's ``summary`` is written in Python
and is authoritative; the ``narrative`` is the model's explanation of
it and is printed *after* it.

That is enforced structurally, not by convention:

* The router returns a **string**. There is no channel by which a
  model could return a number.
* ``apply_narrative`` writes the string into ``finding.narrative`` and
  **nothing else**. It does not parse the model's output for numbers.
* The eval harness asserts that a router which returns complete garbage
  changes no field of any finding except ``narrative``.

Two backends, matching the sibling projects:

``StubRouter``
    Deterministic. It writes a fixed explanatory paragraph built from
    the finding's own fields — so the offline path is not a placeholder
    but a real explanation, and the CI suite exercises it.

``OllamaRouter``
    Optional. Talks to a local Ollama server.

``get_default_router``
    Reads the environment first and matches the provider explicitly. It
    never constructs a client and waits for it to fail — the failure
    would land on the first article rather than at startup.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol, runtime_checkable

from .models import Finding


@runtime_checkable
class LLMRouter(Protocol):
    """The minimal interface the narrative writer needs."""

    name: str

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        """Return free text for a prompt."""
        ...


class LLMError(RuntimeError):
    """Raised when a router cannot fulfil a request."""


# --------------------------------------------------------------------------- #
# Stub router
# --------------------------------------------------------------------------- #


class StubRouter:
    """A deterministic stand-in for a real model.

    It assembles a paragraph from the finding's own fields. It is not
    a mock that returns "" — it produces prose that explains the
    finding, so the offline path is worth exercising.
    """

    name = "stub"

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        if not prompt.strip():
            return ""

        fields = _parse_fields(prompt)
        if not fields:
            return ""

        target = fields.get("Target", "the resource")
        detector = fields.get("Detector", "")
        impact, basis = _impact_and_basis(fields.get("Cost impact", ""))

        if basis == "measured":
            figure = (
                f"The {impact} is what appears on the bill, so this is a measurement "
                f"rather than an estimate."
            )
        elif basis == "modelled":
            figure = (
                f"The {impact} is modelled: an observed volume multiplied by a "
                f"rate from the illustrative rate card. Treat it as indicative."
            )
        elif basis == "upper_bound":
            if impact == "$0.00":
                # Saying "$0.00 is an upper bound" reads like the cost is
                # zero, which is the opposite of the truth. What we
                # actually have is a problem we can name but not price.
                figure = (
                    "The size of this is not quantified: the underlying quantity "
                    "could not be measured directly, so no figure is claimed."
                )
            else:
                figure = (
                    f"The {impact} is an upper bound on a quantity that could not be "
                    f"measured directly, so the real figure may be smaller — or zero."
                )
        else:
            figure = ""

        opener = {
            "growth": "This is a growth finding: the cost went up, and it went up enough to matter.",
            "access": "This is an access-pattern finding: the cost comes from how the data is being read, not from how much of it there is.",
            "lifecycle": "This is a storage-class finding: the data is sitting in a more expensive class than it needs to be.",
            "allocation": "This is an allocation finding: the cost belongs to a team, and that team's share is moving.",
        }.get(detector, "This is a cost finding.")

        # The summary is already printed above the narrative, so
        # repeating it verbatim would read as a stutter. The narrative
        # adds the *kind* of finding and the *basis* of the number.
        parts = [opener]
        if target and target != "the resource":
            parts.append(f"The target is {target}.")
        if figure:
            parts.append(figure)
        return " ".join(parts).strip()


def _parse_fields(prompt: str) -> dict[str, str]:
    """Pull ``Label: value`` pairs out of the prompt."""
    fields: dict[str, str] = {}
    for line in prompt.splitlines():
        match = re.match(r"^([A-Z][A-Za-z ]*):\s*(.+?)\s*$", line)
        if match:
            fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def _impact_and_basis(cost_impact_field: str) -> tuple[str, str]:
    """Split ``"2000.00 USD (measured)"`` into the figure and the basis.

    The basis is in parentheses because that is how the prompt writes
    it, and because the basis is the thing that must not be lost — a
    narrative that drops "measured" reads exactly like one that
    dropped the caveat.
    """
    text = cost_impact_field.strip()
    basis = ""
    match = re.search(r"\(([a-z_]+)\)\s*$", text)
    if match:
        basis = match.group(1)
        text = text[: match.start()].strip()

    amount = ""
    amount_match = re.search(r"([\d,.]+)", text)
    if amount_match:
        amount = amount_match.group(1)

    if not amount:
        return "cost", basis
    return f"${amount}", basis


# --------------------------------------------------------------------------- #
# Ollama router
# --------------------------------------------------------------------------- #


class OllamaRouter:
    """Optional local model backend via an Ollama server.

    Only used when explicitly requested. If the server is not reachable
    the caller falls back to the stub.
    """

    name = "ollama"

    def __init__(self, model: str = "qwen2.5:7b-instruct", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")
        self.tokens_used = 0

    def _post(self, path: str, payload: dict[str, Any], timeout: float = 120.0) -> dict:
        import httpx

        try:
            response = httpx.post(f"{self.host}{path}", json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise LLMError(f"Ollama request to {self.host}{path} failed: {exc}") from exc

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
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
                "options": {"num_predict": max_tokens, "temperature": 0.3},
            },
        )
        content = data.get("message", {}).get("content", "")
        self.tokens_used += int(data.get("eval_count", 0) or 0)
        return content.strip()

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 512) -> dict:
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


def get_default_router(provider: str = "", host: str = "", model: str = "") -> LLMRouter:
    """Pick the router from the environment.

    The environment is read *first* and the provider matched explicitly.
    We never try to construct a hosted client and wait for it to fail.
    """
    chosen = (provider or os.environ.get("AWSCA_PROVIDER", "")).strip().lower()
    if not chosen:
        chosen = os.environ.get("COPYFORGE_LLM_PROVIDER", "stub").strip().lower()

    if chosen == "ollama":
        router = OllamaRouter(
            model=model or os.environ.get("COPYFORGE_OLLAMA_MODEL", "qwen2.5:7b-instruct"),
            host=host or os.environ.get("COPYFORGE_OLLAMA_HOST", "http://localhost:11434"),
        )
        try:
            router.complete("ping", max_tokens=1)
        except LLMError:
            return StubRouter()
        return router

    return StubRouter()


# --------------------------------------------------------------------------- #
# Applying a narrative
# --------------------------------------------------------------------------- #


def build_prompt(finding: Finding) -> str:
    """The prompt for one finding's narrative.

    The prompt carries the finding's *own* numbers and asks the model
    to explain them. The model is never asked for a number — asking it
    for one is how a model ends up in the decision path.
    """
    lines = [
        "Explain this AWS cost finding to the engineer who owns the account.",
        "",
        f"Detector: {finding.detector}",
        f"Target: {finding.target}",
        f"Severity: {finding.severity}",
        f"Cost impact: {finding.cost_impact:.2f} USD ({finding.cost_impact_basis})",
        f"Confidence: {finding.confidence:.2f}",
        f"Summary: {finding.summary}",
    ]
    if finding.evidence:
        lines.append("Evidence:")
        for evidence in finding.evidence:
            lines.append(
                f"  - {evidence.metric}: {evidence.value} {evidence.unit} "
                f"(from {evidence.source}, {evidence.period})"
            )
    if finding.recommendation:
        lines.append(f"Recommendation already determined: {finding.recommendation}")
    lines.extend(
        [
            "",
            "Write two or three sentences explaining what happened and why it matters.",
            "Do not restate the numbers as new figures and do not recommend anything",
            "different from the recommendation above — it has already been decided.",
        ]
    )
    return "\n".join(lines)


def apply_narrative(router: LLMRouter, finding: Finding) -> Finding:
    """Attach a model's explanation to a finding.

    This function writes exactly one field: ``narrative``. Everything
    else about the finding — the severity, the impact, the basis, the
    confidence, the recommendation, the ID — is already fixed by the
    deterministic path, and nothing here can alter it.
    """
    try:
        text = router.complete(build_prompt(finding), max_tokens=200)
    except LLMError:
        text = ""

    finding.narrative = text.strip()
    return finding


def apply_narratives(router: LLMRouter, findings: list[Finding]) -> list[Finding]:
    """Attach narratives to every finding."""
    for finding in findings:
        apply_narrative(router, finding)
    return findings
