"""
Coin Change
Medium | 30 min

Given an integer total and a list of integers coins (denominations),
find the minimum number of coins required to make up the total amount.
Return -1 if impossible, 0 if total == 0.

You have infinite coins of each denomination.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change

Constraints:
- 1 <= coins.length <= 12
- 1 <= coins[i] <= 10^4
- 0 <= total <= 900

Examples:
    coins=[1,5,10,25], total=11 -> 2 (10+1)
    coins=[2], total=3 -> -1
    coins=[1], total=0 -> 0
    coins=[1,2,5], total=11 -> 3 (5+5+1)

Key Insight:
Standard unbounded knapsack / coin change DP.
dp[i] = min coins to make amount i.
dp[0] = 0, dp[i] = min(dp[i-c] + 1) for each coin c <= i.

Time:  O(n * total) — n coins, total iterations.
Space: O(total) for dp array.
"""


# =============================================================================
# WAY 1: Bottom-up DP (BEST - Memorize!)
# =============================================================================
def coin_change_1(coins, total):
    """
    Build dp[i] = min coins to make amount i, for i in 0..total.
    """
    if total == 0:
        return 0
    dp = [float('inf')] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for c in coins:
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[total] if dp[total] != float('inf') else -1


# =============================================================================
# WAY 2: Verbose
# =============================================================================
def coin_change_2(coins, total):
    """Verbose version."""
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for amount in range(1, total + 1):
        for coin in coins:
            if coin <= amount and dp[amount - coin] + 1 < dp[amount]:
                dp[amount] = dp[amount - coin] + 1
    if dp[total] == INF:
        return -1
    return dp[total]


# =============================================================================
# WAY 3: Brute force recursion
# =============================================================================
def coin_change_3(coins, total):
    """Recursive brute force - exponential time."""

    def helper(remaining):
        if remaining == 0:
            return 0
        if remaining < 0:
            return float('inf')
        min_count = float('inf')
        for c in coins:
            result = helper(remaining - c)
            if result != float('inf'):
                min_count = min(min_count, result + 1)
        return min_count

    if total == 0:
        return 0
    result = helper(total)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 4: Memoized recursion
# =============================================================================
def coin_change_4(coins, total):
    """Memoized top-down."""
    import sys
    sys.setrecursionlimit(10000)

    memo = {}

    def helper(remaining):
        if remaining == 0:
            return 0
        if remaining < 0:
            return float('inf')
        if remaining in memo:
            return memo[remaining]
        min_count = float('inf')
        for c in coins:
            result = helper(remaining - c)
            if result != float('inf'):
                min_count = min(min_count, result + 1)
        memo[remaining] = min_count
        return min_count

    if total == 0:
        return 0
    result = helper(total)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 5: BFS approach
# =============================================================================
def coin_change_5(coins, total):
    """
    BFS: each state is an amount. Try adding each coin.
    Return depth when we hit 0 or total.
    """
    if total == 0:
        return 0
    from collections import deque
    visited = {0}
    queue = deque([(0, 0)])  # (amount, count)
    while queue:
        amount, count = queue.popleft()
        if amount == total:
            return count
        if amount > total:
            continue
        for c in coins:
            new_amount = amount + c
            if new_amount <= total and new_amount not in visited:
                visited.add(new_amount)
                queue.append((new_amount, count + 1))
    return -1


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class CoinChanger:
    def __init__(self, coins, total):
        self.coins = coins
        self.total = total

    def change(self):
        if self.total == 0:
            return 0
        INF = float('inf')
        dp = [INF] * (self.total + 1)
        dp[0] = 0
        for i in range(1, self.total + 1):
            for c in self.coins:
                if c <= i:
                    dp[i] = min(dp[i], dp[i - c] + 1)
        return dp[self.total] if dp[self.total] != INF else -1


def coin_change_6(coins, total):
    """Class-based."""
    return CoinChanger(coins, total).change()


# =============================================================================
# WAY 7: numpy version
# =============================================================================
def coin_change_7(coins, total):
    """Vectorized with numpy."""
    try:
        import numpy as np
        if total == 0:
            return 0
        INF = float('inf')
        dp = np.full(total + 1, INF)
        dp[0] = 0
        for c in coins:
            # For each amount >= c, dp[i] = min(dp[i], dp[i-c]+1)
            for i in range(c, total + 1):
                if dp[i - c] + 1 < dp[i]:
                    dp[i] = dp[i - c] + 1
        return int(dp[total]) if dp[total] != INF else -1
    except ImportError:
        return coin_change_1(coins, total)


# =============================================================================
# WAY 8: With lru_cache decorator
# =============================================================================
def coin_change_8(coins, total):
    """Use functools.lru_cache."""
    import sys
    sys.setrecursionlimit(10000)

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def helper(remaining):
        if remaining == 0:
            return 0
        if remaining < 0:
            return float('inf')
        min_count = float('inf')
        for c in coins:
            result = helper(remaining - c)
            if result != float('inf'):
                min_count = min(min_count, result + 1)
        return min_count

    if total == 0:
        return 0
    result = helper(total)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 9: enumerate + min
