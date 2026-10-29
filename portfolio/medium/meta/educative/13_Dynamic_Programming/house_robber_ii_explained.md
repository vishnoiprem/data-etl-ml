# House Robber II - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/house-robber-ii

## The Problem
```
Houses in a circle. Rob max money without robbing two adjacent houses.
First and last houses are neighbors.

Examples:
    [2,3,2] -> 3 (rob house 1 or 2)
    [1,2,3,1] -> 4 (rob houses 1 and 3)
    [0,0] -> 0

Constraints:
- 1 <= n <= 10^3
- 0 <= money[i] <= 10^3
```

## How I Think (The Mental Process)

### Step 1: Understand
```
Standard House Robber, but with wraparound: house 0 and house n-1 are adjacent.
```

### Step 2: The Trick
> "KEY INSIGHT: Two cases.
>
> - Case 1: Don't rob the last house -> solve House Robber I on money[0..n-2].
> - Case 2: Don't rob the first house -> solve House Robber I on money[1..n-1].
>
> Answer = max of both cases.
>
> Why? In any valid solution, at least one of the two endpoint houses is skipped."

### Step 3: Why this works
> "Since the array is circular, house 0 and house n-1 cannot both be robbed. They form a partition: skip the first OR skip the last. Each case reduces to the linear House Robber problem."

### Step 4: Algorithm
> "1. Apply House Robber I to money[:-1] (skip last).
> 2. Apply House Robber I to money[1:] (skip first).
> 3. Return max of both.
>
> House Robber I: dp[i] = max(dp[i-1], dp[i-2] + money[i]) with rolling variables."

### Step 5: Edge cases
> "- n=0: return 0.
> - n=1: return money[0] (only one house).
> - n=2: return max(money) (can't rob both)."

---

## What to Say Aloud in the Interview

**Opening:**
> "This is House Robber but on a circle. First and last houses can't both be robbed."

**Key Insight:**
> "Split into two linear subproblems: skip first OR skip last. Take the max."

**Algorithm:**
> "1. Linear rob on money[1:].
> 2. Linear rob on money[:-1].
> 3. max of both.
>
> Linear rob: prev, cur = 0, 0; for x in arr: prev, cur = cur, max(cur, prev+x); return cur."

**Why this works:**
> "On a circle, the two endpoint houses partition the problem. Either we skip the first or we skip the last, never both robber paths overlap."

**Edge cases:**
- n=1: only one house, rob it.
- n=2: pick the bigger house.

**Complexity:**
- Time:  O(n).
- Space: O(1) for the iterative rob.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Two House Robber I calls (BEST - Memorize!)
```python
def house_robber_1(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob(arr):
        prev, cur = 0, 0
        for x in arr:
            prev, cur = cur, max(cur, prev + x)
        return cur

    return max(rob(money[:-1]), rob(money[1:]))
```

### Way 2: DP on both ranges
### Way 3: Memoized recursion
### Way 4: 2D DP
### Way 5: Skip first / skip last
### Way 6: Class-based
### Way 7: numpy vectorized
### Way 8: lru_cache decorator
### Way 9: Include/exclude variables
### Way 10: Helper functions
### Way 11: n==2 check
### Way 12: enumerate + DP
### Way 13: Tabulation
### Way 14: Compact
### Way 15: State machine
### Way 16: Rolling vars
### Way 17: Recursion with caching
### Way 18: Brute force (bitmask)
### Way 19: Single array DP
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard circular  | Way 1    | O(n) O(1)    |
| Need clarity       | Way 5    | Explicit cases |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Two calls (Way 1) | O(n) | O(1) | Best |
| Brute force (Way 18) | O(n * 2^n) | O(n) | Exponential |

---

## Walkthrough Example

```
money = [2, 3, 2]

Case 1: money[1:] = [3, 2]
  - Rob 3: total = 3
  - Skip 3, rob 2: total = 2
  - Max: 3

Case 2: money[:-1] = [2, 3]
  - Rob 2: total = 2
  - Rob 3: total = 3
  - Max: 3

Answer: max(3, 3) = 3
```

---

## Best Answer to Memorize

```python
def rob(nums):
    n = len(nums)
    if n == 0: return 0
    if n == 1: return nums[0]

    def rob_linear(arr):
        prev, cur = 0, 0
        for x in arr:
            prev, cur = cur, max(cur, prev + x)
        return cur

    return max(rob_linear(nums[:-1]), rob_linear(nums[1:]))
```

**~10 lines. O(n) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why two subproblems?
> "In a circular array, you can't rob both endpoints. So either you skip the first or you skip the last. Each is a linear House Robber."

### Why O(1) space?
> "Each subproblem only needs the previous two DP values. Use rolling variables."

### What about triple circle (k=3)?
> "Generalize: pick 3 partition indices that exclude pairwise-adjacent houses. More complex."

### What about House Robber III (binary tree)?
> "Use DP on tree nodes with two states: robbed or skipped. DP[node][0/1]."

---

## Test Cases

| money | Expected | Notes |
|-------|----------|-------|
| [2,3,2] | 3 | Standard |
| [1,2,3,1] | 4 | Standard 2 |
| [0,0] | 0 | Both zero |
| [5] | 5 | Single |
| [1,2] | 2 | Two houses |
| [] | 0 | Empty |

---

## Common Pitfalls

1. **Empty array**: Handle n==0 separately.
2. **Single house**: Return money[0], not max of nothing.
3. **Two houses**: Can't rob both; just return max.
4. **Confusion**: Don't try to handle the circular constraint directly; split into two linear cases.

---

## Why This Problem Matters

> "Tests:
> 1. Reduction technique (circular -> linear).
> 2. Recognizing House Robber I subproblems.
> 3. Foundation for: variable constraints, k-houses apart, etc."

---

## Beyond This Problem: Related Patterns

### 1. House Robber I (LC 198)
```python
# Linear version. Same recurrence.
```

### 2. House Robber III (LC 337)
```python
# Tree version. DP with two states per node.
```

### 3. Paint House (LC 256)
```python
# Three colors instead of adjacent constraint.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 213 - House Robber II](https://leetcode.com/problems/house-robber-ii/)
