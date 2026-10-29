"""
Transpose Matrix
Easy | 15 min

Given a 2D integer array `matrix`, return the TRANSPOSE of `matrix`.

The transpose of a matrix is the matrix flipped over its main diagonal,
switching the matrix's row and column indices.

Examples:
    [[1, 2, 3],           [[1, 4, 7],
     [4, 5, 6],     ->     [2, 5, 8],
     [7, 8, 9]]            [3, 6, 9]]

    [[1, 2, 3],           [[1, 4],
     [4, 5, 6]]     ->     [2, 5],
                          [3, 6]]

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/transpose-matrix

Constraints:
- m == matrix.length
- n == matrix[i].length
- 1 <= m, n <= 1000
- 1 <= m * n <= 10^5
- -10^9 <= matrix[i][j] <= 10^9
"""


# =============================================================================
# WAY 1: In-place square matrix transpose (BEST - Most Common Interview Answer)
# =============================================================================
def transpose_matrix_1(matrix):
    """
    For a SQUARE matrix (m == n), swap matrix[i][j] with matrix[j][i].
    Only iterate over the UPPER triangle (j starts from i) to avoid
    swapping twice.
    For non-square, build a new matrix (in-place is impossible).

    Time:  O(m * n)  - visits every cell once
    Space: O(1) for square, O(m*n) for non-square
    """
    m, n = len(matrix), len(matrix[0])
    if m != n:
        # Non-square: in-place is impossible, build new matrix
        return [list(col) for col in zip(*matrix)]
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    return matrix


# =============================================================================
# WAY 2: Verbose version of Way 1 (for clarity in explaining)
# =============================================================================
def transpose_matrix_2(matrix):
    """Verbose style with explicit loop variables - great for whiteboard."""
    m, n = len(matrix), len(matrix[0])
    if m != n:
        return [list(col) for col in zip(*matrix)]
    for i in range(n):
        for j in range(i + 1, n):
            temp = matrix[i][j]
            matrix[i][j] = matrix[j][i]
            matrix[j][i] = temp
    return matrix


# =============================================================================
# WAY 3: Build new matrix (works for any m x n, NOT in-place)
# =============================================================================
def transpose_matrix_3(matrix):
    """
    Allocate a fresh n x m matrix. result[j][i] = matrix[i][j].
    Works for ANY rectangular matrix.

    Time:  O(m * n)
    Space: O(m * n)  - new matrix
    """
    m, n = len(matrix), len(matrix[0])
    result = [[0] * m for _ in range(n)]
    for i in range(m):
        for j in range(n):
            result[j][i] = matrix[i][j]
    return result


# =============================================================================
# WAY 4: Build with list comprehension (Pythonic, non-in-place)
# =============================================================================
def transpose_matrix_4(matrix):
    """One-liner using nested list comprehension over zip."""
    return [list(row) for row in zip(*matrix)]


# =============================================================================
# WAY 5: Using zip() with explicit type conversion
# =============================================================================
def transpose_matrix_5(matrix):
    """
    zip(*matrix) groups columns together. zip(*matrix)[j] is the j-th column
    of the original matrix, which becomes the j-th row of the transpose.
    """
    return [list(col) for col in zip(*matrix)]


# =============================================================================
# WAY 6: Using numpy (fastest for large inputs)
# =============================================================================
def transpose_matrix_6(matrix):
    """Numpy .T attribute returns the transpose view."""
    import numpy as np
    return np.array(matrix).T.tolist()


# =============================================================================
# WAY 7: Map-based functional style
# =============================================================================
def transpose_matrix_7(matrix):
    """
    Use map() to grab each column.
    map(lambda row: row[j], matrix) gives the j-th column.
    """
    if not matrix or not matrix[0]:
        return []
    cols = len(matrix[0])
    return [list(map(lambda row: row[j], matrix)) for j in range(cols)]


# =============================================================================
# WAY 8: Using itertools.zip_longest (handles jagged arrays)
# =============================================================================
def transpose_matrix_8(matrix):
    """
    zip_longest handles irregular rows gracefully (fills missing with None).
    Useful if rows might be of different lengths.
    """
    from itertools import zip_longest
    if not matrix or not matrix[0]:
        return []
    return [list(row) for row in zip_longest(*matrix, fillvalue=None)]


# =============================================================================
# WAY 9: Enumerate-based (explicit index tracking)
# =============================================================================
def transpose_matrix_9(matrix):
    """
    For each column index j, build a new row by enumerating all original rows.
    """
    if not matrix or not matrix[0]:
        return []
    n_cols = len(matrix[0])
    result = []
    for j in range(n_cols):
        new_row = []
        for row in matrix:
            new_row.append(row[j])
        result.append(new_row)
    return result


