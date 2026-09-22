"""
Swim in Rising Water
Hard | 40 min

Given an n x n integer matrix grid where each value grid[i][j] represents
the elevation at that point (i, j). The rain starts to fall. At time t, the
water depth everywhere is t. A swimmer can swim from cell to cell (4-dir)
if both cells have elevation <= t. The swimmer can move instantly if both
cells are uncovered.

Return the minimum time t such that the swimmer can travel from (0,0)
to (n-1, n-1).

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/swim-in-rising-water

Examples:
    grid = [[0,1,2,3],
            [12,11,10,4],
            [13,14,9,5],
            [15,8,7,6]]
    -> Output: 6

Constraints:
- n == grid.length == grid[i].length
- 1 <= n <= 50 (Educative says 30, LeetCode says 50)
- 0 <= grid[i][j] < n*n
- All grid[i][j] are unique
"""

import heapq
from collections import deque
from typing import List


# =============================================================================
# WAY 1: Dijkstra's Min-Heap (BEST — Memorize!)
# =============================================================================
def swimInWater_1(grid):
    """
    KEY INSIGHT: The answer is the MIN over all paths from (0,0) to (n-1,n-1)
    of the MAX cell value along that path. This is the "min-max path" problem.

    Dijkstra's algorithm with priority = max elevation seen so far.
    State: (max_so_far, row, col)
    Start: (grid[0][0], 0, 0)
    Goal: when we pop (n-1, n-1), the max_so_far is the answer.

    Why Dijkstra works:
    - Each cell's "cost to reach" = max elevation along the path.
    - This is monotone: extending a path only increases max.
    - Dijkstra's greedy expansion finds shortest path when cost is monotone.

    Time:  O(n^2 log n^2)
    Space: O(n^2)
    """
    n = len(grid)
    visited = set()
    # (max_elevation_so_far, row, col)
    heap = [(grid[0][0], 0, 0)]

    while heap:
        t, r, c = heapq.heappop(heap)
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if r == n - 1 and c == n - 1:
            return t
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in visited:
                heapq.heappush(heap, (max(t, grid[nr][nc]), nr, nc))
    return -1


# =============================================================================
# WAY 2: Dijkstra's with 2D array for visited
# =============================================================================
def swimInWater_2(grid):
    """Same as Way 1 but uses 2D visited array instead of set."""
    n = len(grid)
    visited = [[False] * n for _ in range(n)]
    heap = [(grid[0][0], 0, 0)]

    while heap:
        t, r, c = heapq.heappop(heap)
        if visited[r][c]:
            continue
        visited[r][c] = True
        if r == n - 1 and c == n - 1:
            return t
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and not visited[nr][nc]:
                heapq.heappush(heap, (max(t, grid[nr][nc]), nr, nc))
    return -1


# =============================================================================
# WAY 3: Dijkstra's using best[][] tracking min max per cell
# =============================================================================
def swimInWater_3(grid):
    """Maintain best[r][c] = minimum max-elevation to reach (r,c)."""
    n = len(grid)
    INF = float('inf')
    best = [[INF] * n for _ in range(n)]
    best[0][0] = grid[0][0]
    heap = [(grid[0][0], 0, 0)]

    while heap:
        t, r, c = heapq.heappop(heap)
        if t > best[r][c]:
            continue
        if r == n - 1 and c == n - 1:
            return t
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                nt = max(t, grid[nr][nc])
                if nt < best[nr][nc]:
                    best[nr][nc] = nt
                    heapq.heappush(heap, (nt, nr, nc))
    return best[n - 1][n - 1]


