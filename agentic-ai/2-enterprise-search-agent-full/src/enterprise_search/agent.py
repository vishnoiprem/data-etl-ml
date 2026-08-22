"""The agent: one explicit, observable pipeline.

Control flow is ordinary Python, not an LLM deciding what to call next. For a
pipeline whose shape is known in advance, that is the right choice - it is
cheaper, it cannot loop forever, and every run produces the same trajectory,
which is what makes the whole thing testable.

The pipeline:

    classify -> (exact id?) -> tool call
             -> rewrite -> fan out -> retrieve -> fuse -> rerank
             -> context budget -> grounded answer -> trajectory
"""

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from .answer import (
    CONTEXT_CHARACTER_BUDGET,
    build_citations,
    select_evidence,
    write_grounded_answer,
)
from .checkpoints import CheckpointStore
from .planner import QueryPlanner
from .ranking import rerank, reciprocal_rank_fusion

RERANK_TOP_K = 5


@dataclass
class Step:
    """One row of the trajectory: what ran, whether it worked, how long it took.

    The trajectory is the agent's audit log. Without it, a wrong answer is
    unexplainable - you cannot tell whether retrieval missed the document, the
    reranker buried it, or the budget dropped it.
    """

    name: str
    status: str  # "success" | "cached" | "failed"
    latency_ms: float
    details: dict[str, Any] = field(default_factory=dict)


