# Counting Bits - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/counting-bits

## The Problem
```
For each x in [0, n], return an array ans where ans[x] = number of 1 bits in x.

Examples:
    n=2 -> [0, 1, 1]
    n=5 -> [0, 1, 1, 2, 1, 2]

Constraints:
- 0 <= n <= 10^4
```

## How I Think (The Mental Process)

### Step 1: Understand
```
For each x from 0 to n, count 1s in binary representation.
Output array of length n+1.
```

### Step 2: The Trick
> "KEY INSIGHT: popcount(x) = popcount(x & (x-1)) + 1.
>
> x & (x-1) clears the LOWEST set bit. So popcount(x) = popcount(x with
> lowest bit removed) + 1 (for that bit)."

### Step 3: Alternative recurrences
```
- dp[x] = dp[x >> 1] + (x & 1).  (drop last bit, add last bit)
- dp[x] = dp[x - lowest_power_of_2] + 1.
```

### Step 4: Algorithm
> "1. dp[0] = 0.
> 2. For x in 1..n: dp[x] = dp[x & (x-1)] + 1.
> 3. Return dp."

### Step 5: Edge cases
> "- n=0: return [0].
> - All x <= n have at most log2(n)+1 bits."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to compute the number of 1 bits for each integer from 0 to n."

**Key Insight:**
> "Recurrence: popcount(x) = popcount(x & (x-1)) + 1. The expression x & (x-1) clears the lowest set bit, so removing it reduces popcount by exactly 1."

**Algorithm:**
> "1. dp[0] = 0.
> 2. For i from 1 to n: dp[i] = dp[i & (i-1)] + 1.
> 3. Return dp."

**Why this works:**
> "Each iteration removes one set bit. The count of removals = count of set bits."

**Edge cases:**
- n=0: return [0].
- Just call bin(x).count('1') for small n.

**Complexity:**
- Time:  O(n).
- Space: O(n) for dp array.

---

## The 20 Implementations (Simple to Complex)

### Way 1: DP with x & (x-1) (BEST - Memorize!)
```python
def counting_bits_1(n):
    dp = [0] * (n + 1)
    for x in range(1, n + 1):
        dp[x] = dp[x & (x - 1)] + 1
    return dp
```

### Way 2: DP with x >> 1
### Way 3: bin().count('1') brute
### Way 4: DP with x & -x (lowest power of 2)
### Way 5: Brute force popcount loop
### Way 6: Class-based
### Way 7: numpy vectorized
### Way 8: Recursive memo
### Way 9: lru_cache decorator
### Way 10: Helper function popcount
### Way 11: bit_length trick
### Way 12: BFS-style with x & -x
### Way 13: Lookup table for 8-bit chunks
### Way 14: Python 3.10+ bit_count
### Way 15: Divide by 2 loop
### Way 16: format string conversion
### Way 17: Doubling pattern
### Way 18: One-liner DP
### Way 19: Functional map
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | x & (x-1)    |
| Python 3.10+       | Way 14   | bit_count    |
| Small n            | Way 3    | Brute        |
| NumPy              | Way 7    | Vectorized   |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| DP x & (x-1) (Way 1) | O(n) | O(n) | Best |
| bin().count('1') (Way 3) | O(n * log n) | O(n) | Slow |
| bit_count (Way 14) | O(n) | O(n) | Python 3.10+ |

---

## Walkthrough Example

```
n=5
dp = [0, 0, 0, 0, 0, 0]

i=1: dp[1 & 0] + 1 = dp[0] + 1 = 1. dp = [0, 1, 0, 0, 0, 0]
i=2: dp[2 & 1] + 1 = dp[0] + 1 = 1. dp = [0, 1, 1, 0, 0, 0]
i=3: dp[3 & 2] + 1 = dp[2] + 1 = 2. dp = [0, 1, 1, 2, 0, 0]
i=4: dp[4 & 3] + 1 = dp[0] + 1 = 1. dp = [0, 1, 1, 2, 1, 0]
i=5: dp[5 & 4] + 1 = dp[4] + 1 = 2. dp = [0, 1, 1, 2, 1, 2]

Result: [0, 1, 1, 2, 1, 2]. ✓
```

---

## Best Answer to Memorize

```python
def counting_bits(n):
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = dp[i & (i - 1)] + 1
    return dp
```

**~5 lines. O(n) time. O(n) space. Interview-ready!**

---

## Key Insights

### Why x & (x-1)?
> "It clears the LOWEST set bit. popcount drops by exactly 1. So popcount(x) = popcount(x & (x-1)) + 1."

### Why is x & (x-1) useful?
> "Brian Kernighan's algorithm uses this to count set bits in O(popcount) time per number. Here we use it for DP."

### Alternative: x >> 1 + (x & 1)?
> "Drop the last bit, look up its count, then add the new last bit. Same complexity, slightly different recurrence."

### Why base case dp[0] = 0?
> "Zero has zero set bits. Natural base case."

---

## Test Cases

| n | Expected | Notes |
|---|----------|-------|
| 0 | [0] | Just 0 |
| 1 | [0, 1] | n=1 |
| 2 | [0, 1, 1] | Standard |
| 5 | [0, 1, 1, 2, 1, 2] | Standard |
| 8 | [0,1,1,2,1,2,2,3,1] | Power of 2 |
| 10 | [0,1,1,2,1,2,2,3,1,2,2] | n=10 |

---

## Common Pitfalls

1. **Forgetting dp[0] = 0**: Base case needed.
2. **Wrong recurrence**: Use x & (x-1), not x & (x+1) or others.
3. **Off-by-one**: Range should be 1..n inclusive.
4. **IndexError**: dp array of size n+1 handles x=0..n.

---

## Why This Problem Matters

> "Tests:
> 1. Bit manipulation.
> 2. DP with simple recurrence.
> 3. Foundation for: Hamming distance, parity, bit problems."

---

## Beyond This Problem: Related Patterns

### 1. Hamming Distance (LC 461)
```python
# Number of different bits between two numbers.
# x.bit_count() ^ y.bit_count() or compute popcount(x ^ y).
```

### 2. Power of Two (LC 231)
```python
# n is power of 2 iff n & (n-1) == 0 (for n > 0).
```

### 3. Single Number (LC 136)
```python
# XOR-based, different but related to bit manipulation.
```

### 4. Total Hamming Distance (LC 477)
```python
# Sum of Hamming distances across all pairs.
```

---

## Connection to Bit Manipulation DP

This problem is the simplest bit manipulation DP:

```
PATTERN:
- State: x.
- Recurrence: popcount(x) = popcount(x & (x-1)) + 1.
- Base: popcount(0) = 0.
- Iterate x from 1 to n.

RELATED:
- Compute popcount in O(popcount) time per number.
- DP makes total O(n) for n numbers.
```

---

## Quick Checklist

When given a similar problem:
- [ ] Identify the bit recurrence.
- [ ] dp[0] = 0 as base case.
- [ ] Iterate x from 1 to n.
- [ ] Use x & (x-1) or x >> 1.
- [ ] O(n) total time.
- [ ] Return dp array.

---

## Mathematical Formulation

```
dp[0] = 0
dp[x] = dp[x & (x-1)] + 1 for x >= 1

Equivalent: popcount(x) = number of times we can apply x & (x-1) before reaching 0.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 338 - Counting Bits](https://leetcode.com/problems/counting-bits/)
