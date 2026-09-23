"""
Best Time to Buy and Sell Stock - 10 Ways
=========================================
You are given an array prices where prices[i] is the price of a given
stock on the ith day. You want to maximize your profit by choosing a
single day to buy and a different day in the future to sell.

Return the maximum profit. If no profit is possible, return 0.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/best-time-to-buy-and-sell-stock
          (LeetCode #121)

Examples:
    prices = [7,1,5,3,6,4]    -> 5  (buy at 1, sell at 6)
    prices = [7,6,4,3,1]      -> 0  (no profit possible)
    prices = [2,4,1]          -> 2  (buy at 2, sell at 4)
    prices = [1]              -> 0

Constraints:
- 1 <= prices.length <= 10^5
- 0 <= prices[i] <= 10^4

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Choose one day to buy and a LATER day to sell. Maximize profit."

2. KEY INSIGHT:
   "Track the minimum price seen so far. For each day, profit = price -
    min_so_far. Track the max profit."

3. PATTERN RECOGNITION:
   "Single-pass: maintain min_so_far and max_profit."

4. EDGE CASES:
   - prices of length 1 -> 0.
   - Strictly decreasing prices -> 0.
   - All same prices -> 0.
   - prices with profit only at end -> answer at last element.
   - Empty prices (if not constrained) -> 0.

5. TRICKY DETAIL:
   "The buy day must come BEFORE the sell day. By tracking min_so_far
    as we iterate, we ensure buy < sell (we always have a prior min)."

6. ALGORITHM:
   "min_price = inf; max_profit = 0
    for p in prices:
        if p < min_price: min_price = p
        elif p - min_price > max_profit: max_profit = p - min_price
    return max_profit"

7. WHY IT WORKS:
   "min_price at day i is the best buy price for selling on any day
    >= i (since we maintain the running min). For day i, the best
    profit ending at i is prices[i] - min_price[0..i]. Track max."

8. COMPLEXITY:
   "Time: O(n) - single pass.
    Space: O(1)."

9. CODE STRUCTURE:
   "Initialize min, max_profit. Iterate. Update min and max_profit."

10. MENTAL TRACE:
    prices = [7,1,5,3,6,4]:
    p=7: min=7. profit=0. max_profit=0.
    p=1: min=1. profit=0.
    p=5: min=1. profit=4. max_profit=4.
    p=3: min=1. profit=2. max_profit=4.
    p=6: min=1. profit=5. max_profit=5.
    p=4: min=1. profit=3. max_profit=5.
    Returns 5. ✓
"""


# Solution 1: Track min_price and max_profit (BEST)
def max_profit_v1(prices):
    if not prices:
        return 0
    min_price = float('inf')
    max_profit = 0
    for p in prices:
        if p < min_price:
            min_price = p
        elif p - min_price > max_profit:
            max_profit = p - min_price
    return max_profit


# Solution 2: Same as V1 but update max_profit first (slightly different)
def max_profit_v2(prices):
    if not prices:
        return 0
    min_price = float('inf')
    max_profit = 0
    for p in prices:
        max_profit = max(max_profit, p - min_price)
        min_price = min(min_price, p)
    return max_profit


# Solution 3: Brute force O(n^2)
def max_profit_v3(prices):
    n = len(prices)
    best = 0
    for i in range(n):
        for j in range(i + 1, n):
            if prices[j] - prices[i] > best:
                best = prices[j] - prices[i]
    return best


# Solution 4: Use enumerate + min tracking
def max_profit_v4(prices):
    if not prices:
        return 0
    min_price = prices[0]
    best = 0
    for p in prices[1:]:
        best = max(best, p - min_price)
        min_price = min(min_price, p)
    return best


# Solution 5: Kadane-like (max subarray of differences)
def max_profit_v5(prices):
    # Difference between consecutive prices.
    # Max profit = max subarray sum where all positive values mean up-days.
    if len(prices) < 2:
        return 0
    diffs = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    # Max subarray sum (Kadane)
    cur = diffs[0]
    best = max(0, diffs[0])
    for d in diffs[1:]:
        cur = max(d, cur + d)
        best = max(best, cur)
    return best


