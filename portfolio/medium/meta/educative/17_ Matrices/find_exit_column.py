"""
Where Will the Ball Fall
Medium | 30 min

You have n balls and a 2D grid of size m x n representing a box.
The box is open on the top and bottom. Each cell has a diagonal:
- 1 redirects the ball to the right
- -1 redirects the ball to the left

Drop n balls at each column's top. A ball gets STUCK if:
1. It hits a V-shaped pattern between two adjacent cells (current
   cell redirects toward adjacent cell, but adjacent redirects
   back), OR
2. A cell redirects the ball into a wall (column < 0 or >= n).

Return an array of size n. result[x] = exit column if ball from col x
exits, or -1 if stuck.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/where-will-the-ball-fall

Constraints:
- 1 <= m, n <= 100
- grid[i][j] is 1 or -1

Examples:
    [[1, 1],
     [-1, -1]] -> [0, -1]
    Ball 0: (0,0)=1→right→(1,1)=-1→left→col 0 (NOT stuck, exits at col 0).
    Ball 1: (0,1)=1→right→wall→STUCK.

Key Insight:
- At each cell (r, c) with value v:
  - v == 1: ball moves to (r+1, c+1)
  - v == -1: ball moves to (r+1, c-1)
- Stuck if:
  - New column is out of bounds, OR
  - V-shape: current v and grid[r][c+v] are opposite (1 and -1).
- Otherwise continue.

Time:  O(m*n) - simulate each ball through m rows.
Space: O(1) - just the result array.
"""


# =============================================================================
# WAY 1: Simulate each ball (BEST - Memorize!)
# =============================================================================
def find_exit_column_1(grid):
    """
    For each starting column, simulate the ball's path.
    At each cell, move left/right based on value.
    Return exit column or -1 if stuck.
    """
    if not grid or not grid[0]:
        return []
    m, n = len(grid), len(grid[0])
    result = []

    for start_col in range(n):
        col = start_col
        stuck = False
        for row in range(m):
            # Get direction at current cell
            direction = grid[row][col]
            # Compute next column
            next_col = col + direction
            # Check wall
            if next_col < 0 or next_col >= n:
                stuck = True
                break
            # Check V-shape
            if grid[row][next_col] != direction:
                stuck = True
                break
            # Move
            col = next_col

        result.append(-1 if stuck else col)

    return result


# =============================================================================
# WAY 2: Verbose version with comments
# =============================================================================
def find_exit_column_2(grid):
    """More explicit."""
    if not grid or not grid[0]:
        return []
    m, n = len(grid), len(grid[0])
    result = []

    for start in range(n):
        c = start
        ok = True
        for r in range(m):
            v = grid[r][c]
            # Move left or right
            new_c = c + v
            # Wall check
            if not (0 <= new_c < n):
                ok = False
                break
            # V-shape check
            if grid[r][new_c] == -v:
                ok = False
                break
            c = new_c
        result.append(c if ok else -1)
    return result


# =============================================================================
# WAY 3: Helper function for simulation
# =============================================================================
def find_exit_column_3(grid):
    """Use helper function for one ball's path."""
    if not grid or not grid[0]:
        return []

    def simulate(start_col):
        col = start_col
        for row in range(len(grid)):
            direction = grid[row][col]
            next_col = col + direction
            if next_col < 0 or next_col >= len(grid[0]):
                return -1
            if grid[row][next_col] != direction:
                return -1
            col = next_col
        return col

    return [simulate(c) for c in range(len(grid[0]))]


# =============================================================================
# WAY 4: Use enumerate over start columns
# =============================================================================
def find_exit_column_4(grid):
    """Enumerate start columns."""
    if not grid or not grid[0]:
        return []
    n = len(grid[0])
    result = [-1] * n

    for start_col in range(n):
        col = start_col
        for row in range(len(grid)):
            d = grid[row][col]
            new_col = col + d
            if new_col < 0 or new_col >= n:
                col = -1
                break
            if grid[row][new_col] != d:
                col = -1
                break
            col = new_col
        result[start_col] = col

    return result