# =============================================================================
# WAY 10: Dictionary-based (columnar grouping)
# =============================================================================
def transpose_matrix_10(matrix):
    """
    Use a dict to group elements by column index.
    Then convert dict values to the result rows.
    """
    if not matrix or not matrix[0]:
        return []
    cols = {}
    for row in matrix:
        for j, val in enumerate(row):
            cols.setdefault(j, []).append(val)
    return list(cols.values())


# =============================================================================
# WAY 11: Recursive approach (educational - shows the math)
# =============================================================================
def transpose_matrix_11(matrix):
    """
    Recursively build the transpose by reducing column-by-column.
    """
    if not matrix or not matrix[0]:
        return []
    if len(matrix[0]) == 0:
        return []
    # Take first column as first row of transpose
    first_col = [row[0] for row in matrix]
    # Remaining matrix has each row shortened by 1 element
    rest = [row[1:] for row in matrix if len(row) > 1]
    return [first_col] + transpose_matrix_11(rest) if rest else [first_col]


# =============================================================================
# WAY 12: In-place with enumerate (square only, alternative style)
# =============================================================================
def transpose_matrix_12(matrix):
    """
    In-place transposition for square matrices using enumerate.
    Build each row of the transpose by enumerating columns.
    This MUTATES but creates new rows - not strictly O(1) space.
    """
    m, n = len(matrix), len(matrix[0])
    if m != n:
        return [list(col) for col in zip(*matrix)]
    # Read all rows, then rebuild the matrix
    rows = [list(row) for row in matrix]
    for i in range(n):
        for j in range(n):
            matrix[i][j] = rows[j][i]
    return matrix


# =============================================================================
# WAY 13: Chunked / block transpose (for cache efficiency on huge matrices)
# =============================================================================
def transpose_matrix_13(matrix):
    """
    Block transpose: process matrix in small blocks for better cache locality.
    Useful when matrix doesn't fit in cache.
    """
    if not matrix or not matrix[0]:
        return []
    m, n = len(matrix), len(matrix[0])
    result = [[None] * m for _ in range(n)]
    block = 32  # Typical cache line size
    for i0 in range(0, m, block):
        for j0 in range(0, n, block):
            for i in range(i0, min(i0 + block, m)):
                for j in range(j0, min(j0 + block, n)):
                    result[j][i] = matrix[i][j]
    return result


# =============================================================================
# WAY 14: Using array module (lower-level than list of lists)
# =============================================================================
def transpose_matrix_14(matrix):
    """
    Use the array module for a more memory-efficient representation.
    """
    from array import array
    if not matrix or not matrix[0]:
        return []
    m, n = len(matrix), len(matrix[0])
    result = [array('l', [0] * m) for _ in range(n)]
    for i in range(m):
        for j in range(n):
            result[j][i] = matrix[i][j]
    return [list(row) for row in result]


# =============================================================================
# WAY 15: Generator-based (memory-efficient streaming transpose)
# =============================================================================
def transpose_matrix_15(matrix):
    """
    Yield each row of the transpose - useful when caller wants lazy processing.
    """
    if not matrix or not matrix[0]:
        return
    n_cols = len(matrix[0])
    for j in range(n_cols):
        yield [matrix[i][j] for i in range(len(matrix))]


# =============================================================================
# WAY 16: Inline swap using XOR (no temp variable, square only)
# =============================================================================
def transpose_matrix_16(matrix):
    """
    XOR swap - 'clever' trick but NOT recommended in practice.
    Demonstrates an alternative to tuple unpacking.
    Works only for integer matrices.
    """
    m, n = len(matrix), len(matrix[0])
    if m != n:
        return [list(col) for col in zip(*matrix)]
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j] ^= matrix[j][i]
            matrix[j][i] ^= matrix[i][j]
            matrix[i][j] ^= matrix[j][i]
    return matrix


# =============================================================================
# WAY 17: Most concise (one-liner using zip)
# =============================================================================
def transpose_matrix_17(matrix):
    """Most concise: zip(*matrix) returns tuples, convert to lists."""
    return list(map(list, zip(*matrix)))


# =============================================================================
# WAY 18: Using pandas (dataframe-style transpose)
# =============================================================================
def transpose_matrix_18(matrix):
    """Use pandas DataFrame .T attribute for transpose, then convert."""
    import pandas as pd
    return pd.DataFrame(matrix).T.values.tolist()


# =============================================================================
# WAY 19: Parallelized using concurrent.futures (for very large matrices)
# =============================================================================
def transpose_matrix_19(matrix):
    """
    Process each column in parallel - overkill for normal sizes,
    but useful conceptually for very large matrices.
    """
    from concurrent.futures import ThreadPoolExecutor
    if not matrix or not matrix[0]:
        return []
    n_cols = len(matrix[0])
    n_rows = len(matrix)

    def get_col(j):
        return [matrix[i][j] for i in range(n_rows)]

    with ThreadPoolExecutor() as pool:
        cols = list(pool.map(get_col, range(n_cols)))
    return cols


