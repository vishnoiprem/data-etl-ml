# Counting Bits

## Problem
For a given `n`, return an array of length `n+1` where `ans[x]` is
the count of `1` bits in the binary representation of `x`, for
`0 ≤ x ≤ n`.

## Approach: DP with Right-Shift Recurrence

### Key Insight
For any positive integer `i`:
```
i = (i >> 1) << 1 | (i & 1)
```
That is, the right-shift `i >> 1` removes the lowest bit, and the
lowest bit itself is `i & 1` (0 or 1). So:
```
popcount(i) = popcount(i >> 1) + (i & 1)
```

### Algorithm
```python
dp = [0] * (n + 1)
for i in range(1, n + 1):
    dp[i] = dp[i >> 1] + (i & 1)
return dp
```

The base case `dp[0] = 0` is implicit. Each `dp[i]` depends on
`dp[i >> 1]`, which is at most half as large — so when we reach `i`,
`dp[i >> 1]` is already computed.

## Walkthrough: `n = 5`

```
i : 0  1  2  3  4  5
dp: 0  1  1  2  1  2
```

- `dp[1] = dp[0] + 1 = 1`
- `dp[2] = dp[1] + 0 = 1`
- `dp[3] = dp[1] + 1 = 2`
- `dp[4] = dp[2] + 0 = 1`
- `dp[5] = dp[2] + 1 = 2`

## Complexity
- **Time:** `O(n)` — one pass
- **Space:** `O(n)` for the answer array

## Alternative Approaches
- **Built-in `bin(i).count('1')` per number**: `O(n * log n)` total
- **Lowest set bit trick**: `dp[i] = dp[i & (i-1)] + 1`
- **MSB trick**: `dp[i] = dp[i - highest_power_of_2] + 1`

The right-shift trick is the cleanest and most idiomatic.
