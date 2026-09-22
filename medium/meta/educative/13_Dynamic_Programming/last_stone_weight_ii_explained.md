# Last Stone Weight II - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/last-stone-weight-ii

## The Problem
```
Given an integer array stones where stones[i] is the weight of the i-th stone.

Game: pick any two stones with weights x <= y.
- If x == y: both destroyed.
- If x < y: stone x destroyed, stone y becomes y - x.
- Game ends when at most one stone remains.

Return the SMALLEST POSSIBLE weight of the remaining stone (0 if none).

Examples:
    stones=[2,7,4,1,8,1] -> 1
    stones=[31,26,33,21,40] -> 5

Constraints:
- 1 <= stones.length <= 30
- 1 <= stones[i] <= 100
```

## How I Think (The Mental Process)

### Step 1: Understand the Game
```
We smash stones together. The smaller stone is subtracted from the larger.
Each smash effectively "cancels out" weight.
```

### Step 2: The Trick
> "KEY INSIGHT: The final remaining weight equals |sum(A) - sum(B)|
> where A and B are two subsets of stones (partition).
>
> Why? Each smash is x - y with x <= y. The end result is the absolute
> value of sum of stones with + and - signs. We can think of it as:
> partition stones into A (+) and B (-). Final = |sum(A) - sum(B)|.
>
> Minimize |sum(A) - sum(B)| = minimize |total - 2*sum(A)|.
> Equivalently: find subset sum closest to total/2."

### Step 3: Reduce to Subset Sum
```
We need subset A with sum closest to total/2.
If sum(A) = s, then |sum(A) - sum(B)| = |total - 2s|.
Minimum over all achievable s = answer.

This is the classic partition problem!
```

### Step 4: Algorithm
> "1. Compute total = sum(stones).
> 2. target = total // 2.
> 3. dp[s] = True if sum s is achievable.
>    dp[0] = True. For each stone, iterate s in reverse: dp[s] |= dp[s-stone].
> 4. Find max s <= target where dp[s] = True.
> 5. Return total - 2*s."

### Step 5: Edge cases
> "- 1 stone: answer = stone[0].
> - All equal: 0 if even count, stone[0] if odd.
> - All subset sums achievable (small total): exact balance possible."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the smallest possible weight of the last stone after optimal smashing."

**Key Insight:**
> "Smashing stones is equivalent to partitioning them into two groups A and B. The final weight equals |sum(A) - sum(B)|. I want to minimize this, so I want sum(A) as close to total/2 as possible. This is the classic subset sum / partition problem."

**Algorithm:**
> "1. Compute total. target = total // 2.
> 2. dp[s] = is sum s achievable using some subset of stones?
> 3. For each stone, update dp in reverse: dp[s] |= dp[s-stone].
> 4. Find largest achievable s <= target. Answer = total - 2*s."

**Why this works:**
> "Each stone is in A (+sign) or B (-sign). The final weight is the absolute sum. The sign assignment minimizes |total - 2*sum(A)|. Subset sum DP finds all achievable subset sums."

**Edge cases:**
- 1 stone: return stone[0].
- All same weight: 0 if even, weight if odd.
- total is even and partition possible: answer 0.

**Complexity:**
- Time:  O(n * total) where total <= 3000. O(30 * 3000) = O(90,000).
- Space: O(total).

---

## The 20 Implementations (Simple to Complex)

### Way 1: Subset sum DP (BEST - Memorize!)
```python
def last_stone_weight_ii_1(stones):
    total = sum(stones)
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for stone in stones:
        for s in range(target, stone - 1, -1):
            if dp[s - stone]:
                dp[s] = True
    for s in range(target, -1, -1):
        if dp[s]:
            return total - 2 * s
    return total
```

