"""
LUCKY NUMBERS IN A MATRIX — LeetCode 1380
========================================
A "lucky number" in an m × n matrix is an element that is:
    • the minimum in its ROW, AND
    • the maximum in its COLUMN.

Return all lucky numbers (in any order).

Pattern: don't try to be clever. Pre-compute every row's min and every
column's max, then keep cells where row_min[r] == col_max[c] == matrix[r][c].
"""

from typing import List


def lucky_numbers(matrix: List[List[int]]) -> List[int]:
    if not matrix:
        return []
    row_min = [min(row) for row in matrix]
    col_max = [max(matrix[r][c] for r in range(len(matrix)))
               for c in range(len(matrix[0]))]
    return [matrix[r][c]
            for r in range(len(matrix))
            for c in range(len(matrix[0]))
            if matrix[r][c] == row_min[r] == col_max[c]]


if __name__ == "__main__":
    print(lucky_numbers([[3,7,8],[9,11,13],[15,16,17]]))   # [15]
    print(lucky_numbers([[1,10,4,2],[9,3,8,7],[15,16,17,12]]))  # [12]
