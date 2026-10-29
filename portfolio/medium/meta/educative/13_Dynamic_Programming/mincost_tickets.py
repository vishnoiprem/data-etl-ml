"""
Minimum Cost For Tickets
Medium | 30 min

Given days (list of travel days in strictly increasing order) and costs
(1-day, 7-day, 30-day pass costs), find the minimum cost to cover all
travel days.

A pass bought on day d covers days d through d+duration-1.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-cost-for-tickets

Constraints:
- 1 <= days.length <= 365
- 1 <= days[i] <= 365
- days is strictly increasing
- costs.length == 3
- 1 <= costs[i] <= 1000

Examples:
    days=[1,4,6,7,8,20], ticket costs=[2,7,15] -> 11
    (1-day for 1, 7-day for 4-10 (covers 4,6,7,8), 1-day for 20 = 2+7+2=11)
    days=[1,2,3,4,5,6,7,8,9,10,30,31], costs=[2,7,15] -> 17
    (7-day for 1-7, 7-day for 8-14? No, 30-day for 1-30, 1-day for 31 = 15+2=17)

Key Insight:
Standard DP. dp[d] = min cost to cover all travel days from day 1 to day d.
For each day d:
- If d is a travel day, dp[d] = min(dp[d-1] + cost[0], dp[d-7] + cost[1], dp[d-30] + cost[2])
- If d is not a travel day, dp[d] = dp[d-1]

Time:  O(365) — fixed year range.
Space: O(365) for dp.
"""


# =============================================================================
# WAY 1: DP with set lookup (BEST - Memorize!)
# =============================================================================
def mincost_tickets_1(days, costs):
    """
    dp[d] = min cost to cover days[1..d].
    """
    travel_set = set(days)
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    for d in range(1, last_day + 1):
        if d not in travel_set:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last_day]


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def mincost_tickets_2(days, costs):
    """Verbose."""
    travel_set = set(days)
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    for d in range(1, last_day + 1):
        if d not in travel_set:
            # Not a travel day, no new ticket needed
            dp[d] = dp[d - 1]
        else:
            # Travel day: try 1-day, 7-day, 30-day
            one_day = dp[d - 1] + costs[0]
            seven_day = dp[max(0, d - 7)] + costs[1]
            thirty_day = dp[max(0, d - 30)] + costs[2]
            dp[d] = min(one_day, seven_day, thirty_day)
    return dp[last_day]


# =============================================================================
# WAY 3: DP with index pointer (track position in days array)
# =============================================================================
def mincost_tickets_3(days, costs):
    """
    Use index pointer to know which days are travel days.
    """
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    day_set = set(days)
    for d in range(1, last_day + 1):
        if d in day_set:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
        else:
            dp[d] = dp[d - 1]
    return dp[last_day]


# =============================================================================
# WAY 4: Top-down memoization
# =============================================================================
def mincost_tickets_4(days, costs):
    """Top-down memoization."""

    def helper(d):
        if d <= 0:
            return 0
        if d in memo:
            return memo[d]
        if d not in travel_set:
            memo[d] = helper(d - 1)
            return memo[d]
        result = min(
            helper(d - 1) + costs[0],
            helper(d - 7) + costs[1],
            helper(d - 30) + costs[2]
        )
        memo[d] = result
        return result

    travel_set = set(days)
    memo = {}
    return helper(days[-1])


# =============================================================================
# WAY 5: DP iterating only over travel days
# =============================================================================
def mincost_tickets_5(days, costs):
    """
    Iterate over travel days. For each, dp[i] = min cost to cover days[0..i].
    """
    n = len(days)
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        # Option 1: 1-day pass for days[i-1]
        dp[i] = dp[i - 1] + costs[0]
        # Option 2: 7-day pass covering days[i-1]
        j = i - 1
        while j >= 0 and days[i - 1] - days[j] < 7:
            j -= 1
        dp[i] = min(dp[i], dp[j + 1] + costs[1])
        # Option 3: 30-day pass
        j = i - 1
        while j >= 0 and days[i - 1] - days[j] < 30:
            j -= 1
        dp[i] = min(dp[i], dp[j + 1] + costs[2])
    return dp[n]


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class TicketOptimizer:
    def __init__(self, days, costs):
        self.days = days
        self.costs = costs

    def min_cost(self):
        last_day = self.days[-1]
        dp = [0] * (last_day + 1)
        travel_set = set(self.days)
        for d in range(1, last_day + 1):
            if d not in travel_set:
                dp[d] = dp[d - 1]
            else:
                dp[d] = min(
                    dp[d - 1] + self.costs[0],
                    dp[max(0, d - 7)] + self.costs[1],
                    dp[max(0, d - 30)] + self.costs[2]
                )
        return dp[last_day]


