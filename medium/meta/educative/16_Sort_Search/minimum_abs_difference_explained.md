# Minimum Absolute Difference - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-absolute-difference

## The Problem
```
Given an integer array arr, find the minimum absolute difference between any
two distinct elements. Return a list of all pairs [x, y] with x < y that
achieve this minimum. Pairs must be in ascending order.

Examples:
    arr=[-10,-4,-1,2,9] -> [[-4,-1], [-1,2]]
    (sorted: -10,-4,-1,2,9. Diffs: 6,3,3,7. Min=3. Adjacent pairs with min: (-4,-1),(-1,2))
    arr=[1,3,6,19,20] -> [[19,20]]

Constraints:
- 2 <= arr.length <= 10^5
- -10^6 <= arr[i] <= 10^6
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Find all pairs with the minimum absolute difference between any two distinct
elements. Return pairs in ascending order.
```

### Step 2: The Trick
> "KEY INSIGHT: After sorting, the minimum absolute difference can ONLY
> occur between ADJACENT elements.
>
> Proof: if arr[i] and arr[j] have the smallest diff with j > i+1, then
> arr[i+1] (which is between them) has diff with arr[i] smaller than
> arr[j] - arr[i] (since arr[i+1] is closer). Contradiction.
>
> So we only need to scan adjacent pairs in O(n) after sorting."

### Step 3: Algorithm
> "1. Sort arr.
> 2. First pass: min_diff = min(arr[i+1] - arr[i]).
> 3. Second pass: collect all [arr[i], arr[i+1]] with diff == min_diff."

### Step 4: Edge cases
> "- Two elements: only one pair.
> - Duplicates: min diff = 0, all equal adjacent pairs.
> - Negatives: sorting handles naturally.
> - Already sorted: works correctly."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find all pairs with the minimum absolute difference between any two distinct elements."

**Key Insight:**
> "After sorting, the minimum absolute difference can ONLY occur between adjacent elements. This reduces O(n^2) brute force to O(n) scan after sorting."

**Algorithm:**
> "1. Sort the array.
> 2. First pass: compute min_diff = min(arr[i+1] - arr[i]).
> 3. Second pass: collect all adjacent pairs with that diff."

**Why this works:**
> "For sorted arr, |arr[j] - arr[i]| = arr[j] - arr[i] for j > i. If arr[i] and arr[j] (j > i+1) achieve the min, then arr[i+1] is between them and has a smaller (or equal) diff with arr[i]. So the min must be between adjacent elements."

**Edge cases:**
- Two elements: only one pair.
- Duplicates: diff = 0, equal adjacent pairs.
- Negatives: works automatically.

**Complexity:**
- Time:  O(n log n) — sort dominates.
- Space: O(n) for result.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort + scan (BEST - Memorize!)
```python
def minimum_abs_difference_1(arr):
    arr.sort()
    n = len(arr)
    min_diff = float('inf')
    for i in range(n - 1):
        min_diff = min(min_diff, arr[i + 1] - arr[i])
    result = []
    for i in range(n - 1):
        if arr[i + 1] - arr[i] == min_diff:
            result.append([arr[i], arr[i + 1]])
    return result
```

### Way 2: Verbose
### Way 3: Brute force (using adjacent convention)
### Way 4: Single pass
### Way 5: zip with adjacent pairs
### Way 6: Class-based
### Way 7: numpy
### Way 8: enumerate
### Way 9: zip + min
### Way 10: Helper functions
### Way 11: Functional map
### Way 12: One-liner
### Way 13: itertools.pairwise
### Way 14: While loop
### Way 15: reduce
### Way 16: enumerate tracking min
### Way 17: Counter duplicates
### Way 18: Step-by-step
### Way 19: Single pass combined
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | Sort + scan  |
| Educational        | Way 4    | Single pass  |
| numpy available    | Way 7    | Vectorized   |
| Python 3.10+       | Way 13   | pairwise     |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + scan (Way 1) | O(n log n) | O(n) | Best |
| Single pass (Way 4) | O(n log n) | O(n) | Cleaner |
| Brute force (Way 3) | O(n^2) | O(n) | Too slow |

---

## Walkthrough Example

```
arr = [-10, -4, -1, 2, 9]

Step 1: Sort.
  sorted = [-10, -4, -1, 2, 9]

Step 2: First pass — find min_diff.
  i=0: -4 - (-10) = 6
  i=1: -1 - (-4) = 3
  i=2: 2 - (-1) = 3
  i=3: 9 - 2 = 7
  min_diff = 3

Step 3: Second pass — collect pairs with diff 3.
  i=0: 6 ≠ 3, skip.
  i=1: 3 == 3, add [-4, -1].
  i=2: 3 == 3, add [-1, 2].
  i=3: 7 ≠ 3, skip.

Result: [[-4, -1], [-1, 2]].
```

