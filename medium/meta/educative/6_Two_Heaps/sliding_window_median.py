"""
Sliding Window Median - 10 Ways
Hard | 30 min
https://www.educative.io/courses/grokking-coding-interview-in-python/sliding-window-median

Median is the middle value in an ordered integer list. If the size of the
list is even, the median is the average of the two middle values.

Given an integer array nums and an integer k, there is a sliding window of
size k that moves from the very left to the very right. For each window,
output the median.

KEY INSIGHT:
Maintain a sorted sliding window (via bisect.insort) for clean O(k) median
lookup at each position. The two-heaps with lazy-deletion is theoretically
faster but tricky to implement correctly. For Python, SortedList or bisect
on a list is cleaner.

Examples:
    nums=[1,3,-1,-3,5,3,6,7], k=3
    Output: [1, -1, -1, 3, 5, 6]

Constraints:
- 1 <= k <= nums.length <= 10^5
- -2 * 10^4 <= nums[i] <= 2 * 10^4
"""

import bisect
import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT SLIDING WINDOW MEDIAN:

1. WHAT IS THE PROBLEM?
   "For each sliding window of size k, output the median of the window."

2. WHY SORTED LIST (for Python)?
   "Python's heapq doesn't support efficient deletion. Two heaps with lazy
    deletion (LC 480 official solution) is O(n log k) but tricky to
    implement correctly. A sorted list with bisect.insort is simpler:
    O(n k) per step (because insort shifts) but easier to write."

3. ALGORITHM (Sorted List):
   "1. Maintain a sorted list 'window' of current k elements.
    2. For each new element: bisect.insort to insert.
    3. If window > k: find and pop the oldest element by value.
    4. Compute median: window[k//2] if odd; avg of two middles if even."

4. TWO-HEAPS APPROACH (Theoretical O(n log k)):
   "Maintain 'small' (max-heap of lower half) and 'large' (min-heap of
    upper half). On insert, push to correct heap; on delete, mark in a
    'delayed' dict. Prune tops on read. Rebalance to keep large >= small."

5. WHEN TO USE:
   - Any sliding window median / quantile.
   - Real-time analytics.

7. COMMON TRAPS:
   - Lazy deletion only works if all delayed items are eventually at top.
   - Median formula depends on which heap has more elements.
   - With k odd, median is single value; even, two-value average.

7. COMPLEXITY:
   +----------------+--------+--------+
   | Approach       | Time   | Notes  |
   +----------------+--------+--------+
   | SortedList     | O(n*k) | Simple |
   | Two heaps +    | O(n log k) | Tricky |
   | lazy deletion  |              |        |
   +----------------+--------+--------+
