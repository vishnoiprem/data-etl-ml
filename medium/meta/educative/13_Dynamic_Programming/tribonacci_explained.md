# N-th Tribonacci Number

## Problem
Compute the n-th Tribonacci number:
```
T_0 = 0, T_1 = 1, T_2 = 1
T_n = T_{n-1} + T_{n-2} + T_{n-3}  for n >= 3
```

## Approach: Iterative DP with O(1) Space

### Recurrence
At each step we only need the **previous three** Tribonacci values:
```
T_n = T_{n-1} + T_{n-2} + T_{n-3}
```

### Algorithm
Maintain a rolling window of the last three values:
```python
a, b, c = 0, 1, 1   # T_0, T_1, T_2
for _ in range(3, n + 1):
    a, b, c = b, c, a + b + c
return c
```

After each iteration, `(a, b, c)` rolls forward to `(T_{n-3}, T_{n-2}, T_{n-1})`.

### Edge Cases
- `n = 0` → 0
- `n = 1` or `n = 2` → 1

## Walkthrough: First 11 values

```
n : 0  1  2  3  4  5  6  7  8  9  10
T : 0  1  1  2  4  7 13 24 44 81 149
```

For `n = 4`: `T_4 = T_3 + T_2 + T_1 = 2 + 1 + 1 = 4` ✓

## Complexity
- **Time:** `O(n)`
- **Space:** `O(1)` (only three variables)

## Variants
- **Naive recursion** with memoization: same `O(n)` time, `O(n)` space
- **Matrix exponentiation:** `O(log n)` time using matrix power
  (overkill for `n <= 37`, useful when `n` is much larger)
