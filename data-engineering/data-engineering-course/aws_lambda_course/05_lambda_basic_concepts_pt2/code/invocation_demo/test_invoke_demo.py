"""Tests for the section-5 invocation_demo handlers + driver.

The handlers are pure functions; we exercise them directly. The driver
script's `_invoke_*` helpers are tested by stubbing the boto3 client.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import types
from unittest import mock

import pytest

HERE = pathlib.Path(__file__).resolve().parent


def _load(name: str) -> types.ModuleType:
    """Load a module from a path without polluting sys.path."""
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    assert spec and spec.loader, f"cannot load {name}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _FakeContext:
    aws_request_id = "test-request-id"


# --- async_handler -----------------------------------------------------------

def test_async_handler_returns_summary() -> None:
    mod = _load("async_handler")
    out = mod.handler({"job_id": "j-1", "payload": {"k": 1}}, _FakeContext())
    assert out["job_id"] == "j-1"
    assert out["status"] == "ok"
    assert "elapsed_ms" in out


def test_async_handler_handles_missing_keys() -> None:
    mod = _load("async_handler")
    out = mod.handler({}, _FakeContext())
    assert out["job_id"] == "unknown"
    assert out["status"] == "ok"


# --- sync_handler ------------------------------------------------------------

def test_sync_handler_sums_numbers() -> None:
    mod = _load("sync_handler")
    out = mod.handler({"numbers": [1, 2, 3, 4]}, _FakeContext())
    assert out == {"sum": 10, "count": 4}


def test_sync_handler_empty_list() -> None:
    mod = _load("sync_handler")
    out = mod.handler({"numbers": []}, _FakeContext())
    assert out == {"sum": 0, "count": 0}


def test_sync_handler_rejects_non_list() -> None:
    mod = _load("sync_handler")
    with pytest.raises(TypeError):
        mod.handler({"numbers": "not a list"}, _FakeContext())


# --- invoke_demo driver ------------------------------------------------------

def test_invoke_sync_uses_request_response(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load("invoke_demo")
    fake_client = mock.MagicMock()
    fake_client.invoke.return_value = {
        "StatusCode": 200,
        "Payload": __import__("io").BytesIO(json.dumps({"sum": 15}).encode()),
    }
    monkeypatch.setattr(mod.boto3, "client", lambda *a, **kw: fake_client)
    mod._invoke_sync("my-fn")
    args, kwargs = fake_client.invoke.call_args
    assert kwargs["FunctionName"] == "my-fn"
    assert kwargs["InvocationType"] == "RequestResponse"
    assert json.loads(kwargs["Payload"].decode()) == {"numbers": [1, 2, 3, 4, 5]}


def test_invoke_async_uses_event(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load("invoke_demo")
    fake_client = mock.MagicMock()
    fake_client.invoke.return_value = {"StatusCode": 202, "Payload": __import__("io").BytesIO(b"")}
    monkeypatch.setattr(mod.boto3, "client", lambda *a, **kw: fake_client)
    mod._invoke_async("my-fn")
    args, kwargs = fake_client.invoke.call_args
    assert kwargs["FunctionName"] == "my-fn"
    assert kwargs["InvocationType"] == "Event"


def test_main_local_dispatches(capsys: pytest.CaptureFixture) -> None:
    mod = _load("invoke_demo")
    rc = mod.main(["invoke_demo.py", "local"])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"sum": 15' in out
    assert '"job_id": "demo-1"' in out


def test_main_rejects_bad_args() -> None:
    mod = _load("invoke_demo")
    assert mod.main(["invoke_demo.py"]) == 2
    assert mod.main(["invoke_demo.py", "garbage"]) == 2
