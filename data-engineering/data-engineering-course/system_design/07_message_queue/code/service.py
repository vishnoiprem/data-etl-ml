"""Message queue service (Kafka-like).

A working in-memory broker that implements the design in
``design/README.md``:

* Topics split into N partitions; each partition is an append-only
  log stored in a ``KeyValueStore`` value.
* Producers hash the record key to pick a partition; ``key=None``
  uses round-robin.
* Consumer groups track a committed offset per ``(topic, partition)``.
  ``consume`` auto-commits by default; pass ``commit=False`` to
  advance the offset manually.
* At-least-once semantics: a record is only returned after the
  partition log is durably written. Consumers are responsible for
  deduping on ``message_id`` if a crash causes re-delivery.

The HTTP layer in ``app.py`` is a thin wrapper around this class.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict, field
from threading import RLock
from typing import Optional

from common.ids import Snowflake
from common.storage import KeyValueStore

# Default number of partitions when a topic is created without
# specifying one. Picked small for the lesson; real Kafka topics
# start at 12.
DEFAULT_PARTITIONS = 4

# Maximum partitions per topic. Prevents a runaway "give me 1M
# partitions" request.
MAX_PARTITIONS = 256

# Default cap on a single consume fetch.
DEFAULT_MAX_FETCH = 10

# Hard cap on a single fetch regardless of ?max=.
MAX_FETCH = 1_000

# Default reset policy for a new group: read from the start.
DEFAULT_RESET = "earliest"


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class Topic:
    name: str
    partitions: int
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Record:
    message_id: int
    key: Optional[str]
    value: str
    headers: dict
    partition: int
    offset: int
    ts: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Group:
    name: str
    created_at: float
    offsets: dict = field(default_factory=dict)  # "<topic>:<part>" -> int
    reset: str = DEFAULT_RESET  # "earliest" | "latest"

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class MessageQueueService:
    """A working Kafka-like broker.

    >>> svc = MessageQueueService()
    >>> svc.create_topic("events", partitions=2)
    >>> r = svc.produce("events", key="u1", value="hello")
    >>> r.partition in (0, 1)
    True
    >>> r.offset
    0
    >>> batch = svc.consume("events", group="g1", max=10)
    >>> len(batch)
    1
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        id_gen: Optional[Snowflake] = None,
    ):
        self.store = store or KeyValueStore("message_queue")
        self.id_gen = id_gen or Snowflake(machine_id=7)
        self._lock = RLock()
        # Round-robin counter for keyless produce. Keyed by topic.
        self._rr: dict[str, int] = {}

    # ------------------------------------------------------------------
    # topics — design §4
    # ------------------------------------------------------------------

    def create_topic(self, name: str, partitions: int = DEFAULT_PARTITIONS) -> Topic:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(partitions, int) or partitions <= 0:
            raise ValueError("partitions must be a positive int")
        if partitions > MAX_PARTITIONS:
            raise ValueError(f"partitions must be <= {MAX_PARTITIONS}")
        name = name.strip()
        if self.store.exists(self._k_topic(name)):
            raise ValueError(f"topic {name!r} already exists")
        t = Topic(name=name, partitions=partitions, created_at=time.time())
        self.store.set(self._k_topic(name), t.to_dict())
        return t

    def delete_topic(self, name: str) -> bool:
        """Remove a topic and all of its partition logs.

        Group offsets for the topic are *not* purged — old groups
        keep stale offset rows, which is fine (they just look up
        against an empty log and get nothing back).
        """
        if not self.store.exists(self._k_topic(name)):
            return False
        self.store.delete(self._k_topic(name))
        # Drop the partition logs.
        for p in range(MAX_PARTITIONS + 1):
            self.store.delete(self._k_log(name, p))
        return True

    def list_topics(self) -> list[Topic]:
        out: list[Topic] = []
        for k, v in self.store.scan("topic:"):
            if isinstance(v, dict):
                out.append(Topic(**v))
        out.sort(key=lambda t: t.created_at)
        return out

    def get_topic(self, name: str) -> Optional[Topic]:
        d = self.store.get(self._k_topic(name))
        return Topic(**d) if d else None

    def topic_log_size(self, name: str, partition: int) -> int:
        log = self._read_log(name, partition)
        return len(log)

    def topic_log(self, name: str, partition: int) -> list[Record]:
        return self._read_log(name, partition)

    # ------------------------------------------------------------------
    # produce — design §6 write path
    # ------------------------------------------------------------------

    def produce(
        self,
        topic: str,
        key: Optional[str] = None,
        value: str = "",
        headers: Optional[dict] = None,
    ) -> Record:
        """Append a record to ``topic``. Returns the assigned Record.

        Partition choice:
            * If ``key`` is a non-empty string, partition = hash(key) % N
            * If ``key`` is None or empty, round-robin across partitions
        """
        meta = self.get_topic(topic)
        if meta is None:
            raise ValueError(f"unknown topic {topic!r}")
        if not isinstance(value, str):
            # Force stringification — opaque bytes aren't part of the lesson.
            value = str(value)
        headers = dict(headers) if headers else {}

        partition = self._pick_partition(meta.name, meta.partitions, key)
        log = self._read_log(meta.name, partition)
        offset = len(log)
        rec = Record(
            message_id=self.id_gen.next_id(),
            key=key if key else None,
            value=value,
            headers=headers,
            partition=partition,
            offset=offset,
            ts=time.time(),
        )
        log.append(rec.to_dict())
        self._write_log(meta.name, partition, log)
        return rec

    def _pick_partition(
        self, topic: str, num_partitions: int, key: Optional[str]
    ) -> int:
        if key:
            # Python's hash() is salted per-process but stable within
            # a run; that's all we need for partition stickiness.
            return hash(key) % num_partitions
        with self._lock:
            p = self._rr.get(topic, 0) % num_partitions
            self._rr[topic] = p + 1
            return p

    # ------------------------------------------------------------------
    # groups — design §4
    # ------------------------------------------------------------------

    def create_group(self, name: str, reset: str = DEFAULT_RESET) -> Group:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if reset not in ("earliest", "latest"):
            raise ValueError("reset must be 'earliest' or 'latest'")
        name = name.strip()
        if self.store.exists(self._k_group(name)):
            raise ValueError(f"group {name!r} already exists")
        g = Group(
            name=name, created_at=time.time(), offsets={}, reset=reset
        )
        self.store.set(self._k_group(name), g.to_dict())
        return g

    def list_groups(self) -> list[Group]:
        out: list[Group] = []
        for k, v in self.store.scan("group:"):
            if isinstance(v, dict):
                out.append(Group(**v))
        out.sort(key=lambda g: g.created_at)
        return out

    def get_group(self, name: str) -> Optional[Group]:
        d = self.store.get(self._k_group(name))
        return Group(**d) if d else None

    def commit(self, group: str, topic: str, partition: int, offset: int) -> int:
        g = self.get_group(group)
        if g is None:
            raise ValueError(f"unknown group {group!r}")
        if offset < 0:
            raise ValueError("offset must be >= 0")
        g.offsets[self._k_offset(topic, partition)] = int(offset)
        self.store.set(self._k_group(group), g.to_dict())
        return int(offset)

    def group_offsets(
        self, group: str, topic: Optional[str] = None
    ) -> dict[str, int]:
        g = self.get_group(group)
        if g is None:
            return {}
        if topic is None:
            return dict(g.offsets)
        return {
            k: v
            for k, v in g.offsets.items()
            if k.startswith(f"{topic}:")
        }

    # ------------------------------------------------------------------
    # consume — design §7 read path
    # ------------------------------------------------------------------

    def consume(
        self,
        topic: str,
        group: str,
        max_records: int = DEFAULT_MAX_FETCH,
        commit: bool = True,
        reset: Optional[str] = None,
    ) -> list[Record]:
        """Fetch up to ``max_records`` records from one partition.

        The partition chosen is the one with the smallest committed
        offset relative to its log size — i.e. the most "behind"
        partition. On ties, the lowest partition wins. This is a
        cheap form of fair scheduling.

        ``reset`` overrides the group's default for *this* call only
        (used when the group has no committed offset for a partition
        yet).
        """
        meta = self.get_topic(topic)
        if meta is None:
            raise ValueError(f"unknown topic {topic!r}")
        g = self.get_group(group)
        if g is None:
            raise ValueError(f"unknown group {group!r}")
        if max_records <= 0:
            return []
        max_records = min(int(max_records), MAX_FETCH)

        # Pick the most-behind partition.
        chosen = self._choose_partition(meta, g, reset)
        if chosen is None:
            return []
        partition, start_offset = chosen

        log = self._read_log(meta.name, partition)
        end = min(start_offset + max_records, len(log))
        if end <= start_offset:
            return []

        records = [Record(**log[i]) for i in range(start_offset, end)]
        if commit:
            g.offsets[self._k_offset(meta.name, partition)] = end
            self.store.set(self._k_group(group), g.to_dict())
        return records

    def _choose_partition(
        self, meta: Topic, g: Group, reset: Optional[str]
    ) -> Optional[tuple[int, int]]:
        """Pick the partition with the most unconsumed records.

        Returns ``(partition, start_offset)`` or ``None`` if all
        partitions are fully consumed.
        """
        best: Optional[tuple[int, int, int]] = None
        # tie-breaker: lowest partition id
        policy = reset or g.reset
        for partition in range(meta.partitions):
            log = self._read_log(meta.name, partition)
            log_len = len(log)
            key = self._k_offset(meta.name, partition)
            if key in g.offsets:
                start = int(g.offsets[key])
            else:
                # New group / new partition — apply reset policy.
                if log_len == 0:
                    continue  # nothing to read
                start = 0 if policy == "earliest" else log_len
            if start >= log_len:
                continue
            lag = log_len - start
            if best is None or lag > best[2] or (
                lag == best[2] and partition < best[0]
            ):
                best = (partition, start, lag)
        if best is None:
            return None
        return best[0], best[1]

    # ------------------------------------------------------------------
    # stats / internals
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        topics = self.list_topics()
        return {
            "topics": len(topics),
            "groups": len(self.list_groups()),
            "total_records": sum(
                self.topic_log_size(t.name, p)
                for t in topics
                for p in range(t.partitions)
            ),
        }

    # ------------------------------------------------------------------
    # key naming
    # ------------------------------------------------------------------

    @staticmethod
    def _k_topic(name: str) -> str:
        return f"topic:{name}"

    @staticmethod
    def _k_log(topic: str, partition: int) -> str:
        return f"log:{topic}:{partition}"

    @staticmethod
    def _k_group(name: str) -> str:
        return f"group:{name}"

    @staticmethod
    def _k_offset(topic: str, partition: int) -> str:
        return f"{topic}:{partition}"

    # ------------------------------------------------------------------
    # log read / write helpers
    # ------------------------------------------------------------------

    def _read_log(self, topic: str, partition: int) -> list[dict]:
        log = self.store.get(self._k_log(topic, partition))
        if log is None:
            return []
        return list(log)

    def _write_log(
        self, topic: str, partition: int, log: list[dict]
    ) -> None:
        self.store.set(self._k_log(topic, partition), log)
