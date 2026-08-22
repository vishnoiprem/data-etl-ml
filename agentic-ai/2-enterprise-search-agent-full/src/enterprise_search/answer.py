"""Context budgeting and grounded answer generation.

This is the step that decides what the language model is allowed to see. It is
also the cheapest place to control cost, latency, and hallucination at once.
"""

from .models import SearchResult
from .text import sentences, tokenize

CONTEXT_CHARACTER_BUDGET = 3500
MAX_ANSWER_SENTENCES = 4
NO_EVIDENCE = "No authorized evidence was found for this question."


def select_evidence(
    candidates: list[SearchResult], budget: int = CONTEXT_CHARACTER_BUDGET
) -> tuple[list[SearchResult], int]:
    """Pick the documents that fit the context budget, best-scoring first.

    Two rules that matter more than they look:

    * A document that does not fit is *skipped*, not treated as a stop signal. A
      single long document early in the list must not starve every shorter
      document behind it.
    * Deduplicate by document id. Fusion already does this, but re-checking here
      keeps the budget honest if a caller ever passes an unfused list - paying
      twice for the same text is the most common form of context bloat.
    """
    selected: list[SearchResult] = []
    seen: set[str] = set()
    used = 0

    for hit in candidates:
        if hit.document.id in seen:
            continue
        size = len(hit.document.text)
        if used + size > budget:
            continue
        selected.append(hit)
        seen.add(hit.document.id)
        used += size

    return selected, used


def write_grounded_answer(
    query: str, evidence: list[SearchResult], max_sentences: int = MAX_ANSWER_SENTENCES
) -> str:
    """Build an extractive answer whose every sentence carries a source marker.

    Extractive rather than generative on purpose: it makes the demo runnable with
    no API key, and it makes grounding verifiable - every sentence is copied from
    a retrieved document, so there is nothing for the model to invent. In
    production, this is where an LLM call goes, with the same evidence list and
    the same "cite every claim" contract.
    """
    if not evidence:
        return NO_EVIDENCE

    query_terms = tokenize(query)
    scored: list[tuple[int, int, str]] = []
    seen_sentences: set[str] = set()

    for source_number, hit in enumerate(evidence, start=1):
        for sentence in sentences(hit.document.text):
            if sentence in seen_sentences:  # near-duplicates across sources
                continue
            matches = len(query_terms & tokenize(sentence))
            if matches:
                seen_sentences.add(sentence)
                scored.append((matches, source_number, sentence))

    # Most query terms matched wins; ties go to the better-ranked source, then to
    # the sentence text, so the output is fully deterministic.
    scored.sort(key=lambda row: (-row[0], row[1], row[2]))
    chosen = scored[:max_sentences]

    if not chosen:
        # Nothing overlapped: fall back to the first sentence of the top document
        # rather than dumping the whole document into the answer.
        top = evidence[0]
        first = sentences(top.document.text)
        return f"{first[0] if first else top.document.text} [Source 1]"

    return " ".join(f"{sentence} [Source {number}]" for _, number, sentence in chosen)


def build_citations(evidence: list[SearchResult]) -> list[dict]:
    """Citation numbers must match the ``[Source n]`` markers in the answer."""
    return [
        {
            "source_number": number,
            "title": hit.document.title,
            "uri": hit.document.uri,
            "source": hit.document.source,
        }
        for number, hit in enumerate(evidence, start=1)
    ]
