def maximalSquare(matrix):
    """
    Find the area of the largest square containing only 1s in a binary matrix.

    dp[i][j] = side length of the largest square ending at cell (i, j).
    """
    if not matrix or not matrix[0]:
        return 0

    m, n = len(matrix), len(matrix[0])
    # dp[i][j] = side length of largest all-1 square with bottom-right at (i,j)
    dp = [[0] * n for _ in range(m)]
    best = 0

    for i in range(m):
        for j in range(n):
            if matrix[i][j] == '1':
                if i == 0 or j == 0:
                    # First row or column: cell itself forms a 1x1 square
                    dp[i][j] = 1
                else:
                    # Side length limited by min of neighbors + 1
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],     # top
                        dp[i][j - 1],     # left
                        dp[i - 1][j - 1], # top-left diagonal
                    )
                best = max(best, dp[i][j])
            # else: dp[i][j] stays 0

    return best * best


if __name__ == "__main__":
    # Test cases
    m1 = [
        ['1', '0', '1', '0', '0'],
        ['1', '0', '1', '1', '1'],
        ['1', '1', '1', '1', '1'],
        ['1', '0', '0', '1', '0'],
    ]
    print(maximalSquare(m1))   # 4

    m2 = [
        ['0', '1'],
        ['1', '0'],
    ]
    print(maximalSquare(m2))   # 1

    m3 = [['0']]
    print(maximalSquare(m3))   # 0

    m4 = [['1']]
    print(maximalSquare(m4))   # 1
