"""LLM client with mock + Anthropic implementations.

Mirrors the project's `LLM_MODE=auto` convention: real LLM when an
ANTHROPIC_API_KEY is set, deterministic mock otherwise. Mock returns
canned answers + canned graph triples for the AcmeCorp sample corpus.
"""
from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from .config import get_settings


# ─────────────────────────────────────────────────────────────────────────────
# Abstract base
# ─────────────────────────────────────────────────────────────────────────────

class LLMClient(ABC):
    """Tiny LLM abstraction — `complete` for free-form, `extract_json` for triples."""

    name: str = "abstract"

    @abstractmethod
    def complete(self, prompt: str, system: str = "") -> str: ...

    @abstractmethod
    def extract_json(
        self,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
        system: str = "",
    ) -> dict[str, Any]: ...

    # ---- shared helpers ------------------------------------------------

    def _parse_json_lenient(self, text: str) -> dict[str, Any]:
        """Pull the first JSON object out of `text`. Tolerates ```json fences."""
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise ValueError(f"No JSON object found in LLM response: {text!r}")
        return json.loads(m.group(0))


# ─────────────────────────────────────────────────────────────────────────────
# Mock — deterministic, no network, works for the AcmeCorp sample corpus
# ─────────────────────────────────────────────────────────────────────────────

# Canned answer rules.  First matching rule wins; fallback to a "no info" response.
_MOCK_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(pto|paid time off|vacation)\b", re.I),
     "AcmeCorp offers 20 days of PTO per year for full-time employees, accrued monthly. "
     "New hires begin accruing on day 1. Unused PTO carries over up to 5 days; anything above "
     "that is paid out annually. See pto-policy.md for the full table."),
    (re.compile(r"\b(new hire|onboarding)\b", re.I),
     "All new hires go through a 30-90 day onboarding program. Week 1 covers IT setup, "
     "accounts, and laptop provisioning per it-runbooks.md. Your manager assigns a buddy "
     "in week 2. See onboarding.md for the full timeline."),
    (re.compile(r"\b(approval|approve|approval path|travel.*international|international.*travel)\b", re.I),
     "International travel requires VP-level approval. Submit the request via the "
     "expense system at least 14 days before departure; the path is "
     "Manager → Finance → VP. Per expense-policy.md §3, the VP-approval step is "
     "non-negotiable for any trip outside the home country."),
    (re.compile(r"\b(it|runbook|password|laptop|accounts)\b", re.I),
     "IT runbooks live in it-runbooks.md. Day-1 setup: laptop provisioning, "
     "SSO enrollment, password-manager install, and Slack/Email account creation. "
     "For travel-related IT prep (VPN, device encryption), see expense-policy.md §3."),
    (re.compile(r"\b(expense|reimburs|reimbursement)\b", re.I),
     "Expense reimbursement is filed within 30 days of incurring the cost. "
     "Per expense-policy.md §3, international travel requires VP approval and "
     "original receipts for any line item above $75."),
    (re.compile(r"\b(on-?call|pager|incident)\b", re.I),
     "The on-call rotation is weekly, Monday 10:00 to the following Monday 10:00. "
     "Primary and secondary are assigned in on-call.md. PagerDuty is the paging tool. "
     "Incidents are graded SEV1–SEV4 with response-time SLAs in on-call.md §2."),
    (re.compile(r"\b(hiring|interview|recruit)\b", re.I),
     "Hiring is owned by the hiring manager with a recruiting partner. The loop is "
     "Recruiter screen → Hiring manager → Technical → Bar raiser per hiring.md. "
     "Loop scorecards are due within 24 hours of each interview."),
    (re.compile(r"\b(vendor|third.party|access)\b", re.I),
     "Third-party vendor access requires a signed DPA, security review, and "
     "least-privilege IAM role. See vendor-access.md. Reviews are renewed annually."),
    (re.compile(r"\b(project.*naming|naming|code.?name)\b", re.I),
     "Projects are named after constellations. Codenames are assigned at intake. "
     "See project-naming.md. The current in-flight list is at the bottom of that doc."),
    (re.compile(r"\b(leave|parental|medical leave)\b", re.I),
     "AcmeCorp offers 16 weeks paid parental leave for the primary caregiver, "
     "8 weeks for the secondary. Medical leave is job-protected per FMLA. "
     "See leave-policy.md for the full breakdown."),
]


