"""
LETTER CASE PERMUTATION — LeetCode 784
Given a string `s`, return every string we can get by toggling the
case of every letter. Digits stay as-is.

Example
-------
s = "a1b2"
Answer: ["a1b2","a1B2","A1b2","A1B2"]

Pattern
-------
For each character:
  • If it's a digit: only one branch (itself).
  • If it's a letter: TWO branches (lower, upper).
This is the same "Cartesian product" shape as the phone-keypad problem,
just with mixed "choice count = 1" and "choice count = 2" slots.
"""

from typing import List


def letter_case_permutation(s: str) -> List[str]:
    res, path = [], []

    def backtrack(i: int):
        if i == len(s):
            res.append("".join(path))
            return
        ch = s[i]
        if ch.isdigit():
            path.append(ch)
            backtrack(i + 1)
            path.pop()
        else:
            # Lower case branch
            path.append(ch.lower())
            backtrack(i + 1)
            path.pop()
            # Upper case branch
            path.append(ch.upper())
            backtrack(i + 1)
            path.pop()

    backtrack(0)
    return res


# ---- Iterative (BFS-style) alternative — easy to remember ----
def letter_case_permutation_bfs(s: str) -> List[str]:
    res = [""]
    for ch in s:
        if ch.isdigit():
            res = [r + ch for r in res]
        else:
            res = [r + ch.lower() for r in res] + [r + ch.upper() for r in res]
    return res


if __name__ == "__main__":
    print(letter_case_permutation("a1b2"))
    print(letter_case_permutation_bfs("a1b2"))
