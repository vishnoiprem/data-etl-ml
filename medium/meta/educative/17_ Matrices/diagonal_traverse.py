"""
Diagonal Traverse
Medium | 30 min

Given an m x n matrix mat, return all elements in diagonal order.
Diagonals alternate: first goes UP-RIGHT, next goes DOWN-LEFT, then UP-RIGHT, etc.

Wait - per the educative problem, first diagonal goes DOWN-LEFT (just [10]
in the example), then UP-RIGHT ([20, 60]), etc. So first diagonal is DOWN-LEFT.

Actually, looking again: in the example mat = [[10,20,30,40,50],[60,70,80,90,100]]:
- First element visited: 10 (just starting position).
- Next diagonal: [20, 60] going DOWN-LEFT? No wait, 20 is at (0,1), 60 is at (1,0).
  Going from (0,1) to (1,0) is moving DOWN-LEFT.
- Next: [30, 70, 40] - (0,2)→(1,1)→(2,0)? No, only 2 rows. So (0,2)→(1,1) is DOWN-LEFT.

Hmm, let me re-check: actually [30, 70, 40]? Looking at the educative example, the answer
was [10, 20, 60, 30, 70, 40, 80, 50, 90, 100].

Let me re-interpret: the diagonals are visited in order:
- Diagonal d=0: [(0,0)] = [10]
- Diagonal d=1: [(0,1), (1,0)] = [20, 60] (going DOWN-LEFT from top-right to bottom-left)
- Diagonal d=2: [(0,2), (1,1), (0,?)... ]

Wait, looking at the actual answer: [10, 20, 60, 30, 70, 40, 80, 50, 90, 100]
After [10] we have [20, 60]: that's (0,1), (1,0) — going DOWN-LEFT direction (row+1, col-1).
After [20, 60] we have [30, 70, 40]: that's (0,2), (1,1), (0,?...)... but wait, the answer is
just [30, 70, 40] which is 3 elements. (0,2), (1,1), (0,?).

Hmm, this is confusing. Let me check again: the answer is [10, 60, 20, 30, 70, 40, 80, 50, 90, 100].

Actually re-reading the educative fetch:
"correct answer is B: [10,60,20,30,70,40,80,50,90,100]"

So:
- [10]: (0,0)
- [60, 20]: (1,0), (0,1) — going UP-RIGHT
- [30, 70]: (0,2), (1,1) — going DOWN-LEFT
- [40, 80]: (1,2), (0,3)... wait that's only 2 elements
- ...

Actually the correct answer to the typical Diagonal Traverse problem (LC 498) is:
For mat = [[1,2,3],[4,5,6],[7,8,9]]:
[1,2,4,7,5,3,6,8,9]

First diagonal UP-RIGHT: just (0,0) = [1]
Second diagonal DOWN-LEFT: (0,1), (1,0) = [2,4]
Third diagonal UP-RIGHT: (2,0), (1,1), (0,2) = [7,5,3]
Fourth diagonal DOWN-LEFT: (1,2), (2,1) = [6,8]
Fifth diagonal UP-RIGHT: (2,2) = [9]

So result: [1, 2, 4, 7, 5, 3, 6, 8, 9]

So the first diagonal IS upward (just the starting point).
For mat = [[10,20,30,40,50],[60,70,80,90,100]] (2x5):
- Diagonal 0 (UP): [(0,0)] = [10]
- Diagonal 1 (DOWN-LEFT): [(0,1),(1,0)] = [20, 60]
- Diagonal 2 (UP): [(1,1),(0,2)] = [70, 30]
- Diagonal 3 (DOWN-LEFT): [(0,3),(1,2)] = [40, 80]
- Diagonal 4 (UP): [(1,3),(0,4)] = [90, 50]
- Diagonal 5 (DOWN-LEFT): [(1,4)] = [100]

Result: [10, 20, 60, 70, 30, 40, 80, 90, 50, 100]

OK so the order is: UP-RIGHT first (just the starting cell), then DOWN-LEFT, alternating.
And within UP-RIGHT diagonals (going up means row decreases): we traverse from BOTTOM to TOP.
Within DOWN-LEFT diagonals (going down means row increases): we traverse from TOP to BOTTOM.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/diagonal-traverse
"""


