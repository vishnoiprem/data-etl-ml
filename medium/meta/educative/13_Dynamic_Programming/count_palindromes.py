"""
Count Palindromic Subsequences (length 5)
Medium | 30 min

Given a string s of digits, count the number of 5-element subsequences
that form a palindrome.

A 5-character palindrome has the form: a b c b a
So we need tuples (i < j < k < l < m) such that:
  s[i] == s[m] (call this 'a')
  s[j] == s[l] (call this 'b')
  s[k]        (call this 'c', no constraint)

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-palindromic-subsequences

Constraints:
- 1 <= s.length <= 10^4
- s consists of digits (0-9)

Examples:
  s = "10301" -> 1 (the whole string)
  s = "11111" -> 1
  s = "111111" -> 6 (any 5 indices)

KEY INSIGHT:
For each INNER pair (j, l) with j<l and s[j]==s[l]:
- middle_count = l - j - 1 (choices for k).
- outer_count = sum over 'a' of (# of a in s[0..j-1]) * (# of a in s[l+1..n-1])
- contribution = middle_count * outer_count
Total = sum of contributions.
"""

import sys


# =============================================================================
# WAY 1: For each (j,l) inner pair, count middle k * outer (i,m) (BEST)
# =============================================================================
def count_palindromes_1(s):
    """For each pair (j, l) with s[j]==s[l], compute middle * outer count."""
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    # prefix[d][i] = # of digit d in s[0..i-1]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for dig in range(10):
            prefix[dig][i + 1] = prefix[dig][i]
        prefix[d][i + 1] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):  # l-j >= 2 so middle has at least 1 choice
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = 0
            for a in range(10):
                outer += prefix[a][j] * (prefix[a][n] - prefix[a][l + 1])
            total += middle * outer
    return total