# =============================================================================
# WAY 5: Recursive simulation
# =============================================================================
def find_exit_column_5(grid):
    """Recursive simulation per ball."""
    if not grid or not grid[0]:
        return []
    m, n = len(grid), len(grid[0])

    def drop(col, row):
        if row == m:
            return col
        d = grid[row][col]
        new_col = col + d
        if new_col < 0 or new_col >= n:
            return -1
        if grid[row][new_col] != d:
            return -1
        return drop(new_col, row + 1)

    return [drop(c, 0) for c in range(n)]


# =============================================================================
# WAY 6: Class-based with helper
# =============================================================================
class BallDropper:
    def __init__(self, grid):
        self.grid = grid
        self.m = len(grid)
        self.n = len(grid[0]) if grid else 0

    def drop_one(self, col):
        """Simulate one ball. Return exit col or -1."""
        for row in range(self.m):
            d = self.grid[row][col]
            new_col = col + d
            if new_col < 0 or new_col >= self.n:
                return -1
            if self.grid[row][new_col] != d:
                return -1
            col = new_col
        return col

    def drop_all(self):
        """Drop balls from all columns."""
        return [self.drop_one(c) for c in range(self.n)]


def find_exit_column_6(grid):
    """Class-based."""
    if not grid or not grid[0]:
        return []
    return BallDropper(grid).drop_all()


# =============================================================================
# WAY 7: Use walrus operator
# =============================================================================
def find_exit_column_7(grid):
    """Use walrus operator (Python 3.8+)."""
    if not grid or not grid[0]:
        return []
    m, n = len(grid), len(grid[0])
    result = []

    for start_col in range(n):
        col = start_col
        stuck = False
        for row in range(m):
            if ((next_col := col + grid[row][col]) < 0
                or next_col >= n
                or grid[row][next_col] != grid[row][col]):
                stuck = True
                break
            col = next_col
        result.append(-1 if stuck else col)

    return result


# =============================================================================
# WAY 8: Lambda inside list comprehension
# =============================================================================
def find_exit_column_8(grid):
    """Use lambda."""
    if not grid or not grid[0]:
        return []
    n = len(grid[0])

    def drop(c):
        for r in range(len(grid)):
            d = grid[r][c]
            nc = c + d
            if nc < 0 or nc >= n or grid[r][nc] != d:
                return -1
            c = nc
        return c

    return list(map(drop, range(n)))


# =============================================================================
# WAY 9: Use map for direction lookup
# =============================================================================
def find_exit_column_9(grid):
    """Use map/lambda for direction."""
    if not grid or not grid[0]:
        return []
    n = len(grid[0])
    result = []

    for start_col in range(n):
        col = start_col
        for row in range(len(grid)):
            d = grid[row][col]
            nc = col + d
            # Check wall
            if not (0 <= nc < n):
                col = -1
                break
            # Check V-shape
            if grid[row][nc] == -d:
                col = -1
                break
            col = nc
        result.append(col)

    return result


# =============================================================================
# WAY 10: Early return with sentinels
# =============================================================================
def find_exit_column_10(grid):
    """Use sentinel for stuck detection."""
    if not grid or not grid[0]:
        return []
    n = len(grid[0])
    result = []

    for start_col in range(n):
        col = start_col
        for row in range(len(grid)):
            d = grid[row][col]
            nc = col + d
            if nc < 0 or nc >= n or grid[row][nc] != d:
                col = -1
                break
            col = nc
        result.append(col)

    return result


# =============================================================================
# WAY 11: Use itertools for batch simulation
# =============================================================================
def find_exit_column_11(grid):
    """Use itertools."""
    if not grid or not grid[0]:
        return []
    from itertools import chain
    n = len(grid[0])

    def drop(c):
        for r in range(len(grid)):
            d = grid[r][c]
            nc = c + d
            if nc < 0 or nc >= n or grid[r][nc] != d:
                return -1
            c = nc
        return c

    return [drop(c) for c in chain(range(n))]


# =============================================================================
# WAY 12: Numpy vectorized
# =============================================================================
def find_exit_column_12(grid):
    """Use numpy for vectorized operations."""
    try:
        import numpy as np
        if not grid or not grid[0]:
            return []
        arr = np.array(grid)
        m, n = arr.shape
        result = []

        for start in range(n):
            col = start
            stuck = False
            for row in range(m):
                d = arr[row, col]
                nc = col + d
                if nc < 0 or nc >= n:
                    stuck = True
                    break
                if arr[row, nc] != d:
                    stuck = True
                    break
                col = nc
            result.append(-1 if stuck else col)

        return result
    except ImportError:
        return find_exit_column_1(grid)


