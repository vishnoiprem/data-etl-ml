"""
Q15: Getting Started with AWS Lambda   [AWS | Serverless, Lambda]

Offline driver: invoke a Lambda-style handler against the six test events
in events/ and assert the documented response shape for each one.

How to Think:
- A test event is just a JSON payload. The handler treats it as
  event["operation"] and dispatches. No AWS account needed -- direct
  invocation is "the simplest way to call Lambda," per the AWS docs.
- The handler's return is exactly what the console's Test button shows
  in the Execution result pane. That's what we assert here.

The trap:
- The default operation is ``greet`` -- an event WITHOUT ``operation``
  still produces output. Useful for the lab's "first invocation" but a
  trap if you misread the lab and forget to wire up ``factorial``.
- The ``error`` test event MUST raise. Wrapping it in try/except and
  returning a success code defeats the purpose; the lab stage "read
  CloudWatch Logs after a failure" requires an actual exception.

AWS note:
- In the real lab this runs via the console's Test button. Here we
  invoke the handler directly -- identical code path.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lambda_function"))

import app  # noqa: E402  -- import order matters


def _load_event(name: str) -> Dict[str, Any]:
    with open(os.path.join(_HERE, "events", name), encoding="utf-8") as fh:
        return json.load(fh)


def expect(title: str, got: Any, expected: Any) -> None:
    if got != expected:
        print(f"[FAIL] {title}")
        print(f"   expected: {expected}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")


def main() -> None:
    ctx = type("Ctx", (), {
        "function_name":    "HelloLambdaFunction",
        "memory_limit_in_mb": 128,
        "aws_request_id":   "test-request-0001",
        "get_remaining_time_in_ms": lambda: 10000,
    })()

    print("\n=== Q15 Getting Started with AWS Lambda ===\n")

    # Stage 1: greet -- the canonical first Lambda invocation
    out = app.lambda_handler(_load_event("01_greet.json"), ctx)
    expect("Q15 stage 1 greet",
           out, {"message": "Hello, Vishnoi!", "name": "Vishnoi"})

    # Stage 2: factorial -- 6! = 720
    out = app.lambda_handler(_load_event("02_factorial.json"), ctx)
    expect("Q15 stage 2 factorial(6)", out, {"n": 6, "result": 720})

    # Stage 3: echo -- handler returns the event verbatim
    ev = _load_event("03_echo.json")
    out = app.lambda_handler(ev, ctx)
    expect("Q15 stage 3 echo", out, ev)

    # Stage 4: schedule -- EventBridge rule payload shape
    out = app.lambda_handler(_load_event("04_schedule.json"), ctx)
    expect("Q15 stage 4 schedule",
           out, {"source": "aws.events",
                 "rule":   "arn:aws:events:us-east-1:123456789012:rule/HelloLambdaEvery5Min",
                 "time":   "2026-09-27T08:00:00Z"})

    # Stage 5: apigw -- the proxy integration response shape
    out = app.lambda_handler(_load_event("05_apigw.json"), ctx)
    assert out["statusCode"] == 200, out
    body = json.loads(out["body"])
    assert body == {"message": "Hello, Vishnoi!"}, body
    assert out["headers"]["Content-Type"] == "application/json"
    print("[PASS] Q15 stage 5 apigw -- statusCode=200, body has correct message")

    # Stage 6: error -- the handler MUST raise. lab inspects CloudWatch.
    err_event = _load_event("06_error.json")
    try:
        app.lambda_handler(err_event, ctx)
    except ValueError as e:
        assert str(e) == "intentional failure to inspect CloudWatch Logs", e
        print(f"[PASS] Q15 stage 6 error -- raised ValueError({e!s})")
    else:
        raise AssertionError("Q15 stage 6: handler swallowed the error")

    # Bonus: default operation is greet when no operation key is present
    out = app.lambda_handler({"name": "world"}, ctx)
    expect("Q15 default operation -> greet(\"world\")",
           out, {"message": "Hello, world!", "name": "world"})

    # Bonus: unknown operation echoes the event with a warning
    out = app.lambda_handler({"operation": "weird", "x": 1}, ctx)
    assert out["warning"].startswith("unknown operation"), out
    assert out["echo"] == {"operation": "weird", "x": 1}, out
    print("[PASS] Q15 unknown operation echoes the event with a warning")

    # Bonus: factorial negative -- raises (lab stage 6 also covers errors)
    try:
        app.lambda_handler({"operation": "factorial", "n": -1}, ctx)
    except ValueError as e:
        assert "negative" in str(e), e
        print("[PASS] Q15 factorial(-1) raises ValueError")
    else:
        raise AssertionError("Q15: factorial(-1) should have raised")

    print("\n=== All Q15 stages pass ===\n")


if __name__ == "__main__":
    main()
