"""
Best Time to Buy and Sell Stock III
Hard | 40 min

Given an array prices where prices[i] is the stock price on day i, find
the maximum profit achievable with AT MOST TWO transactions.

Each transaction = buy + sell. Sell before next buy. Hold at most one
stock at a time.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/best-time-to-buy-and-sell-stock-iii

Examples:
    prices=[3,3,5,0,0,3,1,4] -> 6 (buy 0, sell 4 -> 4; buy 1, sell 4 -> 3)
    prices=[1,2,3,4,5]      -> 4 (one transaction: buy 1 sell 5)
    prices=[7,6,4,3,1]      -> 0 (no transaction)
    prices=[1]              -> 0
    prices=[]               -> 0

Constraints:
- 1 <= prices.length <= 10^5
- 0 <= prices[i] <= 10^5

KEY INSIGHT:
Three approaches (pick any):
1. Split point: max(L[i] + R[i]) where L[i]=max profit in [0..i] using
   one tx, R[i]=max profit in [i..n-1] using one tx.
2. State DP: 4 states (no stock 1st tx, stock 1st tx, no stock 2nd tx,
   stock 2nd tx).
3. K transactions generalized: maintain k=2 buy/sell states.
"""


# =============================================================================
# WAY 1: State DP - 4 states (BEST - Memorize!)
# =============================================================================
def max_profit_iii_1(prices):
    """
    State DP. Track 4 states after each day:
      s1 = max profit with stock #1 (bought 1st time) - negative cost
      s2 = max profit after selling stock #1
      s3 = max profit with stock #2 (after selling #1)
      s4 = max profit after selling stock #2 (final answer)
    """
    if not prices:
        return 0
    s1 = -prices[0]  # buy on day 0
    s2 = 0            # do nothing (sell at day 0 break-even; we keep 0)
    s3 = -prices[0]  # already bought 2nd (using best of s2+buy)
    s4 = 0
    for p in prices[1:]:
        s1 = max(s1, -p)                # bought 1st; could buy at -p
        s2 = max(s2, s1 + p)            # sold 1st; bought + sold today
        s3 = max(s3, s2 - p)            # bought 2nd after selling 1st
        s4 = max(s4, s3 + p)            # sold 2nd; final answer
    return s4


# =============================================================================
# WAY 2: Split point - left[] and right[] arrays
# =============================================================================
def max_profit_iii_2(prices):
    """
    Split point: for each i, profit = L[i] (best one-tx profit in [0..i])
                                  + R[i] (best one-tx profit in [i..n-1]).
    Answer = max over i of L[i] + R[i].
    """
    n = len(prices)
    if n < 2:
        return 0
    # L[i]: max profit for one tx ending at or before day i.
    L = [0] * n
    min_price = prices[0]
    for i in range(1, n):
        min_price = min(min_price, prices[i])
        L[i] = max(L[i - 1], prices[i] - min_price)
    # R[i]: max profit for one tx starting at or after day i.
    R = [0] * n
    max_price = prices[-1]
    for i in range(n - 2, -1, -1):
        max_price = max(max_price, prices[i])
        R[i] = max(R[i + 1], max_price - prices[i])
    # Best split
    return max(L[i] + R[i] for i in range(n))


# =============================================================================
# WAY 3: Generalized k=2 transactions
# =============================================================================
def max_profit_iii_3(prices):
    """Generalized: k=2 transactions, maintain buy[i], sell[i]."""
    if not prices:
        return 0
    K = 2  # at most 2 transactions
    n = len(prices)
    # kth buy/sell states
    buy = [-prices[0]] * (K + 1)   # bought k times, holding
    sell = [0] * (K + 1)           # sold k times, not holding
    for p in prices[1:]:
        for k in range(1, K + 1):
            # sell kth: either sold (k-1) before or just sold now
            sell[k] = max(sell[k], buy[k] + p)
            # buy kth: either bought (k-1) and now buying again, or first buy
            buy[k] = max(buy[k], (sell[k - 1] if k > 1 else 0) - p)
    return sell[K]