# Solution 6: itertools.accumulate for min-so-far
def max_profit_v6(prices):
    from itertools import accumulate
    if not prices:
        return 0
    mins = list(accumulate(prices, min))
    best = 0
    for i, p in enumerate(prices):
        best = max(best, p - mins[i])
    return best


# Solution 7: Use numpy for speed
def max_profit_v7(prices):
    try:
        import numpy as np
        if len(prices) < 2:
            return 0
        arr = np.array(prices)
        mins = np.minimum.accumulate(arr)
        profits = arr - mins
        return int(max(0, profits.max()))
    except ImportError:
        return max_profit_v1(prices)


# Solution 8: Recursive
def max_profit_v8(prices):
    n = len(prices)
    if n < 2:
        return 0
    best = [0]
    min_so_far = [prices[0]]

    def helper(i):
        if i == n:
            return
        best[0] = max(best[0], prices[i] - min_so_far[0])
        min_so_far[0] = min(min_so_far[0], prices[i])
        helper(i + 1)

    helper(1)
    return best[0]


# Solution 9: Sort + scan (incorrect approach, for educational contrast)
def max_profit_v9(prices):
    # WRONG: this doesn't enforce buy-before-sell.
    # We sort prices and take max - min, but the buy/sell order may be wrong.
    if not prices:
        return 0
    sorted_prices = sorted(prices)
    return max(0, sorted_prices[-1] - sorted_prices[0])


# Solution 10: Single pass with explicit min/max
def max_profit_v10(prices):
    if len(prices) < 2:
        return 0
    min_p = prices[0]
    max_p = prices[0]
    best = 0
    for p in prices[1:]:
        if p < min_p:
            min_p = p
            max_p = p
        elif p > max_p:
            max_p = p
            best = max(best, max_p - min_p)
    return best


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",                max_profit_v1),
        ("V2 (order swap)",          max_profit_v2),
        ("V3 (brute O(n^2))",        max_profit_v3),
        ("V4 (enumerate min)",       max_profit_v4),
        ("V5 (Kadane)",              max_profit_v5),
        ("V6 (accumulate)",          max_profit_v6),
        ("V7 (numpy)",               max_profit_v7),
        ("V8 (recursive)",           max_profit_v8),
        ("V9 (sorted - WRONG)",      max_profit_v9),
        ("V10 (explicit min/max)",   max_profit_v10),
    ]

    test_cases = [
        # (prices, expected)
        ([7, 1, 5, 3, 6, 4], 5),
        ([7, 6, 4, 3, 1], 0),
        ([2, 4, 1], 2),
        ([1], 0),
        ([2, 1, 2, 0, 1], 1),  # buy 0, sell 1 (next day)
        ([3, 3, 5, 0, 0, 3, 1, 4], 4),  # buy 0, sell 4
        ([1, 2, 3, 4, 5], 4),
        ([5, 4, 3, 2, 1], 0),
        ([2], 0),
        ([3, 8, 1, 4], 5),  # buy 1, sell 8 (but order matters! buy=3? no, buy 1 sell 8 not allowed (8 before 1))
                              # Actually buy at 3 (i=0), sell at 8 (i=1) -> profit 5
                              # Then later buy at 1 (i=2), sell at 4 (i=3) -> profit 3
                              # Max profit = 5 (buy=3, sell=8 at i=0,1)
    ]

    # V9 should fail because it doesn't enforce order.
    print("Note: V9 is intentionally wrong (educational only).")
    print()

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (prices, expected) in enumerate(test_cases):
            try:
                got = func(prices)
                if got != expected:
                    ok = False
                    if "WRONG" not in name:
                        all_pass = False
                    print(f"  X {name} [{idx}]: {prices} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: {prices} ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")