def mincost_tickets_6(days, costs):
    """Class-based."""
    return TicketOptimizer(days, costs).min_cost()


# =============================================================================
# WAY 7: numpy version
# =============================================================================
def mincost_tickets_7(days, costs):
    """Vectorized with numpy."""
    try:
        import numpy as np
        last_day = days[-1]
        dp = np.zeros(last_day + 1, dtype=np.int64)
        travel_arr = np.zeros(last_day + 1, dtype=bool)
        for d in days:
            travel_arr[d] = True
        for d in range(1, last_day + 1):
            if not travel_arr[d]:
                dp[d] = dp[d - 1]
            else:
                dp[d] = min(
                    dp[d - 1] + costs[0],
                    dp[max(0, d - 7)] + costs[1],
                    dp[max(0, d - 30)] + costs[2]
                )
        return int(dp[last_day])
    except ImportError:
        return mincost_tickets_1(days, costs)


# =============================================================================
# WAY 8: While loop approach
# =============================================================================
def mincost_tickets_8(days, costs):
    """While loop."""
    travel_set = set(days)
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    d = 1
    while d <= last_day:
        if d not in travel_set:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
        d += 1
    return dp[last_day]


# =============================================================================
# WAY 9: With helper function
# =============================================================================
def mincost_tickets_9(days, costs):
    """Helper function approach."""

    def min_three(a, b, c):
        return min(a, b, c)

    travel_set = set(days)
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    for d in range(1, last_day + 1):
        if d not in travel_set:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min_three(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last_day]


# =============================================================================
# WAY 10: Recursive with memo
# =============================================================================
def mincost_tickets_10(days, costs):
    """Recursive with explicit memo dict."""
    travel_set = set(days)
    memo = {0: 0}

    def helper(d):
        if d in memo:
            return memo[d]
        if d <= 0:
            return 0
        if d not in travel_set:
            memo[d] = helper(d - 1)
            return memo[d]
        result = min(
            helper(d - 1) + costs[0],
            helper(d - 7) + costs[1],
            helper(d - 30) + costs[2]
        )
        memo[d] = result
        return result

    return helper(days[-1])


# =============================================================================
# WAY 11: lru_cache decorator
# =============================================================================
def mincost_tickets_11(days, costs):
    """Use functools.lru_cache."""
    import sys
    sys.setrecursionlimit(1000)
    travel_set = set(days)
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def helper(d):
        if d <= 0:
            return 0
        if d not in travel_set:
            return helper(d - 1)
        return min(
            helper(d - 1) + costs[0],
            helper(d - 7) + costs[1],
            helper(d - 30) + costs[2]
        )

    return helper(days[-1])


# =============================================================================
# WAY 12: DP with travel_set as bool array
# =============================================================================
def mincost_tickets_12(days, costs):
    """Use bool array instead of set."""
    last_day = days[-1]
    travel = [False] * (last_day + 1)
    for d in days:
        travel[d] = True
    dp = [0] * (last_day + 1)
    for d in range(1, last_day + 1):
        if not travel[d]:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last_day]


# =============================================================================
# WAY 13: Functional with map
# =============================================================================
def mincost_tickets_13(days, costs):
    """Functional style."""
    travel_set = set(days)
    last_day = days[-1]
    dp = [0] * (last_day + 1)

    def update(d):
        if d not in travel_set:
            return dp[d - 1]
        return min(
            dp[d - 1] + costs[0],
            dp[max(0, d - 7)] + costs[1],
            dp[max(0, d - 30)] + costs[2]
        )

    for d in range(1, last_day + 1):
        dp[d] = update(d)
    return dp[last_day]


# =============================================================================
# WAY 14: With sorted days (already sorted per constraints)
# =============================================================================
def mincost_tickets_14(days, costs):
    """With explicit sort (defensive)."""
    sorted_days = sorted(days)
    travel_set = set(sorted_days)
    last_day = sorted_days[-1]
    dp = [0] * (last_day + 1)
    for d in range(1, last_day + 1):
        if d not in travel_set:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last_day]


