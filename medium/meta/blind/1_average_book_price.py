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


def average_price(prices: list[float]) -> float:
    """Return the arithmetic mean of `prices`. Empty list -> 0."""
    if not prices:
        return 0.0
    return sum(prices) / len(prices)


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    # Additional sanity checks
    assert average_price([1.0, 2.0, 3.0, 4.0, 5.0]) == 3.0
    assert average_price([10, 20, 30]) == 20.0  # ints coerced to float on div
    print("All tests passed for average_price.")
