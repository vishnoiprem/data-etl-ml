# Minimum Size Subarray Sum — 10 Solutions + Interview Thinking

## Problem
Given an array of positive integers `nums` and a positive integer
`target`, find the minimal length of a contiguous subarray whose sum is
at least `target`. Return 0 if no such subarray exists.

Reference: LeetCode #209 / Educative Grokking — "Minimum Size Subarray
Sum".

---

## Interview Talking Points

Lead with the **invariant**: "Window sum ≥ target means window is valid;
shrink from left to find the smallest valid window."

Emphasize the **positivity assumption**: shrinking only decreases sum,
so the inner while-loop terminates.

---

## 10-Step Thinking Process

### 1. Understand
"Smallest contiguous subarray with sum ≥ target. All nums are positive."

### 2. Key Insight
Sliding window. Expand `right`; while sum ≥ target, shrink `left`.
Each element added and removed at most once → O(n).

### 3. Pattern Recognition
- Two pointers, both move forward
- Running sum (`cur_sum`)
- Track minimum valid window size

### 4. Edge Cases
- All nums less than target → 0.
- Single element ≥ target → 1.
- Sum of all nums < target → 0.
- `target == 1` → 1 (any single positive element).

### 5. Tricky Detail — Positivity

This algorithm RELIES on `nums[i] > 0`. If negatives were allowed,
shrinking the window wouldn't necessarily decrease the sum (it could
add a negative). For mixed signs, we'd need a different approach
(prefix sums + binary search).

### 6. Algorithm
```
left = 0
cur_sum = 0
best = inf
for right in range(n):
    cur_sum += nums[right]
    while cur_sum >= target:
        best = min(best, right - left + 1)
        cur_sum -= nums[left]
        left += 1
return 0 if best == inf else best
```

### 7. Why It Works
Each `right` adds one element. The inner while-loop shrinks `left` until
sum < target (or `left > right`). After shrinking, the window is the
SMALLEST valid window ending at `right`. We track the minimum over all
such windows.

### 8. Complexity
- **Time**: O(n) — each element added and removed at most once.
- **Space**: O(1).

### 9. Code Structure
1. Initialize pointers and sum.
2. Expand `right`, add to sum.
3. While valid, update best and shrink.
4. Return best (or 0 if none found).

### 10. Mental Trace
`target = 7`, `nums = [2, 3, 1, 2, 4, 3]`:

| right | nums[right] | cur_sum | left | window    | best |
|-------|-------------|---------|------|-----------|------|
| 0     | 2           | 2       | 0    | [2]       | inf  |
| 1     | 3           | 5       | 0    | [2,3]     | inf  |
| 2     | 1           | 6       | 0    | [2,3,1]   | inf  |
| 3     | 2           | 8       | 0    | [2,3,1,2] | 4    |
| shrink| -           | 6       | 1    | [3,1,2]   | -    |
| 4     | 4           | 10      | 1    | [3,1,2,4] | 3    |
| shrink| -           | 7       | 2    | [1,2,4]   | -    |
| shrink| -           | 5       | 3    | [2,4]     | -    |
| 5     | 3           | 8       | 3    | [2,4,3]   | 2    |
| shrink| -           | 6       | 4    | [4,3]     | -    |
| shrink| -           | 2       | 5    | [3]       | -    |

best = 2. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Sliding window (BEST)                 | O(n)    | O(1)  | canonical |
| 2  | Same with var renames                 | O(n)    | O(1)  | alt naming |
| 3  | Brute force                           | O(n²)   | O(1)  | educational |
| 4  | Prefix sum + bisect                   | O(n log n) | O(n) | alt |
| 5  | itertools.accumulate + bisect         | O(n log n) | O(n) | functional |
| 6  | numpy prefix + searchsorted           | O(n log n) | O(n) | vectorized |
| 7  | Deque-based window                    | O(n)    | O(k)  | overkill |
| 8  | Recursive                             | O(n)    | O(n)  | call stack |
| 9  | Same as V1, alt code style             | O(n)    | O(1)  | identical |
| 10 | Final cleanest                        | O(n)    | O(1)  | memorize |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def min_subarray_len(target, nums):
    left = 0
    cur_sum = 0
    best = float('inf')
    for right in range(len(nums)):
        cur_sum += nums[right]
        while cur_sum >= target:
            best = min(best, right - left + 1)
            cur_sum -= nums[left]
            left += 1
    return 0 if best == float('inf') else best
```

---

## Common Pitfalls

1. **Assuming non-positive nums** — algorithm breaks for negatives.
   Use prefix sums + binary search for that case.
2. **Returning `inf` instead of `0`** — when no valid window exists.
3. **Off-by-one in window size** — `right - left + 1`.
4. **Not advancing `left` past `right`** — could cause issues with
   empty windows.
5. **Confusing with "max size subarray with sum ≤ target"** —
   different problem; use similar but reversed logic.

---

## Talking Points — Interview Cheat Sheet

If asked "what if the array has negative numbers?":
> "This approach breaks. The alternative is prefix sums + binary
> search: precompute `prefix[i] = sum(nums[0..i])`. For each `i`, find
> the smallest `j > i` with `prefix[j] - prefix[i] >= target` via
> binary search. O(n log n) total."

If asked "why does the inner while-loop terminate?":
> "Because `nums` are positive. Removing `nums[left]` from `cur_sum`
> strictly decreases it. Eventually `cur_sum < target`, and the loop
> exits."

If asked "can we do this in O(n log n)?":
> "Yes, with prefix sums + binary search. Each element is processed
> once for the prefix array, and we do O(log n) per binary search.
> Total O(n log n)."

If asked "what about MAXIMUM size with sum ≤ target?":
> "Same approach but track max instead of min. Or different problem
> entirely (often DP)."

---

## Related Problems

- **Maximum Size Subarray Sum Equals K** — different constraint
  (= instead of ≥).
- **Subarray Product Less Than K** (LC #713) — multiplicative version.
- **Longest Subarray with Sum at Most K** — similar template.
- **Minimum Window Substring** (LC #76) — character version.

---

## Variants

- **Sum ≤ target, max length**: track max instead of min.
- **Exactly target**: track windows with sum == target.
- **Negative numbers**: prefix sum + binary search.
- **Multiplicative product**: similar template, divide instead of
  subtract.