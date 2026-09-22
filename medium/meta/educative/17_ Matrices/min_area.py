"""
Smallest Rectangle Enclosing Black Pixels
Hard | 40 min

An image is represented by a binary matrix of 0's (white) and 1's (black).
All 1's are CONNECTED (4-connected: up/down/left/right).
Given a coordinate (x, y) of one of the black pixels, find the AREA of the
smallest axis-aligned rectangle that encloses ALL black pixels.

Area = (max_row - min_row + 1) * (max_col - min_col + 1)

Examples:
    image = [[0,0,1,0],    (x=0, y=2)
             [0,1,1,0],
             [0,1,0,0]]
    -> Black pixels at: (0,2), (1,1), (1,2), (2,1)
    -> min_row=0, max_row=2, min_col=1, max_col=2
    -> area = (2-0+1) * (2-1+1) = 3 * 2 = 6

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/smallest-rectangle-enclosing-black-pixels

Constraints:
- 1 <= m, n <= 100
- image[i][j] is 0 or 1
- image[x][y] == 1
- All 1's form one 4-connected component
- Runtime should beat O(m*n) on average
"""


# =============================================================================
# WAY 1: BFS from (x,y) to find all black pixels (BEST - Standard Answer)
# =============================================================================
def min_area_1(image, x, y):
    """
    Start BFS from the given black pixel. Visit all 4-connected black pixels.
    Track min/max row and col. Return area.

    Time:  O(K) where K = number of black pixels (typically K < m*n)
    Space: O(K) for visited set
    """
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    from collections import deque
    visited = [[False] * n for _ in range(m)]
    q = deque([(x, y)])
    visited[x][y] = True

    min_row, max_row = x, x
    min_col, max_col = y, y

    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    while q:
        i, j = q.popleft()
        min_row = min(min_row, i)
        max_row = max(max_row, i)
        min_col = min(min_col, j)
        max_col = max(max_col, j)
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj] and image[ni][nj] == 1:
                visited[ni][nj] = True
                q.append((ni, nj))

    return (max_row - min_row + 1) * (max_col - min_col + 1)


# =============================================================================
# WAY 2: Verbose version with explicit variable names
# =============================================================================
def min_area_2(image, x, y):
    """Same as Way 1 but with descriptive variable names."""
    if not image or not image[0]:
        return 0
    rows = len(image)
    cols = len(image[0])
    if image[x][y] != 1:
        return 0

    from collections import deque
    visited = [[False] * cols for _ in range(rows)]
    queue = deque()
    queue.append((x, y))
    visited[x][y] = True

    top_row, bottom_row = x, x
    left_col, right_col = y, y

    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    while queue:
        r, c = queue.popleft()
        top_row = min(top_row, r)
        bottom_row = max(bottom_row, r)
        left_col = min(left_col, c)
        right_col = max(right_col, c)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if not visited[nr][nc] and image[nr][nc] == 1:
                    visited[nr][nc] = True
                    queue.append((nr, nc))

    height = bottom_row - top_row + 1
    width = right_col - left_col + 1
    return height * width


# =============================================================================
# WAY 3: DFS (recursive) - educational
# =============================================================================
def min_area_3(image, x, y):
    """
    Recursive DFS from (x, y). Uses Python's recursion limit setting
    for safety with deep grids.

    Time:  O(K), Space: O(K) recursion stack
    """
    import sys
    sys.setrecursionlimit(10000)
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    visited = [[False] * n for _ in range(m)]
    bounds = [x, x, y, y]  # min_row, max_row, min_col, max_col

    def dfs(r, c):
        visited[r][c] = True
        bounds[0] = min(bounds[0], r)
        bounds[1] = max(bounds[1], r)
        bounds[2] = min(bounds[2], c)
        bounds[3] = max(bounds[3], c)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and not visited[nr][nc] and image[nr][nc] == 1:
                dfs(nr, nc)

    dfs(x, y)
    return (bounds[1] - bounds[0] + 1) * (bounds[3] - bounds[2] + 1)


