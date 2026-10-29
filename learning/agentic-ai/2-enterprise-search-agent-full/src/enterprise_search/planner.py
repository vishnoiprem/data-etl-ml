"""Query understanding: classify, rewrite, and fan out.

This runs *before* any retrieval. The cheapest way to improve search quality is
to not search at all when the user gave you an exact identifier.
"""

import re
from dataclasses import dataclass


@dataclass
class ExactMatch:
    """An identifier found in the query, and the tool that can resolve it."""

    value: str
    tool: str
    argument: str


class QueryPlanner:
    # Each pattern is bound to the tool that owns that identifier space. Binding
    # the pattern to the tool is what stops "SKU-1234" from being sent to the
    # order API just because it looks like an ID.
    ID_PATTERNS: list[tuple[str, str, str]] = [
        (r"\b(?:ORD|ORDER)[-_]?\d{4,}\b", "get_order", "order_id"),
        (r"\bSKU[-_]?\d{4,}\b", "get_product", "sku"),
    ]

    # Expansions for internal jargon. A lexical index cannot match "MCP" against
    # a document that spells out "model context protocol", so we add both.
    SYNONYMS = {
        "mcp": "model context protocol tool contract",
        "rag": "retrieval augmented generation",
        "bloat": "excess irrelevant context",
        "retry": "transient failure repeat",
        "resume": "checkpoint continue",
        "acl": "access control list permission",
    }

    def exact_id(self, query: str) -> ExactMatch | None:
        """Return the first identifier in the query, or None if it is a real search."""
        for pattern, tool, argument in self.ID_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return ExactMatch(match.group(0).upper(), tool, argument)
        return None

    def classify(self, query: str) -> str:
        """Route the query to a workload type.

        ``exact_lookup`` goes to a typed API (deterministic, cheap, always current).
        ``analytical`` and ``search`` both go through retrieval; the label is kept
        so answer length and evaluation can differ per workload later.
        """
        if self.exact_id(query):
            return "exact_lookup"
        if any(word in query.lower() for word in ("why", "compare", "evaluate", "analyze")):
            return "analytical"
        return "search"

    def rewrite(self, query: str) -> str:
        """Normalize whitespace/case and append synonym expansions.

        Expansions are *added*, never substituted, so the user's own wording still
        contributes to the score.
        """
        expanded: list[str] = []
        for word in query.lower().split():
            expanded.append(word)
            bare = re.sub(r"[^a-z0-9]", "", word)
            if bare in self.SYNONYMS:
                expanded.extend(self.SYNONYMS[bare].split())
        return " ".join(expanded)

    def fan_out(self, query: str, limit: int = 4) -> list[str]:
        """Turn one query into a few complementary queries.

        Each variant biases retrieval toward a different kind of document, which
        raises recall. The limit is what keeps fan-out from becoming a cost bug:
        every extra query is another retrieval call and more candidates to rerank.
        """
        base = self.rewrite(query)
        variants = [
            base,
            f"{base} policy standard",
            f"{base} architecture implementation",
            f"{base} evaluation metrics",
        ]
        return list(dict.fromkeys(variants))[:limit]  # dict.fromkeys keeps order, drops dupes
