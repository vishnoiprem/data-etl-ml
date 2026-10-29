"""
Longest Common Subsequence
Medium | 30 min

Given two strings str1 and str2, return the length of the longest
common subsequence. Return 0 if no common subsequence.

A subsequence is formed by deleting zero or more characters while
preserving order.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-common-subsequence

Examples:
    s1='abcde', s2='ace' -> 3   ('ace')
    s1='abc',  s2='abc'  -> 3
    s1='abc',  s2='def'  -> 0
    s1='bl',   s2='yby'  -> 1   ('b')
    s1='',     s2='abc'  -> 0

Constraints:
- 1 <= str1.length, str2.length <= 500
- Lowercase English letters.

KEY INSIGHT:
2D DP. dp[i][j] = LCS length of s1[0..i-1] and s2[0..j-1].
- Base: dp[0][j] = 0, dp[i][0] = 0.
- Transition:
  - If s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1.
  - Else: dp[i][j] = max(dp[i-1][j], dp[i][j-1]).
- Final: dp[n][m].

Time: O(n*m). Space: O(n*m) or O(min(n,m)) rolling.
"""


# =============================================================================
# WAY 1: 2D DP (BEST - Memorize!)
# =============================================================================
def lcs_1(s1, s2):
    """Standard 2D DP."""
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


# =============================================================================
# WAY 2: 1D DP rolling (space-optimized)
# =============================================================================
def lcs_2(s1, s2):
    """1D DP. Outer loop on s1, inner on s2."""
    n, m = len(s1), len(s2)
    dp = [0] * (m + 1)
    for i in range(1, n + 1):
        prev_diag = 0  # dp[i-1][j-1]
        for j in range(1, m + 1):
            temp = dp[j]
            if s1[i - 1] == s2[j - 1]:
                dp[j] = prev_diag + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev_diag = temp
    return dp[m]


# =============================================================================
# WAY 3: Top-down memoization
# =============================================================================
def lcs_3(s1, s2):
    """DFS + @lru_cache on (i, j)."""
    n, m = len(s1), len(s2)
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def dfs(i, j):
        if i == n or j == m:
            return 0
        if s1[i] == s2[j]:
            return 1 + dfs(i + 1, j + 1)
        return max(dfs(i + 1, j), dfs(i, j + 1))

    return dfs(0, 0)


# =============================================================================
# WAY 4: Memo dict (explicit)
# =============================================================================
def lcs_4(s1, s2):
    """Same as Way 3 but with explicit dict."""
    n, m = len(s1), len(s2)
    memo = {}

    def dfs(i, j):
        if (i, j) in memo:
            return memo[(i, j)]
        if i == n or j == m:
            return 0
        if s1[i] == s2[j]:
            memo[(i, j)] = 1 + dfs(i + 1, j + 1)
        else:
            memo[(i, j)] = max(dfs(i + 1, j), dfs(i, j + 1))
        return memo[(i, j)]

    return dfs(0, 0)


# =============================================================================
# WAY 5: Bottom-up with explicit base row
# =============================================================================
def lcs_5(s1, s2):
    """Same as Way 1 but with verbose base."""
    n, m = len(s1), len(s2)
    if n == 0 or m == 0:
        return 0
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    # Base already 0.
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


# =============================================================================
# WAY 6: 1D DP, swap so s2 is shorter
# =============================================================================
def lcs_6(s1, s2):
    """Ensure s1 is shorter for O(min(n,m)) space."""
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    n, m = len(s1), len(s2)
    dp = [0] * (m + 1)
    for i in range(1, n + 1):
        prev_diag = 0
        for j in range(1, m + 1):
            temp = dp[j]
            if s1[i - 1] == s2[j - 1]:
                dp[j] = prev_diag + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev_diag = temp
    return dp[m]


# =============================================================================
# WAY 7: Class OOP
# =============================================================================
class LCSFinder:
    def __init__(self, s1, s2):
        self.s1 = s1
        self.s2 = s2

    def solve(self):
        s1, s2 = self.s1, self.s2
        n, m = len(s1), len(s2)
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        return dp[n][m]


def lcs_7(s1, s2):
    return LCSFinder(s1, s2).solve()


