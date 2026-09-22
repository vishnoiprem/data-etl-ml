"""
Set Matrix Zeros
Medium | 30 min

Given an m x n matrix mat. If any element is zero, set its ENTIRE row
and column to zero. Do it IN PLACE - modify the matrix directly.

Examples:
    mat = [
      [1, 2, 3],
      [4, 0, 6],
      [7, 8, 9]
    ]
    -> [
      [1, 0, 3],
      [0, 0, 0],
      [7, 0, 9]
    ]

    mat = [
      [0, 1, 2, 0],
      [3, 4, 5, 2],
      [1, 3, 1, 5]
    ]
    -> [
      [0, 0, 0, 0],
      [0, 4, 5, 0],
      [0, 3, 1, 0]
    ]

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/set-matrix-zeroes

Constraints:
- m, n in [1, 20]
- -2^31 <= mat[i][j] <= 2^31 - 1
"""


# =============================================================================
# WAY 1: Use first row/column as markers (BEST - Memorize!)
# =============================================================================
def set_matrix_zeros_1(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    # Track if first row and first column have zeros
    first_row_zero = any(mat[0][j] == 0 for j in range(n))
    first_col_zero = any(mat[i][0] == 0 for i in range(m))

    # Use first row/column as markers for inner cells
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][j] == 0:
                mat[i][0] = 0
                mat[0][j] = 0

    # Zero out cells based on markers
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][0] == 0 or mat[0][j] == 0:
                mat[i][j] = 0

    # Handle first row and column
    if first_row_zero:
        for j in range(n):
            mat[0][j] = 0
    if first_col_zero:
        for i in range(m):
            mat[i][0] = 0
    return mat


