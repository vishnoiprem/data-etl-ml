# Kth Smallest Number in Multiplication Table - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/kth-smallest-number-in-multiplication-table

## The Problem
```
Given an m x n multiplication table where mat[i][j] = i * j (1-indexed),
find the kth smallest number in the table.

Examples:
    m=3, n=3, k=5:
    Table:
        1 2 3
        2 4 6
        3 6 9
    Sorted: 1, 2, 2, 3, 3, 4, 6, 6, 9
    -> 5th smallest = 3

    m=4, n=5, k=8:
    1  2  3  4  5
    2  4  6  8  10
    3  6  9  12 15
    4  8  12 16 20
    -> 8th smallest = 4

Constraints:
- 1 <= m, n <= 30000
- 1 <= k <= m * n
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We have an m x n multiplication table. We want the kth smallest.
Naive: build the table and sort. O(mn log mn) time, O(mn) space.
For m, n up to 30000, this is 9 * 10^8 elements - too much!
```

### Step 2: The Trick
> "We don't need to sort. Instead, BINARY SEARCH on the VALUE:
>
> For a candidate value x, count how many elements in the table are <= x.
> Find the smallest x with count(x) >= k.
>
> COUNT FUNCTION:
> For each row i, the values are i, 2i, 3i, ..., ni.
> Number of values <= x in row i = min(x // i, n).
> Total = sum over all rows."

### Step 3: Why binary search works
> "The count function is MONOTONICALLY INCREASING:
> count(x) >= count(y) whenever x >= y.
> So we can binary search for the smallest x with count(x) >= k."

### Step 4: Optimization
> "If m > n, SWAP them. Then iterate over the smaller dimension
> for counting. Same complexity but smaller constant."

### Step 5: Why this is fast
> "Each count call is O(m) (or O(min(m,n)) after swap).
> Binary search does O(log(m*n)) iterations.
> Total: O(m * log(m*n)) time."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the kth smallest number in an m x n multiplication table.
> Naive sort is O(mn log mn) which is too slow for m, n up to 30000."

**Key Insight:**
> "Binary search on the VALUE. For each candidate x, count how many table
> entries are <= x. Find the smallest x with count >= k.
>
> In row i, values are i, 2i, 3i, ..., ni.
> Count in row i = min(x // i, n)."

**Algorithm:**
> "1. lo = 1, hi = m*n.
> 2. While lo < hi:
>    a. mid = (lo + hi) // 2.
>    b. count = sum(min(mid // i, n) for i in 1..m).
>    c. If count >= k: answer <= mid, hi = mid.
>    d. Else: lo = mid + 1.
> 3. Return lo."

**Why monotonic counting works:**
> "As x increases, count(x) never decreases. So binary search
> finds the smallest x with count(x) >= k."

**Edge cases:**
- k = 1: return 1.
- k = m*n: return m*n.
- m or n = 1: linear sequence, easy.

**Complexity:**
- Time: O((m+n) * log(m*n)) - binary search with O(m) counting per step.
  (Actually O(min(m,n) * log(m*n)) if we swap dimensions.)
- Space: O(1).

---

## The 20 Implementations (Simple to Complex)

### Way 1: Binary search on value (BEST - Memorize!)
```python
def findKthNumber(m, n, k):
    def count_leq(x):
        return sum(min(x // i, n) for i in range(1, m + 1))
    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if count_leq(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

### Way 2-11: Variations
- Verbose naming
- Swap dimensions optimization
- Brute force (for verification)
- Heap-based (alternative)
- Edge case handling
- Explicit vs sum-based counting

### Way 12: Numpy (for small inputs)
- Vectorized table generation, sorting.

### Way 13: Heap approach
- Pop k times from min-heap of (value, row, col).

### Way 14-16: Different binary search styles

### Way 17: Class-based OOP

### Way 18-20: Final variations

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Best general     | Way 1    | O((m+n)logn) |
| Small input      | Way 11   | Brute is OK  |
| Don't swap dims  | Way 1    | Standard     |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Binary search (Way 1) | O((m+n) log mn) | O(1) | Best general |
| With swap (Way 3) | O(min(m,n) log mn) | O(1) | Better constant |
| Heap (Way 5) | O(k log m) | O(m) | When k is small |
| Brute (Way 11) | O(mn log mn) | O(mn) | Small input only |

---

## Walkthrough Example

```
m=4, n=5, k=8

Table:
    1  2  3  4  5
    2  4  6  8  10
    3  6  9  12 15
    4  8  12 16 20

Sorted: 1, 2, 2, 3, 3, 4, 4, 4, 5, 6, 6, 8, 8, 9, 10, 12, 12, 15, 16, 20
                1  2  3  4  5  6  7  8  9 ...
8th = 4

Binary search on value:
lo=1, hi=20

mid=10: count(10) = min(10//1,5)+min(10//2,5)+min(10//3,5)+min(10//4,5)
      = 5 + 5 + 3 + 2 = 15
15 >= 8, so hi=10.

mid=5: count(5) = 5 + min(5//2,5) + min(5//3,5) + min(5//4,5)
     = 5 + 2 + 1 + 1 = 9
9 >= 8, so hi=5.

mid=3: count(3) = 3 + 1 + 1 + 0 = 5
5 < 8, so lo=4.

mid=4: count(4) = 4 + 2 + 1 + 1 = 8
8 >= 8, so hi=4.

lo=hi=4. Return 4. ✓
```

---

## Best Answer to Memorize

```python
def findKthNumber(m, n, k):
    if m > n:
        m, n = n, m

    def count_leq(x):
        return sum(min(x // i, n) for i in range(1, m + 1))

    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if count_leq(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

**~12 lines. O(min(m,n) log(mn)) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why binary search on VALUE (not index)?
> "The answer is a value in [1, m*n]. We can't binary search on index
> because we don't know which value to look for. But count(x) is monotonic,
> so we can binary search for smallest x with count(x) >= k."

### Why does counting work?
> "Row i = i, 2i, 3i, ..., ni. The kth value in this row is k*i.
> Values <= x: x // i values (capped at n).
> So count in row i = min(x // i, n)."

### Why swap dimensions?
> "If m > n, swap so we iterate over the smaller dimension.
> Same asymptotic complexity but smaller constant."

### Why is heap O(k log m)?
> "Heap stores O(m) entries (one per row). Pop k times: O(k log m).
> Binary search is faster when k is large."

---

## Test Cases

| (m, n, k) | Expected |
|-----------|----------|
| (3, 3, 5) | 3 |
| (4, 5, 8) | 4 |
| (2, 3, 6) | 6 |
| (1, 1, 1) | 1 |
| (1, 5, 3) | 3 |
| (3, 3, 1) | 1 |
| (3, 3, 9) | 9 |

---

## Common Pitfalls

1. **Sorting the whole table**: O(mn log mn) is too slow for large m, n.
2. **Wrong counting**: For row i, count is min(x // i, n), not x // i.
3. **Off-by-one in binary search**: The invariant is lo <= answer <= hi.
4. **Not swapping dimensions**: Optimization missed.
5. **Heap duplicates**: Need visited set to avoid duplicates.

---

## Why This Problem Matters

> "Tests:
> 1. Binary search on VALUE (not index).
> 2. Monotonic function property.
> 3. Counting under constraints.
> 4. Optimization (swap dimensions).
> 5. Foundation for: Kth Smallest in Matrix, Order Statistics."

---

## Beyond This Problem: Related Patterns

### 1. Kth Smallest Element in a Sorted Matrix (LC 378)
```python
# Similar binary search on value approach.
# For each row, count values <= x.
```

### 2. Find K Pairs with Smallest Sums (LC 373)
```python
# Heap-based, but different counting.
```

### 3. Search a 2D Matrix II (LC 240)
```python
# Sorted matrix, search from top-right or bottom-left.
```

---

## Connection to Top K Problems

This is a "Top K via Binary Search" pattern:

```
1. Define monotonic predicate P(x) = "at least k values are <= x".
2. Binary search for smallest x with P(x) = True.
3. P is monotonic, so binary search works.
```

This pattern works for many problems where:
- Direct sorting is too expensive.
- The answer is a value, not an index.
- A counting function is easy to compute.

---

## Quick Checklist

When given a similar problem:
- [ ] Is the answer a value or an index?
- [ ] Can I define a monotonic counting function?
- [ ] What are the bounds on the answer? (low, high)
- [ ] Can I optimize by swapping dimensions?
- [ ] Is binary search faster than heap for my constraints?

---

## Sources

- [LeetCode 668 - Kth Smallest Number in Multiplication Table](https://leetcode.com/problems/kth-smallest-number-in-multiplication-table/)
- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
