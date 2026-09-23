"""
Remove Duplicates from Sorted Array - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/remove-duplicates-from-sorted-array

Given a sorted integer array nums, remove duplicates in-place so that each
unique element appears only once. Return the number of unique elements k.
The first k positions of nums must contain the unique elements in sorted
order. Elements beyond k are irrelevant.

KEY INSIGHT:
Two-pointer technique. slow points to the last unique element placed.
fast scans ahead. When nums[fast] differs from nums[slow], advance slow
and copy nums[fast] into nums[slow]. Both pointers move forward; no
nested loops needed — O(n) total.

Examples:
    [1, 1, 2] -> 2, nums becomes [1, 2, _]
    [0, 0, 1, 1, 1, 2, 2, 3, 3, 4] -> 5, nums becomes [0, 1, 2, 3, 4, _, _, _, _, _]

Constraints:
- 1 <= nums.length <= 3 * 10^4
- -100 <= nums[i] <= 100
- nums is sorted in non-decreasing order.
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Slow/fast pointer (BEST - Memorize!)
# ============================================================
def remove_duplicates_1(nums):
    """slow = index of last placed unique; fast scans ahead."""
    if not nums:
        return 0
    slow = 0
    for fast in range(1, len(nums)):
        if nums[fast] != nums[slow]:
            slow += 1
            nums[slow] = nums[fast]
    return slow + 1


# ============================================================
# Way 2: Brute force using set (creates new array)
# ============================================================
def remove_duplicates_2(nums):
    """Convert to set, sort, copy back. Not in-place in spirit but works."""
    unique = sorted(set(nums))
    for i, v in enumerate(unique):
        nums[i] = v
    return len(unique)


# ============================================================
# Way 3: Two-pointer explicit (left/right named)
# ============================================================
def remove_duplicates_3(nums):
    """Same as Way 1, but using 'left' and 'right' instead of slow/fast."""
    if not nums:
        return 0
    left = 0
    for right in range(1, len(nums)):
        if nums[right] != nums[left]:
            left += 1
            nums[left] = nums[right]
    return left + 1


# ============================================================
# Way 4: While-loop version
# ============================================================
def remove_duplicates_4(nums):
    """Manual while loop with explicit pointer increments."""
    if not nums:
        return 0
    i = 0
    j = 1
    while j < len(nums):
        if nums[j] != nums[i]:
            i += 1
            nums[i] = nums[j]
        j += 1
    return i + 1


# ============================================================
# Way 5: enumerate + index tracking
# ============================================================
def remove_duplicates_5(nums):
    """Use enumerate to get index and value together."""
    if not nums:
        return 0
    last_unique_idx = 0
    last_unique_val = nums[0]
    for idx in range(1, len(nums)):
        if nums[idx] != last_unique_val:
            last_unique_idx += 1
            nums[last_unique_idx] = nums[idx]
            last_unique_val = nums[idx]
    return last_unique_idx + 1


# ============================================================
# Way 6: Using zip with shifted array
# ============================================================
def remove_duplicates_6(nums):
    """Pair each element with the previous using zip. Compare and write back."""
    if not nums:
        return 0
    write = 0
    # zip(nums, nums[1:]) yields pairs (prev, curr) - but careful: when write
    # moves ahead, the read index lags behind.
    # Use index-based pair comparison instead.
    for i in range(1, len(nums)):
        if nums[i] != nums[write]:
            write += 1
            nums[write] = nums[i]
    return write + 1


# ============================================================
# Way 7: Recursive with index pointer (educational)
# ============================================================
def remove_duplicates_7(nums):
    """Recursion: scan from index 'i', write unique to 'write'. Pass write_pos
    as the last unique's index (initially 0). Educational only."""
    n = len(nums)
    if n == 0:
        return 0
    if n == 1:
        return 1

    def helper(i, last_unique_idx):
        # Skip duplicates of nums[last_unique_idx]
        while i < n and nums[i] == nums[last_unique_idx]:
            i += 1
        if i >= n:
            return last_unique_idx + 1
        # nums[i] is the next unique
        last_unique_idx += 1
        nums[last_unique_idx] = nums[i]
        return helper(i + 1, last_unique_idx)

    return helper(1, 0)


# ============================================================
# Way 8: numpy-based
# ============================================================
def remove_duplicates_8(nums):
    """Use numpy to find unique values, but copy back in-place."""
    try:
        import numpy as np
        arr = np.array(nums)
        unique = np.unique(arr)
        for i, v in enumerate(unique):
            nums[i] = int(v)
        return len(unique)
    except ImportError:
        return remove_duplicates_1(nums)


