from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Signal:
    """A single piece of contextual data collected from one MCP server."""
    source: str          # "news" | "weather" | "finance" | "media"
    data: Any            # parsed JSON payload from the MCP tool
    error: Optional[str] = None


@dataclass
class ScoutRequest:
    topic: str
    city: str


@dataclass
class ScoutResponse:
    topic: str
    city: str
    signals: list[Signal] = field(default_factory=list)

    def get_signal(self, source: str) -> Optional[Signal]:
        for s in self.signals:
            if s.source == source:
                return s
        return None


@dataclass
class PublishRequest:
    scout_response: ScoutResponse


@dataclass
class PublishResponse:
    article: str                          # Markdown-formatted article
    metadata: dict = field(default_factory=dict)
