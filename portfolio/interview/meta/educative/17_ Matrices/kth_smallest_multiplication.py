"""
Kth Smallest Number in Multiplication Table
Hard | 40 min

Given an m x n multiplication table where mat[i][j] = i * j (1-indexed),
find the kth smallest number in the table.

Examples:
    m=3, n=3, k=5:
    Table:
        1 2 3
        2 4 6
        3 6 9
    Sorted: 1, 2, 2, 3, 3, 4, 6, 6, 9
    -> 5th smallest = 3

    m=4, n=5, k=8:
    1  2  3  4  5
    2  4  6  8  10
    3  6  9  12 15
    4  8  12 16 20
    -> 8th smallest = 4 (3 fours appear: rows 1, 2, 4)

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/kth-smallest-number-in-multiplication-table

Constraints:
- 1 <= m, n <= 30000
- 1 <= k <= m * n
"""


# =============================================================================
# WAY 1: Binary Search on value (BEST - Memorize!)
# =============================================================================
def findKthNumber_1(m, n, k):
    """
    KEY INSIGHT: For a given value x, count how many elements in the table
    are <= x. Each row i has values i*1, i*2, ..., i*n. The count of values
    <= x in row i is min(x // i, n).

    Binary search on x:
    - low = 1, high = m * n
    - mid = (low + high) // 2
    - If count(mid) >= k, the answer is <= mid, search left
    - Else, answer > mid, search right

    Time:  O((m+n) * log(m*n))
    Space: O(1)
    """
    def count_leq(x):
        # Count of values <= x in the table
        total = 0
        for i in range(1, m + 1):
            total += min(x // i, n)
        return total

    low, high = 1, m * n
    while low < high:
        mid = (low + high) // 2
        if count_leq(mid) >= k:
            high = mid
        else:
            low = mid + 1
    return low


# =============================================================================
# WAY 2: Verbose version with explicit names
# =============================================================================
def findKthNumber_2(m, n, k):
    """Same as Way 1 but more readable."""
    def count_smaller_or_equal(x):
        count = 0
        for row in range(1, m + 1):
            # In row `row`, values are row*1, row*2, ..., row*n
            # Count of values <= x is min(x // row, n)
            count += min(x // row, n)
        return count

    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if count_smaller_or_equal(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 3: Swap m and n if m > n for efficiency
# =============================================================================
def findKthNumber_3(m, n, k):
    """
    Optimization: if m > n, swap them. Then iterate over the smaller dimension
    for the count function. Same complexity but smaller constant.
    """
    if m > n:
        m, n = n, m

    def count(x):
        total = 0
        for i in range(1, m + 1):
            total += min(x // i, n)
        return total

    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if count(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 4: Build actual table and sort (only for small m, n)
# =============================================================================
def findKthNumber_4(m, n, k):
    """
    Brute force: build the table, sort, return kth.
    O(m*n*log(m*n)) time, O(m*n) space.
    Only feasible for small m, n.
    """
    if m * n > 10**6:
        # Fall back to binary search for large inputs
        return findKthNumber_1(m, n, k)
    table = []
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            table.append(i * j)
    table.sort()
    return table[k - 1]


# =============================================================================
# WAY 5: Use heap (lazy expansion)
# =============================================================================
def findKthNumber_5(m, n, k):
    """
    Heap-based: start with row 1, then expand. Pop k times.
    Avoid duplicates with visited set.
    """
    import heapq
    if m > n:
        m, n = n, m  # Optimize by handling smaller dimension first

    visited = set()
    heap = [(1, 1, 1)]  # (value, row, col)
    visited.add((1, 1))
    result = 0
    for _ in range(k):
        result, r, c = heapq.heappop(heap)
        # Next in row: (r, c+1)
        if c + 1 <= n and (r, c + 1) not in visited:
            heapq.heappush(heap, (r * (c + 1), r, c + 1))
            visited.add((r, c + 1))
        # Next in col: (r+1, c)
        if r + 1 <= m and (r + 1, c) not in visited:
            heapq.heappush(heap, ((r + 1) * c, r + 1, c))
            visited.add((r + 1, c))
    return result


# =============================================================================
# WAY 6: Binary search with optimized counting
# =============================================================================
def findKthNumber_6(m, n, k):
    """
    Same as Way 1 but more efficient counting using the property that
    each row is an arithmetic progression.
    """
    if m > n:
        m, n = n, m

    def count(x):
        # For each row i, count elements <= x in that row
        # Row i has values i, 2i, 3i, ..., ni
        # Count = min(x // i, n)
        total = 0
        for i in range(1, m + 1):
            total += min(x // i, n)
        return total

    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if count(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 7: Use divergence from naive
# =============================================================================
def findKthNumber_7(m, n, k):
    """Same binary search approach."""
    if m > n:
        m, n = n, m
    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        cnt = sum(min(mid // i, n) for i in range(1, m + 1))
        if cnt >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 8: Use list comprehension for counting
# =============================================================================
def findKthNumber_8(m, n, k):
    """Pythonic counting with list comprehension."""
    if m > n:
        m, n = n, m
    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        cnt = sum([min(mid // i, n) for i in range(1, m + 1)])
        if cnt >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 9: With edge case handling
# =============================================================================
def findKthNumber_9(m, n, k):
    """With explicit edge cases."""
    if k == 1:
        return 1  # smallest is always 1
    if k == m * n:
        return m * n  # largest is m*n

    if m > n:
        m, n = n, m

    def count(x):
        return sum(min(x // i, n) for i in range(1, m + 1))

    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if count(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 10: Binary search with bisect-like behavior
# =============================================================================
def findKthNumber_10(m, n, k):
    """Use a more explicit binary search template."""
    if m > n:
        m, n = n, m

    def count_le(x):
        result = 0
        for i in range(1, m + 1):
            if x // i >= n:
                result += n
            else:
                result += x // i
        return result

    left, right = 1, m * n
    while left < right:
        mid = (left + right) // 2
        if count_le(mid) >= k:
            right = mid
        else:
            left = mid + 1
    return left


# =============================================================================
# WAY 11: Build full table for small inputs (baseline)
# =============================================================================
def findKthNumber_11(m, n, k):
    """Brute force approach. Useful as a baseline / verification."""
    table = []
    for i in range(1, m + 1):
        row = []
        for j in range(1, n + 1):
            row.append(i * j)
        table.append(row)
    # Flatten and sort
    flat = [v for row in table for v in row]
    flat.sort()
    return flat[k - 1]


# =============================================================================
# WAY 12: numpy for small inputs
# =============================================================================
def findKthNumber_12(m, n, k):
    """Use numpy for fast table generation and sorting."""
    try:
        import numpy as np
        if m * n > 10**6:
            return findKthNumber_1(m, n, k)
        i = np.arange(1, m + 1).reshape(-1, 1)
        j = np.arange(1, n + 1).reshape(1, -1)
        table = i * j
        flat = np.sort(table.flatten())
        return int(flat[k - 1])
    except ImportError:
        return findKthNumber_1(m, n, k)


# =============================================================================
# WAY 13: Heap approach (alternative style)
# =============================================================================
def findKthNumber_13(m, n, k):
    """
    Heap-based approach: maintain a min-heap of (value, row).
    Pop k times to get kth smallest.

    Note: This is O(k log k) but with deduplication it can be O(k log m).
    """
    import heapq
    if m > n:
        m, n = n, m

    # Initial: (1*1, 1, 1)
    heap = [(1, 1, 1)]
    seen = {(1, 1)}
    for _ in range(k):
        val, r, c = heapq.heappop(heap)
        # Push (r, c+1) if not seen
        if c + 1 <= n and (r, c + 1) not in seen:
            heapq.heappush(heap, (r * (c + 1), r, c + 1))
            seen.add((r, c + 1))
        # Push (r+1, c) if not seen
        if r + 1 <= m and (r + 1, c) not in seen:
            heapq.heappush(heap, ((r + 1) * c, r + 1, c))
            seen.add((r + 1, c))
    return val


# =============================================================================
# WAY 14: Inverted binary search (right-exclusive)
# =============================================================================
def findKthNumber_14(m, n, k):
    """Binary search with right-exclusive [low, high) interval."""
    if m > n:
        m, n = n, m

    def count(x):
        return sum(min(x // i, n) for i in range(1, m + 1))

    lo, hi = 1, m * n + 1
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if count(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 15: Binary search with while-true loop
# =============================================================================
def findKthNumber_15(m, n, k):
    """Use while-true for clarity."""
    if m > n:
        m, n = n, m

    def count(x):
        return sum(min(x // i, n) for i in range(1, m + 1))

    lo, hi = 1, m * n
    while True:
        mid = (lo + hi) // 2
        cnt = count(mid)
        if cnt >= k:
            if mid == lo:
                return lo
            hi = mid
        else:
            lo = mid + 1


# =============================================================================
# WAY 16: Binary search returning the smallest value with count >= k
# =============================================================================
def findKthNumber_16(m, n, k):
    """Classic binary search for smallest x with count(x) >= k."""
    if m > n:
        m, n = n, m

    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        # Count of values <= mid
        cnt = 0
        for i in range(1, m + 1):
            cnt += min(mid // i, n)
        if cnt >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 17: Class-based OOP
# =============================================================================
class KthSmallestFinder:
    def __init__(self, m, n, k):
        self.m = m
        self.n = n
        self.k = k

    def find(self):
        if self.m > self.n:
            self.m, self.n = self.n, self.m
        return self._binary_search()

    def _count_le(self, x):
        return sum(min(x // i, self.n) for i in range(1, self.m + 1))

    def _binary_search(self):
        lo, hi = 1, self.m * self.n
        while lo < hi:
            mid = (lo + hi) // 2
            if self._count_le(mid) >= self.k:
                hi = mid
            else:
                lo = mid + 1
        return lo


def findKthNumber_17(m, n, k):
    """Class-based version."""
    return KthSmallestFinder(m, n, k).find()


# =============================================================================
# WAY 18: With explicit edge case tests
# =============================================================================
def findKthNumber_18(m, n, k):
    """Comprehensive version with edge cases."""
    if k < 1 or k > m * n:
        return -1

    if m > n:
        m, n = n, m

    def count_le(x):
        total = 0
        for i in range(1, m + 1):
            # In row i, values are i, 2i, 3i, ..., ni
            total += min(x // i, n)
        return total

    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 19: Most concise
# =============================================================================
def findKthNumber_19(m, n, k):
    """Concise one-liner-ish."""
    if m > n:
        m, n = n, m
    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if sum(min(mid // i, n) for i in range(1, m + 1)) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def findKthNumber_20(m, n, k):
    """
    Final clean version.
    Binary search on the ANSWER value (not index).
    For each candidate x, count how many values in table are <= x.
    Find smallest x such that count >= k.

    Time:  O((m+n) * log(m*n))
    Space: O(1)
    """
    if m > n:
        m, n = n, m

    def count_leq(x):
        # For each row i, count values <= x: min(x // i, n)
        return sum(min(x // i, n) for i in range(1, m + 1))

    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if count_leq(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the kth smallest number in an m x n multiplication table
where mat[i][j] = i * j (1-indexed)."

Key Insight:
"Two approaches:
1. BINARY SEARCH on the VALUE (not index): for each candidate x, count
   how many elements in the table are <= x. Find smallest x with count >= k.
2. HEAP: start from (1,1), expand, pop k times.

Binary search is faster: O((m+n) log(mn)) vs heap's O(k log m)."

Counting function:
"For a candidate x, how many values in the table are <= x?
Each row i has values i*1, i*2, ..., i*n.
Count in row i = min(x // i, n).
Total count = sum over all rows."

Algorithm (Binary Search):
"1. lo = 1, hi = m*n. (smallest and largest possible values)
2. While lo < hi:
   a. mid = (lo + hi) // 2
   b. cnt = sum(min(mid // i, n) for i in 1..m)
   c. If cnt >= k: answer <= mid, hi = mid.
   d. Else: answer > mid, lo = mid + 1.
3. Return lo."

Why binary search works:
"The 'count' function is MONOTONICALLY INCREASING in x:
- count(0) = 0, count(m*n) = m*n.
- count(x) >= count(y) for x >= y.

So we can binary search for the smallest x with count(x) >= k."

Edge cases:
- k = 1: return 1.
- k = m*n: return m*n.
- m = 1 or n = 1: linear multiplication, easy.
- m or n very large (up to 30000): use counting approach.

Complexity:
+-----------+------------------+--------+
| Approach  | Time             | Space  |
+-----------+------------------+--------+
| Binary    | O((m+n) log(mn)) | O(1)   |
| Heap      | O(k log m)       | O(m)   |
| Brute     | O(mn log mn)     | O(mn)  |
+-----------+------------------+--------+

KEY TRICK:
The counting function. For each row i, the count of values <= x
is min(x // i, n). This is because row i is the arithmetic sequence
i, 2i, 3i, ..., ni.

OPTIMIZATION: Swap m and n so we iterate over the smaller dimension.
Same complexity but smaller constant factor.

RELATIONSHIP TO OTHER PROBLEMS:
- Search a 2D Matrix (LC 74): Different - sorted matrix.
- Kth Smallest Element in Sorted Matrix (LC 378): Binary search similar.
- Find K Pairs with Smallest Sums (LC 373): Heap-based.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Binary search on value (BEST)", findKthNumber_1),
        ("Way 2: Verbose", findKthNumber_2),
        ("Way 3: Swap dimensions", findKthNumber_3),
        ("Way 4: Build and sort", findKthNumber_4),
        ("Way 5: Heap", findKthNumber_5),
        ("Way 6: Optimized counting", findKthNumber_6),
        ("Way 7: Generator sum", findKthNumber_7),
        ("Way 8: List comp", findKthNumber_8),
        ("Way 9: Edge cases", findKthNumber_9),
        ("Way 10: Explicit count", findKthNumber_10),
        ("Way 11: Build full table", findKthNumber_11),
        ("Way 12: Numpy", findKthNumber_12),
        ("Way 13: Heap alt", findKthNumber_13),
        ("Way 14: Right-exclusive", findKthNumber_14),
        ("Way 15: While-true", findKthNumber_15),
        ("Way 16: Classic", findKthNumber_16),
        ("Way 17: Class-based", findKthNumber_17),
        ("Way 18: Comprehensive", findKthNumber_18),
        ("Way 19: Most concise", findKthNumber_19),
        ("Way 20: Final cleanest", findKthNumber_20),
    ]

    test_cases = [
        # (m, n, k, expected)
        (3, 3, 5, 3),       # 1,2,2,3,3,4,6,6,9 -> 5th = 3
        (4, 5, 8, 4),       # 8th = 4 (verified)
        (2, 3, 6, 6),       # Table: 1,2,3,2,4,6 sorted = 1,2,2,3,4,6 -> 6th = 6
        (1, 1, 1, 1),
        (1, 5, 3, 3),       # 1,2,3,4,5 -> 3rd = 3
        (5, 1, 3, 3),       # 1,2,3,4,5 -> 3rd = 3
        (3, 3, 1, 1),       # 1st = 1
        (3, 3, 9, 9),       # 9th = 9 (largest)
        (2, 2, 1, 1),       # 1,2,2,4 -> 1st = 1
        (2, 2, 2, 2),
        (2, 2, 3, 2),
        (2, 2, 4, 4),
        # 10x10: 50th element of multiplication table
        # Values <= 16: count rows
        # Need to verify with brute force
        (10, 10, 50, 24),
    ]

    print("=" * 70)
    print("KTH SMALLEST NUMBER IN MULTIPLICATION TABLE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/kth-smallest-number-in-multiplication-table")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for m, n, k, expected in test_cases:
            try:
                result = func(m, n, k)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: m={m}, n={n}, k={k} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on m={m}, n={n}, k={k} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)