# Repeated DNA Sequences — 10 Solutions + Interview Thinking

## Problem
Given a string `s` of nucleotides `'A'`, `'C'`, `'G'`, `'T'`, find all
10-letter-long substrings that occur more than once. Return order doesn't
matter.

Reference: LeetCode #187 / Educative Grokking — "Repeated DNA Sequences".

---

## Interview Talking Points

Lead with the **invariant**: "Each 10-char window is a candidate. If
we've seen it before, add to result."

Then mention the rolling hash trick for constant-time window slide.

---

## 10-Step Thinking Process

### 1. Understand
"Find all length-10 substrings that appear at least twice in `s`."

### 2. Key Insight
Fixed-size sliding window. For each starting index `i`, extract
`s[i:i+10]`. Track occurrences in a hashmap. Return those with
count > 1.

### 3. Pattern Recognition
- Fixed window of length 10
- Hashmap (or Counter) of substring → count
- Filter substrings by count

### 4. Edge Cases
- `len(s) < 10` → empty result.
- `len(s) == 10` → empty (only one window, can't repeat).
- All same character (`"AAAAAAAAAA"`) → one big repeated substring.

### 5. Tricky Detail — Rolling Hash Encoding

DNA has only 4 chars. We can encode each char in 2 bits:
- A=00, C=01, G=10, T=11

A 10-char substring = 20 bits = a single integer. To slide:
- Shift left 2 bits, mask to 20 bits, OR in new char's 2 bits.
- Mask is `(1 << 20) - 1 = 0xFFFFF`.

This avoids string slicing and saves memory for very large inputs.

### 6. Algorithm (Simple Hashset)
```
seen = set()
result = set()
for i in range(len(s) - 9):
    sub = s[i:i+10]
    if sub in seen:
        result.add(sub)
    else:
        seen.add(sub)
return list(result)
```

### 7. Why It Works
Each substring is checked. If we've encountered it before (it's in
`seen`), it appears at least twice (current position + the prior
position that put it in `seen`). Add to `result`. The result set
ensures we add each repeated substring at most once.

### 8. Complexity
- **Time**: O(n · 10) for substring slicing, O(n) with rolling hash.
  Python slicing creates a new string each time, so O(10) per slice.
- **Space**: O(n) for the set of unique substrings (worst case).

### 9. Code Structure
1. Edge case: `len(s) < 10`.
2. Initialize sets.
3. Iterate over starting indices.
4. Compare substring with `seen`; update accordingly.

### 10. Mental Trace
`s = "AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT"`:

Substrings of length 10:
| i  | substring       | seen before? |
|----|-----------------|--------------|
| 0  | AAAAACCCCC      | no           |
| 1  | AAAACCCCC A     | no           |
| ...| ...             | no           |
| 10 | AAAAACCCCC      | YES → add    |
| ...| ...             |              |
| 15 | CCCCCAAAAA      | YES → add    |
| ...| ...             |              |

Result: `["AAAAACCCCC", "CCCCCAAAAA"]`. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time       | Space | Notes |
|----|---------------------------------------|------------|-------|-------|
| 1  | Hashset slice (BEST)                  | O(n·10)    | O(n)  | simple |
| 2  | Counter                               | O(n·10)    | O(n)  | counts |
| 3  | Hashset, dedupe result                | O(n·10)    | O(n)  | variant |
| 4  | Rolling hash (20-bit int)             | O(n)       | O(n)  | optimal |
| 5  | Dict counts                           | O(n·10)    | O(n)  | manual |
| 6  | defaultdict                           | O(n·10)    | O(n)  | pythonic |
| 7  | List comprehension                    | O(n·10)    | O(n)  | readable |
| 8  | Brute force O(n²)                     | O(n²)      | O(n)  | educational |
| 9  | Group by index                        | O(n·10)    | O(n)  | tracking |
| 10 | Recursive                             | O(n·10)    | O(n)  | call stack |

---

## Recommended Interview Answer

**Solution 1** — clean, idiomatic:

```python
def find_repeated_dna_sequences(s):
    if len(s) < 10:
        return []
    seen = set()
    result = set()
    for i in range(len(s) - 9):
        sub = s[i:i + 10]
        if sub in seen:
            result.add(sub)
        else:
            seen.add(sub)
    return list(result)
```

If asked about optimization:

```python
def find_repeated_dna_sequences(s):
    if len(s) < 10:
        return []
    char_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
    h = 0
    for i in range(10):
        h = (h << 2) | char_map[s[i]]
    seen = {h}
    result = set()
    mask = (1 << 20) - 1
    for i in range(10, len(s)):
        h = ((h << 2) & mask) | char_map[s[i]]
        if h in seen:
            result.add(s[i - 9:i + 1])
        else:
            seen.add(h)
    return list(result)
```

---

## Common Pitfalls

1. **Off-by-one in range** — there are `n - 10 + 1 = n - 9` windows.
2. **Adding to result twice** — use a set to dedupe.
3. **Using a list and checking `count > 1` without Counter** — slower.
4. **Slicing cost** — Python slicing copies the substring. For very
   large `n`, prefer rolling hash.
5. **Hash collisions with rolling hash** — possible but rare for 20-bit.
   For safety, validate the actual substring when a collision occurs.

---

## Talking Points — Interview Cheat Sheet

If asked "what's the time complexity?":
> "Simple version: O(n · 10) due to string slicing. With rolling hash,
> O(n). Space is O(n) for the hashmap."

If asked "why not use Counter?":
> "We don't need exact counts — just 'seen at least twice'. A single
> hashset works and uses less memory."

If asked "what about hash collisions?":
> "With 20-bit rolling hash, collisions are possible (~1 in 1M).
> Production code would validate the actual substring when a hash
> collision is detected. For interviews, this is usually fine."

If asked "could we use a trie?":
> "Yes! Each path of length 10 represents a substring. Track count
> at each node. O(n · 10) time, O(n · 4) space (trie nodes)."

---

## Related Problems

- **Encode and Decode TinyURL** — different domain (hashing URLs).
- **Longest Repeating Character Replacement** — different problem
  (uniform substring).
- **Substring with Concatenation of All Words** — multi-word search.

---

## Variants

- **k-letter substrings**: change window size to `k`. Same approach.
- **Minimum k for repeats**: binary search on k with "exists
  repeat?" predicate.
- **Top K frequent k-mers**: track counts, sort, take top.