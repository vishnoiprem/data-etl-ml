# Minimum Operations to Make All Array Elements Equal - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-operations-to-make-all-array-elements-equal

## The Problem
```
You are given an integer array nums and an integer array queries.
For each query q in queries, find the minimum number of operations to make
all elements of nums equal to q, where each operation can increment or
decrement an element by 1.

Return the result for each query.

Examples:
    nums=[3,1,6], queries=[4] -> [6]
    (|3-4| + |1-4| + |6-4| = 1+3+2 = 6)
    nums=[2,9,6], queries=[5,4] -> [8, 9]

Constraints:
- 1 <= nums.length, queries.length <= 10^5
- 1 <= nums[i], queries[i] <= 10^9
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
For each query q, total operations = sum of |nums[i] - q| across all i.
This is because each unit of distance requires one operation (±1).
```

### Step 2: The Trick
> "KEY INSIGHT: For sorted nums and a query q, split the array into:
> - Left elements (≤ q): contribute (q - left) each. Total: q*count - sum.
> - Right elements (> q): contribute (right - q) each. Total: sum - q*count.
>
> Use binary search (bisect_right) to find the split point.
> Use prefix sums for O(1) range sum queries.
>
> Each query is O(log n) after O(n log n) preprocessing."

### Step 3: Why split works
> "After sorting, the first idx elements are ≤ q and the rest are > q.
> Sum of (q - left_elem) over the left = q*idx - prefix[idx].
> Sum of (right_elem - q) over the right = (prefix[n] - prefix[idx]) - q*(n-idx)."

### Step 4: Algorithm
> "1. Sort nums.
> 2. Build prefix sum array prefix[0..n].
> 3. For each query q:
>    a. idx = bisect_right(nums, q).
>    b. left_ops = q*idx - prefix[idx].
>    c. right_ops = (prefix[n] - prefix[idx]) - q*(n-idx).
>    d. result.append(left_ops + right_ops).
> 4. Return result."

### Step 5: Edge cases
> "- q smaller than min: idx=0, all in right. ops = total_sum - q*n.
> - q larger than max: idx=n, all in left. ops = q*n - total_sum.
> - All nums equal: ops = |nums[0] - q| * n."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to compute, for each query q, the sum of |nums[i] - q| across all elements."

**Key Insight:**
> "After sorting nums and building prefix sums, I can compute this in O(log n) per query using binary search to split at the query value."

**Algorithm:**
> "1. Sort nums.
> 2. Build prefix sums.
> 3. For each query q:
>    a. idx = bisect_right(nums, q). Number of elements ≤ q.
>    b. Left ops = q*idx - prefix[idx].
>    c. Right ops = (prefix[n] - prefix[idx]) - q*(n-idx).
>    d. Append sum.
> 4. Return results."

**Why this works:**
> "For sorted nums, the first idx elements are ≤ q and the rest are > q.
> Sum of (q - left) = q*count - sum = q*idx - prefix[idx].
> Sum of (right - q) = sum - q*count = (prefix[n] - prefix[idx]) - q*(n-idx)."

**Edge cases:**
- q smaller than min: all in right.
- q larger than max: all in left.
- All nums equal: ops = |nums[0] - q| * n.

**Complexity:**
- Time:  O(n log n + m log n) = O((n+m) log n).
- Space: O(n) for prefix sums.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort + prefix sums + bisect (BEST - Memorize!)
```python
def min_operations_1(nums, queries):
    n = len(nums)
    nums.sort()
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]
    import bisect
    result = []
    for q in queries:
        idx = bisect.bisect_right(nums, q)
        left_ops = q * idx - prefix[idx]
        right_ops = (prefix[n] - prefix[idx]) - q * (n - idx)
        result.append(left_ops + right_ops)
    return result
```

### Way 2: Verbose
### Way 3: Brute force
### Way 4: Brute force with explicit loops
### Way 5: Pre-sort + brute force
### Way 6: With median note
### Way 7: numpy
### Way 8: Manual binary search
### Way 9: Class-based
### Way 10: map + brute force
### Way 11: Generator
### Way 12: One-pass prefix
### Way 13: accumulate
### Way 14: enumerate
### Way 15: Two-pointer concept
### Way 16: Most concise
### Way 17: bisect + sum (slow)
### Way 18: Memoize
### Way 19: Helper functions
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Many queries       | Way 1    | O(log n)/q   |
| Few queries        | Way 3    | Brute force  |
| numpy available    | Way 7    | Vectorized   |
| Educational        | Way 17   | Clear intent |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + bisect (Way 1) | O((n+m) log n) | O(n) | Best |
| Brute force (Way 3) | O(n*m) | O(1) | Slow for many queries |
| numpy (Way 7) | O(n*m) | O(n) | Vectorized |
| Memoize (Way 18) | O((n+m) log n) | O(unique_q) | If few unique queries |

---

## Walkthrough Example

```
nums = [3, 1, 6]
queries = [4]

Step 1: Sort nums.
sorted = [1, 3, 6]

Step 2: Build prefix sums.
prefix = [0, 1, 4, 10]

Step 3: For query q=4:
  idx = bisect_right([1, 3, 6], 4) = 2 (after 1, 3; before 6)
  left_ops = 4 * 2 - prefix[2] = 8 - 4 = 4
    (Left: 1 and 3. Distance from 4: 3 and 1. Sum = 4. ✓)
  right_ops = (prefix[3] - prefix[2]) - 4 * (3-2) = 6 - 4 = 2
    (Right: 6. Distance from 4: 2. Sum = 2. ✓)
  Total = 4 + 2 = 6

Result: [6]
```

