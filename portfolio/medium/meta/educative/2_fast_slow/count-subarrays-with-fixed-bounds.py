"""
Count Subarrays With Fixed Bounds - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/count-subarrays

You are given an integer array nums and two integers minK and maxK.
A fixed-bound subarray of nums is a subarray that satisfies:
- The minimum value in the subarray is equal to minK.
- The maximum value in the subarray is equal to maxK.
Return the number of fixed-bound subarrays.

KEY INSIGHT:
Track three positions while scanning left-to-right:
- last_invalid: last index where nums[i] < minK or nums[i] > maxK (a "wall").
- last_min: last index where nums[i] == minK.
- last_max: last index where nums[i] == maxK.
At each index i, the number of valid subarrays ENDING at i is:
  max(0, min(last_min, last_max) - last_invalid).

Examples:
    nums = [1, 3, 5, 2, 7, 5], minK = 1, maxK = 5 -> 2
    nums = [1, 1, 1, 1], minK = 1, maxK = 1 -> 10
    nums = [1, 5, 1], minK = 1, maxK = 5 -> 1

Constraints:
- 1 <= nums.length <= 10^5
- 1 <= minK <= maxK <= 10^6
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Linear scan with last_invalid, last_min, last_max (BEST - Memorize!)
# ============================================================
def count_subarrays_1(nums, minK, maxK):
    """Single pass tracking three positions. O(n) time, O(1) space."""
    last_invalid = -1
    last_min = -1
    last_max = -1
    count = 0
    for i, num in enumerate(nums):
        if num < minK or num > maxK:
            last_invalid = i
        if num == minK:
            last_min = i
        if num == maxK:
            last_max = i
        # Valid subarrays ending at i start after last_invalid and include both
        valid_starts = min(last_min, last_max) - last_invalid
        if valid_starts > 0:
            count += valid_starts
    return count


# ============================================================
# Way 2: Brute force O(n^2)
# ============================================================
def count_subarrays_2(nums, minK, maxK):
    """For each subarray, check min and max. Educational only."""
    n = len(nums)
    count = 0
    for i in range(n):
        cur_min = float('inf')
        cur_max = float('-inf')
        for j in range(i, n):
            cur_min = min(cur_min, nums[j])
            cur_max = max(cur_max, nums[j])
            if cur_min == minK and cur_max == maxK:
                count += 1
    return count


# ============================================================
# Way 3: Segment tree based (overkill but illustrative)
# ============================================================
def count_subarrays_3(nums, minK, maxK):
    """Brute O(n^2) using cumulative min/max arrays. Easier to verify."""
    n = len(nums)
    count = 0
    for i in range(n):
        cur_min = float('inf')
        cur_max = float('-inf')
        for j in range(i, n):
            cur_min = min(cur_min, nums[j])
            cur_max = max(cur_max, nums[j])
            if cur_min < minK or cur_max > maxK:
                break  # extending will not reduce cur_min or cur_max
            if cur_min == minK and cur_max == maxK:
                count += 1
    return count


# ============================================================
# Way 4: Split by walls and count within each segment
# ============================================================
def count_subarrays_4(nums, minK, maxK):
    """Split array into segments between 'invalid' elements.
    Within each segment, count subarrays containing both minK and maxK."""
    n = len(nums)
    count = 0
    segments = []
    start = 0
    for i in range(n):
        if nums[i] < minK or nums[i] > maxK:
            if start < i:
                segments.append((start, i - 1))
            start = i + 1
    if start < n:
        segments.append((start, n - 1))
    # For each segment, count subarrays containing both minK and maxK
    for seg_start, seg_end in segments:
        last_min = -1
        last_max = -1
        for i in range(seg_start, seg_end + 1):
            if nums[i] == minK:
                last_min = i
            if nums[i] == maxK:
                last_max = i
            if last_min >= seg_start and last_max >= seg_start:
                # Count subarrays ending at i that contain both
                # Start must include min(last_min, last_max) and end at i
                # Number of starts = min(last_min, last_max) - seg_start + 1
                count += min(last_min, last_max) - seg_start + 1
    return count


# ============================================================
# Way 5: Track positions, then sum ranges
# ============================================================
def count_subarrays_5(nums, minK, maxK):
    """Collect positions of minK, maxK, and walls. For each pair of consecutive
    walls, count using positions of minK and maxK in that range."""
    n = len(nums)
    walls = [-1] + [i for i in range(n) if nums[i] < minK or nums[i] > maxK] + [n]
    min_positions = []
    max_positions = []
    for i in range(n):
        if nums[i] == minK:
            min_positions.append(i)
        elif nums[i] == maxK:
            max_positions.append(i)
    # For each segment between walls, count subarrays containing both
    count = 0
    for seg_idx in range(len(walls) - 1):
        seg_start = walls[seg_idx] + 1
        seg_end = walls[seg_idx + 1] - 1
        if seg_start > seg_end:
            continue
        # Last minK and last maxK in this segment, walking from seg_start
        last_min = -1
        last_max = -1
        for i in range(seg_start, seg_end + 1):
            if nums[i] == minK:
                last_min = i
            if nums[i] == maxK:
                last_max = i
            if last_min >= seg_start and last_max >= seg_start:
                count += min(last_min, last_max) - seg_start + 1
    return count


# ============================================================
# Way 6: Pure Python with list comp
# ============================================================
def count_subarrays_6(nums, minK, maxK):
    """Brute force using list comp to enumerate all subarrays (slow but simple)."""
    n = len(nums)
    count = 0
    for i in range(n):
        for j in range(i, n):
            sub = nums[i:j + 1]
            if min(sub) == minK and max(sub) == maxK:
                count += 1
    return count


# ============================================================
# Way 7: Class-based
# ============================================================
class SubarrayCounter_7:
    def __init__(self, nums, minK, maxK):
        self.nums = nums
        self.minK = minK
        self.maxK = maxK

    def count(self):
        last_invalid = -1
        last_min = -1
        last_max = -1
        count = 0
        for i, num in enumerate(self.nums):
            if num < self.minK or num > self.maxK:
                last_invalid = i
            if num == self.minK:
                last_min = i
            if num == self.maxK:
                last_max = i
            valid_starts = min(last_min, last_max) - last_invalid
            if valid_starts > 0:
                count += valid_starts
        return count


def count_subarrays_7(nums, minK, maxK):
    return SubarrayCounter_7(nums, minK, maxK).count()


# ============================================================
# Way 8: numpy version
# ============================================================
def count_subarrays_8(nums, minK, maxK):
    """Use numpy to vectorize min/max within segments, but still loops over i.
    Mostly demonstrates the concept."""
    try:
        import numpy as np
        arr = np.array(nums)
    except ImportError:
        return count_subarrays_1(nums, minK, maxK)
    n = len(arr)
    last_invalid = -1
    last_min = -1
    last_max = -1
    count = 0
    for i in range(n):
        num = int(arr[i])
        if num < minK or num > maxK:
            last_invalid = i
        if num == minK:
            last_min = i
        if num == maxK:
            last_max = i
        valid_starts = min(last_min, last_max) - last_invalid
        if valid_starts > 0:
            count += valid_starts
    return count


# ============================================================
# Way 9: Track using lists of positions
# ============================================================
def count_subarrays_9(nums, minK, maxK):
    """Track positions of minK and maxK explicitly."""
    n = len(nums)
    count = 0
    last_invalid = -1
    min_positions = []
    max_positions = []
    for i in range(n):
        if nums[i] < minK or nums[i] > maxK:
            last_invalid = i
            min_positions = []
            max_positions = []
        if nums[i] == minK:
            min_positions.append(i)
        if nums[i] == maxK:
            max_positions.append(i)
        # Subarrays ending at i that contain both: start must include both
        if min_positions and max_positions:
            # Earliest start that includes both
            earliest_min = min_positions[0]
            earliest_max = max_positions[0]
            # Start must be <= min(earliest_min, earliest_max)
            # AND > last_invalid
            # Number of valid starts: min(earliest_min, earliest_max) - last_invalid
            # But wait: we need both minK and maxK in the subarray, not just one
            # The correct count: for each i, the latest of (last_min, last_max)
            # determines the last position required; the subarray start must
            # be <= that latest position. But it must include both.
            # Valid starts: positions between last_invalid+1 and
            # min(latest_min, latest_max) inclusive, provided both have occurred.
            last_min = min_positions[-1]
            last_max = max_positions[-1]
            valid_starts = min(last_min, last_max) - last_invalid
            if valid_starts > 0:
                count += valid_starts
    return count


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def count_subarrays_10(nums, minK, maxK):
    """
    THE ONE TO MEMORIZE.

    1. last_invalid = last_min = last_max = -1, count = 0.
    2. For i in range(n):
       a. If nums[i] is out of [minK, maxK]: last_invalid = i.
       b. If nums[i] == minK: last_min = i.
       c. If nums[i] == maxK: last_max = i.
       d. count += max(0, min(last_min, last_max) - last_invalid).
    3. Return count.

    Time:  O(n)
    Space: O(1)
    """
    last_invalid = last_min = last_max = -1
    count = 0
    for i, num in enumerate(nums):
        if num < minK or num > maxK:
            last_invalid = i
        if num == minK:
            last_min = i
        if num == maxK:
            last_max = i
        valid_starts = min(last_min, last_max) - last_invalid
        if valid_starts > 0:
            count += valid_starts
    return count


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count subarrays where the minimum equals minK and the maximum
equals maxK."

Key Insight:
"Track three indices as I scan:
- last_invalid: where the array went out of [minK, maxK] (a wall).
- last_min: where minK last appeared.
- last_max: where maxK last appeared.
At index i, a valid subarray ending at i must start after last_invalid and
include both last_min and last_max. The number of such starts is
min(last_min, last_max) - last_invalid."

Algorithm:
1. Initialize last_invalid = last_min = last_max = -1, count = 0.
2. For i, num in enumerate(nums):
   a. If num < minK or num > maxK: last_invalid = i.
   b. If num == minK: last_min = i.
   c. If num == maxK: last_max = i.
   d. valid = min(last_min, last_max) - last_invalid.
      If valid > 0: count += valid.
3. Return count.

Edge Cases:
- No minK or maxK in array: 0.
- All elements are minK (= maxK): every subarray is valid (n*(n+1)/2).
- Walls between minK and maxK: count resets.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Linear    | O(n)   | O(1)   |
| Brute     | O(n^2) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
The formula valid_starts = min(last_min, last_max) - last_invalid
counts starts where the subarray contains BOTH minK and maxK and stays
within [minK, maxK].

RELATED PROBLEMS:
- Subarray With Bounded Maximum (LC 795): similar idea.
- Count Subarrays With Score Less Than K (LC 2302).
- Number of Subarrays With Bounded Maximum (LC 795).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 3, 5, 2, 7, 5], 1, 5, 2, "Standard"),
        ([1, 1, 1, 1], 1, 1, 10, "All same"),
        ([1, 5, 1], 1, 5, 3, "Tiny"),
        ([0, 0, 0, 0], 0, 0, 10, "All zeros"),
        ([1], 1, 1, 1, "Single valid"),
        ([2], 1, 5, 0, "Single invalid"),
        ([5, 1, 5, 1, 5], 1, 5, 10, "Alternating"),
        ([1, 3, 5, 2, 7, 5], 2, 5, 2, "Different bounds"),
        ([1, 3, 5, 2, 7, 5], 1, 7, 2, "Has maxK=7"),
        ([1, 3, 5, 2, 7, 5], 3, 7, 0, "Impossible bounds"),
        ([1, 1, 5, 5, 1, 1], 1, 5, 12, "Two pairs"),
        ([5, 5, 5, 5], 5, 5, 10, "All maxK"),
    ]

    implementations = [
        ("Way 1: Linear (BEST)", count_subarrays_1),
        ("Way 2: Brute O(n^2)", count_subarrays_2),
        ("Way 3: Brute break-early", count_subarrays_3),
        ("Way 4: Split by walls", count_subarrays_4),
        ("Way 5: Walls + positions", count_subarrays_5),
        ("Way 6: List comp brute", count_subarrays_6),
        ("Way 7: Class-based", count_subarrays_7),
        ("Way 8: numpy", count_subarrays_8),
        ("Way 9: Position lists", count_subarrays_9),
        ("Way 10: Final cleanest", count_subarrays_10),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for nums, minK, maxK, expected, desc in test_cases:
            try:
                nums_copy = copy.deepcopy(nums)
                result = fn(nums_copy, minK, maxK)
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