# =============================================================================
# WAY 4: Top-down memo on (i, transactions_done, holding)
# =============================================================================
def max_profit_iii_4(prices):
    """DFS + memo: state = (i, t, h). t=tx done, h=holding."""
    from functools import lru_cache
    n = len(prices)
    if n < 2:
        return 0

    @lru_cache(maxsize=None)
    def dfs(i, t, h):
        if i == n or t == 2:
            return 0
        # Skip
        ans = dfs(i + 1, t, h)
        if h == 0:
            # Buy
            ans = max(ans, dfs(i + 1, t, 1) - prices[i])
        else:
            # Sell
            ans = max(ans, dfs(i + 1, t + 1, 0) + prices[i])
        return ans

    return dfs(0, 0, 0)


# =============================================================================
# WAY 5: Forward + Backward single pass
# =============================================================================
def max_profit_iii_5(prices):
    """Combine two single-tx passes: forward and backward."""
    n = len(prices)
    if n < 2:
        return 0
    # Forward: max profit for one tx ending at or before i.
    left = [0] * n
    lo = prices[0]
    for i in range(1, n):
        lo = min(lo, prices[i])
        left[i] = max(left[i - 1], prices[i] - lo)
    # Backward + combine in one pass.
    best = 0
    hi = prices[-1]
    right = 0
    for i in range(n - 1, -1, -1):
        hi = max(hi, prices[i])
        right = max(right, hi - prices[i])
        best = max(best, left[i] + right)
    return best


# =============================================================================
# WAY 6: DP table - 2D dp[k][d]
# =============================================================================
def max_profit_iii_6(prices):
    """dp[t][d] = max profit with at most t transactions by day d."""
    if not prices:
        return 0
    K = 2
    n = len(prices)
    # dp[t][d]
    dp = [[0] * n for _ in range(K + 1)]
    for t in range(1, K + 1):
        # best = max over j < d of dp[t-1][j] - prices[j]
        best = -prices[0]
        for d in range(1, n):
            # Either don't sell today, or sell today.
            dp[t][d] = max(dp[t][d - 1], prices[d] + best)
            # Update best: either keep best or use dp[t-1][d] - prices[d]
            best = max(best, dp[t - 1][d] - prices[d])
    return dp[K][n - 1]


# =============================================================================
# WAY 7: Space-optimized DP (rolling 2-row)
# =============================================================================
def max_profit_iii_7(prices):
    """Only keep 2 rows of dp."""
    if not prices:
        return 0
    K = 2
    n = len(prices)
    prev = [0] * n
    cur = [0] * n
    for t in range(1, K + 1):
        best = -prices[0]
        for d in range(1, n):
            cur[d] = max(cur[d - 1], prices[d] + best)
            best = max(best, prev[d] - prices[d])
        prev, cur = cur, [0] * n
    return prev[n - 1]


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class MaxProfitFinder:
    def __init__(self, prices):
        self.prices = prices

    def solve_state_dp(self):
        """4-state DP."""
        if not self.prices:
            return 0
        s1 = -self.prices[0]
        s2 = s3 = s4 = 0
        s3 = -self.prices[0]
        for p in self.prices[1:]:
            s1 = max(s1, -p)
            s2 = max(s2, s1 + p)
            s3 = max(s3, s2 - p)
            s4 = max(s4, s3 + p)
        return s4

    def solve_split(self):
        """Split-point method."""
        return max_profit_iii_2(self.prices)


def max_profit_iii_8(prices):
    return MaxProfitFinder(prices).solve_state_dp()


# =============================================================================
# WAY 9: Min/Max tracked in one pass (single transaction, then second)
# =============================================================================
def max_profit_iii_9(prices):
    """
    Find best two transactions in one conceptual pass by tracking min so far
    twice. Implementation: left[] array then combine.
    """
    return max_profit_iii_2(prices)


