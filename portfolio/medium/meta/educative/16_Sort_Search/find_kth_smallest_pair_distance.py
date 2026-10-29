"""
Find K-th Smallest Pair Distance
Hard | 40 min

Given an integer array nums and integer k, return the k-th smallest
distance among all pairs (nums[i], nums[j]) where i < j.

Distance = |nums[i] - nums[j]|.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/find-k-th-smallest-pair-distance

Examples:
    nums=[1,3,1], k=1 -> 0 (pair (1,1))
    nums=[1,1,1], k=2 -> 0
    nums=[1,6,1], k=3 -> 5

Constraints:
- 2 <= n <= 10^3 (educative) / 10^4 (LC)
- 0 <= nums[i] <= 10^3 (educative) / 10^6 (LC)
- 1 <= k <= n*(n-1)/2

KEY INSIGHT: Binary search on the DISTANCE. Count how many pairs have
distance <= d. This count is monotonic in d.
"""

import bisect


# =============================================================================
# WAY 1: Binary search on distance + two-pointer count (BEST - Memorize!)
# =============================================================================
def smallest_distance_pair_1(nums, k):
    """
    KEY INSIGHT: For a given d, count pairs with |nums[i]-nums[j]| <= d
    using two-pointer on sorted nums. This count is monotonic in d.
    Binary search to find smallest d where count >= k.
    """
    a = sorted(nums)
    n = len(a)

    def count_le(d):
        # Count pairs (i, j) with j > i and a[j] - a[i] <= d
        count = 0
        left = 0
        for right in range(n):
            while a[right] - a[left] > d:
                left += 1
            count += right - left
        return count

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 2: Same as Way 1 but with bisect_right
# =============================================================================
def smallest_distance_pair_2(nums, k):
    a = sorted(nums)
    n = len(a)

    def count_le(d):
        count = 0
        for i in range(n):
            # Find rightmost index where a[j] - a[i] <= d, j > i
            j = bisect.bisect_right(a, a[i] + d, i + 1) - 1
            if j >= i + 1:
                count += j - i
        return count

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 3: Brute force - generate all pairs
# =============================================================================
def smallest_distance_pair_3(nums, k):
    """Generate all pairs, collect distances, sort, return k-th."""
    n = len(nums)
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            distances.append(abs(nums[i] - nums[j]))
    distances.sort()
    return distances[k - 1]


# =============================================================================
# WAY 4: Brute force with heap
# =============================================================================
def smallest_distance_pair_4(nums, k):
    """Use min-heap to extract k-th smallest distance."""
    import heapq
    a = sorted(nums)
    n = len(a)
    # Use heap: each entry (distance, i, j) where j > i
    # Initially push (a[i+1]-a[i], i, i+1) for all i
    heap = []
    for i in range(n - 1):
        heapq.heappush(heap, (a[i + 1] - a[i], i, i + 1))
    # Track counts
    count = 0
    visited = set()
    last = -1
    while heap:
        d, i, j = heapq.heappop(heap)
        count += 1
        if count == k:
            return d
        last = d
        if j + 1 < n and (i, j + 1) not in visited:
            heapq.heappush(heap, (a[j + 1] - a[i], i, j + 1))
            visited.add((i, j + 1))
    return last


# =============================================================================
# WAY 5: Sort + count using two-pointer, then sort distances
# =============================================================================
def smallest_distance_pair_5(nums, k):
    """Two-pointer to compute count for each unique distance."""
    a = sorted(nums)
    n = len(a)
    # Generate all distances
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            distances.append(a[j] - a[i])
    distances.sort()
    return distances[k - 1]


# =============================================================================
# WAY 6: Sort + binary search + count with two-pointer (verbose)
# =============================================================================
def smallest_distance_pair_6(nums, k):
    """Verbose version of Way 1."""
    a = sorted(nums)
    n = len(a)

    def count_pairs_at_most(diff):
        count = 0
        i = 0
        for j in range(1, n):
            while a[j] - a[i] > diff:
                i += 1
            count += j - i
        return count

    lo = 0
    hi = a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        c = count_pairs_at_most(mid)
        if c < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 7: Sort + count for each possible distance
