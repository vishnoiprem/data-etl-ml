"""Find Median from Data Stream — two heaps.

Time:  O(log n) per addNum
Space: O(n)
"""

import heapq


class MedianFinder:
    """Maintains a running median with a max-heap (low) and min-heap (high)."""

    def __init__(self):
        self.low = []   # max-heap (negated)
        self.high = []  # min-heap

    def add_num(self, num):
        # Add to the right side, then re-balance sizes.
        if not self.low or num <= -self.low[0]:
            heapq.heappush(self.low, -num)
        else:
            heapq.heappush(self.high, num)
        # Keep low one larger (or equal) — so we can peek the median.
        if len(self.low) > len(self.high) + 1:
            heapq.heappush(self.high, -heapq.heappop(self.low))
        elif len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def find_median(self):
        if len(self.low) > len(self.high):
            return -self.low[0]
        return (-self.low[0] + self.high[0]) / 2


def solve_median_stream(operations):
    """Run a list of operations and return find_median results in order."""
    out = []
    finder = None
    for op in operations:
        if op[0] == "MedianFinder":
            finder = MedianFinder()
        elif op[0] == "addNum":
            finder.add_num(op[1])
        elif op[0] == "findMedian":
            out.append(finder.find_median())
    return out


if __name__ == "__main__":
    ops = [
        ("MedianFinder",),
        ("addNum", 1),
        ("addNum", 2),
        ("findMedian",),
        ("addNum", 3),
        ("findMedian",),
    ]
    print(solve_median_stream(ops))  # [1.5, 2.0]
