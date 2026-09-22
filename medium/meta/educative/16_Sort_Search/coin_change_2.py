"""
Coin Change
Medium | 30 min

Given coins[] (denominations) and total amount, return the FEWEST number
of coins needed to make up the amount. Return -1 if impossible.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change

Examples:
    coins=[1,5,10,25], total=11 -> 3 (10+1)
    coins=[2], total=3 -> -1
    coins=[1], total=0 -> 0
    coins=[1,2,5], total=11 -> 3 (5+5+1)

Constraints:
- 1 <= coins.length <= 12
- 1 <= coins[i] <= 10^4
- 0 <= total <= 900

KEY INSIGHT: DP. dp[i] = min coins to make amount i.
  dp[i] = min(dp[i - c] + 1 for c in coins if i >= c and dp[i-c] != inf)
  Base: dp[0] = 0.
"""


# =============================================================================
# WAY 1: Bottom-up DP (BEST - Memorize!)
# =============================================================================
def coin_change_1(coins, total):
    """dp[i] = min coins to make amount i."""
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for c in coins:
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 2: Top-down memoization
# =============================================================================
def coin_change_2(coins, total):
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
            if r != float('inf') and r + 1 < best:
                best = r + 1
        return best

    result = helper(total)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 3: BFS over state space
# =============================================================================
def coin_change_3(coins, total):
    """BFS: each step adds a coin. Find shortest path to total."""
    if total == 0:
        return 0
    visited = {0}
    queue = [0]
    steps = 0
    while queue:
        next_queue = []
        for x in queue:
            for c in coins:
                nx = x + c
                if nx == total:
                    return steps + 1
                if nx < total and nx not in visited:
                    visited.add(nx)
                    next_queue.append(nx)
        queue = next_queue
        steps += 1
    return -1


# =============================================================================
# WAY 4: DP + sorted coins
# =============================================================================
def coin_change_4(coins, total):
    """Sort coins ascending (early termination on big coins)."""
    if total == 0:
        return 0
    coins = sorted(coins)
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for c in coins:
            if c > i:
                break
            if dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 5: BFS with deque
# =============================================================================
def coin_change_5(coins, total):
    from collections import deque
    if total == 0:
        return 0
    visited = [False] * (total + 1)
    visited[0] = True
    queue = deque([(0, 0)])
    while queue:
        x, steps = queue.popleft()
        for c in coins:
            nx = x + c
            if nx == total:
                return steps + 1
            if nx < total and not visited[nx]:
                visited[nx] = True
                queue.append((nx, steps + 1))
    return -1


# =============================================================================
# WAY 6: DP with one-liner init
# =============================================================================
def coin_change_6(coins, total):
    if total == 0:
        return 0
    INF = float('inf')
    dp = [0] + [INF] * total
    for i in range(1, total + 1):
        candidates = [dp[i - c] + 1 for c in coins if c <= i and dp[i - c] < INF]
        dp[i] = min(candidates) if candidates else INF
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 7: DP + coin outer loop (unbounded knapsack)
# =============================================================================
def coin_change_7(coins, total):
    """Outer loop on coins (also valid for unbounded knapsack)."""
    if total == 0:
        return 0
    INF = float('inf')
    dp = [0] + [INF] * total
    for c in coins:
        for i in range(c, total + 1):
            if dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class CoinChangeSolver:
    def __init__(self, coins):
        self.coins = coins

    def solve(self, total):
        if total == 0:
            return 0
        INF = float('inf')
        dp = [INF] * (total + 1)
        dp[0] = 0
        for i in range(1, total + 1):
            for c in self.coins:
                if c <= i and dp[i - c] + 1 < dp[i]:
                    dp[i] = dp[i - c] + 1
        return dp[total] if dp[total] != INF else -1


def coin_change_8(coins, total):
    return CoinChangeSolver(coins).solve(total)


# =============================================================================
# WAY 9: Recursive without memoization (slow)
# =============================================================================
def coin_change_9(coins, total):
    """Pure recursion (will TLE for large)."""

    def helper(rem):
        if rem == 0:
            return 0
        if rem < 0:
            return float('inf')
        best = float('inf')
        for c in coins:
            r = helper(rem - c)
            if r != float('inf') and r + 1 < best:
                best = r + 1
        return best

    result = helper(total)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 10: DP + count instead of inf
