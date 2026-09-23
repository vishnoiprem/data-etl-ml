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
Two heaps with lazy deletion. Maintain a max-heap 'small' (lower half) and
min-heap 'large' (upper half). Keep them balanced (sizes differ by at most
1). When sliding, lazily mark outgoing elements for deletion and prune
tops on demand.

Examples:
    nums=[1,3,-1,-3,5,3,6,7], k=3
    Output: [1, -1, -1, 3, 5, 6]

Constraints:
- 1 <= k <= nums.length <= 10^5
- -2 * 10^4 <= nums[i] <= 2 * 10^4
"""

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

2. WHY TWO HEAPS WITH LAZY DELETION?
   "Need O(log k) per add/remove. A balanced BST would also work (sorted
   list), but Python's heapq doesn't support removal. Use two heaps and
   a 'delayed' dict to mark outgoing elements; prune tops when they appear."

3. ALGORITHM:
   "1. Add first k elements with the same addNum logic from MedianFinder.
    2. Compute first median.
    3. For each new index i:
       a. addNum(nums[i]).
       b. Mark nums[i - k] for delayed deletion.
       c. Prune tops of both heaps while top is in delayed.
       d. Rebalance if needed.
       e. Compute and append median."

4. MEDIAN FORMULA:
   "If k is odd: top of small (whichever has more elements).
    If k is even: avg of tops of small and large."

5. WHEN TO USE:
   - Any sliding window median / quantile.
   - Streaming median over fixed window.

6. COMMON TRAPS:
   - Forgetting to prune after marking deletion.
   - Wrong median formula (which heap has the extra element?).
   - O(n) deletion by removing from heap directly (use lazy).

7. COMPLEXITY:
   +----------------+--------+--------+
   | Operation      | Time   | Notes  |
   +----------------+--------+--------+
   | Each step      | O(log k)        |
   | Total          | O(n log k)      |
   | Space          | O(k)            |
   +----------------+--------+--------+
"""


# =============================================================================
# WAY 1: Two heaps + lazy deletion (BEST - Memorize!)
# =============================================================================
def median_sliding_window_1(nums, k):
    """Two heaps + delayed map. Prune on demand."""
    small = []  # max-heap (negated)
    large = []  # min-heap
    delayed = {}

    # Helper to prune the top of a heap if it's marked for deletion.
    def prune(heap):
        while heap:
            num = -heap[0] if heap is small else heap[0]
            if delayed.get(num, 0) > 0:
                heapq.heappop(heap)
                delayed[num] -= 1
                if delayed[num] == 0:
                    del delayed[num]
            else:
                break

    def add(num):
        if not small or num <= -small[0]:
            heapq.heappush(small, -num)
        else:
            heapq.heappush(large, num)

    def rebalance():
        # Prune first so size comparisons are honest
        prune(small)
        prune(large)
        # Invariant: len(large) >= len(small); difference <= 1.
        # For k=3: large=2, small=1. For k=4: large=2, small=2.
        target_large = (k + 1) // 2
        # Loop until balanced (may need to alternate directions after prunes).
        for _ in range(k + 2):
            if len(large) < target_large and small:
                heapq.heappush(large, -heapq.heappop(small))
            elif len(large) > target_large:
                heapq.heappush(small, -heapq.heappop(large))
            else:
                break
            prune(small)
            prune(large)
        prune(small)
        prune(large)

    def median():
        prune(small)
        prune(large)
        if len(large) > len(small):
            return float(large[0])
        if len(large) == len(small):
            return (-small[0] + large[0]) / 2.0
        return float(-small[0])

    # Initialize
    for i in range(k):
        add(nums[i])
    rebalance()

    out = [median()]
    for i in range(k, len(nums)):
        out_num = nums[i - k]
        in_num = nums[i]
        delayed[out_num] = delayed.get(out_num, 0) + 1
        add(in_num)
        rebalance()
        out.append(median())
    return out


