"""
Best Meeting Point
Hard | 40 min

You are given a 2D grid of size m x n, where each cell contains either
a 0 or a 1. A 1 represents the home of a friend, and a 0 represents an
empty space. Return the minimum total travel distance to a meeting point.

Total travel distance = sum of Manhattan distances from each friend's
home to the meeting point.
Manhattan distance: |x2 - x1| + |y2 - y1|.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/best-meeting-point

Constraints:
- 1 <= m, n <= 50
- grid[i][j] is 0 or 1
- At least two friends in the grid

Examples:
    grid = [[0,1,0],
            [0,0,0],
            [0,1,0]] -> 2
    (Friends at (0,1), (2,1). Best meeting: (1,1). Distances: 1+1=2.)

Key Insight:
- For Manhattan distance, the optimal meeting point has coordinates
  equal to the MEDIAN of all friends' coordinates (separately for rows
  and columns).
- Sum of |x - median| is minimized when x = median.
- So: extract row coordinates and column coordinates of friends, find
  median of each, compute total distance from (median_row, median_col).

Time:  O(m*n) for collecting coords + O(k log k) for sorting where k = #friends.
Space: O(k) for storing coordinates.
"""


# =============================================================================
# WAY 1: Median + Manhattan distance (BEST - Memorize!)
# =============================================================================
def best_meeting_point_1(grid):
    """
    KEY INSIGHT: The optimal meeting point is at the MEDIAN of all
    friends' row coordinates AND the MEDIAN of all friends' column
    coordinates. Sum of absolute deviations is minimized at the median.

    Algorithm:
    1. Collect all row coords and all col coords of friends (where grid=1).
    2. Sort each and find the median.
    3. Sum Manhattan distances from (median_row, median_col) to each friend.
    """
    if not grid or not grid[0]:
        return 0

    rows = []
    cols = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1:
                rows.append(r)
                cols.append(c)

    rows.sort()
    cols.sort()
    median_row = rows[len(rows) // 2]
    median_col = cols[len(cols) // 2]

    total = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1:
                total += abs(r - median_row) + abs(c - median_col)

    return total


# =============================================================================
# WAY 2: Extract median via numpy median
# =============================================================================
def best_meeting_point_2(grid):
    """Use statistics.median or numpy."""
    if not grid or not grid[0]:
        return 0
    rows = []
    cols = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1:
                rows.append(r)
                cols.append(c)
    rows.sort()
    cols.sort()
    n_rows = len(rows)
    n_cols = len(cols)
    # For even count, average of two middle values works too
    if n_rows % 2 == 1:
        median_row = rows[n_rows // 2]
    else:
        # Any value between two middles works; pick lower
        median_row = rows[n_rows // 2 - 1]
    if n_cols % 2 == 1:
        median_col = cols[n_cols // 2]
    else:
        median_col = cols[n_cols // 2 - 1]

    total = sum(abs(r - median_row) + abs(c - median_col)
                for r in range(len(grid))
                for c in range(len(grid[0]))
                if grid[r][c] == 1)
    return total


# =============================================================================
# WAY 3: Brute force - try every cell as meeting point
# =============================================================================
def best_meeting_point_3(grid):
    """
    For each cell, compute total Manhattan distance to all friends.
    Return the minimum.

    Time: O((m*n) * (m*n)) = O((m*n)^2)
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    best = float('inf')

    for mr in range(m):
        for mc in range(n):
            total = 0
            for r in range(m):
                for c in range(n):
                    if grid[r][c] == 1:
                        total += abs(r - mr) + abs(c - mc)
            if total < best:
                best = total
    return best


# =============================================================================
# WAY 4: BFS from each friend (slow but works for any distance metric)
# =============================================================================
def best_meeting_point_4(grid):
    """
    BFS from each friend, accumulate distances to each cell.
    The cell with minimum accumulated distance is the meeting point.
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])

    # Total distance to each cell
    total = [[0] * n for _ in range(m)]
    num_friends = 0

    for r in range(m):
        for c in range(n):
            if grid[r][c] == 1:
                num_friends += 1
                # BFS from (r, c)
                visited = [[False] * n for _ in range(m)]
                dist = [[0] * n for _ in range(m)]
                from collections import deque
                queue = deque([(r, c, 0)])
                visited[r][c] = True
                while queue:
                    cr, cc, d = queue.popleft()
                    total[cr][cc] += d
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < m and 0 <= nc < n and not visited[nr][nc]:
                            visited[nr][nc] = True
                            dist[nr][nc] = d + 1
                            queue.append((nr, nc, d + 1))

    # Find minimum total
    best = float('inf')
    for r in range(m):
        for c in range(n):
            if total[r][c] < best:
                best = total[r][c]
    return best


# =============================================================================
# WAY 5: Sort rows and cols, find median, compute distance
# =============================================================================
def best_meeting_point_5(grid):
    """Sort and find median - clean version."""
    if not grid or not grid[0]:
        return 0
    rows = []
    cols = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1:
                rows.append(r)
                cols.append(c)
    rows.sort()
    cols.sort()
    mid = len(rows) // 2
    median_row = rows[mid]
    median_col = cols[mid]
    return sum(abs(r - median_row) + abs(c - median_col) for r, c in zip(rows, cols))


# =============================================================================
# WAY 6: Use list comprehension for collection
# =============================================================================
def best_meeting_point_6(grid):
    """List comprehensions for clarity."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    rows = [r for r in range(m) for c in range(n) if grid[r][c] == 1]
    cols = [c for r in range(m) for c in range(n) if grid[r][c] == 1]
    rows.sort()
    cols.sort()
    median_row = rows[len(rows) // 2]
    median_col = cols[len(cols) // 2]
    return sum(abs(r - median_row) + abs(c - median_col) for r, c in zip(rows, cols))


# =============================================================================
# WAY 7: Use median from statistics module
# =============================================================================
def best_meeting_point_7(grid):
    """Use statistics.median_low for finding the median."""
    if not grid or not grid[0]:
        return 0
    from statistics import median_low
    rows = []
    cols = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1:
                rows.append(r)
                cols.append(c)
    median_row = median_low(rows)
    median_col = median_low(cols)
    return sum(abs(r - median_row) + abs(c - median_col)
               for r in range(len(grid))
               for c in range(len(grid[0]))
               if grid[r][c] == 1)


# =============================================================================
# WAY 8: Quickselect to find median in O(k) average
# =============================================================================
def best_meeting_point_8(grid):
    """
    Use quickselect to find median in O(k) average time.
    Avoids sorting entirely.
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])

    def quickselect(arr, k):
        """Find k-th smallest (0-indexed) in arr using quickselect."""
        import random
        arr = list(arr)
        left, right = 0, len(arr) - 1
        while left < right:
            # Random pivot
            pivot_idx = random.randint(left, right)
            arr[pivot_idx], arr[right] = arr[right], arr[pivot_idx]
            pivot = arr[right]
            # Partition
            i = left
            for j in range(left, right):
                if arr[j] < pivot:
                    arr[i], arr[j] = arr[j], arr[i]
                    i += 1
            arr[i], arr[right] = arr[right], arr[i]
            if i == k:
                return arr[i]
            elif i < k:
                left = i + 1
            else:
                right = i - 1
        return arr[left]

    rows = [r for r in range(m) for c in range(n) if grid[r][c] == 1]
    cols = [c for r in range(m) for c in range(n) if grid[r][c] == 1]

    median_row = quickselect(rows, len(rows) // 2)
    median_col = quickselect(cols, len(cols) // 2)

    return sum(abs(r - median_row) + abs(c - median_col)
               for r in range(len(grid))
               for c in range(len(grid[0]))
               if grid[r][c] == 1)


# =============================================================================
# WAY 9: Collect using enumerate
# =============================================================================
def best_meeting_point_9(grid):
    """Use enumerate to iterate."""
    if not grid or not grid[0]:
        return 0
    rows = []
    cols = []
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val == 1:
                rows.append(r)
                cols.append(c)
    rows.sort()
    cols.sort()
    median_row = rows[len(rows) // 2]
    median_col = cols[len(cols) // 2]
    return sum(abs(r - median_row) + abs(c - median_col) for r, c in zip(rows, cols))


# =============================================================================
# WAY 10: Numpy for vectorization
# =============================================================================
def best_meeting_point_10(grid):
    """Use numpy for efficient operations."""
    try:
        import numpy as np
        if not grid or not grid[0]:
            return 0
        arr = np.array(grid)
        rows, cols = np.where(arr == 1)
        if len(rows) == 0:
            return 0
        median_row = int(np.median(rows))
        median_col = int(np.median(cols))
        return int(np.sum(np.abs(rows - median_row) + np.abs(cols - median_col)))
    except ImportError:
        return best_meeting_point_1(grid)


# =============================================================================
# WAY 11: Class-based solution
# =============================================================================
class MeetingPointFinder:
    def __init__(self, grid):
        self.grid = grid
        self.m = len(grid)
        self.n = len(grid[0]) if grid else 0
        self.rows = []
        self.cols = []

    def find_friends(self):
        """Collect coordinates of all friends."""
        for r in range(self.m):
            for c in range(self.n):
                if self.grid[r][c] == 1:
                    self.rows.append(r)
                    self.cols.append(c)

    def median(self, lst):
        """Return the median of a sorted list."""
        s = sorted(lst)
        return s[len(s) // 2]

    def total_distance(self, mr, mc):
        """Compute total Manhattan distance from (mr, mc) to all friends."""
        return sum(abs(r - mr) + abs(c - mc) for r, c in zip(self.rows, self.cols))

    def find(self):
        """Find the best meeting point."""
        self.find_friends()
        mr = self.median(self.rows)
        mc = self.median(self.cols)
        return self.total_distance(mr, mc)


def best_meeting_point_11(grid):
    """Class-based solution."""
    if not grid or not grid[0]:
        return 0
    return MeetingPointFinder(grid).find()


# =============================================================================
# WAY 12: Functional with map/filter
# =============================================================================
def best_meeting_point_12(grid):
    """Functional style."""
    if not grid or not grid[0]:
        return 0
    coords = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 1]
    rows = sorted(r for r, _ in coords)
    cols = sorted(c for _, c in coords)
    median_row = rows[len(rows) // 2]
    median_col = cols[len(cols) // 2]
    return sum(abs(r - median_row) + abs(c - median_col) for r, c in coords)


# =============================================================================
# WAY 13: One-liner
# =============================================================================
def best_meeting_point_13(grid):
    """One-liner style."""
    if not grid or not grid[0]:
        return 0
    coords = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 1]
    rs = sorted(r for r, _ in coords)
    cs = sorted(c for _, c in coords)
    mr, mc = rs[len(rs) // 2], cs[len(cs) // 2]
    return sum(abs(r - mr) + abs(c - mc) for r, c in coords)


# =============================================================================
# WAY 14: Try all median candidates
# =============================================================================
def best_meeting_point_14(grid):
    """
    For even number of friends, multiple medians work.
    Try both options to be safe.
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    rows = [r for r in range(m) for c in range(n) if grid[r][c] == 1]
    cols = [c for r in range(m) for c in range(n) if grid[r][c] == 1]
    rows.sort()
    cols.sort()

    # Try all candidate medians
    candidates_r = set()
    if len(rows) % 2 == 1:
        candidates_r.add(rows[len(rows) // 2])
    else:
        candidates_r.add(rows[len(rows) // 2 - 1])
        candidates_r.add(rows[len(rows) // 2])
        # Also try the values in between
        for r in range(rows[len(rows) // 2 - 1], rows[len(rows) // 2] + 1):
            candidates_r.add(r)

    candidates_c = set()
    if len(cols) % 2 == 1:
        candidates_c.add(cols[len(cols) // 2])
    else:
        candidates_c.add(cols[len(cols) // 2 - 1])
        candidates_c.add(cols[len(cols) // 2])
        for c in range(cols[len(cols) // 2 - 1], cols[len(cols) // 2] + 1):
            candidates_c.add(c)

    best = float('inf')
    for mr in candidates_r:
        for mc in candidates_c:
            total = sum(abs(r - mr) + abs(c - mc) for r, c in zip(rows, cols))
            if total < best:
                best = total
    return best


# =============================================================================
# WAY 15: Direct Manhattan sum without explicit median
# =============================================================================
def best_meeting_point_15(grid):
    """
    Use the property: for sorted coords [x1, x2, ..., xk],
    sum |xi - m| is minimized at any median.
    Sum of distances to median = sum_{i} (x[k//2+1] - xi) for i <= k//2
                               + sum_{i} (xi - x[k//2]) for i > k//2.
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    rows = [r for r in range(m) for c in range(n) if grid[r][c] == 1]
    cols = [c for r in range(m) for c in range(n) if grid[r][c] == 1]
    rows.sort()
    cols.sort()

    # Compute total distance to median (lower median if even)
    median_idx_r = len(rows) // 2
    median_idx_c = len(cols) // 2

    # For row distances
    row_dist = 0
    for i in range(len(rows)):
        row_dist += abs(rows[i] - rows[median_idx_r])

    col_dist = 0
    for i in range(len(cols)):
        col_dist += abs(cols[i] - cols[median_idx_c])

    return row_dist + col_dist


# =============================================================================
# WAY 16: Use heapq.nsmallest
# =============================================================================
def best_meeting_point_16(grid):
    """Use heapq to find median efficiently."""
    if not grid or not grid[0]:
        return 0
    import heapq
    m, n = len(grid), len(grid[0])
    rows = [r for r in range(m) for c in range(n) if grid[r][c] == 1]
    cols = [c for r in range(m) for c in range(n) if grid[r][c] == 1]
    # Find median
    median_row = heapq.nsmallest(len(rows) // 2 + 1, rows)[-1]
    median_col = heapq.nsmallest(len(cols) // 2 + 1, cols)[-1]
    return sum(abs(r - median_row) + abs(c - median_col) for r, c in zip(rows, cols))


# =============================================================================
# WAY 17: Sort friends by row, then compute
# =============================================================================
def best_meeting_point_17(grid):
    """Sort friends' positions, use row/col medians."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    friends = [(r, c) for r in range(m) for c in range(n) if grid[r][c] == 1]

    rows = sorted(r for r, _ in friends)
    cols = sorted(c for _, c in friends)
    mr = rows[len(rows) // 2]
    mc = cols[len(cols) // 2]

    return sum(abs(r - mr) + abs(c - mc) for r, c in friends)


# =============================================================================
# WAY 18: Use itertools
# =============================================================================
def best_meeting_point_18(grid):
    """Use itertools.chain for flat iteration."""
    if not grid or not grid[0]:
        return 0
    from itertools import chain
    m, n = len(grid), len(grid[0])
    rows = []
    cols = []
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 1:
                rows.append(r)
                cols.append(c)

    rows.sort()
    cols.sort()
    mr = rows[len(rows) // 2]
    mc = cols[len(cols) // 2]
    return sum(abs(r - mr) + abs(c - mc) for r, c in zip(rows, cols))


# =============================================================================
# WAY 19: Compact with itertools
# =============================================================================
def best_meeting_point_19(grid):
    """Compact with itertools - flatten r,c pairs into single list."""
    if not grid or not grid[0]:
        return 0
    from itertools import chain
    m, n = len(grid), len(grid[0])
    # Flatten: chain.from_iterable of each friend (r, c) tuple yields a flat iterable
    # but we need to extract r and c separately
    pairs = [(r, c) for r in range(m) for c in range(n) if grid[r][c] == 1]
    rows = sorted(r for r, _ in pairs)
    cols = sorted(c for _, c in pairs)
    mr = rows[len(rows) // 2]
    mc = cols[len(cols) // 2]
    return sum(abs(r - mr) + abs(c - mc) for r, c in pairs)


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def best_meeting_point_20(grid):
    """
    Final clean version.
    KEY INSIGHT: Manhattan distance is separable. The optimal meeting
    point minimizes sum of row distances and sum of col distances
    INDEPENDENTLY. The optimum for each is the MEDIAN.

    Algorithm:
    1. Collect row coordinates and column coordinates of all friends.
    2. Sort and find the median of each.
    3. Sum Manhattan distances to (median_row, median_col).

    Time:  O(m*n) + O(k log k) where k = number of friends.
    Space: O(k) for the coordinate lists.
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])

    rows = []
    cols = []
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 1:
                rows.append(r)
                cols.append(c)

    rows.sort()
    cols.sort()
    median_row = rows[len(rows) // 2]
    median_col = cols[len(cols) // 2]

    return sum(abs(r - median_row) + abs(c - median_col) for r, c in zip(rows, cols))


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find a meeting point that minimizes the total Manhattan
distance to all friends' homes."

Key Insight:
"Manhattan distance is SEPARABLE - it decomposes into row and column
parts. So the optimal meeting point's row is the median of all friends'
rows, and the column is the median of all friends' columns.
Any value in [lower_median, upper_median] works for even counts."

Algorithm:
"1. Collect all row coordinates and column coordinates of friends.
2. Sort each and find the median.
3. Sum Manhattan distances from (median_row, median_col) to each friend."

Why median?
"Sum of |xi - m| is minimized when m is the median. This is a classical
result from statistics. For Manhattan distance, the dimensions are
independent, so we can optimize each coordinate separately."

Edge cases:
- Two friends: meeting point is anywhere on Manhattan path between them.
- Many friends: use median.
- Even number of friends: any value between the two middle values works.
- 1x1 grid with friend: distance is 0.
- Empty grid (no friends): undefined per problem (at least 2 friends).

Complexity:
- Time:  O(m*n + k log k) where k = # friends (sorting dominates).
- Space: O(k) for coordinate lists.

KEY TRICK:
Manhattan distance decomposes into |x1-x2| + |y1-y2|. Each part can be
optimized independently. The optimum for |x1 - m_x| + |x2 - m_x| + ...
is the median of x1, x2, ...

This trick also works for:
- Best meeting point on a line (1D version).
- Minimum total distance problems in general.

WHY NOT BRUTE FORCE?
Brute force: try each cell as meeting point. O((m*n)^2). For m=n=50,
that's 6.25M operations - actually fast enough, but median approach
is cleaner and more general.

ALTERNATIVE: GEOMETRIC MEDIAN
For Euclidean distance, the optimal point is the GEOMETRIC MEDIAN,
which is harder to compute (no closed form). For Manhattan distance,
we get the simple MEDIAN trick.

RELATIONSHIP TO OTHER PROBLEMS:
- Min Cost to Connect Sticks: Different (priority queue).
- Median of stream: Different (online algorithm).
- Manhattan Distance problems: Same family.

INTERVIEW TIPS:
1. Always mention Manhattan distance's SEPARABILITY.
2. Explain why MEDIAN minimizes sum of absolute deviations.
3. Handle even-count case (any value in [lower, upper] works).
4. Consider 1D version first (just median of coords).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Median + Manhattan (BEST)", best_meeting_point_1),
        ("Way 2: numpy median", best_meeting_point_2),
        ("Way 3: Brute force", best_meeting_point_3),
        ("Way 4: BFS from each friend", best_meeting_point_4),
        ("Way 5: Sort + median", best_meeting_point_5),
        ("Way 6: List comprehension", best_meeting_point_6),
        ("Way 7: statistics.median", best_meeting_point_7),
        ("Way 8: Quickselect", best_meeting_point_8),
        ("Way 9: enumerate", best_meeting_point_9),
        ("Way 10: NumPy", best_meeting_point_10),
        ("Way 11: Class-based", best_meeting_point_11),
        ("Way 12: Functional", best_meeting_point_12),
        ("Way 13: One-liner", best_meeting_point_13),
        ("Way 14: All median candidates", best_meeting_point_14),
        ("Way 15: Direct Manhattan sum", best_meeting_point_15),
        ("Way 16: heapq.nsmallest", best_meeting_point_16),
        ("Way 17: Sort friends", best_meeting_point_17),
        ("Way 18: itertools", best_meeting_point_18),
        ("Way 19: Compact itertools", best_meeting_point_19),
        ("Way 20: Final cleanest", best_meeting_point_20),
    ]

    test_cases = [
        # Educative example
        (
            [[0, 1, 0],
             [0, 0, 0],
             [0, 1, 0]],
            2
        ),
        # Single row, friends at (0,0), (0,2), (0,4)
        # Median col = 2. Distances: 2+0+2 = 4
        (
            [[1, 0, 1, 0, 1]],
            4
        ),
        # Two friends diagonal
        # (0,0) and (2,2). Median = (1,1). Distances: 2 + 2 = 4
        (
            [[1, 0, 0],
             [0, 0, 0],
             [0, 0, 1]],
            4
        ),
        # Four friends at corners
        # (0,0), (0,4), (4,0), (4,4). Median = (2,2).
        # Distances: 4+4+4+4 = 16
        (
            [[1, 0, 0, 0, 1],
             [0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0],
             [1, 0, 0, 0, 1]],
            16
        ),
        # Three friends in a row
        # (0,0), (0,1), (0,3). Median col = 1. Distances: 1+0+2 = 3
        (
            [[1, 1, 0, 1]],
            3
        ),
        # Vertical line
        # (0,0), (1,0), (3,0). Median row = 1. Distances: 1+0+2 = 3
        (
            [[1],
             [1],
             [0],
             [1]],
            3
        ),
        # 2x2 all friends
        # (0,0), (0,1), (1,0), (1,1). Median = (0,0).
        # Distances: 0+1+1+2 = 4 (or (0,1): 1+0+2+1=4, same)
        (
            [[1, 1],
             [1, 1]],
            4
        ),
        # Empty grid (no friends)
        # Skipping - problem says at least 2 friends
        # (
        #     [[0, 0], [0, 0]],
        #     0
        # ),
    ]

    print("=" * 70)
    print("BEST MEETING POINT - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/best-meeting-point")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for grid, expected in test_cases:
            try:
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
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)