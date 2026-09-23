# Longest Subarray With Diff At Most Limit — 10 Solutions + Interview Thinking

## Problem
Given `nums` and `limit`, return the longest non-empty subarray where
max - min <= limit.

Reference: LeetCode #1438 / Educative Grokking — "Longest Subarray
With Diff At Most Limit".

---

## Interview Talking Points

Lead with the **monotonic deques trick**: "Track running max in a
decreasing deque and running min in an increasing deque."

---

## 10-Step Thinking Process

### 1. Understand
"Longest subarray where max - min <= limit."

### 2. Key Insight
Standard sliding window tracks max/min implicitly. We need explicit
O(1) access to max/min, achieved with monotonic deques.

### 3. Pattern Recognition
- Sliding window with validity check
- Two monotonic deques (max decreasing, min increasing)

### 4. Edge Cases
- All same values → n.
- limit = 0 → all-equal subarrays only.
- Empty array → 0.

### 5. Tricky Detail — Deque Maintenance

When adding x to `max_d` (decreasing), pop back while back < x. This
keeps `max_d` monotonically decreasing with the current max at front.
Similarly for `min_d` (increasing).

When shrinking, pop front of `max_d` if it equals `nums[left]`
(same for `min_d`).

### 6. Algorithm
```
max_d = deque(); min_d = deque()
left = 0; result = 0
for right, x in enumerate(nums):
    while max_d and max_d[-1] < x: max_d.pop()
    max_d.append(x)
    while min_d and min_d[-1] > x: min_d.pop()
    min_d.append(x)
    while max_d[0] - min_d[0] > limit:
        if nums[left] == max_d[0]: max_d.popleft()
        if nums[left] == min_d[0]: min_d.popleft()
        left += 1
    result = max(result, right - left + 1)
return result
```

### 7. Why It Works
`max_d[0]` is the current window's max; `min_d[0]` is its min. As long
as their diff <= limit, the window is valid. Each element enters and
leaves each deque at most once → O(n).

### 8. Complexity
- **Time**: O(n).
- **Space**: O(n) worst case for deques.

### 9. Code Structure
1. Init deques.
2. Iterate right, update deques.
3. Shrink if invalid.
4. Track max length.

### 10. Mental Trace
`nums=[8,2,4,7]`, `limit=4`:
- right=0, x=8: max_d=[8], min_d=[8]. result=1.
- right=1, x=2: max_d=[8,2], min_d=[2]. 8-2=6>4. Shrink left=1.
  result=1.
- right=2, x=4: max_d=[4], min_d=[2,4]. 4-2=2<=4. result=2.
- right=3, x=7: max_d=[7], min_d=[4,7]. 7-4=3<=4. result=2.
- Final = 2. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Monotonic deques (BEST)               | O(n)    | O(n)  | canonical |
| 2  | SortedList                            | O(n log n) | O(n) | pythonic |
| 3  | Brute force                           | O(n²)   | O(1)  | educational |
| 4  | Heaps with lazy deletion              | O(n log n) | O(n) | alt |
| 5  | SortedList alt                        | O(n log n) | O(n) | same as V2 |
| 6  | numpy fallback                        | O(n)    | O(n)  | vectorized |
| 7  | List as deque                         | O(n)    | O(n)  | alt |
| 8  | Brute force with early break          | O(n²)   | O(1)  | educational |
| 9  | Recursive                             | O(n)    | O(n)  | educational |
| 10 | Same as V1, minimal                   | O(n)    | O(n)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
from collections import deque

def longest_subarray(nums, limit):
    max_d = deque()
    min_d = deque()
    left = 0
    result = 0
    for right, x in enumerate(nums):
        while max_d and max_d[-1] < x:
            max_d.pop()
        max_d.append(x)
        while min_d and min_d[-1] > x:
            min_d.pop()
        min_d.append(x)
        while max_d[0] - min_d[0] > limit:
            if nums[left] == max_d[0]:
                max_d.popleft()
            if nums[left] == min_d[0]:
                min_d.popleft()
            left += 1
        result = max(result, right - left + 1)
    return result
```

---

## Common Pitfalls

1. **Popping wrong end** — append at right, pop from right (back) to
   maintain monotonicity; pop from left (front) on shrink.
2. **Forgetting to shrink** — without it, window can grow unbounded.
3. **Using `max()`/`min()` over the window** — O(n) per check.
4. **Wrong comparison** — `nums[left] == max_d[0]`, not `in max_d`.
5. **Initial deque state** — start empty.

---

## Talking Points — Interview Cheat Sheet

If asked "what are monotonic deques?":
> "Deques that maintain monotonic order. Adding a new element pops
>  from the back until the order is preserved. The front always holds
>  the extreme (max or min) of the current window."

If asked "why not use heaps?":
> "Heaps don't support removal from arbitrary positions. With lazy
>  deletion, you'd need extra bookkeeping. Monotonic deques are
>  cleaner."

If asked "could we use SortedList?":
> "Yes. O(n log n) total due to insertions and deletions. Cleaner
>  code but slightly slower."

If asked "what's the time complexity?":
> "O(n). Each element enters and leaves each deque at most once."

---

## Related Problems

- **Sliding Window Maximum** (LC #239) — one deque for max.
- **Longest Repeating Character Replacement** — different.
- **Longest Well-Performing Interval** (LC #1124) — different.
- **Longest Subarray With Diff At Most Limit** — this problem.

---

## Variants

- **Min length with diff <= limit**: track min.
- **Number of subarrays with diff <= limit**: count.
- **Different metric** (e.g., sum <= k): different algorithm.
- **Variable limit**: just update the check.
