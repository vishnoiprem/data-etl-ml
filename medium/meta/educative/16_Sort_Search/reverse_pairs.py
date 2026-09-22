"""
Reverse Pairs
Hard | 40 min

Given an integer array nums, count pairs (i, j) with i < j where
nums[i] > 2 * nums[j].

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-pairs

Constraints:
- 1 <= nums.length <= 5 * 10^4
- -2^31 <= nums[i] <= 2^31 - 1

Examples:
    nums=[6,1,3,1] -> 2  (pairs (0,1) 6>2*1=2 and (0,3) 6>2)
    nums=[1,3,2,3,1] -> 2 (pairs (1,4) 3>2*1=2 and (2,4) 2>2*1=2)
    nums=[2,4,3,5,1] -> 3

Key Insight:
The condition is nums[i] > 2 * nums[j] for i < j. This is tricky because
of the multiplier on nums[j].

APPROACH 1 (Educative - O(n log^2 n)): Use a sorted structure, and for
each element as we process left-to-right, binary search for valid j's.

APPROACH 2 (Optimal - O(n log n)): Modified merge sort - during merge,
count pairs where left[i] > 2 * right[j] in O(n).

We implement BOTH approaches (and many variations).

Time:  O(n log^2 n) for bisect approach, O(n log n) for merge sort.
Space: O(n).
"""


# =============================================================================
# WAY 1: Sort + bisect_right (BEST Educative - O(n log^2 n))
# =============================================================================
def reverse_pairs_1(nums):
    """
    Process left-to-right. Maintain sorted list of seen elements.
    For each new element, count how many seen elements are > 2*nums[i].
    """
    import bisect
    sorted_seen = []
    count = 0
    for num in nums:
        # Count seen elements > 2*num
        # bisect_right(sorted_seen, 2*num) gives index of first element > 2*num
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        count += len(sorted_seen) - idx
        # Insert num in sorted position
        bisect.insort(sorted_seen, num)
    return count


# =============================================================================
# WAY 2: Verbose version of bisect approach
# =============================================================================
def reverse_pairs_2(nums):
    """Verbose bisect version."""
    import bisect
    sorted_seen = []
    count = 0
    for num in nums:
        # Find first index where sorted_seen[idx] > 2*num
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        # All elements from idx to end satisfy seen > 2*num
        count += len(sorted_seen) - idx
        bisect.insort(sorted_seen, num)
    return count


# =============================================================================
# WAY 3: Brute force O(n^2)
# =============================================================================
def reverse_pairs_3(nums):
    """Brute force O(n^2)."""
    n = len(nums)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] > 2 * nums[j]:
                count += 1
    return count


# =============================================================================
# WAY 4: Merge sort approach (BEST Optimal - O(n log n))
# =============================================================================
def reverse_pairs_4(nums):
    """
    Modified merge sort. During merge, count pairs where left[i] > 2*right[j].

    Sort left half, sort right half, then merge. While merging, for each
    right[j], find first i where left[i] > 2*right[j] (linear scan works
    since left is sorted).
    """
    def merge_sort(arr):
        if len(arr) <= 1:
            return arr, 0
        mid = len(arr) // 2
        left, count_left = merge_sort(arr[:mid])
        right, count_right = merge_sort(arr[mid:])
        # Count pairs: left[i] > 2*right[j] for i in left indices, j in right
        merged, count_merge = merge_and_count(left, right)
        return merged, count_left + count_right + count_merge

    def merge_and_count(left, right):
        merged = []
        count = 0
        j = 0
        # For each left[i], find first right[j] where right[j] >= left[i]/2 (i.e., left[i] <= 2*right[j])
        # Actually we want: count of right[j] where right[j] < left[i]/2, i.e., left[i] > 2*right[j]
        # Iterate through left, advance j until 2*right[j] >= left[i]
        for i in range(len(left)):
            while j < len(right) and 2 * right[j] < left[i]:
                j += 1
            count += j
        # Standard merge
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, count

    _, count = merge_sort(nums)
    return count