# =============================================================================
# WAY 13: Generator-based
# =============================================================================
def find_exit_column_13(grid):
    """Generator-based approach."""
    if not grid or not grid[0]:
        return []
    n = len(grid[0])

    def drop_gen(c):
        col = c
        for row in range(len(grid)):
            d = grid[row][col]
            nc = col + d
            if nc < 0 or nc >= n or grid[row][nc] != d:
                return -1
            col = nc
        return col

    return [drop_gen(c) for c in range(n)]


# =============================================================================
# WAY 14: Use try/except for stuck handling
# =============================================================================
def find_exit_column_14(grid):
    """Use exception for stuck."""
    if not grid or not grid[0]:
        return []

    class StuckException(Exception):
        pass

    def drop(c):
        try:
            for r in range(len(grid)):
                d = grid[r][c]
                nc = c + d
                if nc < 0 or nc >= len(grid[0]) or grid[r][nc] != d:
                    raise StuckException
                c = nc
            return c
        except StuckException:
            return -1

    return [drop(c) for c in range(len(grid[0]))]


# =============================================================================
# WAY 15: Use functools.reduce
# =============================================================================
def find_exit_column_15(grid):
    """Use reduce for path computation."""
    if not grid or not grid[0]:
        return []
    from functools import reduce
    n = len(grid[0])

    def drop(c):
        def step(col, row):
            if col == -1:
                return col
            d = grid[row][col]
            nc = col + d
            if nc < 0 or nc >= n or grid[row][nc] != d:
                return -1
            return nc

        return reduce(step, range(len(grid)), c)

    return [drop(c) for c in range(n)]


# =============================================================================
# WAY 16: Use while loop with explicit flag
# =============================================================================
def find_exit_column_16(grid):
    """Use while loop with flag."""
    if not grid or not grid[0]:
        return []
    m, n = len(grid), len(grid[0])
    result = []

    for start in range(n):
        col = start
        row = 0
        while row < m:
            d = grid[row][col]
            nc = col + d
            if nc < 0 or nc >= n:
                col = -1
                break
            if grid[row][nc] != d:
                col = -1
                break
            col = nc
            row += 1
        result.append(col)

    return result


# =============================================================================
# WAY 17: Vectorized across all starts
# =============================================================================
def find_exit_column_17(grid):
    """Process all start columns in batch (one row at a time)."""
    if not grid or not grid[0]:
        return []
    m, n = len(grid), len(grid[0])
    # cols[c] = current column of ball that started at c, or -1 if stuck
    cols = list(range(n))

    for row in range(m):
        new_cols = list(cols)
        for c in range(n):
            if cols[c] == -1:
                continue
            cur = cols[c]
            d = grid[row][cur]
            nc = cur + d
            if nc < 0 or nc >= n or grid[row][nc] != d:
                new_cols[c] = -1
            else:
                new_cols[c] = nc
        cols = new_cols

    return cols


# =============================================================================
# WAY 18: Use caching for memoization
# =============================================================================
def find_exit_column_18(grid):
    """Use caching (memoization for repeated calls)."""
    if not grid or not grid[0]:
        return []
    from functools import lru_cache

    n = len(grid[0])

    @lru_cache(maxsize=None)
    def drop(col):
        cur = col
        for r in range(len(grid)):
            d = grid[r][cur]
            nc = cur + d
            if nc < 0 or nc >= n or grid[r][nc] != d:
                return -1
            cur = nc
        return cur

    return [drop(c) for c in range(n)]