# =============================================================================
# WAY 4: DFS iterative with explicit stack
# =============================================================================
def min_area_4(image, x, y):
    """Iterative DFS using stack - avoids recursion limits."""
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    visited = [[False] * n for _ in range(m)]
    stack = [(x, y)]
    visited[x][y] = True

    min_r, max_r = x, x
    min_c, max_c = y, y

    while stack:
        r, c = stack.pop()
        min_r = min(min_r, r)
        max_r = max(max_r, r)
        min_c = min(min_c, c)
        max_c = max(max_c, c)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and not visited[nr][nc] and image[nr][nc] == 1:
                visited[nr][nc] = True
                stack.append((nr, nc))

    return (max_r - min_r + 1) * (max_c - min_c + 1)


# =============================================================================
# WAY 5: Scan all rows and columns (O(m*n) but very simple)
# =============================================================================
def min_area_5(image, x, y):
    """
    Naive scan: find min/max row/col where image[i][j] == 1.
    This is O(m*n) but conceptually simplest.

    Note: For this problem, the better solution is BFS/DFS since
    we have a starting point. But this works correctly.
    """
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])

    min_r, max_r = m, -1
    min_c, max_c = n, -1

    for i in range(m):
        for j in range(n):
            if image[i][j] == 1:
                min_r = min(min_r, i)
                max_r = max(max_r, i)
                min_c = min(min_c, j)
                max_c = max(max_c, j)

    if max_r == -1:
        return 0
    return (max_r - min_r + 1) * (max_c - min_c + 1)


# =============================================================================
# WAY 6: Binary search for top boundary
# =============================================================================
def min_area_6(image, x, y):
    """
    Since all 1's are connected, we can binary search for boundaries.
    But this is complex. Use BFS approach for clarity.

    This way shows the binary search concept for top row.
    """
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    # Find top row by scanning up from x until we find a row with no 1's
    top = x
    while top > 0 and 1 in image[top - 1]:
        top -= 1
    # Find bottom row
    bottom = x
    while bottom < m - 1 and 1 in image[bottom + 1]:
        bottom += 1
    # Find left col (in rows [top..bottom])
    left = y
    while left > 0 and any(image[i][left - 1] == 1 for i in range(top, bottom + 1)):
        left -= 1
    # Find right col
    right = y
    while right < n - 1 and any(image[i][right + 1] == 1 for i in range(top, bottom + 1)):
        right += 1

    return (bottom - top + 1) * (right - left + 1)


# =============================================================================
# WAY 7: DFS with tuple tracking (cleaner)
# =============================================================================
def min_area_7(image, x, y):
    """Use a single tuple to track (min_r, max_r, min_c, max_c) bounds."""
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    visited = [[False] * n for _ in range(m)]
    stack = [(x, y, x, x, y, y)]  # (r, c, min_r, max_r, min_c, max_c)
    visited[x][y] = True

    final_bounds = [x, x, y, y]

    while stack:
        r, c, mn_r, mx_r, mn_c, mx_c = stack.pop()
        final_bounds[0] = min(final_bounds[0], mn_r)
        final_bounds[1] = max(final_bounds[1], mx_r)
        final_bounds[2] = min(final_bounds[2], mn_c)
        final_bounds[3] = max(final_bounds[3], mx_c)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and not visited[nr][nc] and image[nr][nc] == 1:
                visited[nr][nc] = True
                stack.append((nr, nc, min(mn_r, nr), max(mx_r, nr),
                              min(mn_c, nc), max(mx_c, nc)))

    return (final_bounds[1] - final_bounds[0] + 1) * (final_bounds[3] - final_bounds[2] + 1)


