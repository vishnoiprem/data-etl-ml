"""
Is Subsequence
Easy | 15 min

Given two strings s and t, return True if s is a subsequence of t.

A subsequence is formed by deleting zero or more characters from the
original string without changing relative order.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/is-subsequence

Examples:
    s="abc", t="ahbgdc" -> True  (a, b, c all in order)
    s="axc", t="ahbgdc" -> False (b is between, no c after)
    s="ace", t="abcde"  -> True
    s="", t="anything"  -> True  (empty is subsequence of anything)
    s="abc", t=""       -> False

Constraints:
- 0 <= s.length <= 100
- 0 <= t.length <= 10^4
- s and t consist of lowercase English letters.

KEY INSIGHT:
Two-pointer technique.
- i walks through s.
- j walks through t.
- When s[i] == t[j]: advance both.
- Else: advance j only.
- At end, s is subsequence iff i == len(s).

Time:  O(|t|) — single pass through t.
Space: O(1).
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT IS SUBSEQUENCE:

1. UNDERSTAND THE PROBLEM:
   "Determine if s can be obtained from t by deleting zero or more chars."

2. KEY OBSERVATION:
   "Walk through t. Look for chars of s IN ORDER.
   If we find all chars of s in this order, s is subsequence."

3. TWO-POINTER GREEDY:
   - i = 0 (pointer in s).
   - j = 0 (pointer in t).
   - While i < len(s) and j < len(t):
     - If s[i] == t[j]: i++, j++.
     - Else: j++.
   - s is subsequence iff i == len(s).

4. WHY THIS WORKS:
   - Greedy: match each s[i] to its first occurrence in t (from j onwards).
   - If we can match all of s, order is preserved.

5. EDGE CASES:
   - s empty: True (trivial subsequence).
   - t empty: True iff s empty.
   - s longer than t: False.

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Two ptr  | O(n)   | O(1)   |
   | In op    | O(n)   | O(n)   |
   +----------+--------+--------+

7. WHY TWO POINTERS:
   - Single pass through t.
   - O(1) extra space.
"""


# =============================================================================
# WAY 1: Two-pointer (BEST - Memorize!)
# =============================================================================
def is_subsequence_1(s, t):
    """Two-pointer. Walk t, match chars of s in order."""
    i = 0
    for c in t:
        if i < len(s) and s[i] == c:
            i += 1
    return i == len(s)


# =============================================================================
# WAY 2: Iterative with explicit while loop
# =============================================================================
def is_subsequence_2(s, t):
    """Same as Way 1 with explicit while."""
    i, j = 0, 0
    while i < len(s) and j < len(t):
        if s[i] == t[j]:
            i += 1
        j += 1
    return i == len(s)


# =============================================================================
# WAY 3: Recursive two-pointer
# =============================================================================
def is_subsequence_3(s, t):
    """Recursive helper."""

    def helper(i, j):
        if i == len(s):
            return True
        if j == len(t):
            return False
        if s[i] == t[j]:
            return helper(i + 1, j + 1)
        return helper(i, j + 1)

    return helper(0, 0)


# =============================================================================
# WAY 4: Pythonic with iter(t)
# =============================================================================
def is_subsequence_4(s, t):
    """Use Python's all() and iter()."""
    it = iter(t)
    return all(c in it for c in s)


# =============================================================================
# WAY 5: Use zip_longest
# =============================================================================
def is_subsequence_5(s, t):
    """zip_longest trick: char by char, pad with None."""
    from itertools import zip_longest
    # Remove chars from t as we match.
    remaining = t
    for c in s:
        if c not in remaining:
            return False
        remaining = remaining[remaining.index(c) + 1 :]
    return True


# =============================================================================
# WAY 6: Brute - check every index in t
# =============================================================================
def is_subsequence_6(s, t):
    """Brute: for each char in s, find in t after current position."""
    pos = -1
    for c in s:
        for j in range(pos + 1, len(t)):
            if t[j] == c:
                pos = j
                break
        else:
            return False
    return True


# =============================================================================
# WAY 7: Use Counter + dictionary of positions
# =============================================================================
def is_subsequence_7(s, t):
    """
    Build index dict for t. For each char in s, find next available index
    after the current position. O(n + m) with preprocessing.
    """
    from collections import defaultdict

    if not s:
        return True
    # Map char to sorted positions.
    char_positions = defaultdict(list)
    for i, c in enumerate(t):
        char_positions[c].append(i)
    # For each char in s, find first position > prev.
    prev_pos = -1
    for c in s:
        if c not in char_positions:
            return False
        # Find smallest position > prev_pos.
        positions = char_positions[c]
        # Binary search.
        lo, hi = 0, len(positions)
        while lo < hi:
            mid = (lo + hi) // 2
            if positions[mid] > prev_pos:
                hi = mid
            else:
                lo = mid + 1
        if lo == len(positions):
            return False
        prev_pos = positions[lo]
    return True


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class SubsequenceChecker:
    def __init__(self, s, t):
        self.s = s
        self.t = t

    def check(self):
        i, j = 0, 0
        while i < len(self.s) and j < len(self.t):
            if self.s[i] == self.t[j]:
                i += 1
            j += 1
        return i == len(self.s)


def is_subsequence_8(s, t):
    return SubsequenceChecker(s, t).check()


# =============================================================================
# WAY 9: Generator-based
# =============================================================================
def is_subsequence_9(s, t):
    """Use generator - match each char in s with next in t."""
    g = iter(t)
    for c in s:
        # Find c in remaining t.
        matched = False
        for x in g:
            if x == c:
                matched = True
                break
        if not matched:
            return False
    return True


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def is_subsequence_10(s, t):
    """
    THE ONE TO MEMORIZE.

    Two-pointer. Walk t, match chars of s in order.
    Greedy: match each s[i] to its first occurrence in t from current j.

    Time:  O(|t|).
    Space: O(1).
    """
    i = 0
    for c in t:
        if i < len(s) and s[i] == c:
            i += 1
    return i == len(s)


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two-pointer (BEST)", is_subsequence_1),
        ("Way 2: While loop explicit", is_subsequence_2),
        ("Way 3: Recursive", is_subsequence_3),
        ("Way 4: iter() + all()", is_subsequence_4),
        ("Way 5: Slice rfind", is_subsequence_5),
        ("Way 6: Brute index search", is_subsequence_6),
        ("Way 7: Dict + binary search", is_subsequence_7),
        ("Way 8: Class OOP", is_subsequence_8),
        ("Way 9: Generator", is_subsequence_9),
        ("Way 10: Final cleanest", is_subsequence_10),
    ]

    test_cases = [
        # (s, t, expected)
        ("abc", "ahbgdc", True),
        ("axc", "ahbgdc", False),
        ("ace", "abcde", True),
        ("", "abc", True),
        ("abc", "", False),
        ("", "", True),
        ("aaaaa", "aaaaaaaaaa", True),
        ("abc", "abc", True),
        ("ab", "ba", False),
        ("aec", "abcde", False),
    ]

    print("=" * 70)
    print("IS SUBSEQUENCE - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/is-subsequence")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for s, t, expected in test_cases:
            try:
                result = func(s, t)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: s={s!r}, t={t!r}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: s={s!r}, t={t!r}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)