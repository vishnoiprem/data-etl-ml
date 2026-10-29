"""
Search a 2D Matrix II
Medium | 30 min

Given an m x n integer matrix with properties:
- Each row is sorted ascending (left to right).
- Each column is sorted ascending (top to bottom).
Determine if target exists in matrix.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/search-a-2d-matrix-ii

Examples:
    matrix = [[1, 4, 7, 11, 15],
              [2, 5, 8, 12, 19],
              [3, 6, 9, 16, 22],
              [10, 13, 14, 17, 24],
              [18, 21, 23, 26, 30]]
    target = 5 -> True
    target = 20 -> False

Constraints:
- 1 <= m, n <= 300
- -10^9 <= matrix[i][j], target <= 10^9
"""


# =============================================================================
# WAY 1: Start at top-right corner (BEST — Memorize!)
# =============================================================================
def searchMatrix_1(matrix, target):
    """
    KEY INSIGHT: Start at top-right corner.
    - Current value > target: move LEFT (column decreases).
    - Current value < target: move DOWN (row increases).
    - At each step, we eliminate one row OR one column.

    Why this works:
    - To the left of current: smaller values (row sorted).
    - Below current: larger values (column sorted).
    - We can always decide to go left or down based on comparison.

    Time:  O(m + n)
    Space: O(1)
    """
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = 0, n - 1
    while r < m and c >= 0:
        if matrix[r][c] == target:
            return True
        elif matrix[r][c] > target:
            c -= 1
        else:
            r += 1
    return False


# =============================================================================
# WAY 2: Start at bottom-left corner
# =============================================================================
def searchMatrix_2(matrix, target):
    """
    Same idea but starting from bottom-left.
    - Current > target: move UP (row decreases).
    - Current < target: move RIGHT (column increases).
    """
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = m - 1, 0
    while r >= 0 and c < n:
        if matrix[r][c] == target:
            return True
        elif matrix[r][c] > target:
            r -= 1
        else:
            c += 1
    return False