# =============================================================================
def coin_change_9(coins, total):
    """Use enumerate for amount iteration."""
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        candidates = []
        for c in coins:
            if c <= i:
                candidates.append(dp[i - c] + 1)
        if candidates:
            dp[i] = min(candidates)
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 10: Helper function approach
# =============================================================================
def coin_change_10(coins, total):
    """Extract helper functions."""
    INF = float('inf')

    def build_dp(n):
        dp = [INF] * (n + 1)
        dp[0] = 0
        return dp

    def update_dp(dp, coins):
        for i in range(1, len(dp)):
            for c in coins:
                if c <= i:
                    dp[i] = min(dp[i], dp[i - c] + 1)
        return dp

    if total == 0:
        return 0
    dp = build_dp(total)
    dp = update_dp(dp, coins)
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 11: Functional with map
# =============================================================================
def coin_change_11(coins, total):
    """Functional style."""
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        # Get all valid candidates
        candidates = list(map(lambda c: dp[i - c] + 1 if c <= i else INF, coins))
        dp[i] = min(candidates)
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 12: BFS approach (alternative)
# =============================================================================
def coin_change_12(coins, total):
    """BFS using set to track visited."""
    if total == 0:
        return 0
    if not coins:
        return -1
    # Filter out coins > total
    coins = [c for c in coins if c <= total]
    if not coins:
        return -1
    from collections import deque
    queue = deque([(0, 0)])
    visited = {0}
    while queue:
        amount, count = queue.popleft()
        if amount == total:
            return count
        for c in coins:
            new_amount = amount + c
            if new_amount <= total and new_amount not in visited:
                visited.add(new_amount)
                queue.append((new_amount, count + 1))
    return -1


# =============================================================================
# WAY 13: itertools.reduce
# =============================================================================
def coin_change_13(coins, total):
    """Use functools.reduce."""
    from functools import reduce
    if total == 0:
        return 0
    INF = float('inf')

    def step(dp, i):
        new_dp = dp.copy()
        for c in coins:
            if c <= i:
                new_dp[i] = min(new_dp[i], dp[i - c] + 1)
        return new_dp

    dp = [INF] * (total + 1)
    dp[0] = 0
    dp = reduce(step, range(1, total + 1), dp)
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 14: With for-else
# =============================================================================
def coin_change_14(coins, total):
    """Use for-else pattern."""
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for c in coins:
            if c <= i:
                dp[i] = min(dp[i], dp[i - c] + 1)
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 15: One-liner with comprehension
# =============================================================================
def coin_change_15(coins, total):
    """Concise."""
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        dp[i] = min((dp[i - c] + 1 for c in coins if c <= i), default=INF)
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 16: While loop variant
# =============================================================================
def coin_change_16(coins, total):
    """While loop variant."""
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    i = 1
    while i <= total:
        for c in coins:
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
        i += 1
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 17: Using list comprehension for dp init
# =============================================================================
def coin_change_17(coins, total):
    """List comprehension for setup."""
    if total == 0:
        return 0
    INF = float('inf')
    dp = [0] + [INF] * total
    for i in range(1, total + 1):
        dp[i] = min((dp[i - c] + 1 for c in coins if c <= i), default=INF)
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 18: With sorted coins
# =============================================================================
def coin_change_18(coins, total):
    """Sort coins first."""
    if total == 0:
        return 0
    INF = float('inf')
    sorted_coins = sorted(coins)
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for c in sorted_coins:
            if c <= i:
                dp[i] = min(dp[i], dp[i - c] + 1)
            else:
                break  # Larger coins won't fit either
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# WAY 19: Recursive with explicit memo
# =============================================================================
def coin_change_19(coins, total):
    """Recursive with explicit memo dict."""
    import sys
    sys.setrecursionlimit(10000)
    if total == 0:
        return 0
    memo = {0: 0}

    def helper(remaining):
        if remaining in memo:
            return memo[remaining]
        if remaining < 0:
            return float('inf')
        min_count = float('inf')
        for c in coins:
            result = helper(remaining - c)
            if result != float('inf'):
                min_count = min(min_count, result + 1)
        memo[remaining] = min_count
        return min_count

    result = helper(total)
    return result if result != float('inf') else -1


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def coin_change_20(coins, total):
    """
    Final clean version.

    Algorithm:
    1. dp[i] = min coins to make amount i. dp[0] = 0.
    2. For each amount i from 1 to total:
       For each coin c:
         If c <= i: dp[i] = min(dp[i], dp[i-c] + 1)
    3. Return dp[total] if finite, else -1.

    Why this works:
    - Each amount i can be reached by adding one coin to amount (i - c).
    - dp[i - c] is already the min coins for (i - c).
    - Adding 1 more coin gives dp[i - c] + 1.
    - Take min over all coins.

    Time:  O(n * total).
    Space: O(total).

    Edge cases:
    - total == 0: return 0.
    - No valid combination: return -1.
    - Coin > total: skip.
    """
    if total == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (total + 1)
    dp[0] = 0
    for i in range(1, total + 1):
        for c in coins:
            if c <= i:
                dp[i] = min(dp[i], dp[i - c] + 1)
    return dp[total] if dp[total] != INF else -1


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the minimum number of coins to make a target total, given
infinite coins of each denomination."

