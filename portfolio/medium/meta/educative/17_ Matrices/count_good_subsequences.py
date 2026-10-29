"""
Count the Number of Good Subsequences
Medium | 30 min

Count good subsequences in s. A subsequence is good if non-empty and
all character frequencies are equal.

Return count modulo 10^9 + 7.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-the-number-of-good-subsequences

Examples:
    s='aab'  -> 6   (k=1: a, aa-pos0, aa-pos1, b, ab-pos0, ab-pos1; k=2: invalid)
    s='abc'  -> 7   (k=1: 2^3 - 1 = 7)
    s='a'    -> 1
    s='ab'   -> 3   (a, b, ab)

Constraints:
- 1 <= s.length <= 10^4
- Lowercase English letters.

KEY INSIGHT:
A good subsequence is k-uniform: each USED char appears exactly k times.
For each k >= 1, count subsequences where each used char has count k.

For each k: each character independently either:
- Not used (1 way), OR
- Used k times: C(cnt[c], k) ways.

Total ways per k = prod over c of (1 + C(cnt[c], k)).
Subtract 1 (empty subsequence).

Answer = sum over k from 1 to max(cnt) of (prod - 1) mod M.

MOD = 10^9 + 7.
"""


# =============================================================================
# WAY 1: Combinatorial formula (BEST - Memorize!)
# =============================================================================
def count_good_1(s):
    """Formula: sum over k of (prod (1 + C(cnt[c], k)) - 1)."""
    MOD = 10**9 + 7
    from math import comb
    from collections import Counter
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    total = 0
    for k in range(1, max_k + 1):
        prod = 1
        for c, cnt in freq.items():
            prod = (prod * (1 + comb(cnt, k))) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 2: Pre-compute comb values
# =============================================================================
def count_good_2(s):
    """Pre-compute comb table for faster access."""
    MOD = 10**9 + 7
    from collections import Counter
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    # Pre-compute comb(cnt, k) for each cnt and k.
    def nCr(n, r):
        if r > n or r < 0:
            return 0
        if r == 0 or r == n:
            return 1
        if r > n - r:
            r = n - r
        res = 1
        for i in range(r):
            res = res * (n - i) // (i + 1)
        return res

    total = 0
    for k in range(1, max_k + 1):
        prod = 1
        for c, cnt in freq.items():
            prod = (prod * (1 + nCr(cnt, k))) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 3: DP on character subsets
# =============================================================================
def count_good_3(s):
    """DP: track for each char whether used k times."""
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    # For each k, compute product of (1 + C(cnt, k)).
    total = 0
    for k in range(1, max_k + 1):
        prod = 1
        for cnt in freq.values():
            prod = (prod * (1 + comb(cnt, k))) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 4: Brute force with bitmask
# =============================================================================
def count_good_4(s):
    """Try all subsequences via bitmask. O(2^n * n)."""
    MOD = 10**9 + 7
    from collections import Counter
    n = len(s)
    count = 0
    for mask in range(1, 1 << n):
        chars = [s[i] for i in range(n) if mask & (1 << i)]
        freq = Counter(chars)
        fs = set(freq.values())
        if len(fs) == 1:
            count = (count + 1) % MOD
    return count


# =============================================================================
# WAY 5: Iterate over subsets of positions per character
# =============================================================================
def count_good_5(s):
    """For each k, count subsequences with k-uniform frequency."""
    MOD = 10**9 + 7
    from collections import Counter, defaultdict
    from math import comb
    positions = defaultdict(list)
    for i, c in enumerate(s):
        positions[c].append(i)
    if not positions:
        return 0
    max_k = max(len(p) for p in positions.values())
    total = 0
    for k in range(1, max_k + 1):
        # Each char: not used (1) OR used k times (C(cnt, k))
        prod = 1
        for pos in positions.values():
            cnt = len(pos)
            prod = (prod * (1 + comb(cnt, k))) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 6: Class OOP
# =============================================================================
class GoodSubseqCounter:
    def __init__(self, s):
        self.s = s

    def count(self):
        MOD = 10**9 + 7
        from collections import Counter
        from math import comb
        freq = Counter(self.s)
        if not freq:
            return 0
        max_k = max(freq.values())
        total = 0
        for k in range(1, max_k + 1):
            prod = 1
            for cnt in freq.values():
                prod = (prod * (1 + comb(cnt, k))) % MOD
            total = (total + prod - 1) % MOD
        return total


def count_good_6(s):
    return GoodSubseqCounter(s).count()


# =============================================================================
# WAY 7: Direct formula with iterative comb computation
# =============================================================================
def count_good_7(s):
    """Compute C(cnt, k) iteratively without math.comb."""
    MOD = 10**9 + 7
    from collections import Counter
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())

    def comb(cnt, k):
        if k > cnt:
            return 0
        # Compute iteratively.
        res = 1
        for i in range(k):
            res = res * (cnt - i) // (i + 1)
        return res

    total = 0
    for k in range(1, max_k + 1):
        prod = 1
        for cnt in freq.values():
            prod = (prod * (1 + comb(cnt, k))) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 8: Same as 1, different style
