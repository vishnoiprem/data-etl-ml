"""Build a GraphStore by extracting (entity, relation, entity) triples per chunk.

For each chunk we ask the LLM to emit JSON, then add the triples to the graph.
"""
from __future__ import annotations

from loguru import logger

from .graph_store import GraphStore, Triple
from .ingestion import Doc
from .llm import LLMClient


_TRIPLE_PROMPT = """Extract entity-relation-entity triples from the text below.

Return JSON of the form:
{{"triples": [{{"head": "...", "head_type": "...", "rel": "...", "tail": "...", "tail_type": "..."}}, ...]}}

Rules:
- Use TitleCase for entity names.
- `rel` should be UPPER_SNAKE (e.g. REQUIRES, REFERENCES, OFFERS, APPLIES_TO).
- Capture only facts actually stated in the text — no inference.
- Aim for 1-5 triples per chunk.

Source: {chunk_id}
Title: {title}

Text:
\"\"\"
{text}
\"\"\"
"""


def build_graph(docs: list[Doc], llm: LLMClient) -> GraphStore:
    store = GraphStore()
    for i, doc in enumerate(docs):
        prompt = _TRIPLE_PROMPT.format(chunk_id=doc.doc_id, title=doc.title, text=doc.text)
        try:
            data = llm.extract_json(prompt)
        except Exception as e:
            logger.warning(f"Triple extraction failed for {doc.chunk_id}: {e}")
            continue
        raw_triples = data.get("triples", []) if isinstance(data, dict) else []
        triples: list[Triple] = []
        for t in raw_triples:
            if not isinstance(t, dict):
                continue
            try:
                triples.append(Triple.from_dict(t))
            except (KeyError, ValueError) as e:
                logger.debug(f"Skipping malformed triple {t!r}: {e}")
        store.add_triples(triples)
        if (i + 1) % 5 == 0:
            logger.info(f"  extracted triples from {i + 1}/{len(docs)} chunks")
    logger.info(f"Graph built: {len(store)} nodes, {len(store.edges())} edges")
    return store
