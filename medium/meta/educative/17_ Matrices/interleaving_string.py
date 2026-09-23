"""
Interleaving String
Medium | 30 min

Given strings s1, s2, s3, determine whether s3 can be formed by
interleaving s1 and s2. The interleaving preserves left-to-right order
within each string.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/interleaving-string

Examples:
    s1='aabcc', s2='dbbca', s3='aadbbcbcac' -> True
    s1='aabcc', s2='dbbca', s3='aadbbbaccc' -> False
    s1='', s2='', s3='' -> True
    s1='', s2='abc', s3='abc' -> True

Constraints:
- 0 <= s1.length, s2.length <= 100
- 0 <= s3.length <= 200
- lowercase letters

KEY INSIGHT:
2D DP. dp[i][j] = True if s3[0..i+j-1] is interleaving of
s1[0..i-1] and s2[0..j-1].
- Base: dp[0][0] = True; dp[i][0] = s1[0..i-1] == s3[0..i-1];
  dp[0][j] = s2[0..j-1] == s3[0..j-1].
- Transition:
  dp[i][j] = (dp[i-1][j] and s1[i-1] == s3[i+j-1])
          or (dp[i][j-1] and s2[j-1] == s3[i+j-1])

Final: dp[n][m].

Time: O(n*m). Space: O(n*m) or O(min(n,m)) rolling.
"""


# =============================================================================
# WAY 1: 2D DP (BEST - Memorize!)
# =============================================================================
def is_interleave_1(s1, s2, s3):
    """2D DP."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] and s1[i - 1] == s3[i - 1]
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            from_s1 = dp[i - 1][j] and s1[i - 1] == s3[i + j - 1]
            from_s2 = dp[i][j - 1] and s2[j - 1] == s3[i + j - 1]
            dp[i][j] = from_s1 or from_s2
    return dp[n][m]


# =============================================================================
# WAY 2: 1D DP rolling (space-optimized)
# =============================================================================
def is_interleave_2(s1, s2, s3):
    """1D DP rolling. Outer loop on s1, inner on s2."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    dp = [False] * (m + 1)
    dp[0] = True
    for j in range(1, m + 1):
        dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, n + 1):
        # Update dp[0] first (j=0 case)
        dp[0] = dp[0] and s1[i - 1] == s3[i - 1]
        for j in range(1, m + 1):
            from_s1 = dp[j] and s1[i - 1] == s3[i + j - 1]
            from_s2 = dp[j - 1] and s2[j - 1] == s3[i + j - 1]
            dp[j] = from_s1 or from_s2
    return dp[m]


# =============================================================================
# WAY 3: Top-down memo on (i, j)
# =============================================================================
def is_interleave_3(s1, s2, s3):
    """DFS + memo."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def dfs(i, j):
        if i == n and j == m:
            return True
        result = False
        if i < n and s1[i] == s3[i + j]:
            result = result or dfs(i + 1, j)
        if j < m and s2[j] == s3[i + j]:
            result = result or dfs(i, j + 1)
        return result

    return dfs(0, 0)


# =============================================================================
# WAY 4: BFS
# =============================================================================
def is_interleave_4(s1, s2, s3):
    """BFS on state space (i, j)."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    from collections import deque
    queue = deque([(0, 0)])
    visited = {(0, 0)}
    while queue:
        i, j = queue.popleft()
        if i == n and j == m:
            return True
        # Take from s1
        if i < n and s1[i] == s3[i + j] and (i + 1, j) not in visited:
            visited.add((i + 1, j))
            queue.append((i + 1, j))
        # Take from s2
        if j < m and s2[j] == s3[i + j] and (i, j + 1) not in visited:
            visited.add((i, j + 1))
            queue.append((i, j + 1))
    return False


