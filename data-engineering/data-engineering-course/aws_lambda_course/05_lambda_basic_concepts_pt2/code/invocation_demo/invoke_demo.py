"""Hands-on companion to L21 in section 5.

Demonstrates the two main invocation models from a client point of view:

1. **Synchronous** — `invoke(InvocationType='RequestResponse')` blocks
   until Lambda returns; the response payload is in `Payload`.
2. **Asynchronous** — `invoke(InvocationType='Event')` returns a 202
   immediately; Lambda discards the function's return value.

The script can be run two ways:

* Locally (no AWS):  `python invoke_demo.py local`
* Against real AWS:  `python invoke_demo.py sync|async <function-name>`

Requires:
    boto3 >= 1.34
"""
from __future__ import annotations

import json
import os
import sys

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
PAYLOAD_SYNC = {"numbers": [1, 2, 3, 4, 5]}
PAYLOAD_ASYNC = {"job_id": "demo-1", "payload": {"records": [1, 2, 3]}}


def _local_demo() -> None:
    """Run the handlers in-process so the student can see both return values."""
    from async_handler import handler as async_handler  # type: ignore
    from sync_handler import handler as sync_handler  # type: ignore

    class _Ctx:
        aws_request_id = "local"

    print("=== local sync ===")
    print(json.dumps(sync_handler(PAYLOAD_SYNC, _Ctx()), indent=2))
    print("=== local async (return value is discarded by Lambda) ===")
    print(json.dumps(async_handler(PAYLOAD_ASYNC, _Ctx()), indent=2))


def _invoke_sync(function_name: str) -> None:
    client = boto3.client("lambda", region_name=REGION)
    resp = client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(PAYLOAD_SYNC).encode("utf-8"),
    )
    print(f"StatusCode: {resp['StatusCode']}")
    payload = resp["Payload"].read().decode("utf-8")
    print(f"Payload:    {payload}")


def _invoke_async(function_name: str) -> None:
    client = boto3.client("lambda", region_name=REGION)
    resp = client.invoke(
        FunctionName=function_name,
        InvocationType="Event",
        Payload=json.dumps(PAYLOAD_ASYNC).encode("utf-8"),
    )
    print(f"StatusCode: {resp['StatusCode']}  (Lambda returns 202 immediately)")
    print("Payload is empty — Lambda discarded the function's return value.")


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "local":
        _local_demo()
        return 0
    if len(argv) < 3 or argv[1] not in {"sync", "async"}:
        print("usage: invoke_demo.py local | sync <fn> | async <fn>", file=sys.stderr)
        return 2
    if argv[1] == "sync":
        _invoke_sync(argv[2])
    else:
        _invoke_async(argv[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