# =============================================================================
# WAY 15: Most concise
# =============================================================================
def mincost_tickets_15(days, costs):
    """Concise."""
    last = days[-1]
    dp = [0] * (last + 1)
    ts = set(days)
    for d in range(1, last + 1):
        dp[d] = dp[d - 1] + (costs[0] if d in ts else 0)
        if d in ts:
            dp[d] = min(
                dp[d],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last]


# =============================================================================
# WAY 16: With enumerate
# =============================================================================
def mincost_tickets_16(days, costs):
    """Use enumerate."""
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    travel_set = set(days)
    for d, _ in enumerate(range(1, last_day + 1), start=1):
        if d not in travel_set:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last_day]


# =============================================================================
# WAY 17: With binary search on days
# =============================================================================
def mincost_tickets_17(days, costs):
    """
    Use binary search on days to find previous travel days.
    """
    import bisect
    n = len(days)
    # dp[i] = min cost to cover days[0..i-1]
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = dp[i - 1] + costs[0]
        # 7-day pass: covers days[i-1] and up to 7 days back
        idx_7 = bisect.bisect_right(days, days[i - 1] - 7)
        dp[i] = min(dp[i], dp[idx_7] + costs[1])
        # 30-day pass
        idx_30 = bisect.bisect_right(days, days[i - 1] - 30)
        dp[i] = min(dp[i], dp[idx_30] + costs[2])
    return dp[n]


# =============================================================================
# WAY 18: Tabulation approach
# =============================================================================
def mincost_tickets_18(days, costs):
    """Tabulation."""
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    is_travel = [False] * (last_day + 1)
    for d in days:
        is_travel[d] = True
    for d in range(1, last_day + 1):
        if not is_travel[d]:
            dp[d] = dp[d - 1]
            continue
        candidates = [dp[d - 1] + costs[0]]
        if d - 7 >= 0:
            candidates.append(dp[d - 7] + costs[1])
        else:
            candidates.append(costs[1])
        if d - 30 >= 0:
            candidates.append(dp[d - 30] + costs[2])
        else:
            candidates.append(costs[2])
        dp[d] = min(candidates)
    return dp[last_day]


# =============================================================================
# WAY 19: In-place DP (no extra array)
# =============================================================================
def mincost_tickets_19(days, costs):
    """Use dict instead of array."""
    last_day = days[-1]
    dp = {0: 0}
    travel_set = set(days)
    for d in range(1, last_day + 1):
        if d not in travel_set:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last_day]


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def mincost_tickets_20(days, costs):
    """
    Final clean version.

    Algorithm:
    1. dp[d] = min cost to cover all travel days from day 1 to day d.
    2. For each day d from 1 to last_day:
       If d is not a travel day: dp[d] = dp[d-1].
       Else: dp[d] = min(dp[d-1] + 1-day, dp[d-7] + 7-day, dp[d-30] + 30-day).

    Why this works:
    - On a travel day, we need to cover it with one of three pass types.
    - 1-day pass: covers only day d.
    - 7-day pass: covers days d-6 to d. So dp[d-7] was the cost BEFORE this pass.
    - 30-day pass: covers days d-29 to d. So dp[d-30] was the cost BEFORE.

    Time:  O(last_day) = O(365) since days are in 1..365.
    Space: O(last_day).

    Edge cases:
    - days has 1 element: simple.
    - All consecutive days: 30-day pass likely cheapest.
    - d-7 or d-30 < 0: clamp to 0.
    """
    travel_set = set(days)
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    for d in range(1, last_day + 1):
        if d not in travel_set:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last_day]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the minimum cost to cover all travel days using 1-day, 7-day,
or 30-day passes."

