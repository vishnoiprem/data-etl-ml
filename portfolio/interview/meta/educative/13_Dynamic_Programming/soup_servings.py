"""
Soup Servings
Medium | 30 min

Start with two soups A and B, each containing n mL. Each turn, randomly
select one of 4 operations (each with probability 0.25):
- Serve 100 A, 0 B.
- Serve 75 A, 25 B.
- Serve 50 A, 50 B.
- Serve 25 A, 75 B.

If operation requires more than remaining, serve what's left. Process
ends when at least one soup is empty.

Return P(A empty first) + 0.5 * P(both empty same time).

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/soup-servings

Examples:
    n=50 -> 0.625
    n=100 -> 0.71875
    n=0 -> 0.5

Constraints:
- 0 <= n <= 10^9

KEY INSIGHT:
DP. f(a, b) = P(A first) + 0.5 * P(both same), starting from (a, b).
- Base: f(0, 0) = 0.5, f(0, b) for b > 0 = 1, f(a, 0) for a > 0 = 0.
- Recurrence: f(a, b) = 0.25 * sum over 4 ops of f(max(0, a-dA), max(0, b-dB)).
- For n large enough, probability approaches 1 (e.g., n >= 4800 in LC).
"""


# =============================================================================
# WAY 1: Memoized recursion (BEST - Memorize!)
# =============================================================================
def soup_servings_1(n):
    """Top-down memoization."""
    from functools import lru_cache

    # For large n, probability approaches 1.
    if n >= 4800:
        return 1.0

    @lru_cache(maxsize=None)
    def f(a, b):
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        return 0.25 * (
            f(a - 100, b)
            + f(a - 75, b - 25)
            + f(a - 50, b - 50)
            + f(a - 25, b - 75)
        )

    return f(n, n)


