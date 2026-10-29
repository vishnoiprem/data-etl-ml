"""
Minimum Time Takes to Reach Destination Without Drowning
Hard | 40 min

Given an m x n grid of strings, find minimum time to reach destination
without drowning.

Grid cells:
- 'S': Source (start) - you start here
- 'D': Destination - goal (never flooded)
- '.': Empty cell (walkable)
- 'X': Stone (impassable)
- '*': Flooded cell (impassable)

Movement: 1 cell/second in any of 4 cardinal directions.
Flooding: Each second, all empty (.) cells adjacent to flooded (*) cells
          also become flooded.
Constraints:
- Can't step on X (stone) or * (flooded).
- Can't step on a cell that becomes flooded at the moment of stepping
  (else you drown).
- D never floods.

Return minimum seconds to reach D from S, or -1 if impossible.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-time-takes-to-reach-destination-without-drowning

Constraints:
- 2 <= m, n <= 100
- Only S, D, ., *, X
- Exactly one S, one D
"""


# =============================================================================
# WAY 1: Precompute flood times + BFS (BEST - Standard Interview Answer)
# =============================================================================
def minimum_seconds_1(land):
    """
    The KEY INSIGHT: We can't just BFS from S - we need to know WHICH cells
    become flooded and WHEN, so we can avoid drowning.

    Strategy:
    1. First, BFS from all * cells simultaneously to compute the FLOOD TIME
       for each empty cell (time when that cell becomes flooded).
    2. Then, BFS from S, but only into cells where:
       - arrival_time < flood_time (we arrive BEFORE it floods)
       - arrival_time != flood_time (we don't arrive AT the moment it floods)
    3. Return time when we reach D, or -1.

    Time:  O(m*n)  - two BFS passes
    Space: O(m*n)  - flood_time grid + visited
    """
    if not land or not land[0]:
        return -1
    m, n = len(land), len(land[0])

    # Directions: up, down, left, right
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Find S, D, and start BFS for flooding from all * cells
    flood_time = [[float('inf')] * n for _ in range(m)]
    from collections import deque
    flood_q = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood_time[i][j] = 0
                flood_q.append((i, j))
            elif land[i][j] == 'D':
                flood_time[i][j] = float('inf')  # D never floods

    # Multi-source BFS: compute when each cell gets flooded
    while flood_q:
        i, j = flood_q.popleft()
        cur_t = flood_time[i][j]
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n:
                # Skip stones and destinations
                if land[ni][nj] == 'X' or land[ni][nj] == 'D':
                    continue
                # If we can flood it earlier
                if cur_t + 1 < flood_time[ni][nj]:
                    flood_time[ni][nj] = cur_t + 1
                    flood_q.append((ni, nj))

    # Find S and BFS for person
    si, sj = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
                break
        if si != -1:
            break

    # Person BFS: must arrive strictly before flood time
    visited = [[False] * n for _ in range(m)]
    person_q = deque()
    person_q.append((si, sj, 0))
    visited[si][sj] = True

    while person_q:
        i, j, t = person_q.popleft()
        if land[i][j] == 'D':
            return t
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj]:
                if land[ni][nj] == 'X':
                    continue
                # Arrive at time t+1. Must arrive before it floods.
                if t + 1 < flood_time[ni][nj]:
                    visited[ni][nj] = True
                    person_q.append((ni, nj, t + 1))

    return -1