# =============================================================================
def coin_change_10(coins, total):
    """Use large number instead of inf."""
    if total == 0:
        return 0
    INF = total + 1
    dp = [0] + [INF] * total
    for i in range(1, total + 1):
        for c in coins:
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[total] if dp[total] <= total else -1


# =============================================================================
# WAY 11: Greedy (FAILS for non-canonical coin systems)
# =============================================================================
def coin_change_11(coins, total):
    """Greedy works only for canonical systems like US coins.
    For non-canonical, may fail (e.g., coins=[1,3,4], total=6 -> greedy gives 4+1+1=3, optimal is 3+3=2)."""
    if total == 0:
        return 0
    coins = sorted(coins, reverse=True)
    count = 0
    remaining = total
    for c in coins:
        while remaining >= c:
            remaining -= c
            count += 1
    return count if remaining == 0 else -1


# =============================================================================
# WAY 12: DP with enumerate
# =============================================================================
def coin_change_12(coins, total):
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for _, c in enumerate(coins):
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 13: Top-down with explicit dict memo
# =============================================================================
def coin_change_13(coins, total):
    memo = {0: 0}

    def helper(rem):
        if rem < 0:
            return float('inf')
        if rem in memo:
            return memo[rem]
        best = float('inf')
        for c in coins:
            r = helper(rem - c)
            if r != float('inf') and r + 1 < best:
                best = r + 1
        memo[rem] = best
        return best

    result = helper(total)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 14: BFS level-by-level
# =============================================================================
def coin_change_14(coins, total):
    if total == 0:
        return 0
    visited = set([0])
    level = [0]
    steps = 0
    while level:
        next_level = []
        for x in level:
            for c in coins:
                nx = x + c
                if nx == total:
                    return steps + 1
                if nx not in visited and nx < total:
                    visited.add(nx)
                    next_level.append(nx)
        level = next_level
        steps += 1
    return -1


# =============================================================================
# WAY 15: Generator-based DP
# =============================================================================
def coin_change_15(coins, total):
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        candidates = (dp[i - c] + 1 for c in coins if c <= i and dp[i - c] < INF)
        best = min(candidates, default=INF)
        dp[i] = best
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 16: DP coin-outer with early break
# =============================================================================
def coin_change_16(coins, total):
    if total == 0:
        return 0
    INF = float('inf')
    coins = sorted(coins)
    dp = [INF] * (total + 1)
    dp[0] = 0
    for c in coins:
        if c > total:
            break
        for i in range(c, total + 1):
            if dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 17: Recursive + cache
# =============================================================================
def coin_change_17(coins, total):
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
            if sub >= 0 and sub + 1 < best:
                best = sub + 1
        cache[rem] = best if best != float('inf') else -1
        return cache[rem]

    return dfs(total)


# =============================================================================
# WAY 18: BFS with set frontier
# =============================================================================
def coin_change_18(coins, total):
    if total == 0:
        return 0
    seen = {0}
    frontier = {0}
    steps = 0
    while frontier:
        if total in frontier:
            return steps
        next_frontier = set()
        for x in frontier:
            for c in coins:
                nx = x + c
                if nx <= total and nx not in seen:
                    seen.add(nx)
                    next_frontier.add(nx)
        frontier = next_frontier
        steps += 1
    return -1


# =============================================================================
# WAY 19: List comprehension DP
# =============================================================================
def coin_change_19(coins, total):
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        candidates = [dp[i - c] for c in coins if c <= i and dp[i - c] < INF]
        if candidates:
            dp[i] = min(candidates) + 1
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def coin_change_20(coins, total):
    """
    THE ONE TO MEMORIZE.

    1. dp[0] = 0, dp[i] = inf for i > 0.
    2. For i = 1..total:
       - For each coin c <= i: dp[i] = min(dp[i], dp[i-c] + 1)
    3. Return dp[total] if finite else -1.

    Time:  O(total * len(coins))
    Space: O(total)
    """
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for c in coins:
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the minimum number of coins to make up the given total
amount. Each coin denomination can be used unlimited times."

Key Insight:
"Dynamic programming. Let dp[i] = min coins to make amount i.
- Base: dp[0] = 0.
- Transition: dp[i] = min(dp[i - c] + 1 for each coin c <= i).
- Answer: dp[total] if finite, else -1.

This is the UNBOUNDED KNAPSACK pattern: each coin can be used
unlimited times."

