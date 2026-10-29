"""
Kth Smallest Number in M Sorted Lists
Medium | 30 min

Given M sorted integer arrays, find the Kth smallest number among
all the arrays.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/kth-smallest-number-in-m-sorted-lists

Examples:
    lists=[[2,6,8],[3,6,7],[1,2,3]], K=5 -> 4
        All: 1,2,2,3,3,6,6,7,8 → 5th = 3? No, let's recount:
        1 (L3), 2 (L1), 2 (L3), 3 (L2), 3 (L3), 6 (L1), 6 (L2), 7 (L2), 8 (L1)
        Sorted: 1, 2, 2, 3, 3, 6, 6, 7, 8. K=5 → 3. Hmm, but expected is 4.
        Actually wait — let's recount carefully:
        L1: [2,6,8]
        L2: [3,6,7]
        L3: [1,2,3]
        Combined sorted: 1, 2, 2, 3, 3, 6, 6, 7, 8. (size 9)
        K=5 → 4th index (0-indexed) → 3. But problem says 4?
        Actually problem: K=5 means 5th smallest (1-indexed). So index 4 → 3.
        Hmm, the example might have a different setup. Let's use K=5 → 3.
    lists=[[1,5,9],[2,6,10],[3,7,11]], K=4 -> 4
        Combined sorted: 1,2,3,4(no),... actually:
        1,2,3,5,6,7,9,10,11. K=4 → 5.
        Wait, with our lists: [1,5,9],[2,6,10],[3,7,11]
        All values: 1,5,9,2,6,10,3,7,11. Sorted: 1,2,3,5,6,7,9,10,11.
        K=4 → 5.

Constraints:
- 1 <= K <= 10^9
- -10^9 <= lists[i][j] <= 10^9 (typically)
- lists[i] sorted in non-decreasing order.

KEY INSIGHT:
Min-heap of size M. Pop K-1 times to skip the smallest K-1.
The K-th pop is the answer.

Alternative: Binary search on value range.

Time:  O(K log M) using heap.
Space: O(M).
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT KTH SMALLEST IN M SORTED LISTS:

1. UNDERSTAND THE PROBLEM:
   "Find K-th smallest element across M sorted arrays combined."

2. KEY OBSERVATION:
   "Same as K-way merge, but we only need the K-th smallest.
   We don't need to merge all, just pop K-1 times and report next."

3. HEAP APPROACH:
   "1. Initialize min-heap with first element of each list.
    2. Pop top, advance to next in same list, push if exists.
    3. Repeat K-1 times.
    4. K-th pop is the answer."

4. WHY HEAP:
   "Each pop/push is O(log M). K operations → O(K log M).
   Naive: collect all, sort → O(N log N)."

5. ALTERNATIVE: BINARY SEARCH
   "Binary search on value range. For each mid, count elements <= mid.
   If count >= K, mid is too high (or just right). Adjust bounds."

6. EDGE CASES:
   - K=1: smallest of all heads.
   - K=total: largest of all tails.
   - Lists with negatives.
   - Empty lists.

7. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Heap K-pops| O(K log M)| O(M)|
   | Collect+sort| O(N log N)| O(N)|
   | Binary srch| O(N log V)| O(1)|
   +----------+--------+--------+

8. WHY HEAP > COLLECT:
   "Don't need to process all N elements if K is small.
   O(K log M) << O(N log N) for K << N."
"""


# =============================================================================
# WAY 1: Heap pop K times (BEST - Memorize!)
# =============================================================================
def kth_smallest_1(lists, K):
    """
    Min-heap of M heads. Pop K-1 times. K-th pop is answer.
    """
    import heapq
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))  # (val, list_idx, elem_idx)
    for _ in range(K - 1):
        if not heap:
            return None
        val, i, j = heapq.heappop(heap)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))
    if heap:
        return heapq.heappop(heap)[0]
    return None


# =============================================================================
# WAY 2: Heap with wrapper class
# =============================================================================
class HeapItem:
    def __init__(self, val, list_idx, elem_idx):
        self.val = val
        self.list_idx = list_idx
        self.elem_idx = elem_idx

    def __lt__(self, other):
        return self.val < other.val


def kth_smallest_2(lists, K):
    """Use wrapper class to handle tie-breaking."""
    import heapq
    counter = 0  # tiebreaker
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], counter, i, 0))
            counter += 1
    for _ in range(K - 1):
        if not heap:
            return None
        val, _, i, j = heapq.heappop(heap)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j + 1], counter, i, j + 1))
            counter += 1
    if heap:
        return heapq.heappop(heap)[0]
    return None


# =============================================================================
# WAY 3: Collect all, sort, pick K-th
# =============================================================================
def kth_smallest_3(lists, K):
    """Naive: collect all, sort, return K-th."""
    all_vals = []
    for lst in lists:
        all_vals.extend(lst)
    all_vals.sort()
    if K - 1 < len(all_vals):
        return all_vals[K - 1]
    return None


