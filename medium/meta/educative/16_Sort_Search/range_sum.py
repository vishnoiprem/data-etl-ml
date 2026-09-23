"""
Range Sum of Sorted Subarray Sums
Medium | 30 min

Given an integer array nums of positive integers and two integers left and right.
Calculate the sum of every non-empty continuous subarray of nums.
Collect these sums into an array, sort in nondecreasing order.
Return the sum of elements from index left to right (1-indexed, inclusive) mod 10^9+7.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/range-sum-of-sorted-subarray-sums

Constraints:
- 1 <= n <= 1000
- 1 <= nums[i] <= 100
- 1 <= left <= right <= n*(n+1)/2

Examples:
    nums=[1,2,3,4], n=4, left=1, right=5 -> 13
    (Subarray sums: [1,2,3,3,4,5,6,7,9,10]. Sorted. Sum of [0..4] = 1+2+3+3+4 = 13.)

    nums=[1,2,3,4], n=4, left=3, right=4 -> 6
    (Sum of [2..3] in sorted array = 3+3 = 6.)

Key Insight:
For each starting index i, extend the subarray to j=i..n-1.
Use a running sum to compute each subarray sum in O(1).
Collect all n*(n+1)/2 sums, sort, return sum[left-1:right] mod 10^9+7.

Time:  O(n^2 log n) for n subarrays.
Space: O(n^2) for the sums array.
"""


# =============================================================================
# WAY 1: Brute force collect all sums + sort + range (BEST - simple)
# =============================================================================
def range_sum_1(nums, n, left, right):
    """
    For each starting index, extend the subarray and collect sums.
    Sort and return sum from left-1 to right-1.
    """
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums.append(s)
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def range_sum_2(nums, n, left, right):
    """Verbose version with comments."""
    MOD = 10**9 + 7
    sums = []
    for start in range(n):
        current_sum = 0
        for end in range(start, n):
            current_sum += nums[end]
            sums.append(current_sum)
    sums.sort()
    # left and right are 1-indexed
    result = 0
    for i in range(left - 1, right):
        result += sums[i]
    return result % MOD


# =============================================================================
# WAY 3: Use prefix sums
# =============================================================================
def range_sum_3(nums, n, left, right):
    """Use prefix sums for O(1) range sum."""
    MOD = 10**9 + 7
    # Build prefix sum
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    sums = []
    for i in range(n):
        for j in range(i + 1, n + 1):
            sums.append(prefix[j] - prefix[i])
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 4: Nested list comprehension
# =============================================================================
def range_sum_4(nums, n, left, right):
    """List comprehension to collect sums."""
    MOD = 10**9 + 7
    sums = [
        sum(nums[i:j + 1])
        for i in range(n)
        for j in range(i, n)
    ]
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 5: With running sum
# =============================================================================
def range_sum_5(nums, n, left, right):
    """Running sum technique for O(1) per subarray."""
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums.append(s)
    sums.sort()
    # Use slicing and sum
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class RangeSumCalculator:
    MOD = 10**9 + 7

    def __init__(self, nums, n, left, right):
        self.nums = nums
        self.n = n
        self.left = left
        self.right = right

    def compute(self):
        sums = []
        for i in range(self.n):
            s = 0
            for j in range(i, self.n):
                s += self.nums[j]
                sums.append(s)
        sums.sort()
        return sum(sums[self.left - 1:self.right]) % self.MOD


def range_sum_6(nums, n, left, right):
    """Class-based."""
    return RangeSumCalculator(nums, n, left, right).compute()


# =============================================================================
# WAY 7: itertools.accumulate
# =============================================================================
def range_sum_7(nums, n, left, right):
    """Use itertools.accumulate for running sum."""
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        for s in __import__('itertools').accumulate(nums[i:]):
            sums.append(s)
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 8: Numpy-based
# =============================================================================
def range_sum_8(nums, n, left, right):
    """Vectorized with numpy."""
    MOD = 10**9 + 7
    try:
        import numpy as np
        arr = np.array(nums)
        # Compute prefix sums
        prefix = np.concatenate([[0], np.cumsum(arr)])
        # Generate all subarray sums
        sums = []
        for i in range(n):
            sums.extend((prefix[i + 1:n + 1] - prefix[i]).tolist())
        sums.sort()
        return sum(sums[left - 1:right]) % MOD
    except ImportError:
        return range_sum_1(nums, n, left, right)