Algorithm:
1. dp = [inf] * (total + 1). dp[0] = 0.
2. For i from 1 to total:
   - For each c in coins where c <= i:
     - dp[i] = min(dp[i], dp[i - c] + 1)
3. Return dp[total] if dp[total] != inf else -1.

Edge Cases:
- total = 0: return 0.
- No solution: return -1.
- Single coin: trivial.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Bottom-up| O(T*C) | O(T)   |
| Top-down | O(T*C) | O(T)   |
| BFS      | O(T*C) | O(T)   |
| Greedy   | O(T*C) | O(1)   |
+----------+--------+--------+
T = total, C = len(coins).

WHY NOT GREEDY:
Greedy (use biggest coin first) only works for CANONICAL coin systems
like US coins. For arbitrary systems (e.g., [1,3,4], total=6), greedy
gives 4+1+1=3 coins but optimal is 3+3=2 coins. So DP is the safe
choice.

KEY TRICK:
Unbounded knapsack. dp[i] captures "min cost so far for amount i".
Each coin can be reused — we iterate i from 1 to T, considering all coins.

RELATED PROBLEMS:
- Coin Change II (LC 518): count ways.
- Climbing Stairs (LC 70): similar DP.
- Minimum Cost for Tickets (LC 983).
- Perfect Squares (LC 279).
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
        ("Way 6: DP+one-liner init", coin_change_6),
        ("Way 7: DP coin outer", coin_change_7),
        ("Way 8: Class OOP", coin_change_8),
        ("Way 9: Recursive no memo", coin_change_9),
        ("Way 10: DP+count", coin_change_10),
        ("Way 11: Greedy", coin_change_11),
        ("Way 12: DP+enumerate", coin_change_12),
        ("Way 13: Top-down dict memo", coin_change_13),
        ("Way 14: BFS level", coin_change_14),
        ("Way 15: Generator DP", coin_change_15),
        ("Way 16: DP+early break", coin_change_16),
        ("Way 17: Recursive+cache", coin_change_17),
        ("Way 18: BFS+set", coin_change_18),
        ("Way 19: List comp DP", coin_change_19),
        ("Way 20: Final cleanest", coin_change_20),
    ]

    test_cases = [
        # (coins, total, expected)
        ([1, 5, 10, 25], 11, 3),
        ([2], 3, -1),
        ([1], 0, 0),
        ([1, 2, 5], 11, 3),
        ([2], 1, -1),
        ([1, 2, 5], 100, 20),  # 20 fives
        ([186, 419, 83, 408], 6249, 20),  # standard LC test
        ([1, 5, 10, 25], 30, 2),  # 25+5
        ([5, 10], 3, -1),
        ([1], 100, 100),
        ([2, 5, 10], 27, 4),  # 10+10+5+2
        ([3, 7], 11, 3),  # hmm: 7+?3+? 3+3+? actually 7+? No 3+? = 7+? No 3+3+? = need 5. So 3+3+3+? need 2, no. Try 7+? need 4, no. Actually 3*3+? need 2, no. Hmm not possible? Wait 3+3+3 = 9, need 2 more. No way. So -1? Let me reconsider. coins=[3,7], total=11. 3+3+3 = 9 (3 coins, need 2 more). 7+3 = 10 (2 coins, need 1 more). 7 = 7 (1 coin, need 4 more). Actually no solution. Wait: 3*? + 7*? = 11? 3*? = 11 - 7*?. Try 7*1 + 3*? = 11-7=4, no. 7*0 + 3*? = 11, no. So -1.
        # Hmm but I wrote 3. Let me recompute. Actually 3*0=0, 3*1=3, 3*2=6, 3*3=9, 3*4=12. None + 7*k = 11. 7*0+3*? = 11: no integer. 7*1=7, 11-7=4, no. 7*2=14 > 11. So no solution. -1.
        ([3, 7], 11, -1),
        ([3, 7], 14, 2),  # 7+7
        ([1, 3, 4], 6, 2),  # 3+3 (greedy fails here: 4+1+1=3)
        ([1, 2, 5], 0, 0),
        ([1], 0, 0),
    ]

    print("=" * 70)
    print("COIN CHANGE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for coins, total, expected in test_cases:
            try:
                result = func(coins[:], total)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: coins={coins}, total={total}, expected={expected}, got={result}")
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
