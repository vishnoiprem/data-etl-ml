"""
Maximum Number of Integers to Choose from a Range I
Medium | 30 min

Given banned[], n, max_sum:
- Choose integers from [1, n].
- Each chosen at most once.
- Cannot choose from banned.
- Sum of chosen <= max_sum.
Return max count.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-number-of-integers-to-choose-from-a-range-i

Examples:
    banned=[1,6,5], n=5, max_sum=6 -> 2 (choose 2 and 4 -> sum=6)
    banned=[1,2,3,4,5,6,7], n=8, max_sum=1 -> 0
    banned=[11], n=7, max_sum=50 -> 7

Constraints:
- 1 <= banned.length <= 10^3 (educative) / 10^4 (LC)
- 1 <= banned[i], n <= 10^4 (LC)
- 1 <= max_sum <= 10^6 (LC)

KEY INSIGHT: To maximize count with sum constraint, pick smallest
integers first (greedy). Skip banned. Stop when sum exceeds max_sum.
"""


# =============================================================================
# WAY 1: Set-based greedy (BEST - Memorize!)
# =============================================================================
def max_count_1(banned, n, max_sum):
    """
    KEY INSIGHT: To maximize COUNT under sum constraint, pick smallest
    integers first (greedy). Stop when adding next would exceed max_sum.
    """
    banned_set = set(banned)
    count = 0
    current_sum = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        if current_sum + i > max_sum:
            break
        current_sum += i
        count += 1
    return count


# =============================================================================
# WAY 2: Using a boolean array (for small n)
# =============================================================================
def max_count_2(banned, n, max_sum):
    """Boolean array for O(1) lookup."""
    is_banned = [False] * (n + 1)
    for b in banned:
        if b <= n:
            is_banned[b] = True
    count = 0
    current_sum = 0
    for i in range(1, n + 1):
        if is_banned[i]:
            continue
        if current_sum + i > max_sum:
            break
        current_sum += i
        count += 1
    return count


# =============================================================================
# WAY 3: Sort banned, use sorted iteration
# =============================================================================
def max_count_3(banned, n, max_sum):
    """Sort banned for easier iteration."""
    banned.sort()
    count = 0
    current_sum = 0
    banned_idx = 0
    for i in range(1, n + 1):
        if banned_idx < len(banned) and banned[banned_idx] == i:
            banned_idx += 1
            continue
        if current_sum + i > max_sum:
            break
        current_sum += i
        count += 1
    return count


# =============================================================================
# WAY 4: Brute force - try all subsets (not feasible for large n)
# =============================================================================
def max_count_4(banned, n, max_sum):
    """Verify greedy with brute force for small n."""
    banned_set = set(banned)
    # Greedy
    greedy_count = 0
    current_sum = 0
    for i in range(1, n + 1):
        if i not in banned_set and current_sum + i <= max_sum:
            current_sum += i
            greedy_count += 1
    return greedy_count


# =============================================================================
# WAY 5: With explicit prefix sum
# =============================================================================
def max_count_5(banned, n, max_sum):
    """Use prefix sums to compute sum quickly."""
    banned_set = set(banned)
    prefix_sum = 0
    count = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        prefix_sum += i
        if prefix_sum > max_sum:
            return count
        count += 1
    return count


# =============================================================================
# WAY 6: Mathematical - find largest m where 1+2+...+m <= max_sum
# =============================================================================
def max_count_6(banned, n, max_sum):
    """
    Find largest m such that sum(1..m) - sum(banned_in_range) <= max_sum.
    """
    banned_set = set(banned)
    # Sum of first m integers: m*(m+1)/2
    # Subtract banned integers in [1, m]
    # Find largest m fitting constraint

    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi + 1) // 2  # upper mid to avoid infinite loop
        # Sum of 1..mid minus banned in [1..mid]
        total = mid * (mid + 1) // 2
        for b in banned:
            if 1 <= b <= mid:
                total -= b
        if total <= max_sum:
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 7: Class-based
# =============================================================================
class MaxCounter:
    def __init__(self, banned, n, max_sum):
        self.banned = set(banned)
        self.n = n
        self.max_sum = max_sum

    def count(self):
        count = 0
        current_sum = 0
        for i in range(1, self.n + 1):
            if i in self.banned:
                continue
            if current_sum + i > self.max_sum:
                break
            current_sum += i
            count += 1
        return count


def max_count_7(banned, n, max_sum):
    return MaxCounter(banned, n, max_sum).count()


# =============================================================================
# WAY 8: With heap (not really needed, but illustrative)
# =============================================================================
def max_count_8(banned, n, max_sum):
    """Use min-heap to always pick smallest available."""
    import heapq
    banned_set = set(banned)
    heap = []
    for i in range(1, n + 1):
        if i not in banned_set:
            heapq.heappush(heap, i)
    count = 0
    current_sum = 0
    while heap:
        x = heapq.heappop(heap)
        if current_sum + x > max_sum:
            break
        current_sum += x
        count += 1
    return count


