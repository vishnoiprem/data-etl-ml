"""Best Time to Buy and Sell Stock — max profit from one buy and one sell.

Time:  O(n) — single pass
Space: O(1) — two scalars
"""


def solve_best_time(prices):
    """Return the max profit (sell - buy) for one transaction.

    >>> solve_best_time([7, 1, 5, 3, 6, 4])
    5
    """
    if not prices:
        return 0
    min_buy = prices[0]
    best = 0
    for price in prices[1:]:
        # Either sell today at today's price, or keep the best so far.
        best = max(best, price - min_buy)
        min_buy = min(min_buy, price)
    return best


if __name__ == "__main__":
    print(solve_best_time([7, 1, 5, 3, 6, 4]))
