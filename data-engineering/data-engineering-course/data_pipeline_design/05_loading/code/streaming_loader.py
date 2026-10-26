"""Kafka-style streaming loader with batching and a tiny in-memory broker.

The pattern:

  1. Producers ``publish()`` events to a topic.
  2. A consumer ``polls()`` events in batches up to ``batch_size``
     or ``linger_ms``, whichever comes first.
  3. The consumer calls a user-supplied ``load_fn(events)`` to
     write to the destination.
  4. After the load succeeds, the consumer commits the offsets.
  5. On crash, the consumer restarts from the last committed
     offset.

The in-memory broker is for tests and demos. In production
this is Kafka / Kinesis / Pub/Sub.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence


@dataclass
class StreamEvent:
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    value: Dict[str, Any]
    ts_ms: int = field(default_factory=lambda: int(time.time() * 1000))


class InMemoryBroker:
    """A tiny in-memory Kafka-like broker.

    Supports partitioned topics, publish, poll, and committed
    offsets per (group, topic, partition).
    """

    def __init__(self) -> None:
        self._topics: Dict[str, Dict[int, List[StreamEvent]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._high_water: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._offsets: Dict[str, Dict[str, Dict[int, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )
        self._lock = threading.Lock()

    def create_topic(self, topic: str, partitions: int = 1) -> None:
        with self._lock:
            for p in range(partitions):
                self._topics[topic].setdefault(p, [])
                self._high_water[topic].setdefault(p, 0)

    def publish(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        partition: Optional[int] = None,
    ) -> StreamEvent:
        with self._lock:
            parts = self._topics[topic]
            if not parts:
                self.create_topic(topic)
                parts = self._topics[topic]
            if partition is None:
                partition = hash(key) % len(parts) if key else 0
            partition = partition % len(parts)
            offset = self._high_water[topic][partition]
            event = StreamEvent(
                topic=topic,
                partition=partition,
                offset=offset,
                key=key,
                value=value,
            )
            parts[partition].append(event)
            self._high_water[topic][partition] = offset + 1
            return event

    def poll(
        self,
        group: str,
        topic: str,
        max_records: int = 100,
    ) -> List[StreamEvent]:
        """Read up to ``max_records`` events starting at the committed
        offset for ``(group, topic)`` across all partitions."""
        with self._lock:
            out: List[StreamEvent] = []
            for partition, events in self._topics[topic].items():
                committed = self._offsets[group][topic].get(partition, 0)
                for ev in events[committed:]:
                    out.append(ev)
                    if len(out) >= max_records:
                        break
                if len(out) >= max_records:
                    break
            return out

    def commit(
        self, group: str, topic: str, events: Sequence[StreamEvent]
    ) -> None:
        """Mark all ``events`` as processed by ``group``."""
        with self._lock:
            for ev in events:
                self._offsets[group][topic][ev.partition] = ev.offset + 1

    def high_water(self, topic: str, partition: int) -> int:
        return self._high_water[topic][partition]


class StreamingLoader:
    """A batched streaming loader.

    Polls the broker, accumulates events up to ``batch_size`` or
    ``linger_ms``, and calls ``load_fn(events)`` to write to the
    destination. On success, commits the offsets.
    """

    def __init__(
        self,
        broker: InMemoryBroker,
        group: str,
        topic: str,
        load_fn: Callable[[List[StreamEvent]], None],
        batch_size: int = 100,
        linger_ms: int = 1000,
    ) -> None:
        self.broker = broker
        self.group = group
        self.topic = topic
        self.load_fn = load_fn
        self.batch_size = batch_size
        self.linger_ms = linger_ms
        self.events_loaded = 0
        self.batches_loaded = 0
        self._buffer: List[StreamEvent] = []
        self._last_flush = time.time()

    def poll_once(self) -> int:
        """Poll for new events; flush if batch_size or linger reached.

        Returns the number of events loaded in this call.
        """
        events = self.broker.poll(
            self.group, self.topic, max_records=self.batch_size
        )
        self._buffer.extend(events)
        if len(self._buffer) >= self.batch_size:
            return self._flush()
        if (
            self._buffer
            and (time.time() - self._last_flush) * 1000 >= self.linger_ms
        ):
            return self._flush()
        return 0

    def _flush(self) -> int:
        if not self._buffer:
            return 0
        self.load_fn(self._buffer)
        self.broker.commit(self.group, self.topic, self._buffer)
        n = len(self._buffer)
        self.events_loaded += n
        self.batches_loaded += 1
        self._buffer = []
        self._last_flush = time.time()
        return n

    def flush(self) -> int:
        """Force a flush regardless of size or linger."""
        return self._flush()
