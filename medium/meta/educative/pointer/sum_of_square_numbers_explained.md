# Sum of Square Numbers — 10 Solutions + Interview Thinking

## Problem
Given a non-negative integer `c`, determine whether there exist non-negative
integers `a` and `b` such that `a^2 + b^2 == c`.

Reference: LeetCode #633 / Educative Grokking — "Sum of Square Numbers".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Find `a, b >= 0` such that `a^2 + b^2 == c`."

### 2. Key Insight
**Two-pointer on `[0, isqrt(c)]`.** `a` starts at 0, `b` starts at `floor(sqrt(c))`. Adjust based on whether the sum is less than or greater than `c`.

### 3. Pattern Recognition
Convergent two-pointer. Each pointer movement adjusts the sum monotonically.

### 4. Edge Cases
- `c == 0` → `0^2 + 0^2 == 0` → True.
- `c == 1` → `0^2 + 1^2 == 1` → True.
- Perfect square → True (b = 0 case).
- c is large; use `math.isqrt` to avoid float precision issues.

### 5. Tricky Detail
**Use `math.isqrt(c)` (Python 3.8+)**, not `int(math.sqrt(c))`. The latter can be off by one for very large `c` due to floating-point precision.

### 6. Algorithm
```
from math import isqrt
a, b = 0, isqrt(c)
while a <= b:
    s = a*a + b*b
    if s == c: return True
    if s < c: a += 1
    else: b -= 1
return False
```

### 7. Why It Works
`a*a` is monotonically increasing in `a`; `b*b` is monotonically decreasing in `b` (as `b` shrinks). The sum `a^2 + b^2` adjusts monotonically:
- Increase `a` → sum increases.
- Decrease `b` → sum decreases.

Hence the two-pointer converges in O(sqrt(c)) steps.

### 8. Complexity
- Time: O(sqrt(c)).
- Space: O(1).

### 9. Code Structure
```python
def sum_sq(c):
    a, b = 0, math.isqrt(c)
    while a <= b:
        s = a*a + b*b
        if s == c: return True
        if s < c: a += 1
        else: b -= 1
    return False
```

### 10. Mental Trace
`c = 5`, `isqrt(5) = 2`:
- a=0, b=2: 0+4=4 < 5 → a=1.
- a=1, b=2: 1+4=5 == 5 → **True** ✓.

`c = 3`:
- a=0, b=1: 0+1=1 < 3 → a=1.
- a=1, b=1: 1+1=2 < 3 → a=2.
- Loop exits (a > b) → **False** ✓.

---

## 10 Solutions Summary

| #  | Approach                              | Time        | Space |
|----|---------------------------------------|-------------|-------|
| 1  | Two-pointer + isqrt (BEST)            | O(√c)       | O(1)  |
| 2  | Two-pointer + sqrt (float)            | O(√c)       | O(1)  |
| 3  | Brute double loop                     | O(c)        | O(1)  |
| 4  | Brute a only                          | O(√c)       | O(1)  |
| 5  | Binary search                         | O(√c · log c)| O(1) |
| 6  | Set lookup                            | O(√c)       | O(√c) |
| 7  | Fermat's sum-of-two-squares theorem   | O(√c)       | O(1)  |
| 8  | Recursive two-pointer                 | O(√c)       | O(√c) |
| 9  | Precomputed sorted squares            | O(√c · log √c)| O(√c)|
| 10 | Iterative deepening                   | O(√c)       | O(1)  |

---

## Recommended Interview Answer
**Solution 1** — clean, O(√c), no float issues:

```python
def judgeSquareSum(c):
    a, b = 0, math.isqrt(c)
    while a <= b:
        s = a*a + b*b
        if s == c: return True
        if s < c: a += 1
        else: b -= 1
    return False
```

---

## Common Pitfalls
1. **Using `int(math.sqrt(c))`** — float precision can be wrong for large c; use `math.isqrt`.
2. **Forgetting to handle c == 0** — `0^2 + 0^2 = 0` should be True.
3. **Setting the wrong initial `b`** — `b` should be `isqrt(c)`, not `c`.
4. **Not terminating** — the loop is `while a <= b`, not `while a < b` (the equal case is necessary).
