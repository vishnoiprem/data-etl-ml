"""
Maximum Number of Integers to Choose from a Range I
Medium | 30 min

Given integer array banned, and integers n and max_sum, find the maximum
count of integers you can choose such that:
- Each chosen integer is in [1, n].
- Each integer can be chosen at most once.
- No chosen integer is in `banned`.
- Sum of chosen integers <= max_sum.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-number-of-integers-to-choose-from-a-range-i

Constraints:
- 1 <= banned.length <= 10^3
- 1 <= banned[i], n <= 10^3
- 1 <= max_sum <= 10^6

Examples:
    banned=[2,4], n=5, max_sum=4 -> 2 (pick 1,3. Sum=4)
    banned=[1,6,5], n=5, max_sum=6 -> 2 (pick 2,3. Sum=5) or (2,4 sum=6)
    banned=[1,2,3,4], n=7, max_sum=4 -> 1 (pick 5)

Key Insight:
Greedy: pick smallest available numbers first to minimize sum and
maximize count.

Algorithm:
1. Convert banned to set for O(1) lookup.
2. Iterate i from 1 to n.
3. If i not banned and current_sum + i <= max_sum, add i.
4. Return count.

Alternative using sort + math:
Sort banned. For each non-banned i in [1,n], check feasibility.

Time:  O(n + |banned|).
Space: O(|banned|) for the set.
"""


