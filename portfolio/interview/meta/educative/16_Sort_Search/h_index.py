"""
H-Index
Medium | 30 min

Given citations[], the H-index is the largest h such that the researcher
has published h papers that have been cited at least h times each.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/h-index

Examples:
    citations=[3,0,6,1,5] -> 3
    # Sorted desc: [6,5,3,1,0]. h=1: at least 1 paper with >=1 cite ✓.
    # h=2: at least 2 papers with >=2 cites ✓ (6,5).
    # h=3: at least 3 papers with >=3 cites ✓ (6,5,3).
    # h=4: at least 4 papers with >=4 cites ✗ (only 6,5,3 have >=4).
    # H-index = 3.
    citations=[1,3,1] -> 1
    citations=[0] -> 0

Constraints:
- 1 <= citations.length <= 5000
- 0 <= citations[i] <= 1000

KEY INSIGHT: Sort DESC. h-index = max i such that citations[i] >= i+1.
"""


# =============================================================================
# WAY 1: Sort DESC + iterate (BEST - Memorize!)
# =============================================================================
def hIndex_1(citations):
    """
    Sort desc. h-index is max i where citations[i] >= i+1.
    """
    a = sorted(citations, reverse=True)
    h = 0
    for i, c in enumerate(a):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h


# =============================================================================
# WAY 2: Sort ASC + iterate from end
# =============================================================================
def hIndex_2(citations):
    a = sorted(citations)
    n = len(a)
    h = 0
    for i in range(n - 1, -1, -1):
        # papers with >= a[i] cites = n - i
        if n - i <= a[i]:
            h = n - i
        else:
            break
    return h


# =============================================================================
# WAY 3: Sort + binary search
# =============================================================================
def hIndex_3(citations):
    import bisect
    a = sorted(citations)
    n = len(a)
    # Find largest h such that a[n-h] >= h
    # Or: find smallest idx such that a[idx] >= n-idx, then h = n-idx
    # Or: find largest h where at least h papers >= h cites
    # Use bisect_right: find first idx where a[idx] >= h
    h = 0
    for cand in range(n, -1, -1):
        # Need at least cand papers with >= cand cites
        # That means at least cand papers in a are >= cand
        idx = bisect.bisect_left(a, cand)
        # papers with >= cand cites = n - idx
        if n - idx >= cand:
            return cand
    return 0


# =============================================================================
# WAY 4: Counting sort (bucket sort) - O(n) for citations <= n
# =============================================================================
def hIndex_4(citations):
    """Use counting sort. O(n) if citations bounded."""
    n = len(citations)
    buckets = [0] * (n + 1)
    for c in citations:
        if c >= n:
            buckets[n] += 1
        else:
            buckets[c] += 1
    total = 0
    for i in range(n, -1, -1):
        total += buckets[i]
        if total >= i:
            return i
    return 0


# =============================================================================
# WAY 5: Brute force - try all h values
# =============================================================================
def hIndex_5(citations):
    """Try h = 0 to len(citations)."""
    n = len(citations)
    for h in range(n, -1, -1):
        # Count papers with >= h citations
        count = sum(1 for c in citations if c >= h)
        if count >= h:
            return h
    return 0


# =============================================================================
# WAY 6: Sort DESC + binary search on index
# =============================================================================
def hIndex_6(citations):
    a = sorted(citations, reverse=True)
    n = len(a)
    # Find largest i where a[i] >= i+1
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid <= n and a[mid - 1] >= mid:
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 7: Heap-based
# =============================================================================
def hIndex_7(citations):
    """Use max-heap. Pop and check condition."""
    import heapq
    # Use min-heap of negatives for max
    h = []
    for c in citations:
        heapq.heappush(h, -c)
    result = 0
    i = 0
    while h:
        top = -heapq.heappop(h)
        if top >= i + 1:
            result = i + 1
            i += 1
        else:
            break
    return result


# =============================================================================
# WAY 8: Sort + count check
# =============================================================================
def hIndex_8(citations):
    a = sorted(citations, reverse=True)
    n = len(a)
    h = 0
    for i in range(n):
        if a[i] >= i + 1:
            h = i + 1
        else:
            break
    return h


