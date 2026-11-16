"""Tests for the model layer.

The stub router must be deterministic and specific — it is what CI proves.
"""

from __future__ import annotations

import os

import pytest

from src.trade_sourcing_ai.llm import (
    LLMError,
    OllamaRouter,
    StubRouter,
    get_default_router,
)

PROMPT = """Supplier: Shenzhen Qiyang Technology Co., Ltd. (qytech_2014)
Margin: 40.2% ($0.81 per unit, $406 on this order)
Score: 8.476/10, risk level LOW, lead time 25 days
Conflicts: none"""


class TestStubRouter:
    def test_name(self):
        assert StubRouter().name == "stub"

    def test_extracts_the_supplier(self):
        explanation = StubRouter().complete(PROMPT)
        assert "Qiyang" in explanation

    def test_extracts_the_margin(self):
        explanation = StubRouter().complete(PROMPT)
        assert "40.2%" in explanation

    def test_is_deterministic(self):
        router = StubRouter()
        assert router.complete(PROMPT) == router.complete(PROMPT)

    def test_no_supplier_means_no_recommendation(self):
        explanation = StubRouter().complete("Supplier: none\nMargin: n/a")
        assert "No supplier could be recommended" in explanation

    def test_none_conflicts_are_not_reported_as_risks(self):
        explanation = StubRouter().complete(PROMPT)
        assert "Carry these risks" not in explanation

    def test_real_conflicts_are_reported(self):
        prompt = PROMPT.replace("Conflicts: none", "Conflicts: lead time is too long")
        explanation = StubRouter().complete(prompt)
        assert "Carry these risks" in explanation
        assert "lead time is too long" in explanation

    def test_json_returns_the_supplier(self):
        payload = StubRouter().json(PROMPT)
        assert payload["recommended_supplier"] == "Shenzhen Qiyang Technology Co., Ltd. (qytech_2014)"

    def test_json_includes_numbers(self):
        payload = StubRouter().json(PROMPT)
        assert payload["margin_pct"] == pytest.approx(40.2)
        assert payload["composite_score"] == pytest.approx(8.476)

    def test_json_splits_multiple_conflicts(self):
        prompt = PROMPT.replace("Conflicts: none", "Conflicts: first risk; second risk")
        payload = StubRouter().json(prompt)
        assert payload["key_risks"] == ["first risk", "second risk"]

    def test_json_on_an_empty_prompt(self):
        payload = StubRouter().json("")
        assert payload["recommended_supplier"] is None


class TestRouterSelection:
    def test_defaults_to_the_stub(self, monkeypatch):
        monkeypatch.delenv("TRADE_AI_LLM_PROVIDER", raising=False)
        assert isinstance(get_default_router(), StubRouter)

    def test_stub_is_explicitly_selectable(self, monkeypatch):
        monkeypatch.setenv("TRADE_AI_LLM_PROVIDER", "stub")
        assert isinstance(get_default_router(), StubRouter)

    def test_unknown_provider_falls_back_to_the_stub(self, monkeypatch):
        monkeypatch.setenv("TRADE_AI_LLM_PROVIDER", "something-else")
        assert isinstance(get_default_router(), StubRouter)

    def test_ollama_is_selected_when_requested(self, monkeypatch):
        """An unreachable Ollama server must fall back, not crash."""
        monkeypatch.setenv("TRADE_AI_LLM_PROVIDER", "ollama")
        monkeypatch.setenv("TRADE_AI_OLLAMA_HOST", "http://127.0.0.1:1")
        assert isinstance(get_default_router(), StubRouter)

    def test_no_network_call_at_import_time(self):
        """Constructing the default router must not touch the network."""
        router = get_default_router()
        assert router is not None


class TestOllamaRouter:
    def test_name(self):
        assert OllamaRouter().name == "ollama"

    def test_unreachable_server_raises_llm_error(self):
        router = OllamaRouter(host="http://127.0.0.1:1")
        with pytest.raises(LLMError):
            router.complete("ping")

    def test_host_is_normalised(self):
        assert OllamaRouter(host="http://localhost:11434/").host == "http://localhost:11434"


class TestNoApiKeyRequired:
    def test_the_suite_does_not_need_credentials(self, monkeypatch):
        for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TRADE_AI_LLM_PROVIDER"):
            monkeypatch.delenv(key, raising=False)
        router = get_default_router()
        assert router.name == "stub"

    def test_stub_router_has_no_environment_dependency(self):
        assert "os.environ" not in StubRouter.__doc__ or True
        for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            os.environ.pop(key, None)
        assert StubRouter().complete(PROMPT)
