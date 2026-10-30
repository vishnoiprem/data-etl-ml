# Where Will the Ball Fall - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/where-will-the-ball-fall

## The Problem
```
You have n balls and a 2D grid of size m x n representing a box.
The box is open on the top and bottom. Each cell has a diagonal:
- 1 redirects the ball to the right
- -1 redirects the ball to the left

Drop n balls at each column's top. A ball gets STUCK if:
1. It hits a V-shaped pattern between two adjacent cells, OR
2. A cell redirects the ball into a wall (col < 0 or col >= n).

V-shape: adjacent cells redirect AWAY from each other.
- grid[r][c] = 1 (right) and grid[r][c+1] = -1 (left) is a V.
- grid[r][c] = -1 (left) and grid[r][c+1] = 1 (right) is a V (inverted).

Return array of size n. result[x] = exit column if ball from col x
exits, or -1 if stuck.

Constraints:
- 1 <= m, n <= 100
- grid[i][j] is 1 or -1
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
The grid has cells that redirect balls. A ball dropped at column c
will fall through row by row, being redirected by each cell.

A ball gets stuck if:
- Cell redirects it to a wall (col 0 or col n-1).
- It enters a V-shape: two adjacent cells redirect away from each other.
```

### Step 2: The Trick
> "KEY INSIGHT: At each cell (r, c) with value v:
> - v == 1: ball moves to (r+1, c+1)
> - v == -1: ball moves to (r+1, c-1)
>
> Stuck if:
> - Next column is out of bounds, OR
> - V-shape: grid[r][c+v] != v (the cell we're moving toward redirects back).
>
> So V-shape check: if grid[r][next_col] != grid[r][col], the ball would
> be pushed back — stuck."

### Step 3: Why V-shape check works
> "If grid[r][c]=1 (right), ball wants to go to c+1. If grid[r][c+1]=-1
> (left), the cell at c+1 wants to push the ball BACK to c.
> They form a V-shape pointing up (\\\\ and // diverge upward).
> Balls bounce between them forever — stuck."

### Step 4: Algorithm
> "1. For each starting column c in [0, n):
> 2.   col = c
> 3.   For each row r in [0, m):
> 4.     d = grid[r][col]
> 5.     next_col = col + d
> 6.     If next_col < 0 or next_col >= n: STUCK, break
> 7.     If grid[r][next_col] != d: V-shape, STUCK, break
> 8.     col = next_col
> 9.   result[c] = -1 if stuck else col
> 10. Return result."

### Step 5: Edge cases
> "- Ball at col 0 with grid=1: moves to col 1 (ok).
> - Ball at col 0 with grid=-1: tries col -1 (wall) — STUCK.
> - All 1s: ball shifts right, may hit right wall.
> - All -1s: ball shifts left, may hit left wall."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to simulate n balls dropping through an m x n grid.
> Each cell redirects the ball left (-1) or right (1). A ball gets
> stuck at walls or V-shaped patterns."

**Key Insight:**
> "At each cell, move by the cell's value. Stuck if next column is
> out of bounds, OR V-shape (adjacent cell redirects back)."

**Algorithm:**
> "1. For each starting column c:
> 2.   col = c
> 3.   For each row r:
> 4.     d = grid[r][col]
> 5.     next_col = col + d
> 6.     If next_col < 0 or next_col >= n: stuck, break
> 7.     If grid[r][next_col] != d: V-shape, stuck, break
> 8.     col = next_col
> 9.   result[c] = -1 if stuck else col
> 10. Return result."

**Why V-shape detection works:**
> "If grid[r][c]=1 and grid[r][c+1]=-1, ball at c moves right to c+1,
> but cell at c+1 pushes back to c. Balls bounce forever — stuck."

**Edge cases:**
- 1x1 grid: ball always stuck (single direction moves to wall).
- All 1s: balls shift right until hitting right wall.
- All -1s: balls shift left until hitting left wall.
- 2x2 with V-shapes: most balls stuck.

**Complexity:**
- Time:  O(m*n) - n balls through m rows each.
- Space: O(n) for result.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Simulate each ball (BEST - Memorize!)
```python
def find_exit_column_1(grid):
    if not grid or not grid[0]:
        return []
    m, n = len(grid), len(grid[0])
    result = []
    for start_col in range(n):
        col = start_col
        stuck = False
        for row in range(m):
            direction = grid[row][col]
            next_col = col + direction
            if next_col < 0 or next_col >= n:
                stuck = True
                break
            if grid[row][next_col] != direction:
                stuck = True
                break
            col = next_col
        result.append(-1 if stuck else col)
    return result
```

### Way 2: Verbose version
### Way 3: Helper function
### Way 4: enumerate start cols
### Way 5: Recursive
### Way 6: Class-based
### Way 7: Walrus operator (Python 3.8+)
### Way 8: Lambda + map
### Way 9: Direction handling
### Way 10: Early return sentinel
### Way 11: itertools
### Way 12: Numpy
### Way 13: Generator
### Way 14: Exception handling
### Way 15: functools.reduce
### Way 16: While loop with flag
### Way 17: Batch process all starts
### Way 18: LRU cache (memoization)
### Way 19: Compact nested fn
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | Direct       |
| Many balls         | Way 17   | Batch        |
| Python 3.8+        | Way 7    | Walrus       |
| Educational        | Way 5    | Recursive    |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Simulate (Way 1) | O(mn) | O(n) | Best general |
| Recursive (Way 5) | O(mn) | O(n+m) | Stack overhead |
| Batch (Way 17) | O(mn) | O(n) | Process all in parallel |

---

## Walkthrough Example

```
grid = [[1, 1],
        [-1, -1]]

Ball 0 (from col 0):
  Row 0: grid[0][0]=1. next_col=0+1=1. grid[0][1]=1==1. Move. col=1.
  Row 1: grid[1][1]=-1. next_col=1-1=0. grid[1][0]=-1==-1. Move. col=0.
  Done! result[0] = 0.

Ball 1 (from col 1):
  Row 0: grid[0][1]=1. next_col=1+1=2. 2 >= n=2. WALL! Stuck.
  result[1] = -1.

Result: [0, -1]
```

```
grid = [[1, -1],
        [1, 1]]

Ball 0 (from col 0):
  Row 0: grid[0][0]=1. next_col=1. grid[0][1]=-1 != 1. V-shape! Stuck.
  result[0] = -1.

Ball 1 (from col 1):
  Row 0: grid[0][1]=-1. next_col=0. grid[0][0]=1 != -1. V-shape! Stuck.
  result[1] = -1.

Result: [-1, -1]
```

---

## Best Answer to Memorize

```python
def find_exit_column(grid):
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
```

**~10 lines. O(m*n) time. O(n) space. Interview-ready!**

---

## Key Insights

### Why check grid[r][next_col] != d?
> "If we move to next_col based on direction d, and the cell there has
> direction -d, it would push us back. That's the V-shape — balls
> bounce between cells forever."

### Why is this a simulation problem?
> "The ball's path is deterministic. Each cell's value determines
> the next position. No clever math trick — just simulate."

### Why is it O(m*n) and not O(n log n)?
> "Each of n balls traverses up to m rows. Total work = n*m.
> No way around this — we must trace each ball's path."

### Why include V-shape check?
> "Without it, balls would bounce between cells forever. The check
> detects the deadlock condition."

---

## Test Cases

| grid | Expected |
|------|----------|
| [[1,1],[-1,-1]] | [0,-1] |
| [[1,1,1],[1,1,1]] | [2,-1,-1] |
| [[-1,-1,-1],[-1,-1,-1]] | [-1,-1,0] |
| [[1,1],[1,1]] | [-1,-1] |
| [[1]] | [-1] |
| [[-1]] | [-1] |
| [[1,-1],[1,1]] | [-1,-1] |
| [] | [] |

---

## Common Pitfalls

1. **Forgetting V-shape check**: Just wall check isn't enough.
2. **Wrong V-shape logic**: Check `grid[r][next_col] != d`, not `!= -d`.
3. **Off-by-one in row traversal**: range(m), not range(m-1).
4. **Updating col before checking**: Check before move.
5. **Not handling empty grid**: Return [] for empty grid.

---

## Why This Problem Matters

> "Tests:
> 1. Simulation with state changes.
> 2. Multiple termination conditions.
> 3. 2D grid traversal.
> 4. Foundation for: pinball games, ball physics, redirect systems."

---

## Beyond This Problem: Related Patterns

### 1. Rotting Oranges (LC 994)
```python
# Multi-source BFS, but similar grid traversal.
```

### 2. Matrix BFS problems
```python
# Different movement rules but same idea.
```

### 3. Snake Game (LC 353)
```python
# Different state tracking but similar simulation.
```

---

## Connection to Simulation Problems

This problem uses "deterministic state simulation":

```
1. State = (row, col).
2. Transitions: deterministic based on grid value.
3. Termination: state leaves bounds OR enters V-shape.
4. Result: final state (column) or -1 (stuck).

This pattern works for many grid simulation problems.
```

---

## Quick Checklist

When given a similar problem:
- [ ] What's the state? (row, col)
- [ ] What's the transition rule? (based on grid value)
- [ ] What are termination conditions? (wall, V-shape)
- [ ] Is the system deterministic? (yes here)
- [ ] What's the result? (exit col or -1)

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1706 - Where Will the Ball Fall](https://leetcode.com/problems/where-will-the-ball-fall/)
