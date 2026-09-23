# Valid Palindrome — 20 Solutions + Interview Thinking

## Problem
A phrase is a palindrome if, after converting all uppercase to lowercase and
removing all non-alphanumeric characters, it reads the same forward and
backward. Determine if `s` is a palindrome.

Reference: LeetCode #125 / Educative Grokking — "Valid Palindrome".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Determine if `s` is a palindrome, ignoring case and non-alphanumeric chars."

### 2. Observe — Key Insight
**Two pointers from both ends.** Skip non-alphanumeric, compare lowercase.
Total work O(n), no extra string needed.

### 3. Pattern Recognition
**Convergent two-pointer.** Both pointers move inward, comparing mirrored
characters.

### 4. Edge Cases
- Empty or single char → True.
- All non-alphanumeric → True (filtered string is empty).
- Mixed case → must lowercase before compare.
- Punctuation in middle → skip both sides.

### 5. Tricky Detail
**ASCII-only optimization**: instead of `isalnum()` (which handles Unicode),
use `ord()` checks on `[a-zA-Z0-9]` for ~10x speedup. For interviews, either
works; mention both.

### 6. Algorithm
```
left, right = 0, n - 1
while left < right:
    while left < right and not is_alnum(s[left]): left += 1
    while left < right and not is_alnum(s[right]): right -= 1
    if left >= right: break
    if s[left].lower() != s[right].lower(): return False
    left += 1; right -= 1
return True
```

### 7. Why It Works
Each comparison advances both pointers by 1 (after skipping). At most 2n
pointer movements + n comparisons → O(n) time, O(1) extra space.

### 8. Complexity
- **Time:** O(n).
- **Space:** O(1) extra (or O(n) if you build the filtered string).

### 9. Code Structure
```python
def is_palindrome(s):
    left, right = 0, len(s) - 1
    while left < right:
        # skip non-alnum
        # compare lowercase
        # advance
    return True
```

### 10. Mental Trace
`"A man, a plan, a canal: Panama"` (length 30):
- L=0 'A', R=29 'a' → match.
- L=1 ' ', R=28 'm' → skip L; ' ' skip R too.
- ...eventually all pairs match → **True** ✓

---

## 20 Solutions Summary

| #  | Approach                                   | Time | Notes |
|----|--------------------------------------------|------|-------|
| 1  | Canonical two-pointer                      | O(n) | ★★★★★ |
| 2  | Filter then reverse list                   | O(n) | pythonic |
| 3  | Filter string then reverse                 | O(n) | same idea |
| 4  | Explicit ASCII skip                        | O(n) | educational |
| 5  | ord() range checks                         | O(n) | fastest |
| 6  | Stack-based                                | O(n) | pop from front |
| 7  | Deque-based                                | O(n) | O(1) popleft |
| 8  | Recursive                                  | O(n) | needs stack |
| 9  | `joined(reversed(...))`                    | O(n) | builtin |
| 10 | Generator-based                            | O(n) | lazy eval |
| 11 | `zip` vs `reversed`                        | O(n) | readable |
| 12 | While-helpers variant                      | O(n) | same as V1 |
| 13 | `reduce`                                   | O(n) | functional |
| 14 | Index-mirror comprehension                 | O(n) | short |
| 15 | Slice-mirror                               | O(n) | same |
| 16 | Single-pass index                          | O(n) | explicit |
| 17 | Class-based                                | O(n) | OOP |
| 18 | Regex `re.sub`                             | O(n) | clever |
| 19 | ord arithmetic                             | O(n) | fastest |
| 20 | `zip(reversed)` with `all`                 | O(n) | clean |

---

## Recommended Interview Answer
**Solution 1** — clean, optimal:

```python
def is_palindrome(s):
    left, right = 0, len(s) - 1
    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
        if left < right:
            if s[left].lower() != s[right].lower():
                return False
            left += 1
            right -= 1
    return True
```

---

## Common Pitfalls
1. **Forgetting to lowercase** before comparing — case mismatches fail.
2. **Comparing without skipping non-alnum** — moves pointers wrong.
3. **Using `s[::-1]` on the original string** — wrong because punctuation
   breaks the mirror; always filter first.
4. **Off-by-one in `while left < right`** — should be `<`, not `<=`,
   because we want pairs (don't compare middle with itself).
5. **Unicode vs ASCII** — Python's `isalnum()` handles Unicode; for
   perf, use ASCII ord checks if input is guaranteed ASCII.
