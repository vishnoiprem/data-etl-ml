# Convert 1D Array Into 2D Array - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/convert-1d-array-into-2d-array

## The Problem
```
Given a 1D integer array `original` and two integers `m` and `n`,
reshape the array into a 2D array with m rows and n columns while
preserving the order of elements.

If len(original) != m * n, return an empty array.

Examples:
    [1,2,3,4], m=2, n=2 -> [[1,2],[3,4]]
    [1,2,3], m=1, n=3 -> [[1,2,3]]
    [1,2,3], m=3, n=1 -> [[1],[2],[3]]
    [1,2,3], m=2, n=2 -> []  (3 != 4)

Constraints:
- 1 <= original.length <= 10^3
- 1 <= original[i] <= 10^3
- 1 <= m, n <= 33
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We have a 1D array. We want to "fold" it into 2D shape (m x n).
The first n elements become row 0, the next n become row 1, etc.
```

### Step 2: The Trick
> "KEY INSIGHT: Reshape is possible iff len(original) == m * n.
> If not, return empty. Otherwise, slice the array into n-sized chunks.
>
> For row i, the slice is original[i*n : (i+1)*n]."

### Step 3: Why slicing works
> "Position (i, j) in the 2D array corresponds to position (i*n + j)
> in the 1D array. So row i contains indices [i*n, i*n+1, ..., i*n+n-1]."

### Step 4: Algorithm
> "1. If len(original) != m * n: return [].
> 2. Otherwise, build the 2D array by slicing."

### Step 5: Edge cases
> "- Empty result possible: len != m * n.
> - 1x1 result: just [[original[0]]].
> - Single row (m=1): one chunk.
> - Single column (n=1): m chunks of size 1."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to reshape a 1D array into a 2D array with m rows and n columns."

**Key Insight:**
> "Check if reshape is possible: len(original) must equal m * n.
> If not, return empty. Otherwise, slice into chunks of size n."

**Algorithm:**
> "1. If len(original) != m * n: return [].
> 2. For each row i in [0, m):
>    result.append(original[i*n : (i+1)*n])
> 3. Return result."

**Why this works:**
> "Position (i, j) in 2D maps to position (i*n + j) in 1D.
> So row i = original[i*n : (i+1)*n]."

**Edge cases:**
- Empty result: len != m * n.
- 1x1: [[original[0]]].
- Single row (m=1): one chunk.
- Single column (n=1): m chunks of size 1.

**Complexity:**
- Time:  O(m*n) - linear in size.
- Space: O(m*n) - for the result.

---

## The 20 Implementations (Simple to Complex)

### Way 1: List comprehension slicing (BEST - Memorize!)
```python
def construct_2d_array_1(original, m, n):
    if len(original) != m * n:
        return []
    return [original[i * n:(i + 1) * n] for i in range(m)]
```

### Way 2: Build row by row with explicit index
### Way 3: enumerate with chunks
### Way 4: zip group
### Way 5: slice with step
### Way 6: itertools.islice
### Way 7: numpy reshape
### Way 8: pre-allocate matrix
### Way 9: operator.itemgetter
### Way 10: zip idiom
### Way 11: Class-based
### Way 12: Functional map
### Way 13: Lambda
### Way 14: Recursive
### Way 15: deque
### Way 16: Generator
### Way 17: Range index calculation
### Way 18: enumerate on rows
### Way 19: One-liner
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | Clean slice  |
| numpy available    | Way 7    | Built-in     |
| Functional         | Way 12   | map+zip      |
| Recursive          | Way 14   | Education    |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| List comp (Way 1) | O(m*n) | O(m*n) | Best general |
| numpy (Way 7) | O(m*n) | O(m*n) | Vectorized |
| Recursive (Way 14) | O(m*n) | O(m*n) | Stack overhead |
| deque (Way 15) | O(m*n) | O(m*n) | popleft O(n) |

---

## Walkthrough Example

```
original = [1, 2, 3, 4, 5, 6], m=2, n=3

Row 0: indices 0-2 -> [1, 2, 3]
Row 1: indices 3-5 -> [4, 5, 6]

Result: [[1, 2, 3], [4, 5, 6]]
```

