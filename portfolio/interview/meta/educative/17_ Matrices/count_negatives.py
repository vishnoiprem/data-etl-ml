"""
Count Negative Numbers in a Sorted Matrix
Easy | 15 min

Given an m x n matrix grid sorted in NON-INCREASING order by both rows
and columns, return the number of NEGATIVE numbers in grid.

"Sorted in non-increasing order by rows and columns":
- Each row is sorted in non-increasing order (left to right)
- Each column is sorted in non-increasing order (top to bottom)

Examples:
    [[4, 3, 2, -1],
     [3, 2, 1, -1],
     [1, 1, -1, -2],
     [-1, -1, -2, -3]]
    -> 8

    [[3, 2], [1, 0]]  -> 0

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-negative-numbers-in-a-sorted-matrix

Constraints:
- m == grid.length
- n == grid[i].length
- 1 <= m, n <= 100
- -100 <= grid[i][j] <= 100

Follow-up: Your solution must be O(m + n) time.
"""


# =============================================================================
# WAY 1: Start from top-right corner, walk left or down (BEST - O(m+n))
# =============================================================================
def count_negatives_1(grid):
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = 0, n - 1  # top-right corner
    while r < m and c >= 0:
        if grid[r][c] < 0:
            # All cells below in column c are also negative
            count += m - r
            c -= 1  # move left
        else:
            # Not negative, move down to find negative
            r += 1
    return count


# =============================================================================
# WAY 2: Start from bottom-left, walk right or up
# =============================================================================
def count_negatives_2(grid):
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = m - 1, 0  # bottom-left corner
    while r >= 0 and c < n:
        if grid[r][c] < 0:
            # All cells to the right in row r are also negative
            count += n - c
            r -= 1  # move up
        else:
            c += 1  # move right
    return count


# =============================================================================
# WAY 3: Binary search on each row
# =============================================================================
def count_negatives_3(grid):
    import bisect
    count = 0
    for row in grid:
        # bisect_left finds first position >= 0, i.e., last negative is bisect_left(row, 0) - 1
        # We want to count negatives, so it's bisect_left(row, 0)
        # But since row is non-increasing, we need to use bisect_left on negative
        # Actually since row is sorted non-increasing, bisect doesn't directly apply
        # We need to search for first position where grid[i][j] < 0
        # In a non-increasing row: [4, 3, 2, -1, -1, -2]
        # Negatives are from first negative onwards
        # Use bisect.bisect_left on negated array
        neg_row = [-x for x in row]
        # Now neg_row is non-decreasing. We want first position where neg_row[i] > 0
        # = first position where row[i] < 0
        idx = bisect.bisect_right(neg_row, 0)
        count += len(row) - idx
    return count


# =============================================================================
# WAY 4: Binary search on each row manually
# =============================================================================
def count_negatives_4(grid):
    def first_negative(row):
        # Returns the index of the first negative in a non-increasing row
        lo, hi = 0, len(row) - 1
        result = len(row)  # if no negative, all non-negative
        while lo <= hi:
            mid = (lo + hi) // 2
            if row[mid] < 0:
                result = mid
                hi = mid - 1
            else:
                lo = mid + 1
        return result

    count = 0
    for row in grid:
        idx = first_negative(row)
        count += len(row) - idx
    return count


# =============================================================================
# WAY 5: Brute force O(m*n)
# =============================================================================
def count_negatives_5(grid):
    count = 0
    for row in grid:
        for val in row:
            if val < 0:
                count += 1
    return count


# =============================================================================
# WAY 6: Flatten and count
# =============================================================================
def count_negatives_6(grid):
    flat = [v for row in grid for v in row]
    return sum(1 for v in flat if v < 0)


# =============================================================================
# WAY 7: With sum of bool
# =============================================================================
def count_negatives_7(grid):
    return sum(v < 0 for row in grid for v in row)


# =============================================================================
# WAY 8: With filter and len
# =============================================================================
def count_negatives_8(grid):
    return sum(len([v for v in row if v < 0]) for row in grid)


# =============================================================================
# WAY 9: Use numpy
# =============================================================================
def count_negatives_9(grid):
    import numpy as np
    return int(np.sum(np.array(grid) < 0))


