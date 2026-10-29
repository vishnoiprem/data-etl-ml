"""Mock 113 — Meta E4/E5 screen.

Two functions:
  1. FizzBuzz
  2. Valid parentheses with '*' wildcards
"""


def solve_fizzbuzz(n):
    """Return the FizzBuzz list for 1..n.

    >>> solve_fizzbuzz(5)
    ['1', '2', 'Fizz', '4', 'Buzz']
    """
    out = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            out.append("FizzBuzz")
        elif i % 3 == 0:
            out.append("Fizz")
        elif i % 5 == 0:
            out.append("Buzz")
        else:
            out.append(str(i))
    return out


def solve_valid_parens_wildcard(s):
    """Return True if s is valid where '*' can be '(', ')' or empty.

    Time:  O(n) — one pass
    Space: O(n) — low/high counters are scalars; the set isn't used.

    Approach: track the range of possible "open count" at each step.
    An open count between low and high (inclusive) is achievable.
    After the full scan, low == 0 means the string can be valid.
    """
    low = high = 0
    for ch in s:
        if ch == "(":
            low += 1
            high += 1
        elif ch == ")":
            # Both extremes shrink by 1.
            low = max(low - 1, 0)
            high -= 1
        else:  # '*'
            # Treat as ')' (low--), '' (low unchanged), or '(' (high++).
            low = max(low - 1, 0)
            high += 1
        if high < 0:
            return False
    return low == 0


if __name__ == "__main__":
    print(solve_fizzbuzz(15))
    print(solve_valid_parens_wildcard("(*))"))
