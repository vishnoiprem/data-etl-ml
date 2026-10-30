"""
Toeplitz Matrix
Easy | 15 min

Given an m x n matrix, return True if the matrix is Toeplitz.
A matrix is Toeplitz if every diagonal from top-left to bottom-right
contains the same elements. Equivalently, matrix[i][j] must equal
matrix[i+1][j+1] for all valid (i, j).

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/toeplitz-matrix

Constraints:
- 1 <= m, n <= 20
- 0 <= matrix[i][j] <= 99

Examples:
    [[1,2,3,4],
     [5,1,2,3],
     [9,5,1,2]] -> True
    [[1,2],
     [2,2]] -> False  (diagonal 0,0 to 1,1 should be all same; 1!=2)

Key Insight:
- Every cell (i, j) should equal the cell to its bottom-right (i+1, j+1).
- Check all (i, j) pairs.

Time:  O(m*n) - check each cell.
Space: O(1) - no extra data structures.
"""


# =============================================================================
# WAY 1: Direct comparison (BEST - Memorize!)
# =============================================================================
def isToeplitzMatrix_1(matrix):
    """
    For each cell (i, j), check if matrix[i][j] == matrix[i+1][j+1].
    If any mismatch, return False. Otherwise True.
    """
    if not matrix or not matrix[0]:
        return True
    m, n = len(matrix), len(matrix[0])
    for i in range(m - 1):
        for j in range(n - 1):
            if matrix[i][j] != matrix[i + 1][j + 1]:
                return False
    return True


# =============================================================================
# WAY 2: All with any/all
# =============================================================================
def isToeplitzMatrix_2(matrix):
    """Use all() with generator expression."""
    if not matrix or not matrix[0]:
        return True
    m, n = len(matrix), len(matrix[0])
    return all(matrix[i][j] == matrix[i + 1][j + 1]
               for i in range(m - 1)
               for j in range(n - 1))


# =============================================================================
# WAY 3: Use zip to compare rows
# =============================================================================
def isToeplitzMatrix_3(matrix):
    """
    Compare each row with the next row shifted by 1.
    If all shifted comparisons match, it's Toeplitz.
    """
    if not matrix or not matrix[0]:
        return True
    return all(row1[j] == row2[j + 1]
               for row1, row2 in zip(matrix, matrix[1:])
               for j in range(len(row1) - 1))


# =============================================================================
# WAY 4: Use enumerate and zip
# =============================================================================
def isToeplitzMatrix_4(matrix):
    """Compare pairs of adjacent rows using enumerate + zip."""
    if not matrix or not matrix[0]:
        return True
    for i, (row, next_row) in enumerate(zip(matrix, matrix[1:])):
        for j in range(len(row) - 1):
            if row[j] != next_row[j + 1]:
                return False
    return True


# =============================================================================
# WAY 5: Iterate over diagonals
# =============================================================================
def isToeplitzMatrix_5(matrix):
    """
    Iterate over each diagonal starting from top row and left column.
    Each diagonal must have all equal elements.
    """
    if not matrix or not matrix[0]:
        return True
    m, n = len(matrix), len(matrix[0])

    # Diagonals starting from top row
    for j in range(n):
        if not all(matrix[i][j + i] == matrix[0][j]
                   for i in range(min(m, n - j))):
            return False

    # Diagonals starting from left column (excluding first cell)
    for i in range(1, m):
        if not all(matrix[i + k][k] == matrix[i][0]
                   for k in range(min(m - i, n))):
            return False

    return True


# =============================================================================
# WAY 6: Use set for each diagonal
# =============================================================================
def isToeplitzMatrix_6(matrix):
    """
    For each diagonal, all elements must be equal (set size = 1).
    """
    if not matrix or not matrix[0]:
        return True
    m, n = len(matrix), len(matrix[0])

    # Iterate over starting positions of diagonals
    for j in range(n):
        diag = [matrix[i][j + i] for i in range(min(m, n - j))]
        if len(set(diag)) != 1:
            return False

    for i in range(1, m):
        diag = [matrix[i + k][k] for k in range(min(m - i, n))]
        if len(set(diag)) != 1:
            return False

    return True