# =============================================================================
# WAY 10: Start from top-right with explicit pointer
# =============================================================================
def count_negatives_10(grid):
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = 0, n - 1
    while r < m and c >= 0:
        if grid[r][c] >= 0:
            r += 1
        else:
            count += m - r
            c -= 1
    return count


# =============================================================================
# WAY 11: Start from bottom-right (simple variant)
# =============================================================================
def count_negatives_11(grid):
    """Alternative O(m+n) - start from bottom-left going right or up."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = m - 1, 0  # bottom-left corner
    while r >= 0 and c < n:
        if grid[r][c] < 0:
            count += n - c
            r -= 1
        else:
            c += 1
    return count


# =============================================================================
# WAY 12: Using binary search per row from left
# =============================================================================
def count_negatives_12(grid):
    count = 0
    for row in grid:
        # Find leftmost negative
        lo, hi = 0, len(row) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if row[mid] < 0:
                hi = mid - 1
            else:
                lo = mid + 1
        # All from lo to end are negative
        count += len(row) - lo
    return count


# =============================================================================
# WAY 13: Walking from bottom-left with pointer
# =============================================================================
def count_negatives_13(grid):
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = m - 1, 0
    while r >= 0 and c < n:
        if grid[r][c] < 0:
            count += n - c
            r -= 1
        else:
            c += 1
    return count


# =============================================================================
# WAY 14: Using count() method
# =============================================================================
def count_negatives_14(grid):
    return sum(row.count(lambda x: x < 0) for row in grid)  # count() doesn't take lambda
# Fix:
def count_negatives_14(grid):
    count = 0
    for row in grid:
        # Manual count of negatives in row
        for v in row:
            if v < 0:
                count += 1
    return count


# =============================================================================
# WAY 15: Recursive (educational)
# =============================================================================
def count_negatives_15(grid):
    def helper(r, c):
        m, n = len(grid), len(grid[0])
        if r >= m or c < 0:
            return 0
        if grid[r][c] < 0:
            # All below are negative in column c
            return (m - r) + helper(r, c - 1)
        else:
            return helper(r + 1, c)
    if not grid or not grid[0]:
        return 0
    return helper(0, len(grid[0]) - 1)


# =============================================================================
# WAY 16: Use sorted property - find negative threshold per row
# =============================================================================
def count_negatives_16(grid):
    if not grid or not grid[0]:
        return 0
    count = 0
    m, n = len(grid), len(grid[0])
    # For each row, find first negative index
    for i in range(m):
        for j in range(n):
            if grid[i][j] < 0:
                # Row from j to n-1 is negative
                count += n - j
                break
    return count


# =============================================================================
# WAY 17: Two-pointer with row tracking
# =============================================================================
def count_negatives_17(grid):
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = 0, n - 1
    while r < m and c >= 0:
        if grid[r][c] < 0:
            count += m - r
            c -= 1
        else:
            r += 1
    return count


# =============================================================================
# WAY 18: Class-based
# =============================================================================
class NegativeCounter:
    def __init__(self, grid):
        self.grid = grid

    def count(self):
        if not self.grid or not self.grid[0]:
            return 0
        m, n = len(self.grid), len(self.grid[0])
        count = 0
        r, c = 0, n - 1
        while r < m and c >= 0:
            if self.grid[r][c] < 0:
                count += m - r
                c -= 1
            else:
                r += 1
        return count


def count_negatives_18(grid):
    return NegativeCounter(grid).count()


# =============================================================================
# WAY 19: Most concise
# =============================================================================
def count_negatives_19(grid):
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    r, c, count = 0, n - 1, 0
    while r < m and c >= 0:
        if grid[r][c] < 0:
            count += m - r
            c -= 1
        else:
            r += 1
    return count


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def count_negatives_20(grid):
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = 0, n - 1
    while r < m and c >= 0:
        if grid[r][c] < 0:
            count += m - r
            c -= 1
        else:
            r += 1
    return count


# =============================================================================
# HOW I THINK - SAY ALOUD IN THE INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I have an m x n matrix sorted in non-increasing order by both rows
and columns. I need to count the negative numbers."

Key Insight (Best O(m+n) approach):
"Start from TOP-RIGHT corner. Walk left or down:
- If current cell is NEGATIVE: all cells BELOW in this column are also
  negative (column-sorted). Count them. Move LEFT.
- If current cell is NON-NEGATIVE: cells to the LEFT might be negative
  (column is non-increasing). Move DOWN to find negatives."

Algorithm:
"1. r=0, c=n-1 (top-right), count=0
2. While r < m and c >= 0:
   a. If grid[r][c] < 0: count += (m - r), c -= 1
   b. Else: r += 1
3. Return count"

Why this works:
"At top-right corner:
- Everything to the LEFT is in a non-increasing column. Could be smaller (negative).
- Everything BELOW is in a non-increasing column. Smaller or equal.
- If grid[r][c] < 0: column below is all negative. Add (m-r). Move left.
- If grid[r][c] >= 0: not negative. Move down to find negatives."

Edge cases:
- 1x1 matrix: trivially check
- All non-negative: traverse down through entire first column, return 0
- All negative: traverse left through top row, count all
- Single row: only left traversal

COMPLEXITY:
+----------------+--------+--------+
| Approach       | Time   | Space  |
+----------------+--------+--------+
| Top-right walk | O(m+n) | O(1)   |
| Binary search  | O(mlogn)| O(1)  |
| Brute force    | O(mn)  | O(1)   |
+----------------+--------+--------+

KEY TRICK:
Start at a CORNER (top-right or bottom-left). The sorted property
gives us O(1) info: if current is negative, all below are negative.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Top-right walk (BEST)", count_negatives_1),
        ("Way 2: Bottom-left walk", count_negatives_2),
        ("Way 3: bisect per row", count_negatives_3),
        ("Way 4: Manual binary search", count_negatives_4),
        ("Way 5: Brute force", count_negatives_5),
        ("Way 6: Flatten and count", count_negatives_6),
        ("Way 7: Sum of bool", count_negatives_7),
        ("Way 8: Filter and len", count_negatives_8),
        ("Way 9: Numpy", count_negatives_9),
        ("Way 10: Top-right explicit", count_negatives_10),
        ("Way 11: Bottom-right", count_negatives_11),
        ("Way 12: Binary search each row", count_negatives_12),
        ("Way 13: Bottom-left explicit", count_negatives_13),
        ("Way 14: Manual count", count_negatives_14),
        ("Way 15: Recursive", count_negatives_15),
        ("Way 16: Per-row threshold", count_negatives_16),
        ("Way 17: Two-pointer", count_negatives_17),
        ("Way 18: Class-based", count_negatives_18),
        ("Way 19: Most concise", count_negatives_19),
        ("Way 20: Final cleanest", count_negatives_20),
    ]

    test_cases = [
        # Standard example
        ([[4, 3, 2, -1], [3, 2, 1, -1], [1, 1, -1, -2], [-1, -1, -2, -3]], 8),
        # All non-negative
        ([[3, 2], [1, 0]], 0),
        # All negative
        ([[-1, -2], [-3, -4]], 4),
        # Single cell non-negative
        ([[5]], 0),
        # Single cell negative
        ([[-5]], 1),
        # Single row mixed (non-increasing)
        ([[3, 2, 1, 0, -1, -2]], 2),
        # Single column mixed (non-increasing)
        ([[3], [2], [1], [0], [-1], [-2]], 2),
        # All zeros
        ([[0, 0], [0, 0]], 0),
        # 3x3 sorted (non-increasing rows and cols)
        # Row 0: 5, 4, -1
        # Row 1: 3, 2, -1
        # Row 2: 1, -1, -1
        # Negatives: row0=1, row1=1, row2=2 = 4 total
        ([[5, 4, -1], [3, 2, -1], [1, -1, -1]], 4),
        # Empty grid
        ([], 0),
        ([[]], 0),
    ]

    print("=" * 70)
    print("COUNT NEGATIVE NUMBERS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-negative-numbers-in-a-sorted-matrix")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for grid, expected in test_cases:
            try:
                # Use deep copy for safety
                import copy
                grid_copy = copy.deepcopy(grid)
                result = func(grid_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: grid={grid} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on grid={grid} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