### Way 2: Verbose 2D DP
### Way 3: Brute force (subset enumeration)
### Way 4: Memoized recursion (sign assignment)
### Way 5: Bitset (Python int as bitmask)
### Way 6: Class-based
### Way 7: numpy vectorized
### Way 8: lru_cache decorator
### Way 9: Set of achievable sums
### Way 10: Helper functions
### Way 11: Functional reduce
### Way 12: itertools.combinations (brute)
### Way 13: DFS with pruning (sorted descending)
### Way 14: Meet in the middle
### Way 15: Tabulation by index (set per stone)
### Way 16: enumerate + next
### Way 17: Sorted DFS cached
### Way 18: BFS over (sum_a - sum_b) states
### Way 19: Iterative memo (i, diff) -> min abs
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+----------------+
| Scenario           | Best     | Why            |
+--------------------+----------+----------------+
| Standard           | Way 1    | Subset sum DP  |
| Top-down           | Way 4    | Memoization    |
| Top-down (clean)   | Way 8    | lru_cache      |
| BFS                | Way 18   | State space    |
| Pythonic           | Way 5    | Bitset trick   |
+--------------------+----------+----------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Subset sum DP (Way 1) | O(n * total) | O(total) | Best |
| 2D DP (Way 2) | O(n * total) | O(n * total) | Verbose |
| Brute force (Way 3) | O(2^n * n) | O(1) | Exponential |
| Bitset (Way 5) | O(n * total/wordsize) | O(total/wordsize) | Compact |
| Meet in middle (Way 14) | O(2^(n/2) * n) | O(2^(n/2)) | For large n |

---

## Walkthrough Example

```
stones = [2, 7, 4, 1, 8, 1]
total = 23
target = 11

dp array size 12 (indices 0..11):
dp[0] = True

Stone 2:
  dp[2] |= dp[0] = True
  dp = [T,F,T,F,F,F,F,F,F,F,F,F]

Stone 7:
  s from 11 down to 7: dp[7] |= dp[0] = True, dp[8] |= dp[1] = F, ...
  dp[7] = True
  dp = [T,F,T,F,F,F,F,T,F,F,F,F]

Stone 4:
  dp[4] |= dp[0] = True, dp[6] |= dp[2] = True, dp[11] |= dp[7] = True
  dp = [T,F,T,F,T,F,T,T,F,F,F,T]

Stone 1:
  dp[1] |= dp[0] = True, dp[3] |= dp[2] = True, dp[5] |= dp[4] = True,
  dp[7] |= dp[6] = True (already), dp[8] |= dp[7] = True,
  dp[10] |= dp[9] = F, dp[11] |= dp[10] = F
  dp = [T,T,T,T,T,T,T,T,T,F,F,T]

Stone 8:
  dp[8] |= dp[0] = True (already), dp[9] |= dp[1] = True,
  dp[10] |= dp[2] = True, dp[11] |= dp[3] = True
  dp = [T,T,T,T,T,T,T,T,T,T,T,T]

Stone 1:
  dp[1..11] all True now.

Find largest s <= 11 with dp[s]=True: s = 11.
Answer = 23 - 2*11 = 1. ✓
```

---

## Best Answer to Memorize

```python
def lastStoneWeightII(stones):
    total = sum(stones)
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for stone in stones:
        for s in range(target, stone - 1, -1):
            if dp[s - stone]:
                dp[s] = True
    for s in range(target, -1, -1):
        if dp[s]:
            return total - 2 * s
    return total
```

**~10 lines. O(n * total) time. O(total) space. Interview-ready!**

---

## Key Insights

### Why partition = smash?
> "Each smash subtracts one stone from another. The final remaining weight
> is the absolute difference between two groups of stones. This is exactly
> the partition problem."

### Why target = total // 2?
> "We want sum(A) close to sum(B). Since sum(A) + sum(B) = total, the
> ideal sum(A) = total/2. By limiting to target = total//2, we find the
> largest achievable sum <= total/2, which gives the smallest answer."

### Why iterate dp in reverse?
> "To use each stone AT MOST ONCE. Forward iteration would let one stone
> contribute multiple times (knapsack vs subset sum)."

### Why dp[0] = True?
> "Zero stones form sum 0. Base case."

