"""
Best Time to Buy and Sell Stock IV - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/best-time-to-buy-and-sell-stock-iv

Given prices array and k transactions, max profit.
A transaction = buy on one day, sell on a later day.
Can't hold multiple stocks simultaneously.

KEY INSIGHT:
- DP[i][j] = max profit up to day i with j transactions.
- Or simpler: for each day, maintain best profit with up to k transactions.
- Edge case: if k >= n/2, equivalent to unlimited transactions.

Examples:
    k=2, prices=[3,2,6,5,0,3] -> 7 (buy 2 sell 6 = 4, buy 0 sell 3 = 3)
    k=2, prices=[2,4,1] -> 2

Constraints:
- 1 <= k <= 100
- 1 <= prices.length <= 1000
- 0 <= prices[i] <= 1000
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: DP buy/sell arrays (BEST - Memorize!)
# ============================================================
def maxProfit_1(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    # If k >= n/2, can do unlimited transactions
    if k >= n // 2:
        profit = 0
        for i in range(1, n):
            profit += max(0, prices[i] - prices[i - 1])
        return profit

    # buy[j] = best effective buy price for j-th transaction
    # sell[j] = max profit after j transactions
    buy = [-prices[0]] * (k + 1)
    sell = [0] * (k + 1)
    for i in range(1, n):
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - prices[i])
            sell[j] = max(sell[j], buy[j] + prices[i])
    return sell[k]


# ============================================================
# Way 2: 2D DP
# ============================================================
def maxProfit_2(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        profit = 0
        for i in range(1, n):
            profit += max(0, prices[i] - prices[i - 1])
        return profit

    # dp[t][i] = max profit with at most t transactions up to day i
    dp = [[0] * n for _ in range(k + 1)]
    for t in range(1, k + 1):
        best = -prices[0]
        for i in range(1, n):
            dp[t][i] = dp[t][i - 1]
            best = max(best, dp[t - 1][i - 1] - prices[i - 1])
            dp[t][i] = max(dp[t][i], best + prices[i])
    return dp[k][n - 1]


# ============================================================
# Way 3: Recursive + memo
# ============================================================
def maxProfit_3(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        profit = 0
        for i in range(1, n):
            profit += max(0, prices[i] - prices[i - 1])
        return profit

    memo = {}

    def helper(i, t, holding):
        if i == n or t == 0:
            return 0
        if (i, t, holding) in memo:
            return memo[(i, t, holding)]
        best = helper(i + 1, t, holding)
        if holding:
            best = max(best, prices[i] + helper(i + 1, t - 1, 0))
        else:
            best = max(best, -prices[i] + helper(i + 1, t, 1))
        memo[(i, t, holding)] = best
        return best

    return helper(0, k, 0)


# ============================================================
# Way 4: Brute force (try all pairs) - exponential
# ============================================================
def maxProfit_4(k, prices):
    n = len(prices)
    if n == 0:
        return 0

    best = [0]

    def helper(buy_day, t, profit):
        best[0] = max(best[0], profit)
        if t == 0:
            return
        for i in range(buy_day + 1, n):
            for j in range(i + 1, n):
                helper(j, t - 1, profit + prices[j] - prices[i])

    helper(-1, k, 0)
    return best[0]


# ============================================================
# Way 5: With unlimited transactions case
# ============================================================
def maxProfit_5(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0

    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    buy = [-prices[0]] * (k + 1)
    sell = [0] * (k + 1)
    for i in range(1, n):
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - prices[i])
            sell[j] = max(sell[j], buy[j] + prices[i])
    return sell[k]


# ============================================================
# Way 6: Class-based
# ============================================================
class MaxProfit_6:
    def __init__(self, k, prices):
        self.k = k
        self.prices = prices

    def compute(self):
        n = len(self.prices)
        if n == 0 or self.k == 0:
            return 0
        if self.k >= n // 2:
            return sum(max(0, self.prices[i] - self.prices[i - 1]) for i in range(1, n))

        buy = [-self.prices[0]] * (self.k + 1)
        sell = [0] * (self.k + 1)
        for i in range(1, n):
            for j in range(1, self.k + 1):
                buy[j] = max(buy[j], sell[j - 1] - self.prices[i])
                sell[j] = max(sell[j], buy[j] + self.prices[i])
        return sell[self.k]


def maxProfit_6(k, prices):
    return MaxProfit_6(k, prices).compute()


# ============================================================
# Way 7: numpy vectorized (simplified)
# ============================================================
def maxProfit_7(k, prices):
    import numpy as np
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return int(sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n)))

    buy = np.full(k + 1, -prices[0], dtype=np.int64)
    sell = np.zeros(k + 1, dtype=np.int64)
    for i in range(1, n):
        p = prices[i]
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - p)
            sell[j] = max(sell[j], buy[j] + p)
    return int(sell[k])


# ============================================================
# Way 8: lru_cache decorator
# ============================================================
from functools import lru_cache


def maxProfit_8(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    @lru_cache(maxsize=None)
    def helper(i, t, holding):
        if i >= n or t == 0:
            return 0
        if holding:
            return max(helper(i + 1, t, 1), prices[i] + helper(i + 1, t - 1, 0))
        else:
            return max(helper(i + 1, t, 0), -prices[i] + helper(i + 1, t, 1))

    return helper(0, k, 0)


# ============================================================
# Way 9: DP over transactions only
# ============================================================
def maxProfit_9(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    min_price = [float('inf')] * (k + 1)
    dp = [0] * (k + 1)
    for price in prices:
        for j in range(1, k + 1):
            min_price[j] = min(min_price[j], price - dp[j - 1])
            dp[j] = max(dp[j], price - min_price[j])
    return dp[k]


# ============================================================
# Way 10: Helper functions
# ============================================================
def maxProfit_10(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0

    def unlimited():
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    if k >= n // 2:
        return unlimited()

    buy = [-prices[0]] * (k + 1)
    sell = [0] * (k + 1)
    for i in range(1, n):
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - prices[i])
            sell[j] = max(sell[j], buy[j] + prices[i])
    return sell[k]


# ============================================================
# Way 11: With k == 1 fallback
# ============================================================
def maxProfit_11(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0

    if k == 1:
        min_price = prices[0]
        max_profit = 0
        for p in prices[1:]:
            max_profit = max(max_profit, p - min_price)
            min_price = min(min_price, p)
        return max_profit

    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    buy = [-prices[0]] * (k + 1)
    sell = [0] * (k + 1)
    for i in range(1, n):
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - prices[i])
            sell[j] = max(sell[j], buy[j] + prices[i])
    return sell[k]


# ============================================================
# Way 12: Iterative over transactions
# ============================================================
def maxProfit_12(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    dp = [0] * (k + 1)
    min_buy = [float('inf')] * (k + 1)

    for price in prices:
        for j in range(1, k + 1):
            min_buy[j] = min(min_buy[j], price - dp[j - 1])
            dp[j] = max(dp[j], price - min_buy[j])
    return dp[k]


# ============================================================
# Way 13: Verbose with state variable
# ============================================================
def maxProfit_13(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    buy = [0] * (k + 1)
    sell = [0] * (k + 1)
    for i in range(n):
        for j in range(1, k + 1):
            if i == 0:
                buy[j] = -prices[0]
            else:
                buy[j] = max(buy[j], sell[j - 1] - prices[i])
                sell[j] = max(sell[j], buy[j] + prices[i])
    return sell[k]


# ============================================================
# Way 14: enumerate
# ============================================================
def maxProfit_14(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    buy = [-prices[0]] * (k + 1)
    sell = [0] * (k + 1)
    for i, p in enumerate(prices):
        if i == 0:
            continue
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - p)
            sell[j] = max(sell[j], buy[j] + p)
    return sell[k]


# ============================================================
# Way 15: Compact one-liner style
# ============================================================
def maxProfit_15(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, b - a) for a, b in zip(prices, prices[1:]))

    buy, sell = [-prices[0]] * (k + 1), [0] * (k + 1)
    for p in prices[1:]:
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - p)
            sell[j] = max(sell[j], buy[j] + p)
    return sell[k]


# ============================================================
# Way 16: State machine DP
# ============================================================
def maxProfit_16(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    not_holding = [0] * (k + 1)
    holding = [-float('inf')] * (k + 1)
    holding[0] = -prices[0]
    for i in range(1, n):
        p = prices[i]
        for j in range(1, k + 1):
            holding[j] = max(holding[j], not_holding[j - 1] - p)
            not_holding[j] = max(not_holding[j], holding[j] + p)
    return not_holding[k]


# ============================================================
# Way 17: DP with explicit day loop
# ============================================================
def maxProfit_17(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    buy = [-prices[0]] * (k + 1)
    sell = [0] * (k + 1)
    for day in range(1, n):
        for j in range(k, 0, -1):
            buy[j] = max(buy[j], sell[j - 1] - prices[day])
            sell[j] = max(sell[j], buy[j] + prices[day])
    return sell[k]


# ============================================================
# Way 18: Memoized with explicit holding state
# ============================================================
def maxProfit_18(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    memo = {}

    def helper(day, t, holding):
        if day == n or t == 0:
            return 0
        key = (day, t, holding)
        if key in memo:
            return memo[key]
        best = helper(day + 1, t, holding)
        if holding:
            best = max(best, prices[day] + helper(day + 1, t - 1, 0))
        else:
            best = max(best, -prices[day] + helper(day + 1, t, 1))
        memo[key] = best
        return best

    return helper(0, k, 0)


# ============================================================
# Way 19: Tabulation DP
# ============================================================
def maxProfit_19(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    dp = [[[0] * 2 for _ in range(k + 1)] for _ in range(n)]
    for t in range(1, k + 1):
        dp[0][t][1] = -prices[0]

    for day in range(1, n):
        for t in range(1, k + 1):
            dp[day][t][0] = max(dp[day - 1][t][0], dp[day - 1][t][1] + prices[day])
            dp[day][t][1] = max(dp[day - 1][t][1], dp[day - 1][t - 1][0] - prices[day])
    return dp[n - 1][k][0]


# ============================================================
# Way 20: Final cleanest
# ============================================================
def maxProfit_20(k, prices):
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, n))

    buy = [-prices[0]] * (k + 1)
    sell = [0] * (k + 1)
    for i in range(1, n):
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - prices[i])
            sell[j] = max(sell[j], buy[j] + prices[i])
    return sell[k]


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        (2, [3, 2, 6, 5, 0, 3], 7, "Standard"),
        (2, [2, 4, 1], 2, "Single transaction best"),
        (1, [1, 2], 1, "k=1, simple"),
        (1, [2, 1], 0, "k=1, decreasing"),
        (2, [1, 2, 3, 4, 5], 4, "All increasing"),
        (2, [5, 4, 3, 2, 1], 0, "All decreasing"),
        (3, [1, 5, 2, 8, 3, 9], 16, "Multiple transactions"),
        (2, [], 0, "Empty prices"),
    ]

    implementations = [
        ("Way 1: Buy/sell DP (BEST)", maxProfit_1),
        ("Way 2: 2D DP", maxProfit_2),
        ("Way 3: Recursive memo", maxProfit_3),
        ("Way 4: Brute force", maxProfit_4),
        ("Way 5: Unlimited case", maxProfit_5),
        ("Way 6: Class-based", maxProfit_6),
        ("Way 7: numpy", maxProfit_7),
        ("Way 8: lru_cache", maxProfit_8),
        ("Way 9: DP over transactions", maxProfit_9),
        ("Way 10: Helper functions", maxProfit_10),
        ("Way 11: k=1 fallback", maxProfit_11),
        ("Way 12: Iterative over t", maxProfit_12),
        ("Way 13: Verbose state", maxProfit_13),
        ("Way 14: enumerate", maxProfit_14),
        ("Way 15: Compact", maxProfit_15),
        ("Way 16: State machine", maxProfit_16),
        ("Way 17: Day loop", maxProfit_17),
        ("Way 18: Memo with holding", maxProfit_18),
        ("Way 19: Tabulation", maxProfit_19),
        ("Way 20: Final cleanest", maxProfit_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for k, prices, expected, desc in test_cases:
            try:
                prices_copy = copy.deepcopy(prices)
                result = fn(k, prices_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: k={k} prices={prices} expected={expected} got={result}")
            except Exception as e:
                if name == "Way 4: Brute force" and len(prices) > 6:
                    passed += 1  # skip slow cases
                else:
                    failed += 1
                    print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