# =============================================================================
# WAY 10: Two single-tx sweeps
# =============================================================================
def max_profit_iii_10(prices):
    """
    Two transactions -> split at every point.
    First sweep: best single tx profit ending at each day.
    Second sweep: best single tx profit starting at each day.
    Sum and max.
    """
    n = len(prices)
    if n < 2:
        return 0
    left = [0] * n
    lo = prices[0]
    for i in range(1, n):
        lo = min(lo, prices[i])
        left[i] = max(left[i - 1], prices[i] - lo)
    ans = left[-1]  # in case 2nd tx is unused
    hi = prices[-1]
    right = 0
    for i in range(n - 2, -1, -1):
        hi = max(hi, prices[i])
        right = max(right, hi - prices[i])
        ans = max(ans, left[i] + right)
    return ans


# =============================================================================
# WAY 11: 1D DP with k=2 implicit
# =============================================================================
def max_profit_iii_11(prices):
    """Same as Way 3 but flattened."""
    if not prices:
        return 0
    b1 = b2 = -prices[0]
    s1 = s2 = 0
    for p in prices[1:]:
        b1 = max(b1, -p)
        s1 = max(s1, b1 + p)
        b2 = max(b2, s1 - p)
        s2 = max(s2, b2 + p)
    return s2


# =============================================================================
# WAY 12: Memo dict (3D state)
# =============================================================================
def max_profit_iii_12(prices):
    """Top-down memo with explicit dict."""
    n = len(prices)
    memo = {}

    def dfs(i, t, h):
        if (i, t, h) in memo:
            return memo[(i, t, h)]
        if i == n or t == 2:
            return 0
        ans = dfs(i + 1, t, h)
        if h == 0:
            ans = max(ans, dfs(i + 1, t, 1) - prices[i])
        else:
            ans = max(ans, dfs(i + 1, t + 1, 0) + prices[i])
        memo[(i, t, h)] = ans
        return ans

    return dfs(0, 0, 0)


# =============================================================================
# WAY 13: Brute force - try all split points
# =============================================================================
def max_profit_iii_13(prices):
    """Try all pairs of (sell1, buy2) split points."""
    n = len(prices)
    if n < 2:
        return 0
    best = 0
    for i in range(n):
        # First transaction in [0..i]
        if i >= 1:
            mn = prices[0]
            mx = prices[0]
            for j in range(i + 1):
                mn = min(mn, prices[j])
                mx = max(mx, prices[j])
            first = mx - mn
        else:
            first = 0
        # Second transaction in [i..n-1]
        if i < n - 1:
            mn2 = prices[i]
            mx2 = prices[i]
            for j in range(i, n):
                mn2 = min(mn2, prices[j])
                mx2 = max(mx2, prices[j])
            second = mx2 - mn2
        else:
            second = 0
        best = max(best, first + second)
    return best


# =============================================================================
# WAY 14: Numpy vectorized
# =============================================================================
def max_profit_iii_14(prices):
    """Vectorized split-point DP."""
    import numpy as np
    arr = np.array(prices, dtype=np.int64)
    if arr.size < 2:
        return 0
    n = arr.size
    # Left: best 1-tx profit ending at or before i
    left = np.zeros(n, dtype=np.int64)
    cmin = arr[0]
    for i in range(1, n):
        cmin = min(cmin, arr[i])
        left[i] = max(left[i - 1], arr[i] - cmin)
    # Right: best 1-tx profit starting at or after i
    right = np.zeros(n, dtype=np.int64)
    cmax = arr[-1]
    for i in range(n - 2, -1, -1):
        cmax = max(cmax, arr[i])
        right[i] = max(right[i + 1], cmax - arr[i])
    return int(max(left + right))


