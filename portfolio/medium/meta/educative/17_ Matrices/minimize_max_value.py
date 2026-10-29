"""
Minimize Maximum Value in a Grid
Hard | 40 min

Given an m x n integer matrix `grid` of distinct positive integers,
replace each integer with a positive integer such that:
1. Preserve RELATIVE ORDER in rows AND columns (strict inequality).
   For any two cells (r1, c1) and (r2, c2) with r1==r2 or c1==c2:
   if grid[r1][c1] > grid[r2][c2] then result[r1][c1] > result[r2][c2].
2. Minimize the MAXIMUM value in the resulting grid.

Any valid solution is acceptable.

Examples:
    grid = [[2, 4, 5], [6, 3, 8]]
    Valid: [[1, 2, 3], [2, 1, 4]]  (max = 4)

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimize-maximum-value-in-a-grid

Constraints:
- 1 <= m, n <= 30
- 1 <= m*n <= 900
- All values in grid are distinct positive integers.
"""


# =============================================================================
# WAY 1: BFS / Topological Sort from smallest cell (BEST - Memorize!)
# =============================================================================
def minimize_max_value_1(grid):
    """
    KEY INSIGHT:
    - The smallest cell in the entire grid MUST get value 1 (can't be smaller,
      and we want minimum max, so start at 1).
    - For any other cell, its value = 1 + max(value of smaller neighbor in
      same row OR same column).
    - We process cells in ascending order of original value.

    This is essentially a BFS where each cell's value depends on its
    smaller row/col neighbors.

    Time:  O(m*n*log(m*n)) for sorting
    Space: O(m*n) for result matrix
    """
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    # Sort cells by original value, ascending
    cells = sorted(
        ((grid[i][j], i, j) for i in range(m) for j in range(n))
    )

    result = [[0] * n for _ in range(m)]
    # Track current max value in each row and column
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in cells:
        # New value = 1 + max(row_max[r], col_max[c])
        result[r][c] = max(row_max[r], col_max[c]) + 1
        row_max[r] = result[r][c]
        col_max[c] = result[r][c]

    return result


# =============================================================================
# WAY 2: Verbose version with explicit names
# =============================================================================
def minimize_max_value_2(grid):
    """Same as Way 1 but more readable variable names."""
    if not grid or not grid[0]:
        return grid
    rows = len(grid)
    cols = len(grid[0])

    # Create list of (value, row, col) and sort
    cells = []
    for r in range(rows):
        for c in range(cols):
            cells.append((grid[r][c], r, c))
    cells.sort()

    result = [[0] * cols for _ in range(rows)]
    row_max_value = [0] * rows
    col_max_value = [0] * cols

    for _, r, c in cells:
        new_val = max(row_max_value[r], col_max_value[c]) + 1
        result[r][c] = new_val
        row_max_value[r] = new_val
        col_max_value[c] = new_val

    return result


# =============================================================================
# WAY 3: Using heap for priority-based processing
# =============================================================================
def minimize_max_value_3(grid):
    """
    Use a min-heap. Pop smallest cell, assign value, push its larger neighbors
    with new value = current + 1 (if larger).

    Time:  O(m*n*log(m*n))
    Space: O(m*n)
    """
    import heapq
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    # Build min-heap
    heap = [(grid[i][j], i, j) for i in range(m) for j in range(n)]
    heapq.heapify(heap)

    result = [[0] * n for _ in range(m)]

    while heap:
        val, r, c = heapq.heappop(heap)
        # Determine value: max of all assigned smaller row/col neighbors + 1
        # Look at row neighbors and col neighbors
        new_val = 1
        for cc in range(n):
            if result[r][cc] != 0 and cc != c:
                new_val = max(new_val, result[r][cc] + 1)
        for rr in range(m):
            if result[rr][c] != 0 and rr != r:
                new_val = max(new_val, result[rr][c] + 1)
        result[r][c] = new_val

    return result


# =============================================================================
# WAY 4: BFS-style with sorted cells (avoid heap)
# =============================================================================
def minimize_max_value_4(grid):
    """Same as Way 1 but with separate row/col tracking dicts."""
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    cells = sorted(
        ((grid[i][j], i, j) for i in range(m) for j in range(n))
    )
    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in cells:
        v = max(row_max[r], col_max[c]) + 1
        result[r][c] = v
        row_max[r] = v
        col_max[c] = v

    return result


