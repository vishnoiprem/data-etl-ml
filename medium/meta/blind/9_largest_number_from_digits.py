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


# ----------------------------------------------------------------------
# L0 — Easy / brute force: try every permutation, take the max.
# How to think: "All permutations, take the max. O(d!). Fine for d≤8;
# don't ship. Start here to anchor, then pivot to sort."
# ----------------------------------------------------------------------
def largest_from_digits_l0(n: int) -> int:
    if n == 0:
        return 0
    from itertools import permutations
    digits = str(abs(n))
    return int(max(int(''.join(p)) for p in permutations(digits)))


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: sort descending.
# How to think: "Sort digits descending, join, convert back. Handle
# n==0 and negatives via abs()."
# ----------------------------------------------------------------------
def largest_from_digits(n: int) -> int:
    """Largest number formed by rearranging the digits of `n`."""
    if n == 0:
        return 0
    digits_desc = sorted(str(abs(n)), reverse=True)
    return int(''.join(digits_desc))


# ----------------------------------------------------------------------
# L2 — Hard / production-grade: counting sort — O(d) and zero
# comparison overhead. Useful when the digit count is huge.
# How to think: "Digits are 0..9 — use a count array. Emit 9..0 in
# order. Same answer, faster on huge inputs and no comparison sort."
# ----------------------------------------------------------------------
def largest_from_digits_l2(n: int) -> int:
    if n == 0:
        return 0
    counts = [0] * 10
    for ch in str(abs(n)):
        counts[int(ch)] += 1
    result = ''.join(str(d) * counts[d] for d in range(9, -1, -1))
    return int(result)


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        (123456, 654321),
        (555, 555),
        (0, 0),
        (9876543210, 9876543210),
        (11111, 11111),
        (987, 987),
        (1020304050, 5432100000),
        (7, 7),
    ]
    for n, expected in samples:
        assert largest_from_digits_l0(n) == expected, n
        assert largest_from_digits(n) == expected, n
        assert largest_from_digits_l2(n) == expected, n
    print("All tests passed for largest_from_digits (L0 + L1 + L2).")
