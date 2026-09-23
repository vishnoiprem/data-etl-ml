"""
GENERATE PARENTHESES — LeetCode 22
Given `n` pairs of parentheses, write a function that generates all
well-formed combinations of parentheses.

Example
-------
n = 3
Answer: ["((()))","(()())","(())()","()(())","()()()"]   (Catalan(3) = 5)

Key idea: PRUNE INVALID PATHS EARLY
----------------------------------
At any prefix, we are building a valid string iff:
  • Number of `(` used so far ≤ n
  • Number of `)` used so far ≤ number of `(` used
These two invariants cut the search tree from 2^(2n) down to the
Catalan number C_n.
"""

from typing import List


def generate_parenthesis(n: int) -> List[str]:
    res, path = [], []

    def backtrack(open_used: int, close_used: int):
        if len(path) == 2 * n:
            res.append("".join(path))
            return
        # Can we still add '(' ?
        if open_used < n:
            path.append("(")
            backtrack(open_used + 1, close_used)
            path.pop()
        # Can we still add ')' without breaking validity?
        if close_used < open_used:
            path.append(")")
            backtrack(open_used, close_used + 1)
            path.pop()

    backtrack(0, 0)
    return res


if __name__ == "__main__":
    print(generate_parenthesis(3))
