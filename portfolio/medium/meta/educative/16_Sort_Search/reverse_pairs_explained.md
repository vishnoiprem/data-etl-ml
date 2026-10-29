# Reverse Pairs - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-pairs

## The Problem
```
Given an integer array nums, count pairs (i, j) with i < j such that
nums[i] > 2 * nums[j].

Examples:
    nums=[6,1,3,1] -> 3
    (Pairs: (0,1) 6>2*1, (0,3) 6>2*1, (2,3) 3>2*1)
    nums=[1,3,2,3,1] -> 2
    (Pairs: (1,4) 3>2*1, (3,4) 3>2*1)

Constraints:
- 1 <= nums.length <= 5 * 10^4
- -2^31 <= nums[i] <= 2^31 - 1
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Count pairs (i, j) with i < j where nums[i] > 2 * nums[j].
This is similar to "Count of Smaller Numbers After Self" but with
a multiplier on nums[j].
```

### Step 2: The Trick (Educative approach)
> "KEY INSIGHT (Approach 1): Process left-to-right. Maintain a sorted list
> of seen elements. For each new num, count seen elements > 2*num using
> bisect_right. Insert num into the sorted list.
>
> Time: O(n^2) worst case (list insert is O(n)), but works for n <= 10^4."

### Step 3: The Trick (Optimal merge sort)
> "KEY INSIGHT (Approach 2): Modified merge sort. During merge of left and
> right halves (both sorted), count pairs where left[i] > 2*right[j].
> Use two pointers: as left[i] grows, j only moves forward.
>
> Time: O(n log n)."

### Step 4: Algorithm (bisect)
> "1. sorted_seen = [].
> 2. count = 0.
> 3. For num in nums:
>    a. idx = bisect_right(sorted_seen, 2*num).
>    b. count += len(sorted_seen) - idx.
>    c. Insert num (insort).
> 4. Return count."

### Step 5: Algorithm (merge sort)
> "1. Recursively sort halves, counting pairs within each half.
> 2. During merge, count cross-pairs:
>    - For each left[i], advance j in right until 2*right[j] >= left[i].
>    - count += j (number of right elements where 2*r < l).
> 3. Standard merge to produce sorted result.
> 4. Return total count."

### Step 6: Edge cases
> "- Empty: 0.
> - Single element: 0.
> - All zeros: 0 (strict >).
> - Negative numbers: works correctly (2*num is also negative)."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to count pairs (i, j) with i < j where nums[i] > 2 * nums[j]."

**Approach 1 (Educative - bisect):**
> "Process left-to-right. Maintain a sorted list of seen elements. For each new num, count seen elements > 2*num using bisect_right. Insert num into sorted list."

**Approach 2 (Optimal - merge sort):**
> "Modified merge sort. During merge of sorted halves, count pairs where left[i] > 2*right[j] using two pointers."

**Why bisect works:**
> "bisect_right(sorted, 2*num) returns the first index where element > 2*num. Everything from that index to the end satisfies the condition."

**Why merge sort works:**
> "Both halves are sorted. For each left[i], as i grows, left[i] grows (since sorted), so 2*right[j] < left[i] becomes easier to satisfy. We can advance j monotonically."

**Edge cases:**
- Empty: 0.
- Single: 0.
- All equal: 0.
- Negative: 2*num is negative, still works.

**Complexity:**
- Bisect: O(n^2) — list insert is O(n).
- Merge sort: O(n log n) — optimal.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort + bisect_right (BEST Educative - Memorize!)
```python
def reverse_pairs_1(nums):
    import bisect
    sorted_seen = []
    count = 0
    for num in nums:
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        count += len(sorted_seen) - idx
        bisect.insort(sorted_seen, num)
    return count
```