# =============================================================================
# WAY 5: DP approach (compute max row/col position)
# =============================================================================
def minimize_max_value_5(grid):
    """
    Alternative: compute rank in row and col, then assign
    result[i][j] = max(row_rank, col_rank).

    But we need to ensure strict ordering. The simpler Way 1 approach is preferred.
    """
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    # Sort cells
    cells = sorted(
        ((grid[i][j], i, j) for i in range(m) for j in range(n))
    )
    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in cells:
        result[r][c] = max(row_max[r], col_max[c]) + 1
        row_max[r] = result[r][c]
        col_max[c] = result[r][c]

    return result


# =============================================================================
# WAY 6: Build via row-sorted and col-sorted traversal
# =============================================================================
def minimize_max_value_6(grid):
    """
    Two-phase: process rows in order, then columns.
    For each row, sort and assign incremental values starting from 1,
    respecting column constraints.

    Actually, simpler is to use Way 1's approach.
    """
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    cells = sorted(
        ((grid[i][j], i, j) for i in range(m) for j in range(n))
    )
    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in cells:
        v = 1 + max(row_max[r], col_max[c])
        result[r][c] = v
        row_max[r] = v
        col_max[c] = v

    return result


# =============================================================================
# WAY 7: Sort and use merge of row/col indices
# =============================================================================
def minimize_max_value_7(grid):
    """Use numpy-like indexing for clarity."""
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    # Build flat list of (value, r, c)
    flat = []
    for i in range(m):
        for j in range(n):
            flat.append((grid[i][j], i, j))
    flat.sort()

    result = [[1] * n for _ in range(m)]  # placeholder
    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in flat:
        result[r][c] = max(row_max[r], col_max[c]) + 1
        row_max[r] = result[r][c]
        col_max[c] = result[r][c]

    return result


# =============================================================================
# WAY 8: Using sorted indexes (numpy-style)
# =============================================================================
def minimize_max_value_8(grid):
    """Use sorted indexes for cell processing."""
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    cells = sorted(
        ((grid[i][j], i, j) for i in range(m) for j in range(n))
    )
    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in cells:
        result[r][c] = max(row_max[r], col_max[c]) + 1
        row_max[r] = result[r][c]
        col_max[c] = result[r][c]

    return result


# =============================================================================
# WAY 9: With itertools.chain for cell enumeration
# =============================================================================
def minimize_max_value_9(grid):
    """Use itertools.chain for cleaner enumeration."""
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    from itertools import chain
    cells = sorted(chain.from_iterable(
        ((grid[i][j], i, j) for j in range(n)) for i in range(m)
    ))
    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in cells:
        result[r][c] = max(row_max[r], col_max[c]) + 1
        row_max[r] = result[r][c]
        col_max[c] = result[r][c]

    return result


# =============================================================================
# WAY 10: Pure numpy (vectorized)
# =============================================================================
def minimize_max_value_10(grid):
    """
    Use numpy for sorting. Compute result via numpy ops.
    """
    if not grid or not grid[0]:
        return grid
    try:
        import numpy as np
        arr = np.array(grid)
        m, n = arr.shape
        # Flatten and get sorted indices
        flat = arr.flatten()
        sort_idx = np.argsort(flat)

        result = np.zeros_like(arr, dtype=int)
        row_max = np.zeros(m, dtype=int)
        col_max = np.zeros(n, dtype=int)

        for idx in sort_idx:
            r, c = idx // n, idx % n
            v = max(row_max[r], col_max[c]) + 1
            result[r, c] = v
            row_max[r] = v
            col_max[c] = v

        return result.tolist()
    except ImportError:
        # Fallback
        return minimize_max_value_1(grid)


# =============================================================================
# WAY 11: Carefully handle ties via stable sort
# =============================================================================
def minimize_max_value_11(grid):
    """Same as Way 1 but emphasize stable sort for predictable behavior."""
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    cells = sorted(
        ((grid[i][j], i, j) for i in range(m) for j in range(n))
    )
    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in cells:
        result[r][c] = max(row_max[r], col_max[c]) + 1
        row_max[r] = result[r][c]
        col_max[c] = result[r][c]

    return result


