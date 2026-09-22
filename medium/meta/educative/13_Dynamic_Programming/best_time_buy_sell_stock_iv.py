def maxProfit(k, prices):
    """
    Return the maximum profit achievable with at most k transactions.
    A transaction = buy then sell later. Cannot hold multiple stocks.

    Optimization: if k >= n//2, the constraint is effectively removed
    (we can't possibly need more than n//2 transactions), so fall back
    to the greedy "add every upward move" approach.
    """
    n = len(prices)
    if n < 2 or k == 0:
        return 0

    # If k is large enough to cover all possible transactions,
    # profit = sum of every consecutive upward move.
    if k >= n // 2:
        profit = 0
        for i in range(1, n):
            if prices[i] > prices[i - 1]:
                profit += prices[i] - prices[i - 1]
        return profit

    # DP:
    # sell[t] = max profit up to today with at most `t` transactions,
    #           ending with a SELL (i.e., not holding stock today).
    # hold[t] = max profit up to today with at most `t` transactions,
    #           ending HOLDING stock (bought but not yet sold).
    # Initialize: hold[0] = -prices[0]; sell[t] = 0 for all t.
    sell = [0] * (k + 1)
    hold = [-prices[0]] * (k + 1)

    for i in range(1, n):
        for t in range(1, k + 1):
            # Either we didn't sell today (carry over sell[t]),
            # or we sold today after holding (uses one transaction):
            new_sell = max(sell[t], hold[t] + prices[i])
            # Either we didn't buy today (carry over hold[t]),
            # or we bought today after a sell in a previous transaction:
            new_hold = max(hold[t], sell[t - 1] - prices[i])
            sell[t] = new_sell
            hold[t] = new_hold

    return sell[k]


if __name__ == "__main__":
    # Test cases
    print(maxProfit(2, [2, 4, 1]))                          # 2
    print(maxProfit(2, [3, 2, 6, 5, 0, 3]))                # 7
    print(maxProfit(1, [7, 1, 5, 3, 6, 4]))                # 5
    print(maxProfit(2, [7, 1, 5, 3, 6, 4]))                # 7
    print(maxProfit(0, [1, 2, 3]))                          # 0
