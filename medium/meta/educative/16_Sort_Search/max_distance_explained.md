# Magnetic Force Between Two Balls - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/magnetic-force-between-two-balls

## The Problem
```
You have baskets at given positions (integer array). Place m balls in the
baskets (one ball per basket) to maximize the minimum distance between any
two balls. Return that maximum minimum distance.

Examples:
    position=[1,2,3,4,7], m=3 -> 3 (place at 1, 4, 7. Min distance = 3.)
    position=[5,4,3,2,1,1000000000], m=2 -> 999999999

Constraints:
- 2 <= position.length <= 10^5
- 2 <= m <= position.length
- 0 <= position[i] <= 10^9
- positions are distinct.
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Place m balls in baskets to maximize the minimum pairwise distance.
This is the "maximize the minimum" pattern — classic binary search on answer.
```

### Step 2: The Trick
> "KEY INSIGHT: Binary search on the answer.
>
> For each candidate distance d, check feasibility: can we place m balls
> with all pairwise distances >= d?
>
> Feasibility check uses GREEDY placement: place each ball at the earliest
> position that's at least d from the previous ball. If we can place m
> balls greedily, d is feasible.
>
> Feasibility is monotone: if d works, all smaller d also work. So we can
> binary search."

### Step 3: Why greedy works for feasibility
> "Greedy uses the earliest positions. If greedy fits m balls, any other
> placement would also fit (since greedy leaves the most room for later
> balls).
>
> Conversely, if greedy fails to fit m balls, no placement works."

### Step 4: Algorithm
> "1. Sort positions.
> 2. Binary search d in [1, max-min].
> 3. For each d:
>    a. Greedy: count balls we can place with min distance d.
>    b. If count >= m, d is feasible.
> 4. Return largest feasible d."

### Step 5: Edge cases
> "- m == n: each basket gets a ball. Min distance = sorted diffs min.
> - m == 2: max distance = max - min.
> - All positions close: distance is small."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to place m balls in baskets to maximize the minimum distance between balls."

**Key Insight:**
> "Binary search on the answer. For each candidate distance d, check if m balls can fit with all pairwise distances >= d using greedy placement. Feasibility is monotone."

**Algorithm:**
> "1. Sort positions.
> 2. Binary search d in [1, max-min].
> 3. Feasibility check:
>    - count = 1, last = position[0].
>    - For each position, if position[i] - last >= d, place ball, update last.
>    - If count >= m, d is feasible.
> 4. Return largest feasible d."

**Why this works:**
> "Greedy placement uses minimum positions, leaving maximum room. If greedy
> fits m balls, any placement does. Binary search exploits monotonicity."

**Edge cases:**
- m == n: each basket gets a ball.
- m == 2: max - min.
- Single cluster: small distance.

**Complexity:**
- Time:  O(n log(max_position)) — binary search * O(n) per check.
- Space: O(1) extra.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Binary search on answer (BEST - Memorize!)
```python
def max_distance_1(position, m):
    position.sort()
    n = len(position)

    def feasible(d):
        count = 1
        last = position[0]
        for i in range(1, n):
            if position[i] - last >= d:
                count += 1
                last = position[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo
```

### Way 2: Verbose
### Way 3: Alternative binary search
### Way 4: Helper functions
### Way 5: Recursive
### Way 6: Class-based
### Way 7: bisect for placement
### Way 8: enumerate
### Way 9: itertools.islice
### Way 10: Lambda
### Way 11: functools.reduce
### Way 12: Cleaner
### Way 13: While True
### Way 14: Two-pointer
### Way 15: Memoize
### Way 16: Iterative placement
### Way 17: Lower bound binary search
### Way 18: Generator
### Way 19: Linear scan (replaced with binary search)
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | O(n log n)   |
| Educational        | Way 5    | Recursive    |
| Class-based        | Way 6    | OOP style    |
| Functional         | Way 11   | reduce       |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Binary search (Way 1) | O(n log(max-min)) | O(1) | Standard |
| Recursive (Way 5) | O(n log(max-min)) | O(log) | Stack overhead |
| Memoize (Way 15) | O(n log(max-min)) | O(distinct_d) | Cache hits |

---

## Walkthrough Example

```
position = [1, 2, 3, 4, 7]
m = 3

Step 1: Sort. Already sorted.

Step 2: Binary search d in [1, 6].

Step 3: Feasibility checks:

  d=4 (mid=(1+6+1)//2=4):
    Greedy: place at 1, 5? (no, position[1]=2 < 1+4=5)
    Place at 1, 7? (no, 2 < 5, 3 < 5, 4 < 5, but 7 >= 5)
    Place at 1, 7. count=2. Need 3. Not feasible.

  d=2 (mid=(1+3+1)//2=2):
    Greedy: place at 1, 3 (2 < 3, 3 >= 3, count=2, last=3), 5? (4 < 5, 7 >= 5, count=3, last=7).
    Place at 1, 3, 7. count=3 >= m. Feasible.

  d=3 (mid=(3+3+1)//2=3):
    Greedy: place at 1, 4 (2 < 4, 3 < 4, 4 >= 4, count=2, last=4), 7? (4 < 7, but 7 >= 7, count=3).
    Place at 1, 4, 7. count=3 >= m. Feasible.

Binary search narrows to d=3. Return 3.
```