# =============================================================================
# WAY 9: Generator-based
# =============================================================================
def range_sum_9(nums, n, left, right):
    """Use generators."""
    MOD = 10**9 + 7
    # Generate all subarray sums
    sums = []
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums.append(s)
    sums.sort()
    # Sum the slice
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 10: enumerate
# =============================================================================
def range_sum_10(nums, n, left, right):
    """Use enumerate."""
    MOD = 10**9 + 7
    sums = []
    for i, num_i in enumerate(nums):
        s = 0
        for num_j in nums[i:]:
            s += num_j
            sums.append(s)
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 11: Helper function approach
# =============================================================================
def range_sum_11(nums, n, left, right):
    """Extract helper functions."""

    def all_subarray_sums(arr):
        n_local = len(arr)
        result = []
        for i in range(n_local):
            s = 0
            for j in range(i, n_local):
                s += arr[j]
                result.append(s)
        return result

    MOD = 10**9 + 7
    sums = all_subarray_sums(nums)
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 12: Functional with map
# =============================================================================
def range_sum_12(nums, n, left, right):
    """Use map for collecting sums."""
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        # Use reduce to compute running sum
        from functools import reduce
        for s in reduce(lambda acc, x: acc + [acc[-1] + x] if acc else [x], nums[i:], []):
            sums.append(s)
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 13: With prefix array built once
# =============================================================================
def range_sum_13(nums, n, left, right):
    """Build prefix array once, use for all subarray sums."""
    MOD = 10**9 + 7
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    sums = []
    for i in range(n):
        for j in range(i + 1, n + 1):
            sums.append(prefix[j] - prefix[i])
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 14: Slice-based (most pythonic)
# =============================================================================
def range_sum_14(nums, n, left, right):
    """Most pythonic version."""
    MOD = 10**9 + 7
    sums = sorted(
        sum(nums[i:j + 1])
        for i in range(n)
        for j in range(i, n)
    )
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 15: Pre-allocate array of known size
# =============================================================================
def range_sum_15(nums, n, left, right):
    """Pre-allocate to avoid dynamic append."""
    MOD = 10**9 + 7
    total = n * (n + 1) // 2
    sums = [0] * total
    idx = 0
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums[idx] = s
            idx += 1
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 16: Most concise
# =============================================================================
def range_sum_16(nums, n, left, right):
    """Most concise."""
    MOD = 10**9 + 7
    sums = sorted(
        s
        for i in range(n)
        for s in [sum(nums[i:j + 1]) for j in range(i, n)]
    )
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 17: With heap (alternative approach for partial sort)
# =============================================================================
def range_sum_17(nums, n, left, right):
    """
    Alternative: for very large n where full sort is too slow,
    we could use partial sort (heapq.nsmallest) to get only the
    (left..right)-th elements. But for n <= 1000, full sort is fine.
    """
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums.append(s)
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 18: Use bisect for efficiency if we sort queries
# =============================================================================
def range_sum_18(nums, n, left, right):
    """Sort then use bisect."""
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums.append(s)
    sums.sort()
    # Sum from left-1 to right-1 (inclusive)
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# WAY 19: Explicit range loop
# =============================================================================
def range_sum_19(nums, n, left, right):
    """Explicit range loop for summing."""
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums.append(s)
    sums.sort()
    total = 0
    for i in range(left - 1, right):
        total += sums[i]
    return total % MOD


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def range_sum_20(nums, n, left, right):
    """
    Final clean version.

    Algorithm:
    1. Collect all n*(n+1)/2 subarray sums.
    2. Sort them.
    3. Return sum of sums[left-1:right] mod 10^9+7.

    Why this works:
    - We need the sum of the k-th to (k+1)-th smallest subarray sums.
    - Sort all subarray sums, then take the range.

    Time:  O(n^2 log n).
    Space: O(n^2) for the sums array.

    Edge cases:
    - left == right: single element.
    - left = 1, right = n*(n+1)/2: sum of all.
    - Single element array: only one subarray.
    """
    MOD = 10**9 + 7
    sums = []
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += nums[j]
            sums.append(s)
    sums.sort()
    return sum(sums[left - 1:right]) % MOD


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to compute the sum of the k-th to m-th smallest subarray sums,
where k=left and m=right (1-indexed), modulo 10^9+7."

Key Insight:
"Collect all n*(n+1)/2 subarray sums. Sort them. Sum the slice from
left-1 to right-1 (converting to 0-indexed). Take mod."

Algorithm:
"1. For each starting index i, extend to j=i..n-1, compute running sum.
2. Collect all sums in a list.
3. Sort the list.
4. Return sum of sums[left-1:right] % 10^9+7."

Why this works:
"After sorting, the (left-1)-th through (right-1)-th elements (0-indexed)
are exactly the sums we need."

Edge cases:
- left == right: single element.
- left=1, right=n*(n+1)/2: sum of all subarray sums.
- Single element array: only one subarray, return sum[0].
- left=0 or right=0: invalid per constraints.

Complexity:
- Time:  O(n^2 log n) — n^2 subarrays, sorting dominates.
- Space: O(n^2) for the sums list.

KEY TRICK:
Use running sum to compute each subarray sum in O(1) instead of recomputing.
Sort all sums, slice, sum, mod.

ALTERNATIVE: Prefix sums
Build prefix array. Subarray sum [i..j] = prefix[j+1] - prefix[i]. O(1) per
subarray, but the sorting dominates anyway.

