"""
Squares of a Sorted Array - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/squares-of-a-sorted-array

Given an integer array nums sorted in non-decreasing order, return an array
of the squares of each number sorted in non-decreasing order.

KEY INSIGHT:
The largest absolute values are at both ends. Use two pointers from both
ends and fill result from the right (largest square first).

Examples:
    [-4, -1, 0, 3, 10] -> [0, 1, 9, 16, 100]
    [-7, -3, 2, 3, 11] -> [4, 9, 9, 49, 121]

Constraints:
- 1 <= nums.length <= 10^4
- -10^4 <= nums[i] <= 10^4
- nums is sorted in non-decreasing order.
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Two-pointer from ends (BEST - Memorize!)
# ============================================================
def sorted_squares_1(nums):
    """Two pointers from ends. Largest absolute values go to the right of result."""
    n = len(nums)
    result = [0] * n
    left, right = 0, n - 1
    pos = n - 1
    while left <= right:
        lsq = nums[left] * nums[left]
        rsq = nums[right] * nums[right]
        if lsq > rsq:
            result[pos] = lsq
            left += 1
        else:
            result[pos] = rsq
            right -= 1
        pos -= 1
    return result


# ============================================================
# Way 2: Brute force square + sort
# ============================================================
def sorted_squares_2(nums):
    """Square each element, then sort. O(n log n) but simple."""
    return sorted(x * x for x in nums)


# ============================================================
# Way 3: Compare absolute values
# ============================================================
def sorted_squares_3(nums):
    """Same as Way 1 but using abs for cleaner comparison."""
    n = len(nums)
    result = [0] * n
    left, right = 0, n - 1
    pos = n - 1
    while left <= right:
        if abs(nums[left]) > abs(nums[right]):
            result[pos] = nums[left] * nums[left]
            left += 1
        else:
            result[pos] = nums[right] * nums[right]
            right -= 1
        pos -= 1
    return result


# ============================================================
# Way 4: Find split point, then merge
# ============================================================
def sorted_squares_4(nums):
    """Find the partition between negative and non-negative. Square both halves
    (negatives reversed), then merge."""
    # Find first non-negative
    n = len(nums)
    split = 0
    while split < n and nums[split] < 0:
        split += 1
    # Negatives: nums[0..split] (reversed and squared)
    # Non-negatives: nums[split..n] (squared)
    neg_sq = [nums[i] * nums[i] for i in range(split - 1, -1, -1)]
    pos_sq = [nums[i] * nums[i] for i in range(split, n)]
    # Merge
    result = []
    i = j = 0
    while i < len(neg_sq) and j < len(pos_sq):
        if neg_sq[i] <= pos_sq[j]:
            result.append(neg_sq[i])
            i += 1
        else:
            result.append(pos_sq[j])
            j += 1
    result.extend(neg_sq[i:])
    result.extend(pos_sq[j:])
    return result


# ============================================================
# Way 5: Heap-based
# ============================================================
def sorted_squares_5(nums):
    """Use heap to merge. Treat each side as a stream."""
    import heapq
    n = len(nums)
    # Find split
    split = 0
    while split < n and nums[split] < 0:
        split += 1
    # Negatives in reversed order
    neg_sq = [nums[i] * nums[i] for i in range(split - 1, -1, -1)]
    pos_sq = [nums[i] * nums[i] for i in range(split, n)]
    # Use two-pointer merged (heap overkill for two sorted lists)
    result = []
    i = j = 0
    while i < len(neg_sq) or j < len(pos_sq):
        if i == len(neg_sq):
            result.append(pos_sq[j])
            j += 1
        elif j == len(pos_sq):
            result.append(neg_sq[i])
            i += 1
        elif neg_sq[i] <= pos_sq[j]:
            result.append(neg_sq[i])
            i += 1
        else:
            result.append(pos_sq[j])
            j += 1
    return result


# ============================================================
# Way 6: One-liner using list comprehension + sort
# ============================================================
def sorted_squares_6(nums):
    """Pythonic one-liner."""
    return sorted([x * x for x in nums])


# ============================================================
# Way 7: numpy vectorized
# ============================================================
def sorted_squares_7(nums):
    """Use numpy."""
    try:
        import numpy as np
        arr = np.array(nums)
        return np.sort(arr * arr).tolist()
    except ImportError:
        return sorted_squares_1(nums)


# ============================================================
# Way 8: Recursive divide-and-conquer
# ============================================================
def sorted_squares_8(nums):
    """Divide and conquer: square each half, then merge."""
    if len(nums) <= 1:
        return [nums[0] * nums[0]] if nums else []
    mid = len(nums) // 2
    left = sorted_squares_8(nums[:mid])
    right = sorted_squares_8(nums[mid:])
    # Merge
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ============================================================
# Way 9: Class-based
# ============================================================
class SortedSquares_9:
    def __init__(self, nums):
        self.nums = nums

    def compute(self):
        n = len(self.nums)
        result = [0] * n
        left, right = 0, n - 1
        pos = n - 1
        while left <= right:
            lsq = self.nums[left] * self.nums[left]
            rsq = self.nums[right] * self.nums[right]
            if lsq > rsq:
                result[pos] = lsq
                left += 1
            else:
                result[pos] = rsq
                right -= 1
            pos -= 1
        return result


def sorted_squares_9(nums):
    return SortedSquares_9(nums).compute()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def sorted_squares_10(nums):
    """
    THE ONE TO MEMORIZE.

    1. left = 0, right = n-1, pos = n-1.
    2. While left <= right:
       - Compare nums[left]^2 vs nums[right]^2.
       - Larger goes to result[pos].
       - Move that pointer inward.
       - pos -= 1.
    3. Return result.

    Time:  O(n)
    Space: O(n) for output.
    """
    n = len(nums)
    result = [0] * n
    left, right, pos = 0, n - 1, n - 1
    while left <= right:
        if abs(nums[left]) > abs(nums[right]):
            result[pos] = nums[left] ** 2
            left += 1
        else:
            result[pos] = nums[right] ** 2
            right -= 1
        pos -= 1
    return result


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to return the squares of a sorted array, also sorted."

Key Insight:
"The largest absolute values are at the ENDS of the input array. So I'll
use two pointers from both ends and fill the result from the right (where
the largest square goes)."

Algorithm:
1. left = 0, right = n-1, pos = n-1.
2. While left <= right:
   a. If nums[left]^2 > nums[right]^2: result[pos] = nums[left]^2; left++.
   b. Else: result[pos] = nums[right]^2; right--.
   c. pos--.
3. Return result.

Edge Cases:
- All non-negative: just square and return (algorithm still works).
- All non-positive: same, fill from left.
- Mix: works as described.
- Single element: just square.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Two-ptr   | O(n)   | O(n)   |
| Brute sort| O(nlogn)| O(n)  |
+-----------+--------+--------+

KEY TRICK:
Fill result from the RIGHT (largest position) because the LARGEST square
always comes from one of the two ends.

RELATED PROBLEMS:
- Sort Array By Parity (LC 905): two-pointer partition.
- Sort Colors (LC 75): three-way partition.
- Merge Sorted Array (LC 88): similar merge pattern.
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([-4, -1, 0, 3, 10], [0, 1, 9, 16, 100], "Standard"),
        ([-7, -3, 2, 3, 11], [4, 9, 9, 49, 121], "Two peaks"),
        ([-1], [1], "Single negative"),
        ([0], [0], "Single zero"),
        ([5], [25], "Single positive"),
        ([-5, -3, -2, -1], [1, 4, 9, 25], "All negative"),
        ([1, 2, 3, 4, 5], [1, 4, 9, 16, 25], "All positive"),
        ([-3, -1, 0, 0, 1, 3], [0, 0, 1, 1, 9, 9], "With zeros"),
        ([-10000], [100000000], "Min range"),
        ([-10000, 10000], [100000000, 100000000], "Both extremes"),
        ([], [], "Empty"),
        ([-3, -2, -1], [1, 4, 9], "Three negatives"),
    ]

    implementations = [
        ("Way 1: Two-pointer (BEST)", sorted_squares_1),
        ("Way 2: Brute square+sort", sorted_squares_2),
        ("Way 3: Abs compare", sorted_squares_3),
        ("Way 4: Split and merge", sorted_squares_4),
        ("Way 5: Heap-based merge", sorted_squares_5),
        ("Way 6: One-liner", sorted_squares_6),
        ("Way 7: numpy", sorted_squares_7),
        ("Way 8: Divide and conquer", sorted_squares_8),
        ("Way 9: Class-based", sorted_squares_9),
        ("Way 10: Final cleanest", sorted_squares_10),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for nums, expected, desc in test_cases:
            try:
                nums_copy = copy.deepcopy(nums)
                result = fn(nums_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: nums={nums} expected={expected} got={result}")
            except Exception as e:
                failed += 1
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
