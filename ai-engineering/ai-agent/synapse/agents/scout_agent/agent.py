"""
Scout Agent

Orchestrates the ContextualistAgent and aggregates its signals into a single
ScoutResponse that the Publisher Agent can consume.

The Scout Agent also registers itself on the shared A2A bus so it can receive
ScoutRequest messages from other agents or the UI.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT))

from protocol.a2a import BaseAgent, Message, bus
from protocol.messages import ScoutRequest, ScoutResponse, Signal
from agents.contextualist_agent.agent import ContextualistAgent


class ScoutAgent(BaseAgent):
    """
    Gathers contextual signals for a topic and city.

    Usage (direct async call)::

        agent = ScoutAgent()
        response = await agent.scout(ScoutRequest(topic="AI", city="San Francisco"))

    Usage via A2A bus::

        response = await bus.send(Message(
            sender="ui",
            recipient="scout_agent",
            type="scout_request",
            payload=ScoutRequest(topic="AI", city="San Francisco"),
        ))
    """

    name = "scout_agent"

    def __init__(self) -> None:
        super().__init__(bus)
        self._contextualist = ContextualistAgent()

    async def scout(self, request: ScoutRequest) -> ScoutResponse:
        """Run the contextualist and return an aggregated ScoutResponse."""
        signals: list[Signal] = await self._contextualist.gather(
            topic=request.topic, city=request.city
        )
        return ScoutResponse(
            topic=request.topic,
            city=request.city,
            signals=signals,
        )

    async def receive(self, message: Message):
        """A2A bus handler — accepts scout_request messages."""
        if message.type != "scout_request":
            raise ValueError(f"ScoutAgent does not handle message type '{message.type}'")
        request: ScoutRequest = message.payload
        return await self.scout(request)
