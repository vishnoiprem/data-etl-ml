# Frequency of the Most Frequent Element — 10 Solutions + Interview Thinking

## Problem
Given an integer array `nums` and integer `k`, increment any element by
1 per operation (at most `k` total operations). Return the maximum
frequency of any element after at most `k` increments.

Reference: LeetCode #1838 / Educative Grokking — "Frequency of Most
Frequent Element".

---

## Interview Talking Points

Lead with the **key transformation**: "Sort the array, then sliding
window. The rightmost element is the target; making all elements in the
window equal to it requires `target * len - sum` operations."

Then note: this is "Longest Subarray After k Increments" template.

---

## 10-Step Thinking Process

### 1. Understand
"Make at most `k` total +1 increments. Maximize the count of any one
value."

### 2. Key Insight
After sorting, we have a non-decreasing array. For window `[left,
right]`, making all values equal to `nums[right]` (the largest)
requires:
`cost = nums[right] * (right - left + 1) - sum(nums[left..right])`.

Find the largest window with `cost <= k`.

### 3. Pattern Recognition
- Sort first
- Sliding window with running sum
- Track maximum valid window

### 4. Edge Cases
- `k == 0`: longest run of equal elements.
- All equal: n.
- `k` very large: n.
- Single element: 1.

### 5. Tricky Detail — Why Sort?

After sorting, the rightmost element of the window is always the
**largest**. The cheapest way to make them all equal is to bring the
smaller ones UP to the largest (no decrements needed). This gives us
the formula `cost = target * len - sum`.

### 6. Algorithm
```
sort(nums)
left = 0; cur_sum = 0; best = 0
for right in range(n):
    cur_sum += nums[right]
    while nums[right] * (right - left + 1) - cur_sum > k:
        cur_sum -= nums[left]
        left += 1
    best = max(best, right - left + 1)
return best
```

### 7. Why It Works
Each element is added to `cur_sum` once (when `right` reaches it) and
subtracted once (when `left` passes it). So O(n) total operations after
the O(n log n) sort.

The inner while-loop shrinks `left` until the window becomes valid.
The window is then the MAXIMUM valid window ending at `right`. We
track the global maximum.

### 8. Complexity
- **Time**: O(n log n) — sorting dominates.
- **Space**: O(1) (in-place sort + scalars) or O(n) depending on sort.

### 9. Code Structure
1. Sort.
2. Initialize left, sum, best.
3. Iterate right.
4. While cost > k, shrink from left.
5. Update best.

### 10. Mental Trace
`nums = [1, 4, 8, 13]`, `k = 5`:
- Sort: [1, 4, 8, 13].
- right=0 '1': sum=1. cost = 1*1 - 1 = 0. best=1.
- right=1 '4': sum=5. cost = 4*2 - 5 = 3. best=2.
- right=2 '8': sum=13. cost = 8*3 - 13 = 11 > 5.
  - shrink: left=0, sum=12. cost = 8*2 - 12 = 4. best=2.
- right=3 '13': sum=25. cost = 13*2 - 25 = 1. best=2.

Returns 2. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time       | Space | Notes |
|----|---------------------------------------|------------|-------|-------|
| 1  | Sort + sliding window (BEST)          | O(n log n) | O(1)  | canonical |
| 2  | Sort + sliding + prefix sum           | O(n log n) | O(n)  | alt |
| 3  | Sort + sliding (clean code)           | O(n log n) | O(1)  | alt style |
| 4  | Sort + brute force                    | O(n²)      | O(1)  | educational |
| 5  | Same as V1, redundant loop            | O(n log n) | O(1)  | variant |
| 6  | Sort + sliding (explicit target)      | O(n log n) | O(1)  | readable |
| 7  | Sort + sliding (alt sliding)          | O(n log n) | O(1)  | alternative |
| 8  | Sort + accumulate                     | O(n log n) | O(n)  | functional |
| 9  | Recursive                             | O(n log n) | O(n)  | call stack |
| 10 | numpy prefix                          | O(n log n) | O(n)  | vectorized |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def max_frequency(nums, k):
    nums.sort()
    left = 0
    cur_sum = 0
    best = 0
    for right in range(len(nums)):
        cur_sum += nums[right]
        while nums[right] * (right - left + 1) - cur_sum > k:
            cur_sum -= nums[left]
            left += 1
        best = max(best, right - left + 1)
    return best
```

---

## Common Pitfalls

1. **Forgetting to sort** — the "rightmost is target" property requires
   sorting.
2. **Using wrong target** — must be `nums[right]` (current), not a
   separate variable.
3. **Off-by-one in window size** — `right - left + 1`.
4. **Including decrements in cost** — we only INCREMENT (not decrement),
   so smaller values can only go UP to the target.
5. **Modifying input array** — call `sorted(nums)` if you don't want to
   mutate.

---

## Talking Points — Interview Cheat Sheet

If asked "why sort first?":
> "After sorting, the rightmost element of any window is the largest.
> We can always make all elements equal to the largest by incrementing
> the smaller ones UP. This gives a clean cost formula:
> `target * len - sum`."

If asked "what if we could also decrement?":
> "Different problem. The cost is the absolute sum of differences.
> Same O(n log n) approach with `sum(|x - target|)` instead."

If asked "is O(n) possible without sorting?":
> "Probably not — the sorting gives us a useful ordering. Without it,
> we'd need different approach. Counting sort can help if the value
> range is small."

If asked "can we use a heap?":
> "Less natural. A heap would track increments per element, but the
> window structure is harder to maintain."

---

## Related Problems

- **Longest Repeating Character Replacement** (LC #424) — same template
  with strings.
- **Minimize the Difference Between Target and Chosen Elements** —
  similar "k operations" pattern.
- **Make Array Non-decreasing** — different problem.
- **Maximum Frequency Stack** (LC #895) — different structure.

---

## Variants

- **At most K decrements too**: different cost metric.
- **Different target per position**: sorting not applicable; different
  approach.
- **Min operations to make all equal**: cost = `max - min` after sort.