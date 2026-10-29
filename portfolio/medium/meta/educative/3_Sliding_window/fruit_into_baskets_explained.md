# Fruit Into Baskets — 10 Solutions + Interview Thinking

## Problem
Given an array `fruits` where `fruits[i]` is the type of fruit at
position `i`, find the longest contiguous subarray containing at most 2
distinct fruit types.

Reference: LeetCode #904 / Educative Grokking — "Fruit Into Baskets".

---

## Interview Talking Points

Lead with the **invariant**: "The window always has at most 2 distinct
types. When it grows beyond, we shrink from the left."

Note this is the **longest-subarray-with-at-most-K-distinct** pattern
with K=2.

---

## 10-Step Thinking Process

### 1. Understand
"Longest contiguous subarray with ≤ 2 distinct values."

### 2. Key Insight
Sliding window with a Counter tracking type frequencies. When the number
of distinct types > 2, shrink from `left`.

### 3. Pattern Recognition
- Counter (or dict) for type frequencies
- Two pointers
- "Longest subarray with at most K distinct" template

### 4. Edge Cases
- All same type → `n`.
- 2 types total → `n`.
- More than 2 types scattered → small windows.

### 5. Tricky Detail — Removing Keys from Counter

When `cnt[fruits[left]]` reaches 0 after decrementing, we MUST `del
cnt[fruits[left]]` so `len(cnt)` accurately reflects distinct types.

### 6. Algorithm
```
from collections import Counter
cnt = Counter()
left = 0
best = 0
for right in range(n):
    cnt[fruits[right]] += 1
    while len(cnt) > 2:
        cnt[fruits[left]] -= 1
        if cnt[fruits[left]] == 0:
            del cnt[fruits[left]]
        left += 1
    best = max(best, right - left + 1)
return best
```

### 7. Why It Works
The window always has at most 2 distinct types. We track the maximum
size across all valid windows.

### 8. Complexity
- **Time**: O(n) — each element added and removed at most once.
- **Space**: O(1) for the Counter (≤ 3 keys at any time).

### 9. Code Structure
1. Initialize Counter, left, best.
2. Expand right.
3. While invalid (3+ types), shrink from left.
4. Update best.

### 10. Mental Trace
`fruits = [1, 2, 1]`:
- right=0 '1': cnt={1:1}. len=1. best=1.
- right=1 '2': cnt={1:1, 2:1}. len=2. best=2.
- right=2 '1': cnt={1:2, 2:1}. len=2. best=3.

Returns 3. ✓

`fruits = [1, 2, 3, 2, 2]`:
- right=0 '1': cnt={1:1}. best=1.
- right=1 '2': cnt={1:1, 2:1}. best=2.
- right=2 '3': cnt={1:1, 2:1, 3:1}. len=3 > 2.
  - shrink: cnt[1]=0, del. left=1. cnt={2:1, 3:1}. len=2.
- right=3 '2': cnt={2:2, 3:1}. best=3.
- right=4 '2': cnt={2:3, 3:1}. best=4.

Returns 4. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Counter + sliding window (BEST)       | O(n)    | O(1)  | canonical |
| 2  | defaultdict                           | O(n)    | O(1)  | pythonic |
| 3  | Counter inline (V1 logic)             | O(n)    | O(1)  | same as V1 |
| 4  | Last-index dict                       | O(n)    | O(1)  | alt |
| 5  | Brute force                           | O(n²)   | O(1)  | educational |
| 6  | Counter brute                         | O(n²)   | O(n)  | educational |
| 7  | Last-index, find min via key           | O(n)    | O(1)  | cleaner V4 |
| 8  | Last-index, manual min scan           | O(n)    | O(1)  | explicit |
| 9  | Recursive                             | O(n)    | O(n)  | call stack |
| 10 | Dict + distinct counter               | O(n)    | O(1)  | explicit count |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
from collections import Counter

def total_fruit(fruits):
    cnt = Counter()
    left = 0
    best = 0
    for right, f in enumerate(fruits):
        cnt[f] += 1
        while len(cnt) > 2:
            cnt[fruits[left]] -= 1
            if cnt[fruits[left]] == 0:
                del cnt[fruits[left]]
            left += 1
        best = max(best, right - left + 1)
    return best
```

---

## Common Pitfalls

1. **Forgetting `del cnt[k]` when count drops to 0** — `len(cnt)`
   would be wrong.
2. **Confusing with "longest with exactly 2 distinct"** — different
   problem; use "at most K" minus "at most K-1".
3. **Using list/set for tracking types** — won't tell you when a type
   disappears from the window.
4. **Off-by-one in window size** — `right - left + 1`.
5. **Returning length of last valid window, not max** — must track
   `best` continuously.

---

## Talking Points — Interview Cheat Sheet

If asked "how does this generalize to K distinct?":
> "Replace `len(cnt) > 2` with `len(cnt) > K`. Everything else stays
> the same. Works for any K."

If asked "how do we count such windows instead of finding max?":
> "Each time the window is valid, count `right - left + 1` new windows
> ending at `right`. Or use the 'at most K minus at most K-1' trick."

If asked "what's the alternative approach?":
> "Track the last index of each type. When you exceed 2 types, drop
> the type with the oldest last index, and set `left` to its index + 1.
> Same O(n), different implementation."

If asked "isn't this just 'longest substring with K distinct chars'?":
> "Yes! Same template, different domain. The classic version is
> LeetCode #340 'Longest Substring with At Most K Distinct Characters'."

---

## Related Problems

- **Longest Substring with At Most K Distinct Characters** (LC #340) —
  same template, K parameter.
- **Longest Substring with At Most Two Distinct Characters** (LC #159)
  — K=2 with strings.
- **Subarrays with K Different Integers** (LC #992) — counts subarrays
  with exactly K distinct.
- **Count Number of Nice Subarrays** — different (parity-based).

---

## Variants

- **K distinct (general)**: change `len(cnt) > 2` to `len(cnt) > K`.
- **Exactly K distinct**: "at most K" minus "at most K-1".
- **Top-K dominant type**: different problem.
- **Strings instead of arrays**: same approach.