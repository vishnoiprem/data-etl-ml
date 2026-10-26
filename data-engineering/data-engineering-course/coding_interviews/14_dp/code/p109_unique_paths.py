"""Unique Paths — top-left to bottom-right on a grid.

Time:  O(m · n)
Space: O(n) — rolling row
"""


def solve_unique_paths(m, n):
    """Return the number of unique paths on an m x n grid.

    >>> solve_unique_paths(3, 7)
    28
    """
    row = [1] * n
    for _ in range(m - 1):
        for j in range(1, n):
            row[j] += row[j - 1]
    return row[-1]


if __name__ == "__main__":
    print(solve_unique_paths(3, 7))