# =============================================================================
# WAY 1: Direction-Flipping Traversal (BEST - Memorize!)
# =============================================================================
def findDiagonalOrder_1(mat):
    """
    KEY INSIGHT: Track position (i, j) and direction (up/down).
    - UP-RIGHT: (i-1, j+1). Flip when hitting top row or right column.
    - DOWN-LEFT: (i+1, j-1). Flip when hitting bottom row or left column.
    - First diagonal is UP (just starting point).

    Time:  O(m * n)
    Space: O(1) excluding output
    """
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    i = j = 0
    going_up = True

    for _ in range(m * n):
        result.append(mat[i][j])
        if going_up:
            if j == n - 1:    # hit right edge
                i += 1
                going_up = False
            elif i == 0:       # hit top edge
                j += 1
                going_up = False
            else:
                i -= 1
                j += 1
        else:  # going down-left
            if i == m - 1:    # hit bottom edge
                j += 1
                going_up = True
            elif j == 0:       # hit left edge
                i += 1
                going_up = True
            else:
                i += 1
                j -= 1
    return result


# =============================================================================
# WAY 2: Verbose with explicit names
# =============================================================================
def findDiagonalOrder_2(mat):
    """Same as Way 1 with verbose naming."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    row = col = 0
    direction = 1  # 1 = up-right, -1 = down-left

    for _ in range(m * n):
        result.append(mat[row][col])
        if direction == 1:  # going up-right
            if col == n - 1:
                row += 1
                direction = -1
            elif row == 0:
                col += 1
                direction = -1
            else:
                row -= 1
                col += 1
        else:  # going down-left
            if row == m - 1:
                col += 1
                direction = 1
            elif col == 0:
                row += 1
                direction = 1
            else:
                row += 1
                col -= 1
    return result


# =============================================================================
# WAY 3: Group by diagonal index (use defaultdict)
# =============================================================================
def findDiagonalOrder_3(mat):
    """
    KEY INSIGHT: Elements on same diagonal share i+j. Group them, then
    alternate direction.
    - Even i+j: reverse the diagonal (it's traversed UP-RIGHT, so we go from
      bottom to top, meaning we collected top-to-bottom and need to reverse)
    - Odd i+j: keep as-is (traversed DOWN-LEFT, top-to-bottom)

    Wait - first diagonal is UP (just starting cell), so i+j=0 (even) is UP.
    Diagonal 1 (DOWN-LEFT) is i+j=1 (odd).
    For UP diagonals: traverse from bottom of diagonal to top.
    For DOWN-LEFT diagonals: traverse from top to bottom.
    """
    from collections import defaultdict
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    diagonals = defaultdict(list)
    for i in range(m):
        for j in range(n):
            diagonals[i + j].append(mat[i][j])

    result = []
    for k in range(m + n - 1):
        if k % 2 == 0:
            # UP-RIGHT diagonal: reverse order
            result.extend(diagonals[k][::-1])
        else:
            # DOWN-LEFT diagonal: as-is
            result.extend(diagonals[k])
    return result


# =============================================================================
# WAY 4: Group by diagonal index with insert (alternate)
# =============================================================================
def findDiagonalOrder_4(mat):
    """Same as Way 3 but use insert at 0 for odd diagonals so they end up reversed naturally."""
    from collections import defaultdict
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    diagonals = defaultdict(list)
    for i in range(m):
        for j in range(n):
            d = i + j
            if d % 2 == 0:
                diagonals[d].append(mat[i][j])  # even (UP) - normal order
            else:
                # odd (DOWN-LEFT) - insert at 0 so they end up reversed
                # Actually: DOWN-LEFT means top-to-bottom (i increasing)
                # which is the natural order. So we just append.
                diagonals[d].append(mat[i][j])
    result = []
    for k in range(m + n - 1):
        if k % 2 == 0:
            # UP-RIGHT: reverse to go from bottom to top
            result.extend(reversed(diagonals[k]))
        else:
            result.extend(diagonals[k])
    return result


# =============================================================================
# WAY 5: Using list of lists for diagonals (no defaultdict)
# =============================================================================
def findDiagonalOrder_5(mat):
    """Allocate all diagonal lists upfront."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    diagonals = [[] for _ in range(m + n - 1)]
    for i in range(m):
        for j in range(n):
            diagonals[i + j].append(mat[i][j])
    result = []
    for k, d in enumerate(diagonals):
        if k % 2 == 0:
            result.extend(reversed(d))
        else:
            result.extend(d)
    return result


