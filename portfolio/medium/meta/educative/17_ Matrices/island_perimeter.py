"""
Island Perimeter
Easy | 15 min

You are given a grid with dimensions row x col, where each cell is land (1)
or water (0). Cells are connected only horizontally/vertically. The grid
contains exactly one island (no lakes), surrounded by water.

Calculate the perimeter of the island.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/island-perimeter

Constraints:
- 1 <= rows, cols <= 100
- grid[i][j] is 0 or 1
- Exactly one island, no lakes.

Examples:
    [[0,1,0,0],
     [1,1,1,0],
     [0,1,0,0],
     [1,1,0,0]] -> 16

    [[1]] -> 4

    [[1,0]] -> 4

Key Insight:
Two equivalent approaches:
1. Count 4*land - 2*shared_edges. Each shared edge is counted twice (once
   per cell), so subtract 2 per shared edge.
2. For each land cell, count its 4 sides. Each side is +1 if neighbor is
   water or out of bounds.

For each land cell:
- Start with 4 sides.
- For each direction (up/down/left/right):
  - If neighbor is also land (and in bounds), this side is internal (-1).
  - Otherwise (water or wall), this side is perimeter (+1).

Time:  O(m*n).
Space: O(1) extra.
"""


# =============================================================================
# WAY 1: Count sides per cell (BEST - Memorize!)
# =============================================================================
def island_perimeter_1(grid):
    """
    For each land cell, check 4 sides. Add 1 per side that's water or wall.
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    perimeter = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                # Up
                if i == 0 or grid[i - 1][j] == 0:
                    perimeter += 1
                # Down
                if i == m - 1 or grid[i + 1][j] == 0:
                    perimeter += 1
                # Left
                if j == 0 or grid[i][j - 1] == 0:
                    perimeter += 1
                # Right
                if j == n - 1 or grid[i][j + 1] == 0:
                    perimeter += 1
    return perimeter


# =============================================================================
# WAY 2: Verbose version with directions list
# =============================================================================
def island_perimeter_2(grid):
    """Use a directions list for cleaner code."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    perimeter = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if ni < 0 or ni >= m or nj < 0 or nj >= n or grid[ni][nj] == 0:
                        perimeter += 1
    return perimeter


# =============================================================================
# WAY 3: 4*land - 2*shared_edges formula
# =============================================================================
def island_perimeter_3(grid):
    """
    Each land cell contributes 4 sides. Each pair of adjacent land cells
    shares one edge, removing 2 from the total (one from each cell).
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    land = 0
    shared = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                land += 1
                # Check right neighbor
                if j + 1 < n and grid[i][j + 1] == 1:
                    shared += 1
                # Check down neighbor
                if i + 1 < m and grid[i + 1][j] == 1:
                    shared += 1
    return 4 * land - 2 * shared


# =============================================================================
# WAY 4: DFS recursion
# =============================================================================
def island_perimeter_4(grid):
    """
    DFS from any land cell. Visit neighbors, count edges between
    land and water (or wall).
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    visited = [[False] * n for _ in range(m)]
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def dfs(i, j):
        # If out of bounds or water, this contributes 1 to perimeter
        if i < 0 or i >= m or j < 0 or j >= n or grid[i][j] == 0:
            return 1
        # If already visited, skip
        if visited[i][j]:
            return 0
        visited[i][j] = True
        total = 0
        for di, dj in directions:
            total += dfs(i + di, j + dj)
        return total

    # Find any land cell to start DFS
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                return dfs(i, j)
    return 0


