# Unique Paths II

## Problem
Count distinct paths from the top-left cell `(0, 0)` to the bottom-right
cell `(m-1, n-1)` in an `m x n` grid, moving only **right** or **down**,
avoiding obstacle cells (marked `1`).

## Approach: 2D Dynamic Programming

### State
`dp[i][j]` = number of paths from `(0, 0)` to `(i, j)` that avoid obstacles.

### Transitions
A cell `(i, j)` can only be reached from above `(i-1, j)` or the left `(i, j-1)`.
If `(i, j)` is blocked, `dp[i][j] = 0`. Otherwise:
```
dp[i][j] = dp[i-1][j] + dp[i][j-1]
```

### Base Cases
- `dp[0][0] = 1` if start is empty, else `0`
- `dp[i][0] = dp[i-1][0]` if cell is empty, else `0` (only one way down a column)
- `dp[0][j] = dp[0][j-1]` if cell is empty, else `0` (only one way across a row)

### Answer
`dp[m-1][n-1]`

## Walkthrough: 3x3 grid with center obstacle
```
0 0 0
0 1 0
0 0 0
```

```
1 1 1
1 0 1
1 1 2
```

Answer: `2` paths.

## Complexity
- **Time:** `O(m * n)`
- **Space:** `O(m * n)` (can be reduced to `O(n)` using rolling array)

## Edge Cases
- Start cell blocked → `0`
- End cell blocked → `0` (propagated by DP)
- Single empty cell → `1`