# =============================================================================
def count_good_8(s):
    """Same as Way 1 with explicit variable."""
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    ans = 0
    for k in range(1, max_k + 1):
        cur = 1
        for c in freq:
            cur = (cur * (1 + comb(freq[c], k))) % MOD
        ans = (ans + cur - 1) % MOD
    return ans


# =============================================================================
# WAY 9: Numpy vectorized approach
# =============================================================================
def count_good_9(s):
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    import numpy as np
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    total = 0
    cnts = np.array(list(freq.values()), dtype=np.int64)
    for k in range(1, max_k + 1):
        combs = np.array([comb(int(c), k) for c in cnts], dtype=np.int64)
        prod = int(np.prod((1 + combs) % MOD)) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 10: Memoized comb for each (cnt, k)
# =============================================================================
def count_good_10(s):
    MOD = 10**9 + 7
    from collections import Counter
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    memo = {}

    def comb(c, k):
        if (c, k) in memo:
            return memo[(c, k)]
        if k > c:
            memo[(c, k)] = 0
            return 0
        if k == 0 or k == c:
            memo[(c, k)] = 1
            return 1
        # Pascal's rule
        res = comb(c - 1, k - 1) + comb(c - 1, k)
        memo[(c, k)] = res
        return res

    total = 0
    for k in range(1, max_k + 1):
        prod = 1
        for cnt in freq.values():
            prod = (prod * (1 + comb(cnt, k))) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 11: Brute force without bitmask (recursive enumeration)
# =============================================================================
def count_good_11(s):
    """Recursive enumeration of all subsequences."""
    MOD = 10**9 + 7
    from collections import Counter
    n = len(s)
    count = 0

    def dfs(idx, freq):
        nonlocal count
        if idx == n:
            if freq:
                fs = set(freq.values())
                if len(fs) == 1:
                    count = (count + 1) % MOD
            return
        # Skip
        dfs(idx + 1, freq)
        # Take
        new_freq = dict(freq)
        c = s[idx]
        new_freq[c] = new_freq.get(c, 0) + 1
        dfs(idx + 1, new_freq)

    dfs(0, {})
    return count


# =============================================================================
# WAY 12: For each subset of characters, count k-uniform subsequences
# =============================================================================
def count_good_12(s):
    """For each subset of chars, count how many k-uniform sequences exist."""
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    from itertools import combinations
    freq = Counter(s)
    chars = list(freq.keys())
    n = len(chars)
    total = 0
    for k in range(1, max(freq.values()) + 1 if freq else 0):
        # For each non-empty subset of chars:
        for size in range(1, n + 1):
            for subset in combinations(chars, size):
                prod = 1
                for c in subset:
                    if freq[c] < k:
                        prod = 0
                        break
                    prod = (prod * comb(freq[c], k)) % MOD
                if prod > 0:
                    total = (total + prod) % MOD
    return total


# =============================================================================
# WAY 13: Iterate by k only, use formula
# =============================================================================
def count_good_13(s):
    """Same as Way 1 but using a helper."""
    return count_good_1(s)


# =============================================================================
# WAY 14: Using reduce
# =============================================================================
def count_good_14(s):
    """Use functools.reduce for product."""
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    from functools import reduce
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    total = 0
    for k in range(1, max_k + 1):
        prod = reduce(lambda a, c: (a * (1 + comb(c, k))) % MOD, freq.values(), 1)
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 15: Larger constraints (sanity check)
# =============================================================================
def count_good_15(s):
    """Same as 1 with explicit int() wrapping."""
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    total = 0
    for k in range(1, max_k + 1):
        prod = 1
        for c in freq:
            v = (1 + comb(freq[c], k))
            prod = (prod * v) % MOD
        total = (total + prod - 1 + MOD) % MOD
    return total


# =============================================================================
# WAY 16: Cache freq computed once
# =============================================================================
def count_good_16(s):
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    freq = sorted(Counter(s).values())
    if not freq:
        return 0
    max_k = max(freq)
    total = 0
    for k in range(1, max_k + 1):
        prod = 1
        for cnt in freq:
            prod = (prod * (1 + comb(cnt, k))) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 17: Direct formula via pow (avoiding math.comb)
# =============================================================================
def count_good_17(s):
    MOD = 10**9 + 7
    from collections import Counter
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())

    def comb(c, k):
        if k > c:
            return 0
        res = 1
        for i in range(k):
            res = res * (c - i) // (i + 1)
        return res

    total = 0
    for k in range(1, max_k + 1):
        # For each k: prod (1 + C(cnt, k)) - 1
        prod = 1
        for cnt in freq.values():
            v = 1 + comb(cnt, k)
            prod = (prod * v) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 18: Iterative enumeration with pre-computed lists
