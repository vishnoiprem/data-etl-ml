"""Q15: Getting Started with AWS Lambda.

A beginner-friendly Lambda handler. Six "test events" map to six small
operations so the lab user can build a function, deploy, invoke, and
read CloudWatch Logs to see what their code did.

How to Think:
- One Lambda, one handler, many test events. The handler dispatches on
  a small "operation" key the test event provides. This is the canonical
  Lambda shape: thin router, real work in helpers. Anything past ~80
  lines in the handler itself is a smell -- split it out.
- Every branch logs at INFO. CloudWatch picks it up. The lab's "follow
  the print output into CloudWatch Logs" step is exactly that.
- Returning a dict is the standard for the API Gateway integration
  response shape. For direct invocations we just return whatever; the
  test console renders it.

The trap:
- Lambda's default timeout is 3 seconds. Anything I/O-bound (S3 list,
  DynamoDB scan) MUST be async/await or it times out. This handler is
  pure-Python and finishes in single-digit ms -- but a careless reader
  would copy the shape into a real data pipeline and forget the async
  conversion.
- Logger is created at MODULE level, not inside the handler. Creating
  it inside the handler makes every cold start pay an extra import
  cost. Standard Lambda pattern: module-level `LOG = logging.getLogger()`.

AWS note:
- The execution role (LambdaIntroLabRole-…) provides CloudWatch Logs
  write permissions. Without it, the LOG.info() lines would still
  print to stdout but never reach CloudWatch.
"""
from __future__ import annotations

import json
import logging
import math
import os
from typing import Any, Dict

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

# Lab environment often injects useful env-vars. Document the ones we read.
LOG_PREFIX = os.environ.get("LOG_PREFIX", "[Q15]")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Route by ``event["operation"]``. Default = greet.

    Supported operations (matched on event["operation"]):
      greet      -> {"message": "Hello, <name>!"}
      factorial  -> {"n": N, "result": N!}
      echo       -> the whole event, returned verbatim
      schedule   -> {"source": "aws.events", "rule": <name>}
      apigw      -> {"statusCode": 200, "body": "..."} (API GW integration)
      error      -> raises ValueError; tests the failure path

    Any other operation -> returns {"echo": event, "warning": "unknown op"}.
    """
    op = event.get("operation", "greet")
    LOG.info("%s received operation=%s event_keys=%s",
             LOG_PREFIX, op, list(event.keys()))

    if op == "greet":
        return _greet(event)
    if op == "factorial":
        return _factorial(event)
    if op == "echo":
        return event
    if op == "schedule":
        return _schedule(event)
    if op == "apigw":
        return _apigw(event)
    if op == "error":
        return _raise_error(event)

    LOG.warning("%s unknown operation=%s", LOG_PREFIX, op)
    return {"echo": event, "warning": f"unknown operation: {op!r}"}


# ---------------------------------------------------------------- operations
def _greet(event: Dict[str, Any]) -> Dict[str, Any]:
    name = event.get("name", "world")
    msg  = f"Hello, {name}!"
    LOG.info("%s greet name=%s -> %s", LOG_PREFIX, name, msg)
    return {"message": msg, "name": name}


def _factorial(event: Dict[str, Any]) -> Dict[str, Any]:
    n = int(event.get("n", 0))
    if n < 0:
        raise ValueError(f"factorial undefined for negative n={n}")
    if n > 20:
        # 21! exceeds 64-bit int range. Lab trap: silently overflows.
        raise ValueError(f"factorial too large for n={n}; cap at 20")
    result = math.factorial(n)
    LOG.info("%s factorial n=%d result=%d", LOG_PREFIX, n, result)
    return {"n": n, "result": result}


def _schedule(event: Dict[str, Any]) -> Dict[str, Any]:
    """EventBridge / EventBridge Scheduler payload shape."""
    return {
        "source": event.get("source", "aws.events"),
        "rule":   event.get("resources", ["<rule>"])[0],
        "time":   event.get("time", "<iso-8601>"),
    }


def _apigw(event: Dict[str, Any]) -> Dict[str, Any]:
    """API Gateway proxy integration response shape."""
    name = event.get("queryStringParameters", {}).get("name", "world")
    return {
        "statusCode": 200,
        "headers":    {"Content-Type": "application/json"},
        "body":       json.dumps({"message": f"Hello, {name}!"}),
    }


def _raise_error(event: Dict[str, Any]) -> Dict[str, Any]:
    """Deliberately fail. Lab stage 5 inspects the failure in CloudWatch."""
    msg = event.get("message", "no message supplied")
    LOG.error("%s raising ValueError(msg=%s)", LOG_PREFIX, msg)
    raise ValueError(msg)
