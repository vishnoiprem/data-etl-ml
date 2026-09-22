# Largest Odd Number in String — 10 Solutions + Interview Thinking

## Problem
Given a string `num` representing a large integer, find the **largest odd-valued integer**
that can be formed as a non-empty substring of `num`. Return the result as a string;
return `""` if no odd integer exists.

Reference: Educative Grokking — "Largest Odd Number in String".

---

## Interview Thinking (10 Steps)

### 1. Understand
"I have a string of digits. Find the largest odd integer that appears as a
contiguous substring. An integer is odd iff its **last digit is odd**, so
parity depends only on the rightmost digit."

### 2. Observe — Key Insight
**Largest odd integer = longest prefix ending at the rightmost odd digit.**

Why? An odd substring must end at an odd digit. Among all odd substrings,
the one that ends at the **rightmost** odd digit is the longest, hence
the largest (longer length = larger value, given the same prefix from
index 0).

### 3. Pattern Recognition
**Greedy with right-to-left scan.** Walk backwards; the first odd digit
you encounter marks the end of the answer.

### 4. Edge Cases
- `num` is empty → return `""` (but constraints say length ≥ 1).
- Single odd digit → return the digit.
- Single even digit → return `""`.
- All digits even → return `""`.
- Last digit is odd → return the entire string.

### 5. Tricky Detail
**No need to handle leading zeros.** Per constraints, the input has no
leading zeros, so the prefix `num[:i+1]` inherits that property.

### 6. Algorithm
```
for i from len(num)-1 down to 0:
    if num[i] is odd:
        return num[:i+1]
return ""
```

### 7. Why Greedy Works
**Exchange argument**: Suppose the answer should end at index `j`, but
there's an odd digit at index `i > j`. Then `num[:i+1]` is also odd (its
last digit `num[i]` is odd) and is longer than `num[:j+1]`. Since both
have the same prefix `num[:j]`, the longer one is larger in value.
Hence the optimal ending index is the **rightmost** odd digit.

### 8. Complexity
- **Time:** `O(n)` — single backward scan.
- **Space:** `O(1)` extra (output is `O(n)`).

### 9. Code Structure
```python
def largest_odd_number(num):
    ODD = {"1", "3", "5", "7", "9"}
    for i in range(len(num) - 1, -1, -1):
        if num[i] in ODD:
            return num[:i + 1]
    return ""
```

### 10. Mental Trace
`num = "1234"`:
- i=3: '4' is even.
- i=2: '3' is odd → return `"123"`. ✓

`num = "13579"`:
- i=4: '9' is odd → return `"13579"`. ✓

`num = "24680"`:
- i=4: '0' even.
- i=3: '8' even.
- i=2: '6' even.
- i=1: '4' even.
- i=0: '2' even.
- return `""`. ✓

`num = "2047"`:
- i=3: '7' odd → return `"2047"`. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time   | Notes |
|----|---------------------------------------|--------|-------|
| 1  | Right-to-left scan with `int() % 2`   | O(n)   | ★★★★★ |
| 2  | Set membership check                  | O(n)   | clean |
| 3  | `range()` from right (same as V2)     | O(n)   | minimal |
| 4  | `rfind`-style search                  | O(n)   | compact |
| 5  | `str.translate` mask + scan           | O(n)   | clever |
| 6  | Numpy vectorized                      | O(n)   | uses `np.where` |
| 7  | `re.finditer` on odd digits           | O(n)   | regex |
| 8  | Strip trailing evens                  | O(n)   | alternative |
| 9  | Helper function for odd check         | O(n)   | readable |
| 10 | Forward scan + track last odd index   | O(n)   | single pass |

---

## Recommended Interview Answer
**Solution 1** (or its tiny variant, Solution 2). Clean, optimal, idiomatic:

```python
def largest_odd_number(num):
    ODD = {"1", "3", "5", "7", "9"}
    for i in range(len(num) - 1, -1, -1):
        if num[i] in ODD:
            return num[:i + 1]
    return ""
```

---

## Common Pitfalls
1. **Trying to find the largest odd *value* numerically** — the string
   may have 10⁴ digits, far exceeding integer range. Stay in string-land.
2. **Returning `num[:i]` (off-by-one)** — the rightmost odd digit is
   *included*, so the slice is `[:i+1]`, not `[:i]`.
3. **Trying to handle leading zeros** — the constraint guarantees none,
   so don't strip them (or you might produce a different string).
4. **Scanning left-to-right** — wastes time finding the leftmost odd
   digit, which won't be optimal. Always go right-to-left.
5. **Computing parity with `int(num[i]) % 2`** — works, but converting
   each digit to an int is slower than a set lookup `"num[i] in ODD"`.