---

## Best Answer to Memorize

```python
def max_distance(position, m):
    position.sort()
    n = len(position)

    def feasible(d):
        count = 1
        last = position[0]
        for i in range(1, n):
            if position[i] - last >= d:
                count += 1
                last = position[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo
```

**~12 lines. O(n log(max-min)) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why binary search on answer?
> "We want to MAXIMIZE a value (min distance). The feasibility function
> (can we fit m balls with min distance d?) is MONOTONE: if d works,
> all smaller d also work. Binary search exploits this."

### Why greedy for feasibility?
> "Greedy places each ball at the earliest valid position. This leaves
> maximum room for subsequent balls. If greedy fails, no placement works."

### Why (lo + hi + 1) // 2?
> "Standard trick to avoid infinite loop when lo < hi but we want the
> upper bound of feasible range."

### Why upper bound max - min?
> "If we have m=2 balls, the best is to place at min and max, giving
> distance max-min. For m>2, smaller. So max-min is a valid upper bound."

### What about m=2?
> "Just return max - min. The greedy always finds the two extremes."

### What if m = n?
> "Each basket gets a ball. Min distance = min gap between consecutive
> sorted positions."

---

## Test Cases

| position | m | Expected | Notes |
|----------|---|----------|-------|
| [1,2,3,4,7] | 3 | 3 | Standard |
| [5,4,3,2,1,10^9] | 2 | 10^9 - 1 | Two extremes |
| [1,2,3] | 3 | 1 | m == n |
| [1,5] | 2 | 4 | m == 2 |
| [1,2,3,4,5] | 3 | 2 | Evenly spaced |
| [1,2,3,10,11,12] | 2 | 11 | Two clusters |
| [1,5,9,10,15,20] | 3 | 9 | Spread out |
| [7,4,3,2,1] | 3 | 3 | Unsorted input |

---

## Common Pitfalls

1. **Not sorting**: Greedy needs sorted positions.
2. **Off-by-one in binary search**: Use (lo + hi + 1) // 2 with lo=mid or hi=mid-1.
3. **Wrong upper bound**: max-min is correct, not 10^9 (would be too slow).
4. **Greedy not optimal**: It IS optimal for feasibility (earliest positions leave most room).
5. **Forgetting m >= 2**: Constraint says m >= 2, so at least 2 balls.

---

## Why This Problem Matters

> "Tests:
> 1. Binary search on answer.
> 2. Greedy feasibility check.
> 3. Monotonicity exploitation.
> 4. Foundation for: Aggressive Cows, Koko Eating Bananas, etc."

---

## Beyond This Problem: Related Patterns

### 1. Aggressive Cows (LC 1552) — SAME PROBLEM
```python
# Identical problem with cows and stalls.
```

### 2. Koko Eating Bananas (LC 875)
```python
# Binary search on eating speed. Different metric.
```

### 3. Minimize Max Distance to Gas Station (LC 774)
```python
# Binary search on max distance.
```

### 4. Book Allocation Problem
```python
# Binary search on max pages per student.
```

---

## Connection to Binary Search on Answer

This problem is a classic "binary search on answer" problem:

```
PATTERN:
1. The answer is a value in [lo, hi].
2. Define a feasibility predicate f(d).
3. f is monotone: if f(d) is True, then f(d') is True for all d' <= d.
4. Binary search for the largest d with f(d) True.

EXAMPLES:
- This problem (max min distance).
- Koko Eating Bananas (min eating speed).
- Book Allocation (min max pages).
- Minimize Max Distance.
```

Master this pattern!

---

## Quick Checklist

When given a similar problem:
- [ ] Maximize or minimize? (max min distance here)
- [ ] Is there a feasibility predicate? (yes — can we fit m balls?)
- [ ] Is the predicate monotone? (yes — if d works, smaller d works)
- [ ] What's the search range? ([1, max-min])
- [ ] Greedy for feasibility? (yes — earliest positions)
- [ ] Why greedy works? (leaves most room)

---

## Mathematical Formulation

```
Given: sorted positions p_1 < p_2 < ... < p_n.
Goal: maximize d such that we can choose m positions with all pairwise distances >= d.

f(d) = True iff we can place m balls with min distance d.
f is monotone.

Greedy for f(d):
  Ball 1 at p_1.
  Ball i+1 at smallest p_j such that p_j >= last + d.
  If we can place m balls, f(d) = True.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1552 - Magnetic Force Between Two Balls](https://leetcode.com/problems/magnetic-force-between-two-balls/)