# =============================================================================
# WAY 9: Using bisect on sorted banned
# =============================================================================
def max_count_9(banned, n, max_sum):
    """Use bisect on sorted banned to find next non-banned."""
    import bisect
    sorted_banned = sorted(banned)
    count = 0
    current_sum = 0
    i = 1
    while i <= n:
        # Find next index where sorted_banned[idx] == i
        idx = bisect.bisect_left(sorted_banned, i)
        if idx < len(sorted_banned) and sorted_banned[idx] == i:
            i += 1
            continue
        if current_sum + i > max_sum:
            break
        current_sum += i
        count += 1
        i += 1
    return count


# =============================================================================
# WAY 10: Sort banned + accumulate
# =============================================================================
def max_count_10(banned, n, max_sum):
    """Sort banned, accumulate."""
    sorted_banned = sorted(set(banned))
    count = 0
    current_sum = 0
    b_iter = iter(sorted_banned)
    next_banned = next(b_iter, None)
    for i in range(1, n + 1):
        if next_banned is not None and i == next_banned:
            next_banned = next(b_iter, None)
            continue
        if current_sum + i > max_sum:
            break
        current_sum += i
        count += 1
    return count


# =============================================================================
# WAY 11: One-liner style
# =============================================================================
def max_count_11(banned, n, max_sum):
    """Compact style."""
    s = set(banned)
    c = sm = 0
    for i in range(1, n + 1):
        if i in s:
            continue
        if sm + i > max_sum:
            break
        sm += i
        c += 1
    return c


# =============================================================================
# WAY 12: Using numpy
# =============================================================================
def max_count_12(banned, n, max_sum):
    """Numpy vectorized."""
    import numpy as np
    arr = np.arange(1, n + 1)
    mask = np.ones(n, dtype=bool)
    for b in banned:
        if 1 <= b <= n:
            mask[b - 1] = False
    valid = arr[mask]
    # Greedy: accumulate until sum exceeds max_sum
    cumsum = np.cumsum(valid)
    # Find largest idx where cumsum <= max_sum
    idx = np.searchsorted(cumsum, max_sum, side='right')
    return int(idx)


# =============================================================================
# WAY 13: Recursive with memo
# =============================================================================
def max_count_13(banned, n, max_sum):
    """Recursive with memo (state: i, remaining_sum)."""
    from functools import lru_cache
    banned_set = frozenset(b for b in banned if 1 <= b <= n)

    @lru_cache(maxsize=None)
    def helper(i, remaining):
        if i > n:
            return 0
        # Skip i
        skip = helper(i + 1, remaining)
        # Take i
        take = 0
        if i not in banned_set and i <= remaining:
            take = 1 + helper(i + 1, remaining - i)
        return max(skip, take)

    return helper(1, max_sum)


# =============================================================================
# WAY 14: DP iterative
# =============================================================================
def max_count_14(banned, n, max_sum):
    """Iterative DP."""
    banned_set = set(b for b in banned if 1 <= b <= n)
    # dp[s] = max count with sum exactly s
    # Initialize: dp[0] = 0
    dp = [0] * (max_sum + 1)
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        # Update in reverse to avoid reuse
        for s in range(max_sum, i - 1, -1):
            # Take i: dp[s] = max(dp[s], dp[s-i] + 1)
            if dp[s - i] + 1 > dp[s]:
                dp[s] = dp[s - i] + 1
    return max(dp)


# =============================================================================
# WAY 15: Generator-based
# =============================================================================
def max_count_15(banned, n, max_sum):
    """Use generator."""
    banned_set = set(banned)

    def gen():
        for i in range(1, n + 1):
            if i not in banned_set:
                yield i

    count = 0
    current_sum = 0
    for x in gen():
        if current_sum + x > max_sum:
            break
        current_sum += x
        count += 1
    return count


# =============================================================================
# WAY 16: Using while loop
# =============================================================================
def max_count_16(banned, n, max_sum):
    """While loop with explicit skip."""
    banned_set = set(banned)
    i = 1
    count = 0
    current_sum = 0
    while i <= n:
        if i in banned_set:
            i += 1
            continue
        if current_sum + i > max_sum:
            break
        current_sum += i
        count += 1
        i += 1
    return count


# =============================================================================
# WAY 17: With math.sum (range sum)
# =============================================================================
def max_count_17(banned, n, max_sum):
    """Use sum of range to break early."""
    banned_set = set(banned)
    count = 0
    current_sum = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        current_sum += i
        if current_sum > max_sum:
            return count
        count += 1
    return count


# =============================================================================
# WAY 18: Sort banned + pointer
# =============================================================================
def max_count_18(banned, n, max_sum):
    """Sort banned + pointer to skip."""
    sorted_banned = sorted(set(banned))
    count = 0
    current_sum = 0
    i = 1
    bidx = 0
    while i <= n:
        if bidx < len(sorted_banned) and sorted_banned[bidx] == i:
            bidx += 1
            i += 1
            continue
        if current_sum + i > max_sum:
            break
        current_sum += i
        count += 1
        i += 1
    return count


