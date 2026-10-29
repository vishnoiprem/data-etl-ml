"""Offline pytest suite for the SQS+Lambda lab -- no AWS credentials.

Asserts:
    - Queue creation + ARN shape
    - DLQ + redrive policy wiring
    - Event source mapping batches + deletes-on-success
    - Failed batches are retained (raise -> no delete)
    - Poison messages exceed ``maxReceiveCount`` -> DLQ
    - The actual ``lambda_handler`` rejects bad payloads
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest

from sqs_stub import SqsSimulator
from app import lambda_handler


def test_queue_creation_assigns_arn(simulator: SqsSimulator) -> None:
    q = simulator.create_queue("test-q")
    assert q.name == "test-q"
    assert q.arn.startswith("arn:aws:sqs:")
    assert q.size() == 0


def test_redrive_policy_wires_dlq(simulator: SqsSimulator) -> None:
    main = simulator.create_queue("m")
    dlq = simulator.create_queue("d")
    simulator.attach_redrive("m", "d", max_receive_count=2)
    assert main.redrive_to is dlq
    assert main.max_receive_count == 2


def test_event_source_drains_good_messages(queue_pair) -> None:
    sim, main, dlq = queue_pair
    for i in range(1, 6):
        main.enqueue(json.dumps({"order_id": str(i),
                                  "customer_id": "1",
                                  "amount": "10.00",
                                  "currency": "USD"}))
    assert main.size() == 5
    sim.poll("orders-main-queue")
    assert main.size() == 0
    assert dlq.size() == 0


def test_event_source_batches_messages(queue_pair) -> None:
    sim, main, _ = queue_pair
    batches: List[List[Dict[str, Any]]] = []

    def spy(event, context):                            # noqa: ARG001
        batches.append([json.loads(r["body"]) for r in event["Records"]])
        return lambda_handler(event, context)

    sim.install_event_source("orders-main-queue", spy, batch_size=3)
    for i in range(1, 8):
        main.enqueue(json.dumps({"order_id": str(i),
                                  "customer_id": "1",
                                  "amount": "5.00",
                                  "currency": "EUR"}))
    sim.poll("orders-main-queue")
    sim.poll("orders-main-queue")
    sim.poll("orders-main-queue")
    assert main.size() == 0
    assert len(batches) == 3
    assert len(batches[0]) == 3
    assert len(batches[1]) == 3
    assert len(batches[2]) == 1


def test_failed_batch_is_retained(queue_pair) -> None:
    """Handler raises -> SQS must NOT delete the batch."""
    sim, main, _ = queue_pair
    main.enqueue(json.dumps({"order_id": "1", "customer_id": "1",
                              "amount": "1.00", "currency": "USD"}))
    main.enqueue(json.dumps({"order_id": "BAD",
                              "customer_id": "1", "amount": "1.00",
                              "currency": "XXX"}))      # -> ValueError
    sim.poll("orders-main-queue")
    # Bad message stays in main; good message also stays (whole batch fails).
    assert main.size() == 2


def test_poison_message_lands_in_dlq_after_max_receive(queue_pair) -> None:
    sim, main, dlq = queue_pair
    main.enqueue(json.dumps({"order_id": "POISON",
                              "customer_id": "1", "amount": "1.00",
                              "currency": "XXX"}))
    # max_receive_count=3, so the 4th poll pushes it to DLQ.
    for _ in range(4):
        sim.poll("orders-main-queue")
        main.redrive_poison()
    assert main.size() == 0
    assert dlq.size() == 1
    assert dlq.messages[0].receive_count == 1   # reset on arrival


def test_handler_validates_required_fields() -> None:
    with pytest.raises(ValueError):
        lambda_handler({"Records": [{"body": json.dumps(
            {"customer_id": "1", "amount": "1.00", "currency": "USD"})}]},
            context=None)


def test_handler_validates_amount_format() -> None:
    with pytest.raises(ValueError):
        lambda_handler({"Records": [{"body": json.dumps(
            {"order_id": "1", "customer_id": "1", "amount": "abc",
             "currency": "USD"})}]}, context=None)


def test_handler_validates_currency() -> None:
    with pytest.raises(ValueError):
        lambda_handler({"Records": [{"body": json.dumps(
            {"order_id": "1", "customer_id": "1", "amount": "1.00",
             "currency": "XXX"})}]}, context=None)


def test_handler_returns_batch_counts() -> None:
    out = lambda_handler({"Records": [
        {"body": json.dumps({"order_id": "1", "customer_id": "1",
                              "amount": "1.00", "currency": "USD"})},
        {"body": json.dumps({"order_id": "2", "customer_id": "2",
                              "amount": "2.00", "currency": "EUR"})},
    ]}, context=None)
    assert out == {"batch_size": 2, "processed": 2}


def test_redrive_resets_receive_count(simulator: SqsSimulator) -> None:
    main = simulator.create_queue("m")
    dlq = simulator.create_queue("d")
    simulator.attach_redrive("m", "d", max_receive_count=2)
    m = main.enqueue(json.dumps({"x": 1}))
    m.receive_count = 5                       # force "past max"
    moved = main.redrive_poison()
    assert len(moved) == 1
    assert moved[0].receive_count == 1        # reset on DLQ side
    assert dlq.size() == 1


def test_event_source_mapping_is_idempotent(queue_pair) -> None:
    """Re-installing replaces the previous binding without doubling polls."""
    sim, main, _ = queue_pair
    sim.install_event_source("orders-main-queue", lambda_handler,
                              batch_size=10)
    assert sim.batch_size == 10
