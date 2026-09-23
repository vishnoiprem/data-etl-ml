# Climbing Stairs - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/climbing-stairs

## The Problem
```
Climb a staircase of n steps. Each move: 1 or 2 steps.
How many distinct ways to reach the top?

Examples:
    n=2 -> 2 (1+1, 2)
    n=3 -> 3 (1+1+1, 1+2, 2+1)

Constraints:
- 1 <= n <= 45
```

## How I Think (The Mental Process)

### Step 1: Understand
```
Count distinct paths to reach step n where each step is +1 or +2.
```

### Step 2: The Trick
> "KEY INSIGHT: This is the Fibonacci sequence.
>
> To reach step n, the last move was either:
> - a 1-step from step n-1 (contributes dp[n-1] ways), or
> - a 2-step from step n-2 (contributes dp[n-2] ways).
>
> dp[n] = dp[n-1] + dp[n-2]
> dp[0] = 1 (empty staircase), dp[1] = 1"

### Step 3: Why this works
> "The recurrence holds because the last move classifies paths into two disjoint groups. Adding the counts gives total paths."

### Step 4: Algorithm
> "Iterate from 2 to n:
>   prev, cur = cur, prev + cur
> Return cur.
>
> Or use a DP array of size n+1."

### Step 5: Edge cases
> "- n=0: return 1 (empty staircase, one way).
> - n=1: return 1 (only one 1-step).
> - n=2: return 2."

---

## What to Say Aloud in the Interview

**Opening:**
> "This is a classic Fibonacci DP. Each step is reachable from 1 or 2 steps below."

**Key Insight:**
> "dp[n] = dp[n-1] + dp[n-2], with dp[0]=dp[1]=1."

**Algorithm:**
> "Two variables prev, cur track the last two values. Each iteration: prev, cur = cur, prev + cur."

**Why this works:**
> "Paths ending in a 1-step = dp[n-1] ways. Paths ending in a 2-step = dp[n-2] ways. Total = sum."

**Edge cases:**
- n=0, n=1: return 1.
- Overflow: Python ints are arbitrary precision.

**Complexity:**
- Time:  O(n).
- Space: O(1) for the iterative version.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Iterative Fibonacci (BEST - Memorize!)
```python
def climb_stairs_1(n):
    if n <= 1:
        return 1
    prev, cur = 1, 2
    for i in range(2, n):
        prev, cur = cur, prev + cur
    return cur
```

### Way 2: DP array
```python
def climb_stairs_2(n):
    if n <= 1:
        return 1
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]
```

### Way 3: Recursion with memo
### Way 4: Brute force recursion (no memo)
### Way 5: Matrix exponentiation (O(log n))
### Way 6: Class-based
### Way 7: numpy vectorized
### Way 8: lru_cache decorator
### Way 9: Tail-recursive style
### Way 10: Helper functions
### Way 11: Generator
### Way 12: enumerate
### Way 13: Binet's formula (closed form)
### Way 14: Reduce style
### Way 15: Verbose with explicit prev/curr
### Way 16: While loop
### Way 17: Itertools.accumulate
### Way 18: Fibonacci helper
### Way 19: Stateful
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | O(n) time, O(1) space |
| Huge n (n > 1e18)  | Way 5    | O(log n) with matrix |
| Closed form        | Way 13   | Binet's formula |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Iterative (Way 1) | O(n) | O(1) | Best |
| DP array (Way 2) | O(n) | O(n) | Less efficient |
| Matrix exp (Way 5) | O(log n) | O(1) | For huge n |
| Brute recursion (Way 4) | O(2^n) | O(n) | Exponential |

---

## Walkthrough Example

```
n = 5

dp[0] = 1, dp[1] = 1
dp[2] = dp[1] + dp[0] = 1 + 1 = 2  (paths: 1+1, 2)
dp[3] = dp[2] + dp[1] = 2 + 1 = 3  (paths: 1+1+1, 1+2, 2+1)
dp[4] = dp[3] + dp[2] = 3 + 2 = 5  (paths: 1+1+1+1, 1+1+2, 1+2+1, 2+1+1, 2+2)
dp[5] = dp[4] + dp[3] = 5 + 3 = 8

Answer: 8
```

---

## Best Answer to Memorize

```python
def climbStairs(n):
    if n <= 1:
        return 1
    prev, cur = 1, 2
    for _ in range(2, n):
        prev, cur = cur, prev + cur
    return cur
```

**~6 lines. O(n) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why Fibonacci?
> "The recurrence dp[n] = dp[n-1] + dp[n-2] mirrors Fibonacci. Each step depends on the previous two."

### Why O(1) space?
> "Only the last two values are needed. Use prev and cur variables."

### What about k steps (not just 1 or 2)?
> "Same pattern: dp[n] = dp[n-1] + dp[n-2] + ... + dp[n-k]. Becomes a sliding window of size k."

### What if we count MODULO?
> "Take mod 10^9+7 at each step to avoid huge numbers. Common variant in contests."

---

## Test Cases

| n | Expected | Notes |
|---|----------|-------|
| 1 | 1 | Single step |
| 2 | 2 | 1+1 or 2 |
| 3 | 3 | |
| 4 | 5 | |
| 5 | 8 | |
| 10 | 89 | |
| 45 | 1836311903 | Max constraint |

---

## Common Pitfalls

1. **Off-by-one**: dp[0]=1, dp[1]=1. Don't confuse with standard Fibonacci F(0)=0, F(1)=1.
2. **Recursion limit**: Brute force recursion crashes Python's stack for n>30.
3. **Initialization**: prev=1, cur=2 (representing dp[0]=1, dp[1]=1, dp[2]=2).
4. **Range**: Use `range(2, n)` not `range(2, n+1)` when working with cur as dp[n].

---

## Why This Problem Matters

> "Tests:
> 1. Recognizing Fibonacci pattern.
> 2. O(1) space optimization (rolling variables).
> 3. Foundation for: climbing stairs with variable steps, decode ways, etc."

---

## Beyond This Problem: Related Patterns

### 1. Climbing Stairs with k steps
```python
# dp[n] = sum(dp[n-1], dp[n-2], ..., dp[n-k])
# Use sliding window of size k.
```

### 2. Decode Ways (LC 91)
```python
# Same Fibonacci recurrence on digit strings.
```

### 3. Fibonacci Number (LC 509)
```python
# Direct Fibonacci computation.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 70 - Climbing Stairs](https://leetcode.com/problems/climbing-stairs/)
