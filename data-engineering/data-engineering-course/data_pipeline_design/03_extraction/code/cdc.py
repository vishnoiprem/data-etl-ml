"""Change Data Capture (CDC) pipeline, Debezium-style.

Implements the *snapshot + diff* pattern: keep a local snapshot of
the source rows, then on each run diff the current source against
the snapshot and emit INSERT / UPDATE / DELETE events to a sink.

The pattern matches Debezium's behavior on first start:

    Phase 1: snapshot the source table.
    Phase 2: tail the transaction log from the snapshot LSN.
    Phase 3: emit a stream of c / u / d events.

This implementation focuses on Phase 1+3 (Phase 2 is the binlog
reader, which is database-specific and out of scope for a teaching
example). The event schema mirrors Debezium's:

    {
      "op": "c" | "u" | "d" | "r",
      "ts_ms": 1700000000000,
      "before": {...} | None,
      "after":  {...} | None,
      "source": {"table": "users", "key": ["id"]}
    }

The pipeline is wrapped in ``common.Pipeline`` so it gets retries
and idempotency for free.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set

from common import Pipeline


# ---- event shape ------------------------------------------------------


@dataclass
class CDCEvent:
    op: str  # "c" create, "u" update, "d" delete, "r" read/snapshot
    table: str
    key: Dict[str, Any]
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    ts_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op": self.op,
            "table": self.table,
            "key": self.key,
            "before": self.before,
            "after": self.after,
            "ts_ms": self.ts_ms,
        }


# ---- the pipeline -----------------------------------------------------


class CDCPipeline:
    """Snapshot + diff CDC pipeline.

    Tracks a local "snapshot" of the source rows, keyed by primary
    key. On every ``run_once()``, it diffs the current source state
    against the snapshot and emits events to a sink.

    The sink is any object with a ``write(events: list)`` method.
    A ``MemorySink`` is the typical test target; a Kafka producer
    or a Parquet writer is the production target.

    Example::

        pipeline = CDCPipeline(sink=memory_sink, table="users", pk="id")
        pipeline.run_once([
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ])
        # snapshot is now: {1: {...}, 2: {...}}, 2 events emitted
    """

    def __init__(
        self,
        sink: Any,
        table: str = "rows",
        pk: str = "id",
    ) -> None:
        self.sink = sink
        self.table = table
        self.pk = pk
        # snapshot: pk-value -> row dict
        self._snapshot: Dict[Any, Dict[str, Any]] = {}
        self._events_emitted: int = 0
        self._last_run_count: int = 0

    @property
    def snapshot(self) -> Dict[Any, Dict[str, Any]]:
        return dict(self._snapshot)

    def _diff(
        self, current: Sequence[Dict[str, Any]]
    ) -> List[CDCEvent]:
        """Diff current rows against the snapshot; return events."""
        events: List[CDCEvent] = []
        seen: Set[Any] = set()
        for row in current:
            key_val = row[self.pk]
            seen.add(key_val)
            if key_val not in self._snapshot:
                # New row.
                events.append(
                    CDCEvent(
                        op="c",
                        table=self.table,
                        key={self.pk: key_val},
                        before=None,
                        after=dict(row),
                    )
                )
            elif self._snapshot[key_val] != row:
                # Updated row.
                events.append(
                    CDCEvent(
                        op="u",
                        table=self.table,
                        key={self.pk: key_val},
                        before=dict(self._snapshot[key_val]),
                        after=dict(row),
                    )
                )
            # else: unchanged, no event

        for key_val, old_row in self._snapshot.items():
            if key_val not in seen:
                # Deleted row.
                events.append(
                    CDCEvent(
                        op="d",
                        table=self.table,
                        key={self.pk: key_val},
                        before=dict(old_row),
                        after=None,
                    )
                )

        # Sort by op so consumers see creates first, then updates, then
        # deletes (matches Debezium's convention for snapshot phase).
        # Use the key value's string form so dicts don't get compared.
        events.sort(key=lambda e: (e.op, str(sorted(e.key.items()))))
        return events

    def run_once(self, current: Sequence[Dict[str, Any]]) -> List[CDCEvent]:
        """Diff ``current`` against the snapshot, emit events, update.

        Returns the list of events emitted (also written to ``sink``).
        """
        events = self._diff(current)
        if events:
            self.sink.write([e.to_dict() for e in events])
            self._events_emitted += len(events)
        # Update the snapshot to reflect the current state.
        self._snapshot = {row[self.pk]: dict(row) for row in current}
        self._last_run_count = len(current)
        return events

    def reset(self) -> None:
        """Clear the snapshot. Use for a fresh full snapshot."""
        self._snapshot.clear()
        self._events_emitted = 0
        self._last_run_count = 0

    # ---- common.Pipeline integration ---------------------------------

    def as_pipeline(
        self,
        extract: Callable[[], Sequence[Dict[str, Any]]],
    ) -> Pipeline:
        """Wrap the CDC in a ``common.Pipeline`` for retries/idempotency.

        The extract callable returns the current source rows; the
        transform is a no-op (the diff is in ``run_once``); the load
        is the sink's ``write`` (which the diff already called, so
        we return the count instead).
        """

        def _load(_events: List[CDCEvent]) -> int:
            return len(_events)

        return Pipeline(
            name=f"cdc.{self.table}",
            extract=extract,
            transform=self.run_once,
            load=_load,
            retries=3,
        )
