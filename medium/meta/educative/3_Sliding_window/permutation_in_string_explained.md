# Permutation in String — 10 Solutions + Interview Thinking

## Problem
Given strings `s1` and `s2`, return true if `s2` contains a permutation
of `s1`.

Reference: LeetCode #567 / Educative Grokking — "Permutation in a
String".

---

## Interview Talking Points

Lead with the **fixed-size sliding window**: "Window of size |s1| over
s2; compare character counts."

---

## 10-Step Thinking Process

### 1. Understand
"Check if any substring of s2 has same character counts as s1."

### 2. Key Insight
A permutation of s1 has identical character counts. So we slide a
window of size |s1| over s2 and compare counts.

### 3. Pattern Recognition
- Fixed-size sliding window
- Counter comparison or sum-of-diffs

### 4. Edge Cases
- |s1| > |s2| → False.
- s1 == s2 → True.
- All same chars: must match length.

### 5. Tricky Detail — Maintaining the Counter

When sliding, add new char and remove outgoing char. Delete from dict
if count drops to 0 (or check via ==0 sentinel).

### 6. Algorithm
```
if len(s1) > len(s2): return False
need = Counter(s1)
window = Counter(s2[:len(s1)])
if window == need: return True
for i in range(len(s1), len(s2)):
    window[s2[i]] += 1
    out = s2[i - len(s1)]
    window[out] -= 1
    if window[out] == 0: del window[out]
    if window == need: return True
return False
```

### 7. Why It Works
Each iteration shifts the window by 1. Counter equality means the
window has the same character counts as s1, hence is a permutation.

### 8. Complexity
- **Time**: O(|s2|) for sliding + O(26) per comparison.
- **Space**: O(1) — bounded 26-letter Counter.

### 9. Code Structure
1. Edge case check.
2. Initial window.
3. Slide and compare.

### 10. Mental Trace
`s1="ab"`, `s2="eidbaooo"`:
- window="ei", not equal.
- Slide: window="id", not equal.
- Slide: window="db", not equal.
- Slide: window="ba", equal! True.

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Counter sliding window (BEST)         | O(n)    | O(1)  | canonical |
| 2  | 26-array sliding                      | O(n)    | O(1)  | faster cmp |
| 3  | matches counter                       | O(n)    | O(1)  | optimized |
| 4  | Brute force                           | O(n*m)  | O(1)  | educational |
| 5  | defaultdict sliding                   | O(n)    | O(1)  | pythonic |
| 6  | numpy fallback                        | O(n)    | O(1)  | vectorized |
| 7  | Anagram style                         | O(n)    | O(1)  | clean |
| 8  | dict.get sliding                      | O(n)    | O(1)  | manual |
| 9  | 26-array clean                        | O(n)    | O(1)  | readable |
| 10 | Same as V1, minimal                   | O(n)    | O(1)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
from collections import Counter

def check_inclusion(s1, s2):
    n = len(s1)
    if n > len(s2):
        return False
    need = Counter(s1)
    win = Counter(s2[:n])
    if win == need:
        return True
    for i in range(n, len(s2)):
        win[s2[i]] += 1
        out = s2[i - n]
        win[out] -= 1
        if win[out] == 0:
            del win[out]
        if win == need:
            return True
    return False
```

---

## Common Pitfalls

1. **Forgetting `del win[out]`** — comparison fails if both sides have
   the same entry with different counts vs no entry.
2. **Off-by-one in slide range** — `range(n, len(s2))`, not `len(s2) + 1`.
3. **Not handling |s1| > |s2|** — return False early.
4. **Wrong window size** — must be exactly |s1|.
5. **Forgetting `del win[out]` when count is 0** — affects equality.

---

## Talking Points — Interview Cheat Sheet

If asked "what's the time complexity?":
> "O(|s2|) since each character is added and removed from the window
>  counter at most once. Equality check is O(26) per slide."

If asked "could we use a 'matches' counter for early termination?":
> "Yes — track how many chars (out of 26) have matching counts. When
>  matches == 26, the window is a permutation. Reduces some comparisons."

If asked "what about uppercase letters or other characters?":
> "Same algorithm. Just adjust the array size or use Counter (which
>  handles arbitrary chars)."

If asked "what if s1 has duplicates?":
> "Same algorithm. Counter handles duplicates naturally."

---

## Related Problems

- **Find All Anagrams in a String** (LC #438) — return all indices.
- **Minimum Window Substring** (LC #76) — variable-size window.
- **Valid Anagram** (LC #242) — basic version.
- **Permutation in String** — this problem.

---

## Variants

- **Return all starting indices**: instead of returning on first match,
  collect all.
- **Count permutations**: same approach, count instead.
- **Min window containing permutation**: variable-size version.
- **Multiple s1's**: run for each.
