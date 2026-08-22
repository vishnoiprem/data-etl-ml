from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json()["status"] == "healthy"

def test_search_pipeline():
    response = client.post("/search", json={"query": "How should an agent reduce context bloat and use retry versus resume?", "user_groups": ["analytics"]})
    assert response.status_code == 200
    data = response.json()
    assert data["citations"]
    assert data["context_characters"] <= 3500
    assert data["trajectory_evaluation"]["trajectory_valid"] is True

def test_exact_lookup():
    data = client.post("/search", json={"query": "Check ORDER-123456", "user_groups": ["analytics"]}).json()
    assert data["workload_type"] == "exact_lookup"
    assert "READY_FOR_PICKUP" in data["answer"]

def test_eval():
    data = client.post("/evaluate/search", json={"retrieved_ids": ["x", "tech-001", "tech-002"], "relevant_ids": ["tech-001", "tech-002"], "k": 3}).json()
    assert data["recall_at_k"] == 1.0
    assert data["mrr"] == 0.5
