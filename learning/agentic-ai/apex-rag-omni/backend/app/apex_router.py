"""Collection classifier + prompt template loader.

Three collections, one API. Each collection has its own prompt template.
The classifier is a lightweight keyword heuristic — production would be
a fine-tuned classifier, but we trade 1-2% accuracy for < 1ms latency.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml

Collection = Literal["hr_policies", "tech_docs", "product_docs"]


_HR_KW = {"pto", "vacation", "leave", "policy", "hr", "benefit", "401k", "parental"}
_TECH_KW = {"api", "endpoint", "deploy", "kubernetes", "docker", "service", "ci", "cd"}
_PRODUCT_KW = {"feature", "roadmap", "spec", "user", "story", "epic", "mvp"}


def classify_collection(query: str, hint: Collection | None = None) -> Collection:
    """Classify the query into one of 3 collections."""
    if hint is not None:
        return hint
    q = query.lower()
    hr = sum(1 for k in _HR_KW if k in q)
    tech = sum(1 for k in _TECH_KW if k in q)
    prod = sum(1 for k in _PRODUCT_KW if k in q)
    if tech > max(hr, prod):
        return "tech_docs"
    if prod > hr:
        return "product_docs"
    return "hr_policies"


_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def load_prompt(collection: Collection) -> dict:
    """Load the YAML prompt template for a collection."""
    path = _PROMPTS_DIR / f"{collection}.yaml"
    if not path.exists():
        # Sensible default if no template exists yet
        return {
            "system": f"You are a {collection.replace('_', ' ')} assistant. Cite [doc_N] for every claim.",
            "user_prefix": "Use the evidence below to ground every claim.",
            "citation_marker": "[doc_{i}]",
            "max_context_docs": 8,
        }
    return yaml.safe_load(path.read_text())