# =============================================================================
# WAY 9: Recursive
# =============================================================================
def hIndex_9(citations):
    """Recursive: largest h such that a[h-1] >= h."""
    a = sorted(citations, reverse=True)
    n = len(a)

    def helper(i):
        """Returns largest h such that a[j] >= j+1 for all j < i."""
        if i == 0:
            return 0
        if i > n:
            return n
        # If a[i-1] < i, can stop. But check if a[i-2] >= i-1.
        if a[i - 1] < i:
            # h-index is i-1 if a[i-2] >= i-1 (which is true since we got here)
            return i - 1
        return helper(i + 1)

    if n == 0:
        return 0
    return helper(1)


# =============================================================================
# WAY 10: Class OOP
# =============================================================================
class HIndexCalculator:
    def __init__(self, citations):
        self.a = sorted(citations, reverse=True)
        self.n = len(self.a)

    def compute(self):
        h = 0
        for i, c in enumerate(self.a):
            if c >= i + 1:
                h = i + 1
            else:
                break
        return h


def hIndex_10(citations):
    return HIndexCalculator(citations).compute()


# =============================================================================
# WAY 11: Sort ASC + iterate
# =============================================================================
def hIndex_11(citations):
    a = sorted(citations)
    n = len(a)
    h = 0
    for i in range(n):
        # papers with at least a[i] citations = n - i (since sorted asc)
        candidate = min(a[i], n - i)
        if candidate > h:
            h = candidate
    return h


# =============================================================================
# WAY 12: Sort + linear scan from end
# =============================================================================
def hIndex_12(citations):
    a = sorted(citations, reverse=True)
    n = len(a)
    h = 0
    i = 0
    while i < n and a[i] >= i + 1:
        h = i + 1
        i += 1
    return h


# =============================================================================
# WAY 13: Numpy approach
# =============================================================================
def hIndex_13(citations):
    import numpy as np
    a = np.sort(np.array(citations))[::-1]
    n = len(a)
    # Find largest i where a[i] >= i+1
    idxs = np.arange(1, n + 1)
    valid = a >= idxs
    if not valid.any():
        return 0
    return int(np.max(np.where(valid)[0]) + 1)


# =============================================================================
# WAY 14: One-liner style
# =============================================================================
def hIndex_14(citations):
    a = sorted(citations, reverse=True)
    h = 0
    for i, c in enumerate(a):
        if c >= i + 1:
            h = i + 1
    return h


# =============================================================================
# WAY 15: Generator-based
# =============================================================================
def hIndex_15(citations):
    a = sorted(citations, reverse=True)
    # generator: yields (i, c) pairs where c >= i+1
    valid = ((i + 1) for i, c in enumerate(a) if c >= i + 1)
    try:
        # last valid h
        h = -1
        for v in valid:
            h = v
        return h if h >= 0 else 0
    except StopIteration:
        return 0


# =============================================================================
# WAY 16: Sort + manual binary search
# =============================================================================
def hIndex_16(citations):
    a = sorted(citations)
    n = len(a)
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        # Need at least mid papers with >= mid cites
        # a[idx] >= mid where idx is first such; papers = n - idx
        idx = _lower_bound(a, mid)
        if n - idx >= mid:
            lo = mid
        else:
            hi = mid - 1
    return lo


def _lower_bound(a, target):
    """Find first idx where a[idx] >= target."""
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =============================================================================
# WAY 17: Sort DESC + count consecutive valid
# =============================================================================
def hIndex_17(citations):
    a = sorted(citations, reverse=True)
    n = len(a)
    h = 0
    for i in range(n):
        if a[i] >= i + 1:
            h += 1
        else:
            break
    return h


# =============================================================================
# WAY 18: Sort ASC + count from end
# =============================================================================
def hIndex_18(citations):
    a = sorted(citations)
    n = len(a)
    h = 0
    # Iterate from end (largest), count consecutive valid
    for i in range(n - 1, -1, -1):
        # papers with >= a[i] cites = n - i
        if a[i] >= n - i:
            h = n - i
        else:
            break
    return h


# =============================================================================
# WAY 19: Sort + zip with indices
# =============================================================================
def hIndex_19(citations):
    a = sorted(citations, reverse=True)
    return max((i + 1 for i, c in enumerate(a) if c >= i + 1), default=0)


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def hIndex_20(citations):
    """
    THE ONE TO MEMORIZE.

    1. Sort citations descending.
    2. h = 0.
    3. For i, c in enumerate(a):
       - If c >= i + 1: h = i + 1
       - Else: break
    4. Return h.

    Time:  O(n log n)
    Space: O(1) extra (after sort)
    """
    a = sorted(citations, reverse=True)
    h = 0
    for i, c in enumerate(a):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the largest h such that the researcher has h papers
