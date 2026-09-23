"""
Problem 9 (Medium) — Largest number from digits

Given a number with multiple digits, return the largest possible number
that can be formed using ALL of its digits.

Examples
--------
>>> largest_from_digits(123456)
654321
>>> largest_from_digits(555)
555
>>> largest_from_digits(0)
0
>>> largest_from_digits(9876543210)
9876543210

How to think (interview script)
------------------------------
"Sort the digits in DESCENDING order and concatenate. The optimal
arrangement for max value is always descending because each higher digit
in a more significant position multiplies the value more.

Treat the input as a string to avoid integer-leading-zero issues when
the input is 0 (which would be dropped by int conversion if we
accidentally tried to convert an empty result)."

Complexity: O(d log d) where d = number of digits.

Follow-ups
----------
- "What if I want the SMALLEST number?"
  Sort ascending; but strip leading zeros (or return 0 if all zero).
- "What if I want the smallest number with no leading zeros?"
  Sort ascending, then move the first non-zero digit to the front.
- "What if the digits are already in a list, not a number?"
  Same logic, just sort the list directly.
"""


def largest_from_digits(n: int) -> int:
    """Largest number formed by rearranging the digits of `n`."""
    if n == 0:
        return 0
    digits_desc = sorted(str(abs(n)), reverse=True)
    return int(''.join(digits_desc))


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    # All same digit
    assert largest_from_digits(11111) == 11111
    # Already descending
    assert largest_from_digits(987) == 987
    # Mixed
    assert largest_from_digits(1020304050) == 5432100000
    # Single digit
    assert largest_from_digits(7) == 7
    print("All tests passed for largest_from_digits.")