# =============================================================================
# WAY 19: One-liner with nested function
# =============================================================================
def find_exit_column_19(grid):
    """Compact version."""
    if not grid or not grid[0]:
        return []
    n = len(grid[0])

    def drop(c):
        for r in range(len(grid)):
            d = grid[r][c]
            nc = c + d
            if nc < 0 or nc >= n or grid[r][nc] != d:
                return -1
            c = nc
        return c

    return [drop(c) for c in range(n)]


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def find_exit_column_20(grid):
    """
    Final clean version.
    Simulate each ball's path through the grid.
    At each cell (r, c) with value v:
    - v == 1: ball moves to (r+1, c+1)
    - v == -1: ball moves to (r+1, c-1)
    - Stuck if next column is out of bounds OR V-shape with neighbor.

    Time:  O(m*n) - simulate each of n balls through m rows.
    Space: O(n) for result.
    """
    if not grid or not grid[0]:
        return []
    m, n = len(grid), len(grid[0])

    def drop(start_col):
        col = start_col
        for row in range(m):
            d = grid[row][col]
            next_col = col + d
            if next_col < 0 or next_col >= n or grid[row][next_col] != d:
                return -1
            col = next_col
        return col

    return [drop(c) for c in range(n)]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to simulate n balls dropping through an m x n grid.
Each cell redirects the ball left (-1) or right (1). A ball gets
stuck at walls or V-shaped patterns."

Key Insight:
"At each cell (r, c) with value v:
- v == 1: ball goes to (r+1, c+1) [right]
- v == -1: ball goes to (r+1, c-1) [left]
- Stuck if: new column out of bounds, OR grid[r][c+v] == -v (V-shape).
  V-shape: current cell redirects toward neighbor, but neighbor
  redirects back - they form a V."

Algorithm:
"1. For each starting column c in [0, n):
2.   col = c
4.   For each row r in [0, m):
5.     d = grid[r][col]
6.     next_col = col + d
7.     If next_col < 0 or next_col >= n: stuck, set result[c] = -1, break
8.     If grid[r][next_col] != d: V-shape, set result[c] = -1, break
9.     col = next_col
10.  If completed all rows: result[c] = col
11. Return result."

Why V-shape detection works:
"When grid[r][c]=1 (right) and grid[r][c+1]=-1 (left), the ball at c
moves right to c+1, but cell at c+1 wants to push ball back to c.
This forms a V where balls bounce between them - stuck."

Edge cases:
- 1x1 grid with grid[0][0]=1: ball at col 0 moves right to col 1 (wall). Stuck.
- 1x1 grid with grid[0][0]=-1: ball at col 0 moves left to col -1 (wall). Stuck.
- All 1s: ball shifts right each row. Exits at col start + m.
- All -1s: ball shifts left each row. Exits at col start - m.
- Alternating 1,-1: many V-shapes, most balls stuck.

Complexity:
- Time:  O(m*n) - n balls through m rows each.
- Space: O(n) - result array.

KEY TRICK:
V-shape check: grid[r][next_col] != grid[r][col]. If they don't match,
the ball would be redirected back - stuck.

V-SHAPE PATTERN:
\\ /   - 1 then -1 -> V from above (\\).
/ \\   - -1 then 1 -> inverted V (\\ / above).

Both are "V-shape" patterns where balls get stuck.

MEMORY NOTE: We're given m x n <= 100 x 100 = 10000 cells. Memory is
not a constraint for any approach.

ALTERNATIVE: BFS
Could model as graph where nodes are (row, col) and edges follow
the redirects. But simulation is simpler.

RELATIONSHIP TO OTHER PROBLEMS:
- Rotting Oranges (LC 994): Multi-source BFS, different rules.
- Snake Game: Different movement.
- Matrix traversal in general: Same family.

INTERVIEW TIPS:
1. Clarify "V-shape" - what makes a V?
   - Adjacent cells redirect AWAY from each other.
