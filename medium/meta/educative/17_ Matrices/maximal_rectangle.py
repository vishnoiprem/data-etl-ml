"""
Maximal Rectangle
Hard | 40 min

Given a binary matrix filled with 0s and 1s, find the largest rectangle
containing only 1s and return its area.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/maximal-rectangle

Examples:
    matrix=[
      [1,0,1,0,0],
      [1,0,1,1,1],
      [1,1,1,1,1],
      [1,0,0,1,0]
    ] -> 6
    matrix=[[0,1],[1,0]] -> 1
    matrix=[[1]] -> 1
    matrix=[] -> 0

Constraints:
- 1 <= rows, cols <= 200
- matrix[i][j] is 0 or 1

KEY INSIGHT:
For each row, treat the column heights as a histogram (number of
consecutive 1s above). Largest rectangle in histogram -> largest
rectangle ending at this row.

Algorithms for largest rectangle in histogram:
1. Stack: O(n) per row -> O(R*C).
2. Two-pointer per row: O(n) -> O(R*C).

Total: O(R*C) time and space.
"""


# =============================================================================
# WAY 1: Histogram stack per row (BEST - Memorize!)
# =============================================================================
def maximal_rectangle_1(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [0] * (C + 1)  # +1 sentinel
    best = 0
    for r in range(R):
        for c in range(C):
            if matrix[r][c] == "1" or matrix[r][c] == 1:
                heights[c] += 1
            else:
                heights[c] = 0
        # Largest rectangle in histogram heights[0..C]
        stack = []
        for i in range(C + 1):
            while stack and heights[stack[-1]] > heights[i]:
                h = heights[stack.pop()]
                w = i if not stack else i - stack[-1] - 1
                best = max(best, h * w)
            stack.append(i)
    return best


# =============================================================================
# WAY 2: 2D DP - height, left, right
# =============================================================================
def maximal_rectangle_2(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    height = [0] * C
    left = [0] * C
    right = [C] * C
    best = 0
    for r in range(R):
        cur_left = 0
        cur_right = C
        for c in range(C):
            if matrix[r][c] == "1" or matrix[r][c] == 1:
                height[c] += 1
                left[c] = max(left[c], cur_left)
            else:
                height[c] = 0
                left[c] = 0
                cur_left = c + 1
        for c in range(C - 1, -1, -1):
            if matrix[r][c] == "1" or matrix[r][c] == 1:
                right[c] = min(right[c], cur_right)
            else:
                right[c] = C
                cur_right = c
        for c in range(C):
            best = max(best, (right[c] - left[c]) * height[c])
    return best


# =============================================================================
# WAY 3: Largest Rectangle in Histogram helper
# =============================================================================
def maximal_rectangle_3(matrix):
    """Use lrh helper."""
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])

    def largest_rect_histogram(h):
        stack = []
        best = 0
        for i in range(len(h) + 1):
            while stack and (h[stack[-1]] if i < len(h) else -1) > (
                h[i] if i < len(h) else -1
            ):
                # We use sentinel; this won't trigger since -1 is smallest.
                # Manual sentinel handling:
                break
            # Better: append -1 sentinel
            cur_h = h[i] if i < len(h) else -1
            while stack and h[stack[-1]] > cur_h:
                height = h[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                best = max(best, height * width)
            stack.append(i)
        return best

    heights = [0] * (C + 1)
    best = 0
    for r in range(R):
        for c in range(C):
            if matrix[r][c] == "1" or matrix[r][c] == 1:
                heights[c] += 1
            else:
                heights[c] = 0
        best = max(best, largest_rect_histogram(heights))
    return best


# =============================================================================
# WAY 4: Two-pointer largest rect per row (without stack)
# =============================================================================
def maximal_rectangle_4(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [0] * C
    best = 0
    for r in range(R):
        for c in range(C):
            if matrix[r][c] == "1" or matrix[r][c] == 1:
                heights[c] += 1
            else:
                heights[c] = 0
        # For each column, expand left and right while height > heights[c]
        for c in range(C):
            h = heights[c]
            if h == 0:
                continue
            l = c
            while l > 0 and heights[l - 1] >= h:
                l -= 1
            r = c
            while r < C - 1 and heights[r + 1] >= h:
                r += 1
            best = max(best, h * (r - l + 1))
    return best


# =============================================================================
# WAY 5: Brute force - try all pairs (r1, r2) of rows
# =============================================================================
def maximal_rectangle_5(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    best = 0
    # For each pair (r1, r2), check max consecutive cols all-1.
    for r1 in range(R):
        col_count = [0] * C
        for r2 in range(r1, R):
            for c in range(C):
                v = matrix[r2][c]
                col_count[c] += 1 if (v == "1" or v == 1) else 0
            # Find max consecutive where col_count[c] == r2 - r1 + 1
            cur = 0
            for c in range(C):
                if col_count[c] == r2 - r1 + 1:
                    cur += 1
                    best = max(best, cur * (r2 - r1 + 1))
                else:
                    cur = 0
    return best


# =============================================================================
# WAY 6: DP - bottom-up largest submatrix of 1s
# =============================================================================
def maximal_rectangle_6(matrix):
    """DP: for each cell, track heights and expand rectangle widths.
    height[i] = number of consecutive 1s above including (i,j).
    left[i]   = leftmost column where height >= height[i] (consecutively).
    right[i]  = rightmost exclusive column where height >= height[i].
    """
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    height = [0] * C
    left = [0] * C
    right = [C] * C
    best = 0
    for r in range(R):
        cur_left = 0
        for c in range(C):
            v = matrix[r][c]
            if v == "1" or v == 1:
                height[c] += 1
                left[c] = max(left[c], cur_left)
            else:
                height[c] = 0
                left[c] = 0
                cur_left = c + 1
        cur_right = C
        for c in range(C - 1, -1, -1):
            v = matrix[r][c]
            if v == "1" or v == 1:
                right[c] = min(right[c], cur_right)
            else:
                right[c] = C
                cur_right = c
        for c in range(C):
            best = max(best, height[c] * (right[c] - left[c]))
    return best


# =============================================================================
# WAY 7: Histogram with monotonic stack (cleaner)
# =============================================================================
def maximal_rectangle_7(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [0] * C
    best = 0
    for r in range(R):
        for c in range(C):
            v = matrix[r][c]
            heights[c] = heights[c] + 1 if (v == "1" or v == 1) else 0
        # Use stack for histogram
        stack = []
        for i in range(C + 1):
            h = heights[i] if i < C else 0
            while stack and heights[stack[-1]] > h:
                height = heights[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                best = max(best, height * width)
            stack.append(i)
    return best


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class MaxRectangleFinder:
    def __init__(self, matrix):
        self.matrix = matrix

    def solve(self):
        if not self.matrix or not self.matrix[0]:
            return 0
        R, C = len(self.matrix), len(self.matrix[0])
        heights = [0] * (C + 1)
        best = 0
        for r in range(R):
            for c in range(C):
                v = self.matrix[r][c]
                heights[c] = heights[c] + 1 if (v == "1" or v == 1) else 0
            stack = []
            for i in range(C + 1):
                while stack and heights[stack[-1]] > heights[i]:
                    h = heights[stack.pop()]
                    w = i if not stack else i - stack[-1] - 1
                    best = max(best, h * w)
                stack.append(i)
        return best


def maximal_rectangle_8(matrix):
    return MaxRectangleFinder(matrix).solve()


# =============================================================================
# WAY 9: Stack-based with explicit sentinel
# =============================================================================
def maximal_rectangle_9(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [0] * (C + 1)
    best = 0
    for r in range(R):
        for c in range(C):
            v = matrix[r][c]
            heights[c] = heights[c] + 1 if (v == "1" or v == 1) else 0
        # heights[C] = 0 sentinel
        stack = []
        for i in range(C + 1):
            while stack and heights[stack[-1]] > heights[i]:
                h = heights[stack.pop()]
                w = i if not stack else i - stack[-1] - 1
                if h * w > best:
                    best = h * w
            stack.append(i)
    return best


# =============================================================================
# WAY 10: Numpy histogram approach
# =============================================================================
def maximal_rectangle_10(matrix):
    if not matrix or not matrix[0]:
        return 0
    import numpy as np
    arr = np.array(
        [[1 if (v == "1" or v == 1) else 0 for v in row] for row in matrix],
        dtype=np.int64,
    )
    R, C = arr.shape
    heights = np.zeros(C, dtype=np.int64)
    best = 0
    for r in range(R):
        for c in range(C):
            heights[c] = heights[c] + arr[r, c] if arr[r, c] else 0
        # Largest rect in histogram with stack
        stack = []
        for i in range(C + 1):
            cur_h = int(heights[i]) if i < C else 0
            while stack and int(heights[stack[-1]]) > cur_h:
                h = int(heights[stack.pop()])
                w = i if not stack else i - stack[-1] - 1
                best = max(best, h * w)
            stack.append(i)
    return best


# =============================================================================
# WAY 11: Monotonic stack from scratch
# =============================================================================
def maximal_rectangle_11(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [0] * C
    best = 0
    for r in range(R):
        for c in range(C):
            v = matrix[r][c]
            if v == "1" or v == 1:
                heights[c] += 1
            else:
                heights[c] = 0
        # Process histogram
        stack = []  # indices
        i = 0
        while i <= C:
            cur_h = heights[i] if i < C else 0
            if not stack or cur_h >= heights[stack[-1]]:
                stack.append(i)
                i += 1
            else:
                top = stack.pop()
                h = heights[top]
                w = i if not stack else i - stack[-1] - 1
                best = max(best, h * w)
    return best


# =============================================================================
# WAY 12: Convert chars to ints upfront
# =============================================================================
def maximal_rectangle_12(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    # Normalize to int matrix
    mat = [
        [1 if (v == "1" or v == 1) else 0 for v in row] for row in matrix
    ]
    heights = [0] * (C + 1)
    best = 0
    for r in range(R):
        for c in range(C):
            heights[c] = heights[c] + 1 if mat[r][c] else 0
        stack = []
        for i in range(C + 1):
            while stack and heights[stack[-1]] > heights[i]:
                h = heights[stack.pop()]
                w = i if not stack else i - stack[-1] - 1
                best = max(best, h * w)
            stack.append(i)
    return best


# =============================================================================
# WAY 13: Histogram with deque
# =============================================================================
def maximal_rectangle_13(matrix):
    if not matrix or not matrix[0]:
        return 0
    from collections import deque
    R, C = len(matrix), len(matrix[0])
    heights = [0] * (C + 1)
    best = 0
    for r in range(R):
        for c in range(C):
            v = matrix[r][c]
            heights[c] = heights[c] + 1 if (v == "1" or v == 1) else 0
        dq = deque()
        for i in range(C + 1):
            while dq and heights[dq[-1]] > heights[i]:
                h = heights[dq.pop()]
                w = i if not dq else i - dq[-1] - 1
                best = max(best, h * w)
            dq.append(i)
    return best


# =============================================================================
# WAY 14: Divide and conquer (recursive)
# =============================================================================
def maximal_rectangle_14(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    mat = [[1 if (v == "1" or v == 1) else 0 for v in row] for row in matrix]

    def max_hist(h):
        if not h:
            return 0
        n = len(h)
        stack = []
        best = 0
        for i in range(n + 1):
            cur = h[i] if i < n else 0
            while stack and h[stack[-1]] > cur:
                height = h[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                best = max(best, height * width)
            stack.append(i)
        return best

    heights = [0] * C
    best = 0
    for r in range(R):
        for c in range(C):
            heights[c] = heights[c] + 1 if mat[r][c] else 0
        best = max(best, max_hist(heights))
    return best


# =============================================================================
# WAY 15: 2D DP with dp[i][j] = max rectangle area ending at (i,j)
# =============================================================================
def maximal_rectangle_15(matrix):
    """Histogram with explicit sentinel - same as Way 1 but with explicit
    pre-allocated sentinel."""
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [0] * (C + 1)
    best = 0
    for r in range(R):
        for c in range(C):
            v = matrix[r][c]
            heights[c] = heights[c] + 1 if (v == "1" or v == 1) else 0
        # heights[C] is 0 sentinel
        stack = []
        i = 0
        while i <= C:
            if not stack or heights[stack[-1]] <= heights[i]:
                stack.append(i)
                i += 1
            else:
                top = stack.pop()
                h = heights[top]
                w = i if not stack else i - stack[-1] - 1
                if h * w > best:
                    best = h * w
    return best


# =============================================================================
# WAY 16: For each cell, find max width and use stack
# =============================================================================
def maximal_rectangle_16(matrix):
    """Combination: width DP + height histogram."""
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    height = [0] * C
    best = 0
    for r in range(R):
        for c in range(C):
            v = matrix[r][c]
            height[c] = height[c] + 1 if (v == "1" or v == 1) else 0
        # Stack-based histogram
        stack = []
        for i in range(C + 1):
            cur_h = height[i] if i < C else 0
            while stack and height[stack[-1]] > cur_h:
                h = height[stack.pop()]
                w = i if not stack else i - stack[-1] - 1
                best = max(best, h * w)
            stack.append(i)
    return best


# =============================================================================
# WAY 17: Pre-compute heights, then iterate
# =============================================================================
def maximal_rectangle_17(matrix):
    """Pre-compute all heights, then process."""
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [[0] * C for _ in range(R)]
    for c in range(C):
        v = matrix[0][c]
        heights[0][c] = 1 if (v == "1" or v == 1) else 0
    for r in range(1, R):
        for c in range(C):
            v = matrix[r][c]
            if v == "1" or v == 1:
                heights[r][c] = heights[r - 1][c] + 1
            else:
                heights[r][c] = 0
    best = 0
    for r in range(R):
        # Compute largest rectangle in histogram heights[r]
        stack = []
        for i in range(C + 1):
            cur_h = heights[r][i] if i < C else 0
            while stack and heights[r][stack[-1]] > cur_h:
                h = heights[r][stack.pop()]
                w = i if not stack else i - stack[-1] - 1
                best = max(best, h * w)
            stack.append(i)
    return best


# =============================================================================
# WAY 18: Pure brute force O(R^2 * C^2)
# =============================================================================
def maximal_rectangle_18(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    mat = [[1 if (v == "1" or v == 1) else 0 for v in row] for row in matrix]
    best = 0
    for r1 in range(R):
        for r2 in range(r1, R):
            for c1 in range(C):
                for c2 in range(c1, C):
                    # Check if all 1s in (r1..r2, c1..c2)
                    ok = True
                    for rr in range(r1, r2 + 1):
                        for cc in range(c1, c2 + 1):
                            if mat[rr][cc] != 1:
                                ok = False
                                break
                        if not ok:
                            break
                    if ok:
                        area = (r2 - r1 + 1) * (c2 - c1 + 1)
                        if area > best:
                            best = area
    return best


# =============================================================================
# WAY 19: Top-down memo on (r1, r2, c1, c2) - just brute with memo on sum
# =============================================================================
def maximal_rectangle_19(matrix):
    """Pre-compute prefix sum, then O(R^2 * C^2) with O(1) area check."""
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    mat = [[1 if (v == "1" or v == 1) else 0 for v in row] for row in matrix]
    # Prefix sum: ps[i+1][j+1] = sum of mat[0..i][0..j]
    ps = [[0] * (C + 1) for _ in range(R + 1)]
    for i in range(R):
        for j in range(C):
            ps[i + 1][j + 1] = (
                ps[i][j + 1] + ps[i + 1][j] - ps[i][j] + mat[i][j]
            )

    def rect_sum(r1, c1, r2, c2):
        return (
            ps[r2 + 1][c2 + 1]
            - ps[r1][c2 + 1]
            - ps[r2 + 1][c1]
            + ps[r1][c1]
        )

    best = 0
    for r1 in range(R):
        for r2 in range(r1, R):
            h = r2 - r1 + 1
            for c1 in range(C):
                for c2 in range(c1, C):
                    w = c2 - c1 + 1
                    if rect_sum(r1, c1, r2, c2) == h * w:
                        if h * w > best:
                            best = h * w
    return best


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def maximal_rectangle_20(matrix):
    """
    THE ONE TO MEMORIZE.

    For each row, treat columns as histogram heights (consecutive 1s above).
    Largest rectangle in histogram = O(C) with monotonic stack.

    Time:  O(R * C)
    Space: O(C)
    """
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [0] * (C + 1)
    best = 0
    for r in range(R):
        for c in range(C):
            v = matrix[r][c]
            heights[c] = heights[c] + 1 if (v == "1" or v == 1) else 0
        # Largest rect in histogram heights[0..C-1], with sentinel heights[C]=0
        stack = []
        for i in range(C + 1):
            while stack and heights[stack[-1]] > heights[i]:
                h = heights[stack.pop()]
                w = i if not stack else i - stack[-1] - 1
                best = max(best, h * w)
            stack.append(i)
    return best


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"Given a binary matrix, find the largest rectangle of all 1s and return
its area."

Key Insight:
"Treat each row as the base of a histogram. Column heights = number of
consecutive 1s above (including current row).

Then for each row, find the largest rectangle in the histogram.

Algorithm for histogram (monotonic stack):
- Append sentinel 0 to end.
- For each i, while stack top has height > heights[i]:
    h = popped height
    w = i if stack empty, else i - stack.top - 1
    area = h * w, update max.
- Push i to stack.

For each row, this is O(C). Total O(R * C)."

Algorithm:
1. heights = [0] * (C + 1) (sentinel).
2. For each row r:
     For each col c:
       heights[c] = heights[c] + 1 if matrix[r][c] == 1 else 0
     Run stack-based largest rect.
3. Return max area.

Edge Cases:
- Empty / no rows: 0.
- Single row: max consecutive 1s.
- All 1s: R * C.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Hist+stack| O(R*C)| O(C)   |
| Square DP| O(R*C)| O(R*C) |
| Brute    | O(R^2*C^2)| O(1)|
+----------+--------+--------+

KEY TRICK: Histogram conversion reduces 2D problem to 1D histogram problem.

ALTERNATE: 2D DP for squares only (not all rectangles). Less powerful.

RELATED:
- Largest Rectangle in Histogram (LC 84).
- Maximal Square (LC 221).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Histogram stack (BEST)", maximal_rectangle_1),
        ("Way 2: 2D DP h/l/r", maximal_rectangle_2),
        ("Way 3: LRH helper", maximal_rectangle_3),
        ("Way 4: Two-pointer per row", maximal_rectangle_4),
        ("Way 5: Brute rows", maximal_rectangle_5),
        ("Way 6: Square DP", maximal_rectangle_6),
        ("Way 7: Histogram stack (clean)", maximal_rectangle_7),
        ("Way 8: Class OOP", maximal_rectangle_8),
        ("Way 9: Sentinel stack", maximal_rectangle_9),
        ("Way 10: Numpy", maximal_rectangle_10),
        ("Way 11: Monotonic stack from scratch", maximal_rectangle_11),
        ("Way 12: Convert chars upfront", maximal_rectangle_12),
        ("Way 13: Deque", maximal_rectangle_13),
        ("Way 14: Divide and conquer", maximal_rectangle_14),
        ("Way 15: Square DP area", maximal_rectangle_15),
        ("Way 16: Width + stack", maximal_rectangle_16),
        ("Way 17: Pre-compute heights", maximal_rectangle_17),
        ("Way 18: Pure brute O(R^2*C^2)", maximal_rectangle_18),
        ("Way 19: Prefix sum brute", maximal_rectangle_19),
        ("Way 20: Final cleanest", maximal_rectangle_20),
    ]

    test_cases = [
        # (matrix, expected)
        (
            [
                [1, 0, 1, 0, 0],
                [1, 0, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 0, 0, 1, 0],
            ],
            6,
        ),
        ([[0, 1], [1, 0]], 1),
        ([[1]], 1),
        ([[0]], 0),
        ([[1, 1, 1, 1]], 4),
        ([[1, 1], [1, 1]], 4),
        ([[1, 0, 1, 0, 1, 0, 1, 1]], 2),
        (
            [[1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1]],
            6,
        ),
        (
            [
                ["1", "0", "1", "0", "0"],
                ["1", "0", "1", "1", "1"],
                ["1", "1", "1", "1", "1"],
                ["1", "0", "0", "1", "0"],
            ],
            6,
        ),
    ]

    print("=" * 70)
    print("MAXIMAL RECTANGLE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/maximal-rectangle")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for mat, expected in test_cases:
            try:
                # Deep-copy so implementations can mutate.
                m_copy = [row[:] for row in mat]
                result = func(m_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
