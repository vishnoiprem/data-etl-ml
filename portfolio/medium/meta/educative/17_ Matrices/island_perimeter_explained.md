# Island Perimeter - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/island-perimeter

## The Problem
```
You are given a grid with dimensions row x col, where each cell is land (1)
or water (0). Cells are connected only horizontally/vertically. The grid
contains exactly one island (no lakes), surrounded by water.

Calculate the perimeter of the island.

Examples:
    [[0,1,0,0],
     [1,1,1,0],
     [0,1,0,0],
     [1,1,0,0]] -> 16

    [[1]] -> 4
    [[1,1]] -> 6

Constraints:
- 1 <= rows, cols <= 100
- grid[i][j] is 0 or 1
- Exactly one island, no lakes.
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Each land cell is a unit square with 4 sides.
- Internal sides (between two land cells) are NOT perimeter.
- External sides (facing water or grid edge) ARE perimeter.
- Sum all external sides across all land cells = total perimeter.
```

### Step 2: The Trick
> "KEY INSIGHT: For each land cell, count its 4 sides. Each side is part of
> the perimeter if it faces water or is on the grid boundary.
>
> Equivalently: perimeter = 4*land_cells - 2*shared_edges.
> Each land cell contributes 4 sides. Each pair of adjacent land cells
> shares one edge, removing 2 sides from the total (one from each cell)."

### Step 3: Why both approaches work
> "Approach 1 (count sides): Direct. For each land cell, check 4 neighbors.
> Side is perimeter if neighbor is water or out of bounds.
>
> Approach 2 (formula): Each land cell starts with 4. Each shared edge
> between two land cells removes 1 from each, total -2.
> So perimeter = 4*land - 2*shared."

### Step 4: Algorithm
> "1. For each cell (i, j) in grid:
> 2.   If grid[i][j] == 1 (land):
> 3.     Up:    add 1 if i==0 or grid[i-1][j]==0
> 4.     Down:  add 1 if i==m-1 or grid[i+1][j]==0
> 5.     Left:  add 1 if j==0 or grid[i][j-1]==0
> 6.     Right: add 1 if j==n-1 or grid[i][j+1]==0
> 7. Return total."

### Step 5: Edge cases
> "- 1x1 land cell: perimeter = 4.
> - 2 adjacent land cells: 4+4-2 = 6.
> - 2x2 all land: 4*4 - 2*4 = 8.
> - All water: perimeter = 0."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to calculate the perimeter of a single island in a grid where
> land cells are 1 and water cells are 0."

**Key Insight:**
> "For each land cell, count its 4 sides. Each side is part of the perimeter
> if it faces water or is on the grid boundary."

**Algorithm:**
> "1. For each cell (i, j):
> 2.   If it's land:
> 3.     Check 4 neighbors. Add 1 for each side that's water or out of bounds.
> 4. Return total."

**Why this works:**
> "Each land cell has 4 sides. A side is internal if it shares a boundary
> with another land cell. Otherwise, it contributes to the perimeter.
> Summing across all cells gives the total."

**Edge cases:**
- 1x1 land cell: perimeter = 4.
- 1xN row of land: perimeter = 2 + 2*N (top + bottom of each, plus left + right ends).
- All water: perimeter = 0.
- All land (m x n): perimeter = 2*m + 2*n.

**Complexity:**
- Time:  O(m*n) - visit each cell once.
- Space: O(1) - no extra data structures.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Count sides per cell (BEST - Memorize!)
```python
def island_perimeter_1(grid):
    m, n = len(grid), len(grid[0])
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
```

### Way 2: Verbose with directions list
### Way 3: 4*land - 2*shared_edges formula
### Way 4: DFS recursion
### Way 5: BFS iterative
### Way 6: enumerate
### Way 7: numpy vectorized
### Way 8: Generator + sum
### Way 9: Compact with directions
### Way 10: Compact single-line (sum of bools)
### Way 11: Class-based
### Way 12: Walk transitions between land/water
### Way 13: itertools.product
### Way 14: Set of land cells
### Way 15: BFS mutate grid (mark visited)
### Way 16: zip traverse
### Way 17: Map-based functional
### Way 18: Sum over neighbors with helper
### Way 19: One-liner compact
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | Direct       |
| Math/cleanest      | Way 3    | 4*L - 2*S    |
| Functional         | Way 9/19 | Compact      |
| numpy available    | Way 7    | Vectorized   |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Count sides (Way 1) | O(mn) | O(1) | Best general |
| 4*L - 2*S (Way 3) | O(mn) | O(1) | Same complexity |
| DFS (Way 4) | O(mn) | O(m+n) | Recursion stack |
| BFS (Way 5) | O(mn) | O(mn) | Queue |
| numpy (Way 7) | O(mn) | O(mn) | Vectorized |

---

## Walkthrough Example

```
grid = [[0, 1, 0, 0],
        [1, 1, 1, 0],
        [0, 1, 0, 0],
        [1, 1, 0, 0]]

For each land cell, count its perimeter sides:

(0,1) → top:wall(+1), right:grid[0][2]=0(+1), bottom:grid[1][1]=1(0), left:grid[0][0]=0(+1) = 3
(1,0) → top:grid[0][0]=0(+1), right:grid[1][1]=1(0), bottom:grid[2][0]=0(+1), left:wall(+1) = 3
(1,1) → top:grid[0][1]=1(0), right:grid[1][2]=1(0), bottom:grid[2][1]=1(0), left:grid[1][0]=1(0) = 0
(1,2) → top:grid[0][2]=0(+1), right:grid[1][3]=0(+1), bottom:grid[2][2]=0(+1), left:grid[1][1]=1(0) = 3
(2,1) → top:grid[1][1]=1(0), right:grid[2][2]=0(+1), bottom:grid[3][1]=1(0), left:grid[2][0]=0(+1) = 2
(3,0) → top:grid[2][0]=0(+1), right:grid[3][1]=1(0), bottom:wall(+1), left:wall(+1) = 3
(3,1) → top:grid[2][1]=1(0), right:grid[3][2]=0(+1), bottom:wall(+1), left:grid[3][0]=1(0) = 2

Total: 3 + 3 + 0 + 3 + 2 + 3 + 2 = 16 ✓
```

