# Different Ways to Add Parentheses

## Problem
Given a valid arithmetic expression string consisting of non-negative integers
and the binary operators `+`, `-`, `*`, return all possible results from
computing the expression in every possible parenthesization.

## Approach: Top-Down DP with Memoization

Each operator is a candidate pivot point. We can recursively split the
expression at every operator into a **left subexpression** and a
**right subexpression**, compute all possible results for each side
independently, then combine pairs using the operator.

To avoid recomputing the same subexpression multiple times, we cache
results in a dictionary keyed by the subexpression string.

## Algorithm
1. Define a recursive helper `compute(expr)`.
2. If `expr` is cached, return it.
3. Iterate through every character of `expr`:
   - If the character is an operator `+`, `-`, or `*`:
     - Recursively compute `left_results = compute(expr[:i])`
     - Recursively compute `right_results = compute(expr[i+1:])`
     - For each pair `(l, r)`, apply the operator and append.
4. **Base case:** If no operator was found, `expr` is just a number.
   Return `[int(expr)]`.
5. Cache and return the results.

## Walkthrough: `"2-1-1"`

- At operator index 1 (`-`):
  - left = `compute("2")` = `[2]`
  - right = `compute("1-1")`:
    - At operator index 1 (`-`):
      - left = `compute("1")` = `[1]`
      - right = `compute("1")` = `[1]`
      - results = `[1 - 1] = [0]`
    - **results: [0]**
  - combined = `[2 - 0] = [2]`

- At operator index 3 (`-`):
  - left = `compute("2-1")` = `[1]`  (similar reasoning)
  - right = `compute("1")` = `[1]`
  - combined = `[1 - 1] = [0]`

**Final result:** `[2, 0]`

## Correctness
The algorithm enumerates **every** valid parenthesization because each
operator defines a possible point where the outermost pair of parentheses
could be placed, and the recursion handles subexpressions identically.

## Complexity
- **Time:** `O(2^N)` where `N` is the number of operators, due to the
  exponential number of parenthesizations, but memoization avoids recomputation
  of identical subexpressions.
- **Space:** `O(2^N)` to store all results, plus `O(N^2)` for the memo cache.

## Edge Cases
- A single number (no operators) → returns `[int(expression)]`.
- Duplicate results are allowed (per problem statement).
