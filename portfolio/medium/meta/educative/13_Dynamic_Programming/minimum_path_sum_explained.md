# Minimum Path Sum

## Problem
Given an `m × n` grid of non-negative integers, find a path from
top-left `(0, 0)` to bottom-right `(m-1, n-1)` moving only **right** or
**down** that minimizes the sum of values along the path.

## Approach: 2D Dynamic Programming

### State
`dp[i][j]` = minimum sum to reach cell `(i, j)` from `(0, 0)`.

### Transitions
A cell `(i, j)` can only be reached from `(i-1, j)` (down) or `(i, j-1)` (right):
```
dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])
```

### Base Cases
- `dp[0][0] = grid[0][0]`
- First row: `dp[0][j] = dp[0][j-1] + grid[0][j]` (only from left)
- First column: `dp[i][0] = dp[i-1][0] + grid[i][0]` (only from above)

### Answer
`dp[m-1][n-1]`

## Walkthrough: `[[1,3,1],[1,5,1],[4,2,1]]`

```
1 3 1
1 5 1
4 2 1
```

DP:
```
1  4  5
2  7  6
6  8  7
```

Answer: **7** ✓ (path: 1→3→1→1→1 = 7)

## Complexity
- **Time:** `O(m * n)`
- **Space:** `O(m * n)` (can be reduced to `O(n)` in-place by modifying grid)

## Edge Cases
- Single cell → returns its value
- Single row/column → sum of the row/column
