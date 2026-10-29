# 0/1 Knapsack

## Problem
Given `n` items with weights and values, and a knapsack with a weight
capacity, find the maximum total value of items that can fit
without exceeding the capacity. Each item is either taken (1) or
not taken (0) — no fractions, no duplicates.

## Approach: 2D Dynamic Programming

### State
`dp[i][c]` = max profit using the **first `i` items** with knapsack
capacity `c`.

### Transitions
For item `i` with weight `w` and value `v`:
- **Skip** it: `dp[i][c] = dp[i-1][c]`
- **Take** it (if `w <= c`): `dp[i][c] = v + dp[i-1][c-w]`
- Take the max of the two.

```python
dp[i][c] = dp[i-1][c]
if w <= c:
    dp[i][c] = max(dp[i][c], v + dp[i-1][c-w])
```

### Base Cases
- `dp[0][c] = 0` (no items → no profit)
- `dp[i][0] = 0` (no capacity → no items fit)

### Answer
`dp[n][capacity]`.

## Walkthrough: capacity=5, weights=[2,3,4,5], values=[3,4,5,6]

```
dp[0]: [0,0,0,0,0,0]
dp[1]: [0,0,3,3,3,3]      # item 1 (w=2, v=3)
dp[2]: [0,0,3,4,4,7]      # item 2 (w=3, v=4)
dp[3]: [0,0,3,4,5,7]      # item 3 (w=4, v=5)
dp[4]: [0,0,3,4,5,7]      # item 4 (w=5, v=6): only fits alone
```

Answer: **7** (items 1+2: 3+4, weight 5).

## Complexity
- **Time:** `O(n * capacity)`
- **Space:** `O(n * capacity)` (can be reduced to `O(capacity)` with a 1D rolling array)

## Space-Optimized 1D Version

```python
def knapsack_1d(capacity, weights, values):
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):
            if dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
    return dp[capacity]
```

Iterate `c` **descending** so each item is used at most once.

## Edge Cases
- No items fit → `0`
- All items fit → sum of all values
- Zero capacity → `0`
- Single item fits → that item's value