# Canned triple extraction rules.  Keyed on chunk_id; in a real system the LLM
# would produce these.  For the demo we hardcode the known relationships from
# the AcmeCorp corpus so the graph is faithful and reproducible.
_MOCK_TRIPLES: dict[str, list[dict[str, str]]] = {
    "pto-policy.md": [
        {"head": "AcmeCorp", "head_type": "Organization", "rel": "OFFERS", "tail": "PTO", "tail_type": "Policy"},
        {"head": "PTO", "head_type": "Policy", "rel": "GRANTS", "tail": "20 days per year", "tail_type": "Quantity"},
        {"head": "New Hire", "head_type": "Persona", "rel": "ACCRUES", "tail": "PTO", "tail_type": "Policy"},
    ],
    "onboarding.md": [
        {"head": "New Hire", "head_type": "Persona", "rel": "FOLLOWS", "tail": "Onboarding Program", "tail_type": "Program"},
        {"head": "Onboarding Program", "head_type": "Program", "rel": "REFERENCES", "tail": "IT Runbooks", "tail_type": "Document"},
        {"head": "Manager", "head_type": "Role", "rel": "ASSIGNS", "tail": "Buddy", "tail_type": "Role"},
    ],
    "it-runbooks.md": [
        {"head": "IT Runbooks", "head_type": "Document", "rel": "COVERS", "tail": "Laptop Provisioning", "tail_type": "Task"},
        {"head": "IT Runbooks", "head_type": "Document", "rel": "REFERENCES", "tail": "Expense Policy", "tail_type": "Document"},
        {"head": "Laptop Provisioning", "head_type": "Task", "rel": "REQUIRES", "tail": "SSO Enrollment", "tail_type": "Task"},
    ],
    "expense-policy.md": [
        {"head": "Expense Policy", "head_type": "Document", "rel": "REQUIRES", "tail": "VP Approval", "tail_type": "Step"},
        {"head": "VP Approval", "head_type": "Step", "rel": "APPLIES_TO", "tail": "International Travel", "tail_type": "Activity"},
        {"head": "Expense Policy", "head_type": "Document", "rel": "DEADLINE", "tail": "30 days", "tail_type": "Duration"},
    ],
    "on-call.md": [
        {"head": "AcmeCorp", "head_type": "Organization", "rel": "USES", "tail": "PagerDuty", "tail_type": "Tool"},
        {"head": "On-call Rotation", "head_type": "Process", "rel": "USES", "tail": "PagerDuty", "tail_type": "Tool"},
        {"head": "Incidents", "head_type": "Process", "rel": "GRADED_BY", "tail": "SEV1-SEV4", "tail_type": "Taxonomy"},
    ],
    "hiring.md": [
        {"head": "Hiring Manager", "head_type": "Role", "rel": "OWNS", "tail": "Hiring Loop", "tail_type": "Process"},
        {"head": "Hiring Loop", "head_type": "Process", "rel": "INCLUDES", "tail": "Bar Raiser", "tail_type": "Role"},
    ],
    "vendor-access.md": [
        {"head": "Vendor Access", "head_type": "Process", "rel": "REQUIRES", "tail": "DPA", "tail_type": "Document"},
        {"head": "Vendor Access", "head_type": "Process", "rel": "REQUIRES", "tail": "Security Review", "tail_type": "Process"},
    ],
    "project-naming.md": [
        {"head": "Project Naming", "head_type": "Policy", "rel": "REQUIRES", "tail": "Constellation Codenames", "tail_type": "Convention"},
    ],
    "leave-policy.md": [
        {"head": "AcmeCorp", "head_type": "Organization", "rel": "OFFERS", "tail": "Parental Leave", "tail_type": "Policy"},
        {"head": "Parental Leave", "head_type": "Policy", "rel": "GRANTS", "tail": "16 weeks primary", "tail_type": "Quantity"},
    ],
}


