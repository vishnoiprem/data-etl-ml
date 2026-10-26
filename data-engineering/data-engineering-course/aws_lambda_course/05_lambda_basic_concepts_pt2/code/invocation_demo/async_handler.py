"""Async Lambda handler used by L21 in section 5 (invocation model hands-on).

When invoked with `InvocationType=Event` (the boto3 default for the
`invoke` API when you set `InvocationType='Event'`), AWS Lambda discards
the response and the function runs in the background. This handler logs
the event and returns a minimal 202-style acknowledgement.

For the synchronous counterpart see `sync_handler.py`.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

LOGGER = logging.getLogger()
if not LOGGER.handlers:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Async-style handler.

    The `event` payload usually carries a job id and a payload. We log
    both, sleep briefly to simulate work, and return a status summary.

    Note: when invoked with `InvocationType=Event`, Lambda discards this
    return value; it's purely a courtesy for the local `__main__` block.
    """
    job_id = event.get("job_id", "unknown")
    payload = event.get("payload", {})
    started = time.time()
    LOGGER.info(
        "async handler starting job_id=%s payload_keys=%s",
        job_id,
        list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__,
    )
    # Simulate work
    time.sleep(0.1)
    elapsed_ms = int((time.time() - started) * 1000)
    summary = {"job_id": job_id, "status": "ok", "elapsed_ms": elapsed_ms}
    LOGGER.info("async handler done %s", json.dumps(summary))
    return summary


if __name__ == "__main__":
    # Local smoke test — no AWS account required.
    fake_event = {"job_id": "demo-1", "payload": {"records": [1, 2, 3]}}
    class _C:
        aws_request_id = "local"
    print(json.dumps(handler(fake_event, _C()), indent=2))
