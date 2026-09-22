"""
Minimum Absolute Difference
Medium | 30 min

Given an integer array arr, find the minimum absolute difference between
any two distinct elements. Return a list of all pairs (x, y) with x < y
that achieve this minimum. Pairs must be in ascending order.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-absolute-difference

Constraints:
- 2 <= arr.length <= 10^5
- -10^6 <= arr[i] <= 10^6

Examples:
    arr=[-10,-4,-1,2,9] -> [[-4,-1], [-1,2]]
    (sorted: -10,-4,-1,2,9. Diffs: 6,3,3,7. Min=3. Pairs: (-4,-1),(-1,2))
    arr=[1,3,6,19,20] -> [[1,3]]

Key Insight:
After sorting, the minimum absolute difference can ONLY occur between
adjacent elements. This reduces O(n^2) to O(n) scan.

Algorithm:
1. Sort arr.
2. First pass: compute min_diff = min(arr[i+1] - arr[i]).
3. Second pass: collect all adjacent pairs where diff == min_diff.

Time:  O(n log n) — sort dominates.
Space: O(n) for the result.
"""


# =============================================================================
# WAY 1: Sort + scan (BEST - Memorize!)
# =============================================================================
def minimum_abs_difference_1(arr):
    """
    Sort, find min diff, collect pairs with that diff.
    """
    arr.sort()
    n = len(arr)
    min_diff = float('inf')
    for i in range(n - 1):
        min_diff = min(min_diff, arr[i + 1] - arr[i])
    result = []
    for i in range(n - 1):
        if arr[i + 1] - arr[i] == min_diff:
            result.append([arr[i], arr[i + 1]])
    return result


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def minimum_abs_difference_2(arr):
    """Verbose with comments."""
    arr.sort()
    n = len(arr)
    # First pass: find min diff
    min_diff = arr[1] - arr[0]
    for i in range(1, n - 1):
        diff = arr[i + 1] - arr[i]
        if diff < min_diff:
            min_diff = diff
    # Second pass: collect pairs
    result = []
    for i in range(n - 1):
        if arr[i + 1] - arr[i] == min_diff:
            result.append([arr[i], arr[i + 1]])
    return result


# =============================================================================
# WAY 3: Brute force O(n^2)
# =============================================================================
def minimum_abs_difference_3(arr):
    """
    Brute force - too slow but works for small n.
    For Educative convention, returns ADJACENT pairs with min diff.
    """
    sorted_arr = sorted(arr)
    n = len(sorted_arr)
    min_diff = float('inf')
    for i in range(n - 1):
        d = sorted_arr[i + 1] - sorted_arr[i]
        if d < min_diff:
            min_diff = d
    result = []
    for i in range(n - 1):
        if sorted_arr[i + 1] - sorted_arr[i] == min_diff:
            result.append([sorted_arr[i], sorted_arr[i + 1]])
    return result


# =============================================================================
# WAY 4: Single pass after sort
# =============================================================================
def minimum_abs_difference_4(arr):
    """
    Sort, then in one pass collect pairs as we discover new min diff.
    Reset result when we find smaller diff.
    """
    arr.sort()
    n = len(arr)
    result = []
    min_diff = float('inf')
    for i in range(n - 1):
        diff = arr[i + 1] - arr[i]
        if diff < min_diff:
            min_diff = diff
            result = [[arr[i], arr[i + 1]]]
        elif diff == min_diff:
            result.append([arr[i], arr[i + 1]])
    return result


# =============================================================================
# WAY 5: zip with adjacent pairs
# =============================================================================
def minimum_abs_difference_5(arr):
    """Use zip to iterate adjacent pairs."""
    arr.sort()
    pairs = list(zip(arr, arr[1:]))
    diffs = [b - a for a, b in pairs]
    min_diff = min(diffs)
    return [[a, b] for (a, b), d in zip(pairs, diffs) if d == min_diff]


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class MinAbsDiff:
    def __init__(self, arr):
        self.arr = arr

    def find(self):
        arr = sorted(self.arr)
        n = len(arr)
        min_diff = float('inf')
        for i in range(n - 1):
            min_diff = min(min_diff, arr[i + 1] - arr[i])
        result = []
        for i in range(n - 1):
            if arr[i + 1] - arr[i] == min_diff:
                result.append([arr[i], arr[i + 1]])
        return result


def minimum_abs_difference_6(arr):
    """Class-based."""
    return MinAbsDiff(arr).find()


