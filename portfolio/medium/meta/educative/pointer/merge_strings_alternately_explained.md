# Merge Strings Alternately — 10 Solutions + Interview Thinking

## Problem
Merge two strings by interleaving their characters in alternating order,
starting with the first character of `word1`. If one string is longer, append
the remaining characters of the longer string.

Reference: LeetCode #1768 / Educative Grokking — "Merge Strings Alternately".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Interleave `word1` and `word2` starting with `word1`'s first character.
Append leftover from the longer string at the end."

### 2. Key Insight
**Two-pointer sequential walk.** Both pointers advance at the same rate
until one exhausts; then drain the longer one.

### 3. Pattern Recognition
Linear two-pointer with a single output buffer.

### 4. Edge Cases
- Equal length → simple interleave, no leftovers.
- `word1` empty → return `word2`.
- `word2` empty → return `word1`.
- Both empty → `""`.
- `word1` much longer → drain `word1` after `word2` exhausts.

### 5. Tricky Detail
**Always start with `word1`'s char.** Once one string is exhausted, append
the rest of the longer string verbatim — do NOT interleave further.

### 6. Algorithm
```
i, j = 0, 0
result = []
while i < len(word1) and j < len(word2):
    result.append(word1[i])
    result.append(word2[j])
    i += 1; j += 1
result += word1[i:]   # leftover from word1 (if any)
result += word2[j:]   # leftover from word2 (if any)
return ''.join(result)
```

### 7. Why It Works
Each character appears exactly once, in the prescribed order:
- The interleaved portion takes one char from each, in sequence.
- The leftover portions preserve the original order.

### 8. Complexity
- Time: O(n + m).
- Space: O(n + m) for the result.

### 9. Code Structure
```python
def mergeAlt(word1, word2):
    i = j = 0
    res = []
    while i < len(word1) and j < len(word2):
        res += word1[i], word2[j]
        i += 1; j += 1
    res += word1[i:]
    res += word2[j:]
    return ''.join(res)
```

### 10. Mental Trace
`"abc"` and `"pqr"`:
- i=0,j=0: append 'a','p'; i=1, j=1
- i=1,j=1: append 'b','q'; i=2, j=2
- i=2,j=2: append 'c','r'; i=3, j=3
- Both exhausted; leftovers are empty.
- Result: `"apbqcr"` ✓

`"ab"` and `"pqrs"`:
- i=0,j=0: 'a','p' → i=1,j=1
- i=1,j=1: 'b','q' → i=2,j=2
- i=2 (>=len(word1)), loop exits. Leftover word1[i:] = "", word2[j:] = "rs".
- Result: `"apbqrs"` ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Notes |
|----|---------------------------------------|---------|-------|
| 1  | Canonical two-pointer (BEST)          | O(n+m)  | clean |
| 2  | `zip` + leftover                      | O(n+m)  | pythonic |
| 3  | `zip_longest`                         | O(n+m)  | handles unequal |
| 4  | `zip` + concat                        | O(n+m)  | one-liner |
| 5  | Loop with `min`                       | O(n+m)  | manual |
| 6  | Recursive                             | O(n+m)  | educational |
| 7  | Stack with `pop(0)`                   | O(n+m²) | slow |
| 8  | List-comp + slice                     | O(n+m)  | explicit |
| 9  | `zip_longest` one-liner               | O(n+m)  | elegant |
| 10 | `reduce`                              | O(n+m)  | functional |

---

## Recommended Interview Answer
**Solution 1** — clean, idiomatic:

```python
def mergeAlternately(word1, word2):
    i, j = 0, 0
    res = []
    while i < len(word1) and j < len(word2):
        res.append(word1[i]); res.append(word2[j])
        i += 1; j += 1
    res += word1[i:]
    res += word2[j:]
    return ''.join(res)
```

---

## Common Pitfalls
1. **Forgetting to handle empty input** — `word1 == ""` or `word2 == ""` should return the other.
2. **Interleaving further after one is exhausted** — once `i` reaches `len(word1)`, append the rest of `word2` verbatim.
3. **Forgetting which string starts** — `word1` always goes first.
4. **Off-by-one in the slicing** — `word1[i:]` is correct (no `-1` needed).