```
nums = [2, 9, 6]
queries = [5, 4]

sorted = [2, 6, 9]
prefix = [0, 2, 8, 17]

For q=5:
  idx = bisect_right([2, 6, 9], 5) = 1 (after 2; before 6)
  left_ops = 5 * 1 - prefix[1] = 5 - 2 = 3 (|2-5|=3)
  right_ops = (17 - 2) - 5 * 2 = 15 - 10 = 5 (|6-5|+|9-5|=1+4=5)
  Total = 8

For q=4:
  idx = bisect_right([2, 6, 9], 4) = 1 (after 2; before 6)
  left_ops = 4 * 1 - 2 = 2 (|2-4|=2)
  right_ops = (17 - 2) - 4 * 2 = 15 - 8 = 7 (|6-4|+|9-4|=2+5=7)
  Total = 9

Result: [8, 9]
```

---

## Best Answer to Memorize

```python
def min_operations(nums, queries):
    n = len(nums)
    nums.sort()
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]
    import bisect
    result = []
    for q in queries:
        idx = bisect.bisect_right(nums, q)
        left_ops = q * idx - prefix[idx]
        right_ops = (prefix[n] - prefix[idx]) - q * (n - idx)
        result.append(left_ops + right_ops)
    return result
```

**~10 lines. O((n+m) log n) time. O(n) space. Interview-ready!**

---

## Key Insights

### Why prefix sums?
> "After splitting, we need sum of left elements and sum of right elements.
> Prefix sums give O(1) range sums."

### Why bisect_right (not bisect_left)?
> "We want elements STRICTLY LESS than or equal to q in the left partition.
> bisect_right returns the insertion point after all elements ≤ q.
> Index = number of elements ≤ q."

### Why split at q?
> "All elements ≤ q contribute (q - x). All elements > q contribute (x - q).
> The split point is exactly q (or the position q would be inserted)."

### What if nums has duplicates?
> "Works fine. bisect_right returns the count of elements ≤ q (including duplicates)."

### What's the alternative to prefix sums?
> "Could use a binary indexed tree (Fenwick tree) for dynamic updates.
> But here, prefix sums suffice since nums is fixed."

---

## Test Cases

| nums | queries | Expected | Notes |
|------|---------|----------|-------|
| [3,1,6] | [4] | [6] | Standard |
| [2,9,6] | [5,4] | [8,9] | Two queries |
| [5] | [3] | [2] | Single element |
| [5] | [5] | [0] | Already equal |
| [5] | [10] | [5] | Increase |
| [3,3,3] | [5] | [6] | All same |
| [1,2,3] | [1,2,3,4,5] | [3,2,3,6,9] | Many queries |
| [1,2,3] | [] | [] | Empty queries |
| [5,10,15] | [1] | [27] | q smaller |
| [5,10,15] | [20] | [30] | q larger |
| [1,4,7,10] | [3,5,8] | [14,12,14] | Larger |
| [1,1,1,1] | [0,1,2,3] | [4,0,4,8] | All same, many queries |

---

## Common Pitfalls

1. **bisect_left vs bisect_right**: Use bisect_right to include all elements ≤ q.
2. **Off-by-one in prefix**: prefix[i] = sum of nums[0..i-1], not nums[0..i].
3. **Forgetting to sort**: bisect requires sorted input.
4. **Modifying nums in place**: Sort modifies, use copy or sorted().
5. **Empty queries**: Return [] correctly.

---

## Why This Problem Matters

> "Tests:
> 1. Sort + binary search + prefix sums (multi-technique).
> 2. Sum of absolute differences.
> 3. Range queries with split point.
> 4. Foundation for: median problems, range queries, prefix sums."

---

## Beyond This Problem: Related Patterns

### 1. Minimum Moves to Equal Array (LC 462)
```python
# Sum |nums[i] - median|. Single query, find optimal q.
```

### 2. Sum of Absolute Differences (LC 1685)
```python
# For each i, sum |nums[i] - nums[j]| for j != i. Different formula.
```

### 3. Best Meeting Point (different problem)
```python
# Manhattan distance median trick.
```

### 4. Find Median from Data Stream (LC 295)
```python
# HEAP-based median finding for streaming data.
```

---

## Connection to Prefix Sums + Binary Search

This problem combines two classic techniques:

```
PREFIX SUMS:
  prefix[i] = sum of first i elements.
  Range sum [a, b) = prefix[b] - prefix[a].
  Used here to get sum of left or right partition in O(1).

BINARY SEARCH (bisect):
  Find split point in sorted array in O(log n).
  Used here to find where q would be inserted.
```

Together: O(log n) per query after O(n log n) preprocessing.

---

## Quick Checklist

When given a similar problem:
- [ ] What's the metric? (sum of |nums[i] - q|)
- [ ] Can we sort? (yes — binary search needs sorted)
- [ ] Need O(1) range sums? (prefix sums)
- [ ] Split point via binary search? (bisect_right)
- [ ] Handle empty queries? (return [])
- [ ] Edge case: q outside nums range?

---

## Mathematical Formulation

For sorted array `a` with prefix `p` of length `n+1`:

```
Let idx = bisect_right(a, q) = #{i : a[i] <= q}.

For i < idx: contribution = q - a[i], sum = q*idx - p[idx].
For i >= idx: contribution = a[i] - q, sum = (p[n] - p[idx]) - q*(n-idx).

Total ops for query q = q*idx - p[idx] + (p[n] - p[idx]) - q*(n-idx).
```

Edge cases:
- idx = 0: all elements > q. ops = p[n] - q*n.
- idx = n: all elements ≤ q. ops = q*n - p[n].

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 3107 - Minimum Operations to Make Array Equal](https://leetcode.com/problems/minimum-operations-to-make-array-equal/) (newer version)