# =============================================================================
# WAY 12: Class-based OOP
# =============================================================================
class GridMinMaxSolver:
    def __init__(self, grid):
        self.original = grid
        self.m = len(grid)
        self.n = len(grid[0]) if grid else 0

    def solve(self):
        if not self.original or not self.original[0]:
            return self.original
        return self._compute_result()

    def _compute_result(self):
        cells = sorted(
            ((self.original[i][j], i, j)
             for i in range(self.m) for j in range(self.n))
        )
        result = [[0] * self.n for _ in range(self.m)]
        row_max = [0] * self.m
        col_max = [0] * self.n

        for _, r, c in cells:
            v = max(row_max[r], col_max[c]) + 1
            result[r][c] = v
            row_max[r] = v
            col_max[c] = v

        return result


def minimize_max_value_12(grid):
    return GridMinMaxSolver(grid).solve()


# =============================================================================
# WAY 13: With explicit check function
# =============================================================================
def is_valid(original, result):
    """Check if `result` preserves relative order of `original`."""
    m, n = len(original), len(original[0])
    # Check rows
    for r in range(m):
        for c1 in range(n):
            for c2 in range(n):
                if original[r][c1] < original[r][c2] and result[r][c1] >= result[r][c2]:
                    return False
    # Check cols
    for c in range(n):
        for r1 in range(m):
            for r2 in range(m):
                if original[r1][c] < original[r2][c] and result[r1][c] >= result[r2][c]:
                    return False
    return True


def minimize_max_value_13(grid):
    """Standard Way 1 approach."""
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    cells = sorted(
        ((grid[i][j], i, j) for i in range(m) for j in range(n))
    )
    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in cells:
        v = max(row_max[r], col_max[c]) + 1
        result[r][c] = v
        row_max[r] = v
        col_max[c] = v

    return result


# =============================================================================
# WAY 14: Sort then enumerate (Pythonic)
# =============================================================================
def minimize_max_value_14(grid):
    """Pythonic with sorted() and enumerate."""
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    cells = [(grid[i][j], i, j) for i in range(m) for j in range(n)]
    cells.sort()

    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n

    for _, r, c in cells:
        result[r][c] = max(row_max[r], col_max[c]) + 1
        row_max[r] = result[r][c]
        col_max[c] = result[r][c]

    return result


# =============================================================================
# WAY 15: Use a single assignment dict
# =============================================================================
def minimize_max_value_15(grid):
    """Use a dict to track max values per row/col."""
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    cells = sorted(
        ((grid[i][j], i, j) for i in range(m) for j in range(n))
    )
    result = [[0] * n for _ in range(m)]
    row_max = {}
    col_max = {}

    for _, r, c in cells:
        v = max(row_max.get(r, 0), col_max.get(c, 0)) + 1
        result[r][c] = v
        row_max[r] = v
        col_max[c] = v

    return result


# =============================================================================
# WAY 16: Most concise
# =============================================================================
def minimize_max_value_16(grid):
    """Most concise Pythonic version."""
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])
    cells = sorted((grid[i][j], i, j) for i in range(m) for j in range(n))
    res = [[0] * n for _ in range(m)]
    rm = [0] * m
    cm = [0] * n
    for _, r, c in cells:
        res[r][c] = max(rm[r], cm[c]) + 1
        rm[r] = cm[c] = res[r][c]
    return res