# =============================================================================
# WAY 7: Numpy-based
# =============================================================================
def isToeplitzMatrix_7(matrix):
    """Use numpy for fast comparison."""
    try:
        import numpy as np
        if not matrix or not matrix[0]:
            return True
        arr = np.array(matrix)
        # Check all (i, j) pairs
        return np.all(arr[:-1, :-1] == arr[1:, 1:])
    except ImportError:
        return isToeplitzMatrix_1(matrix)


# =============================================================================
# WAY 8: Use map/zip on diagonals
# =============================================================================
def isToeplitzMatrix_8(matrix):
    """Use map over diagonals."""
    if not matrix or not matrix[0]:
        return True
    m, n = len(matrix), len(matrix[0])

    def diag_at(r, c):
        """Get elements of diagonal starting at (r, c)."""
        result = []
        while r < m and c < n:
            result.append(matrix[r][c])
            r += 1
            c += 1
        return result

    # Diagonals from top row
    for j in range(n):
        if len(set(diag_at(0, j))) != 1:
            return False
    # Diagonals from left column (skip first, already counted)
    for i in range(1, m):
        if len(set(diag_at(i, 0))) != 1:
            return False
    return True


# =============================================================================
# WAY 9: Group by (i - j) index
# =============================================================================
def isToeplitzMatrix_9(matrix):
    """
    Group elements by (i - j) (same diagonal). All elements in
    each group must be equal.
    """
    if not matrix or not matrix[0]:
        return True
    from collections import defaultdict
    diagonals = defaultdict(set)
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            diagonals[i - j].add(matrix[i][j])
    return all(len(v) == 1 for v in diagonals.values())


# =============================================================================
# WAY 10: Use reduce
# =============================================================================
def isToeplitzMatrix_10(matrix):
    """Use functools.reduce to check all cells."""
    if not matrix or not matrix[0]:
        return True
    from functools import reduce
    m, n = len(matrix), len(matrix[0])
    checks = [matrix[i][j] == matrix[i + 1][j + 1]
              for i in range(m - 1)
              for j in range(n - 1)]
    return reduce(lambda a, b: a and b, checks, True)


# =============================================================================
# WAY 11: Class-based
# =============================================================================
class ToeplitzChecker:
    def __init__(self, matrix):
        self.matrix = matrix
        self.m = len(matrix)
        self.n = len(matrix[0]) if matrix else 0

    def is_toeplitz(self):
        for i in range(self.m - 1):
            for j in range(self.n - 1):
                if self.matrix[i][j] != self.matrix[i + 1][j + 1]:
                    return False
        return True


def isToeplitzMatrix_11(matrix):
    """Class-based solution."""
    if not matrix or not matrix[0]:
        return True
    return ToeplitzChecker(matrix).is_toeplitz()


# =============================================================================
# WAY 12: Use itertools.pairwise (Python 3.10+)
# =============================================================================
def isToeplitzMatrix_12(matrix):
    """Use pairwise to compare adjacent rows."""
    if not matrix or not matrix[0]:
        return True
    try:
        from itertools import pairwise
        return all(row1[j] == row2[j + 1]
                   for row1, row2 in pairwise(matrix)
                   for j in range(len(row1) - 1))
    except ImportError:
        # Fallback for older Python
        return all(row1[j] == row2[j + 1]
                   for row1, row2 in zip(matrix, matrix[1:])
                   for j in range(len(row1) - 1))


# =============================================================================
# WAY 13: Memory-constrained (one row at a time)
# =============================================================================
def isToeplitzMatrix_13(matrix):
    """
    Simulate memory-constrained scenario: only one row at a time.
    We need to remember the previous row's values.
    """
    if not matrix or not matrix[0]:
        return True
    prev_row = None
    for row in matrix:
        if prev_row is not None:
            for j in range(len(row) - 1):
                if prev_row[j] != row[j + 1]:
                    return False
        prev_row = row
    return True


