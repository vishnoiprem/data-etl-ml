"""Snowflake-style 64-bit IDs.

Twitter-style. 41 bits ms + 10 bits machine + 12 bits sequence. Sortable
by time. We use a single-process variant (machine_id=1) since the
services are in-memory; in a real cluster you'd pull machine_id from
ZooKeeper / a config service.
"""

from __future__ import annotations

import threading
import time

EPOCH = 1_577_836_800_000  # 2020-01-01 UTC in ms
MACHINE_BITS = 10
SEQUENCE_BITS = 12
MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1
MAX_MACHINE = (1 << MACHINE_BITS) - 1


class Snowflake:
    """Thread-safe 64-bit ID generator.

    >>> s = Snowflake(machine_id=1)
    >>> a, b = s.next_id(), s.next_id()
    >>> b > a
    True
    """

    def __init__(self, machine_id: int = 1):
        if not 0 <= machine_id <= MAX_MACHINE:
            raise ValueError(f"machine_id must be in [0, {MAX_MACHINE}]")
        self.machine_id = machine_id
        self._last_ms = 0
        self._sequence = 0
        self._lock = threading.Lock()

    def next_id(self) -> int:
        with self._lock:
            now = int(time.time() * 1000)
            if now == self._last_ms:
                self._sequence = (self._sequence + 1) & MAX_SEQUENCE
                if self._sequence == 0:
                    # Sequence overflow in this ms — wait for next ms.
                    while now <= self._last_ms:
                        now = int(time.time() * 1000)
            else:
                self._sequence = 0
            self._last_ms = now
            return (
                ((now - EPOCH) << (MACHINE_BITS + SEQUENCE_BITS))
                | (self.machine_id << SEQUENCE_BITS)
                | self._sequence
            )
