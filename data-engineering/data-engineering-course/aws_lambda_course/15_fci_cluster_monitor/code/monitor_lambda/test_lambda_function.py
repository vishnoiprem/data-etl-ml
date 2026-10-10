"""Unit tests for the FCI Cluster Monitor Lambda handler.

We use ``moto.mock_aws`` to stand in for the FSx control plane so the
suite runs on a developer laptop without an AWS account. moto 5.x does
not implement ``fsx.update_file_system`` (it raises
``NotImplementedError``), so for the grow path we replace the FSx
client with a ``MagicMock`` and verify the call shape and arguments
directly. The no-grow paths use moto for ``describe_file_systems``
realistically.

The test exercises five behaviours:

1. configuration is loaded from environment variables;
2. storage above the threshold does not call ``update_file_system``;
3. storage below the threshold triggers a grow with the right new
   capacity;
4. the cooldown window suppresses a second grow on the immediate next
   invocation;
5. ``FSX_FILE_SYSTEM_ID`` missing produces a structured error result
   without raising.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

# Make sure the lambda_function module under test is importable as
# ``lambda_function`` regardless of how pytest was invoked.
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import lambda_function  # noqa: E402  (sys.path manipulation above)


FS_ID = "fs-0123456789abcdef0"
SUBNET_ID = "subnet-1234567890abcdef"
SCHEDULED_EVENT: dict[str, Any] = {
    "version": "0",
    "id": "test-event",
    "detail-type": "Scheduled Event",
    "source": "aws.events",
    "account": "123456789012",
    "time": "2026-10-10T12:00:00Z",
    "region": "us-east-1",
    "resources": ["arn:aws:events:us-east-1:123456789000:rule/fci-monitor"],
    "detail": {},
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_context() -> MagicMock:
    """A stand-in for the Lambda context object."""
    ctx = MagicMock()
    ctx.aws_request_id = "test-request-id"
    ctx.function_name = "fci-monitor-test"
    return ctx


@pytest.fixture
def fsx_low_storage(monkeypatch: pytest.MonkeyPatch) -> str:
    """Provision a moto-backed FSx file system at 50 GiB and bind it to the lambda module."""
    with mock_aws():
        fsx = boto3.client("fsx", region_name="us-east-1")
        resp = fsx.create_file_system(
            FileSystemType="WINDOWS",
            StorageCapacity=50,
            SubnetIds=[SUBNET_ID],
            WindowsConfiguration={"ThroughputCapacity": 8},
        )
        fs_id = resp["FileSystem"]["FileSystemId"]

        # The handler builds its boto3 client at import time. Re-bind
        # it to a fresh client inside the moto context so describe_file_systems
        # actually returns the file system we just created.
        fresh_client = boto3.client("fsx", region_name="us-east-1")
        monkeypatch.setattr(lambda_function, "_fsx", fresh_client)
        # Reset the cooldown state on every test.
        monkeypatch.setattr(lambda_function, "_last_grow_at", None)
        # Module-level constants were captured at import time; rewrite
        # them so the handler reads the values the test wants.
        monkeypatch.setattr(lambda_function, "FSX_FILE_SYSTEM_ID", fs_id)
        monkeypatch.setattr(lambda_function, "THRESHOLD_GB", 100)
        monkeypatch.setattr(lambda_function, "GROW_FACTOR", 1.2)
        monkeypatch.setattr(lambda_function, "COOLDOWN_SECONDS", 1800)
        monkeypatch.setattr(lambda_function, "DRY_RUN", False)
        yield fs_id


@pytest.fixture
def fsx_high_storage(monkeypatch: pytest.MonkeyPatch) -> str:
    """Provision a moto-backed FSx file system at 200 GiB (above the 100 GiB threshold)."""
    with mock_aws():
        fsx = boto3.client("fsx", region_name="us-east-1")
        resp = fsx.create_file_system(
            FileSystemType="WINDOWS",
            StorageCapacity=200,
            SubnetIds=[SUBNET_ID],
            WindowsConfiguration={"ThroughputCapacity": 8},
        )
        fs_id = resp["FileSystem"]["FileSystemId"]

        fresh_client = boto3.client("fsx", region_name="us-east-1")
        monkeypatch.setattr(lambda_function, "_fsx", fresh_client)
        monkeypatch.setattr(lambda_function, "_last_grow_at", None)
        monkeypatch.setattr(lambda_function, "FSX_FILE_SYSTEM_ID", fs_id)
        monkeypatch.setattr(lambda_function, "THRESHOLD_GB", 100)
        monkeypatch.setattr(lambda_function, "GROW_FACTOR", 1.2)
        monkeypatch.setattr(lambda_function, "COOLDOWN_SECONDS", 1800)
        monkeypatch.setattr(lambda_function, "DRY_RUN", False)
        yield fs_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_module_loads_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """The module exports the expected attributes with the documented defaults."""
    # Drop the env vars so we read the default values from the module.
    for key in ("FSX_FILE_SYSTEM_ID", "THRESHOLD_GB", "GROW_FACTOR",
                "COOLDOWN_SECONDS", "DRY_RUN", "LOG_LEVEL"):
        monkeypatch.delenv(key, raising=False)

    # Re-import the module so the module-level ``os.environ.get`` calls
    # pick up the new (empty) environment.
    reloaded = importlib.reload(lambda_function)

    assert reloaded.THRESHOLD_GB == 100
    assert reloaded.GROW_FACTOR == 1.2
    assert reloaded.COOLDOWN_SECONDS == 1800
    assert reloaded.DRY_RUN is False
    assert reloaded.FSX_FILE_SYSTEM_ID == ""
    assert reloaded.handler.__name__ == "handler"


def test_handler_does_not_grow_when_above_threshold(
    fsx_high_storage: str,
    fake_context: MagicMock,
) -> None:
    """Storage at 200 GiB is above the 100 GiB threshold — no grow call should happen."""
    # moto returns lifecycle="UNKNOWN" right after create_file_system,
    # so we drive describe_file_systems from a MagicMock to model a
    # healthy, AVAILABLE file system. We also assert that the handler
    # does not invoke update_file_system (moto would raise
    # NotImplementedError if it did).
    mock_client = MagicMock()
    mock_client.describe_file_systems.return_value = {
        "FileSystems": [
            {
                "FileSystemId": fsx_high_storage,
                "StorageCapacity": 200,
                "Lifecycle": "AVAILABLE",
            }
        ]
    }

    with patch.object(lambda_function, "_fsx", mock_client):
        result = lambda_function.handler(SCHEDULED_EVENT, fake_context)

    assert result["status"] == "ok"
    assert result["grew"] is False
    assert result["current_capacity_gb"] == 200
    assert result["new_capacity_gb"] == 200
    assert result["reason"] == "above_threshold"
    assert result["file_system_id"] == fsx_high_storage
    mock_client.update_file_system.assert_not_called()


def test_handler_grows_when_below_threshold(
    fsx_low_storage: str,
    fake_context: MagicMock,
) -> None:
    """Storage at 50 GiB is below the 100 GiB threshold — grow by 20% (50 * 1.2 = 60 -> round up to 60)."""
    mock_client = MagicMock()
    # 50 * 1.2 = 60.0 -> ceil(60/10) * 10 = 60.
    mock_client.describe_file_systems.return_value = {
        "FileSystems": [
            {
                "FileSystemId": fsx_low_storage,
                "StorageCapacity": 50,
                "Lifecycle": "AVAILABLE",
            }
        ]
    }
    mock_client.update_file_system.return_value = {
        "FileSystem": {
            "FileSystemId": fsx_low_storage,
            "StorageCapacity": 60,
            "Lifecycle": "UPDATING",
        }
    }

    with patch.object(lambda_function, "_fsx", mock_client):
        result = lambda_function.handler(SCHEDULED_EVENT, fake_context)

    assert result["status"] == "grew"
    assert result["grew"] is True
    assert result["current_capacity_gb"] == 50
    assert result["new_capacity_gb"] == 60
    mock_client.update_file_system.assert_called_once_with(
        FileSystemId=fsx_low_storage,
        StorageCapacity=60,
    )
    # The cooldown timestamp was recorded.
    assert lambda_function._last_grow_at is not None


def test_handler_is_idempotent_within_cooldown(
    fsx_low_storage: str,
    fake_context: MagicMock,
) -> None:
    """A second invocation within COOLDOWN_SECONDS must not call update_file_system again."""
    mock_client = MagicMock()
    mock_client.describe_file_systems.return_value = {
        "FileSystems": [
            {
                "FileSystemId": fsx_low_storage,
                "StorageCapacity": 50,
                "Lifecycle": "AVAILABLE",
            }
        ]
    }
    mock_client.update_file_system.return_value = {
        "FileSystem": {
            "FileSystemId": fsx_low_storage,
            "StorageCapacity": 60,
            "Lifecycle": "UPDATING",
        }
    }

    with patch.object(lambda_function, "_fsx", mock_client):
        first = lambda_function.handler(SCHEDULED_EVENT, fake_context)
        # Second invocation sees the same describe response and
        # therefore the same below-threshold capacity, but the
        # in-process cooldown should suppress the grow.
        second = lambda_function.handler(SCHEDULED_EVENT, fake_context)

    assert first["status"] == "grew"
    assert first["grew"] is True

    assert second["status"] == "ok"
    assert second["grew"] is False
    assert second["reason"] == "cooldown"
    # update_file_system was called exactly once, on the first invocation.
    assert mock_client.update_file_system.call_count == 1


def test_handler_returns_error_when_fsx_id_missing(
    monkeypatch: pytest.MonkeyPatch,
    fake_context: MagicMock,
) -> None:
    """A missing FSX_FILE_SYSTEM_ID must produce a structured error, not raise."""
    monkeypatch.setattr(lambda_function, "FSX_FILE_SYSTEM_ID", "")
    monkeypatch.delenv("FSX_FILE_SYSTEM_ID", raising=False)

    result = lambda_function.handler(SCHEDULED_EVENT, fake_context)

    assert result["status"] == "error"
    assert "FSX_FILE_SYSTEM_ID" in result["reason"]


def test_handler_dry_run_does_not_call_update(
    fsx_low_storage: str,
    monkeypatch: pytest.MonkeyPatch,
    fake_context: MagicMock,
) -> None:
    """DRY_RUN=true must compute the new capacity but never call fsx.update_file_system."""
    mock_client = MagicMock()
    mock_client.describe_file_systems.return_value = {
        "FileSystems": [
            {
                "FileSystemId": fsx_low_storage,
                "StorageCapacity": 50,
                "Lifecycle": "AVAILABLE",
            }
        ]
    }
    # Flip the module flag to True AFTER the fixture resets it to False.
    monkeypatch.setattr(lambda_function, "DRY_RUN", True)

    with patch.object(lambda_function, "_fsx", mock_client):
        result = lambda_function.handler(SCHEDULED_EVENT, fake_context)

    assert result["status"] == "dry_run"
    assert result["grew"] is False
    assert result["new_capacity_gb"] == 60
    mock_client.update_file_system.assert_not_called()


def test_local_main_block_runs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The ``__main__`` block should run the handler and print a JSON result."""
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(THIS_DIR / "lambda_function.py")],
        env={
            "PATH": "/usr/bin:/usr/local/bin",
            "PYTHONPATH": str(THIS_DIR),
            "AWS_REGION": "us-east-1",
            # No FSX_FILE_SYSTEM_ID -> we expect the handler to return
            # ``{"status": "error", ...}`` cleanly.
        },
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert proc.returncode == 0, proc.stderr
    # The ``__main__`` block calls ``print(json.dumps(..., indent=2))``,
    # which produces a multi-line pretty-printed JSON document. Re-join
    # the lines into a single string before parsing.
    payload = json.loads(proc.stdout)
    assert payload["status"] == "error"
    assert "FSX_FILE_SYSTEM_ID" in payload["reason"]