class MockLLM(LLMClient):
    """Deterministic LLM for the demo. No network. Works with no API key."""

    name = "mock"

    def complete(self, prompt: str, system: str = "") -> str:
        # The first ~1000 chars of the prompt always include the user's question
        # (we don't parse it carefully — we just match keywords).
        # Also fall through to a generic "I don't know" for clearly OOS questions.
        if re.search(r"\b(ceo|home address|personal phone|ssn|social security)\b", prompt, re.I):
            return "I don't have that information in the available documentation."

        for pattern, answer in _MOCK_RULES:
            if pattern.search(prompt):
                return answer
        return "I don't have that information in the available documentation."

    def extract_json(
        self,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
        system: str = "",
    ) -> dict[str, Any]:
        # The prompt includes a "Source: <chunk_id>" hint; we use it to look up
        # canned triples.  Fallback: empty list.
        m = re.search(r"Source:\s*(\S+\.md)", prompt)
        if not m:
            return {"triples": []}
        chunk_id = m.group(1)
        triples = _MOCK_TRIPLES.get(chunk_id, [])
        return {"triples": triples}


# ─────────────────────────────────────────────────────────────────────────────
# Anthropic — real LLM
# ─────────────────────────────────────────────────────────────────────────────

class AnthropicLLM(LLMClient):
    name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "anthropic package not installed. Run `make install`."
            ) from e
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Use LLM_MODE=mock to run without a key."
            )
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def complete(self, prompt: str, system: str = "") -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system or "You are a precise, citation-grounded enterprise assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        # All content blocks are text for our use
        return "".join(b.text for b in msg.content if hasattr(b, "text"))

    def extract_json(
        self,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
        system: str = "",
    ) -> dict[str, Any]:
        # Use a tool definition to force JSON.  We give Claude a tool whose
        # input_schema is the triple list shape, and require it.
        tool = {
            "name": "emit_triples",
            "description": "Emit a JSON object with a 'triples' array of subject-predicate-object facts.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "triples": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "head": {"type": "string"},
                                "head_type": {"type": "string"},
                                "rel": {"type": "string"},
                                "tail": {"type": "string"},
                                "tail_type": {"type": "string"},
                            },
                            "required": ["head", "rel", "tail"],
                        },
                    },
                },
                "required": ["triples"],
            },
        }
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system or "Extract entity-relation-entity triples from the text.",
            tools=[tool],
            tool_choice={"type": "tool", "name": "emit_triples"},
            messages=[{"role": "user", "content": prompt}],
        )
        # Find the tool_use block
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use" and block.name == "emit_triples":
                return block.input
        # Fallback: parse the first text block
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        return self._parse_json_lenient(text)


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

def get_llm() -> LLMClient:
    s = get_settings()
    mode = s.llm_mode.lower()
    has_key = bool(s.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", ""))
    if mode == "auto":
        mode = "real" if has_key else "mock"
    if mode == "mock":
        logger.info("Using MockLLM (no network, no API key).")
        return MockLLM()
    if mode == "real":
        key = s.anthropic_api_key or os.environ["ANTHROPIC_API_KEY"]
        logger.info(f"Using AnthropicLLM (model={s.anthropic_model}).")
        return AnthropicLLM(api_key=key, model=s.anthropic_model)
    raise ValueError(f"Unknown LLM_MODE: {mode!r}. Use auto | mock | real.")