# =============================================================================
# WAY 5: BFS iterative
# =============================================================================
def island_perimeter_5(grid):
    """BFS from any land cell."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    visited = [[False] * n for _ in range(m)]
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque

    # Find any land cell
    start = None
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                start = (i, j)
                break
        if start:
            break
    if not start:
        return 0

    perimeter = 0
    queue = deque([start])
    visited[start[0]][start[1]] = True

    while queue:
        i, j = queue.popleft()
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if ni < 0 or ni >= m or nj < 0 or nj >= n or grid[ni][nj] == 0:
                perimeter += 1
            elif not visited[ni][nj]:
                visited[ni][nj] = True
                queue.append((ni, nj))

    return perimeter


# =============================================================================
# WAY 6: enumerate
# =============================================================================
def island_perimeter_6(grid):
    """Enumerate for iteration."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    perimeter = 0
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            if cell == 1:
                if i == 0 or grid[i - 1][j] == 0:
                    perimeter += 1
                if i == m - 1 or grid[i + 1][j] == 0:
                    perimeter += 1
                if j == 0 or grid[i][j - 1] == 0:
                    perimeter += 1
                if j == n - 1 or grid[i][j + 1] == 0:
                    perimeter += 1
    return perimeter


# =============================================================================
# WAY 7: NumPy vectorized
# =============================================================================
def island_perimeter_7(grid):
    """Use numpy for vectorized computation."""
    try:
        import numpy as np
        if not grid or not grid[0]:
            return 0
        g = np.array(grid)
        # Pad with zeros around the grid (so out-of-bounds == water)
        padded = np.pad(g, 1, mode='constant', constant_values=0)
        # For each cell, check 4 neighbors
        top = padded[:-2, 1:-1]
        bottom = padded[2:, 1:-1]
        left = padded[1:-1, :-2]
        right = padded[1:-1, 2:]
        # A side is perimeter if current cell is land and neighbor is water
        # Sum across all directions where this is true
        perimeter = (
            np.sum((g == 1) & (top == 0)) +
            np.sum((g == 1) & (bottom == 0)) +
            np.sum((g == 1) & (left == 0)) +
            np.sum((g == 1) & (right == 0))
        )
        return int(perimeter)
    except ImportError:
        return island_perimeter_1(grid)


# =============================================================================
# WAY 8: Generator + sum
# =============================================================================
def island_perimeter_8(grid):
    """Sum using a generator expression."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])

    def count_perimeter():
        for i in range(m):
            for j in range(n):
                if grid[i][j] == 1:
                    if i == 0 or grid[i - 1][j] == 0:
                        yield 1
                    if i == m - 1 or grid[i + 1][j] == 0:
                        yield 1
                    if j == 0 or grid[i][j - 1] == 0:
                        yield 1
                    if j == n - 1 or grid[i][j + 1] == 0:
                        yield 1

    return sum(count_perimeter())


# =============================================================================
# WAY 9: Compact with directions and sum
# =============================================================================
def island_perimeter_9(grid):
    """Compact using sum() with directions."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def sides(i, j):
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if ni < 0 or ni >= m or nj < 0 or nj >= n:
                yield 1
            elif grid[ni][nj] == 0:
                yield 1

    return sum(sum(sides(i, j)) for i in range(m) for j in range(n) if grid[i][j] == 1)


