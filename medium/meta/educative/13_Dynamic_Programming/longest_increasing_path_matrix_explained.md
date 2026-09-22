# Longest Increasing Path in a Matrix — 10 Solutions

## Problem
Given an `m × n` integer matrix, return the length of the longest
**strictly increasing** path. From any cell, you may move up, down,
left, or right.

## Solution Overview

| # | Approach | Time | Space |
|---|----------|------|-------|
| 1 | Naive DFS (no memo) | `O(2^(mn))` | `O(mn)` call stack |
| 2 | Top-down DP with memo | `O(mn)` | `O(mn)` |
| 3 | Bottom-up DP, sorted cells | `O(mn log(mn))` | `O(mn)` |
| 4 | BFS multi-source (topological) | `O(mn)` | `O(mn)` |
| 5 | Iterative DFS (explicit stack) | `O(mn)` | `O(mn)` |
| 6 | DSU + DFS | `O(mn · α)` | `O(mn)` |
| 7 | Lazy DP (sentinel memoization) | `O(mn)` | `O(mn)` |
| 8 | Priority-queue DP | `O(mn log(mn))` | `O(mn)` |
| 9 | On-demand cache (dict memo) | `O(mn)` | `O(mn)` |
| 10 | Reverse DP (decreasing order) | `O(mn)` | `O(mn)` |

---

## 1. Naive DFS — `O(2^(mn))`
Plain recursion from each cell. Without memoization, every path is
recomputed exponentially many times. Useful as a baseline.

```python
def dfs(i, j):
    best = 1
    for each direction:
        if neighbor larger:
            best = max(best, 1 + dfs(neighbor))
    return best
```

## 2. Top-Down DP — `O(mn)` ✓ (canonical)
Cache `memo[i][j] = longest increasing path starting at (i, j)`.

```python
memo[i][j] = 1 + max(memo[ni][nj] for each valid larger neighbor)
```

## 3. Bottom-Up DP with Sorted Cells
Sort all `mn` cells by value (smallest first). Process in order;
when you reach cell `(i,j)`, all smaller-valued neighbors are
already processed, so:
```
dp[i][j] = 1 + max(dp[ni][nj] for valid smaller neighbors)
```

## 4. BFS Multi-Source Topological Sort
Treat the matrix as a DAG (edges go from a cell to strictly-larger
neighbors). The longest path = number of topological levels. Start
BFS from cells with out-degree 0 (local maxima).

```python
while queue not empty:
    path_len += 1
    for each current cell:
        decrement out_degree of each smaller-valued neighbor
        if out_degree becomes 0: add to next level
```

## 5. Iterative DFS (no recursion)
Use an explicit stack with two states per cell: `False` (visit
children) and `True` (compute memo from children). Avoids Python
recursion limits for large matrices.

## 6. DSU + DFS
Disjoint-Set Union is used to merge cells we've fully explored into
a single component. When DFS later encounters a cell in the
component, we look up its memoized value rather than re-exploring.

## 7. Lazy DP (sentinel memo)
Use `-1` as the sentinel for "uncomputed" instead of relying on a
separate `visited` flag. Avoids the overhead of dual structures.

## 8. Priority-Queue DP
Same logic as Solution 3, but use a `heapq` for cell ordering.
Useful if you want to start traversal from any specific value.

## 9. On-Demand Cache (dict memo)
Use a Python `dict` keyed by `(i, j)` tuples for memoization. Same
complexity as Solution 2, but easier to extend or serialize.

## 10. Reverse DP
Process cells in **decreasing** order of value. Each cell's longest
path = 1 + (longest path through any larger-valued neighbor). Since
we process larger neighbors first, those values are already known.

---

## Why 10 distinct solutions?
Each approach illuminates a different algorithmic technique:
- **Solutions 1, 2, 5, 9**: recursion strategies
- **Solutions 3, 7, 8, 10**: ordering / DP table approaches
- **Solution 4**: graph-theoretic (topological sort)
- **Solution 6**: data structure (DSU) augmentation

In practice, **Solution 2 (top-down memoized DFS)** is the most
common interview answer; **Solution 4 (topological BFS)** is most
elegant for explaining correctness.

## Complexity Summary
- **Best time/space:** `O(mn)` achieved by 2, 4, 5, 6, 7, 9, 10
- **Sorting overhead:** 3 and 8 add `O(log(mn))` factor
- **Naive baseline:** Solution 1 is exponential; included only for contrast