# =============================================================================
# WAY 6: Direction with single-direction vector
# =============================================================================
def findDiagonalOrder_6(mat):
    """Use (di, dj) direction vector instead of boolean."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    i = j = 0
    di, dj = -1, 1  # up-right

    for _ in range(m * n):
        result.append(mat[i][j])
        # Compute next position
        ni, nj = i + di, j + dj
        # If out of bounds, flip direction and adjust
        if not (0 <= ni < m and 0 <= nj < n):
            # Hit top or right edge
            if di == -1:
                # going up, hit top: move to next column (right) or stay
                if j + 1 < n:
                    j += 1
                else:
                    i += 1
                di, dj = 1, -1
            else:
                # going down-left, hit left or bottom
                if i + 1 < m:
                    i += 1
                else:
                    j += 1
                di, dj = -1, 1
        else:
            i, j = ni, nj
    return result


# =============================================================================
# WAY 7: Using BFS-like approach (single queue of diagonals)
# =============================================================================
def findDiagonalOrder_7(mat):
    """Use deque to process diagonals in order."""
    from collections import deque
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    # Each diagonal: list of (i, j) coords
    diagonals = [[] for _ in range(m + n - 1)]
    for i in range(m):
        for j in range(n):
            diagonals[i + j].append((i, j))

    for d, coords in enumerate(diagonals):
        if d % 2 == 0:
            # UP-RIGHT: traverse from bottom to top
            for i, j in reversed(coords):
                result.append(mat[i][j])
        else:
            # DOWN-LEFT: top to bottom
            for i, j in coords:
                result.append(mat[i][j])
    return result


# =============================================================================
# WAY 8: Most concise direction approach
# =============================================================================
def findDiagonalOrder_8(mat):
    """Most concise."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    i = j = 0
    up = True
    for _ in range(m * n):
        result.append(mat[i][j])
        if up:
            if j == n - 1:
                i += 1; up = False
            elif i == 0:
                j += 1; up = False
            else:
                i -= 1; j += 1
        else:
            if i == m - 1:
                j += 1; up = True
            elif j == 0:
                i += 1; up = True
            else:
                i += 1; j -= 1
    return result


# =============================================================================
# WAY 9: Iterative with explicit direction function
# =============================================================================
def findDiagonalOrder_9(mat):
    """Use helper to determine next position."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []

    def next_pos(i, j, up):
        if up:
            if j == n - 1:
                return i + 1, j, False
            if i == 0:
                return i, j + 1, False
            return i - 1, j + 1, True
        else:
            if i == m - 1:
                return i, j + 1, True
            if j == 0:
                return i + 1, j, True
            return i + 1, j - 1, False

    i = j = 0
    up = True
    for _ in range(m * n):
        result.append(mat[i][j])
        i, j, up = next_pos(i, j, up)
    return result


# =============================================================================
# WAY 10: Group by diagonal using dict with reverse logic
# =============================================================================
def findDiagonalOrder_10(mat):
    """Group diagonals, reverse on even."""
    from collections import defaultdict
    if not mat or not mat[0]:
        return []
    diagonals = defaultdict(list)
    m, n = len(mat), len(mat[0])
    for i in range(m):
        for j in range(n):
            diagonals[i + j].append(mat[i][j])
    result = []
    for k in range(m + n - 1):
        # Diagonal 0 is UP, diagonal 1 is DOWN, alternating
        # UP means we want from bottom to top, i.e., reverse
        if k % 2 == 0:
            result.extend(reversed(diagonals[k]))
        else:
            result.extend(diagonals[k])
    return result


# =============================================================================
# WAY 11: Using set for visited + generator (BFS-like)
# =============================================================================
def findDiagonalOrder_11(mat):
    """BFS-like with explicit visited set."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    visited = [[False] * n for _ in range(m)]
    result = []
    i = j = 0
    direction = -1, 1  # up-right

    for _ in range(m * n):
        result.append(mat[i][j])
        visited[i][j] = True
        ni, nj = i + direction[0], j + direction[1]
        if not (0 <= ni < m and 0 <= nj < n) or visited[ni][nj]:
            # Need to flip direction
            if direction == (-1, 1):  # was up-right
                # Move to next diagonal start
                if j + 1 < n:
                    nj = j + 1
                    ni = i
                else:
                    ni = i + 1
                    nj = j
                direction = (1, -1)
            else:  # was down-left
                if i + 1 < m:
                    ni = i + 1
                    nj = j
                else:
                    ni = i
                    nj = j + 1
                direction = (-1, 1)
        i, j = ni, nj
    return result


