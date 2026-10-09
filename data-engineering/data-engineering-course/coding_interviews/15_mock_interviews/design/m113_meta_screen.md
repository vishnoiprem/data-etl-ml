# Mock 113 — E4/E5 Meta Screen (2 problems in 45 min)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

## Format

- 45 minutes, 2 problems, 1 interviewer.
- Problem 1: Easy (warm-up).
- Problem 2: Medium (the "real" signal).

## Problem 1 (Warm-up) — Fizz Buzz

Print the numbers 1..n. For multiples of 3 print "Fizz", for multiples of 5 "Buzz", for both "FizzBuzz".

Time: O(n), Space: O(1) (excluding output).

## Problem 2 (Real) — Valid Parentheses with Wildcards

Given a string `s` containing `(`, `)`, `*`, determine if the string is valid. A `*` can be treated as `(`, `)`, or empty.

Time: O(n), Space: O(n).

## Grading rubric

- **Strong Hire**: both problems clean, optimal complexity, edge cases covered.
- **Hire**: both problems correct, may have minor cleanup on problem 2.
- **Lean Hire**: problem 1 correct, problem 2 partial (e.g. handles `*` as one option but not all three).
- **No Hire**: struggles on problem 1 or misses the trick on `*`.
