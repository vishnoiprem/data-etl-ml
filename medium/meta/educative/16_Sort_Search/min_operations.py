"""
Minimum Operations to Make All Array Elements Equal
Medium | 30 min

You are given an integer array nums and an integer array queries.
For each query q in queries, find the minimum number of operations to make
all elements of nums equal to q, where each operation can increment or
decrement an element by 1.

Return the result for each query.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-operations-to-make-all-array-elements-equal

Constraints:
- 1 <= nums.length, queries.length <= 10^5
- 1 <= nums[i], queries[i] <= 10^9

Examples:
    nums=[3,1,6], queries=[4] -> [6]
    (|3-4| + |1-4| + |6-4| = 1+3+2 = 6)

    nums=[2,9,6], queries=[5,4] -> [8, 9]
    (For q=5: |2-5|+|9-5|+|6-5| = 3+4+1 = 8
     For q=4: |2-4|+|9-4|+|6-4| = 2+5+2 = 9)

Key Insight:
For each query q, total operations = sum of |nums[i] - q|.
After sorting nums, we can use prefix sums for O(log n) per query:
- Find idx = number of elements ≤ q (via bisect_right).
- Left elements (≤ q): sum (q - left) = q * idx - prefix[idx].
- Right elements (> q): sum (right - q) = (prefix[n] - prefix[idx]) - q * (n - idx).
- Total = left + right.

Time:  O((n + m) log n) for sorting + binary searches.
Space: O(n) for prefix sums.
"""


# =============================================================================
# WAY 1: Sort + prefix sums + bisect (BEST - Memorize!)
# =============================================================================
def min_operations_1(nums, queries):
    """
    Sort nums. Build prefix sums. For each query, use binary search to
    split into left (≤ q) and right (> q), compute operations separately.
    """
    n = len(nums)
    nums.sort()
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    import bisect
    result = []
    for q in queries:
        idx = bisect.bisect_right(nums, q)
        # Sum of (q - left_elem) for left elements
        left_ops = q * idx - prefix[idx]
        # Sum of (right_elem - q) for right elements
        right_ops = (prefix[n] - prefix[idx]) - q * (n - idx)
        result.append(left_ops + right_ops)
    return result


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def min_operations_2(nums, queries):
    """Verbose version with comments."""
    n = len(nums)
    sorted_nums = sorted(nums)
    # Build prefix sums
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + sorted_nums[i]

    import bisect
    result = []
    total = prefix[n]
    for q in queries:
        # Number of elements ≤ q
        idx = bisect.bisect_right(sorted_nums, q)
        # Left sum: q * idx - prefix[idx]
        left_ops = q * idx - prefix[idx]
        # Right sum: (total - prefix[idx]) - q * (n - idx)
        right_ops = (total - prefix[idx]) - q * (n - idx)
        result.append(left_ops + right_ops)
    return result


# =============================================================================
# WAY 3: Brute force
# =============================================================================
def min_operations_3(nums, queries):
    """Brute force: for each query, sum absolute differences."""
    return [sum(abs(num - q) for num in nums) for q in queries]


# =============================================================================
# WAY 4: Brute force with explicit loops
# =============================================================================
def min_operations_4(nums, queries):
    """Brute force with explicit loops."""
    result = []
    for q in queries:
        total = 0
        for num in nums:
            total += abs(num - q)
        result.append(total)
    return result


# =============================================================================
# WAY 5: Pre-sort nums once, then brute force
# =============================================================================
def min_operations_5(nums, queries):
    """Sort nums, but still brute force per query."""
    sorted_nums = sorted(nums)
    return [sum(abs(num - q) for num in sorted_nums) for q in queries]


# =============================================================================
# WAY 6: Use median trick for sorted nums
# =============================================================================
def min_operations_6(nums, queries):
    """
    For sorted nums, the optimal q is the median.
    But this problem asks for given queries, so we just compute |num - q|.
    """
    sorted_nums = sorted(nums)
    import bisect
    n = len(sorted_nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + sorted_nums[i]

    result = []
    for q in queries:
        idx = bisect.bisect_right(sorted_nums, q)
        left_ops = q * idx - prefix[idx]
        right_ops = (prefix[n] - prefix[idx]) - q * (n - idx)
        result.append(left_ops + right_ops)
    return result


# =============================================================================
# WAY 7: Using numpy
# =============================================================================
def min_operations_7(nums, queries):
    """Vectorized with numpy."""
    try:
        import numpy as np
        arr = np.array(nums)
        result = []
        for q in queries:
            total = int(np.sum(np.abs(arr - q)))
            result.append(total)
        return result
    except ImportError:
        return min_operations_1(nums, queries)


# =============================================================================
# WAY 8: With manual binary search (left count)
# =============================================================================
def min_operations_8(nums, queries):
    """Manual binary search for the split point."""

    def count_le(arr, target):
        """Count number of elements <= target."""
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] <= target:
                lo = mid + 1
            else:
                hi = mid
        return lo

    n = len(nums)
    nums.sort()
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    result = []
    for q in queries:
        idx = count_le(nums, q)
        left_ops = q * idx - prefix[idx]
        right_ops = (prefix[n] - prefix[idx]) - q * (n - idx)
        result.append(left_ops + right_ops)
    return result