```
original = [1, 2, 3, 4, 5, 6], m=3, n=2

Row 0: indices 0-1 -> [1, 2]
Row 1: indices 2-3 -> [3, 4]
Row 2: indices 4-5 -> [5, 6]

Result: [[1, 2], [3, 4], [5, 6]]
```

```
original = [1, 2, 3], m=2, n=2

len(original) = 3 != m * n = 4
Return: []
```

---

## Best Answer to Memorize

```python
def construct_2d_array(original, m, n):
    if len(original) != m * n:
        return []
    return [original[i * n:(i + 1) * n] for i in range(m)]
```

**~3 lines. O(m*n) time. O(m*n) space. Interview-ready!**

---

## Key Insights

### Why check len(original) == m * n?
> "Total elements must match. If they don't, reshape is impossible.
> Return empty to signal the impossibility."

### Why slice with i*n : (i+1)*n?
> "Row i contains elements at 1D positions i*n, i*n+1, ..., i*n+n-1.
> That's exactly the slice original[i*n : (i+1)*n]."

### Why list comprehension?
> "Cleanest, most Pythonic. Each iteration produces one row.
> The slicing is O(n) per row, total O(m*n)."

### Why is this "row-major" reshaping?
> "Elements fill the array row by row. This is the standard convention
> in C, Python (numpy default), Java, etc."

---

## Test Cases

| original | m | n | Expected |
|----------|---|---|----------|
| [1,2,3,4] | 2 | 2 | [[1,2],[3,4]] |
| [1,2,3] | 1 | 3 | [[1,2,3]] |
| [1,2,3] | 3 | 1 | [[1],[2],[3]] |
| [1,2,3] | 2 | 2 | [] |
| [5] | 1 | 1 | [[5]] |
| [1,2,3,4,5,6] | 2 | 3 | [[1,2,3],[4,5,6]] |
| [1,2,3,4,5,6] | 3 | 2 | [[1,2],[3,4],[5,6]] |
| [1,2,3,4] | 1 | 4 | [[1,2,3,4]] |
| [1,2,3] | 5 | 5 | [] |

---

## Common Pitfalls

1. **Skipping the size check**: Always verify len(original) == m * n.
2. **Wrong index formula**: Use i*n + j for position (i, j), not i*m + j.
3. **Confusing m and n**: m is rows, n is columns. Slice size is n.
4. **Modifying original**: Should create new 2D list, not mutate input.
5. **Numpy reshape side effects**: numpy shares memory; convert to list first.

---

## Why This Problem Matters

> "Tests:
> 1. Index calculation (i*n + j).
> 2. Slice operations.
> 3. Edge case handling (size mismatch).
> 4. Foundation for: image processing, matrix operations, data reshaping."

---

## Beyond This Problem: Related Patterns

### 1. Reshape Matrix (LC 566)
```python
# Same concept: 1D reshape to 2D.
# Also need to check size match.
```

### 2. Matrix Reshape in NumPy
```python
import numpy as np
arr = np.arange(12).reshape(3, 4)  # 0 to 11 in 3x4
```

### 3. Flatten 2D to 1D
```python
# Reverse operation.
flat = [v for row in matrix for v in row]
```

### 4. Transpose Matrix
```python
# Different: swap rows and columns.
```

---

## Connection to Array Reshaping

This problem uses the "slice and chunk" pattern:

```
1. Verify size: total elements match.
2. Chunk the source: divide into n-sized pieces.
3. Build the target: each chunk becomes a row.
```

This pattern works for many problems:
- 1D to 2D reshape (this problem).
- 1D to N-D reshape (generalized).
- File to matrix (chunked reading).
- Stream to batched input.

---

## Quick Checklist

When given a similar problem:
- [ ] Is total size preserved? (yes here)
- [ ] What's the chunk size? (n here)
- [ ] What's the order? (row-major here)
- [ ] How to handle size mismatch? (return empty here)
- [ ] Slice vs allocate? (slice is faster)

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 2022 - Convert 1D Array Into 2D Array](https://leetcode.com/problems/convert-1d-array-into-2d-array/)
