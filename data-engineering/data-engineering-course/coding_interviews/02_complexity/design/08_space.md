# 08 — Space Complexity

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

Space complexity counts the **extra** memory the algorithm uses (not the input itself).

## Common cases

- O(1): a few pointers/scalars, in-place swaps
- O(log n): recursion depth on a balanced tree / binary search
- O(n): a hashmap, a new array, a visited set
- O(n²): a 2D matrix of size n×n

## Stack space counts

If you recurse with depth n, that's O(n) space even if you only use a constant amount of memory per frame.

## Trade-offs

Sometimes trading more space for less time is the right call. A hash table lookup is O(n) space but O(1) per query — a fair price.