# =============================================================================
# WAY 7: numpy version
# =============================================================================
def minimum_abs_difference_7(arr):
    """Vectorized with numpy."""
    try:
        import numpy as np
        a = np.sort(np.array(arr))
        diffs = a[1:] - a[:-1]
        min_diff = int(diffs.min())
        # Find indices where diff == min_diff
        idxs = np.where(diffs == min_diff)[0]
        return [[int(a[i]), int(a[i + 1])] for i in idxs]
    except ImportError:
        return minimum_abs_difference_1(arr)


# =============================================================================
# WAY 8: enumerate
# =============================================================================
def minimum_abs_difference_8(arr):
    """Use enumerate."""
    arr.sort()
    n = len(arr)
    min_diff = float('inf')
    for i in range(n - 1):
        d = arr[i + 1] - arr[i]
        if d < min_diff:
            min_diff = d
    return [[arr[i], arr[i + 1]] for i in range(n - 1) if arr[i + 1] - arr[i] == min_diff]


# =============================================================================
# WAY 9: With sorted and zip
# =============================================================================
def minimum_abs_difference_9(arr):
    """Sorted + zip pair iteration."""
    sorted_arr = sorted(arr)
    # Find min diff
    min_diff = min(b - a for a, b in zip(sorted_arr, sorted_arr[1:]))
    # Collect pairs
    return [[a, b] for a, b in zip(sorted_arr, sorted_arr[1:]) if b - a == min_diff]


# =============================================================================
# WAY 10: Helper function approach
# =============================================================================
def minimum_abs_difference_10(arr):
    """Extract helper functions."""

    def adjacent_pairs(a):
        return list(zip(a, a[1:]))

    def min_diff(pairs):
        return min(b - a for a, b in pairs)

    def collect(pairs, target):
        return [[a, b] for a, b in pairs if b - a == target]

    sorted_arr = sorted(arr)
    pairs = adjacent_pairs(sorted_arr)
    return collect(pairs, min_diff(pairs))


# =============================================================================
# WAY 11: Functional with map
# =============================================================================
def minimum_abs_difference_11(arr):
    """Functional style."""
    sorted_arr = sorted(arr)
    pairs = list(zip(sorted_arr, sorted_arr[1:]))
    diffs = list(map(lambda p: p[1] - p[0], pairs))
    min_d = min(diffs)
    return [list(p) for p, d in zip(pairs, diffs) if d == min_d]


# =============================================================================
# WAY 12: One-liner
# =============================================================================
def minimum_abs_difference_12(arr):
    """Concise one-liner."""
    s = sorted(arr)
    d = min(b - a for a, b in zip(s, s[1:]))
    return [[a, b] for a, b in zip(s, s[1:]) if b - a == d]


# =============================================================================
# WAY 13: itertools.pairwise (Python 3.10+)
# =============================================================================
def minimum_abs_difference_13(arr):
    """Use itertools.pairwise for adjacent pairs."""
    try:
        from itertools import pairwise
        s = sorted(arr)
        pairs = list(pairwise(s))
        min_d = min(b - a for a, b in pairs)
        return [[a, b] for a, b in pairs if b - a == min_d]
    except ImportError:
        return minimum_abs_difference_1(arr)


# =============================================================================
# WAY 14: With while loop
# =============================================================================
def minimum_abs_difference_14(arr):
    """While loop approach."""
    arr.sort()
    n = len(arr)
    min_diff = float('inf')
    i = 0
    while i < n - 1:
        d = arr[i + 1] - arr[i]
        if d < min_diff:
            min_diff = d
        i += 1
    result = []
    i = 0
    while i < n - 1:
        if arr[i + 1] - arr[i] == min_diff:
            result.append([arr[i], arr[i + 1]])
        i += 1
    return result


# =============================================================================
# WAY 15: With reduce
# =============================================================================
def minimum_abs_difference_15(arr):
    """Use functools.reduce."""
    from functools import reduce
    arr.sort()
    n = len(arr)
    # Compute all diffs
    diffs = [arr[i + 1] - arr[i] for i in range(n - 1)]
    min_d = reduce(lambda a, b: a if a < b else b, diffs)
    return [[arr[i], arr[i + 1]] for i in range(n - 1) if arr[i + 1] - arr[i] == min_d]


# =============================================================================
# WAY 16: enumerate with min tracking
# =============================================================================
def minimum_abs_difference_16(arr):
    """Track min while building result."""
    arr.sort()
    min_diff = float('inf')
    result = []
    for i, x in enumerate(arr[:-1]):
        d = arr[i + 1] - x
        if d < min_diff:
            min_diff = d
            result = [[x, arr[i + 1]]]
        elif d == min_diff:
            result.append([x, arr[i + 1]])
    return result