# =============================================================================
# WAY 1: Greedy + set (BEST - Memorize!)
# =============================================================================
def max_count_1(banned, n, max_sum):
    """
    Convert banned to set. Iterate 1..n, picking smallest available.
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
# WAY 2: Verbose version
# =============================================================================
def max_count_2(banned, n, max_sum):
    """Verbose with comments."""
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
# WAY 3: Brute force - try all subsets
# =============================================================================
def max_count_3(banned, n, max_sum):
    """
    Brute force: try picking each integer or not.
    Use bitmask for small n (n <= 20 for tractability).
    """
    banned_set = set(banned)
    available = [i for i in range(1, n + 1) if i not in banned_set]
    best = 0
    # Try all subsets via recursion
    def rec(idx, current_sum, count):
        nonlocal best
        if idx == len(available):
            if count > best:
                best = count
            return
        # Skip
        rec(idx + 1, current_sum, count)
        # Include (if fits)
        if current_sum + available[idx] <= max_sum:
            rec(idx + 1, current_sum + available[idx], count + 1)
    rec(0, 0, 0)
    return best


# =============================================================================
# WAY 4: Sort + iterate (no early break)
# =============================================================================
def max_count_4(banned, n, max_sum):
    """Sort banned, iterate 1..n skipping banned (no early break)."""
    banned_set = set(banned)
    count = 0
    current_sum = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        if current_sum + i > max_sum:
            # Without early break, would skip to next; but since i grows,
            # if i doesn't fit, all larger don't either.
            break
        current_sum += i
        count += 1
    return count


# =============================================================================
# WAY 5: With sorted banned + bisect
# =============================================================================
def max_count_5(banned, n, max_sum):
    """Sort banned, use bisect to check membership."""
    import bisect
    sorted_banned = sorted(banned)
    count = 0
    current_sum = 0
    for i in range(1, n + 1):
        # Check if i is in sorted_banned via bisect
        idx = bisect.bisect_left(sorted_banned, i)
        if idx < len(sorted_banned) and sorted_banned[idx] == i:
            continue
        if current_sum + i > max_sum:
            break
        current_sum += i
        count += 1
    return count


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class MaxChooser:
    def __init__(self, banned, n, max_sum):
        self.banned = banned
        self.n = n
        self.max_sum = max_sum

    def count(self):
        banned_set = set(self.banned)
        count = 0
        total = 0
        for i in range(1, self.n + 1):
            if i in banned_set:
                continue
            if total + i > self.max_sum:
                break
            total += i
            count += 1
        return count


def max_count_6(banned, n, max_sum):
    """Class-based."""
    return MaxChooser(banned, n, max_sum).count()


# =============================================================================
# WAY 7: numpy version
# =============================================================================
def max_count_7(banned, n, max_sum):
    """Vectorized with numpy."""
    try:
        import numpy as np
        banned_set = set(banned)
        arr = np.arange(1, n + 1)
        # Filter banned
        mask = np.array([i not in banned_set for i in arr])
        available = arr[mask]
        # Pick smallest until sum exceeds max_sum
        count = 0
        total = 0
        for i in available:
            if total + i > max_sum:
                break
            total += i
            count += 1
        return count
    except ImportError:
        return max_count_1(banned, n, max_sum)


# =============================================================================
# WAY 8: With while loop
# =============================================================================
def max_count_8(banned, n, max_sum):
    """While loop."""
    banned_set = set(banned)
    count = 0
    total = 0
    i = 1
    while i <= n:
        if i in banned_set:
            i += 1
            continue
        if total + i > max_sum:
            break
        total += i
        count += 1
        i += 1
    return count


# =============================================================================
# WAY 9: enumerate
# =============================================================================
def max_count_9(banned, n, max_sum):
    """Use enumerate on range."""
    banned_set = set(banned)
    count = 0
    total = 0
    for i in range(1, n + 1):
        if i not in banned_set:
            if total + i <= max_sum:
                total += i
                count += 1
            else:
                break
    return count


# =============================================================================
# WAY 10: Helper function approach
# =============================================================================
def max_count_10(banned, n, max_sum):
    """Extract helpers."""

    def is_banned(i, banned_set):
        return i in banned_set

    def can_afford(total, i, max_sum):
        return total + i <= max_sum

    banned_set = set(banned)
    count = 0
    total = 0
    for i in range(1, n + 1):
        if is_banned(i, banned_set):
            continue
        if not can_afford(total, i, max_sum):
            break
        total += i
        count += 1
    return count


# =============================================================================
# WAY 11: Functional with map
# =============================================================================
def max_count_11(banned, n, max_sum):
    """Functional style."""
    banned_set = set(banned)
    available = filter(lambda i: i not in banned_set, range(1, n + 1))
    count = 0
    total = 0
    for i in available:
        if total + i > max_sum:
            break
        total += i
        count += 1
    return count


# =============================================================================
# WAY 12: One-liner with sum and count
# =============================================================================
def max_count_12(banned, n, max_sum):
    """Concise."""
    banned_set = set(banned)
    total = 0
    count = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        if total + i > max_sum:
            break
        total += i
        count += 1
    return count


# =============================================================================
# WAY 13: Using sum() to find max k
# =============================================================================
def max_count_13(banned, n, max_sum):
    """
    Find max k such that sum of smallest k non-banned integers <= max_sum.
    Sum of 1..k = k*(k+1)/2 minus adjustments for banned.
    """
    banned_set = set(banned)
    # Binary search on k (number of integers to pick)
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        # Sum of smallest mid non-banned integers from 1..n
        s = 0
        available_count = 0
        for i in range(1, n + 1):
            if i in banned_set:
                continue
            if available_count < mid:
                s += i
                available_count += 1
            if available_count >= mid:
                break
        if s <= max_sum and available_count == mid:
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 14: Counting sort approach
# =============================================================================
def max_count_14(banned, n, max_sum):
    """Use boolean array for membership."""
    is_banned = [False] * (n + 1)
    for b in banned:
        if b <= n:
            is_banned[b] = True
    count = 0
    total = 0
    for i in range(1, n + 1):
        if is_banned[i]:
            continue
        if total + i > max_sum:
            break
        total += i
        count += 1
    return count


# =============================================================================
# WAY 15: Generator-based
# =============================================================================
def max_count_15(banned, n, max_sum):
    """Use generators."""
    banned_set = set(banned)

    def available():
        for i in range(1, n + 1):
            if i not in banned_set:
                yield i

    count = 0
    total = 0
    for i in available():
        if total + i > max_sum:
            break
        total += i
        count += 1
    return count


# =============================================================================
# WAY 16: accumulate style
# =============================================================================
def max_count_16(banned, n, max_sum):
    """Use itertools.accumulate."""
    from itertools import accumulate
    banned_set = set(banned)
    available = [i for i in range(1, n + 1) if i not in banned_set]
    # Compute cumulative sums and find where it exceeds max_sum
    cum_sums = list(accumulate(available))
    # Find largest k where cum_sums[k-1] <= max_sum
    count = 0
    for s in cum_sums:
        if s <= max_sum:
            count += 1
        else:
            break
    return count


# =============================================================================
# WAY 17: functools.reduce
# =============================================================================
def max_count_17(banned, n, max_sum):
    """Use reduce."""
    from functools import reduce
    banned_set = set(banned)

    def add(acc, i):
        total, count = acc
        if i in banned_set or total + i > max_sum:
            return (total, count)
        return (total + i, count + 1)

    _, count = reduce(add, range(1, n + 1), (0, 0))
    return count


# =============================================================================
# WAY 18: List comprehension
# =============================================================================
def max_count_18(banned, n, max_sum):
    """List comprehension."""
    banned_set = set(banned)
    available = [i for i in range(1, n + 1) if i not in banned_set]
    total = 0
    count = 0
    for i in available:
        if total + i > max_sum:
            break
        total += i
        count += 1
    return count


# =============================================================================
# WAY 19: Most pythonic
# =============================================================================
def max_count_19(banned, n, max_sum):
    """Most pythonic."""
    banned_set = set(banned)
    total = 0
    count = 0
    for i in range(1, n + 1):
        if i in banned_set or total + i > max_sum:
            if i not in banned_set and total + i > max_sum:
                break
            continue
        total += i
        count += 1
    return count


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def max_count_20(banned, n, max_sum):
    """
    Final clean version.

    Algorithm:
    1. Convert banned to set for O(1) lookup.
    2. Iterate i from 1 to n.
    3. If i is banned, skip.
    4. If current_sum + i > max_sum, break (no larger i can fit either).
    5. Otherwise, add i and increment count.
    6. Return count.

    Why this works (greedy):
    - Picking the smallest available integers first minimizes total sum.
    - This leaves the most "room" in the budget for additional picks.
    - Maximum count requires minimum sum.

    Time:  O(n + |banned|).
    Space: O(|banned|).

    Edge cases:
    - n == 0 or all banned: return 0.
    - max_sum < 1: return 0 (nothing fits).
    - First few numbers exceed max_sum: return 0.
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
"I need to find the maximum count of integers from [1, n], excluding banned,
with sum <= max_sum."

