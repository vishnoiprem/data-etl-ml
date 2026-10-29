def uniquePathsWithObstacles(obstacleGrid):
    """
    Count the number of unique paths from top-left to bottom-right of an
    m x n grid, moving only right or down, avoiding obstacles (cells with 1).
    """
    if not obstacleGrid or not obstacleGrid[0]:
        return 0

    m, n = len(obstacleGrid), len(obstacleGrid[0])

    # dp[i][j] = number of paths from (0, 0) to (i, j) avoiding obstacles
    dp = [[0] * n for _ in range(m)]

    # If start cell is blocked, no paths exist
    if obstacleGrid[0][0] == 1:
        return 0
    dp[0][0] = 1

    # First column: only reachable from above
    for i in range(1, m):
        dp[i][0] = 0 if obstacleGrid[i][0] == 1 else dp[i - 1][0]

    # First row: only reachable from the left
    for j in range(1, n):
        dp[0][j] = 0 if obstacleGrid[0][j] == 1 else dp[0][j - 1]

    # Fill the rest of the grid
    for i in range(1, m):
        for j in range(1, n):
            if obstacleGrid[i][j] == 1:
                dp[i][j] = 0
            else:
                dp[i][j] = dp[i - 1][j] + dp[i][j - 1]

    return dp[m - 1][n - 1]


if __name__ == "__main__":
    # Test cases
    grid1 = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    print(uniquePathsWithObstacles(grid1))   # 2

    grid2 = [
        [0, 1],
        [0, 0],
    ]
    print(uniquePathsWithObstacles(grid2))   # 1

    grid3 = [[1, 0]]
    print(uniquePathsWithObstacles(grid3))   # 0

    grid4 = [[0]]
    print(uniquePathsWithObstacles(grid4))   # 1