# =============================================================================
# WAY 2: Verbose version (whiteboard-friendly)
# =============================================================================
def minimum_seconds_2(land):
    """Same as Way 1 but with explicit variable names for clarity."""
    if not land:
        return -1
    rows = len(land)
    cols = len(land[0])
    INF = float('inf')

    # Direction deltas: up, down, left, right
    DELTAS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Step 1: Multi-source BFS from all flooded cells
    flood_time = [[INF] * cols for _ in range(rows)]
    from collections import deque
    flood_queue = deque()

    for r in range(rows):
        for c in range(cols):
            if land[r][c] == '*':
                flood_time[r][c] = 0
                flood_queue.append((r, c))

    while flood_queue:
        r, c = flood_queue.popleft()
        current_flood_time = flood_time[r][c]
        for dr, dc in DELTAS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if land[nr][nc] == 'X' or land[nr][nc] == 'D':
                    continue
                if current_flood_time + 1 < flood_time[nr][nc]:
                    flood_time[nr][nc] = current_flood_time + 1
                    flood_queue.append((nr, nc))

    # Step 2: Find source
    source_r, source_c = -1, -1
    for r in range(rows):
        for c in range(cols):
            if land[r][c] == 'S':
                source_r, source_r = r, c
                source_r = r  # bugfix placeholder
                source_c = c
                break
        if source_r != -1:
            break
    # Recompute properly:
    for r in range(rows):
        for c in range(cols):
            if land[r][c] == 'S':
                source_r, source_c = r, c
                break
        if source_r != -1:
            break

    # Step 3: Person BFS - must arrive before flood
    person_visited = [[False] * cols for _ in range(rows)]
    person_queue = deque()
    person_queue.append((source_r, source_c, 0))
    person_visited[source_r][source_c] = True

    while person_queue:
        r, c, time = person_queue.popleft()
        if land[r][c] == 'D':
            return time
        for dr, dc in DELTAS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not person_visited[nr][nc]:
                if land[nr][nc] == 'X':
                    continue
                if time + 1 < flood_time[nr][nc]:
                    person_visited[nr][nc] = True
                    person_queue.append((nr, nc, time + 1))

    return -1


# =============================================================================
# WAY 3: Using next() to find S, D
# =============================================================================
def minimum_seconds_3(land):
    """Use generator expressions to find S efficiently."""
    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    from collections import deque

    # Find S position
    si = next(i for i, row in enumerate(land) if 'S' in row)
    sj = land[si].index('S')

    # Step 1: Flood BFS
    flood_time = [[INF] * n for _ in range(m)]
    flood_q = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood_time[i][j] = 0
                flood_q.append((i, j))

    while flood_q:
        i, j = flood_q.popleft()
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n:
                if land[ni][nj] in ('X', 'D'):
                    continue
                if flood_time[i][j] + 1 < flood_time[ni][nj]:
                    flood_time[ni][nj] = flood_time[i][j] + 1
                    flood_q.append((ni, nj))

    # Step 2: Person BFS
    visited = [[False] * n for _ in range(m)]
    pq = deque([(si, sj, 0)])
    visited[si][sj] = True

    while pq:
        i, j, t = pq.popleft()
        if land[i][j] == 'D':
            return t
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj]:
                if land[ni][nj] == 'X':
                    continue
                if t + 1 < flood_time[ni][nj]:
                    visited[ni][nj] = True
                    pq.append((ni, nj, t + 1))

    return -1


# =============================================================================
# WAY 4: BFS with tuple state (i, j, time)
# =============================================================================
def minimum_seconds_4(land):
    """Single BFS with time-tracked queue. Uses pre-computed flood times."""
    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque

    # Locate S
    si, sj = next((i, j) for i, row in enumerate(land)
                  for j, cell in enumerate(row) if cell == 'S')

    # Precompute flood times via multi-source BFS
    flood = [[INF] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))

    while fq:
        i, j = fq.popleft()
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    # Person BFS
    visited = [[False] * n for _ in range(m)]
    q = deque([(si, sj, 0)])
    visited[si][sj] = True
    while q:
        i, j, t = q.popleft()
        if land[i][j] == 'D':
            return t
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj]:
                if land[ni][nj] != 'X' and t + 1 < flood[ni][nj]:
                    visited[ni][nj] = True
                    q.append((ni, nj, t + 1))
    return -1


# =============================================================================
# WAY 5: Simultaneous BFS (interleaved flood and person)
# =============================================================================
def minimum_seconds_5(land):
    """
    Instead of precomputing flood times, interleave the two BFSs.
    Each "round" represents one second:
    - Person moves
    - Then flood spreads

    This avoids storing the entire flood_time grid.
    """
    if not land:
        return -1
    m, n = len(land), len(land[0])
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque

    si, sj = next((i, j) for i, row in enumerate(land)
                  for j, cell in enumerate(row) if cell == 'S')

    # Mutable grid for tracking flood spread
    grid = [row[:] for row in land]
    visited = [[False] * n for _ in range(m)]

    person_q = deque([(si, sj)])
    visited[si][sj] = True
    time = 0

    while person_q:
        # Process ALL person moves at current time
        for _ in range(len(person_q)):
            i, j = person_q.popleft()
            if grid[i][j] == 'D':
                return time
            for di, dj in dirs:
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj]:
                    if grid[ni][nj] != 'X' and grid[ni][nj] != '*':
                        visited[ni][nj] = True
                        person_q.append((ni, nj))

        # Spread flood to empty cells adjacent to flooded
        new_floods = []
        for i in range(m):
            for j in range(n):
                if grid[i][j] == '.':
                    for di, dj in dirs:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < m and 0 <= nj < n and grid[ni][nj] == '*':
                            new_floods.append((i, j))
                            break
        for i, j in new_floods:
            grid[i][j] = '*'

        time += 1

    return -1