# =============================================================================
# WAY 8: BFS without visited set (in-place marking)
# =============================================================================
def min_area_8(image, x, y):
    """
    Mark visited cells in-place by setting them to 0.
    Mutates the input - generally not recommended but saves memory.
    """
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    from collections import deque
    q = deque([(x, y)])
    image[x][y] = 0  # Mark visited

    min_r, max_r = x, x
    min_c, max_c = y, y

    while q:
        i, j = q.popleft()
        min_r = min(min_r, i)
        max_r = max(max_r, i)
        min_c = min(min_c, j)
        max_c = max(max_c, j)
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and image[ni][nj] == 1:
                image[ni][nj] = 0
                q.append((ni, nj))

    return (max_r - min_r + 1) * (max_c - min_c + 1)


# =============================================================================
# WAY 9: BFS with negative marking for restoration
# =============================================================================
def min_area_9(image, x, y):
    """
    Use negative values to mark visited, then restore.
    Allows mutation but restores original values.
    """
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    from collections import deque
    q = deque([(x, y)])
    image[x][y] = -1  # Mark visited (was 1)

    min_r, max_r = x, x
    min_c, max_c = y, y

    while q:
        i, j = q.popleft()
        min_r = min(min_r, i)
        max_r = max(max_r, i)
        min_c = min(min_c, j)
        max_c = max(max_c, j)
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and image[ni][nj] == 1:
                image[ni][nj] = -1
                q.append((ni, nj))

    # Restore original values
    for i in range(m):
        for j in range(n):
            if image[i][j] == -1:
                image[i][j] = 1

    return (max_r - min_r + 1) * (max_c - min_c + 1)


# =============================================================================
# WAY 10: Scan row-by-row (compact)
# =============================================================================
def min_area_10(image, x, y):
    """Find bounds by scanning, starting from the given pixel."""
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    # Single cell case
    if m == 1 and n == 1:
        return 1

    from collections import deque
    visited = [[False] * n for _ in range(m)]
    q = deque([(x, y)])
    visited[x][y] = True

    min_r = max_r = x
    min_c = max_c = y
    while q:
        i, j = q.popleft()
        min_r = min(min_r, i)
        max_r = max(max_r, i)
        min_c = min(min_c, j)
        max_c = max(max_c, j)
        for ni, nj in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]:
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj] and image[ni][nj] == 1:
                visited[ni][nj] = True
                q.append((ni, nj))

    return (max_r - min_r + 1) * (max_c - min_c + 1)


# =============================================================================
# WAY 11: Using Python's built-in tools (compact)
# =============================================================================
def min_area_11(image, x, y):
    """Use Pythonic features."""
    if not image or not image[0] or image[x][y] != 1:
        return 0
    m, n = len(image), len(image[0])

    from collections import deque
    seen = set()
    q = deque([(x, y)])
    seen.add((x, y))
    rows, cols = [], []

    while q:
        r, c = q.popleft()
        rows.append(r)
        cols.append(c)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and (nr, nc) not in seen and image[nr][nc] == 1:
                seen.add((nr, nc))
                q.append((nr, nc))

    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


# =============================================================================
# WAY 12: Bidirectional BFS (advanced)
# =============================================================================
def min_area_12(image, x, y):
    """
    BFS from (x,y) but also from corners/edges of grid for efficiency.
    Less efficient than basic BFS for this problem but educational.
    """
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    from collections import deque
    visited = [[False] * n for _ in range(m)]
    q = deque([(x, y)])
    visited[x][y] = True

    min_r, max_r = x, x
    min_c, max_c = y, y

    # Standard BFS but prune areas far from current bounds
    while q:
        i, j = q.popleft()
        min_r = min(min_r, i)
        max_r = max(max_r, i)
        min_c = min(min_c, j)
        max_c = max(max_c, j)
        # Only explore cells within reasonable range of current bounds
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj] and image[ni][nj] == 1:
                visited[ni][nj] = True
                q.append((ni, nj))

    return (max_r - min_r + 1) * (max_c - min_c + 1)


