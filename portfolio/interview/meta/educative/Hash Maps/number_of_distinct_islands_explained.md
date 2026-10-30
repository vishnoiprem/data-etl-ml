# Number of Distinct Islands - 10 Ways with How to Think

## The Problem
```
Given an m x n binary matrix where 1 = land and 0 = water.
An island is a group of connected 1s (horizontally/vertically).
Two islands are "same" if one matches the other without rotation/flip.
Return the number of distinct islands.
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Grid:                Two islands are "same" if they have
1 1 0 1 1           the same SHAPE (not rotated/flipped).
0 0 1 0 0

Islands:
[A] at (0,0)-(0,1) and (1,2)  -> shape: 2 cells horizontal + 1 below
[B] at (0,3)-(0,4)            -> shape: 2 cells horizontal

Count: 2 distinct islands
```

### Step 2: Key Insight
> "Two islands are the same shape if their **relative cell positions** are the same!"

### Step 3: How to Represent a Shape
> "Use the **relative coordinates** of all cells from a starting point, or a **path string** of moves."

```
Path: "RDRD" (Right, Down, Right, Down)  -> same shape!
```

### Step 4: Algorithm
1. Find all islands using DFS/BFS
2. For each island, record its SHAPE (relative coords or path)
3. Use a SET to count unique shapes

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find islands (groups of connected 1s) and count how many have distinct shapes. Two islands have the same shape if they match without rotation or flipping."

**Key Insight:**
> "I'll represent each island's shape using the relative coordinates of all its cells from a starting point. Same relative coordinates means same shape!"

**Algorithm:**
> "1. For each unvisited land cell, do DFS to find its entire island
> 2. Record the shape (e.g., as a string of directions or set of coords)
> 3. Add to a set
> 4. Return the set size"

**Why this works:**
> "Two islands are 'same' if their relative coordinates match. By normalizing to start at (0,0), the absolute position doesn't matter - only the shape does."

**Edge cases:**
- Single cell islands: all have the same shape
- L-shaped vs T-shaped: different shapes
- Two 2x2 squares at different positions: same shape

---

## The 10 Implementations

### Way 1: DFS with Path String (MOST COMMON!)
```python
def num_distinct_islands(grid):
    if not grid:
        return 0

    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, direction):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return ""
        grid[r][c] = 0
        path = direction
        path += dfs(r+1, c, "D")
        path += dfs(r-1, c, "U")
        path += dfs(r, c+1, "R")
        path += dfs(r, c-1, "L")
        path += "B"  # backtrack marker
        return path

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                shape = dfs(i, j, "O")
                seen.add(shape)

    return len(seen)
```

### Way 2: DFS with Relative Coords Tuple
```python
def num_distinct_islands(grid):
    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, r0, c0):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return []
        grid[r][c] = 0
        coords = [(r - r0, c - c0)]
        coords += dfs(r+1, c, r0, c0)
        coords += dfs(r-1, c, r0, c0)
        coords += dfs(r, c+1, r0, c0)
        coords += dfs(r, c-1, r0, c0)
        return coords

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                shape = tuple(sorted(dfs(i, j, i, j)))
                seen.add(shape)

    return len(seen)
```

### Way 3: BFS with Coordinates
```python
from collections import deque

def num_distinct_islands(grid):
    m, n = len(grid), len(grid[0])
    seen = set()

    def bfs(r0, c0):
        q = deque([(r0, c0)])
        grid[r0][c0] = 0
        path = []
        while q:
            r, c = q.popleft()
            path.append((r - r0, c - c0))
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 1:
                    grid[nr][nc] = 0
                    q.append((nr, nc))
        return tuple(sorted(path))

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                shape = bfs(i, j)
                seen.add(shape)

    return len(seen)
```

### Way 4: DFS with Frozen Set
```python
def num_distinct_islands(grid):
    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, r0, c0):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return frozenset()
        grid[r][c] = 0
        coords = {(r - r0, c - c0)}
        coords |= dfs(r+1, c, r0, c0)
        coords |= dfs(r-1, c, r0, c0)
        coords |= dfs(r, c+1, r0, c0)
        coords |= dfs(r, c-1, r0, c0)
        return coords

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                seen.add(dfs(i, j, i, j))

    return len(seen)
```

### Way 5: Iterative DFS with Stack
```python
def num_distinct_islands(grid):
    m, n = len(grid), len(grid[0])
    seen = set()

    def explore(r0, c0):
        stack = [(r0, c0, "O")]
        grid[r0][c0] = 0
        path = ""
        while stack:
            r, c, d = stack.pop()
            path += d
            for dr, dc, name in [(1,0,"D"), (-1,0,"U"), (0,1,"R"), (0,-1,"L")]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 1:
                    grid[nr][nc] = 0
                    stack.append((nr, nc, name))
            path += "B"
        return path

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                seen.add(explore(i, j))

    return len(seen)
```

### Way 6-10: Variations
- Way 6: String with `(row,col)` format
- Way 7: Normalized coordinates
- Way 8: Compact tuple style
- Way 9: Direction string variant
- Way 10: Most compact hash

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest code    | Path string | Easy to read |
| Fastest          | BFS         | No recursion |
| Memory efficient | Iterative   | No stack     |
| Easiest          | Tuple       | Intuitive    |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| DFS path | O(mn) | O(mn) |
| BFS path | O(mn) | O(mn) |

---

## Walkthrough Example

```
grid = [[1,1,0,1,1],
        [0,0,1,0,0]]

Start DFS at (0,0):
  Path: "O" + "R"(0,1) + "D"(nothing) + "B"
  Continue: (0,1) -> "R"(nothing) + "D"(1,2) + ...
  
  Shape of island at (0,0):
  [(0,0), (0,1), (1,2)]  -> sorted: [(0,0), (0,1), (1,2)]

Start DFS at (0,3):
  Shape of island at (0,3):
  [(0,3), (0,4)]  -> sorted: [(0,3), (0,4)]

These two shapes are DIFFERENT.
seen = {((0,0),(0,1),(1,2)), ((0,3),(0,4))}
Return 2 ✓
```

## Best Answer to Memorize

```python
def numDistinctIslands(grid):
    m, n = len(grid), len(grid[0])
    seen = set()

    def dfs(r, c, direction):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
            return ""
        grid[r][c] = 0
        path = direction
        path += dfs(r+1, c, "D")
        path += dfs(r-1, c, "U")
        path += dfs(r, c+1, "R")
        path += dfs(r, c-1, "L")
        path += "B"
        return path

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                seen.add(dfs(i, j, "O"))

    return len(seen)
```

**18 lines. O(mn) time. Clean. Interview-ready!** 🚀

## Key Insight Summary

> "Two islands have the same shape if their relative coordinates match. By normalizing to start at (0,0), we ignore position and only care about shape."

The "B" backtrack marker is crucial - it prevents ambiguity between:
- Shape that goes Right then Back (2 chars)
- Shape that goes Right only (1 char)

## Test Cases

| Grid | Expected | Why |
|------|----------|-----|
| L-shape + horizontal pair | 2 | Different shapes |
| Two 2x2 squares | 1 | Same shape |
| All zeros | 0 | No islands |
| Single cell | 1 | One shape |
| Four single cells | 1 | All same shape |
