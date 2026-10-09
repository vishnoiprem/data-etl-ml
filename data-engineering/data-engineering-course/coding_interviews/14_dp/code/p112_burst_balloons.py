"""Burst Balloons — maximum coins from bursting balloons.

Time:  O(n³) — three nested loops
Space: O(n²)
"""


def solve_burst_balloons(nums):
    """Return the max coins from bursting all balloons.

    >>> solve_burst_balloons([3, 1, 5, 8])
    167
    """
    n = len(nums)
    if n == 0:
        return 0
    # Pad with 1s on each side so the boundary multiplications are well-defined.
    arr = [1] + nums + [1]
    dp = [[0] * (n + 2) for _ in range(n + 2)]
    # Length of the sub-interval.
    for length in range(1, n + 1):
        for left in range(1, n - length + 2):
            right = left + length - 1
            # Try bursting every balloon in [left, right] last.
            for k in range(left, right + 1):
                coins = (arr[left - 1] * arr[k] * arr[right + 1]
                         + dp[left][k - 1] + dp[k + 1][right])
                if coins > dp[left][right]:
                    dp[left][right] = coins
    return dp[1][n]


if __name__ == "__main__":
    print(solve_burst_balloons([3, 1, 5, 8]))
