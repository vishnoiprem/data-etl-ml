# Find Target Indices After Sorting Array - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/find-target-indices-after-sorting-array

## The Problem
```
You are given a 0-indexed array nums of positive integers and a value target.

Return a sorted list of indices in the SORTED array where the value equals target.
If no such indices exist, return [].

Examples:
    nums=[1,2,5,2,3], target=2 -> [1, 2]
    (sorted: [1,2,2,3,5]. 2 is at indices 1, 2.)
    nums=[1,2,5,2,3], target=5 -> [4]
    nums=[1,2,5,2,3], target=4 -> []

Constraints:
- 1 <= nums.length <= 100
- 1 <= nums[i], target <= 100
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
The indices are in the SORTED array, not the original.
After sorting, all occurrences of target are contiguous.
So we want indices [left, left+1, ..., right] where left..right are target.
```

### Step 2: The Trick
> "KEY INSIGHT: After sorting, equal values are contiguous.
>
> Two approaches:
> 1. Sort + linear scan: just iterate and collect matching indices. Simple.
> 2. Sort + binary search: find leftmost (bisect_left) and rightmost (bisect_right).
>    Return range(left, right)."

### Step 3: Why it works
> "After sorting, all `target` values are at consecutive indices. Linear scan
> finds them all in O(n). Binary search finds boundaries in O(log n).
>
> For n <= 100 (small), linear scan is fine. For larger n, binary search wins."

### Step 4: Algorithm (linear scan)
> "1. Sort nums.
> 2. Iterate. Collect i where nums[i] == target."

### Step 5: Algorithm (binary search)
> "1. Sort nums.
> 2. left = bisect_left(nums, target).
> 3. right = bisect_right(nums, target).
> 4. If left == right: return [].
> 5. Return list(range(left, right))."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find all indices where the value equals target in the SORTED array."

**Key Insight:**
> "After sorting, all occurrences of target are contiguous. I can either:
> 1. Sort and linear scan.
> 2. Sort and use binary search (bisect_left, bisect_right) to find the range."

**Algorithm (linear scan):**
> "1. Sort nums.
> 2. Iterate and collect indices where nums[i] == target."

**Algorithm (binary search):**
> "1. Sort nums.
> 2. Find left = bisect_left(nums, target).
> 3. Find right = bisect_right(nums, target).
> 4. If left == right, target not present. Return [].
> 5. Return list(range(left, right))."

**Why this works:**
> "After sorting, equal elements are contiguous. Linear scan finds them all.
> Binary search finds the boundaries."

**Edge cases:**
- Target not in array: return [].
- All elements equal target: return [0, 1, ..., n-1].
- Single element equal to target: return [0].
- Empty array (constraint says n >= 1, but defensive).

**Complexity:**
- Time:  O(n log n) for sort, O(n) for scan.
- Space: O(1) extra (besides output).

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort + linear scan (BEST - Memorize!)
```python
def target_indices_1(nums, target):
    nums.sort()
    return [i for i, num in enumerate(nums) if num == target]
```

### Way 2: Verbose version
### Way 3: bisect range
### Way 4: bisect concise
### Way 5: Brute force with sort
### Way 6: Counter-based
### Way 7: Manual binary search
### Way 8: Find range manually
### Way 9: enumerate
### Way 10: Class-based
### Way 11: While loop
### Way 12: Generator
### Way 13: itertools.compress
### Way 14: numpy
### Way 15: filter+enumerate
### Way 16: One-liner
### Way 17: Sort with key
### Way 18: sorted() (returns new list)
### Way 19: Binary search + scan
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Simplest           | Way 1    | 2 lines      |
| Fastest            | Way 3/4  | Binary search|
| numpy available    | Way 14   | Vectorized   |
| Functional         | Way 12   | Generator    |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + scan (Way 1) | O(n log n) | O(1) | Cleanest |
| Sort + bisect (Way 3) | O(n log n) | O(n) | Range output |
| numpy (Way 14) | O(n log n) | O(n) | Vectorized |
| Counter (Way 6) | O(n log n) | O(n) | Cumulative sum |

---

## Walkthrough Example

```
nums = [1, 2, 5, 2, 3]
target = 2

Sort: nums = [1, 2, 2, 3, 5]

Approach 1 (Linear scan):
  i=0, num=1: skip
  i=1, num=2: collect 1
  i=2, num=2: collect 2
  i=3, num=3: skip
  i=4, num=5: skip
Result: [1, 2]

Approach 2 (Binary search):
  sorted = [1, 2, 2, 3, 5]
  left = bisect_left([1,2,2,3,5], 2) = 1
  right = bisect_right([1,2,2,3,5], 2) = 3
  range(1, 3) = [1, 2]
Result: [1, 2]
```

