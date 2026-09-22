"""
Russian Doll Envelopes
Hard | 40 min

Given envelopes (w, h), find max count of envelopes that can be nested.
Envelope A fits in B iff A.w < B.w AND A.h < B.h (strict).

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/russian-doll-envelopes

Examples:
    [[5,4],[6,4],[6,7],[2,3]] -> 3 ([2,3]->[5,4]->[6,7])
    [[1,1],[1,1],[1,1]] -> 1
    [[4,5],[4,6],[6,5]] -> 2

Constraints:
- 1 <= envelopes.length <= 10^3 (educative) / 10^5 (LC)
- 1 <= wi, hi <= 10^4 (educative) / 10^5 (LC)

KEY INSIGHT: Sort by width ASC, then for equal widths sort height DESC.
Then find LIS on heights. This prevents using two envelopes with same width.

Why? If widths equal, heights DESC means when we do LIS on heights,
equal widths won't both be selected (since heights are in decreasing
sequence within same width).
"""

import bisect


# =============================================================================
# WAY 1: Sort + LIS on heights (BEST - Memorize!)
# =============================================================================
def max_envelopes_1(envelopes):
    """
    Sort by width ASC, then for ties, height DESC.
    Then LIS on heights using binary search.
    """
    envelopes.sort(key=lambda x: (x[0], -x[1]))
    tails = []
    for _, h in envelopes:
        idx = bisect.bisect_left(tails, h)
        if idx == len(tails):
            tails.append(h)
        else:
            tails[idx] = h
    return len(tails)


# =============================================================================
# WAY 2: Sort + manual LIS
# =============================================================================
def max_envelopes_2(envelopes):
    envelopes.sort(key=lambda x: (x[0], -x[1]))
    n = len(envelopes)
    tails = []
    for i in range(n):
        h = envelopes[i][1]
        # Find position to insert
        lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < h:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(h)
        else:
            tails[lo] = h
    return len(tails)


# =============================================================================
# WAY 3: DP - O(n^2)
# =============================================================================
def max_envelopes_3(envelopes):
    """Sort by width then height, find max nesting."""
    envs = sorted(envelopes)
    n = len(envs)
    dp = [1] * n
    for i in range(n):
        for j in range(i):
            if envs[j][0] < envs[i][0] and envs[j][1] < envs[i][1]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp) if dp else 0


# =============================================================================
# WAY 4: Sort by width only + LIS (with care for ties)
# =============================================================================
def max_envelopes_4(envelopes):
    """Sort by width ASC; for ties, sort by height ASC. Then LIS.
    But this fails if widths are equal.
    Actually: we need to break ties carefully."""
    # Sort by width ASC, then height DESC for proper LIS
    envelopes.sort(key=lambda x: (x[0], -x[1]))
    heights = [h for _, h in envelopes]
    return _length_of_lis(heights)


def _length_of_lis(nums):
    tails = []
    for x in nums:
        idx = bisect.bisect_left(tails, x)
        if idx == len(tails):
            tails.append(x)
        else:
            tails[idx] = x
    return len(tails)


# =============================================================================
# WAY 5: Sort width DESC + LIS on heights (alternative)
# =============================================================================
def max_envelopes_5(envelopes):
    """Sort by width DESC; for ties, height ASC. Then LIS on heights."""
    envelopes.sort(key=lambda x: (-x[0], x[1]))
    tails = []
    for _, h in envelopes:
        idx = bisect.bisect_left(tails, h)
        if idx == len(tails):
            tails.append(h)
        else:
            tails[idx] = h
    return len(tails)


# =============================================================================
# WAY 6: Sort by both ASC + use segment tree-like approach (overkill)
# =============================================================================
def max_envelopes_6(envelopes):
    """Simple DP after sort."""
    envs = sorted(envelopes)
    n = len(envs)
    if n == 0:
        return 0
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if envs[j][0] < envs[i][0] and envs[j][1] < envs[i][1]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)


# =============================================================================
# WAY 7: With width DESC and height DESC sorting
# =============================================================================
def max_envelopes_7(envelopes):
    """Sort by both DESC, then LIS."""
    envelopes.sort(key=lambda x: (-x[0], -x[1]))
    heights = [h for _, h in envelopes]
    return _length_of_lis(heights)


# =============================================================================
# WAY 8: Using recursion + memo
# =============================================================================
def max_envelopes_8(envelopes):
    """Recursive with memo. Sort first."""
    envs = sorted(envelopes)
    n = len(envs)
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def helper(i):
        best = 1
        for j in range(i):
            if envs[j][0] < envs[i][0] and envs[j][1] < envs[i][1]:
                best = max(best, helper(j) + 1)
        return best

    if n == 0:
        return 0
    return max(helper(i) for i in range(n))


# =============================================================================
# WAY 9: Brute force - check all subsets (impractical)
# =============================================================================
def max_envelopes_9(envelopes):
    """For verification - check all permutations."""
    n = len(envelopes)
    best = 0
    # Try lengths from 1 to n
    from itertools import combinations
    for k in range(1, n + 1):
        for combo in combinations(envelopes, k):
            # Sort combo and check if it's a valid chain
            sorted_combo = sorted(combo)
            valid = all(sorted_combo[i][0] < sorted_combo[i+1][0] and
                        sorted_combo[i][1] < sorted_combo[i+1][1]
                        for i in range(len(sorted_combo) - 1))
            if valid:
                best = max(best, k)
    return best