# =============================================================================
# WAY 9: Class-based
# =============================================================================
class MinOperationsCalculator:
    def __init__(self, nums, queries):
        self.nums = sorted(nums)
        self.queries = queries
        n = len(self.nums)
        self.prefix = [0] * (n + 1)
        for i in range(n):
            self.prefix[i + 1] = self.prefix[i] + self.nums[i]
        self.n = n

    def solve_query(self, q):
        import bisect
        idx = bisect.bisect_right(self.nums, q)
        left_ops = q * idx - self.prefix[idx]
        right_ops = (self.prefix[self.n] - self.prefix[idx]) - q * (self.n - idx)
        return left_ops + right_ops

    def solve_all(self):
        return [self.solve_query(q) for q in self.queries]


def min_operations_9(nums, queries):
    """Class-based."""
    return MinOperationsCalculator(nums, queries).solve_all()


# =============================================================================
# WAY 10: itertools + map
# =============================================================================
def min_operations_10(nums, queries):
    """Use map with brute force."""
    return list(map(lambda q: sum(abs(num - q) for num in nums), queries))


# =============================================================================
# WAY 11: Generator with sum
# =============================================================================
def min_operations_11(nums, queries):
    """Use generators."""
    sorted_nums = sorted(nums)
    n = len(sorted_nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + sorted_nums[i]

    import bisect

    def ops_for(q):
        idx = bisect.bisect_right(sorted_nums, q)
        return q * idx - prefix[idx] + (prefix[n] - prefix[idx]) - q * (n - idx)

    return [ops_for(q) for q in queries]


# =============================================================================
# WAY 12: One-pass prefix sum then list comp
# =============================================================================
def min_operations_12(nums, queries):
    """Build prefix then list comprehension for queries."""
    nums.sort()
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    import bisect
    total = prefix[n]
    return [
        q * (idx := bisect.bisect_right(nums, q)) - prefix[idx] +
        (total - prefix[idx]) - q * (n - idx)
        for q in queries
    ]


# =============================================================================
# WAY 13: Using functools.reduce for prefix sum
# =============================================================================
def min_operations_13(nums, queries):
    """Build prefix using reduce."""
    from functools import reduce
    from itertools import accumulate

    sorted_nums = sorted(nums)
    n = len(sorted_nums)
    prefix = [0] + list(accumulate(sorted_nums))

    import bisect
    result = []
    for q in queries:
        idx = bisect.bisect_right(sorted_nums, q)
        left_ops = q * idx - prefix[idx]
        right_ops = (prefix[n] - prefix[idx]) - q * (n - idx)
        result.append(left_ops + right_ops)
    return result


# =============================================================================
# WAY 14: With enumerate
# =============================================================================
def min_operations_14(nums, queries):
    """Enumerate-based prefix sum build."""
    sorted_nums = sorted(nums)
    n = len(sorted_nums)
    prefix = [0] * (n + 1)
    for i, num in enumerate(sorted_nums):
        prefix[i + 1] = prefix[i] + num

    import bisect
    result = []
    for q in queries:
        idx = bisect.bisect_right(sorted_nums, q)
        left_ops = q * idx - prefix[idx]
        right_ops = (prefix[n] - prefix[idx]) - q * (n - idx)
        result.append(left_ops + right_ops)
    return result


# =============================================================================
# WAY 15: Two-pointer approach for batch queries
# =============================================================================
def min_operations_15(nums, queries):
    """
    For sorted queries and sorted nums, two pointers can work.
    But bisect is simpler for this problem.
    """
    sorted_nums = sorted(nums)
    n = len(sorted_nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + sorted_nums[i]

    import bisect
    return [
        q * (idx := bisect.bisect_right(sorted_nums, q)) - prefix[idx] +
        (prefix[n] - prefix[idx]) - q * (n - idx)
        for q in queries
    ]


# =============================================================================
# WAY 16: Most concise
# =============================================================================
def min_operations_16(nums, queries):
    """Most concise version."""
    a = sorted(nums)
    n = len(a)
    p = [0]
    for x in a:
        p.append(p[-1] + x)
    import bisect
    return [
        q * (i := bisect.bisect_right(a, q)) - p[i] +
        (p[n] - p[i]) - q * (n - i)
        for q in queries
    ]


# =============================================================================
# WAY 17: Without building prefix (use bisect + sum)
# =============================================================================
def min_operations_17(nums, queries):
    """Use bisect + sum() instead of prefix sums."""
    sorted_nums = sorted(nums)
    import bisect
    result = []
    for q in queries:
        idx = bisect.bisect_right(sorted_nums, q)
        # Slow but clear
        left_ops = sum(q - x for x in sorted_nums[:idx])
        right_ops = sum(x - q for x in sorted_nums[idx:])
        result.append(left_ops + right_ops)
    return result


# =============================================================================
# WAY 18: Memoize operations
# =============================================================================
def min_operations_18(nums, queries):
    """Memoize per-query results."""
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def ops_for(q):
        sorted_nums = sorted(nums)
        n = len(sorted_nums)
        prefix = [0] * (n + 1)
        for i in range(n):
            prefix[i + 1] = prefix[i] + sorted_nums[i]
        import bisect
        idx = bisect.bisect_right(sorted_nums, q)
        left_ops = q * idx - prefix[idx]
        right_ops = (prefix[n] - prefix[idx]) - q * (n - idx)
        return left_ops + right_ops

    return [ops_for(q) for q in queries]


# =============================================================================
# WAY 19: Precompute prefix once, use throughout
# =============================================================================
def min_operations_19(nums, queries):
    """Cleanest split into helper functions."""

    def build_prefix(arr):
        prefix = [0] * (len(arr) + 1)
        for i, x in enumerate(arr):
            prefix[i + 1] = prefix[i] + x
        return prefix

    def ops_for(q, arr, prefix):
        import bisect
        n = len(arr)
        idx = bisect.bisect_right(arr, q)
        left_ops = q * idx - prefix[idx]
        right_ops = (prefix[n] - prefix[idx]) - q * (n - idx)
        return left_ops + right_ops

    arr = sorted(nums)
    prefix = build_prefix(arr)
    return [ops_for(q, arr, prefix) for q in queries]


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def min_operations_20(nums, queries):
    """
    Final clean version.

    Algorithm:
    1. Sort nums.
    2. Build prefix sum array: prefix[i] = sum(nums[0..i-1]).
    3. For each query q:
       a. Find idx = bisect_right(nums, q) = number of elements ≤ q.
       b. Left ops = sum(q - nums[i]) for i < idx = q*idx - prefix[idx].
       c. Right ops = sum(nums[i] - q) for i >= idx = (prefix[n] - prefix[idx]) - q*(n-idx).
       d. Return left_ops + right_ops.

    Why this works:
    For sorted nums, elements ≤ q are at indices [0, idx). For each, the
    distance to q is q - nums[i]. Sum = q * count - sum_of_elements = q*idx - prefix[idx].
    Similarly for elements > q.

    Time:  O((n + m) log n).
    Space: O(n) for prefix sums.

    Edge cases:
    - q smaller than all elements: idx=0, all in right, ops = total_sum - q*n.
    - q larger than all elements: idx=n, all in left, ops = q*n - total_sum.
    """
    n = len(nums)
    nums.sort()
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    import bisect
    total = prefix[n]
    result = []
    for q in queries:
        idx = bisect.bisect_right(nums, q)
        left_ops = q * idx - prefix[idx]
        right_ops = (total - prefix[idx]) - q * (n - idx)
        result.append(left_ops + right_ops)
    return result


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to compute, for each query q, the minimum operations to make all
elements of nums equal to q. Each operation changes one element by ±1."

Key Insight:
"For each q, total operations = sum of |nums[i] - q|. After sorting nums and
building prefix sums, I can compute this in O(log n) per query:
- Find idx = count of elements ≤ q (via bisect_right).
- Left elements (≤ q): q * idx - prefix[idx].
- Right elements (> q): (prefix[n] - prefix[idx]) - q * (n - idx)."

Algorithm:
"1. Sort nums.
2. Build prefix sums.
3. For each query:
   a. Find split point via binary search.
   b. Compute left and right operations.
   c. Append sum.
4. Return results."

Why this works:
"For sorted nums, the first idx elements are ≤ q, the rest are > q.
Sum of (q - left) = q*count - sum = q*idx - prefix[idx].
Sum of (right - q) = sum - q*count = (prefix[n] - prefix[idx]) - q*(n-idx)."

Edge cases:
- All nums equal: ops = |nums[0] - q| * n for each query.
- Single element: ops = |nums[0] - q| for each query.
- Empty nums or queries: handle separately.
- q smaller than min nums: all in right, ops = sum - q*n.
- q larger than max nums: all in left, ops = q*n - sum.

Complexity:
- Time:  O(n log n + m log n) = O((n+m) log n).
- Space: O(n) for prefix sums.

KEY TRICK:
Sort + prefix sums + binary search. Each query is O(log n).

ALTERNATIVE: Brute force O(n*m)
For each query, sum |nums[i] - q|. O(n*m) total. Too slow for large m.

ALTERNATIVE: numpy
Vectorized: np.sum(np.abs(arr - q)) for each query. Same complexity,
faster in practice for large n.

RELATIONSHIP TO OTHER PROBLEMS:
- Minimum Moves to Equal Array (LC 462): Sum |nums[i] - median|.
- Make Array Strictly Increasing (LC 1827): Different.
- Sum of Absolute Differences (LC 1685): Different - pairwise sums.

INTERVIEW TIPS:
1. Recognize this as sum of |nums[i] - q|.
2. Use prefix sums for O(log n) per query.
3. Binary search for the split point.
4. Mention brute force as a fallback.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort + prefix + bisect (BEST)", min_operations_1),
        ("Way 2: Verbose", min_operations_2),
        ("Way 3: Brute force", min_operations_3),
        ("Way 4: Brute force loops", min_operations_4),
        ("Way 5: Pre-sort + brute force", min_operations_5),
        ("Way 6: With median note", min_operations_6),
        ("Way 7: numpy", min_operations_7),
        ("Way 8: Manual binary search", min_operations_8),
        ("Way 9: Class-based", min_operations_9),
        ("Way 10: map + brute", min_operations_10),
        ("Way 11: Generator", min_operations_11),
        ("Way 12: One-pass prefix", min_operations_12),
        ("Way 13: accumulate", min_operations_13),
        ("Way 14: enumerate", min_operations_14),
        ("Way 15: Two-pointer concept", min_operations_15),
        ("Way 16: Most concise", min_operations_16),
        ("Way 17: bisect + sum (slow)", min_operations_17),
        ("Way 18: Memoize", min_operations_18),
        ("Way 19: Helper functions", min_operations_19),
        ("Way 20: Final cleanest", min_operations_20),
    ]

    test_cases = [
        # Educative example
        # nums=[3,1,6], queries=[4]
        # |3-4| + |1-4| + |6-4| = 1 + 3 + 2 = 6
        ([3, 1, 6], [4], [6]),

        # Two queries
        # nums=[2,9,6], queries=[5,4]
        # For q=5: |2-5|+|9-5|+|6-5| = 3+4+1 = 8
        # For q=4: |2-4|+|9-4|+|6-4| = 2+5+2 = 9
        ([2, 9, 6], [5, 4], [8, 9]),

        # Single query, single element
        ([5], [3], [2]),
        ([5], [5], [0]),
        ([5], [10], [5]),

        # Single query, all same elements
        # nums=[3,3,3], queries=[5]
        # 3 * |3-5| = 3 * 2 = 6
        ([3, 3, 3], [5], [6]),

        # Multiple queries
        # nums=[1,2,3], queries=[1,2,3,4,5]
        # q=1: 0+1+2=3
        # q=2: 1+0+1=2
        # q=3: 2+1+0=3
        # q=4: 3+2+1=6
        # q=5: 4+3+2=9
        ([1, 2, 3], [1, 2, 3, 4, 5], [3, 2, 3, 6, 9]),

        # Empty queries
        ([1, 2, 3], [], []),

        # Negative values (problem says positive, but defensive)
        ([1, 2, 3], [0], [6]),  # |1-0|+|2-0|+|3-0| = 1+2+3 = 6

        # Query smaller than min
        ([5, 10, 15], [1], [5 + 10 + 15 - 3*1]),  # 30 - 3 = 27
        # Actually: |5-1|+|10-1|+|15-1| = 4+9+14 = 27 ✓

        # Query larger than max
        ([5, 10, 15], [20], [3*20 - 30]),  # 60 - 30 = 30
        # Actually: |5-20|+|10-20|+|15-20| = 15+10+5 = 30 ✓

        # Larger example
        # nums=[1,4,7,10], queries=[3,5,8]
        # q=3: |1-3|+|4-3|+|7-3|+|10-3| = 2+1+4+7 = 14
        # q=5: |1-5|+|4-5|+|7-5|+|10-5| = 4+1+2+5 = 12
        # q=8: |1-8|+|4-8|+|7-8|+|10-8| = 7+4+1+2 = 14
        ([1, 4, 7, 10], [3, 5, 8], [14, 12, 14]),

        # Many queries, sorted nums
        # nums=[1,1,1,1], queries=[0,1,2,3]
        # All ops = 4 * |1 - q|
        ([1, 1, 1, 1], [0, 1, 2, 3], [4, 0, 4, 8]),
    ]

    print("=" * 70)
    print("MIN OPERATIONS TO MAKE ARRAY EQUAL - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-operations-to-make-all-array-elements-equal")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, queries, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(nums), copy.deepcopy(queries))
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, queries={queries} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on nums={nums}, queries={queries} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)