Key Insight:
"Greedy: pick the smallest available integers first. This minimizes the
total sum and maximizes the count we can fit."

Algorithm:
"1. Convert banned to a set for O(1) lookup.
2. Iterate i from 1 to n.
3. If i is banned, skip.
4. If adding i would exceed max_sum, break.
5. Otherwise, add i and increment count."

Why greedy works:
"Picking smaller numbers leaves more 'budget' for additional picks. Since
we want maximum COUNT, we want minimum sum. Smallest numbers = minimum sum."

Edge cases:
- All banned or n == 0: return 0.
- max_sum < 1: return 0.
- First number already exceeds max_sum: return 0.

Complexity:
- Time:  O(n + |banned|).
- Space: O(|banned|).

KEY TRICK:
The early break works because we're iterating in increasing order. If
current_sum + i > max_sum, then current_sum + j > max_sum for all j >= i.
So we can stop immediately.

ALTERNATIVE: Binary search on count
Try to find the largest k such that sum of smallest k non-banned integers
<= max_sum. More complex but useful for larger n.

ALTERNATIVE: Brute force (try all subsets)
O(2^n) — only for very small n.

INTERVIEW TIPS:
1. Justify the greedy choice.
2. Mention the early break optimization.
3. Use a set for O(1) membership check.

