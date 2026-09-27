"""Offline pytest for the Lambda intro handler -- no AWS credentials required."""
from __future__ import annotations

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "lambda_function"))

import app  # noqa: E402


@pytest.fixture
def ctx():
    """Minimal stand-in for the AWS Lambda context object."""

    class _Ctx:
        function_name = "HelloLambdaFunction"
        memory_limit_in_mb = 128
        aws_request_id = "test-id"
        invoked_function_arn = "arn:aws:lambda:test"

        def get_remaining_time_in_millis(self):  # AWS uses millis
            return 10000

    return _Ctx()


# ============================================================== tests
def test_greet_uses_provided_name(ctx) -> None:
    out = app.lambda_handler({"operation": "greet", "name": "Vishnoi"}, ctx)
    assert out == {"message": "Hello, Vishnoi!", "name": "Vishnoi"}


def test_greet_defaults_to_world_when_name_missing(ctx) -> None:
    out = app.lambda_handler({"operation": "greet"}, ctx)
    assert out == {"message": "Hello, world!", "name": "world"}


def test_default_operation_is_greet(ctx) -> None:
    """No operation key -> greet with default name."""
    out = app.lambda_handler({}, ctx)
    assert out == {"message": "Hello, world!", "name": "world"}


def test_factorial_handles_small_inputs(ctx) -> None:
    assert app.lambda_handler({"operation": "factorial", "n": 0},  ctx) == {"n": 0, "result": 1}
    assert app.lambda_handler({"operation": "factorial", "n": 1},  ctx) == {"n": 1, "result": 1}
    assert app.lambda_handler({"operation": "factorial", "n": 5},  ctx) == {"n": 5, "result": 120}
    assert app.lambda_handler({"operation": "factorial", "n": 10}, ctx) == {"n": 10, "result": 3628800}


def test_factorial_rejects_negative(ctx) -> None:
    with pytest.raises(ValueError, match="negative"):
        app.lambda_handler({"operation": "factorial", "n": -1}, ctx)


def test_factorial_rejects_overflow_past_20(ctx) -> None:
    """20! is the largest factorial that fits in 64-bit int."""
    with pytest.raises(ValueError, match="too large"):
        app.lambda_handler({"operation": "factorial", "n": 21}, ctx)


def test_echo_returns_event_verbatim(ctx) -> None:
    event = {"operation": "echo", "note": "x", "k": 7}
    assert app.lambda_handler(event, ctx) is event


def test_apigw_returns_proxy_integration_shape(ctx) -> None:
    out = app.lambda_handler(
        {"operation": "apigw",
         "queryStringParameters": {"name": "Lambda"}},
        ctx,
    )
    assert out["statusCode"] == 200
    assert out["headers"]["Content-Type"] == "application/json"
    import json as _json
    assert _json.loads(out["body"]) == {"message": "Hello, Lambda!"}


def test_error_event_raises_value_error(ctx) -> None:
    """The lab stage 5 expects a real exception, not a swallowed one."""
    with pytest.raises(ValueError, match="intentional failure"):
        app.lambda_handler({"operation": "error", "message": "intentional failure"}, ctx)


def test_unknown_operation_warns_and_echoes(ctx) -> None:
    out = app.lambda_handler({"operation": "weird", "x": 1}, ctx)
    assert out["echo"] == {"operation": "weird", "x": 1}
    assert "warning" in out and out["warning"].startswith("unknown operation")