# =============================================================================
# WAY 2: With explicit set for rows and cols (extra space)
# =============================================================================
def set_matrix_zeros_2(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    zero_rows = set()
    zero_cols = set()
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                zero_rows.add(i)
                zero_cols.add(j)
    for i in range(m):
        for j in range(n):
            if i in zero_rows or j in zero_cols:
                mat[i][j] = 0
    return mat


# =============================================================================
# WAY 3: Use two lists (extra space)
# =============================================================================
def set_matrix_zeros_3(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    rows = [False] * m
    cols = [False] * n
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                rows[i] = True
                cols[j] = True
    for i in range(m):
        for j in range(n):
            if rows[i] or cols[j]:
                mat[i][j] = 0
    return mat


# =============================================================================
# WAY 4: Brute force - mark with sentinel value, then clean up
# =============================================================================
def set_matrix_zeros_4(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    SENTINEL = None  # Use None as marker

    # First pass: mark with None
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                # Mark entire row
                for k in range(n):
                    if mat[i][k] != 0:
                        mat[i][k] = SENTINEL
                # Mark entire column
                for k in range(m):
                    if mat[k][j] != 0:
                        mat[k][j] = SENTINEL

    # Second pass: replace sentinel with 0
    for i in range(m):
        for j in range(n):
            if mat[i][j] == SENTINEL:
                mat[i][j] = 0
    return mat


# =============================================================================
# WAY 5: Two-pass with marker value (e.g., float('inf'))
# =============================================================================
def set_matrix_zeros_5(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    MARKER = float('inf')

    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                for k in range(n):
                    if mat[i][k] != 0:
                        mat[i][k] = MARKER
                for k in range(m):
                    if mat[k][j] != 0:
                        mat[k][j] = MARKER

    for i in range(m):
        for j in range(n):
            if mat[i][j] == MARKER:
                mat[i][j] = 0
    return mat


# =============================================================================
# WAY 6: With tuples instead of sets
# =============================================================================
def set_matrix_zeros_6(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    zero_positions = []
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                zero_positions.append((i, j))
    for i, j in zero_positions:
        for k in range(n):
            mat[i][k] = 0
        for k in range(m):
            mat[k][j] = 0
    return mat


# =============================================================================
# WAY 7: Using dict for row/col flags
# =============================================================================
def set_matrix_zeros_7(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    row_zero = {}
    col_zero = {}
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                row_zero[i] = True
                col_zero[j] = True
    for i in range(m):
        for j in range(n):
            if row_zero.get(i) or col_zero.get(j):
                mat[i][j] = 0
    return mat


# =============================================================================
# WAY 8: First pass mark in-place, second pass zero (O(1) space variant)
# =============================================================================
def set_matrix_zeros_8(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])

    # Use first row and column as markers
    # Check first row and column separately
    fr_zero = any(mat[0][j] == 0 for j in range(n))
    fc_zero = any(mat[i][0] == 0 for i in range(m))

    # Mark rows and columns that should be zeroed (excluding first row/col)
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][j] == 0:
                mat[0][j] = 0
                mat[i][0] = 0

    # Apply markers to inner matrix
    for i in range(1, m):
        for j in range(1, n):
            if mat[0][j] == 0 or mat[i][0] == 0:
                mat[i][j] = 0

    # Handle first row and column
    for j in range(n):
        if fr_zero:
            mat[0][j] = 0
    for i in range(m):
        if fc_zero:
            mat[i][0] = 0

    return mat


# =============================================================================
# WAY 9: BitSet style (using bitarray concept)
# =============================================================================
def set_matrix_zeros_9(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    row_bits = 0
    col_bits = 0
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                row_bits |= (1 << i)
                col_bits |= (1 << j)
    for i in range(m):
        for j in range(n):
            if (row_bits >> i) & 1 or (col_bits >> j) & 1:
                mat[i][j] = 0
    return mat


# =============================================================================
# WAY 10: With list of bools (most readable)
# =============================================================================
def set_matrix_zeros_10(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    is_zero_row = [False] * m
    is_zero_col = [False] * n
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                is_zero_row[i] = True
                is_zero_col[j] = True
    for i in range(m):
        for j in range(n):
            if is_zero_row[i] or is_zero_col[j]:
                mat[i][j] = 0
    return mat


# =============================================================================
# WAY 11: With helper to clear row/col
# =============================================================================
def set_matrix_zeros_11(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])

    def clear_row(i):
        for j in range(n):
            mat[i][j] = 0

    def clear_col(j):
        for i in range(m):
            mat[i][j] = 0

    rows, cols = set(), set()
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                rows.add(i)
                cols.add(j)
    for i in rows:
        clear_row(i)
    for j in cols:
        clear_col(j)
    return mat


# =============================================================================
# WAY 12: One-pass with marker (use 0 itself carefully)
# =============================================================================
def set_matrix_zeros_12(mat):
    """Use first row/col as markers but cleaner."""
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])

    # Check first col BEFORE marking (since marking sets first col to zero)
    first_col_zero = any(mat[i][0] == 0 for i in range(m))
    first_row_zero = any(mat[0][j] == 0 for j in range(n))

    # First pass: identify zeros (except in first row/col)
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][j] == 0:
                mat[i][0] = 0
                mat[0][j] = 0

    # Second pass: zero out based on markers
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][0] == 0 or mat[0][j] == 0:
                mat[i][j] = 0

    # Third pass: handle first row and column
    if first_col_zero:
        for i in range(m):
            mat[i][0] = 0
    if first_row_zero:
        for j in range(n):
            mat[0][j] = 0

    return mat


# =============================================================================
# WAY 13: Use a single bool flag for first row/col
# =============================================================================
def set_matrix_zeros_13(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    first_row_zero = False
    first_col_zero = False

    # Detect zeros in first row and column
    for j in range(n):
        if mat[0][j] == 0:
            first_row_zero = True
            break
    for i in range(m):
        if mat[i][0] == 0:
            first_col_zero = True
            break

    # Mark rows and cols (excluding first)
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][j] == 0:
                mat[i][0] = 0
                mat[0][j] = 0

    # Zero out cells
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][0] == 0 or mat[0][j] == 0:
                mat[i][j] = 0

    # Handle first row/col
    if first_row_zero:
        for j in range(n):
            mat[0][j] = 0
    if first_col_zero:
        for i in range(m):
            mat[i][0] = 0
    return mat


