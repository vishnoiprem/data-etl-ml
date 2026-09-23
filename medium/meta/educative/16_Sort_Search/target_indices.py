"""
Find Target Indices After Sorting Array
Easy | 15 min

You are given a 0-indexed array nums of positive integers and a value target.

Return a list of indices where nums[i] == target AFTER sorting the array
in nondecreasing order. If no such indices exist, return [].

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/find-target-indices-after-sorting-array

Constraints:
- 1 <= nums.length <= 100
- 1 <= nums[i], target <= 100

Examples:
    nums=[1,2,5,2,3], target=2 -> [1, 2]
    (Sorted: [1,2,2,3,5]. Indices of 2 are 1, 2.)
    nums=[1,2,5,2,3], target=5 -> [4]
    nums=[1,2,5,2,3], target=4 -> []

Key Insight:
After sorting, all occurrences of target are contiguous.
Use binary search to find the leftmost and rightmost positions.
Indices are [left, left+1, ..., right].

Alternative: Sort and linear scan, collecting matching indices.

Time:  O(n log n) for sort, O(log n) for binary search.
Space: O(n) for output (or O(log n) extra for sort).
"""


# =============================================================================
# WAY 1: Sort + linear scan (BEST - simple, easy to remember)
# =============================================================================
def target_indices_1(nums, target):
    """
    Sort, then iterate and collect indices where value == target.
    """
    nums.sort()
    return [i for i, num in enumerate(nums) if num == target]


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def target_indices_2(nums, target):
    """Verbose version with comments."""
    sorted_nums = sorted(nums)
    result = []
    for i, num in enumerate(sorted_nums):
        if num == target:
            result.append(i)
    return result


# =============================================================================
# WAY 3: Sort + binary search for range
# =============================================================================
def target_indices_3(nums, target):
    """
    Use bisect to find leftmost and rightmost positions.
    """
    nums.sort()
    import bisect
    left = bisect.bisect_left(nums, target)
    right = bisect.bisect_right(nums, target) - 1
    if left > right:
        return []
    return list(range(left, right + 1))


# =============================================================================
# WAY 4: Using bisect only
# =============================================================================
def target_indices_4(nums, target):
    """Same as Way 3 but more concise."""
    nums.sort()
    import bisect
    left = bisect.bisect_left(nums, target)
    right = bisect.bisect_right(nums, target)
    if left == right:
        return []
    return list(range(left, right))


# =============================================================================
# WAY 5: Brute force with sort (alternative implementation)
# =============================================================================
def target_indices_5(nums, target):
    """Sort, then linear scan."""
    nums.sort()
    return [i for i, num in enumerate(nums) if num == target]


# =============================================================================
# WAY 6: Counter-based
# =============================================================================
def target_indices_6(nums, target):
    """
    Count occurrences, sort, then build range.
    """
    from collections import Counter
    counts = Counter(nums)
    if target not in counts:
        return []
    # Find where target starts in sorted array
    cumsum = 0
    sorted_nums = sorted(set(nums))
    for val in sorted_nums:
        if val == target:
            start = cumsum
            break
        cumsum += counts[val]
    return list(range(start, start + counts[target]))


# =============================================================================
# WAY 7: Manual binary search
# =============================================================================
def target_indices_7(nums, target):
    """Manual binary search for left and right bounds."""

    def lower_bound(arr, x):
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def upper_bound(arr, x):
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] <= x:
                lo = mid + 1
            else:
                hi = mid
        return lo

    nums.sort()
    left = lower_bound(nums, target)
    right = upper_bound(nums, target) - 1
    if left > right:
        return []
    return list(range(left, right + 1))


# =============================================================================
# WAY 8: Sort and find range manually
# =============================================================================
def target_indices_8(nums, target):
    """Sort, scan to find first occurrence, then count consecutive."""
    nums.sort()
    n = len(nums)
    # Find first occurrence
    first = -1
    for i in range(n):
        if nums[i] == target:
            first = i
            break
    if first == -1:
        return []
    # Count consecutive
    last = first
    while last + 1 < n and nums[last + 1] == target:
        last += 1
    return list(range(first, last + 1))


# =============================================================================
# WAY 9: With enumerate after sort
# =============================================================================
def target_indices_9(nums, target):
    """Use enumerate for the iteration."""
    nums.sort()
    return [i for i, num in enumerate(nums) if num == target]