### Way 2: Verbose
### Way 3: Brute force O(n^2)
### Way 4: Merge sort (BEST Optimal)
### Way 5: Manual sorted list
### Way 6: Class-based
### Way 7: numpy bisect
### Way 8: Merge sort helper
### Way 9: bisect_left variant
### Way 10: Helper function
### Way 11: BIT/Fenwick tree
### Way 12: Pure Python merge sort
### Way 13: enumerate-based
### Way 14: accumulate variant
### Way 15: Negative-aware merge
### Way 16: Manual binary search
### Way 17: Heap variant
### Way 18: numpy vectorized
### Way 19: Recursive
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Educative style    | Way 1    | bisect       |
| Optimal            | Way 4    | Merge sort   |
| Few elements       | Way 3    | Brute force  |
| Complex queries    | Way 11   | BIT          |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Bisect (Way 1) | O(n^2) worst | O(n) | List insert is O(n) |
| Merge sort (Way 4) | O(n log n) | O(n) | Optimal |
| Brute force (Way 3) | O(n^2) | O(1) | Simple |
| BIT (Way 11) | O(n log n) | O(n) | Complex but general |

---

## Walkthrough Example

```
nums = [6, 1, 3, 1]

Step 1: Process 6.
  sorted_seen = []
  bisect_right([], 12) = 0. count += 0 - 0 = 0.
  Insert 6. sorted_seen = [6].

Step 2: Process 1.
  2*1 = 2.
  bisect_right([6], 2) = 0. count += 1 - 0 = 1.
  Insert 1. sorted_seen = [1, 6].

Step 3: Process 3.
  2*3 = 6.
  bisect_right([1, 6], 6) = 2 (after the 6). count += 2 - 2 = 0.
  Insert 3. sorted_seen = [1, 3, 6].

Step 4: Process 1.
  2*1 = 2.
  bisect_right([1, 3, 6], 2) = 1 (after the 1). count += 3 - 1 = 2.
  Insert 1. sorted_seen = [1, 1, 3, 6].

Total = 0 + 1 + 0 + 2 = 3. ✓
```

```
nums = [6, 1, 3, 1] via merge sort:

merge_count([6,1,3,1]):
  left = [6,1], right = [3,1]
  merge_count([6,1]):
    left=[6], right=[1]
    For left[0]=6: 2*1<6 true, j=1. count=1.
    return [1,6], 1
  merge_count([3,1]):
    left=[3], right=[1]
    For left[0]=3: 2*1<3 true, j=1. count=1.
    return [1,3], 1
  Merge [1,6] and [1,3]:
    For left[0]=1: 2*1<1 false. count+=0.
    For left[1]=6: 2*1<6 true (j=1). 2*3<6 false. count+=1.
    count=1.
  Total = 1+1+1 = 3. ✓
```

---

## Best Answer to Memorize

```python
def reversePairs(nums):
    import bisect
    sorted_seen = []
    count = 0
    for num in nums:
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        count += len(sorted_seen) - idx
        bisect.insort(sorted_seen, num)
    return count
```

**~7 lines. O(n^2) worst case. O(n) space. Interview-ready!**

For optimal: use merge sort.

```python
def reversePairs_optimal(nums):
    def merge_count(arr):
        if len(arr) <= 1:
            return arr, 0
        mid = len(arr) // 2
        left, lc = merge_count(arr[:mid])
        right, rc = merge_count(arr[mid:])
        merged = []
        count = 0
        j = 0
        for i in range(len(left)):
            while j < len(right) and 2 * right[j] < left[i]:
                j += 1
            count += j
        # Standard merge
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, lc + rc + count
    _, count = merge_count(nums)
    return count
```

---

## Key Insights

### Why bisect_right (not bisect_left)?
> "We need STRICT > 2*num. bisect_right gives first index where arr > 2*num.
> bisect_left would give arr >= 2*num, which includes the equality case."

### Why process left-to-right?
> "When processing nums[i], all elements in sorted_seen are from nums[0..i-1],
> which are valid 'previous' elements (i < j). We don't need to worry about
> order — we just count those satisfying the inequality."

### Why merge sort is O(n log n)?
> "Each merge step takes O(n) (two-pointer sweep). There are log n levels
> of recursion. Total: O(n log n)."

