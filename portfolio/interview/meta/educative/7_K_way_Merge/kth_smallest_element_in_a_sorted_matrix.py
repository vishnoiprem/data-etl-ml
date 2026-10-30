"""
Kth Smallest Element in a Sorted Matrix
Medium | 30 min

Given an n x n matrix where each of the rows and columns is sorted in
ascending order, return the kth smallest element in the matrix.

Note that it is the kth smallest element in the sorted order, not the
kth distinct element.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/kth-smallest-element-in-a-sorted-matrix

Examples:
    matrix=[[1,5,9],[10,11,13],[12,13,15]], k=8 -> 13
        Sorted: 1,5,9,10,11,12,13,13,15. K=8 → 13.
    matrix=[[-5]], k=1 -> -5

Constraints:
- n == matrix.length == matrix[i].length
- 1 <= n <= 300
- -10^9 <= matrix[i][j] <= 10^9
- 1 <= k <= n^2
- Rows and columns sorted in non-decreasing order.

KEY INSIGHT:
Treat matrix as n sorted lists (each row).
Heap pop K-1 times. K-th pop is answer.

Alternative: Binary search on value range.

Time:  O(K log n) using heap.
Space: O(n).
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT KTH SMALLEST IN SORTED MATRIX:

1. UNDERSTAND THE PROBLEM:
   "n×n matrix, rows and columns sorted. Find K-th smallest element."

2. KEY OBSERVATION:
   "Each ROW is a sorted list. We can think of the matrix as N sorted lists
   and use K-way merge (heap-based)."

3. HEAP APPROACH:
   "1. Push first element of each row into heap (n elements).
    2. Pop top K-1 times.
    3. After each pop, push next element in same row.
    4. K-th pop is answer."

4. WHY HEAP WORKS:
   "Smallest unseen element is among row heads.
   Heap gives smallest in O(log n)."

5. BINARY SEARCH ALTERNATIVE:
   "Binary search on value range [min, max].
   For each mid, count elements <= mid (using row-wise binary search).
   Adjust bounds based on count vs K."

6. EDGE CASES:
   - Single element: return it.
   - K=1: top-left element.
   - K=n²: bottom-right element.

7. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Heap     | O(K log n)| O(n)|
   | Binary srch| O(n log V)| O(1)|
   | Sort all | O(n² log n²)|O(n²)|
   +----------+--------+--------+

8. WHY HEAP > SORT:
   "Don't need to sort all n² elements.
   O(K log n) << O(n² log n²) for K << n²."
"""


# =============================================================================
# WAY 1: Heap pop K times (BEST - Memorize!)
# =============================================================================
def kth_smallest_1(matrix, k):
    """
    Min-heap of size n (one entry per row).
    Push (matrix[i][0], i, 0) for each row.
    Pop K-1 times; advance j; push next.
    """
    import heapq
    n = len(matrix)
    heap = [(matrix[i][0], i, 0) for i in range(n)]
    heapq.heapify(heap)
    for _ in range(k - 1):
        val, i, j = heapq.heappop(heap)
        if j + 1 < n:
            heapq.heappush(heap, (matrix[i][j + 1], i, j + 1))
    return heapq.heappop(heap)[0] if heap else None


