"""Pytest fixtures for the SQS+Lambda lab.

Single shared simulator + the project's actual ``lambda_handler`` from
``lambda_function/app.py``. Tests assert redrive, batching, and poison-
message behaviour without touching AWS.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "lambda_function"))

from sqs_stub import SqsSimulator       # noqa: E402
from app import lambda_handler          # noqa: E402


def _cols() -> List[str]:
    """Shared fixture -- the SQS columns we validate in the lab."""
    return ["order_id", "customer_id", "amount", "currency"]


@pytest.fixture
def cols() -> List[str]:
    return _cols()


@pytest.fixture
def simulator() -> SqsSimulator:
    return SqsSimulator()


@pytest.fixture
def queue_pair(simulator: SqsSimulator):
    """Wire main + DLQ + event source mapping the same way the lab does."""
    main = simulator.create_queue("orders-main-queue")
    dlq = simulator.create_queue("orders-dlq")
    simulator.attach_redrive("orders-main-queue", "orders-dlq",
                              max_receive_count=3)
    simulator.install_event_source("orders-main-queue", lambda_handler,
                                    batch_size=5)
    return simulator, main, dlq


def good_payload(i: int) -> Dict[str, Any]:
    return {"order_id": str(2000 + i),
            "customer_id": str(i),
            "amount": f"{i + 0.50:.2f}",
            "currency": "USD"}


def poison_payload(reason: str) -> Dict[str, Any]:
    if reason == "missing_amount":
        return {"order_id": "POISON1", "customer_id": "99", "currency": "USD"}
    if reason == "bad_currency":
        return {"order_id": "POISON2", "customer_id": "44",
                "amount": "10.00", "currency": "XXX"}
    if reason == "bad_amount":
        return {"order_id": "POISON3", "customer_id": "55",
                "amount": "-1.00", "currency": "USD"}
    raise ValueError(reason)
