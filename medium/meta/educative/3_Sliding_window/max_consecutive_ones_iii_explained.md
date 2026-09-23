# Max Consecutive Ones III — 10 Solutions + Interview Thinking

## Problem
Longest subarray of 1's if we can flip at most k 0's in a binary array.

Reference: LeetCode #1004 / Educative Grokking — "Max Consecutive
Ones III".

---

## Interview Talking Points

Lead with the **longest window with at most k zeros** reframing.

---

## 10-Step Thinking Process

### 1. Understand
"Find longest subarray achievable by flipping <= k zeros."

### 2. Key Insight
Flipping k zeros turns them to 1's. So we want the longest subarray
containing at most k zeros.

### 3. Pattern Recognition
- Sliding window with at most k zeros
- Counter for zeros

### 4. Edge Cases
- k == 0 → longest run of 1's.
- All zeros with k >= n → n.
- All ones → n.

### 5. Tricky Detail — Window Expansion

The window expands as `right` advances. It contracts only when zero
count exceeds k. Track max length throughout.

### 6. Algorithm
```
left = 0; zero = 0; result = 0
for right in range(n):
    if nums[right] == 0: zero += 1
    while zero > k:
        if nums[left] == 0: zero -= 1
        left += 1
    result = max(result, right - left + 1)
return result
```

### 7. Why It Works
Window always has at most k zeros, so flipping them yields all 1's.
Track max window length across all valid windows.

### 8. Complexity
- **Time**: O(n).
- **Space**: O(1).

### 9. Code Structure
1. Init.
2. Iterate right.
3. Shrink if zero_count > k.
4. Update result.

### 10. Mental Trace
`nums=[1,1,1,0,0,0,1,1,1,1,0]`, `k=2`:
- right=0,1,2: zero=0. result=3.
- right=3: zero=1. result=4.
- right=4: zero=2. result=5.
- right=5: zero=3. shrink: zero=2, left=4. result=max(5, 5-4+1=2)=5.
- right=6: zero=2. result=3.
- right=7: result=4.
- right=8: result=5.
- right=9: result=6.
- right=10: zero=3. shrink: zero=2, left=5. result=max(6, 6)=6.

Final = 6. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Sliding window (BEST)                 | O(n)    | O(1)  | canonical |
| 2  | Counter for tracking                  | O(n)    | O(1)  | pythonic |
| 3  | Same logic, alt code                  | O(n)    | O(1)  | same |
| 4  | Brute force                           | O(n²)   | O(1)  | educational |
| 5  | Track one_count instead              | O(n)    | O(1)  | alt |
| 6  | numpy fallback                        | O(n)    | O(1)  | vectorized |
| 7  | Recursive                             | O(n)    | O(n)  | educational |
| 8  | Same with length tracking             | O(n)    | O(1)  | alt |
| 9  | Skip-zero variant                     | O(n)    | O(1)  | clean |
| 10 | Same as V1, minimal                   | O(n)    | O(1)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def longest_ones(nums, k):
    left = 0
    zero = 0
    result = 0
    for right in range(len(nums)):
        if nums[right] == 0:
            zero += 1
        while zero > k:
            if nums[left] == 0:
                zero -= 1
            left += 1
        result = max(result, right - left + 1)
    return result
```

---

## Common Pitfalls

1. **Shrinking past max** — track max BEFORE or AFTER shrinking;
   both work, just be consistent.
2. **Tracking wrong variable** — count zeros, not ones.
3. **Off-by-one in shrink** — increment left AFTER decrementing zero.
4. **Off-by-one in result** — `right - left + 1` after shrinking.
5. **Single-pass vs two-pass** — single pass works.

---

## Talking Points — Interview Cheat Sheet

If asked "why track zeros instead of ones?":
> "Tracking zeros directly maps to the constraint (at most k zeros).
>  Tracking ones gives the same info indirectly."

If asked "can we use prefix sums?":
> "Yes — for each right, binary search for smallest left with
>  (right - left + 1) - (prefix_ones[right+1] - prefix_ones[left]) <= k.
>  O(n log n)."

If asked "what if k is large (>= n)?":
> "Window never shrinks; result = n."

If asked "what's the difference from LC 487 (Max Consecutive Ones II)?":
> "LC 487 allows flipping at most ONE zero (k=1 fixed). LC 1004
>  generalizes to k."

---

## Related Problems

- **Max Consecutive Ones II** (LC #487) — k=1 case.
- **Max Consecutive Ones** (LC #485) — no flips.
- **Longest Repeating Character Replacement** — different.
- **Longest Subarray With Diff At Most Limit** — different metric.

---

## Variants

- **Min length with at most k zeros**: track min instead of max.
- **Number of subarrays with at most k zeros**: count.
- **At most k other value**: generalize.
- **Multiple flips counted**: same algorithm.
