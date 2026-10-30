# Number of Good Subsets

## Problem
A subset of `nums` is "good" if the product of its elements equals a
product of **two or more distinct primes** (i.e., square-free with at
least two prime factors). Return the number of good subsets modulo
`10^9 + 7`. Two subsets are different if they pick different indices.

## Key Insight: Mask DP

`nums[i] <= 30`, so only the 10 primes ≤ 30 are relevant:
```
{2, 3, 5, 7, 11, 13, 17, 19, 23, 29}
```

Encode any square-free product as a **10-bit mask** where bit `i`
indicates whether prime `primes[i]` appears.

For each `n ∈ [2, 30]`:
- Compute its prime factorization.
- If any prime appears twice (e.g., 4 = 2², 8 = 2³, 12 = 2²·3) →
  **invalid** (its product would not be square-free).
- Otherwise, encode it as a mask `m = mask_of[n]`.

## Algorithm: DP over masks

`dp[mask]` = number of subsets (index-distinct) whose product has
exactly the prime set `mask`.

1. Initialize `dp[0] = 1` (empty subset).
2. For each `n` (with valid mask `m` and `cnt[n]` occurrences):
   - For each `old_mask` not overlapping with `m`:
     ```
     dp[old_mask | m] += dp[old_mask] * cnt[n]
     ```
3. Sum `dp[mask]` for masks with ≥ 2 bits set (excluding `dp[0]`).
4. Multiply by `2^cnt[1]` because each `1` can independently be in/out
   of any subset without affecting the product.

## Walkthrough: `[1, 2, 5, 6]`

- cnt[1]=1, cnt[2]=1, cnt[5]=1, cnt[6]=1
- Valid numbers: 2 (mask {2}), 5 (mask {5}), 6 (mask {2,3})

DP:
```
dp[0] = 1
+ n=2 (mask {2}): dp[{2}] = 1
+ n=5 (mask {5}): dp[{5}] = 1; dp[{2,5}] = 1
+ n=6 (mask {2,3}): dp[{2,3}] = 1; dp[{2,3,5}] = 1
```

Masks with ≥ 2 bits: {2,5}, {2,3}, {2,3,5} → sum = 3
Multiply by 2^1 (for the one 1) → **6** ✓

The 6 good subsets are:
`[6], [1,6], [2,5], [5,6], [1,2,5], [1,5,6]`

## Complexity
- **Time:** `O(n + 2^P · V)` ≈ `O(2^10 · 30)` = ~30K — very fast
  (`P` = number of primes = 10, `V` = 30)
- **Space:** `O(2^P)` = `O(1024)` for the `dp` array

## Edge Cases
- `[1, 1, 1]` → 0 (no non-1 element to combine with)
- All numbers non-square-free (e.g., `[4, 8, 9]`) → 0