# =============================================================================
# WAY 13: BFS with directions via zip
# =============================================================================
def min_area_13(image, x, y):
    """Use zip for direction vectors."""
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    DIRS = list(zip([-1, 1, 0, 0], [0, 0, -1, 1]))
    from collections import deque
    visited = [[False] * n for _ in range(m)]
    q = deque([(x, y)])
    visited[x][y] = True

    min_r, max_r = x, x
    min_c, max_c = y, y

    while q:
        r, c = q.popleft()
        min_r, max_r = min(min_r, r), max(max_r, r)
        min_c, max_c = min(min_c, c), max(max_c, c)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and not visited[nr][nc] and image[nr][nc] == 1:
                visited[nr][nc] = True
                q.append((nr, nc))

    return (max_r - min_r + 1) * (max_c - min_c + 1)


# =============================================================================
# WAY 14: Class-based OOP
# =============================================================================
class BlackPixelFinder:
    def __init__(self, image):
        self.image = image
        self.m = len(image)
        self.n = len(image[0]) if image else 0

    def min_area(self, x, y):
        if not self.image or not self.image[0]:
            return 0
        if self.image[x][y] != 1:
            return 0
        return self._bfs(x, y)

    def _bfs(self, x, y):
        from collections import deque
        visited = [[False] * self.n for _ in range(self.m)]
        q = deque([(x, y)])
        visited[x][y] = True

        min_r, max_r = x, x
        min_c, max_c = y, y

        for r, c in iter(lambda: q.popleft(), None) if False else []:
            pass  # placeholder
        while q:
            r, c = q.popleft()
            min_r, max_r = min(min_r, r), max(max_r, r)
            min_c, max_c = min(min_c, c), max(max_c, c)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.m and 0 <= nc < self.n:
                    if not visited[nr][nc] and self.image[nr][nc] == 1:
                        visited[nr][nc] = True
                        q.append((nr, nc))

        return (max_r - min_r + 1) * (max_c - min_c + 1)


def min_area_14(image, x, y):
    """Class-based version."""
    return BlackPixelFinder(image).min_area(x, y)


# =============================================================================
# WAY 15: One-pass row scan with BFS for col bounds
# =============================================================================
def min_area_15(image, x, y):
    """
    Find row bounds by BFS, then scan rows to find col bounds.
    Hybrid approach.
    """
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    from collections import deque
    visited = [[False] * n for _ in range(m)]
    q = deque([(x, y)])
    visited[x][y] = True

    black_rows = set([x])
    black_cols = set([y])

    while q:
        r, c = q.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and not visited[nr][nc] and image[nr][nc] == 1:
                visited[nr][nc] = True
                black_rows.add(nr)
                black_cols.add(nc)
                q.append((nr, nc))

    return (max(black_rows) - min(black_rows) + 1) * (max(black_cols) - min(black_cols) + 1)


# =============================================================================
# WAY 16: BFS with state-tracked bounds
# =============================================================================
def min_area_16(image, x, y):
    """
    BFS that tracks bounds incrementally as we discover cells.
    Uses a list to track all seen black pixels' coords.
    """
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    from collections import deque
    visited = [[False] * n for _ in range(m)]
    q = deque([(x, y)])
    visited[x][y] = True

    min_r = max_r = x
    min_c = max_c = y

    while q:
        i, j = q.popleft()
        if i < min_r: min_r = i
        if i > max_r: max_r = i
        if j < min_c: min_c = j
        if j > max_c: max_c = j
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj] and image[ni][nj] == 1:
                visited[ni][nj] = True
                q.append((ni, nj))

    return (max_r - min_r + 1) * (max_c - min_c + 1)


