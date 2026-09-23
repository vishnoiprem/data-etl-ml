import os
os.environ.setdefault("SERVING_ENDPOINT", "test-endpoint")
from fastapi.testclient import TestClient
from src.server import app

def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