### Why total - 2*s?
> "If subset sum = s, then other subset sum = total - s.
> Difference = |s - (total-s)| = |total - 2s|."

### What's the connection to Partition Equal Subset Sum (LC 416)?
> "LC 416 asks if partition into EQUAL halves is possible (return bool).
> This problem asks for MINIMUM DIFFERENCE (return int).
> Same DP, different objective."

---

## Test Cases

| stones | Expected | Notes |
|--------|----------|-------|
| [2,7,4,1,8,1] | 1 | Standard |
| [31,26,33,21,40] | 5 | LeetCode |
| [1,2] | 1 | Two stones |
| [1] | 1 | Single |
| [5,5] | 0 | Two equal |
| [5,5,5] | 5 | Three equal |
| [1,1,1,1] | 0 | Four ones |
| [10,20] | 10 | Two unequal |
| [1,2,3,4,5] | 1 | total=15, closest subset=7, diff=1 |
| [3,3,3,3] | 0 | Four equal |
| [1,2,4,8] | 1 | Powers of 2 |
| [1,3,5,7] | 0 | Balanced |

---

## Common Pitfalls

1. **Forward iteration in dp**: Causes using same stone multiple times.
2. **Forgetting dp[0] = True**: Base case essential.
3. **Off-by-one in target**: total // 2 is correct (we want closest, not exceeding).
4. **Wrong partition interpretation**: It's |sum(A) - sum(B)|, not max(s) - min(s).
5. **Forgetting edge case total = 0**: Returns 0 correctly with the algorithm.

---

## Why This Problem Matters

> "Tests:
> 1. Problem reframe (smash game -> partition).
> 2. Subset sum DP (0/1 knapsack variant).
> 3. Reverse iteration technique.
> 4. Foundation for: Partition Equal Subset Sum, Min Difference Subset."

---

## Beyond This Problem: Related Patterns

### 1. Partition Equal Subset Sum (LC 416)
```python
# Boolean version: can we partition into equal halves?
# Same DP, just check dp[total//2] == True.
```

### 2. Minimum Difference Between Largest and Smallest in Subset
```python
# Different problem, similar subset exploration.
```

### 3. Target Sum (LC 494)
```python
# Assign + or - to each element, count ways to reach target.
# Equivalent to subset sum counting.
```

### 4. Last Stone Weight (LC 1046) - the simpler version
```python
# Without optimization: always smash largest two.
# Uses heap, not DP.
```

---

## Connection to Subset Sum / 0/1 Knapsack

This problem is "subset sum with optimization":

```
PATTERN:
- dp[s] = is sum s achievable?
- dp[0] = True. For each item, update in reverse.
- For "count ways": dp[i] += dp[i-c].
- For "min/max": dp[i] = min/max(dp[i], dp[i-c] + ...).

EXAMPLES:
- Coin Change (LC 322): min count.
- Coin Change II (LC 518): count ways.
- Partition Equal Subset Sum (LC 416): boolean.
- Last Stone Weight II (LC 1049): minimum difference.
```

---

## Quick Checklist

When given a similar problem:
- [ ] Can the problem be reframed as partition / subset sum?
- [ ] Define total and target.
- [ ] dp[s] = is sum s achievable? dp[0] = True.
- [ ] Iterate stones/items in outer loop.
- [ ] Iterate dp in REVERSE for 0/1 knapsack.
- [ ] Find optimal s and compute answer.
- [ ] Handle edge cases (single item, etc.).

---

## Mathematical Formulation

Let stones = [s_1, s_2, ..., s_n], total = sum(s_i).

```
dp[0] = True
dp[i] = True if exists j such that dp[i - s_j] = True (for some unprocessed stone)

Answer = min |total - 2*s| over all s with dp[s] = True
       = total - 2*max{s : s <= total/2 and dp[s] = True}
```

This is equivalent to finding the optimal partition A, B with sum(A) - sum(B)
minimized in absolute value.

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1049 - Last Stone Weight II](https://leetcode.com/problems/last-stone-weight-ii/)