2. Handle the edge case: ball at wall.
3. Mention that simulation is the simplest approach.
4. Discuss time complexity clearly: n balls * m rows each.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Simulate each ball (BEST)", find_exit_column_1),
        ("Way 2: Verbose version", find_exit_column_2),
        ("Way 3: Helper function", find_exit_column_3),
        ("Way 4: enumerate start cols", find_exit_column_4),
        ("Way 5: Recursive", find_exit_column_5),
        ("Way 6: Class-based", find_exit_column_6),
        ("Way 7: Walrus operator", find_exit_column_7),
        ("Way 8: Lambda", find_exit_column_8),
        ("Way 9: Direction handling", find_exit_column_9),
        ("Way 10: Early return sentinel", find_exit_column_10),
        ("Way 11: itertools", find_exit_column_11),
        ("Way 12: Numpy", find_exit_column_12),
        ("Way 13: Generator", find_exit_column_13),
        ("Way 14: Exception handling", find_exit_column_14),
        ("Way 15: functools.reduce", find_exit_column_15),
        ("Way 16: While loop flag", find_exit_column_16),
        ("Way 17: Batch process", find_exit_column_17),
        ("Way 18: LRU cache", find_exit_column_18),
        ("Way 19: Compact nested fn", find_exit_column_19),
        ("Way 20: Final cleanest", find_exit_column_20),
    ]

    test_cases = [
        # Ball 0: (0,0)=1 -> col 1. (1,1)=-1 -> col 0. Exit col 0. NOT stuck!
        # Ball 1: (0,1)=1 -> col 2 (wall). Stuck.
        # The "Educative quiz" answer [-1,-1] is incorrect; the correct trace gives [0,-1].
        ([[1, 1],
          [-1, -1]], [0, -1]),
        # 2x3 all 1s: ball shifts right each row
        # Col 0: 0->1->2. Exit col 2.
        # Col 1: 1->2->3 (wall). Stuck.
        # Col 2: 2->3 (wall). Stuck.
        ([[1, 1, 1],
          [1, 1, 1]], [2, -1, -1]),
        # 2x3 all -1s: ball shifts left each row
        # Col 0: 0->-1 (wall). Stuck.
        # Col 1: 1->0->-1 (wall). Stuck.
        # Col 2: 2->1->0. Exit col 0.
        ([[-1, -1, -1],
          [-1, -1, -1]], [-1, -1, 0]),
        # 2x2 all 1s: n=2 means col 2 is wall
        # Col 0: 0->1->2 (wall). Stuck.
        # Col 1: 1->2 (wall). Stuck.
        ([[1, 1],
          [1, 1]], [-1, -1]),
        # Simple 1x1
        ([[1]], [-1]),
        ([[-1]], [-1]),
        # V-shape pattern in 2x2
        # Col 0: 1(0,0)->col 1. V-shape with grid[0][1]=-1. Stuck.
        # Col 1: -1(0,1)->col 0. V-shape with grid[0][0]=1. Stuck.
        ([[1, -1],
          [-1, 1]], [-1, -1]),
        # 3x3 all 1s: ball shifts right, all stuck at wall
        # Col 0: 0->1->2->3 (wall). Stuck.
        # Col 1: 1->2->3 (wall). Stuck.
        # Col 2: 2->3 (wall). Stuck.
        ([[1, 1, 1],
          [1, 1, 1],
          [1, 1, 1]], [-1, -1, -1]),
        # 3x3 all -1s: ball shifts left, all stuck at wall
        # Col 0: 0->-1 (wall). Stuck.
        # Col 1: 1->0->-1 (wall). Stuck.
        # Col 2: 2->1->0->-1 (wall). Stuck.
        ([[-1, -1, -1],
          [-1, -1, -1],
          [-1, -1, -1]], [-1, -1, -1]),
        # Empty grid
        ([], []),
        # 1x3: ball shifts once based on direction
        # Col 0: 1 -> col 1. Exit col 1.
        # Col 1: 1 -> col 2. Exit col 2.
        # Col 2: 1 -> col 3 (wall). Stuck.
        ([[1, 1, 1]], [1, 2, -1]),
        # 2x2 V-shape grid (different from above)
        # [[1,-1],
        #  [1,1]]
        # Col 0: 1(0,0)->col 1. V-shape with grid[0][1]=-1. Stuck.
        # Col 1: -1(0,1)->col 0. grid[0][0]=1 != -1. V-shape! Stuck.
        # Wait, V-shape check: grid[0][next_col] != d. d=-1, grid[0][0]=1. 1 != -1. Yes, V-shape. Stuck.
        # Col 0 trace: d=1, next_col=1, grid[0][1]=-1. -1 != 1. V-shape. Stuck.
        # Col 1 trace: d=-1, next_col=0, grid[0][0]=1. 1 != -1. V-shape. Stuck.
        ([[1, -1],
          [1, 1]], [-1, -1]),
    ]

    print("=" * 70)
    print("WHERE WILL THE BALL FALL - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/where-will-the-ball-fall")
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