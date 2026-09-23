# Longest Substring Without Repeating Characters — 10 Solutions + Interview Thinking

## Problem
Given a string `s`, find the length of the longest substring without
repeating characters.

Reference: LeetCode #3 / Educative Grokking — "Longest Substring Without
Repeating Characters".

---

## Interview Talking Points

Lead with the **invariant**: "The window `[left, right]` always contains
unique characters. When a repeat is encountered, `left` jumps past the
previous occurrence."

Then describe why `left = max(left, last[c]+1)` (to prevent retreating).

---

## 10-Step Thinking Process

### 1. Understand
"Find the longest contiguous substring where no character appears twice."

### 2. Key Insight
Sliding window with a `last_seen` map. For each new char `c` at index
`right`, if `c` was last seen at index `last[c]`, the window must start
at `max(left, last[c]+1)`.

### 3. Pattern Recognition
- Two pointers
- Hashmap `char -> last index`
- Update `left = max(left, last[c]+1)` on repeat

### 4. Edge Cases
- Empty string → 0.
- All same char ("bbbb") → 1.
- All unique ("abcdef") → len(s).
- "abba" — `left` must NOT retreat. Solution: use `max(left, last[c]+1)`.

### 5. Tricky Detail — Why `max` Is Necessary

Consider `"abba"`:
- right=0 'a': last[a]=-1. left=0. last[a]=0.
- right=1 'b': last[b]=-1. left=0. last[b]=1.
- right=2 'b': last[b]=1 >= left=0. left = 1+1 = 2. last[b]=2.
- right=3 'a': last[a]=0. **But** left=2 now, last[a]=0 < left=2.
  - If we did `left = last[a]+1 = 1`, we'd retreat left to 1, which
    is wrong (window [1..3]="bba" has a repeat).
  - With `max(left, last[a]+1) = max(2, 1) = 2`, we keep left=2.
  - Window [2..3]="ba" len 2. ✓

### 6. Algorithm
```
last = {}  # default -1 if missing
left = 0
best = 0
for right in range(n):
    c = s[right]
    if c in last and last[c] >= left:
        left = last[c] + 1
    last[c] = right
    best = max(best, right - left + 1)
return best
```

### 7. Why It Works
`left` always points to the smallest index such that `s[left..right]`
has all unique chars. When we see `c` at `right`, if `c` is already in
the window (i.e., `last[c] >= left`), we must shift `left` past it.
Otherwise, we leave `left` alone. Either way, after the update, the
window is unique.

### 8. Complexity
- **Time**: O(n) — each char visited once.
- **Space**: O(min(n, alphabet)) for the last-seen map.

### 9. Code Structure
1. Initialize `last`, `left`, `best`.
2. Loop `right` from 0 to n-1.
3. Update `left` if needed.
4. Update `last[c]` and `best`.

### 10. Mental Trace
`s = "abcabcbb"`:
- right=0 'a': last[a] missing. left=0. last[a]=0. best=1.
- right=1 'b': not seen. left=0. last[b]=1. best=2.
- right=2 'c': not seen. left=0. last[c]=2. best=3.
- right=3 'a': last[a]=0 >= left=0. left=1. last[a]=3. best=3.
- right=4 'b': last[b]=1 >= left=1. left=2. last[b]=4. best=3.
- right=5 'c': last[c]=2 >= left=2. left=3. last[c]=5. best=3.
- right=6 'b': last[b]=4 >= left=3. left=5. last[b]=6. best=3.
- right=7 'b': last[b]=6 >= left=5. left=7. last[b]=7. best=3.
- Returns 3. ✓

`s = "abba"`:
- right=0 'a': left=0, last[a]=0, best=1.
- right=1 'b': left=0, last[b]=1, best=2.
- right=2 'b': last[b]=1 >= left=0. left=2. last[b]=2. best=2.
- right=3 'a': last[a]=0 < left=2. left stays 2. last[a]=3. best=2.
- Returns 2. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Hashmap + max trick (BEST)            | O(n)    | O(min(n,k)) | canonical |
| 2  | ASCII array (size 128)                | O(n)    | O(128) | faster |
| 3  | defaultdict                           | O(n)    | O(min(n,k)) | pythonic |
| 4  | Set-based shrink                      | O(n)    | O(min(n,k)) | O(2n) |
| 5  | Brute force                           | O(n²)   | O(n)  | educational |
| 6  | Counter (freq > 1 means repeat)       | O(n)    | O(min(n,k)) | counter-based |
| 7  | Bitmap                                | O(n)    | O(1)  | over-engineered |
| 8  | 256-array (full ASCII)                | O(n)    | O(256) | bigger array |
| 9  | Recursive                             | O(n)    | O(min(n,k)) | educational |
| 10 | Pythonic set + shrink                 | O(n)    | O(min(n,k)) | clean |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal, idiomatic:

```python
def length_of_longest_substring(s):
    last = {}
    left = 0
    best = 0
    for right, c in enumerate(s):
        if c in last and last[c] >= left:
            left = last[c] + 1
        last[c] = right
        best = max(best, right - left + 1)
    return best
```

---

## Common Pitfalls

1. **Forgetting `last[c] >= left` check** — without it, we'd retreat
   `left` in cases like "abba".
2. **Using `left = last[c] + 1` without `max`** — same issue.
3. **Not updating `last[c] = right` AFTER computing `left`** — must
   update after to avoid using the new index.
4. **Resetting `left` to 0 on repeat** — that loses valid context.
5. **Using a set without tracking indices** — works (V4) but slower
   due to repeated lookups.

---

## Talking Points — Interview Cheat Sheet

If asked "why `max(left, last[c]+1)`?":
> "If the previous occurrence of `c` is BEFORE the current window
> (i.e., `last[c] < left`), we don't need to move `left`. Using `max`
> prevents retreating `left` backward."

If asked "what if the input has unicode?":
> "Use a `dict` instead of an array (Solution 1, 3, 6, 9, 10).
> Arrays only work for bounded alphabets like ASCII (size 128 or 256)."

If asked "what's the difference between V4 (set) and V1 (map)?":
> "V4 uses a set: when we see a repeat, we shrink from `left` until the
> repeat is removed. V1 jumps `left` directly using `last[c]+1`. Both
> are O(n) amortized, but V1 is simpler and faster."

If asked "what's the bottleneck?":
> "For very long strings with a small alphabet (like DNA), the set/map
> is small. For very long strings with large alphabets (Unicode),
> the map can grow large. In practice, O(min(n, alphabet)) is fine."

---

## Related Problems

- **Longest Substring with At Most K Distinct Characters** — generalizes
  to K distinct (use Counter).
- **Longest Substring with At Most Two Distinct Characters** — K=2.
- **Fruit Into Baskets** — same template.
- **Subarrays with K Different Integers** — counts such subarrays.
- **Minimum Window Substring** — different requirement (cover all
  chars of `t`).

---

## Variants

- **At most K distinct**: use `freq` Counter; shrink while
  `len(freq) > k`.
- **Exactly K distinct**: count windows with at most K minus at most K-1.
- **Longest substring with K repeats allowed**: use Counter with
  threshold.