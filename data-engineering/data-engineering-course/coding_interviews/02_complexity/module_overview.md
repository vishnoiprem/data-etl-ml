# Module 02: Time & Space Complexity

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

Big-O is the language of coding interviews. This module covers the four lessons you need to be fluent.

## Why this module

The interviewer scores your solution in two passes: correctness
first, complexity second. A correct O(n²) solution when an O(n)
or O(n log n) one is obvious will get you downleveled at L5+,
even if it produces the right answer. The reverse — an optimal
solution that doesn't actually solve the problem — also fails,
but at least it's a *different* failure mode.

Complexity is the second thing they look for because it tells
them whether you can reason about a problem at scale. A 100-element
array runs in O(n²) in 10ms; a 10M-element array runs in O(n²) in
3 hours. The interviewer wants to know that you can see the
second case before you write the code.

The four lessons here are the minimum vocabulary: Big-O notation,
space complexity, amortized analysis, and a one-page cheatsheet
for interviews. Read them in order. By the end you should be able
to look at any algorithm and state its time + space complexity
without running it.

## Lessons

| # | Title | Link |
| - | --- | --- |
| 07 | Big-O Notation | [07_big_o.md](design/07_big_o.md) |
| 08 | Space Complexity | [design/08_space.md](design/08_space.md) |
| 09 | Amortized Analysis | [design/09_amortized.md](design/09_amortized.md) |
| 10 | The Complexity Cheatsheet | [design/10_cheatsheet.md](design/10_cheatsheet.md) |