# =============================================================================
# WAY 4: Binary Search on Time + DFS
# =============================================================================
def swimInWater_4(grid):
    """
    KEY INSIGHT: For a given time t, can the swimmer reach the destination?
    - DFS/BFS from (0,0), only entering cells with elevation <= t.
    - The answer is the smallest t such that this DFS reaches (n-1,n-1).
    - This predicate (reachable at time t) is MONOTONE in t.
    - Binary search t in [0, n*n - 1].

    Time:  O(n^2 log n^2)
    Space: O(n^2)
    """
    n = len(grid)

    def can_swim(t):
        if grid[0][0] > t:
            return False
        visited = [[False] * n for _ in range(n)]
        visited[0][0] = True
        stack = [(0, 0)]
        while stack:
            r, c = stack.pop()
            if r == n - 1 and c == n - 1:
                return True
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and not visited[nr][nc] and grid[nr][nc] <= t:
                    visited[nr][nc] = True
                    stack.append((nr, nc))
        return False

    lo, hi = 0, n * n - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if can_swim(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 5: Binary Search + BFS
# =============================================================================
def swimInWater_5(grid):
    """Same as Way 4 but with BFS instead of DFS."""
    n = len(grid)

    def can_swim(t):
        if grid[0][0] > t:
            return False
        visited = [[False] * n for _ in range(n)]
        visited[0][0] = True
        q = deque([(0, 0)])
        while q:
            r, c = q.popleft()
            if r == n - 1 and c == n - 1:
                return True
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and not visited[nr][nc] and grid[nr][nc] <= t:
                    visited[nr][nc] = True
                    q.append((nr, nc))
        return False

    lo, hi = 0, n * n - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if can_swim(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 6: Union-Find (process cells in elevation order)
# =============================================================================
def swimInWater_6(grid):
    """
    KEY INSIGHT: Process cells in order of increasing elevation.
    When we add a cell, union it with its neighbors that are already added.
    When (0,0) and (n-1,n-1) are in the same component, the current
    elevation is the answer.

    Time:  O(n^2 * alpha(n^2))
    Space: O(n^2)
    """
    n = len(grid)
    parent = list(range(n * n))
    rank = [0] * (n * n)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px == py:
            return
        if rank[px] < rank[py]:
            px, py = py, px
        parent[py] = px
        if rank[px] == rank[py]:
            rank[px] += 1

    # Sort cells by elevation
    cells = sorted([(grid[i][j], i, j) for i in range(n) for j in range(n)])
    added = [[False] * n for _ in range(n)]

    for elev, r, c in cells:
        added[r][c] = True
        idx = r * n + c
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and added[nr][nc]:
                union(idx, nr * n + nc)
        if find(0) == find(n * n - 1):
            return elev
    return -1


# =============================================================================
# WAY 7: Union-Find with path compression only
# =============================================================================
def swimInWater_7(grid):
    """Same as Way 6 but simpler find (path compression without union by rank)."""
    n = len(grid)
    parent = list(range(n * n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    cells = sorted([(grid[i][j], i, j) for i in range(n) for j in range(n)])
    added = [[False] * n for _ in range(n)]

    for elev, r, c in cells:
        added[r][c] = True
        idx = r * n + c
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and added[nr][nc]:
                union(idx, nr * n + nc)
        if find(0) == find(n * n - 1):
            return elev
    return -1


# =============================================================================
# WAY 8: Dijkstra's with (max, row, col) state and tuple ordering
# =============================================================================
def swimInWater_8(grid):
    """Verbose Dijkstra with explicit tuple for clarity."""
    n = len(grid)
    if n == 0:
        return 0
    DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    dist = [[float('inf')] * n for _ in range(n)]
    dist[0][0] = grid[0][0]
    pq = [(grid[0][0], 0, 0)]

    while pq:
        d, r, c = heapq.heappop(pq)
        if d > dist[r][c]:
            continue
        if r == n - 1 and c == n - 1:
            return d
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                nd = max(d, grid[nr][nc])
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(pq, (nd, nr, nc))
    return dist[n - 1][n - 1]


# =============================================================================
# WAY 9: Binary search on time with virtual visited
# =============================================================================
def swimInWater_9(grid):
    """Binary search + DFS, marking visited via set to avoid modifying grid."""
    n = len(grid)

    def can_swim(t):
        if grid[0][0] > t:
            return False
        visited = set()
        visited.add((0, 0))
        stack = [(0, 0)]
        while stack:
            r, c = stack.pop()
            if r == n - 1 and c == n - 1:
                return True
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in visited and grid[nr][nc] <= t:
                    visited.add((nr, nc))
                    stack.append((nr, nc))
        return False

    lo, hi = 0, n * n - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if can_swim(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 10: BFS with elevation ordering (Union-Find style with BFS check)
# =============================================================================
def swimInWater_10(grid):
    """
    Process cells in order of increasing elevation. After adding each cell,
    BFS to see if (0,0) is connected to (n-1,n-1) via added cells.
    """
    n = len(grid)
    added = [[False] * n for _ in range(n)]
    cells_sorted = sorted([(grid[i][j], i, j) for i in range(n) for j in range(n)])

    for elev, r, c in cells_sorted:
        added[r][c] = True
        # Only check connectivity if start AND end are added
        if not added[0][0] or not added[n - 1][n - 1]:
            continue
        # BFS from (0,0)
        visited = [[False] * n for _ in range(n)]
        visited[0][0] = True
        q = deque([(0, 0)])
        while q:
            cr, cc = q.popleft()
            if cr == n - 1 and cc == n - 1:
                return elev
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < n and 0 <= nc < n and added[nr][nc] and not visited[nr][nc]:
                    visited[nr][nc] = True
                    q.append((nr, nc))
    return -1


# =============================================================================
# WAY 11: Dijkstra's using bisect for time optimization
# =============================================================================
def swimInWater_11(grid):
    """Dijkstra's where priority is (max_elevation, row, col)."""
    n = len(grid)
    heap = [(grid[0][0], 0, 0)]
    best = {}
    best[(0, 0)] = grid[0][0]

    while heap:
        t, r, c = heapq.heappop(heap)
        if (r, c) in best and best[(r, c)] < t:
            continue
        if r == n - 1 and c == n - 1:
            return t
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                nt = max(t, grid[nr][nc])
                if (nr, nc) not in best or nt < best[(nr, nc)]:
                    best[(nr, nc)] = nt
                    heapq.heappush(heap, (nt, nr, nc))
    return -1


# =============================================================================
# WAY 12: A* with Manhattan heuristic
# =============================================================================
def swimInWater_12(grid):
    """A* with h(r,c) = grid[r][c] as heuristic (admissible since values >= 0)."""
    n = len(grid)
    g = [[float('inf')] * n for _ in range(n)]
    g[0][0] = grid[0][0]
    # f = g + h, where h = grid[r][c] (lower bound on remaining max)
    heap = [(grid[0][0] + grid[0][0], 0, 0)]
    while heap:
        f, r, c = heapq.heappop(heap)
        if r == n - 1 and c == n - 1:
            return g[r][c]
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                ng = max(g[r][c], grid[nr][nc])
                if ng < g[nr][nc]:
                    g[nr][nc] = ng
                    heapq.heappush(heap, (ng + grid[nr][nc], nr, nc))
    return -1


# =============================================================================
# WAY 13: Iterative DP bottom-up via Dijkstra-like relaxation
# =============================================================================
def swimInWater_13(grid):
    """
    Dijkstra-style with sorted cells: process cells in order of best-known
    max-elevation. When we pop (n-1, n-1), return its best-known value.
    """
    n = len(grid)
    INF = float('inf')
    best = [[INF] * n for _ in range(n)]
    best[0][0] = grid[0][0]
    heap = [(grid[0][0], 0, 0)]

    while heap:
        t, r, c = heapq.heappop(heap)
        if t > best[r][c]:
            continue
        if r == n - 1 and c == n - 1:
            return t
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                nt = max(t, grid[nr][nc])
                if nt < best[nr][nc]:
                    best[nr][nc] = nt
                    heapq.heappush(heap, (nt, nr, nc))
    return -1


# =============================================================================
# WAY 14: BFS from low elevations (process cells like Union-Find, simpler)
# =============================================================================
def swimInWater_14(grid):
    """Process cells in elevation order, expanding reachable region via BFS."""
    n = len(grid)
    added = [[False] * n for _ in range(n)]
    cells = sorted([(grid[i][j], i, j) for i in range(n) for j in range(n)])

    for elev, r, c in cells:
        added[r][c] = True
        # Check if (0,0) connects to (n-1,n-1)
        if added[0][0] and added[n - 1][n - 1]:
            # BFS from (0,0)
            visited = [[False] * n for _ in range(n)]
            visited[0][0] = True
            q = deque([(0, 0)])
            found = False
            while q:
                cr, cc = q.popleft()
                if cr == n - 1 and cc == n - 1:
                    found = True
                    break
                for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < n and 0 <= nc < n and added[nr][nc] and not visited[nr][nc]:
                        visited[nr][nc] = True
                        q.append((nr, nc))
            if found:
                return elev
    return -1


# =============================================================================
# WAY 15: Dijkstra's with named constants and clean code
# =============================================================================
def swimInWater_15(grid):
    """Cleanest Dijkstra implementation."""
    n = len(grid)
    DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    INF = float('inf')
    dist = [[INF] * n for _ in range(n)]
    dist[0][0] = grid[0][0]
    pq = [(grid[0][0], 0, 0)]

    while pq:
        d, r, c = heapq.heappop(pq)
        if d > dist[r][c]:
            continue
        if r == n - 1 and c == n - 1:
            return d
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                nd = max(d, grid[nr][nc])
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(pq, (nd, nr, nc))
    return dist[n - 1][n - 1]


# =============================================================================
# WAY 16: Dijkstra's using a state class
# =============================================================================
class State:
    __slots__ = ('max_elev', 'r', 'c')

    def __init__(self, max_elev, r, c):
        self.max_elev = max_elev
        self.r = r
        self.c = c

    def __lt__(self, other):
        return self.max_elev < other.max_elev


def swimInWater_16(grid):
    """Dijkstra's using a State class for clarity."""
    n = len(grid)
    DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    INF = float('inf')
    dist = [[INF] * n for _ in range(n)]
    dist[0][0] = grid[0][0]
    pq = [State(grid[0][0], 0, 0)]

    while pq:
        s = heapq.heappop(pq)
        d, r, c = s.max_elev, s.r, s.c
        if d > dist[r][c]:
            continue
        if r == n - 1 and c == n - 1:
            return d
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                nd = max(d, grid[nr][nc])
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(pq, State(nd, nr, nc))
    return dist[n - 1][n - 1]


# =============================================================================
# WAY 17: Binary search + Union-Find (combo)
# =============================================================================
def swimInWater_17(grid):
    """Binary search on time, check connectivity via Union-Find."""
    n = len(grid)
    parent = list(range(n * n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def can_swim(t):
        # Reset Union-Find
        for i in range(n * n):
            parent[i] = i
        for i in range(n):
            for j in range(n):
                if grid[i][j] > t:
                    continue
                for dr, dc in [(1, 0), (0, 1)]:
                    ni, nj = i + dr, j + dc
                    if 0 <= ni < n and 0 <= nj < n and grid[ni][nj] <= t:
                        a, b = i * n + j, ni * n + nj
                        pa, pb = find(a), find(b)
                        if pa != pb:
                            parent[pa] = pb
        return find(0) == find(n * n - 1)

    lo, hi = 0, n * n - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if can_swim(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 18: Recursive Kruskal-like (Union-Find processed)
# =============================================================================
def swimInWater_18(grid):
    """Process cells in elevation order, union with already-processed neighbors."""
    n = len(grid)
    parent = list(range(n * n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    # Sort cells (i, j) by elevation
    cells = [(grid[i][j], i, j) for i in range(n) for j in range(n)]
    cells.sort()
    visited = [[False] * n for _ in range(n)]

    for elev, r, c in cells:
        visited[r][c] = True
        idx = r * n + c
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and visited[nr][nc]:
                # Union idx with nr*n+nc
                a, b = idx, nr * n + nc
                while parent[a] != a:
                    parent[a] = parent[parent[a]]
                    a = parent[a]
                while parent[b] != b:
                    parent[b] = parent[parent[b]]
                    b = parent[b]
                if a != b:
                    parent[a] = b
        # Check if (0,0) and (n-1,n-1) are connected
        a, b = 0, n * n - 1
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        while parent[b] != b:
            parent[b] = parent[parent[b]]
            b = parent[b]
        if a == b:
            return elev
    return -1


# =============================================================================
# WAY 19: Most concise Dijkstra (one-liner style)
# =============================================================================
def swimInWater_19(grid):
    """Most concise Dijkstra."""
    n = len(grid)
    seen = set()
    heap = [(grid[0][0], 0, 0)]
    while heap:
        t, r, c = heapq.heappop(heap)
        if (r, c) in seen:
            continue
        if r == n - 1 and c == n - 1:
            return t
        seen.add((r, c))
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen:
                heapq.heappush(heap, (max(t, grid[nr][nc]), nr, nc))


# =============================================================================
# WAY 20: The one to memorize (Union-Find, clean)
# =============================================================================
def swimInWater_20(grid):
    """
    THE ONE TO MEMORIZE.

    Union-Find: Process cells in order of elevation. When (0,0) and (n-1,n-1)
    become connected, the current elevation is the answer.

    Time:  O(n^2 * alpha(n^2))
    Space: O(n^2)
    """
    n = len(grid)
    parent = list(range(n * n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    cells = sorted([(grid[i][j], i, j) for i in range(n) for j in range(n)])
    visited = [[False] * n for _ in range(n)]

    for elev, r, c in cells:
        visited[r][c] = True
        for dr, dc in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and visited[nr][nc]:
                a, b = r * n + c, nr * n + nc
                pa, pb = find(a), find(b)
                if pa != pb:
                    parent[pa] = pb
        if find(0) == find(n * n - 1):
            return elev
    return -1


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the minimum time t at which a swimmer can cross from
(0,0) to (n-1,n-1) in a grid where cells have unique elevation values,
and water rises to height t over time."

Key Insight:
"The answer is the MIN over all paths from start to end of the MAX
elevation along that path. This is the 'min-max path' problem."

Two Approaches:
1. DIJKSTRA'S: Treat each cell as a node. Cost to enter cell = its elevation.
   State = (max_elev_so_far, row, col). Start at (grid[0][0], 0, 0).
   Pop minimum, expand neighbors with new_max = max(current, neighbor).
   Return max_elev when we pop (n-1, n-1).

2. UNION-FIND: Sort cells by elevation. Add cells in order. When (0,0) and
   (n-1,n-1) become connected, the current elevation is the answer.
   Cleaner, slightly faster (no heap).

3. BINARY SEARCH + DFS: For a given time t, can the swimmer reach the end?
   This predicate is MONOTONE in t. Binary search t in [0, n*n - 1].

Best: Union-Find for cleanliness, Dijkstra for intuition.

Why Dijkstra works:
"The 'cost to reach a cell' = max elevation along path. This is monotone
(non-decreasing as we extend the path). Standard Dijkstra with this cost
gives shortest path, which here is min-max."

Why Union-Find works:
"At time t, all cells with elevation <= t are 'unlocked'. The swimmer can
reach any unlocked cell connected to (0,0). When (0,0) and (n-1,n-1)
become connected via unlocked cells, t is the answer."

Edge Cases:
- n = 1: return grid[0][0].
- grid[0][0] is not 0: still works (start at elevation grid[0][0]).
- grid[n-1][n-1] is max: usually the bottleneck.

Complexity:
+-------------------+--------------------+--------+
| Approach          | Time               | Space  |
+-------------------+--------------------+--------+
| Dijkstra          | O(n^2 log n^2)     | O(n^2) |
| Union-Find        | O(n^2 * alpha(n^2))| O(n^2) |
| Binary Search+DFS | O(n^2 log n^2)     | O(n^2) |
+-------------------+--------------------+--------+

KEY TRICK:
The min-max path formulation. The answer is the min over paths of the
max cell value. This is exactly what Dijkstra finds when cost = max so far.

RELATED PROBLEMS:
- Path with Maximum Minimum Value (LC 1102): Same idea, find max of min.
- Cheapest Flight with K Stops (LC 787): Dijkstra variant.
- Network Delay Time (LC 743): Dijkstra.
- Min Cost to Reach Destination (LC 1928): BFS.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Dijkstra (BEST)", swimInWater_1),
        ("Way 2: Dijkstra 2D visited", swimInWater_2),
        ("Way 3: Dijkstra best[][]", swimInWater_3),
        ("Way 4: Binary search + DFS", swimInWater_4),
        ("Way 5: Binary search + BFS", swimInWater_5),
        ("Way 6: Union-Find", swimInWater_6),
        ("Way 7: Union-Find simple", swimInWater_7),
        ("Way 8: Verbose Dijkstra", swimInWater_8),
        ("Way 9: Binary search + DFS in-place", swimInWater_9),
        ("Way 10: BFS by elevation", swimInWater_10),
        ("Way 11: Dijkstra dict", swimInWater_11),
        ("Way 12: A* search", swimInWater_12),
        ("Way 13: Recursive DFS memo", swimInWater_13),
        ("Way 14: BFS by elevation simple", swimInWater_14),
        ("Way 15: Clean Dijkstra", swimInWater_15),
        ("Way 16: Dijkstra State class", swimInWater_16),
        ("Way 17: Binary search + Union-Find", swimInWater_17),
        ("Way 18: Union-Find inline", swimInWater_18),
        ("Way 19: Most concise Dijkstra", swimInWater_19),
        ("Way 20: Final Union-Find (BEST)", swimInWater_20),
    ]

    test_cases = [
        # Standard example from problem
        ([[0, 1, 2, 3],
          [12, 11, 10, 4],
          [13, 14, 9, 5],
          [15, 8, 7, 6]], 6),
        # Trivial n=1
        ([[0]], 0),
        # 2x2: [[0,1],[3,2]]: top path max=2, left path max=3. Min=2
        ([[0, 1], [3, 2]], 2),
        # 2x2: [[0,2],[1,3]]: top max=3, left max=3. Min=3
        ([[0, 2], [1, 3]], 3),
        # 2x2: [[0,1],[2,3]]: top max=3, left max=3. Min=3
        ([[0, 1], [2, 3]], 3),
        # 3x3 monotonic - max along any path = 8
        ([[0, 1, 2], [3, 4, 5], [6, 7, 8]], 8),
        # 3x3 reversed - max along any path = 8
        ([[8, 7, 6], [5, 4, 3], [2, 1, 0]], 8),
        # 3x3 [[0,1,2],[5,4,3],[6,7,8]]:
        #   All paths must include (2,2)=8, so answer = 8
        ([[0, 1, 2], [5, 4, 3], [6, 7, 8]], 8),
        # 3x3 [[0,3,2],[4,5,1],[6,7,8]]:
        #   All paths include (2,2)=8, answer=8
        ([[0, 3, 2], [4, 5, 1], [6, 7, 8]], 8),
        # Better 3x3: [[0,3,5],[1,4,2],[7,8,6]]
        #   (0,0)->(1,0)->(1,1)->(2,1)->(2,2): max=8
        #   (0,0)->(1,0)->(1,1)->(1,2)->(2,2): max=6
        #   (0,0)->(0,1)->(1,1)->(1,2)->(2,2): max=6
        #   (0,0)->(0,1)->(1,1)->(2,1)->(2,2): max=8
        #   Min=6
        ([[0, 3, 5], [1, 4, 2], [7, 8, 6]], 6),
        # 2x2 [[0,1],[4,3]]: top max=3, left max=4. Min=3
        ([[0, 1], [4, 3]], 3),
    ]

    print("=" * 70)
    print("SWIM IN RISING WATER - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/swim-in-rising-water")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for grid, expected in test_cases:
            try:
                # Make a copy for in-place modifications
                grid_copy = [row[:] for row in grid]
                result = func(grid_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: grid={grid}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on grid={grid} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
