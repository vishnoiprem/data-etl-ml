"""test_get_default_router.py — the env-var fallback chain.

`get_default_router()` (in src/router.py) decides which router to
use at runtime:
  1. Try AnthropicRouter
  2. Fall back to OpenAIRouter
  3. Fall back to StubRouter

The routers read API keys implicitly from the SDK constructors
(anthropic.Anthropic() and openai.OpenAI()), which look at
ANTHROPIC_API_KEY and OPENAI_API_KEY. If neither SDK is
installed, the import fails and the next is tried.

These tests mock the router classes so they don't need the real
SDKs installed and don't hit the network. The test of "real
SDK + real key" is the CI smoke test (CI does not run; this
test file replaces it).
"""

from __future__ import annotations

import importlib
import sys

import pytest


@pytest.fixture
def fresh_router(monkeypatch):
    """Force a fresh import of `router` so env-var / module changes
    take effect, and clean up env vars that influence the chain."""
    for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "HUSTLE_LLM_PROVIDER"):
        monkeypatch.delenv(var, raising=False)
    # Drop any cached imports so a stale router module from a
    # previous test doesn't shadow the new env.
    for mod in [m for m in list(sys.modules) if m.startswith("router")]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    import router  # noqa: F401  -- re-import after env change
    return importlib.import_module("router")


# ---------------------------------------------------------------- happy path

def test_returns_stub_when_no_sdks_available(fresh_router, monkeypatch):
    """No SDKs installed (or they raise) → StubRouter.

    Simulates the 'I just cloned this and ran make demo' state:
    no env vars, no anthropic / openai packages.
    """
    class _Broken:
        def __init__(self, *a, **kw):
            raise ImportError("sdk not installed")

    monkeypatch.setattr(fresh_router, "AnthropicRouter", _Broken)
    monkeypatch.setattr(fresh_router, "OpenAIRouter", _Broken)

    r = fresh_router.get_default_router()
    assert isinstance(r, fresh_router.StubRouter)
    assert r.name == "stub"


def test_anthropic_wins_when_available(fresh_router, monkeypatch):
    """If AnthropicRouter constructs without error, it's picked
    over OpenAI. (The SDK reads ANTHROPIC_API_KEY; we just
    simulate 'SDK installed + key set' as 'constructor succeeds'.)"""
    class _AnthropicFake:
        name = "anthropic"
        def __init__(self, *a, **kw): pass

    class _OpenAIFake:
        def __init__(self, *a, **kw):
            raise RuntimeError("should not be called")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(fresh_router, "AnthropicRouter", _AnthropicFake)
    monkeypatch.setattr(fresh_router, "OpenAIRouter", _OpenAIFake)

    r = fresh_router.get_default_router()
    assert r.name == "anthropic"


def test_openai_used_when_anthropic_unavailable(fresh_router, monkeypatch):
    """Anthropic constructor raises → fall through to OpenAI."""
    class _AnthropicBroken:
        def __init__(self, *a, **kw):
            raise ImportError("anthropic sdk missing")

    class _OpenAIFake:
        name = "openai"
        def __init__(self, *a, **kw): pass

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(fresh_router, "AnthropicRouter", _AnthropicBroken)
    monkeypatch.setattr(fresh_router, "OpenAIRouter", _OpenAIFake)

    r = fresh_router.get_default_router()
    assert r.name == "openai"


def test_stub_used_when_keys_missing_even_if_sdks_install(fresh_router, monkeypatch):
    """SDK installed but no key: the SDK constructors succeed (auth is
    deferred to the first call), so the router must check the env itself
    and fall back to the stub instead of picking a router that fails on
    every request."""
    class _Constructs:
        name = "should-not-be-picked"
        def __init__(self, *a, **kw): pass

    monkeypatch.setattr(fresh_router, "AnthropicRouter", _Constructs)
    monkeypatch.setattr(fresh_router, "OpenAIRouter", _Constructs)

    r = fresh_router.get_default_router()
    assert r.name == "stub"


def test_openai_picked_when_only_openai_key_set(fresh_router, monkeypatch):
    class _Anthropic:
        name = "anthropic"
        def __init__(self, *a, **kw): pass

    class _OpenAI:
        name = "openai"
        def __init__(self, *a, **kw): pass

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(fresh_router, "AnthropicRouter", _Anthropic)
    monkeypatch.setattr(fresh_router, "OpenAIRouter", _OpenAI)

    assert fresh_router.get_default_router().name == "openai"


def test_provider_override_forces_stub(fresh_router, monkeypatch):
    """HUSTLE_LLM_PROVIDER=stub wins even when a key is set."""
    class _Anthropic:
        name = "anthropic"
        def __init__(self, *a, **kw): pass

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("HUSTLE_LLM_PROVIDER", "stub")
    monkeypatch.setattr(fresh_router, "AnthropicRouter", _Anthropic)

    assert fresh_router.get_default_router().name == "stub"


def test_stub_used_when_both_keys_missing_and_sdks_missing(fresh_router, monkeypatch):
    """The common case on a fresh clone: no SDKs, no env vars.
    `make demo` works, dashboard renders, content is template-based."""
    class _Both:
        def __init__(self, *a, **kw):
            raise ImportError("sdk missing")

    monkeypatch.setattr(fresh_router, "AnthropicRouter", _Both)
    monkeypatch.setattr(fresh_router, "OpenAIRouter", _Both)

    r = fresh_router.get_default_router()
    assert r.name == "stub"
    # And the stub actually works end-to-end.
    out = r.complete("Keyword: foo", system="You are an SEO writer.")
    assert isinstance(out, str)
    assert "foo" in out.lower() or "Foo" in out
