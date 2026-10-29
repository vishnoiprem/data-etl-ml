# Coin Change - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change

## The Problem
```
Given integer total and list coins (denominations), find the minimum number
of coins to make up the total amount. Infinite coins of each denomination.
Return -1 if impossible, 0 if total == 0.

Examples:
    coins=[1,5,10,25], total=11 -> 2 (10+1)
    coins=[2], total=3 -> -1
    coins=[1], total=0 -> 0

Constraints:
- 1 <= coins.length <= 12
- 1 <= coins[i] <= 10^4
- 0 <= total <= 900
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Classic unbounded knapsack / coin change problem.
Each coin can be used infinitely many times.
We want the MINIMUM NUMBER of coins to reach exactly `total`.
```

### Step 2: The Trick
> "KEY INSIGHT: Bottom-up DP.
>
> dp[i] = minimum coins to make amount i.
> dp[0] = 0, dp[i] = infinity initially.
>
> For each i from 1 to total:
>   For each coin c with c <= i:
>     dp[i] = min(dp[i], dp[i-c] + 1)"

### Step 3: Why this works
> "Each amount i can be reached by adding one coin c to amount (i-c).
> Since dp[i-c] is the minimum for (i-c), adding one more coin gives
> dp[i-c] + 1. Take the minimum over all coins."

### Step 4: Algorithm
> "1. Initialize dp[0] = 0, others = infinity.
> 2. For i in 1..total:
>    For each coin c with c <= i:
>      dp[i] = min(dp[i], dp[i-c] + 1)
> 3. Return dp[total] if finite, else -1."

### Step 5: Edge cases
> "- total == 0: return 0 (no coins needed).
> - No valid combination: dp[total] stays infinity, return -1.
> - Single coin = 1: answer = total.
> - Coin > total: skip."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the minimum number of coins to make a target total, with infinite coins of each denomination."

**Key Insight:**
> "This is unbounded knapsack / coin change DP. dp[i] = min coins to make amount i. dp[0] = 0. For each amount, try each coin and update dp[i] = min(dp[i], dp[i-c] + 1)."

**Algorithm:**
> "1. Initialize dp[0] = 0, others = infinity.
> 2. For i from 1 to total: for each coin c with c <= i: dp[i] = min(dp[i], dp[i-c] + 1).
> 3. Return dp[total] if finite, else -1."

**Why this works:**
> "Each amount i can be formed by adding one coin c to (i-c). dp[i-c] is already the min for i-c, so dp[i-c]+1 is a candidate. Take min over all coins."

**Edge cases:**
- total == 0: return 0.
- No valid combination: return -1.

**Complexity:**
- Time:  O(n * total) — n coins, total amounts.
- Space: O(total) for dp.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Bottom-up DP (BEST - Memorize!)
```python
def coin_change_1(coins, total):
    if total == 0:
        return 0
    dp = [float('inf')] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for c in coins:
            if c <= i:
                dp[i] = min(dp[i], dp[i - c] + 1)
    return dp[total] if dp[total] != float('inf') else -1
```

### Way 2: Verbose
### Way 3: Brute force recursion
### Way 4: Memoized recursion
### Way 5: BFS approach
### Way 6: Class-based
### Way 7: numpy
### Way 8: lru_cache decorator
### Way 9: enumerate + min
### Way 10: Helper functions
### Way 11: Functional map
### Way 12: BFS alternative
### Way 13: functools.reduce
### Way 14: Standard for-else
### Way 15: One-liner comprehension
### Way 16: While loop
### Way 17: List comp init
### Way 18: Sorted coins
### Way 19: Recursive with explicit memo
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | Bottom-up DP |
| Top-down           | Way 8    | lru_cache    |
| Brute (small n)    | Way 3    | Exponential  |
| BFS                | Way 5    | Shortest path|
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Bottom-up (Way 1) | O(n * total) | O(total) | Best |
| Memoized (Way 4) | O(n * total) | O(total) | Same |
| Brute (Way 3) | O(n^total) | O(total) | Too slow |
| BFS (Way 5) | O(n * total) | O(total) | Same |

---

## Walkthrough Example

```
coins = [1, 5, 10, 25]
total = 11

Step 1: Initialize dp = [0, inf, inf, ..., inf] (12 elements).

Step 2: Fill dp.
  i=1: try coin 1. dp[0]+1 = 1. dp[1] = 1.
  i=2: try coin 1. dp[1]+1 = 2. dp[2] = 2.
  i=3: dp[3] = 3.
  i=4: dp[4] = 4.
  i=5: try 1 -> 5, try 5 -> 1. dp[5] = 1.
  i=6: try 1 -> 2, try 5 -> 2. dp[6] = 2.
  ...
  i=10: dp[10] = 1 (one 10-coin).
  i=11: try 1 -> 11, try 5 -> 3, try 10 -> 2. dp[11] = 2.

Return dp[11] = 2.
```