# =============================================================================
# WAY 5: 2D DP with explicit base
# =============================================================================
def is_interleave_5(s1, s2, s3):
    """Same as Way 1 but verbose base."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                dp[i][j] = True
            elif i == 0:
                dp[i][j] = dp[i][j - 1] and s2[j - 1] == s3[j - 1]
            elif j == 0:
                dp[i][j] = dp[i - 1][j] and s1[i - 1] == s3[i - 1]
            else:
                a = dp[i - 1][j] and s1[i - 1] == s3[i + j - 1]
                b = dp[i][j - 1] and s2[j - 1] == s3[i + j - 1]
                dp[i][j] = a or b
    return dp[n][m]


# =============================================================================
# WAY 6: Pure recursion (no memo) - exponential
# =============================================================================
def is_interleave_6(s1, s2, s3):
    """Brute recursion, exponential."""

    def dfs(i, j):
        if i == len(s1) and j == len(s2):
            return True
        result = False
        if i < len(s1) and s1[i] == s3[i + j]:
            result = result or dfs(i + 1, j)
        if j < len(s2) and s2[j] == s3[i + j]:
            result = result or dfs(i, j + 1)
        return result

    return dfs(0, 0)


# =============================================================================
# WAY 7: Memo dict (3, j) with tuple keys
# =============================================================================
def is_interleave_7(s1, s2, s3):
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    memo = {}

    def dfs(i, j):
        if (i, j) in memo:
            return memo[(i, j)]
        if i == n and j == m:
            return True
        result = False
        if i < n and s1[i] == s3[i + j]:
            result = result or dfs(i + 1, j)
        if j < m and s2[j] == s3[i + j]:
            result = result or dfs(i, j + 1)
        memo[(i, j)] = result
        return result

    return dfs(0, 0)


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class InterleaveChecker:
    def __init__(self, s1, s2, s3):
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3

    def solve(self):
        return is_interleave_1(self.s1, self.s2, self.s3)


def is_interleave_8(s1, s2, s3):
    return InterleaveChecker(s1, s2, s3).solve()


# =============================================================================
# WAY 9: 2D DP with chars as list-comprehension
# =============================================================================
def is_interleave_9(s1, s2, s3):
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] and s1[i - 1] == s3[i - 1]
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, n + 1):
        dp_i = dp[i]
        dp_im1 = dp[i - 1]
        for j in range(1, m + 1):
            a = dp_im1[j] and s1[i - 1] == s3[i + j - 1]
            b = dp_i[j - 1] and s2[j - 1] == s3[i + j - 1]
            dp_i[j] = a or b
    return dp[n][m]


# =============================================================================
# WAY 10: Numpy DP
# =============================================================================
def is_interleave_10(s1, s2, s3):
    import numpy as np
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    dp = np.zeros((n + 1, m + 1), dtype=bool)
    dp[0, 0] = True
    for i in range(1, n + 1):
        dp[i, 0] = dp[i - 1, 0] and s1[i - 1] == s3[i - 1]
    for j in range(1, m + 1):
        dp[0, j] = dp[0, j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            a = dp[i - 1, j] and s1[i - 1] == s3[i + j - 1]
            b = dp[i, j - 1] and s2[j - 1] == s3[i + j - 1]
            dp[i, j] = a or b
    return bool(dp[n, m])


# =============================================================================
# WAY 11: 2D DP, swap s1 and s2 if s2 is longer
# =============================================================================
def is_interleave_11(s1, s2, s3):
    """1D DP, ensure s1 is shorter (so dp array is smaller)."""
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        dp[i] = dp[i - 1] and s1[i - 1] == s3[i - 1]
    for j in range(1, m + 1):
        dp[0] = dp[0] and s2[j - 1] == s3[j - 1]
        for i in range(1, n + 1):
            a = dp[i] and s2[j - 1] == s3[i + j - 1]
            b = dp[i - 1] and s1[i - 1] == s3[i + j - 1]
            dp[i] = a or b
    return dp[n]


# =============================================================================
# WAY 12: 2D DP built character by character
# =============================================================================
def is_interleave_12(s1, s2, s3):
    """2D DP. Build with simple if-else structure."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for i in range(n + 1):
        for j in range(m + 1):
            if i > 0 and s1[i - 1] == s3[i + j - 1]:
                dp[i][j] = dp[i][j] or dp[i - 1][j]
            if j > 0 and s2[j - 1] == s3[i + j - 1]:
                dp[i][j] = dp[i][j] or dp[i][j - 1]
    return dp[n][m]


# =============================================================================
# WAY 13: Bottom-up with closure-based memo
# =============================================================================
def is_interleave_13(s1, s2, s3):
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    cache = [[False] * (m + 1) for _ in range(n + 1)]
    cache[0][0] = True
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            ok = False
            if i > 0 and s1[i - 1] == s3[i + j - 1]:
                ok = ok or cache[i - 1][j]
            if j > 0 and s2[j - 1] == s3[i + j - 1]:
                ok = ok or cache[i][j - 1]
            cache[i][j] = ok
    return cache[n][m]