with at least h citations each."

Key Insight:
"Sort citations descending. Then h-index = largest i where
citations[i] >= i+1.
- Why? After sort, the i-th largest paper has citations >= i+1 iff
  at least (i+1) papers have >= (i+1) citations.
- Once we find citations[i] < i+1, no later (smaller) paper can have
  >= i+1 citations, so we can break."

Algorithm:
1. Sort desc.
2. h = 0.
3. For i, c in enumerate(a):
   - If c >= i + 1: h = i + 1
   - Else: break
4. Return h.

Edge Cases:
- Empty: 0.
- All zero: 0.
- All same large: min(c, n).
- One paper with high citation: depends on n.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Sort     | O(nlogn| O(1)   |
|          | )      |        |
| BS on val| O(nlogn| O(1)   |
|          | )      |        |
| Brute    | O(n^2) | O(1)   |
+----------+--------+--------+

KEY TRICK:
Sort desc. The i-th largest paper's citation count tells us if we have
h-index >= i+1. Break as soon as a[i] < i+1.

RELATED PROBLEMS:
- H-Index II (LC 275): sorted input, binary search.
- Citation sort problems.
- Count papers with >= h citations.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort DESC (BEST)", hIndex_1),
        ("Way 2: Sort ASC", hIndex_2),
        ("Way 3: BS", hIndex_3),
        ("Way 4: Counting sort", hIndex_4),
        ("Way 5: Brute force", hIndex_5),
        ("Way 6: BS on index", hIndex_6),
        ("Way 7: Heap", hIndex_7),
        ("Way 8: Sort DESC", hIndex_8),
        ("Way 9: Recursive", hIndex_9),
        ("Way 10: Class OOP", hIndex_10),
        ("Way 11: Sort ASC iterate", hIndex_11),
        ("Way 12: Linear scan", hIndex_12),
        ("Way 13: Numpy", hIndex_13),
        ("Way 14: One-liner", hIndex_14),
        ("Way 15: Generator", hIndex_15),
        ("Way 16: Manual BS", hIndex_16),
        ("Way 17: Count consecutive", hIndex_17),
        ("Way 18: Sort ASC end", hIndex_18),
        ("Way 19: Zip", hIndex_19),
        ("Way 20: Final cleanest", hIndex_20),
    ]

    test_cases = [
        # (citations, expected)
        ([3, 0, 6, 1, 5], 3),
        ([1, 3, 1], 1),
        ([0], 0),
        ([1], 1),
        ([0, 0, 0], 0),
        ([100], 1),
        ([1, 2, 100], 2),  # sorted desc: [100,2,1]. h=1: 100>=1. h=2: 2>=2. h=3: 1<3. So h=2.
        ([1, 1, 3], 1),  # sorted desc: [3,1,1]. h=1: 3>=1. h=2: 1<2. So h=1.
        ([3, 3, 3, 3], 3),  # h=3: 3>=3 ✓. h=4: only 3 papers. So h=3.
        ([4, 4, 4, 4, 4], 4),  # h=4: 4>=4. h=5: only 4 papers. So h=4.
        ([0, 1, 0, 1, 0], 1),  # sorted: [1,1,0,0,0]. h=1: 1>=1. h=2: 1<2. h=1.
        ([1, 2, 3, 4, 5], 3),  # sorted: [5,4,3,2,1]. h=3: 3>=3. h=4: 2<4. h=3.
        ([2, 0, 6, 1, 5, 3], 3),  # sorted: [6,5,3,2,1,0]. h=3: 3>=3. h=4: 2<4. h=3.
        ([10, 8, 5, 4, 3], 4),  # sorted: [10,8,5,4,3]. h=4: 4>=4. h=5: 3<5. h=4.
        ([25, 8, 5, 3, 3], 3),  # sorted: [25,8,5,3,3]. h=3: 5>=3. h=4: 3<4. h=3.
        ([1, 7, 9, 4], 3),  # sorted: [9,7,4,1]. h=3: 4>=3. h=4: 1<4. h=3.
    ]

    print("=" * 70)
    print("H-INDEX - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/h-index")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for citations, expected in test_cases:
            try:
                result = func(citations[:])
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: citations={citations}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