# =============================================================================
def smallest_distance_pair_7(nums, k):
    """For each d from 0 to max, count pairs with distance == d. Cumulate."""
    a = sorted(nums)
    n = len(a)
    max_d = a[-1] - a[0]

    def count_eq(d):
        count = 0
        i = 0
        for j in range(1, n):
            while a[j] - a[i] > d:
                i += 1
            # Now a[j] - a[i] <= d
            # We want exact d
            # Hmm, two-pointer gives <= not ==
            break  # This doesn't work for exact
        return count

    # Better: count <= d, and use difference
    def count_le(d):
        count = 0
        i = 0
        for j in range(1, n):
            while a[j] - a[i] > d:
                i += 1
            count += j - i
        return count

    cum = 0
    for d in range(max_d + 1):
        cnt = count_le(d) - cum
        cum += cnt
        if cum >= k:
            return d
    return max_d


# =============================================================================
# WAY 8: Binary search with on-the-fly left pointer
# =============================================================================
def smallest_distance_pair_8(nums, k):
    """Binary search with inline two-pointer."""
    a = sorted(nums)
    n = len(a)

    def count_le(diff):
        cnt = 0
        left = 0
        for right in range(n):
            while a[right] - a[left] > diff:
                left += 1
            cnt += right - left
        return cnt

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 9: Sort + binary search + bisect count
# =============================================================================
def smallest_distance_pair_9(nums, k):
    """Use bisect for count."""
    a = sorted(nums)
    n = len(a)

    def count_le(diff):
        cnt = 0
        for i in range(n):
            # j: smallest index where a[j] > a[i] + diff
            j = bisect.bisect_right(a, a[i] + diff, i + 1)
            cnt += j - i - 1  # -1 because we want count of j's strictly greater than i
        return cnt

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 10: Class-based
# =============================================================================
class PairDistanceFinder:
    def __init__(self, nums):
        self.a = sorted(nums)
        self.n = len(self.a)

    def count_le(self, diff):
        cnt = 0
        left = 0
        for right in range(self.n):
            while self.a[right] - self.a[left] > diff:
                left += 1
            cnt += right - left
        return cnt

    def find_kth(self, k):
        lo, hi = 0, self.a[-1] - self.a[0]
        while lo < hi:
            mid = (lo + hi) // 2
            if self.count_le(mid) < k:
                lo = mid + 1
            else:
                hi = mid
        return lo


def smallest_distance_pair_10(nums, k):
    return PairDistanceFinder(nums).find_kth(k)


# =============================================================================
# WAY 11: Binary search with floating-point safety
# =============================================================================
def smallest_distance_pair_11(nums, k):
    """Same as Way 1 but explicit mid calculation."""
    a = sorted(nums)
    n = len(a)
    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        count = 0
        left = 0
        for right in range(n):
            while a[right] - a[left] > mid:
                left += 1
            count += right - left
        if count < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 12: Sort + recursive binary search
# =============================================================================
def smallest_distance_pair_12(nums, k):
    """Recursive binary search."""
    a = sorted(nums)
    n = len(a)

    def count_le(diff):
        cnt = 0
        left = 0
        for right in range(n):
            while a[right] - a[left] > diff:
                left += 1
            cnt += right - left
        return cnt

    def search(lo, hi):
        if lo == hi:
            return lo
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            return search(mid + 1, hi)
        return search(lo, mid)

    return search(0, a[-1] - a[0])


