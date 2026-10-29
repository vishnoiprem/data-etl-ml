"""
Count Pairs in Two Arrays
Medium | 30 min

Given two integer arrays nums1 and nums2 of length n, count pairs (i, j) with
i < j such that nums1[i] + nums1[j] > nums2[i] + nums2[j].

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-pairs-in-two-arrays

Constraints:
- 1 <= n <= 10^3
- 1 <= nums1[i], nums2[i] <= 10^4

Examples:
    nums1=[2,4,6], nums2=[1,3,5] -> 3
    (Pairs: (0,1) 2+4>1+3, (0,2) 2+6>1+5, (1,2) 4+6>3+5)

Key Insight:
Rearrange the inequality:
    nums1[i] + nums1[j] > nums2[i] + nums2[j]
    (nums1[i] - nums2[i]) + (nums1[j] - nums2[j]) > 0
    diff[i] + diff[j] > 0
where diff[k] = nums1[k] - nums2[k].

After sorting diff, for each i, find the first j > i where diff[j] > -diff[i]
using binary search. The number of valid j's is n - j.

Time:  O(n log n) — sort + n binary searches.
Space: O(n) for the diff array.
"""


# =============================================================================
# WAY 1: Sort + bisect_right (BEST - Memorize!)
# =============================================================================
def count_pairs_1(nums1, nums2):
    """
    Build diff, sort, then for each i, binary search for valid j > i.
    """
    import bisect
    n = len(nums1)
    diff = sorted([nums1[i] - nums2[i] for i in range(n)])
    count = 0
    for i in range(n - 1):
        # Need diff[j] > -diff[i], first such j (strict greater)
        idx = bisect.bisect_right(diff, -diff[i])
        # All indices from idx..n-1 work, but only those > i count
        # Since diff is sorted and diff[i] is at position i (or close),
        # idx >= i+1 typically. We need max(idx, i+1).
        valid = n - max(idx, i + 1)
        count += valid
    return count


# =============================================================================
# WAY 2: Verbose with explicit comments
# =============================================================================
def count_pairs_2(nums1, nums2):
    """Verbose version."""
    n = len(nums1)
    # Compute differences
    diff = [0] * n
    for i in range(n):
        diff[i] = nums1[i] - nums2[i]
    # Sort diff
    diff.sort()
    # For each i, count j > i where diff[i] + diff[j] > 0
    # That is, diff[j] > -diff[i]
    import bisect
    count = 0
    for i in range(n - 1):
        target = -diff[i]
        # Find first index >= i+1 where diff[j] > target
        # bisect_right gives first index where diff > target
        idx = bisect.bisect_right(diff, target)
        # We need j > i, so j starts at i+1
        start = max(idx, i + 1)
        count += n - start
    return count


# =============================================================================
# WAY 3: Brute force O(n^2)
# =============================================================================
def count_pairs_3(nums1, nums2):
    """Brute force O(n^2)."""
    n = len(nums1)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if nums1[i] + nums1[j] > nums2[i] + nums2[j]:
                count += 1
    return count


# =============================================================================
# WAY 4: Brute force with diff
# =============================================================================
def count_pairs_4(nums1, nums2):
    """Brute force using diff."""
    n = len(nums1)
    diff = [nums1[i] - nums2[i] for i in range(n)]
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if diff[i] + diff[j] > 0:
                count += 1
    return count


# =============================================================================
# WAY 5: Sort + bisect_left (need to handle equality)
# =============================================================================
def count_pairs_5(nums1, nums2):
    """
    Use bisect_left to find first index where diff[j] >= -diff[i] + 1,
    equivalently bisect_right on -diff[i].
    """
    import bisect
    n = len(nums1)
    diff = sorted(nums1[i] - nums2[i] for i in range(n))
    count = 0
    for i in range(n - 1):
        # Need diff[j] > -diff[i], strict inequality
        idx = bisect.bisect_right(diff, -diff[i])
        start = max(idx, i + 1)
        count += n - start
    return count


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class PairCounter:
    def __init__(self, nums1, nums2):
        self.nums1 = nums1
        self.nums2 = nums2
        self.n = len(nums1)

    def count(self):
        import bisect
        diff = sorted(self.nums1[i] - self.nums2[i] for i in range(self.n))
        count = 0
        for i in range(self.n - 1):
            idx = bisect.bisect_right(diff, -diff[i])
            start = max(idx, i + 1)
            count += self.n - start
        return count