# =============================================================================
# WAY 10: Class-based
# =============================================================================
class RussianDollSolver:
    def __init__(self, envelopes):
        self.envs = envelopes

    def solve(self):
        if not self.envs:
            return 0
        envs = sorted(self.envs, key=lambda x: (x[0], -x[1]))
        tails = []
        for _, h in envs:
            idx = bisect.bisect_left(tails, h)
            if idx == len(tails):
                tails.append(h)
            else:
                tails[idx] = h
        return len(tails)


def max_envelopes_10(envelopes):
    return RussianDollSolver(envelopes).solve()


# =============================================================================
# WAY 11: Sort + filter, then DP
# =============================================================================
def max_envelopes_11(envelopes):
    """Sort, then DP on filtered set."""
    envs = sorted(envelopes, key=lambda x: (x[0], -x[1]))
    heights = [h for _, h in envs]
    return _length_of_lis(heights)


# =============================================================================
# WAY 12: Using numpy
# =============================================================================
def max_envelopes_12(envelopes):
    """Use numpy for sort."""
    import numpy as np
    envs = np.array(envelopes)
    # Sort by width ASC, then height DESC
    sorted_idx = np.lexsort((-envs[:, 1], envs[:, 0]))
    envs = envs[sorted_idx]
    heights = envs[:, 1].tolist()
    return _length_of_lis(heights)


# =============================================================================
# WAY 13: Sort + bisect_left pattern
# =============================================================================
def max_envelopes_13(envelopes):
    """Same as Way 1 with explicit bisect_left."""
    envelopes.sort(key=lambda x: (x[0], -x[1]))
    tails = []
    for _, h in envelopes:
        i = bisect.bisect_left(tails, h)
        tails[i:i+1] = [h] if i < len(tails) else tails + [h]
    return len(tails)


# =============================================================================
# WAY 14: Using sorted() with custom key
# =============================================================================
def max_envelopes_14(envelopes):
    """Custom sort key."""
    from functools import cmp_to_key

    def cmp(a, b):
        if a[0] != b[0]:
            return a[0] - b[0]
        return b[1] - a[1]  # DESC for equal widths

    envelopes.sort(key=cmp_to_key(cmp))
    heights = [h for _, h in envelopes]
    return _length_of_lis(heights)


# =============================================================================
# WAY 15: Sort by sum, then LIS (works for some cases)
# =============================================================================
def max_envelopes_15(envelopes):
    """Sort by sum w+h ASC. This is wrong for general case but might
    work for some inputs. Include as illustration only."""
    envs = sorted(envelopes, key=lambda x: x[0] + x[1])
    n = len(envs)
    # DP
    dp = [1] * n
    for i in range(n):
        for j in range(i):
            if envs[j][0] < envs[i][0] and envs[j][1] < envs[i][1]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp) if dp else 0


# =============================================================================
# WAY 16: Iterative DP with sorted keys
# =============================================================================
def max_envelopes_16(envelopes):
    """Sort by width ASC, then height DESC. Iterative DP."""
    envs = sorted(envelopes, key=lambda x: (x[0], -x[1]))
    n = len(envs)
    if n == 0:
        return 0
    # Use LIS DP: dp[i] = smallest tail of LIS of length i+1
    tails = [float('inf')] * n
    size = 0
    for _, h in envs:
        # Find first tail >= h
        lo, hi = 0, size
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < h:
                lo = mid + 1
            else:
                hi = mid
        tails[lo] = h
        if lo == size:
            size += 1
    return size


# =============================================================================
# WAY 17: Sort + custom LIS using array
# =============================================================================
def max_envelopes_17(envelopes):
    """Use list with append + assignment."""
    envelopes.sort(key=lambda x: (x[0], -x[1]))
    tails = []
    for _, h in envelopes:
        i = bisect.bisect_left(tails, h)
        if i == len(tails):
            tails.append(h)
        else:
            tails[i] = h
    return len(tails)


# =============================================================================
# WAY 18: With min-heap of size k
# =============================================================================
def max_envelopes_18(envelopes):
    """Use min-heap. Replace first element >= h with h. Length = LIS."""
    import heapq
    envelopes.sort(key=lambda x: (x[0], -x[1]))
    heap = []
    for _, h in envelopes:
        if heap and heap[0] <= h:
            heapq.heapreplace(heap, h)
        else:
            heapq.heappush(heap, h)
    return len(heap)