# =============================================================================
# WAY 14: Use all() with generator - compact
# =============================================================================
def isToeplitzMatrix_14(matrix):
    """Compact all() generator."""
    if not matrix or not matrix[0]:
        return True
    m, n = len(matrix), len(matrix[0])
    return all(matrix[i][j] == matrix[i + 1][j + 1]
               for i in range(m - 1)
               for j in range(n - 1))


# =============================================================================
# WAY 15: Generator-based check
# =============================================================================
def isToeplitzMatrix_15(matrix):
    """Generator-based check."""
    if not matrix or not matrix[0]:
        return True

    def check():
        for i in range(len(matrix) - 1):
            for j in range(len(matrix[0]) - 1):
                if matrix[i][j] != matrix[i + 1][j + 1]:
                    yield False
                    return
                yield True

    return all(check())


# =============================================================================
# WAY 16: Use product from itertools
# =============================================================================
def isToeplitzMatrix_16(matrix):
    """Use itertools.product."""
    if not matrix or not matrix[0]:
        return True
    from itertools import product
    m, n = len(matrix), len(matrix[0])
    return all(matrix[i][j] == matrix[i + 1][j + 1]
               for i, j in product(range(m - 1), range(n - 1)))


# =============================================================================
# WAY 17: Early return with flag
# =============================================================================
def isToeplitzMatrix_17(matrix):
    """Early return with explicit flag."""
    if not matrix or not matrix[0]:
        return True
    is_valid = True
    for i in range(len(matrix) - 1):
        if not is_valid:
            break
        for j in range(len(matrix[0]) - 1):
            if matrix[i][j] != matrix[i + 1][j + 1]:
                is_valid = False
                break
    return is_valid


# =============================================================================
# WAY 18: Use map with lambda
# =============================================================================
def isToeplitzMatrix_18(matrix):
    """Use map with lambda."""
    if not matrix or not matrix[0]:
        return True
    m, n = len(matrix), len(matrix[0])
    # Generate all checks
    checks = map(lambda x: matrix[x[0]][x[1]] == matrix[x[0] + 1][x[1] + 1],
                 [(i, j) for i in range(m - 1) for j in range(n - 1)])
    return all(checks)


# =============================================================================
# WAY 19: One-liner
# =============================================================================
def isToeplitzMatrix_19(matrix):
    """One-liner."""
    if not matrix or not matrix[0]:
        return True
    return all(matrix[i][j] == matrix[i + 1][j + 1]
               for i in range(len(matrix) - 1)
               for j in range(len(matrix[0]) - 1))


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def isToeplitzMatrix_20(matrix):
    """
    Final clean version.
    A matrix is Toeplitz iff matrix[i][j] == matrix[i+1][j+1]
    for all valid (i, j).

    Time:  O(m*n)
    Space: O(1)
    """
    if not matrix or not matrix[0]:
        return True
    return all(matrix[i][j] == matrix[i + 1][j + 1]
               for i in range(len(matrix) - 1)
               for j in range(len(matrix[0]) - 1))


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to verify if a matrix is Toeplitz - i.e., every diagonal
from top-left to bottom-right has the same elements."

Key Insight:
"Equivalent condition: matrix[i][j] == matrix[i+1][j+1]
for all valid (i, j). This is because each diagonal moves one step
right and one step down, so consecutive diagonal elements are at
(i, j) and (i+1, j+1)."

Algorithm:
"1. For each (i, j) in [0, m-1) x [0, n-1):
2. If matrix[i][j] != matrix[i+1][j+1]: return False.
3. Return True."

Why this works:
"Diagonal elements are at positions (i, j), (i+1, j+1), (i+2, j+2), etc.
For all to be equal, we just need adjacent pairs to be equal:
matrix[i][j] == matrix[i+1][j+1] for all (i, j)."