# =============================================================================
def count_good_18(s):
    """Pre-compute C(cnt, k) for all cnt, k combinations."""
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    # Pre-compute comb table.
    comb_table = {}
    for cnt in set(freq.values()):
        for k in range(1, cnt + 1):
            comb_table[(cnt, k)] = comb(cnt, k)
    total = 0
    for k in range(1, max_k + 1):
        prod = 1
        for cnt in freq.values():
            v = 1 + comb_table.get((cnt, k), 0)
            prod = (prod * v) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 19: Using Counter.values() directly
# =============================================================================
def count_good_19(s):
    """Loop over Counter.values()."""
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    vals = list(Counter(s).values())
    if not vals:
        return 0
    max_k = max(vals)
    total = 0
    for k in range(1, max_k + 1):
        prod = 1
        for v in vals:
            prod = (prod * (1 + comb(v, k))) % MOD
        total = (total + prod - 1) % MOD
    return total


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def count_good_20(s):
    """
    THE ONE TO MEMORIZE.

    For each k >= 1, count subsequences where each USED char appears k times.

    Each char independently: not used (1 way) OR used k times (C(cnt, k) ways).
    Per-k total: prod over chars of (1 + C(cnt, k)).
    Subtract 1 for empty subsequence.

    Answer = sum over k from 1 to max(cnt) of (prod - 1) mod M.

    Time:  O(K * 26) where K = max char count, 26 = alphabet size.
    Space: O(1).
    """
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    ans = 0
    for k in range(1, max_k + 1):
        prod = 1
        for cnt in freq.values():
            prod = (prod * (1 + comb(cnt, k))) % MOD
        ans = (ans + prod - 1) % MOD
    return ans


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"Count good subsequences where each character's frequency is the same.
Return mod 10^9 + 7."

Key Insight:
"A good subsequence is k-uniform: each used char appears exactly k times.
For each k >= 1, count subsequences with this property.

Each character independently:
- Not used (1 way), OR
- Used k times (C(cnt[c], k) ways).

So per k, total = prod over c of (1 + C(cnt[c], k)).
Subtract 1 for empty.

Answer = sum over k from 1 to max(cnt) of (prod - 1)."

Algorithm:
1. freq = Counter(s). Find max_k.
2. For k in 1..max_k:
     prod = 1
     For each char c: prod *= (1 + C(freq[c], k))
     ans += prod - 1
3. Return ans mod M.

Edge Cases:
- Empty s: 0 (constraint says len >= 1).
- Single char: 1.
- All same: max_k = n, many k-uniform sequences.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Formula  | O(K*S) | O(S)   |
| Brute bitmask| O(2^n)| O(n) |
+----------+--------+--------+
K = max char freq, S = alphabet size (26).

THE TRICK:
- (1 + C(cnt, k)) captures 'not used' (1) and 'used k times' (C(cnt, k)).
- Product over chars = independent choices.
- Subtract 1 for empty subsequence.

RELATED:
- Subsequence counting problems.
- Inclusion-exclusion.
- Combinatorial DP.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Formula (BEST)", count_good_1),
        ("Way 2: Pre-compute", count_good_2),
        ("Way 3: DP subsets", count_good_3),
        ("Way 4: Brute bitmask", count_good_4),
        ("Way 5: Per char positions", count_good_5),
        ("Way 6: Class OOP", count_good_6),
        ("Way 7: Iterative comb", count_good_7),
        ("Way 8: Explicit variable", count_good_8),
        ("Way 9: Numpy", count_good_9),
        ("Way 10: Memoized comb", count_good_10),
        ("Way 11: Brute recursion", count_good_11),
        ("Way 12: Subset iteration", count_good_12),
        ("Way 13: Same as 1", count_good_13),
        ("Way 14: Reduce", count_good_14),
        ("Way 15: Modulo wrap", count_good_15),
        ("Way 16: Sorted freq", count_good_16),
        ("Way 17: comb function", count_good_17),
        ("Way 18: Pre-compute table", count_good_18),
        ("Way 19: Counter.values", count_good_19),
        ("Way 20: Final cleanest", count_good_20),
    ]

    # Brute force (without dedup) verified expected values
    test_cases = [
        ("aab", 6),
        ("abc", 7),
        ("aaaa", 15),
        ("aabb", 11),
        ("a", 1),
        ("aa", 3),
        ("ab", 3),
        ("aabbcc", 33),
        ("abcabc", 33),
        ("xyz", 7),
        ("aaaaaa", 63),  # n=6: k=1..6, prod = (1+C(6,k))-1
        ("", 0),  # Edge: empty
    ]

    print("=" * 70)
    print("COUNT GOOD SUBSEQUENCES - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-the-number-of-good-subsequences")
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
