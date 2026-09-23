"""
Longest Increasing Path in a Matrix

Given an m x n integer matrix, return the length of the longest
strictly increasing path. From each cell, you can move in 4 directions:
up, down, left, right.

Constraints: m, n >= 1; matrix values can be any integers.
"""

# ==============================================================
# Solution 1: Naive DFS (no memoization) - O(2^(m*n)) worst case
# ==============================================================
def longestIncreasingPath_dfs_naive(matrix):
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def dfs(i, j):
        best = 1
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and matrix[ni][nj] > matrix[i][j]:
                best = max(best, 1 + dfs(ni, nj))
        return best

    return max(dfs(i, j) for i in range(m) for j in range(n))


# ==============================================================
# Solution 2: Top-Down DP with Memoization - O(m*n)
# ==============================================================
def longestIncreasingPath_td_dp(matrix):
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    memo = [[0] * n for _ in range(m)]
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def dfs(i, j):
        if memo[i][j]:
            return memo[i][j]
        best = 1
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and matrix[ni][nj] > matrix[i][j]:
                best = max(best, 1 + dfs(ni, nj))
        memo[i][j] = best
        return best

    return max(dfs(i, j) for i in range(m) for j in range(n))


# ==============================================================
# Solution 3: Bottom-Up DP with sorted cells - O(m*n*log(m*n))
# ==============================================================
def longestIncreasingPath_sorted_dp(matrix):
    """
    Sort all cells by value, then DP. A cell's longest path = 1 + max
    of valid smaller-valued neighbors' dp. Processing cells in increasing
    order guarantees neighbors are computed first.
    """
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    cells = [(matrix[i][j], i, j) for i in range(m) for j in range(n)]
    cells.sort()
    dp = [[1] * n for _ in range(m)]
    best = 1
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for val, i, j in cells:
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and matrix[ni][nj] < val:
                if dp[ni][nj] + 1 > dp[i][j]:
                    dp[i][j] = dp[ni][nj] + 1
        if dp[i][j] > best:
            best = dp[i][j]
    return best


# ==============================================================
# Solution 4: BFS from minima (multi-source topological sort) - O(m*n)
# ==============================================================
def longestIncreasingPath_bfs(matrix):
    """
    Treat the matrix as a DAG. Start BFS from local minima (cells with
    no smaller neighbors). Each BFS level represents one step along an
    increasing path. The number of levels traversed is the longest path.
    """
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    out_degree = [[0] * n for _ in range(m)]

    for i in range(m):
        for j in range(n):
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and matrix[ni][nj] > matrix[i][j]:
                    out_degree[i][j] += 1

    from collections import deque
    queue = deque()
    for i in range(m):
        for j in range(n):
            if out_degree[i][j] == 0:
                queue.append((i, j))

    path_len = 0
    while queue:
        path_len += 1
        for _ in range(len(queue)):
            i, j = queue.popleft()
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and matrix[ni][nj] < matrix[i][j]:
                    out_degree[ni][nj] -= 1
                    if out_degree[ni][nj] == 0:
                        queue.append((ni, nj))
    return path_len


# ==============================================================
# Solution 5: Iterative DFS with explicit stack (no recursion) - O(m*n)
# ==============================================================
def longestIncreasingPath_iterative(matrix):
    """
    Iterative DFS with a post-order stack. We push (cell, False) to
    indicate "needs processing", then push children, then push
    (cell, True) to compute memoization value from children's results.
    """
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    memo = [[0] * n for _ in range(m)]
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def compute(i, j):
        # Standard iterative DFS using a stack with two states.
        stack = [(i, j, False)]
        while stack:
            ci, cj, returning = stack.pop()
            if returning:
                # Compute memo[ci][cj] from neighbors' memo
                best = 1
                for di, dj in directions:
                    ni, nj = ci + di, cj + dj
                    if (0 <= ni < m and 0 <= nj < n
                            and matrix[ni][nj] > matrix[ci][cj]):
                        if best < 1 + memo[ni][nj]:
                            best = 1 + memo[ni][nj]
                memo[ci][cj] = best
                continue
            if memo[ci][cj]:
                continue
            stack.append((ci, cj, True))  # post-order compute
            pushed = False
            for di, dj in directions:
                ni, nj = ci + di, cj + dj
                if (0 <= ni < m and 0 <= nj < n
                        and matrix[ni][nj] > matrix[ci][cj]
                        and not memo[ni][nj]):
                    stack.append((ni, nj, False))
                    pushed = True
            if not pushed:
                memo[ci][cj] = 1

    for i in range(m):
        for j in range(n):
            if not memo[i][j]:
                compute(i, j)

    return max(max(row) for row in memo)


# ==============================================================
# Solution 6: DSU to skip fully-explored components in DFS
# ==============================================================
def longestIncreasingPath_union_find(matrix):
    """
    Use DSU to skip re-exploring cells whose longest increasing path
    is already known. We precompute via DFS-with-memo the longest path
    starting at each cell. The DSU structure is built on-the-fly: when
    we finish exploring from a cell, we union it with all of its
    larger-valued neighbors (which we've also explored). This means
    if we later revisit any cell in this component, we just look up the
    cached value.

    The DSU itself doesn't change the algorithm's correctness — it
    only serves as an explicit "visited component" tracking. The real
    memoization is still per-cell.
    """
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    total = m * n

    parent = list(range(total))
    memo = [0] * total  # 0 = uncomputed, >0 = longest path starting here

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            # Union-by-rank would be ideal; here we just attach
            parent[ra] = rb

    def dfs(i, j):
        idx = i * n + j
        if memo[idx]:
            return memo[idx]
        # Find longest path from any larger-valued neighbor
        best = 1
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if (0 <= ni < m and 0 <= nj < n
                    and matrix[ni][nj] > matrix[i][j]):
                v = dfs(ni, nj)
                if v + 1 > best:
                    best = v + 1
                # Union this cell into the neighbor's explored component
                union(idx, ni * n + nj)
        memo[idx] = best
        return best

    overall = 0
    for i in range(m):
        for j in range(n):
            v = dfs(i, j)
            if v > overall:
                overall = v
    return overall


