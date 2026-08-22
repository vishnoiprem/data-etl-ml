"""Data structures shared by every stage of the pipeline."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """One unit of enterprise content.

    `acl` lists the groups allowed to read the document; ``["all"]`` is public.
    Access control lives on the document rather than on the query so that every
    retrieval channel enforces exactly the same rule.
    """

    id: str
    title: str
    text: str
    source: str
    uri: str
    metadata: dict[str, Any] = field(default_factory=dict)
    acl: list[str] = field(default_factory=lambda: ["all"])

    def is_visible_to(self, groups: list[str]) -> bool:
        if "all" in self.acl:
            return True
        return bool(set(self.acl) & set(groups))


@dataclass
class SearchResult:
    """A document plus the scores it collected while moving through the pipeline.

    Three score fields on purpose, because they are not comparable with each other:

    * ``retrieval_score`` - channel-native relevance (TF-IDF cosine, connector score).
      Only meaningful *within* one channel.
    * ``fusion_score`` - reciprocal rank fusion score. Comparable across channels
      because it is computed from ranks, not from raw scores.
    * ``rerank_score`` - final 0..1 precision score used for ordering, for the
      context budget, and as the reported confidence.
    """

    document: Document
    retrieval_score: float
    rank: int = 0
    query: str = ""
    channel: str = ""
    fusion_score: float = 0.0
    rerank_score: float = 0.0