---

## Best Answer to Memorize

```python
def coinChange(coins, total):
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for c in coins:
            if c <= i:
                dp[i] = min(dp[i], dp[i - c] + 1)
    return dp[total] if dp[total] != INF else -1
```

**~10 lines. O(n * total) time. O(total) space. Interview-ready!**

---

## Key Insights

### Why bottom-up DP?
> "The recurrence dp[i] = min(dp[i-c] + 1) depends only on smaller amounts.
> We can compute in order from 0 to total."

### Why initialize with infinity?
> "We need to know if an amount is UNREACHABLE. Infinity (or large number)
> lets us check dp[total] at the end."

### Why dp[0] = 0?
> "Zero coins are needed to make amount 0. This is the base case."

### Why iterate i from 1 to total?
> "We compute each amount i based on smaller amounts (i-c). Smaller i's
> are already computed when we reach i."

### Why coin <= i?
> "A coin larger than the amount can't be used to make it."

### Why min over all coins?
> "Each amount can be reached via any coin. We want the minimum across
> all possibilities."

---

## Test Cases

| coins | total | Expected | Notes |
|-------|-------|----------|-------|
| [1,5,10,25] | 11 | 2 | 10+1 |
| [2] | 3 | -1 | Impossible |
| [1] | 0 | 0 | Zero total |
| [1,2,5] | 11 | 3 | 5+5+1 |
| [186,419,83,408] | 6249 | 20 | LeetCode |
| [1,2,5] | 100 | 20 | All 5s |
| [3,7,405,436] | 8839 | 25 | LeetCode |
| [1] | 100 | 100 | All singles |
| [5,10] | 15 | 2 | 5+10 |
| [7] | 15 | -1 | Impossible |

---

## Common Pitfalls

1. **Forgetting dp[0] = 0**: Without base case, all dp values are infinity.
2. **Not checking coin <= i**: IndexError on dp[i-c] when c > i.
3. **Not handling total == 0**: Return 0 directly.
4. **Forgetting impossible case**: dp[total] may be infinity; check before returning.
5. **Recursion depth**: Top-down with large total exceeds default Python recursion limit.

---

## Why This Problem Matters

> "Tests:
> 1. Bottom-up DP pattern.
> 2. Subproblem identification.
> 3. Initialization with infinity.
> 4. Foundation for: unbounded knapsack, coin change variants."

---

## Beyond This Problem: Related Patterns

### 1. Coin Change II (LC 518)
```python
# Count ways (not min coins). dp[i] += dp[i-c].
```

### 2. Climbing Stairs (LC 70)
```python
# Smaller variant: ways to climb n stairs with 1 or 2 steps.
```

### 3. Perfect Squares (LC 279)
```python
# Min perfect squares summing to n. Same DP structure.
```

### 4. Minimum Cost For Tickets (LC 983)
```python
# Different: min cost for travel days with ticket durations.
```

---

## Connection to Unbounded Knapsack

Coin Change is the canonical "unbounded knapsack" problem:

```
PATTERN:
- Items can be used unlimited times.
- dp[i] = min/max/some-aggregation for subproblem of size i.
- Recurrence uses dp[i - weight] + 1 (for "min items").

EXAMPLES:
- Coin Change (min coins).
- Rod Cutting (max value).
- Integer Break (max product).
- Unbounded knapsack variants.
```

The recurrence structure is the same; only the aggregation function differs.

---

## Quick Checklist

When given a similar problem:
- [ ] Are items bounded or unbounded? (here: unbounded)
- [ ] What's the objective? (min count, max value, count ways)
- [ ] Define dp[i] clearly.
- [ ] Initialize dp[0] = 0 (for min/max) or dp[0] = 1 (for count).
- [ ] Initialize others with infinity (min) or 0 (max/count).
- [ ] Iterate i from 1 to target.
- [ ] For each coin/item, update dp[i].
- [ ] Handle edge cases (target 0, impossible).

---

## Mathematical Formulation

For coins C and target T:

```
dp[0] = 0
dp[i] = min(dp[i-c] + 1) for c in C with c <= i, otherwise infinity

If dp[T] = infinity: impossible, return -1.
Else: return dp[T].
```

This is an unbounded knapsack where each "item" (coin) has weight c and
"value" 1 (each coin contributes 1 to count).

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 322 - Coin Change](https://leetcode.com/problems/coin-change/)