# Substring With Concatenation of All Words — 10 Solutions + Interview Thinking

## Problem
Given `s` and array `words` (all same length), find all starting indices
of substrings that are concatenations of exactly the words in any
permutation.

Reference: LeetCode #30 / Educative Grokking — "Substring With
Concatenation of All Words".

---

## Interview Talking Points

Lead with the **interleave observation**: since each word has same length
k, we can treat s as k independent character streams.

---

## 10-Step Thinking Process

### 1. Understand
"Find all starting positions where a contiguous substring equals a
permutation of `words`."

### 2. Key Insight
Each word has length k. The concatenated substring has length m*k.
Within s, valid starting positions are at multiples of k (relative to
some offset). Process k interleave streams independently.

### 3. Pattern Recognition
- Multi-stream sliding window
- Counter comparison (need vs seen)

### 4. Edge Cases
- empty `words` or empty `s` → `[]`.
- `m * k > n` → `[]`.
- duplicates in `words` must appear that many times.

### 5. Tricky Detail — Interleaved Streams

For each offset `0..k-1`, the positions in that stream are
`offset, offset+k, offset+2k, ...`. These are disjoint and together
cover all possible starting positions for a window of length m*k.

### 6. Algorithm
```
need = Counter(words)
for offset in range(k):
    left = offset; seen = Counter(); count = 0
    for right in range(offset, n - k + 1, k):
        w = s[right:right+k]
        if w in need:
            seen[w] += 1; count += 1
            while seen[w] > need[w]:
                seen[s[left:left+k]] -= 1
                left += k; count -= 1
            if count == m:
                result.append(left)
                seen[s[left:left+k]] -= 1
                left += k; count -= 1
        else:
            seen.clear(); count = 0; left = right + k
```

### 7. Why It Works
Each starting index falls into exactly one offset class. Within a
class, sliding window over word chunks mirrors normal string sliding
window. When total in-window word count == m, window is full
concatenation; record and slide left by one word to find more.

### 8. Complexity
- **Time**: O(n) — each position in each interleave touched O(1) times.
- **Space**: O(m) — Counter.

### 9. Code Structure
1. Build need Counter.
2. For each offset (interleave), sliding window over word chunks.
3. Shrink when over-count; record when full.

### 10. Mental Trace
`s = "barfoothefoobarman"`, `words = ["foo","bar"]`, k=3, m=2, total=6.
- offset=0: positions 0,3,6,9,12,15.
  - right=0: "bar" in need, seen[bar]=1, count=1.
  - right=3: "foo" in need, seen[foo]=1, count=2. count==m. result=[0]. Slide.
  - right=6: "the" not in need. Reset.
  - right=9: "foo". seen[foo]=1, count=1.
  - right=12: "bar". count=2=m. result=[0,9].
- offset=1, 2: nothing matches.
- Total = [0, 9]. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time  | Space | Notes |
|----|---------------------------------------|-------|-------|-------|
| 1  | Per-offset sliding window (BEST)      | O(n)  | O(m)  | canonical |
| 2  | Brute force comparison                | O(n*m)| O(m)  | educational |
| 3  | defaultdict version                   | O(n)  | O(m)  | pythonic |
| 4  | dict.get version                      | O(n)  | O(m)  | manual |
| 5  | Same as V2, refactored                | O(n*m)| O(m)  | readable |
| 6  | numpy fallback                        | O(n)  | O(m)  | vectorized |
| 7  | Inline counting                       | O(n)  | O(m)  | alt |
| 8  | Alt code                              | O(n)  | O(m)  | same |
| 9  | Brute with dict equality              | O(n*m)| O(m)  | clean |
| 10 | Same as V1, minimal                   | O(n)  | O(m)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
from collections import Counter

def find_substring(s, words):
    if not s or not words:
        return []
    n, m, k = len(s), len(words), len(words[0])
    if m * k > n:
        return []
    need = Counter(words)
    result = []
    for offset in range(k):
        left, seen, count = offset, Counter(), 0
        for right in range(offset, n - k + 1, k):
            w = s[right:right + k]
            if w in need:
                seen[w] += 1
                count += 1
                while seen[w] > need[w]:
                    seen[s[left:left + k]] -= 1
                    left += k
                    count -= 1
                if count == m:
                    result.append(left)
                    seen[s[left:left + k]] -= 1
                    left += k
                    count -= 1
            else:
                seen.clear()
                count = 0
                left = right + k
    return result
```

---

## Common Pitfalls

1. **Wrong interleave offset range** — must be `0..k-1`, not just `0`.
2. **Missing slide-left step after record** — without it, infinite loop
   or wrong counts.
3. **Confusing word count vs seen count** — `count` is total in-window
   word count (== m at full window).
4. **Forgetting `del seen[w]`** when count drops to 0 — only matters if
   using Counter equality later; otherwise fine.
5. **Off-by-one with `n - k + 1`** — last word chunk starts at `n - k`.

---

## Talking Points — Interview Cheat Sheet

If asked "why k interleave streams?":
> "Each word is k chars. A concatenated substring starts at some offset
> 0..k-1 relative to its first word boundary. Process each offset
> independently — together they cover all possible starting indices."

If asked "could we sort the words?":
> "We could sort need and sort the window's words list, then compare.
>  But that's O(m log m) per window. Counter is more efficient."

If asked "what if words have different lengths?":
> "Different problem entirely. We'd need a different approach (e.g.,
>  backtracking or hash-based search)."

If asked "what's the time complexity?":
> "O(n). Each index is visited at most k times across the k offset
>  streams, so total visits are O(n*k). Within each visit, the Counter
>  operations are O(1) amortized."

---

## Related Problems

- **Minimum Window Substring** (LC #76) — different counting.
- **Find All Anagrams** (LC #438) — same counter pattern.
- **Permutation in String** (LC #567) — checks if any permutation.
- **Substring With Concatenation of All Words** — this problem.

---

## Variants

- **Return indices not list**: same algorithm.
- **Count instead of indices**: same algorithm; just count instead.
- **Variable word lengths**: trie-based search.
- **Case-insensitive**: lowercase the input.
