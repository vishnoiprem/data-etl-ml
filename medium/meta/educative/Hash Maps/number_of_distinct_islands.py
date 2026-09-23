"""
Number of Distinct Islands
Medium | 30 min

Given an m x n binary matrix where 1 = land and 0 = water.
An island is a group of connected 1s (horizontally or vertically).
Two islands are "same" if one matches the other without rotation/flip.
Return the number of distinct islands.

Constraints:
- m == grid.length
- n == grid[i].length
- 1 <= m, n <= 100
- grid[i][j] is 0 or 1

Example:
    grid = [
        [1, 1, 0, 1, 1],
        [0, 0, 1, 0, 0]
    ]
    Output: 2 (L-shape and horizontal pair)

    grid = [
        [1, 1, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1],
        [0, 0, 0, 1, 1]
    ]
    Output: 1 (two identical 2x2 squares)
"""

from collections import deque


# =============================================================================
# WAY 1: DFS with Path String (MOST COMMON!)
# =============================================================================
# THINKING: "Each island is a path of moves from origin. Same path = same shape."
def num_distinct_islands_1(grid):
    if not grid:
        return 0

    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, direction):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return ""
        grid[r][c] = 0
        path = direction
        path += dfs(r+1, c, "D")
        path += dfs(r-1, c, "U")
        path += dfs(r, c+1, "R")
        path += dfs(r, c-1, "L")
        path += "B"  # backtrack marker (prevents ambiguity)
        return path

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                shape = dfs(i, j, "O")
                seen.add(shape)

    return len(seen)


# =============================================================================
# WAY 2: DFS with Relative Coords as Tuple
# =============================================================================
def num_distinct_islands_2(grid):
    if not grid:
        return 0

    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, r0, c0):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return []
        grid[r][c] = 0
        coords = [(r - r0, c - c0)]
        coords += dfs(r+1, c, r0, c0)
        coords += dfs(r-1, c, r0, c0)
        coords += dfs(r, c+1, r0, c0)
        coords += dfs(r, c-1, r0, c0)
        return coords

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                shape = tuple(sorted(dfs(i, j, i, j)))
                seen.add(shape)

    return len(seen)


# =============================================================================
# WAY 3: BFS with Coordinates
# =============================================================================
def num_distinct_islands_3(grid):
    if not grid:
        return 0

    m, n = len(grid), len(grid[0])
    seen = set()

    def bfs(r0, c0):
        q = deque([(r0, c0)])
        grid[r0][c0] = 0
        path = []
        while q:
            r, c = q.popleft()
            path.append((r - r0, c - c0))
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 1:
                    grid[nr][nc] = 0
                    q.append((nr, nc))
        return tuple(sorted(path))

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                shape = bfs(i, j)
                seen.add(shape)

    return len(seen)


# =============================================================================
# WAY 4: DFS with Frozen Set
# =============================================================================
def num_distinct_islands_4(grid):
    if not grid:
        return 0

    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, r0, c0):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return frozenset()
        grid[r][c] = 0
        coords = {(r - r0, c - c0)}
        coords |= dfs(r+1, c, r0, c0)
        coords |= dfs(r-1, c, r0, c0)
        coords |= dfs(r, c+1, r0, c0)
        coords |= dfs(r, c-1, r0, c0)
        return coords

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                seen.add(dfs(i, j, i, j))

    return len(seen)


# =============================================================================
# WAY 5: Iterative DFS with Stack
# =============================================================================
def num_distinct_islands_5(grid):
    if not grid:
        return 0

    m, n = len(grid), len(grid[0])
    seen = set()

    def explore(r0, c0):
        stack = [(r0, c0, "O")]
        grid[r0][c0] = 0
        path = ""
        while stack:
            r, c, d = stack.pop()
            path += d
            for dr, dc, name in [(1,0,"D"), (-1,0,"U"), (0,1,"R"), (0,-1,"L")]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 1:
                    grid[nr][nc] = 0
                    stack.append((nr, nc, name))
            path += "B"
        return path

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                seen.add(explore(i, j))

    return len(seen)


# =============================================================================
# WAY 6: DFS with String Concatenation
# =============================================================================
def num_distinct_islands_6(grid):
    if not grid:
        return 0

    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, r0, c0):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return "#"
        grid[r][c] = 0
        s = f"({r-r0},{c-c0})"
        s += dfs(r+1, c, r0, c0)
        s += dfs(r-1, c, r0, c0)
        s += dfs(r, c+1, r0, c0)
        s += dfs(r, c-1, r0, c0)
        return s

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                seen.add(dfs(i, j, i, j))

    return len(seen)


