# Maximum Average Subarray I — 10 Solutions + Interview Thinking

## Problem
Given an integer array `nums` and integer `k`, find the contiguous
subarray of length EXACTLY `k` with the maximum average value. Return
that average.

Reference: LeetCode #643 / Educative Grokking — "Maximum Average
Subarray I".

---

## Interview Talking Points

Lead with the **invariant**: "Sliding window of size `k`. Track max
sum (equivalently, max average)."

Note: maximum **sum** corresponds to maximum **average** since divisor
`k` is constant.

---

## 10-Step Thinking Process

### 1. Understand
"Find the maximum average over all subarrays of length exactly `k`."

### 2. Key Insight
Sliding window of fixed size `k`. Track running sum. The window with
maximum sum has the maximum average.

### 3. Pattern Recognition
- Fixed-size window
- Running sum (add new, remove old)
- Track max sum

### 4. Edge Cases
- `k == 1` → max element.
- `k == n` → average of all.
- All negative → least-negative consecutive k.
- `n == 1`, `k == 1` → the single element.

### 5. Tricky Detail — Why Sum, Not Average?

Since `k` is fixed, maximizing the sum is equivalent to maximizing the
average. We can avoid division in the inner loop.

### 6. Algorithm
```
cur = sum(nums[:k])
best = cur
for i in range(k, n):
    cur += nums[i] - nums[i - k]
    best = max(best, cur)
return best / k
```

### 7. Why It Works
Each iteration slides the window by one position:
- Remove `nums[i - k]` (leftmost going out).
- Add `nums[i]` (rightmost coming in).

This gives the new sum in O(1). Track max.

### 8. Complexity
- **Time**: O(n).
- **Space**: O(1).

### 9. Code Structure
1. Compute initial sum of first `k` elements.
2. Set `best = cur`.
3. Iterate `i` from `k` to `n-1`.
4. Update `cur` by sliding.
5. Update `best`.
6. Return `best / k`.

### 10. Mental Trace
`nums = [1, 12, -5, -6, 50, 3]`, `k = 4`:

- Initial: sum = 1 + 12 + (-5) + (-6) = 2. best=2.
- i=4 (50): cur = 2 + 50 - 1 = 51. best=51.
- i=5 (3): cur = 51 + 3 - 12 = 42. best=51.
- Return 51 / 4 = 12.75. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Sliding window (BEST)                 | O(n)    | O(1)  | canonical |
| 2  | Same logic, alt form                  | O(n)    | O(1)  | same |
| 3  | Brute force                           | O(nk)   | O(1)  | educational |
| 4  | Prefix sums                           | O(n)    | O(n)  | alternative |
| 5  | accumulate                            | O(n)    | O(n)  | functional |
| 6  | numpy sliding_window_view             | O(n)    | O(n)  | vectorized |
| 7  | Deque-based                           | O(n)    | O(k)  | overkill |
| 8  | Manual array slice                    | O(nk)   | O(k)  | slow |
| 9  | Recursive                             | O(n)    | O(n)  | educational |
| 10 | Same as V1, minimal code              | O(n)    | O(1)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def find_max_average(nums, k):
    cur = sum(nums[:k])
    best = cur
    for i in range(k, len(nums)):
        cur += nums[i] - nums[i - k]
        best = max(best, cur)
    return best / k
```

---

## Common Pitfalls

1. **Variable-size window** — must be EXACTLY k, not "at most k".
2. **Off-by-one in initial window** — `nums[:k]` is the first window.
3. **Forgetting to divide by k** at the end.
4. **Using float comparison `==`** — use `abs(a - b) < 1e-9`.
5. **Modifying input** — Python `nums[:k]` doesn't modify, but
   `nums[:k] = ...` would.

---

## Talking Points — Interview Cheat Sheet

If asked "what if `k` is variable?":
> "That's a different problem. For 'at least k' or 'at most k', we'd
> use a variable-size sliding window with a different objective."

If asked "why not track the average directly?":
> "Tracking the sum avoids division in the inner loop. Since k is
> constant, max sum gives max average."

If asked "what's the time complexity?":
> "O(n) — one pass, with O(1) update per step."

If asked "what about floating-point accuracy?":
> "Each subarray sum is an integer (or large integer). We only divide
> by `k` at the end, minimizing precision loss."

---

## Related Problems

- **Maximum Average Subarray II** (LC #644) — at LEAST k length.
- **Sliding Window Maximum** — different objective (max element).
- **Subarray Sum Equals K** (LC #560) — different constraint.
- **Maximum Sum of 3 Subarrays** (LC #689) — multiple non-overlapping.

---

## Variants

- **At least k**: maintain max sum of any window of length ≥ k.
- **Multiple windows**: combine results from disjoint windows.
- **Subarray with at most K distinct**: different criterion.