# =============================================================================
# WAY 14: Use array of row indices and col indices
# =============================================================================
def set_matrix_zeros_14(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    zero_rows = []
    zero_cols = []
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                if i not in zero_rows:
                    zero_rows.append(i)
                if j not in zero_cols:
                    zero_cols.append(j)
    for i in zero_rows:
        for j in range(n):
            mat[i][j] = 0
    for j in zero_cols:
        for i in range(m):
            mat[i][j] = 0
    return mat


# =============================================================================
# WAY 15: Most concise
# =============================================================================
def set_matrix_zeros_15(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    r, c = set(), set()
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                r.add(i)
                c.add(j)
    for i in range(m):
        for j in range(n):
            if i in r or j in c:
                mat[i][j] = 0
    return mat


# =============================================================================
# WAY 16: Use a single combined hash
# =============================================================================
def set_matrix_zeros_16(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    cells = {}  # (i,j) -> True
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                cells[(i, j)] = True
    # Apply
    for i in range(m):
        for j in range(n):
            # Row i has zero?
            row_has_zero = any((i, k) in cells for k in range(n))
            col_has_zero = any((k, j) in cells for k in range(m))
            if row_has_zero or col_has_zero:
                mat[i][j] = 0
    return mat


# =============================================================================
# WAY 17: With numpy (for completeness)
# =============================================================================
def set_matrix_zeros_17(mat):
    if not mat or not mat[0]:
        return mat
    import numpy as np
    arr = np.array(mat)
    zero_rows = np.any(arr == 0, axis=1)
    zero_cols = np.any(arr == 0, axis=0)
    arr[zero_rows, :] = 0
    arr[:, zero_cols] = 0
    for i in range(len(mat)):
        for j in range(len(mat[0])):
            mat[i][j] = int(arr[i][j])
    return mat


# =============================================================================
# WAY 18: Recursive (not practical, for completeness)
# =============================================================================
def set_matrix_zeros_18(mat):
    """Recursive approach - find all zeros, then process."""
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])

    def find_zeros():
        zeros = []
        for i in range(m):
            for j in range(n):
                if mat[i][j] == 0:
                    zeros.append((i, j))
        return zeros

    def apply_zeros(zeros):
        for i, j in zeros:
            for k in range(n):
                mat[i][k] = 0
            for k in range(m):
                mat[k][j] = 0

    apply_zeros(find_zeros())
    return mat


# =============================================================================
# WAY 19: Class-based
# =============================================================================
class MatrixZeroer:
    def __init__(self, mat):
        self.mat = mat

    def zero(self):
        m, n = len(self.mat), len(self.mat[0])
        rows, cols = set(), set()
        for i in range(m):
            for j in range(n):
                if self.mat[i][j] == 0:
                    rows.add(i)
                    cols.add(j)
        for i in range(m):
            for j in range(n):
                if i in rows or j in cols:
                    self.mat[i][j] = 0
        return self.mat


def set_matrix_zeros_19(mat):
    return MatrixZeroer(mat).zero()


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def set_matrix_zeros_20(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    fr = any(mat[0][j] == 0 for j in range(n))
    fc = any(mat[i][0] == 0 for i in range(m))
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][j] == 0:
                mat[i][0] = mat[0][j] = 0
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][0] == 0 or mat[0][j] == 0:
                mat[i][j] = 0
    if fr:
        for j in range(n):
            mat[0][j] = 0
    if fc:
        for i in range(m):
            mat[i][0] = 0
    return mat


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I have an m x n matrix. For any cell that's zero, I need to set its
entire row and column to zero. Must be done IN PLACE."

Key Insight:
"Use the FIRST ROW and FIRST COLUMN as MARKERS!
- For each zero at mat[i][j] (excluding first row/col):
  * Mark mat[i][0] = 0 and mat[0][j] = 0
- Later: if mat[i][0] == 0 OR mat[0][j] == 0, set mat[i][j] = 0
- Handle first row/col separately (they need their own flag)"

Algorithm:
"1. Detect if first row/col have any zeros (save flags)
2. For i in 1..m-1, j in 1..n-1:
   if mat[i][j] == 0:
     mat[i][0] = 0
     mat[0][j] = 0
