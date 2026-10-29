"""
Find K Pairs with Smallest Sums
Medium | 30 min

You are given two integer arrays nums1 and nums2 sorted in non-decreasing
order, and an integer k. Find the k pairs (u, v) with the smallest sums,
where u is from nums1 and v is from nums2.

Return the k pairs in any order.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/find-k-pairs-with-smallest-sums

Examples:
    nums1=[1,7,11], nums2=[2,4,6], k=3 -> [[1,2],[1,4],[1,6]]
    nums1=[1,1,2], nums2=[1,2,3], k=2 -> [[1,1],[1,1]]
    nums1=[1,2], nums2=[3], k=3 -> [[1,3],[2,3]] (only 2 pairs)

Constraints:
- 1 <= nums1.length, nums2.length <= 10^5
- -10^9 <= nums1[i], nums2[i] <= 10^9
- nums1 and nums2 are sorted in non-decreasing order.
- 1 <= k <= 10^4

KEY INSIGHT:
Treat each pair (i, j) as a node. Sum = nums1[i] + nums2[j].
Start with all (0, j) pairs. Pop smallest, advance its i.

Use heap with (sum, i, j). Visited set to avoid duplicates.

Time:  O(k log k).
Space: O(k).
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT FIND K PAIRS WITH SMALLEST SUMS:

1. UNDERSTAND THE PROBLEM:
   "Given two sorted arrays, find K pairs (a, b) with smallest sums."

2. KEY OBSERVATION:
   "Each pair (i, j) has sum nums1[i] + nums2[j].
   Since both arrays are sorted, we can use a heap to enumerate pairs
   in increasing sum order."

3. HEAP APPROACH:
   "1. Initialize heap with (nums1[i]+nums2[0], i, 0) for i in 0..k-1.
    2. Pop smallest sum (i, j).
    3. If j+1 < len(nums2), push (nums1[i]+nums2[j+1], i, j+1).
    4. Repeat K times."

4. WHY ONLY FIRST K OF NUMS1 INITIALLY:
   "Top K smallest sums must include at least one element from nums1[0..k-1].
   Beyond that, sums are larger."

5. VISITED SET (alternative formulation):
   "Push all (sum, i, j) initially. Track visited (i, j) pairs.
   When popping, push (i, j+1) and (i+1, j) if not visited."

6. EDGE CASES:
   - K > total pairs: return all pairs.
   - One array of size 1: at most n pairs.

7. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Heap     | O(k log k)| O(k)|
   | Brute    | O(n*m log)|O(k)|
   +----------+--------+--------+

8. WHY HEAP:
   "Always gives next smallest sum.
   K pops × log k per op = O(k log k)."
"""


# =============================================================================
# WAY 1: Heap with first k of nums1 init (BEST - Memorize!)
# =============================================================================
def k_smallest_pairs_1(nums1, nums2, k):
    """
    Push (nums1[i]+nums2[0], i, 0) for first k of nums1.
    Pop, advance j, push next from same i.
    """
    import heapq
    if not nums1 or not nums2 or k == 0:
        return []
    heap = []
    # Push first min(k, len(nums1)) pairs.
    for i in range(min(k, len(nums1))):
        heapq.heappush(heap, (nums1[i] + nums2[0], i, 0))
    result = []
    while heap and len(result) < k:
        s, i, j = heapq.heappop(heap)
        result.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return result


# =============================================================================
# WAY 2: Heap with visited set
# =============================================================================
def k_smallest_pairs_2(nums1, nums2, k):
    """Use heap + visited set. Push (i+1, j) and (i, j+1)."""
    import heapq
    if not nums1 or not nums2 or k == 0:
        return []
    visited = set()
    heap = [(nums1[0] + nums2[0], 0, 0)]
    visited.add((0, 0))
    result = []
    while heap and len(result) < k:
        s, i, j = heapq.heappop(heap)
        result.append([nums1[i], nums2[j]])
        # Push (i+1, j) and (i, j+1).
        if i + 1 < len(nums1) and (i + 1, j) not in visited:
            heapq.heappush(heap, (nums1[i + 1] + nums2[j], i + 1, j))
            visited.add((i + 1, j))
        if j + 1 < len(nums2) and (i, j + 1) not in visited:
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
            visited.add((i, j + 1))
    return result


# =============================================================================
# WAY 3: Brute force - generate first k*k pairs, sort, take k
# =============================================================================
def k_smallest_pairs_3(nums1, nums2, k):
    """Generate all pairs, sort by sum, return first k."""
    pairs = []
    for a in nums1:
        for b in nums2:
            pairs.append((a + b, a, b))
    pairs.sort()
    return [[a, b] for _, a, b in pairs[:k]]


# =============================================================================
# WAY 4: Use itertools.product + heapq.nsmallest
# =============================================================================
def k_smallest_pairs_4(nums1, nums2, k):
    """Use nsmallest on generator."""
    import heapq
    import itertools
    if not nums1 or not nums2 or k == 0:
        return []
    pairs = heapq.nsmallest(
        k,
        ((a + b, a, b) for a, b in itertools.product(nums1, nums2))
    )
    return [[a, b] for _, a, b in pairs]


# =============================================================================
# WAY 5: Heap with only first k of nums1 (cleaner)
# =============================================================================
def k_smallest_pairs_5(nums1, nums2, k):
    """Same as Way 1 with cleaner code."""
    import heapq
    if not nums1 or not nums2:
        return []
    pairs = []
    heap = [(nums1[i] + nums2[0], i, 0) for i in range(min(k, len(nums1)))]
    heapq.heapify(heap)
    while heap and len(pairs) < k:
        s, i, j = heapq.heappop(heap)
        pairs.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return pairs


