"""Tokenization shared by ranking and answer generation.

One tokenizer for the whole project. If reranking and answer generation split
text differently, the scores they produce stop being comparable and results
become hard to explain - a common source of "why did this document win?" bugs.
"""

import re

# Small stopword list. Question words such as "how" or "should" appear in almost
# every query and in almost no document, so keeping them would dilute every
# overlap ratio and push all rerank scores toward zero.
STOPWORDS = frozenset(
    """
    a an the and or but if then than that this these those of in on at to for from by with
    is are was were be been being do does did doing have has had how what when where which
    who whom why should would could can may might will shall must i you he she it we they
    versus vs use used using about into over under between not no yes as
    """.split()
)

WORD = re.compile(r"[a-z0-9]+")
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def tokenize(text: str) -> set[str]:
    """Lowercase, split on word characters, drop stopwords and single characters."""
    return {
        token
        for token in WORD.findall(text.lower())
        if len(token) > 1 and token not in STOPWORDS
    }


def sentences(text: str) -> list[str]:
    """Split text into sentences. Good enough for prose; use a real segmenter for
    contracts, code, or tables."""
    return [part.strip() for part in SENTENCE_BOUNDARY.split(text) if part.strip()]


def overlap_ratio(query_terms: set[str], text: str) -> float:
    """Fraction of the query's meaningful terms that appear in `text` (0..1)."""
    if not query_terms:
        return 0.0
    return len(query_terms & tokenize(text)) / len(query_terms)