3. For i in 1..m-1, j in 1..n-1:
   if mat[i][0] == 0 or mat[0][j] == 0:
     mat[i][j] = 0
4. If first row had zero, zero out first row
5. If first col had zero, zero out first col"

Why this works (in-place):
"The first row stores 'which column has zero', first column stores
'which row has zero'. We can't process first row/col directly because
they ARE the markers. So we save their state FIRST and process them
LAST."

Edge cases:
- Single cell: trivial
- Single row/col: handled
- All zeros: everything zeros
- No zeros: nothing changes

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| In-place  | O(mn)  | O(1)   |
| Sets      | O(mn)  | O(m+n) |
| Brute     | O(mn)  | O(1)   |
+-----------+--------+--------+

KEY TRICK:
Reuse the matrix itself for markers (first row/column).
But handle them SEPARATELY (save flags, process last).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: First row/col markers (BEST)", set_matrix_zeros_1),
        ("Way 2: Sets", set_matrix_zeros_2),
        ("Way 3: Boolean lists", set_matrix_zeros_3),
        ("Way 4: Sentinel brute", set_matrix_zeros_4),
        ("Way 5: Marker brute", set_matrix_zeros_5),
        ("Way 6: Tuples of positions", set_matrix_zeros_6),
        ("Way 7: Dict flags", set_matrix_zeros_7),
        ("Way 8: O(1) variant", set_matrix_zeros_8),
        ("Way 9: BitSet", set_matrix_zeros_9),
        ("Way 10: Bool lists readable", set_matrix_zeros_10),
        ("Way 11: With helpers", set_matrix_zeros_11),
        ("Way 12: 3-pass markers", set_matrix_zeros_12),
        ("Way 13: Single bool flag", set_matrix_zeros_13),
        ("Way 14: Indices lists", set_matrix_zeros_14),
        ("Way 15: Most concise", set_matrix_zeros_15),
        ("Way 16: Cells dict", set_matrix_zeros_16),
        ("Way 17: Numpy", set_matrix_zeros_17),
        ("Way 18: Recursive", set_matrix_zeros_18),
        ("Way 19: Class-based", set_matrix_zeros_19),
        ("Way 20: Final cleanest", set_matrix_zeros_20),
    ]

    def make_mat(rows):
        return [row[:] for row in rows]

    test_cases = [
        # (input, expected)
        (
            [[1, 2, 3], [4, 0, 6], [7, 8, 9]],
            [[1, 0, 3], [0, 0, 0], [7, 0, 9]]
        ),
        (
            [[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]],
            [[0, 0, 0, 0], [0, 4, 5, 0], [0, 3, 1, 0]]
        ),
        # No zeros - unchanged
        (
            [[1, 2], [3, 4]],
            [[1, 2], [3, 4]]
        ),
        # Single element zero
        (
            [[0]],
            [[0]]
        ),
        # Single element non-zero
        (
            [[1]],
            [[1]]
        ),
        # All zeros
        (
            [[0, 0], [0, 0]],
            [[0, 0], [0, 0]]
        ),
        # Zero in first row
        (
            [[1, 0, 3], [4, 5, 6], [7, 8, 9]],
            [[0, 0, 0], [4, 0, 6], [7, 0, 9]]
        ),
        # Zero in first col
        (
            [[1, 2, 3], [0, 5, 6], [7, 8, 9]],
            [[0, 2, 3], [0, 0, 0], [0, 8, 9]]
        ),
        # Multiple zeros
        (
            [[1, 2, 3, 4], [5, 0, 7, 8], [9, 10, 11, 12], [13, 14, 15, 0]],
            [[1, 0, 3, 0], [0, 0, 0, 0], [9, 0, 11, 0], [0, 0, 0, 0]]
        ),
    ]

    print("=" * 70)
    print("SET MATRIX ZEROS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/set-matrix-zeroes")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for mat_input, expected in test_cases:
            try:
                mat_copy = make_mat(mat_input)
                result = func(mat_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: input={mat_input} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on input={mat_input} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