### Why two pointers work in merge?
> "Both halves are sorted. As we iterate left[i] (which is non-decreasing),
> the number of right[j] satisfying 2*right[j] < left[i] can only increase.
> So j only moves forward."

### What if all numbers are negative?
> "2*num is also negative. The bisect still works correctly because the
> sorted list ordering is consistent."

---

## Test Cases

| nums | Expected | Notes |
|------|----------|-------|
| [6,1,3,1] | 3 | Standard |
| [1,3,2,3,1] | 2 | Standard |
| [2,4,3,5,1] | 3 | Standard |
| [] | 0 | Empty |
| [5] | 0 | Single |
| [3,3,3,3] | 0 | All same |
| [1,2,3,4] | 0 | Ascending |
| [4,3,2,1] | 2 | Descending |
| [-1,-2] | 1 | Negatives |
| [5,4,3,2,1] | 4 | Big descending |

---

## Common Pitfalls

1. **Using bisect_left**: Includes equality, incorrect for STRICT >.
2. **Forgetting to insert**: After counting, must insert into sorted list.
3. **Merge sort not accumulating**: Forgetting `lc + rc + count`.
4. **Negative handling**: 2*num is negative too; works automatically.
5. **Integer overflow**: In Python, no overflow issue.

---

## Why This Problem Matters

> "Tests:
> 1. Pair counting with inequality.
> 2. Modified merge sort for cross-pair counting.
> 3. Two-pointer technique.
> 4. Handling negative numbers.
> 5. Foundation for: count smaller after self, count of range sum."

---

## Beyond This Problem: Related Patterns

### 1. Count of Smaller Numbers After Self (LC 315)
```python
# Same merge sort but condition is nums[i] > nums[j].
```

### 2. Count of Range Sum (LC 327)
```python
# Similar but with prefix sums and ranges.
```

### 3. Merge Sort Basics
```python
# Standard merge sort without pair counting.
```

### 4. K-th Smallest Element
```python
# Quick-select or merge sort variant.
```

---

## Connection to Merge Sort Pair Counting

This problem extends merge sort's natural pair counting:

```
STANDARD MERGE SORT:
- Merge two sorted halves in O(n).
- No extra counting.

REVERSE PAIRS EXTENSION:
- During merge, count pairs where left[i] > 2*right[j].
- Two pointers: j only advances forward.
- O(n) per merge, O(n log n) total.

KEY OBSERVATION:
The pair counting happens AT MERGE TIME because:
- Within each half, recursion handles it.
- Cross-half pairs (left_orig < right_orig) are counted at merge.
- The condition `2*right[j] < left[i]` is monotone in j for fixed i.
```

---

## Quick Checklist

When given a similar problem:
- [ ] What's the inequality? (here: nums[i] > 2*nums[j])
- [ ] Strict or non-strict? (here: STRICT >)
- [ ] Sorted or unsorted input? (unsorted — sort or use sorted structure)
- [ ] Optimal approach? (merge sort for O(n log n))
- [ ] Educative approach? (bisect with sorted list)
- [ ] Edge case: negatives? (works automatically)
- [ ] Edge case: empty/single? (return 0)

---

## Mathematical Formulation

For an array `nums` of length n, count pairs (i,j) with i<j and nums[i] > 2*nums[j]:

```
APPROACH 1 (bisect):
  sorted_seen = []
  for num in nums:
    idx = bisect_right(sorted_seen, 2*num)
    count += len(sorted_seen) - idx
    insort(sorted_seen, num)

APPROACH 2 (merge sort):
  merge_count(arr):
    split into left, right
    lc = merge_count(left)
    rc = merge_count(right)
    count = 0
    j = 0
    for i in range(len(left)):
      while j < len(right) and 2*right[j] < left[i]:
        j += 1
      count += j
    merge left and right
    return merged, lc + rc + count
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 493 - Reverse Pairs](https://leetcode.com/problems/reverse-pairs/)