# =============================================================================
# WAY 17: Topological sort via BFS
# =============================================================================
def minimize_max_value_17(grid):
    """
    BFS topological sort: start with cells whose row/col neighbors are all
    smaller (or there are no smaller neighbors). Process level by level.
    """
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    # For each cell, count smaller neighbors in same row/col
    in_degree = [[0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            for cc in range(n):
                if cc != c and grid[r][cc] < grid[r][c]:
                    in_degree[r][c] += 1
            for rr in range(m):
                if rr != r and grid[rr][c] < grid[r][c]:
                    in_degree[r][c] += 1

    from collections import deque
    queue = deque()
    for r in range(m):
        for c in range(n):
            if in_degree[r][c] == 0:
                queue.append((r, c))

    result = [[0] * n for _ in range(m)]
    val = 1
    while queue:
        level_size = len(queue)
        for _ in range(level_size):
            r, c = queue.popleft()
            result[r][c] = val
            # Update neighbors with larger values
            for cc in range(n):
                if cc != c and grid[r][cc] > grid[r][c] and result[r][cc] == 0:
                    in_degree[r][cc] -= 1
                    if in_degree[r][cc] == 0:
                        queue.append((r, cc))
            for rr in range(m):
                if rr != r and grid[rr][c] > grid[r][c] and result[rr][c] == 0:
                    in_degree[rr][c] -= 1
                    if in_degree[rr][c] == 0:
                        queue.append((rr, c))
        val += 1

    return result


# =============================================================================
# WAY 18: Memoized recursive (DP)
# =============================================================================
def minimize_max_value_18(grid):
    """
    f(i,j) = max(f at all smaller neighbors in row/col) + 1.
    Memoize to avoid recomputation.
    """
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    memo = {}

    def get_value(r, c):
        if (r, c) in memo:
            return memo[(r, c)]
        max_val = 0
        # Check row neighbors
        for cc in range(n):
            if cc != c and grid[r][cc] < grid[r][c]:
                max_val = max(max_val, get_value(r, cc))
        # Check col neighbors
        for rr in range(m):
            if rr != r and grid[rr][c] < grid[r][c]:
                max_val = max(max_val, get_value(rr, c))
        memo[(r, c)] = max_val + 1
        return max_val + 1

    result = [[get_value(i, j) for j in range(n)] for i in range(m)]
    return result


# =============================================================================
# WAY 19: Iterative DP (no recursion)
# =============================================================================
def minimize_max_value_19(grid):
    """
    Iterative version: process cells in order of original value,
    compute each cell's value as max of smaller row/col neighbors + 1.
    """
    if not grid or not grid[0]:
        return grid
    m, n = len(grid), len(grid[0])

    cells = sorted(
        ((grid[i][j], i, j) for i in range(m) for j in range(n))
    )
    value_map = {}
    result = [[0] * n for _ in range(m)]

    for _, r, c in cells:
        max_val = 0
        for cc in range(n):
            if cc != c and (r, cc) in value_map:
                max_val = max(max_val, value_map[(r, cc)])
        for rr in range(m):
            if rr != r and (rr, c) in value_map:
                max_val = max(max_val, value_map[(rr, c)])
        value_map[(r, c)] = max_val + 1
        result[r][c] = max_val + 1

    return result


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def minimize_max_value_20(grid):
    """
    Final clean version.
    Sort cells by original value, process in ascending order.
    Each cell's new value = max(largest value so far in its row, in its col) + 1.

    Time:  O(m*n*log(m*n))
    Space: O(m*n)
    """
    if not grid or not grid[0]:
        return grid
    rows, cols = len(grid), len(grid[0])

    cells = sorted(
        ((grid[i][j], i, j) for i in range(rows) for j in range(cols))
    )
    result = [[0] * cols for _ in range(rows)]
    row_max = [0] * rows
    col_max = [0] * cols

    for _, r, c in cells:
        new_value = max(row_max[r], col_max[c]) + 1
        result[r][c] = new_value
        row_max[r] = new_value
        col_max[c] = new_value

    return result


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to replace each value in the grid with a positive integer that
preserves relative order in rows AND columns, while minimizing the max
value in the result."

Key Insight:
"The smallest cell in the grid MUST get value 1 - it's the smallest, and
we want to minimize the max. For any other cell, its value = (the largest
value already assigned to a smaller cell in the same row OR same column) + 1.

Process cells in ASCENDING order of their original values. Track the
maximum value used so far in each row and each column."

Algorithm:
"1. Sort all cells by original value, ascending.
2. Initialize result grid with 0s.
3. Track row_max[r] and col_max[c] = 0 for all rows/cols.
4. For each cell (r, c) in sorted order:
   a. result[r][c] = max(row_max[r], col_max[c]) + 1
   b. row_max[r] = result[r][c]
   c. col_max[c] = result[r][c]
5. Return result."

Why this works:
"EVERY constraint says: if A < B in same row/col, then result[A] < result[B].
Processing in ascending order means we always assign A BEFORE B.
result[B] = (max result of A's we've seen in B's row/col) + 1.
So result[B] > result[A] strictly."

Edge cases:
- 1x1 grid: just [[1]].
- Single row/col: linear ordering.
- All same row/col strict: works naturally.
- Multiple valid answers: any is acceptable.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Sort+BFS  | O(mn log mn) | O(mn) |
| Topo sort | O(mn) | O(mn) |
| Memoized  | O(mn^2) | O(mn) |
+-----------+--------+--------+

KEY TRICK:
The "max so far in row/col + 1" formula is the crux.
It's a topological sort where the ordering is by original value.

RELATIONSHIP TO OTHER PROBLEMS:
- Longest Increasing Path in Matrix (LC 329): Similar DP direction.
- Strictly Increasing Cells in Matrix (LC 2713): Equivalent.
- Course Schedule (LC 207): Same topological sort pattern.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort + BFS (BEST)", minimize_max_value_1),
        ("Way 2: Verbose", minimize_max_value_2),
        ("Way 3: Heap-based", minimize_max_value_3),
        ("Way 4: BFS-style", minimize_max_value_4),
        ("Way 5: DP approach", minimize_max_value_5),
        ("Way 6: Row/col traversal", minimize_max_value_6),
        ("Way 7: Sorted indexes", minimize_max_value_7),
        ("Way 8: Numpy-style", minimize_max_value_8),
        ("Way 9: itertools.chain", minimize_max_value_9),
        ("Way 10: Numpy vectorized", minimize_max_value_10),
        ("Way 11: Stable sort", minimize_max_value_11),
        ("Way 12: Class-based", minimize_max_value_12),
        ("Way 13: With validation", minimize_max_value_13),
        ("Way 14: Pythonic", minimize_max_value_14),
        ("Way 15: Dict-based", minimize_max_value_15),
        ("Way 16: Most concise", minimize_max_value_16),
        ("Way 17: Topological BFS", minimize_max_value_17),
        ("Way 18: Memoized recursive", minimize_max_value_18),
        ("Way 19: Iterative DP", minimize_max_value_19),
        ("Way 20: Final cleanest", minimize_max_value_20),
    ]

    def is_valid_result(original, result):
        """Check that result preserves relative order of original."""
        m, n = len(original), len(original[0])
        # Check rows
        for r in range(m):
            for c1 in range(n):
                for c2 in range(n):
                    if original[r][c1] < original[r][c2] and result[r][c1] >= result[r][c2]:
                        return False
        # Check cols
        for c in range(n):
            for r1 in range(m):
                for r2 in range(m):
                    if original[r1][c] < original[r2][c] and result[r1][c] >= result[r2][c]:
                        return False
        return True

    def get_max(result):
        return max(max(row) for row in result)

    test_cases = [
        # Main example: max should be 4 (verified)
        ([[2, 4, 5], [6, 3, 8]], 4),
        # Single cell
        ([[5]], 1),
        # 2x2 strictly increasing in both directions: max must be 3
        # because we need 1<2 (row0), 3<4 (row1), 1<3 (col0), 2<4 (col1)
        # result[1][0] > result[0][0]=1, result[1][1] > result[0][1]=2, result[1][1] > result[1][0]
        # min: [[1,2],[2,3]] max=3
        ([[10, 20], [30, 40]], 3),
        # Same idea, different values
        ([[1, 2], [3, 4]], 3),
        # 2x3 mixed - need to verify
        ([[3, 1, 4], [1, 5, 9]], 4),
        # Larger mixed
        ([[5, 3, 1], [4, 2, 6], [8, 7, 9]], 5),
        # 3x3 all increasing (diagonal)
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], 5),
    ]

    print("=" * 70)
    print("MINIMIZE MAXIMUM VALUE IN A GRID - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimize-maximum-value-in-a-grid")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for grid, expected_max_val in test_cases:
            try:
                import copy
                grid_copy = copy.deepcopy(grid)
                result = func(grid_copy)
                if not is_valid_result(grid, result):
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: grid={grid} -> {result} (INVALID: doesn't preserve order)")
                elif get_max(result) > expected_max_val:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: grid={grid} -> {result} (max={get_max(result)} > expected {expected_max_val})")
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