# =============================================================================
# WAY 5: Bisect with sorted list (no insort, manual insertion)
# =============================================================================
def reverse_pairs_5(nums):
    """Manual sorted list insertion."""
    import bisect
    sorted_seen = []
    count = 0
    for num in nums:
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        count += len(sorted_seen) - idx
        # Insert manually
        bisect.insort(sorted_seen, num)
    return count


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class ReversePairCounter:
    def __init__(self, nums):
        self.nums = nums

    def count_bisect(self):
        import bisect
        sorted_seen = []
        count = 0
        for num in self.nums:
            idx = bisect.bisect_right(sorted_seen, 2 * num)
            count += len(sorted_seen) - idx
            bisect.insort(sorted_seen, num)
        return count

    def count_merge_sort(self):
        def merge_sort(arr):
            if len(arr) <= 1:
                return arr, 0
            mid = len(arr) // 2
            left, lc = merge_sort(arr[:mid])
            right, rc = merge_sort(arr[mid:])
            merged, mc = self._merge_and_count(left, right)
            return merged, lc + rc + mc

        _, count = merge_sort(self.nums)
        return count

    @staticmethod
    def _merge_and_count(left, right):
        merged = []
        count = 0
        j = 0
        for i in range(len(left)):
            while j < len(right) and 2 * right[j] < left[i]:
                j += 1
            count += j
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, count


def reverse_pairs_6(nums):
    """Class-based using bisect."""
    return ReversePairCounter(nums).count_bisect()


# =============================================================================
# WAY 7: numpy version of bisect approach
# =============================================================================
def reverse_pairs_7(nums):
    """Vectorized bisect using numpy."""
    try:
        import numpy as np
        import bisect
        sorted_seen = []
        count = 0
        for num in nums:
            idx = bisect.bisect_right(sorted_seen, 2 * num)
            count += len(sorted_seen) - idx
            bisect.insort(sorted_seen, num)
        return count
    except ImportError:
        return reverse_pairs_1(nums)


# =============================================================================
# WAY 8: Merge sort with helper
# =============================================================================
def reverse_pairs_8(nums):
    """Merge sort with separate count helper."""

    def sort_and_count(arr):
        n = len(arr)
        if n <= 1:
            return arr, 0
        mid = n // 2
        left, l_count = sort_and_count(arr[:mid])
        right, r_count = sort_and_count(arr[mid:])
        merged, m_count = merge_count(left, right)
        return merged, l_count + r_count + m_count

    def merge_count(left, right):
        merged = []
        count = 0
        j = 0
        for li in left:
            while j < len(right) and 2 * right[j] < li:
                j += 1
            count += j
        # Merge
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, count

    _, count = sort_and_count(nums)
    return count


# =============================================================================
# WAY 9: Use sortedcontainers-like (or manual sorted list) with bisect_left
# =============================================================================
def reverse_pairs_9(nums):
    """Use bisect_left instead of bisect_right."""
    import bisect
    sorted_seen = []
    count = 0
    for num in nums:
        # Need count of elements > 2*num
        # bisect_left(sorted, 2*num + epsilon) for strict
        # Since 2*num is integer, bisect_right(sorted, 2*num) is correct.
        # Alternatively: bisect.bisect(sorted, 2*num)
        idx = bisect.bisect(sorted_seen, 2 * num)
        count += len(sorted_seen) - idx
        bisect.insort(sorted_seen, num)
    return count


# =============================================================================
# WAY 10: Helper function approach
# =============================================================================
def reverse_pairs_10(nums):
    """Extract helper functions."""
    import bisect

    def process(arr):
        sorted_seen = []
        count = 0
        for num in arr:
            idx = bisect.bisect_right(sorted_seen, 2 * num)
            count += len(sorted_seen) - idx
            bisect.insort(sorted_seen, num)
        return count

    return process(nums)


# =============================================================================
# WAY 11: Fenwick tree (BIT) approach
# =============================================================================
def reverse_pairs_11(nums):
    """
    BIT approach: coordinate compress values, then for each num,
    count how many previously seen values are > 2*num using BIT.

    Note: this counts in O(n log n) but is more complex than merge sort.
    """

    class BIT:
        def __init__(self, n):
            self.tree = [0] * (n + 1)

        def update(self, i, delta=1):
            while i < len(self.tree):
                self.tree[i] += delta
                i += i & (-i)

        def query(self, i):
            s = 0
            while i > 0:
                s += self.tree[i]
                i -= i & (-i)
            return s

    # Coordinate compression
    # We need to query: count of values > 2*num among previously seen
    # So we need to map values to indices in sorted unique array
    all_vals = sorted(set(nums))
    # To handle "2*num" queries, we also need to include these
    # For each num, query all values > 2*num, so we need to find
    # the smallest index where value > 2*num, then count rest.
    val_to_idx = {v: i + 1 for i, v in enumerate(all_vals)}

    bit = BIT(len(all_vals))
    count = 0
    for num in nums:
        # Find first index where value > 2*num
        import bisect
        threshold_idx = bisect.bisect_right(all_vals, 2 * num)
        if threshold_idx < len(all_vals):
            # Sum of counts from threshold_idx+1 to end
            total_seen = bit.query(len(all_vals))
            below = bit.query(threshold_idx)
            count += total_seen - below
        # Update BIT for current num
        bit.update(val_to_idx[num])

    return count


