# Count Pairs in Two Arrays - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/count-pairs-in-two-arrays

## The Problem
```
Given two integer arrays nums1 and nums2 of length n, count pairs (i, j)
with i < j such that nums1[i] + nums1[j] > nums2[i] + nums2[j].

Examples:
    nums1=[2,4,6], nums2=[1,3,5] -> 3
    nums1=[1,2,3], nums2=[4,5,6] -> 0

Constraints:
- 1 <= n <= 10^3
- 1 <= nums1[i], nums2[i] <= 10^4
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We need to count pairs (i, j) with i < j where the sum of nums1 values
exceeds the sum of nums2 values at those indices.
```

### Step 2: The Trick
> "KEY INSIGHT: Rearrange the inequality.
>
> nums1[i] + nums1[j] > nums2[i] + nums2[j]
> (nums1[i] - nums2[i]) + (nums1[j] - nums2[j]) > 0
> diff[i] + diff[j] > 0
>
> Define diff[k] = nums1[k] - nums2[k]. We need to count pairs where
> the sum of two diffs is strictly positive."

### Step 3: Sort and binary search
> "After sorting diff in ascending order, for each i, we need to count
> how many j > i satisfy diff[j] > -diff[i].
>
> Since diff is sorted, all valid j's form a contiguous suffix. Find
> the leftmost such j with binary search (bisect_right for STRICT >)."

### Step 4: Algorithm
> "1. Compute diff[i] = nums1[i] - nums2[i] for each i.
> 2. Sort diff.
> 3. For each i from 0 to n-2:
>    a. idx = bisect_right(diff, -diff[i]).
>    b. valid count = n - max(idx, i+1).
>    c. Add to result.
> 4. Return result."

### Step 5: Edge cases
> "- n == 1: no pairs possible.
> - All diff zero: 0 pairs (strict > fails).
> - All diff positive: all pairs work.
> - All diff negative: 0 pairs.
> - diff[i] very negative: many valid j's (everything > i)."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to count pairs (i, j) with i < j where nums1[i] + nums1[j] > nums2[i] + nums2[j]."

**Key Insight:**
> "Rearrange to (nums1[i] - nums2[i]) + (nums1[j] - nums2[j]) > 0. Define diff[k] = nums1[k] - nums2[k]. Now count pairs where diff[i] + diff[j] > 0."

**Algorithm:**
> "1. Build and sort diff array.
> 2. For each i, binary search for first j where diff[j] > -diff[i].
> 3. Count j's from there to the end (skipping j <= i)."

**Why this works:**
> "For sorted diff, valid j's form a contiguous suffix. bisect_right finds the boundary; everything to the right is valid."

**Edge cases:**
- n == 1: return 0.
- All diff zero: 0 (strict >).
- All diff positive: C(n, 2) pairs.
- Mixed: depends on values.

**Complexity:**
- Time:  O(n log n) — sort dominates.
- Space: O(n) for diff.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort + bisect_right (BEST - Memorize!)
```python
def count_pairs_1(nums1, nums2):
    import bisect
    n = len(nums1)
    diff = sorted([nums1[i] - nums2[i] for i in range(n)])
    count = 0
    for i in range(n - 1):
        idx = bisect.bisect_right(diff, -diff[i])
        start = max(idx, i + 1)
        count += n - start
    return count
```

### Way 2: Verbose
### Way 3: Brute force O(n^2)
### Way 4: Brute force with diff
### Way 5: bisect_left (alternative)
### Way 6: Class-based
### Way 7: numpy
### Way 8: bisect with lo/hi bounds
### Way 9: enumerate
### Way 10: Helper functions
### Way 11: map + lambda
### Way 12: Functional with sum
### Way 13: Manual binary search
### Way 14: functools.reduce
### Way 15: Negated diff variant
### Way 16: while loop binary search
### Way 17: itertools.starmap
### Way 18: numpy fully vectorized
### Way 19: Recursive
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | Sort + bisect|
| Few pairs          | Way 3    | Brute force  |
| numpy available    | Way 18   | Vectorized   |
| Educational        | Way 13   | Manual BS    |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + bisect (Way 1) | O(n log n) | O(n) | Best |
| Brute force (Way 3) | O(n^2) | O(1) | Simple but slow |
| numpy (Way 18) | O(n log n) | O(n) | Vectorized |

---

## Walkthrough Example

```
nums1 = [2, 4, 6]
nums2 = [1, 3, 5]

Step 1: Compute diff = [1, 1, 1].

Step 2: Sort. diff = [1, 1, 1].

Step 3: For each i, find j where diff[j] > -diff[i] = -1.

  i=0: bisect_right([1,1,1], -1) = 0. start = max(0, 1) = 1. count += 3-1 = 2.
  i=1: bisect_right([1,1,1], -1) = 0. start = max(0, 2) = 2. count += 3-2 = 1.
  i=2: skip (n-1 = 2, so i=2 is out of range).

Total = 3. ✓
```