# ============================================================
# Way 9: Class-based
# ============================================================
class DuplicateRemover_9:
    def __init__(self, nums):
        self.nums = nums

    def remove(self):
        if not self.nums:
            return 0
        slow = 0
        for fast in range(1, len(self.nums)):
            if self.nums[fast] != self.nums[slow]:
                slow += 1
                self.nums[slow] = self.nums[fast]
        return slow + 1


def remove_duplicates_9(nums):
    return DuplicateRemover_9(nums).remove()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def remove_duplicates_10(nums):
    """
    THE ONE TO MEMORIZE.

    1. slow = 0.
    2. For fast in range(1, n):
       - If nums[fast] != nums[slow]:
           slow += 1
           nums[slow] = nums[fast]
    3. Return slow + 1.

    Time:  O(n)
    Space: O(1) extra (in-place).
    """
    if not nums:
        return 0
    slow = 0
    for fast in range(1, len(nums)):
        if nums[fast] != nums[slow]:
            slow += 1
            nums[slow] = nums[fast]
    return slow + 1


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to remove duplicates from a sorted array in-place and return
the count of unique elements."

Key Insight:
"Since the array is sorted, all duplicates are adjacent. I'll use a
two-pointer technique: 'slow' marks the last placed unique element,
'fast' scans ahead. When nums[fast] differs from nums[slow], advance
slow and copy the new unique value."

Algorithm:
1. slow = 0.
2. For fast in range(1, n):
   a. If nums[fast] != nums[slow]:
      - slow += 1
      - nums[slow] = nums[fast]
3. Return slow + 1.

Edge Cases:
- Empty array: return 0.
- Single element: return 1.
- All same: return 1.
- All unique: return n.
- Negative numbers: works fine.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Two-ptr   | O(n)   | O(1)   |
| Set-based | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
Because the array is sorted, a single pass with two pointers is enough.
No nested loops. No extra data structure.

RELATED PROBLEMS:
- Remove Element (LC 27): remove all occurrences of val.
- Remove Duplicates II (LC 80): allow at most 2 of each.
- Move Zeroes (LC 283): same slow/fast pattern.
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (input, expected_k, expected_first_k, description)
        ([1, 1, 2], 2, [1, 2], "Standard"),
        ([0, 0, 1, 1, 1, 2, 2, 3, 3, 4], 5, [0, 1, 2, 3, 4], "LeetCode standard"),
        ([1, 2, 3], 3, [1, 2, 3], "All unique"),
        ([1, 1, 1, 1, 1], 1, [1], "All same"),
        ([1], 1, [1], "Single element"),
        ([], 0, [], "Empty"),
        ([-1, -1, 0, 0, 1], 3, [-1, 0, 1], "With negatives"),
        ([-3, -3, -3, -2, -1, 0, 0, 0, 1, 2, 2], 6, [-3, -2, -1, 0, 1, 2], "Mixed"),
        ([1, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5], 5, [1, 2, 3, 4, 5], "Consecutive duplicates"),
        ([1, 1, 1, 2, 2, 2, 3, 3, 3], 3, [1, 2, 3], "Triple dup"),
    ]

    implementations = [
        ("Way 1: Slow/fast (BEST)", remove_duplicates_1),
        ("Way 2: Set + sort", remove_duplicates_2),
        ("Way 3: Left/right", remove_duplicates_3),
        ("Way 4: While loop", remove_duplicates_4),
        ("Way 5: enumerate", remove_duplicates_5),
        ("Way 6: Index compare", remove_duplicates_6),
        ("Way 7: Recursive", remove_duplicates_7),
        ("Way 8: numpy", remove_duplicates_8),
        ("Way 9: Class-based", remove_duplicates_9),
        ("Way 10: Final cleanest", remove_duplicates_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for nums, expected_k, expected_first, desc in test_cases:
            try:
                nums_copy = copy.deepcopy(nums)
                # Some implementations (Way 7) destroy the array structure.
                # We test k and the first k elements.
                # If Way 7 recurses on nums[1:] it changes length — handle that.
                orig_len = len(nums_copy)
                if name == "Way 7: Recursive":
                    # Way 7 modifies nums in-place by recursive slicing —
                    # the resulting array is shorter.
                    # We just verify the first k elements.
                    pass
                result_k = fn(nums_copy)
                # Get first k elements (whatever they are now)
                first_k = nums_copy[:result_k] if result_k <= len(nums_copy) else list(nums_copy)
                # For Way 7, the array is now exactly the unique values.
                if name == "Way 7: Recursive":
                    ok = (result_k == expected_k and first_k == expected_first)
                else:
                    ok = (result_k == expected_k and first_k == expected_first)
                if ok:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: nums={nums} k={result_k} first_k={first_k} (expected k={expected_k} first_k={expected_first})")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 60)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
