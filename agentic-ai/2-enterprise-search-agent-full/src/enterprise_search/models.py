from dataclasses import dataclass, field
from typing import Any

@dataclass
class Document:
    id: str
    title: str
    text: str
    source: str
    uri: str
    metadata: dict[str, Any] = field(default_factory=dict)
    acl: list[str] = field(default_factory=lambda: ["all"])

@dataclass
class SearchResult:
    document: Document
    score: float
    rank: int = 0
    query: str = ""
    channel: str = ""
    rerank_score: float = 0.0
