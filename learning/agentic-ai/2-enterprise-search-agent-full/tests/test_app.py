"""End-to-end API tests."""

import re

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

SEARCH_QUERY = "How should an agent reduce context bloat and use retry versus resume?"


def post_search(**overrides):
    payload = {"query": SEARCH_QUERY, "user_groups": ["analytics"]}
    payload.update(overrides)
    response = client.post("/search", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_health():
    body = client.get("/health").json()
    assert body["status"] == "healthy"
    assert body["indexed_documents"] > 0
    assert body["tools"] == 2


def test_tool_catalogue_exposes_json_schema():
    tools = {tool["name"]: tool for tool in client.get("/tools").json()["tools"]}
    assert set(tools) == {"get_order", "get_product"}
    assert tools["get_order"]["inputSchema"]["required"] == ["order_id"]
    assert tools["get_order"]["idempotent"] is True


def test_search_pipeline_is_grounded_and_within_budget():
    data = post_search()

    assert data["workload_type"] == "search"
    assert data["citations"]
    assert data["context_characters"] <= 3500
    assert data["trajectory_evaluation"]["trajectory_valid"] is True
    assert 0.0 < data["confidence"] <= 1.0

    executed = [step["name"] for step in data["trajectory"]]
    assert executed == [
        "classify",
        "rewrite",
        "fan_out",
        "retrieve",
        "rank_fusion",
        "rerank",
        "context_budget",
        "answer_generation",
    ]


@pytest.mark.parametrize("query", [SEARCH_QUERY, "Check ORDER-123456", "Price of SKU-99881?"])
def test_every_source_marker_has_a_matching_citation(query):
    """The grounding contract, on both paths: no answer may point at a citation
    that isn't there."""
    data = post_search(query=query)
    cited = {citation["source_number"] for citation in data["citations"]}
    referenced = {int(n) for n in re.findall(r"\[Source (\d+)\]", data["answer"])}
    assert referenced
    assert referenced <= cited


def test_rewrite_expands_jargon():
    data = post_search(query="What does MCP require?")
    assert "model context protocol" in data["rewritten_query"]


def test_fan_out_is_capped():
    data = post_search()
    assert 1 <= len(data["fanout_queries"]) <= 4
    assert len(set(data["fanout_queries"])) == len(data["fanout_queries"])


def test_exact_order_id_routes_to_the_order_tool():
    data = post_search(query="Check ORDER-123456")
    assert data["workload_type"] == "exact_lookup"
    assert "READY_FOR_PICKUP" in data["answer"]
    assert data["confidence"] == 1.0
    # No retrieval happened at all - that is the whole point of the routing.
    assert data["retrieved_documents"] == []
    assert [step["name"] for step in data["trajectory"]] == ["classify", "tool_call"]


def test_exact_sku_routes_to_the_product_tool_not_the_order_tool():
    """Regression: a SKU used to be sent to get_order just for looking like an ID."""
    data = post_search(query="What is the price of SKU-99881?")
    assert data["workload_type"] == "exact_lookup"
    assert data["trajectory"][1]["details"]["tool"] == "get_product"
    assert "Bulk Palm Cooking Oil" in data["answer"]


def test_acl_hides_restricted_documents():
    """A group that owns no policy documents must never see one cited."""
    restricted = post_search(query="promotion discount approval policy", user_groups=["guest"])
    allowed = post_search(query="promotion discount approval policy", user_groups=["commercial"])

    restricted_uris = {citation["uri"] for citation in restricted["citations"]}
    allowed_uris = {citation["uri"] for citation in allowed["citations"]}

    assert "sharepoint://promotion-policy" not in restricted_uris
    assert "sharepoint://promotion-policy" in allowed_uris


def test_resume_replays_completed_steps():
    first = post_search()
    replayed = post_search(run_id=first["run_id"], resume=True)

    assert replayed["run_id"] == first["run_id"]
    assert replayed["trajectory_evaluation"]["steps_replayed"] == len(first["trajectory"])
    assert replayed["answer"] == first["answer"]
    assert all(step["status"] == "cached" for step in replayed["trajectory"])


def test_search_is_deterministic():
    assert post_search()["answer"] == post_search()["answer"]


@pytest.mark.parametrize("query", ["a", ""])
def test_query_too_short_is_rejected_by_validation(query):
    assert client.post("/search", json={"query": query}).status_code == 422


def test_evaluate_endpoint():
    data = client.post(
        "/evaluate/search",
        json={
            "retrieved_ids": ["x", "tech-001", "tech-002"],
            "relevant_ids": ["tech-001", "tech-002"],
            "k": 3,
        },
    ).json()
    assert data["recall_at_k"] == 1.0
    assert data["mrr"] == 0.5
    assert data["precision_at_k"] == pytest.approx(2 / 3, abs=1e-3)
