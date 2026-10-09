"""Letter Combinations of a Phone Number.

Time:  O(4^n) — 4 letters per digit, n digits
Space: O(n) — recursion stack
"""

PHONE = {
    "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
    "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz",
}


def solve_letter_combinations(digits):
    """Return all possible letter combinations.

    >>> sorted(solve_letter_combinations("23"))
    ['ad', 'ae', 'af', 'bd', 'be', 'bf', 'cd', 'ce', 'cf']
    """
    if not digits:
        return []
    out = []

    def backtrack(idx, current):
        if idx == len(digits):
            out.append("".join(current))
            return
        for ch in PHONE[digits[idx]]:
            current.append(ch)
            backtrack(idx + 1, current)
            current.pop()

    backtrack(0, [])
    return out


if __name__ == "__main__":
    print(solve_letter_combinations("23"))