# =============================================================================
# WAY 4: Binary search on value range
# =============================================================================
def kth_smallest_4(lists, K):
    """Binary search on value range. Count elements <= mid."""

    def count_leq(mid):
        """Count total elements <= mid across all lists."""
        total = 0
        for lst in lists:
            # Binary search within sorted list.
            lo, hi = 0, len(lst)
            while lo < hi:
                m = (lo + hi) // 2
                if lst[m] <= mid:
                    lo = m + 1
                else:
                    hi = m
            total += lo
        return total

    if not lists or K <= 0:
        return None
    lo = min(lst[0] for lst in lists if lst)
    hi = max(lst[-1] for lst in lists if lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if count_leq(mid) >= K:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 5: Use heapq.merge iterator, take K-th
# =============================================================================
def kth_smallest_5(lists, K):
    """Stream merge and take K-th."""
    import heapq
    merged = heapq.merge(*lists)
    val = None
    for i, v in enumerate(merged):
        if i == K - 1:
            val = v
            break
    return val


# =============================================================================
# WAY 6: While loop variant of heap
# =============================================================================
def kth_smallest_6(lists, K):
    """Same as Way 1 but with while loop."""
    import heapq
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))
    popped = 0
    while heap and popped < K:
        val, i, j = heapq.heappop(heap)
        popped += 1
        if popped == K:
            return val
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))
    return None


# =============================================================================
# WAY 7: heapq.nsmallest (cleanest)
# =============================================================================
def kth_smallest_7(lists, K):
    """Use heapq.nsmallest to get K smallest, return last."""
    import heapq
    # Flatten iterators.
    iters = [iter(lst) for lst in lists if lst]
    # Manually merge using heapq.merge.
    merged = heapq.merge(*iters)
    # Take K-th using iter.
    result = None
    for i, v in enumerate(merged):
        if i + 1 == K:
            result = v
            break
    return result


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class KthFinder:
    def __init__(self, lists, K):
        self.lists = lists
        self.K = K

    def find(self):
        import heapq
        heap = []
        for i, lst in enumerate(self.lists):
            if lst:
                heapq.heappush(heap, (lst[0], i, 0))
        for _ in range(self.K - 1):
            if not heap:
                return None
            val, i, j = heapq.heappop(heap)
            if j + 1 < len(self.lists[i]):
                heapq.heappush(heap, (self.lists[i][j + 1], i, j + 1))
        if heap:
            return heapq.heappop(heap)[0]
        return None


def kth_smallest_8(lists, K):
    return KthFinder(lists, K).find()


# =============================================================================
# WAY 9: Binary search with two pointers
# =============================================================================
def kth_smallest_9(lists, K):
    """Binary search with two-pointer count. Faster count."""
    if not lists or K <= 0:
        return None
    lo = min(lst[0] for lst in lists if lst)
    hi = max(lst[-1] for lst in lists if lst)

    def count_leq(mid):
        total = 0
        for lst in lists:
            # Count elements <= mid in sorted lst using bisect.
            import bisect
            total += bisect.bisect_right(lst, mid)
        return total

    while lo < hi:
        mid = (lo + hi) // 2
        if count_leq(mid) >= K:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def kth_smallest_10(lists, K):
    """
    THE ONE TO MEMORIZE.

    Min-heap of M heads (one per list).
    Pop K-1 times to skip smallest K-1.
    K-th pop is the answer.

    Time:  O(K log M).
    Space: O(M).
    """
    import heapq
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))
    for _ in range(K - 1):
        if not heap:
            return None
        val, i, j = heapq.heappop(heap)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))
    if heap:
        return heapq.heappop(heap)[0]
    return None


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Heap pop K (BEST)", kth_smallest_1),
        ("Way 2: Wrapper class", kth_smallest_2),
        ("Way 3: Collect+sort", kth_smallest_3),
        ("Way 4: Binary search", kth_smallest_4),
        ("Way 5: heapq.merge stream", kth_smallest_5),
        ("Way 6: While loop heap", kth_smallest_6),
        ("Way 7: heapq.merge iter", kth_smallest_7),
        ("Way 8: Class OOP", kth_smallest_8),
        ("Way 9: Binary search bisect", kth_smallest_9),
        ("Way 10: Final cleanest", kth_smallest_10),
    ]

    test_cases = [
        # (lists, K, expected)
        ([[2, 6, 8], [3, 6, 7], [1, 2, 3]], 5, 3),
        ([[1, 5, 9], [2, 6, 10], [3, 7, 11]], 4, 5),
        ([[1, 2, 3]], 2, 2),
        ([[1], [2], [3]], 1, 1),
        ([[1], [2], [3]], 3, 3),
        ([[5, 10, 15], [3, 6, 9, 12, 18]], 4, 9),
        ([[-5, -2, 1], [0, 3, 7]], 3, 0),
        ([[1, 3, 5], [2, 4, 6]], 5, 5),
    ]

    print("=" * 70)
    print("KTH SMALLEST IN M SORTED LISTS - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/kth-smallest-number-in-m-sorted-lists")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for lists, K, expected in test_cases:
            try:
                # Deep copy lists.
                lists_copy = [list(l) for l in lists]
                result = func(lists_copy, K)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: lists={lists}, K={K}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: lists={lists}, K={K}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