# =============================================================================
# WAY 10: All four directions in one expression
# =============================================================================
def island_perimeter_10(grid):
    """Compact single-line check per cell."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    perimeter = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                # Add 1 for each side that is water or wall
                perimeter += (i == 0 or grid[i - 1][j] == 0)
                perimeter += (i == m - 1 or grid[i + 1][j] == 0)
                perimeter += (j == 0 or grid[i][j - 1] == 0)
                perimeter += (j == n - 1 or grid[i][j + 1] == 0)
    return perimeter


# =============================================================================
# WAY 11: Class-based
# =============================================================================
class IslandPerimeter:
    def __init__(self, grid):
        self.grid = grid
        self.m = len(grid) if grid else 0
        self.n = len(grid[0]) if grid and grid[0] else 0

    def compute(self):
        perimeter = 0
        for i in range(self.m):
            for j in range(self.n):
                if self.grid[i][j] == 1:
                    perimeter += self._contribution(i, j)
        return perimeter

    def _contribution(self, i, j):
        count = 0
        if i == 0 or self.grid[i - 1][j] == 0:
            count += 1
        if i == self.m - 1 or self.grid[i + 1][j] == 0:
            count += 1
        if j == 0 or self.grid[i][j - 1] == 0:
            count += 1
        if j == self.n - 1 or self.grid[i][j + 1] == 0:
            count += 1
        return count


def island_perimeter_11(grid):
    """Class-based."""
    return IslandPerimeter(grid).compute()


# =============================================================================
# WAY 12: Walk and count only land-water transitions
# =============================================================================
def island_perimeter_12(grid):
    """
    Count land-water (or wall) transitions across all horizontal and
    vertical edges. Each transition contributes 1 to the perimeter.
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    perimeter = 0
    # Horizontal edges (between (i,j) and (i,j+1))
    for i in range(m):
        for j in range(n - 1):
            # Left is land, right is water -> +1
            if grid[i][j] == 1 and grid[i][j + 1] == 0:
                perimeter += 1
            # Left is water, right is land -> +1
            elif grid[i][j] == 0 and grid[i][j + 1] == 1:
                perimeter += 1
    # Vertical edges (between (i,j) and (i+1,j))
    for i in range(m - 1):
        for j in range(n):
            if grid[i][j] == 1 and grid[i + 1][j] == 0:
                perimeter += 1
            elif grid[i][j] == 0 and grid[i + 1][j] == 1:
                perimeter += 1
    # Outer boundary: count edges where cell is land and is on edge
    # Top boundary
    for j in range(n):
        if grid[0][j] == 1:
            perimeter += 1
    # Bottom boundary
    for j in range(n):
        if grid[m - 1][j] == 1:
            perimeter += 1
    # Left boundary
    for i in range(m):
        if grid[i][0] == 1:
            perimeter += 1
    # Right boundary
    for i in range(m):
        if grid[i][n - 1] == 1:
            perimeter += 1
    return perimeter


# =============================================================================
# WAY 13: Using itertools.product
# =============================================================================
def island_perimeter_13(grid):
    """Use itertools.product for iteration."""
    from itertools import product
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    perimeter = 0
    for i, j in product(range(m), range(n)):
        if grid[i][j] == 1:
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if ni < 0 or ni >= m or nj < 0 or nj >= n or grid[ni][nj] == 0:
                    perimeter += 1
    return perimeter


# =============================================================================
# WAY 14: Using set for land cells
# =============================================================================
def island_perimeter_14(grid):
    """Store land cell positions in a set for fast lookup."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    land = set()
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                land.add((i, j))
    perimeter = 0
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for i, j in land:
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if (ni, nj) not in land:
                perimeter += 1
    return perimeter


# =============================================================================
# WAY 15: Modified BFS without explicit visited (mutate grid)
# =============================================================================
def island_perimeter_15(grid):
    """
    Mutate the grid to mark visited cells. Same as BFS but uses -1 as
    a visited marker (works since input has only 0s and 1s).
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    from collections import deque

    # Find any land cell
    start = None
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                start = (i, j)
                break
        if start:
            break
    if not start:
        return 0

    perimeter = 0
    queue = deque([start])
    grid[start[0]][start[1]] = -1  # mark visited

    while queue:
        i, j = queue.popleft()
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if ni < 0 or ni >= m or nj < 0 or nj >= n:
                perimeter += 1
            elif grid[ni][nj] == 0:
                perimeter += 1
            elif grid[ni][nj] == 1:
                grid[ni][nj] = -1  # mark visited
                queue.append((ni, nj))

    return perimeter


# =============================================================================
# WAY 16: Using zip to traverse
# =============================================================================
def island_perimeter_16(grid):
    """Use zip-based traversal."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    perimeter = 0

    # Check vertical adjacencies (using zip of consecutive rows)
    for row_above, row_current in zip([None] + grid[:-1], grid):
        for j, (curr, above) in enumerate(zip(row_current, [None] + list(row_above[:-1]) if row_above else [None] * n)):
            if curr == 1:
                if above is None or above == 0:
                    perimeter += 1

    # Simpler: just iterate
    perimeter = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                if i == 0 or grid[i - 1][j] == 0:
                    perimeter += 1
                if i == m - 1 or grid[i + 1][j] == 0:
                    perimeter += 1
                if j == 0 or grid[i][j - 1] == 0:
                    perimeter += 1
                if j == n - 1 or grid[i][j + 1] == 0:
                    perimeter += 1
    return perimeter


# =============================================================================
# WAY 17: Functional with map
# =============================================================================
def island_perimeter_17(grid):
    """Map-based functional approach."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])

    def cell_perimeter(i, j):
        if grid[i][j] != 1:
            return 0
        c = 0
        if i == 0 or grid[i - 1][j] == 0:
            c += 1
        if i == m - 1 or grid[i + 1][j] == 0:
            c += 1
        if j == 0 or grid[i][j - 1] == 0:
            c += 1
        if j == n - 1 or grid[i][j + 1] == 0:
            c += 1
        return c

    # Sum all cell perimeters
    total = 0
    for i in range(m):
        for j in range(n):
            total += cell_perimeter(i, j)
    return total