Key Insight:
"This is the unbounded knapsack / coin change DP. Define dp[i] = min coins
to make amount i. dp[0] = 0. For each amount, try adding each coin."

Algorithm:
"1. Initialize dp[0] = 0, dp[i] = infinity for i > 0.
2. For i from 1 to total:
   For each coin c with c <= i:
     dp[i] = min(dp[i], dp[i-c] + 1)
3. Return dp[total] or -1 if infinity."

Why this works:
"Each amount i can be made by adding one coin c to amount (i-c). Since
dp[i-c] is the minimum for i-c, dp[i-c]+1 is a candidate. Take min over
all coins and previous subproblems."

Edge cases:
- total == 0: return 0 (no coins needed).
- No valid combination: dp[total] remains infinity, return -1.
- Single coin value > total: impossible if it doesn't match.

Complexity:
- Time:  O(n * total) — n coins, total amounts.
- Space: O(total) for dp array.

KEY TRICK:
Initialize with dp[0] = 0 and infinity elsewhere. For each amount, try each
coin and update.

ALTERNATIVE: Top-down memoization
Recursion with memo dict. Same complexity, cleaner code for some.

ALTERNATIVE: BFS
Each state is an amount. Use BFS to find shortest path. O(n * total) time.

INTERVIEW TIPS:
1. Recognize "unbounded knapsack" / "coin change" pattern.
2. Mention dp state and recurrence clearly.
3. Handle total == 0 and impossible cases.

RELATIONSHIP TO OTHER PROBLEMS:
- Coin Change II (LC 518): Count ways, not min coins.
- Climbing Stairs (LC 70): Smaller variant.
- Perfect Squares (LC 279): Similar structure.
- Minimum Cost For Tickets (LC 983): Different DP.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Bottom-up DP (BEST)", coin_change_1),
        ("Way 2: Verbose", coin_change_2),
        ("Way 3: Brute recursion", coin_change_3),
        ("Way 4: Memoized", coin_change_4),
        ("Way 5: BFS", coin_change_5),
        ("Way 6: Class-based", coin_change_6),
        ("Way 7: numpy", coin_change_7),
        ("Way 8: lru_cache", coin_change_8),
        ("Way 9: enumerate + min", coin_change_9),
        ("Way 10: Helper functions", coin_change_10),
        ("Way 11: Functional map", coin_change_11),
        ("Way 12: BFS alt", coin_change_12),
        ("Way 13: reduce", coin_change_13),
        ("Way 14: for-else", coin_change_14),
        ("Way 15: One-liner comp", coin_change_15),
        ("Way 16: While loop", coin_change_16),
        ("Way 17: List comp init", coin_change_17),
        ("Way 18: Sorted coins", coin_change_18),
        ("Way 19: Recursive memo", coin_change_19),
        ("Way 20: Final cleanest", coin_change_20),
    ]

    test_cases = [
        # Standard examples
        ([1, 5, 10, 25], 11, 2),  # 10+1
        ([2], 3, -1),  # impossible
        ([1], 0, 0),  # total 0
        ([1, 2, 5], 11, 3),  # 5+5+1
        ([186, 419, 83, 408], 6249, 20),  # LeetCode example
        ([1, 2, 5], 100, 20),  # 20 fives
        ([3, 7, 405, 436], 8839, 25),  # LeetCode example
        ([1], 1, 1),  # single coin
        ([1], 100, 100),  # many singles
        ([5, 10], 15, 2),  # 5+10
        ([2, 5, 10, 1], 7, 2),  # 5+2 or 2+2+2+1 etc. Min=2 (5+2)
        ([5, 2, 1], 11, 3),  # 5+5+1
        ([7], 14, 2),  # 7+7
        ([7], 15, -1),  # impossible with 7 only
    ]

    print("=" * 70)
    print("COIN CHANGE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        # Skip large tests for brute force recursion
        test_subset = test_cases
        if "Brute recursion" in name:
            test_subset = [(c, t, e) for c, t, e in test_cases if t <= 30]
        for coins, total, expected in test_subset:
            try:
                import copy
                result = func(copy.deepcopy(coins), total)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: coins={coins}, total={total} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on coins={coins}, total={total} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)