ALTERNATIVE: Heap-based partial sort
For huge n, use heapq.nsmallest(right, ...) + heapq.nlargest to find the
needed range without full sort. But for n <= 1000, full sort is fast.

ALTERNATIVE: numpy
Vectorized computation of all subarray sums.

RELATIONSHIP TO OTHER PROBLEMS:
- Sum of Subarray Minimums (LC 907): Different formula (count contributions).
- Range Sum Query 2D (LC 304): 2D prefix sums.
- Subarray Sum Equals K (LC 560): Different - hashmap prefix.

INTERVIEW TIPS:
1. Mention the running sum trick for O(1) per subarray.
2. Convert 1-indexed to 0-indexed carefully.
3. Apply mod only at the end.
4. Discuss space complexity (O(n^2) is large).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Brute force collect (BEST)", range_sum_1),
        ("Way 2: Verbose", range_sum_2),
        ("Way 3: Prefix sums", range_sum_3),
        ("Way 4: List comprehension", range_sum_4),
        ("Way 5: With running sum", range_sum_5),
        ("Way 6: Class-based", range_sum_6),
        ("Way 7: itertools.accumulate", range_sum_7),
        ("Way 8: numpy", range_sum_8),
        ("Way 9: Generator", range_sum_9),
        ("Way 10: enumerate", range_sum_10),
        ("Way 11: Helper function", range_sum_11),
        ("Way 12: Functional", range_sum_12),
        ("Way 13: Prefix built once", range_sum_13),
        ("Way 14: Most pythonic", range_sum_14),
        ("Way 15: Pre-allocate", range_sum_15),
        ("Way 16: Most concise", range_sum_16),
        ("Way 17: Heap note", range_sum_17),
        ("Way 18: bisect note", range_sum_18),
        ("Way 19: Explicit range", range_sum_19),
        ("Way 20: Final cleanest", range_sum_20),
    ]

    test_cases = [
        # Example 1: nums=[1,2,3,4], n=4, left=1, right=5
        # Subarray sums: [1,2,3,3,4,5,6,7,9,10]
        # Sorted: [1,2,3,3,4,5,6,7,9,10]
        # Sum of indices 0-4 (1-indexed 1-5): 1+2+3+3+4 = 13
        ([1, 2, 3, 4], 4, 1, 5, 13),

        # Example 2: nums=[1,2,3,4], n=4, left=3, right=4
        # Sorted: [1,2,3,3,4,5,6,7,9,10]
        # Sum of indices 2-3 (1-indexed 3-4): 3+3 = 6
        ([1, 2, 3, 4], 4, 3, 4, 6),

        # Single element
        # Subarray sums: [5]
        # left=1, right=1 -> 5
        ([5], 1, 1, 1, 5),

        # All elements, single query
        # nums=[1,2], n=2, left=1, right=3
        # Subarray sums: [1,2,3]. Sorted: [1,2,3]. Sum = 6.
        ([1, 2], 2, 1, 3, 6),

        # Single subarray
        # nums=[1,2,3], n=3, left=2, right=2
        # Subarray sums: [1,2,3,3,5,6]. Sorted: [1,2,3,3,5,6].
        # Index 1 (0-indexed) = 2. Sum = 2.
        ([1, 2, 3], 3, 2, 2, 2),

        # Edge: left=right (single element from sorted array)
        # nums=[5,1,2], n=3
        # Subarray sums: [5,1,2,6,3,8]. Sorted: [1,2,3,5,6,8].
        # left=right=4 -> sums[3] = 5.
        ([5, 1, 2], 3, 4, 4, 5),

        # Larger example
        # nums=[1,2,3,4,5], n=5
        # 15 subarrays total
        # left=1, right=15 -> sum of all
        # subarray sums: 1,3,6,10,15, 2,5,9,14, 3,7,12, 4,9, 5
        # Sorted: 1,2,3,3,4,5,5,6,7,9,9,10,12,14,15
        # Sum = 1+2+3+3+4+5+5+6+7+9+9+10+12+14+15 = 105
        ([1, 2, 3, 4, 5], 5, 1, 15, 105),

        # Larger example: take middle range
        # Same nums=[1,2,3,4,5], take indices 4-10 (1-indexed)
        # Sorted: 1,2,3,3,4,5,5,6,7,9,9,10,12,14,15
        # Indices 3-9 (0-indexed): 3,4,5,5,6,7,9 = 39
        ([1, 2, 3, 4, 5], 5, 4, 10, 39),

        # All same nums
        # nums=[2,2,2], n=3
        # Subarray sums: 2,2,2, 4,4, 6. Sorted: 2,2,2,4,4,6.
        # left=1, right=6 -> sum = 20
        ([2, 2, 2], 3, 1, 6, 20),
    ]

    print("=" * 70)
    print("RANGE SUM OF SORTED SUBARRAY SUMS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/range-sum-of-sorted-subarray-sums")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, n, left, right, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(nums), n, left, right)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, left={left}, right={right} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on nums={nums}, left={left}, right={right} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)