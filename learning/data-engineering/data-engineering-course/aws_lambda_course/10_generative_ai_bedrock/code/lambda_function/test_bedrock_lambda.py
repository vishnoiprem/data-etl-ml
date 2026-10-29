"""
test_bedrock_lambda.py
======================

Unit tests for the Bedrock defect-summarizer Lambda.

We deliberately do **not** depend on `moto` for Bedrock — moto added
partial Bedrock support in 5.0 but the `bedrock-runtime:InvokeModel`
API surface is still under-mocked, and the `cohere.command-text-v14`
model ID is not in moto's catalogue.

Instead we inject a tiny stub client that satisfies the interface our
handler uses (`invoke_model(**kwargs) -> {"body": readable stream}`).
This makes the suite hermetic and CI-friendly.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import sys
import types
from typing import Any

import pytest

HERE = pathlib.Path(__file__).resolve().parent
CODE_DIR = HERE.parent
sys.path.insert(0, str(HERE))


# ─────────────────────────────────────────────────────────────────────────────
# Test fixtures
# ─────────────────────────────────────────────────────────────────────────────

class _StubBody:
    """Mimics botocore's StreamingBody for the response['body'] field."""

    def __init__(self, payload: dict[str, Any]):
        self._buf = io.BytesIO(json.dumps(payload).encode("utf-8"))

    def read(self) -> bytes:
        return self._buf.read()


