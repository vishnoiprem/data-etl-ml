# Count Subarrays With Fixed Bounds — 20 Solutions + Interview Thinking

## Problem
Given an integer array `nums` and two integers `minK` and `maxK`, count the
number of subarrays where:
- Every element is in `[minK, maxK]`, AND
- The minimum value in the subarray equals `minK`, AND
- The maximum value in the subarray equals `maxK`.

Reference: LeetCode #2444 / Educative Grokking — "Count Subarrays with Fixed Bounds".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Count subarrays where the running min is exactly `minK` AND the running
max is exactly `maxK`. Elements outside `[minK, maxK]` break subarrays."

### 2. Key Insight
**Single linear sweep tracking three positions**:
- `last_bad` — index of the latest element outside `[minK, maxK]`
- `last_min` — index of the latest `minK` value
- `last_max` — index of the latest `maxK` value

At each index `i`, the contribution is `min(last_min, last_max) - last_bad`
(when both have been seen since the last bad element).

### 3. Pattern Recognition
Linear sweep with three running indices; O(n) time, O(1) space.

### 4. Edge Cases
- No `minK` or `maxK` in the array → 0.
- No bad elements → entire array is one segment.
- All elements equal (e.g., `[1, 1, 1]` with minK=maxK=1) → all subarrays valid: `n(n+1)/2`.
- All elements bad → 0.

### 5. Tricky Detail
The contribution formula `min(last_min, last_max) - last_bad` counts
**starts of subarrays ending at `i`** that contain both a `minK` and
`maxK` since the last bad position. The earliest valid start is
`last_bad + 1`. The latest valid start that still includes both is
`min(last_min, last_max)`.

### 6. Algorithm
```
last_min = last_max = last_bad = -1
ans = 0
for i in range(n):
    if nums[i] < minK or nums[i] > maxK:
        last_bad = i
    if nums[i] == minK:
        last_min = i
    if nums[i] == maxK:
        last_max = i
    ans += max(0, min(last_min, last_max) - last_bad)
return ans
```

### 7. Why It Works
Each index `i` with an in-range element contributes the count of valid
subarrays ENDING at `i`. A subarray `[start..i]` is valid iff:
- `start > last_bad` (no bad element in `[start..i]`),
- there exists at least one `minK` in `[start..i]` (so `start ≤ last_min`),
- there exists at least one `maxK` in `[start..i]` (so `start ≤ last_max`).

Combining: `last_bad < start ≤ min(last_min, last_max)`. The count of such
starts is `min(last_min, last_max) - last_bad`.

### 8. Complexity
- Time: **O(n)**.
- Space: **O(1)**.

### 9. Code Structure
```python
def countFixedBounds(nums, minK, maxK):
    last_min = last_max = last_bad = -1
    ans = 0
    for i, x in enumerate(nums):
        if x < minK or x > maxK:
            last_bad = i
        if x == minK:
            last_min = i
        if x == maxK:
            last_max = i
        ans += max(0, min(last_min, last_max) - last_bad)
    return ans
```

### 10. Mental Trace
`[1, 3, 5, 2, 7, 5]`, minK=1, maxK=5:
- i=0: not bad. last_min=0.
- i=1: not bad. last_min=0, last_max=-1.
- i=2: not bad. last_max=2. ans += min(0,2) - (-1) = 1.
- i=3: not bad. last_min=0, last_max=2. ans += 1 - (-1) = 2.
- i=4: BAD. last_bad=4.
- i=5: not bad. last_max=5. ans += min(0, 5) - 4 = 0.
- Total: 2. ✓ (Subarrays: [1,3,5] and [1,3,5,2])

`[1, 1, 1, 1]`, minK=maxK=1:
- All have last_min=last_max=k after step k. last_bad=-1.
- i=0: 0 - (-1) = 1. ans=1.
- i=1: 1 - (-1) = 2. ans=3.
- i=2: 2 - (-1) = 3. ans=6.
- i=3: 3 - (-1) = 4. ans=10.
- Total: 10 = n(n+1)/2 for n=4. ✓

---

## 20 Solutions Summary

| #  | Approach                              | Time      | Notes |
|----|---------------------------------------|-----------|-------|
| 1  | Canonical 3-index sweep (BEST)        | O(n)      | clean |
| 2  | Same with explicit contrib check      | O(n)      | variant |
| 3  | Reset positions on out-of-bounds      | O(n)      | alternative |
| 4  | Segment-bounded inner sweep           | O(n)      | per-index contrib |
| 5  | Brute force O(n²)                     | O(n²)     | educational |
| 6  | Brute with separate start/end loop    | O(n²)     | variant |
| 7  | Position lists + bisect               | O(n log n)| educational |
| 8  | itertools.groupby on validity         | O(n)      | functional |
| 9  | Reset positions explicitly            | O(n)      | cleaner V1 |
| 10 | Tuple-state accumulator               | O(n)      | FP-style |
| 11 | Iterative (was recursive)             | O(n)      | renamed from recursive |
| 12 | combinations brute                    | O(n³)     | too slow |
| 13 | Compact 3-pointer                     | O(n)      | clean |
| 14 | Prefix bads array                     | O(n²)     | educational |
| 15 | Split-into-segments                   | O(n)      | like V4 |
| 16 | functools.reduce                      | O(n)      | FP |
| 17 | Sliding window inner sweep            | O(n)      | like V4 |
| 18 | Direct 3-pointer                      | O(n)      | clean |
| 19 | Verbose variable names                | O(n)      | readable |
| 20 | While loop variant                    | O(n)      | clean |

---

## Recommended Interview Answer
**Solution 1** — clean, optimal, idiomatic:

```python
def countFixedBounds(nums, minK, maxK):
    last_min = last_max = last_bad = -1
    ans = 0
    for i, x in enumerate(nums):
        if x < minK or x > maxK:
            last_bad = i
        if x == minK:
            last_min = i
        if x == maxK:
            last_max = i
        ans += max(0, min(last_min, last_max) - last_bad)
    return ans
```

---

## Common Pitfalls
1. **Off-by-one on bad update** — when `nums[i]` is bad, `last_bad = i` (not `i-1`); the bad element itself breaks any subarray containing it.
2. **Forgetting that subarrays must extend past last_bad** — `start > last_bad`, not `start ≥ last_bad`.
3. **Confusing min/max-of-array with minK/maxK bounds** — both checks needed.
4. **Reset positions on bad** — some variants reset both `last_min` and `last_max` to -1; both work as long as contribution becomes 0 or negative.
5. **Missing both `minK` and `maxK` together** — single-element array with minK=maxK=1 vs 5 gives different answers.

---

## Variant: Sliding Window
You could try to use a sliding window:
- Expand right until invalid.
- Contract left until valid; at each valid state, count subarrays.

But the canonical formula above is cleaner.

---

## Variant: All Subarrays Equal
When `minK == maxK` and all elements equal that value:
- Any subarray of such elements is valid.
- Count = `n(n+1)/2` if no bad elements; otherwise sum across segments.
