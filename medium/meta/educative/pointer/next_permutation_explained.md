# Next Permutation — 10 Solutions + Interview Thinking

## Problem
Given an integer array `nums`, rearrange it into the lexicographically next
greater permutation **in-place**. If no such permutation exists (the array
is in descending order), reset to the smallest (ascending) order.

Reference: LeetCode #31 / Educative Grokking — "Next Permutation".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Find the next lexicographic permutation, in-place. Wrap around if needed."

### 2. Key Insight
**Find the pivot** — the largest index `i` where `nums[i] < nums[i+1]`.
Then find the rightmost `j > i` where `nums[j] > nums[i]` (the smallest
"just larger" element). Swap, then **reverse** the suffix `i+1..n-1` to
make it ascending.

### 3. Pattern Recognition
Two-pointer / scan from the right: pivot + successor + reverse suffix.

### 4. Edge Cases
- Already descending (e.g., `[3,2,1]`) → reverse entire array.
- Already ascending (e.g., `[1,2,3]`) → swap last two.
- Single element → no change.
- All same elements (e.g., `[2,2,2]`) → no change.

### 5. Tricky Detail
**Reverse (not sort)** the suffix after the swap. Since the suffix was
descending before the swap, reversing makes it ascending in O(n). Sorting
would also work but is O(n log n) and unnecessary — and missing this
distinction leads to skipping over valid permutations.

### 6. Algorithm
```
1. Find pivot i = largest index with nums[i] < nums[i+1].
   If none, reverse the entire array.
2. Find swap j = largest index > i with nums[j] > nums[i].
3. Swap nums[i] and nums[j].
4. Reverse nums[i+1..n-1].
```

### 7. Why It Works
- The pivot is the rightmost position where a "bump up" is possible.
- Swapping with the smallest "just larger" element minimizes the new prefix.
- The suffix, having been non-increasing, becomes ascending after reversing,
  which yields the lexicographically smallest result overall.

### 8. Complexity
- Time: **O(n)**.
- Space: **O(1)**.

### 9. Code Structure
```python
def nextPermutation(nums):
    n = len(nums)
    if n <= 1:
        return nums
    # Find pivot
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        # Find successor
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    # Reverse suffix
    nums[i + 1:] = nums[i + 1:][::-1]
    return nums
```

### 10. Mental Trace
`[5, 6, 4, 3, 2]`:
- From right, find pivot: `nums[0]=5 < nums[1]=6`, so `i=0`.
- From right, find `j` where `nums[j] > 5`: `nums[1]=6 > 5` → `j=1`.
- Swap: `[6, 5, 4, 3, 2]`.
- Reverse suffix `nums[1:] = [5, 4, 3, 2]` → `[2, 3, 4, 5]`.
- Result: `[6, 2, 3, 4, 5]` ✓

`[1, 3, 2]`:
- Pivot: `i=0` (1 < 3).
- Successor: `nums[2]=2 > 1` → `j=2`. Swap: `[2, 3, 1]`.
- Reverse `nums[1:] = [3, 1]` → `[1, 3]`. Result: `[2, 1, 3]` ✓

`[6, 5, 4]` (descending — wraparound):
- Pivot loop fails (`i = -1`).
- Reverse entire array: `[4, 5, 6]` ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time  | Notes |
|----|---------------------------------------|-------|-------|
| 1  | Canonical pivot+successor+reverse (BEST) | O(n) | clean |
| 2  | In-place reverse with two-pointer     | O(n)  | no slicing |
| 3  | `bisect` on reversed suffix           | O(n)  | tricky |
| 4  | Sort suffix after swap                | O(n log n) | simpler but slower |
| 5  | Recursive helpers                     | O(n)  | educational |
| 6  | Brute force — generate all perms      | O(n!) | OOM for large n |
| 7  | Early-return when no pivot            | O(n)  | clean variant |
| 8  | NumPy-based                           | O(n)  | extra dep |
| 9  | `reversed()` builtin                  | O(n)  | functional |
| 10 | Explicit for-loop                     | O(n)  | most explicit |

---

## Recommended Interview Answer
**Solution 1** — clean, optimal, idiomatic:

```python
def nextPermutation(nums):
    n = len(nums)
    if n <= 1:
        return nums
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    nums[i + 1:] = nums[i + 1:][::-1]
    return nums
```

---

## Common Pitfalls
1. **Forgetting the wraparound case** — when no pivot exists, reverse the entire array (don't return).
2. **Wrong successor** — must pick the smallest element **greater than** pivot (rightmost such element from the right).
3. **Sort vs reverse suffix** — sort works but is O(n log n); reverse is O(n).
4. **Modifying during scan** — if you do the swap inside the pivot loop, you break the scan.
5. **Off-by-one in pivot scan** — start at `n-2`, not `n-1`.

---

## Comparison: Next Permutation vs Previous Permutation
Same algorithm structure but **mirror the comparisons**:
- Pivot: `nums[i] > nums[i+1]` (was `<`).
- Successor: `nums[j] < nums[i]` (was `>`).
- Sort suffix in DESCENDING order instead of ascending.