# =============================================================================
# WAY 13: Using numpy
# =============================================================================
def smallest_distance_pair_13(nums, k):
    """Vectorized using numpy."""
    import numpy as np
    a = np.sort(np.array(nums))
    n = len(a)

    def count_le(diff):
        # For each i, count j where a[j] - a[i] <= diff, j > i
        counts = np.searchsorted(a, a + diff, side='right') - np.arange(1, n + 1)
        return int(counts.sum())

    lo, hi = 0, int(a[-1] - a[0])
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 14: Sort + binary search + cumulative count
# =============================================================================
def smallest_distance_pair_14(nums, k):
    """Same as Way 7 but more efficient."""
    a = sorted(nums)
    n = len(a)
    max_d = a[-1] - a[0]

    def count_le(d):
        cnt = 0
        left = 0
        for right in range(n):
            while a[right] - a[left] > d:
                left += 1
            cnt += right - left
        return cnt

    # Binary search instead of linear
    lo, hi = 0, max_d
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 15: Sort + tuple distance enumeration
# =============================================================================
def smallest_distance_pair_15(nums, k):
    """Enumerate pairs as tuples, sort, return k-th."""
    n = len(nums)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((abs(nums[i] - nums[j]), i, j))
    pairs.sort()
    return pairs[k - 1][0]


# =============================================================================
# WAY 16: Sort + binary search + count with idx subtraction
# =============================================================================
def smallest_distance_pair_16(nums, k):
    """Binary search with optimized count."""
    a = sorted(nums)
    n = len(a)

    def count_le(diff):
        # Two-pointer
        cnt = 0
        j = 0
        for i in range(n):
            while j < n and a[j] - a[i] <= diff:
                j += 1
            cnt += j - i - 1  # j-i elements from i, but exclude i itself
        return cnt

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 17: Using sets to deduplicate
# =============================================================================
def smallest_distance_pair_17(nums, k):
    """Generate distances, sort, return k-th."""
    a = sorted(nums)
    n = len(a)
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            distances.append(a[j] - a[i])
    distances.sort()
    return distances[k - 1]


# =============================================================================
# WAY 18: Sort + binary search with early termination
# =============================================================================
def smallest_distance_pair_18(nums, k):
    """Binary search + early termination."""
    a = sorted(nums)
    n = len(a)

    def count_le(diff):
        cnt = 0
        left = 0
        for right in range(n):
            while a[right] - a[left] > diff:
                left += 1
            cnt += right - left
            if cnt >= k:
                return cnt
        return cnt

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 19: One-liner style
# =============================================================================
def smallest_distance_pair_19(nums, k):
    """Concise."""
    a = sorted(nums)
    n = len(a)

    def cnt(d):
        c = 0
        l = 0
        for r in range(n):
            while a[r] - a[l] > d:
                l += 1
            c += r - l
        return c

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        m = (lo + hi) // 2
        lo, hi = (m + 1, hi) if cnt(m) < k else (lo, m)
    return lo


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def smallest_distance_pair_20(nums, k):
    """
    THE ONE TO MEMORIZE.

    1. Sort nums.
    2. Binary search on distance d in [0, max-min].
    3. For each d, count pairs with |a[j] - a[i]| <= d using two-pointer.
    4. Find smallest d with count >= k.

    Time:  O(n log n + n log(max_diff)) = O(n log n)
    Space: O(1) extra (or O(n) for sort)
    """
    a = sorted(nums)
    n = len(a)

    def count_le(d):
        count = 0
        left = 0
        for right in range(n):
            while a[right] - a[left] > d:
                left += 1
            count += right - left
        return count

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the k-th smallest absolute difference among all pairs
in nums."

Key Insight:
"For a given distance d, I can count pairs with |nums[i]-nums[j]| <= d.
This count is MONOTONICALLY NON-DECREASING in d. So I can BINARY SEARCH
on d."

Algorithm:
1. Sort nums. After sorting, |a[j] - a[i]| = a[j] - a[i] for j > i.
2. count_le(d): use two-pointer on sorted array. For each right pointer,
   advance left while a[right] - a[left] > d. Count pairs = right - left.
3. Binary search on d in [0, max-min]:
   - If count_le(mid) < k, d is too small -> lo = mid + 1.
   - Else, d might be the answer -> hi = mid.
4. Return lo.

Edge Cases:
- All same elements: distance is 0.
- k=1: smallest distance.
- k=n(n-1)/2: largest distance.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| BS+count  | O(nlogn)| O(1)   |
| Brute     | O(n^2l)| O(n^2) |
+-----------+--------+--------+

