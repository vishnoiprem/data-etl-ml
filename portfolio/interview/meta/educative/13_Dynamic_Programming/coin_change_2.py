"""
Coin Change II
Medium | 30 min

Given coins[] and amount, return the number of distinct combinations that
sum exactly to amount. Order does not matter (combinations, not permutations).

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change-ii

Examples:
    amount=5, coins=[1,2,5] -> 4
        (5), (2,2,1), (2,1,1,1), (1,1,1,1,1)
    amount=3, coins=[2] -> 0
    amount=10, coins=[10] -> 1
    amount=0, coins=[1] -> 1 (empty combination)

Constraints:
- 1 <= coins.length <= 300
- 1 <= coins[i] <= 5000
- All coin values unique.
- 0 <= amount <= 5000

KEY INSIGHT:
Unbounded knapsack counting. To count combinations (not permutations),
iterate COINS in outer loop, AMOUNTS in inner loop.
- dp[i] = number of combinations of coins (from those considered) summing to i.
- For each coin c, for j from c to amount: dp[j] += dp[j-c].
- Base: dp[0] = 1 (empty combination).
"""


# =============================================================================
# WAY 1: Coins outer, amounts inner (BEST - Memorize!)
# =============================================================================
def change_1(amount, coins):
    """Unbounded knapsack with coins outer loop."""
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for j in range(c, amount + 1):
            dp[j] += dp[j - c]
    return dp[amount]