def count_pairs_6(nums1, nums2):
    """Class-based."""
    return PairCounter(nums1, nums2).count()


# =============================================================================
# WAY 7: With numpy
# =============================================================================
def count_pairs_7(nums1, nums2):
    """Vectorized with numpy."""
    try:
        import numpy as np
        a = np.array(nums1)
        b = np.array(nums2)
        diff = np.sort(a - b)
        # For each i, count j > i where diff[j] > -diff[i]
        # diff[j] > -diff[i] iff diff[j] >= -diff[i] + 1 (for integers)
        # But diff values are integers, so we need strict > which is
        # equivalent to diff[j] >= -diff[i] + 1 when values are integers.
        # However, diff can be negative. Use searchsorted with 'right' style.
        # np.searchsorted returns leftmost insertion point.
        # For first index where diff > target, use searchsorted on
        # negated diff trick.
        n = len(diff)
        count = 0
        for i in range(n - 1):
            target = -diff[i]
            # First index where diff > target
            idx = np.searchsorted(diff, target, side='right')
            start = max(idx, i + 1)
            count += n - start
        return int(count)
    except ImportError:
        return count_pairs_1(nums1, nums2)


# =============================================================================
# WAY 8: Two-pointer (since diff is sorted, we can use a different approach)
# =============================================================================
def count_pairs_8(nums1, nums2):
    """
    Sort diff. Use two-pointer: for each i, find smallest j > i with
    diff[j] > -diff[i]. But binary search is more natural here.
    """
    import bisect
    n = len(nums1)
    diff = sorted(nums1[i] - nums2[i] for i in range(n))
    count = 0
    # For each i from 0 to n-2:
    for i in range(n - 1):
        target = -diff[i]
        # Find first j where diff[j] > target, starting search at i+1
        idx = bisect.bisect_right(diff, target, i + 1, n)
        count += n - idx
    return count


# =============================================================================
# WAY 9: enumerate
# =============================================================================
def count_pairs_9(nums1, nums2):
    """Use enumerate."""
    import bisect
    n = len(nums1)
    diff = sorted(nums1[i] - nums2[i] for i in range(n))
    count = 0
    for i, d in enumerate(diff):
        if i >= n - 1:
            break
        idx = bisect.bisect_right(diff, -d)
        start = max(idx, i + 1)
        count += n - start
    return count


# =============================================================================
# WAY 10: Helper function approach
# =============================================================================
def count_pairs_10(nums1, nums2):
    """Extract helper functions."""

    def build_diff(a, b):
        return sorted(x - y for x, y in zip(a, b))

    def count_for_i(diff, i):
        import bisect
        target = -diff[i]
        idx = bisect.bisect_right(diff, target)
        start = max(idx, i + 1)
        return len(diff) - start

    diff = build_diff(nums1, nums2)
    n = len(diff)
    return sum(count_for_i(diff, i) for i in range(n - 1))


# =============================================================================
# WAY 11: Use map to compute diff
# =============================================================================
def count_pairs_11(nums1, nums2):
    """Use map to compute diff."""
    import bisect
    diff = sorted(map(lambda a, b: a - b, nums1, nums2))
    n = len(diff)
    count = 0
    for i in range(n - 1):
        idx = bisect.bisect_right(diff, -diff[i])
        start = max(idx, i + 1)
        count += n - start
    return count


# =============================================================================
# WAY 12: Functional with sum
# =============================================================================
def count_pairs_12(nums1, nums2):
    """Functional with sum."""
    import bisect
    diff = sorted(nums1[i] - nums2[i] for i in range(len(nums1)))
    n = len(diff)

    def pairs_for(i):
        idx = bisect.bisect_right(diff, -diff[i])
        return n - max(idx, i + 1)

    return sum(pairs_for(i) for i in range(n - 1))


# =============================================================================
# WAY 13: Manual binary search
# =============================================================================
def count_pairs_13(nums1, nums2):
    """Manual binary search."""

    def upper_bound(arr, target, lo, hi):
        # First index in [lo, hi) where arr[idx] > target
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] <= target:
                lo = mid + 1
            else:
                hi = mid
        return lo

    n = len(nums1)
    diff = sorted(nums1[i] - nums2[i] for i in range(n))
    count = 0
    for i in range(n - 1):
        idx = upper_bound(diff, -diff[i], i + 1, n)
        count += n - idx
    return count


