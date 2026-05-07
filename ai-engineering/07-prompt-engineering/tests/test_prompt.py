from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.context import Chunk, pack_context
from src.experiments import BayesianAB, Variant
from src.registry import PromptVersion, Registry
from src.templates import Template


def test_template_renders_with_filter():
    t = Template("greet", "hi {{ name | upper }}")
    assert t.render(name="alice") == "hi ALICE"


def test_template_missing_var_raises():
    t = Template("greet", "hi {{ name }}")
    with pytest.raises(KeyError):
        t.render()


def test_registry_register_promote_render():
    with tempfile.TemporaryDirectory() as td:
        reg = Registry(path=Path(td) / "r.json")
        v = PromptVersion.of("p1", "say {{ x }}")
        reg.register(v)
        reg.promote("p1", v.content_hash, "prod")
        assert reg.render("p1", "prod", x="hello") == "say hello"


def test_registry_rollback():
    with tempfile.TemporaryDirectory() as td:
        reg = Registry(path=Path(td) / "r.json")
        v1 = PromptVersion.of("p1", "v1: {{ x }}")
        v2 = PromptVersion.of("p1", "v2: {{ x }}")
        reg.register(v1); reg.register(v2)
        reg.promote("p1", v1.content_hash, "prod")
        reg.promote("p1", v2.content_hash, "prod")
        assert reg.render("p1", "prod", x="z").startswith("v2:")
        reg.rollback("p1", "prod", v1.content_hash)
        assert reg.render("p1", "prod", x="z").startswith("v1:")


def test_bayesian_ab_detects_clear_winner():
    a = Variant("a", successes=30, failures=70)
    b = Variant("b", successes=70, failures=30)
    ab = BayesianAB(a, b)
    assert ab.posterior_prob_b_better() > 0.99
    assert ab.decide() == "ship_b"


def test_context_pack_drops_when_over_budget():
    chunks = [Chunk(f"c{i}", "word " * 50, score=1.0 - i * 0.1) for i in range(5)]
    pack = pack_context(chunks, budget_tokens=200, reserved_tokens=0)
    assert pack.used_tokens <= 200
    assert len(pack.dropped) > 0