# =============================================================================
# WAY 14: DFS with manual stack (no recursion)
# =============================================================================
def is_interleave_14(s1, s2, s3):
    """Iterative DFS with stack."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    if n == 0 and m == 0:
        return True
    stack = [(0, 0)]
    visited = {(0, 0)}
    while stack:
        i, j = stack.pop()
        if i == n and j == m:
            return True
        # Try s1
        if i < n and s1[i] == s3[i + j] and (i + 1, j) not in visited:
            visited.add((i + 1, j))
            stack.append((i + 1, j))
        # Try s2
        if j < m and s2[j] == s3[i + j] and (i, j + 1) not in visited:
            visited.add((i, j + 1))
            stack.append((i, j + 1))
    return False


# =============================================================================
# WAY 15: 2D DP with bitmask
# =============================================================================
def is_interleave_15(s1, s2, s3):
    """Bitmask DP. Track which chars matched."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    # State as (i, j) bitmask: which previous states are reachable.
    # For each (i, j), check both transitions.
    reach = [[False] * (m + 1) for _ in range(n + 1)]
    reach[0][0] = True
    for i in range(n + 1):
        for j in range(m + 1):
            if not reach[i][j]:
                continue
            if i < n and s1[i] == s3[i + j]:
                reach[i + 1][j] = True
            if j < m and s2[j] == s3[i + j]:
                reach[i][j + 1] = True
    return reach[n][m]


# =============================================================================
# WAY 16: Reverse perspective
# =============================================================================
def is_interleave_16(s1, s2, s3):
    """Same as Way 1."""
    return is_interleave_1(s1, s2, s3)


