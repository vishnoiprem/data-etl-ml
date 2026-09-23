"""
Find Median from Data Stream - 10 Ways
Hard | 20 min
https://www.educative.io/courses/grokking-coding-interview-in-python/find-median-from-data-stream

The median is the middle value in an ordered integer list. If the size of
the list is even, there is no middle value; the median is the mean of the
two middle values.

Implement the MedianFinder class:
- MedianFinder() initializes the object.
- void addNum(int num) adds the integer num to the data structure.
- double findMedian() returns the median of current data stream.

KEY INSIGHT:
Maintain TWO heaps:
- A max-heap for the LOWER half (top is the largest of lower half).
- A min-heap for the UPPER half (top is the smallest of upper half).
Keep them balanced: sizes differ by at most 1. The median is then either
the top of the larger heap (odd count) or the average of both tops (even).

Examples:
    addNum(1), addNum(2) -> findMedian = 1.5
    addNum(3) -> findMedian = 2.0

Constraints:
- -10^5 <= num <= 10^5
- At most 5 * 10^4 calls to addNum/findMedian
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT FIND MEDIAN FROM DATA STREAM:

1. WHAT IS THE PROBLEM?
   "Maintain a stream of numbers and report the median at any point."

2. WHY TWO HEAPS?
   "Sorting on every findMedian is O(n log n). With two heaps, addNum and
   findMedian are both O(log n) (addNum) and O(1) (findMedian).
    - max-heap 'small': holds the lower half; top is the largest of lower.
    - min-heap 'large': holds the upper half; top is the smallest of upper.
    - Invariant: len(small) >= len(large); len(small) <= len(large) + 1.
    - Median: top of small (odd total) or avg of tops (even total)."

3. INVARIANT DETAILS:
   "After every addNum, rebalance so sizes differ by at most 1.
    Convention: small has one more element than large if total is odd.
    So median = -small[0] when odd; avg(-small[0], large[0]) when even."

4. ADD LOGIC (THE ONE TO MEMORIZE):
   "1. heappush(-num, small).
    2. heappush(-small[0], large).  # ensure every element of small <= every element of large
    3. If len(small) < len(large): heappush(-heappop(large), small).
    4. If len(small) > len(large) + 1: heappush(-heappop(small), large).
    Simpler version (always push to small, then rebalance):
      heappush(small, -num)
      heappush(large, -heappop(small))   # move largest of small to large
      if len(small) < len(large):
          heappush(small, -heappop(large))  # keep small >= large"

5. WHEN TO USE:
   - Streaming median / quantile.
   - Sliding window median (LC 480).
   - Running percentiles.

6. COMMON TRAPS:
   - Forgetting to negate for max-heap (heapq is min-heap).
   - Off-by-one in size invariant.
   - Forgetting to handle empty case in findMedian.

7. COMPLEXITY:
   +----------------+--------+--------+
   | Operation      | Time   | Notes  |
   +----------------+--------+--------+
   | addNum         | O(log n)        |
   | findMedian     | O(1)            |
   | Space          | O(n)            |
   +----------------+--------+--------+
"""


# =============================================================================
# WAY 1: Two heaps, rebalance by size (BEST - Memorize!)
# =============================================================================
class MedianFinder_1:
    """Maintain small (max-heap) and large (min-heap)."""

    def __init__(self):
        self.small = []  # max-heap via negation
        self.large = []  # min-heap

    def addNum(self, num):
        heapq.heappush(self.small, -num)
        # Every element in small must be <= every element in large
        if self.large and -self.small[0] > self.large[0]:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        # Rebalance: small has equal or one more element
        if len(self.small) < len(self.large):
            heapq.heappush(self.small, -heapq.heappop(self.large))
        elif len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))

    def findMedian(self):
        if not self.small:
            return 0.0
        if len(self.small) > len(self.large):
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2.0


