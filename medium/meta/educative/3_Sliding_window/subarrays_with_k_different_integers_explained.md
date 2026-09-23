# Subarrays with K Different Integers — 10 Solutions + Interview Thinking

## Problem
Given an integer array `nums` and integer `k`, return the number of
subarrays with EXACTLY `k` distinct integers.

Reference: LeetCode #992 / Educative Grokking — "Subarrays with K
Different Integers".

---

## Interview Talking Points

Lead with the **key insight**: "Exactly K = At most K − At most (K−1)."

Then describe the sliding window that counts subarrays with at most K
distinct.

---

## 10-Step Thinking Process

### 1. Understand
"Count subarrays where the count of distinct values equals exactly K."

### 2. Key Insight
Exactly K = (At most K) − (At most K−1). Each "at most K" can be
counted in O(n) with a sliding window.

### 3. Pattern Recognition
- Sliding window for "at most K distinct"
- For each right, count valid subarrays ending at right
- Subtract two counts

### 4. Edge Cases
- `k > len(set(nums))` → 0.
- `k == 1` → only subarrays of single type.
- All same elements → n(n+1)/2 when k=1.

### 5. Tricky Detail — Counting Subarrays Per Right

At each `right`, after shrinking `left` to make the window valid (at
most K distinct), the window `[left..right]` is valid. Any subarray
ending at `right` with start in `[left..right]` is also valid (fewer
elements = fewer distinct). There are `right - left + 1` such subarrays.

### 6. Algorithm
```
def at_most(k_val):
    cnt = Counter()
    left = 0
    result = 0
    for right in range(n):
        cnt[nums[right]] += 1
        while len(cnt) > k_val:
            cnt[nums[left]] -= 1
            if cnt[nums[left]] == 0: del cnt[nums[left]]
            left += 1
        result += right - left + 1
    return result

return at_most(k) - at_most(k - 1)
```

### 7. Why It Works
- Any subarray with exactly K distinct is counted in "at most K" but
  not in "at most K−1".
- The difference gives the exact count.

### 8. Complexity
- **Time**: O(n) per call to `at_most`, called twice → O(n) total.
- **Space**: O(K) for the counter.

### 9. Code Structure
1. Define `at_most(k_val)` helper.
2. Compute `at_most(k) - at_most(k-1)`.

### 10. Mental Trace
`nums = [1, 2, 1, 2, 3]`, `k = 2`:

**at_most(2)**:
| right | num | cnt        | left | result |
|-------|-----|------------|------|--------|
| 0     | 1   | {1}        | 0    | +1=1   |
| 1     | 2   | {1,2}      | 0    | +2=3   |
| 2     | 1   | {1,2}      | 0    | +3=6   |
| 3     | 2   | {1,2}      | 0    | +4=10  |
| 4     | 3   | {1,2,3} → shrink → {2,3}, left=1 | 1 | +4=14 |

Total: 14.

**at_most(1)**:
| right | num | cnt        | left | result |
|-------|-----|------------|------|--------|
| 0     | 1   | {1}        | 0    | +1=1   |
| 1     | 2   | {1,2} → {2}, left=1 | 1 | +1=2 |
| 2     | 1   | {2,1} → {1}, left=2 | 2 | +1=3 |
| 3     | 2   | {1,2} → {2}, left=3 | 3 | +1=4 |
| 4     | 3   | {2,3} → {3}, left=4 | 4 | +1=5 |

Total: 5.

Result: 14 − 5 = 9. Wait, expected 7. Let me re-verify...

Actually let me re-trace `at_most(2)`:
- right=0 (1): cnt={1:1}, left=0, result += 1. result=1.
- right=1 (2): cnt={1:1, 2:1}, left=0, result += 2. result=3.
- right=2 (1): cnt={1:2, 2:1}, left=0, result += 3. result=6.
- right=3 (2): cnt={1:2, 2:2}, left=0, result += 4. result=10.
- right=4 (3): cnt={1:2, 2:2, 3:1}, > 2 distinct. Shrink: cnt[1]=1, left=1. Still > 2. cnt[2]=1, left=2. cnt={1:1, 2:1, 3:1}, still > 2. cnt[1]=0, del. left=3. cnt={2:1, 3:1}, distinct=2. OK. result += 4-3+1=2. result=12.

