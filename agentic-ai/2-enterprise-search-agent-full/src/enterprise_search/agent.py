import math, re, time, uuid
from dataclasses import asdict, dataclass
from .planner import QueryPlanner
from .ranking import rrf, rerank

@dataclass
class Step:
    name: str
    status: str
    latency_ms: float
    details: dict

class SearchAgent:
    def __init__(self, index, federated, tools):
        self.index, self.federated, self.tools = index, federated, tools
        self.planner = QueryPlanner()
        self.checkpoints = {}

    def run_step(self, steps, name, fn):
        start = time.perf_counter()
        value, details = fn()
        steps.append(Step(name, "success", round((time.perf_counter()-start)*1000, 3), details))
        return value

    def run(self, query: str, groups: list[str], run_id=None, resume=False):
        run_id = run_id or str(uuid.uuid4())
        steps = []
        kind = self.run_step(steps, "classify", lambda: (self.planner.classify(query), {"query": query}))
        exact = self.planner.exact_id(query)
        if kind == "exact_lookup":
            order = self.run_step(steps, "tool_call", lambda: (self.tools.invoke("get_order", {"order_id": exact}), {"tool": "get_order", "idempotent": True}))
            answer = f"Order {order['order_id']} has status {order['status']} at {order['store']}. Total {order['total']} {order['currency']}."
            return self._response(run_id, kind, query, query, [query], answer, [{"title": "Legacy Order API", "uri": "legacy-api://orders"}], [], steps, 1.0)
        rewritten = self.run_step(steps, "rewrite", lambda: (self.planner.rewrite(query), {}))
        queries = self.run_step(steps, "fan_out", lambda: (self.planner.fan_out(query), {"count": 4}))
        lists = self.run_step(steps, "retrieve", lambda: ([result for q in queries for result in [self.index.search(q, groups), self.federated.search(q, groups)]], {"queries": len(queries)}))
        fused = self.run_step(steps, "rank_fusion", lambda: (rrf(lists), {"lists": len(lists)}))
        ranked = self.run_step(steps, "rerank", lambda: (rerank(query, fused, 5), {"top_k": 5}))
        selected, chars = [], 0
        for row in ranked:
            if chars + len(row.document.text) > 3500: break
            selected.append(row); chars += len(row.document.text)
        steps.append(Step("context_budget", "success", 0.0, {"documents": len(selected), "characters": chars, "limit": 3500}))
        qterms = set(re.findall(r"\w+", query.lower()))
        sentences = []
        for i, row in enumerate(selected, 1):
            for sentence in re.split(r"(?<=[.!?])\s+", row.document.text):
                overlap = len(qterms & set(re.findall(r"\w+", sentence.lower())))
                if overlap: sentences.append((overlap, sentence, i))
        sentences.sort(reverse=True)
        chosen = sentences[:4] or ([(1, selected[0].document.text, 1)] if selected else [])
        answer = " ".join(f"{s} [Source {i}]" for _, s, i in chosen) if chosen else "No authorized evidence was found."
        citations = [{"source_number": i, "title": r.document.title, "uri": r.document.uri, "source": r.document.source} for i, r in enumerate(selected, 1)]
        confidence = min(1.0, max([r.rerank_score for r in selected], default=0) * 4)
        steps.append(Step("answer_generation", "success", 0.0, {"citations": len(citations)}))
        docs = [{"id": r.document.id, "title": r.document.title, "rank": r.rank, "channel": r.channel, "score": round(r.score, 6), "rerank_score": round(r.rerank_score, 6)} for r in ranked]
        return self._response(run_id, kind, query, rewritten, queries, answer, citations, docs, steps, round(confidence, 3), chars)

    def _response(self, run_id, kind, query, rewritten, queries, answer, citations, docs, steps, confidence, chars=0):
        valid = bool(answer) and bool(citations) and chars <= 3500
        return {"run_id": run_id, "workload_type": kind, "original_query": query, "rewritten_query": rewritten, "fanout_queries": queries, "answer": answer, "citations": citations, "confidence": confidence, "context_characters": chars, "retrieved_documents": docs, "trajectory": [asdict(x) for x in steps], "trajectory_evaluation": {"trajectory_valid": valid, "step_count": len(steps), "citation_count": len(citations)}}

def dcg(values):
    return sum(v / math.log2(i + 2) for i, v in enumerate(values))

def evaluate_search(retrieved, relevant, k=5):
    take, truth = retrieved[:k], set(relevant)
    hits = [x for x in take if x in truth]
    rr = next((1/i for i, x in enumerate(retrieved, 1) if x in truth), 0)
    rel = [1 if x in truth else 0 for x in take]
    ideal = sorted(rel, reverse=True)
    return {"precision_at_k": round(len(hits)/max(len(take),1),3), "recall_at_k": round(len(hits)/max(len(truth),1),3), "mrr": round(rr,3), "ndcg_at_k": round(dcg(rel)/dcg(ideal),3) if dcg(ideal) else 0.0}