KEY TRICK:
After sorting, two-pointer counts pairs with difference <= d.
Then binary search on d.

RELATED PROBLEMS:
- Kth Smallest Element in Sorted Matrix (LC 378): similar search.
- Find K-th Smallest Pair Distance (LC 719): this problem.
- Kth Smallest Number in Multiplication Table (LC 668).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: BS+two-ptr (BEST)", smallest_distance_pair_1),
        ("Way 2: BS+bisect_right", smallest_distance_pair_2),
        ("Way 3: Brute force pairs", smallest_distance_pair_3),
        ("Way 4: Heap-based", smallest_distance_pair_4),
        ("Way 5: Two-ptr enumerate", smallest_distance_pair_5),
        ("Way 6: BS verbose", smallest_distance_pair_6),
        ("Way 7: For each d", smallest_distance_pair_7),
        ("Way 8: BS inline", smallest_distance_pair_8),
        ("Way 9: BS+bisect", smallest_distance_pair_9),
        ("Way 10: Class OOP", smallest_distance_pair_10),
        ("Way 11: BS+mid safety", smallest_distance_pair_11),
        ("Way 12: Recursive BS", smallest_distance_pair_12),
        ("Way 13: Numpy", smallest_distance_pair_13),
        ("Way 14: BS+cumulative", smallest_distance_pair_14),
        ("Way 15: Tuple enumerate", smallest_distance_pair_15),
        ("Way 16: BS+idx subtract", smallest_distance_pair_16),
        ("Way 17: Set dedup", smallest_distance_pair_17),
        ("Way 18: BS+early term", smallest_distance_pair_18),
        ("Way 19: Most concise", smallest_distance_pair_19),
        ("Way 20: Final cleanest", smallest_distance_pair_20),
    ]

    test_cases = [
        # (nums, k, expected)
        ([1, 3, 1], 1, 0),
        ([1, 3, 1], 2, 2),
        ([1, 3, 1], 3, 2),
        ([1, 6, 1], 3, 5),
        ([1, 1, 1], 1, 0),
        ([1, 1, 1], 2, 0),
        ([1, 1, 1], 3, 0),
        ([0, 5, 3, 4], 1, 1),
        # pairs: |0-3|=3, |0-4|=4, |0-5|=5, |5-3|=2, |5-4|=1, |4-3|=1
        # sorted: 1,1,2,3,4,5 -> k=1 is 1
        ([1, 2, 3, 4, 5], 1, 1),
        # pairs (10 total): all differences 1-4
        # sorted: 1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4... wait n=5 gives 10 pairs
        # (1,2)=1, (1,3)=2, (1,4)=3, (1,5)=4, (2,3)=1, (2,4)=2, (2,5)=3, (3,4)=1, (3,5)=2, (4,5)=1
        # sorted: 1,1,1,1,2,2,2,3,3,4
        ([1, 2, 3, 4, 5], 4, 1),    # 4th is 1
        ([1, 2, 3, 4, 5], 5, 2),    # 5th is 2
        ([1, 2, 3, 4, 5], 10, 4),   # 10th is 4
        ([9, 10, 7, 10, 6], 1, 0),  # pair of 10s has distance 0
        # pairs: (6,7)=1, (6,9)=3, (6,10)=4, (6,10)=4, (7,9)=2, (7,10)=3, (7,10)=3, (9,10)=1, (9,10)=1, (10,10)=0
        # sorted: 0,1,1,1,2,3,3,3,4,4
        ([9, 10, 7, 10, 6], 5, 2),  # 5th is 2
        ([9, 10, 7, 10, 6], 10, 4), # 10th is 4
    ]

    print("=" * 70)
    print("FIND K-TH SMALLEST PAIR DISTANCE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/find-k-th-smallest-pair-distance")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, k, expected in test_cases:
            try:
                result = func(nums[:], k)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, k={k}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on nums={nums}, k={k} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