Key Insight:
"Standard DP. dp[d] = min cost to cover all travel days from 1 to d.
For each day, decide which pass to buy (if it's a travel day)."

Algorithm:
"1. dp[d] = min cost up to day d.
2. For d in 1..last_day:
   - If d not in days: dp[d] = dp[d-1].
   - Else: dp[d] = min(dp[d-1] + 1-day, dp[d-7] + 7-day, dp[d-30] + 30-day)."

Why this works:
"On a travel day, we need a pass covering it. A 7-day pass bought today
covers days d-6 to d. The cost BEFORE buying this pass was dp[d-7] (i.e.,
everything up to 7 days ago). Same for 30-day."

Edge cases:
- Single day: simple min.
- All consecutive: 30-day usually best.
- d-7 or d-30 < 0: clamp to 0.

Complexity:
- Time:  O(last_day) = O(365).
- Space: O(last_day).

KEY TRICK:
The recurrence dp[d] = min(dp[d-1] + c0, dp[d-7] + c1, dp[d-30] + c2) handles
all three pass options.

ALTERNATIVE: Iterate only over travel days (Way 5)
Slightly different state: dp[i] = min cost to cover first i travel days.

ALTERNATIVE: Binary search (Way 17)
Use bisect to find previous travel days when considering 7/30-day passes.

INTERVIEW TIPS:
1. Recognize DP with bounded horizon (1, 7, 30 days).
2. Use a set for O(1) travel-day lookup.
3. Clamp to 0 when d-7 or d-30 < 0.

RELATIONSHIP TO OTHER PROBLEMS:
- Coin Change (LC 322): Similar DP structure.
- House Robber variants: Different recurrence.
- Minimum Cost For Tickets II: Different durations.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: DP + set (BEST)", mincost_tickets_1),
        ("Way 2: Verbose", mincost_tickets_2),
        ("Way 3: DP + index", mincost_tickets_3),
        ("Way 4: Top-down memo", mincost_tickets_4),
        ("Way 5: DP over travel days", mincost_tickets_5),
        ("Way 6: Class-based", mincost_tickets_6),
        ("Way 7: numpy", mincost_tickets_7),
        ("Way 8: While loop", mincost_tickets_8),
        ("Way 9: Helper min_three", mincost_tickets_9),
        ("Way 10: Recursive memo", mincost_tickets_10),
        ("Way 11: lru_cache", mincost_tickets_11),
        ("Way 12: Bool array", mincost_tickets_12),
        ("Way 13: Functional", mincost_tickets_13),
        ("Way 14: Sorted days", mincost_tickets_14),
        ("Way 15: Most concise", mincost_tickets_15),
        ("Way 16: enumerate", mincost_tickets_16),
        ("Way 17: Binary search", mincost_tickets_17),
        ("Way 18: Tabulation", mincost_tickets_18),
        ("Way 19: Dict DP", mincost_tickets_19),
        ("Way 20: Final cleanest", mincost_tickets_20),
    ]

    test_cases = [
        # Standard example 1
        # days=[1,4,6,7,8,20], costs=[2,7,15]
        # 1-day for 1 (2), 7-day for 4-10 (covers 4,6,7,8) (7), 1-day for 20 (2)
        # Total: 2+7+2 = 11
        ([1, 4, 6, 7, 8, 20], [2, 7, 15], 11),

        # Standard example 2
        # days=[1,2,3,4,5,6,7,8,9,10,30,31], costs=[2,7,15]
        # 30-day for 1-30 (15), 1-day for 31 (2) = 17
        # OR 7-day for 1-7 (7), 7-day for 8-14 (7), 1-day for 30 (2), 1-day for 31 (2) = 18
        # OR 7-day for 1-7 (7), 1-day each for 8-10 (6), 30-day for 30-... no wait, 30-day starts day 30
        # Let's trace: 7-day for 1-7 (7), then days 8-10 need 1-day each (6), day 30: 1-day (2), day 31: 1-day (2). Total 7+6+4 = 17.
        # Or: 30-day for 1-30 (15), 1-day for 31 (2) = 17.
        # Or: 7-day for 4-10 (covers 4,5,6,7,8,9,10) (7), 1-day for 1 (2), 1-day for 2 (2), 1-day for 3 (2), 30-day for 30 (15), 1-day for 31 (2). Total 30.
        # Best = 17.
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 30, 31], [2, 7, 15], 17),

        # Single day
        # days=[1], costs=[2,7,15]. 1-day = 2. Total = 2.
        ([1], [2, 7, 15], 2),

        # Two consecutive days
        # days=[1,2], costs=[2,7,15]. 1-day+1-day=4. 7-day=7. Best=4.
        ([1, 2], [2, 7, 15], 4),

        # Two consecutive days (small cost)
        # days=[1,2], costs=[2,5,15]. 1+1=4, 7-day=5. Best=4.
        ([1, 2], [2, 5, 15], 4),

        # Single day, very expensive 1-day but cheap 7-day
        # days=[5], costs=[10,1,100]. 1-day=10, 7-day=1. Best=1.
        ([5], [10, 1, 100], 1),

        # Spread over month
        # days=[1,4,6,7,8,20], costs=[3,10,30]
        # 1-day for 1 (3), 7-day for 4-10 (covers 4,6,7,8) (10), 1-day for 20 (3)
        # Total: 3+10+3 = 16
        # Or 30-day for 1-30 (30) covering everything = 30. Worse.
        ([1, 4, 6, 7, 8, 20], [3, 10, 30], 16),

        # All consecutive 7 days
        # days=[1,2,3,4,5,6,7], costs=[2,7,15]
        # 7-day for 1-7 = 7. 1-day each = 14. Best = 7.
        ([1, 2, 3, 4, 5, 6, 7], [2, 7, 15], 7),

        # All consecutive 8 days
        # days=[1,2,3,4,5,6,7,8], costs=[2,7,15]
        # Two 7-day = 14. 30-day = 15. 8 1-days = 16. Best = 14.
        # OR 7-day for 2-8 (covers 2-8) + 1-day for 1 = 7+2 = 9. Better!
        # Let me trace:
        # d=1: 1-day (2). dp[1]=2.
        # d=2: 1-day (4), 7-day (7). dp[2]=4. But actually dp[2-7]+7 = dp[0]+7 = 7. Hmm.
        # Wait dp[d-7] when d=2 is dp[0]+7 = 7. But min(4, 7) = 4.
        # Hmm but 7-day covers 2 days -4 to 2, which is days 2 only (since 1-(-4) to 2).
        # Actually a 7-day pass on day 2 covers days 2 through 8 (inclusive), so covers 2-8.
        # dp[max(0, 2-7)] = dp[0] = 0. So 7-day = 0 + 7 = 7.
        # dp[2] = min(4, 7) = 4.
        # d=3: dp[2]+2=6, dp[0]+7=7. dp[3]=6.
        # d=4: dp[3]+2=8, dp[0]+7=7. dp[4]=7.
        # d=5: dp[4]+2=9, dp[0]+7=7. dp[5]=7.
        # d=6: dp[5]+2=9, dp[0]+7=7. dp[6]=7.
        # d=7: dp[6]+2=9, dp[0]+7=7. dp[7]=7.
        # d=8: dp[7]+2=9, dp[1]+7=9. dp[8]=9. Wait, dp[max(0,8-7)]=dp[1]=2, so 2+7=9.
        # 1-day at 8 = 9. 7-day at 8 = 9. Hmm.
        # But wait, we could buy a 7-day pass at day 2 covering days 2-8.
        # dp[max(0, 8-7)] = dp[1] = 2 (cost up to day 1 = 1-day for day 1 = 2).
        # Then 7-day for days 2-8 = 7. Total = 2 + 7 = 9.
        # Alternative: 1-day for day 1 = 2. Then 7-day for days 2-8 = 7. Total = 9.
        # Alternative: 7-day for days 1-7 = 7, 1-day for day 8 = 2. Total = 9.
        # All give 9.
        # Actually wait, dp[max(0, d-7)] when d=2 should give dp[max(0, -5)] = dp[0] = 0.
        # And dp[d-1]+1-day for d=2 = dp[1]+2 = 2+2 = 4.
        # min(4, 7) = 4. dp[2] = 4.
        # d=3: dp[2]+2=6, dp[0]+7=7. dp[3]=6.
        # d=4: dp[3]+2=8, dp[0]+7=7. dp[4]=7.
        # d=5: dp[4]+2=9, dp[0]+7=7. dp[5]=7.
        # d=6: dp[5]+2=9, dp[0]+7=7. dp[6]=7.
        # d=7: dp[6]+2=9, dp[0]+7=7. dp[7]=7.
        # d=8: dp[7]+2=9, dp[1]+7=9, dp[0]+15=15. dp[8]=9.
        # Answer = 9. Wait but 30-day for 1-30 = 15? No, dp[max(0,8-30)]=dp[0]=0, so 0+15=15. min(9,15)=9.
        # So answer is 9.
        ([1, 2, 3, 4, 5, 6, 7, 8], [2, 7, 15], 9),

        # 30-day better than 7-day
        # days=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], costs=[7,20,30]
        # 30-day = 30. 7-day each ~ 40. 1-day each = 105. Best = 30.
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], [7, 20, 30], 30),
    ]

    print("=" * 70)
    print("MINIMUM COST FOR TICKETS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-cost-for-tickets")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for days, costs, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(days), copy.deepcopy(costs))
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: days={days}, costs={costs} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on days={days}, costs={costs} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)