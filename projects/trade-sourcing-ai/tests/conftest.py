"""Shared fixtures.

Every test runs against the real trade-finder data with the stub router, so
the suite is hermetic: no API key, no network, no Docker.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUOTES_PATH = PROJECT_ROOT / "data" / "quotes.json"


@pytest.fixture(scope="session")
def quotes_payload() -> dict:
    return json.loads(QUOTES_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def all_quote_dicts(quotes_payload) -> list[dict]:
    return quotes_payload["quotes"]


@pytest.fixture(scope="session")
def primary_quote_dicts(all_quote_dicts) -> list[dict]:
    """The three viable phone-case quotes."""
    return [q for q in all_quote_dicts if q["product"] == "phone case silicone"]


@pytest.fixture(scope="session")
def unviable_quote_dicts(all_quote_dicts) -> list[dict]:
    """The two compression-sock quotes priced at watch level."""
    return [q for q in all_quote_dicts if q["product"] == "compression socks"]


@pytest.fixture(scope="session")
def documents():
    from src.trade_sourcing_ai.corpus import build_corpus

    return build_corpus()


@pytest.fixture(scope="session")
def retriever(documents):
    """A lexical-only retriever. Dense would download a model in CI."""
    from src.trade_sourcing_ai.retrieval import HybridRetriever

    return HybridRetriever(documents, use_dense=False)


@pytest.fixture
def service(tmp_path):
    """A fresh service with its own audit log, so tests do not interfere."""
    from src.trade_sourcing_ai.audit import AuditLog
    from src.trade_sourcing_ai.service import SourcingService

    audit = AuditLog(tmp_path / "decisions.jsonl")
    return SourcingService.create(audit=audit)