# =============================================================================
# WAY 2: Same as Way 1 but using inline pruning
# =============================================================================
def median_sliding_window_2(nums, k):
    """Two heaps, lazy deletion, inline pruning."""
    small = []
    large = []
    delayed = {}

    def prune(h):
        while h:
            top = -h[0] if h is small else h[0]
            if delayed.get(top, 0) > 0:
                heapq.heappop(h)
                delayed[top] -= 1
                if delayed[top] == 0:
                    del delayed[top]
            else:
                break

    def add(num):
        if not small or num <= -small[0]:
            heapq.heappush(small, -num)
        else:
            heapq.heappush(large, num)

    def balance():
        prune(small)
        prune(large)
        target_large = (k + 1) // 2
        for _ in range(k + 2):
            if len(large) < target_large and small:
                heapq.heappush(large, -heapq.heappop(small))
            elif len(large) > target_large:
                heapq.heappush(small, -heapq.heappop(large))
            else:
                break
            prune(small)
            prune(large)
        prune(small)
        prune(large)

    def med():
        prune(small)
        prune(large)
        if len(large) > len(small):
            return float(large[0])
        if len(large) == len(small):
            return (-small[0] + large[0]) / 2.0
        return float(-small[0])

    for i in range(k):
        add(nums[i])
    balance()
    out = [med()]
    for i in range(k, len(nums)):
        delayed[nums[i - k]] = delayed.get(nums[i - k], 0) + 1
        add(nums[i])
        balance()
        out.append(med())
    return out


# =============================================================================
# WAY 3: Sorted list via insort and bisect.bisect for removal
# =============================================================================
import bisect


