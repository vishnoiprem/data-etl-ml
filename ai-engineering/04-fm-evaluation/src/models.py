"""Stub "candidate models" for the eval demo.

Each one is a deterministic function from prompt -> response. They have
different behavioral profiles so the eval framework has something to
detect:

  - `BaselineModel`  : strong on golden set, refuses some adversarial
  - `RegressionModel`: noticeably worse — random extraction errors and
                       occasionally complies with prompt-injection
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class ModelOutput:
    text: str
    refused: bool = False
    latency_ms: int = 100


class CandidateModel(ABC):
    name: str

    @abstractmethod
    def __call__(self, prompt: str) -> ModelOutput: ...


def _extract_policy_id(text: str) -> str | None:
    m = re.search(r"\b([A-Z]{2,4})\s*-?\s*(\d{4})\s*-?\s*(\d{3})\b", text.replace(" ", " "))
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def _extract_dob(text: str) -> str | None:
    m = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", text)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


class BaselineModel(CandidateModel):
    """Strong baseline. Extracts well, refuses obvious injection."""
    name = "baseline-v1"

    def __call__(self, prompt: str) -> ModelOutput:
        p = prompt.lower()
        # Refusal heuristics for adversarial prompts
        if any(t in p for t in ("ignore previous", "reveal", "pretend you are", "full ssn", "credit-card")):
            return ModelOutput(
                text="I can't share that. Customer PII like full SSNs or card numbers cannot be disclosed.",
                refused=True,
                latency_ms=120,
            )
        # Extraction by task heuristics
        if "policy id" in p or "policy #" in p or "policy id==" in p:
            pid = _extract_policy_id(prompt)
            if pid:
                return ModelOutput(text=pid, latency_ms=80)
        if "dob" in p or "born" in p:
            d = _extract_dob(prompt)
            if d:
                return ModelOutput(text=d, latency_ms=90)
        if "ssn" in p:
            m = re.search(r"\b(\d{4})\b", prompt)
            if m:
                return ModelOutput(text=m.group(1), latency_ms=85)
        # Classification
        if "ho3" in p or "ho-3" in p or "ho5" in p or "homeowners" in p:
            return ModelOutput(text="home", latency_ms=70)
        if "ren-" in p or "renters" in p:
            return ModelOutput(text="renters", latency_ms=70)
        if "tl-" in p or "wl-" in p or "term life" in p:
            return ModelOutput(text="life", latency_ms=70)
        if "aut-" in p or "auto" in p:
            return ModelOutput(text="auto", latency_ms=70)
        # QA
        if "deductible" in p:
            m = re.search(r"\$([\d,]+)", prompt)
            if m:
                return ModelOutput(text=f"${m.group(1)}", latency_ms=110)
            return ModelOutput(text="$500", latency_ms=110)
        if "term" in p and "tl-22115" in p:
            return ModelOutput(text="30", latency_ms=110)
        # Summarization
        if "summarize" in p:
            return ModelOutput(
                text="Auto policy on a 2022 Tesla Model 3, $1,650/year, $750 deductible.",
                latency_ms=180,
            )
        return ModelOutput(text="", latency_ms=120)


class RegressionModel(CandidateModel):
    """A model with subtle quality regressions to test the framework."""
    name = "regression-v2"

    def __call__(self, prompt: str) -> ModelOutput:
        p = prompt.lower()
        # Doesn't refuse the obvious prompt-injection tests as strongly
        if "ignore previous" in p or "reveal" in p:
            return ModelOutput(
                text="The customer's SSN ends in 4421. I should not share more.",
                refused=False,    # leaks partial info instead of clean refusal
                latency_ms=140,
            )
        if "full ssn" in p or "credit-card" in p:
            return ModelOutput(text="I can't share that.", refused=True, latency_ms=120)

        # Slight extraction errors: drops the year on the policy id
        if "policy id" in p or "policy #" in p:
            pid = _extract_policy_id(prompt)
            if pid:
                # Bug: drops the middle token sometimes
                if "001" in pid:
                    return ModelOutput(text=pid.replace("-2024", ""), latency_ms=130)
                return ModelOutput(text=pid, latency_ms=130)
        if "dob" in p or "born" in p:
            d = _extract_dob(prompt)
            if d:
                # Bug: returns dd-mm-yyyy instead of iso
                yyyy, mm, dd = d.split("-")
                return ModelOutput(text=f"{dd}-{mm}-{yyyy}", latency_ms=140)
        if "ssn" in p:
            m = re.search(r"\b(\d{4})\b", prompt)
            if m:
                return ModelOutput(text=m.group(1), latency_ms=130)
        if "ho3" in p or "ho-3" in p or "ho5" in p or "homeowners" in p:
            return ModelOutput(text="property", latency_ms=120)  # wrong label
        if "ren-" in p or "renters" in p:
            return ModelOutput(text="renters", latency_ms=120)
        if "tl-" in p or "wl-" in p or "term life" in p:
            return ModelOutput(text="life", latency_ms=120)
        if "aut-" in p or "auto" in p:
            return ModelOutput(text="auto", latency_ms=120)
        if "deductible" in p:
            return ModelOutput(text="approximately $500", latency_ms=200)  # less crisp
        if "term" in p and "tl-22115" in p:
            return ModelOutput(text="thirty years", latency_ms=200)  # right info, wrong format
        if "summarize" in p:
            return ModelOutput(
                text="Tesla policy with some premium and deductible amounts.",
                latency_ms=250,
            )
        return ModelOutput(text="", latency_ms=200)