# =============================================================================
# WAY 17: Iterative state DP with merge
# =============================================================================
def is_interleave_17(s1, s2, s3):
    """Iterative — same as Way 2, but with verbose variable names."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    if n == 0 and m == 0:
        return len(s3) == 0
    dp = [False] * (m + 1)
    dp[0] = True
    for j in range(1, m + 1):
        dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, n + 1):
        # j=0 base
        dp[0] = dp[0] and s1[i - 1] == s3[i - 1]
        for j in range(1, m + 1):
            take_s1 = dp[j] and s1[i - 1] == s3[i + j - 1]
            take_s2 = dp[j - 1] and s2[j - 1] == s3[i + j - 1]
            dp[j] = take_s1 or take_s2
    return dp[m]


# =============================================================================
# WAY 18: Memo with @lru_cache and explicit state
# =============================================================================
def is_interleave_18(s1, s2, s3):
    from functools import lru_cache
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False

    @lru_cache(maxsize=None)
    def check(i, j):
        if i == n and j == m:
            return i + j == len(s3)
        if i + j >= len(s3):
            return False
        ok = False
        if i < n and s1[i] == s3[i + j]:
            ok = ok or check(i + 1, j)
        if j < m and s2[j] == s3[i + j]:
            ok = ok or check(i, j + 1)
        return ok

    return check(0, 0)


# =============================================================================
# WAY 19: 2D DP but built as list of lists
# =============================================================================
def is_interleave_19(s1, s2, s3):
    """2D DP with separate base initialization."""
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    # Fill first row
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] and (s2[j - 1] == s3[j - 1])
    # Fill first column
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] and (s1[i - 1] == s3[i - 1])
    # Fill rest
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            a = dp[i - 1][j] and (s1[i - 1] == s3[i + j - 1])
            b = dp[i][j - 1] and (s2[j - 1] == s3[i + j - 1])
            dp[i][j] = a or b
    return dp[n][m]


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def is_interleave_20(s1, s2, s3):
    """
    THE ONE TO MEMORIZE.

    dp[i][j] = True iff s3[0..i+j-1] is interleaving of s1[0..i-1] and s2[0..j-1].

    Base:
      dp[0][0] = True.
      dp[i][0] = dp[i-1][0] AND s1[i-1] == s3[i-1].
      dp[0][j] = dp[0][j-1] AND s2[j-1] == s3[j-1].

    Transition:
      dp[i][j] = (dp[i-1][j] AND s1[i-1] == s3[i+j-1])
              OR (dp[i][j-1] AND s2[j-1] == s3[i+j-1])

    Quick check: |s1| + |s2| must equal |s3|.

    Time:  O(n*m)
    Space: O(min(n,m)) with rolling array.
    """
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    # 1D rolling array
    dp = [False] * (m + 1)
    dp[0] = True
    for j in range(1, m + 1):
        dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, n + 1):
        dp[0] = dp[0] and s1[i - 1] == s3[i - 1]
        for j in range(1, m + 1):
            f1 = dp[j] and s1[i - 1] == s3[i + j - 1]
            f2 = dp[j - 1] and s2[j - 1] == s3[i + j - 1]
            dp[j] = f1 or f2
    return dp[m]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to check if s3 is formed by interleaving s1 and s2."

Key Insight:
"2D DP. State: (i, j) = how many chars of s1 and s2 used so far.
dp[i][j] = True iff s3[0..i+j-1] is a valid interleaving of s1[0..i-1]
                                     and s2[0..j-1].

Quick check: |s1| + |s2| must equal |s3|. Otherwise return False.

Base cases:
- dp[0][0] = True.
- dp[i][0] = dp[i-1][0] AND s1[i-1] == s3[i-1] (only s1 used).
- dp[0][j] = dp[0][j-1] AND s2[j-1] == s3[j-1] (only s2 used).

Transition:
dp[i][j] = (dp[i-1][j] AND s1[i-1] == s3[i+j-1])  -- take from s1
        OR (dp[i][j-1] AND s2[j-1] == s3[i+j-1])  -- take from s2

Last char of s3 (position i+j-1) must come from s1[i-1] or s2[j-1]."

Algorithm:
1. If len(s1)+len(s2) != len(s3): return False.
2. dp[0][0] = True. Initialize first row/col.
3. Iterate i, j. Update dp.
4. Return dp[n][m].

Space optimization: 1D rolling array.

Edge Cases:
- Empty s1 or s2: s3 must equal the other.
- Both empty: s3 must be empty.
- Single chars: trivial.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| 2D DP    | O(n*m) | O(n*m) |
| 1D DP    | O(n*m) | O(m)   |
| DFS+memo | O(n*m) | O(n*m) |
| BFS      | O(n*m) | O(n*m) |
| Brute    | O(2^n+m)| O(n+m)|
+----------+--------+--------+

THE TRICK:
dp[i+j-1] is the last matched char in s3. Check both transitions.

RELATED:
- Edit Distance (LC 72) — similar 2D structure.
- Distinct Subsequences (LC 115).
- Word Break (LC 139).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: 2D DP (BEST)", is_interleave_1),
        ("Way 2: 1D DP rolling", is_interleave_2),
        ("Way 3: Top-down memo", is_interleave_3),
        ("Way 4: BFS", is_interleave_4),
        ("Way 5: 2D DP verbose", is_interleave_5),
        ("Way 6: Pure recursion", is_interleave_6),
        ("Way 7: Memo dict", is_interleave_7),
        ("Way 8: Class OOP", is_interleave_8),
        ("Way 9: 2D DP refs", is_interleave_9),
        ("Way 10: Numpy", is_interleave_10),
        ("Way 11: 1D DP swap", is_interleave_11),
        ("Way 12: 2D char-by-char", is_interleave_12),
        ("Way 13: Closure memo", is_interleave_13),
        ("Way 14: Iter DFS", is_interleave_14),
        ("Way 15: Bitmask reach", is_interleave_15),
        ("Way 16: Reverse perspective", is_interleave_16),
        ("Way 17: Iterative merge", is_interleave_17),
        ("Way 18: lru_cache", is_interleave_18),
        ("Way 19: 2D list of lists", is_interleave_19),
        ("Way 20: Final cleanest", is_interleave_20),
    ]

    test_cases = [
        # (s1, s2, s3, expected)
        ("aabcc", "dbbca", "aadbbcbcac", True),
        ("aabcc", "dbbca", "aadbbbaccc", False),
        ("", "", "", True),
        ("", "abc", "abc", True),
        ("abc", "", "abc", True),
        ("a", "b", "ab", True),
        ("a", "b", "ba", True),  # s2[0]='b'=s3[0], s1[0]='a'=s3[1]
        ("aa", "ab", "aaba", True),
        ("aa", "ab", "abaa", True),  # s1,s2,s2,s1 = a,a,b,a
        ("aabc", "abcd", "aabcabcd", True),
        ("aabc", "abcd", "aabcbcd", False),
        ("aaaa", "aaaa", "aaaaaaaa", True),
        ("abc", "def", "abcdef", True),
        ("abc", "def", "abdcfe", False),
    ]

    print("=" * 70)
    print("INTERLEAVING STRING - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/interleaving-string")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for s1, s2, s3, expected in test_cases:
            try:
                result = func(s1, s2, s3)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: s1={s1!r}, s2={s2!r}, s3={s3!r}, expected={expected}, got={result}")
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