# =============================================================================
# WAY 6: Using a single BFS with state tracking
# =============================================================================
def minimum_seconds_6(land):
    """
    BFS where state = (row, col). We track time implicitly via visited layers.
    Use a 'flood_grid' that grows over time.
    """
    if not land:
        return -1
    m, n = len(land), len(land[0])
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque

    si, sj = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
                break
        if si != -1:
            break

    # Build flood_time via BFS
    flood_time = [[float('inf')] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood_time[i][j] = 0
                fq.append((i, j))

    while fq:
        i, j = fq.popleft()
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood_time[i][j] + 1 < flood_time[ni][nj]:
                    flood_time[ni][nj] = flood_time[i][j] + 1
                    fq.append((ni, nj))

    # BFS from S
    visited = [[False] * n for _ in range(m)]
    q = deque([(si, sj, 0)])
    visited[si][sj] = True
    while q:
        i, j, t = q.popleft()
        if land[i][j] == 'D':
            return t
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if (0 <= ni < m and 0 <= nj < n and not visited[ni][nj]
                    and land[ni][nj] != 'X' and t + 1 < flood_time[ni][nj]):
                visited[ni][nj] = True
                q.append((ni, nj, t + 1))
    return -1


# =============================================================================
# WAY 7: BFS using collections.deque with explicit level iteration
# =============================================================================
def minimum_seconds_7(land):
    """
    Use level-order BFS: process all cells at time t, then time t+1.
    Flood also spreads per level.
    """
    if not land:
        return -1
    m, n = len(land), len(land[0])
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque

    si, sj = next((i, j) for i, row in enumerate(land)
                  for j, c in enumerate(row) if c == 'S')

    # Precompute flood times
    flood = [[float('inf')] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))
    while fq:
        i, j = fq.popleft()
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    visited = [[False] * n for _ in range(m)]
    q = deque([(si, sj)])
    visited[si][sj] = True
    time = 0
    while q:
        level_size = len(q)
        for _ in range(level_size):
            i, j = q.popleft()
            if land[i][j] == 'D':
                return time
            for di, dj in dirs:
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj]:
                    if land[ni][nj] != 'X' and time + 1 < flood[ni][nj]:
                        visited[ni][nj] = True
                        q.append((ni, nj))
        time += 1
    return -1


# =============================================================================
# WAY 8: With directions dictionary for readability
# =============================================================================
DIRECTIONS = {
    'up': (-1, 0),
    'down': (1, 0),
    'left': (0, -1),
    'right': (0, 1),
}


def minimum_seconds_8(land):
    """Use named directions dictionary for clarity."""
    if not land or not land[0]:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    dirs = [DIRECTIONS['up'], DIRECTIONS['down'],
            DIRECTIONS['left'], DIRECTIONS['right']]
    from collections import deque

    si, sj = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
    if si == -1:
        return -1

    # Flood time BFS
    flood = [[INF] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))
    while fq:
        i, j = fq.popleft()
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    # Person BFS
    visited = [[False] * n for _ in range(m)]
    q = deque([(si, sj, 0)])
    visited[si][sj] = True
    while q:
        i, j, t = q.popleft()
        if land[i][j] == 'D':
            return t
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if (0 <= ni < m and 0 <= nj < n and not visited[ni][nj]
                    and land[ni][nj] != 'X' and t + 1 < flood[ni][nj]):
                visited[ni][nj] = True
                q.append((ni, nj, t + 1))
    return -1