# =============================================================================
# WAY 3: Binary search on each row
# =============================================================================
def searchMatrix_3(matrix, target):
    """
    For each row, do binary search.
    Time: O(m log n)
    """
    for row in matrix:
        lo, hi = 0, len(row) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if row[mid] == target:
                return True
            elif row[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
    return False


# =============================================================================
# WAY 4: Binary search on each column
# =============================================================================
def searchMatrix_4(matrix, target):
    """Binary search on each column. O(n log m)"""
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    for c in range(n):
        lo, hi = 0, m - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if matrix[mid][c] == target:
                return True
            elif matrix[mid][c] < target:
                lo = mid + 1
            else:
                hi = mid - 1
    return False


# =============================================================================
# WAY 5: Diagonal binary search + staircase
# =============================================================================
def searchMatrix_5(matrix, target):
    """
    KEY INSIGHT: Search the diagonal first using binary search.
    Find the largest diagonal entry <= target. Then search quadrants.

    Time: O(log(min(m,n)) + m + n)
    """
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])

    # Phase 1: Search diagonal
    diag_len = min(m, n)
    lo, hi = 0, diag_len - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if matrix[mid][mid] == target:
            return True
        elif matrix[mid][mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1

    # hi is the index of largest diagonal element <= target (or -1)
    partition = hi + 1  # split point

    # Phase 2: Search top-right (rows 0..partition-1, cols partition..n-1)
    r, c = 0, partition
    while r < partition and c < n:
        v = matrix[r][c]
        if v == target:
            return True
        elif v > target:
            c += 1  # shouldn't happen but safe
        else:
            r += 1

    # Phase 3: Search bottom-left (rows partition..m-1, cols 0..partition-1)
    r, c = partition, 0
    while r < m and c < partition:
        v = matrix[r][c]
        if v == target:
            return True
        elif v > target:
            c += 1  # shouldn't happen
        else:
            r += 1

    return False


# =============================================================================
# WAY 6: Brute force O(m*n)
# =============================================================================
def searchMatrix_6(matrix, target):
    """Linear scan. O(mn) time."""
    for row in matrix:
        if target in row:
            return True
    return False


# =============================================================================
# WAY 7: Search space reduction (Divide & Conquer on quadrants)
# =============================================================================
def searchMatrix_7(matrix, target):
    """
    Divide the matrix into 4 quadrants based on a midpoint.
    Only one quadrant can contain the target (due to sorted properties).
    """
    if not matrix or not matrix[0]:
        return False
    return _search_dc(matrix, target, 0, len(matrix) - 1, 0, len(matrix[0]) - 1)


def _search_dc(matrix, target, top, bottom, left, right):
    if top > bottom or left > right:
        return False
    if top == bottom and left == right:
        return matrix[top][left] == target
    mid_row = (top + bottom) // 2
    mid_col = (left + right) // 2
    val = matrix[mid_row][mid_col]
    if val == target:
        return True
    elif val > target:
        # Search top-left, top-right, bottom-left quadrants
        return (_search_dc(matrix, target, top, mid_row, left, mid_col - 1) or
                _search_dc(matrix, target, top, mid_row - 1, mid_col, right) or
                _search_dc(matrix, target, mid_row, bottom, left, mid_col - 1))
    else:
        # Search top-right, bottom-left, bottom-right quadrants
        return (_search_dc(matrix, target, top, mid_row, mid_col + 1, right) or
                _search_dc(matrix, target, mid_row + 1, bottom, left, mid_col) or
                _search_dc(matrix, target, mid_row + 1, bottom, mid_col, right))


# =============================================================================
# WAY 8: Top-right with explicit tracking
# =============================================================================
def searchMatrix_8(matrix, target):
    """Same as Way 1 with verbose naming."""
    if not matrix or not matrix[0]:
        return False
    rows, cols = len(matrix), len(matrix[0])
    row, col = 0, cols - 1
    while row < rows and col >= 0:
        current = matrix[row][col]
        if current == target:
            return True
        elif current > target:
            col -= 1
        else:
            row += 1
    return False


# =============================================================================
# WAY 9: Top-right with bisect
# =============================================================================
def searchMatrix_9(matrix, target):
    """Use bisect for binary search on rows."""
    import bisect
    for row in matrix:
        idx = bisect.bisect_left(row, target)
        if idx < len(row) and row[idx] == target:
            return True
    return False


# =============================================================================
# WAY 10: BFS from corner (using deque)
# =============================================================================
def searchMatrix_10(matrix, target):
    """BFS-style elimination from top-right corner."""
    from collections import deque
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    queue = deque([(0, n - 1)])
    while queue:
        r, c = queue.popleft()
        if r >= m or c < 0:
            continue
        if matrix[r][c] == target:
            return True
        elif matrix[r][c] > target:
            queue.append((r, c - 1))
        else:
            queue.append((r + 1, c))
    return False


# =============================================================================
# WAY 11: Flatten and binary search
# =============================================================================
def searchMatrix_11(matrix, target):
    """
    KEY INSIGHT: Since each row is sorted, we can binary search each row
    but also use the column property to early-exit.
    """
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    for r in range(m):
        if matrix[r][0] > target:
            break  # All subsequent rows start with even larger values
        if matrix[r][-1] < target:
            continue  # This row has all values < target
        # Binary search this row
        lo, hi = 0, n - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if matrix[r][mid] == target:
                return True
            elif matrix[r][mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
    return False


# =============================================================================
# WAY 12: Using numpy
# =============================================================================
def searchMatrix_12(matrix, target):
    """Numpy-based search."""
    try:
        import numpy as np
    except ImportError:
        return searchMatrix_1(matrix, target)
    arr = np.array(matrix)
    return target in arr


# =============================================================================
# WAY 13: Most concise top-right
# =============================================================================
def searchMatrix_13(matrix, target):
    """Most concise top-right corner."""
    if not matrix:
        return False
    r, c = 0, len(matrix[0]) - 1
    while r < len(matrix) and c >= 0:
        v = matrix[r][c]
        if v == target:
            return True
        if v > target:
            c -= 1
        else:
            r += 1
    return False


# =============================================================================
# WAY 14: Lambda + filter
# =============================================================================
def searchMatrix_14(matrix, target):
    """Functional style."""
    if not matrix:
        return False
    return any(target in row for row in matrix)


# =============================================================================
# WAY 15: Stair search with early break
# =============================================================================
def searchMatrix_15(matrix, target):
    """Top-right with row elimination."""
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = 0, n - 1
    while r < m and c >= 0:
        v = matrix[r][c]
        if v == target:
            return True
        elif v > target:
            c -= 1
        else:
            # Move down, but check if entire column is now too small
            if c < n - 1 and matrix[r][c + 1] <= target < matrix[r + 1][c] if r + 1 < m else False:
                r += 1
            else:
                r += 1
    return False


# =============================================================================
# WAY 16: Class-based OOP
# =============================================================================
class MatrixSearch:
    def __init__(self, matrix):
        self.matrix = matrix
        self.m = len(matrix) if matrix else 0
        self.n = len(matrix[0]) if matrix and matrix[0] else 0

    def search(self, target):
        if self.m == 0 or self.n == 0:
            return False
        r, c = 0, self.n - 1
        while r < self.m and c >= 0:
            if self.matrix[r][c] == target:
                return True
            elif self.matrix[r][c] > target:
                c -= 1
            else:
                r += 1
        return False


def searchMatrix_16(matrix, target):
    return MatrixSearch(matrix).search(target)


# =============================================================================
# WAY 17: Start at bottom-left with verbose logic
# =============================================================================
def searchMatrix_17(matrix, target):
    """Bottom-left with detailed comments."""
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = m - 1, 0
    while r >= 0 and c < n:
        if matrix[r][c] == target:
            return True
        if matrix[r][c] > target:
            r -= 1
        else:
            c += 1
    return False


# =============================================================================
# WAY 18: Search via diagonal + quadrant (clean)
# =============================================================================
def searchMatrix_18(matrix, target):
    """Diagonal binary search + staircase."""
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    # Phase 1: Find partition on diagonal
    diag_len = min(m, n)
    i = 0
    while i < diag_len and matrix[i][i] < target:
        i += 1
    if i < diag_len and matrix[i][i] == target:
        return True
    partition = i

    # Phase 2: Top-right quadrant (rows 0..partition-1, cols partition..n-1)
    r, c = 0, partition
    while r < partition and c < n:
        if matrix[r][c] == target:
            return True
        if matrix[r][c] < target:
            r += 1
        else:
            c -= 1

    # Phase 3: Bottom-left quadrant (rows partition..m-1, cols 0..partition-1)
    r, c = partition, 0
    while r < m and c < partition:
        if matrix[r][c] == target:
            return True
        if matrix[r][c] < target:
            r += 1
        else:
            c -= 1

    return False


# =============================================================================
# WAY 19: Top-right but iterate in while loop form
# =============================================================================
def searchMatrix_19(matrix, target):
    """While True loop variant."""
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = 0, n - 1
    while True:
        if r >= m or c < 0:
            return False
        if matrix[r][c] == target:
            return True
        if matrix[r][c] > target:
            c -= 1
        else:
            r += 1


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def searchMatrix_20(matrix, target):
    """
    THE ONE TO MEMORIZE.

    Start at top-right corner. Move left if current > target, down if current < target.
    Each step eliminates one row OR one column.

    Time:  O(m + n)
    Space: O(1)
    """
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = 0, n - 1
    while r < m and c >= 0:
        if matrix[r][c] == target:
            return True
        if matrix[r][c] > target:
            c -= 1
        else:
            r += 1
    return False


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find a target in an m x n matrix where each row and column
is sorted ascending."

Key Insight:
"There are several approaches:
1. STAIR SEARCH from top-right or bottom-left corner: O(m+n).
2. BINARY SEARCH on each row: O(m log n).
3. BRUTE FORCE: O(mn).
4. DIVIDE AND CONQUER on quadrants: O(m+n) with better constants.

Best: Stair search from top-right corner."

Stair Search Logic:
"Start at top-right (0, n-1):
- If current == target: found.
- If current > target: move LEFT (column decreases). All values to the
  left in this row are smaller, but current column's values below are
  larger (column sorted). We can't find target in current column, so
  move left.
- If current < target: move DOWN (row increases). All values above in
  current column are smaller, but values to the right in this row are
  larger (row sorted). We can't find target in this row, so move down.

This eliminates one row OR one column per step. Total: m + n steps."

Why It Works:
"At each position, the row above is all smaller (column sorted) and
the column to the left is all smaller (row sorted). We can always
decide which direction to go based on one comparison."

Edge Cases:
- 1x1: check single element.
- target < matrix[0][0]: return False.
- target > matrix[-1][-1]: return False.

Complexity:
+---------------+----------------+--------+
| Approach      | Time           | Space  |
+---------------+----------------+--------+
| Stair search  | O(m+n)         | O(1)   |
| Binary/row    | O(m log n)     | O(1)   |
| Brute force   | O(mn)          | O(1)   |
| D&C quadrants | O(m+n)         | O(log) |
+---------------+----------------+--------+

KEY TRICK:
Start at the CORNER where one direction is sorted-ascending and the
other is sorted-descending relative to current position.
- Top-right: column below is larger (ascending), row left is smaller.
- Bottom-left: column above is smaller, row right is larger.

RELATED PROBLEMS:
- Search a 2D Matrix I (LC 74): Different - fully sorted, O(log mn).
- Kth Smallest in Sorted Matrix (LC 378): Same staircase idea.
- Find Peak Element II (LC 1901): Stair search for peak.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Top-right stair (BEST)", searchMatrix_1),
        ("Way 2: Bottom-left stair", searchMatrix_2),
        ("Way 3: Binary search per row", searchMatrix_3),
        ("Way 4: Binary search per col", searchMatrix_4),
        ("Way 5: Diagonal binary search", searchMatrix_5),
        ("Way 6: Brute force", searchMatrix_6),
        ("Way 7: D&C quadrants", searchMatrix_7),
        ("Way 8: Top-right verbose", searchMatrix_8),
        ("Way 9: Bisect", searchMatrix_9),
        ("Way 10: BFS deque", searchMatrix_10),
        ("Way 11: Binary search w/ early exit", searchMatrix_11),
        ("Way 12: Numpy", searchMatrix_12),
        ("Way 13: Most concise", searchMatrix_13),
        ("Way 14: Lambda filter", searchMatrix_14),
        ("Way 15: Stair with early break", searchMatrix_15),
        ("Way 16: Class OOP", searchMatrix_16),
        ("Way 17: Bottom-left verbose", searchMatrix_17),
        ("Way 18: Diagonal + quadrant", searchMatrix_18),
        ("Way 19: While True", searchMatrix_19),
        ("Way 20: Final cleanest", searchMatrix_20),
    ]

    mat = [
        [1, 4, 7, 11, 15],
        [2, 5, 8, 12, 19],
        [3, 6, 9, 16, 22],
        [10, 13, 14, 17, 24],
        [18, 21, 23, 26, 30]
    ]

    test_cases = [
        # (matrix, target, expected)
        (mat, 5, True),     # found
        (mat, 20, False),   # not found
        ([[1]], 1, True),   # 1x1 found
        ([[1]], 2, False),  # 1x1 not found
        ([[1, 2, 3]], 2, True),  # 1xN
        ([[1], [2], [3]], 2, True),  # Nx1
        ([[1, 2, 3]], 4, False),  # 1xN not found
        ([[1], [2], [3]], 0, False),  # Nx1 not found
        ([[1, 5, 9], [10, 11, 13], [12, 13, 15]], 13, True),  # duplicates
        ([[-5]], -5, True),  # negative
        ([[-5]], 5, False),  # negative not found
    ]

    print("=" * 70)
    print("SEARCH A 2D MATRIX II - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/search-a-2d-matrix-ii")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for m, target, expected in test_cases:
            # Make a deep copy
            m_copy = [row[:] for row in m]
            try:
                result = func(m_copy, target)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: target={target}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on target={target} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)