# =============================================================================
# WAY 2: Binary search on value range
# =============================================================================
def kth_smallest_2(matrix, k):
    """Binary search on value range. Count elements <= mid."""

    def count_leq(mid):
        """Count elements <= mid in matrix."""
        count = 0
        n = len(matrix)
        # Start from bottom-left.
        i, j = n - 1, 0
        while i >= 0 and j < n:
            if matrix[i][j] <= mid:
                count += i + 1
                j += 1
            else:
                i -= 1
        return count

    n = len(matrix)
    lo = matrix[0][0]
    hi = matrix[n - 1][n - 1]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_leq(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 3: Sort all elements, take K-th
# =============================================================================
def kth_smallest_3(matrix, k):
    """Naive: flatten, sort, return K-th."""
    flat = []
    for row in matrix:
        flat.extend(row)
    flat.sort()
    return flat[k - 1]


# =============================================================================
# WAY 4: Heap with visited set (handles non-strict sort)
# =============================================================================
def kth_smallest_4(matrix, k):
    """Use visited set to handle duplicates across rows."""
    import heapq
    n = len(matrix)
    heap = [(matrix[0][0], 0, 0)]
    visited = {(0, 0)}
    for _ in range(k - 1):
        val, i, j = heapq.heappop(heap)
        # Push right and down.
        if j + 1 < n and (i, j + 1) not in visited:
            heapq.heappush(heap, (matrix[i][j + 1], i, j + 1))
            visited.add((i, j + 1))
        if i + 1 < n and (i + 1, j) not in visited:
            heapq.heappush(heap, (matrix[i + 1][j], i + 1, j))
            visited.add((i + 1, j))
    return heapq.heappop(heap)[0]


# =============================================================================
# WAY 5: heapq.nsmallest on flatten
# =============================================================================
def kth_smallest_5(matrix, k):
    """Use heapq.nsmallest to get K smallest from flattened iterator."""
    import heapq
    flat = (x for row in matrix for x in row)
    return heapq.nsmallest(k, flat)[-1]


# =============================================================================
# WAY 6: Binary search with row-wise binary search
# =============================================================================
def kth_smallest_6(matrix, k):
    """Binary search on value range with row-wise binary search."""
    import bisect

    def count_leq(mid):
        count = 0
        for row in matrix:
            count += bisect.bisect_right(row, mid)
        return count

    n = len(matrix)
    lo = matrix[0][0]
    hi = matrix[n - 1][n - 1]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_leq(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 7: Use heapq.merge on rows
# =============================================================================
def kth_smallest_7(matrix, k):
    """Stream merge rows using heapq.merge."""
    import heapq
    merged = heapq.merge(*matrix)
    val = None
    for i, v in enumerate(merged):
        if i == k - 1:
            val = v
            break
    return val


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class MatrixKthFinder:
    def __init__(self, matrix, k):
        self.matrix = matrix
        self.k = k

    def find(self):
        import heapq
        n = len(self.matrix)
        heap = [(self.matrix[i][0], i, 0) for i in range(n)]
        heapq.heapify(heap)
        for _ in range(self.k - 1):
            val, i, j = heapq.heappop(heap)
            if j + 1 < n:
                heapq.heappush(heap, (self.matrix[i][j + 1], i, j + 1))
        return heapq.heappop(heap)[0]


def kth_smallest_8(matrix, k):
    return MatrixKthFinder(matrix, k).find()


# =============================================================================
# WAY 9: While loop with heap
# =============================================================================
def kth_smallest_9(matrix, k):
    """Same as Way 1 but with while loop."""
    import heapq
    n = len(matrix)
    heap = []
    for i in range(n):
        heapq.heappush(heap, (matrix[i][0], i, 0))
    popped = 0
    while heap and popped < k:
        val, i, j = heapq.heappop(heap)
        popped += 1
        if popped == k:
            return val
        if j + 1 < n:
            heapq.heappush(heap, (matrix[i][j + 1], i, j + 1))
    return None


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def kth_smallest_10(matrix, k):
    """
    THE ONE TO MEMORIZE.

    Min-heap of size n (one per row).
    Push first column. Pop K-1 times. K-th pop is answer.

    Time:  O(K log n).
    Space: O(n).
    """
    import heapq
    n = len(matrix)
    heap = [(matrix[i][0], i, 0) for i in range(n)]
    heapq.heapify(heap)
    for _ in range(k - 1):
        val, i, j = heapq.heappop(heap)
        if j + 1 < n:
            heapq.heappush(heap, (matrix[i][j + 1], i, j + 1))
    return heapq.heappop(heap)[0]


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Heap pop K (BEST)", kth_smallest_1),
        ("Way 2: Binary search cnt", kth_smallest_2),
        ("Way 3: Sort all", kth_smallest_3),
        ("Way 4: Heap visited", kth_smallest_4),
        ("Way 5: nsmallest", kth_smallest_5),
        ("Way 6: Binary srch bisect", kth_smallest_6),
        ("Way 7: heapq.merge", kth_smallest_7),
        ("Way 8: Class OOP", kth_smallest_8),
        ("Way 9: While heap", kth_smallest_9),
        ("Way 10: Final cleanest", kth_smallest_10),
    ]

    test_cases = [
        # (matrix, k, expected)
        ([[1, 5, 9], [10, 11, 13], [12, 13, 15]], 8, 13),
        ([[-5]], 1, -5),
        ([[1, 2], [3, 4]], 3, 3),
        ([[1, 2], [1, 3]], 4, 3),
        ([[1, 2], [3, 4]], 1, 1),
        ([[1, 2], [3, 4]], 4, 4),
        ([[1, 3, 5], [2, 4, 6], [7, 8, 9]], 5, 5),
    ]

    print("=" * 70)
    print("KTH SMALLEST IN SORTED MATRIX - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/kth-smallest-element-in-a-sorted-matrix")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for matrix, k, expected in test_cases:
            try:
                matrix_copy = [list(row) for row in matrix]
                result = func(matrix_copy, k)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: matrix={matrix}, k={k}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: matrix={matrix}, k={k}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
