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


# ----------------------------------------------------------------------
# L0 — Easy / brute force: build a list of odd ints, sort ascending,
# concatenate manually.
# How to think: "Extract, sort ascending, join. The most literal way
# to write it. Fine as a starting point — pivot to L1 once you've
# shown the answer."
# ----------------------------------------------------------------------
def smallest_from_odd_digits_l0(n: int) -> int:
    odd = [int(d) for d in str(n) if int(d) % 2 == 1]
    odd.sort()
    if not odd:
        return 0
    result = 0
    for d in odd:
        result = result * 10 + d
    return result


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: `sorted` directly on the string.
# How to think: "`sorted` works on strings and gives characters back.
# `abs()` handles negatives. Join with empty separator and convert."
# ----------------------------------------------------------------------
def smallest_from_odd_digits(n: int) -> int:
    """Smallest non-negative integer composed of all odd digits of `n`. 0 if none."""
    odd_digits = sorted(d for d in str(abs(n)) if int(d) % 2 == 1)
    if not odd_digits:
        return 0
    return int(''.join(odd_digits))


# ----------------------------------------------------------------------
# L2 — Hard / production-grade: counting sort — O(d) and zero
# comparison overhead.
# How to think: "Digits are 0..9 — use a count array and emit in
# ascending order. No sort call. Mention only if asked about lower
# bounds; in practice L1 is plenty fast."
# ----------------------------------------------------------------------
def smallest_from_odd_digits_l2(n: int) -> int:
    counts = [0] * 10
    for ch in str(abs(n)):
        d = int(ch)
        if d % 2 == 1:
            counts[d] += 1
    # Emit 1,3,5,7,9 in order
    result = ''.join(str(d) * counts[d] for d in (1, 3, 5, 7, 9))
    return int(result) if result else 0


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        (123456, 135),
        (2468, 0),
        (97531, 13579),
        (0, 0),
        (13579, 13579),
        (333, 333),
        (222, 0),
        (7, 7),
    ]
    for n, expected in samples:
        assert smallest_from_odd_digits_l0(n) == expected, n
        assert smallest_from_odd_digits(n) == expected, n
        assert smallest_from_odd_digits_l2(n) == expected, n
    print("All tests passed for smallest_from_odd_digits (L0 + L1 + L2).")