---

## Best Answer to Memorize

```python
def minimumAbsDifference(arr):
    arr.sort()
    min_diff = min(arr[i + 1] - arr[i] for i in range(len(arr) - 1))
    return [[arr[i], arr[i + 1]] for i in range(len(arr) - 1)
            if arr[i + 1] - arr[i] == min_diff]
```

**~4 lines. O(n log n) time. O(n) space. Interview-ready!**

---

## Key Insights

### Why sort first?
> "After sorting, only adjacent pairs can have the minimum difference. This
> reduces from O(n^2) to O(n) for the scanning phase."

### Why min can only be adjacent?
> "If arr[i] and arr[j] have min diff with j > i+1, then arr[i+1] is between
> them. Since arr[i+1] is closer to arr[i] than arr[j], arr[i+1] - arr[i] is
> smaller than arr[j] - arr[i]. Contradiction with min."

### Why two passes (or single pass with reset)?
> "We need the min BEFORE we know which pairs to collect. Two passes are
> clearest. Single pass with result reset is more elegant but trickier."

### Why duplicates give diff 0?
> "If arr has equal elements, the diff between them is 0, which is the
> smallest possible. All adjacent equal pairs qualify."

### What about negative numbers?
> "Sorting handles them naturally. The same logic applies."

---

## Test Cases

| arr | Expected | Notes |
|-----|----------|-------|
| [-10,-4,-1,2,9] | [[-4,-1],[-1,2]] | Standard |
| [1,3,6,19,20] | [[19,20]] | Standard |
| [1,2] | [[1,2]] | Two elements |
| [1,1,2,3] | [[1,1]] | Duplicates |
| [5,5,5] | [[5,5],[5,5]] | All same |
| [-5,-2,-1,0,3] | [[-2,-1],[-1,0]] | Negatives |
| [3,8,-9,1,2,-6,5] | [[1,2],[2,3]] | Larger |
| [1,2,4,5] | [[1,2],[4,5]] | Multiple pairs |

---

## Common Pitfalls

1. **Forgetting to sort**: bisect/scan requires sorted input.
2. **Wrong direction**: arr[i+1] - arr[i] (not absolute value since sorted).
3. **Using O(n^2) brute force**: Too slow for n = 10^5.
4. **Missing pairs**: Collecting only FIRST occurrence, not all with min.
5. **In-order output**: Pairs come out sorted if arr is sorted.

---

## Why This Problem Matters

> "Tests:
> 1. Sort + scan optimization.
> 2. Understanding why only adjacent pairs matter.
> 3. Two-pass vs single-pass approach.
> 4. Foundation for: closest pair, two-sum closest, range queries."

---

## Beyond This Problem: Related Patterns

### 1. Two Sum Closest (LC 16)
```python
# Find single pair closest to target.
```

### 2. Minimum Absolute Difference in BST (LC 530)
```python
# In-order traversal of BST.
```

### 3. Closest Pair of Points (divide and conquer)
```python
# Geometric version, O(n log n) with divide and conquer.
```

### 4. Smallest Difference of Two Arrays
```python
# Different: minimize diff between two arrays.
```

---

## Connection to Sort + Scan Pattern

This problem is the canonical "sort + scan" example:

```
PATTERN:
1. Sort the input.
2. After sorting, the property only holds for adjacent elements.
3. Scan adjacent pairs in O(n).
4. Collect result.

EXAMPLES:
- This problem (min abs diff).
- Max consecutive diff.
- Check for arithmetic progression.
- Detect duplicates (after sort).
```

The key insight is recognizing WHEN sorting reduces complexity from O(n^2) to O(n).

---

## Quick Checklist

When given a similar problem:
- [ ] Is there a min/max property between elements?
- [ ] Does the property only hold between adjacent (sorted) elements?
- [ ] Sort first, then scan adjacent pairs.
- [ ] Edge case: duplicates (diff = 0).
- [ ] Edge case: two elements.
- [ ] Two passes: find min, collect pairs.

---

## Mathematical Formulation

For sorted array `a` of length n:

```
Let D = min(a[i+1] - a[i]) for i in 0..n-2.

Result = { [a[i], a[i+1]] : a[i+1] - a[i] == D }.

The pairs are naturally sorted because the input is sorted.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1200 - Minimum Absolute Difference](https://leetcode.com/problems/minimum-absolute-difference/)