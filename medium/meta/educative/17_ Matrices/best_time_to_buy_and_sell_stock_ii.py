"""
Best Time to Buy and Sell Stock II
Medium | 30 min

Given an array prices where prices[i] is the stock price on day i,
find the maximum profit. You may complete as many transactions as
you like (buy one, sell one) but you must hold at most one share
at any time.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/best-time-to-buy-and-sell-stock-ii

Examples:
    [7,1,5,3,6,4] -> 7   (buy 1 sell 5, buy 3 sell 6)
    [1,2,3,4,5]   -> 4   (buy 1 sell 5)
    [7,6,4,3,1]   -> 0   (no transactions)
    [1]           -> 0
    []            -> 0

Constraints:
- 1 <= prices.length <= 3*10^4
- 0 <= prices[i] <= 10^4

KEY INSIGHT:
Greedy: capture every upward slope. For each day, if price goes
up from previous day, add the difference to profit.
Equivalent to: sum of all positive diffs (prices[i+1] - prices[i]).

Time:  O(n) — single pass.
Space: O(1) — constant.
"""


# =============================================================================
# WAY 1: Greedy sum of positive diffs (BEST - Memorize!)
# =============================================================================
def max_profit_1(prices):
    """Greedy: add every positive diff."""
    profit = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i - 1]:
            profit += prices[i] - prices[i - 1]
    return profit


# =============================================================================
# WAY 2: Greedy with explicit delta
# =============================================================================
def max_profit_2(prices):
    """Same as Way 1 but with explicit delta variable."""
    profit = 0
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            profit += diff
    return profit


# =============================================================================
# WAY 3: Peak-valley approach
# =============================================================================
def max_profit_3(prices):
    """Find peaks and valleys; sum (peak - valley) for each uptrend."""
    if len(prices) < 2:
        return 0
    profit = 0
    i = 0
    while i < len(prices) - 1:
        # Find valley (lowest before going up).
        while i < len(prices) - 1 and prices[i] >= prices[i + 1]:
            i += 1
        valley = prices[i]
        # Find peak (highest before going down).
        while i < len(prices) - 1 and prices[i] <= prices[i + 1]:
            i += 1
        peak = prices[i]
        profit += peak - valley
    return profit


# =============================================================================
# WAY 4: DP with two states (cash, hold)
# =============================================================================
def max_profit_4(prices):
    """
    DP: cash = max profit when not holding.
        hold = max profit when holding (negative value).
    """
    if not prices:
        return 0
    cash = 0
    hold = -prices[0]
    for i in range(1, len(prices)):
        cash = max(cash, hold + prices[i])
        hold = max(hold, cash - prices[i])  # buy today
    return cash


# =============================================================================
# WAY 5: One-pass with prev variable
# =============================================================================
def max_profit_5(prices):
    """Track previous price and current profit."""
    if len(prices) < 2:
        return 0
    prev = prices[0]
    profit = 0
    for i in range(1, len(prices)):
        if prices[i] > prev:
            profit += prices[i] - prev
        prev = prices[i]
    return profit


# =============================================================================
# WAY 6: Use sum with generator
# =============================================================================
def max_profit_6(prices):
    """sum of max(0, prices[i] - prices[i-1]) for each i."""
    return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, len(prices)))


# =============================================================================
# WAY 7: Functional with reduce
# =============================================================================
def max_profit_7(prices):
    """Use functools.reduce to accumulate positive diffs."""
    from functools import reduce
    return reduce(
        lambda acc, i: acc + max(0, prices[i] - prices[i - 1]),
        range(1, len(prices)),
        0,
    )


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class Trader:
    def __init__(self, prices):
        self.prices = prices

    def max_profit(self):
        profit = 0
        for i in range(1, len(self.prices)):
            if self.prices[i] > self.prices[i - 1]:
                profit += self.prices[i] - self.prices[i - 1]
        return profit


def max_profit_8(prices):
    return Trader(prices).max_profit()


# =============================================================================
# WAY 9: Iterative with zip
# =============================================================================
def max_profit_9(prices):
    """Use zip to pair consecutive prices."""
    profit = 0
    for prev, cur in zip(prices, prices[1:]):
        if cur > prev:
            profit += cur - prev
    return profit


