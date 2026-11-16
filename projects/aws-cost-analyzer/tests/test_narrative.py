"""The narrative layer.

The most important test in this file is the one that shows a router
returning complete garbage cannot change a finding. That is the
architecture's central claim, and it has to be enforced by a test
rather than by good intentions.
"""

from __future__ import annotations

import copy
import os
from unittest.mock import patch

import pytest

from aws_cost_analyzer.models import MEASURED, MODELLED, Evidence, Finding
from aws_cost_analyzer.narrative import (
    LLMError,
    OllamaRouter,
    StubRouter,
    apply_narrative,
    apply_narratives,
    build_prompt,
    get_default_router,
)


def _finding() -> Finding:
    return Finding(
        id="growth:analytics-raw:2026-10",
        detector="growth",
        title="analytics-raw grew 500%",
        severity="high",
        summary="analytics-raw cost $2,400.00 in 2026-10, up 500% from a trailing median of $400.00.",
        target="analytics-raw",
        cost_impact=2000.0,
        cost_impact_basis=MEASURED,
        savings_estimate=2000.0,
        savings_basis="modelled_from_rate_card",
        evidence=[
            Evidence(
                metric="monthly_spend",
                value=2400.0,
                unit="USD",
                source="cost_explorer",
                period="2026-10",
            ),
            Evidence(
                metric="storage_gb",
                value=5000.0,
                unit="GB",
                source="cloudwatch",
                period="2026-10",
            ),
        ],
        confidence=1.0,
        recommendation="Check whether the volume grew.",
    )


class _GarbageRouter:
    """A router that returns nonsense — and numbers, to tempt the parser."""

    name = "garbage"

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        return (
            "The bucket definitely grew by $9,999,999.99 due to a 47x increase in "
            "requests. Severity should be high. Confidence 0.99. Savings: $500,000. "
            "Just add a lifecycle rule."
        )


class TestStubRouter:
    def test_it_writes_something(self):
        prompt = build_prompt(_finding())
        assert StubRouter().complete(prompt).strip()

    def test_it_is_deterministic(self):
        prompt = build_prompt(_finding())
        router = StubRouter()
        assert router.complete(prompt) == router.complete(prompt)

    def test_an_empty_prompt_returns_empty(self):
        assert StubRouter().complete("") == ""

    def test_it_names_the_target(self):
        prompt = build_prompt(_finding())
        assert "analytics-raw" in StubRouter().complete(prompt)

    def test_it_marks_a_modelled_figure_as_modelled(self):
        finding = _finding()
        finding.cost_impact_basis = MODELLED
        text = StubRouter().complete(build_prompt(finding))
        assert "modelled" in text.lower()

    def test_it_marks_a_measured_figure_as_measured(self):
        text = StubRouter().complete(build_prompt(_finding()))
        assert "measurement" in text.lower()

    def test_it_has_a_name(self):
        assert StubRouter().name == "stub"


class TestThePrompt:
    def test_the_prompt_carries_the_finding_numbers(self):
        prompt = build_prompt(_finding())
        assert "2000.00" in prompt
        assert "analytics-raw" in prompt

    def test_the_prompt_carries_the_basis(self):
        prompt = build_prompt(_finding())
        assert "measured" in prompt

    def test_the_prompt_carries_the_evidence(self):
        prompt = build_prompt(_finding())
        assert "storage_gb" in prompt
        assert "cost_explorer" in prompt

    def test_the_prompt_carries_the_determined_recommendation(self):
        prompt = build_prompt(_finding())
        assert "Check whether the volume grew." in prompt

    def test_the_prompt_does_not_ask_the_model_for_a_number(self):
        # Asking a model for a number is how a model ends up in the
        # decision path.
        prompt = build_prompt(_finding()).lower()
        assert "what is the cost" not in prompt
        assert "compute" not in prompt
        assert "calculate" not in prompt


class TestApplyingANarrative:
    def test_the_narrative_is_attached(self):
        finding = apply_narrative(StubRouter(), _finding())
        assert finding.narrative.strip()

    def test_a_garbage_router_cannot_change_the_finding(self):
        # The architecture's central claim, enforced by a test.
        finding = _finding()
        before = copy.deepcopy(finding)

        apply_narrative(_GarbageRouter(), finding)

        assert finding.id == before.id
        assert finding.detector == before.detector
        assert finding.title == before.title
        assert finding.severity == before.severity
        assert finding.summary == before.summary
        assert finding.target == before.target
        assert finding.cost_impact == before.cost_impact
        assert finding.cost_impact_basis == before.cost_impact_basis
        assert finding.savings_estimate == before.savings_estimate
        assert finding.savings_basis == before.savings_basis
        assert finding.confidence == before.confidence
        assert finding.recommendation == before.recommendation
        assert finding.evidence == before.evidence

    def test_a_garbage_router_cannot_change_any_finding(self):
        findings = [_finding(), _finding()]
        before = [copy.deepcopy(f) for f in findings]
        apply_narratives(_GarbageRouter(), findings)
        for finding, original in zip(findings, before, strict=True):
            assert finding.cost_impact == original.cost_impact
            assert finding.severity == original.severity
            assert finding.confidence == original.confidence

    def test_the_narrative_is_where_the_garbage_lands(self):
        finding = apply_narrative(_GarbageRouter(), _finding())
        assert "9,999,999.99" in finding.narrative
        # ...and nowhere else.
        assert finding.cost_impact == 2000.0

    def test_a_failing_router_leaves_the_narrative_empty(self):
        class FailingRouter:
            name = "failing"

            def complete(self, prompt, system="", max_tokens=512):
                raise LLMError("boom")

        finding = apply_narrative(FailingRouter(), _finding())
        assert finding.narrative == ""
        assert finding.cost_impact == 2000.0

    def test_a_failing_router_does_not_sink_the_batch(self):
        class FailingRouter:
            name = "failing"

            def complete(self, prompt, system="", max_tokens=512):
                raise LLMError("boom")

        findings = [_finding(), _finding()]
        apply_narratives(FailingRouter(), findings)
        assert all(f.cost_impact == 2000.0 for f in findings)


class TestOllamaRouter:
    def test_it_has_a_name(self):
        assert OllamaRouter().name == "ollama"

    def test_it_defaults_to_a_local_host(self):
        assert OllamaRouter().host == "http://localhost:11434"

    def test_an_unreachable_server_raises(self):
        router = OllamaRouter(host="http://127.0.0.1:9")
        with pytest.raises(LLMError):
            router.complete("ping")


class TestSelection:
    def test_the_default_is_the_stub(self):
        with patch.dict(os.environ, {}, clear=True):
            assert isinstance(get_default_router(), StubRouter)

    def test_an_unreachable_ollama_falls_back_to_the_stub(self):
        with patch.dict(os.environ, {"AWSCA_PROVIDER": "ollama"}, clear=True):
            assert isinstance(get_default_router(host="http://127.0.0.1:9"), StubRouter)

    def test_an_unknown_provider_falls_back_to_the_stub(self):
        with patch.dict(os.environ, {"AWSCA_PROVIDER": "openai"}, clear=True):
            assert isinstance(get_default_router(), StubRouter)

    def test_a_blank_provider_falls_back_to_the_stub(self):
        with patch.dict(os.environ, {"AWSCA_PROVIDER": "  "}, clear=True):
            assert isinstance(get_default_router(), StubRouter)

    def test_the_router_satisfies_the_protocol(self):
        from aws_cost_analyzer.narrative import LLMRouter

        assert isinstance(StubRouter(), LLMRouter)
        assert isinstance(OllamaRouter(), LLMRouter)