# =============================================================================
# WAY 9: A* search with flood-aware heuristic (advanced)
# =============================================================================
def minimum_seconds_9(land):
    """
    Use A* with Manhattan distance heuristic.
    We weight each move by (cost to enter, including flood awareness).
    This gives optimal path but typically slower than BFS for unweighted grids.
    """
    import heapq
    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    si, sj = -1, -1
    di_, dj_ = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
            if land[i][j] == 'D':
                di_, dj_ = i, j

    if si == -1 or di_ == -1:
        return -1

    # Precompute flood times
    from collections import deque
    flood = [[INF] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))
    while fq:
        i, j = fq.popleft()
        for ddr, ddc in dirs:
            ni, nj = i + ddr, j + ddc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    # A* search
    def heuristic(r, c):
        return abs(r - di_) + abs(c - dj_)

    pq = [(heuristic(si, sj), 0, si, sj)]  # (f_score, g_score, r, c)
    best_g = {(si, sj): 0}

    while pq:
        f, g, r, c = heapq.heappop(pq)
        if (r, c) == (di_, dj_):
            return g
        if g > best_g.get((r, c), INF):
            continue
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < m and 0 <= nc < n):
                continue
            if land[nr][nc] == 'X':
                continue
            new_g = g + 1
            if new_g >= flood[nr][nc]:
                continue  # Would drown
            if new_g < best_g.get((nr, nc), INF):
                best_g[(nr, nc)] = new_g
                heapq.heappush(pq, (new_g + heuristic(nr, nc), new_g, nr, nc))
    return -1


# =============================================================================
# WAY 10: Using array of directions (zip)
# =============================================================================
def minimum_seconds_10(land):
    """Use zip with direction arrays."""
    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    DIRS = list(zip([-1, 1, 0, 0], [0, 0, -1, 1]))
    from collections import deque

    si, sj = next((i, j) for i, row in enumerate(land)
                  for j, c in enumerate(row) if c == 'S')

    flood = [[INF] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))
    while fq:
        i, j = fq.popleft()
        for dr, dc in DIRS:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    visited = [[False] * n for _ in range(m)]
    q = deque([(si, sj, 0)])
    visited[si][sj] = True
    while q:
        i, j, t = q.popleft()
        if land[i][j] == 'D':
            return t
        for dr, dc in DIRS:
            ni, nj = i + dr, j + dc
            if (0 <= ni < m and 0 <= nj < n and not visited[ni][nj]
                    and land[ni][nj] != 'X' and t + 1 < flood[ni][nj]):
                visited[ni][nj] = True
                q.append((ni, nj, t + 1))
    return -1


# =============================================================================
# WAY 11: Using sys.setrecursionlimit (avoid deep recursion)
# =============================================================================
def minimum_seconds_11(land):
    """
    Recursive DFS with memoization (less efficient than BFS but shows
    alternative approach). Set recursion limit for large grids.
    """
    import sys
    sys.setrecursionlimit(10000)
    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Precompute flood times via BFS (must be BFS, not DFS)
    from collections import deque
    flood = [[INF] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))
    while fq:
        i, j = fq.popleft()
        for dr, dc in DIRS:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    # Find S, D
    si, sj = -1, -1
    di_, dj_ = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
            if land[i][j] == 'D':
                di_, dj_ = i, j

    # DFS with memoization
    memo = {}

    def dfs(r, c, t):
        if (r, c) in memo and memo[(r, c)] <= t:
            return INF
        memo[(r, c)] = t
        if (r, c) == (di_, dj_):
            return t
        if land[r][c] == 'X':
            return INF
        if t >= flood[r][c]:
            return INF
        best = INF
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                if land[nr][nc] != 'X' and t + 1 < flood[nr][nc]:
                    res = dfs(nr, nc, t + 1)
                    if res < best:
                        best = res
        return best

    result = dfs(si, sj, 0)
    return result if result != INF else -1


# =============================================================================
# WAY 12: Multi-source BFS for flood + filter candidates early
# =============================================================================
def minimum_seconds_12(land):
    """
    Same as Way 1, but with a small optimization:
    Filter out 'unsafe' cells (those with flood_time=0 or 1) from the
    person BFS queue immediately. This avoids pushing doomed states.
    """
    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque

    si, sj = next((i, j) for i, row in enumerate(land)
                  for j, c in enumerate(row) if c == 'S')

    # Flood time computation
    flood = [[INF] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))
    while fq:
        i, j = fq.popleft()
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    # Person BFS with early filtering
    visited = [[False] * n for _ in range(m)]
    q = deque()
    if flood[si][sj] > 0:  # S itself isn't already flooded
        q.append((si, sj, 0))
        visited[si][sj] = True

    while q:
        i, j, t = q.popleft()
        if land[i][j] == 'D':
            return t
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj]:
                if land[ni][nj] != 'X' and t + 1 < flood[ni][nj]:
                    visited[ni][nj] = True
                    q.append((ni, nj, t + 1))
    return -1