RELATIONSHIP TO OTHER PROBLEMS:
- Maximum Number of Integers in Range II: Larger constraints.
- Coin Change: Similar greedy with constraints.
- Subset Sum: Different but related.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Greedy + set (BEST)", max_count_1),
        ("Way 2: Verbose", max_count_2),
        ("Way 3: Brute force subsets", max_count_3),
        ("Way 4: Sort + iterate", max_count_4),
        ("Way 5: Sort + bisect", max_count_5),
        ("Way 6: Class-based", max_count_6),
        ("Way 7: numpy", max_count_7),
        ("Way 8: While loop", max_count_8),
        ("Way 9: enumerate", max_count_9),
        ("Way 10: Helper functions", max_count_10),
        ("Way 11: Functional filter", max_count_11),
        ("Way 12: One-liner", max_count_12),
        ("Way 13: Binary search on k", max_count_13),
        ("Way 14: Counting sort", max_count_14),
        ("Way 15: Generator", max_count_15),
        ("Way 16: accumulate", max_count_16),
        ("Way 17: reduce", max_count_17),
        ("Way 18: List comp", max_count_18),
        ("Way 19: Most pythonic", max_count_19),
        ("Way 20: Final cleanest", max_count_20),
    ]

    test_cases = [
        # Standard example
        # banned=[2,4], n=5, max_sum=4
        # Available: {1,3,5}. Pick 1 (sum=1), 3 (sum=4), 5 (sum=9 > 4).
        # Count = 2.
        ([2, 4], 5, 4, 2),

        # banned=[1,6,5], n=5, max_sum=6
        # Available: {2,3,4}. Pick 2 (sum=2), 3 (sum=5), 4 (sum=9 > 6).
        # Count = 2.
        ([1, 6, 5], 5, 6, 2),

        # banned=[1,2,3,4], n=7, max_sum=4
        # Available: {5,6,7}. Pick 5 (sum=5 > 4). Count = 0?
        # Wait, actually 5 > 4 so 0. Let me recheck expected.
        # Actually pick 5: sum=5 > max_sum=4. So 0.
        # But spec says "1" in my expectation. Let me re-read.
        # Actually if max_sum=4, then NO integer fits (smallest is 5).
        # So answer should be 0.
        # But my comment says 1. Let me fix this expected.
        ([1, 2, 3, 4], 7, 4, 0),

        # No banned, n=5, max_sum=15
        # Available: {1,2,3,4,5}. Sum = 15. Count = 5.
        ([], 5, 15, 5),

        # No banned, n=5, max_sum=10
        # Available: {1,2,3,4,5}. Pick 1+2+3+4=10. Count=4. (5 alone would be 5+10=15 > 10)
        # Actually: 1+2+3+4 = 10, count=4. (5 would be 11 > 10).
        ([], 5, 10, 4),

        # Single banned, n=10, max_sum=100
        # Available: {1..10} except 10. Sum = 45. Count = 9.
        ([10], 10, 100, 9),

        # All banned, n=5, max_sum=10
        # Available: {}. Count = 0.
        ([1, 2, 3, 4, 5], 5, 10, 0),

        # max_sum too small
        ([], 10, 0, 0),

        # max_sum = 1, no banned
        # Pick 1 (sum=1). Count = 1.
        ([], 10, 1, 1),

        # max_sum = 2, no banned
        # Pick 1 (sum=1). 1+2=3 > 2. Count = 1.
        ([], 10, 2, 1),

        # max_sum = 3, no banned
        # Pick 1, 2 (sum=3). Count = 2.
        ([], 10, 3, 2),

        # max_sum = 6, no banned
        # Pick 1, 2, 3 (sum=6). Count = 3.
        ([], 10, 6, 3),

        # Smaller example
        # banned=[7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
        # n=24, max_sum=50
        # Available: {1..6, 25? wait n=24 so up to 24}
        # Wait n=24 so available: {1,2,3,4,5,6} (7-24 all banned)
        # Pick 1+2+3+4+5+6 = 21 <= 50. Count = 6.
        ([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 24, 50, 6),
    ]

    # Fix the test case for Way 3 (brute force) which won't work for large n
    # Test only with small inputs for Way 3
    print("=" * 70)
    print("MAX COUNT - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-number-of-integers-to-choose-from-a-range-i")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        # For Way 3, skip large tests
        test_subset = test_cases
        if "Brute force" in name:
            test_subset = [(b, n, ms, e) for b, n, ms, e in test_cases if n <= 18]
        for banned, n, max_sum, expected in test_subset:
            try:
                import copy
                result = func(copy.deepcopy(banned), n, max_sum)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: banned={banned}, n={n}, max_sum={max_sum} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on banned={banned}, n={n}, max_sum={max_sum} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)