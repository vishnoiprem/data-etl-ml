"""In-memory event bus stand-in for EventBridge.

Each pipeline stage emits events; subscribers (observability, drift,
auto-rollback) react. In production this is EventBridge with rules routing
to SNS, SQS, Lambda.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable


@dataclass
class Event:
    name: str
    detail: dict
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    def __init__(self):
        self.events: list[Event] = []
        self._subs: dict[str, list[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, name: str, fn: Callable[[Event], None]):
        self._subs[name].append(fn)

    def emit(self, name: str, **detail):
        e = Event(name=name, detail=detail)
        self.events.append(e)
        for fn in self._subs.get(name, []):
            try:
                fn(e)
            except Exception as exc:  # never let a subscriber crash the bus
                self.events.append(Event(name="bus.subscriber_error",
                                         detail={"target": name, "error": str(exc)}))

    def dump(self) -> str:
        return "\n".join(json.dumps(asdict(e)) for e in self.events)