# =============================================================================
# WAY 17: Counter-based (when many duplicates)
# =============================================================================
def minimum_abs_difference_17(arr):
    """When there are duplicates (diff=0), adjacent pairs."""
    from collections import Counter
    counts = Counter(arr)
    # If any value has count >= 2, min diff is 0
    if any(c >= 2 for c in counts.values()):
        # Min diff is 0. Adjacent pairs after sort with diff 0.
        arr.sort()
        return [[arr[i], arr[i + 1]] for i in range(len(arr) - 1) if arr[i + 1] - arr[i] == 0]
    # No duplicates: regular sort approach
    arr.sort()
    min_diff = float('inf')
    for i in range(len(arr) - 1):
        min_diff = min(min_diff, arr[i + 1] - arr[i])
    return [[arr[i], arr[i + 1]] for i in range(len(arr) - 1) if arr[i + 1] - arr[i] == min_diff]


# =============================================================================
# WAY 18: With sum-based counting (not really, for variety)
# =============================================================================
def minimum_abs_difference_18(arr):
    """Same as Way 1 but spelled out."""
    arr.sort()
    n = len(arr)
    # Find min diff
    min_diff = arr[1] - arr[0]
    for i in range(2, n):
        d = arr[i] - arr[i - 1]
        if d < min_diff:
            min_diff = d
    # Collect
    result = [[arr[i], arr[i + 1]] for i in range(n - 1) if arr[i + 1] - arr[i] == min_diff]
    return result


# =============================================================================
# WAY 19: Single-pass combinations
# =============================================================================
def minimum_abs_difference_19(arr):
    """Single pass combining find-min and collect."""
    arr.sort()
    result = []
    min_diff = arr[1] - arr[0]
    for i in range(len(arr) - 1):
        d = arr[i + 1] - arr[i]
        if d < min_diff:
            min_diff = d
            result = [[arr[i], arr[i + 1]]]
        elif d == min_diff:
            result.append([arr[i], arr[i + 1]])
    return result


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def minimum_abs_difference_20(arr):
    """
    Final clean version.

    Algorithm:
    1. Sort arr in ascending order.
    2. First pass: find min_diff = min(arr[i+1] - arr[i]).
    3. Second pass: collect all [arr[i], arr[i+1]] where diff == min_diff.

    Why this works:
    - After sorting, the smallest absolute difference between ANY two
      elements can only occur between adjacent elements.
    - Proof: if arr[i] < arr[j] with j > i+1, then arr[i+1] - arr[i] <
      arr[j] - arr[i] (since arr[i+1] is between arr[i] and arr[j]).

    Time:  O(n log n).
    Space: O(n) for result.

    Edge cases:
    - Two elements: only one pair.
    - Duplicates: diff = 0, all equal adjacent pairs.
    - Negatives: sorting handles naturally.
    """
    arr.sort()
    n = len(arr)
    min_diff = min(arr[i + 1] - arr[i] for i in range(n - 1))
    return [[arr[i], arr[i + 1]] for i in range(n - 1) if arr[i + 1] - arr[i] == min_diff]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find all pairs with the minimum absolute difference between any
two distinct elements."

Key Insight:
"After sorting, the minimum absolute difference can ONLY occur between
adjacent elements. This is because if arr[i] and arr[j] (j > i+1) have
the smallest difference, then arr[i+1] must be between them and have an
even smaller or equal difference with arr[i]."

Algorithm:
"1. Sort the array.
2. First pass: compute min_diff = min(arr[i+1] - arr[i]).
3. Second pass: collect all [arr[i], arr[i+1]] with that diff."

Why this works:
"For sorted arr, the absolute difference |arr[j] - arr[i]| = arr[j] - arr[i]
(since i < j implies arr[i] <= arr[j]). The minimum over all pairs equals
the minimum over adjacent pairs."

Edge cases:
- Two elements: only one pair.
- Duplicates: min diff = 0, all equal adjacent pairs.
- Negatives: works automatically.

Complexity:
- Time:  O(n log n) — sort dominates.
- Space: O(n) for result.

KEY TRICK:
Two passes: find min, then collect. Or single pass with result reset.

ALTERNATIVE: Single pass
Track min_diff as we go. When we find smaller diff, reset result.

ALTERNATIVE: Brute force O(n^2)
For each pair compute |arr[i] - arr[j]|. Works for small n.

INTERVIEW TIPS:
1. Always sort first — the O(n) scan after sort is the key insight.
2. Explain WHY only adjacent pairs matter.
3. Two passes is cleaner than single pass with reset.