# =============================================================================
# WAY 19: With dict-based lookup
# =============================================================================
def max_envelopes_19(envelopes):
    """Use dict for memoization."""
    envs = sorted(envelopes, key=lambda x: (x[0], -x[1]))
    n = len(envs)
    if n == 0:
        return 0
    tails = []
    for _, h in envs:
        i = bisect.bisect_left(tails, h)
        if i == len(tails):
            tails.append(h)
        else:
            tails[i] = h
    return len(tails)


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def max_envelopes_20(envelopes):
    """
    THE ONE TO MEMORIZE.

    1. Sort by width ASC. For ties, sort by height DESC.
       This ensures equal-width envelopes can't both fit.
    2. Find LIS on heights using binary search.
    3. Length of LIS = max envelopes.

    Time:  O(n log n)
    Space: O(n)
    """
    envelopes.sort(key=lambda x: (x[0], -x[1]))
    tails = []
    for _, h in envelopes:
        idx = bisect.bisect_left(tails, h)
        if idx == len(tails):
            tails.append(h)
        else:
            tails[idx] = h
    return len(tails)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the maximum number of envelopes that can be nested,
where A fits in B iff A.w < B.w AND A.h < B.h."

Key Insight:
"Sort by width ASC. For equal widths, sort by height DESC.
Then find LIS on heights using binary search."

Why this works:
- After sorting by width, smaller widths come first.
- For equal widths, sorting heights DESC means heights are non-increasing.
- LIS on heights with non-increasing sequence at same width: only ONE
  envelope of each width can be selected (because heights can't be
  strictly increasing when sorted DESC).

Algorithm:
1. Sort envelopes by (width ASC, height DESC).
2. Extract heights.
3. LIS using binary search on tails array.
4. Return length of tails.

Edge Cases:
- Empty input: return 0.
- All same: return 1.
- Two same widths, different heights: return 1.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Sort+LIS  | O(nlogn)| O(n)   |
| DP        | O(n^2) | O(n)   |
+-----------+--------+--------+

KEY TRICK:
Sort widths ASC, heights DESC for ties. Then standard LIS.

RELATED PROBLEMS:
- Longest Increasing Subsequence (LC 300).
- Maximum Height of Stacking Cuboids (LC 1691): 3D variant.
- Increasing Triplets (LC 334).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort+LIS (BEST)", max_envelopes_1),
        ("Way 2: Sort+manual LIS", max_envelopes_2),
        ("Way 3: DP O(n^2)", max_envelopes_3),
        ("Way 4: Sort width+LIS", max_envelopes_4),
        ("Way 5: Width DESC+LIS", max_envelopes_5),
        ("Way 6: Simple DP", max_envelopes_6),
        ("Way 7: Both DESC", max_envelopes_7),
        ("Way 8: Recursive memo", max_envelopes_8),
        ("Way 9: Brute force subsets", max_envelopes_9),
        ("Way 10: Class OOP", max_envelopes_10),
        ("Way 11: Sort+filter", max_envelopes_11),
        ("Way 12: Numpy", max_envelopes_12),
        ("Way 13: Bisect_left slice", max_envelopes_13),
        ("Way 14: cmp_to_key", max_envelopes_14),
        ("Way 15: Sort by sum", max_envelopes_15),
        ("Way 16: Iterative DP", max_envelopes_16),
        ("Way 17: Same as 1", max_envelopes_17),
        ("Way 18: Min-heap", max_envelopes_18),
        ("Way 19: Dict-based", max_envelopes_19),
        ("Way 20: Final cleanest", max_envelopes_20),
    ]

    test_cases = [
        # (envelopes, expected)
        ([[5, 4], [6, 4], [6, 7], [2, 3]], 3),  # [2,3]->[5,4]->[6,7]
        ([[1, 1], [1, 1], [1, 1]], 1),
        ([[4, 5], [4, 6], [6, 5]], 2),  # [4,5]->[6,5]
        ([[1, 2], [2, 3], [3, 4]], 3),
        ([[2, 3]], 1),
        ([], 0),
        ([[1, 1]], 1),
        ([[2, 2], [3, 3]], 2),
        ([[3, 3], [2, 2], [1, 1]], 3),
        # Tricky: equal widths
        ([[2, 100], [3, 200], [3, 50], [4, 300], [4, 100], [5, 400], [5, 200], [5, 300]], 4),
        # Sort by (w, -h): [(2,100),(3,200),(3,50),(4,300),(4,100),(5,400),(5,300),(5,200)]
        # heights: [100, 200, 50, 300, 100, 400, 300, 200]
        # LIS: 100, 200, 300, 400 -> 4 ✓
        # But with [3,200],[3,50]: only one of [3,*] can be in LIS
        # Pick 200 (idx 1). Then 50 won't help (decreasing).
        # Actually [100,200,50,300,100,400,300,200] -> 50 is less than 200, so it replaces 200? No bisect_left replaces.
        # Tails after 100: [100]
        # After 200: [100, 200]
        # After 50: [50, 200] (replaces 100)
        # After 300: [50, 200, 300]
        # After 100: [50, 100, 300]
        # After 400: [50, 100, 300, 400]
        # After 300: [50, 100, 300, 400] (replaces 300)
        # After 200: [50, 100, 200, 400]
        # Length 4. ✓
    ]

    print("=" * 70)
    print("RUSSIAN DOLL ENVELOPES - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/russian-doll-envelopes")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for env, expected in test_cases:
            try:
                result = func([e[:] for e in env])  # copy to avoid mutation
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: env={env}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on env={env} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)