# Maximal Square

## Problem
Given an `m × n` binary matrix of 0s and 1s, find the **area** of the
largest square containing only 1s.

## Approach: 2D Dynamic Programming

### State
`dp[i][j]` = side length of the largest all-1 square whose
**bottom-right corner** is at cell `(i, j)`.

### Transitions
If `matrix[i][j] == 1`:
- **First row or column** (`i == 0` or `j == 0`): the largest square
  ending here is just the cell itself → `dp[i][j] = 1`.
- **Otherwise**: extend the smaller square from neighbors.
  ```
  dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
  ```
  Why? To form an `(s+1) × (s+1)` square ending at `(i,j)`, we need
  `s × s` squares at top, left, and top-left. The smallest of those
  limits us.

If `matrix[i][j] == 0`: `dp[i][j] = 0`.

### Answer
`max_side^2` where `max_side = max over all dp[i][j]`.

## Walkthrough

```
1 0 1 0 0
1 0 1 1 1
1 1 1 1 1
1 0 0 1 0
```

DP grid (side lengths):
```
1 0 1 0 0
1 0 1 1 1
1 1 2 2 2
1 0 0 1 0
```

Max side = 2 → area = **4** ✓

## Complexity
- **Time:** `O(m * n)`
- **Space:** `O(m * n)` (can be reduced to `O(n)` with a rolling array)

## Edge Cases
- All 0s → area 0
- Single `1` cell → area 1
- Single `0` cell → area 0
