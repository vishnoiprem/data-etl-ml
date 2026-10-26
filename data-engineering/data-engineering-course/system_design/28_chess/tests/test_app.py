"""HTTP tests for the Chess service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import ChessService  # noqa: E402


class ChessAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = ChessService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_e2e_game(self):
        r = self.client.post(
            "/api/games", json={"white_id": 1, "black_id": 2}
        )
        self.assertEqual(r.status_code, 201)
        gid = r.get_json()["game_id"]
        r = self.client.post(
            f"/api/games/{gid}/moves",
            json={"user_id": 1, "from_sq": "e2", "to_sq": "e4"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "IN_PROGRESS")
        r = self.client.post(
            f"/api/games/{gid}/moves",
            json={"user_id": 2, "from_sq": "e7", "to_sq": "e5"},
        )
        self.assertEqual(r.status_code, 200)
        r = self.client.get(f"/api/games/{gid}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["history"]), 2)

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_illegal_move_returns_400(self):
        r = self.client.post("/api/games", json={"white_id": 1, "black_id": 2})
        gid = r.get_json()["game_id"]
        r = self.client.post(
            f"/api/games/{gid}/moves",
            json={"user_id": 1, "from_sq": "e2", "to_sq": "e5"},
        )
        self.assertEqual(r.status_code, 400)

    def test_matchmaking_endpoint(self):
        r = self.client.get("/api/matchmaking?user_id=42")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "waiting")
        r = self.client.get("/api/matchmaking?user_id=43")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "matched")

    def test_resign_endpoint(self):
        r = self.client.post("/api/games", json={"white_id": 1, "black_id": 2})
        gid = r.get_json()["game_id"]
        r = self.client.post(
            f"/api/games/{gid}/resign", json={"user_id": 1}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["result"], "BLACK_WIN")


if __name__ == "__main__":
    unittest.main()