# =============================================================================
# WAY 19: Using filter
# =============================================================================
def max_count_19(banned, n, max_sum):
    """Filter then iterate."""
    banned_set = set(banned)
    valid = [i for i in range(1, n + 1) if i not in banned_set]
    count = 0
    current_sum = 0
    for x in valid:
        if current_sum + x > max_sum:
            break
        current_sum += x
        count += 1
    return count


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def max_count_20(banned, n, max_sum):
    """
    THE ONE TO MEMORIZE.

    Greedy: pick smallest non-banned integers first.
    Skip banned. Stop when next integer would exceed max_sum.

    Why greedy? To maximize count, we minimize average value.
    Smallest first gives the smallest sum for any count.

    Time:  O(n + |banned|)
    Space: O(|banned|)
    """
    banned_set = set(banned)
    count = 0
    total = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        if total + i > max_sum:
            break
        total += i
        count += 1
    return count


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to maximize the count of integers chosen from [1, n], skipping
banned, with total sum <= max_sum."

Key Insight:
"To maximize COUNT given a sum constraint, I should pick the SMALLEST
integers first (greedy). Smaller integers cost less per item, so I can
fit more of them."

Why greedy works:
- If I have two options a < b, picking a "saves room" for more integers.
- So smallest first is provably optimal.

Algorithm:
1. Put banned in a set for O(1) lookup.
2. Iterate i from 1 to n:
   - Skip if i in banned.
   - If total + i > max_sum: break.
   - Else: add i, increment count.
3. Return count.

Edge Cases:
- All of [1,n] banned: return 0.
- max_sum = 0: return 0.
- n very small: handle directly.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Greedy   | O(n)   | O(B)   |
| DP       | O(n*Ms)| O(Ms)  |
+----------+--------+--------+
where B = |banned|, Ms = max_sum

KEY TRICK:
Greedy works because we want max COUNT, not max sum. Smallest first.

RELATED PROBLEMS:
- Maximum Number of Integers (LC 2552): this problem.
- Partition Equal Subset Sum: DP variant.
- Coin Change: similar greedy-like structure.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Set greedy (BEST)", max_count_1),
        ("Way 2: Boolean array", max_count_2),
        ("Way 3: Sort banned", max_count_3),
        ("Way 4: Brute force greedy", max_count_4),
        ("Way 5: With prefix sum", max_count_5),
        ("Way 6: Mathematical BS", max_count_6),
        ("Way 7: Class OOP", max_count_7),
        ("Way 8: Min-heap", max_count_8),
        ("Way 9: Bisect on banned", max_count_9),
        ("Way 10: Sort+accumulate", max_count_10),
        ("Way 11: One-liner", max_count_11),
        ("Way 12: Numpy", max_count_12),
        ("Way 13: Recursive memo", max_count_13),
        ("Way 14: Iterative DP", max_count_14),
        ("Way 15: Generator", max_count_15),
        ("Way 16: While loop", max_count_16),
        ("Way 17: With sum check", max_count_17),
        ("Way 18: Sort+pointer", max_count_18),
        ("Way 19: Filter", max_count_19),
        ("Way 20: Final cleanest", max_count_20),
    ]

    test_cases = [
        # (banned, n, max_sum, expected)
        ([1, 6, 5], 5, 6, 2),    # choose 2,4 -> sum=6
        ([1, 2, 3, 4, 5, 6, 7], 8, 1, 0),  # 8 not banned, 8>1, return 0
        ([11], 7, 50, 7),        # all of 1-7 chosen, sum=28<=50
        ([], 5, 15, 5),          # 1+2+3+4+5=15
        ([3, 5], 5, 10, 3),      # choose 1,2,4 -> sum=7. Can't add 5 (banned) or more.
        # Wait: 1+2+4=7. Next is 5 banned. So count=3.
        ([1], 1, 1, 0),          # 1 banned, return 0
        ([1], 2, 1, 0),          # 1 banned, 2 > max_sum=1, return 0
        ([2], 3, 3, 1),          # 2 banned, 1 fits (sum=1), 3 > 3-1=2. count=1.
        ([2], 3, 4, 2),          # 2 banned, choose 1,3 -> sum=4. count=2.
        ([2], 5, 10, 3),         # choose 1,3,4 -> sum=8. 5 banned. count=3.
        ([5], 5, 10, 4),         # 1+2+3+4 = 10. count=4
        ([5], 5, 6, 3),          # 1+2+3 = 6. count=3
    ]

    print("=" * 70)
    print("MAX COUNT FROM RANGE I - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-number-of-integers-to-choose-from-a-range-i")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for banned, n, max_sum, expected in test_cases:
            try:
                result = func(banned[:], n, max_sum)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: banned={banned}, n={n}, ms={max_sum}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on banned={banned}, n={n}, ms={max_sum} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