# =============================================================================
# WAY 13: Class-based with clear separation
# =============================================================================
class FloodEscapeSolver:
    def __init__(self, land):
        self.land = land
        self.m = len(land)
        self.n = len(land[0]) if land else 0
        self.dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def solve(self):
        if not self.land or not self.land[0]:
            return -1
        flood_time = self._compute_flood_times()
        si, sj = self._find_cell('S')
        return self._bfs_person(si, sj, flood_time)

    def _compute_flood_times(self):
        from collections import deque
        INF = float('inf')
        flood_time = [[INF] * self.n for _ in range(self.m)]
        q = deque()
        for i in range(self.m):
            for j in range(self.n):
                if self.land[i][j] == '*':
                    flood_time[i][j] = 0
                    q.append((i, j))
        while q:
            i, j = q.popleft()
            for dr, dc in self.dirs:
                ni, nj = i + dr, j + dc
                if 0 <= ni < self.m and 0 <= nj < self.n:
                    if self.land[ni][nj] in ('X', 'D'):
                        continue
                    if flood_time[i][j] + 1 < flood_time[ni][nj]:
                        flood_time[ni][nj] = flood_time[i][j] + 1
                        q.append((ni, nj))
        return flood_time

    def _find_cell(self, target):
        for i in range(self.m):
            for j in range(self.n):
                if self.land[i][j] == target:
                    return i, j
        return -1, -1

    def _bfs_person(self, si, sj, flood_time):
        from collections import deque
        visited = [[False] * self.n for _ in range(self.m)]
        q = deque([(si, sj, 0)])
        visited[si][sj] = True
        while q:
            i, j, t = q.popleft()
            if self.land[i][j] == 'D':
                return t
            for dr, dc in self.dirs:
                ni, nj = i + dr, j + dc
                if (0 <= ni < self.m and 0 <= nj < self.n
                        and not visited[ni][nj]
                        and self.land[ni][nj] != 'X'
                        and t + 1 < flood_time[ni][nj]):
                    visited[ni][nj] = True
                    q.append((ni, nj, t + 1))
        return -1


def minimum_seconds_13(land):
    """Class-based solver - clean separation of concerns."""
    return FloodEscapeSolver(land).solve()


# =============================================================================
# WAY 14: Using namedtuple for state
# =============================================================================
def minimum_seconds_14(land):
    """Use namedtuple for clearer state representation."""
    from collections import namedtuple, deque
    State = namedtuple('State', ['r', 'c', 'time'])

    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    si, sj = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
                break
        if si != -1:
            break

    # Compute flood times
    flood = [[INF] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))
    while fq:
        i, j = fq.popleft()
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    # Person BFS with State
    visited = [[False] * n for _ in range(m)]
    q = deque([State(si, sj, 0)])
    visited[si][sj] = True
    while q:
        s = q.popleft()
        if land[s.r][s.c] == 'D':
            return s.time
        for dr, dc in dirs:
            nr, nc = s.r + dr, s.c + dc
            if (0 <= nr < m and 0 <= nc < n and not visited[nr][nc]
                    and land[nr][nc] != 'X' and s.time + 1 < flood[nr][nc]):
                visited[nr][nc] = True
                q.append(State(nr, nc, s.time + 1))
    return -1


# =============================================================================
# WAY 15: Using list as queue (slower but educational)
# =============================================================================
def minimum_seconds_15(land):
    """Use list with index pointer instead of deque."""
    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    si, sj = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
                break
        if si != -1:
            break

    # Flood times
    flood = [[INF] * n for _ in range(m)]
    from collections import deque
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))
    while fq:
        i, j = fq.popleft()
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    # Person BFS using list
    visited = [[False] * n for _ in range(m)]
    queue = [(si, sj, 0)]
    visited[si][sj] = True
    head = 0
    while head < len(queue):
        i, j, t = queue[head]
        head += 1
        if land[i][j] == 'D':
            return t
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if (0 <= ni < m and 0 <= nj < n and not visited[ni][nj]
                    and land[ni][nj] != 'X' and t + 1 < flood[ni][nj]):
                visited[ni][nj] = True
                queue.append((ni, nj, t + 1))
    return -1