# =============================================================================
# WAY 7: Normalized Coordinates
# =============================================================================
def num_distinct_islands_7(grid):
    if not grid:
        return 0

    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, r0, c0):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return []
        grid[r][c] = 0
        cells = [(r - r0, c - c0)]
        cells += dfs(r+1, c, r0, c0)
        cells += dfs(r-1, c, r0, c0)
        cells += dfs(r, c+1, r0, c0)
        cells += dfs(r, c-1, r0, c0)
        return cells

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                cells = dfs(i, j, i, j)
                # Normalize: shift so min row/col is 0
                min_r = min(r for r, c in cells)
                min_c = min(c for r, c in cells)
                normalized = frozenset((r - min_r, c - min_c) for r, c in cells)
                seen.add(normalized)

    return len(seen)


# =============================================================================
# WAY 8: Compact One-Liner Style
# =============================================================================
def num_distinct_islands_8(grid):
    if not grid:
        return 0
    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, i, j):
        if 0 <= r < m and 0 <= c < n and grid[r][c]:
            grid[r][c] = 0
            return ((r-i, c-j),) + dfs(r+1, c, i, j) + dfs(r-1, c, i, j) + dfs(r, c+1, i, j) + dfs(r, c-1, i, j)
        return ()

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                seen.add(dfs(i, j, i, j))

    return len(seen)


# =============================================================================
# WAY 9: Using String Direction + Position
# =============================================================================
def num_distinct_islands_9(grid):
    if not grid:
        return 0

    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, r0, c0, path):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return path + "X"
        grid[r][c] = 0
        path = dfs(r+1, c, r0, c0, path + "D")
        path = dfs(r-1, c, r0, c0, path + "U")
        path = dfs(r, c+1, r0, c0, path + "R")
        path = dfs(r, c-1, r0, c0, path + "L")
        return path + "B"

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                seen.add(dfs(i, j, i, j, ""))

    return len(seen)


# =============================================================================
# WAY 10: Most Compact with Hash
# =============================================================================
def num_distinct_islands_10(grid):
    if not grid: return 0
    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, i, j, s):
        if not (0 <= r < m and 0 <= c < n) or grid[r][c] == 0:
            return s + "X"
        grid[r][c] = 0
        s = dfs(r+1, c, i, j, s + "1")  # down
        s = dfs(r-1, c, i, j, s + "2")  # up
        s = dfs(r, c+1, i, j, s + "3")  # right
        s = dfs(r, c-1, i, j, s + "4")  # left
        return s + "0"  # back

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                seen.add(dfs(i, j, i, j, ""))

    return len(seen)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find islands (groups of connected 1s) and count how many
have distinct shapes. Two islands have the same shape if they match
without rotation or flipping."

Key Insight:
"I'll represent each island's shape using the relative coordinates
of all its cells from a starting point. Same relative coordinates
means same shape!"

Algorithm:
"1. For each unvisited land cell, do DFS to find its entire island
2. Record the shape (e.g., as a string of directions or set of coords)
3. Add to a set
4. Return the set size"

Why this works:
"Two islands are 'same' if their relative coordinates match. By
normalizing to start at (0,0), the absolute position doesn't matter -
only the shape does."

Edge cases:
- Single cell islands: all have the same shape (one cell)
- L-shaped vs T-shaped: different shapes
- Two 2x2 squares at different positions: same shape

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| DFS path  | O(mn)  | O(mn)    |
| BFS path  | O(mn)  | O(mn)    |
+-----------+--------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: DFS path string", num_distinct_islands_1),
        ("Way 2: DFS tuple", num_distinct_islands_2),
        ("Way 3: BFS coords", num_distinct_islands_3),
        ("Way 4: DFS frozenset", num_distinct_islands_4),
        ("Way 5: Iterative DFS", num_distinct_islands_5),
        ("Way 6: String concat", num_distinct_islands_6),
        ("Way 7: Normalized", num_distinct_islands_7),
        ("Way 8: Compact tuple", num_distinct_islands_8),
        ("Way 9: Direction str", num_distinct_islands_9),
        ("Way 10: Compact hash", num_distinct_islands_10),
    ]

    test_cases = [
        # Case 1: Two L-shapes + horizontal pair
        ([[1,1,0,1,1],
          [0,0,1,0,0]], 2),
        # Case 2: Two identical 2x2 squares
        ([[1,1,0,0,0],
          [1,1,0,0,0],
          [0,0,0,1,1],
          [0,0,0,1,1]], 1),
        # Case 3: All zeros
        ([[0,0],[0,0]], 0),
        # Case 4: Single cell
        ([[1]], 1),
        # Case 5: Multiple single cells (all same shape)
        ([[1,0,1],[0,0,0],[1,0,1]], 1),
    ]

    print("=" * 70)
    print("NUMBER OF DISTINCT ISLANDS - ALL 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for grid, expected in test_cases:
            try:
                # Deep copy grid to avoid mutation issues
                import copy
                test_grid = copy.deepcopy(grid)
                result = func(test_grid)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                status = "✓" if result == expected else "✗"
                print(f"  {status} {name}: grid={grid} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: ERROR - {e}")
        print(f"  Overall: {'PASS' if all_test_pass else 'FAIL'}\n")

    print("=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS! 🎉")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