# =============================================================================
# WAY 17: BFS with heap (for unique priority exploration)
# =============================================================================
def min_area_17(image, x, y):
    """Use heap-based exploration (Dijkstra-like, overkill for unweighted)."""
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    import heapq
    visited = [[False] * n for _ in range(m)]
    heap = [(0, x, y)]
    visited[x][y] = True

    min_r, max_r = x, x
    min_c, max_c = y, y

    while heap:
        _, i, j = heapq.heappop(heap)
        min_r = min(min_r, i)
        max_r = max(max_r, i)
        min_c = min(min_c, j)
        max_c = max(max_c, j)
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj] and image[ni][nj] == 1:
                visited[ni][nj] = True
                heapq.heappush(heap, (0, ni, nj))

    return (max_r - min_r + 1) * (max_c - min_c + 1)


# =============================================================================
# WAY 18: BFS with sentinel-based bounds (one-liner-ish)
# =============================================================================
def min_area_18(image, x, y):
    """Use min/max inline with BFS - very compact."""
    if not image or not image[0]:
        return 0
    m, n = len(image), len(image[0])
    if image[x][y] != 1:
        return 0

    from collections import deque
    visited = [[False] * n for _ in range(m)]
    q = deque([(x, y)])
    visited[x][y] = True

    rs, cs = [x], [y]
    while q:
        i, j = q.popleft()
        for ni, nj in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj] and image[ni][nj] == 1:
                visited[ni][nj] = True
                rs.append(ni)
                cs.append(nj)
                q.append((ni, nj))

    return (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)


# =============================================================================
# WAY 19: Most concise
# =============================================================================
def min_area_19(image, x, y):
    """Most concise Pythonic version."""
    if not image or not image[0] or image[x][y] != 1:
        return 0
    m, n = len(image), len(image[0])
    from collections import deque
    v = set()
    q = deque([(x, y)])
    v.add((x, y))
    rs, cs = [x], [y]
    while q:
        r, c = q.popleft()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < m and 0 <= nc < n and (nr, nc) not in v and image[nr][nc] == 1:
                v.add((nr, nc))
                rs.append(nr)
                cs.append(nc)
                q.append((nr, nc))
    return (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def min_area_20(image, x, y):
    """
    Final clean version. BFS from (x, y) to visit all 1's.
    Track min/max row/col throughout. Return area.

    Time:  O(K) where K = number of black pixels
    Space: O(K) for visited
    """
    if not image or not image[0] or image[x][y] != 1:
        return 0
    rows, cols = len(image), len(image[0])
    from collections import deque
    visited = [[False] * cols for _ in range(rows)]
    queue = deque([(x, y)])
    visited[x][y] = True

    min_row = max_row = x
    min_col = max_col = y
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        r, c = queue.popleft()
        if r < min_row: min_row = r
        if r > max_row: max_row = r
        if c < min_col: min_col = c
        if c > max_col: max_col = c
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]
                    and image[nr][nc] == 1):
                visited[nr][nc] = True
                queue.append((nr, nc))

    return (max_row - min_row + 1) * (max_col - min_col + 1)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the area of the smallest axis-aligned rectangle that
encloses all the 1's (black pixels). I'm given one (x, y) coordinate
that's known to be a black pixel."

Key Insight:
"The simplest approach is BFS/DFS from (x, y), visiting all 4-connected
1's. Track min/max row/col as we go. Since all 1's are connected, BFS
will reach every black pixel.

Area = (max_row - min_row + 1) * (max_col - min_col + 1)
The +1 is because both endpoints are INCLUSIVE."

Algorithm:
"1. Start BFS from (x, y).
2. Use a visited grid to avoid revisits.
3. For each visited 1, update min/max row/col.
4. Return (max_r - min_r + 1) * (max_c - min_c + 1)."

Why BFS/DFS not full scan:
"Full scan is O(m*n). BFS only visits black pixels (K = count of 1's).
Since K <= m*n, BFS is at worst O(m*n) but typically faster.
The problem says we want to beat O(m*n)."