# =============================================================================
# WAY 12: Using BFS from each diagonal
# =============================================================================
def findDiagonalOrder_12(mat):
    """Process diagonals one by one, BFS along each."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    # Diagonal d has elements (i, j) with i+j=d, 0<=i<m, 0<=j<n
    # Diagonal 0: just (0,0)
    # Diagonal 1: (0,1), (1,0)
    # etc.
    for d in range(m + n - 1):
        # Get cells on this diagonal
        cells = []
        i_start = max(0, d - (n - 1))
        i_end = min(m - 1, d)
        for i in range(i_start, i_end + 1):
            j = d - i
            cells.append((i, j))
        # For UP-RIGHT (even d): reverse (bottom to top)
        # For DOWN-LEFT (odd d): keep (top to bottom)
        if d % 2 == 0:
            cells.reverse()
        for i, j in cells:
            result.append(mat[i][j])
    return result


# =============================================================================
# WAY 13: Compact BFS-style with direction changes
# =============================================================================
def findDiagonalOrder_13(mat):
    """Compact direction-based."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    i = j = 0
    up = True
    for _ in range(m * n):
        result.append(mat[i][j])
        # Compute next
        if up:
            if i == 0 and j < n - 1:
                j += 1; up = False
            elif j == n - 1:
                i += 1; up = False
            else:
                i -= 1; j += 1
        else:
            if j == 0 and i < m - 1:
                i += 1; up = True
            elif i == m - 1:
                j += 1; up = True
            else:
                i += 1; j -= 1
    return result


# =============================================================================
# WAY 14: Generator-based traversal
# =============================================================================
def diagonal_cells(mat, d):
    """Generator for cells on diagonal d."""
    m, n = len(mat), len(mat[0])
    i_start = max(0, d - (n - 1))
    i_end = min(m - 1, d)
    for i in range(i_start, i_end + 1):
        j = d - i
        if 0 <= j < n:
            yield mat[i][j]


def findDiagonalOrder_14(mat):
    """Use generator to yield cells."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    for d in range(m + n - 1):
        cells = list(diagonal_cells(mat, d))
        if d % 2 == 0:
            cells.reverse()
        result.extend(cells)
    return result


# =============================================================================
# WAY 15: With boundary helper function
# =============================================================================
def findDiagonalOrder_15(mat):
    """Use helper functions for clarity."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])

    def in_bounds(r, c):
        return 0 <= r < m and 0 <= c < n

    result = []
    i = j = 0
    up = True
    for _ in range(m * n):
        result.append(mat[i][j])
        ni, nj = i + (-1 if up else 1), j + (1 if up else -1)
        if not in_bounds(ni, nj):
            up = not up
            if up:
                # Was going down, now going up
                if i == m - 1:
                    j += 1
                else:
                    i += 1
            else:
                # Was going up, now going down
                if j == n - 1:
                    i += 1
                else:
                    j += 1
        else:
            i, j = ni, nj
    return result


