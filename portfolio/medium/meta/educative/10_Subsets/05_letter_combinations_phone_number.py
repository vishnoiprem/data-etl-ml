"""
LETTER COMBINATIONS OF A PHONE NUMBER — LeetCode 17
Given a digit string `digits` (2-9), return ALL possible letter
combinations that the number could represent (classic phone keypad).

Example
-------
digits = "23"
Answer: ["ad","ae","af","bd","be","bf","cd","ce","cf"]

Pattern
-------
This is a Cartesian-product problem disguised as a backtracking problem.
For each digit we pick one of its letters. The number of paths is
the PRODUCT of the choice counts: 3 × 3 = 9 in the example.
"""

from typing import List

PHONE = {
    "2": "abc",
    "3": "def",
    "4": "ghi",
    "5": "jkl",
    "6": "mno",
    "7": "pqrs",
    "8": "tuv",
    "9": "wxyz",
}


def letter_combinations(digits: str) -> List[str]:
    if not digits:
        return []
    res, path = [], []

    def backtrack(i: int):
        if i == len(digits):
            res.append("".join(path))
            return
        for ch in PHONE[digits[i]]:
            path.append(ch)
            backtrack(i + 1)
            path.pop()

    backtrack(0)
    return res


if __name__ == "__main__":
    print(letter_combinations("23"))