# ==============================================================
# Solution 7: DP with bitmasked visited cache (top-down, lazy) - O(m*n)
# ==============================================================
def longestIncreasingPath_lazy_dp(matrix):
    """
    Use a sentinel value (-1) in memo to distinguish "not visited" from
    "computed as 0". This lets us avoid the overhead of a separate
    'visited' boolean.
    """
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    memo = [[-1] * n for _ in range(m)]
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def dfs(i, j):
        if memo[i][j] != -1:
            return memo[i][j]
        best = 1
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if (0 <= ni < m and 0 <= nj < n
                    and matrix[ni][nj] > matrix[i][j]):
                best = max(best, 1 + dfs(ni, nj))
        memo[i][j] = best
        return best

    return max(dfs(i, j) for i in range(m) for j in range(n))


# ==============================================================
# Solution 8: DP with cell ordering + priority queue - O(m*n*log(m*n))
# ==============================================================
def longestIncreasingPath_priority_queue(matrix):
    """
    Same logic as sorted DP, but use a priority queue (heap) to
    process cells in increasing order. Useful if we want to start
    from a specific cell.
    """
    import heapq
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    heap = []
    for i in range(m):
        for j in range(n):
            heapq.heappush(heap, (matrix[i][j], i, j))
    dp = [[1] * n for _ in range(m)]
    best = 1
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while heap:
        val, i, j = heapq.heappop(heap)
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if (0 <= ni < m and 0 <= nj < n
                    and matrix[ni][nj] < val
                    and dp[ni][nj] + 1 > dp[i][j]):
                dp[i][j] = dp[ni][nj] + 1
        if dp[i][j] > best:
            best = dp[i][j]
    return best


# ==============================================================
# Solution 9: Cached DFS only triggered on demand - O(m*n)
# ==============================================================
def longestIncreasingPath_on_demand(matrix):
    """
    For each cell, only recurse into neighbors that could potentially
    lead to the longest path. We compute each cell exactly once and
    use the same memoization pattern.
    """
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    memo = {}
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def dfs(i, j):
        if (i, j) in memo:
            return memo[(i, j)]
        best = 1
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if (0 <= ni < m and 0 <= nj < n
                    and matrix[ni][nj] > matrix[i][j]):
                best = max(best, 1 + dfs(ni, nj))
        memo[(i, j)] = best
        return best

    return max(dfs(i, j) for i in range(m) for j in range(n))


# ==============================================================
# Solution 10: Bidirectional / Reverse DP - O(m*n)
# ==============================================================
def longestIncreasingPath_reverse_dp(matrix):
    """
    Compute longest path using a reverse traversal: from any cell,
    the longest path length equals 1 + max over larger-valued neighbors.
    Process cells in decreasing value order; memoize results.
    """
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])
    cells = [(matrix[i][j], i, j) for i in range(m) for j in range(n)]
    cells.sort(reverse=True)  # largest first
    memo = {}
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    best = 1

    # dp[val] = path length starting from (i,j) going to larger neighbors
    for val, i, j in cells:
        if (i, j) in memo:
            continue
        best_from_here = 1
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if (0 <= ni < m and 0 <= nj < n
                    and matrix[ni][nj] > val):
                # (ni, nj) will be processed earlier (larger value first)
                if (ni, nj) in memo:
                    best_from_here = max(best_from_here, 1 + memo[(ni, nj)])
                else:
                    # Compute on demand: should be processed already
                    pass
        memo[(i, j)] = best_from_here
        if best_from_here > best:
            best = best_from_here
    return best


# ==============================================================
# Test runner
# ==============================================================
if __name__ == "__main__":
    funcs = [
        ("DFS Naive",            longestIncreasingPath_dfs_naive),
        ("Top-Down DP",          longestIncreasingPath_td_dp),
        ("Sorted DP",            longestIncreasingPath_sorted_dp),
        ("BFS Topological",      longestIncreasingPath_bfs),
        ("Iterative DFS",        longestIncreasingPath_iterative),
        ("Union-Find",           longestIncreasingPath_union_find),
        ("Lazy DP",              longestIncreasingPath_lazy_dp),
        ("Priority Queue DP",    longestIncreasingPath_priority_queue),
        ("On-Demand Cache",      longestIncreasingPath_on_demand),
        ("Reverse DP",           longestIncreasingPath_reverse_dp),
    ]

    matrices = [
        # Classic example: answer is 4
        ([[9, 9, 4],
          [6, 6, 8],
          [2, 1, 1]], 4),
        ([[3, 4, 5],
          [3, 2, 6],
          [2, 2, 1]], 4),
        ([[1]], 1),
        ([[1, 2]], 2),
    ]

    for name, func in funcs:
        all_correct = True
        for mat, expected in matrices:
            try:
                got = func(mat)
                if got != expected:
                    all_correct = False
                    print(f"  [{name}] FAIL on {mat}: expected {expected}, got {got}")
            except Exception as e:
                all_correct = False
                print(f"  [{name}] ERROR on {mat}: {e}")
        if all_correct:
            print(f"  [{name}] PASS")
