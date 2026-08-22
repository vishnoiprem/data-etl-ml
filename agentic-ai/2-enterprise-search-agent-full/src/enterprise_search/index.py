from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Document, SearchResult

class LocalIndex:
    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        corpus = [f"{d.title} {d.text} {' '.join(map(str, d.metadata.values()))}" for d in documents]
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, groups: list[str], top_k: int = 10) -> list[SearchResult]:
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        rows = []
        for i, score in enumerate(scores):
            doc = self.documents[i]
            if "all" not in doc.acl and not set(doc.acl).intersection(groups):
                continue
            if score > 0:
                rows.append(SearchResult(doc, float(score), query=query, channel="indexed"))
        rows.sort(key=lambda x: x.score, reverse=True)
        for rank, row in enumerate(rows[:top_k], 1):
            row.rank = rank
        return rows[:top_k]

class FederatedConnector:
    def search(self, query: str, groups: list[str], top_k: int = 5) -> list[SearchResult]:
        from .models import Document
        live = Document("live-001", "Current Inventory Notice", "Inventory availability changes frequently and must be checked at request time in the authoritative inventory service.", "inventory-api", "api://inventory/current", {"freshness": "live"}, ["all"])
        terms = set(query.lower().split())
        content = set(f"{live.title} {live.text}".lower().split())
        score = len(terms & content) / max(len(terms), 1)
        return [SearchResult(live, score, 1, query, "federated")] if score > 0 else []
