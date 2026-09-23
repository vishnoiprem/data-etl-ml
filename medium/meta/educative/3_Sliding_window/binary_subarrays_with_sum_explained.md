# Binary Subarrays With Sum — 10 Solutions + Interview Thinking

## Problem
Given a binary array `nums` and integer `goal`, count the subarrays
whose sum equals `goal`.

Reference: LeetCode #930 / Educative Grokking — "Binary Subarrays With
Sum".

---

## Interview Talking Points

Lead with the **at-most trick**: "Exactly K = atMost(K) − atMost(K−1)."

---

## 10-Step Thinking Process

### 1. Understand
"Count subarrays where sum == goal."

### 2. Key Insight
Define `atMost(k)` = number of subarrays with sum <= k. Then
`exactly(k) = atMost(k) - atMost(k-1)`. The `atMost` function is
computable in O(n) using sliding window (works because nums is binary).

### 3. Pattern Recognition
- Sliding window for sum <= k
- Subtract two counts

### 4. Edge Cases
- `goal == 0` → count of "all-zero" subarrays.
- All zeros → n*(n+1)/2 when goal = 0.
- `goal > sum(nums)` → 0.

### 5. Tricky Detail — atMost(−1) = 0

When goal = 0, we compute `atMost(0) - atMost(-1)`. The latter must
return 0 (no subarray has sum <= -1). We handle this with a guard.

### 6. Algorithm
```
def at_most(k):
    if k < 0: return 0
    left = 0; cur = 0; result = 0
    for right in range(n):
        cur += nums[right]
        while cur > k:
            cur -= nums[left]; left += 1
        result += right - left + 1
    return result

return at_most(goal) - at_most(goal - 1)
```

### 7. Why It Works
After shrinking, the window [left..right] has sum <= k. Every
sub-window (with start > left) has even smaller sum. So there are
`right - left + 1` valid starting positions for this right.

### 8. Complexity
- **Time**: O(n) per `at_most`, two calls → O(n).
- **Space**: O(1).

### 9. Code Structure
1. Define `at_most(k)`.
2. Return `at_most(g) - at_most(g-1)`.

### 10. Mental Trace
`nums=[1,0,1,0,1]`, `goal=2`:
- `at_most(2)` = 14, `at_most(1)` = 10. Difference = 4. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | at_most helper (BEST)                 | O(n)    | O(1)  | canonical |
| 2  | Same logic, alt code                  | O(n)    | O(1)  | same |
| 3  | Brute force                           | O(n²)   | O(1)  | educational |
| 4  | Prefix sum + hashmap                  | O(n)    | O(n)  | alternative |
| 5  | defaultdict version                   | O(n)    | O(n)  | pythonic |
| 6  | numpy fallback                        | O(n)    | O(1)  | vectorized |
| 7  | Manual hashmap                        | O(n)    | O(n)  | alt |
| 8  | Same as V1, refactored                | O(n)    | O(1)  | readable |
| 9  | accumulate + Counter                  | O(n)    | O(n)  | functional |
| 10 | Same as V1, minimal                   | O(n)    | O(1)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def num_subarrays_with_sum(nums, goal):
    def at_most(k):
        if k < 0:
            return 0
        left = 0
        cur = 0
        result = 0
        for right in range(len(nums)):
            cur += nums[right]
            while cur > k:
                cur -= nums[left]
                left += 1
            result += right - left + 1
        return result

    return at_most(goal) - at_most(goal - 1)
```

---

## Common Pitfalls

1. **Forgetting `at_most(-1) == 0`** — handles goal=0 case.
2. **Off-by-one in counting** — `right - left + 1` after shrinking.
3. **Modifying nums in place** — keep a copy.
4. **Calling with negative goal** — guard at start.
5. **Breaking early in brute force** — only when goal >= 0; with
   nums = 0, sum doesn't increase.

---

## Talking Points — Interview Cheat Sheet

If asked "why not just sliding window with sum == goal?":
> "Sliding window with exact equality is tricky. We could shrink
>  while sum >= goal and add 1 when sum == goal, but it's cleaner to
>  compute atMost twice and subtract."

If asked "could we use prefix sums?":
> "Yes. Number of subarrays with sum == goal = number of pairs (i, j)
>  with i < j and prefix[j] - prefix[i] == goal. Use a hashmap of
>  prefix sums to count pairs in O(n)."

If asked "what's the difference between this and 'subarray sum equals k'?":
> "Same algorithm works for any non-negative integers. This problem
>  happens to use binary (0/1), but the at_most trick is general."

---

## Related Problems

- **Subarray Sum Equals K** (LC #560) — general integers.
- **Count Number of Nice Subarrays** (LC #1248) — parity.
- **Number of Subarrays with Bounded Maximum** (LC #795) — different.
- **Binary Subarrays With Sum** — this problem.

---

## Variants

- **General non-negative integers**: same algorithm.
- **All integers**: need hashmap approach (prefix sums).
- **Max length with sum == goal**: track longest window.
- **Min length with sum == goal**: hashmap + first occurrence.
