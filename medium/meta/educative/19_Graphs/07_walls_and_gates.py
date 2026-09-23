"""
WALLS AND GATES — LeetCode 286
==============================
You are given a m × n grid where:
    -1  wall (impassable)
     0  gate
   INF  empty room

Fill each empty room with the distance to its NEAREST gate. If a room
cannot reach any gate, leave it as INF.

Pattern: MULTI-SOURCE BFS
-------------------------
Seed the queue with EVERY gate, then run a single BFS.
Because BFS expands layer-by-layer from all seeds simultaneously,
the first time we visit any empty cell IS its shortest distance
to the closest gate.

This pattern shows up everywhere: rot spreading to neighbours,
fire spreading to buildings, shortest distance from any of multiple
sources, etc. Memorise it.
"""

from collections import deque
from typing import List


def walls_and_gates(rooms: List[List[int]]) -> None:
    """In-place fill. Mutates the input as LeetCode expects."""
    if not rooms:
        return
    m, n = len(rooms), len(rooms[0])
    INF = 2**31 - 1
    q = deque()
    for r in range(m):
        for c in range(n):
            if rooms[r][c] == 0:        # enqueue ALL gates as sources
                q.append((r, c))

    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    while q:
        r, c = q.popleft()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and rooms[nr][nc] == INF:
                rooms[nr][nc] = rooms[r][c] + 1     # first visit = shortest
                q.append((nr, nc))


# ---------- Bonus: Rotting Oranges (LeetCode 994) ----------
# Same multi-source BFS skeleton, different metric (minutes elapsed).
def oranges_rotting(grid: List[List[int]]) -> int:
    if not grid:
        return 0
    m, n = len(grid), len(grid[0])
    fresh = 0
    q = deque()
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 2:
                q.append((r, c, 0))     # (r, c, minute)
            elif grid[r][c] == 1:
                fresh += 1
    minutes = 0
    while q:
        r, c, t = q.popleft()
        minutes = max(minutes, t)
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                q.append((nr, nc, t + 1))
    return minutes if fresh == 0 else -1


if __name__ == "__main__":
    rooms = [[2147483647,-1,0,2147483647],
             [2147483647,2147483647,2147483647,-1],
             [2147483647,-1,2147483647,-1],
             [0,-1,2147483647,2147483647]]
    walls_and_gates(rooms)
    for row in rooms:
        print(row)

    print("rot minutes:", oranges_rotting([[2,1,1],[1,1,0],[0,1,1]]))  # 4