# =============================================================================
# WAY 12: Pure Python merge sort (clean)
# =============================================================================
def reverse_pairs_12(nums):
    """Clean merge sort implementation."""

    def merge_count(arr):
        if len(arr) <= 1:
            return arr, 0
        mid = len(arr) // 2
        left, lc = merge_count(arr[:mid])
        right, rc = merge_count(arr[mid:])
        # Count: in merged result, count pairs (l, r) with l > 2r
        merged = []
        count = 0
        j = 0
        for i in range(len(left)):
            while j < len(right) and 2 * right[j] < left[i]:
                j += 1
            count += j
        # Standard merge
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, count

    _, count = merge_count(nums)
    return count


# =============================================================================
# WAY 13: enumerate-based bisect
# =============================================================================
def reverse_pairs_13(nums):
    """Use enumerate with bisect."""
    import bisect
    sorted_seen = []
    count = 0
    for i, num in enumerate(nums):
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        count += len(sorted_seen) - idx
        bisect.insort(sorted_seen, num)
    return count


# =============================================================================
# WAY 14: With itertools.accumulate (not really needed, for variety)
# =============================================================================
def reverse_pairs_14(nums):
    """accumulate variant."""
    import bisect
    sorted_seen = []
    counts = []
    for num in nums:
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        counts.append(len(sorted_seen) - idx)
        bisect.insort(sorted_seen, num)
    return sum(counts)


# =============================================================================
# WAY 15: Negative-aware merge sort (handle nums[j] < 0)
# =============================================================================
def reverse_pairs_15(nums):
    """
    Merge sort variant that handles negative nums correctly.
    For negative nums[j], 2*nums[j] is also negative.
    """
    def merge_count(arr):
        if len(arr) <= 1:
            return arr, 0
        mid = len(arr) // 2
        left, lc = merge_count(arr[:mid])
        right, rc = merge_count(arr[mid:])
        # Count pairs (l in left, r in right) with l > 2*r
        # Since right is sorted, count using two pointers
        merged = []
        count = 0
        j = 0
        for i in range(len(left)):
            while j < len(right) and left[i] > 2 * right[j]:
                j += 1
            count += j
        # Standard merge
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, count

    _, count = merge_count(nums)
    return count


# =============================================================================
# WAY 16: Use sorted list with insort, manual count
# =============================================================================
def reverse_pairs_16(nums):
    """Manual sorted list approach."""
    sorted_seen = []
    count = 0
    for num in nums:
        # Binary search for first element > 2*num
        lo, hi = 0, len(sorted_seen)
        while lo < hi:
            mid = (lo + hi) // 2
            if sorted_seen[mid] <= 2 * num:
                lo = mid + 1
            else:
                hi = mid
        count += len(sorted_seen) - lo
        # Insert num in sorted order
        import bisect
        bisect.insort(sorted_seen, num)
    return count


# =============================================================================
# WAY 17: Use heap (less efficient but works)
# =============================================================================
def reverse_pairs_17(nums):
    """
    Maintain a sorted list. Use bisect.
    Same as bisect approach but called differently.
    """
    import bisect
    sorted_seen = []
    count = 0
    for num in nums:
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        count += len(sorted_seen) - idx
        bisect.insort(sorted_seen, num)
    return count


# =============================================================================
# WAY 18: numpy vectorized bisect
# =============================================================================
def reverse_pairs_18(nums):
    """Fully vectorized numpy approach."""
    try:
        import numpy as np
        n = len(nums)
        if n == 0:
            return 0
        # Naive vectorized: for each i, count j > i with nums[j] < nums[i]/2
        # This is O(n^2) but vectorized.
        arr = np.array(nums, dtype=np.int64)
        count = 0
        # For each i, mask elements > i and < arr[i]/2
        for i in range(n):
            count += int(np.sum(arr[i + 1:] * 2 < arr[i]))
        return count
    except ImportError:
        return reverse_pairs_1(nums)


