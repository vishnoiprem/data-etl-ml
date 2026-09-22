# Largest Number — 10 Solutions + Interview Thinking

## Problem
Given a list of non-negative integers `nums`, rearrange them to form
the **largest possible number**. Return as a string.

## Interview Thinking (10 Steps)

### 1. Understand
"I need to reorder nums so the resulting concatenated string is the largest possible."

### 2. Observe — Key Insight
"Two numbers `a` and `b`: which comes first?
Whichever gives the larger `a+b` vs `b+a` (string concatenation)."

### 3. Pattern Recognition
"This is a **CUSTOM COMPARATOR** problem.
Sort nums with comparator `(a, b)` returning `+1` if `b+a > a+b`."

### 4. Edge Cases
- All zeros → return `"0"` (not `"000...0"`).
- Single element → return `str(element)`.
- Leading zeros in input → still treated as integers.

### 5. Tricky Detail
Standard sort uses natural ordering. For custom ordering, use
`functools.cmp_to_key` (Python) or pass a custom comparator (Java).

### 6. Algorithm
1. Convert each num to string.
2. Sort with custom comparator.
3. Concatenate.
4. If result starts with `'0'`, return `"0"` (all-zero edge case).

### 7. Why It Works (Proof Sketch)
**Transposition argument**: in any valid arrangement, swapping any
two adjacent elements that are "out of order" (i.e., `b+a > a+b` but
`b` comes before `a`) strictly improves the result. So the optimal
arrangement has no such pair — meaning it's exactly our sorted order.

### 8. Complexity
- **Time:** `O(n log n * k)` where `k` = max string length
- **Space:** `O(n)` for the string array

### 9. Code Structure
```python
from functools import cmp_to_key

def compare(a, b):
    if a + b > b + a: return -1  # a first
    if a + b < b + a: return 1   # b first
    return 0

result = "".join(sorted(map(str, nums), key=cmp_to_key(compare)))
return "0" if result[0] == "0" else result
```

### 10. Mental Tracing
`[3, 30, 34, 5, 9]`:
- Compare 3 & 30: "330" > "303" → 3 first.
- Compare 30 & 34: "3430" > "3034" → 34 first.
- ... → final: 9, 5, 34, 3, 30 → `"9534330"` ✓

---

## 10 Solutions Summary

| #  | Approach                          | Time            | Notes |
|----|-----------------------------------|-----------------|-------|
| 1  | `cmp_to_key` sort (CANONICAL)     | O(n log n)      | ★★★★★ |
| 2  | Sort by `x * 10` reverse          | O(n log n)      | works when nums ≤ 10 |
| 3  | Bubble sort with comparator       | O(n²)           | educational |
| 4  | Selection sort with comparator    | O(n²)           | educational |
| 5  | Sort by `x * 4` reverse           | O(n log n)      | works when nums ≤ 999 |
| 6  | Quicksort with comparator         | O(n log n) avg  | educational |
| 7  | Merge sort with comparator        | O(n log n)      | stable |
| 8  | Heap sort with comparator         | O(n log n)      | in-place possible |
| 9  | Insertion sort with comparator    | O(n²)           | educational |
| 10 | Sort by length-normalized key     | O(n log n)      | alternative encoding |

---

## Recommended Interview Answer
**Solution 1** (cmp_to_key): clean, idiomatic Python, optimal complexity.

```python
from functools import cmp_to_key

def largest_number(nums):
    s = list(map(str, nums))
    s.sort(key=cmp_to_key(lambda a, b: -1 if a+b > b+a else (1 if a+b < b+a else 0)))
    result = "".join(s)
    return "0" if result[0] == "0" else result
```

---

## Common Pitfalls
1. **Forgetting the all-zeros edge case** — `[0, 0]` should return `"0"`, not `"00"`.
2. **Using `cmp_to_key` incorrectly** — must return `-1`, `0`, or `1`, not boolean.
3. **Confusing `a+b > b+a` direction** — larger should come FIRST in sorted order.
4. **Off-by-one in custom comparison** — the comparator must be transitive.