# =============================================================================
# WAY 16: Numpy-based (for fun)
# =============================================================================
def findDiagonalOrder_16(mat):
    """Use numpy for diagonal extraction."""
    try:
        import numpy as np
    except ImportError:
        return findDiagonalOrder_1(mat)
    if not mat or not mat[0]:
        return []
    arr = np.array(mat)
    m, n = arr.shape
    result = []
    for d in range(m + n - 1):
        # Indices where i + j == d
        i_min = max(0, d - (n - 1))
        i_max = min(m - 1, d)
        cells = []
        for i in range(i_min, i_max + 1):
            j = d - i
            if 0 <= j < n:
                cells.append(int(arr[i, j]))
        if d % 2 == 0:
            cells.reverse()
        result.extend(cells)
    return result


# =============================================================================
# WAY 17: Functional with map
# =============================================================================
def findDiagonalOrder_17(mat):
    """Functional style."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    diagonals = [[] for _ in range(m + n - 1)]
    for i in range(m):
        for j in range(n):
            diagonals[i + j].append(mat[i][j])

    def flat_with_reverse(diags):
        result = []
        for d, lst in enumerate(diags):
            if d % 2 == 0:
                result.extend(reversed(lst))
            else:
                result.extend(lst)
        return result
    return flat_with_reverse(diagonals)


# =============================================================================
# WAY 18: Track separate up/down counters
# =============================================================================
def findDiagonalOrder_18(mat):
    """Use count-up pattern."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    # Process each diagonal
    for d in range(m + n - 1):
        # Start positions for diagonal d:
        # UP diagonals (even d): start at bottom of diagonal
        # DOWN diagonals (odd d): start at top of diagonal
        if d % 2 == 0:
            # UP: start at i=max(0, d-(n-1)), go up to i=min(m-1, d)
            i_start = min(m - 1, d)
            i_end = max(0, d - (n - 1)) - 1
            step = -1
            for i in range(i_start, i_end, step):
                j = d - i
                if 0 <= j < n:
                    result.append(mat[i][j])
        else:
            # DOWN: start at top, go down
            i_start = max(0, d - (n - 1))
            i_end = min(m - 1, d) + 1
            for i in range(i_start, i_end):
                j = d - i
                if 0 <= j < n:
                    result.append(mat[i][j])
    return result


# =============================================================================
# WAY 19: Use islice for clarity
# =============================================================================
def findDiagonalOrder_19(mat):
    """Use itertools for cleaner code."""
    from itertools import chain
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    diagonals = []
    for d in range(m + n - 1):
        cells = []
        for i in range(max(0, d - (n - 1)), min(m - 1, d) + 1):
            j = d - i
            cells.append(mat[i][j])
        diagonals.append(cells)
    result = list(chain.from_iterable(
        reversed(d) if i % 2 == 0 else d for i, d in enumerate(diagonals)
    ))
    return result


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def findDiagonalOrder_20(mat):
    """
    THE ONE TO MEMORIZE.

    Track position (i, j) and direction (up/down).
    - UP-RIGHT: (i-1, j+1). Flip when hitting top row or right column.
    - DOWN-LEFT: (i+1, j-1). Flip when hitting bottom row or left column.

    Time:  O(m * n)
    Space: O(1) excluding output
    """
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    i = j = 0
    going_up = True
    for _ in range(m * n):
        result.append(mat[i][j])
        if going_up:
            if j == n - 1:
                i += 1
                going_up = False
            elif i == 0:
                j += 1
                going_up = False
            else:
                i -= 1
                j += 1
        else:
            if i == m - 1:
                j += 1
                going_up = True
            elif j == 0:
                i += 1
                going_up = True
            else:
                i += 1
                j -= 1
    return result


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to traverse an m x n matrix in diagonal order, alternating
between up-right and down-left directions."

Key Insight:
"Two approaches:
1. SIMULATION: Track (i, j) and a direction flag. Move and flip at boundaries.
2. GROUP BY DIAGONAL: Elements on the same diagonal share i+j. Group them
   and reverse the order for up-right diagonals.