# =============================================================================
# WAY 16: Precompute flood times using a separate function
# =============================================================================
def compute_flood_times(land):
    """Helper function to compute flood times for all cells."""
    if not land:
        return []
    m, n = len(land), len(land[0])
    INF = float('inf')
    flood = [[INF] * n for _ in range(m)]
    from collections import deque
    q = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                q.append((i, j))
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    while q:
        i, j = q.popleft()
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    q.append((ni, nj))
    return flood


def minimum_seconds_16(land):
    """Separated concern: use compute_flood_times helper."""
    if not land or not land[0]:
        return -1
    m, n = len(land), len(land[0])
    flood = compute_flood_times(land)
    if not flood:
        return -1

    si, sj = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
                break
        if si != -1:
            break

    from collections import deque
    visited = [[False] * n for _ in range(m)]
    q = deque([(si, sj, 0)])
    visited[si][sj] = True
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    while q:
        i, j, t = q.popleft()
        if land[i][j] == 'D':
            return t
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if (0 <= ni < m and 0 <= nj < n and not visited[ni][nj]
                    and land[ni][nj] != 'X' and t + 1 < flood[ni][nj]):
                visited[ni][nj] = True
                q.append((ni, nj, t + 1))
    return -1


# =============================================================================
# WAY 17: Optimized flood computation using set-based BFS
# =============================================================================
def minimum_seconds_17(land):
    """
    Use a 'frontier' set approach for flood propagation.
    More memory efficient for sparse floods.
    """
    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque

    si, sj = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
                break
        if si != -1:
            break

    # Flood BFS using sets
    flood = [[INF] * n for _ in range(m)]
    flood_frontier = set()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                flood_frontier.add((i, j))

    t = 0
    while flood_frontier:
        t += 1
        new_frontier = set()
        for i, j in flood_frontier:
            for dr, dc in dirs:
                ni, nj = i + dr, j + dc
                if (0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D')
                        and flood[ni][nj] == INF):
                    flood[ni][nj] = t
                    new_frontier.add((ni, nj))
        flood_frontier = new_frontier

    # Person BFS
    visited = [[False] * n for _ in range(m)]
    q = deque([(si, sj, 0)])
    visited[si][sj] = True
    while q:
        i, j, time = q.popleft()
        if land[i][j] == 'D':
            return time
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if (0 <= ni < m and 0 <= nj < n and not visited[ni][nj]
                    and land[ni][nj] != 'X' and time + 1 < flood[ni][nj]):
                visited[ni][nj] = True
                q.append((ni, nj, time + 1))
    return -1


# =============================================================================
# WAY 18: Using integer encoding for state
# =============================================================================
def minimum_seconds_18(land):
    """
    Encode (row, col, time) as a single integer for queue efficiency.
    row * N * T + col * T + time. Saves tuple memory.
    """
    if not land:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    MAX_TIME = m * n + 1
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque

    si, sj = -1, -1
    for i in range(m):
        for j in range(n):
            if land[i][j] == 'S':
                si, sj = i, j
                break
        if si != -1:
            break

    # Compute flood
    flood = [[INF] * n for _ in range(m)]
    fq = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == '*':
                flood[i][j] = 0
                fq.append((i, j))
    while fq:
        i, j = fq.popleft()
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in ('X', 'D'):
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    fq.append((ni, nj))

    # Person BFS with integer encoding
    visited = [[False] * n for _ in range(m)]
    q = deque([(si * MAX_TIME * n + sj * MAX_TIME, 0)])
    visited[si][sj] = True
    while q:
        code, t = q.popleft()
        i = code // (MAX_TIME * n)
        rem = code % (MAX_TIME * n)
        j = rem // MAX_TIME
        if land[i][j] == 'D':
            return t
        for dr, dc in dirs:
            ni, nj = i + dr, j + dc
            if (0 <= ni < m and 0 <= nj < n and not visited[ni][nj]
                    and land[ni][nj] != 'X' and t + 1 < flood[ni][nj]):
                visited[ni][nj] = True
                new_code = ni * MAX_TIME * n + nj * MAX_TIME + (t + 1)
                q.append((new_code, t + 1))
    return -1


