"""
Problem 3 (Medium) — Max unique books within a budget

Given a list of (positive) book prices and a budget, find the maximum
number of UNIQUE books you can buy. Each book can be purchased only once.

Examples
--------
>>> max_unique_books([12.5, 9.99, 15.0, 11.25, 8.0], 30)
3
>>> max_unique_books([1.0, 2.0, 3.0], 0)
0
>>> max_unique_books([5.0, 5.0, 5.0], 10)
2
>>> max_unique_books([], 100)
0

How to think (interview script)
------------------------------
"Classic greedy: sort ascending, take the cheapest first until we can't
afford the next one. This is optimal because every cheaper book costs
less and frees more budget for later books.

I could use a heap for theoretical elegance, but a sorted list is
simpler, faster in practice, and easier to read. The interviewer is
testing for clarity, not heap usage."

Complexity: O(n log n) time for the sort; O(1) extra space.

Follow-ups
----------
- "What if we could buy multiple copies?"
  Different problem — it's the unbounded knapsack variant.
- "What if we want the CHEAPEST subset of exactly k books?"
  Take the k cheapest. Trivial.
- "What if there are discounts (e.g., 3 books = 10% off)?"
  Becomes NP-hard in general — different problem.
"""

import heapq
from itertools import combinations
from typing import Iterable, List


# ----------------------------------------------------------------------
# L0 — Easy / brute force: enumerate every subset, find the cheapest
# affordable one with the largest size.
# How to think: "All subsets — O(2ⁿ·n). Fine for n≤20; useless
# otherwise. Start here to anchor the answer, then say 'I can do
# better' and pivot to the greedy."
# ----------------------------------------------------------------------
def max_unique_books_l0(prices: List[float], budget: float) -> int:
    if budget <= 0 or not prices:
        return 0
    best = 0
    n = len(prices)
    for r in range(1, n + 1):
        for combo in combinations(prices, r):
            if sum(combo) <= budget:
                best = max(best, r)
    return best


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: greedy sort.
# How to think: "Greedy: buy cheapest first. Optimal because each cheap
# book frees budget. O(n log n)."
# ----------------------------------------------------------------------
def max_unique_books(prices: List[float], budget: float) -> int:
    """Maximum number of unique books we can buy within `budget`."""
    if budget <= 0 or not prices:
        return 0
    prices_sorted = sorted(prices)
    spent = 0.0
    count = 0
    for p in prices_sorted:
        if spent + p > budget:
            break
        spent += p
        count += 1
    return count


# ----------------------------------------------------------------------
# L2 — Hard / production-grade: heapq.nsmallest avoids sorting the
# whole list when you stop early on a tight budget.
# How to think: "If budget is tiny relative to the prices (say budget
# 10 but 1M books), `nsmallest` stops as soon as the heap head exceeds
# budget. Same complexity in the worst case but better constant factor
# when k (the answer) is small."
# ----------------------------------------------------------------------
def max_unique_books_l2(prices: Iterable[float], budget: float) -> int:
    if budget <= 0:
        return 0
    spent = 0.0
    count = 0
    # nsmallest yields ascending; stop the moment the next price breaks the budget.
    for p in heapq.nsmallest(len(list(prices)), prices):  # materialize once for length
        if spent + p > budget:
            break
        spent += p
        count += 1
    return count


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        ([12.5, 9.99, 15.0, 11.25, 8.0], 30, 3),
        ([1.0, 2.0, 3.0], 0, 0),
        ([5.0, 5.0, 5.0], 10, 2),
        ([], 100, 0),
        ([10, 20, 30, 40, 50], 60, 3),
        ([10, 20, 30, 40, 50], 200, 5),
        ([10, 20, 30], 100, 3),
    ]
    for prices, budget, expected in samples:
        assert max_unique_books_l0(prices, budget) == expected, prices
        assert max_unique_books(prices, budget) == expected, prices
        assert max_unique_books_l2(prices, budget) == expected, prices
    print("All tests passed for max_unique_books (L0 + L1 + L2).")