class _StubBedrockClient:
    """A minimal stub of the bedrock-runtime client used by the handler."""

    def __init__(self, payload: dict[str, Any] | None = None, fail: bool = False):
        self._payload = payload or {
            "generations": [
                {
                    "text": json.dumps(
                        {
                            "summary": "Stamping press #2 producing 2 mm burr on flange.",
                            "category": "mechanical",
                            "severity": "high",
                        }
                    )
                }
            ]
        }
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def invoke_model(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.fail:
            from botocore.exceptions import ClientError

            raise ClientError(
                {"Error": {"Code": "AccessDeniedException", "Message": "no access"}},
                "InvokeModel",
            )
        return {"body": _StubBody(self._payload)}


@pytest.fixture()
def stub_client() -> _StubBedrockClient:
    return _StubBedrockClient()


@pytest.fixture()
def handler(monkeypatch, stub_client):
    """Import the handler fresh and patch the Bedrock client factory."""
    # Force a fresh import in case pytest already cached the module.
    sys.modules.pop("bedrock_lambda", None)
    spec = importlib.util.spec_from_file_location("bedrock_lambda", HERE / "bedrock_lambda.py")
    assert spec and spec.loader, "could not load bedrock_lambda.py"
    mod = importlib.util.module_from_spec(spec)
    # Register in sys.modules so dataclass introspection can find it.
    sys.modules["bedrock_lambda"] = mod
    spec.loader.exec_module(mod)

    # Reset the module-level cache so the stub is used.
    mod._bedrock_client_cache.clear()
    monkeypatch.setattr(
        mod,
        "_get_bedrock_client",
        lambda region: stub_client,
    )
    return mod


# ─────────────────────────────────────────────────────────────────────────────
# Prompt construction
# ─────────────────────────────────────────────────────────────────────────────

def test_build_prompt_includes_user_text(handler):
    prompt = handler._build_prompt("press #2 coolant leak")
    assert "press #2 coolant leak" in prompt
    assert "{user}" not in prompt  # placeholder must be substituted


def test_prompt_template_file_exists_and_has_placeholder():
    path = CODE_DIR / "prompt_template.txt"
    assert path.exists(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "{user}" in text


# ─────────────────────────────────────────────────────────────────────────────
# Event validation
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_defect_text_accepts_top_level_key(handler):
    assert handler._extract_defect_text({"defect_description": "x"}) == "x"


def test_extract_defect_text_accepts_stringified_body(handler):
    event = {"body": json.dumps({"defect_description": "x"})}
    assert handler._extract_defect_text(event) == "x"


def test_extract_defect_text_accepts_dict_body(handler):
    event = {"body": {"defect_description": "x"}}
    assert handler._extract_defect_text(event) == "x"


def test_extract_defect_text_rejects_missing_field(handler):
    with pytest.raises(handler.ValidationError):
        handler._extract_defect_text({})


def test_extract_defect_text_rejects_invalid_json_body(handler):
    with pytest.raises(handler.ValidationError):
        handler._extract_defect_text({"body": "{not json"})


# ─────────────────────────────────────────────────────────────────────────────
# Model-output parsing
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_model_json_strips_fences(handler):
    text = "```json\n" + json.dumps({"summary": "ok", "category": "mechanical", "severity": "low"}) + "\n```"
    out = handler._parse_model_json(text)
    assert out["summary"] == "ok"


def test_parse_model_json_handles_embedded_object(handler):
    text = "Here you go: " + json.dumps({"summary": "s", "category": "c", "severity": "x"})
    out = handler._parse_model_json(text)
    assert out["summary"] == "s"


def test_parse_model_json_raises_on_garbage(handler):
    with pytest.raises(RuntimeError):
        handler._parse_model_json("no json at all")


# ─────────────────────────────────────────────────────────────────────────────
# Output normalization
# ─────────────────────────────────────────────────────────────────────────────

def test_normalize_category_accepts_known_values(handler):
    for c in handler.ALLOWED_CATEGORIES:
        assert handler._normalize_category(c) == c


def test_normalize_category_maps_synonyms(handler):
    assert handler._normalize_category("Mech") == "mechanical"
    assert handler._normalize_category("wiring") == "electrical"
    assert handler._normalize_category("hydraulic") == "pneumatic"
    assert handler._normalize_category("???") == "other"


def test_normalize_severity_accepts_known_values(handler):
    for s in handler.ALLOWED_SEVERITIES:
        assert handler._normalize_severity(s) == s


def test_normalize_severity_maps_synonyms(handler):
    assert handler._normalize_severity("5") == "critical"
    assert handler._normalize_severity("Urgent") == "high"
    assert handler._normalize_severity("??") == "medium"


def test_normalize_output_fills_missing_summary(handler):
    out = handler._normalize_output({"category": "mechanical", "severity": "high"})
    assert "Defect reported" in out["summary"]


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end handler
# ─────────────────────────────────────────────────────────────────────────────

def test_lambda_handler_happy_path(handler, stub_client):
    event = {"defect_description": "press #2 coolant leak"}
    resp = handler.lambda_handler(event, context=None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert set(body.keys()) == {"summary", "category", "severity"}
    assert body["category"] in handler.ALLOWED_CATEGORIES
    assert body["severity"] in handler.ALLOWED_SEVERITIES
    # Stub returned "mechanical"/"high".
    assert body["category"] == "mechanical"
    assert body["severity"] == "high"
    # Verify the handler actually invoked the Bedrock client.
    assert len(stub_client.calls) == 1
    assert stub_client.calls[0]["modelId"] == "cohere.command-text-v14"


def test_lambda_handler_truncates_long_input(handler, stub_client):
    long_text = "x" * 10_000
    event = {"defect_description": long_text}
    resp = handler.lambda_handler(event, context=None)
    assert resp["statusCode"] == 200
    # The model receives the truncated text in the request body.
    body_arg = stub_client.calls[0]["body"]
    decoded = json.loads(body_arg.decode("utf-8"))
    assert len(decoded["prompt"]) < len(long_text)


def test_lambda_handler_returns_400_on_empty(handler):
    resp = handler.lambda_handler({"defect_description": "   "}, context=None)
    assert resp["statusCode"] == 400


def test_lambda_handler_returns_400_on_missing_field(handler):
    resp = handler.lambda_handler({}, context=None)
    assert resp["statusCode"] == 400


def test_lambda_handler_returns_502_on_bedrock_error(handler, monkeypatch):
    failing = _StubBedrockClient(fail=True)
    monkeypatch.setattr(handler, "_get_bedrock_client", lambda region: failing)
    handler._bedrock_client_cache.clear()
    resp = handler.lambda_handler({"defect_description": "x"}, context=None)
    assert resp["statusCode"] == 502


def test_lambda_handler_uses_env_var_model_id(handler, monkeypatch, stub_client):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "cohere.command-r-plus-v1:0")
    resp = handler.lambda_handler({"defect_description": "x"}, context=None)
    assert resp["statusCode"] == 200
    assert stub_client.calls[0]["modelId"] == "cohere.command-r-plus-v1:0"


# ─────────────────────────────────────────────────────────────────────────────
# Sample defects sanity
# ─────────────────────────────────────────────────────────────────────────────

def test_sample_defects_file_is_valid_json():
    path = CODE_DIR / "sample_defects.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 3
    for d in data:
        assert "defect_description" in d
        assert isinstance(d["defect_description"], str)