# =============================================================================
# WAY 14: Reduce / accumulate
# =============================================================================
def count_pairs_14(nums1, nums2):
    """Use functools.reduce."""
    import bisect
    from functools import reduce
    diff = sorted(nums1[i] - nums2[i] for i in range(len(nums1)))
    n = len(diff)

    def add(acc, i):
        idx = bisect.bisect_right(diff, -diff[i])
        return acc + n - max(idx, i + 1)

    return reduce(add, range(n - 1), 0)


# =============================================================================
# WAY 15: Pre-compute negated diff for clarity
# =============================================================================
def count_pairs_15(nums1, nums2):
    """
    For each i, need diff[j] > -diff[i]. Equivalently,
    find pairs where diff[i] + diff[j] > 0.
    """
    import bisect
    n = len(nums1)
    diff = sorted(nums1[i] - nums2[i] for i in range(n))
    count = 0
    for i in range(n - 1):
        # Use bisect_right for strict greater than
        idx = bisect.bisect_right(diff, -diff[i])
        count += max(0, n - max(idx, i + 1))
    return count


# =============================================================================
# WAY 16: With while loop binary search
# =============================================================================
def count_pairs_16(nums1, nums2):
    """While loop binary search."""

    def first_greater(arr, target):
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] <= target:
                lo = mid + 1
            else:
                hi = mid
        return lo

    n = len(nums1)
    diff = sorted(nums1[i] - nums2[i] for i in range(n))
    count = 0
    for i in range(n - 1):
        idx = first_greater(diff, -diff[i])
        start = max(idx, i + 1)
        count += n - start
    return count


# =============================================================================
# WAY 17: itertools.starmap
# =============================================================================
def count_pairs_17(nums1, nums2):
    """Use itertools.starmap to compute diff."""
    import bisect
    from itertools import starmap
    diff = sorted(starmap(lambda a, b: a - b, zip(nums1, nums2)))
    n = len(diff)
    count = 0
    for i in range(n - 1):
        idx = bisect.bisect_right(diff, -diff[i])
        start = max(idx, i + 1)
        count += n - start
    return count


# =============================================================================
# WAY 18: Use numpy searchsorted vectorized
# =============================================================================
def count_pairs_18(nums1, nums2):
    """Fully vectorized numpy."""
    try:
        import numpy as np
        a = np.array(nums1, dtype=np.int64)
        b = np.array(nums2, dtype=np.int64)
        diff = np.sort(a - b)
        n = len(diff)
        # For each i, we need count of j in (i, n) with diff[j] > -diff[i]
        # Searchsorted with side='right' gives first index > target
        # Then subtract (i+1) since we need j > i.
        targets = -diff  # what we need diff[j] > targets[i]
        idxs = np.searchsorted(diff, targets, side='right')
        # For each i, count = max(0, n - max(idxs[i], i+1))
        counts = np.maximum(0, n - np.maximum(idxs, np.arange(1, n + 1)))
        return int(counts[:n - 1].sum())
    except ImportError:
        return count_pairs_1(nums1, nums2)


