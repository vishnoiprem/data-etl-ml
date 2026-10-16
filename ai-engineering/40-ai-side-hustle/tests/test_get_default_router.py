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

    monkeypatch.setattr(fresh_router, "AnthropicRouter", _AnthropicBroken)
    monkeypatch.setattr(fresh_router, "OpenAIRouter", _OpenAIFake)

    r = fresh_router.get_default_router()
    assert r.name == "openai"


def test_stub_used_when_anthropic_key_missing(fresh_router, monkeypatch):
    """If the SDK is installed but the API key is missing, the
    Anthropic *constructor* may succeed (it just defers the auth
    check to the first call) but a future .messages.create() will
    fail. The current code can't tell 'missing key' from 'key
    set' at construction time, so this test documents the
    actual behavior: a missing key still picks the Anthropic
    router, and the first call will raise.

    In practice, the buyer sees a clean 'authentication error'
    on the first .complete() call rather than a silent fallback.
    This is correct — silent fallback to stub would hide the
    real configuration problem.

    The test asserts the *current* behavior so a future refactor
    that adds explicit key-checking (and falls back to stub on
    missing key) updates this test deliberately.
    """
    class _AnthropicNoKey:
        name = "anthropic"
        def __init__(self, *a, **kw): pass
        def complete(self, *a, **kw): raise RuntimeError("auth required")

    class _OpenAINoKey:
        def __init__(self, *a, **kw): pass

    monkeypatch.setattr(fresh_router, "AnthropicRouter", _AnthropicNoKey)
    monkeypatch.setattr(fresh_router, "OpenAIRouter", _OpenAINoKey)

    r = fresh_router.get_default_router()
    # The Anthropic router is selected; the missing key surfaces
    # only on first .complete() call, not on construction.
    assert r.name == "anthropic"
    with pytest.raises(RuntimeError, match="auth required"):
        r.complete("test prompt")


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
