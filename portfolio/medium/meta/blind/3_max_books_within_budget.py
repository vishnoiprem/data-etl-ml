"""
Problem 3 (Medium) — Max unique books within a budget

Given a list of (positive) book prices and a budget, find the maximum
number of UNIQUE books you can buy. Each book can be purchased only once.

Examples
--------
>>>
([12.5, 9.99, 15.0, 11.25, 8.0], 30)
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
# L2 — Hard / production-grade: heapify + pop cheapest until over budget.
# How to think: "If budget is tiny relative to the prices (say budget
# 10 but 1M books), heapify is O(n) and we pop only k+1 times, so
# O(n + k log n) instead of a full O(n log n) sort. Same answer."
# ----------------------------------------------------------------------
def max_unique_books_l2(prices: Iterable[float], budget: float) -> int:
    if budget <= 0:
        return 0
    heap = list(prices)          # materialize once — works for generators too
    heapq.heapify(heap)          # O(n)
    spent = 0.0
    count = 0
    # Pop the cheapest book while it still fits the budget.
    while heap and spent + heap[0] <= budget:
        spent += heapq.heappop(heap)
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
    # L2 must accept any iterable, including a one-shot generator.
    assert max_unique_books_l2((p for p in [1.0, 2.0, 3.0]), 10) == 3
    print("All tests passed for max_unique_books (L0 + L1 + L2).")


def max_unique_books(prices, budget):
    """
    Find max unique books you can buy within budget using greedy approach.

    Strategy: Sort ascending, greedily buy cheapest books first.
    Why it works: Every cheaper book "frees up" more budget for additional books.

    Time: O(n log n) — sort dominates
    Space: O(1) if sort is in-place; O(n) if not (depends on language)
    """
    if not prices or budget <= 0:
        return 0

    sorted_prices = sorted(prices)
    total_spent = 0
    books_bought = 0

    for price in sorted_prices:
        if total_spent + price <= budget:
            total_spent += price
            books_bought += 1
        else:
            break  # Can't afford any more books

    return books_bought


# Test 1: Mixed prices, budget = 30
prices = [12.5, 9.99, 15.0, 11.25, 8.0]
# Sorted: [8.0, 9.99, 11.25, 12.5, 15.0]
# Buy: 8.0 (total: 8.0), 9.99 (17.99), 11.25 (29.24) ✓ 3 books
assert max_unique_books(prices, 30) == 3

# Test 2: Zero budget
assert max_unique_books([1.0, 2.0, 3.0], 0) == 0

# Test 3: Duplicates in prices
prices = [5.0, 5.0, 5.0]
# Sorted: [5.0, 5.0, 5.0]
# Buy: 5.0 (5.0), 5.0 (10.0) — can't afford third ✓
assert max_unique_books(prices, 10) == 2

# Test 4: Empty list
assert max_unique_books([], 100) == 0



import heapq

def max_unique_books_heap(prices, budget):
    """Use heap instead of sorting"""
    heap = prices.copy()
    heapq.heapify(heap)  # O(n)

    total_spent = 0
    books_bought = 0

    while heap and total_spent + heap[0] <= budget:
        total_spent += heapq.heappop(heap)  # O(log n)
        books_bought += 1

    return books_bought


def max_unique_books_presorted(sorted_prices, budget):
    """If prices already sorted, no need to sort again"""
    total_spent = 0
    for i, price in enumerate(sorted_prices):
        if total_spent + price <= budget:
            total_spent += price
        else:
            return i
    return len(sorted_prices)


def max_unique_books_knapsack(prices, budget):
    """DP approach (more general, handles duplicates)"""
    dp = [0] * (int(budget) + 1)

    for price in prices:
        for coin in range(int(price), int(budget) + 1):
            dp[coin] = max(dp[coin], dp[coin - int(price)] + 1)

    return dp[int(budget)