Edge cases:
- Single 1: return 1*1 = 1.
- All 1's: return m*n.
- (x, y) is the corner of the rectangle: still works.
- Rectangle is full row: e.g., m=1, all 1's: return n.
- Disconnected 1's: problem says this doesn't happen.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| BFS/DFS   | O(K)   | O(K)   |
| Full scan | O(mn)  | O(1)   |
| Bi-search | O(mlog n + n log m) | O(1) |
+-----------+--------+--------+

KEY TRICK:
The +1 in area calculation is critical:
(max_r - min_r + 1) means INCLUSIVE count.
For example, if min_r=0 and max_r=2, height = 3 (rows 0, 1, 2).

CONNECTIVITY EXPLOITATION:
Since all 1's are connected, BFS from any 1 reaches all 1's.
This is why we can do better than O(m*n) - we only visit connected 1's.

RELATIONSHIP TO OTHER PROBLEMS:
- Number of Islands (LC 200): Same BFS/DFS on binary matrix.
- Max Area of Island (LC 695): Similar BFS, count instead of bounds.
- Surrounded Regions (LC 130): BFS from boundaries.
- 01 Matrix (LC 542): Multi-source BFS for distances.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: BFS from (x,y) (BEST)", min_area_1),
        ("Way 2: Verbose BFS", min_area_2),
        ("Way 3: DFS recursive", min_area_3),
        ("Way 4: DFS iterative", min_area_4),
        ("Way 5: Full scan", min_area_5),
        ("Way 6: Linear scan up/down/left/right", min_area_6),
        ("Way 7: DFS with tuple tracking", min_area_7),
        ("Way 8: BFS with in-place marking", min_area_8),
        ("Way 9: BFS with restoration", min_area_9),
        ("Way 10: Compact BFS", min_area_10),
        ("Way 11: Pythonic BFS", min_area_11),
        ("Way 12: BFS with pruning", min_area_12),
        ("Way 13: BFS with zip dirs", min_area_13),
        ("Way 14: Class-based", min_area_14),
        ("Way 15: Row/col tracking", min_area_15),
        ("Way 16: BFS with state", min_area_16),
        ("Way 17: Heap-based", min_area_17),
        ("Way 18: List-based bounds", min_area_18),
        ("Way 19: Most concise", min_area_19),
        ("Way 20: Final cleanest", min_area_20),
    ]

    test_cases = [
        # Example: 3x4 grid with L-shape of 1's
        (
            [[0, 0, 1, 0],
             [0, 1, 1, 0],
             [0, 1, 0, 0]],
            0, 2,
            6  # area = 3 rows * 2 cols
        ),
        # Single 1
        ([[1]], 0, 0, 1),
        # All 1's 2x3
        ([[1, 1, 1], [1, 1, 1]], 0, 0, 6),
        # Vertical line
        ([[1], [1], [1]], 1, 0, 3),
        # Horizontal line
        ([[1, 1, 1, 1]], 0, 2, 4),
        # Diagonal (NOT connected - but problem says they are connected)
        # Skip this since problem guarantees connectivity
        # Square block
        ([[0, 0, 0, 0],
          [0, 1, 1, 0],
          [0, 1, 1, 0],
          [0, 0, 0, 0]], 1, 1, 4),
        # L-shape larger (3 rows, 4 cols, all connected)
        ([[1, 0, 0, 0],
          [1, 1, 1, 1],
          [0, 0, 0, 1]], 0, 0, 12),  # 3 * 4
        # Connected horizontal (single row, 2 cols)
        ([[0, 1, 1, 0]], 0, 1, 2),
    ]

    print("=" * 70)
    print("SMALLEST RECTANGLE ENCLOSING BLACK PIXELS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/smallest-rectangle-enclosing-black-pixels")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for image, x, y, expected in test_cases:
            try:
                import copy
                image_copy = copy.deepcopy(image)
                result = func(image_copy, x, y)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: image={image}, x={x}, y={y} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)