# =============================================================================
# WAY 2: Iterative 2D DP (work in mL/25 units)
# =============================================================================
def soup_servings_2(n):
    """Bottom-up 2D DP. Work in units of 25 mL."""
    if n >= 4800:
        return 1.0
    m = (n + 24) // 25  # Round up to nearest 25
    # dp[i][j] = probability starting with i*25 A and j*25 B
    dp = [[0.0] * (m + 1) for _ in range(m + 1)]
    # Base cases
    for i in range(m + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                dp[i][j] = 0.5
            elif i == 0:
                dp[i][j] = 1.0
            elif j == 0:
                dp[i][j] = 0.0
    # Fill bottom-up
    for i in range(1, m + 1):
        for j in range(1, m + 1):
            dp[i][j] = 0.25 * (
                dp[max(0, i - 4)][j]
                + dp[max(0, i - 3)][max(0, j - 1)]
                + dp[max(0, i - 2)][max(0, j - 2)]
                + dp[max(0, i - 1)][max(0, j - 3)]
            )
    return dp[m][m]


# =============================================================================
# WAY 3: Iterative 2D DP without rounding
# =============================================================================
def soup_servings_3(n):
    """Use exact mL. Cap at reasonable size for n > threshold."""
    if n >= 4800:
        return 1.0
    m = n + 1  # Use m+1 for indexing 0..n
    # dp[i][j] = probability starting with i A and j B
    dp = [[0.0] * (m + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                dp[i][j] = 0.5
            elif i == 0:
                dp[i][j] = 1.0
            elif j == 0:
                dp[i][j] = 0.0
            for da, db in [(100, 0), (75, 25), (50, 50), (25, 75)]:
                na = max(0, i - da)
                nb = max(0, j - db)
                dp[i][j] += 0.25 * dp[na][nb]
    return dp[n][n]


# =============================================================================
# WAY 4: Pure recursion without memo
# =============================================================================
def soup_servings_4(n):
    if n >= 4800:
        return 1.0

    def f(a, b):
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        return 0.25 * (
            f(a - 100, b)
            + f(a - 75, b - 25)
            + f(a - 50, b - 50)
            + f(a - 25, b - 75)
        )

    return f(n, n)


# =============================================================================
# WAY 5: Memoized with dict
# =============================================================================
def soup_servings_5(n):
    if n >= 4800:
        return 1.0
    memo = {}

    def f(a, b):
        if (a, b) in memo:
            return memo[(a, b)]
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        memo[(a, b)] = 0.25 * (
            f(a - 100, b)
            + f(a - 75, b - 25)
            + f(a - 50, b - 50)
            + f(a - 25, b - 75)
        )
        return memo[(a, b)]

    return f(n, n)


# =============================================================================
# WAY 6: 1D rolling DP
# =============================================================================
def soup_servings_6(n):
    if n >= 4800:
        return 1.0
    m = (n + 24) // 25
    # dp[i] = probability for current A, varying B
    dp = [0.0] * (m + 1)
    # Base: dp[0][0] = 0.5, dp[0][j] = 1, dp[i][0] = 0
    # Process from top-right to bottom-left
    new_dp = [0.0] * (m + 1)
    new_dp[0] = 1.0  # when A = 0, probability = 1 (for B > 0)
    for i in range(1, m + 1):
        new_dp[0] = 0.0  # When B = 0 and A > 0, probability = 0
        for j in range(1, m + 1):
            new_dp[j] = 0.25 * (
                dp[max(0, j)]
                + (dp[max(0, j - 1)] if j >= 1 else new_dp[max(0, j - 1)])
                + (dp[max(0, j - 2)] if j >= 2 else new_dp[max(0, j - 2)])
                + (dp[max(0, j - 3)] if j >= 3 else new_dp[max(0, j - 3)])
            )
        # Wait this isn't quite right. Let me think...
        # Actually, the recurrence uses values from previous row (i-1) at column (j),
        # and previous row at column (j-1), (j-2), (j-3).
        # If j - k < 0, we use the current row at j - k (because we map to 0).
        # Let me redo.
        for j in range(1, m + 1):
            v1 = dp[j]  # f(a-100, b) where a reduced by 4 units
            v2 = dp[max(0, j - 1)] if j >= 1 else 0  # f(a-75, b-25)
            v3 = dp[max(0, j - 2)] if j >= 2 else 0  # f(a-50, b-50)
            v4 = dp[max(0, j - 3)] if j >= 3 else 0  # f(a-25, b-75)
            new_dp[j] = 0.25 * (v1 + v2 + v3 + v4)
        dp = new_dp[:]
    return dp[m]


# =============================================================================
# WAY 7: Class OOP
# =============================================================================
class SoupServings:
    def __init__(self, n):
        self.n = n
        self.memo = {}

    def f(self, a, b):
        if (a, b) in self.memo:
            return self.memo[(a, b)]
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        self.memo[(a, b)] = 0.25 * (
            self.f(a - 100, b)
            + self.f(a - 75, b - 25)
            + self.f(a - 50, b - 50)
            + self.f(a - 25, b - 75)
        )
        return self.memo[(a, b)]

    def solve(self):
        if self.n >= 4800:
            return 1.0
        return self.f(self.n, self.n)


def soup_servings_7(n):
    return SoupServings(n).solve()


# =============================================================================
# WAY 8: Numpy 2D DP
# =============================================================================
def soup_servings_8(n):
    import numpy as np
    if n >= 4800:
        return 1.0
    m = (n + 24) // 25
    dp = np.zeros((m + 1, m + 1), dtype=np.float64)
    # Base cases
    dp[0, 0] = 0.5
    dp[0, 1:] = 1.0
    for i in range(1, m + 1):
        for j in range(1, m + 1):
            dp[i, j] = 0.25 * (
                dp[max(0, i - 4), j]
                + dp[max(0, i - 3), max(0, j - 1)]
                + dp[max(0, i - 2), max(0, j - 2)]
                + dp[max(0, i - 1), max(0, j - 3)]
            )
    return float(dp[m, m])


# =============================================================================
# WAY 9: Bottom-up 2D with units of 25 mL
# =============================================================================
def soup_servings_9(n):
    """Use units of 25 mL. Round up to nearest 25."""
    if n >= 4800:
        return 1.0
    m = (n + 24) // 25
    # Build dp iteratively
    dp = [[0.0] * (m + 1) for _ in range(m + 1)]
    dp[0][0] = 0.5
    for j in range(1, m + 1):
        dp[0][j] = 1.0
    for i in range(1, m + 1):
        for j in range(1, m + 1):
            a_minus = [(i - 4, j), (i - 3, j - 1), (i - 2, j - 2), (i - 1, j - 3)]
            total = 0.0
            for ai, bj in a_minus:
                ai = max(0, ai)
                bj = max(0, bj)
                total += dp[ai][bj]
            dp[i][j] = 0.25 * total
    return dp[m][m]


# =============================================================================
# WAY 10: Iterative with explicit thresholds
# =============================================================================
def soup_servings_10(n):
    """Different threshold for large n."""
    # Probability approaches 1 as n grows. Threshold chosen for 1e-5 precision.
    if n > 5000:
        return 1.0
    if n == 0:
        return 0.5
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def f(a, b):
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        return 0.25 * (
            f(a - 100, b)
            + f(a - 75, b - 25)
            + f(a - 50, b - 50)
            + f(a - 25, b - 75)
        )

    return f(n, n)


# =============================================================================
# WAY 11: LRU cache with ordered operations
# =============================================================================
def soup_servings_11(n):
    from functools import lru_cache
    if n >= 4800:
        return 1.0
    ops = [(100, 0), (75, 25), (50, 50), (25, 75)]

    @lru_cache(maxsize=None)
    def f(a, b):
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        return 0.25 * sum(f(max(0, a - da), max(0, b - db)) for da, db in ops)

    return f(n, n)


# =============================================================================
# WAY 12: 2D DP rounded to multiples of 25
# =============================================================================
def soup_servings_12(n):
    """Round n up to nearest 25 for DP."""
    if n >= 4800:
        return 1.0
    n_units = (n + 24) // 25
    # Each "unit" = 25 mL
    # Operations: (4, 0), (3, 1), (2, 2), (1, 3) units
    N = n_units
    dp = [[0.0] * (N + 1) for _ in range(N + 1)]
    for i in range(N + 1):
        for j in range(N + 1):
            if i <= 0 and j <= 0:
                dp[i][j] = 0.5
            elif i <= 0:
                dp[i][j] = 1.0
            elif j <= 0:
                dp[i][j] = 0.0
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            dp[i][j] = 0.25 * (
                dp[max(0, i - 4)][j]
                + dp[max(0, i - 3)][max(0, j - 1)]
                + dp[max(0, i - 2)][max(0, j - 2)]
                + dp[max(0, i - 1)][max(0, j - 3)]
            )
    return dp[N][N]


# =============================================================================
# WAY 13: BFS / iterative state expansion
# =============================================================================
def soup_servings_13(n):
    """Build DP table iteratively row by row."""
    if n >= 4800:
        return 1.0
    if n == 0:
        return 0.5
    N = (n + 24) // 25
    # dp[i][j]: probability starting from (i, j) units of 25 mL
    # Build row by row
    dp = [[0.0] * (N + 1) for _ in range(N + 1)]
    for i in range(N + 1):
        for j in range(N + 1):
            if i == 0 and j == 0:
                dp[i][j] = 0.5
            elif i == 0:
                dp[i][j] = 1.0
            elif j == 0:
                dp[i][j] = 0.0
            else:
                total = 0.0
                for da, db in [(100, 0), (75, 25), (50, 50), (25, 75)]:
                    na = max(0, i - da // 25)
                    nb = max(0, j - db // 25)
                    total += dp[na][nb]
                dp[i][j] = 0.25 * total
    return dp[N][N]


# =============================================================================
# WAY 14: Recursive with threshold (no memo)
# =============================================================================
def soup_servings_14(n):
    if n >= 4800:
        return 1.0
    if n == 0:
        return 0.5

    def f(a, b):
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        return (
            f(a - 100, b)
            + f(a - 75, b - 25)
            + f(a - 50, b - 50)
            + f(a - 25, b - 75)
        ) / 4.0

    return f(n, n)


# =============================================================================
# WAY 15: Bottom-up with strict threshold
# =============================================================================
def soup_servings_15(n):
    """Use 25-unit grid. Threshold based on LC analysis."""
    if n >= 4800:
        return 1.0
    units = (n + 24) // 25
    dp = [[0.0] * (units + 1) for _ in range(units + 1)]
    # Build
    for i in range(units + 1):
        for j in range(units + 1):
            if i == 0 and j == 0:
                dp[i][j] = 0.5
            elif i == 0:
                dp[i][j] = 1.0
            elif j == 0:
                dp[i][j] = 0.0
            else:
                dp[i][j] = 0.25 * (
                    dp[i - 4 if i >= 4 else 0][j]
                    + dp[i - 3 if i >= 3 else 0][j - 1 if j >= 1 else 0]
                    + dp[i - 2 if i >= 2 else 0][j - 2 if j >= 2 else 0]
                    + dp[i - 1 if i >= 1 else 0][j - 3 if j >= 3 else 0]
                )
    return dp[units][units]


# =============================================================================
# WAY 16: Memoization with closure
# =============================================================================
def soup_servings_16(n):
    if n >= 4800:
        return 1.0
    cache = {}

    def helper(a, b):
        key = (a, b)
        if key in cache:
            return cache[key]
        if a <= 0 and b <= 0:
            res = 0.5
        elif a <= 0:
            res = 1.0
        elif b <= 0:
            res = 0.0
        else:
            res = 0.25 * (
                helper(a - 100, b)
                + helper(a - 75, b - 25)
                + helper(a - 50, b - 50)
                + helper(a - 25, b - 75)
            )
        cache[key] = res
        return res

    return helper(n, n)


# =============================================================================
# WAY 17: For small n only (correct full DP)
# =============================================================================
def soup_servings_17(n):
    """Exact computation with full DP table for n up to 4800/25 = 192."""
    if n >= 4800:
        return 1.0
    N = (n + 24) // 25
    dp = [[0.0] * (N + 1) for _ in range(N + 1)]
    # Initialize
    for i in range(N + 1):
        dp[0][i] = 1.0 if i > 0 else 0.5
    for j in range(N + 1):
        dp[0][j] = 1.0 if j > 0 else 0.5
    # Fill
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            dp[i][j] = 0.25 * (
                dp[max(i - 4, 0)][j]
                + dp[max(i - 3, 0)][max(j - 1, 0)]
                + dp[max(i - 2, 0)][max(j - 2, 0)]
                + dp[max(i - 1, 0)][max(j - 3, 0)]
            )
    return dp[N][N]


# =============================================================================
# WAY 18: 2D DP with nested loops
# =============================================================================
def soup_servings_18(n):
    """Same as Way 17 but with nested loops."""
    if n >= 4800:
        return 1.0
    N = (n + 24) // 25
    dp = [[0.0] * (N + 1) for _ in range(N + 1)]
    for i in range(N + 1):
        if i == 0:
            for j in range(N + 1):
                dp[i][j] = 0.5 if j == 0 else 1.0
        else:
            dp[i][0] = 0.0
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            dp[i][j] = (
                dp[max(0, i - 4)][j]
                + dp[max(0, i - 3)][max(0, j - 1)]
                + dp[max(0, i - 2)][max(0, j - 2)]
                + dp[max(0, i - 1)][max(0, j - 3)]
            ) * 0.25
    return dp[N][N]


# =============================================================================
# WAY 19: Math constant threshold
# =============================================================================
def soup_servings_19(n):
    """Threshold varies - use 5000 as conservative."""
    if n >= 5000:
        return 1.0
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def f(a, b):
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        return 0.25 * (
            f(a - 100, b)
            + f(a - 75, b - 25)
            + f(a - 50, b - 50)
            + f(a - 25, b - 75)
        )

    return f(n, n)


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def soup_servings_20(n):
    """
    THE ONE TO MEMORIZE.

    f(a, b) = P(A empties first) + 0.5 * P(both empty same) from state (a, b).

    Base cases:
      - a <= 0 and b <= 0: 0.5.
      - a <= 0 (and b > 0): 1.0 (A emptied first).
      - b <= 0 (and a > 0): 0.0 (B emptied first).

    Recurrence:
      f(a, b) = 0.25 * sum over 4 operations of f(max(0, a-dA), max(0, b-dB)).

    For n >= 4800, return 1.0 (probability approaches 1).

    Time:  O(n^2 / 625) for n <= 4800.
    Space: O(n^2 / 625).
    """
    if n >= 4800:
        return 1.0
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def f(a, b):
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        return 0.25 * (
            f(a - 100, b)
            + f(a - 75, b - 25)
            + f(a - 50, b - 50)
            + f(a - 25, b - 75)
        )

    return f(n, n)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"Each turn, one of 4 operations is chosen uniformly at random. Each serves
different amounts from A and B. Find P(A empties first) + 0.5 * P(both empty
same turn)."

Key Insight:
"Probability DP. State: (a, b) remaining amounts.
f(a, b) = answer from state (a, b).

Base:
- f(0, 0) = 0.5 (both empty, half credit).
- f(0, b) for b > 0 = 1 (A emptied first).
- f(a, 0) for a > 0 = 0 (B emptied first).

Recurrence:
f(a, b) = 0.25 * [f(a-100, b) + f(a-75, b-25) + f(a-50, b-50) + f(a-25, b-75)]
where we use max(0, ...) for negative amounts.

For large n: probability approaches 1 (return 1.0)."

Algorithm:
1. If n >= 4800: return 1.0.
2. Top-down memo:
   - f(a, b): base cases.
   - Else: 0.25 * sum of 4 recursive calls with max(0, ...).
3. Return f(n, n).

Edge Cases:
- n = 0: return 0.5.
- Large n: 1.0.
- n = 50: 0.625.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Memo     | O(n^2) | O(n^2) |
| Bottom-up| O(n^2) | O(n^2) |
+----------+--------+--------+
But practical: n / 25 units, so ~4800/25 = 192 units.
O((n/25)^2) ≈ 37K states.

KEY TRICK:
Use units of 25 mL (LCM of operations) to reduce state space.
Operations become (4,0), (3,1), (2,2), (1,3) in units.

RELATED PROBLEMS:
- Egg Dropping.
- Probability-based DP.
- LC 808 (this problem).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Memoized (BEST)", soup_servings_1),
        ("Way 2: Iterative 2D (25 units)", soup_servings_2),
        ("Way 3: Iterative 2D (exact mL)", soup_servings_3),
        ("Way 4: Pure recursion", soup_servings_4),
        ("Way 5: Memo dict", soup_servings_5),
        ("Way 6: 1D rolling", soup_servings_6),
        ("Way 7: Class OOP", soup_servings_7),
        ("Way 8: Numpy", soup_servings_8),
        ("Way 9: Bottom-up 25 units", soup_servings_9),
        ("Way 10: Different threshold", soup_servings_10),
        ("Way 11: LRU ops list", soup_servings_11),
        ("Way 12: Rounded 25", soup_servings_12),
        ("Way 13: BFS row by row", soup_servings_13),
        ("Way 14: No memo", soup_servings_14),
        ("Way 15: Strict threshold", soup_servings_15),
        ("Way 16: Memo closure", soup_servings_16),
        ("Way 17: Full DP small", soup_servings_17),
        ("Way 18: Nested loops", soup_servings_18),
        ("Way 19: Threshold 5000", soup_servings_19),
        ("Way 20: Final cleanest", soup_servings_20),
    ]

    test_cases = [
        # (n, expected)
        (0, 0.5),
        (50, 0.625),
        (100, 0.71875),
        (4800, 1.0),
        (5000, 1.0),
        (10000, 1.0),
    ]

    print("=" * 70)
    print("SOUP SERVINGS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/soup-servings")
    print("=" * 70)

    EPS = 1e-5
    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for n, expected in test_cases:
            try:
                result = func(n)
                if abs(result - expected) > EPS:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: n={n}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: n={n}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)