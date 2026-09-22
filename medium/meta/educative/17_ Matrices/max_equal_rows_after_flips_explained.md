# Flip Columns For Maximum Number of Equal Rows - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/flip-columns-for-maximum-number-of-equal-rows

## The Problem
```
Given an m x n binary matrix, return the maximum number of rows that
can be made equal (all 0s or all 1s) by flipping any number of columns.
Flipping a column inverts all values in that column.

Examples:
    matrix = [[0,1],[1,0]] -> 2
    matrix = [[0,1],[1,1]] -> 1

Constraints:
- 1 <= m, n <= 50
- matrix[i][j] is 0 or 1
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We can flip any subset of columns. Each flip inverts the column.
After flipping, we want the maximum number of rows that have all values
EQUAL (uniform within the row).

The "uniform" condition is per-row, NOT all rows must have the same value.
A row becomes uniform (all 0s or all 1s) iff it can be made uniform by flips.
```

### Step 2: The Trick
> "KEY INSIGHT: A row can be made UNIFORM by flips iff... well, actually
> any row can be made uniform by flipping every column where it has a
> 'wrong' value. So the question is: which rows can be made uniform by
> the SAME set of flips?
>
> Two rows can be made uniform by the SAME set of column flips iff
> they are IDENTICAL or COMPLEMENTARY (one is the bitwise NOT of the other).
>
> Why? Suppose rows A and B become uniform after the same flip mask:
> - After flips, position j of row A equals position j of row B.
> - That happens iff for each position j, EITHER (A[j]=B[j] and j not flipped)
>   OR (A[j]≠B[j] and j flipped).
> - This means: A and B agree wherever the mask is 0, disagree wherever
>   the mask is 1. So either A==B (mask=0) or A==complement(B) (mask=1).
>
> Generalization: For multiple rows, they can all be made uniform by the
> same flips iff they're all pairwise identical-or-complement, which means
> they all share a CANONICAL form = min(row, complement)."

### Step 3: The canonical form
> "For each row, compute its CANONICAL form: the lex-smaller of
> (row, complement(row)). Two rows share canonical form iff they are
> flippable together. So the answer = max group size."

### Step 4: Why canonical form works
> "Suppose rows A and B share canonical form C:
> - C = min(A, complement(A)) and C = min(B, complement(B)).
> - If A==B: they have the same canonical.
> - If A==complement(B): then complement(A)==B. So
>   min(B, complement(B)) = min(A, complement(A)) = C.
>
> Conversely, if min(A, complement(A)) == min(B, complement(B)):
> - If C == A and C == B: A == B.
> - If C == A and C == complement(B): A == complement(B).
> - If C == complement(A) and C == B: B == complement(A) -> A == complement(B).
> - If C == complement(A) and C == complement(B): A == B.
>
> So in all cases, A and B are identical or complementary."

### Step 5: Implementation
> "1. For each row, compute its canonical = min(row, complement).
> 2. Count occurrences of each canonical.
> 3. Return the max count."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the maximum number of rows that can be made uniform
> (all 0s or all 1s) by flipping any subset of columns."

**Key Insight:**
> "Two rows can be made uniform by the SAME flips iff they are IDENTICAL
> or COMPLEMENTARY. So I group rows by canonical form = min(row, complement)
> and return the largest group."

**Algorithm:**
> "1. For each row, compute canonical = min(row, complement).
> 2. Count occurrences using a Counter.
> 3. Return max count."

**Why identical-or-complement?**
> "After flips, two rows A, B are identical position-by-position.
> Position j agrees iff either j was not flipped (so A[j]==B[j])
> or j was flipped (so A[j]!=B[j]).
> So in all positions, A[j] and B[j] are either BOTH the same or BOTH
> different. This means A==B (all same) or A==complement(B) (all different)."

**Edge cases:**
- All rows identical: answer = m.
- No two rows identical or complementary: answer = 1.
- 1x1 matrix: answer = 1.
- Empty matrix: return 0.

**Complexity:**
- Time: O(m*n) for canonicalization + O(m) for counting.
- Space: O(m*n) for hash map.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Canonical form + Counter (BEST - Memorize!)
```python
def max_equal_rows_after_flips_1(matrix):
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0
    canonical = []
    for row in matrix:
        complement = [1 - v for v in row]
        row_t = tuple(row)
        comp_t = tuple(complement)
        canonical.append(min(row_t, comp_t))
    counter = Counter(canonical)
    return max(counter.values())
```

### Way 2: Verbose version (whiteboard-friendly)

### Way 3: String canonical form
- Use string representation for canonical form.

### Way 4: defaultdict-based hash map

### Way 5: First-column pivot
- If first element is 1, use complement. Gives canonical with leading 0.

### Way 6: Brute force subsets (Way 6 in code)

### Way 7: Bitmask representation

### Way 8: Pairwise compare

### Way 9: Frozenset representation

### Way 10: XOR with all-ones

### Way 11: Sort and group consecutive

### Way 12: dict.get counting

### Way 13: itertools-style

### Way 14: First row as reference

### Way 15: hash() builtin

### Way 16: NumPy vectorized

### Way 17: Class-based OOP

### Way 18: First-element canonical (compact)

### Way 19: Most concise one-liner

### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | O(mn)        |
| Small n (<=20)     | Way 6    | Brute OK     |
| Educational        | Way 14   | Intuitive    |
| Avoid hash         | Way 11   | Sort-based   |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Canonical + Counter (Way 1) | O(mn) | O(mn) | Best general |
| Brute (Way 6) | O(2^n * mn) | O(1) | Only for small n |
| Pairwise (Way 8) | O(m^2 * n) | O(1) | Works for small m |
| Sort (Way 11) | O(mn log mn) | O(mn) | No hash needed |

---

## Walkthrough Example

```
matrix = [[0,1],[1,0]]

Row 0 = [0,1], complement = [1,0]. canonical = min((0,1),(1,0)) = (0,1).
Row 1 = [1,0], complement = [0,1]. canonical = min((1,0),(0,1)) = (0,1).

Both have canonical (0,1). Count = 2.
Answer = 2. ✓

Verify: flip column 0 -> [[1,1],[0,0]]. Row 0 uniform (all 1s), Row 1 uniform (all 0s). 
Both are uniform! So 2 rows can be made uniform. ✓
```

```
matrix = [[0,0,1],[1,1,0],[0,0,1]]

Row 0 = [0,0,1], complement = [1,1,0]. canonical = min = (0,0,1).
Row 1 = [1,1,0], complement = [0,0,1]. canonical = min = (0,0,1).
Row 2 = [0,0,1], complement = [1,1,0]. canonical = min = (0,0,1).

All three have canonical (0,0,1). Count = 3.
Answer = 3. ✓
```

---

## Best Answer to Memorize

```python
def max_equal_rows_after_flips(matrix):
    if not matrix or not matrix[0]:
        return 0
    from collections import Counter
    canonicals = []
    for row in matrix:
        row_t = tuple(row)
        comp_t = tuple(1 - v for v in row)
        canonicals.append(min(row_t, comp_t))
    return max(Counter(canonicals).values())
```

**~10 lines. O(m*n) time. O(m*n) space. Interview-ready!**

---

## Key Insights

### Why identical-or-complement?
> "Flipping a column inverts all values in that column. Two rows A, B
> become identical after the same flips iff, for each column j:
> - Either j wasn't flipped and A[j]==B[j], OR
> - j was flipped and A[j]!=B[j].
> So in every position, A[j] and B[j] are the SAME or DIFFERENT in all
> positions consistently. Hence A==B or A==complement(B)."

### Why canonical form (min)?
> "min(row, complement) gives a unique representative for each
> identical-or-complement equivalence class. Group by canonical,
> max group = answer."

### Why first-element pivot also works?
> "If first element is 1, complement. Now every row starts with 0.
> Two rows with same first element 0 share canonical iff they are
> identical (since complement would start with 1).
> Group by tuple -> max group = answer."

---

## Test Cases

| matrix | Expected |
|--------|----------|
| [[0,1],[1,0]] | 2 |
| [[0,1],[1,1]] | 1 |
| [[1,1,1],[1,1,1],[1,1,1]] | 3 |
| [[0,0],[1,1],[1,1],[0,0]] | 4 |
| [[0,0,1],[1,1,0],[0,0,1]] | 3 |
| [[0,0,0],[1,1,0],[1,0,1]] | 1 |
| [[1,0,1]] | 1 |
| [] | 0 |

---

## Common Pitfalls

1. **Wrong flippability check**: The condition is "all positions same OR all positions different", not "each position either same or different".
2. **Forgetting complement**: Must consider both row and complement for canonical.
3. **Off-by-one in tuple comparison**: `min` on tuples compares lex order, which works for our case.
4. **Brute force complexity**: 2^n is infeasible for n > 25.

---

## Why This Problem Matters

> "Tests:
> 1. Pattern recognition: identical-or-complement.
> 2. Canonical form / hashing trick.
> 3. Equivalence classes.
> 4. Foundation for: matrix transformations, hashing patterns."

---

## Beyond This Problem: Related Patterns

### 1. Group Anagrams (LC 49)
```python
# Use sorted string as canonical.
# Group by canonical.
```

### 2. Valid Sudoku (LC 36)
```python
# Different problem but uses similar set-based deduplication.
```

### 3. Image Flipping
```python
# Geometric operation, different algorithm.
```

---

## Connection to Equivalence Class Problems

This problem uses the "canonical form" pattern:

```
1. Define an equivalence relation on rows (identical-or-complement).
2. Compute a CANONICAL representative for each class.
3. Group by canonical.
4. Return max group size.

The canonical form is min(row, complement). Two rows are in the same
class iff they have the same canonical.
```

This pattern works for many problems where:
- An equivalence relation is easy to compute.
- A canonical representative is easy to derive.
- We want the largest equivalence class.

---

## Quick Checklist

When given a similar problem:
- [ ] What's the equivalence relation? (identical? complement? similar?)
- [ ] Can I derive a canonical form?
- [ ] What data structure for counting? (Counter, dict, defaultdict)
- [ ] Do I need to handle edge cases (empty matrix, single row)?
- [ ] Is brute force (Way 6) feasible given constraints?

---

## Sources

- [LeetCode 1072 - Flip Columns For Maximum Number of Equal Rows](https://leetcode.com/problems/flip-columns-for-maximum-number-of-equal-rows/)
- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