# =============================================================================
# WAY 18: Using sum over neighbors
# =============================================================================
def island_perimeter_18(grid):
    """Sum the contribution from each cell in a clean way."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])

    # For each cell, sum the 4 sides
    def sides(i, j):
        return sum(
            1 for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            if i + di < 0 or i + di >= m or j + dj < 0 or j + dj >= n
            or grid[i + di][j + dj] == 0
        )

    return sum(sides(i, j) for i in range(m) for j in range(n) if grid[i][j] == 1)


# =============================================================================
# WAY 19: One-liner compact
# =============================================================================
def island_perimeter_19(grid):
    """One-liner style."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    return sum(
        (i == 0 or grid[i - 1][j] == 0) +
        (i == m - 1 or grid[i + 1][j] == 0) +
        (j == 0 or grid[i][j - 1] == 0) +
        (j == n - 1 or grid[i][j + 1] == 0)
        for i in range(m) for j in range(n) if grid[i][j] == 1
    )


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def island_perimeter_20(grid):
    """
    Final clean version.

    For each land cell, count its 4 sides. Each side is +1 if the neighbor
    is water or out of bounds.

    Why this works:
    Each side of a land cell is either:
    - Shared with another land cell (internal) -> NOT perimeter.
    - Facing water -> perimeter (+1).
    - On the boundary of the grid -> perimeter (+1).
    Total = sum of these per-side counts over all land cells.

    Alternative: 4*land - 2*shared_edges (mathematical equivalent).

    Time:  O(m*n).
    Space: O(1) - in place.
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    perimeter = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                # Top side
                if i == 0 or grid[i - 1][j] == 0:
                    perimeter += 1
                # Bottom side
                if i == m - 1 or grid[i + 1][j] == 0:
                    perimeter += 1
                # Left side
                if j == 0 or grid[i][j - 1] == 0:
                    perimeter += 1
                # Right side
                if j == n - 1 or grid[i][j + 1] == 0:
                    perimeter += 1
    return perimeter


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to calculate the perimeter of a single island in a grid where
land cells are 1 and water cells are 0. Cells are connected 4-directionally."

Key Insight:
"For each land cell, count its 4 sides. Each side is part of the perimeter
if it faces water or the boundary of the grid. Sum across all land cells."

Algorithm:
"1. For each cell (i, j):
2.   If grid[i][j] == 1 (land):
3.     Check 4 neighbors: up, down, left, right.
4.     For each side that's water or out of bounds, add 1 to perimeter.
5. Return perimeter."

Why this works:
"Each land cell has 4 sides. A side is internal if both it and its neighbor
are land. Otherwise it's perimeter (water side or grid edge). Summing across
all land cells gives the total perimeter."

Edge cases:
- 1x1 grid with one land cell: perimeter = 4.
- 1x2 grid with both land cells: perimeter = 6 (each cell shares 1 side).
- All water: perimeter = 0.
- All land: perimeter = 2*m + 2*n (outer boundary only).
- Single row: perimeter = 2 + 2*n (top, bottom, left of first, right of last).

Complexity:
- Time:  O(m*n) - visit each cell once.
- Space: O(1) - no extra data structures.

KEY TRICK:
For each land cell, count perimeter sides by checking if neighbor is water
or out of bounds. Four checks per cell.

ALTERNATIVE: 4 * land - 2 * shared_edges
Each land cell contributes 4 sides. Each shared edge between two land cells
removes 2 sides from the perimeter (one from each cell). So total perimeter
= 4*land - 2*shared_edges.

ALTERNATIVE: DFS/BFS
Walk the island. For each cell visited, count the sides that face water
or wall. Sum gives perimeter. Same complexity.

ALTERNATIVE: Edge counting
Count transitions between land and water across all edges (horizontal and
vertical). Each transition is +1 to perimeter. Plus count outer boundary
edges for land cells.

RELATIONSHIP TO OTHER PROBLEMS:
- Number of Islands (LC 200): Same grid pattern, different question.
- Max Area of Island (LC 695): Count cells, not perimeter.
- Surrounded Regions (LC 130): Boundary DFS pattern.

INTERVIEW TIPS:
1. Mention the "count 4 sides per cell" approach.
2. Note the alternative: 4*land - 2*shared_edges.
3. Handle boundary check carefully (out of bounds counts as water).
4. Test with a 1x1 grid for sanity.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Count sides per cell (BEST)", island_perimeter_1),
        ("Way 2: Verbose with directions", island_perimeter_2),
        ("Way 3: 4*land - 2*shared", island_perimeter_3),
        ("Way 4: DFS recursion", island_perimeter_4),
        ("Way 5: BFS iterative", island_perimeter_5),
        ("Way 6: enumerate", island_perimeter_6),
        ("Way 7: numpy vectorized", island_perimeter_7),
        ("Way 8: Generator + sum", island_perimeter_8),
        ("Way 9: Compact directions", island_perimeter_9),
        ("Way 10: Compact single-line", island_perimeter_10),
        ("Way 11: Class-based", island_perimeter_11),
        ("Way 12: Walk transitions", island_perimeter_12),
        ("Way 13: itertools.product", island_perimeter_13),
        ("Way 14: Set of land cells", island_perimeter_14),
        ("Way 15: BFS mutate grid", island_perimeter_15),
        ("Way 16: zip traverse", island_perimeter_16),
        ("Way 17: Map-based", island_perimeter_17),
        ("Way 18: Sum over neighbors", island_perimeter_18),
        ("Way 19: One-liner compact", island_perimeter_19),
        ("Way 20: Final cleanest", island_perimeter_20),
    ]

    test_cases = [
        # LeetCode 463 standard example
        # Trace: (0,1)=3, (1,0)=3, (1,1)=0, (1,2)=3, (2,1)=2, (3,0)=3, (3,1)=2
        # Total = 16
        ([[0, 1, 0, 0],
          [1, 1, 1, 0],
          [0, 1, 0, 0],
          [1, 1, 0, 0]], 16),

        # 1x1 land: 4 sides, all perimeter
        ([[1]], 4),

        # 1x2 land: 4+4-2*1 = 6
        ([[1, 1]], 6),

        # 1x2 mixed
        ([[1, 0]], 4),

        # 2x2 all land: 4*4 - 2*4 = 8
        ([[1, 1],
          [1, 1]], 8),

        # 2x2 L-shape: 3 cells, 2 shared edges: 4*3 - 2*2 = 8
        ([[1, 0],
          [1, 1]], 8),

        # Single row of 4 land cells: 4*4 - 2*3 = 10
        ([[1, 1, 1, 1]], 10),

        # Single column of 3 land cells: 4*3 - 2*2 = 8
        ([[1], [1], [1]], 8),

        # All water: 0
        ([[0, 0], [0, 0]], 0),

        # 2x2 half-land: single cell = 4
        ([[1, 0], [0, 0]], 4),

        # Plus shape: 5 cells, 4 shared edges: 4*5 - 2*4 = 12
        ([[0, 1, 0],
          [1, 1, 1],
          [0, 1, 0]], 12),

        # Empty grid
        ([], 0),

        # Single empty row
        ([[]], 0),

        # 3x3 all land: 4*9 - 2*12 = 12 (perimeter of full square)
        ([[1, 1, 1],
          [1, 1, 1],
          [1, 1, 1]], 12),
    ]

    print("=" * 70)
    print("ISLAND PERIMETER - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/island-perimeter")
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
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