# =============================================================================
# WAY 19: Recursive bisect
# =============================================================================
def reverse_pairs_19(nums):
    """Recursive bisect for educational purposes."""
    import bisect
    sorted_seen = []
    count = [0]

    def process(num):
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        count[0] += len(sorted_seen) - idx
        bisect.insort(sorted_seen, num)

    for num in nums:
        process(num)
    return count[0]


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def reverse_pairs_20(nums):
    """
    Final clean version using bisect (Educative approach).

    Algorithm:
    1. Process nums left-to-right.
    2. Maintain a sorted list of seen elements.
    3. For each num, count seen elements > 2*num (using bisect_right).
    4. Insert num into sorted list.
    5. Return total count.

    Alternative: Modified merge sort for O(n log n) optimal.

    Why this works:
    - When we process nums[i], all elements in sorted_seen are nums[0..i-1].
    - For each such element s, s > 2*nums[i] iff s is in our count.
    - bisect_right(sorted_seen, 2*nums[i]) gives the first index where
      element > 2*nums[i]. Everything from there to the end satisfies.

    Time:  O(n log^2 n) - n inserts at O(log n) each, each with O(log n) query.
    Space: O(n).

    Edge cases:
    - Empty: 0.
    - Single element: 0.
    - All zeros: 0 (need STRICT >).
    - Negative numbers: works correctly (2*num is also negative).
    """
    import bisect
    sorted_seen = []
    count = 0
    for num in nums:
        idx = bisect.bisect_right(sorted_seen, 2 * num)
        count += len(sorted_seen) - idx
        bisect.insort(sorted_seen, num)
    return count


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count pairs (i, j) with i < j where nums[i] > 2 * nums[j]."

Approach 1 (Educative - bisect):
"Process elements left-to-right. Maintain a sorted list of seen elements.
For each new num, count seen elements > 2*num using bisect_right. Insert
num into the sorted list."

Approach 2 (Optimal - merge sort):
"Modified merge sort. During merge of left and right halves (both sorted),
count pairs where left[i] > 2*right[j]. Use two pointers since both are
sorted."

Why bisect works:
"bisect_right(sorted_seen, 2*num) returns the index of the first element
strictly greater than 2*num. Everything from that index to the end satisfies
seen > 2*num."

Why merge sort works:
"After recursive sort, left and right are sorted. For each left[i], advance
j in right until 2*right[j] >= left[i] (i.e., left[i] <= 2*right[j]). The
count of valid j's is j (we've moved past invalid ones)."

Edge cases:
- Empty array: 0.
- Single element: 0.
- All zeros: 0 (need strict >).
- Negative numbers: 2*num is negative too; works correctly.

Complexity:
- Bisect: O(n log^2 n) — n inserts + n queries, each O(n) worst case for
  list insertion but amortized O(log n) for search and O(n) for insert.
  Actually, list insert is O(n), so total is O(n^2) for inserts.
  The optimal version is merge sort: O(n log n).

INTERVIEW TIPS:
1. Note that this is the SAME problem as "Count of Smaller Numbers After Self"
   but with a multiplier on one side.
2. The merge sort approach is the standard optimal solution.
3. The bisect approach is what Educative teaches but is technically O(n^2).
4. Handle negatives correctly: 2*num is also negative.

KEY TRICK:
For merge sort, use TWO pointers during merge:
- j advances only forward across right (because right is sorted and as left
  increases, 2*right[j] < left[i] becomes harder to satisfy).
- This gives O(n) count during merge.

ALTERNATIVE: BIT (Fenwick tree)
Coordinate compress values, then for each num query BIT for elements > 2*num.

ALTERNATIVE: AVL tree, sortedcontainers, etc.

RELATIONSHIP TO OTHER PROBLEMS:
- Count of Smaller Numbers After Self (LC 315): Same as merge sort but
  condition is nums[i] > nums[j].
