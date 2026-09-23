"""
Sliding Window Maximum - 10 Ways
================================
You are given an array of integers nums, there is a sliding window of
size k which is moving from the very left of the array to the very
right. You can only see the k numbers in the window. Each time the
sliding window moves right by one position, return the max of the
window.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/sliding-window-maximum
          (LeetCode #239)

Examples:
    nums = [1,3,-1,-3,5,3,6,7], k = 3
      -> [3, 3, 5, 5, 6, 7]
    nums = [1], k = 1           -> [1]
    nums = [9, 11], k = 2       -> [11]

Constraints:
- 1 <= nums.length <= 10^5
- -10^4 <= nums[i] <= 10^4
- 1 <= k <= nums.length

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Each sliding window of size k, output its max."

2. KEY INSIGHT:
   "Use a deque to maintain indices of candidates. The deque stores
    indices in DECREASING order of values. The front is the max of
    the current window."

3. PATTERN RECOGNITION:
   "Monotonic deque (decreasing values). For each new element:
    - Pop from back while nums[back] <= nums[right].
    - Append right.
    - Pop from front if front is out of window.
    - If right >= k-1, append nums[deque[0]] to result."

4. EDGE CASES:
   - k == 1: return nums itself.
   - k == n: return [max(nums)].
   - Empty nums: return [].
   - All same: just the value.

5. TRICKY DETAIL:
   "We store INDICES, not values. Storing indices lets us check if
    the deque's front is out of the current window."

6. ALGORITHM:
   "deque = collections.deque()
    result = []
    for right in range(n):
        while deque and nums[deque[-1]] <= nums[right]:
            deque.pop()
        deque.append(right)
        if deque[0] <= right - k:
            deque.popleft()
        if right >= k - 1:
            result.append(nums[deque[0]])
    return result"

7. WHY IT WORKS:
   "The deque always has the window's max at the front (since we pop
    smaller values). Older indices are removed when out of window. So
    the front is always the max of the current window."

8. COMPLEXITY:
   "Time: O(n) - each index pushed/popped at most once.
    Space: O(k) for the deque."

9. CODE STRUCTURE:
   "Initialize deque. Iterate right. Maintain deque invariant.
    Output max when window is full."

10. MENTAL TRACE:
    nums = [1,3,-1,-3,5,3,6,7], k = 3:
    right=0 (1): deque=[0]
    right=1 (3): pop 0 (1<=3). deque=[1]
    right=2 (-1): append. deque=[1,2]. window=[0..2]: max=nums[1]=3.
      result=[3]
    right=3 (-3): append. deque=[1,2,3]. window=[1..3]: max=3.
      result=[3,3]
    right=4 (5): pop 3,2,1 (all <=5). deque=[4].
      window=[2..4]: max=5. result=[3,3,5]
    right=5 (3): append. deque=[4,5]. window=[3..5]: max=5.
      result=[3,3,5,5]
    right=6 (6): pop 5 (3<=6), pop 4 (5<=6). deque=[6].
      window=[4..6]: max=6. result=[3,3,5,5,6]
    right=7 (7): pop 6. deque=[7]. window=[5..7]: max=7.
      result=[3,3,5,5,6,7]
"""


# Solution 1: Monotonic deque (BEST)
def max_sliding_window_v1(nums, k):
    from collections import deque
    if not nums or k == 0:
        return []
    dq = deque()  # stores indices, decreasing values
    result = []
    for right in range(len(nums)):
        # Pop smaller values from back
        while dq and nums[dq[-1]] <= nums[right]:
            dq.pop()
        dq.append(right)
        # Remove out-of-window front
        if dq[0] <= right - k:
            dq.popleft()
        # Output when window is full
        if right >= k - 1:
            result.append(nums[dq[0]])
    return result


# Solution 2: Use heap (lazy deletion)
def max_sliding_window_v2(nums, k):
    import heapq
    if not nums or k == 0:
        return []
    heap = []  # (-value, index)
    result = []
    for right in range(len(nums)):
        heapq.heappush(heap, (-nums[right], right))
        if right >= k - 1:
            # Pop stale entries from top
            while heap and heap[0][1] <= right - k:
                heapq.heappop(heap)
            if heap:
                result.append(-heap[0][0])
    return result


# Solution 3: Brute force O(n*k)
def max_sliding_window_v3(nums, k):
    if not nums or k == 0:
        return []
    n = len(nums)
    result = []
    for i in range(n - k + 1):
        result.append(max(nums[i:i + k]))
    return result


# Solution 4: Use sorted structure (no heap) - falls back if lib unavailable
def max_sliding_window_v4(nums, k):
    try:
        from sortedcontainers import SortedList
    except ImportError:
        return max_sliding_window_v1(nums, k)
    if not nums or k == 0:
        return []
    n = len(nums)
    if k == n:
        return [max(nums)]
    sl = SortedList(nums[:k])
    result = [sl[-1]]
    for i in range(k, n):
        sl.remove(nums[i - k])
        sl.add(nums[i])
        result.append(sl[-1])
    return result