The simulation approach is cleaner because it's O(1) extra space."

Direction Logic:
"UP-RIGHT (going up): move (i-1, j+1). Flip when:
- j == n-1 (right edge): move to (i+1, j), flip down.
- i == 0 (top edge): move to (i, j+1), flip down.

DOWN-LEFT (going down): move (i+1, j-1). Flip when:
- i == m-1 (bottom edge): move to (i, j+1), flip up.
- j == 0 (left edge): move to (i+1, j), flip up."

Edge Cases:
- m=1 or n=1: just iterate row by row.
- Single cell: return [mat[0][0]].
- Square matrix: simpler to reason about.
- Tall vs wide matrix: same logic.

First Diagonal:
"The first diagonal is UP-RIGHT and contains just (0,0)."

Complexity:
+------------------+-----------------+--------+
| Approach         | Time            | Space  |
+------------------+-----------------+--------+
| Simulation       | O(mn)           | O(1)   |
| Group by diag    | O(mn)           | O(mn)  |
+------------------+-----------------+--------+

KEY TRICK:
The boundary conditions. When you hit the edge, you move to the next
diagonal's start position (not just flip direction). The order of
precedence matters:
- For UP-RIGHT: right edge first, then top edge (right edge takes precedence).

RELATED PROBLEMS:
- Spiral Matrix (LC 54): similar traversal logic.
- Zigzag Conversion (LC 6): 1D zigzag.
- Diagonal Traverse II (LC 1424): same but with diagonals starting from bottom.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Direction-flipping (BEST)", findDiagonalOrder_1),
        ("Way 2: Verbose", findDiagonalOrder_2),
        ("Way 3: Group by diagonal", findDiagonalOrder_3),
        ("Way 4: Group + insert", findDiagonalOrder_4),
        ("Way 5: List of lists", findDiagonalOrder_5),
        ("Way 6: Direction vector", findDiagonalOrder_6),
        ("Way 7: BFS-like", findDiagonalOrder_7),
        ("Way 8: Most concise", findDiagonalOrder_8),
        ("Way 9: Helper function", findDiagonalOrder_9),
        ("Way 10: Group + reverse", findDiagonalOrder_10),
        ("Way 11: BFS visited", findDiagonalOrder_11),
        ("Way 12: Process diagonals", findDiagonalOrder_12),
        ("Way 13: Compact BFS", findDiagonalOrder_13),
        ("Way 14: Generator", findDiagonalOrder_14),
        ("Way 15: Boundary helper", findDiagonalOrder_15),
        ("Way 16: Numpy", findDiagonalOrder_16),
        ("Way 17: Functional", findDiagonalOrder_17),
        ("Way 18: Count-up", findDiagonalOrder_18),
        ("Way 19: Itertools", findDiagonalOrder_19),
        ("Way 20: Final cleanest", findDiagonalOrder_20),
    ]

    test_cases = [
        # 3x3 standard
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]],
         [1, 2, 4, 7, 5, 3, 6, 8, 9]),
        # 2x5 educative example
        ([[10, 20, 30, 40, 50], [60, 70, 80, 90, 100]],
         [10, 20, 60, 70, 30, 40, 80, 90, 50, 100]),
        # 1x1
        ([[5]], [5]),
        # 1x4
        ([[1, 2, 3, 4]], [1, 2, 3, 4]),
        # 4x1
        ([[1], [2], [3], [4]], [1, 2, 3, 4]),
        # 2x2
        ([[1, 2], [3, 4]], [1, 2, 3, 4]),
        # 3x4
        ([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]],
         [1, 2, 5, 9, 6, 3, 4, 7, 10, 11, 8, 12]),
        # 4x4
        ([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],
         [1, 2, 5, 9, 6, 3, 4, 7, 10, 13, 14, 11, 8, 12, 15, 16]),
    ]

    print("=" * 70)
    print("DIAGONAL TRAVERSE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/diagonal-traverse")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for mat, expected in test_cases:
            try:
                result = func(mat)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: mat={mat}, expected={expected}, got={result}")
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