# =============================================================================
# WAY 2: Build position lists per digit, iterate pairs
# =============================================================================
def count_palindromes_2(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    positions = [[] for _ in range(10)]
    for i, d in enumerate(digits):
        positions[d].append(i)
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for dig in range(10):
            prefix[dig][i + 1] = prefix[dig][i]
        prefix[d][i + 1] += 1
    total = 0
    for d in range(10):
        pos = positions[d]
        for idx_j in range(len(pos)):
            j = pos[idx_j]
            for idx_l in range(idx_j + 1, len(pos)):
                l = pos[idx_l]
                if l - j < 2:
                    continue
                middle = l - j - 1
                outer = 0
                for a in range(10):
                    outer += prefix[a][j] * (prefix[a][n] - prefix[a][l + 1])
                total += middle * outer
    return total


# =============================================================================
# WAY 3: Fix middle k, iterate inner pair (j,l) with j<k<l
# =============================================================================
def count_palindromes_3(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for dig in range(10):
            prefix[dig][i + 1] = prefix[dig][i]
        prefix[d][i + 1] += 1
    total = 0
    for k in range(1, n - 1):
        # For each inner pair (j, l) with j < k < l and s[j] == s[l]
        # contribution: outer count (sum over a of count_a(j) * count_a(l+1, n))
        # Sum over j < k: count_left[j] = (# of digit s[j] in s[j+1..k-1]) etc.
        # Iterate j < k, for each, iterate l > k.
        for j in range(k):
            dj = digits[j]
            for l in range(k + 1, n):
                if digits[l] != dj:
                    continue
                outer = 0
                for a in range(10):
                    outer += prefix[a][j] * (prefix[a][n] - prefix[a][l + 1])
                total += outer
    return total


# =============================================================================
# WAY 4: Brute force O(n^5)
# =============================================================================
def count_palindromes_4(s):
    n = len(s)
    if n < 5:
        return 0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                for l in range(k + 1, n):
                    for m in range(l + 1, n):
                        if s[i] == s[m] and s[j] == s[l]:
                            count += 1
    return count


# =============================================================================
# WAY 5: For each (j, l) inner pair, iterate (i, m)
# =============================================================================
def count_palindromes_5(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            # Count (i, m) with i < j, m > l, s[i] == s[m]
            outer = 0
            for a in range(10):
                left_count = sum(1 for i in range(j) if digits[i] == a)
                right_count = sum(1 for i in range(l + 1, n) if digits[i] == a)
                outer += left_count * right_count
            total += middle * outer
    return total


# =============================================================================
# WAY 6: For each (j, l) with s[j]==s[l], use prefix sums
# =============================================================================
def count_palindromes_6(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for dig in range(10):
            prefix[dig][i + 1] = prefix[dig][i]
        prefix[d][i + 1] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = sum(prefix[a][j] * (prefix[a][n] - prefix[a][l + 1]) for a in range(10))
            total += middle * outer
    return total


# =============================================================================
# WAY 7: With itertools.product for the outer loop
# =============================================================================
def count_palindromes_7(s):
    import itertools
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for dig in range(10):
            prefix[dig][i + 1] = prefix[dig][i]
        prefix[d][i + 1] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = sum(prefix[a][j] * (prefix[a][n] - prefix[a][l + 1]) for a in range(10))
            total += middle * outer
    return total


# =============================================================================
# WAY 8: For each (j, l), precompute outer via running count
# =============================================================================
def count_palindromes_8(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    total = 0
    # Precompute count_left[j] = (# of each digit in s[0..j-1])
    # and count_right[l] = (# of each digit in s[l+1..n-1])
    left = [[0] * 10 for _ in range(n + 1)]
    right = [[0] * 10 for _ in range(n + 1)]
    for i in range(n):
        for a in range(10):
            left[i + 1][a] = left[i][a]
        left[i + 1][digits[i]] += 1
    for i in range(n - 1, -1, -1):
        for a in range(10):
            right[i][a] = right[i + 1][a]
        right[i][digits[i]] += 1
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = sum(left[j][a] * right[l + 1][a] for a in range(10))
            total += middle * outer
    return total


# =============================================================================
# WAY 9: For each (j, l), compute outer on-the-fly
# =============================================================================
def count_palindromes_9(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    total = 0
    for j in range(n):
        left = [0] * 10
        for i in range(j):
            left[digits[i]] += 1
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = 0
            for a in range(10):
                right_count = sum(1 for i in range(l + 1, n) if digits[i] == a)
                outer += left[a] * right_count
            total += middle * outer
    return total


# =============================================================================
# WAY 10: Numpy vectorized
# =============================================================================
def count_palindromes_10(s):
    import numpy as np
    n = len(s)
    if n < 5:
        return 0
    arr = np.array([ord(c) - 48 for c in s], dtype=np.int64)
    prefix = np.zeros((10, n + 1), dtype=np.int64)
    for d in range(10):
        prefix[d, 1:] = np.cumsum(arr == d)
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if arr[j] != arr[l]:
                continue
            middle = l - j - 1
            outer = int(np.sum(prefix[:, j] * (prefix[:, n] - prefix[:, l + 1])))
            total += middle * outer
    return total


# =============================================================================
# WAY 11: Class OOP
# =============================================================================
class PalindromeCounter:
    def __init__(self, s):
        self.s = s
        self.n = len(s)
        self.digits = [ord(c) - 48 for c in s]
        self.prefix = [[0] * (self.n + 1) for _ in range(10)]
        for i in range(self.n):
            d = self.digits[i]
            for dig in range(10):
                self.prefix[dig][i + 1] = self.prefix[dig][i]
            self.prefix[d][i + 1] += 1

    def count(self):
        total = 0
        for j in range(self.n):
            for l in range(j + 2, self.n):
                if self.digits[j] != self.digits[l]:
                    continue
                middle = l - j - 1
                outer = sum(self.prefix[a][j] * (self.prefix[a][self.n] - self.prefix[a][l + 1])
                            for a in range(10))
                total += middle * outer
        return total


def count_palindromes_11(s):
    return PalindromeCounter(s).count()


# =============================================================================
# WAY 12: For each (i, m) outer pair, count inner pair + middle
# =============================================================================
def count_palindromes_12(s):
    """For each outer pair (i, m) with i<m and s[i]==s[m]:
    - For each inner pair (j, l) with i<j<l<m and s[j]==s[l]:
      middle = l - j - 1
    Contribution: middle for each inner pair.
    """
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    total = 0
    for i in range(n):
        for m in range(i + 4, n):  # need at least 4 indices between
            if digits[i] != digits[m]:
                continue
            # Count inner pairs (j, l) with i<j<l<m and s[j]==s[l].
            # Middle count = l - j - 1.
            inner_total = 0
            for j in range(i + 1, m - 1):
                for l in range(j + 2, m):  # l - j >= 2
                    if digits[j] != digits[l]:
                        continue
                    inner_total += l - j - 1
            total += inner_total
    return total


# =============================================================================
# WAY 13: 1D prefix (10 only)
# =============================================================================
def count_palindromes_13(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    # prefix[i][d] = # of digit d in s[0..i-1]
    prefix = [[0] * 10 for _ in range(n + 1)]
    for i in range(n):
        for a in range(10):
            prefix[i + 1][a] = prefix[i][a]
        prefix[i + 1][digits[i]] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = 0
            for a in range(10):
                outer += prefix[j][a] * (prefix[n][a] - prefix[l + 1][a])
            total += middle * outer
    return total


# =============================================================================
# WAY 14: For each middle k, enumerate (j, l) inner pairs
# =============================================================================
def count_palindromes_14(s):
    """For each middle k, enumerate (j, l) with j<k<l and s[j]==s[l].
    For each such pair, contribution = sum_a count_a(j) * count_a(l+1, n).
    """
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for dig in range(10):
            prefix[dig][i + 1] = prefix[dig][i]
        prefix[d][i + 1] += 1
    total = 0
    for k in range(1, n - 1):
        for j in range(k):
            dj = digits[j]
            for l in range(k + 1, n):
                if digits[l] != dj:
                    continue
                outer = 0
                for a in range(10):
                    outer += prefix[a][j] * (prefix[a][n] - prefix[a][l + 1])
                total += outer
    return total


# =============================================================================
# WAY 15: Memoized helper
# =============================================================================
def count_palindromes_15(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    # Precompute prefix[d][i] using a helper
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def count_prefix(d, i):
        """Count of digit d in s[0..i-1]."""
        c = 0
        for x in range(i):
            if digits[x] == d:
                c += 1
        return c

    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = 0
            for a in range(10):
                outer += count_prefix(a, j) * (count_prefix(a, n) - count_prefix(a, l + 1))
            total += middle * outer
    return total


# =============================================================================
# WAY 16: Generator-based
# =============================================================================
def count_palindromes_16(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for dig in range(10):
            prefix[dig][i + 1] = prefix[dig][i]
        prefix[d][i + 1] += 1

    def contributions():
        for j in range(n):
            for l in range(j + 2, n):
                if digits[j] != digits[l]:
                    continue
                middle = l - j - 1
                outer = sum(prefix[a][j] * (prefix[a][n] - prefix[a][l + 1]) for a in range(10))
                yield middle * outer

    return sum(contributions())


# =============================================================================
# WAY 17: With explicit reduce for outer sum
# =============================================================================
def count_palindromes_17(s):
    from functools import reduce
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for dig in range(10):
            prefix[dig][i + 1] = prefix[dig][i]
        prefix[d][i + 1] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = reduce(
                lambda acc, a: acc + prefix[a][j] * (prefix[a][n] - prefix[a][l + 1]),
                range(10),
                0,
            )
            total += middle * outer
    return total


# =============================================================================
# WAY 18: For each (j, l), sum outer per digit individually
# =============================================================================
def count_palindromes_18(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    # Use 10 prefix arrays
    pref = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        for d in range(10):
            pref[d][i + 1] = pref[d][i]
        pref[digits[i]][i + 1] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = 0
            for a in range(10):
                outer += pref[a][j] * (pref[a][n] - pref[a][l + 1])
            total += middle * outer
    return total


# =============================================================================
# WAY 19: With left/right arrays precomputed (transposed prefix)
# =============================================================================
def count_palindromes_19(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    # left[j][a] = count of digit a in s[0..j-1]
    # right[l][a] = count of digit a in s[l+1..n-1]
    left = [[0] * 10 for _ in range(n + 1)]
    for i in range(n):
        for a in range(10):
            left[i + 1][a] = left[i][a]
        left[i + 1][digits[i]] += 1
    right = [[0] * 10 for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for a in range(10):
            right[i][a] = right[i + 1][a]
        right[i][digits[i]] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = sum(left[j][a] * right[l + 1][a] for a in range(10))
            total += middle * outer
    return total


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def count_palindromes_20(s):
    """
    THE ONE TO MEMORIZE.

    For each INNER pair (j, l) with j<l and s[j]==s[l]:
      - middle_count = l - j - 1 (choices for k).
      - outer_count = sum over 'a' of (# of a in s[0..j-1]) * (# of a in s[l+1..n-1])
      - contribution = middle_count * outer_count
    Total = sum of contributions.

    Time:  O(n^2 * 10) where n=10^4 (10 = # digits).
    Space: O(n * 10) for prefix counts.
    """
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    # prefix[a][i] = # of digit a in s[0..i-1]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for a in range(10):
            prefix[a][i + 1] = prefix[a][i]
        prefix[d][i + 1] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = 0
            for a in range(10):
                outer += prefix[a][j] * (prefix[a][n] - prefix[a][l + 1])
            total += middle * outer
    return total


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count 5-character subsequences of s that form a palindrome.
A 5-character palindrome has the form a b c b a, so I need tuples
(i < j < k < l < m) where s[i]=s[m]='a', s[j]=s[l]='b', and s[k]='c'."

Key Insight:
"For each INNER pair (j, l) with j<l and s[j]==s[l]:
- middle_count = l - j - 1 (choices for k)
- outer_count = sum over 'a' of count_a_in_left(j) * count_a_in_right(l+1, n)
- contribution = middle_count * outer_count

This counts all valid (i, k, m) choices for fixed (j, l)."

Algorithm:
1. Build prefix[d][i] = # of digit d in s[0..i-1] for each d in 0..9.
2. For each j from 0 to n-1:
   - For each l from j+2 to n-1:
     - If s[j] != s[l], skip.
     - middle = l - j - 1
     - outer = sum over a of prefix[a][j] * (prefix[a][n] - prefix[a][l+1])
     - Add middle * outer to total.
3. Return total.

Edge Cases:
- n < 5: return 0.
- All same digit ("11111"): pairs give the answer.
- Distinct digits: 0.

Complexity:
+----------+-------------+----------+
| Approach | Time        | Space    |
+----------+-------------+----------+
| Best     | O(10 * n^2) | O(10*n)  |
| Brute    | O(n^5)      | O(1)     |
| O(n^4)   | O(n^4)      | O(1)     |
+----------+-------------+----------+
With n=10^4 and 10 digits, prefix approach is best.

WHY INNER PAIR (not outer or middle):
Fixing inner pair (j, l) gives:
- middle k has (l-j-1) choices.
- outer (i, m) factorizes cleanly: count_a in left * count_a in right.
- No overcount or ordering issues.

If we fixed outer pair (i, m), the middle k has (m-i-1) choices but the
inner pair (j, l) requires j<k<l with s[j]==s[l], which is harder to
factorize.

If we fixed middle k, the inner pair (j, l) straddles k with s[j]==s[l],
and the outer pair (i, m) needs i<j, m>l — ordering constraints that
make this harder.

KEY TRICK:
Since the alphabet is only digits (10), the inner loop over digits is
constant. Total work = O(n^2 * 10) = 10^9 ops for n=10^4. With early
skip when s[j] != s[l] (only ~10% of pairs match), effective ~10^8 ops.

RELATED PROBLEMS:
- Count Palindromic Substrings (LC 647).
- Distinct Subsequences (LC 940).
- Count Different Palindromic Subsequences (LC 730).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: For each (j,l)", count_palindromes_1),
        ("Way 2: Position lists", count_palindromes_2),
        ("Way 3: Fix middle k", count_palindromes_3),
        ("Way 4: Brute O(n^5)", count_palindromes_4),
        ("Way 5: Iterate (i,m)", count_palindromes_5),
        ("Way 6: Prefix sums", count_palindromes_6),
        ("Way 7: itertools", count_palindromes_7),
        ("Way 8: Left/right running", count_palindromes_8),
        ("Way 9: On-the-fly left", count_palindromes_9),
        ("Way 10: Numpy", count_palindromes_10),
        ("Way 11: Class OOP", count_palindromes_11),
        ("Way 12: For each outer (i,m)", count_palindromes_12),
        ("Way 13: 1D prefix", count_palindromes_13),
        ("Way 14: Fix middle enumerate", count_palindromes_14),
        ("Way 15: Memoized", count_palindromes_15),
        ("Way 16: Generator", count_palindromes_16),
        ("Way 17: Reduce", count_palindromes_17),
        ("Way 18: Explicit digits", count_palindromes_18),
        ("Way 19: Transposed prefix", count_palindromes_19),
        ("Way 20: Final cleanest", count_palindromes_20),
    ]

    test_cases = [
        # (s, expected)
        ("10301", 1),
        ("11111", 1),
        ("00000", 1),
        ("10101", 1),
        ("12121", 1),
        ("11211", 1),
        ("111111", 6),
        ("1010101", 9),
        ("1212121", 9),
        ("100001", 4),
        ("110011", 2),
        ("121121", 2),
        ("12321", 1),
        ("11", 0),
        ("1", 0),
        ("", 0),
        ("0000000", 21),  # C(7,5) = 21
        ("12345", 0),
        ("99999", 1),
        # "9090909" same structure as 1010101 = 9
        ("9090909", 9),
    ]

    print("=" * 70)
    print("COUNT PALINDROMIC SUBSEQUENCES - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-palindromic-subsequences")
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