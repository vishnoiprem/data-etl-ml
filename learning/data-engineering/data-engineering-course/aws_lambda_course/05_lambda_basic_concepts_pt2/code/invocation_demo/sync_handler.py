"""Synchronous Lambda handler used by L21 in section 5 (invocation model hands-on).

When invoked with `InvocationType=RequestResponse` (the boto3 default for
`client.invoke()`), AWS Lambda runs the function and returns the
response payload to the caller. This handler computes a sum over the
records in the event and returns it inline.

For the async counterpart see `async_handler.py`.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

LOGGER = logging.getLogger()
if not LOGGER.handlers:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Sync-style handler that returns the sum of the `numbers` list.

    Expected event shape:
        {"numbers": [1, 2, 3, 4]}

    Returns:
        {"sum": 10, "count": 4}
    """
    numbers = event.get("numbers", [])
    if not isinstance(numbers, list):
        raise TypeError(f"`numbers` must be a list, got {type(numbers).__name__}")
    total = sum(numbers)
    LOGGER.info("sync handler sum=%d count=%d", total, len(numbers))
    return {"sum": total, "count": len(numbers)}


if __name__ == "__main__":
    fake_event = {"numbers": [1, 2, 3, 4, 5]}
    class _C:
        aws_request_id = "local"
    print(json.dumps(handler(fake_event, _C()), indent=2))