```
nums1 = [2, 3, 4, 5]
nums2 = [5, 4, 3, 2]

diff = [-3, -1, 1, 3]
sorted = [-3, -1, 1, 3]

For each i:
  i=0: target=3. bisect_right(diff, 3) = 4. start = max(4, 1) = 4. count += 0.
  i=1: target=1. bisect_right(diff, 1) = 3. start = max(3, 2) = 3. count += 1.
  i=2: target=-1. bisect_right(diff, -1) = 2. start = max(2, 3) = 3. count += 1.

Total = 2.
```

---

## Best Answer to Memorize

```python
def count_pairs(nums1, nums2):
    import bisect
    n = len(nums1)
    diff = sorted(nums1[i] - nums2[i] for i in range(n))
    count = 0
    for i in range(n - 1):
        idx = bisect.bisect_right(diff, -diff[i])
        start = max(idx, i + 1)
        count += n - start
    return count
```

**~8 lines. O(n log n) time. O(n) space. Interview-ready!**

---

## Key Insights

### Why rearrange the inequality?
> "The form nums1[i] + nums1[j] > nums2[i] + nums2[j] couples the
> two arrays. By moving all to one side, we decouple them into a
> single diff array. This is the standard 'reduction' technique."

### Why bisect_right (not bisect_left)?
> "We need STRICT inequality: diff[j] > -diff[i]. bisect_right returns
> the first index where arr[idx] > target. bisect_left would give us
> >=, which incorrectly includes diff[j] = -diff[i] (not strictly greater)."

### Why max(idx, i+1)?
> "We need j > i, but bisect might return an index <= i. The constraint
> i < j means we only count j's strictly after i."

### Why sort?
> "After sorting, all valid j's form a contiguous suffix. We can find
> the boundary with binary search in O(log n)."

### What if diff is unsorted?
> "We MUST sort. Without sorting, we'd need O(n) per query to find valid j's,
> giving O(n^2) total. Sorting + bisect is O(n log n)."

---

## Test Cases

| nums1 | nums2 | Expected | Notes |
|-------|-------|----------|-------|
| [2,4,6] | [1,3,5] | 3 | Standard |
| [5] | [3] | 0 | n=1 |
| [3,5,7] | [3,5,7] | 0 | All diff zero |
| [5,6,7] | [1,2,3] | 3 | All diff positive |
| [1,2,3] | [5,6,7] | 0 | All diff negative |
| [2,3,4,5] | [5,4,3,2] | 2 | Mixed |
| [1,5,9] | [9,5,1] | 1 | One positive, others zero/negative |
| [3,3,3,3] | [1,1,1,1] | 6 | All same |
| [2,5] | [3,4] | 0 | Equal sums (strict fails) |

---

## Common Pitfalls

1. **Using bisect_left**: Returns first index where arr[idx] >= target. We need > not >=.
2. **Forgetting j > i**: bisect might return idx <= i; use max(idx, i+1).
3. **Not sorting**: bisect requires sorted input.
4. **Integer overflow**: diff values can be -10^4 to 10^4, no overflow in Python.
5. **n == 1**: Loop range(n-1) = range(0) is empty, returns 0 correctly.

---

## Why This Problem Matters

> "Tests:
> 1. Algebraic rearrangement (key insight).
> 2. Sort + binary search pattern.
> 3. Strict vs non-strict inequality.
> 4. Boundary handling (j > i).
> 5. Foundation for: pair counting problems, two-sum variants."

---

## Beyond This Problem: Related Patterns

### 1. Two Sum (LC 1)
```python
# Different: find pairs equal to target, not greater than.
```

### 2. Count Pairs Whose Sum is Less Than Target
```python
# Same pattern, different inequality.
```

### 3. Count of Smaller Numbers After Self (LC 315)
```python
# For each i, count j > i with nums[j] < nums[i]. Use BIT or merge sort.
```

### 4. 3Sum (LC 15)
```python
# Three-sum, sort + two-pointer.
```

---

## Connection to Pair Counting Patterns

This problem is a classic pair counting problem:

```
PATTERN:
1. Reduce to diff array.
2. Sort.
3. For each i, binary search for valid j.
4. Sum counts.

EXAMPLES:
- This problem (sum of pairs > 0).
- Two Sum (sum == target).
- Count of Smaller Numbers After Self (j > i, nums[j] < nums[i]).
```

The algebraic rearrangement is the key insight that makes this tractable.

---

## Quick Checklist

When given a similar problem:
- [ ] Rearrange the inequality algebraically
- [ ] Define diff or transformed array
- [ ] Sort for efficient boundary finding
- [ ] Use bisect_right for STRICT >, bisect_left for >=
- [ ] Handle j > i constraint
- [ ] Edge case: n == 1
- [ ] Edge case: all equal (strict > fails)

---

## Mathematical Formulation

For sorted array `diff` of length n, and a query value `target = -diff[i]`:

```
Let idx = bisect_right(diff, target) = #{j : diff[j] > target}.

For position i, valid j's are: max(idx, i+1), max(idx, i+1)+1, ..., n-1.

Number of valid j's: n - max(idx, i+1).

Total pairs: sum over all i of this count.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1885 - Count Pairs in Two Arrays](https://leetcode.com/problems/count-pairs-in-two-arrays/)