# =============================================================================
# WAY 10: Pure math / greedy with sentinel
# =============================================================================
def max_profit_10(prices):
    """Append sentinel (0) to avoid index bounds."""
    if not prices:
        return 0
    profit = 0
    prev = prices[0]
    for cur in prices[1:] + [0]:
        if cur > prev:
            profit += cur - prev
        prev = cur
    return profit


# =============================================================================
# WAY 11: Brute force recursion - try every (buy, sell) at every day
# =============================================================================
def max_profit_11(prices):
    """O(n^2) brute: try every (buy, sell) pair and recurse on remainder."""
    n = len(prices)
    if n < 2:
        return 0

    def best_from(start):
        """Max profit starting from `start`, given we're not holding."""
        if start >= n - 1:
            return 0
        best = 0
        # Try every (buy, sell) pair where sell > buy >= start.
        for buy in range(start, n - 1):
            for sell in range(buy + 1, n):
                profit = prices[sell] - prices[buy] + best_from(sell + 1)
                best = max(best, profit)
        return best

    return best_from(0)


# =============================================================================
# WAY 12: DP array (explicit states)
# =============================================================================
def max_profit_12(prices):
    """DP with arrays for hold and cash."""
    if not prices:
        return 0
    n = len(prices)
    cash = [0] * n
    hold = [0] * n
    hold[0] = -prices[0]
    for i in range(1, n):
        cash[i] = max(cash[i - 1], hold[i - 1] + prices[i])
        hold[i] = max(hold[i - 1], cash[i - 1] - prices[i])
    return cash[n - 1]


# =============================================================================
# WAY 13: Recursive with memoization
# =============================================================================
def max_profit_13(prices):
    """DFS + memo: at each day, decide buy/sell/rest."""
    from functools import lru_cache
    n = len(prices)
    if n < 2:
        return 0

    @lru_cache(maxsize=None)
    def dfs(i, holding):
        if i >= n:
            return 0
        # Option 1: do nothing.
        skip = dfs(i + 1, holding)
        if holding:
            # Option 2: sell today.
            sell = prices[i] + dfs(i + 1, False)
            return max(skip, sell)
        else:
            # Option 2: buy today.
            buy = -prices[i] + dfs(i + 1, True)
            return max(skip, buy)

    return dfs(0, False)


# =============================================================================
# WAY 14: Iterative with explicit state transitions
# =============================================================================
def max_profit_14(prices):
    """Track buy/sell decisions iteratively."""
    if not prices:
        return 0
    n = len(prices)
    # sell[i] = max profit if we end NOT holding on day i.
    # buy[i] = max profit if we end HOLDING on day i.
    sell = [0] * n
    buy = [0] * n
    buy[0] = -prices[0]
    for i in range(1, n):
        sell[i] = max(sell[i - 1], buy[i - 1] + prices[i])
        buy[i] = max(buy[i - 1], sell[i - 1] - prices[i])
    return sell[n - 1]


# =============================================================================
# WAY 15: Single variable accumulation (most concise)
# =============================================================================
def max_profit_15(prices):
    """Same as Way 1 but most concise."""
    profit = 0
    for i in range(len(prices) - 1):
        profit += max(0, prices[i + 1] - prices[i])
    return profit


# =============================================================================
# WAY 16: Use itertools.accumulate
# =============================================================================
def max_profit_16(prices):
    """Use accumulate just to demonstrate the library."""
    from itertools import accumulate
    diffs = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    pos_diffs = [max(0, d) for d in diffs]
    # accumulate yields running sums; take the last.
    return list(accumulate(pos_diffs))[-1] if pos_diffs else 0


# =============================================================================
# WAY 17: Math identity - monotonic subsequence sum
# =============================================================================
def max_profit_17(prices):
    """
    Same as Way 1 with explicit formula.
    sum of max(0, delta) where delta = prices[i] - prices[i-1].
    """
    return sum(max(0, b - a) for a, b in zip(prices, prices[1:]))


# =============================================================================
# WAY 18: Simulate transactions explicitly
# =============================================================================
def max_profit_18(prices):
    """Simulate buy/sell pairs explicitly."""
    profit = 0
    n = len(prices)
    i = 0
    while i < n - 1:
        # Find next upturn (buy point).
        while i < n - 1 and prices[i] >= prices[i + 1]:
            i += 1
        if i == n - 1:
            break
        buy = prices[i]
        # Find next downturn (sell point).
        while i < n - 1 and prices[i] <= prices[i + 1]:
            i += 1
        sell = prices[i]
        profit += sell - buy
    return profit


