"""Shared utilities for the AI Engineering portfolio.

This module provides common helpers used across projects:
- Mode detection (LOCAL vs AWS)
- Logging configuration
- Cost tracking primitives
- A simple AWS client factory
"""
from __future__ import annotations

import os
import sys
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from loguru import logger


class Mode(str, Enum):
    LOCAL = "LOCAL"
    AWS = "AWS"


def get_mode() -> Mode:
    """Returns the current execution mode."""
    return Mode(os.getenv("AI_ENGINEERING_MODE", "LOCAL").upper())


def configure_logging(level: str = "INFO") -> None:
    """One-line logging setup used by every project."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
               "<level>{message}</level>",
    )


@lru_cache(maxsize=1)
def get_boto_session():
    """Cached boto3 session — only imported in AWS mode."""
    import boto3
    return boto3.Session(region_name=os.getenv("AWS_REGION", "us-east-1"))


def aws_client(service: str) -> Any:
    """Get an AWS client for the given service."""
    return get_boto_session().client(service)


def project_root(marker: str = "Makefile") -> Path:
    """Find the project root by walking up from cwd."""
    p = Path.cwd().resolve()
    for parent in [p, *p.parents]:
        if (parent / marker).exists():
            return parent
    return p


class CostTracker:
    """In-memory cost tracker for demo purposes.

    In production, this would be replaced by a proper observability
    pipeline emitting to CloudWatch Metrics or a custom telemetry sink.
    """

    # Indicative pricing per 1K tokens (USD, as of 2024-2025)
    PRICING = {
        "claude-3-5-sonnet": {"in": 0.003, "out": 0.015},
        "claude-3-haiku": {"in": 0.00025, "out": 0.00125},
        "titan-embed-v2": {"in": 0.00002, "out": 0.0},
        "llama-3-1-8b": {"in": 0.00022, "out": 0.00022},
    }

    def __init__(self):
        self.events: list[dict] = []

    def record(self, model: str, in_tokens: int, out_tokens: int = 0) -> float:
        p = self.PRICING.get(model, {"in": 0.0, "out": 0.0})
        cost = (in_tokens / 1000) * p["in"] + (out_tokens / 1000) * p["out"]
        self.events.append({
            "model": model,
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
            "cost_usd": cost,
        })
        return cost

    @property
    def total_usd(self) -> float:
        return sum(e["cost_usd"] for e in self.events)

    def summary(self) -> dict:
        from collections import defaultdict
        by_model = defaultdict(lambda: {"calls": 0, "in_tokens": 0, "out_tokens": 0, "cost_usd": 0.0})
        for e in self.events:
            m = by_model[e["model"]]
            m["calls"] += 1
            m["in_tokens"] += e["in_tokens"]
            m["out_tokens"] += e["out_tokens"]
            m["cost_usd"] += e["cost_usd"]
        return {"total_usd": self.total_usd, "by_model": dict(by_model)}
