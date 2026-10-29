"""
Problem 1 (Easy) — Average book price from a list

Return the mean of a list of positive book prices. Empty list -> 0.

Examples
--------
>>> average_price([12.5, 9.99, 15.0, 11.25, 8.0])
11.348
>>> average_price([])
0.0
>>> average_price([10.0])
10.0

How to think (interview script)
------------------------------
"Two-line solution: sum the list, divide by length. The edge case is the
empty list — I'll guard against div-by-zero. The interviewer doesn't
care about precision to many decimal places; round to 2 in production
code but keep the float here for the doctest."

Complexity: O(n) time, O(1) extra space.
"""

from typing import Iterable


# ----------------------------------------------------------------------
# L0 — Easy / brute force: explicit accumulator loop.
# How to think: "Loop through and accumulate sum + count. The only edge
# case is empty. The interview asks for the average; this is the most
# literal implementation."
# ----------------------------------------------------------------------
def average_price_l0(prices: list[float]) -> float:
    total = 0.0
    count = 0
    for p in prices:
        total += p
        count += 1
    return total / count if count else 0.0


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: built-in sum + len.
# How to think: "Python's `sum` + `len` is the built-in answer. Two
# lines, O(n). This is the cleanest solution and the one I'd ship."
# ----------------------------------------------------------------------
def average_price(prices: list[float]) -> float:
    """Return the arithmetic mean of `prices`. Empty list -> 0."""
    if not prices:
        return 0.0
    return sum(prices) / len(prices)


# ----------------------------------------------------------------------
# L2 — Hard / production-grade: numerically stable, accepts any iterable.
# How to think: "`statistics.fmean` is faster than `sum/len` for huge
# lists and handles precision better. It also accepts iterators, so
# this works for a generator or a database cursor — not just a list."
# ----------------------------------------------------------------------
def average_price_l2(prices: Iterable[float]) -> float:
    import statistics
    prices_list = list(prices)  # fmean needs at least one pass; materialize first
    return statistics.fmean(prices_list) if prices_list else 0.0


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    # Cross-check all three implementations agree
    samples = [
        [12.5, 9.99, 15.0, 11.25, 8.0],
        [],
        [10.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [10, 20, 30],
    ]
    for s in samples:
        a = average_price_l0(s)
        b = average_price(s)
        c = average_price_l2(s)
        assert abs(a - b) < 1e-9 and abs(b - c) < 1e-9, (s, a, b, c)
    # Additional sanity checks
    assert average_price([1.0, 2.0, 3.0, 4.0, 5.0]) == 3.0
    assert average_price([10, 20, 30]) == 20.0  # ints coerced to float on div
    print("All tests passed for average_price (L0 + L1 + L2).")