# =============================================================================
# WAY 10: Class-based
# =============================================================================
class TargetIndicesFinder:
    def __init__(self, nums, target):
        self.nums = nums
        self.target = target

    def find(self):
        sorted_nums = sorted(self.nums)
        return [i for i, num in enumerate(sorted_nums) if num == self.target]


def target_indices_10(nums, target):
    """Class-based."""
    return TargetIndicesFinder(nums, target).find()


# =============================================================================
# WAY 11: With while loop
# =============================================================================
def target_indices_11(nums, target):
    """Sort, then iterate with explicit while loop."""
    nums.sort()
    result = []
    i = 0
    while i < len(nums):
        if nums[i] == target:
            result.append(i)
        i += 1
    return result


# =============================================================================
# WAY 12: Generator-based
# =============================================================================
def target_indices_12(nums, target):
    """Use a generator expression."""
    nums.sort()
    return list(i for i, num in enumerate(nums) if num == target)


# =============================================================================
# WAY 13: Using itertools
# =============================================================================
def target_indices_13(nums, target):
    """Use compress for filtering."""
    nums.sort()
    from itertools import compress
    # Create a boolean mask
    mask = [num == target for num in nums]
    # Return indices where mask is True
    return [i for i, keep in enumerate(mask) if keep]


# =============================================================================
# WAY 14: Numpy-based
# =============================================================================
def target_indices_14(nums, target):
    """Vectorized with numpy."""
    try:
        import numpy as np
        arr = np.array(nums)
        sorted_arr = np.sort(arr)
        indices = np.where(sorted_arr == target)[0]
        return indices.tolist()
    except ImportError:
        return target_indices_1(nums, target)


# =============================================================================
# WAY 15: Functional with filter
# =============================================================================
def target_indices_15(nums, target):
    """Use filter and enumerate."""
    nums.sort()
    return [
        i for i, num in
        filter(lambda x: x[1] == target, enumerate(nums))
    ]


# =============================================================================
# WAY 16: One-liner
# =============================================================================
def target_indices_16(nums, target):
    """One-liner."""
    nums.sort()
    return [i for i, n in enumerate(nums) if n == target]


# =============================================================================
# WAY 17: Sort with key (no benefit here, just for variety)
# =============================================================================
def target_indices_17(nums, target):
    """Sort with explicit key."""
    nums.sort(key=lambda x: x)
    return [i for i, num in enumerate(nums) if num == target]


# =============================================================================
# WAY 18: Using sorted() (returns new list)
# =============================================================================
def target_indices_18(nums, target):
    """Use sorted() instead of .sort()."""
    return [i for i, num in enumerate(sorted(nums)) if num == target]


# =============================================================================
# WAY 19: Most efficient (binary search approach)
# =============================================================================
def target_indices_19(nums, target):
    """
    Sort, then binary search for first occurrence, then linear scan.
    """
    nums.sort()
    import bisect
    left = bisect.bisect_left(nums, target)
    if left == len(nums) or nums[left] != target:
        return []
    # All target values are at positions left, left+1, ..., left+count-1
    right = bisect.bisect_right(nums, target)
    return list(range(left, right))


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def target_indices_20(nums, target):
    """
    Final clean version.

    Algorithm:
    1. Sort nums.
    2. Iterate and collect indices where value == target.

    Why this works:
    After sorting, all occurrences of target are contiguous. A simple
    linear scan after sorting is O(n). For even better O(log n), use
    binary search for the boundaries.

    Why sort + scan is the cleanest:
    - O(n log n) sort + O(n) scan.
    - Code is 1 line after sort.

    Time:  O(n log n).
    Space: O(1) extra.
    """
    nums.sort()
    return [i for i, num in enumerate(nums) if num == target]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find all indices in the SORTED array where the value equals target."

Key Insight:
"After sorting, all occurrences of target are contiguous (since the array
is sorted). So I can either:
1. Sort + linear scan, collecting matching indices.
2. Sort + binary search to find left and right bounds, then return range."

Algorithm (linear scan):
"1. Sort nums.
2. Iterate and collect indices where value == target."

Algorithm (binary search):
"1. Sort nums.
2. Find left = bisect_left(nums, target).
3. Find right = bisect_right(nums, target).
4. If left == right: no occurrences, return [].
5. Return list(range(left, right))."

