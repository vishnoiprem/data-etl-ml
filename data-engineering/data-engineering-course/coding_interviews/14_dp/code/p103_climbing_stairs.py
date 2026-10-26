"""Climbing Stairs — count ways to reach the top taking 1 or 2 steps.

Time:  O(n) — single pass
Space: O(1) — two scalars
"""


def solve_climbing_stairs(n):
    """Return the number of distinct ways to reach step n.

    >>> solve_climbing_stairs(3)
    3
    """
    if n <= 1:
        return 1
    prev, curr = 1, 2
    for _ in range(3, n + 1):
        prev, curr = curr, prev + curr
    return curr


if __name__ == "__main__":
    print(solve_climbing_stairs(3))
