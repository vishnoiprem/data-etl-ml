# Count Substring With K-Frequency Characters II — 10 Solutions + Interview Thinking

## Problem
Given a string `s` and integer `k`, count the substrings of `s` in which
the frequency of every character in the substring is at least `k`.

Reference: Educative Grokking — "Count Substring With K-Frequency
Characters II" (LeetCode #3327).

---

## Interview Talking Points

Lead with the **brute-force baseline** since this problem has tricky
sliding-window semantics (validity is NOT monotone in window size —
adding a new char can ADD a bad char with freq=1 < k).

Then discuss the per-char optimization and the O(n^2) approach.

---

## 10-Step Thinking Process

### 1. Understand
"Count substrings where every distinct character has freq >= k."

### 2. Key Insight
Validity is NOT monotone in window size — extending the window can
ADD a new character with frequency 1 (which is < k if k > 1), making
the window invalid. So a direct sliding window doesn't track valid
windows linearly.

### 3. Pattern Recognition
- Brute force: enumerate all O(n^2) substrings, check validity.
- Per-char tracking with 26-letter counter.

### 4. Edge Cases
- `k == 1` → every substring works → `n*(n+1)/2`.
- `k > n` → 0.
- All same chars with len n, k=2 → `n*(n-1)/2`.

### 5. Tricky Detail — Non-Monotonicity

If we expand the window by adding a new character, freq of existing
chars can only INCREASE (good), but we add a NEW char with freq 1
(bad if k > 1). So validity can flip in either direction on
extension.

### 6. Algorithm (Brute Force)
```
result = 0
for i in range(n):
    cnt = [0] * 26
    for j in range(i, n):
        cnt[ord(s[j]) - ord('a')] += 1
        if all(v == 0 or v >= k for v in cnt):
            result += 1
return result
```

### 7. Why It Works
We enumerate all substrings. For each, check if every char with
non-zero frequency has freq >= k.

### 8. Complexity
- **Time**: O(n² × 26) — for each of n² substrings, check 26 letters.
- **Space**: O(1) — fixed 26-array.

### 9. Code Structure
1. Outer loop over left.
2. Inner loop over right.
3. Maintain freq array.
4. Check validity after each char addition.

### 10. Mental Trace
`s = "aaabb", k = 3`:
- i=0: "a" cnt[a]=1 bad, "aa" cnt[a]=2 bad, "aaa" cnt[a]=3 OK,
  "aaab" cnt[b]=1 bad, "aaabb" cnt[b]=2 bad. 1 valid.
- i=1: "a" bad, "aa" bad, "aab" bad, "aabb" bad. 0.
- i=2: "a" bad, "ab" bad, "abb" bad. 0.
- i=3: "b" bad, "bb" bad. 0.
- i=4: "b" bad. 0.
- Total = 1. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time        | Space | Notes |
|----|---------------------------------------|-------------|-------|-------|
| 1  | Brute force 26-array (BEST baseline)  | O(n² × 26)  | O(1)  | canonical |
| 2  | Counter-based brute                   | O(n² × K)   | O(K)  | pythonic |
| 3  | valid flag (early break)              | O(n² × 26)  | O(1)  | readable |
| 4  | Raw array brute                       | O(n² × 26)  | O(1)  | alt |
| 5  | Inline brute                          | O(n² × 26)  | O(1)  | educational |
| 6  | numpy fallback                        | O(n²)       | O(1)  | vectorized |
| 7  | any() check                           | O(n² × 26)  | O(1)  | pythonic |
| 8  | defaultdict brute                     | O(n² × K)   | O(K)  | alt |
| 9  | Same as V1, refactored                | O(n² × 26)  | O(1)  | readable |
| 10 | Same as V1, minimal                   | O(n² × 26)  | O(1)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean baseline:

```python
def count_k_freq_substrings(s, k):
    n = len(s)
    result = 0
    for i in range(n):
        cnt = [0] * 26
        for j in range(i, n):
            cnt[ord(s[j]) - ord('a')] += 1
            if all(v == 0 or v >= k for v in cnt):
                result += 1
    return result
```

---

## Common Pitfalls

1. **Assuming sliding window works directly** — validity is NOT monotone.
2. **Off-by-one in checking `cnt[c]`** — `0 < cnt[c] < k` is BAD,
   `cnt[c] == 0` is OK (not in window).
3. **Confusing "every char" with "every char in window"** — chars
   with freq=0 don't need to satisfy freq >= k.
4. **Forgetting to reset counter for each i** — each new starting
   position needs a fresh count.
5. **Integer overflow** — in other languages; Python is fine.

---

## Talking Points — Interview Cheat Sheet

If asked "can we use sliding window?":
> "Direct sliding window is tricky because validity isn't monotone —
> adding a new char can ADD a character with freq=1 (which is < k if
> k>1). So we'd need a more sophisticated approach or accept O(n²)."

If asked "why O(n²) is acceptable?":
> "For n up to 3*10^4, O(n²) with a constant 26-letter check is
> ~9*10^9 operations, which is too slow. We need optimization for
> large n. But for smaller n or k=1 (where all substrings work),
> O(n²) is fine."

If asked "what's the k=1 special case?":
> "If k=1, every substring works (every char has freq >=1 in any
> non-empty substring). Total = n*(n+1)/2."

If asked "what if we want strictly less than k?":
> "Same algorithm with `cnt < k` instead of `cnt < k`. Need to add 1
> (or be careful about zero-freq chars)."

---

## Related Problems

- **Count Substrings With K-Frequency Characters I** (LC #3197) — k=1 case.
- **Number of Substrings With Fixed Ratio** — different constraint.
- **Substring with Concatenation of All Words** — words instead of chars.
- **Count Number of Nice Subarrays** (LC #1248) — parity constraint.

---

## Variants

- **Min frequency instead of >= k**: same algorithm, change check.
- **Different metric** (e.g., sum ≥ k): use prefix sums.
- **Longest such substring**: track max length over all valid windows.
- **Exact K distinct chars**: use at_most(K) − at_most(K-1).
