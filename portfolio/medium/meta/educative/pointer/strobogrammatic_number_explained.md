# Strobogrammatic Number — 10 Solutions + Interview Thinking

## Problem
Determine whether a string `num` represents a strobogrammatic number —
one that appears the same when rotated 180 degrees.

Valid rotations:
- `0 ↔ 0`
- `1 ↔ 1`
- `6 ↔ 9`
- `8 ↔ 8`
- `9 ↔ 6`

All other digits (`2`, `3`, `4`, `5`, `7`) are invalid.

Reference: LeetCode #246 / Educative Grokking — "Strobogrammatic Number".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Determine if `num` looks the same when rotated 180°."

### 2. Key Insight
**Two-pointer from both ends.** For each pair `(i, j)`, the digit at `i` must rotate to the digit at `j`. Use a rotation map.

### 3. Pattern Recognition
Convergent two-pointer with pairwise mapping check.

### 4. Edge Cases
- Single digit `0`, `1`, `8` → True (self-mapping).
- Single digit `6`, `9` → False (no partner to pair with).
- Other single digits → False.
- Empty string → True (vacuously strobogrammatic).
- Odd length: middle char must be self-mapping.
- Even length: every pair must match.

### 5. Tricky Detail
**Check both directions:** `num[i]` must be in the valid map AND `MAP[num[i]] == num[j]`. Don't just check the latter — digits like `2`, `3`, `4`, `5`, `7` would silently fail the first check.

### 6. Algorithm
```
MAP = {'0':'0', '1':'1', '6':'9', '8':'8', '9':'6'}
i, j = 0, n - 1
while i <= j:
    if num[i] not in MAP or MAP[num[i]] != num[j]:
        return False
    i += 1; j -= 1
return True
```

### 7. Why It Works
Each position has at most one valid partner. The map enforces the rotation
rules. Two-pointer ensures each pair is checked exactly once. O(n) total.

### 8. Complexity
- Time: O(n).
- Space: O(1) extra (or O(5) for the map).

### 9. Code Structure
```python
def isStrobogrammatic(num):
    MAP = {'0':'0', '1':'1', '6':'9', '8':'8', '9':'6'}
    i, j = 0, len(num) - 1
    while i <= j:
        if num[i] not in MAP or MAP[num[i]] != num[j]:
            return False
        i += 1; j -= 1
    return True
```

### 10. Mental Trace
`"69"`: i=0, j=1. MAP['6']='9', num[1]='9'. ✓ → True.
`"962"`: i=0, j=2. MAP['9']='6', num[2]='2'. '6' != '2'. ✗ → False.
`"906"`: i=0, j=2. MAP['9']='6', num[2]='6'. ✓ i=1, j=1. MAP['0']='0', num[1]='0'. ✓ → True.
`"101"`: i=0, j=2. MAP['1']='1', num[2]='1'. ✓ i=1, j=1. MAP['0']='0', num[1]='0'. ✓ → True.

---

## 10 Solutions Summary

| #  | Approach                              | Time | Notes |
|----|---------------------------------------|------|-------|
| 1  | Canonical two-pointer with map (BEST) | O(n) | clean |
| 2  | Valid set + pair check                | O(n) | explicit valid |
| 3  | Mirror the string, compare            | O(n) | alternative |
| 4  | Build rotated, compare                | O(n) | same idea |
| 5  | Brute force — generate all            | O(5^(n/2)) | educational |
| 6  | Explicit while with middle check      | O(n) | manual |
| 7  | `str.translate`                       | O(n) | clever |
| 8  | `all()` with zip                      | O(n) | pythonic |
| 9  | Recursive                             | O(n) | educational |
| 10 | `reduce` functional                   | O(n) | FP style |

---

## Recommended Interview Answer
**Solution 1** — clean, optimal, idiomatic:

```python
def isStrobogrammatic(num):
    MAP = {'0':'0', '1':'1', '6':'9', '8':'8', '9':'6'}
    i, j = 0, len(num) - 1
    while i <= j:
        if num[i] not in MAP or MAP[num[i]] != num[j]:
            return False
        i += 1; j -= 1
    return True
```

---

## Common Pitfalls
1. **Forgetting to check that `num[i]` is in the map** — digits like `2`, `3`, `4`, `5`, `7` should fail, but if you only check the pair match, you'll get a `KeyError`.
2. **Confusing with plain palindrome** — `"919"` is a palindrome but NOT strobogrammatic (9 maps to 6, not 1).
3. **Single digit `6` or `9`** — these aren't self-mapping; they need a partner.
4. **Empty string handling** — vacuously True.
