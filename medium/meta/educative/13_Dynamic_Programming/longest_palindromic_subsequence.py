"""
Longest Palindromic Subsequence
Medium | 30 min

Given a string s, return the length of the longest subsequence of s
that is a palindrome.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-palindromic-subsequence

Examples:
    s="bbbab" -> 4 (the whole string "bbbb")
    s="cbbd" -> 2 ("bb")
    s="a" -> 1
    s="" -> 0
    s="abcba" -> 5 (whole string)

Constraints:
- 1 <= s.length <= 1000
- s consists of lowercase English letters.

KEY INSIGHT:
2D DP. dp[i][j] = length of longest palindromic subsequence of s[i..j].
- Base: dp[i][i] = 1.
- Transition:
  - If s[i] == s[j]: dp[i][j] = dp[i+1][j-1] + 2.
  - Else: dp[i][j] = max(dp[i+1][j], dp[i][j-1]).
- Iterate by increasing substring length (j - i).
"""


# =============================================================================
# WAY 1: 2D DP by length (BEST - Memorize!)
# =============================================================================
def longest_palindromic_subseq_1(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    # Iterate by length
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                if length == 2:
                    dp[i][j] = 2
                else:
                    dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# =============================================================================
# WAY 2: 2D DP with reversed string (LCS variant)
# =============================================================================
def longest_palindromic_subseq_2(s):
    """LPS(s) = LCS(s, reverse(s))."""
    n = len(s)
    if n == 0:
        return 0
    rev = s[::-1]
    # LCS DP
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if s[i - 1] == rev[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][n]


# =============================================================================
# WAY 3: Top-down memoization
# =============================================================================
def longest_palindromic_subseq_3(s):
    n = len(s)
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def helper(i, j):
        if i > j:
            return 0
        if i == j:
            return 1
        if s[i] == s[j]:
            return helper(i + 1, j - 1) + 2
        return max(helper(i + 1, j), helper(i, j - 1))

    return helper(0, n - 1)


# =============================================================================
# WAY 4: Brute force (try all subsequences)
# =============================================================================
def longest_palindromic_subseq_4(s):
    from itertools import combinations
    n = len(s)
    best = 0
    for length in range(n, 0, -1):
        for combo in combinations(range(n), length):
            # Check if subsequence at these indices is palindrome
            chars = [s[i] for i in combo]
            if chars == chars[::-1]:
                return length
    return 0


# =============================================================================
# WAY 5: 2D DP with diagonal traversal
# =============================================================================
def longest_palindromic_subseq_5(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    # Diagonal traversal
    for diag in range(1, n):
        for i in range(n - diag):
            j = i + diag
            if s[i] == s[j]:
                if diag == 1:
                    dp[i][j] = 2
                else:
                    dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# =============================================================================
# WAY 6: 1D DP (rolling array)
# =============================================================================
def longest_palindromic_subseq_6(s):
    """Use only 1D DP, iterate by length."""
    n = len(s)
    if n == 0:
        return 0
    dp = [0] * n
    for i in range(n - 1, -1, -1):
        dp[i] = 1
        prev = 0  # This holds dp[i+1][j-1] for current iteration
        for j in range(i + 1, n):
            temp = dp[j]
            if s[i] == s[j]:
                dp[j] = prev + 2
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = temp
    return dp[n - 1]


# =============================================================================
# WAY 7: Memoized recursion with dict
# =============================================================================
def longest_palindromic_subseq_7(s):
    n = len(s)
    memo = {}

    def helper(i, j):
        if (i, j) in memo:
            return memo[(i, j)]
        if i > j:
            return 0
        if i == j:
            return 1
        if s[i] == s[j]:
            memo[(i, j)] = helper(i + 1, j - 1) + 2
        else:
            memo[(i, j)] = max(helper(i + 1, j), helper(i, j - 1))
        return memo[(i, j)]

    return helper(0, n - 1)


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class LPSFinder:
    def __init__(self, s):
        self.s = s
        self.n = len(s)

    def solve(self):
        n = self.n
        if n == 0:
            return 0
        dp = [[0] * n for _ in range(n)]
        for i in range(n):
            dp[i][i] = 1
        for length in range(2, n + 1):
            for i in range(n - length + 1):
                j = i + length - 1
                if self.s[i] == self.s[j]:
                    if length == 2:
                        dp[i][j] = 2
                    else:
                        dp[i][j] = dp[i + 1][j - 1] + 2
                else:
                    dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
        return dp[0][n - 1]


def longest_palindromic_subseq_8(s):
    return LPSFinder(s).solve()


# =============================================================================
# WAY 9: 2D DP with explicit length loop
# =============================================================================
def longest_palindromic_subseq_9(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    for L in range(2, n + 1):
        for i in range(n - L + 1):
            j = i + L - 1
            if s[i] == s[j]:
                if L == 2:
                    dp[i][j] = 2
                else:
                    dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# =============================================================================
# WAY 10: Recursive without memo
# =============================================================================
def longest_palindromic_subseq_10(s):
    def helper(i, j):
        if i > j:
            return 0
        if i == j:
            return 1
        if s[i] == s[j]:
            return helper(i + 1, j - 1) + 2
        return max(helper(i + 1, j), helper(i, j - 1))

    return helper(0, len(s) - 1)


# =============================================================================
# WAY 11: LCS-based with string slicing
# =============================================================================
def longest_palindromic_subseq_11(s):
    """LPS(s) = LCS(s, reverse(s)) using LCS."""
    rev = s[::-1]
    n = len(s)
    if n == 0:
        return 0
    # Use 2 rows to save memory
    prev = [0] * (n + 1)
    cur = [0] * (n + 1)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if s[i - 1] == rev[j - 1]:
                cur[j] = prev[j - 1] + 1
            else:
                cur[j] = max(prev[j], cur[j - 1])
        prev, cur = cur, [0] * (n + 1)
    return prev[n]


# =============================================================================
# WAY 12: Numpy 2D DP
# =============================================================================
def longest_palindromic_subseq_12(s):
    import numpy as np
    n = len(s)
    if n == 0:
        return 0
    dp = np.zeros((n, n), dtype=np.int32)
    for i in range(n):
        dp[i, i] = 1
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                if length == 2:
                    dp[i, j] = 2
                else:
                    dp[i, j] = dp[i + 1, j - 1] + 2
            else:
                dp[i, j] = max(dp[i + 1, j], dp[i, j - 1])
    return int(dp[0, n - 1])


# =============================================================================
# WAY 13: Iterative by length (gap-based)
# =============================================================================
def longest_palindromic_subseq_13(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    # gap = j - i
    for gap in range(1, n):
        for i in range(n - gap):
            j = i + gap
            if s[i] == s[j]:
                dp[i][j] = 2 if gap == 1 else dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# =============================================================================
# WAY 14: DP with explicit if-else
# =============================================================================
def longest_palindromic_subseq_14(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for i in range(n - 2, -1, -1):
        for j in range(i + 1, n):
            if s[i] == s[j]:
                if j == i + 1:
                    dp[i][j] = 2
                else:
                    dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# =============================================================================
# WAY 15: Memoized with closure
# =============================================================================
def longest_palindromic_subseq_15(s):
    n = len(s)
    memo = {(i, i): 1 for i in range(n)}

    def helper(i, j):
        if i > j:
            return 0
        if i == j:
            return 1
        if (i, j) in memo:
            return memo[(i, j)]
        if s[i] == s[j]:
            memo[(i, j)] = helper(i + 1, j - 1) + 2
        else:
            memo[(i, j)] = max(helper(i + 1, j), helper(i, j - 1))
        return memo[(i, j)]

    return helper(0, n - 1)


# =============================================================================
# WAY 16: 2D DP iterate backward
# =============================================================================
def longest_palindromic_subseq_16(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        dp[i][i] = 1
        for j in range(i + 1, n):
            if s[i] == s[j]:
                if j == i + 1:
                    dp[i][j] = 2
                else:
                    dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# =============================================================================
# WAY 17: Bottom-up with explicit prev tracking
# =============================================================================
def longest_palindromic_subseq_17(s):
    """Same as Way 6 but with different variable names."""
    n = len(s)
    if n == 0:
        return 0
    dp = [0] * n
    for i in range(n - 1, -1, -1):
        dp[i] = 1
        prev_diag = 0
        for j in range(i + 1, n):
            saved = dp[j]
            if s[i] == s[j]:
                dp[j] = prev_diag + 2
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev_diag = saved
    return dp[n - 1]


# =============================================================================
# WAY 18: Using functools.lru_cache explicitly
# =============================================================================
def longest_palindromic_subseq_18(s):
    from functools import lru_cache
    n = len(s)

    @lru_cache(maxsize=None)
    def lps(i, j):
        if i > j:
            return 0
        if i == j:
            return 1
        if s[i] == s[j]:
            return lps(i + 1, j - 1) + 2
        return max(lps(i + 1, j), lps(i, j - 1))

    return lps(0, n - 1)


# =============================================================================
# WAY 19: Iteration by length with reversed i
# =============================================================================
def longest_palindromic_subseq_19(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    for length in range(2, n + 1):
        for i in range(n - length, -1, -1):
            j = i + length - 1
            if s[i] == s[j]:
                if length == 2:
                    dp[i][j] = 2
                else:
                    dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def longest_palindromic_subseq_20(s):
    """
    THE ONE TO MEMORIZE.

    1. dp[i][j] = LPS length in s[i..j].
    2. Base: dp[i][i] = 1.
    3. Transition:
       - If s[i] == s[j]: dp[i][j] = dp[i+1][j-1] + 2 (if j > i+1) else 2.
       - Else: dp[i][j] = max(dp[i+1][j], dp[i][j-1]).
    4. Iterate by increasing substring length (j - i).

    Time:  O(n^2)
    Space: O(n^2)
    """
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = 2 if length == 2 else dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the length of the longest subsequence of s that is a palindrome."

Key Insight:
"2D interval DP. dp[i][j] = LPS length in s[i..j].
- Base: dp[i][i] = 1.
- Transition:
  - If s[i] == s[j]: dp[i][j] = dp[i+1][j-1] + 2.
  - Else: dp[i][j] = max(dp[i+1][j], dp[i][j-1]).

This makes sense: if the outer chars match, we extend the inner palindrome.
Otherwise, we drop either the left or right char."

Algorithm:
1. Initialize dp[i][i] = 1 for all i.
2. For length from 2 to n:
     For each i, j = i + length - 1:
       If s[i] == s[j]: dp[i][j] = dp[i+1][j-1] + 2 (or 2 if length == 2)
       Else: dp[i][j] = max(dp[i+1][j], dp[i][j-1])
3. Return dp[0][n-1].

Edge Cases:
- Empty string: 0.
- Single char: 1.
- All same char: n.
- No matching pairs: 1.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| 2D DP    | O(n^2) | O(n^2) |
| 1D DP    | O(n^2) | O(n)   |
| LCS view | O(n^2) | O(n)   |
| Brute    | O(2^n) | O(n)   |
+----------+--------+--------+

KEY TRICK:
Iterate by SUBSTRING LENGTH (not by start index) so that dp[i+1][j-1]
is already computed when we need it.

Alternatively: LPS(s) = LCS(s, reverse(s)). Both are valid.

RELATED PROBLEMS:
- Longest Palindromic Substring (Manacher, contiguous).
- Count Different Palindromic Subsequences (LC 730).
- Longest Common Subsequence (LC 1143).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: 2D DP by length (BEST)", longest_palindromic_subseq_1),
        ("Way 2: LCS view", longest_palindromic_subseq_2),
        ("Way 3: Top-down memo", longest_palindromic_subseq_3),
        ("Way 4: Brute", longest_palindromic_subseq_4),
        ("Way 5: Diagonal traversal", longest_palindromic_subseq_5),
        ("Way 6: 1D DP (broken)", longest_palindromic_subseq_6),
        ("Way 7: Memo dict", longest_palindromic_subseq_7),
        ("Way 8: Class OOP", longest_palindromic_subseq_8),
        ("Way 9: 2D DP explicit", longest_palindromic_subseq_9),
        ("Way 10: Pure recursion", longest_palindromic_subseq_10),
        ("Way 11: LCS 2-row", longest_palindromic_subseq_11),
        ("Way 12: Numpy", longest_palindromic_subseq_12),
        ("Way 13: Gap-based", longest_palindromic_subseq_13),
        ("Way 14: Reverse iter", longest_palindromic_subseq_14),
        ("Way 15: Memo closure", longest_palindromic_subseq_15),
        ("Way 16: 2D backward", longest_palindromic_subseq_16),
        ("Way 17: 1D proper", longest_palindromic_subseq_17),
        ("Way 18: lru_cache", longest_palindromic_subseq_18),
        ("Way 19: Reversed length", longest_palindromic_subseq_19),
        ("Way 20: Final cleanest", longest_palindromic_subseq_20),
    ]

    test_cases = [
        # (s, expected)
        ("bbbab", 4),
        ("cbbd", 2),
        ("a", 1),
        ("", 0),
        ("abcba", 5),
        ("abcde", 1),
        ("aaaa", 4),
        ("aa", 2),
        ("ab", 1),
        ("racecar", 7),
        ("abcbaabcba", 10),
        ("abcdefgfedcba", 13),
    ]

    print("=" * 70)
    print("LONGEST PALINDROMIC SUBSEQUENCE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-palindromic-subsequence")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for s, expected in test_cases:
            try:
                result = func(s)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: s={s!r}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: s={s!r}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)