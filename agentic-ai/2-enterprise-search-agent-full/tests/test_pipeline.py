"""Unit tests for each pipeline stage, no HTTP involved."""

import pytest

from src.enterprise_search.answer import select_evidence, write_grounded_answer
from src.enterprise_search.checkpoints import CheckpointStore
from src.enterprise_search.evaluation import evaluate_search
from src.enterprise_search.index import LocalIndex
from src.enterprise_search.models import Document, SearchResult
from src.enterprise_search.planner import QueryPlanner
from src.enterprise_search.ranking import reciprocal_rank_fusion, rerank
from src.enterprise_search.tools import ToolError, default_registry


def make_hit(doc_id: str, score: float = 0.5, text: str = "some text", title: str = "Title"):
    return SearchResult(Document(doc_id, title, text, "test", f"test://{doc_id}"), score)


# ------------------------------- planner ---------------------------------- #

class TestPlanner:
    planner = QueryPlanner()

    @pytest.mark.parametrize(
        "query, tool",
        [
            ("where is ORDER-123456", "get_order"),
            ("status of ord_998877", "get_order"),
            ("price for SKU-99881", "get_product"),
        ],
    )
    def test_identifiers_route_to_their_own_tool(self, query, tool):
        assert self.planner.exact_id(query).tool == tool

    def test_plain_question_has_no_identifier(self):
        assert self.planner.exact_id("how do we reduce context bloat") is None

    @pytest.mark.parametrize(
        "query, workload",
        [
            ("ORDER-123456", "exact_lookup"),
            ("why did the promotion fail", "analytical"),
            ("cooking oil pack sizes", "search"),
        ],
    )
    def test_classify(self, query, workload):
        assert self.planner.classify(query) == workload

    def test_rewrite_adds_synonyms_without_dropping_the_original_words(self):
        rewritten = self.planner.rewrite("MCP retry rules")
        assert "mcp" in rewritten
        assert "model context protocol" in rewritten
        assert "transient failure repeat" in rewritten

    def test_fan_out_is_capped_and_unique(self):
        queries = self.planner.fan_out("context budget", limit=3)
        assert len(queries) == 3
        assert len(set(queries)) == 3


# ---------------------------- indexed retrieval --------------------------- #

class TestLocalIndex:
    documents = [
        Document("pub", "Public Oil Guide", "palm cooking oil in ten litre packs", "catalog", "u://1"),
        Document("sec", "Secret Margin Report", "palm cooking oil margin targets", "finance", "u://2", acl=["finance"]),
    ]

    def test_authorized_group_sees_both(self):
        hits = LocalIndex(self.documents).search("palm cooking oil", ["finance"])
        assert {hit.document.id for hit in hits} == {"pub", "sec"}

    def test_unauthorized_group_never_sees_the_restricted_document(self):
        hits = LocalIndex(self.documents).search("palm cooking oil", ["marketing"])
        assert {hit.document.id for hit in hits} == {"pub"}

    def test_results_are_ranked_and_numbered_from_one(self):
        hits = LocalIndex(self.documents).search("palm cooking oil", ["finance"])
        assert [hit.rank for hit in hits] == [1, 2]
        assert hits[0].retrieval_score >= hits[1].retrieval_score


# --------------------------------- fusion --------------------------------- #

class TestFusion:
    def test_agreement_between_lists_beats_a_single_strong_hit(self):
        list_a = [make_hit("agreed", 0.20), make_hit("only-a", 0.99)]
        list_b = [make_hit("agreed", 0.15)]

        fused = reciprocal_rank_fusion([list_a, list_b])

        assert fused[0].document.id == "agreed"
        assert fused[0].fusion_score > fused[1].fusion_score

    def test_duplicates_collapse_to_one_entry_per_document(self):
        fused = reciprocal_rank_fusion([[make_hit("same")], [make_hit("same")], [make_hit("same")]])
        assert len(fused) == 1

    def test_representative_keeps_the_strongest_retrieval_score(self):
        fused = reciprocal_rank_fusion([[make_hit("d", 0.1)], [make_hit("d", 0.8)]])
        assert fused[0].retrieval_score == 0.8


# -------------------------------- reranking ------------------------------- #

class TestRerank:
    def test_scores_stay_inside_zero_to_one(self):
        hits = reciprocal_rank_fusion([[make_hit("a", 0.5, title="context budget guide")]])
        ranked = rerank("context budget", hits)
        assert 0.0 <= ranked[0].rerank_score <= 1.0

    def test_title_match_outranks_a_body_only_match(self):
        title_match = make_hit("title", 0.5, title="Context Budget Standard", text="unrelated prose")
        body_match = make_hit("body", 0.5, title="Unrelated Notes", text="context budget appears here")

        ranked = rerank("context budget", reciprocal_rank_fusion([[title_match], [body_match]]))
        assert ranked[0].document.id == "title"

    def test_fusion_score_still_influences_the_order(self):
        """Guards the normalization fix: raw RRF scores are ~0.016, so without
        normalizing they would be swamped by the 0..1 overlap terms."""
        agreed = make_hit("agreed", 0.5, title="Alpha", text="alpha")
        loner = make_hit("loner", 0.5, title="Alpha", text="alpha")

        ranked = rerank("alpha", reciprocal_rank_fusion([[agreed], [agreed], [loner]]))
        assert ranked[0].document.id == "agreed"

    def test_empty_candidates(self):
        assert rerank("anything", []) == []


