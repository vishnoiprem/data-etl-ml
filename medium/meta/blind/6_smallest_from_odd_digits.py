"""
Problem 6 (Easy-Medium) — Smallest non-negative number from a digit's odd digits

Given a non-negative integer, return the smallest non-negative integer
that can be formed using ALL of its odd-valued digits (in any order).
If there are no odd digits, return 0.

Examples
--------
>>> smallest_from_odd_digits(123456)
135
>>> smallest_from_odd_digits(2468)
0
>>> smallest_from_odd_digits(97531)
13579
>>> smallest_from_odd_digits(0)
0
>>> smallest_from_odd_digits(13579)
13579

How to think (interview script)
------------------------------
"Extract odd digits (d % 2 == 1). Sort them ascending — that's the
smallest arrangement. Concatenate. If empty, return 0.

This is a string problem, not a math problem. Treat the integer as a
string and stay in strings; don't do integer concatenation via
multiplication by 10 because leading zeros (if they appeared) would
be lost.

Edge case to mention in the interview: if 0 itself is an odd digit (it
isn't — 0 is even). So the empty case is the only zero-return path."

Complexity: O(d log d) where d = number of digits.

Follow-ups
----------
- "What if I want the LARGEST such number?"
  Sort descending.
- "What about even digits?"
  Trivial change to the parity check.
- "What if the input has leading zeros after we extract?"
  Can't happen — leading zeros never appear in digit extraction.
"""


def smallest_from_odd_digits(n: int) -> int:
    """Smallest non-negative integer composed of all odd digits of `n`. 0 if none."""
    odd_digits = sorted(d for d in str(abs(n)) if int(d) % 2 == 1)
    if not odd_digits:
        return 0
    return int(''.join(odd_digits))


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    # Only odd
    assert smallest_from_odd_digits(333) == 333
    # Mixed
    assert smallest_from_odd_digits(13579) == 13579
    # Only even
    assert smallest_from_odd_digits(222) == 0
    # Single digit odd
    assert smallest_from_odd_digits(7) == 7
    print("All tests passed for smallest_from_odd_digits.")