# =============================================================================
# WAY 6: Use heapq with explicit comparator (sum)
# =============================================================================
def k_smallest_pairs_6(nums1, nums2, k):
    """Use heap with explicit sum tuples."""
    import heapq
    if not nums1 or not nums2 or k == 0:
        return []
    heap = []
    for i in range(min(k, len(nums1))):
        # (sum, i, j)
        heapq.heappush(heap, (nums1[i] + nums2[0], i, 0))
    result = []
    for _ in range(min(k, len(nums1) * len(nums2))):
        if not heap:
            break
        s, i, j = heapq.heappop(heap)
        result.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return result


# =============================================================================
# WAY 7: Pre-filter nums1 to first k
# =============================================================================
def k_smallest_pairs_7(nums1, nums2, k):
    """Pre-filter nums1 to first k elements (saves work)."""
    import heapq
    if not nums1 or not nums2 or k == 0:
        return []
    nums1 = nums1[:k]  # Top K smallest pairs must use one of first k of nums1.
    heap = [(nums1[i] + nums2[0], i, 0) for i in range(len(nums1))]
    heapq.heapify(heap)
    result = []
    while heap and len(result) < k:
        s, i, j = heapq.heappop(heap)
        result.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return result


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class KPairFinder:
    def __init__(self, nums1, nums2, k):
        self.nums1 = nums1
        self.nums2 = nums2
        self.k = k

    def find(self):
        import heapq
        if not self.nums1 or not self.nums2 or self.k == 0:
            return []
        heap = []
        for i in range(min(self.k, len(self.nums1))):
            heapq.heappush(heap, (self.nums1[i] + self.nums2[0], i, 0))
        result = []
        while heap and len(result) < self.k:
            s, i, j = heapq.heappop(heap)
            result.append([self.nums1[i], self.nums2[j]])
            if j + 1 < len(self.nums2):
                heapq.heappush(heap, (self.nums1[i] + self.nums2[j + 1], i, j + 1))
        return result


def k_smallest_pairs_8(nums1, nums2, k):
    return KPairFinder(nums1, nums2, k).find()


# =============================================================================
# WAY 9: Two-pointer technique
# =============================================================================
def k_smallest_pairs_9(nums1, nums2, k):
    """
    Two-pointer: start with (0, 0). Move the smaller-nums pointer.
    Less efficient than heap but educational.
    """
    if not nums1 or not nums2 or k == 0:
        return []
    pairs = []
    i, j = 0, 0
    # Start with smallest: nums1[0]+nums2[0].
    visited = set()
    visited.add((0, 0))
    # Use a heap anyway for correctness.
    import heapq
    heap = [(nums1[0] + nums2[0], 0, 0)]
    while heap and len(pairs) < k:
        s, i, j = heapq.heappop(heap)
        pairs.append([nums1[i], nums2[j]])
        if i + 1 < len(nums1) and (i + 1, j) not in visited:
            heapq.heappush(heap, (nums1[i + 1] + nums2[j], i + 1, j))
            visited.add((i + 1, j))
        if j + 1 < len(nums2) and (i, j + 1) not in visited:
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
            visited.add((i, j + 1))
    return pairs


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def k_smallest_pairs_10(nums1, nums2, k):
    """
    THE ONE TO MEMORIZE.

    Push (nums1[i]+nums2[0], i, 0) for first k of nums1.
    Pop, advance j, push (nums1[i]+nums2[j+1], i, j+1) if exists.

    Time:  O(k log k).
    Space: O(k).
    """
    import heapq
    if not nums1 or not nums2 or k == 0:
        return []
    heap = [(nums1[i] + nums2[0], i, 0) for i in range(min(k, len(nums1)))]
    heapq.heapify(heap)
    result = []
    while heap and len(result) < k:
        s, i, j = heapq.heappop(heap)
        result.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return result


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Heap first k (BEST)", k_smallest_pairs_1),
        ("Way 2: Heap visited", k_smallest_pairs_2),
        ("Way 3: Brute sort", k_smallest_pairs_3),
        ("Way 4: nsmallest product", k_smallest_pairs_4),
        ("Way 5: Heapify", k_smallest_pairs_5),
        ("Way 6: Explicit heap", k_smallest_pairs_6),
        ("Way 7: Pre-filter", k_smallest_pairs_7),
        ("Way 8: Class OOP", k_smallest_pairs_8),
        ("Way 9: Two-pointer heap", k_smallest_pairs_9),
        ("Way 10: Final cleanest", k_smallest_pairs_10),
    ]

    # Helper to normalize pairs (some implementations may return tuples).
    def normalize(pairs):
        return sorted([tuple(sorted(p)) for p in pairs])

    test_cases = [
        # (nums1, nums2, k, expected_pairs_set)
        # For test, we use unordered comparison via sorted tuple.
        ([1, 7, 11], [2, 4, 6], 3, [[1, 2], [1, 4], [1, 6]]),
        ([1, 1, 2], [1, 2, 3], 2, [[1, 1], [1, 1]]),
        ([1, 2], [3], 3, [[1, 3], [2, 3]]),
        ([1, 2, 3], [1, 2, 3], 3, [[1, 1], [1, 2], [2, 1]]),
        ([1, 1, 1], [1, 1, 1], 4, [[1, 1], [1, 1], [1, 1], [1, 1]]),
    ]

    print("=" * 70)
    print("FIND K PAIRS WITH SMALLEST SUMS - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/find-k-pairs-with-smallest-sums")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums1, nums2, k, expected in test_cases:
            try:
                result = func(list(nums1), list(nums2), k)
                if normalize(result) != normalize(expected):
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums1={nums1}, nums2={nums2}, k={k}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: nums1={nums1}, nums2={nums2}, k={k}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