# ----------------------------- context budget ----------------------------- #

class TestContextBudget:
    def test_an_oversized_document_is_skipped_not_treated_as_a_stop_signal(self):
        """Regression: the loop used to `break`, so one long document starved
        every shorter document ranked behind it."""
        huge = make_hit("huge", text="x" * 4000)
        small = make_hit("small", text="y" * 100)

        evidence, characters = select_evidence([huge, small], budget=3500)

        assert [hit.document.id for hit in evidence] == ["small"]
        assert characters == 100

    def test_budget_is_never_exceeded(self):
        hits = [make_hit(f"d{i}", text="z" * 1000) for i in range(10)]
        evidence, characters = select_evidence(hits, budget=3500)
        assert characters <= 3500
        assert len(evidence) == 3

    def test_repeated_documents_are_only_paid_for_once(self):
        evidence, characters = select_evidence([make_hit("d", text="abc")] * 3)
        assert len(evidence) == 1
        assert characters == 3


# --------------------------- answer generation ---------------------------- #

class TestGroundedAnswer:
    def test_every_sentence_carries_a_source_marker(self):
        hit = make_hit("d", text="Context budgets cap evidence. Something unrelated entirely.")
        answer = write_grounded_answer("context budgets", [hit])
        assert "[Source 1]" in answer
        assert "Something unrelated" not in answer

    def test_no_evidence_produces_an_explicit_refusal_not_a_guess(self):
        answer = write_grounded_answer("anything", [])
        assert "No authorized evidence" in answer

    def test_falls_back_to_one_sentence_when_nothing_overlaps(self):
        hit = make_hit("d", text="First sentence here. Second sentence here.")
        answer = write_grounded_answer("zzz nonexistent", [hit])
        assert answer == "First sentence here. [Source 1]"


# ------------------------------- evaluation ------------------------------- #

class TestEvaluation:
    def test_precision_divides_by_k_not_by_result_count(self):
        """Returning fewer results must not inflate the score."""
        assert evaluate_search(["a"], ["a"], k=5)["precision_at_k"] == 0.2

    def test_duplicates_cannot_inflate_precision(self):
        assert evaluate_search(["a", "a", "a"], ["a"], k=3)["precision_at_k"] == 0.333

    def test_perfect_ranking(self):
        result = evaluate_search(["a", "b"], ["a", "b"], k=2)
        assert result == {
            "k": 2,
            "precision_at_k": 1.0,
            "recall_at_k": 1.0,
            "mrr": 1.0,
            "ndcg_at_k": 1.0,
        }

    def test_nothing_relevant_retrieved(self):
        result = evaluate_search(["x", "y"], ["a"], k=2)
        assert result["mrr"] == 0.0
        assert result["ndcg_at_k"] == 0.0

    def test_ndcg_rewards_putting_the_relevant_document_first(self):
        first = evaluate_search(["a", "x", "y"], ["a"], k=3)["ndcg_at_k"]
        last = evaluate_search(["x", "y", "a"], ["a"], k=3)["ndcg_at_k"]
        assert first > last

    def test_relevant_document_outside_the_cutoff_does_not_count(self):
        assert evaluate_search(["x", "y", "a"], ["a"], k=2)["recall_at_k"] == 0.0


# ------------------------------ tool contract ----------------------------- #

class TestToolRegistry:
    registry = default_registry()

    def test_valid_call(self):
        assert self.registry.invoke("get_order", {"order_id": "ORDER-1"})["status"] == "READY_FOR_PICKUP"

    def test_unknown_tool(self):
        with pytest.raises(ToolError, match="unknown tool"):
            self.registry.invoke("delete_everything", {})

    def test_missing_required_argument(self):
        with pytest.raises(ToolError, match="missing required"):
            self.registry.invoke("get_order", {})

    def test_unexpected_argument_is_rejected(self):
        with pytest.raises(ToolError, match="unexpected"):
            self.registry.invoke("get_order", {"order_id": "ORDER-1", "drop_table": "users"})

    def test_wrong_type_is_rejected(self):
        with pytest.raises(ToolError, match="must be string"):
            self.registry.invoke("get_order", {"order_id": 123})


# ------------------------------- checkpoints ------------------------------ #

class TestCheckpointStore:
    def test_found_flag_distinguishes_a_missing_step_from_a_none_result(self):
        store = CheckpointStore()
        store.put("run", "step", None)
        assert store.get("run", "step") == (True, None)
        assert store.get("run", "other") == (False, None)

    def test_runs_are_isolated_and_clearable(self):
        store = CheckpointStore()
        store.put("run-a", "step", 1)
        store.put("run-b", "step", 2)
        assert store.get("run-b", "step") == (True, 2)

        store.clear("run-a")
        assert store.get("run-a", "step") == (False, None)
        assert store.completed_steps("run-b") == ["step"]
