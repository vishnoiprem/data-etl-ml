"""
service/rag.py — Mock vector store + retrieval for PacificFreight Phase 2.

What this file does
-------------------
- Loads `shared/policy_chunks.jsonl` (the chunked style guide).
- Loads `phase-1-foundations/shared/shipments.json` (one chunk per shipment).
- Provides `retrieve(query, k)` that ranks documents by deterministic
  token-overlap score (no embeddings API needed).
- Provides `build_rag_prompt(email, shipment, chunks, base_system_prompt)` that
  augments the system prompt with the retrieved context.

Why a mock
----------
Phase 2 teaches retrieval, not vector DB ops. Real embeddings +
Pinecone/Qdrant is Phase 3. The mock has the same interface (`retrieve`)
so swapping in a real vector store is a 1-function change.

The deterministic token-overlap scorer mirrors the pattern in
`course/hardcode/level-8-evaluation-testing/12-ragas-evaluation.py` —
file-private there, but lifted into a small library here for reuse.

How to run / import
-------------------
    from rag import retrieve, build_rag_prompt, MockVectorStore
    store = MockVectorStore()                 # auto-loads chunks + shipments
    chunks = store.retrieve("customs duty", k=3)
    prompt = build_rag_prompt("...", shipment, chunks)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RetrievedChunk:
    """One retrieved document. `score` is in [0.0, 1.0]; higher is better."""
    id: str
    text: str
    score: float
    source: str   # "policy" or "shipment" — for the model's metadata
    metadata: dict


# ---------------------------------------------------------------------------
# Token-overlap scorer (deterministic, no embeddings, no API key)
# ---------------------------------------------------------------------------
_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "but", "if", "of", "at", "by", "for", "with", "about",
    "to", "in", "on", "as", "this", "that", "these", "those", "it", "its",
    "i", "you", "we", "they", "he", "she", "my", "your", "our", "their",
    "do", "does", "did", "have", "has", "had", "can", "could", "will",
    "would", "should", "may", "might", "must", "shall", "just", "so",
    "than", "then", "now", "very", "really",
})


def _tokenize(text: str) -> list[str]:
    """Lowercase + split on non-word chars + drop stop words + short tokens."""
    tokens = re.findall(r"\b[a-z0-9_-]+\b", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) >= 2]


def _score(query_tokens: set[str], doc_tokens: set[str]) -> float:
    """Jaccard-like overlap with a length penalty for very short docs.

    The length penalty prevents a 3-token policy chunk from outscoring a
    30-token shipment chunk purely because it has fewer tokens to miss.
    Mirrors the heuristic in `12-ragas-evaluation.py::_mock_dense_retrieve`.
    """
    if not query_tokens or not doc_tokens:
        return 0.0
    overlap = query_tokens & doc_tokens
    if not overlap:
        return 0.0
    recall = len(overlap) / len(query_tokens)
    precision = len(overlap) / len(doc_tokens)
    # F1 with a length bonus for longer docs (more context).
    f1 = 2 * precision * recall / (precision + recall)
    length_bonus = min(1.0, len(doc_tokens) / 30.0)
    return round(f1 * (0.6 + 0.4 * length_bonus), 4)


# ---------------------------------------------------------------------------
# Mock vector store
# ---------------------------------------------------------------------------
class MockVectorStore:
    """In-memory retrieval over pre-chunked policy + shipments.

    On startup the store:
      1. Loads every policy chunk from `policy_chunks.jsonl` (one per H2
         section of the style guide).
      2. Builds one chunk per shipment from `shipments.json`, where the
         chunk text is a flat text dump of the shipment's fields and events.

    Retrieval ranks all chunks by token-overlap score against the query
    and returns the top-k. This is the same shape as a real vector store
    would return: (id, text, score, source, metadata).
    """

    def __init__(
        self,
        policy_chunks_path: Path | None = None,
        shipments_path: Path | None = None,
    ) -> None:
        # Resolve default paths relative to this file's location so the
        # service is runnable from any directory.
        here = Path(__file__).parent
        root = here.parent
        self._policy_path = policy_chunks_path or (
            root / "shared" / "policy_chunks.jsonl"
        )
        self._shipments_path = shipments_path or (
            root.parent / "phase-1-foundations" / "shared" / "shipments.json"
        )
        self.chunks: list[RetrievedChunk] = []
        self._load()

    def _load(self) -> None:
        # 1. Policy chunks.
        if self._policy_path.exists():
            with self._policy_path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    c = json.loads(line)
                    self.chunks.append(RetrievedChunk(
                        id=c["id"],
                        text=c["text"],
                        score=0.0,
                        source="policy",
                        metadata={"section": c.get("section"), "path": c.get("source")},
                    ))

        # 2. Shipment chunks.
        if self._shipments_path.exists():
            with self._shipments_path.open() as fh:
                data = json.load(fh)
            for s in data["shipments"]:
                text = self._shipment_to_text(s)
                self.chunks.append(RetrievedChunk(
                    id=f"shipment:{s['id']}",
                    text=text,
                    score=0.0,
                    source="shipment",
                    metadata={
                        "shipment_id": s["id"],
                        "status": s.get("status"),
                        "customer_name": s.get("customer_name"),
                    },
                ))

    @staticmethod
    def _shipment_to_text(s: dict) -> str:
        """Flatten a shipment dict into a single retrievable text blob."""
        lines = [
            f"Shipment {s['id']}",
            f"Customer: {s.get('customer_name', '?')}",
            f"Route: {s.get('origin', '?')} → {s.get('destination', '?')}",
            f"Status: {s.get('status', '?')}",
            f"Last event ({s.get('last_event_at', '?')}): {s.get('last_event', '?')}",
        ]
        if s.get("eta"):
            lines.append(f"ETA: {s['eta']}")
        if s.get("next_action_required"):
            lines.append(f"Action required: {s['next_action_required']}")
        events = s.get("events") or []
        if events:
            lines.append("Recent events:")
            for ev in events[-3:]:
                lines.append(f"  - {ev.get('ts', '?')}: {ev.get('event', '?')}")
        return "\n".join(lines)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        source_filter: str | None = None,
    ) -> list[RetrievedChunk]:
        """Return the top-k chunks for `query`, ordered by score desc.

        `source_filter`: optional "policy" or "shipment" to restrict the
        candidate pool — useful when the application knows which kind of
        context it wants.
        """
        if not query.strip():
            return []
        q_tokens = set(_tokenize(query))
        candidates = self.chunks
        if source_filter:
            candidates = [c for c in candidates if c.source == source_filter]
        scored = [
            RetrievedChunk(
                id=c.id, text=c.text,
                score=_score(q_tokens, set(_tokenize(c.text))),
                source=c.source, metadata=c.metadata,
            )
            for c in candidates
        ]
        scored = [c for c in scored if c.score > 0.0]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]


# ---------------------------------------------------------------------------
# RAG prompt builder
# ---------------------------------------------------------------------------
def build_rag_prompt(
    *,
    base_system: str,
    email: str,
    shipment: dict | None,
    chunks: Iterable[RetrievedChunk],
) -> str:
    """Augment a base system prompt with retrieved context.

    Layout:
      [base_system]                              ← persona + voice rules
      ---                                        ← divider (visible to model)
      Retrieved policy chunks:                  ← cite by [1], [2], ...
        [1] (style-guide#5, score=0.81)
            <text>
        [2] (style-guide#2, score=0.62)
            <text>
      ---                                        ← divider
      Retrieved shipment chunks:                 ← cite by [S1], [S2], ...
        [S1] (PF-1003, score=0.79, status=held_customs)
            <text>
      ---                                        ← divider
      Provided shipment (explicit lookup):
        <shipment dict as text>                  ← only if shipment is not None
      ---                                        ← divider
      Customer email:
        <email>
      Draft a reply in the customer's language.
      Output ONLY the reply, no preamble.
    """
    parts: list[str] = [base_system]

    chunks_list = list(chunks)
    policy = [c for c in chunks_list if c.source == "policy"]
    ship = [c for c in chunks_list if c.source == "shipment"]

    if policy:
        parts.append("---")
        parts.append("Retrieved policy chunks (cite as [1], [2], ...):")
        for i, c in enumerate(policy, start=1):
            parts.append(
                f"[{i}] ({c.id}, score={c.score:.2f})\n{c.text}"
            )

    if ship:
        parts.append("---")
        parts.append("Retrieved shipment chunks (cite as [S1], [S2], ...):")
        for i, c in enumerate(ship, start=1):
            parts.append(
                f"[S{i}] ({c.metadata.get('shipment_id', c.id)}, "
                f"score={c.score:.2f}, status={c.metadata.get('status', '?')})\n{c.text}"
            )

    if shipment is not None:
        parts.append("---")
        parts.append("Provided shipment (explicit lookup):")
        parts.append(json.dumps(shipment, indent=2, ensure_ascii=False))

    parts.append("---")
    parts.append("Customer email:")
    parts.append(email)
    parts.append(
        "Draft a reply in the customer's language. "
        "Output ONLY the reply, no preamble, no labels."
    )

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
def main() -> int:
    store = MockVectorStore()
    print(f"Loaded {len(store.chunks)} chunks")
    print(f"  policy chunks: {sum(1 for c in store.chunks if c.source == 'policy')}")
    print(f"  shipment chunks: {sum(1 for c in store.chunks if c.source == 'shipment')}")

    # Top-3 policy chunks for "customs duty"
    for c in store.retrieve("customs duty", k=3, source_filter="policy"):
        print(f"  [{c.id}] score={c.score:.3f}")

    # Top-3 shipment chunks for "PF-1003 held at customs"
    for c in store.retrieve("PF-1003 held at customs", k=3, source_filter="shipment"):
        print(f"  [{c.id}] score={c.score:.3f}")

    # All chunks for the angry PF-1004 customer
    chunks = store.retrieve("PF-1004 angry delivery failed", k=5)
    for c in chunks:
        print(f"  [{c.source}] [{c.id}] score={c.score:.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
