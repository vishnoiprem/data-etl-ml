"""
Introduction to Heaps - 10 Ways
Beginner | 15 min

Heaps are complete binary trees satisfying the heap property:
- Min-heap: parent <= children. Top is minimum.
- Max-heap: parent >= children. Top is maximum.

Common operations:
- push / heappush: O(log n)
- pop / heappop: O(log n)
- peek [0]: O(1)
- heapify: O(n)

Python's heapq is a min-heap. For max-heap, negate values.

This file demonstrates 10 ways to implement a heap and solve classic
heap-based interview problems.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/introduction-to-heaps

Examples:
    min_heap = [1, 3, 5, 7, 9]
    heapq.heappush(min_heap, 0)  # [0, 3, 5, 7, 9, 1]
    heapq.heappop(min_heap)       # returns 0
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT HEAPS:

1. WHAT IS A HEAP?
   "A complete binary tree where every parent is <= (min-heap) or >=
   (max-heap) its children. Always the smallest (or largest) element is
   at the root."

2. WHY HEAPS?
   "Get the smallest/largest element in O(1).
    Insert/remove in O(log n).
    Perfect for: top-K, sliding window median, k-way merge,
    priority scheduling, Dijkstra."

3. PYTHON'S heapq:
   "heapq is a MIN-heap. Use heappush, heappop, heapify, nlargest,
   nsmallest. For max-heap, store -value or wrap in a tuple."

4. WHEN TO USE:
   - Top K largest/smallest: heapify + nlargest/nsmallest
   - K-th element: heap with size k
   - Median from stream: two heaps (max-heap for lower, min-heap for upper)
   - Merge K sorted lists: k-way merge with heap
   - Schedule by priority: push (priority, n) pairs

5. COMMON TRAPS:
   - Confusing min/max: heapq is min-heap.
   - Comparing tuples: heapq compares element 0 first, then 1, etc.
   - Heapify requires a list; it modifies in-place.

6. COMPLEXITY:
   +----------+--------+--------+
   | Operation| Time   | Notes  |
   +----------+--------+--------+
   | push     | O(log n)        |
   | pop      | O(log n)        |
   | peek     | O(1)            |
   | heapify  | O(n)            |
   | nlargest | O(n log k)      |
   +----------+--------+--------+
"""


# =============================================================================
# WAY 1: Python heapq (BEST)
# =============================================================================
def find_kth_smallest_1(nums, k):
    """Use heapq.nlargest (or build a heap of size k)."""
    if not nums or k < 1 or k > len(nums):
        return None
    # heapq.nsmallest(k, nums)[-1] gives the k-th smallest
    return heapq.nsmallest(k, nums)[-1]


# =============================================================================
# WAY 2: Sort + index
# =============================================================================
def find_kth_smallest_2(nums, k):
    """Sort and pick k-th index."""
    return sorted(nums)[k - 1]


# =============================================================================
# WAY 3: Manual heap class (min-heap)
# =============================================================================
class MinHeap:
    """Manual min-heap implementation."""

    def __init__(self):
        self.heap = []

    def push(self, val):
        self.heap.append(val)
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        if not self.heap:
            return None
        top = self.heap[0]
        last = self.heap.pop()
        if self.heap:
            self.heap[0] = last
            self._sift_down(0)
        return top

    def peek(self):
        return self.heap[0] if self.heap else None

    def _sift_up(self, i):
        while i > 0:
            parent = (i - 1) // 2
            if self.heap[parent] > self.heap[i]:
                self.heap[parent], self.heap[i] = self.heap[i], self.heap[parent]
                i = parent
            else:
                break

    def _sift_down(self, i):
        n = len(self.heap)
        while 2 * i + 1 < n:
            left = 2 * i + 1
            right = 2 * i + 2
            smallest = i
            if left < n and self.heap[left] < self.heap[smallest]:
                smallest = left
            if right < n and self.heap[right] < self.heap[smallest]:
                smallest = right
            if smallest != i:
                self.heap[i], self.heap[smallest] = self.heap[smallest], self.heap[i]
                i = smallest
            else:
                break

    def __len__(self):
        return len(self.heap)


def find_kth_smallest_3(nums, k):
    """Use manual MinHeap class."""
    h = MinHeap()
    for v in nums:
        h.push(v)
    result = None
    for _ in range(k):
        result = h.pop()
    return result


# =============================================================================
# WAY 4: Max-heap via negation
# =============================================================================
def find_kth_smallest_4(nums, k):
    """Use negation for max-heap trick.
    Pop k-1 largest -> remaining top is k-th LARGEST.
    Negate: k-th largest of nums == k-th smallest of nums viewed as positives.
    Actually: pop k-1 from max-heap -> top is k-th LARGEST.
    For k-th SMALLEST: use min-heap (just heapify).
    """
    # Use min-heap; pop k-1 smallest; top is k-th smallest
    heap = list(nums)
    heapq.heapify(heap)
    for _ in range(k - 1):
        heapq.heappop(heap)
    return heap[0]