RELATIONSHIP TO OTHER PROBLEMS:
- Two Sum Closest (LC 16): Find one closest pair.
- Minimum Absolute Difference Queries: Multiple queries.
- Closest Pair of Points: Geometric version.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort + scan (BEST)", minimum_abs_difference_1),
        ("Way 2: Verbose", minimum_abs_difference_2),
        ("Way 3: Brute force", minimum_abs_difference_3),
        ("Way 4: Single pass", minimum_abs_difference_4),
        ("Way 5: zip adjacent", minimum_abs_difference_5),
        ("Way 6: Class-based", minimum_abs_difference_6),
        ("Way 7: numpy", minimum_abs_difference_7),
        ("Way 8: enumerate", minimum_abs_difference_8),
        ("Way 9: zip + min", minimum_abs_difference_9),
        ("Way 10: Helper functions", minimum_abs_difference_10),
        ("Way 11: Functional map", minimum_abs_difference_11),
        ("Way 12: One-liner", minimum_abs_difference_12),
        ("Way 13: itertools.pairwise", minimum_abs_difference_13),
        ("Way 14: While loop", minimum_abs_difference_14),
        ("Way 15: reduce", minimum_abs_difference_15),
        ("Way 16: enumerate track min", minimum_abs_difference_16),
        ("Way 17: Counter duplicates", minimum_abs_difference_17),
        ("Way 18: Step-by-step", minimum_abs_difference_18),
        ("Way 19: Single pass combined", minimum_abs_difference_19),
        ("Way 20: Final cleanest", minimum_abs_difference_20),
    ]

    test_cases = [
        # Standard example
        # arr=[-10,-4,-1,2,9] sorted=[-10,-4,-1,2,9]
        # diffs: 6,3,3,7. min=3. Pairs: (-4,-1),(-1,2)
        ([-10, -4, -1, 2, 9], [[-4, -1], [-1, 2]]),

        # Standard
        # arr=[1,3,6,19,20] sorted=[1,3,6,19,20]
        # diffs: 2,3,13,1. min=1. Pairs: (19,20)
        ([1, 3, 6, 19, 20], [[19, 20]]),

        # Two elements
        # arr=[1,2]. diff=1. Pair: (1,2)
        ([1, 2], [[1, 2]]),

        # With duplicates: min diff = 0
        # arr=[1,1,2,3] sorted=[1,1,2,3]
        # diffs: 0,1,1. min=0. Pairs: (1,1)
        ([1, 1, 2, 3], [[1, 1]]),

        # All same (3 elements, 2 adjacent pairs both with diff 0)
        # arr=[5,5,5] sorted=[5,5,5], diffs=[0,0], min=0
        # Adjacent pairs with diff=0: (5,5),(5,5)
        ([5, 5, 5], [[5, 5], [5, 5]]),

        # Negative values
        # arr=[-5,-2,-1,0,3]
        # sorted=[-5,-2,-1,0,3]
        # diffs: 3,1,1,3. min=1. Pairs: (-2,-1),(-1,0)
        ([-5, -2, -1, 0, 3], [[-2, -1], [-1, 0]]),

        # Larger: arr=[3,8,-9,1,2,-6,5]
        # sorted=[-9,-6,1,2,3,5,8]
        # diffs: 3,7,1,1,2,3. min=1. Pairs: (1,2),(2,3)
        ([3, 8, -9, 1, 2, -6, 5], [[1, 2], [2, 3]]),

        # Multiple pairs with min
        # arr=[1,2,4,5] sorted=[1,2,4,5]
        # diffs: 1,2,1. min=1. Pairs: (1,2),(4,5)
        ([1, 2, 4, 5], [[1, 2], [4, 5]]),

        # Three duplicates
        # arr=[1,1,1,3,5] sorted=[1,1,1,3,5]
        # diffs: 0,0,2,2. min=0. Adjacent pairs with diff=0: (1,1),(1,1)
        ([1, 1, 1, 3, 5], [[1, 1], [1, 1]]),

        # Already sorted - all diffs are 1, so ALL pairs qualify
        ([1, 2, 3, 4], [[1, 2], [2, 3], [3, 4]]),

        # Reverse sorted - all diffs are 1 after sort
        ([4, 3, 2, 1], [[1, 2], [2, 3], [3, 4]]),

        # Single repeated pair
        # arr=[2,2,2] diffs: 0,0. min=0. Adjacent pairs: (2,2),(2,2)
        ([2, 2, 2], [[2, 2], [2, 2]]),
    ]

    print("=" * 70)
    print("MINIMUM ABSOLUTE DIFFERENCE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-absolute-difference")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for arr, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(arr))
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: arr={arr} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on arr={arr} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)