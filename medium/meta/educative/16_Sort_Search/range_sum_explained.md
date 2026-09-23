# Range Sum of Sorted Subarray Sums - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/range-sum-of-sorted-subarray-sums

## The Problem
```
Given an integer array nums of positive integers and two integers left, right.
Calculate the sum of every non-empty continuous subarray of nums.
Collect these sums into an array, sort in nondecreasing order.
Return the sum of elements from index left to right (1-indexed, inclusive)
modulo 10^9 + 7.

Examples:
    nums=[1,2,3,4], n=4, left=1, right=5 -> 13
    (Subarray sums: [1,2,3,3,4,5,6,7,9,10]. Sum of indices 0-4 = 13.)
    nums=[1,2,3,4], n=4, left=3, right=4 -> 6

Constraints:
- 1 <= n <= 1000
- 1 <= nums[i] <= 100
- 1 <= left <= right <= n*(n+1)/2
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
There are n*(n+1)/2 non-empty continuous subarrays.
For each, compute its sum.
Sort all sums.
Take the sum of the (left-1)-th through (right-1)-th elements (0-indexed).
Apply mod.
```

### Step 2: The Trick
> "KEY INSIGHT: For each starting index i, extend the subarray from j=i
> to j=n-1. Use a RUNNING SUM so each subarray sum is computed in O(1).
>
> Total: n*(n+1)/2 sums. Sort them in O(n^2 log n). Take the slice."

### Step 3: Why running sum
> "Without running sum, each subarray sum is O(j-i+1). Total: O(n^3).
> With running sum: extend j from i, accumulate. Each step O(1). Total: O(n^2)."

### Step 4: Algorithm
> "1. sums = [].
> 2. For i in 0..n-1:
>      s = 0.
>      For j in i..n-1:
>        s += nums[j].
>        sums.append(s).
> 3. Sort sums.
> 4. Return sum(sums[left-1:right]) % 10^9+7."

### Step 5: 1-indexed vs 0-indexed
> "The problem uses 1-indexed left and right. Convert to 0-indexed by
> left-1 and right (right exclusive in Python slice)."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to compute all n*(n+1)/2 subarray sums, sort them, then sum a
> specific range from the sorted array (mod 10^9+7)."

**Key Insight:**
> "Use a running sum to compute each subarray sum in O(1). Then sort and slice."

**Algorithm:**
> "1. Collect all subarray sums using a running sum (start at each index, extend).
> 2. Sort the sums.
> 3. Return sum of sums[left-1:right] mod 10^9+7."

**Why this works:**
> "After sorting, the (left-1)-th through (right-1)-th (0-indexed) elements
> are exactly what we need."

**Edge cases:**
- left == right: single element.
- Single element array: only one subarray.
- left = 1, right = n*(n+1)/2: sum of all subarrays.

**Complexity:**
- Time:  O(n^2 log n).
- Space: O(n^2) for sums.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Brute force collect + sort (BEST - simple to remember)
```python
def range_sum_1(nums, n, left, right):
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums.append(s)
    sums.sort()
    return sum(sums[left - 1:right]) % MOD
```

### Way 2: Verbose
### Way 3: Prefix sums
### Way 4: List comprehension
### Way 5: With running sum
### Way 6: Class-based
### Way 7: itertools.accumulate
### Way 8: numpy
### Way 9: Generator
### Way 10: enumerate
### Way 11: Helper function
### Way 12: Functional with map
### Way 13: Prefix built once
### Way 14: Most pythonic (slice)
### Way 15: Pre-allocate
### Way 16: Most concise
### Way 17: Heap note (partial sort)
### Way 18: bisect note
### Way 19: Explicit range loop
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Simple/clean       | Way 1    | Most pythonic|
| Fast subarray sum  | Way 3    | Prefix sums  |
| numpy available    | Way 8    | Vectorized   |
| Educational        | Way 14   | Slice-based  |
+--------------------+----------+--------------|
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Running sum + sort (Way 1) | O(n^2 log n) | O(n^2) | Standard |
| Prefix sum (Way 3) | O(n^2 log n) | O(n^2) | Same |
| numpy (Way 8) | O(n^2 log n) | O(n^2) | Vectorized |
| Heap partial (Way 17) | O(n^2 log(right)) | O(n^2) | If right << n^2 |

---

## Walkthrough Example

```
nums = [1, 2, 3, 4]
n = 4
left = 1, right = 5

Step 1: Collect subarray sums.
  i=0: 1, 1+2=3, 1+2+3=6, 1+2+3+4=10
  i=1: 2, 2+3=5, 2+3+4=9
  i=2: 3, 3+4=7
  i=3: 4
  All: [1, 3, 6, 10, 2, 5, 9, 3, 7, 4]

Step 2: Sort.
  [1, 2, 3, 3, 4, 5, 6, 7, 9, 10]

Step 3: Take slice [left-1..right-1] = [0..4].
  [1, 2, 3, 3, 4]

Step 4: Sum.
  1 + 2 + 3 + 3 + 4 = 13

Result: 13
```