Why this works:
"After sorting, equal elements are contiguous. Linear scan finds them all.
Binary search finds the boundaries faster."

Edge cases:
- No target in array: return [].
- All elements are target: return [0, 1, ..., n-1].
- Single element equal to target: return [0].
- Empty array: return [] (constraint says n >= 1, but defensive).

Complexity:
- Time:  O(n log n) for sort, O(n) for scan.
- Space: O(1) extra.

KEY TRICK:
Sort, then collect indices in a single pass.

ALTERNATIVE: Binary search boundaries
Find first and last occurrence with bisect. Then return range.
O(n log n) total (sort dominates).

ALTERNATIVE: Don't sort
The problem says "after sorting", so we MUST sort. Even if we don't,
we'd just get the original indices (which the problem doesn't want).

RELATIONSHIP TO OTHER PROBLEMS:
- Find First and Last Position (LC 34): Same binary search pattern.
- Search Insert Position (LC 35): Related binary search.
- Sort an Array (LC 912): Just sort.

INTERVIEW TIPS:
1. Mention sort + scan approach.
2. Note binary search as an alternative.
3. Discuss why sort is necessary.
4. Handle empty/missing target.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort + scan (BEST)", target_indices_1),
        ("Way 2: Verbose", target_indices_2),
        ("Way 3: bisect range", target_indices_3),
        ("Way 4: bisect concise", target_indices_4),
        ("Way 5: Brute no sort (wrong)", target_indices_5),
        ("Way 6: Counter", target_indices_6),
        ("Way 7: Manual binary search", target_indices_7),
        ("Way 8: Find range manually", target_indices_8),
        ("Way 9: enumerate", target_indices_9),
        ("Way 10: Class-based", target_indices_10),
        ("Way 11: While loop", target_indices_11),
        ("Way 12: Generator", target_indices_12),
        ("Way 13: itertools", target_indices_13),
        ("Way 14: numpy", target_indices_14),
        ("Way 15: filter+enumerate", target_indices_15),
        ("Way 16: One-liner", target_indices_16),
        ("Way 17: Sort with key", target_indices_17),
        ("Way 18: sorted()", target_indices_18),
        ("Way 19: Binary search + scan", target_indices_19),
        ("Way 20: Final cleanest", target_indices_20),
    ]

    test_cases = [
        # Educative examples
        # nums=[1,2,5,2,3], target=2 -> sorted [1,2,2,3,5] -> [1, 2]
        ([1, 2, 5, 2, 3], 2, [1, 2]),
        # target=5 -> sorted [1,2,2,3,5] -> [4]
        ([1, 2, 5, 2, 3], 5, [4]),
        # target=4 -> not in array -> []
        ([1, 2, 5, 2, 3], 4, []),

        # Single element
        ([5], 5, [0]),
        ([5], 3, []),

        # All same
        ([3, 3, 3, 3], 3, [0, 1, 2, 3]),
        ([3, 3, 3, 3], 5, []),

        # Already sorted
        ([1, 2, 3, 4, 5], 3, [2]),
        ([1, 2, 3, 4, 5], 1, [0]),
        ([1, 2, 3, 4, 5], 5, [4]),

        # Reverse sorted
        ([5, 4, 3, 2, 1], 3, [2]),

        # Multiple occurrences scattered
        ([1, 5, 2, 5, 3, 5], 5, [3, 4, 5]),  # sorted: [1,2,3,5,5,5]

        # Target not in array
        ([1, 2, 3], 4, []),
        ([1, 2, 3], 0, []),

        # Two elements
        ([2, 1], 1, [0]),
        ([2, 1], 2, [1]),
        ([2, 1], 3, []),

        # Larger example
        # nums=[1,2,5,2,3,1,5,2,3], target=2 -> sorted [1,1,2,2,2,3,3,5,5]
        # Indices of 2: 2, 3, 4
        ([1, 2, 5, 2, 3, 1, 5, 2, 3], 2, [2, 3, 4]),

        # All distinct
        ([1, 2, 3, 4], 3, [2]),
    ]

    print("=" * 70)
    print("TARGET INDICES - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/find-target-indices-after-sorting-array")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, target, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(nums), target)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, target={target} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on nums={nums}, target={target} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)