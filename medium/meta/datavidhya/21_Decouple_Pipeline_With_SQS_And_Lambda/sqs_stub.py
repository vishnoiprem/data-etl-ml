"""In-memory SQS + event-source-mapping simulator for the Q21 lab.

Mirrors the AWS surface area the lab uses:

  - ``create_queue``                  -- a Queue with optional DLQ redrive
  - ``send_message``                  -- producer-side enqueue
  - ``receive_message``               -- consumer-side peek + ReceiveCount++
  - ``delete_message``                -- consumer-side ack
  - ``set_queue_attributes``          -- attach redrive policy / maxReceiveCount
  - Lambda event source mapping      -- poll + batch + invoke handler

The simulator tracks per-message state in-memory and replays the lab's
seven stages in order. Poison messages keep failing the Lambda handler;
once a message's ``receive_count`` exceeds ``maxReceiveCount`` the
simulator moves it to the DLQ -- exactly what SQS does in production.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ============================================================ primitives
@dataclass
class SqsMessage:
    """One message in a queue, with the attributes SQS tracks per message."""
    message_id:      str
    body:            str
    receipt_handle:  str
    receive_count:   int             = 0
    attributes:      Dict[str, Any] = field(default_factory=dict)

    def to_record(self, queue_arn: str) -> Dict[str, Any]:
        """Render the message in the SQS event-source-mapping Records[] shape."""
        return {
            "messageId":      self.message_id,
            "receiptHandle":  self.receipt_handle,
            "body":           self.body,
            "attributes": {
                "ApproximateReceiveCount":      str(self.receive_count),
                "SentTimestamp":                self.attributes.get("SentTimestamp",
                                                                     "1700000000000"),
                "VisibilityTimeout":            self.attributes.get("VisibilityTimeout",
                                                                     "30"),
                "ApproximateFirstReceiveTimestamp": "1700000000000",
            },
            "messageAttributes": {},
            "eventSource":  "aws:sqs",
            "eventSourceARN": queue_arn,
            "awsRegion":    "us-east-1",
        }


@dataclass
class Queue:
    """One SQS queue -- main or DLQ. The redrive policy points at the DLQ."""
    name:           str
    arn:            str
    messages:       List[SqsMessage] = field(default_factory=list)
    redrive_to:     Optional["Queue"] = None
    max_receive_count: int           = 3   # default before redrive

    def enqueue(self, body: str) -> SqsMessage:
        m = SqsMessage(message_id=str(uuid.uuid4()),
                        body=body,
                        receipt_handle=str(uuid.uuid4()))
        self.messages.append(m)
        return m

    def receive(self, max_messages: int = 1) -> List[SqsMessage]:
        """Peek up to ``max_messages`` from the head; bump ReceiveCount.

        AWS visibility timeout hides the message for N seconds; we model
        the simpler "received but not yet deleted" semantics -- the caller
        either deletes (ack) or doesn't (nack on next poll, ReceiveCount++).
        """
        batch: List[SqsMessage] = []
        for m in self.messages[:max_messages]:
            m.receive_count += 1
            batch.append(m)
        return batch

    def delete(self, receipt_handle: str) -> None:
        """Ack: remove the message from the queue."""
        self.messages = [m for m in self.messages
                          if m.receipt_handle != receipt_handle]

    def size(self) -> int:
        return len(self.messages)

    def redrive_poison(self) -> List[SqsMessage]:
        """Move messages past maxReceiveCount into the DLQ.

        Returns the list of moved messages so the caller can log/assert.
        """
        if self.redrive_to is None:
            return []
        moved: List[SqsMessage] = []
        survivors: List[SqsMessage] = []
        for m in self.messages:
            if m.receive_count > self.max_receive_count:
                # Reset ReceiveCount on the DLQ side -- the DLQ starts fresh.
                m.receive_count = 1
                moved.append(m)
                self.redrive_to.messages.append(m)
            else:
                survivors.append(m)
        self.messages = survivors
        return moved


# ============================================================ simulator
class SqsSimulator:
    """Owns the queues + the producer/consumer relationship for one lab."""

    def __init__(self) -> None:
        self.queues: Dict[str, Queue] = {}
        self.batch_size: int = 10
        self.event_source_mappings: Dict[str, Callable[[], None]] = {}

    # ----------------------------------------------------------- queues
    def create_queue(self, name: str) -> Queue:
        q = Queue(name=name, arn=f"arn:aws:sqs:us-east-1:123:{name}")
        self.queues[name] = q
        return q

    def get_queue(self, name: str) -> Queue:
        return self.queues[name]

    def attach_redrive(self, queue_name: str, dlq_name: str,
                        max_receive_count: int = 3) -> None:
        q = self.get_queue(queue_name)
        q.redrive_to = self.get_queue(dlq_name)
        q.max_receive_count = max_receive_count

    # ----------------------------------------------------------- mapping
    def install_event_source(self, queue_name: str,
                              handler: Callable[[Dict[str, Any], Any], Any],
                              batch_size: int = 10) -> None:
        """Wire a Lambda handler to a queue -- one invocation per batch.

        ``handler`` is the lab's ``app.lambda_handler``. The mapping is
        idempotent: re-installing replaces the previous binding.
        """
        self.batch_size = batch_size
        queue = self.get_queue(queue_name)

        def poll_once() -> None:
            messages = queue.receive(max_messages=batch_size)
            if not messages:
                return
            event = {"Records": [m.to_record(queue.arn) for m in messages]}
            try:
                handler(event, context=None)
            except Exception:                       # noqa: BLE001 -- intentional
                # SQS-level behaviour: do NOT delete any messages; let the
                # next poll re-receive them with ReceiveCount++.
                return
            for m in messages:
                queue.delete(m.receipt_handle)

        self.event_source_mappings[queue_name] = poll_once

    def poll(self, queue_name: str) -> None:
        """Run one poll cycle -- equivalent to one Lambda invocation."""
        self.event_source_mappings[queue_name]()


# ============================================================ helpers
def batch_event(queue: Queue, messages: List[SqsMessage]) -> Dict[str, Any]:
    """Synthesise a Records-shaped event the Lambda handler accepts."""
    return {"Records": [m.to_record(queue.arn) for m in messages]}
