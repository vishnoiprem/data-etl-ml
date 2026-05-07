"""Indicative pricing table — USD per 1K tokens (US East, 2025).

These numbers are a simplification of public Bedrock pricing for the
purposes of the demo. In production, the router pulls effective prices
from a daily-refreshed config so price changes don't require a deploy.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelSpec:
    name: str
    in_per_1k: float
    out_per_1k: float
    base_latency_ms: int   # rough p50 for a 500-token response
    quality_tier: str      # "small" | "medium" | "large"


REGISTRY: dict[str, ModelSpec] = {
    "haiku":  ModelSpec("anthropic.claude-3-haiku-20240307-v1:0", 0.00025, 0.00125, 600,  "small"),
    "sonnet": ModelSpec("anthropic.claude-3-5-sonnet-20241022-v2:0", 0.003,  0.015,  1300, "medium"),
    "opus":   ModelSpec("anthropic.claude-3-opus-20240229-v1:0",   0.015,  0.075,  2400, "large"),
}


def cost_usd(model_key: str, in_tokens: int, out_tokens: int) -> float:
    m = REGISTRY[model_key]
    return (in_tokens / 1000.0) * m.in_per_1k + (out_tokens / 1000.0) * m.out_per_1k
