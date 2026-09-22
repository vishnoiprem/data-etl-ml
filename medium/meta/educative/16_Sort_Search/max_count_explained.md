# Maximum Number of Integers to Choose from a Range I - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-number-of-integers-to-choose-from-a-range-i

## The Problem
```
Given banned (array), n, max_sum, find max count of integers in [1, n]
such that:
- Each chosen at most once.
- Not in banned.
- Sum <= max_sum.

Examples:
    banned=[2,4], n=5, max_sum=4 -> 2 (pick 1, 3)
    banned=[1,6,5], n=5, max_sum=6 -> 2 (pick 2, 3 or 2, 4)

Constraints:
- 1 <= banned.length <= 10^3
- 1 <= banned[i], n <= 10^3
- 1 <= max_sum <= 10^6
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We want MAXIMUM COUNT, which means MINIMUM SUM per integer.
So we should pick the SMALLEST integers first.
```

### Step 2: The Trick
> "KEY INSIGHT: Greedy works. Pick the smallest available integers.
>
> Why? Picking smaller numbers leaves more budget for more numbers. To
> maximize count, we want to minimize the per-element sum."

### Step 3: Algorithm
> "1. Convert banned to a set for O(1) lookup.
> 2. Iterate i from 1 to n in increasing order.
> 3. Skip if i is banned.
> 4. If current_sum + i > max_sum, BREAK (larger i won't fit either).
> 5. Otherwise, add i and increment count."

### Step 4: Edge cases
> "- All banned: return 0.
> - max_sum < 1: return 0.
> - First non-banned i already > max_sum: return 0.
> - Empty banned, n large, max_sum large: pick everything."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the maximum count of integers from [1, n], excluding banned, with sum <= max_sum."

**Key Insight:**
> "Greedy: pick the smallest available integers. To maximize count, we want minimum sum, which means smallest integers."

**Algorithm:**
> "1. Convert banned to set for O(1) lookup.
> 2. Iterate i from 1 to n in increasing order.
> 3. Skip banned. Break if can't afford. Otherwise add."

**Why greedy works:**
> "Picking smaller numbers leaves more budget. Since we want max count with sum constraint, smaller is better."

**Edge cases:**
- All banned: 0.
- max_sum too small: 0.
- Empty banned with enough budget: pick all.

**Complexity:**
- Time:  O(n + |banned|).
- Space: O(|banned|) for set.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Greedy + set (BEST - Memorize!)
```python
def max_count_1(banned, n, max_sum):
    banned_set = set(banned)
    count = 0
    current_sum = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        if current_sum + i > max_sum:
            break
        current_sum += i
        count += 1
    return count
```

### Way 2: Verbose
### Way 3: Brute force subsets
### Way 4: Sort + iterate
### Way 5: Sort + bisect
### Way 6: Class-based
### Way 7: numpy
### Way 8: While loop
### Way 9: enumerate
### Way 10: Helper functions
### Way 11: Functional filter
### Way 12: One-liner
### Way 13: Binary search on k
### Way 14: Counting sort
### Way 15: Generator
### Way 16: accumulate
### Way 17: reduce
### Way 18: List comprehension
### Way 19: Most pythonic
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | Greedy + set |
| Small n            | Way 3    | Brute force  |
| numpy              | Way 7    | Vectorized   |
| Large n, complex   | Way 13   | Binary search|
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Greedy (Way 1) | O(n + |banned|) | O(|banned|) | Best |
| Brute force (Way 3) | O(2^n) | O(n) | Too slow |
| Binary search (Way 13) | O(n log n) | O(n) | Alternative |

---

## Walkthrough Example

```
banned = [2, 4]
n = 5
max_sum = 4

Step 1: banned_set = {2, 4}.

Step 2: Iterate i = 1 to 5.
  i=1: not banned. total=0, 0+1=1 <= 4. total=1, count=1.
  i=2: banned. skip.
  i=3: not banned. total=1, 1+3=4 <= 4. total=4, count=2.
  i=4: banned. skip.
  i=5: not banned. total=4, 4+5=9 > 4. BREAK.

Return 2.
```

---

## Best Answer to Memorize

```python
def maxCount(banned, n, max_sum):
    banned_set = set(banned)
    count = 0
    total = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        if total + i > max_sum:
            break
        total += i
        count += 1
    return count
```

**~10 lines. O(n + |banned|) time. O(|banned|) space. Interview-ready!**

---

## Key Insights

### Why greedy?
> "To maximize COUNT, we want MINIMUM SUM. Smallest integers give minimum sum."

### Why early break?
> "We're iterating in increasing order. If current_sum + i > max_sum, then
> for any j > i, current_sum + j >= current_sum + i + 1 > max_sum.
> So no future i can fit. Break."

### Why use a set?
> "O(1) membership check. Sorted list with bisect is O(log n), still fine
> but set is cleaner."

### Why count sum as we go?
> "We need to check sum constraint after each pick. Maintaining running sum
> avoids recomputing."

### What if n is huge?
> "Greedy still O(n). For larger constraints, consider binary search on the
> answer (count) and computing the sum of smallest k non-banned integers."

---

## Test Cases

| banned | n | max_sum | Expected | Notes |
|--------|---|---------|----------|-------|
| [2,4] | 5 | 4 | 2 | Standard |
| [1,6,5] | 5 | 6 | 2 | Standard |
| [1,2,3,4] | 7 | 4 | 0 | Small max_sum |
| [] | 5 | 15 | 5 | All fit |
| [] | 5 | 10 | 4 | Sum 1+2+3+4 |
| [10] | 10 | 100 | 9 | Single banned |
| [1..5] | 5 | 10 | 0 | All banned |
| [] | 10 | 0 | 0 | No budget |
| [] | 10 | 1 | 1 | Pick 1 |

---

## Common Pitfalls

1. **Not using a set**: O(n) lookup with list is slow for many queries.
2. **Forgetting to skip banned**: Iterate through ALL i, not just non-banned.
3. **No early break**: Wasteful when sum exceeds early.
4. **Modifying banned in place**: Use copy or set construction.
5. **Off-by-one**: Range is 1..n inclusive.

---

## Why This Problem Matters

> "Tests:
> 1. Greedy selection under constraints.
> 2. Set lookup optimization.
> 3. Early termination.
> 4. Foundation for: knapsack variants, subset selection."

---

## Beyond This Problem: Related Patterns

### 1. Maximum Number of Integers in Range II (LC 2557)
```python
# Same but with larger constraints (n, max_sum up to 10^9).
# Uses binary search on answer.
```

### 2. Coin Change (LC 322)
```python
# Greedy works for canonical coin systems.
```

### 3. Maximum Count of Positive/Negative Sum
```python
# Different problem variant.
```

### 4. Subset Sum (LC 416)
```python
# Different: target exact sum, not constraint.
```

---

## Connection to Greedy + Constraint

This problem is a classic greedy + constraint:

```
PATTERN:
1. Define "value per cost" or "min cost for max benefit".
2. Pick items in order of best ratio.
3. Skip excluded items.
4. Stop when constraint violated.

EXAMPLES:
- This problem (max count = min sum per item).
- Fractional knapsack.
- Activity selection.
```

The greedy choice "smallest first" works because the objective
(MAX COUNT) and constraint (sum <= max_sum) are aligned: smaller
items contribute less to the sum, allowing more items.

---

## Quick Checklist

When given a similar problem:
- [ ] What's the objective? (max count, max value, min cost)
- [ ] What's the constraint? (sum <= max_sum, weight <= limit)
- [ ] Does greedy work? (here: smallest first minimizes sum)
- [ ] What data structure for fast lookup? (here: set)
- [ ] Early break possible? (here: yes, since i grows)
- [ ] Edge cases: empty/all banned, max_sum too small

---

## Mathematical Formulation

Given banned set B, n, max_sum:

```
Find max |S| where:
- S ⊆ {1, 2, ..., n}
- S ∩ B = ∅
- sum(S) <= max_sum

Solution: Greedily pick smallest elements.
Let S* = {i ∈ [1, n] : i ∉ B, i ≤ i_max}, where i_max is the largest i
such that sum of first |S*| elements <= max_sum.

|S*| = max count.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 2557 - Maximum Number of Integers to Choose From a Range I](https://leetcode.com/problems/maximum-number-of-integers-to-choose-from-a-range-i/)