# =============================================================================
# WAY 15: Three-array split (left, right, max)
# =============================================================================
def max_profit_iii_15(prices):
    """
    left[i] = max 1-tx profit in [0..i]
    right[i] = max 1-tx profit in [i..n-1]
    ans = max(left[i] + right[i])
    """
    n = len(prices)
    if n < 2:
        return 0
    left = [0] * n
    cmin = prices[0]
    for i in range(1, n):
        cmin = min(cmin, prices[i])
        left[i] = max(left[i - 1], prices[i] - cmin)
    right = [0] * n
    cmax = prices[-1]
    for i in range(n - 2, -1, -1):
        cmax = max(cmax, prices[i])
        right[i] = max(right[i + 1], cmax - prices[i])
    return max(left[i] + right[i] for i in range(n))


# =============================================================================
# WAY 16: Helper recursive (3-arg)
# =============================================================================
def max_profit_iii_16(prices):
    """Recursive helper, no memo."""
    n = len(prices)
    if n < 2:
        return 0
    best = 0

    def helper(i, t, h):
        nonlocal best
        if i == n or t == 2:
            return 0
        skip = helper(i + 1, t, h)
        if h == 0:
            action = helper(i + 1, t, 1) - prices[i]
        else:
            action = helper(i + 1, t + 1, 0) + prices[i]
        return max(skip, action)

    return helper(0, 0, 0)


# =============================================================================
# WAY 17: Iterative state machine with k=2
# =============================================================================
def max_profit_iii_17(prices):
    """Same as Way 11 (1D), with even more explicit names."""
    if not prices:
        return 0
    INF = float("inf")
    # State: after 1st buy, after 1st sell, after 2nd buy, after 2nd sell
    buy1 = buy2 = -INF
    sell1 = sell2 = 0
    for p in prices:
        buy1 = max(buy1, -p)
        sell1 = max(sell1, buy1 + p)
        buy2 = max(buy2, sell1 - p)
        sell2 = max(sell2, buy2 + p)
    return sell2


# =============================================================================
# WAY 18: DP using 'best so far' formula (LC classic)
# =============================================================================
def max_profit_iii_18(prices):
    """
    LC solution: maintain 'best' for each transaction count.
    dp[t][d] = max(dp[t][d-1], prices[d] + best[t-1])
    best[t-1] = max(best[t-1], dp[t-1][d] - prices[d])
    """
    if not prices:
        return 0
    K = 2
    n = len(prices)
    dp = [[0] * n for _ in range(K + 1)]
    for t in range(1, K + 1):
        best = -prices[0]
        for d in range(1, n):
            dp[t][d] = max(dp[t][d - 1], prices[d] + best)
            best = max(best, dp[t - 1][d] - prices[d])
    return dp[K][n - 1]


# =============================================================================
# WAY 19: Pure recursive (no memo) - exponential
# =============================================================================
def max_profit_iii_19(prices):
    """Brute recursion. Exponential. Only for very small n."""

    def helper(i, t, h):
        if i == len(prices) or t == 2:
            return 0
        skip = helper(i + 1, t, h)
        if h == 0:
            return max(skip, helper(i + 1, t, 1) - prices[i])
        return max(skip, helper(i + 1, t + 1, 0) + prices[i])

    return helper(0, 0, 0)


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def max_profit_iii_20(prices):
    """
    THE ONE TO MEMORIZE.

    State DP with 4 variables updated each day:
      buy1  = max profit with 1st stock held (after 1st buy)
      sell1 = max profit after selling 1st stock
      buy2  = max profit with 2nd stock held (after selling 1st)
      sell2 = max profit after selling 2nd stock  <- ANSWER

    Transitions (each day, in order):
      buy1  = max(buy1,  -p)             # buy 1st at p
      sell1 = max(sell1, buy1 + p)       # sell 1st at p
      buy2  = max(buy2,  sell1 - p)      # buy 2nd at p
      sell2 = max(sell2, buy2 + p)       # sell 2nd at p

    Time:  O(n)
    Space: O(1)
    """
    if not prices:
        return 0
    buy1 = sell1 = buy2 = sell2 = 0
    buy1 = -prices[0]
    for p in prices[1:]:
        buy1 = max(buy1, -p)
        sell1 = max(sell1, buy1 + p)
        buy2 = max(buy2, sell1 - p)
        sell2 = max(sell2, buy2 + p)
    return sell2


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need max profit with at most two buy-sell transactions. Each tx is buy
then sell, and we can hold at most one stock at a time."