Edge cases:
- 1x1 matrix: vacuously True.
- 1xN or Nx1: trivially True (only one element per row/column pair).
- All same values: True.
- Differ at one diagonal: False.

Complexity:
- Time:  O(m*n) - check each cell once.
- Space: O(1) - no extra data structures.

KEY TRICK:
Just check matrix[i][j] == matrix[i+1][j+1]. No need to enumerate
diagonals or use sets.

MEMORY-CONSTRAINED VARIANT:
If only one row at a time is in memory, keep prev_row and check:
prev_row[j] == curr_row[j+1] for all j.

ALTERNATIVE: diagonal grouping
Group cells by (i - j). All cells in the same group are on the same
diagonal. Check that each group has only one distinct value.

RELATIONSHIP TO OTHER PROBLEMS:
- Valid Diagonal Sudoku (LC 2133): Different - check 3 diagonals.
- Set Matrix Zeroes: Different.
- Diagonal Traverse (LC 498): Different.

INTERVIEW TIPS:
1. Mention the equivalence: matrix[i][j] == matrix[i+1][j+1].
2. Mention the memory-constrained follow-up: keep prev_row.
3. Discuss numpy vectorization if matrix is huge.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Direct comparison (BEST)", isToeplitzMatrix_1),
        ("Way 2: All with any/all", isToeplitzMatrix_2),
        ("Way 3: zip adjacent rows", isToeplitzMatrix_3),
        ("Way 4: enumerate + zip", isToeplitzMatrix_4),
        ("Way 5: Iterate over diagonals", isToeplitzMatrix_5),
        ("Way 6: Use set for each diagonal", isToeplitzMatrix_6),
        ("Way 7: Numpy", isToeplitzMatrix_7),
        ("Way 8: Map zip diagonals", isToeplitzMatrix_8),
        ("Way 9: Group by (i-j)", isToeplitzMatrix_9),
        ("Way 10: reduce", isToeplitzMatrix_10),
        ("Way 11: Class-based", isToeplitzMatrix_11),
        ("Way 12: pairwise", isToeplitzMatrix_12),
        ("Way 13: Memory-constrained", isToeplitzMatrix_13),
        ("Way 14: all() compact", isToeplitzMatrix_14),
        ("Way 15: Generator check", isToeplitzMatrix_15),
        ("Way 16: itertools.product", isToeplitzMatrix_16),
        ("Way 17: Early return flag", isToeplitzMatrix_17),
        ("Way 18: map with lambda", isToeplitzMatrix_18),
        ("Way 19: One-liner", isToeplitzMatrix_19),
        ("Way 20: Final cleanest", isToeplitzMatrix_20),
    ]

    test_cases = [
        # Standard Toeplitz
        ([[1, 2, 3, 4],
          [5, 1, 2, 3],
          [9, 5, 1, 2]], True),
        # Not Toeplitz (different diagonals)
        ([[1, 2],
          [2, 2]], False),
        # 1x1 (trivially True)
        ([[99]], True),
        # 1xN
        ([[1, 2, 3, 4, 5]], True),
        # Nx1
        ([[1], [2], [3], [4]], True),
        # All same
        ([[5, 5, 5], [5, 5, 5], [5, 5, 5]], True),
        # All different
        ([[1, 2], [3, 4]], False),  # 1 != 4 (diagonal)
        # 3x3 valid
        ([[1, 2, 3],
          [4, 1, 2],
          [5, 4, 1]], True),
        # 3x3 invalid
        ([[1, 2, 3],
          [4, 1, 2],
          [5, 5, 1]], False),  # 4 != 5 at (1,0) vs (2,1)
        # Empty matrix
        ([], True),
    ]

    print("=" * 70)
    print("TOEPLITZ MATRIX - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/toeplitz-matrix")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for matrix, expected in test_cases:
            try:
                import copy
                matrix_copy = copy.deepcopy(matrix)
                result = func(matrix_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: matrix={matrix} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on matrix={matrix} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)