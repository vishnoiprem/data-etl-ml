"""Chess service: full rules (castling, en-passant, promotion, check, mate).

Board is a list-of-lists 8x8, index [rank][file] from WHITE's perspective
(rank 0 = rank 1, rank 7 = rank 8). Pieces: upper = white, lower = black.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.ids import Snowflake
from common.storage import KeyValueStore

PENDING = "PENDING"
IN_PROGRESS = "IN_PROGRESS"
ENDED = "ENDED"

WHITE_WIN = "WHITE_WIN"
BLACK_WIN = "BLACK_WIN"
DRAW = "DRAW"

INITIAL_BOARD = [
    list("rnbqkbnr"),
    list(".ppppppp"),
    list("........"),
    list("........"),
    list("........"),
    list("........"),
    list("PPPPPPPP"),
    list("RNBQKBNR"),
]


def sq_to_idx(sq: str) -> tuple:
    """algebraic like 'e2' -> (rank, file) zero-based."""
    if len(sq) != 2:
        raise ValueError(f"bad square: {sq}")
    f = ord(sq[0].lower()) - ord("a")
    r = int(sq[1]) - 1
    if not (0 <= f < 8 and 0 <= r < 8):
        raise ValueError(f"out of bounds: {sq}")
    return r, f


def idx_to_sq(r: int, f: int) -> str:
    return chr(ord("a") + f) + str(r + 1)


@dataclass
class Game:
    game_id: int
    white_id: Optional[int]
    black_id: Optional[int]
    board: list
    turn: str  # "W" or "B"
    status: str
    result: Optional[str]
    history: list = field(default_factory=list)
    castling: str = "KQkq"  # rights still available
    en_passant: Optional[str] = None
    halfmove_clock: int = 0
    fullmove_number: int = 1
    ply: int = 0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class ChessService:
    """Authoritative chess service with full rules.

    >>> svc = ChessService()
    >>> g = svc.create_game(white_id=1, black_id=2)
    >>> m = svc.submit_move(g.game_id, user_id=1, from_sq="e2", to_sq="e4")
    >>> m["status"]
    'IN_PROGRESS'
    """

    def __init__(self):
        self.snow = Snowflake(machine_id=28)
        self.games = KeyValueStore("chess_games")
        self.queue = KeyValueStore("chess_queue")  # ordered list of (uid, ts)
        self.user_game = KeyValueStore("chess_user_game")  # uid -> game_id
        # listener registry: game_id -> [Queue]
        self._listeners: dict[int, list] = {}

    # ---- lifecycle ----------------------------------------------------

    def create_game(
        self, white_id: Optional[int] = None, black_id: Optional[int] = None
    ) -> Game:
        gid = self.snow.next_id()
        g = Game(
            game_id=gid,
            white_id=white_id,
            black_id=black_id,
            board=[row[:] for row in INITIAL_BOARD],
            turn="W",
            status=PENDING if (white_id is None or black_id is None) else IN_PROGRESS,
            result=None,
            history=[],
            castling="KQkq",
            en_passant=None,
            halfmove_clock=0,
            fullmove_number=1,
            ply=0,
            created_at=time.time(),
        )
        self.games.set(f"game:{gid}", g.to_dict())
        if white_id is not None:
            self.user_game.set(f"user_game:{white_id}", gid)
        if black_id is not None:
            self.user_game.set(f"user_game:{black_id}", gid)
        return g

    def get_game(self, game_id: int) -> Optional[Game]:
        d = self.games.get(f"game:{game_id}")
        return Game(**d) if d else None

    def join(self, game_id: int, user_id: int, color: str = "any") -> Game:
        g = self.get_game(game_id)
        if not g:
            raise ValueError("game not found")
        uid = int(user_id)
        if color not in ("white", "black", "any"):
            raise ValueError("color must be white|black|any")
        # Already joined?
        if uid in (g.white_id, g.black_id):
            return g
        if color == "white" and g.white_id is None:
            g.white_id = uid
        elif color == "black" and g.black_id is None:
            g.black_id = uid
        elif color == "any":
            if g.white_id is None:
                g.white_id = uid
            elif g.black_id is None:
                g.black_id = uid
            else:
                raise ValueError("game is full")
        else:
            raise ValueError("requested color is taken")
        if g.white_id is not None and g.black_id is not None:
            g.status = IN_PROGRESS
        self.games.set(f"game:{game_id}", g.to_dict())
        self.user_game.set(f"user_game:{uid}", game_id)
        return g

    def resign(self, game_id: int, user_id: int) -> Game:
        g = self.get_game(game_id)
        if not g:
            raise ValueError("game not found")
        if g.status == ENDED:
            return g
        uid = int(user_id)
        if uid == g.white_id:
            g.result = BLACK_WIN
        elif uid == g.black_id:
            g.result = WHITE_WIN
        else:
            raise ValueError("only a player can resign")
        g.status = ENDED
        self.games.set(f"game:{game_id}", g.to_dict())
        self._broadcast(g)
        return g

    # ---- matchmaking --------------------------------------------------

    def enqueue(self, user_id: int) -> dict:
        uid = int(user_id)
        q = self.queue.get("queue") or []
        if any(item[0] == uid for item in q):
            return {"status": "waiting"}
        q.append([uid, time.time()])
        self.queue.set("queue", q)
        if len(q) >= 2:
            q.sort(key=lambda x: x[1])
            a = q.pop(0)[0]
            b = q.pop(0)[0]
            self.queue.set("queue", q)
            g = self.create_game(white_id=a, black_id=b)
            return {"status": "matched", "game_id": g.game_id, "opponent_id": b}
        return {"status": "waiting"}

    def queue_size(self) -> int:
        return len(self.queue.get("queue") or [])

    # ---- moves --------------------------------------------------------

    def submit_move(
        self,
        game_id: int,
        user_id: int,
        from_sq: str,
        to_sq: str,
        promotion: Optional[str] = None,
    ) -> dict:
        g = self.get_game(game_id)
        if not g:
            raise ValueError("game not found")
        if g.status == ENDED:
            raise ValueError("game is over")
        if g.status == PENDING:
            raise ValueError("game not yet started")
        uid = int(user_id)
        if g.turn == "W" and uid != g.white_id:
            raise ValueError("not your turn")
        if g.turn == "B" and uid != g.black_id:
            raise ValueError("not your turn")
        fr = sq_to_idx(from_sq)
        to = sq_to_idx(to_sq)
        piece = g.board[fr[0]][fr[1]]
        if piece == ".":
            raise ValueError("no piece on from_sq")
        if (piece.isupper() and g.turn != "W") or (piece.islower() and g.turn != "B"):
            raise ValueError("wrong color for current turn")
        # Validate the move.
        san = self._apply_move(g, fr, to, promotion)
        # After move, does the mover's own king remain (was in check only
        # before the move). _apply_move handles check detection.
        g.ply += 1
        g.fullmove_number += 0 if g.turn == "W" else 1
        g.turn = "B" if g.turn == "W" else "W"
        # Check for terminal state on the side to move.
        terminal = self._terminal_status(g)
        if terminal:
            g.status = ENDED
            g.result = terminal
        self.games.set(f"game:{game_id}", g.to_dict())
        self._broadcast(g)
        return {
            "game_id": game_id,
            "san": san,
            "status": g.status,
            "result": g.result,
            "turn": g.turn,
            "ply": g.ply,
            "fen_like": self._board_to_str(g),
        }

    # ---- listeners ----------------------------------------------------

    def _broadcast(self, g: Game) -> None:
        for q in list(self._listeners.get(g.game_id, [])):
            try:
                q.put_nowait(g.to_dict())
            except Exception:
                pass

    def register_listener(self, game_id: int):
        import queue
        q = queue.Queue(maxsize=200)
        self._listeners.setdefault(game_id, []).append(q)
        return q

    def unregister_listener(self, game_id: int, q) -> None:
        lst = self._listeners.get(game_id, [])
        if q in lst:
            lst.remove(q)

    # ---- move logic ---------------------------------------------------

    def _apply_move(
        self, g: Game, fr: tuple, to: tuple, promotion: Optional[str]
    ) -> str:
        r0, f0 = fr
        r1, f1 = to
        piece = g.board[r0][f0]
        color = "W" if piece.isupper() else "B"
        target = g.board[r1][f1]

        legal = self._legal_moves(g, color)
        if (r1, f1) not in legal.get((r0, f0), []):
            raise ValueError("illegal move")

        # Capture en-passant: if pawn moves diagonally to an empty square,
        # remove the captured pawn on the same rank as 'from'.
        ep_capture = False
        if piece.lower() == "p" and f0 != f1 and target == ".":
            ep_capture = True

        # Build SAN (algebraic). Toy SAN — disambiguation not handled.
        san_piece = "" if piece.lower() == "p" else piece.upper()
        if target != "." or ep_capture:
            san_piece = san_piece if piece.lower() != "p" else (from_sq_file(fr) if False else from_sq_file(fr))
            san = f"{san_piece or from_sq_file(fr)}x{idx_to_sq(r1, f1)}"
        else:
            san = f"{san_piece}{idx_to_sq(r1, f1)}"

        # Move the piece.
        g.board[r1][f1] = piece
        g.board[r0][f0] = "."

        # En-passant capture removal.
        if ep_capture:
            captured_rank = r0
            g.board[captured_rank][f1] = "."

        # Set en-passant target square.
        g.en_passant = None
        if piece.lower() == "p" and abs(r1 - r0) == 2:
            ep_rank = (r0 + r1) // 2
            g.en_passant = idx_to_sq(ep_rank, f0)

        # Castling rights updates.
        if piece == "K":
            g.castling = g.castling.replace("K", "").replace("Q", "")
            # If castling, also move the rook.
            if abs(f1 - f0) == 2:
                if f1 > f0:  # kingside
                    g.board[r0][5] = g.board[r0][7]
                    g.board[r0][7] = "."
                    san = "O-O"
                else:  # queenside
                    g.board[r0][3] = g.board[r0][0]
                    g.board[r0][0] = "."
                    san = "O-O-O"
        elif piece == "k":
            g.castling = g.castling.replace("k", "").replace("q", "")
            if abs(f1 - f0) == 2:
                if f1 > f0:
                    g.board[r0][5] = g.board[r0][7]
                    g.board[r0][7] = "."
                    san = "O-O"
                else:
                    g.board[r0][3] = g.board[r0][0]
                    g.board[r0][0] = "."
                    san = "O-O-O"
        if fr == (7, 0) or to == (7, 0):
            g.castling = g.castling.replace("Q", "")
        if fr == (7, 7) or to == (7, 7):
            g.castling = g.castling.replace("K", "")
        if fr == (0, 0) or to == (0, 0):
            g.castling = g.castling.replace("q", "")
        if fr == (0, 7) or to == (0, 7):
            g.castling = g.castling.replace("k", "")

        # Promotion.
        if piece.lower() == "p" and (r1 == 0 or r1 == 7):
            promo = (promotion or "q").lower()
            if promo not in ("q", "r", "b", "n"):
                raise ValueError("promotion must be q|r|b|n")
            new_piece = promo.upper() if color == "W" else promo
            g.board[r1][f1] = new_piece
            san = san + "=" + promo.upper()

        # Check / mate annotation.
        opp = "B" if color == "W" else "W"
        if self._in_check(g, opp):
            if self._no_legal_moves(g, opp):
                san = san + "#"
            else:
                san = san + "+"

        # Halfmove clock.
        if piece.lower() == "p" or target != "." or ep_capture:
            g.halfmove_clock = 0
        else:
            g.halfmove_clock += 1

        g.history.append({
            "from": idx_to_sq(r0, f0),
            "to": idx_to_sq(r1, f1),
            "promotion": promotion,
            "san": san,
        })
        return san

    def _legal_moves(self, g: Game, color: str) -> dict:
        """Return {from_sq: [to_sq, ...]}."""
        moves: dict = {}
        for r in range(8):
            for f in range(8):
                p = g.board[r][f]
                if p == "." or (color == "W" and not p.isupper()) or (color == "B" and not p.islower()):
                    continue
                raw = self._pseudo_moves(g, r, f, color)
                # Filter: a move is legal only if own king is not left in check.
                legal_for_piece = []
                for (r1, f1, special) in raw:
                    if self._move_keeps_king_safe(g, r, f, r1, f1, special, color):
                        legal_for_piece.append((r1, f1))
                if legal_for_piece:
                    moves[(r, f)] = legal_for_piece
        return moves

    def _pseudo_moves(self, g: Game, r: int, f: int, color: str):
        piece = g.board[r][f]
        p = piece.lower()
        out = []
        if p == "p":
            direction = -1 if color == "W" else 1
            start_rank = 6 if color == "W" else 1
            promote_rank = 0 if color == "W" else 7
            # Forward
            nr = r + direction
            if 0 <= nr < 8 and g.board[nr][f] == ".":
                if nr == promote_rank:
                    for promo in ("q", "r", "b", "n"):
                        out.append((nr, f, ("promo", promo)))
                else:
                    out.append((nr, f, None))
                # Double push from start
                if r == start_rank:
                    nr2 = r + 2 * direction
                    if g.board[nr2][f] == ".":
                        out.append((nr2, f, ("double",)))
            # Captures
            for df in (-1, 1):
                nf = f + df
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = g.board[nr][nf]
                    if target != "." and ((color == "W" and target.islower()) or (color == "B" and target.isupper())):
                        if nr == promote_rank:
                            for promo in ("q", "r", "b", "n"):
                                out.append((nr, nf, ("promo", promo)))
                        else:
                            out.append((nr, nf, None))
                    elif g.en_passant == idx_to_sq(nr, nf):
                        out.append((nr, nf, ("en_passant",)))
        elif p == "n":
            for dr, df in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                nr, nf = r + dr, f + df
                if 0 <= nr < 8 and 0 <= nf < 8:
                    t = g.board[nr][nf]
                    if t == "." or (color == "W" and t.islower()) or (color == "B" and t.isupper()):
                        out.append((nr, nf, None))
        elif p in ("b", "r", "q"):
            directions = []
            if p == "b":
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            elif p == "r":
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            else:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, df in directions:
                nr, nf = r + dr, f + df
                while 0 <= nr < 8 and 0 <= nf < 8:
                    t = g.board[nr][nf]
                    if t == ".":
                        out.append((nr, nf, None))
                    elif (color == "W" and t.islower()) or (color == "B" and t.isupper()):
                        out.append((nr, nf, None))
                        break
                    else:
                        break
                    nr += dr
                    nf += df
        elif p == "k":
            for dr in (-1, 0, 1):
                for df in (-1, 0, 1):
                    if dr == 0 and df == 0:
                        continue
                    nr, nf = r + dr, f + df
                    if 0 <= nr < 8 and 0 <= nf < 8:
                        t = g.board[nr][nf]
                        if t == "." or (color == "W" and t.islower()) or (color == "B" and t.isupper()):
                            out.append((nr, nf, None))
            # Castling
            if not self._in_check(g, color):
                rank = 7 if color == "W" else 0
                if r == rank and f == 4:
                    if color == "W":
                        if "K" in g.castling and g.board[rank][5] == "." and g.board[rank][6] == "." \
                                and g.board[rank][7] == "R" \
                                and not self._sq_attacked(g, rank, 5, "B") \
                                and not self._sq_attacked(g, rank, 6, "B"):
                            out.append((rank, 6, ("castle",)))
                        if "Q" in g.castling and g.board[rank][1] == "." and g.board[rank][2] == "." \
                                and g.board[rank][3] == "." and g.board[rank][0] == "R" \
                                and not self._sq_attacked(g, rank, 2, "B") \
                                and not self._sq_attacked(g, rank, 3, "B") \
                                and not self._sq_attacked(g, rank, 4, "B"):
                            out.append((rank, 2, ("castle",)))
                    else:
                        if "k" in g.castling and g.board[rank][5] == "." and g.board[rank][6] == "." \
                                and g.board[rank][7] == "r" \
                                and not self._sq_attacked(g, rank, 5, "W") \
                                and not self._sq_attacked(g, rank, 6, "W"):
                            out.append((rank, 6, ("castle",)))
                        if "q" in g.castling and g.board[rank][1] == "." and g.board[rank][2] == "." \
                                and g.board[rank][3] == "." and g.board[rank][0] == "r" \
                                and not self._sq_attacked(g, rank, 2, "W") \
                                and not self._sq_attacked(g, rank, 3, "W") \
                                and not self._sq_attacked(g, rank, 4, "W"):
                            out.append((rank, 2, ("castle",)))
        return out

    def _move_keeps_king_safe(self, g: Game, r0: int, f0: int, r1: int, f1: int, special, color: str) -> bool:
        # Save state
        piece = g.board[r0][f0]
        target = g.board[r1][f1]
        ep_remove = None
        if special and special[0] == "en_passant":
            ep_remove = (r0, f1)
            g.board[r0][f1] = "."
        # Special: castling — must check squares-in-between aren't attacked,
        # but _pseudo_moves already filtered; we also check king doesn't
        # land in check.
        g.board[r1][f1] = piece
        g.board[r0][f0] = "."
        # If castling, also move the rook
        if special and special[0] == "castle":
            rank = r0
            if f1 == 6:
                g.board[rank][5] = g.board[rank][7]
                g.board[rank][7] = "."
            else:
                g.board[rank][3] = g.board[rank][0]
                g.board[rank][0] = "."
        safe = not self._in_check(g, color)
        # Undo
        g.board[r0][f0] = piece
        g.board[r1][f1] = target
        if ep_remove:
            g.board[ep_remove[0]][ep_remove[1]] = (
                "p" if color == "W" else "P"
            )
        if special and special[0] == "castle":
            rank = r0
            if f1 == 6:
                g.board[rank][7] = g.board[rank][5]
                g.board[rank][5] = "."
            else:
                g.board[rank][0] = g.board[rank][3]
                g.board[rank][3] = "."
        return safe

    def _king_pos(self, g: Game, color: str) -> tuple:
        target = "K" if color == "W" else "k"
        for r in range(8):
            for f in range(8):
                if g.board[r][f] == target:
                    return (r, f)
        return (-1, -1)

    def _in_check(self, g: Game, color: str) -> bool:
        kr, kf = self._king_pos(g, color)
        if kr < 0:
            return False
        return self._sq_attacked(g, kr, kf, "B" if color == "W" else "W")

    def _sq_attacked(self, g: Game, r: int, f: int, by_color: str) -> bool:
        for rr in range(8):
            for ff in range(8):
                p = g.board[rr][ff]
                if p == ".":
                    continue
                if by_color == "W" and not p.isupper():
                    continue
                if by_color == "B" and not p.islower():
                    continue
                # Cheap: check if (r, f) is in the pseudo-move set of (rr, ff)
                for (nr, nf, _s) in self._pseudo_moves(g, rr, ff, by_color):
                    if (nr, nf) == (r, f):
                        return True
        return False

    def _no_legal_moves(self, g: Game, color: str) -> bool:
        return all(len(v) == 0 for v in self._legal_moves(g, color).values())

    def _terminal_status(self, g: Game) -> Optional[str]:
        side = g.turn
        in_check = self._in_check(g, side)
        no_moves = self._no_legal_moves(g, side)
        if no_moves and in_check:
            return WHITE_WIN if side == "B" else BLACK_WIN
        if no_moves and not in_check:
            return DRAW
        if g.halfmove_clock >= 100:
            return DRAW
        return None

    def _board_to_str(self, g: Game) -> str:
        return "/".join("".join(row) for row in g.board)

    def stats(self) -> dict:
        return {
            "games": self.games.size(),
            "queue": self.queue_size(),
        }


def from_sq_file(fr: tuple) -> str:
    return idx_to_sq(fr[0], fr[1])[0]