class SearchAgent:
    def __init__(self, index, federated, tools, checkpoints: CheckpointStore | None = None):
        self.index = index
        self.federated = federated
        self.tools = tools
        self.planner = QueryPlanner()
        self.checkpoints = checkpoints or CheckpointStore()

    # ----------------------------- step plumbing ----------------------------- #

    def _step(
        self,
        trajectory: list[Step],
        run_id: str,
        name: str,
        resume: bool,
        work: Callable[[], tuple[Any, dict]],
    ) -> Any:
        """Run one step, time it, checkpoint it, and record it in the trajectory.

        With ``resume=True`` a step that already succeeded under this ``run_id`` is
        replayed from its checkpoint instead of being executed again.
        """
        if resume:
            found, saved = self.checkpoints.get(run_id, name)
            if found:
                value, details = saved
                trajectory.append(Step(name, "cached", 0.0, {**details, "replayed": True}))
                return value

        started = time.perf_counter()
        try:
            value, details = work()
        except Exception as exc:
            elapsed = round((time.perf_counter() - started) * 1000, 3)
            trajectory.append(Step(name, "failed", elapsed, {"error": str(exc)}))
            raise

        elapsed = round((time.perf_counter() - started) * 1000, 3)
        self.checkpoints.put(run_id, name, (value, details))
        trajectory.append(Step(name, "success", elapsed, details))
        return value

    # -------------------------------- pipeline -------------------------------- #

    def run(
        self,
        query: str,
        groups: list[str],
        run_id: str | None = None,
        resume: bool = False,
    ) -> dict[str, Any]:
        run_id = run_id or str(uuid.uuid4())
        trajectory: list[Step] = []

        workload, match = self._step(
            trajectory, run_id, "classify", resume, lambda: self._classify(query)
        )

        if match is not None:
            return self._resolve_exact_id(trajectory, run_id, resume, query, workload, match)
        return self._search(trajectory, run_id, resume, query, workload, groups)

    def _classify(self, query: str):
        match = self.planner.exact_id(query)
        workload = self.planner.classify(query)
        details = {"workload_type": workload, "exact_id": match.value if match else None}
        return (workload, match), details

    def _resolve_exact_id(self, trajectory, run_id, resume, query, workload, match):
        """Exact identifier -> typed API call, no retrieval at all.

        Retrieval is the wrong tool for "where is ORDER-123456": the index is a
        stale copy, ranking is fuzzy, and the true answer lives in one row of a
        system of record. Detecting the ID and calling the API is faster, exact,
        and always current.
        """
        result = self._step(
            trajectory,
            run_id,
            "tool_call",
            resume,
            lambda: (
                self.tools.invoke(match.tool, {match.argument: match.value}),
                {"tool": match.tool, "argument": match.argument, "value": match.value},
            ),
        )

        return self._build_response(
            run_id=run_id,
            workload=workload,
            query=query,
            rewritten=query,  # no rewrite: the identifier is already exact
            fanout=[],
            # Same grounding contract as the search path: the answer cites its
            # source, even when that source is an API rather than a document.
            answer=f"{result['summary']} [Source 1]",
            citations=[
                {
                    "source_number": 1,
                    "title": f"{match.tool} (system of record)",
                    "uri": f"tool://{match.tool}/{match.value}",
                    "source": result.get("source", match.tool),
                }
            ],
            documents=[],
            trajectory=trajectory,
            confidence=1.0,  # deterministic lookup, not a ranked guess
            context_characters=0,
        )

    def _search(self, trajectory, run_id, resume, query, workload, groups):
        rewritten = self._step(
            trajectory, run_id, "rewrite", resume, lambda: self._rewrite(query)
        )

        queries = self._step(
            trajectory, run_id, "fan_out", resume, lambda: self._fan_out(query)
        )

        result_lists = self._step(
            trajectory, run_id, "retrieve", resume,
            lambda: self._retrieve(queries, groups),
        )

        fused = self._step(
            trajectory, run_id, "rank_fusion", resume,
            lambda: (
                reciprocal_rank_fusion(result_lists),
                {"input_lists": len(result_lists)},
            ),
        )

        ranked = self._step(
            trajectory, run_id, "rerank", resume,
            lambda: (rerank(query, fused, RERANK_TOP_K), {"candidates": len(fused), "top_k": RERANK_TOP_K}),
        )

        evidence, characters = self._step(
            trajectory, run_id, "context_budget", resume,
            lambda: self._budget(ranked),
        )

        answer = self._step(
            trajectory, run_id, "answer_generation", resume,
            lambda: (
                write_grounded_answer(query, evidence),
                {"evidence_documents": len(evidence)},
            ),
        )

        # Confidence is the top result's rerank score, already normalized to 0..1
        # by construction (the rerank weights sum to 1). No magic multiplier.
        confidence = round(max((hit.rerank_score for hit in evidence), default=0.0), 3)

        return self._build_response(
            run_id=run_id,
            workload=workload,
            query=query,
            rewritten=rewritten,
            fanout=queries,
            answer=answer,
            citations=build_citations(evidence),
            documents=[self._describe(hit) for hit in ranked],
            trajectory=trajectory,
            confidence=confidence,
            context_characters=characters,
        )

    def _rewrite(self, query: str):
        rewritten = self.planner.rewrite(query)
        expansion_count = len(rewritten.split()) - len(query.split())
        return rewritten, {"rewritten_query": rewritten, "terms_added": expansion_count}

    def _fan_out(self, query: str):
        queries = self.planner.fan_out(query)
        return queries, {"count": len(queries), "queries": queries}

    def _retrieve(self, queries: list[str], groups: list[str]):
        """Query every channel with every fan-out query.

        Each (query, channel) pair returns its own ranked list and stays separate
        until fusion, because fusion needs the ranks - flattening here would throw
        away the only information RRF can use.
        """
        result_lists = []
        for query in queries:
            result_lists.append(self.index.search(query, groups))
            result_lists.append(self.federated.search(query, groups))

        non_empty = [results for results in result_lists if results]
        details = {
            "queries": len(queries),
            "channels": 2,
            "lists_with_hits": len(non_empty),
            "candidates": sum(len(results) for results in non_empty),
        }
        return non_empty, details

    @staticmethod
    def _budget(ranked):
        evidence, characters = select_evidence(ranked)
        details = {
            "documents": len(evidence),
            "characters": characters,
            "limit": CONTEXT_CHARACTER_BUDGET,
            "dropped": len(ranked) - len(evidence),
        }
        return (evidence, characters), details

    @staticmethod
    def _describe(hit) -> dict[str, Any]:
        return {
            "id": hit.document.id,
            "title": hit.document.title,
            "rank": hit.rank,
            "channel": hit.channel,
            "retrieval_score": round(hit.retrieval_score, 6),
            "fusion_score": round(hit.fusion_score, 6),
            "rerank_score": round(hit.rerank_score, 6),
        }

    def _build_response(
        self, run_id, workload, query, rewritten, fanout, answer, citations,
        documents, trajectory, confidence, context_characters,
    ) -> dict[str, Any]:
        # A trajectory is valid when the run produced an answer, that answer is
        # backed by at least one citation, and it stayed inside the context
        # budget. Any of these failing means the answer should not be trusted.
        grounded = bool(answer) and bool(citations)
        within_budget = context_characters <= CONTEXT_CHARACTER_BUDGET

        return {
            "run_id": run_id,
            "workload_type": workload,
            "original_query": query,
            "rewritten_query": rewritten,
            "fanout_queries": fanout,
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
            "context_characters": context_characters,
            "retrieved_documents": documents,
            "trajectory": [asdict(step) for step in trajectory],
            "trajectory_evaluation": {
                "trajectory_valid": grounded and within_budget,
                "grounded": grounded,
                "context_within_budget": within_budget,
                "step_count": len(trajectory),
                "citation_count": len(citations),
                "steps_replayed": sum(1 for step in trajectory if step.status == "cached"),
                "total_latency_ms": round(sum(step.latency_ms for step in trajectory), 3),
            },
        }