# =============================================================================
# WAY 19: Most concise (Pythonic)
# =============================================================================
def minimum_seconds_19(land):
    """Concise Pythonic version."""
    from collections import deque
    if not land or not land[0]:
        return -1
    m, n = len(land), len(land[0])
    INF = float('inf')
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Find S
    si, sj = next((i, j) for i, row in enumerate(land)
                  for j, c in enumerate(row) if c == 'S')

    # Multi-source BFS for flood times
    flood = [[INF] * n for _ in range(m)]
    q = deque([(i, j) for i, row in enumerate(land)
               for j, c in enumerate(row) if c == '*'])
    for i, j in q:
        flood[i][j] = 0
    while q:
        i, j = q.popleft()
        for dr, dc in DIRS:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and land[ni][nj] not in 'XD':
                if flood[i][j] + 1 < flood[ni][nj]:
                    flood[ni][nj] = flood[i][j] + 1
                    q.append((ni, nj))

    # Person BFS
    seen = [[False] * n for _ in range(m)]
    seen[si][sj] = True
    q = deque([(si, sj, 0)])
    while q:
        i, j, t = q.popleft()
        if land[i][j] == 'D':
            return t
        for dr, dc in DIRS:
            ni, nj = i + dr, j + dc
            if 0 <= ni < m and 0 <= nj < n and not seen[ni][nj]:
                if land[ni][nj] != 'X' and t + 1 < flood[ni][nj]:
                    seen[ni][nj] = True
                    q.append((ni, nj, t + 1))
    return -1


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def minimum_seconds_20(land):
    """
    Final clean version. Combines best of all approaches:
    - Multi-source BFS for flood times
    - Person BFS with strict less-than comparison
    - Clear variable names
    """
    from collections import deque
    if not land or not land[0]:
        return -1
    rows, cols = len(land), len(land[0])
    INF = float('inf')
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Locate source
    si, sj = next((r, c) for r, row in enumerate(land)
                  for c, cell in enumerate(row) if cell == 'S')

    # Phase 1: Compute when each cell gets flooded (multi-source BFS from *)
    flood_time = [[INF] * cols for _ in range(rows)]
    flood_queue = deque()
    for r in range(rows):
        for c in range(cols):
            if land[r][c] == '*':
                flood_time[r][c] = 0
                flood_queue.append((r, c))

    while flood_queue:
        r, c = flood_queue.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and land[nr][nc] not in ('X', 'D'):
                if flood_time[r][c] + 1 < flood_time[nr][nc]:
                    flood_time[nr][nc] = flood_time[r][c] + 1
                    flood_queue.append((nr, nc))

    # Phase 2: Person BFS - must arrive strictly BEFORE flood
    visited = [[False] * cols for _ in range(rows)]
    person_queue = deque([(si, sj, 0)])
    visited[si][sj] = True

    while person_queue:
        r, c, t = person_queue.popleft()
        if land[r][c] == 'D':
            return t
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]
                    and land[nr][nc] != 'X' and t + 1 < flood_time[nr][nc]):
                visited[nr][nc] = True
                person_queue.append((nr, nc, t + 1))

    return -1


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the shortest time to reach D from S while avoiding both
stones (impassable) and flooded cells (which spread each second to
adjacent empty cells)."

Key Insight:
"This is NOT just BFS from S! The cell I want to step onto might be
safe NOW but be flooded by the time I get there. So I need to know
WHEN each cell becomes flooded, then plan my path to ARRIVE BEFORE
that time.

Strategy:
1. Compute FLOOD TIMES for every cell via multi-source BFS starting
   from all * cells. flood_time[i][j] = time when cell (i,j) floods.
2. BFS from S, but only allow moving to a cell if arrival_time < flood_time.
   The strict < is critical: arriving AT the same time it floods = drowning.
3. Return time when we reach D, or -1.

Why strict less-than (not <=)?
"Each second, BOTH you move AND the flood spreads (simultaneously). So if
you step onto a cell at the same time the flood reaches it, you drown.
You need to arrive STRICTLY BEFORE the flood arrives."