# =============================================================================
# WAY 8: Recursive with explicit closure
# =============================================================================
def lcs_8(s1, s2):
    n, m = len(s1), len(s2)
    memo = {}

    def helper(i, j):
        key = (i, j)
        if key in memo:
            return memo[key]
        if i == n or j == m:
            res = 0
        elif s1[i] == s2[j]:
            res = 1 + helper(i + 1, j + 1)
        else:
            res = max(helper(i + 1, j), helper(i, j + 1))
        memo[key] = res
        return res

    return helper(0, 0)


# =============================================================================
# WAY 9: Bottom-up with diagonal traversal
# =============================================================================
def lcs_9(s1, s2):
    """Iterate by sum of indices (diagonal order)."""
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for total in range(2, n + m + 1):
        for i in range(1, min(total, n) + 1):
            j = total - i
            if j < 1 or j > m:
                continue
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


# =============================================================================
# WAY 10: Iterative with rows reversed
# =============================================================================
def lcs_10(s1, s2):
    """Iterate i from n down to 1, j from m down to 1."""
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if s1[i] == s2[j]:
                dp[i][j] = dp[i + 1][j + 1] + 1
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])
    return dp[0][0]


# =============================================================================
# WAY 11: BFS - reachability
# =============================================================================
def lcs_11(s1, s2):
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


