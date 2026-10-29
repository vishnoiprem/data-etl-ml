def minPathSum(grid):
    """
    Find the minimum sum path from top-left to bottom-right of a grid,
    moving only right or down.
    """
    if not grid or not grid[0]:
        return 0

    m, n = len(grid), len(grid[0])
    # dp[i][j] = min sum to reach (i, j)
    dp = [[0] * n for _ in range(m)]
    dp[0][0] = grid[0][0]

    # First row: only from the left
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + grid[0][j]

    # First column: only from above
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + grid[i][0]

    # Fill the rest
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = grid[i][j] + min(dp[i - 1][j], dp[i][j - 1])

    return dp[m - 1][n - 1]


if __name__ == "__main__":
    # Test cases
    g1 = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1],
    ]
    print(minPathSum(g1))   # 7  (path: 1→3→1→1→1 = 7, or 1→1→4→2→1 = 9, etc.)

    g2 = [
        [1, 2, 3],
        [4, 5, 6],
    ]
    print(minPathSum(g2))   # 12 (path: 1→2→3→6 = 12)

    g3 = [[1]]
    print(minPathSum(g3))   # 1

    g4 = [[1, 2], [1, 1]]
    print(minPathSum(g4))   # 3 (path: 1→1→1 = 3)
