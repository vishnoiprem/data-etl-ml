"""The two retrieval channels: indexed and federated.

Both expose the same ``search(query, groups, top_k) -> list[SearchResult]``
signature, so the agent can add or remove a channel without changing the
pipeline. Both enforce ACLs, because a channel that forgets is a data leak.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Document, SearchResult


class LocalIndex:
    """Indexed retrieval over a synchronized snapshot of the corpus.

    TF-IDF stands in for a production hybrid stack (BM25 + vector search). Fast
    and cheap, but only as fresh as the last sync - which is exactly why the
    federated channel below also exists.
    """

    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),  # bigrams so "context bloat" scores above two loose words
            sublinear_tf=True,  # log-damped term frequency: repetition should not dominate
        )
        corpus = [self._indexable_text(doc) for doc in documents]
        self.matrix = self.vectorizer.fit_transform(corpus)

    @staticmethod
    def _indexable_text(doc: Document) -> str:
        metadata = " ".join(str(value) for value in doc.metadata.values())
        return f"{doc.title} {doc.text} {metadata}"

    def search(self, query: str, groups: list[str], top_k: int = 10) -> list[SearchResult]:
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()

        hits = [
            SearchResult(doc, float(score), query=query, channel="indexed")
            for doc, score in zip(self.documents, scores)
            # ACL first, then relevance: an unauthorized document must never be
            # scored into the candidate set, not even to be dropped later.
            if doc.is_visible_to(groups) and score > 0
        ]
        hits.sort(key=lambda hit: hit.retrieval_score, reverse=True)

        top = hits[:top_k]
        for rank, hit in enumerate(top, start=1):
            hit.rank = rank
        return top


# The federated document is a constant, not rebuilt on every call.
LIVE_INVENTORY = Document(
    id="live-001",
    title="Current Inventory Notice",
    text=(
        "Inventory availability changes frequently and must be checked at request "
        "time in the authoritative inventory service."
    ),
    source="inventory-api",
    uri="api://inventory/current",
    metadata={"freshness": "live"},
    acl=["all"],
)


class FederatedConnector:
    """Request-time retrieval from a system of record.

    Nothing is copied into our index, so the answer is always current - the trade
    is added latency and a hard dependency on someone else's uptime. Use it for
    volatile data (stock, order state, prices); use the index for stable content.
    """

    def __init__(self, documents: list[Document] | None = None):
        self.documents = documents if documents is not None else [LIVE_INVENTORY]

    def search(self, query: str, groups: list[str], top_k: int = 5) -> list[SearchResult]:
        from .text import overlap_ratio, tokenize

        query_terms = tokenize(query)
        hits = []
        for doc in self.documents:
            if not doc.is_visible_to(groups):  # remote source, same ACL rule
                continue
            score = overlap_ratio(query_terms, f"{doc.title} {doc.text}")
            if score > 0:
                hits.append(SearchResult(doc, score, query=query, channel="federated"))

        hits.sort(key=lambda hit: hit.retrieval_score, reverse=True)
        top = hits[:top_k]
        for rank, hit in enumerate(top, start=1):
            hit.rank = rank
        return top
