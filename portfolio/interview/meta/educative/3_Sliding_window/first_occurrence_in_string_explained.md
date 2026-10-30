# First Occurrence in a String — 10 Solutions + Interview Thinking

## Problem
Find the first occurrence of `needle` in `haystack`, return index or -1.

Reference: LeetCode #28 / Educative Grokking — "First Occurrence in a
String".

---

## Interview Talking Points

Lead with **KMP** if asked about linear-time matching. Otherwise, the
**built-in `find()`** is the practical answer.

---

## 10-Step Thinking Process

### 1. Understand
"Find first index where needle starts in haystack."

### 2. Key Insight
Multiple approaches: brute force O(nm), KMP O(n+m), Rabin-Karp O(n),
or built-in.

### 3. Pattern Recognition
- String matching with failure function (KMP)
- Hash-based matching (Rabin-Karp)

### 4. Edge Cases
- empty needle → 0.
- needle longer than haystack → -1.
- needle at end → n - m.

### 5. Tricky Detail — KMP Failure Function

`fail[i]` = length of longest proper prefix of pattern[0..i] that's
also a suffix. On mismatch at position k, jump to `fail[k-1]`.

### 6. Algorithm (KMP)
```
m = len(needle)
fail = [0] * m
j = 0
for i in range(1, m):
    while j > 0 and needle[i] != needle[j]:
        j = fail[j - 1]
    if needle[i] == needle[j]:
        j += 1
    fail[i] = j

j = 0
for i in range(len(haystack)):
    while j > 0 and needle[j] != haystack[i]:
        j = fail[j - 1]
    if needle[j] == haystack[i]:
        j += 1
    if j == m:
        return i - m + 1
return -1
```

### 7. Why It Works
After partial match at position j in pattern and mismatch at haystack,
`fail[j-1]` tells us how many chars are still matching (prefix =
suffix). We can skip those and continue matching.

### 8. Complexity
- **Time**: O(n + m).
- **Space**: O(m).

### 9. Code Structure
1. Edge case (empty needle).
2. Build failure function.
3. Search haystack.

### 10. Mental Trace
`haystack="aabaaabaaac"`, `needle="aabaaac"`:
- fail = [0,1,0,1,2,2,3].
- Search: matches positions 0-6 in haystack. Return 4. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time       | Space | Notes |
|----|---------------------------------------|------------|-------|-------|
| 1  | KMP (BEST)                            | O(n+m)     | O(m)  | canonical |
| 2  | Brute force                           | O(nm)      | O(1)  | educational |
| 3  | Built-in find()                       | O(n+m) C   | O(1)  | practical |
| 4  | Slice comparison                      | O(nm)      | O(1)  | pythonic |
| 5  | KMP alt structure                     | O(n+m)     | O(m)  | alt |
| 6  | numpy fallback                        | O(n+m)     | O(m)  | vectorized |
| 7  | Brute for-else                        | O(nm)      | O(1)  | clean |
| 8  | Recursive KMP                         | O(n+m)     | O(m)  | educational |
| 9  | Refactored KMP                        | O(n+m)     | O(m)  | readable |
| 10 | KMP concise                           | O(n+m)     | O(m)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — KMP:

```python
def str_str(haystack, needle):
    if not needle:
        return 0
    m = len(needle)
    fail = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and needle[i] != needle[j]:
            j = fail[j - 1]
        if needle[i] == needle[j]:
            j += 1
        fail[i] = j
    j = 0
    for i in range(len(haystack)):
        while j > 0 and needle[j] != haystack[i]:
            j = fail[j - 1]
        if needle[j] == haystack[i]:
            j += 1
        if j == m:
            return i - m + 1
    return -1
```

For interviews, often the **built-in find()** or simple brute force is
acceptable.

---

## Common Pitfalls

1. **Empty needle** must return 0.
2. **Off-by-one in failure function** — `fail[i]` is length, not index.
3. **Resetting j incorrectly** — `j = fail[j-1]`, not `fail[j]`.
4. **Not building failure function** — without it, KMP degenerates.
5. **Wrong return index** — `i - m + 1`, where i is current pos.

---

## Talking Points — Interview Cheat Sheet

If asked "what's KMP?":
> "Knuth-Morris-Pratt. Precompute a failure function that tells you how
>  much of the pattern has been matched after a mismatch. Then skip
>  unnecessary comparisons, giving O(n+m) total time."

If asked "is KMP always faster?":
> "In practice, no — Python's find() is highly optimized C. KMP shines
>  when building from scratch or teaching algorithmic principles."

If asked "what's Rabin-Karp?":
> "Hash-based matching. Compute rolling hash of needle and window.
>  Match when hashes equal (and verify). O(n+m) expected time, but
>  worst case O(nm) due to collisions."

If asked "could we use built-in find?":
> "Yes. haystack.find(needle) returns the index or -1. Simple and
>  optimized."

---

## Related Problems

- **Repeated Substring Pattern** — uses KMP failure function.
- **Shortest Palindrome** (LC #214) — uses KMP.
- **Implement strStr()** (LC #28) — this problem.
- **Find the Index of the First Occurrence** — alternate name.

---

## Variants

- **All occurrences**: keep searching after finding one.
- **Ignore case**: lowercase both strings.
- **Wildcards** (`?`, `*`): requires DP or backtracking.
- **Last occurrence**: reverse the search.
