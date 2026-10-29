"""FCI Cluster Monitor Lambda.

Triggered on a fixed schedule (every 5 minutes by default) by an EventBridge
rule, this function checks the free storage capacity of an Amazon FSx for
Windows File Server file system that is joined to an AWS Managed Microsoft
AD directory, and grows the volume when free storage drops below a
configurable threshold.

The handler is intentionally small, idempotent, and side-effect-aware:

- It reads ``FSX_FILE_SYSTEM_ID``, ``THRESHOLD_GB``, ``GROW_FACTOR``,
  ``COOLDOWN_SECONDS``, and ``DRY_RUN`` from environment variables.
- It calls ``fsx.describe_file_systems`` to get the current
  ``StorageCapacity`` (GB).
- When ``StorageCapacity < THRESHOLD_GB`` *and* the previous grow is
  older than ``COOLDOWN_SECONDS``, it calls ``fsx.update_file_system``
  with the new capacity.
- The grow-time is persisted in a process-level module attribute so
  consecutive invocations within the cooldown window do not call
  ``update_file_system`` again. (For cross-process durability, swap
  this for a DynamoDB item; see ``lecture_scripts/L86``.)
- It emits one structured JSON log line per decision so CloudWatch Logs
  Insights can answer "did we grow? when? why not?".
- The function never raises. A failure is logged and a structured
  ``status`` is returned so the EventBridge schedule keeps firing.

Environment variables:

    FSX_FILE_SYSTEM_ID   (required)  FSx file-system ID, e.g. ``fs-0123456789abcdef0``.
    THRESHOLD_GB         (default 100) Grow when ``StorageCapacity`` < threshold.
    GROW_FACTOR          (default 1.2)  Multiplicative grow factor, e.g. 1.2 = +20%.
    COOLDOWN_SECONDS     (default 1800) Minimum seconds between two grow calls.
    DRY_RUN              (default "false") If "true", log but do not call FSx.
    LOG_LEVEL            (default "INFO") Python log level.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

# ---------------------------------------------------------------------------
# Configuration via environment variables
# ---------------------------------------------------------------------------

FSX_FILE_SYSTEM_ID = os.environ.get("FSX_FILE_SYSTEM_ID", "")
THRESHOLD_GB = int(os.environ.get("THRESHOLD_GB", "100"))
GROW_FACTOR = float(os.environ.get("GROW_FACTOR", "1.2"))
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "1800"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() in {"1", "true", "yes"}
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# ---------------------------------------------------------------------------
# Module-level clients. boto3 clients are thread-safe and Lambda re-uses the
# same container across invocations, so we build them once at import time.
# ---------------------------------------------------------------------------

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

_region = os.environ.get("AWS_REGION", "us-east-1")
_fsx = boto3.client("fsx", region_name=_region)

# Process-level "last grow time" in epoch seconds. Lambda re-uses the
# execution environment across invocations, so a module attribute is
# enough to enforce the cooldown for one function. For multi-instance
# fleets, persist this in DynamoDB with a conditional write.
_last_grow_at: float | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(level: int, event: str, **fields: Any) -> None:
    """Emit one structured JSON line to CloudWatch.

    Structured logs are easy to query with Logs Insights. We use
    ``default=str`` so non-serialisable values (datetime, etc.) are
    coerced to their string form rather than crashing the invocation.
    """
    payload = {"event": event, **fields}
    logger.log(level, json.dumps(payload, default=str))


def _cooldown_active(now: float) -> bool:
    """Return True if the function is still inside the cooldown window."""
    if _last_grow_at is None:
        return False
    return (now - _last_grow_at) < COOLDOWN_SECONDS


def _new_capacity(current_gb: int) -> int:
    """Compute the new storage capacity after a grow.

    FSx for Windows requires ``StorageCapacity`` to be a multiple of
    10 GiB and at least 32 GiB, and supports at most 65,536 GiB. We
    clamp the result to those bounds and round *up* to the next 10.
    """
    grown = current_gb * GROW_FACTOR
    rounded = int(math.ceil(grown / 10.0) * 10)
    return max(32, min(65536, rounded))


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Run one monitor pass.

    Parameters
    ----------
    event:
        Scheduled EventBridge payload (the contents are ignored — the
        function is parameterless). We still accept it so the same
        handler shape works for manual ``aws lambda invoke`` testing.
    context:
        Lambda context object (unused, but required by the runtime).

    Returns
    -------
    dict
        ``{status, file_system_id, current_capacity_gb, new_capacity_gb,
        grew, reason}``. Always returned, even on errors, so the
        EventBridge schedule keeps invoking the function.
    """
    request_id = getattr(context, "aws_request_id", "local")
    now = time.time()
    # The cooldown timestamp is module-level; declare it ``global`` before
    # any reference inside this function (including the call to
    # ``_cooldown_active`` below, which reads the same name).
    global _last_grow_at

    _log(
        logging.INFO,
        "monitor.start",
        request_id=request_id,
        file_system_id=FSX_FILE_SYSTEM_ID,
        threshold_gb=THRESHOLD_GB,
        grow_factor=GROW_FACTOR,
        cooldown_seconds=COOLDOWN_SECONDS,
        dry_run=DRY_RUN,
    )

    if not FSX_FILE_SYSTEM_ID:
        msg = "FSX_FILE_SYSTEM_ID is not set"
        _log(logging.ERROR, "monitor.config_missing", request_id=request_id, reason=msg)
        return {"status": "error", "reason": msg}

    # ------------------------------------------------------------------
    # 1. Read current capacity from FSx
    # ------------------------------------------------------------------
    try:
        response = _fsx.describe_file_systems(FileSystemIds=[FSX_FILE_SYSTEM_ID])
    except ClientError as exc:
        _log(
            logging.ERROR,
            "monitor.describe_failed",
            request_id=request_id,
            file_system_id=FSX_FILE_SYSTEM_ID,
            error=exc.response["Error"]["Code"],
            message=exc.response["Error"].get("Message", ""),
        )
        return {"status": "error", "reason": "describe_failed"}

    file_systems = response.get("FileSystems", [])
    if not file_systems:
        _log(
            logging.WARNING,
            "monitor.not_found",
            request_id=request_id,
            file_system_id=FSX_FILE_SYSTEM_ID,
        )
        return {"status": "error", "reason": "file_system_not_found"}

    fs = file_systems[0]
    lifecycle = fs.get("Lifecycle", "UNKNOWN")
    current_gb = int(fs.get("StorageCapacity", 0))
    lifecycle_ok = lifecycle in {"AVAILABLE", "UPDATING"}

    _log(
        logging.INFO,
        "monitor.snapshot",
        request_id=request_id,
        file_system_id=FSX_FILE_SYSTEM_ID,
        current_capacity_gb=current_gb,
        lifecycle=lifecycle,
    )

    # ------------------------------------------------------------------
    # 2. Decide whether to grow
    # ------------------------------------------------------------------
    if not lifecycle_ok:
        _log(
            logging.WARNING,
            "monitor.skip",
            request_id=request_id,
            reason="lifecycle_not_ok",
            lifecycle=lifecycle,
        )
        return {
            "status": "skipped",
            "file_system_id": FSX_FILE_SYSTEM_ID,
            "current_capacity_gb": current_gb,
            "new_capacity_gb": current_gb,
            "grew": False,
            "reason": f"lifecycle={lifecycle}",
        }

    if current_gb >= THRESHOLD_GB:
        _log(
            logging.INFO,
            "monitor.skip",
            request_id=request_id,
            reason="above_threshold",
            current_capacity_gb=current_gb,
            threshold_gb=THRESHOLD_GB,
        )
        return {
            "status": "ok",
            "file_system_id": FSX_FILE_SYSTEM_ID,
            "current_capacity_gb": current_gb,
            "new_capacity_gb": current_gb,
            "grew": False,
            "reason": "above_threshold",
        }

    if _cooldown_active(now):
        _log(
            logging.INFO,
            "monitor.skip",
            request_id=request_id,
            reason="cooldown",
            last_grow_at=_last_grow_at,
            cooldown_seconds=COOLDOWN_SECONDS,
        )
        return {
            "status": "ok",
            "file_system_id": FSX_FILE_SYSTEM_ID,
            "current_capacity_gb": current_gb,
            "new_capacity_gb": current_gb,
            "grew": False,
            "reason": "cooldown",
        }

    new_gb = _new_capacity(current_gb)
    if new_gb <= current_gb:
        new_gb = current_gb + 10  # force a minimum 10 GiB grow

    # ------------------------------------------------------------------
    # 3. Grow (unless dry-run)
    # ------------------------------------------------------------------
    if DRY_RUN:
        _log(
            logging.INFO,
            "monitor.grow_dry_run",
            request_id=request_id,
            file_system_id=FSX_FILE_SYSTEM_ID,
            current_capacity_gb=current_gb,
            new_capacity_gb=new_gb,
        )
        return {
            "status": "dry_run",
            "file_system_id": FSX_FILE_SYSTEM_ID,
            "current_capacity_gb": current_gb,
            "new_capacity_gb": new_gb,
            "grew": False,
            "reason": "dry_run",
        }

    try:
        _fsx.update_file_system(
            FileSystemId=FSX_FILE_SYSTEM_ID,
            StorageCapacity=new_gb,
        )
    except ClientError as exc:
        _log(
            logging.ERROR,
            "monitor.grow_failed",
            request_id=request_id,
            file_system_id=FSX_FILE_SYSTEM_ID,
            current_capacity_gb=current_gb,
            new_capacity_gb=new_gb,
            error=exc.response["Error"]["Code"],
            message=exc.response["Error"].get("Message", ""),
        )
        return {
            "status": "error",
            "file_system_id": FSX_FILE_SYSTEM_ID,
            "current_capacity_gb": current_gb,
            "new_capacity_gb": new_gb,
            "grew": False,
            "reason": "grow_failed",
        }

    # Update the in-process cooldown timestamp *after* a successful grow.
    _last_grow_at = now

    _log(
        logging.INFO,
        "monitor.grew",
        request_id=request_id,
        file_system_id=FSX_FILE_SYSTEM_ID,
        old_capacity_gb=current_gb,
        new_capacity_gb=new_gb,
    )
    return {
        "status": "grew",
        "file_system_id": FSX_FILE_SYSTEM_ID,
        "current_capacity_gb": current_gb,
        "new_capacity_gb": new_gb,
        "grew": True,
        "reason": "below_threshold",
    }


# ---------------------------------------------------------------------------
# Local entry point — invoke with:  python lambda_function.py
# ---------------------------------------------------------------------------

class _FakeContext:
    """Minimal stand-in for the Lambda context object."""

    def __init__(self, request_id: str = "local") -> None:
        self.aws_request_id = request_id
        self.function_name = "fci-monitor-local"
        self.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:000000000000:function:fci-monitor-local"
        )


if __name__ == "__main__":
    # Allow running ``python lambda_function.py`` against a real or
    # mocked AWS account to smoke-test the handler end-to-end.
    sample_event = {
        "version": "0",
        "id": "local-1",
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "account": "123456789012",
        "time": "2026-10-10T12:00:00Z",
        "region": os.environ.get("AWS_REGION", "us-east-1"),
        "resources": ["arn:aws:events:us-east-1:123456789012:rule/fci-monitor"],
        "detail": {},
    }
    result = handler(sample_event, _FakeContext())
    print(json.dumps(result, indent=2))