# =============================================================================
# WAY 5: Heap of size k (efficient for k << n)
# =============================================================================
def find_kth_smallest_5(nums, k):
    """Maintain max-heap of size k."""
    heap = []
    for v in nums:
        if len(heap) < k:
            heapq.heappush(heap, -v)
        elif -heap[0] > v:
            heapq.heapreplace(heap, -v)
    return -heap[0]


# =============================================================================
# WAY 6: QuickSelect (O(n) average)
# =============================================================================
def find_kth_smallest_6(nums, k):
    """QuickSelect: average O(n), worst O(n^2)."""

    def partition(lo, hi):
        pivot = nums[hi]
        i = lo
        for j in range(lo, hi):
            if nums[j] < pivot:
                nums[i], nums[j] = nums[j], nums[i]
                i += 1
        nums[i], nums[hi] = nums[hi], nums[i]
        return i

    lo, hi = 0, len(nums) - 1
    while True:
        p = partition(lo, hi)
        if p == k - 1:
            return nums[p]
        elif p > k - 1:
            hi = p - 1
        else:
            lo = p + 1


# =============================================================================
# WAY 7: Sorted order via heapq
# =============================================================================
def find_kth_smallest_7(nums, k):
    """Push all, then pop k-1 times."""
    heap = list(nums)
    heapq.heapify(heap)
    result = None
    for _ in range(k):
        result = heapq.heappop(heap)
    return result


# =============================================================================
# WAY 8: Class-based wrapper
# =============================================================================
class KthFinder:
    """Find k-th smallest using heapq."""

    def __init__(self, nums):
        self.nums = nums

    def kth(self, k):
        return find_kth_smallest_1(self.nums, k)


def find_kth_smallest_8(nums, k):
    return KthFinder(nums).kth(k)


# =============================================================================
# WAY 9: Heap with tuple keys (for tie-breaking)
# =============================================================================
def find_kth_smallest_9(nums, k):
    """Use heapq with index for stability (tie-breaking)."""
    # Use (value, index) so heapq orders by value first; index breaks ties.
    heap = [(v, i) for i, v in enumerate(nums)]
    heapq.heapify(heap)
    for _ in range(k - 1):
        heapq.heappop(heap)
    return heap[0][0]


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def find_kth_smallest_10(nums, k):
    """
    THE ONE TO MEMORIZE.

    Use heapq.nsmallest(k, nums)[-1] — clean and idiomatic.

    Time:  O(n log k)
    Space: O(k).
    """
    return heapq.nsmallest(k, nums)[-1]


# =============================================================================
# DEMO: BASIC HEAP OPERATIONS
# =============================================================================
def demo_basic_heap():
    """Demonstrate basic heap operations."""
    # Min-heap
    h = [5, 3, 8, 1, 9]
    heapq.heapify(h)
    # h is now [1, 3, 8, 5, 9]
    heapq.heappush(h, 0)
    # h is now [0, 1, 8, 5, 9, 3]
    smallest = heapq.heappop(h)
    # smallest = 0; h = [1, 3, 8, 5, 9]

    # Max-heap via negation
    h = [-5, -3, -8, -1, -9]
    heapq.heapify(h)
    largest = -heapq.heappop(h)
    # largest = 9

    return smallest, largest


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: heapq.nsmallest (BEST)", find_kth_smallest_1),
        ("Way 2: Sort + index", find_kth_smallest_2),
        ("Way 3: Manual MinHeap", find_kth_smallest_3),
        ("Way 4: Max-heap negation", find_kth_smallest_4),
        ("Way 5: Size-k heap", find_kth_smallest_5),
        ("Way 6: QuickSelect", find_kth_smallest_6),
        ("Way 7: Heapify + pop k-1", find_kth_smallest_7),
        ("Way 8: Class OOP", find_kth_smallest_8),
        ("Way 9: Heap with tuple", find_kth_smallest_9),
        ("Way 10: Final cleanest", find_kth_smallest_10),
    ]

    test_cases = [
        # (nums, k, expected)
        ([5, 3, 8, 1, 9], 1, 1),
        ([5, 3, 8, 1, 9], 3, 5),
        ([5, 3, 8, 1, 9], 5, 9),
        ([1], 1, 1),
        ([7, 4, 6, 3, 9, 8], 3, 6),
        ([10, 20, 30, 40, 50], 1, 10),
        ([3, 3, 3, 3], 2, 3),
        ([5, -1, 4, 2, 8], 2, 2),
    ]

    print("=" * 70)
    print("INTRODUCTION TO HEAPS - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/introduction-to-heaps")
    print("=" * 70)

    demo_result = demo_basic_heap()
    print(f"  Demo: smallest={demo_result[0]}, largest={demo_result[1]}")

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, k, expected in test_cases:
            try:
                # copy to avoid mutating test data for non-pure implementations
                nums_copy = list(nums)
                result = func(nums_copy, k)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, k={k}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: nums={nums}, k={k}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)