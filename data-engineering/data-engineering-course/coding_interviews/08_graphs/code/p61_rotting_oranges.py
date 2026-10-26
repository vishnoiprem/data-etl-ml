"""Rotting Oranges — BFS spread; return minutes until all are rotten (or -1).

Time:  O(m · n) — each cell visited at most once
Space: O(m · n) — the queue
"""

from collections import deque


def solve_rotting_oranges(grid):
    """Return the minutes until all fresh oranges go rotten, or -1 if impossible.

    0 = empty, 1 = fresh, 2 = rotten.
    """
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    queue = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c, 0))
            elif grid[r][c] == 1:
                fresh += 1
    if fresh == 0:
        return 0
    minutes = 0
    while queue:
        r, c, t = queue.popleft()
        minutes = max(minutes, t)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                queue.append((nr, nc, t + 1))
    return minutes if fresh == 0 else -1


if __name__ == "__main__":
    g = [[2, 1, 1], [1, 1, 0], [0, 1, 1]]
    print(solve_rotting_oranges(g))