# =============================================================================
# WAY 19: Recursive count
# =============================================================================
def count_pairs_19(nums1, nums2):
    """Recursive helper for binary search."""

    def upper_bound_rec(arr, target, lo, hi):
        if lo >= hi:
            return lo
        mid = (lo + hi) // 2
        if arr[mid] <= target:
            return upper_bound_rec(arr, target, mid + 1, hi)
        else:
            return upper_bound_rec(arr, target, lo, mid)

    n = len(nums1)
    diff = sorted(nums1[i] - nums2[i] for i in range(n))
    count = 0
    for i in range(n - 1):
        idx = upper_bound_rec(diff, -diff[i], i + 1, n)
        count += n - idx
    return count


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def count_pairs_20(nums1, nums2):
    """
    Final clean version.

    Algorithm:
    1. Compute diff[i] = nums1[i] - nums2[i] for each i.
    2. Sort diff.
    3. For each i, find the first j > i where diff[j] > -diff[i] using bisect_right.
    4. The count of valid j's is n - max(idx, i+1).
    5. Sum across all i.

    Why this works:
    - (nums1[i] + nums1[j]) > (nums2[i] + nums2[j])
    - (nums1[i] - nums2[i]) + (nums1[j] - nums2[j]) > 0
    - diff[i] + diff[j] > 0
    - diff[j] > -diff[i]

    For sorted diff, all j with diff[j] > -diff[i] form a suffix. Find the
    leftmost such index with binary search.

    Time:  O(n log n).
    Space: O(n).

    Edge cases:
    - n == 1: no pairs possible, return 0.
    - All diff equal: count pairs where 2*diff > 0, i.e., diff > 0.
    - All diff zero: 0 pairs.
    """
    import bisect
    n = len(nums1)
    diff = sorted(nums1[i] - nums2[i] for i in range(n))
    count = 0
    for i in range(n - 1):
        idx = bisect.bisect_right(diff, -diff[i])
        start = max(idx, i + 1)
        count += n - start
    return count


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count pairs (i, j) with i < j where nums1[i] + nums1[j] >
nums2[i] + nums2[j]."

Key Insight:
"Rearrange the inequality: (nums1[i] - nums2[i]) + (nums1[j] - nums2[j]) > 0.
Define diff[k] = nums1[k] - nums2[k]. Now I need pairs where diff[i] +
diff[j] > 0."

Algorithm:
"1. Build diff array.
2. Sort diff in ascending order.
3. For each i, binary search for the first j where diff[j] > -diff[i].
4. All j's from that point to the end are valid.
5. Sum the counts."

