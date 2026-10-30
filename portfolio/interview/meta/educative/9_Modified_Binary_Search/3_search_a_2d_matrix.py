"""
Problem 3 (Medium) — Search a 2D Matrix
Pattern shape: A — Index-based with index mapping

Write an efficient algorithm that searches for a value target in an
m x n integer matrix. The matrix has the following properties:
  - Integers in each row are sorted in ascending order.
  - The first integer of each row is greater than the last integer of
    the previous row.
In other words, the matrix can be 'flattened' into a single sorted array.

Return True if target exists in the matrix, otherwise False. O(log(mn)).

Examples
--------
>>> search_matrix([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3)
True
>>> search_matrix([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13)
False

How to think (interview script)
------------------------------
"This matrix is essentially a sorted 1D array of length m*n. Two ways:

1) Treat it as a 1D binary search over a virtual array. Compute
   - row = mid // n
   - col = mid % n
   and compare matrix[row][col] to target. This is the cleanest.

2) Two-pass: first BS to find the candidate row (last row with first
   element <= target), then BS within that row.

I'll go with #1 — it shows I can recognize that the 'flattened' array
view is valid given the row-prefix property, and it gets O(log mn) in
one shot. Index mapping is a common trick interviewers love.

Edge case: if n == 0 (empty matrix) or any row is empty, return False."

Complexity: O(log(mn)) time, O(1) space.

Edge cases
----------
- m == 0 or n == 0 -> False
- m == 1 -> standard 1D BS on a single row
- Target smaller than all elements -> False
- Target larger than all elements -> False
- Target equals a boundary element -> True

Follow-ups the interviewer may ask
-----------------------------------
- "What if each row is sorted but row[0] of row i is NOT > row[-1] of row i-1?"
  Answer: that's a different problem (#search-a-2d-matrix-ii). You'd
  start at the top-right corner and walk down/left.
- "What if I want the index, not just True/False?"
  Answer: track the row/col at the return point.
- "Memory-constrained variant?"
  Answer: still O(1) space — we never materialize the 1D array.
"""
from typing import List


def search_matrix(matrix: List[List[int]], target: int) -> bool:
    """Search a row-major sorted matrix for target in O(log(mn)) time."""
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    lo, hi = 0, m * n - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        row, col = divmod(mid, n)
        val = matrix[row][col]
        if val == target:
            return True
        if val < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False


if __name__ == "__main__":
    M = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
    assert search_matrix(M, 3) is True
    assert search_matrix(M, 13) is False
    assert search_matrix(M, 1) is True
    assert search_matrix(M, 60) is True
    assert search_matrix(M, 0) is False
    assert search_matrix(M, 100) is False
    assert search_matrix([[1]], 1) is True
    assert search_matrix([], 1) is False
    assert search_matrix([[]], 1) is False
    print("All tests passed for search_a_2d_matrix.")
