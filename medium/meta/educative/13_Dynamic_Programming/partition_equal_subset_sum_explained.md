# Partition Equal Subset Sum

## Problem
Given a non-empty array of positive integers, determine whether it can
be split into two subsets whose sums are equal.

## Key Insight
If two subsets have equal sums, each must sum to `total / 2`. So the
problem reduces to: **does any subset sum to `total / 2`?**

If `total` is odd, the answer is immediately `False`.

## Approach: 1D Subset-Sum DP

### State
`dp[i]` = `True` if some subset of `nums` sums to exactly `i`.

### Transition
For each `num` in `nums`, update `dp[s] = dp[s] or dp[s - num]`
**iterating `s` from `target` down to `num`** so we don't reuse the
same element twice.

### Initialization
`dp[0] = True` (empty subset sums to 0).

### Answer
`dp[target]`.

## Walkthrough: `[1, 5, 11, 5]`

`total = 22`, `target = 11`.

| num | dp updates (descending)        |
|-----|--------------------------------|
| 1   | dp[1] = True                   |
| 5   | dp[6] = True, dp[5] = True     |
| 11  | dp[11] = True (via dp[0])      |
| 5   | dp[11] stays True              |

`dp[11] = True` → can partition ✓

## Complexity
- **Time:** `O(n * target)` = `O(n * total_sum)` ≈ `O(n² * 100)`
- **Space:** `O(target)` = `O(total_sum / 2)` ≈ `O(n * 50)`

## Edge Cases
- Odd total sum → False (no equal integer split)
- Two equal elements → True
- Empty array → not allowed by constraints