Edge cases:
- D never floods (problem guarantees this).
- Stone cells (X) are never walkable.
- * cells are impassable from start.
- If S is adjacent to D and D doesn't flood: answer is 1.
- If S is surrounded by stones/flood: return -1.
- Flood can never reach D (problem guarantees).

Complexity:
- Time:  O(m*n) - two BFS passes over m*n grid
- Space: O(m*n) - flood_time grid + visited grid

KEY TRICK:
The two-phase BFS pattern:
- Phase 1: Multi-source BFS from all * cells to compute flood times.
- Phase 2: Standard BFS from S, but with the flood_time check.

This is a common pattern for "time-dependent grid" problems.

RELATIONSHIP TO OTHER PROBLEMS:
- Rotting Oranges (LeetCode 994): Same multi-source BFS pattern.
- 01 Matrix (LeetCode 542): Distance from boundary.
- Walls and Gates (LeetCode 286): Multi-source BFS from gates.
- Shortest Path in Grid: Basic BFS without time-dependence.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Precompute flood + BFS (BEST)", minimum_seconds_1),
        ("Way 2: Verbose", minimum_seconds_2),
        ("Way 3: next() for finding S", minimum_seconds_3),
        ("Way 4: Tuple state BFS", minimum_seconds_4),
        ("Way 5: Simultaneous BFS", minimum_seconds_5),
        ("Way 6: BFS with state tracking", minimum_seconds_6),
        ("Way 7: Level-order BFS", minimum_seconds_7),
        ("Way 8: Named directions", minimum_seconds_8),
        ("Way 9: A* search", minimum_seconds_9),
        ("Way 10: zip directions", minimum_seconds_10),
        ("Way 11: DFS with memoization", minimum_seconds_11),
        ("Way 12: With early filtering", minimum_seconds_12),
        ("Way 13: Class-based", minimum_seconds_13),
        ("Way 14: Namedtuple state", minimum_seconds_14),
        ("Way 15: List as queue", minimum_seconds_15),
        ("Way 16: Helper function", minimum_seconds_16),
        ("Way 17: Set-based frontier", minimum_seconds_17),
        ("Way 18: Integer encoding", minimum_seconds_18),
        ("Way 19: Most concise", minimum_seconds_19),
        ("Way 20: Final cleanest", minimum_seconds_20),
    ]

    test_cases = [
        # Example from problem: 3 seconds (verified)
        # Path: S(0,1) -> (1,1) -> (2,1) -> D(2,2)
        (
            [['.', 'S', 'X', '*'],
             ['.', '.', 'X', '.'],
             ['.', '.', 'D', '.'],
             ['.', 'X', '.', '.'],
             ['*', '.', '.', '.']],
            3
        ),
        # Simple 2x3: S adjacent to D, D in same row, no obstacles
        (
            [['S', '.', 'D'],
             ['X', 'X', 'X']],
            2
        ),
        # Direct path S -> D (1 second)
        (
            [['S', 'D']],
            1
        ),
        # Flooded cell - flood at (0,1) spreads to (1,1) at t=1, blocking path
        # S(0,0) -> (1,0) at t=1. (1,0)'s flood_time=2. At t=2 from (1,0): (1,1) flood_time=1, blocked.
        # Cannot escape - return -1
        (
            [['S', '*', '.', '.', 'D'],
             ['.', '.', '.', '.', '.']],
            -1
        ),
        # Surrounded by stone - impossible
        (
            [['S', 'X', 'X'],
             ['X', 'X', 'X'],
             ['X', 'X', 'D']],
            -1
        ),
        # Larger example
        (
            [['S', '.', '.', '*', '.'],
             ['.', 'X', '.', 'X', '.'],
             ['.', '.', '.', '.', 'D']],
            -1  # flood at (0,3) spreads - check if reachable
        ),
        # Empty grid - return -1 (no S)
        ([], -1),
        # Single row, no obstacles
        ([['S', 'D']], 1),
        # 3x3 with no obstacles
        ([['S', '.', 'D']], 2),
        # Already flooded adjacent to S - impossible
        ([['S', '*', 'D']], -1),
    ]

    print("=" * 70)
    print("MINIMUM SECONDS TO REACH WITHOUT DROWNING - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-time-takes-to-reach-destination-without-drowning")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for land, expected in test_cases:
            try:
                import copy
                land_copy = copy.deepcopy(land)
                result = func(land_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: land={land} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on land={land} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)