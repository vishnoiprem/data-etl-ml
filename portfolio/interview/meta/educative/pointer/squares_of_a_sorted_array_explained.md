# Squares of a Sorted Array — 20 Solutions + Interview Thinking

## Problem
Given an integer array `nums` sorted in non-decreasing order, return an array
of the **squares** of each number, also sorted in non-decreasing order.

Reference: LeetCode #977 / Educative Grokking — "Squares of a Sorted Array".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Square every element of a sorted array; the result must also be sorted."

### 2. Key Insight
**The largest absolute values are at the OUTER ends.** After squaring,
the largest values come from either the most-negative left element or
the largest positive right element. So a two-pointer from both ends,
placing the winner at the **tail** of the output, builds the array in
descending order from the back — yielding the final ascending result.

### 3. Pattern Recognition
Two-pointer **descending fill** into output. Compare `|nums[i]|` vs `|nums[j]|`,
take the larger, write at position `k` (starting at `n-1`), advance that pointer.

### 4. Edge Cases
- All non-negative → trivially square in order.
- All negative → result is reverse-square.
- Mixed signs → pointer work.
- Single element → square and return.
- Zero in array → zero squared is zero, doesn't disturb ordering.
- Duplicates with mixed signs (e.g., `[-1, 0, 0, 1]`) → `[0, 0, 1, 1]`.

### 5. Tricky Detail
**Always compare absolute values.** Don't just take `nums[j]^2` because
"positive side". If the negatives extend far enough, the left's absolute
value exceeds the right's.

### 6. Algorithm
```
result = [0] * n
i, j = 0, n - 1
for k in range(n - 1, -1, -1):
    if abs(nums[i]) > abs(nums[j]):
        result[k] = nums[i] ** 2
        i += 1
    else:
        result[k] = nums[j] ** 2
        j -= 1
return result
```

### 7. Why It Works
The squaring function is monotonic for `|x|`. Each step places the current
largest `|x|` at the back of the output. The remaining left/right pointers
cover the smallest remaining `|x|`s. After `n` steps, all positions are
filled, in ascending order.

### 8. Complexity
- Time: **O(n)**.
- Space: **O(n)** for output (or O(1) extra if output is treated as the array).

### 9. Code Structure
```python
def sortedSquares(nums):
    n = len(nums)
    result = [0] * n
    i, j = 0, n - 1
    for k in range(n - 1, -1, -1):
        if abs(nums[i]) > abs(nums[j]):
            result[k] = nums[i] ** 2
            i += 1
        else:
            result[k] = nums[j] ** 2
            j -= 1
    return result
```

### 10. Mental Trace
`[-4, -1, 0, 3, 10]`:
- k=4: `|-4|=4` vs `|10|=10` → `100`, j=3
- k=3: `|-4|=4` vs `|3|=3` → `16`, i=1
- k=2: `|-1|=1` vs `|3|=3` → `9`, j=2
- k=1: `|-1|=1` vs `|0|=0` → `1`, i=2
- k=0: `|0|=0` vs `|0|=0` → `0`, j=1
- Result: `[0, 1, 9, 16, 100]` ✓

`[-7, -3, 2, 3, 11]`:
- k=4: `7` vs `11` → `121`, j=3
- k=3: `7` vs `3` → `49`, i=1
- k=2: `3` vs `3` → `9`, j=2 (or i=2, ties go right)
- k=1: `3` vs `2` → `9`, i=2
- k=0: `2` vs `2` → `4`, j=1
- Result: `[4, 9, 9, 49, 121]` ✓

---

## 20 Solutions Summary

| #  | Approach                              | Time      | Notes |
|----|---------------------------------------|-----------|-------|
| 1  | Canonical two-pointer (BEST)          | O(n)      | clean |
| 2  | While loop variant                    | O(n)      | alternative |
| 3  | Find split, merge two halves          | O(n)      | divide & conquer |
| 4  | Brute force + sort                    | O(n log n)| educational |
| 5  | List comp + sort                      | O(n log n)| one-liner |
| 6  | `map` + sorted                        | O(n log n)| functional |
| 7  | Two-pointer with `>=` variant         | O(n)      | tie-break |
| 8  | Recursive                             | O(n)      | educational |
| 9  | NumPy                                 | O(n log n)| extra dep |
| 10 | Sort by abs, then square              | O(n log n)| key=abs |
| 11 | Split + ascending merge               | O(n)      | like V3 |
| 12 | Sort by abs via tuples                | O(n log n)| heap-style |
| 13 | Manual square + sort                  | O(n log n)| verbose |
| 14 | `map` then sort                       | O(n log n)| verbose |
| 15 | Manual index pointer                  | O(n)      | alternative |
| 16 | List comp + sorted                    | O(n log n)| minimal |
| 17 | `key=abs` ascending                   | O(n log n)| clean |
| 18 | `key=abs` sorted (same as V17)        | O(n log n)| |
| 19 | Two-pointer `>=` variant              | O(n)      | like V7 |
| 20 | Split + merge with `reversed`         | O(n)      | cleaner |

---

## Recommended Interview Answer
**Solution 1** — clean, optimal, idiomatic:

```python
def sortedSquares(nums):
    n = len(nums)
    result = [0] * n
    i, j = 0, n - 1
    for k in range(n - 1, -1, -1):
        if abs(nums[i]) > abs(nums[j]):
            result[k] = nums[i] ** 2
            i += 1
        else:
            result[k] = nums[j] ** 2
            j -= 1
    return result
```

---

## Common Pitfalls
1. **Comparing signed values** — comparing `nums[i]` vs `nums[j]` directly
   would fail for `[-5, 0, 5]`: `-5 < 5` so you'd take `5^2` first, but the
   answer `[25, 0, 25]` is wrong; the correct answer is `[0, 25, 25]`.
   Always compare absolute values.
2. **Forgetting absolute values when equal** — when `abs(nums[i]) == abs(nums[j])`,
   either choice works for the algorithm; pick one consistently.
3. **Output buffer size** — must be `n`, not `n - 1`.
4. **Off-by-one on initial `k`** — should be `n - 1`, not `n`.
5. **Modifying input** — the problem allows a new array; only modify input if explicitly required.

---

## Variant: In-Place Squaring
If the problem allowed O(1) extra space, use the split-then-swap approach:
1. Square each element in-place.
2. Reverse the negative half.
3. Merge two halves.

This is what most "in-place" solutions look like.