Key Insight 1 - State DP (preferred):
"Track 4 states per day:
- buy1:  max profit while holding stock #1 (just bought or held)
- sell1: max profit after selling stock #1 (done with 1st tx)
- buy2:  max profit while holding stock #2
- sell2: max profit after selling stock #2 [ANSWER]

Each day update in order:
  buy1  = max(buy1, -p)
  sell1 = max(sell1, buy1 + p)
  buy2  = max(buy2, sell1 - p)
  sell2 = max(sell2, buy2 + p)"

Key Insight 2 - Split Point (alternative):
"For each split day i, total profit = best one-tx profit in [0..i] +
best one-tx profit in [i..n-1]. Compute both in O(n) and combine."

Edge Cases:
- Empty / single: 0.
- Monotonically decreasing: 0 (no tx).
- One rising then falling: 1 tx profit.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| State DP | O(n)   | O(1)   |
| Split DP | O(n)   | O(n)   |
| K-tx DP  | O(n*K) | O(n*K) |
| Brute    | O(n^2) | O(1)   |
+----------+--------+--------+

THE TRICK: 4-state machine updates in-place. sell2 holds final answer.

RELATED PROBLEMS:
- Stock I (LC 121): one tx. K=1 case.
- Stock II (LC 122): unlimited tx. Different problem.
- Stock IV (LC 188): at most K tx. K=2 is this.
- Stock with cooldown (LC 309), with fee (LC 714).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: State DP (BEST)", max_profit_iii_1),
        ("Way 2: Split point", max_profit_iii_2),
        ("Way 3: K=2 generalized", max_profit_iii_3),
        ("Way 4: Top-down memo", max_profit_iii_4),
        ("Way 5: Forward+backward", max_profit_iii_5),
        ("Way 6: 2D DP", max_profit_iii_6),
        ("Way 7: Rolling 2-row", max_profit_iii_7),
        ("Way 8: Class OOP", max_profit_iii_8),
        ("Way 9: Min/Max tracked", max_profit_iii_9),
        ("Way 10: Two sweeps", max_profit_iii_10),
        ("Way 11: 1D K=2", max_profit_iii_11),
        ("Way 12: Memo dict", max_profit_iii_12),
        ("Way 13: Brute split", max_profit_iii_13),
        ("Way 14: Numpy", max_profit_iii_14),
        ("Way 15: Split arrays", max_profit_iii_15),
        ("Way 16: Recursive no memo", max_profit_iii_16),
        ("Way 17: Iter state machine", max_profit_iii_17),
        ("Way 18: Best so far", max_profit_iii_18),
        ("Way 19: Pure recursive", max_profit_iii_19),
        ("Way 20: Final cleanest", max_profit_iii_20),
    ]

    test_cases = [
        # (prices, expected)
        ([3, 3, 5, 0, 0, 3, 1, 4], 6),
        ([1, 2, 3, 4, 5], 4),
        ([7, 6, 4, 3, 1], 0),
        ([1], 0),
        ([], 0),
        ([1, 5, 2, 8], 10),  # (5-1) + (8-2)
        ([0, 0, 0, 0], 0),
        ([2, 1, 4, 5, 2, 9, 7], 11),  # buy 1 sell 5 -> 4; buy 2 sell 9 -> 7
        ([3, 2, 6, 5, 0, 3], 7),  # (6-2)=4 + (3-0)=3
        ([1, 2, 4, 2, 5, 7, 2, 4, 8, 9], 13),  # (7-1)=6 + (9-2)=7
    ]

    print("=" * 70)
    print("BEST TIME TO BUY AND SELL STOCK III - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/best-time-to-buy-and-sell-stock-iii")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for prices, expected in test_cases:
            try:
                result = func(prices[:])
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
