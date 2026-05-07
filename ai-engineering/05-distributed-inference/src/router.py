"""Difficulty classification + routing logic."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class RouteDecision:
    model_key: str
    tier: str
    reason: str


_HARD_CUES = re.compile(r"\b(analyze|synthesize|compare and contrast|long-form|essay|tradeoffs|multi-step)\b", re.I)
_MEDIUM_CUES = re.compile(r"\b(summarize|explain|why|how does|reason|infer|recommend)\b", re.I)
_EASY_CUES = re.compile(r"\b(extract|what is|find|list|classify|yes/no)\b", re.I)


def classify_difficulty(prompt: str, expected_output_tokens: int = 200) -> RouteDecision:
    """Heuristic difficulty router.

    In production, swap with a tiny-LLM classifier (one Haiku call per route)
    or a fine-tuned distilbert. Heuristics get you 70–80% accuracy, which is
    enough for cost wins.
    """
    n = len(prompt.split())
    long = n > 800 or expected_output_tokens > 800

    if _HARD_CUES.search(prompt) or long:
        return RouteDecision("opus", "hard", "complex reasoning / long-form")
    if _MEDIUM_CUES.search(prompt) or n > 200:
        return RouteDecision("sonnet", "medium", "explanation / multi-step")
    if _EASY_CUES.search(prompt) or n <= 200:
        return RouteDecision("haiku", "easy", "extraction / lookup")
    return RouteDecision("sonnet", "medium", "default")