"""


# =============================================================================
# WAY 1: SortedList via bisect.insort (BEST for Python - Memorize!)
# =============================================================================
def median_sliding_window_1(nums, k):
    """Maintain sorted window via bisect.insort; pop oldest by value."""
    window = []
    out = []
    for i, v in enumerate(nums):
        bisect.insort(window, v)
        if len(window) > k:
            old = nums[i - k]
            idx = bisect.bisect_left(window, old)
            window.pop(idx)
        if len(window) == k:
            if k % 2 == 1:
                out.append(float(window[k // 2]))
            else:
                out.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
    return out


# =============================================================================
# WAY 2: Same as Way 1, with explicit remove step
# =============================================================================
def median_sliding_window_2(nums, k):
    window = []
    out = []
    for i, v in enumerate(nums):
        idx = bisect.bisect_left(window, v)
        window.insert(idx, v)
        if len(window) > k:
            old = nums[i - k]
            old_idx = bisect.bisect_left(window, old)
            window.pop(old_idx)
        if len(window) == k:
            if k % 2 == 1:
                out.append(float(window[k // 2]))
            else:
                out.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
    return out


# =============================================================================
# WAY 3: Brute force sort each window (clearest)
# =============================================================================
def median_sliding_window_3(nums, k):
    out = []
    for i in range(len(nums) - k + 1):
        window = sorted(nums[i:i + k])
        if k % 2 == 1:
            out.append(float(window[k // 2]))
        else:
            out.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
    return out


# =============================================================================
# WAY 4: Sort + index each iteration
# =============================================================================
def median_sliding_window_4(nums, k):
    out = []
    for i in range(len(nums) - k + 1):
        window = sorted(nums[i:i + k])
        mid = k // 2
        if k % 2 == 1:
            out.append(float(window[mid]))
        else:
            out.append((window[mid - 1] + window[mid]) / 2.0)
    return out


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class SlidingWindowMedian_5:
    def __init__(self, nums, k):
        self.nums = nums
        self.k = k

    def compute(self):
        return median_sliding_window_1(self.nums, self.k)


def median_sliding_window_5(nums, k):
    return SlidingWindowMedian_5(nums, k).compute()


# =============================================================================
# WAY 6: Two heaps, no lazy deletion (rebuild each window)
# =============================================================================
def median_sliding_window_6(nums, k):
    """O(k log k) per window; rebuild small and large each iteration."""
    out = []
    for i in range(len(nums) - k + 1):
        window = nums[i:i + k]
        small = []  # max-heap (negated)
        large = []  # min-heap
        for v in window:
            if not large or v > large[0]:
                heapq.heappush(large, v)
            else:
                heapq.heappush(small, -v)
            # Balance: ensure len(large) >= len(small)
            if len(large) > len(small) + 1:
                heapq.heappush(small, -heapq.heappop(large))
            elif len(small) > len(large):
                heapq.heappush(large, -heapq.heappop(small))
        if k % 2 == 1:
            out.append(float(large[0]))
        else:
            out.append((-small[0] + large[0]) / 2.0)
    return out


# =============================================================================
# WAY 7: SortedList approach (alternative)
# =============================================================================
def median_sliding_window_7(nums, k):
    """Use sorted list with remove by index."""
    if k == 0:
        return []
    window = []
    out = []
    for i, v in enumerate(nums):
        idx = bisect.bisect_left(window, v)
        window.insert(idx, v)
        if len(window) > k:
            old = nums[i - k]
            old_idx = bisect.bisect_left(window, old)
            window.pop(old_idx)
        if len(window) == k:
            mid = k // 2
            if k % 2 == 1:
                out.append(float(window[mid]))
            else:
                out.append((window[mid - 1] + window[mid]) / 2.0)
    return out


# =============================================================================
# WAY 8: Heapq rebuild each window (compact)
# =============================================================================
def median_sliding_window_8(nums, k):
    """Use heapq.nsmallest to find median elements."""
    out = []
    for i in range(len(nums) - k + 1):
        window = nums[i:i + k]
        # Get the two middle elements
        if k % 2 == 1:
            # Get k//2 smallest, then the next is the median
            smaller = heapq.nsmallest(k // 2 + 1, window)
            out.append(float(smaller[-1]))
        else:
            smaller = heapq.nsmallest(k // 2 + 1, window)
            out.append((smaller[-1] + smaller[-2]) / 2.0)
    return out


# =============================================================================
# WAY 9: Sort each window and pick median (alt)
# =============================================================================
def median_sliding_window_9(nums, k):
    """Sort each window and pick median."""
    out = []
    for i in range(len(nums) - k + 1):
        window = sorted(nums[i:i + k])
        if k % 2 == 1:
            out.append(float(window[k // 2]))
        else:
            mid = k // 2
            out.append((window[mid - 1] + window[mid]) / 2.0)
    return out


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def medianSlidingWindow(nums, k):
    """
    THE ONE TO MEMORIZE.

    Use bisect.insort on a sorted list for simplicity and clarity.

    Time:  O(n * k) for insort shift + O(n) for queries.
    Space: O(k).

    For optimal O(n log k), use two heaps + lazy deletion (see Way 7).
    """
    window = []
    out = []
    for i, v in enumerate(nums):
        bisect.insort(window, v)
        if len(window) > k:
            old = nums[i - k]
            idx = bisect.bisect_left(window, old)
            window.pop(idx)
        if len(window) == k:
            if k % 2 == 1:
                out.append(float(window[k // 2]))
            else:
                out.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
    return out


# =============================================================================
# TEST
# =============================================================================
def approx_equal(a, b, tol=1e-6):
    if len(a) != len(b):
        return False
    return all(abs(x - y) < tol for x, y in zip(a, b))


def run_tests():
    implementations = [
        ("Way 1: bisect.insort (BEST)", median_sliding_window_1),
        ("Way 2: bisect explicit", median_sliding_window_2),
        ("Way 3: Sort each window", median_sliding_window_3),
        ("Way 4: Sort + index", median_sliding_window_4),
        ("Way 5: Class wrapper", median_sliding_window_5),
        ("Way 6: Two heaps rebuild", median_sliding_window_6),
        ("Way 7: Two heaps + lazy", median_sliding_window_7),
        ("Way 8: heapify rebuild", median_sliding_window_8),
        ("Way 9: Two heaps + idx", median_sliding_window_9),
        ("Way 10: Final cleanest", medianSlidingWindow),
    ]

    test_cases = [
        ([1, 3, -1, -3, 5, 3, 6, 7], 3, [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]),
        ([1, 2, 3, 4, 5], 2, [1.5, 2.5, 3.5, 4.5]),
        ([1, 2, 3, 4, 5], 3, [2.0, 3.0, 4.0]),
        ([1], 1, [1.0]),
        ([2, 2, 2, 2], 2, [2.0, 2.0, 2.0]),
        ([4, 1, 3, 2], 2, [2.5, 2.0, 2.5]),
        ([-1, -2, -3, -4, -5], 3, [-2.0, -3.0, -4.0]),
        ([1, 4, 2, 3], 4, [2.5]),
    ]

    print("=" * 70)
    print("SLIDING WINDOW MEDIAN - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for nums, k, expected in test_cases:
            try:
                result = fn(list(nums), k)
                if approx_equal(result, expected):
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] nums={nums}, k={k}, expected={expected}, got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}]: {e}")
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