# =============================================================================
# WAY 19: Numpy vectorized
# =============================================================================
def max_profit_19(prices):
    """Use numpy for vectorized diff."""
    import numpy as np
    arr = np.array(prices)
    diffs = np.diff(arr)
    return int(np.maximum(diffs, 0).sum())


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def max_profit_20(prices):
    """
    THE ONE TO MEMORIZE.

    Greedy: every upward step contributes to profit.
    Sum of all positive (prices[i] - prices[i-1]) for i=1..n-1.

    Time:  O(n).
    Space: O(1).
    """
    profit = 0
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            profit += diff
    return profit


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"Find max profit with unlimited transactions, but only 1 share held."

Key Insight:
"Greedy: every upward step in price is profit we can capture.
Sum of all positive (prices[i] - prices[i-1]) for consecutive days."

Algorithm:
1. profit = 0.
2. For i in 1..n-1:
     if prices[i] > prices[i-1]:
       profit += prices[i] - prices[i-1].
3. Return profit.

Why Greedy is Optimal:
- Any uptrend (a < b < c) can be split into (a,b) + (b,c) = (b-a) + (c-b) = c-a.
- One transaction captures c-a profit.
- Multiple transactions capture same c-a but with more flexibility.
- So always capturing positive diffs is optimal.

Edge Cases:
- Empty: 0.
- Single price: 0.
- All decreasing: 0.
- All increasing: prices[-1] - prices[0].

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Greedy   | O(n)   | O(1)   |
| DP       | O(n)   | O(1)   |
| Brute    | O(n^2) | O(1)   |
+----------+--------+--------+

THE TRICK:
- "Up step = profit" captures every local gain.
- Sum of up steps = max profit.

ALTERNATE: DP with cash/hold states. Same complexity, more verbose.

RELATED:
- Stock I (LC 121): 1 transaction.
- Stock III (LC 123): 2 transactions.
- Stock with Cooldown (LC 309): add cooldown state.
- Stock with Fee (LC 714): subtract fee.
- Stock IV (LC 188): K transactions.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Greedy sum of positive diffs", max_profit_1),
        ("Way 2: Greedy with explicit delta", max_profit_2),
        ("Way 3: Peak-valley", max_profit_3),
        ("Way 4: DP cash/hold", max_profit_4),
        ("Way 5: One-pass prev", max_profit_5),
        ("Way 6: Sum with generator", max_profit_6),
        ("Way 7: Reduce", max_profit_7),
        ("Way 8: Class OOP", max_profit_8),
        ("Way 9: Zip", max_profit_9),
        ("Way 10: Sentinel", max_profit_10),
        ("Way 11: Brute O(n^2)", max_profit_11),
        ("Way 12: DP arrays", max_profit_12),
        ("Way 13: Recursive memo", max_profit_13),
        ("Way 14: Iterative states", max_profit_14),
        ("Way 15: Concise", max_profit_15),
        ("Way 16: Itertools", max_profit_16),
        ("Way 17: Math identity", max_profit_17),
        ("Way 18: Explicit sim", max_profit_18),
        ("Way 19: Numpy", max_profit_19),
        ("Way 20: Final cleanest", max_profit_20),
    ]

    test_cases = [
        # (prices, expected)
        ([7, 1, 5, 3, 6, 4], 7),
        ([1, 2, 3, 4, 5], 4),
        ([7, 6, 4, 3, 1], 0),
        ([1], 0),
        ([], 0),
        ([1, 2], 1),
        ([2, 1], 0),
        ([1, 5, 2, 8], 10),  # buy 1 sell 5 = 4, buy 2 sell 8 = 6, total 10
        ([3, 3, 3, 3], 0),
        ([1, 9, 2, 8, 3, 7], 18),  # (9-1)+(8-2)+(7-3) = 8+6+4 = 18
    ]

    print("=" * 70)
    print("BEST TIME TO BUY AND SELL STOCK II - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/best-time-to-buy-and-sell-stock-ii")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for prices, expected in test_cases:
            try:
                result = func(prices)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: prices={prices}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: prices={prices}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)