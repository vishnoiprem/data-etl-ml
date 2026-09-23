# Count Subarrays With Score Less Than K — 10 Solutions + Interview Thinking

## Problem
The score of a subarray = (sum of elements) × (length). Given `nums` and
`k`, count the number of subarrays whose score is STRICTLY less than k.

Reference: LeetCode #2302 / Educative Grokking — "Count Subarrays With
Score Less Than K".

---

## Interview Talking Points

Lead with the **invariant**: "For each right, find the smallest left
where extending would make score >= k. All windows ending at right
starting in [left..right] are valid."

---

## 10-Step Thinking Process

### 1. Understand
"Count subarrays where sum × length < k."

### 2. Key Insight
For fixed right, as left decreases (window grows), both sum and length
increase, so score INCREASES monotonically. Once score >= k for some
left, all smaller lefts are invalid too.

So we find the smallest left such that score < k, then count
`right - left + 1` valid windows ending at right.

### 3. Pattern Recognition
- Sliding window with monotonic score
- For each right, count valid lefts

### 4. Edge Cases
- All elements >= k → 0 (each single element scores >= k).
- k very large → n(n+1)/2 (all subarrays).
- Single element: 1 if num < k, else 0.

### 5. Tricky Detail — Positivity Assumption

If nums could be negative, the score wouldn't be monotonic in window
size. We rely on positivity for the sliding window approach.

### 6. Algorithm
```
left = 0; cur_sum = 0; result = 0
for right in range(n):
    cur_sum += nums[right]
    while cur_sum * (right - left + 1) >= k:
        cur_sum -= nums[left]
        left += 1
    result += right - left + 1
return result
```

### 7. Why It Works
After the while loop, `[left..right]` is the LARGEST valid window
ending at `right` (extending it would push score >= k). All
sub-windows (smaller starts) are also valid (smaller score).
Count = `right - left + 1`.

### 8. Complexity
- **Time**: O(n) — each element added and removed at most once.
- **Space**: O(1).

### 9. Code Structure
1. Initialize left, cur_sum, result.
2. For each right, expand.
3. While score >= k, shrink from left.
4. Add count.

### 10. Mental Trace
`nums = [2, 1, 4, 3, 5]`, `k = 10`:
- right=0 (2): cur=2. score=2*1=2. result=1.
- right=1 (1): cur=3. score=3*2=6. result+=2 → 3.
- right=2 (4): cur=7. score=7*3=21 >= 10.
  - shrink: cur=5, left=1. score=5*2=10 >= 10.
  - shrink: cur=4, left=2. score=4*1=4. result+=1 → 4.
- right=3 (3): cur=7. score=7*2=14 >= 10.
  - shrink: cur=3, left=3. score=3*1=3. result+=1 → 5.
- right=4 (5): cur=8. score=8*2=16 >= 10.
  - shrink: cur=5, left=4. score=5*1=5. result+=1 → 6.

Returns 6. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Sliding window (BEST)                 | O(n)    | O(1)  | canonical |
| 2  | Same logic, alt code                  | O(n)    | O(1)  | same |
| 3  | Brute force                           | O(n²)   | O(1)  | educational |
| 4  | Prefix sum + binary search            | O(n log n) | O(n) | alternative |
| 5  | Recursive                             | O(n)    | O(n)  | call stack |
| 6  | accumulate + binsearch                | O(n log n) | O(n) | functional |
| 7  | numpy fallback                        | O(n)    | O(1)  | vectorized |
| 8  | Deque-based                           | O(n)    | O(k)  | overkill |
| 9  | Explicit length tracking              | O(n)    | O(1)  | readable |
| 10 | Same as V1, minimal                   | O(n)    | O(1)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def count_subarrays(nums, k):
    left = 0
    cur_sum = 0
    result = 0
    for right in range(len(nums)):
        cur_sum += nums[right]
        while cur_sum * (right - left + 1) >= k:
            cur_sum -= nums[left]
            left += 1
        result += right - left + 1
    return result
```

---

## Common Pitfalls

1. **Forgetting positivity assumption** — algorithm breaks with
   negatives.
2. **Off-by-one in count** — `right - left + 1` after shrinking.
3. **Updating result BEFORE shrinking** — count valid windows, not
   invalid.
4. **Confusing "<" with "<="** — `score < k` strict.
5. **Integer overflow** — in other languages, use 64-bit; Python is
   fine.

---

## Talking Points — Interview Cheat Sheet

If asked "why does the count formula work?":
> "After shrinking, [left..right] is the LARGEST valid window ending
> at right. All sub-windows (with start > left) have smaller score,
> so they're also valid. There are `right - left + 1` such starts."

If asked "what if the array has negatives?":
> "The score isn't monotonic in window size anymore, so this sliding
> window approach breaks. We'd need a different approach (perhaps
> prefix sums + something)."

If asked "is this O(n log n) possible without sliding window?":
> "Yes — for each right, binary search over left using prefix sums.
> O(n log n). The sliding window approach is faster (O(n)) but
> requires positivity."

If asked "why not use a deque?":
> "Overkill. Sliding window with two pointers and a sum is sufficient.
> Deque is for sliding window maximum/minimum (where we need ordering)."

---

## Related Problems

- **Minimum Size Subarray Sum** (LC #209) — different metric.
- **Subarray Product Less Than K** (LC #713) — multiplicative version.
- **Count Subarrays With Score Less Than K** — this problem.
- **Subarrays with K Different Integers** (LC #992) — different
  criterion.

---

## Variants

- **Score <= k**: change `>=` to `>`.
- **Maximum score**: track max instead of count.
- **Different formula** (e.g., sum + length): use that in the while
  condition.
- **Negative nums**: needs different approach.