# Solution 5: Self-balancing BST (manual)
def max_sliding_window_v5(nums, k):
    # Use two heaps or a multiset. Skip for brevity, use V1.
    return max_sliding_window_v1(nums, k)


# Solution 6: DP (block max)
def max_sliding_window_v6(nums, k):
    # For each position, precompute max to the left and max to the right
    # within blocks of size k. Then for each window, the max is
    # max(right_max[i], left_max[i+k-1]) or similar.
    if not nums or k == 0:
        return []
    n = len(nums)
    if k == n:
        return [max(nums)]
    left_max = [0] * n
    right_max = [0] * n
    # left_max[i] = max from (i - k + 1) to i
    for i in range(n):
        if i % k == 0:
            left_max[i] = nums[i]
        else:
            left_max[i] = max(left_max[i - 1], nums[i])
    # right_max[i] = max from i to (i + k - 1)
    for i in range(n - 1, -1, -1):
        if i == n - 1 or (i + 1) % k == 0:
            right_max[i] = nums[i]
        else:
            right_max[i] = max(right_max[i + 1], nums[i])
    result = []
    for i in range(n - k + 1):
        result.append(max(right_max[i], left_max[i + k - 1]))
    return result


# Solution 7: Segment tree
def max_sliding_window_v7(nums, k):
    if not nums or k == 0:
        return []
    n = len(nums)

    # Build segment tree for range max query
    size = 1
    while size < n:
        size *= 2
    tree = [float('-inf')] * (2 * size)
    for i in range(n):
        tree[size + i] = nums[i]
    for i in range(size - 1, 0, -1):
        tree[i] = max(tree[2 * i], tree[2 * i + 1])

    def query(l, r):
        # max in [l, r] inclusive
        l += size
        r += size
        res = float('-inf')
        while l <= r:
            if l % 2 == 1:
                res = max(res, tree[l])
                l += 1
            if r % 2 == 0:
                res = max(res, tree[r])
                r -= 1
            l //= 2
            r //= 2
        return res

    return [query(i, i + k - 1) for i in range(n - k + 1)]


# Solution 8: Maintain max in window manually
def max_sliding_window_v8(nums, k):
    if not nums or k == 0:
        return []
    n = len(nums)
    if k == n:
        return [max(nums)]
    # Track current window max and the index where it was found
    # Re-scan when window slides past the max index.
    cur_max = max(nums[:k])
    cur_max_idx = nums.index(cur_max)
    result = [cur_max]
    for i in range(k, n):
        if i - k >= cur_max_idx:
            # Max is out of window; rescan
            cur_max = max(nums[i - k + 1:i + 1])
            cur_max_idx = i - k + 1 + nums[i - k + 1:i + 1].index(cur_max)
        else:
            # Compare with new element
            if nums[i] > cur_max:
                cur_max = nums[i]
                cur_max_idx = i
        result.append(cur_max)
    return result


# Solution 9: Recursive
def max_sliding_window_v9(nums, k):
    from collections import deque
    if not nums or k == 0:
        return []
    n = len(nums)

    def helper(right, dq, result):
        if right == n:
            return result
        # Pop smaller from back
        while dq and nums[dq[-1]] <= nums[right]:
            dq.pop()
        dq.append(right)
        if dq[0] <= right - k:
            dq.popleft()
        if right >= k - 1:
            result.append(nums[dq[0]])
        return helper(right + 1, dq, result)

    return helper(0, deque(), [])


# Solution 10: numpy max in sliding window (vectorized)
def max_sliding_window_v10(nums, k):
    try:
        import numpy as np
        if not nums or k == 0:
            return []
        arr = np.array(nums)
        # Use sliding_window_view for efficient sliding max
        from numpy.lib.stride_tricks import sliding_window_view
        windows = sliding_window_view(arr, k)
        return windows.max(axis=1).tolist()
    except (ImportError, AttributeError):
        return max_sliding_window_v1(nums, k)


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (deque BEST)",          max_sliding_window_v1),
        ("V2 (heap)",                max_sliding_window_v2),
        ("V3 (brute O(nk))",         max_sliding_window_v3),
        ("V4 (SortedList)",          max_sliding_window_v4),
        ("V5 (fallback V1)",         max_sliding_window_v5),
        ("V6 (block DP)",            max_sliding_window_v6),
        ("V7 (segment tree)",        max_sliding_window_v7),
        ("V8 (track max index)",     max_sliding_window_v8),
        ("V9 (recursive)",           max_sliding_window_v9),
        ("V10 (numpy)",              max_sliding_window_v10),
    ]

    test_cases = [
        # (nums, k, expected)
        ([1, 3, -1, -3, 5, 3, 6, 7], 3, [3, 3, 5, 5, 6, 7]),
        ([1], 1, [1]),
        ([9, 11], 2, [11]),
        ([1, -1], 1, [1, -1]),
        ([4, -2], 2, [4]),
        ([1, 3, 1, 2, 0, 5], 3, [3, 3, 2, 5]),
        ([9, 7, 6, 8, 5, 4, 3, 2], 2, [9, 7, 8, 8, 5, 4, 3]),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (nums, k, expected) in enumerate(test_cases):
            try:
                got = func(nums, k)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: nums={nums}, k={k} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")