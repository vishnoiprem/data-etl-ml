# Rotate Array — 20 Solutions + Interview Thinking

## Problem
Given an integer array `nums`, rotate the array to the right by `k` steps,
where `k` is non-negative.

Reference: LeetCode #189 / Educative Grokking — "Rotate Array".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Shift the array elements right by `k` positions. Elements that fall off
the end wrap to the front. Modulo `n` first to handle `k >= n`."

### 2. Key Insight
**Three reversals.** Reverse the whole array, then reverse the first `k`
elements, then reverse the last `n-k` elements. Result: a right rotation
by `k`.

Why this works:
- After reversing all: `[..., n-k-1, ..., n-1, n-k, ..., 0]` becomes `[n-1, ..., n-k, ..., 0]`
- After reversing first `k`: `[n-1, ..., n-k]` becomes `[n-k, ..., n-1]`
- After reversing last `n-k`: `[..., 0]` becomes `[0, ..., n-k-1]`
- Final: `[n-k, ..., n-1, 0, ..., n-k-1]` = right rotation by `k`.

### 3. Pattern Recognition
Three in-place reversals with slice assignments or two-pointer swaps.

### 4. Edge Cases
- `k == 0` → no change.
- `k == n` → no change (full cycle).
- `k > n` → use `k % n`.
- `n == 1` → no change.
- Empty array → no change.
- `k == n - 1` → swap last element to front.

### 5. Tricky Detail
Always take `k = k % n` BEFORE any reversal. Otherwise, ranges like
`[0:k]` would be invalid when `k >= n`. Also handle empty arrays
specially (`n=0`) to avoid modulo-by-zero.

### 6. Algorithm
```
k = k % n
def reverse(arr, lo, hi):
    while lo < hi:
        arr[lo], arr[hi] = arr[hi], arr[lo]
        lo += 1; hi -= 1
reverse(nums, 0, n - 1)
reverse(nums, 0, k - 1)
reverse(nums, k, n - 1)
```

### 7. Why It Works
Reversing inverts the order. Two subsequent reversals on disjoint halves
restore the order within each half while preserving their new positions
relative to each other. After the three reversals, the last `k` elements
end up at the front.

### 8. Complexity
- Time: **O(n)**.
- Space: **O(1)** (in-place).

### 9. Code Structure
```python
def rotate(nums, k):
    n = len(nums)
    k = k % n
    if k == 0 or n <= 1:
        return nums
    def reverse(arr, lo, hi):
        while lo < hi:
            arr[lo], arr[hi] = arr[hi], arr[lo]
            lo += 1
            hi -= 1
    reverse(nums, 0, n - 1)
    reverse(nums, 0, k - 1)
    reverse(nums, k, n - 1)
    return nums
```

### 10. Mental Trace
`[1, 2, 3, 4, 5, 6, 7]`, k=3:
- `k = 3 % 7 = 3`
- Reverse all: `[7, 6, 5, 4, 3, 2, 1]`
- Reverse first 3: `[5, 6, 7, 4, 3, 2, 1]`
- Reverse last 4: `[5, 6, 7, 1, 2, 3, 4]` ✓

`[1, 2]`, k=3:
- `k = 3 % 2 = 1`
- Reverse all: `[2, 1]`
- Reverse first 1: `[2, 1]`
- Reverse last 1: `[2, 1]` ✓

`[1, 2, 3, 4, 5]`, k=5:
- `k = 5 % 5 = 0`
- Early return: `[1, 2, 3, 4, 5]` ✓

---

## 20 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Three reversals (BEST)                | O(n)    | O(1)  | clean |
| 2  | Cyclic replacements                   | O(n)    | O(1)  | in-place |
| 3  | Extra array                           | O(n)    | O(n)  | simple |
| 4  | Slice concatenation                   | O(n)    | O(n)  | pythonic |
| 5  | Pop+prepend k times                   | O(nk)   | O(1)  | slow |
| 6  | `deque.rotate`                        | O(n)    | O(n)  | lib |
| 7  | One-by-one shift                      | O(nk)   | O(1)  | slow |
| 8  | `numpy.roll`                          | O(n)    | O(n)  | extra dep |
| 9  | Class-based                           | O(n)    | O(1)  | OOP |
| 10 | Final cleanest                        | O(n)    | O(1)  | minimal |
| 11 | Slice reversal                        | O(n)    | O(1)  | `[::-1]` |
| 12 | Save tail + shift                     | O(n)    | O(1)  | manual |
| 13 | GCD cycle swap                        | O(n)    | O(1)  | math |
| 14 | `deque.rotate` v2                     | O(n)    | O(n)  | like V6 |
| 15 | Extra array v2                        | O(n)    | O(n)  | modular |
| 16 | numpy                                 | O(n)    | O(n)  | extra dep |
| 17 | Recursive three-reversal              | O(n)    | O(1)  | educational |
| 18 | `reversed()` builtin                  | O(n)    | O(1)  | functional |
| 19 | Pop+insert k times                    | O(nk)   | O(1)  | slow |
| 20 | List comprehension                    | O(n)    | O(n)  | new list |

---

## Recommended Interview Answer
**Solution 1** — clean, optimal, idiomatic:

```python
def rotate(nums, k):
    n = len(nums)
    k = k % n
    if k == 0 or n <= 1:
        return nums
    def reverse(arr, lo, hi):
        while lo < hi:
            arr[lo], arr[hi] = arr[hi], arr[lo]
            lo += 1
            hi -= 1
    reverse(nums, 0, n - 1)
    reverse(nums, 0, k - 1)
    reverse(nums, k, n - 1)
    return nums
```

---

## Common Pitfalls
1. **Forgetting `k % n`** — when `k >= n`, you must reduce first.
2. **Empty array modulo** — `0 % 0` raises an error. Always check `n == 0`.
3. **Off-by-one in reverse range** — `[0, k-1]` has `k` elements; `[k, n-1]` has `n-k` elements.
4. **Modifying slice vs in-place** — `nums[:] = ...` works for both list and string-like.
5. **XOR swap on integers** — works but fails if values are equal (xors to 0). Two-pointer swap is safer.

---

## Variant: Left Rotation
The same algorithm but for left rotation by `k`:
- `reverse(nums, 0, k - 1)`
- `reverse(nums, k, n - 1)`
- `reverse(nums, 0, n - 1)`

(Order of first two reverses is swapped.)

---

## Variant: Using Cyclic Replacements
Instead of three reversals, walk the array in `k`-step jumps and place
each element in its final position. Number of cycles = `gcd(n, k)`.
This is **Solution 13** and works in O(n) time with O(1) extra space.
