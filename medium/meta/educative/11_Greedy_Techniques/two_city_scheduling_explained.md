# Two City Scheduling - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/two-city-scheduling

## The Problem
```
Send n people to two cities A and B, exactly n/2 each, minimizing total cost.
costs[i] = [costA_i, costB_i].

Examples:
    [[10,20],[30,200],[400,50],[30,20]] -> 110
    [[259,770],[448,54],[926,667],[184,139],[840,118],[577,469]] -> 1859

Constraints:
- 2 <= costs.length <= 100, even
- 1 <= costA, costB <= 1000
```

## How I Think (The Mental Process)

### Step 1: Understand
```
We must send each person to exactly one of two cities. The constraint is
exactly n/2 to each city. Find the assignment minimizing total cost.
```

### Step 2: The Trick
> "KEY INSIGHT: Greedy with sorting by SAVINGS.
>
> For each person, compute the SAVINGS of sending them to city A vs B:
>   savings_i = costB_i - costA_i (positive = prefer A)
>
> Send everyone to A first (n/2 of them), then re-evaluate. The n/2 we
> send to B should be those with the LARGEST costA - costB (i.e., biggest
> 'penalties' if sent to A, meaning they prefer B the most).
>
> Equivalently: sort by (costA - costB) ASCENDING. First n/2 → A.
> Rest → B."

### Step 3: Why this works
> "Imagine sending everyone to A. The cost savings from sending
> person i to B instead is (costA_i - costB_i). We want to pick the n/2
> people with the LARGEST savings to switch to B. That's exactly sorting
> by (costA - costB) and taking the LAST n/2 to switch (or equivalently,
> keeping the FIRST n/2 at A)."

### Step 4: Algorithm
> "1. Sort costs by (costA - costB) ASCENDING.
> 2. Sum costA for the first n/2 people.
> 3. Sum costB for the remaining n/2 people.
> 4. Return total."

### Step 5: Edge cases
> "- n == 0: return 0.
> - All costs equal: any split works.
> - 2 people: pick cheaper for each."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to send n/2 people to each of two cities, minimizing total cost."

**Key Insight:**
> "Sort people by (costA - costB). Those with the smallest difference prefer city A. Send first n/2 to A, the rest to B."

**Algorithm:**
> "1. Sort the array by (costA - costB) ascending.
> 2. Sum costA[i] for i in 0..n/2-1.
> 3. Sum costB[i] for i in n/2..n-1.
> 4. Return total."

**Why this works:**
> "Imagine sending everyone to A. Switching person i to B saves (costA - costB). The n/2 with biggest savings should switch. Sorting ascending then taking first n/2 keeps the people with smallest (or negative) savings at A."

**Edge cases:**
- Empty list: 0.
- n == 2: pick cheapest assignment.

**Complexity:**
- Time:  O(n log n) for sort.
- Space: O(n) for sorted copy.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort by savings (BEST - Memorize!)
```python
def two_city_scheduling(costs):
    n = len(costs)
    costs_sorted = sorted(costs, key=lambda x: x[0] - x[1])
    total = 0
    for i, (a, b) in enumerate(costs_sorted):
        total += a if i < n // 2 else b
    return total
```

### Way 2: Sort + explicit slicing
### Way 3: Sort descending variant
### Way 4: Brute force combinations
### Way 5: Class-based
### Way 6: Heap-based
### Way 7: 2D DP
### Way 8: Recursive
### Way 9: numpy vectorized
### Way 10: zip/unpack style
### Way 11: lru_cache decorator
### Way 12: Comparison key
### Way 13: Stable partition
### Way 14: Generator
### Way 15: operator module
### Way 16: Tabulation DP
### Way 17: Counter priority
### Way 18: Explicit half
### Way 19: Sort + reduce
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | Sort + greedy |
| Small n, can brute | Way 4    | O(2^n) check  |
| DP preference      | Way 7    | 2D DP         |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + greedy (Way 1) | O(n log n) | O(n) | Best |
| Brute force (Way 4) | O(2^n) | O(n) | Slow |
| 2D DP (Way 7) | O(n^2) | O(n^2) | Alternative |

---

## Walkthrough Example

```
costs = [[10,20],[30,200],[400,50],[30,20]]
n = 4, half = 2

Compute diffs (a - b):
  [10-20, 30-200, 400-50, 30-20] = [-10, -170, 350, 10]

Sort ascending: [-170, -10, 10, 350]
  → [30,200], [10,20], [30,20], [400,50]

First 2 go to A: 30 + 10 = 40
Last 2 go to B: 20 + 50 = 70
Total: 40 + 70 = 110 ✓
```

---

## Best Answer to Memorize

```python
def twoCitySchedCost(costs):
    costs.sort(key=lambda x: x[0] - x[1])
    return sum(c[0] for c in costs[:len(costs)//2]) + sum(c[1] for c in costs[len(costs)//2:])
```

**~3 lines. O(n log n) time. O(1) extra space. Interview-ready!**

---

## Key Insights

### Why sort by (costA - costB)?
> "Each person's 'preference' for A is the diff. Sorting ascending places those with strongest A-preference (most negative diff) first."

### Why first n/2 to A?
> "These people have the smallest (or most negative) differences, meaning sending them to A is cheapest. The rest prefer B."

### Why not DP?
> "DP works but is O(n^2). The greedy is provably optimal because the constraint is exactly n/2 each, and sorting ranks people optimally."

### What's the alternative insight?
> "Imagine sending all to A, then choose n/2 to switch to B based on biggest savings. Same result."

---

## Test Cases

| costs | Expected | Notes |
|-------|---------|-------|
| [[10,20],[30,200],[400,50],[30,20]] | 110 | Standard |
| LeetCode sample | 1859 | Real-world |
| [[1,2],[3,4],[5,6],[7,8]] | 18 | Linear |
| Equal costs | sum | No preference |
| Strong preference | min | Each to pref |
| Two people | min | Pair-wise |

---

## Common Pitfalls

1. **Sort direction**: ASCENDING by (costA - costB), not descending.
2. **Boundary**: Exactly n/2 to each city, not "at most".
3. **Empty list**: Return 0.
4. **Sample data**: For LeetCode, expected is 1859 for the sample.

---

## Why This Problem Matters

> "Tests:
> 1. Greedy with sorting by custom key.
> 2. Recognizing 'savings' formulation.
> 3. Foundation for: assignment problems, k-way splits."

---

## Beyond This Problem: Related Patterns

### 1. Three-Way Partition (LC 462 variant)
```python
# Similar sort-and-select pattern.
```

### 2. Assign Cookies (LC 455)
```python
# Greedy with sorting.
```

### 3. K-Send Problem
```python
# Generalize: send to k cities, each k/n size.
```

### 4. Hungarian Algorithm
```python
# For truly balanced assignment with costs matrix.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1029 - Two City Scheduling](https://leetcode.com/problems/two-city-scheduling/)