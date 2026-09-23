# Number of Substrings With All Three Characters — 10 Solutions + Interview Thinking

## Problem
Given a string `s` of 'a', 'b', 'c', count substrings containing at
least one occurrence of each character.

Reference: Educative Grokking — "Number of Substrings With All Three
Characters" (similar to LeetCode #1357).

---

## Interview Talking Points

Lead with the **shrinking-while-valid trick**: "For each right, shrink
from left until window is INVALID. Then valid substrings ending at
right = left."

---

## 10-Step Thinking Process

### 1. Understand
"Count substrings containing at least one 'a', 'b', and 'c'."

### 2. Key Insight
For each right, find the smallest invalid left. Then valid i for that
right = number of i in [0..left-1].

### 3. Pattern Recognition
- Sliding window with validity check
- Counter for each of 3 chars

### 4. Edge Cases
- n < 3 → 0.
- All same chars → 0.
- Length 3 with all distinct → 1.

### 5. Tricky Detail — Shrink while VALID

We shrink from left while window has all 3 chars (>0 of each). Once
window becomes invalid (or empty), we stop. The smallest invalid i =
left.

### 6. Algorithm
```
left = 0; cnt = {'a':0, 'b':0, 'c':0}; result = 0
for right in range(n):
    cnt[s[right]] += 1
    while left <= right and cnt['a'] > 0 and cnt['b'] > 0 and cnt['c'] > 0:
        cnt[s[left]] -= 1
        left += 1
    result += left
return result
```

### 7. Why It Works
After shrinking, [left..right] is invalid (or empty). All [i..right]
for i in [0..left-1] are valid (since we shrank past exactly the
boundary). Count = left.

### 8. Complexity
- **Time**: O(n).
- **Space**: O(1).

### 9. Code Structure
1. Initialize counter.
2. For each right, add char.
3. Shrink while valid.
4. Add left to result.

### 10. Mental Trace
`s = "abcabc"`:
- right=0 'a': cnt[a]=1. Not all 3. result=0.
- right=1 'b': cnt[b]=1. Not all 3. result=0.
- right=2 'c': cnt[c]=1. All 3. Shrink: cnt[a]=0, left=1. Not all 3. result=1.
- right=3 'a': cnt[a]=1. All 3. Shrink: cnt[b]=0, left=2. result=3.
- right=4 'b': cnt[b]=1. All 3. Shrink: cnt[c]=0, left=3. result=6.
- right=5 'c': cnt[c]=1. All 3. Shrink: cnt[a]=0, left=4. result=10. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Sliding window + 3 vars (BEST)        | O(n)    | O(1)  | canonical |
| 2  | dict-based counter                    | O(n)    | O(1)  | pythonic |
| 3  | Brute force                           | O(n²)   | O(1)  | educational |
| 4  | Counter (collections)                 | O(n)    | O(1)  | cleaner |
| 5  | defaultdict version                   | O(n)    | O(1)  | pythonic |
| 6  | numpy fallback                        | O(n)    | O(1)  | vectorized |
| 7  | index array                           | O(n)    | O(1)  | readable |
| 8  | inline if-else                        | O(n)    | O(1)  | minimal |
| 9  | Recursive                             | O(n)    | O(n)  | educational |
| 10 | Same as V2, minimal                   | O(n)    | O(1)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def number_of_substrings(s):
    cnt_a = cnt_b = cnt_c = 0
    left = 0
    result = 0
    for right in range(len(s)):
        c = s[right]
        if c == 'a':   cnt_a += 1
        elif c == 'b': cnt_b += 1
        else:          cnt_c += 1
        while left <= right and cnt_a > 0 and cnt_b > 0 and cnt_c > 0:
            lc = s[left]
            if lc == 'a':   cnt_a -= 1
            elif lc == 'b': cnt_b -= 1
            else:           cnt_c -= 1
            left += 1
        result += left
    return result
```

---

## Common Pitfalls

1. **Shrinking while INVALID** — should be shrink while VALID.
2. **Off-by-one in result calculation** — `result += left`, not `left+1`.
3. **Confusing "all three >0" with "all three >=1"** — they mean same thing here.
4. **Forgetting guard** `left <= right` in while loop.
5. **Wrong test for empty window** — cnt of all chars = 0 means invalid (vacuously).

---

## Talking Points — Interview Cheat Sheet

If asked "why shrink while valid?":
> "We want the smallest invalid i, which equals the number of valid i's
>  in [0..right]."

If asked "what if there are more than 3 distinct chars?":
> "Generalize: track counts of each char. Valid = all >0. Same algorithm."

If asked "could we just count valid windows directly?":
> "Yes, but counting invalid windows gives us the count in one variable:
>  `result += left` directly gives the count of valid i's."

If asked "what's the time complexity?":
> "O(n). Each character is added and removed at most once."

---

## Related Problems

- **Minimum Window Substring** (LC #76) — different objective.
- **Find All Anagrams** (LC #438) — fixed-size.
- **Substrings With K Different** (LC #992) — K distinct.
- **Substrings Containing All Three Characters** — this problem.

---

## Variants

- **Min length**: track min length of valid window.
- **K distinct chars**: generalize the algorithm.
- **At least k of each**: change comparison to >= k.
- **Longest such substring**: track max window length.