```
Verification with formula:
land_cells = 7
shared_edges: (0,1)-(1,1), (1,0)-(1,1), (1,1)-(1,2), (1,1)-(2,1), (2,1)-(3,1), (3,0)-(3,1) = 6
perimeter = 4*7 - 2*6 = 28 - 12 = 16 ✓
```

---

## Best Answer to Memorize

```python
def island_perimeter(grid):
    m, n = len(grid), len(grid[0])
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
```

**~10 lines. O(m*n) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why count 4 sides per cell?
> "Each land cell has 4 sides. A side is perimeter if its neighbor is water
> or out of bounds. Summing all such sides across all land cells gives the
> total perimeter."

### Why does 4*land - 2*shared work?
> "Each land cell starts with 4 sides. Each shared edge between two adjacent
> land cells removes 1 side from each cell, total -2 per shared edge.
> So perimeter = 4*land - 2*shared_edges."

### Why O(1) space?
> "We just count. No data structures needed beyond a single integer
> accumulator. The formula approach uses O(1) too."

### What about DFS/BFS?
> "DFS/BFS works but uses O(m+n) stack or O(m*n) queue space. Not needed —
> we can just iterate the grid directly."

### Why can we ignore the "exactly one island" constraint?
> "The algorithm counts perimeter per land cell, regardless of whether they
> form one or many islands. Works for any configuration of land cells."

---

## Test Cases

| grid | Expected | Notes |
|------|----------|-------|
| [[0,1,0,0],[1,1,1,0],[0,1,0,0],[1,1,0,0]] | 16 | Standard LC 463 |
| [[1]] | 4 | Single cell |
| [[1,1]] | 6 | Two adjacent |
| [[1,1],[1,1]] | 8 | 2x2 square |
| [[1,0],[1,1]] | 8 | L-shape |
| [[1,1,1,1]] | 10 | Row of 4 |
| [[1],[1],[1]] | 8 | Column of 3 |
| [[1,1,1],[1,1,1],[1,1,1]] | 12 | 3x3 all land |
| [[0,0],[0,0]] | 0 | All water |
| [[1,0],[0,0]] | 4 | Single cell |
| [[0,1,0],[1,1,1],[0,1,0]] | 12 | Plus shape |
| [] | 0 | Empty |
| [[]] | 0 | Empty row |

---

## Common Pitfalls

1. **Off-by-one on grid boundary**: Wall = `i == 0 or i == m - 1`. Don't use `i == -1` or `i == m`.
2. **Confusing wall and water**: Out-of-bounds acts like water for perimeter purposes.
3. **Forgetting the 2x factor in formula**: Each shared edge is counted by BOTH cells in `4*L`, so subtract 2*shared (not 1*shared).
4. **Iterating with wrong range**: `range(m)` and `range(n)` for the cell check, not `range(m-1)`.
5. **Ignoring the destination**: For this problem, just count; no need to find the island.

---

## Why This Problem Matters

> "Tests:
> 1. Grid traversal with neighbor checks.
> 2. Boundary handling.
> 3. Mathematical formulation (4*L - 2*S).
> 4. Foundation for: image processing, geographic computations, area/perimeter calculations."

---

## Beyond This Problem: Related Patterns

### 1. Number of Islands (LC 200)
```python
# DFS/BFS to count connected components of 1s.
```

### 2. Max Area of Island (LC 695)
```python
# Count cells, not perimeter. DFS/BFS to find connected component sizes.
```

### 3. Surrounded Regions (LC 130)
```python
# Boundary DFS - find regions not connected to edges.
```

### 4. Flood Fill (LC 733)
```python
# BFS to fill connected region with new color.
```

---

## Connection to Grid Traversal

This problem uses the "examine each cell and its neighbors" pattern:

```
For each cell (i, j):
  Check 4 neighbors (up/down/left/right).
  Each neighbor check is bounded by grid edges.

This pattern appears in:
- Perimeter (this problem)
- Border coloring
- Distance calculation
- Game of Life (next state based on neighbors)
```

---

## Quick Checklist

When given a similar problem:
- [ ] What's the cell type? (1=land, 0=water here)
- [ ] What's the connectivity? (4-directional)
- [ ] What's the metric? (perimeter = count sides facing water/wall)
- [ ] Is it single island? (doesn't matter for this algorithm)
- [ ] Can I use the formula? (4*L - 2*S, same complexity)

---

## Mathematical Formulation

For an island with `L` land cells and `S` shared edges:
```
perimeter = 4L - 2S
```

This works because:
- Each cell has 4 sides: `4L` total.
- Each shared edge is counted twice (once per cell) in `4L`.
- Each shared edge should NOT be in the perimeter (it's internal).
- So subtract 2 per shared edge: `4L - 2S`.

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 463 - Island Perimeter](https://leetcode.com/problems/island-perimeter/)
