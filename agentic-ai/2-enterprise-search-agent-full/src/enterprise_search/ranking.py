import re
from collections import defaultdict
from .models import SearchResult

def rrf(lists: list[list[SearchResult]], constant: int = 60) -> list[SearchResult]:
    scores = defaultdict(float)
    best = {}
    for rows in lists:
        for rank, row in enumerate(rows, 1):
            scores[row.document.id] += 1 / (constant + rank)
            if row.document.id not in best or row.score > best[row.document.id].score:
                best[row.document.id] = row
    out = [SearchResult(best[k].document, v, query=best[k].query, channel=best[k].channel) for k, v in scores.items()]
    out.sort(key=lambda x: x.score, reverse=True)
    return out

def rerank(query: str, rows: list[SearchResult], top_k: int = 5) -> list[SearchResult]:
    q = set(re.findall(r"\w+", query.lower()))
    for row in rows:
        title = set(re.findall(r"\w+", row.document.title.lower()))
        body = set(re.findall(r"\w+", row.document.text.lower()))
        row.rerank_score = .55 * row.score + .3 * len(q & title) / max(len(q), 1) + .15 * len(q & body) / max(len(q), 1)
    rows.sort(key=lambda x: x.rerank_score, reverse=True)
    for rank, row in enumerate(rows[:top_k], 1):
        row.rank = rank
    return rows[:top_k]