Why this works:
"For sorted diff, if diff[j] > -diff[i], then all larger j's also satisfy
diff[j'] > diff[j] > -diff[i]. So they form a contiguous suffix."

Edge cases:
- n == 1: 0 pairs.
- All diff positive: all pairs.
- All diff negative: 0 pairs.
- All diff zero: 0 pairs (since diff[i] + diff[j] = 0, not > 0).
- Mix: depends on values.

Complexity:
- Time:  O(n log n) — sort dominates.
- Space: O(n) for diff array.

KEY TRICK:
bisect_right for STRICT inequality (diff[j] > -diff[i], not >=).
After sorting, find the boundary index, all to the right are valid.

BOUNDARY HANDLING:
We need j > i, so the valid range starts at max(bisect_result, i+1).
If bisect_result < i+1, all positions from i+1 onward might still need to be
checked, but if bisect_right(diff, -diff[i]) <= i, that means -diff[i] is so
small that all positions from i+1 onward have diff > -diff[i].

Wait, let me reconsider. If diff is sorted and diff[i] is at position i, and
we look for first j where diff[j] > -diff[i], then:
- If -diff[i] < diff[i]: the answer idx could be < i (since many earlier
  elements might also be > -diff[i]).
- We only care about j > i, so we use start = max(idx, i+1).

ALTERNATIVE: Brute force O(n^2)
Just check all pairs. Acceptable for n <= 1000.

ALTERNATIVE: Two-pointer variant
Sort diff. Use two pointers, but binary search is cleaner.

INTERVIEW TIPS:
1. Highlight the algebraic rearrangement (key trick).
2. Use bisect_right for STRICT inequality.
3. Remember j > i constraint, so use max(idx, i+1).
4. Verify with a small example: nums1=[2,4,6], nums2=[1,3,5] -> diff=[1,1,1].
   For i=0: need diff[j] > -1, idx=0 (since 1 > -1). start = max(0, 1) = 1.
   count += 3 - 1 = 2. ✓
   For i=1: need diff[j] > -1, idx=0. start = max(0, 2) = 2. count += 1.
   For i=2: no j > 2, skip. Total = 3. ✓
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort + bisect (BEST)", count_pairs_1),
        ("Way 2: Verbose", count_pairs_2),
        ("Way 3: Brute force", count_pairs_3),
        ("Way 4: Brute force with diff", count_pairs_4),
        ("Way 5: Sort + bisect_left", count_pairs_5),
        ("Way 6: Class-based", count_pairs_6),
        ("Way 7: numpy", count_pairs_7),
        ("Way 8: Two-pointer concept", count_pairs_8),
        ("Way 9: enumerate", count_pairs_9),
        ("Way 10: Helper functions", count_pairs_10),
        ("Way 11: map", count_pairs_11),
        ("Way 12: Functional sum", count_pairs_12),
        ("Way 13: Manual binary search", count_pairs_13),
        ("Way 14: reduce", count_pairs_14),
        ("Way 15: Negated diff", count_pairs_15),
        ("Way 16: While loop BS", count_pairs_16),
        ("Way 17: itertools.starmap", count_pairs_17),
        ("Way 18: numpy vectorized", count_pairs_18),
        ("Way 19: Recursive", count_pairs_19),
        ("Way 20: Final cleanest", count_pairs_20),
    ]

    test_cases = [
        # Example: nums1=[2,4,6], nums2=[1,3,5], diff=[1,1,1]
        # All pairs: (0,1), (0,2), (1,2) -> 3
        ([2, 4, 6], [1, 3, 5], 3),

        # n=1: no pairs
        ([5], [3], 0),

        # All diff zero: 0 pairs (need strict >)
        ([3, 5, 7], [3, 5, 7], 0),

        # All diff positive: all pairs
        # nums1=[5,6,7], nums2=[1,2,3], diff=[4,4,4]
        # All 3 pairs: (0,1),(0,2),(1,2)
        ([5, 6, 7], [1, 2, 3], 3),

        # All diff negative: 0 pairs
        ([1, 2, 3], [5, 6, 7], 0),

        # Mixed: nums1=[2,3,4,5], nums2=[5,4,3,2]
        # diff=[-3,-1,1,3] sorted=[-3,-1,1,3]
        # Brute force check pairs:
        # (0,1): 2+3=5 vs 5+4=9 -> no
        # (0,2): 2+4=6 vs 5+3=8 -> no
        # (0,3): 2+5=7 vs 5+2=7 -> no (strict)
        # (1,2): 3+4=7 vs 4+3=7 -> no (strict)
        # (1,3): 3+5=8 vs 4+2=6 -> YES
        # (2,3): 4+5=9 vs 3+2=5 -> YES
        # Total = 2
        ([2, 3, 4, 5], [5, 4, 3, 2], 2),

        # Mixed smaller: nums1=[1,5,9], nums2=[9,5,1]
        # diff=[-8,0,8] sorted=[-8,0,8]
        # i=0: need diff[j] > 8, no j -> 0
        # i=1: need diff[j] > 0, j=2 -> 1
        # Total = 1
        ([1, 5, 9], [9, 5, 1], 1),

        # With duplicates in diff:
        # nums1=[3,3,3,3], nums2=[1,1,1,1], diff=[2,2,2,2]
        # All pairs: C(4,2) = 6
        ([3, 3, 3, 3], [1, 1, 1, 1], 6),

        # Edge: diff=[-1, 1]
        # i=0: need diff[j] > 1, no j -> 0
        # Total = 0
        ([2, 5], [3, 4], 0),

        # Edge: diff=[1, -1]
        # sorted=[-1, 1]
        # Check pair (0,1): 5+2=7 vs 4+3=7 -> not > (equal, strict)
        # Total = 0
        ([5, 2], [4, 3], 0),

        # Larger example:
        # nums1=[4,5,6,7,8], nums2=[8,7,6,5,4]
        # diff=[-4,-2,0,2,4] sorted=[-4,-2,0,2,4]
        # i=0: need >4 -> 0
        # i=1: need >2 -> j=4 -> 1
        # i=2: need >0 -> j=3,4 -> 2
        # i=3: need >-2 -> j=4 -> 1
        # Total = 4
        ([4, 5, 6, 7, 8], [8, 7, 6, 5, 4], 4),

        # Two elements with positive diff both ways:
        # nums1=[10,1], nums2=[1,10]
        # diff=[9,-9] sorted=[-9,9]
        # i=0: need >9 -> 0
        # Total = 0
        ([10, 1], [1, 10], 0),
    ]

    print("=" * 70)
    print("COUNT PAIRS IN TWO ARRAYS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-pairs-in-two-arrays")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums1, nums2, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(nums1), copy.deepcopy(nums2))
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums1={nums1}, nums2={nums2} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on nums1={nums1}, nums2={nums2} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
