# Coding Interviews — Capstone Exercises

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

Five graded problems to finish the course. Each is harder than the lessons. Treat them like a real interview: plan, code, test, and time-box yourself.

## Grading rubric (per problem)

- Correctness: passes all visible + hidden test cases.
- Complexity: optimal big-O.
- Code quality: clear variable names, comments on the tricky parts.
- Edge cases: empty input, single element, large input.

## Problems

1. **Median of Two Sorted Arrays** (Hard) — find the median of two sorted arrays in O(log(m+n)).
2. **Serialize/Deserialize a Binary Search Tree** (Hard) — encode a BST to a string and back.
3. **Word Search II** (Hard) — given a board and a list of words, return all words present.
4. **Trapping Rain Water II** (Hard) — 2D version of M04 lesson 29.
5. **Alien Dictionary with Cycle** (Hard) — extend M08 lesson 59 to handle empty-string edge cases.

## How to submit

1. Create `coding_interviews/exercises/<problem_name>.py` with the function `solve_X(input) -> output`.
2. Add tests under `coding_interviews/exercises/tests/test_<problem_name>.py`.
3. Run `python3 -m unittest discover -s coding_interviews/exercises`.
