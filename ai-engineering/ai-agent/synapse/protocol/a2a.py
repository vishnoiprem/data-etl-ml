"""
Agent-to-Agent (A2A) messaging protocol.

Provides an in-process message bus that routes typed envelopes between named
agents.  In a production deployment each agent would run as its own service;
the bus would be replaced by an HTTP/gRPC transport while the Message schema
stays identical.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional


@dataclass
class Message:
    sender: str
    recipient: str
    type: str                  # e.g. "scout_request", "publish_request"
    payload: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AgentBus:
    """Simple synchronous-style routing bus for in-process agents."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}

    def register(self, agent_name: str, handler: Callable) -> None:
        self._handlers[agent_name] = handler

    async def send(self, message: Message) -> Any:
        handler = self._handlers.get(message.recipient)
        if not handler:
            raise ValueError(f"No agent registered as '{message.recipient}'")
        return await handler(message)


# Module-level shared bus — agents import this singleton.
bus = AgentBus()


class BaseAgent:
    """Mixin that gives any agent a name, a bus handle, and send/receive wiring."""

    name: str = "base_agent"

    def __init__(self, agent_bus: Optional[AgentBus] = None) -> None:
        self.bus = agent_bus or bus
        self.bus.register(self.name, self.receive)

    async def receive(self, message: Message) -> Any:
        raise NotImplementedError(f"{self.name}.receive() must be implemented")

    async def send(self, recipient: str, msg_type: str, payload: Any) -> Any:
        msg = Message(
            sender=self.name,
            recipient=recipient,
            type=msg_type,
            payload=payload,
        )
        return await self.bus.send(msg)
