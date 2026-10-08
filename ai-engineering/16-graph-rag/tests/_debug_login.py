"""Quick debug script — runs a single login against the patched TestClient."""
import os
import sys

os.environ["LLM_MODE"] = "mock"
os.environ["JWT_SECRET"] = "test"

sys.path.insert(0, ".")
sys.path.insert(0, "tests")

from fastapi.testclient import TestClient
from api.app import main as api_main
from _fake_ch import FakeCHClient

_fake = FakeCHClient()
api_main.ch = _fake
client = TestClient(api_main.app)
r = client.post("/auth/login", json={"username": "admin", "password": "admin"})
print("status:", r.status_code)
print("body:", r.text[:300])
print("cookies:", dict(r.cookies))