```
nums = [1, 2, 5, 2, 3]
target = 4

Sort: nums = [1, 2, 2, 3, 5]

Approach 2 (Binary search):
  left = bisect_left([1,2,2,3,5], 4) = 3
  right = bisect_right([1,2,2,3,5], 4) = 3
  left == right: return []
Result: []
```

---

## Best Answer to Memorize

```python
def target_indices(nums, target):
    nums.sort()
    return [i for i, num in enumerate(nums) if num == target]
```

**~2 lines. O(n log n) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why sort first?
> "The problem asks for indices in the SORTED array. So we must sort before
> finding indices. Without sorting, the indices would be in the original
> array, which is different."

### Why are equal values contiguous after sort?
> "Sorting arranges elements in nondecreasing order. All elements equal to
> target must be next to each other."

### When to use binary search vs linear scan?
> "For n <= 100 (this problem), linear scan is fine.
> For n > 1000, binary search (bisect) gives O(log n) per query."

### Why bisect_left vs bisect_right?
> "bisect_left(arr, x): first index where arr[idx] >= x.
> bisect_right(arr, x): first index where arr[idx] > x.
>
> For target, left = bisect_left (first >= target).
> Right boundary is bisect_right (first > target).
> Range = [left, right)."

### Can we avoid modifying nums?
> "Use sorted(nums) instead of nums.sort() — returns new list, original unchanged."

---

## Test Cases

| nums | target | Expected | Notes |
|------|--------|----------|-------|
| [1,2,5,2,3] | 2 | [1, 2] | Standard |
| [1,2,5,2,3] | 5 | [4] | Last |
| [1,2,5,2,3] | 4 | [] | Missing |
| [5] | 5 | [0] | Single |
| [5] | 3 | [] | Single, missing |
| [3,3,3,3] | 3 | [0,1,2,3] | All same |
| [3,3,3,3] | 5 | [] | All wrong |
| [1,2,3,4,5] | 3 | [2] | Already sorted |
| [5,4,3,2,1] | 3 | [2] | Reverse sorted |
| [1,5,2,5,3,5] | 5 | [3,4,5] | Multiple |
| [1,2,5,2,3,1,5,2,3] | 2 | [2,3,4] | Larger |
| [1,2,3,4] | 3 | [2] | All distinct |

---

## Common Pitfalls

1. **Forgetting to sort**: Indices must be in SORTED array.
2. **Modifying nums in place**: Use deep copy in tests, or use sorted() to avoid mutation.
3. **Off-by-one with bisect**: bisect_left is for >=, bisect_right is for >.
4. **Empty range handling**: If left == right, target not present.
5. **Returning unsorted indices**: After sort, indices are automatically in order.

---

## Why This Problem Matters

> "Tests:
> 1. Sorting + iteration.
> 2. Binary search boundaries.
> 3. List comprehension for collection.
> 4. Foundation for: range queries, position finding."

---

## Beyond This Problem: Related Patterns

### 1. Find First and Last Position (LC 34)
```python
# Same pattern: sort + binary search for boundaries.
def searchRange(nums, target):
    left = bisect.bisect_left(nums, target)
    right = bisect.bisect_right(nums, target)
    if left == right:
        return [-1, -1]
    return [left, right - 1]
```

### 2. Search Insert Position (LC 35)
```python
# Find index where target would be inserted.
def searchInsert(nums, target):
    return bisect.bisect_left(nums, target)
```

### 3. Find All Anagrams in String (LC 438)
```python
# Different - sliding window on string.
```

### 4. K-diff Pairs (LC 532)
```python
# Pair with absolute difference == k. Set-based.
```

---

## Connection to Binary Search

This problem uses the "range" pattern:

```
After sorting:
- bisect_left(arr, target) = first index where arr[idx] >= target.
- bisect_right(arr, target) = first index where arr[idx] > target.

Range of target in sorted array: [bisect_left, bisect_right).
Indices = list(range(left, right)).
```

Master `bisect_left` and `bisect_right` — they appear in many problems.

---

## Quick Checklist

When given a similar problem:
- [ ] Sort first? (yes — required by problem)
- [ ] Find range or single index? (range here — list of indices)
- [ ] What about missing target? (return [])
- [ ] In-place or new list? (in-place sort OK, or use sorted())
- [ ] Linear scan vs bisect? (linear fine for small n)

---

## Mathematical Formulation

Given sorted array `arr` and target `t`:

```
left  = min { i : arr[i] >= t }  (lower bound)
right = min { i : arr[i] >  t }  (upper bound)

indices = [left, left+1, ..., right-1]

If left == right: target not present.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 2089 - Find Target Indices After Sorting Array](https://leetcode.com/problems/find-target-indices-after-sorting-array/)