```
nums = [1, 2, 3, 4, 5]
n = 5
left = 1, right = 15 (sum all)

Step 1: Collect subarray sums.
  15 subarrays total.

Step 2: Sort.
  [1, 2, 3, 3, 4, 5, 5, 6, 7, 9, 9, 10, 12, 14, 15]

Step 3: Sum all.
  1+2+3+3+4+5+5+6+7+9+9+10+12+14+15 = 105

Result: 105
```

---

## Best Answer to Memorize

```python
def range_sum(nums, n, left, right):
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums.append(s)
    sums.sort()
    return sum(sums[left - 1:right]) % MOD
```

**~7 lines. O(n^2 log n) time. O(n^2) space. Interview-ready!**

---

## Key Insights

### Why running sum?
> "For each start i, extend j from i to n-1. The running sum keeps track of
> the cumulative sum, so each new subarray sum is computed in O(1) instead
> of O(j-i+1)."

### Why convert 1-indexed to 0-indexed?
> "Problem uses 1-indexed (left=1 means first element). Python uses 0-indexed.
> Convert: left-1 for start (inclusive), right for end (exclusive)."

### Why mod at the end?
> "Intermediate sums can be large. Apply mod only at the very end to avoid
> overflow (Python handles big ints natively, but for clarity and safety)."

### Why full sort?
> "For n <= 1000, full sort is fast. For larger n, partial sort (heap) might
> be needed if right << n^2."

### What's the alternative to collecting all sums?
> "Could use a min-heap of size 'right' to keep only the smallest sums seen.
> But for n=1000, simple approach is fine."

---

## Test Cases

| nums | n | left | right | Expected | Notes |
|------|---|------|-------|----------|-------|
| [1,2,3,4] | 4 | 1 | 5 | 13 | Standard |
| [1,2,3,4] | 4 | 3 | 4 | 6 | Middle |
| [5] | 1 | 1 | 1 | 5 | Single |
| [1,2] | 2 | 1 | 3 | 6 | All |
| [1,2,3] | 3 | 2 | 2 | 2 | Single element |
| [5,1,2] | 3 | 4 | 4 | 5 | After sort |
| [1,2,3,4,5] | 5 | 1 | 15 | 105 | Sum all |
| [1,2,3,4,5] | 5 | 4 | 10 | 39 | Middle range |
| [2,2,2] | 3 | 1 | 6 | 20 | All same |

---

## Common Pitfalls

1. **Off-by-one in indexing**: 1-indexed to 0-indexed conversion.
2. **Forgetting running sum**: Recomputing each sum makes it O(n^3).
3. **Modulo placement**: Apply mod at the end (Python handles big ints).
4. **Sorting direction**: Nondecreasing — smallest to largest.
5. **Empty array**: Not in constraints but defensive coding helps.

---

## Why This Problem Matters

> "Tests:
> 1. Subarray enumeration.
> 2. Running sum technique.
> 3. Sorting + slicing.
> 4. Modular arithmetic.
> 5. Foundation for: range queries, prefix sums."

---

## Beyond This Problem: Related Patterns

### 1. Sum of Subarray Minimums (LC 907)
```python
# Different formula: count contributions of each element.
```

### 2. Range Sum Query 2D (LC 304)
```python
# 2D prefix sums for rectangular sums.
```

### 3. Subarray Sum Equals K (LC 560)
```python
# Count subarrays with sum == k. Use hashmap.
```

### 4. Maximum Subarray (LC 53)
```python
# Kadane's algorithm - different problem.
```

---

## Connection to Subarray Enumeration

This problem uses the classic subarray enumeration pattern:

```
For each start i in 0..n-1:
  For each end j in i..n-1:
    Process subarray nums[i..j].

Total: n*(n+1)/2 subarrays.
With running sum: O(n^2) total work.
With naive recomputation: O(n^3).
```

The running sum trick is essential for O(n^2) subarray problems.

---

## Quick Checklist

When given a similar problem:
- [ ] How many subarrays? (n*(n+1)/2)
- [ ] What metric? (sum)
- [ ] Can we use running sum? (yes — extend from start)
- [ ] Need to sort? (yes — for this problem)
- [ ] Need to slice? (left-1 to right)
- [ ] Modulo? (apply at end)

---

## Mathematical Formulation

```
Let S = set of all subarray sums.
After sorting: S_sorted[0] <= S_sorted[1] <= ... <= S_sorted[n*(n+1)/2 - 1].

Result = sum(S_sorted[i] for i in [left-1, right-1]) mod 10^9 + 7.
```

Total subarrays = n*(n+1)/2.

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1508 - Range Sum of Sorted Subarray Sums](https://leetcode.com/problems/range-sum-of-sorted-subarray-sums/)