Total at_most(2) = 12. at_most(1) = 5 (need to recheck).
- right=0 (1): cnt={1:1}, left=0, result += 1.
- right=1 (2): cnt={1:1, 2:1}, > 1. shrink: cnt[1]=0, del. left=1. cnt={2:1}. result += 1.
- right=2 (1): cnt={2:1, 1:1}, > 1. shrink: cnt[2]=0, del. left=2. cnt={1:1}. result += 1.
- right=3 (2): cnt={1:1, 2:1}, > 1. shrink: cnt[1]=0, del. left=3. cnt={2:1}. result += 1.
- right=4 (3): cnt={2:1, 3:1}, > 1. shrink: cnt[2]=0, del. left=4. cnt={3:1}. result += 1.

Total at_most(1) = 5.

Result = 12 − 5 = 7. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Counter + at_most (BEST)              | O(n)    | O(K)  | canonical |
| 2  | defaultdict + at_most                 | O(n)    | O(K)  | pythonic |
| 3  | Dual pointer single pass              | O(n)    | O(K)  | optimized |
| 4  | Brute force set                       | O(n²)   | O(K)  | educational |
| 5  | Brute force Counter                   | O(n²)   | O(K)  | educational |
| 6  | numpy fallback                        | O(n)    | O(K)  | vectorized |
| 7  | Recursive                             | O(n)    | O(n)  | educational |
| 8  | dict.get + at_most                    | O(n)    | O(K)  | manual |
| 9  | Manual loop                           | O(n)    | O(K)  | alt |
| 10 | Same as V9, minimal                   | O(n)    | O(K)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
from collections import Counter

def subarrays_with_k_distinct(nums, k):
    def at_most(k_val):
        cnt = Counter()
        left = 0
        result = 0
        for right in range(len(nums)):
            cnt[nums[right]] += 1
            while len(cnt) > k_val:
                cnt[nums[left]] -= 1
                if cnt[nums[left]] == 0:
                    del cnt[nums[left]]
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)
```

---

## Common Pitfalls

1. **Confusing "exactly K" with "at most K"** — must subtract two counts.
2. **Forgetting `del cnt[k]` when count drops to 0** — affects
   `len(cnt)`.
3. **Off-by-one in counting** — at each `right`, count is
   `right - left + 1`, not `right - left`.
4. **Calling `at_most(k-1)` when k=0** — would call `at_most(-1)`,
   which never enters the inner while loop and returns 0. OK but
   careful with negative.
5. **Re-counting windows** — make sure `at_most` is called twice,
   not nested in a way that confuses state.

---

## Talking Points — Interview Cheat Sheet

If asked "why subtract?":
> "Subarrays with exactly K distinct are counted in 'at most K' but not
> in 'at most K-1'. So the difference gives exactly K."

If asked "could we do this in a single pass?":
> "Yes — maintain two sliding windows simultaneously: one for 'at most
> K' and one for 'at most K-1'. The difference `left2 - left1` at each
> `right` gives the count of subarrays ending at `right` with exactly
> K distinct."

If asked "what's the time complexity?":
> "O(n). Each element is added and removed from each counter at most
> once. Two passes total (one for each `at_most`)."

If asked "what if K is large?":
> "Same approach. The Counter will have up to K keys at any time. Space
> is O(K) which is bounded by K, not n."

---

## Related Problems

- **Fruit Into Baskets** (LC #904) — K=2 case.
- **Longest Substring with At Most K Distinct** (LC #340) — max
  length, not count.
- **Count Number of Nice Subarrays** (LC #1248) — different criterion
  (parity).
- **Subarrays with K Different Integers** — this problem.

---

## Variants

- **Max length with exactly K**: use at_most to find longest window.
- **Subarrays with at most K distinct**: just one call.
- **Subarrays with at least K distinct**: total − at most (K-1).
- **Sum of lengths** instead of count: track length instead of count.