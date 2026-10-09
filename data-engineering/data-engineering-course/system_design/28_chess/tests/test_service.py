"""Tests for the Chess service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import ChessService, INITIAL_BOARD  # noqa: E402


class ChessServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = ChessService()

    def test_initial_board(self):
        g = self.svc.create_game(white_id=1, black_id=2)
        self.assertEqual(g.board[0], list("rnbqkbnr"))
        self.assertEqual(g.board[7], list("RNBQKBNR"))
        self.assertEqual(g.turn, "W")
        self.assertEqual(g.status, "IN_PROGRESS")

    def test_basic_pawn_move(self):
        g = self.svc.create_game(white_id=1, black_id=2)
        r = self.svc.submit_move(g.game_id, 1, "e2", "e4")
        self.assertEqual(r["status"], "IN_PROGRESS")
        self.assertEqual(self.svc.get_game(g.game_id).turn, "B")

    def test_illegal_move_rejected(self):
        g = self.svc.create_game(white_id=1, black_id=2)
        with self.assertRaises(ValueError):
            # pawn can't move 3 squares
            self.svc.submit_move(g.game_id, 1, "e2", "e5")

    def test_knight_move(self):
        g = self.svc.create_game(white_id=1, black_id=2)
        self.svc.submit_move(g.game_id, 1, "e2", "e4")
        r = self.svc.submit_move(g.game_id, 2, "e7", "e5")
        self.assertEqual(r["status"], "IN_PROGRESS")
        r = self.svc.submit_move(g.game_id, 1, "g1", "f3")
        self.assertEqual(r["status"], "IN_PROGRESS")

    def test_castling_kingside(self):
        g = self.svc.create_game(white_id=1, black_id=2)
        # Clear path: e2-e4, d2-d3, f2-f3, g2-g3, h2-h3 then Ng1-f3, Bf1-e2, etc.
        # Easier: build a position where white can castle.
        # Empty row 7 except king+rook, row 6 empty.
        b = [row[:] for row in INITIAL_BOARD]
        b[7] = list("R...K..R")
        b[6] = list("........")
        b[0] = list("r...k..r")
        b[1] = list("........")
        # set via a "test" route? We instead clear through captures:
        # The simplest is to call internal helpers via creating a game then mutating.
        g.board = b
        g.castling = "KQkq"
        self.svc.games.set(f"game:{g.game_id}", g.to_dict())
        r = self.svc.submit_move(g.game_id, 1, "e1", "g1")
        self.assertEqual(r["status"], "IN_PROGRESS")
        self.assertIn("O-O", r["san"])

    def test_castling_blocked_by_check(self):
        g = self.svc.create_game(white_id=1, black_id=2)
        b = [row[:] for row in INITIAL_BOARD]
        b[7] = list("R...K..R")
        b[6] = list("........")
        b[0] = list("r...k..r")
        b[1] = list("........")
        b[3] = list("...r....")  # black rook attacking e1
        b[4] = list("....n...")  # extra
        g.board = b
        g.castling = "KQkq"
        self.svc.games.set(f"game:{g.game_id}", g.to_dict())
        with self.assertRaises(ValueError):
            # King is in check, can't castle
            self.svc.submit_move(g.game_id, 1, "e1", "g1")

    def test_en_passant(self):
        g = self.svc.create_game(white_id=1, black_id=2)
        b = [row[:] for row in INITIAL_BOARD]
        # Set up: white pawn on e5, black pawn on d7. Black plays d7-d5.
        b[3] = list("....P...")
        b[1] = list("...p....")
        g.board = b
        g.turn = "B"
        self.svc.games.set(f"game:{g.game_id}", g.to_dict())
        # Black moves d7->d5
        self.svc.submit_move(g.game_id, 2, "d7", "d5")
        g = self.svc.get_game(g.game_id)
        # Now white plays e5xd6 en passant
        r = self.svc.submit_move(g.game_id, 1, "e5", "d6")
        # d5 pawn should be gone
        g2 = self.svc.get_game(g.game_id)
        self.assertEqual(g2.board[3][3], ".")  # d5 empty (the captured pawn)

    def test_promotion(self):
        g = self.svc.create_game(white_id=1, black_id=2)
        b = [row[:] for row in INITIAL_BOARD]
        # White pawn on a7, rest empty
        for r in range(8):
            for f in range(8):
                b[r][f] = "."
        b[6][0] = "P"
        b[1][4] = "k"  # black king
        b[0][0] = "K"  # white king (so it's not stalemate at start)
        g.board = b
        g.castling = ""
        g.turn = "W"
        self.svc.games.set(f"game:{g.game_id}", g.to_dict())
        r = self.svc.submit_move(g.game_id, 1, "a7", "a8", promotion="q")
        self.assertEqual(g.board[0][0] if False else self.svc.get_game(g.game_id).board[0][0], "Q")

    def test_checkmate_fools(self):
        # Fool's mate: 1.f3 e5 2.g4 Qh4#
        g = self.svc.create_game(white_id=1, black_id=2)
        self.svc.submit_move(g.game_id, 1, "f2", "f3")
        self.svc.submit_move(g.game_id, 2, "e7", "e5")
        self.svc.submit_move(g.game_id, 1, "g2", "g4")
        r = self.svc.submit_move(g.game_id, 2, "d8", "h4")
        self.assertEqual(r["status"], "ENDED")
        self.assertEqual(r["result"], "BLACK_WIN")

    def test_resign(self):
        g = self.svc.create_game(white_id=1, black_id=2)
        g2 = self.svc.resign(g.game_id, 1)
        self.assertEqual(g2.status, "ENDED")
        self.assertEqual(g2.result, "BLACK_WIN")

    def test_matchmaking(self):
        r1 = self.svc.enqueue(100)
        r2 = self.svc.enqueue(200)
        # First enqueue waits, second matches and creates a game.
        self.assertEqual(r1["status"], "waiting")
        self.assertEqual(r2["status"], "matched")
        self.assertIn("game_id", r2)


if __name__ == "__main__":
    unittest.main()