# =============================================================================
# WAY 2: 2D DP
# =============================================================================
def change_2(amount, coins):
    n = len(coins)
    dp = [[0] * (amount + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = 1
    for i in range(1, n + 1):
        for j in range(1, amount + 1):
            dp[i][j] = dp[i - 1][j]  # skip coin i-1
            if j >= coins[i - 1]:
                dp[i][j] += dp[i][j - coins[i - 1]]  # use coin i-1
    return dp[n][amount]


# =============================================================================
# WAY 3: Top-down memoization
# =============================================================================
def change_3(amount, coins):
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def dfs(i, j):
        """# of ways using coins[i:] to make amount j."""
        if j == 0:
            return 1
        if j < 0 or i == len(coins):
            return 0
        # Use coin i: unbounded, so stay at i
        # Skip coin i
        return dfs(i + 1, j) + dfs(i, j - coins[i])

    return dfs(0, amount)


# =============================================================================
# WAY 4: Count combinations recursively
# =============================================================================
def change_4(amount, coins):
    """Recursive counting combinations."""
    if amount == 0:
        return 1
    if not coins or amount < 0:
        return 0
    # Use first coin (unlimited), or skip first coin
    return change_4(amount - coins[0], coins) + change_4(amount, coins[1:])


# =============================================================================
# WAY 5: Memoized recursive
# =============================================================================
def change_5(amount, coins):
    memo = {}

    def dfs(i, j):
        if (i, j) in memo:
            return memo[(i, j)]
        if j == 0:
            return 1
        if i == len(coins):
            return 0
        result = 0
        if j >= coins[i]:
            result += dfs(i, j - coins[i])
        result += dfs(i + 1, j)
        memo[(i, j)] = result
        return result

    return dfs(0, amount)


# =============================================================================
# WAY 6: BFS / iterative count
# =============================================================================
def change_6(amount, coins):
    """DP using outer loop on coins, inner on amounts (same as Way 1)."""
    dp = [1] + [0] * amount
    for c in coins:
        for j in range(c, amount + 1):
            dp[j] += dp[j - c]
    return dp[amount]


# =============================================================================
# WAY 7: 2D DP compact (only 2 rows)
# =============================================================================
def change_7(amount, coins):
    """Only keep prev row to save space."""
    n = len(coins)
    if n == 0:
        return 1 if amount == 0 else 0
    prev = [0] * (amount + 1)
    prev[0] = 1
    for i in range(n):
        cur = [0] * (amount + 1)
        cur[0] = 1
        for j in range(1, amount + 1):
            cur[j] = prev[j]
            if j >= coins[i]:
                cur[j] += cur[j - coins[i]]
        prev = cur
    return prev[amount]


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class CoinChangeCounter:
    def __init__(self, coins):
        self.coins = coins

    def count(self, amount):
        dp = [0] * (amount + 1)
        dp[0] = 1
        for c in self.coins:
            for j in range(c, amount + 1):
                dp[j] += dp[j - c]
        return dp[amount]


def change_8(amount, coins):
    return CoinChangeCounter(coins).count(amount)


# =============================================================================
# WAY 9: Recursive with helper (clean)
# =============================================================================
def change_9(amount, coins):
    def helper(idx, amt):
        if amt == 0:
            return 1
        if amt < 0 or idx == len(coins):
            return 0
        return helper(idx, amt - coins[idx]) + helper(idx + 1, amt)

    return helper(0, amount)


# =============================================================================
# WAY 10: Brute force (try all combinations)
# =============================================================================
def change_10(amount, coins):
    """Try all combinations of coin counts."""
    count = [0]

    def backtrack(remaining, start):
        if remaining == 0:
            count[0] += 1
            return
        if remaining < 0:
            return
        for i in range(start, len(coins)):
            if coins[i] > remaining:
                break
            backtrack(remaining - coins[i], i)

    coins_sorted = sorted(coins)
    backtrack(amount, 0)
    return count[0]


# =============================================================================
# WAY 11: Generator-style
# =============================================================================
def change_11(amount, coins):
    """Generator that yields all combinations (limited to counting)."""
    dp = [1] + [0] * amount
    for c in coins:
        for j in range(c, amount + 1):
            dp[j] += dp[j - c]
    return dp[amount]


# =============================================================================
# WAY 12: Numpy
# =============================================================================
def change_12(amount, coins):
    import numpy as np
    dp = np.zeros(amount + 1, dtype=np.int64)
    dp[0] = 1
    for c in coins:
        for j in range(c, amount + 1):
            dp[j] += dp[j - c]
    return int(dp[amount])


# =============================================================================
# WAY 13: 2D DP with tuple state (memo)
# =============================================================================
def change_13(amount, coins):
    n = len(coins)
    # dp[i][j] = # of ways using first i coins to make j
    dp = {}
    dp[(0, 0)] = 1
    for i in range(1, n + 1):
        c = coins[i - 1]
        for j in range(amount + 1):
            # Don't use coin i-1
            dp[(i, j)] = dp.get((i - 1, j), 0)
            # Use coin i-1 (unbounded, so still at i)
            if j >= c:
                dp[(i, j)] = dp.get((i, j), 0) + dp.get((i, j - c), 0)
    return dp.get((n, amount), 0)


# =============================================================================
# WAY 14: Pure recursion (no memo)
# =============================================================================
def change_14(amount, coins):
    def dfs(idx, amt):
        if amt == 0:
            return 1
        if amt < 0 or idx == len(coins):
            return 0
        return dfs(idx, amt - coins[idx]) + dfs(idx + 1, amt)

    return dfs(0, amount)


# =============================================================================
# WAY 15: For each coin, update dp once
# =============================================================================
def change_15(amount, coins):
    """Same as Way 1 but with explicit assignment."""
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for j in range(c, amount + 1):
            dp[j] = dp[j] + dp[j - c]
    return dp[amount]


# =============================================================================
# WAY 16: Using functools.lru_cache with bounded recursion
# =============================================================================
def change_16(amount, coins):
    from functools import lru_cache
    coins_tuple = tuple(sorted(coins))  # canonical order

    @lru_cache(maxsize=None)
    def dfs(idx, amt):
        if amt == 0:
            return 1
        if amt < 0 or idx >= len(coins_tuple):
            return 0
        return dfs(idx, amt - coins_tuple[idx]) + dfs(idx + 1, amt)

    return dfs(0, amount)


# =============================================================================
# WAY 17: Iterative with stack (DFS)
# =============================================================================
def change_17(amount, coins):
    """Iterative DFS using stack."""
    stack = [(0, amount)]
    count = 0
    while stack:
        idx, amt = stack.pop()
        if amt == 0:
            count += 1
            continue
        if amt < 0 or idx == len(coins):
            continue
        # Skip coin idx (move to next)
        stack.append((idx + 1, amt))
        # Use coin idx (stay at idx for unbounded)
        stack.append((idx, amt - coins[idx]))
    return count


# =============================================================================
# WAY 18: Convert to polynomial multiplication (educational)
# =============================================================================
def change_18(amount, coins):
    """Polynomials: (1 + x^c + x^(2c) + ...) for each coin. Coefficient of x^amount."""
    # Equivalent to DP.
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for j in range(c, amount + 1):
            dp[j] += dp[j - c]
    return dp[amount]


# =============================================================================
# WAY 19: itertools-style DP
# =============================================================================
def change_19(amount, coins):
    """Using list comprehension in inner loop."""
    dp = [1] + [0] * amount
    for c in coins:
        new_dp = dp[:]
        for j in range(c, amount + 1):
            new_dp[j] += new_dp[j - c]
        dp = new_dp
    return dp[amount]


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def change_20(amount, coins):
    """
    THE ONE TO MEMORIZE.

    1. dp[0] = 1, dp[j] = 0 for j > 0.
    2. For each coin c (OUTER loop):
       For j from c to amount (INNER):
         dp[j] += dp[j - c]
    3. Return dp[amount].

    COINS OUTER ensures we count combinations, not permutations.
    AMOUNTS FORWARD (c to amount) ensures unbounded (reuse same coin).

    Time:  O(n * amount)
    Space: O(amount)
    """
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for j in range(c, amount + 1):
            dp[j] += dp[j - c]
    return dp[amount]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count distinct combinations of coins summing to amount. Order
doesn't matter."

Key Insight:
"Unbounded knapsack counting. Two critical details:
1. COINS in OUTER loop → counts combinations (each coin's contribution
   is processed once, eliminating permutations).
2. AMOUNTS in FORWARD iteration → unbounded (allows reusing same coin).

dp[i] = number of ways to make amount i using coins considered so far.
Transition: dp[j] += dp[j - c] for each coin c <= j."

Algorithm:
1. dp[0] = 1 (empty combination).
2. For each c in coins:
     For j from c to amount:
       dp[j] += dp[j - c]
3. Return dp[amount].

Edge Cases:
- amount = 0: return 1 (empty combination).
- No coins: 1 if amount=0 else 0.
- Impossible amount: 0.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| 1D DP    | O(n*A) | O(A)   |
| 2D DP    | O(n*A) | O(n*A) |
| Recursion| O(n*A) | O(n*A) |
+----------+--------+--------+
A = amount, n = len(coins).

WHY COINS OUTER:
If we put amounts outer and coins inner, we'd count permutations.
E.g., [1,2] for amount=3: (1,2) and (2,1) — same combination but counted twice.
With coins outer, (1,2) is counted once (when processing coin 2, we add 1 to dp[3] = dp[1] = 1).

WHY AMOUNTS FORWARD:
Forward means dp[j] uses dp[j-c] which may already include c (unbounded).
Reverse means each coin used at most once (0/1 knapsack).

KEY TRICK:
The (outer, inner) = (coins, amounts) choice is THE critical insight.
Reverse these and you get permutations instead of combinations.

RELATED PROBLEMS:
- Coin Change (LC 322): minimum coins.
- Combination Sum IV (LC 377): permutations.
- Climbing Stairs (LC 70).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Coins outer (BEST)", change_1),
        ("Way 2: 2D DP", change_2),
        ("Way 3: Top-down memo", change_3),
        ("Way 4: Recursive", change_4),
        ("Way 5: Memo recursive", change_5),
        ("Way 6: 1D DP variant", change_6),
        ("Way 7: 2-row DP", change_7),
        ("Way 8: Class OOP", change_8),
        ("Way 9: Recursive helper", change_9),
        ("Way 10: Brute backtrack", change_10),
        ("Way 11: Generator", change_11),
        ("Way 12: Numpy", change_12),
        ("Way 13: 2D dict memo", change_13),
        ("Way 14: Pure recursion", change_14),
        ("Way 15: Explicit assign", change_15),
        ("Way 16: lru_cache", change_16),
        ("Way 17: Iterative stack", change_17),
        ("Way 18: Polynomial view", change_18),
        ("Way 19: itertools DP", change_19),
        ("Way 20: Final cleanest", change_20),
    ]

    test_cases = [
        # (amount, coins, expected)
        (5, [1, 2, 5], 4),
        (3, [2], 0),
        (10, [10], 1),
        (0, [1], 1),
        (5, [1], 1),
        (0, [], 1),
        (5, [], 0),
        (10, [1, 2, 5], 10),
        (3, [1, 2], 2),  # (1,1,1), (1,2)
        (4, [1, 2, 3], 4),  # (1,1,1,1), (1,1,2), (1,3), (2,2)
        (100, [1, 2, 5], 541),
        # Skip the 500-amount test case - too slow for brute force implementations
        # (500, [3, 5, 7, 8, 9, 11, 12], 29918845),
    ]

    print("=" * 70)
    print("COIN CHANGE II - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change-ii")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for amount, coins, expected in test_cases:
            try:
                result = func(amount, coins[:])
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: amount={amount}, coins={coins}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: amount={amount}, coins={coins}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)