# =============================================================================
# WAY 2: Always insert to small then move top
# =============================================================================
class MedianFinder_2:
    def __init__(self):
        self.small = []
        self.large = []

    def addNum(self, num):
        heapq.heappush(self.small, -num)
        heapq.heappush(self.large, -heapq.heappop(self.small))
        if len(self.small) < len(self.large):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def findMedian(self):
        if not self.small:
            return 0.0
        if len(self.small) > len(self.large):
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2.0


# =============================================================================
# WAY 3: bisect + manual balance (lazy SortedList alternative)
# =============================================================================
class MedianFinder_3:
    """Use bisect.insort to maintain sorted list, with two top-of-half pointers."""

    def __init__(self):
        self.data = []

    def addNum(self, num):
        import bisect
        bisect.insort(self.data, num)

    def findMedian(self):
        n = len(self.data)
        if n == 0:
            return 0.0
        if n % 2 == 1:
            return float(self.data[n // 2])
        return (self.data[n // 2 - 1] + self.data[n // 2]) / 2.0


# =============================================================================
# WAY 4: Sorted list (plain Python list with bisect.insort)
# =============================================================================
import bisect


class MedianFinder_4:
    def __init__(self):
        self.data = []

    def addNum(self, num):
        bisect.insort(self.data, num)

    def findMedian(self):
        n = len(self.data)
        if n == 0:
            return 0.0
        if n % 2 == 1:
            return float(self.data[n // 2])
        return (self.data[n // 2 - 1] + self.data[n // 2]) / 2.0


# =============================================================================
# WAY 5: Class-based wrapper around Way 2
# =============================================================================
class _TwoHeapCore_5:
    def __init__(self):
        self.small = []
        self.large = []

    def add(self, num):
        heapq.heappush(self.small, -num)
        if self.large and -self.small[0] > self.large[0]:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        if len(self.small) < len(self.large):
            heapq.heappush(self.small, -heapq.heappop(self.large))
        elif len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))

    def median(self):
        if not self.small:
            return 0.0
        if len(self.small) > len(self.large):
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2.0


class MedianFinder_5:
    def __init__(self):
        self.core = _TwoHeapCore_5()

    def addNum(self, num):
        self.core.add(num)

    def findMedian(self):
        return self.core.median()


# =============================================================================
# WAY 6: Lazy deletion with multiset
# =============================================================================
class MedianFinder_6:
    def __init__(self):
        self.small = []  # max-heap
        self.large = []  # min-heap
        self.delayed = {}  # num -> count to delete

    def _prune(self, heap):
        while heap and self.delayed.get(-heap[0] if heap is self.small else heap[0], 0) > 0:
            top = -heapq.heappop(heap) if heap is self.small else heapq.heappop(heap)
            self.delayed[top] -= 1
            if self.delayed[top] == 0:
                del self.delayed[top]

    def addNum(self, num):
        if not self.small or num <= -self.small[0]:
            heapq.heappush(self.small, -num)
        else:
            heapq.heappush(self.large, num)
        # Rebalance
        if len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        elif len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def findMedian(self):
        if not self.small:
            return 0.0
        if len(self.small) > len(self.large):
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2.0


# =============================================================================
# WAY 7: Insertion into correct heap directly
# =============================================================================
class MedianFinder_7:
    def __init__(self):
        self.small = []  # max-heap
        self.large = []  # min-heap

    def addNum(self, num):
        # Choose heap based on num vs tops
        if not self.small or num <= -self.small[0]:
            heapq.heappush(self.small, -num)
        else:
            heapq.heappush(self.large, num)
        # Rebalance
        if len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        elif len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def findMedian(self):
        if not self.small:
            return 0.0
        if len(self.small) > len(self.large):
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2.0


# =============================================================================
# WAY 8: Using heapq for max-heap; one helper to balance
# =============================================================================
class MedianFinder_8:
    def __init__(self):
        self.small = []
        self.large = []

    def addNum(self, num):
        heapq.heappush(self.small, -num)
        # Move the largest of small to large if it exceeds large's min
        if self.large and -self.small[0] > self.large[0]:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        # Balance sizes
        if len(self.small) - len(self.large) > 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        elif len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def findMedian(self):
        if not self.small:
            return 0.0
        if len(self.small) > len(self.large):
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2.0


# =============================================================================
# WAY 9: Always insert to small first, then balance
# =============================================================================
class MedianFinder_9:
    def __init__(self):
        self.small = []
        self.large = []

    def addNum(self, num):
        heapq.heappush(self.small, -num)
        heapq.heappush(self.large, -heapq.heappop(self.small))
        if len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def findMedian(self):
        if not self.small:
            return 0.0
        if len(self.small) > len(self.large):
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2.0


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
class MedianFinder:
    """
    THE ONE TO MEMORIZE.

    Invariant:
      - small (max-heap) holds the lower half; large (min-heap) holds upper half.
      - len(small) >= len(large); difference <= 1.
      - Every small element <= every large element.

    addNum(num):
      1. heappush(small, -num).
      2. If large and -small[0] > large[0]: heappush(large, -heappop(small)).
      3. If len(small) < len(large): heappush(small, -heappop(large)).
      4. If len(small) > len(large) + 1: heappush(large, -heappop(small)).

    findMedian():
      - If empty: 0.0.
      - If odd total: -small[0].
      - If even: avg of -small[0] and large[0].

    Time:  addNum O(log n), findMedian O(1).
    Space: O(n).
    """

    def __init__(self):
        self.small = []  # max-heap via negation
        self.large = []  # min-heap

    def addNum(self, num):
        heapq.heappush(self.small, -num)
        if self.large and -self.small[0] > self.large[0]:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        if len(self.small) < len(self.large):
            heapq.heappush(self.small, -heapq.heappop(self.large))
        elif len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))

    def findMedian(self):
        if not self.small:
            return 0.0
        if len(self.small) > len(self.large):
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2.0


# =============================================================================
# TEST
# =============================================================================
def run_tests():
    implementations = [
        ("Way 1: Two heaps (BEST)", MedianFinder_1),
        ("Way 2: Insert small then move", MedianFinder_2),
        ("Way 3: SortedList", MedianFinder_3),
        ("Way 4: bisect.insort", MedianFinder_4),
        ("Way 5: Class wrapper", MedianFinder_5),
        ("Way 6: Lazy deletion", MedianFinder_6),
        ("Way 7: Choose heap", MedianFinder_7),
        ("Way 8: Balance helper", MedianFinder_8),
        ("Way 9: Always small first", MedianFinder_9),
        ("Way 10: Final cleanest", MedianFinder),
    ]

    # Each test: (sequence of adds, expected medians after each step)
    test_cases = [
        ([1, 2, 3], [1.0, 1.5, 2.0]),
        ([6, 10, 2, 6, 5, 0, 6, 3, 1, 0, 0], [6.0, 8.0, 6.0, 6.0, 6.0, 5.5, 6.0, 5.5, 5.0, 4.0, 3.0]),
        ([1], [1.0]),
        ([2, 3], [2.0, 2.5]),
        ([-1, -2, -3, -4], [-1.0, -1.5, -2.0, -2.5]),
        ([0, 0, 0, 0], [0.0, 0.0, 0.0, 0.0]),
        ([1, 2], [1.0, 1.5]),
        ([5, 4, 3, 2, 1], [5.0, 4.5, 4.0, 3.5, 3.0]),
    ]

    print("=" * 70)
    print("FIND MEDIAN FROM DATA STREAM - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, cls in implementations:
        passed = 0
        failed = 0
        for nums, expected_meds in test_cases:
            try:
                mf = cls()
                ok = True
                for i, num in enumerate(nums):
                    mf.addNum(num)
                    got = mf.findMedian()
                    exp = expected_meds[i]
                    # Use tolerance for floats
                    if abs(got - exp) > 1e-9:
                        ok = False
                        break
                if ok:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] nums={nums} expected={expected_meds[-1]} got={got}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] nums={nums}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
