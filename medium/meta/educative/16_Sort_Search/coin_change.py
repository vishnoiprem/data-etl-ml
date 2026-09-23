"""
Coin Change
Medium | 30 min

Given coins[] (denominations) and amount, return the FEWEST number of
coins needed to make up amount. Return -1 if impossible.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change

Examples:
    coins=[1,5,10,25], amount=11 -> 3 (10+1)
    coins=[2], amount=3 -> -1
    coins=[1], amount=0 -> 0
    coins=[1,2,5], amount=11 -> 3 (5+5+1)

Constraints:
- 1 <= coins.length <= 12
- 1 <= coins[i] <= 2^31 - 1
- 0 <= amount <= 10^4

KEY INSIGHT: DP. dp[i] = min coins to make amount i.
  dp[i] = min(dp[i - c] for c in coins if i >= c) + 1
  Base: dp[0] = 0.
"""


# =============================================================================
# WAY 1: Bottom-up DP (BEST - Memorize!)
# =============================================================================
def coin_change_1(coins, amount):
    """dp[i] = min coins to make amount i."""
    if amount == 0:
        return 0
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in coins:
            if i >= c and dp[i - c] != float('inf'):
                dp[i] = min(dp[i], dp[i - c] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1


# =============================================================================
# WAY 2: Top-down memoization
# =============================================================================
def coin_change_2(coins, amount):
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def helper(rem):
        if rem == 0:
            return 0
        if rem < 0:
            return float('inf')
        best = float('inf')
        for c in coins:
            r = helper(rem - c)
            if r != float('inf'):
                best = min(best, r + 1)
        return best

    result = helper(amount)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 3: BFS over state space
# =============================================================================
def coin_change_3(coins, amount):
    """BFS: each step adds a coin. Find shortest path to amount."""
    if amount == 0:
        return 0
    visited = {0}
    queue = [0]
    steps = 0
    while queue:
        next_queue = []
        for x in queue:
            for c in coins:
                nx = x + c
                if nx == amount:
                    return steps + 1
                if nx < amount and nx not in visited:
                    visited.add(nx)
                    next_queue.append(nx)
        queue = next_queue
        steps += 1
    return -1


# =============================================================================
# WAY 4: DP + sorted coins
# =============================================================================
def coin_change_4(coins, amount):
    """Sort coins ascending."""
    if amount == 0:
        return 0
    coins = sorted(coins)
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in coins:
            if c > i:
                break
            if dp[i - c] != float('inf'):
                dp[i] = min(dp[i], dp[i - c] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1


# =============================================================================
# WAY 5: BFS with deque
# =============================================================================
def coin_change_5(coins, amount):
    from collections import deque
    if amount == 0:
        return 0
    visited = [False] * (amount + 1)
    visited[0] = True
    queue = deque([(0, 0)])
    while queue:
        x, steps = queue.popleft()
        for c in coins:
            nx = x + c
            if nx == amount:
                return steps + 1
            if nx < amount and not visited[nx]:
                visited[nx] = True
                queue.append((nx, steps + 1))
    return -1


# =============================================================================
# WAY 6: DP with one-liner init
# =============================================================================
def coin_change_6(coins, amount):
    if amount == 0:
        return 0
    INF = float('inf')
    dp = [0] + [INF] * amount
    for i in range(1, amount + 1):
        dp[i] = min((dp[i - c] + 1 for c in coins if i >= c and dp[i - c] < INF), default=INF)
    return dp[amount] if dp[amount] != INF else -1


# =============================================================================
# WAY 7: DP + space optimization
# =============================================================================
def coin_change_7(coins, amount):
    """Same DP, slightly different style."""
    if amount == 0:
        return 0
    dp = [0] + [float('inf')] * amount
    for c in coins:
        for i in range(c, amount + 1):
            if dp[i - c] != float('inf'):
                dp[i] = min(dp[i], dp[i - c] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class CoinChangeSolver:
    def __init__(self, coins):
        self.coins = coins

    def solve(self, amount):
        if amount == 0:
            return 0
        dp = [float('inf')] * (amount + 1)
        dp[0] = 0
        for i in range(1, amount + 1):
            for c in self.coins:
                if i >= c and dp[i - c] != float('inf'):
                    dp[i] = min(dp[i], dp[i - c] + 1)
        return dp[amount] if dp[amount] != float('inf') else -1


def coin_change_8(coins, amount):
    return CoinChangeSolver(coins).solve(amount)


# =============================================================================
# WAY 9: Recursive without memoization (slow)
# =============================================================================
def coin_change_9(coins, amount):
    """Pure recursion (will TLE for large)."""

    def helper(rem):
        if rem == 0:
            return 0
        if rem < 0:
            return float('inf')
        best = float('inf')
        for c in coins:
            r = helper(rem - c)
            if r != float('inf'):
                best = min(best, r + 1)
        return best

    result = helper(amount)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 10: DP + count instead of inf
# =============================================================================
def coin_change_10(coins, amount):
    """Use large number instead of inf."""
    if amount == 0:
        return 0
    INF = amount + 1
    dp = [0] + [INF] * amount
    for i in range(1, amount + 1):
        for c in coins:
            if i >= c and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[amount] if dp[amount] <= amount else -1


# =============================================================================
# WAY 11: Greedy (FAILS for non-canonical coin systems)
# =============================================================================
def coin_change_11(coins, amount):
    """Greedy works only for canonical systems like US coins."""
    coins = sorted(coins, reverse=True)
    count = 0
    for c in coins:
        while amount >= c:
            amount -= c
            count += 1
    return count if amount == 0 else -1


# =============================================================================
# WAY 12: DP with enumerate
# =============================================================================
def coin_change_12(coins, amount):
    if amount == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for idx, c in enumerate(coins):
            if i >= c and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[amount] if dp[amount] != INF else -1


# =============================================================================
# WAY 13: Top-down with explicit dict memo
# =============================================================================
def coin_change_13(coins, amount):
    memo = {0: 0}

    def helper(rem):
        if rem < 0:
            return float('inf')
        if rem in memo:
            return memo[rem]
        best = float('inf')
        for c in coins:
            r = helper(rem - c)
            if r != float('inf'):
                best = min(best, r + 1)
        memo[rem] = best
        return best

    result = helper(amount)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 14: BFS level-by-level
# =============================================================================
def coin_change_14(coins, amount):
    if amount == 0:
        return 0
    visited = set([0])
    level = [0]
    steps = 0
    while level:
        next_level = []
        for x in level:
            for c in coins:
                nx = x + c
                if nx == amount:
                    return steps + 1
                if nx not in visited and nx < amount:
                    visited.add(nx)
                    next_level.append(nx)
        level = next_level
        steps += 1
    return -1


# =============================================================================
# WAY 15: Generator-based DP
# =============================================================================
def coin_change_15(coins, amount):
    if amount == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        candidates = (dp[i - c] + 1 for c in coins if i >= c and dp[i - c] < INF)
        best = min(candidates, default=INF)
        dp[i] = best
    return dp[amount] if dp[amount] != INF else -1


# =============================================================================
# WAY 16: DP with one big loop
# =============================================================================
def coin_change_16(coins, amount):
    if amount == 0:
        return 0
    INF = amount + 1
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for c in coins:
        for i in range(c, amount + 1):
            if dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[amount] if dp[amount] <= amount else -1


# =============================================================================
# WAY 17: Recursive + cache
# =============================================================================
def coin_change_17(coins, amount):
    """Recursive with manual cache."""
    cache = {}

    def dfs(rem):
        if rem == 0:
            return 0
        if rem < 0:
            return -1
        if rem in cache:
            return cache[rem]
        best = float('inf')
        for c in coins:
            sub = dfs(rem - c)
            if sub >= 0:
                best = min(best, sub + 1)
        cache[rem] = best if best != float('inf') else -1
        return cache[rem]

    return dfs(amount)


# =============================================================================
# WAY 18: BFS with set
# =============================================================================
def coin_change_18(coins, amount):
    if amount == 0:
        return 0
    seen = {0}
    frontier = {0}
    steps = 0
    while frontier:
        if amount in frontier:
            return steps
        next_frontier = set()
        for x in frontier:
            for c in coins:
                nx = x + c
                if nx <= amount and nx not in seen:
                    seen.add(nx)
                    next_frontier.add(nx)
        frontier = next_frontier
        steps += 1
    return -1


# =============================================================================
# WAY 19: List comprehension DP
# =============================================================================
def coin_change_19(coins, amount):
    if amount == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        dp[i] = min(
            (dp[i - c] for c in coins if i >= c and dp[i - c] < INF),
            default=INF,
        )
        if dp[i] < INF:
            dp[i] += 1
    return dp[amount] if dp[amount] != INF else -1


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def coin_change_20(coins, amount):
    """
    THE ONE TO MEMORIZE.

    1. dp[0] = 0, dp[i] = inf for i > 0.
    2. For i = 1..amount:
       - For each coin c <= i: dp[i] = min(dp[i], dp[i-c] + 1)
    3. Return dp[amount] if finite else -1.

    Time:  O(amount * len(coins))
    Space: O(amount)
    """
    if amount == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in coins:
            if i >= c and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[amount] if dp[amount] != INF else -1


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the minimum number of coins to make up the given amount."

Key Insight:
"Dynamic programming. Let dp[i] = min coins to make amount i.
- Base: dp[0] = 0.
- Transition: dp[i] = min(dp[i - c] + 1 for each coin c <= i).
- Answer: dp[amount] if finite, else -1."

Algorithm:
1. dp = [inf] * (amount + 1). dp[0] = 0.
2. For i from 1 to amount:
   - For each c in coins where c <= i:
     - dp[i] = min(dp[i], dp[i - c] + 1)
3. Return dp[amount] if dp[amount] != inf else -1.

Edge Cases:
- amount = 0: return 0.
- No solution: return -1.
- Single coin: trivial.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Bottom-up| O(A*C) | O(A)   |
| Top-down | O(A*C) | O(A)   |
| BFS      | O(A*C) | O(A)   |
| Greedy   | O(A*C) | O(1)   |
+----------+--------+--------+
A = amount, C = len(coins).

KEY TRICK:
Unbounded knapsack pattern. Each coin can be used unlimited times. dp
state captures "minimum cost so far".

RELATED PROBLEMS:
- Coin Change II (LC 518): count ways.
- Climbing Stairs (LC 70): similar DP.
- Minimum Cost for Tickets (LC 983).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Bottom-up DP (BEST)", coin_change_1),
        ("Way 2: Top-down memo", coin_change_2),
        ("Way 3: BFS", coin_change_3),
        ("Way 4: DP+sorted coins", coin_change_4),
        ("Way 5: BFS+deque", coin_change_5),
        ("Way 6: DP+one-liner", coin_change_6),
        ("Way 7: DP+space opt", coin_change_7),
        ("Way 8: Class OOP", coin_change_8),
        ("Way 9: Recursive no memo", coin_change_9),
        ("Way 10: DP+count", coin_change_10),
        ("Way 11: Greedy", coin_change_11),
        ("Way 12: DP+enumerate", coin_change_12),
        ("Way 13: Top-down dict memo", coin_change_13),
        ("Way 14: BFS level", coin_change_14),
        ("Way 15: Generator DP", coin_change_15),
        ("Way 16: DP+big loop", coin_change_16),
        ("Way 17: Recursive+cache", coin_change_17),
        ("Way 18: BFS+set", coin_change_18),
        ("Way 19: List comp DP", coin_change_19),
        ("Way 20: Final cleanest", coin_change_20),
    ]

    test_cases = [
        # (coins, amount, expected)
        ([1, 5, 10, 25], 11, 3),
        ([2], 3, -1),
        ([1], 0, 0),
        ([1, 2, 5], 11, 3),
        ([2], 1, -1),
        ([1, 2, 5], 100, 20),  # 20 fives
        ([186, 419, 83, 408], 6249, 20),
        # Verify: greedy would fail here but DP works.
        # 20 coins
        ([1, 5, 10, 25], 30, 2),  # 25+5
        ([5, 10], 3, -1),
        ([1], 100, 100),
    ]

    print("=" * 70)
    print("COIN CHANGE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for coins, amount, expected in test_cases:
            try:
                result = func(coins[:], amount)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: coins={coins}, amount={amount}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