# =============================================================================
# WAY 20: Final cleanest (combined best of all)
# =============================================================================
def transpose_matrix_20(matrix):
    """
    Final clean version: combines the elegance of zip with explicit list conversion.
    Works for any rectangular matrix.
    """
    if not matrix or not matrix[0]:
        return []
    return [list(col) for col in zip(*matrix)]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"The transpose of a matrix swaps rows and columns: result[j][i] = matrix[i][j].
For example, element at row 2, column 3 moves to row 3, column 2."

Key Insight:
"There are TWO main approaches depending on whether the matrix is square:

1. IN-PLACE (Square only, m == n):
   - Swap matrix[i][j] with matrix[j][i].
   - Only iterate over UPPER triangle (j starts from i+1) to avoid
     double-swapping.
   - Time O(m*n), Space O(1).

2. BUILD NEW (Any shape):
   - Allocate a new matrix of size n x m.
   - For each cell (i, j) in the original, place it at (j, i) in the new.
   - Time O(m*n), Space O(m*n).

3. PYTHONIC (Any shape):
   - Use zip(*matrix). This is Python's built-in transpose.
   - Convert tuples to lists if needed."

Edge cases:
- 1x1 matrix: return as-is
- Single row m=1: result has 1 column per element
- Single column n=1: result is just a flat list
- Rectangular: result dimensions are swapped (m x n) -> (n x m)

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| In-place  | O(mn)  | O(1)   |
| New matrix| O(mn)  | O(mn)  |
| zip(*)    | O(mn)  | O(mn)  |
+-----------+--------+--------+

KEY TRICK:
- In-place: j starts from i+1, NOT j from 0 (avoids re-swapping).
- For non-square: must build a new matrix (sizes differ).
- Python's zip(*matrix) IS a transpose operation.

TIPS:
- If the interviewer says 'in-place', check whether it's a square matrix.
- If they say 'don't allocate extra space', you must do in-place (square only).
- Otherwise, the pythonic zip(*matrix) is the most readable.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: In-place swap (BEST for square)", transpose_matrix_1),
        ("Way 2: Verbose in-place", transpose_matrix_2),
        ("Way 3: Build new matrix", transpose_matrix_3),
        ("Way 4: List comprehension", transpose_matrix_4),
        ("Way 5: zip with conversion", transpose_matrix_5),
        ("Way 6: Numpy .T", transpose_matrix_6),
        ("Way 7: Map-based", transpose_matrix_7),
        ("Way 8: zip_longest", transpose_matrix_8),
        ("Way 9: Enumerate-based", transpose_matrix_9),
        ("Way 10: Dict grouping", transpose_matrix_10),
        ("Way 11: Recursive", transpose_matrix_11),
        ("Way 12: In-place enumerate", transpose_matrix_12),
        ("Way 13: Block transpose", transpose_matrix_13),
        ("Way 14: array module", transpose_matrix_14),
        ("Way 15: Generator", transpose_matrix_15),
        ("Way 16: XOR swap", transpose_matrix_16),
        ("Way 17: Most concise", transpose_matrix_17),
        ("Way 18: Pandas", transpose_matrix_18),
        ("Way 19: Parallelized", transpose_matrix_19),
        ("Way 20: Final clean", transpose_matrix_20),
    ]

    # Test cases include both square and rectangular
    test_cases = [
        # 3x3 square
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]],
         [[1, 4, 7], [2, 5, 8], [3, 6, 9]]),
        # 2x3 rectangular
        ([[1, 2, 3], [4, 5, 6]],
         [[1, 4], [2, 5], [3, 6]]),
        # 3x2 rectangular
        ([[1, 2], [3, 4], [5, 6]],
         [[1, 3, 5], [2, 4, 6]]),
        # 1x1
        ([[1]], [[1]]),
        # 1x4 single row
        ([[1, 2, 3, 4]], [[1], [2], [3], [4]]),
        # 4x1 single column
        ([[1], [2], [3], [4]], [[1, 2, 3, 4]]),
        # 2x2
        ([[1, 2], [3, 4]], [[1, 3], [2, 4]]),
        # 2x4 wider
        ([[1, 2, 3, 4], [5, 6, 7, 8]],
         [[1, 5], [2, 6], [3, 7], [4, 8]]),
        # 4x2 taller
        ([[1, 2], [3, 4], [5, 6], [7, 8]],
         [[1, 3, 5, 7], [2, 4, 6, 8]]),
        # Identity-like
        ([[5]], [[5]]),
    ]

    print("=" * 70)
    print("TRANSPOSE MATRIX - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/transpose-matrix")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for mat, expected in test_cases:
            try:
                import copy
                mat_copy = copy.deepcopy(mat)
                result = func(mat_copy)
                # Convert generator to list if needed
                if hasattr(result, '__next__'):
                    result = list(result)
                elif isinstance(result, type(iter([]))):
                    result = list(result)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: mat={mat} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on mat={mat} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)