def median_sliding_window_3(nums, k):
    window = []
    out = []
    for i, v in enumerate(nums):
        idx = bisect.bisect_left(window, v)
        window.insert(idx, v)
        if len(window) > k:
            # Remove oldest element
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
# WAY 4: Sorted list with explicit pop
# =============================================================================
def median_sliding_window_4(nums, k):
    window = []
    out = []
    for i, v in enumerate(nums):
        idx = bisect.bisect_left(window, v)
        window.insert(idx, v)
        if len(window) > k:
            # Find and remove the oldest element by value
            old = nums[i - k]
            idx = bisect.bisect_left(window, old)
            # could have duplicates; remove one occurrence
            window.pop(idx)
        if len(window) == k:
            if k % 2 == 1:
                out.append(float(window[k // 2]))
            else:
                out.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
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
# WAY 6: Two heaps, more explicit balancing
# =============================================================================
def median_sliding_window_6(nums, k):
    small = []  # max-heap
    large = []  # min-heap
    delayed = {}

    def prune(h):
        while h:
            top = -h[0] if h is small else h[0]
            if delayed.get(top, 0):
                heapq.heappop(h)
                delayed[top] -= 1
                if delayed[top] == 0:
                    del delayed[top]
            else:
                break

    out = []
    for i, v in enumerate(nums):
        # Add
        if not small or v <= -small[0]:
            heapq.heappush(small, -v)
        else:
            heapq.heappush(large, v)
        # Mark removal
        if i >= k:
            out_v = nums[i - k]
            delayed[out_v] = delayed.get(out_v, 0) + 1
        # Balance: prune first
        prune(small)
        prune(large)
        target_large = (k + 1) // 2
        for _ in range(k + 2):
            if len(large) < target_large and small:
                heapq.heappush(large, -heapq.heappop(small))
            elif len(large) > target_large:
                heapq.heappush(small, -heapq.heappop(large))
            else:
                break
            prune(small)
            prune(large)
        prune(small)
        prune(large)
        # Median
        if i >= k - 1:
            if len(large) > len(small):
                out.append(float(large[0]))
            elif len(large) == len(small):
                out.append((-small[0] + large[0]) / 2.0)
            else:
                out.append(float(-small[0]))
    return out


# =============================================================================
# WAY 7: Brute force sort each window (slow but simple)
# =============================================================================
def median_sliding_window_7(nums, k):
    out = []
    for i in range(len(nums) - k + 1):
        window = sorted(nums[i:i + k])
        if k % 2 == 1:
            out.append(float(window[k // 2]))
        else:
            out.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
    return out


# =============================================================================
# WAY 8: Two heaps, no delayed, just rebuild (cleaner but O(k log k) per step)
# =============================================================================
def median_sliding_window_8(nums, k):
    out = []
    for i in range(len(nums) - k + 1):
        window = nums[i:i + k]
        small = []
        large = []
        for v in window:
            if not small or v <= -small[0]:
                heapq.heappush(small, -v)
            else:
                heapq.heappush(large, v)
            if len(small) > len(large) + 1:
                heapq.heappush(large, -heapq.heappop(small))
            elif len(large) > len(small):
                heapq.heappush(small, -heapq.heappop(large))
        if k % 2 == 1:
            out.append(float(-small[0]))
        else:
            out.append((-small[0] + large[0]) / 2.0)
    return out


# =============================================================================
# WAY 9: Two heaps + lazy deletion with tuple (tie-break by index)
# =============================================================================
def median_sliding_window_9(nums, k):
    small = []  # (-val, idx) max-heap
    large = []  # (val, idx) min-heap
    delayed = {}  # idx -> True for removal

    def prune(h):
        while h:
            top_idx = h[0][1]
            if delayed.get(top_idx):
                heapq.heappop(h)
                del delayed[top_idx]
            else:
                break

    out = []
    for i, v in enumerate(nums):
        if not small or v <= -small[0][0]:
            heapq.heappush(small, (-v, i))
        else:
            heapq.heappush(large, (v, i))
        if i >= k:
            delayed[i - k] = True
        prune(small)
        prune(large)
        target_large = (k + 1) // 2
        for _ in range(k + 2):
            if len(large) < target_large and small:
                top = heapq.heappop(small)
                heapq.heappush(large, (-top[0], top[1]))
            elif len(large) > target_large:
                top = heapq.heappop(large)
                heapq.heappush(small, (-top[0], top[1]))
            else:
                break
            prune(small)
            prune(large)
        prune(small)
        prune(large)
        if i >= k - 1:
            if len(large) > len(small):
                out.append(float(large[0][0]))
            elif len(large) == len(small):
                out.append((-small[0][0] + large[0][0]) / 2.0)
            else:
                out.append(float(-small[0][0]))
    return out


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def medianSlidingWindow(nums, k):
    """
    THE ONE TO MEMORIZE.

    Two heaps (small as max, large as min) + delayed dict for lazy deletion.
    After each add and remove-mark, prune tops and rebalance sizes so
    len(small) - len(large) is 0 or 1.

    Time:  O(n log k).
    Space: O(k).
    """
    small, large = [], []
    delayed = {}

    def prune(h):
        while h:
            num = -h[0] if h is small else h[0]
            if delayed.get(num, 0):
                heapq.heappop(h)
                delayed[num] -= 1
                if delayed[num] == 0:
                    del delayed[num]
            else:
                break

    def add(num):
        if not small or num <= -small[0]:
            heapq.heappush(small, -num)
        else:
            heapq.heappush(large, num)

    def balance():
        prune(small)
        prune(large)
        target_large = (k + 1) // 2
        for _ in range(k + 2):
            if len(large) < target_large and small:
                heapq.heappush(large, -heapq.heappop(small))
            elif len(large) > target_large:
                heapq.heappush(small, -heapq.heappop(large))
            else:
                break
            prune(small)
            prune(large)
        prune(small)
        prune(large)

    out = []
    for i in range(k):
        add(nums[i])
    balance()
    prune(small)
    prune(large)
    if len(large) > len(small):
        out.append(float(large[0]))
    elif len(large) == len(small):
        out.append((-small[0] + large[0]) / 2.0)
    else:
        out.append(float(-small[0]))

    for i in range(k, len(nums)):
        delayed[nums[i - k]] = delayed.get(nums[i - k], 0) + 1
        add(nums[i])
        balance()
        prune(small)
        prune(large)
        if len(large) > len(small):
            out.append(float(large[0]))
        elif len(large) == len(small):
            out.append((-small[0] + large[0]) / 2.0)
        else:
            out.append(float(-small[0]))
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
        ("Way 1: Two heaps + lazy (BEST)", median_sliding_window_1),
        ("Way 2: Inline pruning", median_sliding_window_2),
        ("Way 3: bisect.insort", median_sliding_window_3),
        ("Way 4: bisect + pop", median_sliding_window_4),
        ("Way 5: Class wrapper", median_sliding_window_5),
        ("Way 6: Explicit balance", median_sliding_window_6),
        ("Way 7: Brute force sort", median_sliding_window_7),
        ("Way 8: Rebuild each window", median_sliding_window_8),
        ("Way 9: Tie-break idx", median_sliding_window_9),
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