# 28 — Chess.com (Real-Time Multiplayer + Move Validation)

> **Lesson 3 of 5 — Real-Time & Collaborative Systems**

A real-time chess platform: matchmaking puts two players into a game,
each move is validated against the full rules of chess, the board
state is broadcast to both clients, and the game ends on checkmate,
resignation, or draw agreement. The service is authoritative — clients
cannot move pieces; they submit moves and the server decides whether
they are legal.

---

## 1. Requirements

### Functional
- Create a game (white vs. black).
- Join / claim a color.
- Submit a move (algebraic-coordinate: `e2`→`e4`); promotion includes
  the piece letter (`q`, `r`, `b`, `n`).
- Validate full rules: piece movement, check, checkmate, stalemate,
  castling (kingside / queenside), en-passant, promotion.
- Track game lifecycle: `PENDING → IN_PROGRESS → ENDED` (with result).
- Matchmaking queue: pair the two longest-waiting players.
- Get game state (board, turn, history).

### Non-functional
- Server is authoritative; clients never compute legality.
- p99 move-ack < 200 ms.
- Idempotent move submission via (game_id, ply, client_nonce).

### Out of scope
- Clocks / time controls.
- Spectator chat.
- Tournament brackets.
- Anti-cheat heuristics (engine detection).

---

## 2. Capacity

| Metric | Value |
|---|---|
| Concurrent games | ~1M (peak) |
| Moves / sec | ~200k peak (avg game ~40 moves, avg ~5 min) |
| Matchmaking QPS | ~10k |

---

## 3. High-level

```
[client] ─POST /api/games──────────────► [API]
[client] ─POST /api/games/{id}/moves───► [API] ─validate──► [Game store]
[client] ─GET  /api/matchmaking────────► [API] ─pair──────► [Matchmaker]
[client] ─SSE /api/games/{id}/stream───► [API] ◄──broadcast on new move
```

The matchmaker keeps a sorted set of pending players by wait time. The
move validator runs against an internal 8×8 board representation; the
result is an updated FEN-like snapshot plus a status flag.

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/games` | `{"white_id"?, "black_id"?}` | game record |
| `GET`  | `/api/games/<id>` | — | full game (board, history, status) |
| `POST` | `/api/games/<id>/join` | `{"user_id", "color"?: "white"\|"black"\|"any"}` | game record |
| `POST` | `/api/games/<id>/moves` | `{"user_id", "from_sq", "to_sq", "promotion"?}` | move + new state |
| `POST` | `/api/games/<id>/resign` | `{"user_id"}` | updated game |
| `GET`  | `/api/matchmaking?user_id=` | — | opponent info or `{"status":"waiting"}` |
| `GET`  | `/api/games/<id>/stream` | — | **SSE** of moves |
| `GET`  | `/health`, `/metrics` | — | ops |

Squares use algebraic coordinates: file `a..h` × rank `1..8` →
`a1` = (0,0) bottom-left (white's perspective).

---

## 5. Data model

| Key | Value |
|---|---|
| `game:<id>` | `{game_id, white_id, black_id, status, result, board: 8x8, turn, history: [{from,to,promotion,san}], castling, en_passant, halfmove, fullmove, ply}` |
| `matchmaking:queue` | sorted list of `(user_id, joined_at)` |
| `user_game:<user_id>` | active game_id |

`board` is an 8x8 list of single-char codes: `r,n,b,q,k,p` (lowercase =
black, uppercase = white), `.` for empty.

---

## 6. Read / Write paths

**Move:**
1. Look up game, check turn matches sender.
2. Generate pseudo-legal moves for the piece.
3. Filter out moves that leave own king in check.
4. Check for checkmate / stalemate on resulting position.
5. Persist, advance turn, append to history, broadcast.

**Matchmaking:** enqueue; if ≥2 players waiting, pop the two oldest,
create a game, return opponent info to each.

---

## 7. Failure modes

- **Concurrent move submission** — atomic test-and-set on `(game_id,
  ply)`: a move with a stale ply is rejected as 409.
- **Disconnection mid-game** — game is paused, not ended; reconnect
  pulls state from store.
- **Matchmaker crash** — queue is rebuilt from `matchmaking:queue` on
  boot; players re-enqueue.

---

## 8. Tradeoffs

- **Authoritative server (chosen) vs. trust-the-client** — only the
  server knows the rules. Trusting the client invites cheating.
- **Synchronous move validation** vs. async with a queue. Sync is
  simpler and our games are tiny; an async pipeline would help with
  anti-cheat ML scoring.
- **Full rules in a single Python module** — fine for a course; real
  engines use bitboards and magic-move tables for speed.

---

## 9. Code map

| File | Purpose |
|---|---|
| `code/service.py` | `ChessService`: board, rules, matchmaking, SSE listeners. |
| `code/app.py` | Flask HTTP API with SSE stream. |
| `tests/test_service.py` | Per-piece movement, castling, en-passant, check, checkmate, promotion, matchmaking. |
| `tests/test_app.py` | HTTP smoke for a full game. |