# =============================================================================
# WAY 12: 1D DP double buffer
# =============================================================================
def lcs_12(s1, s2):
    """Use two arrays, swap each row."""
    n, m = len(s1), len(s2)
    prev = [0] * (m + 1)
    cur = [0] * (m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                cur[j] = prev[j - 1] + 1
            else:
                cur[j] = max(prev[j], cur[j - 1])
        prev, cur = cur, [0] * (m + 1)
    return prev[m]


# =============================================================================
# WAY 13: Bottom-up loop with explicit if-else
# =============================================================================
def lcs_13(s1, s2):
    n, m = len(s1), len(s2)
    if not n or not m:
        return 0
    dp = [[0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            if s1[i] == s2[j]:
                if i == 0 or j == 0:
                    dp[i][j] = 1
                else:
                    dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                a = dp[i - 1][j] if i > 0 else 0
                b = dp[i][j - 1] if j > 0 else 0
                dp[i][j] = max(a, b)
    return dp[n - 1][m - 1]


# =============================================================================
# WAY 14: Numpy 2D DP
# =============================================================================
def lcs_14(s1, s2):
    import numpy as np
    n, m = len(s1), len(s2)
    dp = np.zeros((n + 1, m + 1), dtype=np.int32)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i, j] = dp[i - 1, j - 1] + 1
            else:
                dp[i, j] = max(dp[i - 1, j], dp[i, j - 1])
    return int(dp[n, m])


# =============================================================================
# WAY 15: Memo with closure-style
# =============================================================================
def lcs_15(s1, s2):
    """Memo with closure and pre-fill base cases."""
    n, m = len(s1), len(s2)
    memo = {(i, m): 0 for i in range(n + 1)}
    memo.update({(n, j): 0 for j in range(m + 1)})

    def helper(i, j):
        if (i, j) in memo:
            return memo[(i, j)]
        if s1[i] == s2[j]:
            memo[(i, j)] = 1 + helper(i + 1, j + 1)
        else:
            memo[(i, j)] = max(helper(i + 1, j), helper(i, j + 1))
        return memo[(i, j)]

    return helper(0, 0)


# =============================================================================
# WAY 16: 2D DP with sorted indices
# =============================================================================
def lcs_16(s1, s2):
    """Same as Way 1 but different iteration order."""
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp_i = dp[i]
        dp_im1 = dp[i - 1]
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp_i[j] = dp_im1[j - 1] + 1
            else:
                dp_i[j] = dp_im1[j] if dp_im1[j] > dp_i[j - 1] else dp_i[j - 1]
    return dp[n][m]


# =============================================================================
# WAY 17: Pure recursion (no memo) - exponential
# =============================================================================
def lcs_17(s1, s2):
    """Brute force recursion."""

    def dfs(i, j):
        if i == len(s1) or j == len(s2):
            return 0
        if s1[i] == s2[j]:
            return 1 + dfs(i + 1, j + 1)
        return max(dfs(i + 1, j), dfs(i, j + 1))

    return dfs(0, 0)


# =============================================================================
# WAY 18: Bottom-up with smaller first loop
# =============================================================================
def lcs_18(s1, s2):
    """Outer loop on smaller string for cache locality."""
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


# =============================================================================
# WAY 19: 2D DP with explicit row/col initialization
# =============================================================================
def lcs_19(s1, s2):
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    # Already initialized 0
    for i in range(n):
        for j in range(m):
            if s1[i] == s2[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
    return dp[n][m]


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def lcs_20(s1, s2):
    """
    THE ONE TO MEMORIZE.

    dp[i][j] = LCS length of s1[0..i-1] and s2[0..j-1].

    Base: dp[0][*] = dp[*][0] = 0.

    Transition:
      if s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1
      else:                  dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    Time:  O(n*m)
    Space: O(min(n,m)) with rolling array.
    """
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    n, m = len(s1), len(s2)
    dp = [0] * (m + 1)
    for i in range(1, n + 1):
        prev_diag = 0
        for j in range(1, m + 1):
            temp = dp[j]
            if s1[i - 1] == s2[j - 1]:
                dp[j] = prev_diag + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev_diag = temp
    return dp[m]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"Find the length of the longest common subsequence of two strings."

Key Insight:
"2D DP. dp[i][j] = LCS length of s1[0..i-1] and s2[0..j-1].

Base: dp[0][*] = dp[*][0] = 0.

Transition:
- If s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1
                          (extend the matched char)
- Else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        (skip one char from either string)"

Algorithm:
1. dp = [[0] * (m+1) for _ in range(n+1)].
2. For i, j from 1: apply transition.
3. Return dp[n][m].

Edge Cases:
- Empty: 0.
- Equal strings: length.
- No common: 0.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| 2D DP    | O(n*m) | O(n*m) |
| 1D DP    | O(n*m) | O(m)   |
| Memo     | O(n*m) | O(n*m) |
+----------+--------+--------+

THE TRICK:
- If chars match: extend diagonal by 1.
- Else: take max of skipping i or skipping j.

ALTERNATE: 1D rolling array saves space. Track prev_diag.

RELATED:
- Edit Distance (LC 72) - 3-way transition.
- Longest Common Substring (LC 5-like) - reset on mismatch.
- LPS = LCS(s, reverse(s)).
- Distinct Subsequences (LC 115).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: 2D DP (BEST)", lcs_1),
        ("Way 2: 1D DP rolling", lcs_2),
        ("Way 3: Top-down memo", lcs_3),
        ("Way 4: Memo dict", lcs_4),
        ("Way 5: 2D DP verbose", lcs_5),
        ("Way 6: 1D DP swap", lcs_6),
        ("Way 7: Class OOP", lcs_7),
        ("Way 8: Closure memo", lcs_8),
        ("Way 9: Diagonal iter", lcs_9),
        ("Way 10: Reverse iter", lcs_10),
        ("Way 11: Same as 1", lcs_11),
        ("Way 12: Double buffer", lcs_12),
        ("Way 13: Explicit if", lcs_13),
        ("Way 14: Numpy", lcs_14),
        ("Way 15: Closure memo", lcs_15),
        ("Way 16: Refs DP", lcs_16),
        ("Way 17: Pure recursion", lcs_17),
        ("Way 18: Smaller outer", lcs_18),
        ("Way 19: 2D explicit", lcs_19),
        ("Way 20: Final cleanest", lcs_20),
    ]

    test_cases = [
        # (s1, s2, expected)
        ("abcde", "ace", 3),
        ("abc", "abc", 3),
        ("abc", "def", 0),
        ("", "abc", 0),
        ("abc", "", 0),
        ("bl", "yby", 1),
        ("ezupk", "ubmrapg", 2),
        ("aggtab", "gxtxayb", 4),
        ("aaaa", "aa", 2),
        ("abcba", "abcbcba", 5),
    ]

    print("=" * 70)
    print("LONGEST COMMON SUBSEQUENCE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-common-subsequence")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for s1, s2, expected in test_cases:
            try:
                result = func(s1, s2)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: s1={s1!r}, s2={s2!r}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: s1={s1!r}, s2={s2!r}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