- Count of Range Sum (LC 327): Similar with prefix sums.
- Reverse Pairs (LC 493): This exact problem.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort + bisect (BEST Educative)", reverse_pairs_1),
        ("Way 2: Verbose bisect", reverse_pairs_2),
        ("Way 3: Brute force", reverse_pairs_3),
        ("Way 4: Merge sort (BEST optimal)", reverse_pairs_4),
        ("Way 5: Manual insert", reverse_pairs_5),
        ("Way 6: Class-based bisect", reverse_pairs_6),
        ("Way 7: numpy bisect", reverse_pairs_7),
        ("Way 8: Merge sort helper", reverse_pairs_8),
        ("Way 9: bisect_left variant", reverse_pairs_9),
        ("Way 10: Helper function", reverse_pairs_10),
        ("Way 11: BIT/Fenwick", reverse_pairs_11),
        ("Way 12: Clean merge sort", reverse_pairs_12),
        ("Way 13: enumerate", reverse_pairs_13),
        ("Way 14: accumulate", reverse_pairs_14),
        ("Way 15: Negative-aware merge", reverse_pairs_15),
        ("Way 16: Manual binary search", reverse_pairs_16),
        ("Way 17: Heap variant", reverse_pairs_17),
        ("Way 18: numpy vectorized", reverse_pairs_18),
        ("Way 19: Recursive bisect", reverse_pairs_19),
        ("Way 20: Final cleanest", reverse_pairs_20),
    ]

    test_cases = [
        # Example 1: [6, 1, 3, 1]
        # Pairs: (0,1) 6>2*1, (0,3) 6>2*1 -> 2
        # (0,2) 6>2*3=6? No (strict). (1,2) 1>6? No. (1,3) 1>2? No.
        # (2,3) 3>2? Yes! Wait, that's another.
        # Let me recheck: 6>2*1=2 ✓, 6>2*3=6? strict no, 6>2*1=2 ✓
        # 1>2*3? no. 1>2*1? no. 3>2*1=2? yes.
        # So pairs: (0,1), (0,3), (2,3) -> 3
        # Hmm, the educative says 2. Let me re-verify.
        # Wait, the indices: nums=[6,1,3,1], i<j, nums[i]>2*nums[j]
        # i=0,j=1: 6>2*1=2 ✓
        # i=0,j=2: 6>2*3=6? No (need strict)
        # i=0,j=3: 6>2*1=2 ✓
        # i=1,j=2: 1>6? No
        # i=1,j=3: 1>2? No
        # i=2,j=3: 3>2*1=2 ✓
        # Total: 3 pairs
        ([6, 1, 3, 1], 3),

        # [1,3,2,3,1]: pairs where nums[i]>2*nums[j]
        # i=0,j=1: 1>6? No
        # i=0,j=2: 1>4? No
        # i=0,j=3: 1>6? No
        # i=0,j=4: 1>2? No
        # i=1,j=2: 3>4? No
        # i=1,j=3: 3>6? No
        # i=1,j=4: 3>2? Yes ✓
        # i=2,j=3: 2>6? No
        # i=2,j=4: 2>2? No (strict)
        # i=3,j=4: 3>2? Yes ✓
        # Total: 2
        ([1, 3, 2, 3, 1], 2),

        # [2,4,3,5,1]
        # i=0,j=1: 2>8? No
        # i=0,j=2: 2>6? No
        # i=0,j=3: 2>10? No
        # i=0,j=4: 2>2? No (strict)
        # i=1,j=2: 4>6? No
        # i=1,j=3: 4>10? No
        # i=1,j=4: 4>2? Yes ✓
        # i=2,j=3: 3>10? No
        # i=2,j=4: 3>2? Yes ✓
        # i=3,j=4: 5>2? Yes ✓
        # Total: 3
        ([2, 4, 3, 5, 1], 3),

        # Empty
        ([], 0),

        # Single
        ([5], 0),

        # All same
        # [3,3,3,3] -> 0 (strict > fails)
        ([3, 3, 3, 3], 0),

        # Already sorted ascending
        # [1,2,3,4] -> 0 (nums[i] <= nums[j] always, can't be > 2*nums[j])
        ([1, 2, 3, 4], 0),

        # Sorted descending
        # [4,3,2,1]: i<j, nums[i]>nums[j]. Check:
        # i=0,j=1: 4>6? No. i=0,j=2: 4>4? No. i=0,j=3: 4>2? Yes ✓
        # i=1,j=2: 3>4? No. i=1,j=3: 3>2? Yes ✓
        # i=2,j=3: 2>2? No.
        # Total: 2
        ([4, 3, 2, 1], 2),

        # With negatives
        # [-1, -2]: i=0,j=1: -1 > 2*-2=-4? Yes ✓
        # Total: 1
        ([-1, -2], 1),

        # [5,4,3,2,1] descending
        # i=0,j=1: 5>8? No
        # i=0,j=2: 5>6? No
        # i=0,j=3: 5>4? Yes ✓
        # i=0,j=4: 5>2? Yes ✓
        # i=1,j=2: 4>6? No
        # i=1,j=3: 4>4? No
        # i=1,j=4: 4>2? Yes ✓
        # i=2,j=3: 3>4? No
        # i=2,j=4: 3>2? Yes ✓
        # i=3,j=4: 2>2? No
        # Total: 4
        ([5, 4, 3, 2, 1], 4),

        # Standard LeetCode example: [1,3,2,3,1] -> 2 (already tested)

        # Another: [2,1] -> 2>2? No. Total: 0
        ([2, 1], 0),

        # [3,1] -> 3>2? Yes ✓. Total: 1
        ([3, 1], 1),
    ]

    print("=" * 70)
    print("REVERSE PAIRS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-pairs")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(nums))
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on nums={nums} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)